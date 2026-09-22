"""Compare real M4v2 orders with M1 static queues using measured lifetime bounds."""
from collections import Counter
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import gzip
import importlib.util
import json
from statistics import median

from prepare import OUT, read, write

SPEC = importlib.util.spec_from_file_location('m1', OUT.parent/'btc5m_maker_feasibility_20260921/replay.py')
m1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1)


def eligible(flow, order):
    return flow['side'] == order['oi'] and (Decimal(str(flow['price']))-Decimal(str(order['price'])))*Decimal(str(flow['qty'])) <= Decimal('.000002')


def main():
    for name, digest in read(OUT/'input_manifest.json')['files'].items():
        assert sha256((OUT/name).read_bytes()).hexdigest() == digest
    fetch = OUT/'receipt_fetch'
    manifest = read(fetch/'fetch_manifest.json')
    assert not manifest['failures']
    for name, digest in manifest['files'].items():
        assert sha256((fetch/name).read_bytes()).hexdigest() == digest
    for name, digest in read(OUT/'own_manifest.json').items():
        assert sha256((OUT/name).read_bytes()).hexdigest() == digest
    orders = read(OUT/'orders.json')
    events = [json.loads(s) for s in gzip.open(OUT/'events.jsonl.gz', 'rt')]
    groups = {p.stem:m1.matches(read(p)) for p in (fetch/'receipts').glob('*.json')}
    wallet = read(OUT.parent/'btc5m_own_execution_20260921/public_wallet.json')['address']
    own = [f for gs in groups.values() for g in gs for f in [g['active'], *g['makers']] if f['owner']==wallet]
    rows, all_flows = [], []
    for start in sorted({o['S'] for o in orders}):
        market_orders = [o for o in orders if o['S']==start]
        evs = [e for e in events if e['S']==start]
        ltp = [e for e in evs if e['k']=='last_trade_price' and e['p'].get('transaction_hash') in groups]
        flows, mapping_errors, _ = m1.trade_flows(ltp, groups, market_orders[0]['tokens'])
        all_flows.extend(flows)
        for order in market_orders:
            actual = [f for f in own if f['order_hash']==order['oid']]
            assert abs(sum(f['qty'] for f in actual)/m1.UNIT-order['actual']) <= 1e-6
            assert all(f['role']=='maker' and f['token']==order['tokens'][order['oi']] for f in actual)
            when = int(order['send_ms'])-100
            snapshots, issues = m1.books_at(evs, order['tokens'], [when])
            pair = snapshots[when]
            problems = list(mapping_errors)
            if issues:
                problems.extend(issues)
            if any(not b['ready'] or not 0<=when-b['rcv']<=3000 or not 0<=when-b['obs']<=3000 for b in pair):
                problems.append('initial_book_missing_or_stale')
            px = m1.units(order['price'])
            ahead = pair[order['oi']]['BUY'].get(px, 0)
            if ahead != pair[1-order['oi']]['SELL'].get(m1.UNIT-px, 0):
                problems.append('mirror_depth_mismatch')
            lo, hi = order['send_ms']-100, order['terminal_observed_ms']+100
            clock_flows = [f for f in flows if f['obs_hi']>=lo and f['obs_lo']<=hi]
            for fill in actual:
                clock = next((f for f in flows if (f['tx'], f['log_index'])==(fill['tx'], fill['log_index'])), None)
                if clock is None or clock['obs_lo']<lo or clock['obs_hi']>hi:
                    problems.append('own_fill_clock_outside_sdk_bounds')
            if any(f['min_delay']<0 or f['max_delay']>1000 for f in clock_flows):
                problems.append('late_trade_clock')
            interval = [lo]+[e['rcv'] for e in evs if lo<e['rcv']<hi]+[hi]
            gap = max(b-a for a, b in zip(interval, interval[1:]))
            if gap>1000:
                problems.append('stream_gap')
            valid = [f for f in clock_flows if eligible(f, order)]
            # Favorable interval includes SDK uncertainty and status-confirmation lag.
            # These are diagnostic queue scenarios, not strict fill/PnL bounds.
            strict_end = order['cancel_begin_ms'] if order['cancel_success'] else order['terminal_observed_ms']
            volumes = [sum(m1.units(f['qty']) for f in valid if order['ack_ms']+100<=f['obs_lo']<=f['obs_hi']<=strict_end-100),
                       sum(m1.units(f['qty']) for f in valid)]
            predicted = [m1.queue_fill(ahead, m1.units(order['size']), v)[1]/m1.UNIT for v in volumes]
            bounds = dict(send_to_terminal_ms=order['terminal_observed_ms']-order['send_ms'],
                          post_ms=order['post_duration_ms'], cancel_ms=order['cancel_duration_ms'])
            rows.append(dict(oid=order['oid'], S=start, actual=order['actual'], status=order['status'],
                ahead=ahead/m1.UNIT, eligible_volume=[v/m1.UNIT for v in volumes],
                static_queue=predicted if not problems else None,
                front_queue=[min(order['size'], v/m1.UNIT) for v in volumes] if not problems else None,
                errors=sorted(set(problems)), max_gap_ms=gap, bounds=bounds,
                own_fills=[dict(tx=f['tx'], log_index=f['log_index'], quantity=f['qty']/m1.UNIT,
                               fee=f['fee']/m1.UNIT, role=f['role']) for f in actual]))
    flow_ids = {(f['tx'], f['log_index']):f for f in all_flows}
    clocks = []
    for fill in own:
        order = next((o for o in orders if o['oid']==fill['order_hash']), None)
        if order is None:
            continue
        flow = flow_ids.get((fill['tx'], fill['log_index']))
        clocks.append(dict(oid=order['oid'], quantity=fill['qty']/m1.UNIT,
            source_ms=flow['obs_lo'] if flow else None,
            clock_unique=bool(flow and flow['obs_lo']==flow['obs_hi']),
            receipt_delay_ms=flow['max_delay'] if flow else None,
            after_send_ms=flow['obs_lo']-order['send_ms'] if flow else None))
    usable = [r for r in rows if r['static_queue'] is not None]
    summary = dict(status='NOT_CALIBRATED_CLOCK_AND_QUEUE_MISMATCH', accepted=len(rows),
        own_chain_shares=sum(o['actual'] for o in orders), own_chain_fills=sum(len(r['own_fills']) for r in rows),
        cancel_calls=sum(o['cancel_begin_ms'] is not None for o in orders),
        confirmed_cancel_calls=sum(o['cancel_success'] for o in orders),
        usable_orders=len(usable), missing_reasons=dict(Counter(e for r in rows for e in r['errors'])),
        actual_usable=sum(r['actual'] for r in usable),
        static_usable=[sum(r['static_queue'][i] for r in usable) for i in (0, 1)],
        front_usable=[sum(r['front_queue'][i] for r in usable) for i in (0, 1)],
        actual_outside_static=sum(not r['static_queue'][0]-1e-6<=r['actual']<=r['static_queue'][1]+1e-6 for r in usable),
        post_median_ms=median(o['post_duration_ms'] for o in orders),
        cancel_median_ms=median(o['cancel_duration_ms'] for o in orders if o['cancel_duration_ms'] is not None),
        lifetime_median_ms=median(r['bounds']['send_to_terminal_ms'] for r in rows),
        methodology='SDK clocks are scenario endpoints, not proven exchange activation/cancel bounds; static pre-send queue, unchanged 100ms guards; no economic strategy claim',
        clock_qualification=read(OUT/'clock_qualification.json'))
    write('report.json', dict(summary=summary, rows=rows, own_fill_clocks=clocks,
        source_sha256={str(p.relative_to(OUT.parent)):sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), OUT/'prepare.py', OUT.parent/'btc5m_maker_feasibility_20260921/replay.py']}))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
