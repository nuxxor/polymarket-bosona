"""Replay the real 429/408/429 stop; no network, credentials or live orders."""
import copy
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from test_g import load


def http(code):
    return HTTPError('https://test.invalid/positions', code, 'test', {}, None)


def exercise(stop=None, failure=None):
    b=load(); now=[1000.0]; events=[]; reads=[]; ledger=[]
    responses=iter([[], *(failure or [http(429),http(408),http(429)]), [], []])
    def read(*args):
        reads.append((now[0],b.MUTABAKAT_OK))
        result=next(responses)
        if isinstance(result,Exception): raise result
        return result
    def reconcile():
        ledger.append(now[0]); b.MUTABAKAT_OK=False
        if len(ledger)==2 and stop is None: return None
        b.MUTABAKAT_OK=True
        return 0.0
    def log(k,**kw):
        events.append((k,kw,now[0],b.MUTABAKAT_OK))
    def sleep(seconds):
        now[0]+=seconds
        assert now[0]<1200, 'recovery stalled'
    b.LIVE=True; b.PAZAR=[]; b.MAX_SAAT=None; b.STOP='fake_stop'
    b.state_yukle=lambda:None; b.state_kaydet=lambda:None
    b.d_acik_kontrol=lambda:True; b.d_gecmis_dogrula=lambda:True
    b.adres=lambda:'public_test'; b.jget=read; b.mutabakat=reconcile; b.log=log
    b.kesici_asilir=lambda *args:stop=='budget' and now[0]>=1010
    b.healthy=lambda *args: not (stop=='recorder' and now[0]>=1010)
    def exists(path):
        return path==b.STOP and ((stop=='operator' and now[0]>=1010)
                               or any(k=='G_HESAP_DUZELDI' for k,*_ in events))
    with (patch.object(b.time,'time',lambda:now[0]), patch.object(b.time,'sleep',sleep),
          patch.object(b.os.path,'exists',exists), patch('signal.signal'),
          patch.object(b.emir_iz,'aktif',SimpleNamespace(errors=0))):
        b.main()
    ended=next(v for k,v,*_ in events if k=='bitti')
    if stop:
        assert ended['sebep']=={'operator':'STOP','budget':'kesici','recorder':'kayit_yok'}[stop]
        assert not any(k=='G_HESAP_DUZELDI' for k,*_ in events)
    elif failure:
        assert ended['sebep']=='maruziyet_teyitsiz'
        assert not any(k=='G_HESAP_BEKLE' for k,*_ in events)
    else:
        wait=next(e for e in events if e[0]=='G_HESAP_BEKLE')
        recovered=next(e for e in events if e[0]=='G_HESAP_DUZELDI')
        assert wait[1]['bekle']==30 and not wait[3] and recovered[3]
        assert reads[4][0]-wait[2]>=30 and not reads[4][1]
        assert reads[5][0]-ledger[1]>=30 and not reads[5][1]
        assert len([k for k,*_ in events if k=='basladi'])==1
        assert ended['sebep']=='STOP' and b.st['emir']==0
    return b


def main():
    exercise()
    for stop in ('operator','budget','recorder'): exercise(stop=stop)
    for failure in ([{'broken':True}], [http(401)]*3, [http(403)]*3):
        exercise(failure=failure)
    for error in (http(408),http(429),http(503),URLError('timeout'),TimeoutError()):
        b=load(); b.LIVE=True; b.MUTABAKAT_OK=True; b.adres=lambda:'public_test'
        b.log=lambda *a,**kw:None
        with patch.object(b,'jget',side_effect=error),patch.object(b.time,'sleep'):
            assert b.acilis_maruziyeti() is None and b.MARUZIYET_GECICI and not b.MUTABAKAT_OK
        b.jget=lambda *args:[]
        assert b.acilis_maruziyeti()==0 and not b.MARUZIYET_GECICI and not b.MUTABAKAT_OK
    # The account gate can close while reserving or while POST is in flight.
    for when in ('before','during','already_closed'):
        b=load(); b.LIVE=True; b.MUTABAKAT_OK=when!='already_closed'
        b.log=lambda *a,**kw:None; b.healthy=lambda *a:True
        b.kesici_asilir=lambda *a:False; b.f_kalite=lambda *a:(True,'test')
        b.STOP='/no/test/stop'; calls=[]; cancels=[]
        w={'emir':[],'klip':5}; key=('btc',1000); b.pen={key:w}
        def save():
            if when=='before': b.MUTABAKAT_OK=False
        def post(rows):
            calls.append(rows); b.MUTABAKAT_OK=False
            return [(0,.4,'test-order','KABUL')]
        b.state_kaydet=save; b.koy_toplu=post
        b.kapat=lambda r,*args:cancels.append(r['oid']) or False
        with patch.object(b.emir_iz,'aktif',SimpleNamespace(errors=0)):
            b.d_koy(key,w,0,'up',.4,5,.41,.42,10)
        if when=='during':
            assert len(calls)==1 and cancels==['test-order']
            assert b.toplam_risk()==2  # Failed cancellation never releases reserve.
        else: assert not calls
        before=copy.deepcopy(w)
        assert b.d_koy(key,w,0,'up',.4,5,.41,.42,10) is None and w==before
    print('PASS: 429/408/429 pause, both account checks before recovery, STOP/budget/recorder gates, invalid data, POST races')


if __name__=='__main__':main()
