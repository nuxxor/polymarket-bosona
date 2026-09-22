"""Gercek F karar dongusu, yalniz kamu verisi; kimlik, emir, sanal dolum yok."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import threading
import time
from unittest.mock import patch

from test_d import load


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=float,default=180)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    with contextlib.redirect_stdout(io.StringIO()):
        b=load(Path(__file__).with_name('ab.py'),['--lane-f'])
    counts={}; observations=[]; threads=[]; seen=set()
    def log(event,**kw):
        if event=='D_KARAR_HATA': raise AssertionError(kw)
        if event in ('F_KALITE','F_REFERANS','F_REFERANS_YOK','taze_ws_hata','taze_bitti'):
            row=dict(utc_ms=round(time.time()*1000),k=event,**kw)
            with args.out.open('a') as f: f.write(json.dumps(row)+'\n')
            if event=='F_KALITE':
                reason=kw['neden']; counts[reason]=counts.get(reason,0)+1
        observations.append(event)
    b.log=log; b.state_kaydet=lambda:None
    # Strateji sinyali ve ayni WS yolu gercek; d_koy salt aday sayar.
    def candidate(*a,**kw):
        counts['uygun_aday']=counts.get('uygun_aday',0)+1
    b.d_koy=candidate
    def forbidden(*a,**kw): raise AssertionError('Golgede emir/kimlik yolu yasak')
    b.koy_toplu=b.adres=b.iptal=b.iptal_toplu=forbidden
    end=time.monotonic()+args.seconds
    with patch.object(b,'LIVE',False):
        while time.monotonic()<end:
            S=int(time.time())//300*300
            if S not in seen and 5<time.time()-S<195:
                tk=b.tokens('btc',S)
                if tk:
                    seen.add(S)
                    w=dict(emir=[],klip=5,cozuldu=False,kol='F',f_reference=b.F_REF.get(('btc',S)))
                    thread=threading.Thread(target=b.taze_izle,args=(('btc',S),w,tk))
                    threads.append(thread);thread.start()
            time.sleep(.5)
        b.DURDUR=True
        for thread in threads: thread.join(12)
    assert all(not t.is_alive() for t in threads)
    assert 'D_KARAR_HATA' not in observations and counts, 'Karar dongusu dogrulanmadi'
    print(json.dumps(dict(windows=sorted(seen),counts=counts,real_orders=0)))


if __name__=='__main__': main()
