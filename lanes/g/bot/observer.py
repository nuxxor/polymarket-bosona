"""Two independent, finite M7 recorders. No order submission or cancellation."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

SOURCE = Path(__file__).resolve().parent
HERE = Path(__file__).resolve().parent/'measurement'
PIN = '4ae34533bf793bb5cf45f2f7af7d697d383775dd03841b21c97e81fef1a78dff'


def healthy(root):
    """Availability guard only; it does not assert event completeness or zero gaps."""
    run = Path(root)/'measurement/run1'
    for lane in ('A', 'B'):
        try:
            ready = json.loads((run/f'{lane}_ready.json').read_text())
            args = (Path('/proc')/str(ready['pid'])/'cmdline').read_bytes().split(b'\0')
            if str(Path(root)/'observer.py').encode() not in args or lane.encode() not in args:
                continue
            paths = list((run/lane).glob('*.jsonl'))
            if len(paths) == 1 and 0 <= time.time()-paths[0].stat().st_mtime <= 3:
                return True
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return False


def start_for_pilot(root):
    root = Path(root)
    with (root/'measurement/console.log').open('x') as log:
        child = subprocess.Popen([sys.executable, str(root/'observer.py')], stdout=log, stderr=log,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
    deadline = time.monotonic()+20
    while time.monotonic() < deadline:
        assert child.poll() is None, 'G observer startup failed'
        ready = []
        for lane in ('A', 'B'):
            found = set()
            for path in (root/'measurement/run1'/lane).glob('*.jsonl'):
                with path.open('rb') as file:
                    for line in file:
                        if not line.endswith(b'\n'):
                            break
                        row = json.loads(line)
                        if row['event'] == 'pong':
                            found.add(row['channel'])
                        if found == {'market', 'user'}:
                            break
            ready.append(found == {'market', 'user'})
        if all(ready) and healthy(root):
            return
        time.sleep(.1)
    raise ValueError('G observer channels not ready; no budget activated')


def write(path, value):
    assert not path.exists()
    temporary = path.with_suffix('.tmp')
    with temporary.open('x') as file:
        json.dump(value, file, indent=2)
        file.write('\n')
    temporary.rename(path)


def main():
    os.umask(0o077)
    assert sha256((SOURCE/'stream_iz.py').read_bytes()).hexdigest() == PIN
    sys.path.insert(0, str(SOURCE))
    import stream_iz as stream
    run = HERE/'run1'
    protocol = json.loads((HERE/'protocol.json').read_text())
    seconds = protocol['seconds_per_recorder']
    if len(sys.argv) == 2:
        lane = sys.argv[1]
        assert lane in ('A', 'B')
        roster = json.loads((run/'roster.json').read_text())
        auth, count = stream.credentials(Path('/home/taygun/Masaüstü/polymarket/.env.live'))
        assert count == 0
        write(run/f'{lane}_ready.json', dict(pid=os.getpid(), at=stream.saat(), open_orders=count))
        limit = time.monotonic()+30
        while not (run/'start.json').exists():
            assert time.monotonic() < limit
            time.sleep(.05)
        start = json.loads((run/'start.json').read_text())['mono_ns']
        while time.monotonic_ns() < start:
            time.sleep(.01)
        _, summary = stream.capture(run/lane, roster, auth, seconds, count, threading.Event())
        write(run/f'{lane}_done.json', summary)
        return
    run.mkdir(exist_ok=False)
    write(run/'roster.json', stream.roster(seconds+30))
    write(run/'manifest.json', dict(created=stream.saat(), sources={
        str(p):sha256(p.read_bytes()).hexdigest() for p in
        (Path(__file__), HERE/'protocol.json', SOURCE/'stream_iz.py', SOURCE/'emir_iz.py')}))
    workers = []
    for lane in ('A', 'B'):
        with (run/f'{lane}.console.log').open('x') as log:
            workers.append(subprocess.Popen([sys.executable, str(Path(__file__)), lane], stdout=log, stderr=log))
    limit = time.monotonic()+25
    while not all((run/f'{lane}_ready.json').exists() for lane in ('A', 'B')):
        assert time.monotonic() < limit and all(p.poll() is None for p in workers)
        time.sleep(.1)
    write(run/'start.json', dict(mono_ns=time.monotonic_ns()+2_000_000_000, at=stream.saat()))
    codes = [p.wait(timeout=seconds+60) for p in workers]
    write(run/'done.json', dict(ended=stream.saat(), exit_codes=codes))
    assert codes == [0, 0]


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('M7_DUAL_FAILED: '+type(error).__name__, flush=True)
        raise SystemExit(1) from None
