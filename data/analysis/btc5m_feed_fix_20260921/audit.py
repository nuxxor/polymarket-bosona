#!/usr/bin/env python3
"""Read-only verification of the deployed shadow journals and frozen sources."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--complete', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(args.root/'analiz/izleme'))
import bosona_inventory_shadow as inv  # noqa: E402

report = dict(captured_ms=round(time.time()*1000), shadows={})
for name, module in [('inventory', inv), ('rebound_v3', inv.r)]:
    out = args.root/'data'/name
    manifest = json.loads((out/'watch_manifest.json').read_text())
    assert manifest['mode'] == 'SHADOW_NO_ORDERS'
    for filename, sha in manifest['source_sha256'].items():
        assert hashlib.sha256((args.root/'analiz/izleme'/filename).read_bytes()).hexdigest() == sha
    events = [json.loads(line) for line in (out/'shadow.jsonl').read_text().splitlines()]
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
        assert e['execution_ms']-d['decision_ms'] <= 3000
        if name == 'inventory':
            for lane, f in e['fills'].items():
                key = e['S'], e['age'], lane
                assert key not in seen
                seen.add(key)
                gross, fee = inv.base.ask_cost(e['books'][f['side']], markets[e['S']], f['qty'])
                assert abs(f['cost']-gross-fee) < 1e-8
                history = histories[e['S'], lane]
                if f['kind'] == 'complete':
                    assert inv.paired_cost(inv.position(history), f['side'], f['qty'])+f['cost'] <= .98*f['qty']+1e-8
                history.append(f)
                p = inv.position(history)
                assert p['cash'] <= 15+1e-8 and p['floor'] >= -5-1e-8 and abs(p['qty'][0]-p['qty'][1]) <= 10+1e-8
        else:
            for side, cost in enumerate(e['costs']):
                if cost is None:
                    assert e['cost_errors'][side]
                else:
                    assert list(inv.base.ask_cost(e['execution_books'][side], markets[e['S']])) == cost
    S = manifest['start_S']
    first = [e for e in decisions.values() if e['S'] == S]
    attempted = {e['age'] for e in events if e.get('S') == S and e['kind'] in ('decision', 'gap')}
    if args.complete:
        assert attempted == set(module.SLOTS), (name, sorted(attempted))
        if name == 'rebound_v3':
            assert (S, 280) in decisions, 'first primary t280 still lacks valid context'
    report['shadows'][name] = dict(manifest=manifest, first_window_attempted=sorted(attempted),
        decisions=len(decisions), first_window_valid_context=sum(not e.get('context_gap') for e in first),
        context_gaps=dict(Counter(e['context_gap'] for e in decisions.values() if e.get('context_gap'))),
        gaps=dict(Counter(e['reason'] for e in events if e['kind'] == 'gap')),
        partial_book_decisions=sum(any(b and (b['bid'] is None or b['ask'] is None) for b in e['books'])
                                   for e in decisions.values() if not e.get('context_gap')),
        selected=sum(e.get('entry_side', e.get('rebound')) is not None for e in decisions.values()),
        fills=len(seen) if name == 'inventory' else None,
        executed_rules={rule: sum(e['kind'] == 'execution' and e[rule] is not None and e['costs'][e[rule]] is not None
                                  for e in events) for rule in ('rebound', 'favorite')} if name == 'rebound_v3' else None,
        unavailable_rules={rule: sum(e['kind'] == 'execution' and e[rule] is not None and e['costs'][e[rule]] is None
                                    for e in events) for rule in ('rebound', 'favorite')} if name == 'rebound_v3' else None,
        positions=[dict(S=s, lane=lane, **inv.position(fs)) for (s, lane), fs in histories.items()],
        latest_health=next(e for e in reversed(events) if e['kind'] == 'health'),
        latest_recorded_ms=events[-1]['recorded_ms'])
report['validation'] = 'PASS'
print(json.dumps(report, separators=(',', ':')))
