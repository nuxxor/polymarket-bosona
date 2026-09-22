"""Run through SSH stdin: read existing logs only, emit a bounded JSONL snapshot."""
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path('/home/ubuntu/polymarket-bosona-g-continuous/bot')
START, END = 1790095500, 1790097300  # First six complete G4 windows, UTC.


def emit(kind, row, **meta):
    print(json.dumps(dict(kind=kind, row=row, **meta), separators=(',', ':')))


def main():
    os.nice(10)
    state = json.loads((ROOT/'STATE_g.json').read_text())
    windows = {k: v for k, v in state['pen'].items() if START <= int(k.split('|')[1]) < END}
    hashes = {n: sha256((ROOT/n).read_bytes()).hexdigest()
              for n in ('ab.py', 'g_policy.py', 'BUDGET_G.json', 'RUN_G.json')}
    emit('manifest', dict(start=START, end=END, captured_ns=time.time_ns(), hashes=hashes,
                         budget=json.loads((ROOT/'BUDGET_G.json').read_text()),
                         assigned=list(range(START, END, 300))))
    emit('state', dict(st=state['st'], windows=windows))
    for name, kind in (('LOG_g.jsonl', 'bot'), ('LOG_g_emir_iz.jsonl', 'sdk')):
        path = ROOT/name
        raw = path.read_bytes()
        emit('source', dict(path=str(path), bytes=len(raw), sha256=sha256(raw).hexdigest()))
        for line in raw.splitlines():
            if not line.endswith(b'}'):
                continue
            r = json.loads(line)
            ms = r.get('utc_ns', 0)/1e6 or r.get('utc_ms', 0)
            if START*1000-180000 <= ms <= END*1000+60000:
                emit(kind, r)
    # Existing recorder payloads are allowlisted by stream_iz; auth is never stored.
    # Read only fills/LTP and transport metadata; no expensive book reconstruction.
    for lane in ('A', 'B'):
        for path in sorted((ROOT/'measurement/run1'/lane).glob('*/*.jsonl.gz')):
            length = path.stat().st_size
            emitted = 0
            truncated = False
            try:
                with gzip.open(path, 'rt') as stream:
                    for i, line in enumerate(stream):
                        if i % 20000 == 0:
                            time.sleep(.01)
                        if not ('"channel":"user"' in line or '"channel": "user"' in line
                                or '"event_type":"last_trade_price"' in line
                                or '"event_type": "last_trade_price"' in line
                                or '"session_start"' in line):
                            continue
                        r = json.loads(line)
                        ns = r.get('received', r.get('started', {})).get('utc_ns', 0)
                        if ns > (END+60)*10**9:
                            break
                        if ns >= (START-180)*10**9:
                            emit('stream', r, lane=lane, source=str(path.relative_to(ROOT)))
                            emitted += 1
            except (EOFError, json.JSONDecodeError):
                truncated = True  # An unfinished live gzip tail is not a complete file.
            emit('stream_source', dict(path=str(path), initial_bytes=length,
                                      final_bytes=path.stat().st_size, emitted=emitted,
                                      incomplete_tail=truncated))
    emit('end', dict(finished_ns=time.time_ns()))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
