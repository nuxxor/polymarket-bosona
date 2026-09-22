"""Frozen G4 quote lifecycle diagnosis. No network, bot imports or invented fills."""
from bisect import bisect_right
from collections import Counter, defaultdict
from decimal import Decimal as D
import gzip
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def quote_at(quotes, target, end):
    if target >= end:
        return None
    i = bisect_right([x['karar_ms'] for x in quotes], target)-1
    if i < 0:
        return None
    q = quotes[i]
    age = target-q['karar_ms']
    if not (0 <= age <= 1500 and 0 <= q['defter_yasi']*1000+age <= 3000
            and q['bb'] is not None and q['ba'] is not None
            and 0 < q['bb'] < q['ba'] <= 1):
        return None
    return dict(ms=q['karar_ms'], gap_ms=age, mid=(q['bb']+q['ba'])/2,
                bid=q['bb'], source_age_ms=q['defter_yasi']*1000+age)


def cancel_relation(fill, cancel, tolerance_ms=100):
    if cancel is None:
        return 'no_cancel_request'
    if fill['received_mono_ns'] < cancel['begin']['mono_ns']:
        return 'fill_seen_before_cancel'
    if fill['exchange_ms'] is None:
        return 'execution_clock_missing'
    t, a, b = fill['exchange_ms'], cancel['begin']['utc_ns']/1e6, cancel['end']['utc_ns']/1e6
    if t+tolerance_ms < a:
        return 'reported_fill_before_cancel'
    if t-tolerance_ms > b:
        return 'reported_fill_after_cancel_response'
    return 'reported_clock_overlaps_cancel_call'


def metrics(rows, horizon):
    known = [r for r in rows if r['markout'].get(str(horizon)) is not None]
    if not known:
        return dict(fills=0, parents=0, windows=0, shares=0, mid_minus_paid=None)
    q = sum(r['q'] for r in known)
    by_parent, by_window = defaultdict(list), defaultdict(list)
    for r in known:
        by_parent[r['oid']].append(r)
        by_window[r['S']].append(r)
    def avg(rs):
        return sum(r['q']*r['markout'][str(horizon)]['mid_minus_paid'] for r in rs)/sum(r['q'] for r in rs)
    return dict(fills=len(known), parents=len(by_parent), windows=len(by_window), shares=q,
                mid_minus_paid=avg(known), parent_equal=mean(avg(v) for v in by_parent.values()),
                window_equal=mean(avg(v) for v in by_window.values()),
                by_window={s: avg(v) for s, v in by_window.items()})


def matched_cells(rows, horizon, same_window):
    cells = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r['markout'][str(horizon)] is None:
            continue
        # Fixed diagnostic buckets, not searched thresholds or a trading policy.
        k = (r['oi'], int((r['price']+1e-9)*5), int(r['age_s']//30))
        if same_window:
            k = (r['S'],)+k
        cells[k][r['recent_up_replace']].append(r)
    pairs = []
    for k, arms in cells.items():
        if set(arms) != {False, True}:
            continue
        a, b = metrics(arms[True], horizon), metrics(arms[False], horizon)
        pairs.append(dict(cell=k, up_parents=a['parents'], control_parents=b['parents'],
                          up_windows=a['windows'], control_windows=b['windows'],
                          difference=a['parent_equal']-b['parent_equal']))
    leave_out = {}
    if same_window:
        for start in {p['cell'][0] for p in pairs}:
            rest = [p['difference'] for p in pairs if p['cell'][0] != start]
            leave_out[start] = mean(rest) if rest else None
    return dict(cells=pairs, mean_difference=mean(p['difference'] for p in pairs) if pairs else None,
                leave_one_window_out=leave_out)


def analyze(path):
    with gzip.open(path, 'rt') as f:
        rows = [json.loads(line) for line in f]
    assert rows[-1]['kind'] == 'end', 'incomplete extraction'
    meta = next(r['row'] for r in rows if r['kind'] == 'manifest')
    state = next(r['row'] for r in rows if r['kind'] == 'state')
    assert meta['hashes']['ab.py'] == '0fd30f9faee281d59ca57597005391579b0debbf5ff131ea66ee5a2bb9182ee1'
    assert meta['budget']['id'] == '9e510ca7460ed5970db5'
    orders = {o['oid']: dict(o, S=int(k.split('|')[1])) for k, w in state['windows'].items()
              for o in w['emir'] if o.get('oid')}
    sdk = [r['row'] for r in rows if r['kind'] == 'sdk']
    assert len({r['session'] for r in sdk}) == 1 and not any(r['errors'] for r in sdk)
    assert [r['seq'] for r in sdk] == list(range(1, len(sdk)+1))
    requests, posts, cancels = {}, {}, defaultdict(list)
    cancel_results = defaultdict(list)
    observed = defaultdict(list)
    for r in sdk:
        if r['event'] == 'request':
            requests[r['attempt']] = r
        if r['event'] == 'fill_observed' and r['oid'] in orders:
            observed[r['oid']].append(r)
        if r['event'] == 'g4_cancel_result':
            cancel_results[r['oid']].append(r)
        if r['event'] != 'response':
            continue
        req = requests[r['attempt']]
        if r['op'] == 'post_batch':
            for slot, result in zip(req['meta']['orders'], r['reply'].get('items') or [], strict=True):
                oid = result['oid']
                if oid in orders:
                    assert abs(slot['price']-orders[oid]['p']) < 1e-8 and req['meta']['post_only']
                    assert oid not in posts
                    posts[oid] = dict(begin=r['begin'], end=r['end'], S=orders[oid]['S'],
                                      oi=orders[oid]['oi'], price=slot['price'])
        if r['op'] in ('cancel', 'cancel_batch'):
            for oid in req['meta']['oids']:
                if oid in orders:
                    cancels[oid].append(r)
    assert set(posts) == set(orders), 'every accepted order needs a recorded POST'
    previous = {}
    for oid, p in sorted(posts.items(), key=lambda x: x[1]['begin']['mono_ns']):
        key = (p['S'], p['oi'])
        prev = previous.get(key)
        p.update(reprice='initial_or_after_fill', previous_oid=prev)
        closed = [r for r in cancel_results[prev] if r['confirmed'] and
                  r['mono_ns'] <= p['begin']['mono_ns']] if prev else []
        if closed and closed[-1]['matched'] < orders[prev]['boy']-1e-6:
            gap = (p['begin']['mono_ns']-closed[-1]['mono_ns'])/1e9
            if gap <= 10:
                p['reprice'] = ('up_replace' if p['price'] > posts[prev]['price']+1e-8
                                else 'down_or_same_replace')
        previous[key] = oid
    fills, ltps = {}, defaultdict(set)
    raw_private = 0
    for item in rows:
        if item['kind'] != 'stream':
            continue
        r = item['row']
        p = r.get('payload', {})
        if p.get('event_type') == 'last_trade_price' and p.get('transaction_hash'):
            ltps[p['transaction_hash']].add(int(p['timestamp']))
        if p.get('event_type') != 'trade' or p.get('status') != 'MATCHED':
            continue
        for maker in p['maker_orders']:
            oid = maker['order_id']
            if oid not in orders:
                continue
            assert p['trader_side'] == 'MAKER'
            raw_private += 1
            key = (p['id'], oid)
            q, price = D(maker['matched_amount']), D(maker['price'])
            if key not in fills:
                fills[key] = dict(oid=oid, trade=p['id'], q=q, price=price, S=orders[oid]['S'],
                                  oi=orders[oid]['oi'], tx=p.get('transaction_hash'),
                                  received_ns=r['received']['utc_ns'],
                                  received_mono_ns=r['received']['mono_ns'], lanes=set())
            old = fills[key]
            assert (old['q'], old['price'], old['tx']) == (q, price, p.get('transaction_hash'))
            old['lanes'].add(item['lane'])
            if r['received']['mono_ns'] < old['received_mono_ns']:
                old.update(received_ns=r['received']['utc_ns'], received_mono_ns=r['received']['mono_ns'])
    for oid, o in orders.items():
        actual = sum(f['q'] for f in fills.values() if f['oid'] == oid)
        assert abs(actual-D(str(o['pay']))) <= D('.000001'), (oid, actual, o['pay'])
    quotes = defaultdict(list)
    for item in rows:
        r = item['row']
        if item['kind'] == 'bot' and r.get('k') == 'G_KARAR':
            quotes[(r['S'], r['oi'])].append(r)
    for qs in quotes.values():
        qs.sort(key=lambda q: q['karar_ms'])
    output = []
    for f in fills.values():
        timestamps = ltps[f['tx']]
        ex = next(iter(timestamps)) if len(timestamps) == 1 else None
        # LTP source time is reported exchange time, not a proven execution instant.
        valid_clock = ex is not None and abs(f['received_ns']/1e6-ex) <= 2000
        f['exchange_ms'] = ex if valid_clock else None
        p = posts[f['oid']]
        f['post_to_receipt_ms'] = (f['received_mono_ns']-p['begin']['mono_ns'])/1e6
        assert f['post_to_receipt_ms'] >= 0
        f['reprice'] = p['reprice']
        f['reported_post_to_fill_ms'] = ex-p['begin']['utc_ns']/1e6 if valid_clock else None
        f['recent_up_replace'] = (p['reprice'] == 'up_replace' and valid_clock
                                  and 0 <= f['reported_post_to_fill_ms'] <= 10000)
        f['first_cancel_relation'] = cancel_relation(f, cancels[f['oid']][0] if cancels[f['oid']] else None)
        f['cancel_sensitivity'] = {t: cancel_relation(f, cancels[f['oid']][0] if cancels[f['oid']] else None, t)
                                   for t in (0, 100, 250)}
        f['observed_sources'] = sorted({x['source'] for x in observed[f['oid']]})
        f['lanes'] = sorted(f['lanes'])
        f['q'], f['price'] = float(f['q']), float(f['price'])
        anchor = f['exchange_ms']
        f['age_s'] = ((anchor if anchor is not None else f['received_ns']/1e6)/1000-f['S'])
        f['markout'] = {}
        for h in (10, 30):
            after = quote_at(quotes[(f['S'], f['oi'])], anchor+h*1000, (f['S']+300)*1000) if anchor else None
            f['markout'][str(h)] = (dict(after, mid_minus_paid=after['mid']-f['price'],
                                       bid_minus_paid=after['bid']-f['price']) if after else None)
        output.append(f)
    windows = []
    for key, w in sorted(state['windows'].items()):
        q = [sum(D(str(o.get('pay', 0))) for o in w['emir'] if o['oi'] == side) for side in (0, 1)]
        cost = sum(D(str(o.get('pay', 0)))*D(str(o['p']))+D(str(o.get('ucret', 0))) for o in w['emir'])
        pnl = q[w['kazanan']]-cost if w['cozuldu'] else None
        if pnl is not None:
            assert abs(pnl-D(str(w['hesap']['pnl']))) < D('.000001')
        windows.append(dict(S=int(key.split('|')[1]), qty=list(map(float, q)), cost=float(cost),
                            pnl=float(pnl) if pnl is not None else None, resolved=w['cozuldu'],
                            accepted=sum(bool(o.get('oid')) for o in w['emir'])))
    return dict(status='DESCRIPTIVE_SMALL_SAMPLE_NO_POLICY_CHANGE', manifest=meta,
                capture_sha256=sha256(path.read_bytes()).hexdigest(),
                accepted_parents=len(orders), filled_parents=len({f['oid'] for f in output}),
                unfilled_parents=sum(o['pay'] == 0 for o in orders.values()),
                raw_private_matches=raw_private, unique_trade_parent=len(output),
                shares=sum(f['q'] for f in output), quantity_reconciled=True,
                reported_clock_found=sum(f['exchange_ms'] is not None for f in output),
                raw_stream_tails=[r['row'] for r in rows if r['kind'] == 'stream_source'],
                sdk_rows=len(sdk), sdk_sequence_complete=True,
                placement_groups=dict(Counter(p['reprice'] for p in posts.values())),
                fill_groups=dict(Counter(f['reprice'] for f in output)),
                cancel_relations=dict(Counter(f['first_cancel_relation'] for f in output)),
                cancel_tagged_parent_fills=dict(Counter(f['first_cancel_relation'] for f in output
                    if any(s.startswith('kapat:') for s in f['observed_sources']))),
                cancel_marks={k: {h: metrics([f for f in output if f['first_cancel_relation'] == k], h)
                                  for h in (10, 30)} for k in sorted({f['first_cancel_relation'] for f in output})},
                observed_fill_sources=dict(Counter(x['source'] for xs in observed.values() for x in xs)),
                marks={h: {name: metrics(rs, h) for name, rs in (
                    ('all', output), ('up_replace_recent', [f for f in output if f['recent_up_replace']]),
                    ('other', [f for f in output if not f['recent_up_replace']]))} for h in (10, 30)},
                matched={h: dict(same_window=matched_cells(output, h, True),
                                pooled=matched_cells(output, h, False)) for h in (10, 30)},
                windows=windows, realized_pnl=sum(w['pnl'] for w in windows if w['resolved']),
                rows=output,
                limitations=['Only first six G4 windows on one day; not statistical validation.',
                             'Reported LTP timestamp with +/-100ms sensitivity; cancel effective time unknown.',
                             'Quotes are causal local decision snapshots at about 1Hz; not executable depth.',
                             'Mid/bid markouts are diagnostics, not realized strategy or guaranteed sale PnL.',
                             'Up-replacement and cancel labels are observational, not randomized policy effects.',
                             'Matching uses 20-cent price / 30-second age buckets and side; inventory is not matched.',
                             'Cross-window matched cells may still differ in market regime and inventory.',
                             'No receipt fetch or new authenticated account query; private fills checked against saved state.'])


if __name__ == '__main__':
    result = analyze(HERE/'capture.jsonl.gz')
    (HERE/'results.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ('accepted_parents', 'unique_trade_parent', 'shares',
                                           'reported_clock_found', 'fill_groups', 'cancel_relations',
                                           'realized_pnl')}, indent=2))
