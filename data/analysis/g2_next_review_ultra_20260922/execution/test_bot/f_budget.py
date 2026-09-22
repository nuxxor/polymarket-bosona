"""F icin operator onayli tek yeni $10 butce; PnL gecmisi silinmez."""
import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


def budget_id(data):
    return hashlib.sha256(json.dumps({k:v for k,v in data.items() if k!='id'},sort_keys=True).encode()).hexdigest()[:20]


def read_budget(path, allow_unlimited=False):
    if not Path(path).exists(): return None
    b=json.loads(Path(path).read_text())
    if (b['limit']!=10 or not all(math.isfinite(b[k]) for k in ('anchor','cutoff'))
            or not ((allow_unlimited and b.get('continuous') is True and b['end_ms'] is None)
                    or (isinstance(b['end_ms'],(int,float)) and math.isfinite(b['end_ms'])))
            or abs(b['cutoff']-(b['anchor']-b['limit']))>1e-9 or b['id']!=budget_id(b)):
        raise ValueError('F butce dosyasi gecersiz')
    return b


def create_budget(state,ending,start_ms):
    st=state['st'];ws=state['pen'].values()
    if st.get('f_budget_id'): raise ValueError('F butcesi daha once acilmis')
    if not ending or ending.get('lane')!='F' or ending.get('sebep') not in ('STOP','sure','sinyal','kesici'):
        raise ValueError('F temiz kapanisi yok')
    if any(st[k]!=ending[k] for k in ('pnl','pencere','emir')): raise ValueError('State/kapanis farki')
    if any(not math.isfinite(st[k]) for k in ('pnl','pnl_yerel')) or abs(st['pnl']-st['pnl_yerel'])>.0002:
        raise ValueError('Muhasebe mutabik degil')
    if any(w.get('kol') not in ('D','E','F') for w in ws): raise ValueError('Bilinmeyen lane')
    if any(not w.get('cozuldu') for w in ws if w.get('kol')!='F'):
        raise ValueError('Eski D/E sonuclari tamamlanmamis')
    if any(r.get('durum') not in ('kapali','dolu') or r.get('gonderiliyor') for w in ws for r in w['emir']):
        raise ValueError('Acik/belirsiz emir var')
    if any(r.get('pay',0)>0 for w in ws if w.get('kol')=='F' for r in w['emir']):
        raise ValueError('F dolumu var; bu arac baslangici yeniden yazamaz')
    if not 0<start_ms<=time.time()*1000<start_ms+120*60000-60000:
        raise ValueError('Ilk 120 dakikalik deneme suresi bitiyor')
    anchor=min(st['pnl'],st['pnl_yerel'])
    b=dict(limit=10,anchor=anchor,cutoff=anchor-10,end_ms=start_ms+120*60000,
           created_ms=round(time.time()*1000),previous_stop=st.get('durdu'))
    b['id']=budget_id(b)
    return b


def restart_recorder(bot,source):
    directory=(bot/'../data/d_olcum').resolve()
    (directory/'STOP').touch()
    deadline=time.monotonic()+20
    with (directory/'.lock').open('a') as lock:
        while True:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic()>deadline:raise ValueError('Fiyat kaydedicisi kapanmadi')
                time.sleep(1)
        (directory/'STOP').rename(directory/'STOP.butce_once')
    with (directory/'console.log').open('a') as out:
        proc=subprocess.Popen([sys.executable,str(source),'--directory',str(directory)],
                              stdin=subprocess.DEVNULL,stdout=out,stderr=out,start_new_session=True)
    (directory/'collector.pid').write_text(str(proc.pid)+'\n')
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if proc.poll() is not None:raise ValueError('Fiyat kaydedicisi baslatilamadi')
        latest=json.loads((directory/'latest.json').read_text())
        if latest.get('connected') and all(0<=time.time()*1000-latest.get('prices',{}).get(s,{}).get(k,0)<=3000
                for s in ('crypto_prices','crypto_prices_chainlink','crypto_prices_twap_thirty','crypto_prices_twap_sixty')
                for k in ('received_ms','observed_ms')):return
        time.sleep(1)
    raise ValueError('Dort fiyat akisi tazelenmedi; F STOP korunuyor')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uygula',action='store_true')
    args=parser.parse_args()
    stage=Path(__file__).resolve().parent
    bot=stage.parent
    if stage.name!='F_BUDGET_STAGE': raise SystemExit('Bu arac dogrulanmis F_BUDGET_STAGE icinden calistirilmali')
    with contextlib.redirect_stdout(io.StringIO()): import ab
    def writers():
        out=[]
        for proc in Path('/proc').glob('[0-9]*'):
            try:
                argv=(proc/'cmdline').read_bytes().decode('utf8','ignore').split('\0')
                if 'python' in argv[0] and ab.d_baska_yazici(argv,os.readlink(proc/'cwd')):
                    out.append((int(proc.name),str(bot/'f.py') in argv))
            except OSError: pass
        return out
    if not args.uygula:
        print(json.dumps(dict(writers=writers(),already_applied=(bot/'BUDGET_F.json').exists())))
        return
    with (bot/'.f_budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        old=json.loads((bot/'F_RELEASE.json').read_text())
        new=json.loads((stage/'F_RELEASE.json').read_text())
        from f_gecis import RELEASE_FILES
        if set(new['sha256'])!=set(RELEASE_FILES): raise ValueError('Yeni kaynak listesi eksik/farkli')
        for n,digest in old['sha256'].items():
            if hashlib.sha256((bot/n).read_bytes()).hexdigest()!=digest: raise ValueError('Mevcut F kaynak farki')
        for n,digest in new['sha256'].items():
            p=stage/n if (stage/n).is_file() else bot/n
            if hashlib.sha256(p.read_bytes()).hexdigest()!=digest: raise ValueError('Yeni F kaynak farki')
        if (bot/'BUDGET_F.json').exists() or (bot/'STATE_f.json.butce_oncesi').exists():
            raise ValueError('Bu butce islemi zaten uygulanmis; yeniden sifirlanamaz')
        if any(not own for _,own in writers()): raise ValueError('F disi canli yazici var')
        if subprocess.run(['tmux','has-session','-t','bosona-f-budget'],capture_output=True).returncode==0:
            raise ValueError('bosona-f-budget oturumu zaten var')
        # Tum kontrollerden sonra operatorun gercek STOP/start islemi.
        (bot/'STOP_F').touch()
        deadline=time.monotonic()+180
        while writers():
            if time.monotonic()>deadline: raise ValueError('F temiz kapanmadi; zorla kill yok')
            time.sleep(1)
        raw=(bot/'STATE_f.json').read_bytes();state=json.loads(raw)
        events=[json.loads(l) for l in (bot/'LOG_f.jsonl').open() if l.strip()]
        start=next(e['utc_ms'] for e in events if e['k']=='SURUM')
        ending=None
        for e in events:
            if e['k']=='SURUM': ending=None
            if e['k']=='bitti': ending=e
        b=create_budget(state,ending,start)
        b['state_sha']=hashlib.sha256(raw).hexdigest();b['id']=budget_id(b)
        restart_recorder(bot,stage/'d_olcum.py')
        with (bot/'STATE_f.json.butce_oncesi').open('xb') as f: f.write(raw)
        with (bot/'BUDGET_F.json').open('x') as f: json.dump(b,f,indent=2)
        state['st']['f_budget_id']=b['id'];state['st']['durdu']=None
        tmp=bot/'STATE_f.json.butce_tmp';tmp.write_text(json.dumps(state));os.replace(tmp,bot/'STATE_f.json')
        for n in ('ab.py','emir_iz.py','f_budget.py','f_gecis.py','d_olcum.py','F_RELEASE.json'):
            with (bot/(n+'.butce_once')).open('xb') as f:
                if (bot/n).exists(): f.write((bot/n).read_bytes())
            tmp=bot/(n+'.butce_tmp');tmp.write_bytes((stage/n).read_bytes());os.replace(tmp,bot/n)
        (bot/'STOP_F').rename(bot/'STOP_F.butce_once')
        remaining=(b['end_ms']-time.time()*1000)/60000
        try:
            subprocess.run(['tmux','new-session','-d','-s','bosona-f-budget',sys.executable,'-u',
                            str(bot/'f.py'),'--live','--dk',str(remaining)],check=True)
        except Exception:
            (bot/'STOP_F').touch();raise
        print(f"F yeni butce: $10; gecmis PnL {b['anchor']:.6f}; toplam kesici {b['cutoff']:.6f}; kalan {remaining:.1f} dk.")
        print('Baslatma istendi; LIVE F_BUTCE kaydi ayrica teyit edilmeli.')


if __name__=='__main__':main()
