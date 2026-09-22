"""G4 real sizing/POST paths and fresh-budget transition, with no financial API calls."""
import argparse
import copy
import importlib.util
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from unittest.mock import patch

import g4_operator as g


def materialize(root, base, candidate=True):
    files, old, new = g.package()
    for name in old:
        dest = root/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base/name, dest)
    if base == g.HERE/'transport_fix/bot':
        with tarfile.open(g.HERE/'G3_package.tar.gz') as archive:
            (root/'ab.py').write_bytes(archive.extractfile('ab.py').read())
    (root/'G_RELEASE.json').write_text(json.dumps(old))
    assert g.verify(root, old, new) == old
    if candidate:
        for name, data in files.items():
            (root/name).write_bytes(data)
        (root/'G_RELEASE.json').write_text(json.dumps(new))
    for name in ('test_transport.py', 'test_identity.py', 'identity_case.json'):
        source = base/name if (base/name).exists() else g.HERE/name
        shutil.copyfile(source, root/name)
    return files, old, new


def checks(root, base):
    sys.path.insert(0, str(root))
    import test_g
    import f_budget
    import g_guard
    import pilot
    from test_g3 import scenario
    b = test_g.load()
    order = test_g.order
    b.log = lambda *a, **k: None
    b.state_kaydet = lambda: None
    b.STOP = str(root/'STOP_TEST')
    b.st['pnl'] = b.st['pnl_yerel'] = -15
    b.KESICI = -115
    b.MUTABAKAT_OK = True
    now = round(time.time()*1000)
    S = int(now/1000)-30
    signal = dict(S=S, karar_ms=now, book_ms=now, model_sha=b.g_policy.SHA, bb=.41, ba=.42, tick=.01)
    calls = []
    b.koy_toplu = lambda rows: calls.append(rows) or [(oi, p, 'mock'+str(len(calls)), 'KABUL') for oi, t, p, q in rows]
    w = dict(emir=[order(0, .4)], klip=5, kol='G', cozuldu=False)
    b.pen = {('btc', S): w}
    r = b.d_koy(('btc', S), w, 0, 'up', .4, 5, .41, .42, 10, signal)
    assert r is not None and b.d_miktar(w, 0) == 0 and len(calls) == 1
    b.pay_ekle(r, 5, 'test', ('btc', S))
    assert b.d_miktar(w, 0) == 0 and b.d_miktar(w, 1) == 5
    assert b.d_koy(('btc', S), w, 0, 'up', .4, 5, .41, .42, 10, signal) is None
    # Exhaustively bound filled net plus same-side reserves; opposite pending fills never create credit.
    for q0, q1, side in itertools.product((0, 2, 5, 7, 10), (0, 2, 5, 7, 10), (0, 1)):
        w = dict(emir=[order(0, .4, q0), order(1, .4, q1)], klip=5, kol='G', cozuldu=False)
        q = [q0, q1]
        size = b.d_miktar(w, side)
        assert 0 <= size <= 5 and q[side]-q[1-side]+size <= 10+1e-9
        if q[side] < q[1-side]:
            assert size <= q[1-side]-q[side]
        if size:
            w['emir'].append({**order(side, .4, 0, 'belirsiz'), 'boy': size})
            assert b.d_miktar(w, side) == 0
    partial = dict(emir=[order(0, .4, 2)], klip=5, kol='G', cozuldu=False)
    assert b.d_miktar(partial, 0) == 5 and b.d_miktar(partial, 1) == 2
    b.pen = {('btc', S): partial}
    count = len(calls)
    assert b.d_koy(('btc', S), partial, 1, 'down', .4, 5, .41, .42, 10, signal) is None
    b.st['pnl'] = b.st['pnl_yerel'] = -114.5
    assert b.d_koy(('btc', S), partial, 0, 'up', .4, 5, .41, .42, 10, signal) is None
    assert len(calls) == count
    # Price retention is G2 behavior. STOP/data/account gates still cancel through the real loop.
    for case in ('fallen', 'unchanged', 'rising', 'reducing', 'stale', 'gate', 'budget', 'opposite_uncertain', 'logging_error'):
        scenario(root, case, candidate=False)
    with tempfile.TemporaryDirectory(dir=g.HERE/'validation', prefix='.g4-money-') as directory:
        target = Path(directory)
        files, old, new = materialize(target, base, candidate=False)
        state = dict(st=dict(pnl=-15.33, pnl_yerel=-15.33001, emir=1234, durdu='STOP', f_budget_id='old'),
                     pen={'btc|1': dict(cozuldu=True, emir=[])})
        for name, value in [('STATE_g.json', state), ('RUN_G.json', {'old': True}),
                            ('BUDGET_G.json', {'id': 'old', 'anchor': -6, 'cutoff': -16, 'limit': 10})]:
            (target/name).write_text(json.dumps(value))
        proof = dict(checked_ms=1000, pnl=-15.33001, risk=0, open_orders=0)
        (target/'STOP_G').touch()
        untouched = {n: g.digest(target/n) for n in ('STATE_g.json', 'RUN_G.json', 'BUDGET_G.json')}
        for reason in ('running', 'unresolved', 'pending', 'stale'):
            bad = copy.deepcopy(state)
            if reason == 'unresolved':
                bad['pen']['btc|1']['cozuldu'] = False
            if reason == 'pending':
                bad['pen']['btc|1']['emir'] = [order(0, .4, 0, 'belirsiz')]
            with patch.object(g, 'processes', return_value=[999] if reason == 'running' else []):
                try:
                    g.activate(target, files, old, new, bad, proof, 40001 if reason == 'stale' else 1001)
                except AssertionError:
                    pass
                else:
                    raise AssertionError(reason)
            assert untouched == {n: g.digest(target/n) for n in untouched}
        with patch.object(g, 'processes', return_value=[]):
            budget = g.activate(target, files, old, new, state, proof, 1001)
            assert budget['limit'] == 100 and budget['anchor'] == -15.33001 and budget['cutoff'] == -115.33001
            assert state['st']['f_budget_id'] == 'old'
            assert json.loads((target/'STATE_g.json').read_text())['st']['emir'] == 1234
            assert untouched == {n: g.digest(target/'G4_before_activation'/n) for n in untouched}
            try:
                g.activate(target, files, old, new, state, proof, 1002)
            except AssertionError:
                pass
            else:
                raise AssertionError('G4 budget reset')
        assert f_budget.read_budget(target/'BUDGET_G.json', allow_unlimited=True) == budget
        g_guard.verify(target, budget)
        before = {n: g.digest(target/n) for n in ('RUN_G.json', 'BUDGET_G.json')}
        resumed = json.loads((target/'STATE_g.json').read_text())
        resumed['st'].update(pnl=-16, pnl_yerel=-16)
        pilot.resume_files(target, resumed, proof, budget, 1002)
        assert before == {n: g.digest(target/n) for n in before}
        resumed['st'].update(pnl=budget['cutoff'], pnl_yerel=budget['cutoff'])
        try:
            pilot.resume_files(target, resumed, proof, budget, 1003)
        except ValueError:
            pass
        else:
            raise AssertionError('exhausted G4 resumed')
        bad = {**budget, 'limit': 1000, 'cutoff': budget['anchor']-1000}
        bad['id'] = f_budget.budget_id(bad)
        (target/'bad.json').write_text(json.dumps(bad))
        try:
            f_budget.read_budget(target/'bad.json', allow_unlimited=True)
        except ValueError:
            pass
        else:
            raise AssertionError('unfrozen budget accepted')
    with tempfile.TemporaryDirectory(dir=g.HERE/'validation', prefix='.g4-interrupted-') as directory:
        target = Path(directory)
        files, old, new = materialize(target, base, candidate=False)
        for name, value in [('STATE_g.json', state), ('RUN_G.json', {'old': True}),
                            ('BUDGET_G.json', {'id': 'old', 'limit': 10})]:
            (target/name).write_text(json.dumps(value))
        (target/'STOP_G').touch()
        replace = Path.replace
        def interrupted(path, destination):
            if Path(destination).name == 'STATE_g.json':
                raise OSError('injected write interruption')
            return replace(path, destination)
        with patch.object(g, 'processes', return_value=[]), patch.object(Path, 'replace', interrupted):
            try:
                g.activate(target, files, old, new, state, proof, 1001)
            except OSError:
                pass
            else:
                raise AssertionError('interruption not injected')
        marker = (target/'G4_ACTIVATION.json').read_bytes()
        assert (target/'STOP_G').exists()
        with patch.object(g, 'processes', return_value=[]):
            try:
                g.activate(target, files, old, new, state, proof, 1002)
            except AssertionError:
                pass
            else:
                raise AssertionError('partial activation reset')
        assert (target/'G4_ACTIVATION.json').read_bytes() == marker
    # Actual shell launcher with a fake SSH executable; it must not activate anything here.
    with tempfile.TemporaryDirectory(dir=g.HERE/'validation') as directory:
        tmp = Path(directory)
        fake = tmp/'ssh'
        fake.write_text('#!'+sys.executable+'\nimport sys\nassert "--operator-start" in sys.argv[-1]\nassert "bosona-g4" in sys.argv[-1]\n')
        fake.chmod(0o755)
        launcher = g.HERE/'londra_g4_baslat.sh'
        if not launcher.exists():
            launcher = g.HERE.parents[1]/'londra_g4_baslat.sh'
        subprocess.run(['bash', '-n', str(launcher)], check=True)
        subprocess.run(['bash', str(launcher)], env={**os.environ, 'PATH': directory+':'+os.environ['PATH']}, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-root', type=Path, default=g.HERE/'transport_fix/bot')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(dir=g.HERE/'validation', prefix='.g4-check-') as directory:
        root = Path(directory)
        materialize(root, args.base_root)
        checks(root, args.base_root)
        results = {}
        for name in ('test_transport.py', 'test_identity.py', 'test_g.py', 'test_g_pilot.py', 'test_continuous.py', 'test_g_stream.py'):
            result = subprocess.run([sys.executable, '-B', str(root/name)], cwd=root, capture_output=True, text=True, timeout=90)
            assert result.returncode == 0, (name, result.stdout, result.stderr)
            results[name] = 'PASS'
        for name in g.package()[0]:
            if name.endswith('.py'):
                compile((root/name).read_text(), name, 'exec')
        if importlib.util.find_spec('ruff'):
            result = subprocess.run([sys.executable, '-m', 'ruff', 'check', '--select', 'F,E9',
                                     *[str(root/n) for n in g.package()[0] if n.endswith('.py')],
                                     str(g.HERE/'g4_operator.py'), str(Path(__file__))], capture_output=True, text=True)
            assert result.returncode == 0, result.stdout+result.stderr
            results['ruff'] = 'PASS'
        else:
            results['ruff'] = 'NOT_INSTALLED_ON_THIS_HOST'
    proof = dict(status='PASS', regressions=results, source_sha=g.package()[2]['ab.py'],
                 net_cap=10, clip=5, fresh_loss_limit=100, actual_orders=0,
                 checks='second clip, reserved net, no over-hedge, small partial, dollar guard, nine quote-loop cases, transition, history, resume, exhaustion, interrupted activation, invalid budget, launcher')
    (g.HERE/'validation/G4_checks.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
