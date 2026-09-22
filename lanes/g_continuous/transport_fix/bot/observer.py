"""Two staggered, compressed M7 recorders; no financial actions."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

SOURCE = Path(__file__).resolve().parent
HERE = SOURCE/'measurement'


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def healthy(root, require_both=False):
    """Availability only. Rejected messages remain incomplete measurement evidence."""
    root = Path(root)
    try:
        free = shutil.disk_usage(root).free
    except OSError:
        return False
    if free < 2*1024**3:
        return False
    valid = 0
    for lane in ('A', 'B'):
        try:
            row = json.loads((root/f'measurement/run1/{lane}.health.json').read_text())
            args = (Path('/proc')/str(row['pid'])/'cmdline').read_bytes().split(b'\0')
            if str(root/'observer.py').encode() not in args or lane.encode() not in args:
                continue
            now = time.time_ns()
            if (row['status'] == 'active' and row['queue_overflow'] == 0 and
                    0 <= now-row['at_ns'] <= 3_000_000_000 and
                    all(0 <= now-row['pongs'][ch] <= 30_000_000_000 for ch in ('market', 'user'))):
                valid += 1
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return valid == 2 if require_both else valid >= 1


def start_for_pilot(root):
    root = Path(root)
    with (root/'measurement/console.log').open('x') as log:
        child = subprocess.Popen([sys.executable, str(root/'observer.py'), '--owner', str(os.getpid())],
                                 stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
    deadline = time.monotonic()+20
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise ValueError('G observer startup failed')
        if healthy(root, require_both=True):
            return
        time.sleep(.1)
    raise ValueError('G observer channels not ready; no budget activated')


def archive_finished(root, stamp):
    root = Path(root)
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            args = (proc/'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue
        if str(root/'observer.py').encode() in args:
            raise ValueError('Previous recorder still running')
    for name in ('run1', 'console.log', 'STOP_OBSERVER'):
        path = root/'measurement'/name
        if path.exists():
            path.rename(path.with_name(name+'.finished_'+str(stamp)))


def worker(lane, protocol):
    import stream_iz as stream
    run = HERE/'run1'
    auth, count = stream.credentials(Path('/home/taygun/Masaüstü/polymarket/.env.live'))
    assert count == 0  # Before the operator activates the financial engine.
    index = 0
    while not (HERE/'STOP_OBSERVER').exists():
        seconds = protocol['chunk_seconds']+(protocol['first_b_extra_seconds'] if lane == 'B' and index == 0 else 0)
        markets = stream.roster(seconds+30)
        output = run/lane/f'{index:06d}'
        _, summary = stream.capture(output, markets, auth, seconds, count, threading.Event(),
                                    compressed=True, health_path=run/f'{lane}.health.json',
                                    stop_path=HERE/'STOP_OBSERVER')
        assert not summary['writer_failed'] and not summary['reader_alive']
        assert not any(c['queue_overflow'] for c in summary['stats'].values())
        index += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lane', nargs='?', choices=('A', 'B'))
    parser.add_argument('--owner', type=int, default=0)
    args = parser.parse_args()
    os.umask(0o077)
    protocol = json.loads((HERE/'protocol.json').read_text())
    if args.lane:
        worker(args.lane, protocol)
        return
    manifest = json.loads((SOURCE/'G_RELEASE.json').read_text())
    assert sha256((SOURCE/'stream_iz.py').read_bytes()).hexdigest() == manifest['stream_iz.py']
    assert not (HERE/'STOP_OBSERVER').exists()
    run = HERE/'run1'
    run.mkdir(exist_ok=False)
    write(run/'manifest.json', dict(created_ns=time.time_ns(), owner_pid=args.owner, sources=manifest))
    workers = []
    started = time.monotonic()
    try:
        for lane in ('A', 'B'):
            with (run/f'{lane}.console.log').open('x') as log:
                workers.append(subprocess.Popen([sys.executable, str(Path(__file__)), lane], stdout=log, stderr=log))
        while all(p.poll() is None for p in workers):
            if (HERE/'STOP_OBSERVER').exists():
                break
            if args.owner and not (Path('/proc')/str(args.owner)).exists():
                break
            if protocol['total_seconds'] is not None and time.monotonic()-started >= protocol['total_seconds']:
                break
            if shutil.disk_usage(HERE).free < protocol['min_free_bytes']:
                break
            time.sleep(.5)
    finally:
        (HERE/'STOP_OBSERVER').touch()
        codes = [p.wait(timeout=25) for p in workers]
        write(run/'done.json', dict(ended_ns=time.time_ns(), exit_codes=codes))
    assert codes == [0, 0]


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('G_OBSERVER_FAILED: '+type(error).__name__, flush=True)
        raise SystemExit(1) from None
