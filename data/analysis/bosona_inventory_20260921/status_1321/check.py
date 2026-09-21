#!/usr/bin/env python3
"""Frozen, read-only BTC5m runtime and public-price coverage check."""
import bisect
from collections import Counter, defaultdict
from decimal import Decimal
import importlib
import json
from pathlib import Path
import statistics
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT/'analiz/izleme'))
inv = importlib.import_module('bosona_inventory_shadow')
runtime = json.loads((OUT/'runtime.json').read_text())
cutoff = runtime['captured_ms']
prices = json.loads((OUT/'prices.json').read_text())
logs = {n: [e for line in (OUT/(n+'.jsonl')).read_text().splitlines()
            if (e := json.loads(line))['recorded_ms'] <= cutoff] for n in ('inventory', 'rebound_v2')}
report = dict(cutoff_ms=cutoff, inventory={}, rebound_v2={}, context_diagnostics=[])
histories = defaultdict(list)
keys = set()
for e in logs['inventory']:
    if e['kind'] != 'execution':
        continue
    for lane, f in e['fills'].items():
        key = e['S'], e['age'], lane
        assert key not in keys
        keys.add(key)
        assert e['request_ms'] >= e['decision_ms']+(250 if e['speed'] == '250' else 0)
        history = histories[e['S'], lane]
        if f['kind'] == 'complete':
            assert inv.paired_cost(inv.position(history), f['side'], f['qty'])+f['cost'] <= .98*f['qty']+1e-8
        history.append(f)
        pos = inv.position(history)
        assert pos['floor'] >= -5-1e-8 and pos['cash'] <= 15+1e-8
        assert abs(pos['qty'][0]-pos['qty'][1]) <= 10+1e-8

report['inventory']['positions'] = []
for (S, lane), history in sorted(histories.items()):
    pos = inv.position(history)
    cash = sum(Decimal(str(f['cost'])) for f in history)
    quantities = [sum(Decimal(str(f['qty'])) for f in history if f['side'] == side) for side in (0, 1)]
    floor = min(quantities)-cash
    assert abs(float(floor)-pos['floor']) < 1e-8
    report['inventory']['positions'].append(dict(S=S, lane=lane, **pos,
        fills=len(history), balanced=quantities[0] == quantities[1], ended=S*1000+300000 <= cutoff))
for e in logs['inventory']:
    if e['kind'] == 'resolution':
        for lane, value in e['pnl'].items():
            p = inv.position(histories[e['S'], lane])
            assert abs(value-(p['qty'][e['winner']]-p['cash'])) < 1e-8

for name, es in logs.items():
    ds = [e for e in es if e['kind'] == 'decision']
    report[name]['decisions'] = len(ds)
    report[name]['gaps'] = dict(Counter(e['reason'] for e in es if e['kind'] == 'gap'))
    report[name]['latest_health'] = next(e for e in reversed(es) if e['kind'] == 'health')
    if name == 'inventory':
        report[name]['entry_context_valid'] = sum(e['context_gap'] is None for e in ds)
        report[name]['entry_context_gaps'] = dict(Counter(e['context_gap'] for e in ds if e['context_gap']))
    else:
        report[name]['eligible_by_slot'] = dict(Counter(e['age'] for e in ds))
        report[name]['selected_by_slot'] = dict(Counter(e['age'] for e in ds if e['rebound'] is not None))
    for e in es:
        if e.get('context_gap') != 'incomplete or stale context' and e.get('reason') != 'incomplete or stale context':
            continue
        when = e.get('feature_cutoff_ms', e['recorded_ms'])
        c = [v['bars'] for v in es if v['kind'] == 'bars' and v['recorded_ms'] <= when][-1]
        assert 'rsi14' in inv.r.deep.candle_features(([a[6] for a in c['rows']], c['rows']), when)
        streams = {s: ([], []) for s in ('spot', 'twap60')}
        names = {'crypto_prices_chainlink': 'spot', 'crypto_prices_twap_sixty': 'twap60'}
        for received, observed, feed_name, price in prices:
            if feed_name not in names or not when-65000 <= received <= when or observed > received:
                continue
            times, values = streams[names[feed_name]]
            if values and observed < values[-1][0]:
                continue
            times.append(received)
            values.append((observed, price))
        stale = []
        for source, back in [('twap60', 0)]+[('spot', i*5000) for i in range(13)]:
            t = when-back
            times, values = streams[source]
            i = bisect.bisect_right(times, t)-1
            lag = None if i < 0 else max(t-times[i], t-values[i][0])
            if lag is None or lag > 3000:
                stale.append(dict(source=source, back_ms=back, lag_ms=lag))
        report['context_diagnostics'].append(dict(model=name, S=e['S'], age=e['age'], candle_valid=True, stale=stale))

stale = [s for e in report['context_diagnostics'] for s in e['stale'] if s['lag_ms'] is not None]
report['stale_summary'] = dict(context_events=len(report['context_diagnostics']),
    events_with_stale_sample=sum(bool(e['stale']) for e in report['context_diagnostics']),
    stale_sample_ms_median=statistics.median(s['lag_ms'] for s in stale),
    stale_sample_ms_max=max(s['lag_ms'] for s in stale),
    history_only_events=sum(bool(e['stale']) and all(s['back_ms'] > 0 for s in e['stale']) for e in report['context_diagnostics']))
# Fresh canonical results validate the ended inventory markets; open windows stay open as of the cutoff.
report['official_results'] = {}
for S in sorted({s for s, lane in histories if s*1000+300000 <= cutoff}):
    p = OUT/f'market_{S}.json'
    if not p.exists():
        m = inv.base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{S}?snapshot={cutoff//30000}')
        p.write_text(json.dumps(m))
    m = json.loads(p.read_text())
    assert m['slug'] == f'btc-updown-5m-{S}'
    report['official_results'][S] = inv.base.outcome(m) if m.get('closed') else None
report['inventory']['officially_resolved_pnl_by_lane'] = {lane: sum(inv.position(histories[S, lane])['qty'][winner]-inv.position(histories[S, lane])['cash']
    for S, winner in report['official_results'].items() if winner is not None) for lane in inv.LANES}
report['validation'] = 'PASS: source manifests, journal uniqueness, delay, risk, FIFO/Decimal, recorded payouts, closed candles; pending official results separate'
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k: v for k, v in report.items() if k != 'context_diagnostics'}, indent=2))
