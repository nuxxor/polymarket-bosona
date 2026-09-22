"""Read-only raw-prefix and causal-regression checks for the frozen context output."""
from collections import Counter
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import reconstruct as r


def raw_check(row):
    s = row['S']
    market = r.deep.markets()[s]
    tokens = json.loads(market['clobTokenIds'])
    condition = market['conditionId'].encode()
    path = r.deep.TAPE / datetime.fromtimestamp(s, timezone.utc).strftime('tape_%Y%m%d_%H.jsonl.gz')
    times = sorted(row[f'lag{lag}']['book']['snapshot_ms'] for lag in (5, 10))
    books = {t: dict(BUY={}, SELL={}, ready=False, rcv=0, obs=0,
                     rate=float(market.get('feeSchedule', {}).get('rate', 0))) for t in tokens}
    output, idx, scanned, digest, stats = {}, 0, 0, sha256(), Counter()
    with gzip.open(path, 'rb') as stream:
        for line in stream:
            scanned += len(line)
            digest.update(line)
            if condition not in line:
                continue
            d = json.loads(line)
            p, kind, rcv = d.get('p') or {}, d.get('k'), d.get('rcv')
            if p.get('market') != market['conditionId'] or rcv is None:
                continue
            while idx < len(times) and times[idx] < rcv:
                output[times[idx]] = [r.deep.book_view(b, times[idx]) for b in books.values()]
                idx += 1
            if idx == len(times):
                break
            obs = int(p.get('timestamp', d.get('src') or rcv))
            if kind == 'pm:book' and p.get('asset_id') in books:
                b = books[p['asset_id']]
                if obs < b['obs'] or rcv < b['rcv']:
                    continue
                for side, key in [('BUY', 'bids'), ('SELL', 'asks')]:
                    b[side] = {float(x['price']): float(x['size']) for x in p.get(key, []) if float(x['size']) > 0}
                b.update(rcv=rcv, obs=obs, ready=True)
            elif kind == 'pm:price_change':
                for c in p.get('price_changes', []):
                    b = books.get(c.get('asset_id'))
                    if b is None or not b['ready'] or obs < b['obs'] or rcv < b['rcv']:
                        continue
                    px, q = float(c['price']), float(c['size'])
                    if q > 0:
                        b[c['side']][px] = q
                    else:
                        b[c['side']].pop(px, None)
                    b.update(rcv=rcv, obs=obs)
                    if b['BUY'] and b['SELL'] and c.get('best_bid') and c.get('best_ask'):
                        if abs(max(b['BUY'])-float(c['best_bid'])) > 1e-8 or abs(min(b['SELL'])-float(c['best_ask'])) > 1e-8:
                            b['ready'] = False
                            stats['l1_mismatch_invalidated'] += 1
            stats['matched_market_records'] += 1
    assert len(output) == 2
    for lag in (5, 10):
        cached = row[f'lag{lag}']['book']
        raw = output[cached['snapshot_ms']]
        assert 0 <= (row['ts']-lag)*1000-cached['snapshot_ms'] <= 1250
        assert all(raw)
        for a, b in zip(raw, cached['books']):
            expected = r.cached_book(a)
            assert expected == b, (s, lag, expected, b)
    return dict(S=s, age=row['age'], raw_path=str(path), compared_snapshots=2,
                decompressed_prefix_bytes=scanned, prefix_sha256=digest.hexdigest(), stats=dict(stats))


def main():
    events = r.read(r.OUT/'events.json')
    r.checks(events)
    assert len(events) == 390 and sum(x['kind']=='control' for x in events) == 128
    report = r.read(r.DATA/'btc5m_parent_research_20260921/report.json')
    fill_map = {}
    for fill in report['fills']:
        fill_map.setdefault(fill['S'], []).append(fill)
    checks = Counter()
    for row in events:
        for lag in (5, 10):
            c = row[f'lag{lag}']
            prior = [f for f in fill_map[row['S']] if f['ts']*1000 <= c['now_ms']]
            expected = sum((1 if f['outcome']==0 else -1)*f['qty'] for f in prior)
            assert c['net_at_cutoff_units'] == expected
            assert c['held_side'] == (0 if expected > 0 else 1 if expected < 0 else None)
            checks['inventory_cutoffs'] += 1
            if row['kind']=='control':
                ex = c['execution250']
                assert ex['execution_only_not_signal'] and ex['target_ms']==c['now_ms']+250
                if ex['book']:
                    assert ex['book']['snapshot_ms']==ex['target_ms']
                    for b in ex['book']['books']:
                        if b:
                            assert b['received_ms'] <= ex['target_ms'] and b['observed_ms'] <= ex['target_ms']
                checks['execution_labels'] += 1
    # Future outcome is not an input to context generation.
    row = dict(events[0], outcome_label={'winner': 0, 'market_pnl': 9999999})
    market = r.deep.markets()[row['S']]
    args = (5, {}, {'spot': ([], []), 'twap60': ([], [])}, {}, market, {}, fill_map[row['S']])
    a = r.context(row, *args)
    row['outcome_label'] = {'winner': 1, 'market_pnl': -9999999}
    assert r.context(row, *args) == a
    checks['outcome_invariance'] += 1
    # Future quotes cannot leak into current signal or history.
    snaps = {1: ([1001], {1001: dict(source='future', books=[None, None])})}
    assert r.at_book(snaps, 1, 1000) is None
    assert r.price_at({'spot': ([1001], [(999, 1.)])}, 'spot', 1000) is None
    checks['future_rejection'] += 2
    raw = [raw_check(next(x for x in events if x['S']==s and x['role']=='taker' and x['kind']=='reduce'))
           for s in (1789449300, 1789546200)]
    # Running the check never rewrites source or frozen derived inputs.
    source = r.read(r.OUT/'sources.json')
    assert source['code_sha256'] == sha256((r.OUT/'reconstruct.py').read_bytes()).hexdigest()
    for path, expected in source['hashes'].items():
        assert sha256(Path(path).read_bytes()).hexdigest() == expected
    checks['source_hashes'] = len(source['hashes'])+1
    r.save('verification.json', dict(status='PASS', checks=dict(checks), raw_prefix_checks=raw,
        output_sha256=sha256((r.OUT/'events.json').read_bytes()).hexdigest(),
        code_sha256=sha256(Path(__file__).read_bytes()).hexdigest()))
    print(json.dumps(dict(status='PASS', checks=dict(checks), raw_prefix_checks=raw), indent=2))


if __name__ == '__main__':
    main()
