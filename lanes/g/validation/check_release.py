"""Offline release/activation checks. SSH is replaced; no network or live order."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT/'bot'
sys.path.insert(0, str(BOT))
import g_guard
import observer
import pilot


def rejected(call):
    try:
        call()
    except (ValueError, OSError):
        return
    raise AssertionError('Invalid activation was accepted')


def main():
    manifest = json.loads((BOT/'G_RELEASE.json').read_text())
    assert g_guard.REQUIRED <= manifest.keys()
    assert all(hashlib.sha256((BOT/n).read_bytes()).hexdigest() == h for n, h in manifest.items())
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name in (*manifest, 'G_RELEASE.json'):
            (root/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(BOT/name, root/name)
        budget = {'end_ms': time.time()*1000+60000}
        (root/'RUN_G.json').write_text(json.dumps({'budget': budget}))
        g_guard.verify(root, budget)
        assert pilot.verify(root)['loss_limit'] == 10
        rejected(lambda: g_guard.verify(root, None))
        rejected(lambda: g_guard.verify(root, {'end_ms': 1}))
        rejected(lambda: g_guard.verify(root, {**budget, 'extra': True}))
        (root/'G_RELEASE.json').write_text('{}')
        rejected(lambda: g_guard.verify(root, budget))
        rejected(lambda: pilot.verify(root))
        (root/'G_RELEASE.json').write_text(json.dumps(manifest))
        (root/'g.py').write_text('changed source')
        rejected(lambda: g_guard.verify(root, budget))
        rejected(lambda: pilot.verify(root))
        assert not observer.healthy(root)
        (root/'measurement/run1').mkdir()
        for lane in ('A', 'B'):
            (root/f'measurement/run1/{lane}_ready.json').write_text('null')
        assert not observer.healthy(root)
    launcher = ROOT.parents[1]/'londra_g_baslat.sh'
    subprocess.run(['bash', '-n', str(launcher)], check=True)
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        fake = folder/'ssh'
        fake.write_text('#!'+sys.executable+'\nimport json,os,sys\nopen(os.environ["G_SSH_CAPTURE"],"w").write(json.dumps(sys.argv[1:]))\n')
        fake.chmod(0o700)
        capture = folder/'captured.json'
        result = subprocess.run(['bash', str(launcher)], env={**os.environ, 'PATH':td+':'+os.environ['PATH'],
                                'G_SSH_CAPTURE':str(capture)}, capture_output=True, text=True, check=True)
        args = json.loads(capture.read_text())
        assert 'StrictHostKeyChecking=yes' in args and 'BatchMode=yes' in args
        assert '/home/ubuntu/polymarket-bosona-g-v2/bot/pilot.py --live' in args[-1]
        assert 'tmux new-session -d -s bosona-g' in args[-1]
        assert '30 dakika / 5 pay / $10' in result.stdout
    result = dict(passed=True, source_files=len(manifest), live_activated=False,
                  checks=['source manifest', 'required files', 'budget expiry/mismatch', 'source tamper',
                          'missing/corrupt observer metadata', 'launcher syntax', 'launcher fake SSH'])
    print(json.dumps(result))


if __name__ == '__main__':
    main()
