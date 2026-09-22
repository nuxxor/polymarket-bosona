#!/usr/bin/env python3
"""Offline Decimal audit; source directories are strictly read-only."""
import hashlib
import json
import statistics as st
import sys
from collections import Counter, defaultdict, deque
from decimal import Decimal as D
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
S = R / 'btc15_followup/status_20260921_1800'
sys.path.insert(0, str(R))
import research as ref  # noqa: E402

INPUTS = {}


def read(path):
    data = path.read_bytes()
    INPUTS[str(path)] = hashlib.sha256(data).hexdigest()
    return json.loads(data)


def save(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                       default=lambda x: str(x) if isinstance(x, D) else None) + '\n')


def key(x):
    return tuple(str(x.get(k, '')) for k in ('transactionHash', 'timestamp', 'type',
                 'asset', 'outcomeIndex', 'side', 'size', 'price', 'usdcSize'))


def merge(parts, condition=False):
    counts, examples = Counter(), {}
    identity = (lambda x: (x.get('conditionId', ''),)+key(x)) if condition else key
    for part in parts:
        assert part['complete']
        rows = [x for x in part['rows'] if ref.LOOKBACK <= x['timestamp'] < ref.END]
        counts |= Counter(map(identity, rows))
        examples.update((identity(x), x) for x in rows)
    return [examples[k] for k in sorted(counts) for _ in range(counts[k])]


def ledger(trades, winner, start, order='source', first_seconds=None):
    """Independent Decimal FIFO. first_seconds groups opening parts, never orders."""
    tie = {'source': lambda x: (x['transactionHash'], x['outcomeIndex']),
           'up_first': lambda x: (x['outcomeIndex'], x['transactionHash']),
           'down_first': lambda x: (-x['outcomeIndex'], x['transactionHash']),
           'reverse': lambda x: tuple(-ord(c) for c in x['transactionHash'])}
    trades = sorted(trades, key=lambda x: (x['timestamp'], tie[order](x)))
    lots, q, cost, rows, ever = [deque(), deque()], [D(0), D(0)], D(0), [], False
    first = trades[0]['timestamp'] if trades else 0
    pair = D(0)
    for x in trades:
        if x['side'] != 'BUY':
            raise ValueError('SELL needs a separate inventory ledger; never silently dropped')
        size, cash, p, side = D(str(x['size'])), D(str(x['usdcSize'])), D(str(x['price'])), x['outcomeIndex']
        if not all(v.is_finite() for v in (size, cash, p)) or size <= 0 or cash < 0 or not 0 <= p <= 1 or side not in (0, 1):
            raise ValueError('invalid trade')
        price = cash / size
        pre = q[0] - q[1]
        before = [v-cost for v in q]
        unmatched = sum((a*b for ll in lots for a, b in ll), D(0))
        remain, paired, pair_change = size, D(0), D(0)
        while remain and lots[1-side]:
            lot = lots[1-side][0]
            take = min(remain, lot[0])
            pair_change += take * (1-price-lot[1])
            lot[0] -= take
            remain -= take
            paired += take
            if not lot[0]:
                lots[1-side].popleft()
        kind = None
        if remain:
            kind = 'first' if not ever else 'add' if pre and side == (0 if pre > 0 else 1) else 'reopen'
            if first_seconds is not None and x['timestamp'] <= first + first_seconds:
                kind = 'first'
            lots[side].append([remain, price])
            ever = True
        q[side] += size
        cost += cash
        pair += pair_change
        rows.append(dict(ts=x['timestamp'], tx=x['transactionHash'], side=side, qty=size,
                         price=p, cash=cash, cash_price=price, age=x['timestamp']-start,
                         pre_qty=[q[i]-(size if i == side else 0) for i in (0, 1)],
                         pre_net=pre, pre_unmatched_cash_cost=unmatched,
                         pre_payoff=before, post_payoff=[v-cost for v in q],
                         opening_kind=kind, opening_qty=remain, completion_qty=paired,
                         pair_cash_pnl=pair_change, pnl=size*(side == winner)-cash))
    residual = sum((a*((side == winner)-b) for side in (0, 1) for a, b in lots[side]), D(0))
    total = q[winner]-cost
    assert abs(pair+residual-total) < D('1e-20')
    return rows, dict(qty=q, cash=cost, pnl=total, pair=pair, residual=residual,
                      peak_risk=max([D(0)]+[-min(x['post_payoff']) for x in rows]))


def aggregate(rows):
    by = defaultdict(lambda: [D(0), D(0)])
    for x in rows:
        by[x['slug']][0] += x['pnl']
        by[x['slug']][1] += x['qty']
    vals = [v[0] for v in by.values()]
    return dict(fills=len(rows), markets=len(by), pnl=sum(vals, D(0)),
                ex_top3=sum(sorted(vals, reverse=True)[3:], D(0)),
                equal5=sum((5*v/q for v, q in by.values()), D(0)))


def late(rows):
    return [x for x in rows if x['opening_kind'] == 'add' and 600 <= x['age'] < 900]


def packet_trades(trades, seconds):
    """Anchored non-overlapping time packets; no claim of shared parent orders."""
    batches, batch = [], []
    for x in sorted(trades, key=lambda x: (x['timestamp'], x['transactionHash'], x['outcomeIndex'])):
        if batch and x['timestamp'] > batch[0]['timestamp']+seconds:
            batches.append(batch)
            batch = []
        batch.append(x)
    if batch:
        batches.append(batch)
    result = []
    for batch in batches:
        for side in (0, 1):
            part = [x for x in batch if x['outcomeIndex'] == side]
            if not part:
                continue
            q = sum(D(str(x['size'])) for x in part)
            cash = sum(D(str(x['usdcSize'])) for x in part)
            result.append(dict(part[0], timestamp=batch[0]['timestamp'], size=str(q),
                usdcSize=str(cash), price=str(sum(D(str(x['size']))*D(str(x['price'])) for x in part)/q)))
    return result


def actual_inventory(rows, acts):
    # ponytail: per-market O(n²); use a sorted cashflow cursor if histories grow large.
    for x in rows:
        merges = [v for v in acts if v['type'] == 'MERGE' and v['timestamp'] < x['ts']]
        quantity = sum((D(str(v['size'])) for v in merges), D(0))
        cash = sum((D(str(v['usdcSize'])) for v in merges), D(0))
        redeems = [v for v in acts if v['type'] == 'REDEEM' and v['timestamp'] < x['ts']]
        # Zero-cash losing-token REDEEM rows do not disclose the burned token quantity.
        x['pre_actual_qty'] = None if redeems else [v-quantity for v in x['pre_qty']]
        x['prior_redeem_inventory_unknown'] = bool(redeems)
        x['pre_net_cash_spent'] = x['pre_qty'][0]-x['pre_payoff'][0]-cash-sum((D(str(v['usdcSize'])) for v in redeems), D(0))
        x['same_second_merge_ambiguous'] = any(v['type'] == 'MERGE' and v['timestamp'] == x['ts'] for v in acts)


def run():
    for name in ('research.py', 'study.py', 'src/bosona_gec_arastirma.py', 'src/muhasebe.py'):
        INPUTS[str(R/name)] = hashlib.sha256((R/name).read_bytes()).hexdigest()
    parts = [read(p) for p in sorted((R/'raw/activity').glob('*.json'))]
    covered_until = ref.LOOKBACK
    for part in sorted(parts, key=lambda p: p['start']):
        assert all(part['start'] <= x['timestamp'] <= part['end'] for x in part['rows'])
        if part['start'] <= covered_until:
            covered_until = max(covered_until, part['end']+1)
    assert covered_until >= ref.END
    rebuilt = merge(parts)
    original = read(R/'raw/activity.json')
    a, b = Counter(map(key, rebuilt)), Counter(map(key, original))
    merge_diff = dict(rebuilt=len(rebuilt), cached=len(original), added=sum((a-b).values()), removed=sum((b-a).values()))
    corrections = {p.stem: read(p) for p in sorted((R/'raw/activity_checks').glob('*.json'))}
    corrected = [x for x in merge(parts, condition=True) if x.get('slug') not in corrections]
    corrected += [x for part in corrections.values() for x in part if x['timestamp'] < ref.END]
    by = defaultdict(list)
    for x in corrected:
        if x.get('slug') and not x['slug'].startswith('btc-updown-5m-'):
            by[x['slug']].append(x)
    published = {w['slug']: w for w in read(R/'results/windows.json')}
    stored_fills = defaultdict(list)
    for x in read(R/'results/fills.json'):
        stored_fills[x['slug']].append(x)
    expected = set(read(R/'raw/universe.json')['expected'])
    wanted = expected | {s for s, v in by.items() if any(x['type'] == 'TRADE' for x in v)}
    coverage, windows, allrows, cases, extras, phase_changes = [], [], [], {}, [], []
    buckets = defaultdict(list)
    ordering = defaultdict(list)
    ordering_changes = defaultdict(list)
    packet_late = defaultdict(list)
    clean_raw_late = []
    completion_parts = []
    activity_counts = Counter()
    merge_during = []
    for slug in sorted(wanted):
        path = R/'raw/markets'/f'{slug}.json'
        if not path.exists():
            coverage.append(dict(slug=slug, status='metadata_missing'))
            continue
        m = read(path)
        meta = ref.classify(m)
        if not ref.START <= meta['S'] < ref.END or meta['end'] > ref.END:
            coverage.append(dict(slug=slug, group=meta['group'], status='outside_cohort'))
            continue
        try:
            winner = ref.base.outcome(m)
        except ValueError:
            coverage.append(dict(slug=slug, group=meta['group'], status='unresolved'))
            continue
        tt = [x for x in by[slug] if x['type'] == 'TRADE']
        coverage.append(dict(slug=slug, group=meta['group'], status='traded' if tt else 'no_observed_trade',
                             schedule_complete=meta['group'] in ref.PRIMARY))
        if not tt:
            continue
        assert slug in published
        assert not any(x['type'] in ('SPLIT', 'CONVERSION') for x in by[slug])
        tokens = json.loads(m['clobTokenIds'])
        assert all(x['conditionId'] == m['conditionId'] and str(x['asset']) == tokens[x['outcomeIndex']] and x['outcome'] == ['Up', 'Down'][x['outcomeIndex']] for x in tt)
        rr, totals = ledger(tt, winner, meta['S'])
        actual_inventory(rr, by[slug])
        for x in rr:
            x.update(slug=slug, S=meta['S'], group=meta['group'], winner=winner)
        assert abs(totals['pnl']-D(str(published[slug]['cash_cost_pnl']))) < D('0.00001')
        assert len(rr) == len(stored_fills[slug])
        for x, old in zip(rr, stored_fills[slug]):
            assert x['opening_kind'] == old['opening_kind']
            for k in ('pre_net', 'completion_qty', 'opening_qty', 'pair_cash_pnl'):
                assert abs(x[k]-D(str(old[k]))) < D('0.00001')
        activity_counts.update((x['type'], x.get('side', '')) for x in by[slug])
        merged = sum((D(str(x['usdcSize'])) for x in by[slug] if x['type'] == 'MERGE'), D(0))
        redeemed = sum((D(str(x['usdcSize'])) for x in by[slug] if x['type'] == 'REDEEM'), D(0))
        assert merged <= min(totals['qty']) + D('.0001')
        assert merged+redeemed <= totals['qty'][winner] + D('.0001')
        assert abs((-totals['cash']+merged+redeemed + totals['qty'][winner]-merged-redeemed)-totals['pnl']) < D('1e-20')
        for x in by[slug]:
            if x['type'] == 'MERGE' and x['timestamp'] <= max(t['timestamp'] for t in tt):
                merge_during.append(dict(slug=slug, timestamp=x['timestamp'], shares=x['size']))
        counts = Counter(map(key, tt))
        dedup = list({key(x): x for x in tt}.values())
        if len(dedup) != len(tt):
            _, reduced = ledger(dedup, winner, meta['S'])
            extras.append(dict(slug=slug, extra=len(tt)-len(dedup),
                               shares=sum(D(k[6])*(n-1) for k, n in counts.items()),
                               cash=totals['cash']-reduced['cash'], pnl=totals['pnl']-reduced['pnl']))
        first = min(x['ts'] for x in rr)
        mislabeled = [x for x in rr if x['ts'] == first and x['opening_kind'] == 'add']
        phase_changes.extend(mislabeled)
        qsum = sum(totals['qty'])
        w = dict(slug=slug, **meta, winner=winner, fills=len(tt), **totals,
                 first_age=first-meta['S'], both=min(totals['qty']) > 0,
                 first_qty=sum(x['qty'] for x in rr if x['ts'] == first),
                 first_price=sum(x['cash'] for x in rr if x['ts'] == first)/sum(x['qty'] for x in rr if x['ts'] == first),
                 equal5=5*totals['pnl']/qsum, late_pnl=sum(x['pnl'] for x in late(rr)),
                 merged=merged, redeemed=redeemed)
        windows.append(w)
        allrows.extend(rr)
        if meta['group'] != 'btc_15m':
            continue
        completion_parts.extend([x for x in rr if x['completion_qty'] > 0])
        for seconds in (0, 5, 10):
            keep = [x for x in late(rr) if x['ts'] > first+seconds]
            buckets[seconds].extend(keep)
            packed = packet_trades(tt, seconds)
            sides = defaultdict(set)
            for x in packed:
                sides[x['timestamp']].add(x['outcomeIndex'])
            if all(len(v) == 1 for v in sides.values()):
                pr, _ = ledger(packed, winner, meta['S'])
                packet_late[seconds].extend(dict(x, slug=slug) for x in late(pr))
                if seconds == 0:
                    clean_raw_late.extend(late(rr))
        for mode in ('source', 'up_first', 'down_first', 'reverse'):
            other, total2 = ledger(tt, winner, meta['S'], mode)
            assert totals['pnl'] == total2['pnl']
            other = [dict(x, slug=slug) for x in other]
            ordering[mode].extend(late(other))
            if abs(total2['pair']-totals['pair']) > D('0.000001') or aggregate(late(other))['pnl'] != aggregate(late(rr))['pnl']:
                ordering_changes[mode].append(dict(slug=slug, pair_delta=total2['pair']-totals['pair'],
                  late_delta=aggregate(late(other))['pnl']-aggregate(late(rr))['pnl']))
        cases[slug] = dict(window=w, fills=rr)
    groups = {}
    for group in sorted({w['group'] for w in windows}):
        ww = [w for w in windows if w['group'] == group]
        cc = Counter(x['status'] for x in coverage if x.get('group') == group)
        ff = [x for x in allrows if x['group'] == group]
        groups[group] = dict(coverage=dict(cc), full_schedule=group in ref.PRIMARY,
           fills=sum(w['fills'] for w in ww), pnl=sum(w['pnl'] for w in ww),
           ex_top3=sum(w['pnl'] for w in sorted(ww, key=lambda w: w['pnl'], reverse=True)[3:]),
           equal5=sum(w['equal5'] for w in ww), pair=sum(w['pair'] for w in ww),
           residual=sum(w['residual'] for w in ww), first_age_median=st.median(w['first_age'] for w in ww),
           first_qty_median=st.median(w['first_qty'] for w in ww), first_price_median=st.median(w['first_price'] for w in ww),
           both_sides=sum(w['both'] for w in ww), peak_risk_median=st.median(w['peak_risk'] for w in ww),
           peak_risk_max=max(w['peak_risk'] for w in ww),
           opening_add_qty=sum(x['opening_qty'] for x in ff if x['opening_kind'] == 'add'),
           completion_qty=sum(x['completion_qty'] for x in ff),
           total_qty=sum(x['qty'] for x in ff))
    btc = [x for x in allrows if x['group'] == 'btc_15m']
    btcwindows = [w for w in windows if w['group'] == 'btc_15m']
    postclose = [x for x in allrows if x['ts'] >= published[x['slug']]['end']]
    packages = {}
    for sec in (0, 5, 10):
        count, ambiguous = 0, 0
        sizes, first_sizes = [], []
        for w in btcwindows:
            ff = cases[w['slug']]['fills']
            first_sizes.append(sum(x['qty'] for x in ff if x['ts'] <= ff[0]['ts']+sec))
            batch = []
            for x in ff:
                if batch and x['ts'] > batch[0]['ts']+sec:
                    count += 1
                    ambiguous += len({z['side'] for z in batch}) > 1
                    sizes.append(len(batch))
                    batch = []
                batch.append(x)
            if batch:
                count += 1
                ambiguous += len({z['side'] for z in batch}) > 1
                sizes.append(len(batch))
        packages[str(sec)] = dict(packages=count, mixed_side_packages=ambiguous,
                                  fills_per_package_median=st.median(sizes), first_qty_median=st.median(first_sizes),
                                  late_after_first_package=aggregate(buckets[sec]))
    costly = [x for x in completion_parts if x['pair_cash_pnl']/x['completion_qty'] < D('-.000001')]
    riskparts = dict(completions=len(completion_parts), costly=len(costly), costly_pair_pnl=sum(x['pair_cash_pnl'] for x in costly),
       costly_risk_reduced=sum(min(x['post_payoff']) > min(x['pre_payoff'])+D('.00000001') for x in costly),
       overshoot=sum(x['opening_qty'] > 0 for x in completion_parts))
    quality = read(S/'results/book_quality.json')
    sw, sf, scases = [], [], {}
    for path in sorted((S/'raw/new_period_markets').glob('*.json')):
        slug = path.stem
        m = read(path)['data']
        meta = ref.classify(m)
        acts = [x for p in sorted((S/'raw/new_period_full').glob(slug+'_*.json')) for x in read(p)['data']]
        tt = [x for x in acts if x['type'] == 'TRADE']
        try:
            winner = ref.base.outcome(m)
        except ValueError:
            winner = None
        full = meta['S']*1000 >= quality['first_ms'] and meta['end']*1000 <= quality['asof_ms']
        rr, totals = ledger(tt, winner or 0, meta['S'])
        actual_inventory(rr, acts)
        rr = [dict(x, slug=slug, winner=winner) for x in rr]
        row = dict(slug=slug, **meta, full=full, winner=winner, fills=len(tt), **totals,
                   late=aggregate(late(rr)), activity_types=dict(Counter(x['type'] for x in acts)))
        if winner is None:
            row['pnl'] = None
        if full and winner is not None:
            sf.extend(rr)
        sw.append(row)
        scases[slug] = dict(window=row, fills=rr)
    closed = [w for w in sw if w['full'] and w['winner'] is not None]
    status = dict(full_closed=len(closed), traded=sum(w['fills'] > 0 for w in closed),
                  fills=sum(w['fills'] for w in closed), pnl=sum(w['pnl'] for w in closed),
                  late=aggregate(late(sf)), windows=sw)
    grid = read(R/'btc15_followup/results/risk_set.json')
    changed_grid = []
    for x in grid:
        before = [v for v in by[x['slug']] if v['timestamp'] <= x['ts']-5]
        gross_q = [sum((D(str(v['size'])) for v in before if v['type'] == 'TRADE' and v['outcomeIndex'] == i), D(0)) for i in (0, 1)]
        merged = sum((D(str(v['size'])) for v in before if v['type'] == 'MERGE'), D(0))
        if not merged:
            continue
        actual_q = [v-merged for v in gross_q]
        assert min(actual_q) >= -D('.000001') and sum(actual_q) > 0
        actual = abs(actual_q[0]-actual_q[1])/sum(actual_q)
        assert abs(actual_q[0]-actual_q[1]) == abs(gross_q[0]-gross_q[1])
        changed_grid.append(dict(slug=x['slug'], ts=x['ts'], old=x['imbalance'], actual=actual,
                                  merged=merged, gross_q=gross_q, actual_q=actual_q))
        x['imbalance'] = float(actual)
    chosen = [min(btcwindows, key=lambda w: w['pnl']), max(btcwindows, key=lambda w: w['pnl'])]
    chosen_s = [min(closed, key=lambda w: w['late']['pnl']), max(closed, key=lambda w: w['pnl']),
                next(w for w in closed if w['fills'] and not w['late']['fills'])]
    report = dict(groups=groups, windows=len(windows), fills=len(allrows), pnl=sum(w['pnl'] for w in windows),
      coverage=dict(Counter(x['status'] for x in coverage)), merge_reproduction=merge_diff,
      corrections=len(corrections), actual_equal_fills=extras, activity_counts={str(k): v for k, v in activity_counts.items()},
      merge_before_final_trade=merge_during, original_late=aggregate(late(btc)),
      first_second_mislabels=dict(all=aggregate(phase_changes), btc15=aggregate([x for x in phase_changes if x['group'] == 'btc_15m']),
                                 late=aggregate(late([x for x in phase_changes if x['group'] == 'btc_15m']))),
      packages=packages, ordering={k: dict(late=aggregate(v), changed=ordering_changes[k]) for k, v in ordering.items()},
      atomic_packet_late={str(k): aggregate(v) for k, v in packet_late.items()},
      same_second_unambiguous_raw_late=aggregate(clean_raw_late),
      merge_imbalance=dict(rows=len(changed_grid), markets=len({x['slug'] for x in changed_grid}),
          median_change=st.median(x['actual']-D(str(x['old'])) for x in changed_grid),
          max_change=max(x['actual']-D(str(x['old'])) for x in changed_grid)),
      postclose=dict(all=aggregate(postclose), btc15=aggregate([x for x in postclose if x['group'] == 'btc_15m']),
          initial_after_end=[w['slug'] for w in windows if w['first_age'] >= w['duration']]),
      completion=riskparts, status=status)
    save('result.json', report)
    save('windows.json', windows)
    save('coverage.json', coverage)
    save('cases.json', dict(historical={w['slug']: cases[w['slug']] for w in chosen},
                            status={w['slug']: scases[w['slug']] for w in chosen_s}))
    save('first_second_mislabels.json', phase_changes)
    save('merge_imbalance_changes.json', changed_grid)
    save('risk_set_actual_inventory.json', grid)
    save('postclose_fills.json', postclose)
    save('inputs.json', INPUTS)
    print(json.dumps({k: report[k] for k in ('windows', 'fills', 'pnl', 'coverage', 'first_second_mislabels', 'packages', 'completion')}, default=str))


if __name__ == '__main__':
    run()
