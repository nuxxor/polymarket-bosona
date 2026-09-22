"""Inventory older public archives; their provenance is not assumed complete."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def main():
    result = []
    for name in ('activity.jsonl', 'bosona_activity_7g.json', 'bosona_ledger_pen.csv'):
        path = ROOT / 'data/bosona' / name
        if path.suffix == '.csv':
            with path.open() as stream:
                rows = list(csv.DictReader(stream))
            starts = [int(r['S']) for r in rows]
            detail = dict(derived_rows=len(rows), unique_starts=len(set(starts)),
                          note='Derived ledger; multiplicity and primary provenance not re-audited.')
        else:
            rows = ([json.loads(line) for line in path.read_text().splitlines() if line]
                    if path.suffix == '.jsonl' else json.loads(path.read_text()))
            rows = [r for r in rows if r.get('slug', '').startswith('btc-updown-5m-')]
            starts = [int(r['slug'].rsplit('-', 1)[1]) for r in rows]
            detail = dict(raw_rows=len(rows), types=dict(Counter(r['type'] for r in rows)),
                          buys=sum(r.get('side') == 'BUY' and r['type'] == 'TRADE' for r in rows),
                          unique_starts=len(set(starts)),
                          latest_activity_utc=utc(max(r['timestamp'] for r in rows)),
                          note='Additional public archive; overlaps primary cohort, not added to its totals.')
        assert starts
        result.append(dict(file=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                           sha256=sha256(path.read_bytes()).hexdigest(),
                           first_start_utc=utc(min(starts)), last_start_utc=utc(max(starts)), **detail))
    (OUT / 'older_archive_inventory.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
