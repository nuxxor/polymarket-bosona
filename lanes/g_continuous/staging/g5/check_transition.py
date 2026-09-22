"""Offline G5 activation/account gates in disposable files; never touches London."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'bot'))
import f_budget  # noqa: E402
import g_guard  # noqa: E402
import pilot  # noqa: E402
import g4_operator as transition  # noqa: E402


def main():
    transition.HERE = HERE
    transition.EXPERIMENT = 'G5'
    files, old, new = transition.package()
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[3]/'.git/g4-publication-20260922/lanes/g_continuous/bot'
    with tempfile.TemporaryDirectory(prefix='.money-', dir=HERE) as directory:
        root = Path(directory)
        for n in old:
            dest = root/n
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(base/n, dest)
        (root/'G_RELEASE.json').write_text(json.dumps(old))
        (root/'STOP_G').touch()
        for n in ('RUN_G.json', 'BUDGET_G.json', 'STATE_g.json'):
            (root/n).write_text('{}')
        now = round(time.time()*1000)
        state = dict(st=dict(pnl=-12.6869, pnl_yerel=-12.6869), pen={})
        proof = dict(checked_ms=now, open_orders=0, risk=0, pnl=-12.6869)
        with patch.object(transition, 'processes', return_value=[]):
            budget = transition.activate(root, files, old, new, state, proof, now)
        assert budget['experiment'] == 'G5' and budget['limit'] == 100 and budget['anchor'] == -12.6869
        assert f_budget.read_budget(root/'BUDGET_G.json', allow_unlimited=True) == budget
        g_guard.verify(root, budget)
        assert json.loads((root/'STATE_g.json').read_text())['st']['pnl_yerel'] == -12.6869
        before = {n: (root/n).read_bytes() for n in ('RUN_G.json', 'BUDGET_G.json', 'STATE_g.json')}
        try:
            with patch.object(transition, 'processes', return_value=[]):
                transition.activate(root, files, old, new, state, proof, now)
        except AssertionError:
            pass
        else:
            raise AssertionError('Repeated activation reset budget')
        assert before == {n: (root/n).read_bytes() for n in before}
        try:
            pilot.activate_files(root, state, proof, now)
        except pilot.CheckFailed:
            pass
        else:
            raise AssertionError('Generic pilot bypassed G5 transition')
        (root/'G5_ACTIVATION.json').write_text(json.dumps(dict(budget={**budget, 'anchor': 0})))
        try:
            g_guard.verify(root, budget)
        except ValueError:
            pass
        else:
            raise AssertionError('Mismatched activation accepted')
    assert not any((HERE/'bot'/n).exists() for n in ('G5_ACTIVATION.json', 'RUN_G.json', 'BUDGET_G.json'))
    proof = dict(status='PASS', budget_created_only_in_disposable_test=True, history_preserved=True,
                 repeated_activation_rejected=True, generic_activation_rejected=True,
                 mismatched_marker_rejected=True, real_budget_created=False, live_activation=False)
    (HERE/'transition_checks.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
