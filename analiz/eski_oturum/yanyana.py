#!/usr/bin/env python3
"""HER PENCEREDE BIZ vs BOSONA — kalici, es zamanli.
Kamu akisi ~300sn gecikmeli, o yuzden bosona'yi 2 pencere geriden okur."""
import json,urllib.request,time,sys,os
D='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5'
UA={'User-Agent':'python-urllib/3'}; BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def jget(u,t=15):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
    except Exception: return None
gor=set()
while True:
    try:
        k=[json.loads(l) for l in open(f'{D}/LOG_ab.jsonl') if l.strip().startswith('{')]
        for r in [x for x in k if x['k']=='COZULDU' and x['S']>=1789824900]:
            S=r['S']
            if S in gor: continue
            gor.add(S)
            q={0:0.0,1:0.0}; co={0:0.0,1:0.0}; det=[]
            for e in r['emirler']:
                if e['pay']>0:
                    q[e['oi']]+=e['pay']; co[e['oi']]+=e['pay']*e['p']
                    det.append(('U' if e['oi']==0 else 'D')+f"{e['pay']:.0f}@{e['p']:.2f}")
            kz='Up' if r['kazanan']==0 else 'Dn'
            tip='CIFT' if (q[0]>0 and q[1]>0) else ('TEK' if q[0]+q[1]>0 else 'BOS')
            print(f"\n=== {time.strftime('%H:%M',time.gmtime(S))}Z  kazanan={kz}")
            print(f"  BIZ    {tip:4} Up{q[0]:>4.0f}/Dn{q[1]:<4.0f} pnl={r['pnl']:+6.2f}  {' '.join(det[:9])}")
            Sb=S-600   # 2 pencere geri: akis gecikmesi
            tr=jget(f"https://data-api.polymarket.com/trades?user={BOS}&limit=500&takerOnly=false") or []
            w=sorted([x for x in tr if x.get('slug')==f'btc-updown-5m-{Sb}'],key=lambda y:y['timestamp'])
            if not w:
                print(f"  BOSONA (S-2={time.strftime('%H:%M',time.gmtime(Sb))}Z): veri yok")
            else:
                bq={'Up':0.0,'Down':0.0}; bm={'Up':0.0,'Down':0.0}; bd=[]
                for x in w:
                    bq[x['outcome']]+=x['size']; bm[x['outcome']]+=x['size']*x['price']
                    bd.append(f"t{x['timestamp']-Sb}:{'U' if x['outcome']=='Up' else 'D'}{x['size']:.0f}@{x['price']:.2f}")
                btip='CIFT' if (bq['Up']>0 and bq['Down']>0) else 'TEK'
                ou=bm['Up']/bq['Up'] if bq['Up'] else 0; od=bm['Down']/bq['Down'] if bq['Down'] else 0
                print(f"  BOSONA {btip:4} Up{bq['Up']:>4.0f}@{ou:.2f}/Dn{bq['Down']:<4.0f}@{od:.2f}  {' '.join(bd[:9])}")
                print(f"         (S-2={time.strftime('%H:%M',time.gmtime(Sb))}Z, akis gecikmesi)")
            sys.stdout.flush()
    except Exception as e:
        print("[hata]",str(e)[:70]); sys.stdout.flush()
    time.sleep(45)
