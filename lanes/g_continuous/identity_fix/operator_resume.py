"""Default verifies parked files only. Financial restart is an explicit operator action."""
import argparse
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
TARGET=Path('/home/ubuntu/polymarket-bosona-g-continuous/bot')


def read(path):return json.loads(path.read_text())


def digest(path):return sha256(path.read_bytes()).hexdigest()


def verify_package():
    old=read(HERE/'before_release.json');new=read(HERE/'bot/G_RELEASE.json')
    assert old.keys()==new.keys() and [n for n in old if old[n]!=new[n]]==['ab.py']
    for name,value in new.items():assert digest(HERE/'bot'/name)==value, name
    return old,new


def apply(root,old,new):
    """Called with operator lock and no bot/recorder processes; only two source files change."""
    current=read(root/'G_RELEASE.json')
    assert current in (old,new), 'unexpected installed release'
    for name,value in current.items():assert digest(root/name)==value, name
    protected={name:digest(root/name) for name in ('RUN_G.json','BUDGET_G.json','STATE_g.json','protocol.json','g_policy.py')}
    if current==old:
        archive=root/('identity_fix_backup_'+str(time.time_ns()))
        archive.mkdir()
        for name in ('ab.py','G_RELEASE.json'):
            (archive/name).write_bytes((root/name).read_bytes())
        (archive/'protected_hashes.json').write_text(json.dumps(protected,indent=2)+'\n')
        for name in ('ab.py','G_RELEASE.json'):
            temporary=root/(name+'.identity_tmp')
            with temporary.open('xb') as file:file.write((HERE/'bot'/name).read_bytes())
            temporary.replace(root/name)
    assert protected=={name:digest(root/name) for name in protected}
    for name,value in new.items():assert digest(root/name)==value, name
    return protected


def processes(root):
    found=[]
    for path in Path('/proc').glob('[0-9]*'):
        try:args=(path/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        if any(str(root/name).encode() in args for name in ('g.py','ab.py','pilot.py','observer.py')):
            found.append(int(path.name))
    return found


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator-restart',action='store_true')
    args=parser.parse_args();old,new=verify_package()
    if not args.operator_restart:
        print(json.dumps(dict(status='PARKED_VERIFIED',source_sha=new['ab.py'],financial_action=False)))
        return
    root=TARGET
    sys.path.insert(0,str(root))
    import pilot
    with (root/'.g_operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert set(pilot.writers())<=set(processes(root)), 'unrelated live writer'
        pilot.verify(root)  # Verify before requesting the operator-authorized shutdown.
        before={name:digest(root/name) for name in ('BUDGET_G.json','RUN_G.json')}
        (root/'STOP_G').touch()
        deadline=time.monotonic()+180
        while processes(root) and time.monotonic()<deadline:time.sleep(1)
        assert not processes(root) and not pilot.writers(), 'old processes not closed; no force-kill'
        apply(root,old,new)
    # Existing read-only preflight may wait for the official resolution of the last market.
    ready=False
    for _ in range(60):
        with (HERE/'preflight.console.log').open('a') as log:
            result=subprocess.run([sys.executable,str(root/'pilot.py'),'--resume'],stdout=log,stderr=log)
        if result.returncode==0:
            ready=True;break
        print('Eski pencere/hesap teyidi bekleniyor; emir gonderilmedi.',flush=True)
        time.sleep(15)
    assert ready, 'preflight unresolved; remains stopped'
    assert before=={name:digest(root/name) for name in before}, 'budget/activation changed'
    print('999 yamasi dogrulandi; ayni butceyle operator LIVE devam yolu.',flush=True)
    os.execv(sys.executable,[sys.executable,'-u',str(root/'pilot.py'),'--live','--resume'])


if __name__=='__main__':
    try:main()
    except Exception as error:
        print('IDENTITY_FIX_FAILED: '+type(error).__name__,flush=True)
        raise SystemExit(1) from None
