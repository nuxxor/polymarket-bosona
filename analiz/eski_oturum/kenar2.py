#!/usr/bin/env python3
"""PIYASA MARJI FIYATLIYOR MU? — tape taramadan, dogrudan API ile.

t=180'de |marj|>=8bp -> isabet %94.7 (1391 pencere ile olculdu).
Soru: o anda marjin gosterdigi tarafin PIYASA FIYATI kac?
  fiyat < 0.947 -> KENAR VAR
"""
import json,urllib.request,time,statistics as ist
UA={'User-Agent':'python-urllib/3'}
def jget(u,t=20,n=3):
    for i in range(n):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
        except Exception:
            if i==n-1: return None
            time.sleep(1.5*(i+1))
# 1) Binance marj
SON=1789775100; ILK=SON-4*86400
K={}
t=ILK
while t<SON:
    d=jget(f"https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&startTime={t*1000}&limit=1500")
    if not d: break
    for c in d: K[int(c[0]//1000)]=float(c[4])
    t=int(d[-1][0]//1000)+60; time.sleep(0.15)
print(f"kline dakika: {len(K)}",flush=True)
def px(ts):
    m=ts//60*60
    for d in range(4):
        if m-d*60 in K: return K[m-d*60]
    return None
# 2) marj>=8bp olan pencereleri sec
aday=[]
for S in range(ILK//300*300,SON,300):
    b=px(S); v=px(S+180); e=px(S+300)
    if None in (b,v,e): continue
    marj=(v-b)/b*1e4
    if abs(marj)<8: continue
    aday.append((S,marj,1 if e>=b else 0))   # 1=Up kazandi (yaklasik)
print(f"marj>=8bp pencere: {len(aday)}",flush=True)
import random as _r; _r.Random(4).shuffle(aday); aday=aday[:420]
# 3) gamma'dan token, sonra fiyat
R=[]
for i,(S,marj,kz) in enumerate(aday):
    g=jget(f"https://gamma-api.polymarket.com/events?slug=btc-updown-5m-{S}",12)
    if not g: continue
    try:
        mk=g[0]['markets'][0]
        tok=json.loads(mk['clobTokenIds'])
        pr=mk.get('outcomePrices')
        son=json.loads(pr) if isinstance(pr,str) else pr
        gercek = 0 if float(son[0])>0.5 else 1      # 0=Up kazandi
    except Exception: continue
    tahmin = 0 if marj>=0 else 1                    # marjin gosterdigi taraf
    h=jget(f"https://clob.polymarket.com/prices-history?market={tok[tahmin]}&startTs={S+150}&endTs={S+210}&fidelity=1",12)
    hh=(h.get('history') if isinstance(h,dict) else h) or []
    if not hh: continue
    yakin=min(hh,key=lambda x:abs(x['t']-(S+180)))
    if abs(yakin['t']-(S+180))>70: continue
    R.append((marj,yakin['p'],1 if tahmin==gercek else 0))
    if (i+1)%60==0: print(f"  {i+1}/{len(aday)} ... gecerli {len(R)}",flush=True)
    time.sleep(0.1)
print(f"\n### SONUC — {len(R)} pencere, t=180, |marj|>=8bp")
if R:
    fy=[p for _,p,_ in R]; ok=sum(o for _,_,o in R)
    print(f"  marjin gosterdigi tarafin ISABETI : %{100*ok/len(R):.1f}")
    print(f"  o tarafin PIYASA FIYATI  medyan   : {ist.median(fy):.3f}")
    print(f"                           ortalama : {ist.mean(fy):.3f}")
    print(f"                           %25/%75  : {sorted(fy)[len(fy)//4]:.3f} / {sorted(fy)[3*len(fy)//4]:.3f}")
    print(f"\n  KENAR = isabet - fiyat = {100*ok/len(R) - 100*ist.mean(fy):+.1f} puan")
    for lo,hi in ((8,12),(12,20),(20,999)):
        x=[(m,p,o) for m,p,o in R if lo<=abs(m)<hi]
        if len(x)<20: continue
        print(f"    marj {lo}-{hi}bp: n={len(x):>3} isabet %{100*sum(o for _,_,o in x)/len(x):.1f} "
              f"fiyat {ist.mean([p for _,p,_ in x]):.3f} -> kenar {100*sum(o for _,_,o in x)/len(x)-100*ist.mean([p for _,p,_ in x]):+.1f}")
