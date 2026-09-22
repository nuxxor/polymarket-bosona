"""Actor-conditioned parent/order and first-reduction diagnostics; never a strategy replay."""
from collections import Counter, defaultdict
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import random
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT/'analiz/izleme'))
import bosona_gec_arastirma as base  # noqa: E402

PROBE = OUT.parent/'btc5m_order_identity_20260921/check.py'
spec = importlib.util.spec_from_file_location('order_probe', PROBE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
UNIT = 1000000


def read(name):
    return json.loads((OUT/name).read_text())


def units(value):
    result = D(str(value))*UNIT
    assert result == result.to_integral_value(), 'unexpected token/cash precision'
    return int(result)


def activity_key(r):
    return (r['transactionHash'], r['timestamp'], r['asset'], r['side'],
            r['outcomeIndex'], D(str(r['size'])), D(str(r['usdcSize'])))


def lot_cost(lots, quantity, reverse=False):
    remaining, cost = quantity, 0.
    for qty, price in sorted(lots, key=lambda x:x[1], reverse=reverse):
        take = min(qty, remaining)
        cost += take*price
        remaining -= take
        if remaining == 0:
            return cost/quantity
    raise ValueError('insufficient unmatched inventory')


def first_reduction(fills, winner):
    """First observed reducing second; ambiguity never selects a later, easier event."""
    by_second = defaultdict(list)
    for f in fills:
        by_second[f['ts']].append(f)
    balances, lots = [0, 0], []
    for ts, group in sorted(by_second.items()):
        sides = {f['outcome'] for f in group}
        net = balances[0]-balances[1]
        held = 0 if net > 0 else 1 if net < 0 else None
        if len(sides) > 1:
            return dict(status='ambiguous_first_reduction_both_sides', ts=ts)
        side, = sides
        if held is not None and side != held:
            if 'S' in group[0] and ts >= group[0]['S']+300:
                return dict(status='ambiguous_first_reduction_after_public_end', ts=ts)
            parents = {f['order_hash'] for f in group}
            if len(parents) != 1:
                return dict(status='ambiguous_first_reduction_multiple_parents', ts=ts,
                            parents=len(parents))
            quantity = sum(f['qty'] for f in group)
            closing = min(quantity, abs(net))
            prices = [f['cash_cost']/f['qty'] for f in group]
            if quantity > closing and max(prices)-min(prices) > 1e-8:
                return dict(status='ambiguous_overshoot_allocation', ts=ts)
            price = sum(f['cash_cost'] for f in group)/quantity
            low, high = lot_cost(lots, closing), lot_cost(lots, closing, True)
            delta = closing/UNIT*(1-price-(held == winner))
            return dict(status='valid', ts=ts, qty=closing/UNIT, held=held,
                        parent=next(iter(parents)), role=sorted({f['role'] for f in group}),
                        opposite_cash_price=price, held_qty=abs(net)/UNIT,
                        min_pair_cost=low+price, max_pair_cost=high+price,
                        all_lot_pair_cost_over_one=low+price > 1+1e-8,
                        delta=delta, normalized_five_delta=min(5,closing/UNIT)*(1-price-(held == winner)),
                        note='Whole first single-parent public-second group; no later fills replayed. Five-share value is arithmetic, not executable ask repricing.')
        for f in group:
            balances[side] += f['qty']
            lots.append((f['qty'], f['cash_cost']/f['qty']))
    return dict(status='no_reduction', delta=0., qty=0.)


def ratio_band(rows, numerator, denominator):
    days = defaultdict(lambda:[0., 0.])
    for r in rows:
        days[r['S']//86400][0] += r[numerator]
        days[r['S']//86400][1] += r[denominator]
    if not days or not sum(v[1] for v in days.values()):
        return None
    rng = random.Random(20260921)
    values = list(days.values())
    samples = []
    for _ in range(2000):
        batch = rng.choices(values, k=len(values))
        den = sum(x[1] for x in batch)
        if den:
            samples.append(sum(x[0] for x in batch)/den)
    samples.sort()
    return dict(ratio=sum(x[0] for x in values)/sum(x[1] for x in values),
                day_cluster_ci95=[samples[int(.025*len(samples))], samples[int(.975*len(samples))]],
                days=len(days), inference='Exploratory historical day bootstrap; not clean prospective validation.')


def continuation_bounds(selected, full):
    """No clock assumption: at most one fill can be the first fill of each order."""
    by_parent = defaultdict(list)
    for row in selected:
        by_parent[row['parent']].append(row)
    lower, upper, qlower, qupper = 0, 0, 0., 0.
    for parent, rows in by_parent.items():
        whole = len(rows) == len(full[parent])
        quantity = sum(r['qty'] for r in rows)
        lower += len(rows)-1
        upper += len(rows)-int(whole)
        qlower += quantity-max(r['qty'] for r in rows)
        qupper += quantity-(min(r['qty'] for r in rows) if whole else 0)
    return dict(records=[lower,upper], shares=[qlower,qupper],
                note='Order identity alone; any ordering allowed. Which same-second fill came first remains unknown.')


def main():
    manifest, markets, raw = read('manifest.json'), read('markets.json'), read('activity.json')
    fetch = read('fetch_manifest.json')
    for name, digest in manifest['input_sha256'].items():
        assert sha256((OUT/name).read_bytes()).hexdigest() == digest
    for name, digest in fetch['files'].items():
        assert sha256((OUT/name).read_bytes()).hexdigest() == digest
    actor, = {r['proxyWallet'].lower() for r in raw}
    raw_buys = [r for r in raw if r['type'] == 'TRADE']
    by_tx, by_market = defaultdict(list), defaultdict(list)
    for row in raw_buys:
        by_tx[row['transactionHash']].append(row)
        by_market[int(row['slug'].rsplit('-',1)[1])].append(row)
    decoded, failures = {}, []
    for tx, group in by_tx.items():
        try:
            receipt = read(f'receipts/{tx}.json')
            assert receipt['transactionHash'] == tx
            fills = probe.decode(receipt, actor)
            times = {r['timestamp'] for r in group}
            assert len(times) == 1
            for token in {r['asset'] for r in group} | {f['token'] for f in fills}:
                api = [r for r in group if r['asset'] == token]
                actual = [f for f in fills if f['token'] == token]
                assert all(r['side'] == 'BUY' for r in api) and all(f['side'] == 0 for f in actual)
                assert sum(units(r['size']) for r in api) == sum(f['qty'] for f in actual), 'API/token quantity mismatch'
                assert abs(sum(units(r['usdcSize']) for r in api)-sum(f['cash_cost'] for f in actual)) <= 10, 'API cash mismatch'
            for f in fills:
                candidate = next(r for r in group if r['asset'] == f['token'])
                start = int(candidate['slug'].rsplit('-',1)[1])
                market = markets[str(start)]
                tokens = json.loads(market['clobTokenIds'])
                assert all(r['conditionId'] == market['conditionId'] and r['asset'] == tokens[r['outcomeIndex']]
                           for r in group if r['asset'] == f['token'])
                f.update(S=start, outcome=tokens.index(f['token']), ts=next(iter(times)),
                         block=int(receipt['blockNumber'],16), transaction_index=int(receipt['transactionIndex'],16))
            decoded[tx] = fills
        except (OSError, ValueError, AssertionError, KeyError, IndexError, TypeError) as error:
            failures.append(dict(tx=tx, error=type(error).__name__, reason=str(error)[:180]))
    all_fills = [f for ff in decoded.values() for f in ff]
    parent_fills = defaultdict(list)
    for f in all_fills:
        parent_fills[f['order_hash']].append(f)
    market_results = []
    for start in manifest['selected']:
        buys = by_market[start]
        matched = [r for r in buys if r['transactionHash'] in decoded]
        fs = [f for f in all_fills if f['S'] == start]
        parents = {f['order_hash'] for f in fs}
        result = dict(S=start, records=len(buys), matched_records=len(matched),
                      shares=sum(float(r['size']) for r in buys), matched_shares=sum(float(r['size']) for r in matched),
                      exchange_fills=len(fs), parents=len(parents),
                      maker_shares=sum(f['qty'] for f in fs if f['role']=='maker')/UNIT,
                      maker_fills=sum(f['role']=='maker' for f in fs),
                      multiparent_role_orders=sum(len({x['role'] for x in parent_fills[p]})>1 for p in parents),
                      split_orders=sum(len(parent_fills[p])>1 for p in parents))
        try:
            history = read(f'full_activity/{start}.json')
            assert history['complete']
            fresh_buys = [r for r in history['rows'] if r['type']=='TRADE']
            assert Counter(map(activity_key, fresh_buys)) == Counter(map(activity_key, buys)), 'full-history trade multiset differs'
            assert len(matched) == len(buys), 'incomplete onchain trade coverage'
            winner = base.outcome(markets[str(start)])
            q, cash = [0.,0.], 0.
            for r in history['rows']:
                size, usd = float(r['size']), float(r['usdcSize'])
                if r['type']=='TRADE':
                    q[r['outcomeIndex']] += size
                    cash -= usd
                elif r['type']=='MERGE':
                    q = [x-size for x in q]
                    cash += usd
                elif r['type']=='REDEEM':
                    assert r['outcomeIndex'] in (0,1), 'unknown redeem token'
                    q[r['outcomeIndex']] -= size
                    cash += usd
                else:
                    raise ValueError('unsupported non-trade inventory event')
                assert min(q) >= -.00002, 'negative observed token balance'
            expected = sum(float(r['size'])*(r['outcomeIndex']==winner)-float(r['usdcSize']) for r in buys)
            assert abs(cash+q[winner]-expected) <= .00002, 'terminal cash/inventory mismatch'
            result.update(status='complete', api_cash_pnl=expected, winner=winner,
                          remaining=q, observed_cash=cash, initial_inventory='zero; full public condition history assumption')
            reduction = first_reduction(fs,winner)
            result['first_reduction'] = reduction
        except (OSError, ValueError, AssertionError, KeyError, IndexError) as error:
            result.update(status='missing', reason=str(error)[:180])
        market_results.append(result)

    late_results = []
    for row in read('late20_labels.json'):
        candidates = [f for f in decoded.get(row['tx'],[]) if f['outcome']==row['side']
                      and abs(f['qty']/UNIT-row['qty']) < 1e-6
                      and abs(f['cash_cost']/UNIT-row['qty']*row['cash_price']) < .000011]
        parents = {f['order_hash'] for f in candidates}
        result = dict(S=row['S'], tx=row['tx'], qty=row['qty'], parent_mapping='unique' if len(candidates)==1 else 'ambiguous_or_missing')
        if len(candidates)==1:
            parent, = parents
            history = parent_fills[parent]
            before = [f for f in history if f['ts'] < row['ts']]
            same = [f for f in history if f['ts']==row['ts']]
            result.update(parent=parent, earlier_second=bool(before), same_second_other_fill=len(same)>1,
                          log_index=candidates[0]['log_index'], total_parent_fills=len(history),
                          roles=sorted({f['role'] for f in candidates}))
        late_results.append(result)

    cohorts = {}
    for name, starts in manifest['cohorts'].items():
        rr = [r for r in market_results if r['S'] in starts]
        good = [r for r in rr if r['status']=='complete']
        first = [dict(S=r['S'], **r['first_reduction']) for r in good]
        valid = [r for r in first if r['status'] in ('valid','no_reduction')]
        actual = [r for r in valid if r['status']=='valid']
        by_role = {}
        for role in sorted({','.join(r['role']) for r in actual}):
            subset = [r for r in actual if ','.join(r['role'])==role]
            by_role[role] = dict(markets=len(subset), shares=sum(r['qty'] for r in subset),
                local_delta=sum(r['delta'] for r in subset),
                robust_over_one_markets=sum(r['all_lot_pair_cost_over_one'] for r in subset))
        cohorts[name] = dict(markets=len(rr), complete_markets=len(good),
            records=sum(r['records'] for r in rr), matched_records=sum(r['matched_records'] for r in rr),
            shares=sum(r['shares'] for r in rr), matched_shares=sum(r['matched_shares'] for r in rr),
            exchange_fills=sum(r['exchange_fills'] for r in rr), parents=sum(r['parents'] for r in rr),
            split_orders=sum(r['split_orders'] for r in rr), mixed_role_orders=sum(r['multiparent_role_orders'] for r in rr),
            maker_share_ratio=ratio_band(rr,'maker_shares','matched_shares'),
            maker_fill_ratio=ratio_band(rr,'maker_fills','exchange_fills'),
            first_reduction_status=Counter(r['status'] for r in first),
            first_reduction_local=base.summary(valid,field='delta') if valid else None,
            local_delta_per_evaluable_market=sum(r['delta'] for r in valid)/len(valid) if valid else None,
            first_reduction_by_role=by_role,
            robust_over_one_markets=sum(r['all_lot_pair_cost_over_one'] for r in actual),
            robust_over_one_shares=sum(r['qty'] for r in actual if r['all_lot_pair_cost_over_one']),
            first_reduction_shares=sum(r['qty'] for r in actual))
    eligible = [r for r in late_results if r['parent_mapping']=='unique']
    late = dict(records=len(late_results), mapped=len(eligible),
                earlier_second_records=sum(r['earlier_second'] for r in eligible),
                earlier_second_shares=sum(r['qty'] for r in eligible if r['earlier_second']),
                same_second_only_records=sum(not r['earlier_second'] and r['same_second_other_fill'] for r in eligible),
                total_shares=sum(r['qty'] for r in late_results),
                mapped_shares=sum(r['qty'] for r in eligible), parents=len({r['parent'] for r in eligible}))
    if len(eligible)==len(late_results):
        late['clock_free_continuation_bounds'] = continuation_bounds(eligible,parent_fills)
    result = dict(cohorts=cohorts, late20=late, receipt_failures=failures,
        market_results=market_results, late20_records=late_results, fills=all_fills,
        limits='Actor-conditioned historical sample. No fills/placements invented, no executable independent strategy PnL, no clean OOS interval.',
        source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__),PROBE,Path(base.__file__))})
    (OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(cohorts=cohorts,late20=late,receipt_failures=len(failures),
                    market_failures=Counter(r.get('reason') for r in market_results if r['status']!='complete')),indent=2))


if __name__ == '__main__':
    main()
