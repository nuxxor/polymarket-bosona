"""Parked G4 package. Only --operator-start stops G3 and activates G4 money."""
import argparse
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys
import tarfile
import time

HERE = Path(__file__).resolve().parent
TARGET = Path('/home/ubuntu/polymarket-bosona-g-continuous/bot')
LIMIT = 100
EXPERIMENT = 'G4'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def package():
    protocol = json.loads((HERE/f'{EXPERIMENT}_PROTOCOL.json').read_text())
    assert protocol['loss_limit'] == LIMIT
    assert digest(HERE/f'{EXPERIMENT}_package.tar.gz') == protocol['package_sha256']
    with tarfile.open(HERE/f'{EXPERIMENT}_package.tar.gz') as archive:
        old = json.load(archive.extractfile('BASE_RELEASE.json'))
        new = json.load(archive.extractfile('G_RELEASE.json'))
        changed = {n for n in new if old[n] != new[n]}
        assert set(archive.getnames()) == changed | {'BASE_RELEASE.json', 'G_RELEASE.json'}
        files = {n: archive.extractfile(n).read() for n in changed}
    assert all(sha256(data).hexdigest() == new[n] for n, data in files.items())
    assert new['ab.py'] == protocol['candidate_sha256']
    return files, old, new


def verify(root, old, new):
    installed = json.loads((root/'G_RELEASE.json').read_text())
    assert installed in (old, new), 'unknown release'
    assert all(digest(root/n) == value for n, value in installed.items()), 'changed source'
    return installed


def processes(root):
    found = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            args = (proc/'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue
        if any(str(root/n).encode() in args for n in ('g.py', 'ab.py', 'pilot.py', 'observer.py')):
            found.append(int(proc.name))
    return found


def activate(root, files, old, new, state, proof, now):
    """No exchange operations; caller holds operator lock after full reconciliation."""
    from f_budget import budget_id
    assert not processes(root) and (root/'STOP_G').exists(), 'normal shutdown required'
    assert verify(root, old, new) == old, 'G4 already installed; resume, never reset'
    assert not (root/f'{EXPERIMENT}_ACTIVATION.json').exists(), 'activation already attempted'
    assert 0 <= now-proof['checked_ms'] <= 30000 and proof['open_orders'] == proof['risk'] == 0
    st = state['st']
    assert all(math.isfinite(st[k]) for k in ('pnl', 'pnl_yerel'))
    assert abs(st['pnl']-st['pnl_yerel']) <= .0002 and abs(proof['pnl']-st['pnl_yerel']) <= 1e-9
    assert all(w.get('cozuldu') and all(r['durum'] in ('kapali', 'dolu') and not r.get('gonderiliyor')
                                      for r in w['emir']) for w in state['pen'].values())
    anchor = min(st['pnl'], st['pnl_yerel'])
    budget = dict(experiment=EXPERIMENT, limit=LIMIT, anchor=anchor, cutoff=anchor-LIMIT,
                  end_ms=None, continuous=True, created_ms=now, previous_stop=st.get('durdu'))
    budget['id'] = budget_id(budget)
    archive = root/f'{EXPERIMENT}_before_activation'
    archive.mkdir()
    for name in files.keys() | {'G_RELEASE.json', 'RUN_G.json', 'BUDGET_G.json', 'STATE_g.json'}:
        dest = archive/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((root/name).read_bytes())
    marker = dict(budget=budget, previous_budget=json.loads((root/'BUDGET_G.json').read_text()),
                  source_sha=new['ab.py'], proof=proof)
    # Exclusive marker is committed before any replacement: interrupted installs stay stopped.
    with (root/f'{EXPERIMENT}_ACTIVATION.json').open('x') as file:
        json.dump(marker, file, indent=2)
    state = {**state, 'st': {**st, 'f_budget_id': budget['id'], 'durdu': None}}
    replacements = {**files, 'BUDGET_G.json': json.dumps(budget).encode(),
                    'STATE_g.json': json.dumps(state).encode(),
                    'RUN_G.json': json.dumps(dict(proof=proof, budget=budget)).encode(),
                    'G_RELEASE.json': json.dumps(new, indent=2).encode()}
    for name, data in replacements.items():
        temporary = root/(name+f'.{EXPERIMENT.lower()}_tmp')
        with temporary.open('xb') as file:
            file.write(data)
        temporary.replace(root/name)
    assert verify(root, old, new) == new and (root/'STOP_G').exists()
    return budget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator-start', action='store_true')
    args = parser.parse_args()
    files, old, new = package()
    root = TARGET
    installed = verify(root, old, new)
    if not args.operator_start:
        print(json.dumps(dict(status='PARKED_VERIFIED', installed_sha=installed['ab.py'],
                              candidate_sha=new['ab.py'], new_loss_limit=LIMIT, live_action=False)))
        return
    sys.path.insert(0, str(root))
    import pilot
    from f_budget import read_budget
    with (root/'.g_operator.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        installed = verify(root, old, new)
        writers = pilot.writers()
        assert set(writers) <= set(processes(root)), 'unrelated LIVE writer'
        if installed == new:
            budget = read_budget(root/'BUDGET_G.json', allow_unlimited=True)
            marker = json.loads((root/f'{EXPERIMENT}_ACTIVATION.json').read_text())
            assert marker['budget'] == budget and budget['experiment'] == EXPERIMENT and budget['limit'] == LIMIT
            if writers:
                print(EXPERIMENT+' zaten LIVE; butce/sure sifirlanmadi.', flush=True)
                return
        else:
            assert not (root/f'{EXPERIMENT}_ACTIVATION.json').exists(), 'incomplete activation; remains stopped'
            (root/'STOP_G').touch()
            deadline = time.monotonic()+180
            while processes(root) and time.monotonic() < deadline:
                time.sleep(1)
            assert not processes(root) and not pilot.writers(), 'normal shutdown incomplete'
            ready = None
            for _ in range(60):
                protocol = {**pilot.verify(root), 'source_bot': str(root), 'source_state': 'STATE_g.json',
                            'source_log': 'LOG_g.jsonl', 'source_state_sha': digest(root/'STATE_g.json')}
                try:
                    ready = pilot.preflight(root, protocol)
                    break
                except Exception as error:
                    print(EXPERIMENT+' hesap teyidi bekleniyor: '+type(error).__name__, flush=True)
                    time.sleep(15)
            assert ready is not None, 'preflight unresolved; remains stopped'
            budget = activate(root, files, old, new, *ready, round(time.time()*1000))
            print(json.dumps(dict(event=EXPERIMENT+'_FRESH_BUDGET', **budget)), flush=True)
    # Fresh process loads the new source; standard launcher verifies the budget, account and both recorders.
    os.execv(sys.executable, [sys.executable, '-u', str(root/'pilot.py'), '--live', '--resume'])


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('G4_PREPARE_FAILED: '+type(error).__name__, flush=True)
        raise SystemExit(1) from None
