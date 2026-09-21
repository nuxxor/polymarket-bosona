"""Offline review calculations; reads frozen evidence, never changes experiments."""
from collections import Counter, defaultdict
from decimal import Decimal
from hashlib import sha256
from itertools import groupby
from pathlib import Path
import gzip
import json

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'data/analysis'
OUT = Path(__file__).parent
COMMIT = 'add159d343948e4b46a5491b9bab4c78fceeeb40'


def read(relative):
    return json.loads((DATA / relative).read_text())


def multiplicity(winners):
    chunks = [json.loads(p.read_text()) for p in sorted((DATA/'bosona_gec_20260921/activity').glob('*.json'))]
    assert all(a['end']+1 == b['start'] for a, b in zip(chunks, chunks[1:]))
    assert all(c['complete'] and c['pages'] <= 11 for c in chunks)
    raw = [r for c in chunks for r in c['rows']
           if r.get('slug', '').startswith('btc-updown-5m-')
           and int(r['slug'].rsplit('-', 1)[1]) in winners]
    buys = [r for r in raw if r['type'] == 'TRADE']
    cash = sum(Decimal(str(r['usdcSize'])) for r in buys)
    payout = sum(Decimal(str(r['size'])) for r in buys
                 if r['outcomeIndex'] == winners[int(r['slug'].rsplit('-', 1)[1])])
    assert len(buys) == 19768 and payout-cash == Decimal('8313.228464')
    return dict(chunks=len(chunks), records=len(buys), cash=str(cash), payout=str(payout),
                pnl=str(payout-cash), raw_fetch_ms_range=[min(c['fetched_ms'] for c in chunks),
                                                       max(c['fetched_ms'] for c in chunks)])


def execution_roles(features):
    # Transaction-level event proxies; never silently treat them as actor order IDs.
    wanted = {r['tx'] for r in features}
    events = {}
    for path in sorted((DATA/'bosona_derin_20260921/tape_snapshots').glob('*.gz')):
        with gzip.open(path, 'rt') as stream:
            trades = json.load(stream)['trades']
        for _, _, _, event in trades:
            tx = event.get('transaction_hash')
            if tx in wanted:
                events.setdefault(tx, event)
    events.update(read('bosona_derin_20260921/new_trade_times.json'))
    tokens, groups, burst = {}, defaultdict(list), []
    for r in features:
        event = events.get(r['tx'])
        if event is None:
            continue
        S = r['S']
        if S not in tokens:
            market = read(f'bosona_gec_20260921/markets/btc-updown-5m-{S}.json')
            tokens[S] = json.loads(market['clobTokenIds'])
        same = tokens[S][r['side']] == event['asset_id']
        key = f"{'same' if same else 'opposite'}_token_{event['side']}_fee_{r['cost']-r['price'] > 1e-6}"
        groups[key].append(r)
        if S == 1789402200 and r['age'] == 256:
            burst.append(dict(tx=r['tx'], actor_qty=r['q'], actor_price=r['price'], actor_cost=r['cost'],
                              event_qty=event['size'], event_price=event['price'], role_proxy=key))
    counts = {k: len(v) for k, v in groups.items()}
    assert counts == {'opposite_token_BUY_fee_False': 3599, 'same_token_BUY_fee_True': 316,
                      'same_token_SELL_fee_False': 416}
    assert abs(sum(r['actor_qty'] for r in burst)-297) < 1e-8
    return dict(counts=counts, markets=len({r['S'] for rows in groups.values() for r in rows}), burst_297=burst)


def main():
    fills = read('bosona_gec_20260921/fill_ledger.json')
    windows = read('bosona_gec_20260921/windows.json')
    activity = read('bosona_gec_20260921/activity.json')
    features = read('bosona_derin_20260921/features.json')
    winners = {r['S']: r['winner'] for r in windows}
    buys = [r for r in activity if r['type'] == 'TRADE']
    assert all(r['side'] == 'BUY' for r in buys)
    cash = sum(Decimal(str(r['usdcSize'])) for r in buys)
    payout = sum(Decimal(str(r['size'])) for r in buys
                 if r['outcomeIndex'] == winners[int(r['slug'].rsplit('-', 1)[1])])
    assert len(buys) == len(fills) == 19761
    assert payout - cash == Decimal('8319.438464')
    grouped = defaultdict(list)
    for r in fills:
        grouped[r['S']].append(r)
    first = [r for r in fills if r['opening_kind'] == 'first']
    completion = [r for r in fills if r['completion_qty'] > 0]
    late = [r for r in fills if r['opening_kind'] == 'add' and 280 <= r['age'] < 300]
    assert len(late) == 271 and len({r['S'] for r in late}) == 66
    assert abs(sum(r['marginal_cash_pnl'] for r in late) - 1888.805825) < 1e-6
    burst = {}
    for gap in (0, 3):
        rows = [r for seq in grouped.values() for previous, r in zip(seq, seq[1:])
                if r['opening_kind'] == 'add' and 280 <= r['age'] < 300
                and r['side'] == previous['side'] and r['ts'] - previous['ts'] <= gap]
        burst[str(gap)] = dict(records=len(rows), pnl=sum(r['marginal_cash_pnl'] for r in rows))
    assert burst['0']['records'] == 157 and burst['3']['records'] == 210
    fees = {}
    for name, rows in (
        ('zero_premium_proxy', [r for r in fills if abs(r['cash_price'] - r['price']) < 1e-6]),
        ('positive_premium_proxy', [r for r in fills if r['cash_price'] - r['price'] >= 1e-6]),
    ):
        fees[name] = dict(records=len(rows), shares=sum(r['qty'] for r in rows),
                          pnl=sum(r['marginal_cash_pnl'] for r in rows),
                          equal_five_per_record=sum(5*r['marginal_cash_pnl']/r['qty'] for r in rows))
    assert sum(r['records'] for r in fees.values()) == len(fills)
    fees['positive_matches_fee_formula'] = sum(
        r['cash_price'] - r['price'] >= 1e-6
        and abs(r['cash_price'] - r['price'] - .07*r['price']*(1-r['price'])) < 1e-6
        for r in fills)
    cases = {}
    for S in (1789676700, 1789402200, 1789582500):
        qty, cumulative_cash, events = [0., 0.], 0., []
        for age, iterator in groupby(grouped[S], key=lambda r: r['age']):
            rows = list(iterator)
            before = qty.copy()
            for r in rows:
                qty[r['side']] += r['qty']
            cost = sum(r['qty']*r['cash_price'] for r in rows)
            cumulative_cash += cost
            events.append(dict(age=age, records=len(rows), before=before, after=qty.copy(),
                               price_range=[min(r['price'] for r in rows), max(r['price'] for r in rows)],
                               cash=cost, pnl=sum(r['marginal_cash_pnl'] for r in rows),
                               payoff_floor=min(qty)-cumulative_cash))
        total = qty[winners[S]] - cumulative_cash
        expected = next(r['cash_cost_pnl'] for r in windows if r['S'] == S)
        assert abs(total - expected) < 1e-6
        cases[str(S)] = dict(winner=winners[S], events=events, total_cash=cumulative_cash,
                             final_qty=qty, pnl=total,
                             contexts=[{k: r[k] for k in ('age', 'now', 'side', 'ref', 'spot', 'twap',
                                        'own_rsi', 'own_momentum', 'bid', 'ask', 'exchange_age') if k in r}
                                       for r in features if r['S'] == S])
    inputs = ['bosona_gec_20260921/' + n for n in ('activity.json', 'fill_ledger.json', 'windows.json')]
    inputs += ['bosona_derin_20260921/features.json']
    result = dict(commit=COMMIT, historical_market_starts_utc=['2026-09-13T00:00:00Z', '2026-09-20T22:30:00Z'],
                  end_exclusive=True, input_sha256={n: sha256((DATA/n).read_bytes()).hexdigest() for n in inputs},
                  accounting=dict(markets=len(windows), records=len(fills), cash=str(cash), payout=str(payout),
                                  pnl=str(payout-cash), shares=sum(r['qty'] for r in fills),
                                  ex_top3=sum(r['cash_cost_pnl'] for r in sorted(windows, key=lambda r: r['cash_cost_pnl'], reverse=True)[3:]),
                                  equal_five_per_market=sum(5*r['cash_cost_pnl']/r['qty'] for r in windows)),
                  first=dict(count=len(first), before_t30=sum(r['age'] < 30 for r in first),
                             at_least_50c=sum(r['price'] >= .5 for r in first)),
                  completion=dict(records=len(completion), negative_fifo=sum(r['pair_cash_pnl'] < 0 for r in completion),
                                  fails_average_98c=sum(r['pair_cash_pnl'] < .02*r['completion_qty']-1e-8 for r in completion)),
                  after_t200_openings=dict(Counter(r['opening_kind'] for r in fills
                                                   if r['opening_kind'] in ('first', 'reopen') and 200 < r['age'] < 300)),
                  late20_same_side_predecessor=burst, fees=fees, cases=cases,
                  raw_multiplicity=multiplicity(winners), execution_roles=execution_roles(features))
    (OUT/'calculations.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: cash reconciliation, fill-fragmentation counts, fee proxies and three market paths')


if __name__ == '__main__':
    main()
