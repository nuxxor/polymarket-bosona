#!/usr/bin/env python3
"""MARJ>=8bp ALTKUMESINDE piyasa kalibre mi?
Genel kalibrasyon -0.88 puan (iyi). Ama ben marj filtresi uygulamistim.
Eger o altkumede de kalibre ise, +15 puanim ARTEFAKT ve sebebini bulmaliyim.
"""
import json,urllib.request,time,collections,random,statistics as ist
UA={'User-Agent':'python-urllib/3'}
def jget(u,t=15,n=2):
    for i in range(n):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
        except Exception:
            if i==n-1: return None
            time.sleep(1)
SON=1789775100; ILK=SON-4*86400
K={}; t=ILK
while t<SON:
    d=jget(f"https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&startTime={t*1000}&limit=1500")
    if not d: break
    for c in d: K[int(c[0]//1000)]=float(c[4])
    t=int(d[-1][0]//1000)+60; time.sleep(0.12)
def px(ts):
    m=ts//60*60
    for d in range(4):
        if m-d*60 in K: return K[m-d*60]
    return None
aday=[]
for S in range(ILK//300*300,SON,300):
    b=px(S); v=px(S+180)
    if None in (b,v): continue
    marj=(v-b)/b*1e4
    if abs(marj)>=8: aday.append((S,marj))
random.Random(4).shuffle(aday); aday=aday[:420]
print(f"marj>=8bp aday: {len(aday)}",flush=True)
kova=collections.defaultdict(lambda:[0,0]); R=[]
for i,(S,marj) in enumerate(aday):
    g=jget(f"https://gamma-api.polymarket.com/events?slug=btc-updown-5m-{S}",10)
    if not g: continue
    try:
        mk=g[0]['markets'][0]; tok=json.loads(mk['clobTokenIds'])
        pr=mk.get('outcomePrices'); son=json.loads(pr) if isinstance(pr,str) else pr
        gercek=0 if float(son[0])>0.5 else 1
    except Exception: continue
    tahmin=0 if marj>=0 else 1
    h=jget(f"https://clob.polymarket.com/prices-history?market={tok[tahmin]}&startTs={S+150}&endTs={S+215}&fidelity=1",10)
    hh=(h.get('history') if isinstance(h,dict) else h) or []
    if not hh: continue
    y=min(hh,key=lambda x:abs(x['t']-(S+180)))
    if abs(y['t']-(S+180))>70: continue
    p=float(y['p']); kaz=1 if tahmin==gercek else 0
    kova[min(int(p*10),9)][0]+=1; kova[min(int(p*10),9)][1]+=kaz
    R.append((p,kaz))
    time.sleep(0.08)
print(f"\n### MARJ>=8bp ALTKUMESI — {len(R)} pencere, marjin gosterdigi taraf")
print(f"  {'fiyat kovasi':>14} {'n':>5} {'gercek kazanma':>15} {'fark':>7}")
tf=0.0;tn=0
for kv in range(10):
    c,w=kova[kv]
    if c<8: continue
    orta=(kv+0.5)/10
    print(f"  {kv/10:.1f}-{(kv+1)/10:.1f}      {c:>5} {100*w/c:>14.1f}% {100*w/c-100*orta:>+7.1f}")
    tf+=(w/c-orta)*c; tn+=c
if tn: print(f"\n  AGIRLIKLI SAPMA: {100*tf/tn:+.2f} puan")
if R:
    print(f"  ort fiyat {ist.mean([p for p,_ in R]):.3f} | ort kazanma %{100*ist.mean([k for _,k in R]):.1f}")
    print(f"  -> ham fark {100*ist.mean([k for _,k in R])-100*ist.mean([p for p,_ in R]):+.1f} puan")
