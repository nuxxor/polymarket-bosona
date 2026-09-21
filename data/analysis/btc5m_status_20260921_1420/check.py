#!/usr/bin/env python3
"""Frozen six-window BTC5m checkpoint; public GETs only, no runtime changes."""
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path
import statistics
import sys
import time
import urllib.parse

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[2]/'analiz/izleme'))
import bosona_inventory_shadow as inv  # noqa: E402

base = inv.base
START, END = 1789998600, 1790000400
logs = {name: [json.loads(line) for line in (OUT/(name+'.jsonl')).read_text().splitlines()]
        for name in ('inventory', 'rebound_v3')}
assert all(e['recorded_ms'] <= END*1000 for events in logs.values() for e in events)


def cached(name, url):
    p = OUT/name
    if not p.exists():
        base.save(p, base.get(url))
    return json.loads(p.read_text())


def public_rows(endpoint, market):
    rows = []
    for offset in range(0, 5001, 500):
        query = dict(user=base.WALLET, market=market['conditionId'], limit=500, offset=offset)
        query.update(dict(takerOnly='false') if endpoint == 'trades' else dict(type='TRADE', sortBy='TIMESTAMP', sortDirection='ASC'))
        time.sleep(.2)
        batch = cached(f'{endpoint}_{market["slug"]}_{offset}.json',
                       'https://data-api.polymarket.com/'+endpoint+'?'+urllib.parse.urlencode(query))
        assert isinstance(batch, list)
        assert all(r['proxyWallet'].lower() == base.WALLET and r['conditionId'] == market['conditionId'] for r in batch)
        rows.extend(batch)  # Preserve genuine identical fills, do not set/dict-deduplicate.
        if len(batch) < 500:
            return [r for r in rows if r['timestamp'] < END]
    raise ValueError('pagination incomplete')


windows, bosona_fills, winners = {}, [], {}
for S in range(START, END, 300):
    slug = f'btc-updown-5m-{S}'
    m = cached(f'market_{S}.json', f'https://gamma-api.polymarket.com/markets/slug/{slug}?snapshot={END//30}')
    assert m['slug'] == slug and json.loads(m['outcomes']) == ['Up', 'Down']
    try:
        winners[S] = base.outcome(m)
    except ValueError:
        winners[S] = None
    aa, tt = public_rows('activity', m), public_rows('trades', m)
    def identity(r):
        return r['transactionHash'], r['outcomeIndex'], r['side'], round(float(r['size']), 6)
    assert Counter(map(identity, aa)) == Counter(map(identity, tt)), slug
    assert all(r['side'] == 'BUY' and str(r['asset']) == json.loads(m['clobTokenIds'])[r['outcomeIndex']] for r in aa)
    quantities = [sum(Decimal(str(r['size'])) for r in aa if r['outcomeIndex'] == side) for side in (0, 1)]
    cost = sum(Decimal(str(r['usdcSize'])) for r in aa)
    first_time = min((r['timestamp'] for r in aa), default=None)
    first = [r for r in aa if r['timestamp'] == first_time]
    q_first = sum(float(r['size']) for r in first)
    same_second = defaultdict(set)
    for a in aa:
        same_second[a['timestamp']].add(a['outcomeIndex'])
    window = dict(S=S, winner=winners[S], records=len(aa), shares=float(sum(quantities)),
                  cash_cost=float(cost), pnl=float(quantities[winners[S]]-cost) if winners[S] is not None else None,
                  qty=list(map(float, quantities)), first_age=first_time-S if first_time is not None else None,
                  first_side=first[0]['outcomeIndex'] if len({r['outcomeIndex'] for r in first}) == 1 else None,
                  first_price=sum(float(r['usdcSize']) for r in first)/q_first if q_first else None,
                  ambiguous_order=any(len(sides)>1 for sides in same_second.values()))
    if aa:
        ff, totals = base.ledger(aa, winners[S])
        if winners[S] is not None:
            assert abs(totals['cash_cost_pnl']-window['pnl']) < 1e-6
        bosona_fills.extend(ff)
    windows[S] = window

portfolios, seen = defaultdict(list), set()
for e in logs['inventory']:
    if e['kind'] != 'execution':
        continue
    for lane, f in e['fills'].items():
        key = e['S'], e['age'], lane
        assert key not in seen
        seen.add(key)
        history = portfolios[e['S'], lane]
        if f['kind'] == 'complete':
            assert inv.paired_cost(inv.position(history), f['side'], f['qty'])+f['cost'] <= .98*f['qty']+1e-8
        history.append(f)
        p = inv.position(history)
        assert p['cash'] <= 15+1e-8 and p['floor'] >= -5-1e-8 and abs(p['qty'][0]-p['qty'][1]) <= 10+1e-8
        assert e['request_ms'] >= e['decision_ms']+(250 if e['speed'] == '250' else 0)
for e in logs['inventory']:
    if e['kind'] == 'resolution':
        assert e['winner'] == winners[e['S']]
        for lane, pnl in e['pnl'].items():
            p = inv.position(portfolios[e['S'], lane])
            assert abs(p['qty'][e['winner']]-p['cash']-pnl) < 1e-8

lanes = {}
for lane in inv.LANES:
    fs = [f for (s, name), fills in portfolios.items() if name == lane for f in fills]
    positions = [dict(S=S, winner=winners[S], **inv.position(portfolios[S, lane])) for S in windows]
    firsts = [(S, fills[0]) for (S, name), fills in portfolios.items() if name == lane and fills]
    comparable = [(S, f) for S, f in firsts if windows[S]['first_side'] is not None]
    near = []
    for (S, name), fills in portfolios.items():
        if name != lane:
            continue
        for f in fills:
            ff = [b for b in bosona_fills if b['S'] == S and abs(b['age']-f['age']) <= 15]
            sides = {b['side'] for b in ff}
            if len(sides) == 1:
                near.append(f['side'] == next(iter(sides)))
    lanes[lane] = dict(traded_windows=len(firsts), fills=len(fs), kinds=dict(Counter(f['kind'] for f in fs)),
        pnl=sum(p['qty'][p['winner']]-p['cash'] for p in positions if p['winner'] is not None),
        pending_positions=[p for p in positions if p['winner'] is None and p['cash']],
        first_age_median=statistics.median(f['age'] for _, f in firsts) if firsts else None,
        first_price_median=statistics.median((f['cost']-f['fee'])/f['qty'] for _, f in firsts) if firsts else None,
        first_direction_comparable=len(comparable), first_direction_same=sum(windows[S]['first_side'] == f['side'] for S, f in comparable),
        nearby_15s_comparable=len(near), nearby_15s_same=sum(near), positions=positions)

rebound = {}
for age in inv.r.SLOTS:
    ds = [e for e in logs['rebound_v3'] if e['kind'] == 'decision' and e['age'] == age]
    es = [e for e in logs['rebound_v3'] if e['kind'] == 'execution' and e['age'] == age]
    vals = [inv.r.settle(e, winners[e['S']]) for e in es if winners[e['S']] is not None]
    rebound[age] = dict(decisions=len(ds), selected=sum(e['rebound'] is not None for e in es),
        pnl={rule: (sum(v[rule] for v in vals if v[rule] is not None)
                    if any(v[rule] is not None for v in vals) else None) for rule in ('rebound', 'favorite')},
        unavailable={rule: sum(v[rule] is None for v in vals) for rule in ('rebound', 'favorite')})
report = dict(start_S=START, end_S=END, windows=list(windows.values()), lanes=lanes, rebound=rebound,
    bosona=dict(traded_windows=sum(w['records']>0 for w in windows.values()), records=sum(w['records'] for w in windows.values()),
        pnl=sum(w['pnl'] for w in windows.values() if w['pnl'] is not None),
        role_shares={kind: sum(f['opening_qty'] for f in bosona_fills if f['opening_kind'] == kind) for kind in ('first', 'add', 'reopen')},
        completion_shares=sum(f['completion_qty'] for f in bosona_fills)),
    validation='PASS: frozen cutoff, per-market API multiplicities, tokens, independent cash totals, FIFO/risk/delay, official outcomes')
base.save(OUT/'report.json', report)
print(json.dumps({k:v for k,v in report.items() if k not in ('windows', 'lanes')}, indent=2))
print(json.dumps({lane:{k:v for k,v in d.items() if k != 'positions'} for lane,d in lanes.items()}, indent=2))
