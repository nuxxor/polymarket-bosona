"""Freeze the predeclared historical cohorts without deduplicating actual fills."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

OUT = Path(__file__).resolve().parent
DATA = OUT.parent
SOURCE = DATA/'bosona_gec_20260921'


def read(path):
    return json.loads(path.read_text())


def main():
    windows = read(SOURCE/'windows.json')
    days = defaultdict(list)
    for row in windows:
        days[datetime.fromtimestamp(row['S'], timezone.utc).strftime('%Y-%m-%d')].append(row['S'])
    representative = {s for ss in days.values() for s in sorted(
        ss, key=lambda x: sha256(f'R1-20260921:{x}'.encode()).hexdigest())[:8]}
    fills = read(SOURCE/'fill_ledger.json')
    late = {r['S'] for r in fills if r['opening_kind'] == 'add' and 280 <= r['age'] < 300}
    raw, sources, previous = [], {}, None
    for path in sorted((SOURCE/'activity').glob('*.json')):
        chunk = read(path)
        assert chunk['complete'] and (previous is None or previous+1 == chunk['start'])
        assert all(chunk['start'] <= r['timestamp'] <= chunk['end'] for r in chunk['rows'])
        raw.extend(chunk['rows'])
        previous = chunk['end']
        sources[str(path.relative_to(DATA))] = sha256(path.read_bytes()).hexdigest()
    universe = {w['S'] for w in windows}
    raw = [r for r in raw if r.get('slug', '').startswith('btc-updown-5m-')
           and int(r['slug'].rsplit('-', 1)[1]) in universe]
    fields = ('transactionHash', 'timestamp', 'type', 'asset', 'outcomeIndex',
              'side', 'size', 'price', 'usdcSize')
    counts = Counter(tuple(str(r.get(k, '')) for k in fields) for r in raw if r['type'] == 'TRADE')
    duplicate = {int(r['slug'].rsplit('-', 1)[1]) for r in raw if r['type'] == 'TRADE'
                 and counts[tuple(str(r.get(k, '')) for k in fields)] > 1}
    diagnostic = duplicate | {1789402200, 1789676700, 1789582500,
                              1789852200, 1789852800, 1789853400, 1789853700}
    selected = representative | late | diagnostic
    rows = [r for r in raw if int(r['slug'].rsplit('-', 1)[1]) in selected]
    markets = {str(s): read(SOURCE/'markets'/f'btc-updown-5m-{s}.json') for s in sorted(selected)}
    late_rows = [r for r in fills if r['S'] in late and r['opening_kind'] == 'add' and 280 <= r['age'] < 300]
    features = read(DATA/'bosona_derin_20260921/features.json')
    contexts = [r for r in features if r['S'] in selected]
    assert len(representative) == 64 and len(late) == 66 and len(selected) == 137
    assert sum(r['type'] == 'TRADE' for r in rows) == 2066 and len(late_rows) == 271
    payloads = {'activity.json': rows, 'markets.json': markets,
                'late20_labels.json': late_rows, 'contexts.json': contexts}
    manifest = dict(mode='ACTOR_CONDITIONAL_MECHANISM_RESEARCH_NO_ORDERS',
        calendar_start=1789257600, calendar_end=1789943400, calendar_slots=2286,
        observed_markets=len(universe), selection_seed='R1-20260921',
        cohorts=dict(representative=sorted(representative), late20=sorted(late), diagnostic=sorted(diagnostic)),
        representative_per_day=8, selected=sorted(selected), raw_chunk_sha256=sources,
        first_reduction='First reducing public-second group; one parent and unambiguous reduction allocation only. No later actor actions replayed.',
        ordering='Public seconds do not order their component fills. Exchange event clocks reported separately.',
        gates=dict(count_reconciliation=.95, share_reconciliation=.95),
        inference='Historical, previously inspected. Representative cohort sampled only from observed markets; not 2286 complete calendar slots or clean OOS.',
        input_sha256={name: sha256((json.dumps(value, separators=(',', ':'))+'\n').encode()).hexdigest()
                      for name, value in payloads.items()})
    payloads['manifest.json'] = manifest
    for name, value in payloads.items():
        text = json.dumps(value, separators=(',', ':'))+'\n'
        path = OUT/name
        if path.exists():
            assert path.read_text() == text, f'frozen preparation changed: {name}'
        else:
            path.write_text(text)
    print('Frozen: 64 representative + 66 late-add + 14 diagnostics; union 137, 2066 BUY')


if __name__ == '__main__':
    main()
