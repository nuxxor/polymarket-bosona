"""Default is read-only verification. Only the operator requests --operator-restart."""
import argparse
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tarfile
import time
import subprocess

HERE=Path(__file__).resolve().parent
TARGET=Path('/home/ubuntu/polymarket-bosona-g-continuous/bot')


def digest(path):return sha256(path.read_bytes()).hexdigest()


def package():
    protocol=json.loads((HERE/'G3_LIVE_PROTOCOL.json').read_text())
    archive=HERE/'G3_package.tar.gz'
    assert digest(archive)==protocol['package_sha256'], 'package changed'
    with tarfile.open(archive) as tar:
        assert set(tar.getnames())=={'ab.py','G_RELEASE.json','BASE_RELEASE.json'}
        source=tar.extractfile('ab.py').read()
        old=json.load(tar.extractfile('BASE_RELEASE.json'))
        new=json.load(tar.extractfile('G_RELEASE.json'))
    assert old.keys()==new.keys() and [n for n in old if old[n]!=new[n]]==['ab.py']
    assert old['ab.py']==protocol['base_sha256'] and new['ab.py']==protocol['candidate_sha256']==sha256(source).hexdigest()
    assert old['g_policy.py']==protocol['policy_sha256']
    return source,old,new


def verify(root,old,new):
    installed=json.loads((root/'G_RELEASE.json').read_text())
    assert installed in (old,new), 'unknown installed release'
    for name,value in installed.items():assert digest(root/name)==value, 'installed source mismatch: '+name
    return installed


def processes(root):
    found=[]
    for proc in Path('/proc').glob('[0-9]*'):
        try:args=(proc/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        if any(str(root/name).encode() in args for name in ('g.py','ab.py','pilot.py','observer.py')):found.append(int(proc.name))
    return found


def apply(root,source,old,new):
    assert not processes(root), 'old bot or recorder still running'
    installed=verify(root,old,new)
    names=('RUN_G.json','BUDGET_G.json','STATE_g.json','protocol.json','g_policy.py')
    before={n:digest(root/n) for n in names}
    if installed==old:
        archive=root/('G3_backup_'+str(time.time_ns()));archive.mkdir()
        for name in ('ab.py','G_RELEASE.json'):(archive/name).write_bytes((root/name).read_bytes())
        (archive/'protected_hashes.json').write_text(json.dumps(before,indent=2)+'\n')
        for name,content in (('ab.py',source),('G_RELEASE.json',(json.dumps(new,indent=2)+'\n').encode())):
            temporary=root/(name+'.g3_tmp')
            with temporary.open('xb') as f:f.write(content)
            temporary.replace(root/name)
    assert {n:digest(root/n) for n in names}==before
    assert verify(root,old,new)==new
    return before


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator-restart',action='store_true');args=parser.parse_args()
    source,old,new=package();root=TARGET
    installed=verify(root,old,new)
    if not args.operator_restart:
        print(json.dumps({'status':'PARKED_VERIFIED','source_sha':new['ab.py'],'installed':installed['ab.py'],'financial_action':False}))
        return
    sys.path.insert(0,str(root))
    import pilot
    with (root/'.g_operator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        writers=pilot.writers()
        assert set(writers)<=set(processes(root)), 'unrelated live writer'
        if writers and installed==new:
            print('G3 zaten calisiyor; yeniden baslatilmadi, butce ayni.',flush=True);return
        pilot.verify(root)
        before={n:digest(root/n) for n in ('BUDGET_G.json','RUN_G.json')}
        (root/'STOP_G').touch()
        deadline=time.monotonic()+180
        while processes(root) and time.monotonic()<deadline:time.sleep(1)
        assert not processes(root) and not pilot.writers(), 'normal shutdown incomplete; no force-kill'
        apply(root,source,old,new)
    ready=False
    for _ in range(60):
        with (HERE/'validation/G3_preflight.console.log').open('a') as log:
            result=subprocess.run([sys.executable,str(root/'pilot.py'),'--resume'],stdout=log,stderr=log)
        if result.returncode==0:ready=True;break
        print('Son pencere/hesap teyidi bekleniyor; yeni emir yok.',flush=True);time.sleep(15)
    assert ready, 'preflight unresolved; remains stopped'
    assert before=={n:digest(root/n) for n in before}, 'original budget changed'
    proof=json.loads((root/'preflight.json').read_text())
    budget=json.loads((root/'BUDGET_G.json').read_text())
    assert proof['pnl']>budget['cutoff'], 'existing loss budget exhausted; no reset'
    # The existing launcher repeats account/source checks, rejects exhausted budgets,
    # starts both recorders, and preserves RUN/BUDGET and historical accounting.
    print('G3 olcum deneyi: G2/G3 pencere atamasi; mevcut butceyle operator LIVE yolu.',flush=True)
    print(json.dumps({'event':'G3_OPERATOR_ACTIVATE','source_sha':new['ab.py'],
                      'budget_sha':before['BUDGET_G.json'],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                      'utc_ns':time.time_ns(),'mono_ns':time.monotonic_ns()}),flush=True)
    os.execv(sys.executable,[sys.executable,'-u',str(root/'pilot.py'),'--live','--resume'])


if __name__=='__main__':
    try:main()
    except Exception as error:
        print('G3_PREPARE_FAILED: '+type(error).__name__,flush=True)
        raise SystemExit(1) from None
