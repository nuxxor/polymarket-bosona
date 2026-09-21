"""Verify archived graceful shadow shutdown; never changes remote processes."""
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT/'bosona-shadow-stop-20260921'
before = json.loads((ARCHIVE/'before.json').read_text())
after = json.loads((ARCHIVE/'after_corrected.json').read_text())
assert len(before['processes']) == len(after['results']) == 8
for start, stop in zip(before['processes'], after['results']):
    assert start['pid'] == stop['pid'] and stop['stopped']
    raw = (ARCHIVE/str(start['pid'])/Path(start['log']).name).read_bytes()
    assert raw.endswith(b'\n')
    assert sha256(raw).hexdigest() == stop['sha256']
    assert sha256(raw[:start['bytes_before']]).hexdigest() == start['log_sha256_prefix_before']
    rows = [json.loads(line) for line in raw.splitlines()]
    assert rows[-1] == stop['last']
    assert rows[-1]['kind'] == 'stop' and rows[-1]['reason'] == 'stop_file'
    pending = set(rows[-1].get('pending', []))
    filled = set()
    for row in rows:
        s = row.get('S')
        if s not in pending:
            continue
        if row['kind'] == 'execution' and row.get('fills'):
            filled.add(s)
        if row['kind'] == 'execution' and 'costs' in row and any(
                row.get(rule) is not None and row['costs'][row[rule]] is not None
                for rule in ('rebound', 'favorite')):
            filled.add(s)
        if row['kind'] == 'decision' and any(row.get('selected', {}).values()):
            filled.add(s)
    assert sorted(filled) == stop['filled_unresolved']
print('PASS: eight graceful stop records, preserved log prefixes, archive hashes and pending paper positions')
