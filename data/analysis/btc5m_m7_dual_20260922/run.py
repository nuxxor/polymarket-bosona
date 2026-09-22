"""Two independent, finite M7 recorders. No order submission or cancellation."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

SOURCE = Path('/home/ubuntu/polymarket-bosona-m7-v3')
HERE = Path(__file__).resolve().parent
PIN = '4ae34533bf793bb5cf45f2f7af7d697d383775dd03841b21c97e81fef1a78dff'


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
