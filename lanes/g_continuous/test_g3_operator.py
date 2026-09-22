"""No network/process control: real source update and operator flow in a temporary tree."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import g3_operator as g


def main():
    source,old,new=g.package();cases=[]
    with tempfile.TemporaryDirectory(prefix='.g3-operator-',dir=g.HERE/'validation') as directory:
        root=Path(directory)/'bot';root.mkdir()
        for name in old:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(g.HERE/'transport_fix/bot'/name,target)
        (root/'G_RELEASE.json').write_text(json.dumps(old))
        for name,value in [('RUN_G.json',{'unchanged':True}),('BUDGET_G.json',{'limit':10,'anchor':100,'cutoff':90}),('STATE_g.json',{'unchanged':True})]:
            (root/name).write_text(json.dumps(value))
        protected={name:g.digest(root/name) for name in ('RUN_G.json','BUDGET_G.json','STATE_g.json','protocol.json','g_policy.py')}
        with patch.object(g,'TARGET',root),patch.object(sys,'argv',['g3_operator.py']):g.main()
        assert not (root/'STOP_G').exists() and g.verify(root,old,new)==old;cases.append('default_read_only')
        with patch.object(g,'processes',return_value=[999]):
            try:g.apply(root,source,old,new)
            except AssertionError:pass
            else:raise AssertionError('updated a running bot')
        assert g.verify(root,old,new)==old;cases.append('active_update_rejected')
        with patch.object(g,'processes',return_value=[]):
            assert g.apply(root,source,old,new)==protected
            assert g.apply(root,source,old,new)==protected
        assert len(list(root.glob('G3_backup_*')))==1;cases.extend(['source_update','idempotent','immutable_money_state_policy'])
        (root/'ab.py').write_text('foreign edit')
        try:g.verify(root,old,new)
        except AssertionError:pass
        else:raise AssertionError('foreign source accepted')
        (root/'ab.py').write_bytes(source);cases.append('foreign_edit_rejected')
        pilot=SimpleNamespace(writers=lambda:[],verify=lambda r:g.verify(r,old,new))
        def preflight(cmd,**kwargs):
            assert cmd[-1]=='--resume' and '--live' not in cmd
            (root/'preflight.json').write_text(json.dumps({'pnl':99}))
            return SimpleNamespace(returncode=0)
        with (patch.dict(sys.modules,{'pilot':pilot}),patch.object(g,'TARGET',root),
              patch.object(g,'processes',return_value=[]),patch.object(sys,'argv',['g3_operator.py','--operator-restart']),
              patch.object(g.subprocess,'run',side_effect=preflight),patch.object(g.os,'execv') as execute):
            g.main()
            assert execute.call_count==1 and execute.call_args.args[1][-2:]==['--live','--resume']
        cases.append('explicit_operator_resume_only')
        def exhausted(cmd,**kwargs):
            (root/'preflight.json').write_text(json.dumps({'pnl':90}));return SimpleNamespace(returncode=0)
        with (patch.dict(sys.modules,{'pilot':pilot}),patch.object(g,'TARGET',root),
              patch.object(g,'processes',return_value=[]),patch.object(sys,'argv',['g3_operator.py','--operator-restart']),
              patch.object(g.subprocess,'run',side_effect=exhausted),patch.object(g.os,'execv') as execute):
            try:g.main()
            except AssertionError:pass
            else:raise AssertionError('exhausted budget continued')
            assert not execute.called
        cases.append('exhausted_budget_no_restart')
        pilot.writers=lambda:[111]
        with (patch.dict(sys.modules,{'pilot':pilot}),patch.object(g,'TARGET',root),
              patch.object(g,'processes',return_value=[111]),patch.object(sys,'argv',['g3_operator.py','--operator-restart']),
              patch.object(g.subprocess,'run') as preflight_call,patch.object(g.os,'execv') as execute):
            before=(root/'STOP_G').stat().st_mtime_ns;g.main()
            assert not preflight_call.called and not execute.called and (root/'STOP_G').stat().st_mtime_ns==before
        cases.append('active_g3_not_interrupted')
        assert {name:g.digest(root/name) for name in protected}==protected
        # Execute the real shell launcher against a recording stub, never SSH.
        fake=Path(directory)/'ssh';capture=Path(directory)/'ssh_args.json'
        fake.write_text('#!'+sys.executable+'\nimport json,sys\nfrom pathlib import Path\nPath('+repr(str(capture))+').write_text(json.dumps(sys.argv[1:]))\n')
        fake.chmod(0o755)
        launcher=g.HERE.parents[1]/'londra_g3_baslat.sh'
        subprocess.run(['bash','-n',str(launcher)],check=True)
        subprocess.run(['bash',str(launcher)],env={**os.environ,'PATH':directory+os.pathsep+os.environ['PATH']},check=True,stdout=subprocess.DEVNULL)
        args=json.loads(capture.read_text())
        assert args[-2]=='ubuntu@18.135.99.14' and '--operator-restart' in args[-1] and 'bosona-g3' in args[-1]
        cases.append('real_launcher_fake_ssh')
    result={'status':'PASS','cases':cases,'real_orders':0,'real_process_control':False}
    (g.HERE/'validation/G3_operator_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
