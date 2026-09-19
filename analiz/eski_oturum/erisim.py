#!/usr/bin/env python3
"""ERISIM OLCUMU — 0.99/0.97/0.95 bid seviyesine t=270'te girsek dolar miydik?

Fable'in bulgusu: sinyal mukemmel (kapi >=3bps -> 1.006 pencerede 0 hata),
arz var (130-350 pay/pencere), ama onde MEDYAN 24.000 PAY var.
Bu betik onu tape'ten dogrudan olcer:
   Q = t=270'te o fiyattaki bid seviyesinin boyu (bizden ONCE duranlar)
   V = [270,300] araliginda o fiyattan GECEN hacim
   dolar miyiz?  ->  V > Q  (FIFO)
Ayrica: seviye ne zaman aciliyor, kuyruk ne hizda eriyor.
"""
import json,gzip,glob,sys,collections,statistics as ist
HAR={int(a):b for a,b in json.load(open('/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad/asset_harita.json')).items()}
LOG='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
k=[json.loads(l) for l in open(LOG) if l.strip().startswith('{')]
KAZ={x['S']:x['kazanan'] for x in k if x['k']=='COZULDU'}
# ilgilendigimiz asset -> (S, oi)
A={}
for S,t in HAR.items():
    if S in KAZ:
        for oi in (0,1): A[t[oi]]=(S,oi)
print(f"izlenen asset: {len(A)} / {len(KAZ)} pencere",flush=True)
FIY=('0.99','0.97','0.95')
boy=collections.defaultdict(dict)      # asset -> {fiyat: [(t_rel, size)]}
islem=collections.defaultdict(list)    # asset -> [(t_rel, price, size)]
mid=collections.defaultdict(list)
for f in sorted(glob.glob('/home/taygun/Masaüstü/polymarket/data/tape/tape_20260918_*.jsonl.gz')):
    try:
        with gzip.open(f,'rt') as fh:
            for ln in fh:
                if 'price_change' not in ln and 'last_trade' not in ln: continue
                try: d=json.loads(ln)
                except Exception: continue
                p=d.get('p') or {}; ms=d.get('src')
                if ms is None: continue
                if d['k']=='pm:price_change':
                    for c in p.get('price_changes') or []:
                        a=c.get('asset_id')
                        if a not in A: continue
                        S,_=A[a]; tr=ms/1000.0-S
                        if not (200<=tr<=310): continue
                        if c.get('price') in FIY and c.get('side')=='BUY':
                            try: boy[a].setdefault(c['price'],[]).append((tr,float(c['size'])))
                            except Exception: pass
                        bb,ba=c.get('best_bid'),c.get('best_ask')
                        if bb and ba:
                            try: mid[a].append((tr,(float(bb)+float(ba))/2))
                            except Exception: pass
                elif d['k']=='pm:last_trade_price':
                    a=p.get('asset_id')
                    if a not in A: continue
                    S,_=A[a]; tr=ms/1000.0-S
                    if 200<=tr<=310:
                        try: islem[a].append((tr,float(p['price']),float(p['size'])))
                        except Exception: pass
    except EOFError: pass
print(f"boy serisi olan asset: {len(boy)} | islemi olan: {len(islem)}",flush=True)

def at(seri,t):
    en=None
    for tr,v in seri:
        if tr<=t: en=v
        else: break
    return en
print("\n### t=270'te KILITLI tarafa bid koysak (FIFO, onumuzdekiler once)")
print(f"  {'fiyat':>6} {'pencere':>8} {'Q medyan':>10} {'V medyan':>10} {'V>Q':>7} {'dolum%':>8}")
for fy in FIY:
    R=[]
    for a,(S,oi) in A.items():
        if a not in boy or fy not in boy[a]: continue
        m=at(mid[a],270) if a in mid else None
        if m is None or m<0.80: continue          # yalniz kilitli taraf
        Q=at(boy[a][fy],270)
        if Q is None: continue
        V=sum(sz for tr,px,sz in islem.get(a,[]) if 270<=tr<=300 and abs(px-float(fy))<1e-9)
        R.append((Q,V,V>Q))
    if not R: print(f"  {fy:>6}   veri yok"); continue
    print(f"  {fy:>6} {len(R):>8} {ist.median(x[0] for x in R):>10,.0f} "
          f"{ist.median(x[1] for x in R):>10,.0f} {sum(1 for x in R if x[2]):>7} "
          f"{100*sum(1 for x in R if x[2])/len(R):>7.1f}%")
print("\n### 0.99 seviyesi: kuyruk ne zaman ve ne hizda")
L=[]
for a,(S,oi) in A.items():
    if a not in boy or '0.99' not in boy[a]: continue
    m=at(mid[a],270) if a in mid else None
    if m is None or m<0.80: continue
    s=boy[a]['0.99']
    L.append((at(s,240),at(s,270),at(s,290),at(s,300)))
if L:
    for i,t in enumerate((240,270,290,300)):
        v=[x[i] for x in L if x[i] is not None]
        if v: print(f"  t={t}: kuyruk medyan {ist.median(v):>9,.0f} pay  (%25 {sorted(v)[len(v)//4]:,.0f} / %75 {sorted(v)[3*len(v)//4]:,.0f})  n={len(v)}")
