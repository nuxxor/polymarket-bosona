#!/usr/bin/env python3
"""Observe committed rebound decisions, without changing either frozen shadow."""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import bosona_rebound_shadow as shadow


def compare(original, observed):
    fast = {(r['S'], r['age']): r for r in observed if r['kind'] == 'fast_quote'}
    delayed = {(r['S'], r['age']): r for r in original if r['kind'] == 'execution'}
    rows = []
    for key in sorted(fast.keys() & delayed.keys()):
        a, b = fast[key], delayed[key]
        assert (a['rebound'], a['favorite']) == (b['rebound'], b['favorite'])
        rows.append(dict(S=key[0], age=key[1], selected=a['rebound'] is not None,
                         fast_ms=a['received_ms']-a['decision_ms'], delayed_ms=b['delay_ms'],
                         gain={rule: 0. if a[rule] is None else sum(b['costs'][a[rule]])-sum(a['costs'][a[rule]])
                               for rule in ('rebound', 'favorite')}))
    return dict(paired=len(rows), fast_only=len(fast.keys()-delayed.keys()),
                delayed_only=len(delayed.keys()-fast.keys()), counts=dict(Counter(r['kind'] for r in observed)),
                by_age={str(age): dict(pairs=len(rr), selected=sum(r['selected'] for r in rr),
                                      fast_median_ms=statistics.median(r['fast_ms'] for r in rr),
                                      delayed_median_ms=statistics.median(r['delayed_ms'] for r in rr),
                                      fast_minus_delayed_pnl={rule: sum(r['gain'][rule] for r in rr)
                                                              for rule in ('rebound', 'favorite')})
                        for age in shadow.SLOTS if (rr := [r for r in rows if r['age'] == age])},
                note='Same selected side and five shares. Paired cost difference; resolution cancels out. '
                     'Missing quotes excluded from paired comparison and counted separately. HTTP quotes, not actual fills.',
                rows=rows)


def watch(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    lock = (out/'watch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    parent = json.loads((args.parent/'watch_manifest.json').read_text())
    source = dict(observer=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), parent=shadow.hashes())
    if source['parent'] != parent['source_sha256']:
        raise ValueError('parent source changed')
    manifest = dict(mode='SHADOW_NO_ORDERS_LATENCY', source=source, parent=str(args.parent.resolve()),
                    started_ms=shadow.now_ms(), end_S=parent['end_S'], poll_ms=5, max_notification_lag_ms=100,
                    policy='Use the committed decision unchanged; request a new quote without an intentional wait.')
    mp = out/'watch_manifest.json'
    if mp.exists():
        old = json.loads(mp.read_text())
        if any(old[k] != manifest[k] for k in ('source', 'parent', 'end_S')):
            raise ValueError('observer experiment changed')
        manifest = old
    else:
        shadow.base.save(mp, manifest)
    output = out/'quotes.jsonl'
    observed = [json.loads(x) for x in output.open()] if output.exists() else []
    seen = {(r['S'], r['age']) for r in observed if r['kind'] in ('fast_quote', 'gap')}

    def emit(kind, **kw):
        r = dict(kind=kind, recorded_ms=shadow.now_ms(), **kw)
        with output.open('a') as stream:
            stream.write(json.dumps(r, separators=(',', ':'), allow_nan=False)+'\n')
        observed.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != 'books'}), flush=True)

    with (args.parent/'shadow.jsonl').open() as stream, ThreadPoolExecutor(max_workers=2) as pool:
        original = [json.loads(x) for x in stream]
        markets = {r['S']: r['market'] for r in original if r['kind'] == 'market'}
        emit('start', **manifest)
        last_health = 0.
        while time.time() < manifest['end_S']+30 and not (out/'STOP_SHADOW').exists():
            pos = stream.tell()
            line = stream.readline()
            if line and not line.endswith('\n'):
                stream.seek(pos)
                line = ''
            if line:
                r = json.loads(line)
                original.append(r)
                if r['kind'] == 'market':
                    markets[r['S']] = r['market']
                if r['kind'] == 'decision' and (r['S'], r['age']) not in seen:
                    seen.add((r['S'], r['age']))
                    try:
                        lag = shadow.now_ms()-r['decision_ms']
                        if not 0 <= lag <= 100:
                            raise ValueError('late decision notification')
                        m = markets[r['S']]
                        pair, requested, received = shadow.books(pool, json.loads(m['clobTokenIds']))
                        if requested < r['decision_ms'] or received-r['decision_ms'] > 3000:
                            raise ValueError('quote outside causal delay bounds')
                        emit('fast_quote', S=r['S'], age=r['age'], rebound=r['rebound'], favorite=r['favorite'],
                             decision_ms=r['decision_ms'], request_ms=requested, received_ms=received,
                             notification_ms=lag, http_ms=received-requested, books=pair,
                             costs=[shadow.base.ask_cost(b, m) for b in pair])
                    except shadow.ERRORS as ex:
                        emit('gap', S=r['S'], age=r['age'], reason=str(ex)[:180], error=type(ex).__name__)
            elif time.time()-last_health >= 60:
                last_health = time.time()
                summary = compare([r for r in original if r.get('recorded_ms', 0) >= manifest['started_ms']], observed)
                shadow.base.save(out/'comparison.json', summary)
                emit('health', paired=summary['paired'], end_S=manifest['end_S'])
            else:
                time.sleep(.005)
        emit('stop', reason='stop_file' if (out/'STOP_SHADOW').exists() else 'duration')
        shadow.base.save(out/'comparison.json', compare(original, observed))


def check():
    a = dict(kind='fast_quote', S=0, age=280, rebound=0, favorite=1, costs=[[1., .056], [4., .056]],
             decision_ms=1000, request_ms=1005, received_ms=1030)
    b = dict(kind='execution', S=0, age=280, rebound=0, favorite=1, costs=[[1.1, .06006], [3.9, .06006]], delay_ms=280)
    result = compare([b], [a])
    assert result['paired'] == 1 and result['rows'][0]['fast_ms'] == 30
    for winner in (0, 1):
        for rule in ('rebound', 'favorite'):
            assert abs(shadow.settle(a, winner)[rule]-shadow.settle(b, winner)[rule]-result['rows'][0]['gain'][rule]) < 1e-9
    a['rebound'] = b['rebound'] = None
    assert compare([b], [a])['rows'][0]['gain']['rebound'] == 0
    assert compare([], [a])['fast_only'] == 1
    assert compare([b], [])['delayed_only'] == 1
    print('Paired fees/PnL, either outcome, zero signal and missing quote checks passed')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['watch', 'check'])
    p.add_argument('--parent', type=Path)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if args.action == 'check':
        check()
    else:
        if args.parent is None or args.out is None or not (args.parent/'shadow.jsonl').is_file():
            p.error('existing parent shadow and separate output are required')
        watch(args)
