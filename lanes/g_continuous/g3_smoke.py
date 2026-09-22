"""Real public book, dry engine only. No account auth, actual orders or fill simulation."""
import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
from unittest.mock import patch

import g3_operator as deploy


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=360);args=parser.parse_args()
    assert 60<=args.seconds<=900
    source,old,new=deploy.package();deploy.verify(deploy.TARGET,old,new)
    output=deploy.HERE/'validation';output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.g3-public-',dir=output) as directory:
        root=Path(directory)
        for name in old:
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(deploy.TARGET/name,dest)
        (root/'ab.py').write_bytes(source);(root/'G_RELEASE.json').write_text(json.dumps(new))
        sys.path.insert(0,str(root))
        spec=importlib.util.spec_from_file_location('g3_public_dry',root/'ab.py');b=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(root/'ab.py'),'--lane-g']):spec.loader.exec_module(b)
        assert not b.LIVE and b.client is None
        b.LOG=str(output/'G3_smoke_bot.jsonl');b.STATE=str(root/'STATE_dry.json')
        journal=b.emir_iz.baslat(output/'G3_smoke_telemetry.jsonl','DRY_PUBLIC_ONLY',root/'ab.py')
        events=[];b.log=lambda event,**fields:events.append({'k':event,**fields})
        posted=[];canceled=[];post=b.koy_toplu;cancel=b.iptal
        def dry_post(orders):
            assert not b.LIVE;result=post(orders)
            assert all(r[2].startswith('KURU-') for r in result)
            posted.extend(result);return result
        def dry_cancel(oid):
            assert not b.LIVE and oid.startswith('KURU-');canceled.append(oid);return cancel(oid)
        b.koy_toplu=dry_post;b.iptal=dry_cancel;b.MUTABAKAT_OK=True
        deadline=time.monotonic()+args.seconds;windows=[]
        def stop():b.DURDUR=True
        timer=threading.Timer(args.seconds,stop);timer.start()
        try:
            while time.monotonic()<deadline and not b.DURDUR:
                S=int(time.time())//300*300
                market=[m for e in b.jget(b.GAMMA.format('btc',S)) for m in e.get('markets',[])
                        if m.get('slug')==f'btc-updown-5m-{S}'][0]
                tokens=json.loads(market['clobTokenIds']);w={'emir':[],'klip':5,'kol':'G','cozuldu':False}
                b.pen={('btc',S):w};windows.append({'S':S,'arm':b.g3_arm(S)})
                b.taze_izle(('btc',S),w,{0:tokens[0],1:tokens[1]})
        finally:
            b.DURDUR=True;timer.cancel()
            for t in threading.enumerate():
                if t.name.startswith('taze-ws-'):t.join(5)
            journal.yaz('session_end');b.emir_iz.aktif=None
        (output/'G3_smoke_bot.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
        rows=[json.loads(line) for line in (output/'G3_smoke_telemetry.jsonl').read_text().splitlines()]
        rows=[r for r in rows if r['session']==journal.session]
        quotes=[r for r in rows if r['event']=='g3_quote'];results=[r for r in rows if r['event']=='g3_cancel_result']
        valid=[]
        for q in quotes:
            d=q['decision'];book=q['book']
            valid.append(book is not None and book['mono_ns']<=d['mono_ns']<=q['mono_ns']
                         and book['utc_ns']<=d['utc_ns']<=q['utc_ns'] and -100<=d['utc_ns']/1e6-book['source_ms']<=3000
                         and all(p['oid'].startswith('KURU-') and p['durum']=='acik' and p['boy']==5 and p['pay']==0 for p in q['pending']))
        assert quotes and all(valid) and not journal.errors
        assert all(sum(r.get('pay',0) for r in w['emir'])==0 for w in b.pen.values())
        assert not any(e['k']=='G_KARAR_HATA' for e in events)
        for q in quotes:assert q['flags']['buffer_cancel']==(q['flags']['buffer_signal'] and q['arm']=='G3')
        assert results and all(r['confirmed'] and r['status']=='kapali' and r['matched']==0 for r in results)
        proof={'status':'PASS','scope':'REAL_PUBLIC_FEED_DRY_ORDERS_ONLY','seconds':args.seconds,'windows':windows,
               'quotes':len(quotes),'complete_quote_records':sum(valid),'dry_posts':len(posted),'dry_cancels':len(canceled),
               'buffer_signals':sum(q['flags']['buffer_signal'] for q in quotes),
               'treatment_cancels':sum(q['flags']['buffer_cancel'] for q in quotes),
               'observed_cancel_results':len(results),'real_orders':0,'real_fills':0,'economic_result':None,
               'source_sha256':sha256(source).hexdigest(),'recording_errors':journal.errors,
               'ws_reconnections':sum(e['k']=='taze_ws_hata' for e in events)}
        (output/'G3_smoke.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)


if __name__=='__main__':main()
