"""Audit M5 queue assumptions; diagnostic sensitivities, never inferred real fills."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import gzip
import importlib.util
import json
import sys

OUT = Path(__file__).resolve().parent
BASE = OUT.parent/'btc5m_m5_20260922'
sys.path.insert(0, str(BASE))
SPEC = importlib.util.spec_from_file_location('m5', BASE/'analyze.py')
m5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m5)
m1, read = m5.m1, m5.read


def level_path(events, order):
    """Reuse the frozen book parser, retaining only changes at this order's price."""
    lo, hi = int(order['send_ms'])-100, order['terminal_observed_ms']+1000
    token, px = order['tokens'][order['oi']], m1.units(order['price'])
    times = {lo, int(order['send_ms']), int(order['ack_ms']), int(hi)}
    times.update(e['rcv'] for e in events if lo <= e['rcv'] <= hi and
                 (e['k']=='book' and e['p']['asset_id']==token or
                  e['k']=='price_change' and any(c['asset_id']==token and c['side']=='BUY'
                  and m1.units(c['price'])==px for c in e['p']['price_changes'])))
    snapshots, issues = m1.books_at(events, order['tokens'], times)
    assert not issues, issues
    path = []
    for when, pair in snapshots.items():
        book = pair[order['oi']]
        qty = book['BUY'].get(px, 0)
        assert book['ready'] and qty == pair[1-order['oi']]['SELL'].get(m1.UNIT-px, 0)
        if not path or path[-1]['quantity_units'] != qty:
            path.append(dict(received_ms=when, source_ms=book['obs'], quantity_units=qty))
    return path


def depth_at(path, when):
    return next(r['quantity_units'] for r in reversed(path) if r['received_ms'] <= when)


def matching_decrements(path, flow, quantity):
    """Candidate links only: equal quantities do not prove event identity or cause."""
    return [dict(before_units=a['quantity_units'], after_units=b['quantity_units'],
                 source_ms=b['source_ms'], received_ms=b['received_ms'],
                 public_source_lag_ms=flow['obs_lo']-b['source_ms'])
            for a, b in zip(path, path[1:])
            if a['quantity_units']-b['quantity_units']==quantity
            and 0 <= flow['obs_lo']-b['source_ms'] <= 1000]


def verify_inputs():
    files = [BASE/'analyze.py', BASE/'prepare.py', BASE/'report.json',
             BASE/'clock_qualification.json', Path(m1.__file__), Path(m1.probe.__file__),
             OUT.parent/'btc5m_maker_feasibility_20260921/report.json',
             OUT.parent/'btc5m_own_execution_20260921/report.json']
    manifest = read(BASE/'input_manifest.json')
    expected = {BASE/n:h for n,h in manifest['files'].items()}
    expected.update({OUT.parent/n:h for n,h in manifest['source'].items()})
    fetch = BASE/'receipt_fetch'
    fetched = read(fetch/'fetch_manifest.json')
    assert not fetched['failures']
    expected.update({fetch/n:h for n,h in fetched['files'].items()})
    expected.update({BASE/n:h for n,h in read(BASE/'own_manifest.json').items()})
    for path, digest in expected.items():
        assert sha256(path.read_bytes()).hexdigest()==digest, path
    return {str(p.relative_to(OUT.parent)):sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(files)|set(expected))}


def main():
    hashes = verify_inputs()
    orders, baseline = read(BASE/'orders.json'), read(BASE/'report.json')
    events = [json.loads(s) for s in gzip.open(BASE/'events.jsonl.gz', 'rt')]
    groups = {p.stem:m1.matches(read(p)) for p in sorted((BASE/'receipt_fetch/receipts').glob('*.json'))}
    trace = [json.loads(s) for s in (OUT.parent/'btc5m_m4_v2_20260922/final_0112/LOG_f_emir_iz.jsonl').read_text().splitlines()]
    rows = []
    for start in sorted({o['S'] for o in orders}):
        market_orders = [o for o in orders if o['S']==start]
        evs = [e for e in events if e['S']==start]
        flows, errors, _ = m1.trade_flows([e for e in evs if e['k']=='last_trade_price'
            and e['p'].get('transaction_hash') in groups], groups, market_orders[0]['tokens'])
        assert not errors, errors
        makers = {(f['tx'],f['log_index']):(g,f) for gs in groups.values()
                  for g in gs for f in g['makers']}
        for order in market_orders:
            old = next(r for r in baseline['rows'] if r['oid']==order['oid'])
            path = level_path(evs, order)
            samples = {k:depth_at(path,t)/m1.UNIT for k,t in
                       [('pre100',int(order['send_ms'])-100),('send',order['send_ms']),('ack',order['ack_ms'])]}
            eligible = [f for f in flows if m5.eligible(f,order)
                        and order['send_ms']-100 <= f['obs_lo'] <= order['terminal_observed_ms']+100]
            actual = [(f, makers[f['tx'],f['log_index']]) for f in flows
                      if makers[f['tx'],f['log_index']][1]['order_hash']==order['oid']]
            assert sum(mk['qty'] for _,(_,mk) in actual)==m1.units(order['actual'])
            own = []
            for f,(group,maker) in actual:
                at_level = [x for x in flows if x['tx']==f['tx'] and
                    makers[x['tx'],x['log_index']][0]['match_log']==group['match_log'] and
                    x['side']==f['side'] and abs((x['price']-order['price'])*x['qty'])<=.000002]
                own.append(dict(tx=f['tx'], log_index=f['log_index'], quantity_units=maker['qty'],
                    source_ms=f['obs_lo'], received_ms=f['received'],
                    source_after_terminal_ms=f['obs_lo']-order['terminal_observed_ms'],
                    same_price_match_units=sum(m1.units(x['qty']) for x in at_level),
                    decrement_candidates=matching_decrements(path,f,sum(m1.units(x['qty']) for x in at_level))))
            # Arrival-depth substitution is an ablation, not the actual ahead queue:
            # own five shares and unknown additions behind us may be in this depth.
            ack_sensitivity = None if old['static_queue'] is None else [
                m1.queue_fill(m1.units(max(0,samples['ack']-order['size'])),m1.units(order['size']),m1.units(v))[1]/m1.UNIT
                for v in old['eligible_volume']]
            mismatch = old['static_queue'] is not None and not old['static_queue'][0] <= order['actual'] <= old['static_queue'][1]
            first = min((f['obs_lo'] for f in eligible),default=order['terminal_observed_ms'])
            prefix = [r for r in path if order['ack_ms'] <= r['received_ms'] < first]
            terminal = [r for r in trace if r['event']=='response' and r['op']=='get_order'
                        and r['reply'].get('oid')==order['oid'] and r['end']['utc_ns']/1e6<=order['terminal_observed_ms']+1]
            rows.append(dict(number=len(rows)+1, oid=order['oid'], S=start, side=order['oi'], price=order['price'],
                actual=order['actual'], send_ms=order['send_ms'], ack_ms=order['ack_ms'],
                terminal_ms=order['terminal_observed_ms'], initial_depth=samples,
                baseline_static=old['static_queue'], baseline_errors=old['errors'],
                baseline_mismatch=mismatch, ack_depth_sensitivity=ack_sensitivity,
                eligible_volume=old['eligible_volume'],
                depth_min_before_first_public_source=min((r['quantity_units']/m1.UNIT for r in prefix),default=None),
                level_path=path, own_fills=own,
                eligible_flows=[dict(f, order_hash=makers[f['tx'],f['log_index']][1]['order_hash']) for f in eligible],
                last_status_observations=[dict(begin_ms=r['begin']['utc_ns']/1e6,end_ms=r['end']['utc_ns']/1e6,
                    status=r['reply']['status'],matched=r['reply']['matched']) for r in terminal[-2:]],
                calibrated_prediction=None))
    summary = dict(accepted=len(rows), actual_shares=sum(r['actual'] for r in rows),
        baseline_mismatches=sum(r['baseline_mismatch'] for r in rows),
        arrival_sensitivity_mismatches=sum(r['ack_depth_sensitivity'] is not None and
            not r['ack_depth_sensitivity'][0]<=r['actual']<=r['ack_depth_sensitivity'][1] for r in rows),
        clock_nulls=sum(r['ack_depth_sensitivity'] is None for r in rows),
        eligible_route_counts=dict(Counter(f['route'] for r in rows for f in r['eligible_flows'])),
        own_fills=sum(len(r['own_fills']) for r in rows), status='NOT_CALIBRATED_QUEUE_AND_EVENT_IDENTITY_UNKNOWN')
    output = dict(summary=summary, rows=rows, inputs_sha256=hashes,
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        method='All 12 M4v2 accepts; M5 clocks/guards/volumes unchanged. Ack depth minus clip is sensitivity only. L2 decrement candidates never retime fills or earn queue credit. Same sample diagnostic, no OOS or strategy PnL.',
        limits='Millisecond L2 states coalesce same-ms messages. Depth includes unknown queue rank and our order. Equal-volume decrement is not order/trade identity. Cross-machine UTC synchronization is not established by these files.')
    (OUT/'report.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
