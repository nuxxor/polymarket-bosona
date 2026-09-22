"""G3 patch on a temporary copy of G2; actual quote/cancel loop, no network."""
from hashlib import sha256
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE/'transport_fix/bot'


def scenario(root, case, candidate=True):
    spec=importlib.util.spec_from_file_location('g3_test_engine',root/'ab.py')
    b=importlib.util.module_from_spec(spec)
    with patch.object(sys,'argv',[str(root/'ab.py'),'--lane-g']):spec.loader.exec_module(b)
    now=time.time(); S=int(now)-20; tick=.001 if case=='small_tick' else .01
    if hasattr(b,'g3_arm'):
        while b.g3_arm(S)!=('G2' if case=='control' else 'G3'):S-=1
    price=.543 if case=='small_tick' else .59
    bid=.550 if case=='small_tick' else .59
    if case=='unchanged':bid=.60
    if case=='rising':bid=.61
    log=[]; audit=[]; actions=[]; drained=threading.Event(); loops=[0]
    row={'oi':0,'p':price,'boy':5,'pay':0,'durum':'acik','oid':'original','dolumlar':[]}
    w={'emir':[row],'klip':5,'cozuldu':False,'kol':'G'}
    if case=='reducing':w['emir'].append({'oi':1,'p':.30,'pay':5,'boy':5,'durum':'kapali','oid':'held','dolumlar':[{'q':5,'p':.3,'ms':1}]})
    if case=='opposite_uncertain':w['emir'].append({'oi':1,'p':.30,'pay':0,'boy':5,'durum':'belirsiz','oid':'unknown','dolumlar':[]})
    if case=='partial_existing':row.update(pay=2,dolumlar=[{'q':2,'p':price,'ms':1}])
    b.LIVE=True; b.MUTABAKAT_OK=case!='gate'; b.tick=lambda _:tick
    b.STOP='/__g3_test_no_stop__'; b.pen={('btc',S):w}
    b.log=lambda event,**kw:log.append((event,kw))
    b.state_kaydet=lambda:None; b.healthy=lambda _:True
    b.kesici_asilir=lambda *args:case=='budget'
    def cancel(oid):
        actions.append(('cancel',oid))
        return (False,'pending') if case=='cancel_pending' else (True,'canceled')
    b.iptal=cancel
    b.dolum_oku=lambda oid:(5 if case=='cancel_filled' else (2 if case=='cancel_fill' else 0),
                          'LIVE' if case=='cancel_pending' else ('MATCHED' if case=='cancel_filled' else 'CANCELED'))
    def post(rows):
        assert row['durum']=='kapali', 'replacement preceded confirmed cancellation'
        assert row['pay']==0, 'partial fill ignored'
        actions.append(('post',rows))
        return [(oi,p,'replacement','KABUL') for oi,token,p,q in rows]
    b.koy_toplu=post
    def sleep(seconds):
        loops[0]+=1
        if loops[0]>=2:b.DURDUR=True
        time.sleep(1.05)  # Preserve the real one-second replacement cooldown.
    b.time=SimpleNamespace(time=time.time,sleep=sleep,monotonic=time.monotonic,
                           monotonic_ns=time.monotonic_ns,time_ns=time.time_ns)
    frames=[json.dumps({'event_type':'book','asset_id':'up','timestamp':str(round((now-(4 if case=='stale' else 0))*1000)),
                        'bids':[{'price':str(bid),'size':'20'}],
                        'asks':[{'price':str(bid+tick),'size':'20'}]})]
    class Book:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def send(self,value):pass
        def recv(self,timeout):
            if frames:return frames.pop(0)
            drained.set();time.sleep(.005);raise TimeoutError
    original_start=threading.Thread.start;threads=[]
    def start(thread):
        threads.append(thread);original_start(thread)
        assert drained.wait(2)
    journal=SimpleNamespace(errors=0)
    def record(event,**fields):
        audit.append((event,fields))
        if case=='logging_error':journal.errors=1
    journal.yaz=record
    with (patch('websockets.sync.client.connect',lambda *args,**kw:Book()),
          patch.object(threading.Thread,'start',start),
          patch.object(b.emir_iz,'aktif',journal)):
        b.taze_izle(('btc',S),w,{0:'up',1:'down'})
    for thread in threads:
        thread.join(2);assert not thread.is_alive()
    flags=[x for k,x in log if k=='G3_KORUMA_IPTAL']
    triggered=case in ('fallen','small_tick','cancel_pending','cancel_fill','cancel_filled','partial_existing') and candidate
    assert bool(flags)==triggered,(case,candidate,flags)
    if triggered:
        assert flags[0]['emirler'][0]['oid']=='original'
        assert flags[0].get('mono_ns',flags[0].get('decision',{}).get('mono_ns',0))>0
        assert actions[0]==('cancel','original')
        if case=='cancel_pending':
            assert row['durum']=='belirsiz' and not any(a[0]=='post' for a in actions)
            assert b.toplam_risk()>=price*5-1e-9
        elif case in ('cancel_fill','cancel_filled','partial_existing'):
            assert row['pay']==(5 if case=='cancel_filled' else 2) and not any(a[0]=='post' for a in actions)
        else:
            assert actions[1][0]=='post' and abs(actions[1][1][0][2]-(bid-.01))<1e-9
    elif case in ('stale','gate','budget'):
        assert actions[0]==('cancel','original') and not any(a[0]=='post' for a in actions)
    else:assert not actions,(case,actions)
    if hasattr(b,'g3_arm'):
        for event,fields in audit:
            if event=='g3_quote':
                assert fields['arm']==b.g3_arm(S) and fields['book']['mono_ns']<=fields['decision']['mono_ns']
                assert fields['pending'] and fields['inventory']==([2,0] if case=='partial_existing' else ([0,5] if case=='reducing' else [0,0]))
        if case=='logging_error':assert b.DURDUR and b.st['durdu']=='emir_kaydi_hata'
    return {'case':case,'candidate':candidate,'flags':len(flags),'actions':[a[0] for a in actions]}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--operator-candidate',action='store_true')
    parser.add_argument('--base-root',type=Path);args=parser.parse_args()
    base=args.base_root or BASE
    label='G3_LIVE' if args.operator_candidate else 'G3'
    protocol=json.loads((HERE/(label+'_PROTOCOL.json')).read_text())
    assert sha256((base/'ab.py').read_bytes()).hexdigest()==protocol['base_sha256']
    assert sha256((HERE/(label+'.patch')).read_bytes()).hexdigest()==protocol['patch_sha256']
    results=[]
    with tempfile.TemporaryDirectory(prefix='.g3-check-',dir=HERE/'validation') as directory:
        root=Path(directory)
        manifest=json.loads((base/'G_RELEASE.json').read_text())
        for name in set(manifest)|{'test_transport.py','test_identity.py','identity_case.json'}:
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(base/name if (base/name).exists() else HERE/name,dest)
        proc=subprocess.run(['/usr/bin/patch','--batch','-p0','-d',str(root),'-i',str(HERE/(label+'.patch'))],capture_output=True,text=True)
        assert proc.returncode==0,proc.stdout+proc.stderr
        assert sha256((root/'ab.py').read_bytes()).hexdigest()==protocol['candidate_sha256']
        manifest['ab.py']=protocol['candidate_sha256'];(root/'G_RELEASE.json').write_text(json.dumps(manifest))
        sys.path.insert(0,str(root))
        try:
            results.append(scenario(base,'fallen',candidate=False))
            for case in ('fallen','small_tick','reducing','unchanged','rising','stale','gate','budget','cancel_pending','cancel_fill'):
                results.append(scenario(root,case))
            if args.operator_candidate:
                for case in ('control','logging_error','cancel_filled','opposite_uncertain','partial_existing'):
                    results.append(scenario(root,case))
        finally:sys.path.remove(str(root))
        regressions={}
        for name in ('test_transport.py','test_identity.py','test_g.py','test_g_pilot.py','test_continuous.py','test_g_stream.py'):
            proc=subprocess.run([sys.executable,'-B',str(root/name)],cwd=root,capture_output=True,text=True,timeout=60)
            assert proc.returncode==0,(name,proc.stdout,proc.stderr)
            regressions[name]=proc.returncode
        lint_status='PASS'
        if importlib.util.find_spec('ruff') is None:
            local=json.loads((HERE/'validation/G3_LOCAL_checks.json').read_text())
            assert local['candidate_sha256']==protocol['candidate_sha256'] and local['ruff_F_E9']=='PASS'
            lint_status='PASS_LOCAL_IDENTICAL_SOURCE'
        else:
            lint=subprocess.run([sys.executable,'-m','ruff','check','--select','F,E9',str(root/'ab.py'),str(Path(__file__))],capture_output=True,text=True)
            assert lint.returncode==0,lint.stdout+lint.stderr
        compile((root/'ab.py').read_text(),str(root/'ab.py'),'exec')
    result={'status':'PASS','cases':results,'regressions':regressions,'ruff_F_E9':lint_status,'syntax':'PASS',
            'base_sha256':protocol['base_sha256'],'candidate_sha256':protocol['candidate_sha256'],'live_actions':0}
    (HERE/('validation/'+label+'_checks.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: {len(results)} real quote-loop cases, 6 G2 regression scripts, lint/syntax; no live action')


if __name__=='__main__':main()
