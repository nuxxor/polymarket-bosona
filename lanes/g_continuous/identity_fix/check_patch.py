"""Offline operator update: exact source change, preserved budget/state, no process control."""
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import operator_resume as update


def main():
    old,new=update.verify_package()
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        for name in old:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
            original=update.HERE/'before_ab.py' if name=='ab.py' else update.HERE/'bot'/name
            shutil.copyfile(original,target)
        shutil.copyfile(update.HERE/'before_release.json',root/'G_RELEASE.json')
        for name in ('RUN_G.json','BUDGET_G.json','STATE_g.json'):
            (root/name).write_text('{"unchanged": true}')
        before={name:update.digest(root/name) for name in ('RUN_G.json','BUDGET_G.json','STATE_g.json','protocol.json','g_policy.py')}
        with patch.object(update.os,'execv',side_effect=AssertionError('No live execution in test')):
            assert update.apply(root,old,new)==before
            assert update.apply(root,old,new)==before
        assert len(list(root.glob('identity_fix_backup_*')))==1
        assert update.digest(root/'ab.py')==new['ab.py']
        (root/'ab.py').write_text('changed outside release')
        try:update.apply(root,old,new)
        except AssertionError:pass
        else:raise AssertionError('foreign change overwritten')
    print('PASS: exact source update, idempotency, immutable money/state/policy, foreign change rejected')


if __name__=='__main__':main()
