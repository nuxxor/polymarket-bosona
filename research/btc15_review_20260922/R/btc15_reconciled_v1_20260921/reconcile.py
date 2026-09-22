"""Rebuild public activity -> corrected phase/inventory -> role, offline."""
from collections import Counter, defaultdict
from decimal import Decimal as D
import gzip
import hashlib
import json

from common import INPUTS, R, U, accounting as a, protected, read, roles, save


def phase(x):
    return ('mixed' if x['opening_qty'] else 'completion') if x['completion_qty'] else x['opening_kind']


def summarize(rows):
    by = defaultdict(lambda: dict(qty=D(0), cash=D(0), pnl=D(0)))
    for x in rows:
        for k in by[x['slug']]:
            by[x['slug']][k] += x[k]
    pnl = sorted((x['pnl'] for x in by.values()), reverse=True)
    return dict(fills=len(rows), markets=len(by), pnl=sum(pnl, D(0)),
                ex_top3=sum(pnl[3:], D(0)), ex_top10=sum(pnl[10:], D(0)),
                equal5shares=sum((5*x['pnl']/x['qty'] for x in by.values()), D(0)),
                equal5cash=sum((5*x['pnl']/x['cash'] for x in by.values()), D(0)))


def main():
    protected()
    slices = [read(p) for p in sorted((R/'raw/activity').glob('*.json'))]
    until = a.ref.LOOKBACK
    for part in sorted(slices, key=lambda x: x['start']):
        assert part['complete']
        assert all(part['start'] <= x['timestamp'] <= part['end'] for x in part['rows'])
        if part['start'] <= until:
            until = max(until, part['end']+1)
    assert until >= a.ref.END
    # Reuse Ultra's multiplicity-preserving merge with corrected condition identity.
    acts = a.merge(slices, condition=True)
    overrides = {p.stem: read(p) for p in sorted((R/'raw/activity_checks').glob('*.json'))}
    acts = [x for x in acts if x.get('slug') not in overrides]
    acts += [x for rows in overrides.values() for x in rows if x['timestamp'] < a.ref.END]
    by = defaultdict(list)
    for x in acts:
        by[x.get('slug')].append(x)
    windows = read(R/'results/windows.json')
    published = defaultdict(list)
    for x in read(R/'results/fills.json'):
        published[x['slug']].append(x)
    rows, changes, groups = [], [], defaultdict(list)
    btc_activities = []
    for w in windows:
        slug = w['slug']
        m = read(R/'raw/markets'/f'{slug}.json')
        meta = a.ref.classify(m)
        assert meta['group'] != 'btc_5m' and meta['group'] == w['group']
        winner = a.ref.base.outcome(m)
        tokens = json.loads(m['clobTokenIds'])
        aa = by[slug]
        trades = [x for x in aa if x['type'] == 'TRADE']
        assert not any(x['type'] in ('SELL', 'SPLIT', 'CONVERSION') for x in aa)
        for x in trades:
            assert x['side'] == 'BUY' and x['conditionId'] == m['conditionId']
            assert x['asset'] == tokens[x['outcomeIndex']]
        rr, totals = a.ledger(trades, winner, meta['S'], first_seconds=0)
        a.actual_inventory(rr, aa)
        assert len(rr) == len(published[slug])
        assert abs(totals['pnl']-D(str(w['cash_cost_pnl']))) < D('0.000001')
        rate = m.get('feeSchedule', {}).get('rate')
        exponent = m.get('feeSchedule', {}).get('exponent')
        for x, old in zip(rr, published[slug]):
            assert (x['ts'], x['tx'], x['side']) == (old['ts'], old['tx'], old['side'])
            x.update(slug=slug, group=w['group'], S=meta['S'], end=meta['end'], winner=winner,
                     condition_id=m['conditionId'], token=tokens[x['side']],
                     phase=phase(x), old_phase=phase(old),
                     role=roles.role(float(x['price']), float(x['cash_price']), float(x['qty']), rate)
                     if rate is not None and exponent == 1 else 'unknown_fee_rule',
                     time_basis='public_activity_block_second',
                     old_window_ambiguous=old['ambiguous'])
            x['pre_inventory_valid'] = (x['pre_actual_qty'] is not None
                and not x['same_second_merge_ambiguous'] and min(x['pre_actual_qty']) >= 0)
            if x['phase'] != x['old_phase']:
                changes.append({k:x[k] for k in ('slug', 'group', 'ts', 'tx', 'role', 'phase', 'old_phase', 'pnl')})
            rows.append(x)
            groups[w['group']].append(x)
        if w['group'] == 'btc_15m':
            btc_activities.extend(aa)
    assert len(rows) == 14014 and len(windows) == 3503
    assert sum((x['pnl'] for x in rows), D(0)) == D('13393.820008')
    btc = groups['btc_15m']
    assert len(btc) == 5441
    late = a.late(btc)
    assert len(late) == 1150 and sum((x['pnl'] for x in late), D(0)) == D('3364.652672')
    table = {}
    for g, rr in sorted(groups.items()):
        table[g] = {role: summarize([x for x in rr if x['role'] == role])
                    for role in sorted({x['role'] for x in rr})}
    btc_table = {f'{p}|{r}': summarize([x for x in btc if x['phase'] == p and x['role'] == r])
                 for p in sorted({x['phase'] for x in btc}) for r in ('maker', 'taker')}
    # Preserve original temporal risk set; fix measured inventory/context/labels.
    # A fresh complete grid below also retains past states of future-ambiguous windows.
    context_path = U/'execution/corrected_contexts.json.gz'
    INPUTS[str(context_path)] = hashlib.sha256(context_path.read_bytes()).hexdigest()
    with gzip.open(context_path, 'rt') as f:
        contexts = json.load(f)
    grids, counts = [], Counter()
    btc_by = defaultdict(list)
    for x in btc:
        btc_by[x['slug']].append(x)
    for w in [w for w in windows if w['group'] == 'btc_15m']:
        ff = btc_by[w['slug']]
        for age in range(600, 900, 30):
            now = w['S']+age
            prior = [x for x in ff if x['ts'] <= now-5]
            if any(now-5 < x['ts'] < now for x in ff):
                counts['blind_interval_trade'] += 1
                continue
            aa = [x for x in by[w['slug']] if x['timestamp'] <= now-5]
            q = [sum((x['qty'] for x in prior if x['side'] == side), D(0)) for side in (0, 1)]
            net = q[0]-q[1]
            if not net:
                counts['no_open_net'] += 1
                continue
            merged = sum((D(str(x['size'])) for x in aa if x['type'] == 'MERGE'), D(0))
            actual = [v-merged for v in q]
            valid = min(actual) >= 0 and not any(x['type'] == 'REDEEM' for x in aa)
            cash = sum((x['cash'] for x in prior), D(0))-sum(
                (D(str(x['usdcSize'])) for x in aa if x['type'] in ('MERGE', 'REDEEM')), D(0))
            side = int(net < 0)
            after = [x for x in ff if now <= x['ts'] < now+30]
            add = [x for x in after if x['opening_kind'] == 'add' and x['side'] == side]
            opposite = [x for x in after if x['side'] != side]
            mixed_second = any(len({x['side'] for x in ff if x['ts'] == ts}) > 1
                               for ts in {x['ts'] for x in after})
            label = ('ambiguous' if mixed_second else 'mixed' if add and opposite else
                     'add' if add else 'opposite' if opposite else 'other' if after else 'no_observed_fill')
            grids.append(dict(slug=w['slug'], S=w['S'], ts=now, age=age, side=side,
                actual_qty=actual if valid else None, inventory_valid=valid, net=net,
                imbalance=abs(net)/sum(actual) if valid else None,
                old_imbalance=abs(net)/sum(q), net_cash=cash,
                label=label, role_counts=dict(Counter(x['role'] for x in after)),
                previously_excluded_whole_window=any(x['old_window_ambiguous'] for x in prior),
                context=contexts.get(f'{w["S"]}:{now}')))
    save('results/fills.json', rows)
    save('results/btc15_activity.json', sorted(btc_activities, key=lambda x:(x['timestamp'], x['transactionHash'])))
    save('results/phase_changes.json', changes)
    save('results/risk_set.json', grids)
    summary = dict(groups=table, btc15_role_phase=btc_table,
        late={role: summarize([x for x in late if role == 'ALL' or x['role'] == role])
              for role in ('ALL', 'maker', 'taker')}, phase_changes=len(changes),
        btc15_phase_changes=sum(x['group'] == 'btc_15m' for x in changes),
        risk_set=dict(states=len(grids), labels=dict(Counter(x['label'] for x in grids)),
                      exclusions=dict(counts), inventory_unknown=sum(not x['inventory_valid'] for x in grids),
                      context_missing=sum(x['context'] is None for x in grids),
                      future_window_filter_removed=sum(x['previously_excluded_whole_window'] for x in grids)),
        inputs_note='Corrected context artifact reused from Ultra; all raw activity remerged. '
                    'First-second phase is not parent identity; no new explanatory fit.')
    save('results/reconciliation.json', summary)
    save('results/input_manifest.json', INPUTS)
    protected()
    print(json.dumps({'late':summary['late'], 'risk_set':summary['risk_set']}, default=str))


if __name__ == '__main__':
    main()
