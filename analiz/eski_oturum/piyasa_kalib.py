#!/usr/bin/env python3
"""EN KESIN TEST: piyasa fiyatinin KENDI kalibrasyonu.
Marji hic kullanma. t=180'deki fiyat 0.75 ise, gercekten %75 mi kaziniyor?
Kalibre ise -> kenar yok, benim +15 puanim artefakt.
Kalibre degilse -> ya piyasa bozuk ya benim fiyat verim yanlis.
"""
import json,urllib.request,time,collections,random
UA={'User-Agent':'python-urllib/3'}
def jget(u,t=15,n=2):
    for i in range(n):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
        except Exception:
            if i==n-1: return None
            time.sleep(1)
SON=1789775100; ILK=SON-4*86400
pencereler=list(range(ILK//300*300,SON,300))
random.Random(8).shuffle(pencereler); pencereler=pencereler[:500]
kova=collections.defaultdict(lambda:[0,0])
n=0
for S in pencereler:
    g=jget(f"https://gamma-api.polymarket.com/events?slug=btc-updown-5m-{S}",10)
    if not g: continue
    try:
        mk=g[0]['markets'][0]; tok=json.loads(mk['clobTokenIds'])
        pr=mk.get('outcomePrices'); son=json.loads(pr) if isinstance(pr,str) else pr
        if son is None: continue
        kazanan=0 if float(son[0])>0.5 else 1
    except Exception: continue
    h=jget(f"https://clob.polymarket.com/prices-history?market={tok[0]}&startTs={S+150}&endTs={S+215}&fidelity=1",10)
    hh=(h.get('history') if isinstance(h,dict) else h) or []
    if not hh: continue
    y=min(hh,key=lambda x:abs(x['t']-(S+180)))
    if abs(y['t']-(S+180))>70: continue
    p0=float(y['p'])                     # token 0 (Up) fiyati
    kv=min(int(p0*10),9)
    kova[kv][0]+=1; kova[kv][1]+= (1 if kazanan==0 else 0)
    n+=1
    if n%100==0: print(f"  {n} pencere...",flush=True)
    time.sleep(0.08)
print(f"\n### PIYASA FIYATININ KALIBRASYONU — t=180, {n} pencere")
print(f"  {'fiyat kovasi':>14} {'n':>5} {'gercek kazanma':>15} {'fark':>7}")
tf=0.0;tn=0
for kv in range(10):
    c,w=kova[kv]
    if c<10: continue
    orta=(kv+0.5)/10
    print(f"  {kv/10:.1f}-{(kv+1)/10:.1f}      {c:>5} {100*w/c:>14.1f}% {100*w/c-100*orta:>+7.1f}")
    tf+=(w/c-orta)*c; tn+=c
if tn: print(f"\n  AGIRLIKLI ORTALAMA SAPMA: {100*tf/tn:+.2f} puan  (0 ise piyasa kalibre)")
