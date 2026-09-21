#!/usr/bin/env python3
"""Frozen London journals + cached public API checkpoint; no runtime mutations."""
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
START, END = 1790001900, 1790012400
snapshot = json.loads((OUT/'snapshot.json').read_text())


def cached(name, url):
    p = OUT/name
    if not p.exists():
        time.sleep(.25)
        base.save(p, base.get(url))
    return json.loads(p.read_text())


def public_rows(endpoint, market):
    rows = []
    for offset in range(0, 5001, 500):
        query = dict(user=base.WALLET, market=market['conditionId'], limit=500, offset=offset)
        query.update(dict(takerOnly='false') if endpoint == 'trades' else
                     dict(type='TRADE', sortBy='TIMESTAMP', sortDirection='ASC'))
        batch = cached(f'{endpoint}_{market["slug"]}_{offset}.json',
                       'https://data-api.polymarket.com/'+endpoint+'?'+urllib.parse.urlencode(query))
        assert isinstance(batch, list)
        assert all(r['proxyWallet'].lower() == base.WALLET and r['conditionId'] == market['conditionId'] for r in batch)
        rows.extend(batch)  # Preserve genuine repeated fills within complete market histories.
        if len(batch) < 500:
            return rows
    raise ValueError('incomplete pagination')


def identity(row):
    return row['transactionHash'], row['outcomeIndex'], row['side'], round(float(row['size']), 6)


winners, actor, actor_fills = {}, {}, {}
earliest = min(p['manifest']['start_S'] for p in snapshot['profiles'].values())
for S in range(earliest, END, 300):
    slug = f'btc-updown-5m-{S}'
    m = cached(f'market_{S}.json', 'https://gamma-api.polymarket.com/markets/slug/'+slug)
    assert m['slug'] == slug and json.loads(m['outcomes']) == ['Up', 'Down']
    winners[S] = base.outcome(m)  # Unresolved/invalid is an error, never a zero outcome.
    if S < START:
        continue
    aa, tt = public_rows('activity', m), public_rows('trades', m)
    assert Counter(map(identity, aa)) == Counter(map(identity, tt)), slug
    assert all(r['side'] == 'BUY' and str(r['asset']) == json.loads(m['clobTokenIds'])[r['outcomeIndex']] for r in aa)
    qty = [sum((Decimal(str(r['size'])) for r in aa if r['outcomeIndex'] == side), Decimal(0)) for side in (0, 1)]
    cash = sum((Decimal(str(r['usdcSize'])) for r in aa), Decimal(0))
    first = min((r['timestamp'] for r in aa), default=None)
    first_rows = [r for r in aa if r['timestamp'] == first]
    actor[S] = dict(S=S, records=len(aa), qty=list(map(float, qty)), cash=float(cash),
                    pnl=float(qty[winners[S]]-cash), winner=winners[S],
                    first_side=first_rows[0]['outcomeIndex'] if len({r['outcomeIndex'] for r in first_rows}) == 1 else None,
                    first_age=first-S if first is not None else None)
    actor_fills[S] = aa
    if (S-START)//300 % 10 == 0:
        print('public market checks', (S-START)//300+1, '/', (END-START)//300, flush=True)


def stats(values):
    running = peak = drawdown = 0.
    for value in values:
        running += value
        peak = max(peak, running)
        drawdown = max(drawdown, peak-running)
    return dict(pnl=sum(values), ex_top3=sum(values)-sum(sorted(values, reverse=True)[:3]),
                settlement_sequence_drawdown=drawdown)


report = dict(start_S=START, end_S=END, captured_ms=snapshot['captured_ms'], profiles={})
for name, profile in snapshot['profiles'].items():
    m, events = profile['manifest'], profile['events']
    assert m['mode'] == 'SHADOW_NO_ORDERS' and m['source_sha256'] == profile['hashes']
    assert profile['process'].split()[1] == '0'
    assert 0 <= snapshot['captured_ms']-events[-1]['recorded_ms'] < 90000
    decisions = {(e['S'], e['age']): e for e in events if e['kind'] == 'decision'}
    assert len(decisions) == sum(e['kind'] == 'decision' for e in events)
    markets = {e['S']: e['market'] for e in events if e['kind'] == 'market'}
    histories, seen = defaultdict(list), set()
    for e in events:
        if e['kind'] != 'execution':
            continue
        d = decisions[e['S'], e['age']]
        delay = 250 if name == 'rebound_v3' or e['speed'] == '250' else 0
        assert e['request_ms'] >= d['decision_ms']+delay
        assert 0 <= e['execution_ms']-d['decision_ms'] <= 3000
        if name == 'rebound_v3':
            for side, cost in enumerate(e['costs']):
                if cost is None:
                    assert e['cost_errors'][side]
                else:
                    assert list(base.ask_cost(e['execution_books'][side], markets[e['S']])) == cost
            continue
        for lane, f in e['fills'].items():
            key = e['S'], e['age'], lane
            assert key not in seen
            seen.add(key)
            fs = histories[e['S'], lane]
            expected = inv.execute(d['intents'][lane], fs, e['books'], markets[e['S']], f['age'])
            assert expected == f
            for clock in ('observed_ms', 'received_ms'):
                assert 0 <= e['execution_ms']-e['books'][f['side']][clock] <= 3000
            fs.append(f)
            p = inv.position(fs)
            assert p['cash'] <= 15+1e-8 and p['floor'] >= -5-1e-8 and abs(p['qty'][0]-p['qty'][1]) <= 10+1e-8
    common = [e for e in events if START <= e.get('S', 0) < END]
    attempted = {(e['S'], e['age']) for e in common if e['kind'] in ('decision', 'gap')}
    expected = {(s, age) for s in range(START, END, 300) for age in m['slots']}
    assert attempted == expected, (name, expected-attempted, attempted-expected)
    ds = [e for e in common if e['kind'] == 'decision']
    details = dict(process=profile['process'], version=m['version'], scheduled=len(expected),
                   decisions=len(ds), gaps=dict(Counter(e['reason'] for e in common if e['kind'] == 'gap')),
                   context_gaps=dict(Counter(e['context_gap'] for e in ds if e.get('context_gap'))),
                   latest_ms=events[-1]['recorded_ms'], missing_scheduled=0)
    for e in events:
        if e['kind'] != 'resolution' or e['S'] >= END:
            continue
        assert e['winner'] == winners[e['S']]
        if name != 'rebound_v3':
            for lane, pnl in e['pnl'].items():
                fs = histories[e['S'], lane]
                cash = sum((Decimal(str(f['cost'])) for f in fs), Decimal(0))
                payout = sum((Decimal(str(f['qty'])) for f in fs if f['side'] == e['winner']), Decimal(0))
                assert abs(float(payout-cash)-pnl) < 1e-8
        else:
            for x in events:
                if x['kind'] == 'execution' and x['S'] == e['S']:
                    assert e['pnl'][str(x['age'])] == inv.r.settle(x, e['winner'])
    if name == 'rebound_v3':
        details['slots'] = {}
        for age in m['slots']:
            es = [e for e in common if e['kind'] == 'execution' and e['age'] == age]
            details['slots'][age] = dict(valid_decisions=sum(e['age'] == age for e in ds), executions=len(es))
            for rule in ('rebound', 'favorite'):
                selected = [e for e in es if e[rule] is not None]
                fills = [e for e in selected if e['costs'][e[rule]] is not None]
                vals = [inv.r.settle(e, winners[e['S']])[rule] for e in es]
                details['slots'][age][rule] = dict(selected=len(selected), fills=len(fills),
                    unavailable=len(selected)-len(fills), valid_zero=sum(e[rule] is None for e in es),
                    **stats([v for v in vals if v is not None]))
    else:
        for period, start in [('common', START), ('since_start', m['start_S'])]:
            details[period] = {}
            for lane in inv.LANES:
                positions, firsts, fs_all, near = [], [], [], []
                for S in range(start, END, 300):
                    fs = histories[S, lane]
                    pos = inv.position(fs)
                    cash = sum((Decimal(str(f['cost'])) for f in fs), Decimal(0))
                    payout = sum((Decimal(str(f['qty'])) for f in fs if f['side'] == winners[S]), Decimal(0))
                    positions.append(dict(S=S, qty=pos['qty'], cash=float(cash), pnl=float(payout-cash), winner=winners[S]))
                    fs_all.extend(fs)
                    if fs:
                        firsts.append((S, fs[0]))
                    if S in actor:
                        for f in fs:
                            sides = {a['outcomeIndex'] for a in actor_fills[S] if abs(a['timestamp']-S-f['age']) <= 15}
                            if len(sides) == 1:
                                near.append(f['side'] == next(iter(sides)))
                comparable = [(S, f) for S, f in firsts if S in actor and actor[S]['first_side'] is not None]
                total_qty = sum(sum(p['qty']) for p in positions)
                details[period][lane] = dict(assigned=len(positions), traded=len(firsts), fills=len(fs_all),
                    kinds=dict(Counter(f['kind'] for f in fs_all)), fees=sum(f['fee'] for f in fs_all),
                    cash=sum(p['cash'] for p in positions), shares=total_qty,
                    paired_share_fraction=2*sum(min(p['qty']) for p in positions)/total_qty if total_qty else None,
                    terminal_unmatched_shares=sum(abs(p['qty'][0]-p['qty'][1]) for p in positions),
                    first_age_median=statistics.median(f['age'] for _, f in firsts) if firsts else None,
                    first_direction_comparable=len(comparable), first_direction_same=sum(actor[S]['first_side'] == f['side'] for S, f in comparable),
                    nearby_comparable=len(near), nearby_same=sum(near), positions=positions,
                    **stats([p['pnl'] for p in positions]))
        details['after_cohort_inventory'] = [dict(S=s, lane=lane, **inv.position(fs))
                                              for (s, lane), fs in histories.items() if s >= END and fs]
    report['profiles'][name] = details
report['bosona'] = dict(assigned=len(actor), traded=sum(a['records'] > 0 for a in actor.values()),
    records=sum(a['records'] for a in actor.values()), cash=sum(a['cash'] for a in actor.values()),
    shares=sum(sum(a['qty']) for a in actor.values()), windows=list(actor.values()),
    **stats([a['pnl'] for a in actor.values()]))
report['validation'] = 'PASS: complete schedules, frozen sources, fees/FIFO/risk/delay/uniqueness, official outcomes, Decimal cash, activity/trades multiplicities'
base.save(OUT/'report.json', report)
print(report['validation'])
for name, d in report['profiles'].items():
    print(name, json.dumps({k: v for k, v in d.items() if k not in ('common', 'since_start', 'after_cohort_inventory')}))
    for period in ('common', 'since_start'):
        if period in d:
            print(period, json.dumps({lane: {k: v for k, v in s.items() if k != 'positions'} for lane, s in d[period].items()}))
print('bosona', json.dumps({k: v for k, v in report['bosona'].items() if k != 'windows'}))
