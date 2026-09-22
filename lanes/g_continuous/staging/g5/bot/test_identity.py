"""Real 999 incident replay and fail-closed identity regressions; all IO mocked."""
import copy
import json
from pathlib import Path
from unittest.mock import patch

from test_g import load


def reject(call):
    try:call()
    except (ValueError,KeyError,TypeError):return
    raise AssertionError('ambiguous identity accepted')


def main():
    fixture=json.loads(Path(__file__).with_name('identity_case.json').read_text())
    market=fixture['market'];rows=fixture['trades'];slug=market['slug'];S=int(slug.rsplit('-',1)[1])
    b=load();events=[];requests=[]
    b.log=lambda event,**kw:events.append((event,kw))
    b.LIVE=True;b.adres=lambda:'public_wallet';b.pen={}
    b.st.update(pencereler=[['btc',S]],gorulen_tx=[],gorulen_islem=[],gorulen_cokluk={},mutabakat_pencere=0)
    b.resmi_sonuc=lambda *args:0
    def read(url,*args):
        requests.append(url)
        return copy.deepcopy(rows) if '/trades?' in url else [{'markets':[market]}]
    b.jget=read
    original=copy.deepcopy(rows)
    with patch.object(b.time,'sleep'):
        assert abs(b.mutabakat()+2.3)<1e-9 and b.MUTABAKAT_OK
        assert rows==original and sum(b.st['gorulen_cokluk'].values())==5
        assert sum('gamma' in url for url in requests)==1
        before=copy.deepcopy(b.st)
        rows=[dict(r,outcomeIndex=json.loads(market['clobTokenIds']).index(r['asset'])) for r in rows]
        assert abs(b.mutabakat()+2.3)<1e-9 and b.st['gorulen_cokluk']==before['gorulen_cokluk']
        assert b.st['gorulen_tx']==before['gorulen_tx'] and b.st['gorulen_islem']==before['gorulen_islem']
        rows[0]['outcomeIndex']=1-rows[0]['outcomeIndex']
        assert b.mutabakat() is None and not b.MUTABAKAT_OK and b.st['pnl']==before['pnl']
    raw=next(r for r in original if r['outcomeIndex']==999)
    for changes in ({'asset':'123'},{'conditionId':'0x'+'0'*64},{'outcomeIndex':1},
                    {'outcomeIndex':True},{'outcomeIndex':None},{'outcomeIndex':0.9}):
        reject(lambda changes=changes:b.islem_yonu({**raw,**changes}))
    for changes in ({'slug':'other'},{'outcomes':'["Down","Up"]'},
                    {'clobTokenIds':'["1","1"]'},{'conditionId':'x'}):
        reject(lambda changes=changes:b.islem_piyasa_kimligi({**market,**changes},slug))
    b.ISLEM_PIYASA.clear();b.jget=lambda *args:[{'markets':[market,market]}]
    reject(lambda:b.islem_yonu(raw))
    b.jget=lambda *args:[{'markets':[]}]
    reject(lambda:b.islem_yonu(raw))
    b.ISLEM_PIYASA[slug]=b.islem_piyasa_kimligi(market,slug)
    repeated=[b.islem_yonu(raw),b.islem_yonu(raw)]
    import g_policy
    ledger=[];g_policy.append_page(ledger,repeated,b.islem_anahtari)
    assert len(ledger)==2
    reject(lambda:g_policy.append_page(ledger,repeated,b.islem_anahtari))
    assert any(k=='mutabakat_YON_DUZELT' for k,_ in events)
    print('PASS: actual 999 incident, canonical keys across recovery, cash/multiset, conflicting identities fail closed')


if __name__=='__main__':main()
