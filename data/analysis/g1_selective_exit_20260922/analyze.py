"""Historical actor diagnostics only; no strategy, network, or order submission."""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'btc5m_parent_research_20260921'
UNIT = 1_000_000


def read(name):
    return json.loads((SOURCE / name).read_text())


def classify(fills):
    """First filled public-second group per parent, never presumed placement time."""
    seconds = defaultdict(list)
    for f in fills:
        seconds[f['ts']].append(f)
    net, seen, rows, excluded = 0, set(), [], []
    for ts, group in sorted(seconds.items()):
        parents = {f['order_hash'] for f in group}
        sides = {f['outcome'] for f in group}
        new = parents - seen
        if len(parents) == len(sides) == 1 and ts < group[0]['S'] + 300:
            parent, = parents
            side, = sides
            qty = sum(f['qty'] for f in group)
            direction = 1 if side == 0 else -1
            reducing = min(qty, abs(net)) if net * direction < 0 else 0
            kind = ('open' if net == 0 else 'add' if net * direction > 0
                    else 'reduce' if qty <= abs(net) else 'reverse')
            if new:
                rows.append(dict(S=group[0]['S'], ts=ts, age=ts-group[0]['S'],
                                 parent=parent, side=side, net_before_units=net,
                                 quantity_units=qty, reducing_units=reducing, kind=kind,
                                 role='+'.join(sorted({f['role'] for f in group})),
                                 cash_price=sum(f['cash_cost'] for f in group)/qty,
                                 closed_fraction=reducing/abs(net) if reducing else None,
                                 transactions=sorted({f['tx'] for f in group})))
        elif new:
            excluded.append(dict(S=group[0]['S'], ts=ts, parents=sorted(new),
                                 reason='same-second multiple parents/sides or public time after end'))
        # All fills affect later inventory, including ambiguous groups and continuations.
        net += sum((1 if f['outcome'] == 0 else -1)*f['qty'] for f in group)
        seen.update(parents)
    assert net == sum((1 if f['outcome'] == 0 else -1)*f['qty'] for f in fills)
    assert len(rows) + sum(len(x['parents']) for x in excluded) == len(seen)
    return rows, excluded


def context(row, index):
    candidates = [c for tx in row['transactions'] for c in index[row['S'], tx, row['side']]]
    fields = ('now', 'bid', 'ask', 'spot', 'twap', 'ref')
    good = [c for c in candidates if all(k in c for k in fields)
            and c.get('exchange_age') is not None
            and c['now'] <= (row['S']+c['exchange_age'])*1000]
    unique = {tuple(c[k] for k in fields) for c in good}
    if len(unique) != 1 or not good or len(good) != len(candidates):
        return dict(status='missing_or_ambiguous_clock_book_reference')
    c = good[0]
    direction = 1 if row['side'] == 0 else -1
    return dict(status='observed_clock_context', **{k:c[k] for k in fields},
                spot_favors_bought_side=direction*(c['spot']-c['ref']) > 0,
                twap_favors_bought_side=direction*(c['twap']-c['ref']) > 0)


def summarize(rows):
    result = {}
    for role in sorted({x['role'] for x in rows}):
        group = [x for x in rows if x['role'] == role]
        reducing = [x for x in group if x['reducing_units']]
        ctx = [x for x in reducing if x['context']['status'] == 'observed_clock_context']
        result[role] = dict(
            parents=len(group), kinds=dict(Counter(x['kind'] for x in group)),
            markets=len({x['S'] for x in group}),
            reducing_share_fraction=sum(x['reducing_units'] for x in group)/sum(x['quantity_units'] for x in group),
            reducing_markets=len({x['S'] for x in reducing}),
            median_reducing_age=median(x['age'] for x in reducing) if reducing else None,
            median_closed_fraction=median(x['closed_fraction'] for x in reducing) if reducing else None,
            median_reducing_cash_price=median(x['cash_price'] for x in reducing) if reducing else None,
            near_flat_99pct=sum(x['closed_fraction'] >= .99 for x in reducing),
            reducing_contexts=len(ctx),
            spot_favors_bought_side=sum(x['context']['spot_favors_bought_side'] for x in ctx),
            twap_favors_bought_side=sum(x['context']['twap_favors_bought_side'] for x in ctx))
    return result


def check():
    def f(side, qty, ts, parent):
        return dict(S=0, outcome=side, qty=qty, cash_cost=qty//2,
                    ts=ts, order_hash=parent, role='taker', tx=parent)
    fs = [f(0, 5*UNIT, 1, 'a'), f(0, 5*UNIT, 2, 'a'),
          f(1, 10*UNIT, 3, 'b'), f(1, UNIT, 4, 'c'), f(0, 2*UNIT, 5, 'd')]
    rows, excluded = classify(fs)
    assert [x['kind'] for x in rows] == ['open', 'reduce', 'open', 'reverse']
    assert rows[1]['closed_fraction'] == 1 and rows[1]['net_before_units'] == 10*UNIT
    assert rows[-1]['reducing_units'] == UNIT and not excluded
    assert classify([dict(x, winner=1) for x in fs]) == classify([dict(x, winner=0) for x in fs])
    ambiguous = [f(0, UNIT, 1, 'a'), f(1, UNIT, 1, 'b'), f(0, UNIT, 2, 'c')]
    rows, excluded = classify(ambiguous)
    assert len(excluded) == 1 and rows[0]['kind'] == 'open'
    assert len(classify([f(0, UNIT, 300, 'a')])[0]) == 0
    dust = [f(0, UNIT+1, 1, 'a'), f(1, UNIT, 2, 'b'), f(1, 1, 3, 'c')]
    rows, _ = classify(dust)
    assert rows[-1]['net_before_units'] == 1 and rows[-1]['kind'] == 'reduce'


def main():
    check()
    report, manifest, contexts = read('report.json'), read('manifest.json'), read('contexts.json')
    assert sha256((SOURCE/'contexts.json').read_bytes()).hexdigest() == manifest['input_sha256']['contexts.json']
    assert read('verification.json')['report_sha256'] == sha256((SOURCE/'report.json').read_bytes()).hexdigest()
    assert all(x['status'] == 'complete' for x in report['market_results'])
    fills, index, rows, excluded = defaultdict(list), defaultdict(list), [], []
    parents = defaultdict(list)
    for f in report['fills']:
        fills[f['S']].append(f)
        parents[f['order_hash']].append(f)
    for c in contexts:
        index[c['S'], c['tx'], c['side']].append(c)
    for start, fs in sorted(fills.items()):
        history = read(f'full_activity/{start}.json')
        assert history['complete']
        assert all(x['type'] in ('TRADE', 'MERGE') and (x['type'] != 'TRADE' or x['side'] == 'BUY')
                   for x in history['rows'] if x['timestamp'] < start+300), 'unsupported live inventory flow'
        rr, ee = classify(fs)
        for row in rr:
            row['context'] = context(row, index)
        rows.extend(rr); excluded.extend(ee)
    result = dict(mode='EXPLORATORY_ACTOR_CONDITIONAL_NO_STRATEGY',
                  limitations=['First filled group is not order placement or full submitted quantity.',
                               'Contexts exist only for late fills; observed WS time is not exact actor decision time.',
                               'Historical cohorts were previously inspected; no clean OOS economic claim.',
                               'No observed counter-fill does not prove no counter-order.'],
                  inputs={n:sha256((SOURCE/n).read_bytes()).hexdigest() for n in ('report.json','manifest.json','contexts.json')},
                  code_sha256=sha256(Path(__file__).read_bytes()).hexdigest(), cohorts={},
                  rows=rows, excluded=excluded)
    for name, starts in dict(manifest['cohorts'], union=manifest['selected']).items():
        rr = [x for x in rows if x['S'] in starts]
        ee = [x for x in excluded if x['S'] in starts]
        first = [x for x in report['market_results'] if x['S'] in starts]
        excluded_roles = Counter()
        for event in ee:
            for parent in event['parents']:
                fs = parents[parent]
                first_ts = min(f['ts'] for f in fs)
                excluded_roles['+'.join(sorted({f['role'] for f in fs if f['ts'] == first_ts}))] += 1
        result['cohorts'][name] = dict(markets=len(starts), included_parents=len(rr),
            excluded_parents=sum(len(x['parents']) for x in ee), by_role=summarize(rr),
            excluded_first_group_roles=dict(excluded_roles),
            first_reduction_status=dict(Counter(x['first_reduction']['status'] for x in first)))
    (OUT/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['cohorts']['representative'], indent=2))


if __name__ == '__main__':
    main()
