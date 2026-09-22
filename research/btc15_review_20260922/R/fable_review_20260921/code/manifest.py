#!/usr/bin/env python3
"""SHA256 manifest of this review's code/results/raw and the frozen inputs it depends on."""
import hashlib
import json
import time
from pathlib import Path

MY = Path(__file__).resolve().parents[1]
R = MY.parent
INPUTS = [R/'results/fills.json', R/'results/windows.json', R/'results/universe.json', R/'raw/btc15_context.json',
          R/'candidate.py', R/'protocol.json', R/'btc15_followup/status_20260921_1800/raw/book_validation_prefix.json.gz',
          R/'btc15_followup/record_books.py']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    out = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), files={}, inputs={})
    for sub in ('code', 'results', 'raw'):
        for p in sorted((MY/sub).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                out['files'][str(p.relative_to(MY))] = dict(bytes=p.stat().st_size, sha256=sha(p))
    for p in ('RAPOR_FABLE.md', 'OZET.md', 'plan.md', 'AGENT_BRIEF.md'):
        if (MY/p).exists():
            out['files'][p] = dict(bytes=(MY/p).stat().st_size, sha256=sha(MY/p))
    for p in INPUTS:
        out['inputs'][str(p)] = sha(p) if p.exists() else None
    (MY/'results/manifest.json').write_text(json.dumps(out, indent=1))
    print('manifest', len(out['files']), 'files;', 'inputs', len(out['inputs']))


if __name__ == '__main__':
    main()
