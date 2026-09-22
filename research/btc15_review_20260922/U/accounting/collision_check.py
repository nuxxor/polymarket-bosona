#!/usr/bin/env python3
"""Condition-aware activity identity; finite cached public checks for lost MERGEs."""
import argparse
from collections import Counter, defaultdict
import difflib
import json
import time
import urllib.parse
import urllib.request
import sys

sys.dont_write_bytecode = True
import audit as a  # noqa: E402


def key(x):
    return (x.get('conditionId', ''),) + a.key(x)


def run(fetch=False):
    counts, samples, domains = Counter(), {}, defaultdict(set)
    for path in sorted((a.R/'raw/activity').glob('*.json')):
        rows = [x for x in a.read(path)['rows'] if a.ref.LOOKBACK <= x['timestamp'] < a.ref.END]
        counts |= Counter(map(key, rows))
        samples.update((key(x), x) for x in rows)
        for x in rows:
            domains[a.key(x)].add(x['conditionId'])
    corrections = {p.stem: a.read(p) for p in sorted((a.R/'raw/activity_checks').glob('*.json'))}
    fresh = [x for part in corrections.values() for x in part if x['timestamp'] < a.ref.END]
    original = [x for x in a.read(a.R/'raw/activity.json') if x.get('slug') not in corrections] + fresh
    improved = [samples[k] for k, n in counts.items() for _ in range(n) if samples[k].get('slug') not in corrections] + fresh
    before, after = Counter(map(key, original)), Counter(map(key, improved))
    plus, minus = after-before, before-after
    sample_all = {key(x): x for x in original+improved}
    cohort = {x['slug'] for x in a.read(a.R/'results/windows.json')}
    added = [dict(sample_all[k], extra=n) for k, n in plus.items() if sample_all[k]['slug'] in cohort]
    removed = [dict(sample_all[k], extra=n) for k, n in minus.items() if sample_all[k]['slug'] in cohort]
    merges = [x for x in added if x['type'] == 'MERGE']
    raw = a.HERE/'raw_collision_checks'
    raw.mkdir(exist_ok=True)
    checks = []
    for x in merges:
        path = raw/(x['slug']+'.json')
        if not path.exists() and fetch:
            query = dict(user=a.ref.base.WALLET, market=x['conditionId'], start=1, end=a.ref.END-1,
                         limit=500, offset=0, sortBy='TIMESTAMP', sortDirection='ASC')
            url = 'https://data-api.polymarket.com/activity?'+urllib.parse.urlencode(query)
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
            assert len(data) < 500 and all(y['conditionId'] == x['conditionId'] for y in data)
            path.write_text(json.dumps(dict(url=url, received_ms=round(time.time()*1000), data=data), ensure_ascii=False)+'\n')
            time.sleep(.7)
        if not path.exists():
            checks.append(dict(slug=x['slug'], verified=False))
            continue
        data = a.read(path)['data']
        n = Counter(map(key, data))[key(x)]
        assert n == after[key(x)]
        checks.append(dict(slug=x['slug'], verified=True, restored_matches=n, shares=x['size'],
                           tx=x['transactionHash'], condition=x['conditionId']))
    report = dict(collision_keys=len([v for v in domains.values() if len(v) > 1]),
        collision_types=dict(Counter(k[2] for k, v in domains.items() if len(v) > 1)),
        added=added, removed=removed, restored_merge_cash=sum(a.D(str(x['usdcSize']))*x['extra'] for x in merges),
        fresh_checks=checks, restored_btc15_merges=sum(x['slug'].startswith('btc-updown-15m-') for x in merges))
    a.save('collision_result.json', report)
    a.save('collision_inputs.json', a.INPUTS)
    source = (a.R/'src/bosona_gec_arastirma.py').read_text()
    fixed = source.replace("('transactionHash', 'timestamp', 'type',", "('conditionId', 'transactionHash', 'timestamp', 'type',")
    (a.HERE/'condition_identity.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True), fixed.splitlines(True),
        fromfile='a/src/bosona_gec_arastirma.py', tofile='b/src/bosona_gec_arastirma.py')))
    # Synthetic regression: equal nontrade amounts across contracts must remain distinct.
    x = dict(type='MERGE', asset='', transactionHash='a', timestamp=1, size=50, usdcSize=50, conditionId='one')
    y = dict(x, conditionId='two')
    assert a.key(x) == a.key(y) and key(x) != key(y)
    ns = dict(__name__='condition_patch', __file__=str(a.R/'src/bosona_gec_arastirma.py'))
    exec(compile(fixed, ns['__file__'], 'exec'), ns)
    assert ns['activity_key'](x) != ns['activity_key'](y)
    print(json.dumps({k: v for k, v in report.items() if k not in ('added', 'removed', 'fresh_checks')}, default=str))
    print('cohort added', len(added), 'removed', len(removed), 'public checks', sum(x['verified'] for x in checks))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    run(parser.parse_args().fetch)
