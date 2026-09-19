#!/usr/bin/env python3
import json,urllib.request,collections,os,concurrent.futures as cf,time
UA={'User-Agent':'Mozilla/5.0'}
A='0x32ed2e546b187ca15e2841edc82b22c713cf8ec3'
def g(u,t=30):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
def cek(to,n=6000):
    tr=[];off=0
    while off<n:
        b=g(f"https://data-api.polymarket.com/trades?user={A}&limit=500&offset={off}&takerOnly={to}")
        if not b: break
        tr+=b; off+=len(b)
        if len(b)<500: break
    return tr
if os.path.exists('mo_tum.json'):
    tum=json.load(open('mo_tum.json')); tak=json.load(open('mo_tak.json'))
else:
    tum=cek('false'); tak=cek('true')
    json.dump(tum,open('mo_tum.json','w')); json.dump(tak,open('mo_tak.json','w'))
sl=sorted({x['slug'] for x in tum if '-updown-5m-' in (x.get('slug') or '')})
C=json.load(open('mo_kaz.json')) if os.path.exists('mo_kaz.json') else {}
todo=[s for s in sl if C.get(s) is None]
def kaz(s):
    for u in (f"https://gamma-api.polymarket.com/events?slug={s}", f"https://gamma-api.polymarket.com/markets?slug={s}"):
        try:
            d=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read())
            ms=[m for e in d for m in e.get('markets',[])] if 'events?' in u else d
            for m in ms:
                if m.get('slug')!=s: continue
                op=[float(z) for z in json.loads(m.get('outcomePrices') or '[]')]
                if op==[1.0,0.0]: return s,0
                if op==[0.0,1.0]: return s,1
        except Exception: pass
    return s,None
if todo:
    with cf.ThreadPoolExecutor(12) as ex:
        for s,k in ex.map(kaz,todo): C[s]=k
    json.dump(C,open('mo_kaz.json','w'))
print(f"mo-money: {len(sl)} pencere, etiketli {sum(1 for v in C.values() if v is not None)}")
ana=lambda x:(x.get('transactionHash'),str(x.get('outcomeIndex')),x.get('side'),str(x.get('size')))
takset={ana(x) for x in tak}
ucret=lambda p: 0.07*p*(1-p)
g2=collections.defaultdict(lambda:[0.0,0.0,0.0]); tp=0.0; tot=0.0
for x in tum:
    s=x.get('slug') or ''
    if '-updown-5m-' not in s or C.get(s) is None: continue
    oi=int(x['outcomeIndex']); p=float(x['price']); q=float(x['size']); kz=C[s]
    rol='maker' if ana(x) not in takset else 'taker'
    Y=1.0 if oi==kz else 0.0
    brut=q*(Y-p) if x.get('side')=='BUY' else q*(p-Y)
    net=brut-(q*ucret(p) if rol=='taker' else 0.0)
    a=g2[(x.get('side'),rol)]; a[0]+=q; a[1]+=net; a[2]+= q if oi==kz else 0.0
    tp+=q; tot+=net
print(f"\n{'yon/rol':>14} {'pay':>10} {'NET PnL $':>11} {'kr/pay':>9} {'hacim%':>8} {'kazanma%':>9}")
print("-"*66)
for k in sorted(g2):
    a=g2[k]
    print(f"{k[0]+'/'+k[1]:>14} {a[0]:10,.0f} {a[1]:+11.2f} {100*a[1]/max(a[0],1):+9.2f} {100*a[0]/tp:7.1f}% {100*a[2]/max(a[0],1):8.1f}%")
print("-"*66)
print(f"{'TOPLAM':>14} {tp:10,.0f} {tot:+11.2f} {100*tot/tp:+9.2f}")
mk=g2[('BUY','maker')]; tk=g2[('BUY','taker')]
if tot: print(f"\n=> maker alim: %{100*mk[0]/tp:.1f} hacim -> karin %{100*mk[1]/tot:.1f}'i")
if tot: print(f"=> TAKER alim: %{100*tk[0]/tp:.1f} hacim -> karin %{100*tk[1]/tot:.1f}'i")
