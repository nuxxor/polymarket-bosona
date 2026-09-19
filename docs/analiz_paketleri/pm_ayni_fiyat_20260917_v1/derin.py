#!/usr/bin/env python3
"""bosona TAM gecmis (offset ~14k'ya kadar) + kazanan etiketleri.
Amac: taker kenarinin 34 saatlik bir dalgalanma mi yoksa kalici mi oldugunu olcmek."""
import json,urllib.request,os,time,concurrent.futures as cf
UA={'User-Agent':'Mozilla/5.0'}
A='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def g(u,t=40):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
def cek(to,ad):
    if os.path.exists(ad): return json.load(open(ad))
    tr=[];off=0
    while off<14500:
        try: b=g(f"https://data-api.polymarket.com/trades?user={A}&limit=500&offset={off}&takerOnly={to}")
        except Exception: break
        if not b: break
        tr+=b; off+=len(b)
        if len(b)<500: break
    json.dump(tr,open(ad,'w')); return tr
tum=cek('false','bos_tum_derin.json'); tak=cek('true','bos_tak_derin.json')
ts=lambda L:[int(x.get('timestamp') or 0) for x in L]
print(f"tum {len(tum)} ({time.strftime('%m-%d',time.gmtime(min(ts(tum))))} -> {time.strftime('%m-%d',time.gmtime(max(ts(tum))))})")
print(f"tak {len(tak)} ({time.strftime('%m-%d',time.gmtime(min(ts(tak))))} -> {time.strftime('%m-%d',time.gmtime(max(ts(tak))))})")
sl=sorted({x['slug'] for x in tum if '-updown-5m-' in (x.get('slug') or '')})
C=json.load(open('bos_kaz_derin.json')) if os.path.exists('bos_kaz_derin.json') else {}
todo=[s for s in sl if C.get(s) is None]
print(f"pencere {len(sl)}, etiket eksik {len(todo)}")
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
        for i,(s,k) in enumerate(ex.map(kaz,todo)):
            C[s]=k
            if i%400==0: print('  ',i,flush=True)
    json.dump(C,open('bos_kaz_derin.json','w'))
print(f"etiketli: {sum(1 for v in C.values() if v is not None)}/{len(C)}")
