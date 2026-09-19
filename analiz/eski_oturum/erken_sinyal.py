#!/usr/bin/env python3
"""TWAP-60 SINYALI ERKEN SAATLERDE NE KADAR DOGRU?

Uzlasma kurali (Fable dogruladi, %99,2 yeniden uretiyor):
    Up  <=>  TWAP60(S+300) >= TWAP60(S)
t anindaki tahmin: marj = TWAP60(t) - TWAP60(S), isareti tahmin.
SIZINTI YOK: t anindaki deger yalnizca t'ye kadarki veriyi tasir.

Cikti: her (t, marj esigi) icin ISABET ve KAPSAM.
Ekonomik soru: t=180'de %99 isabet varsa ve fiyat 0,80 ise, 19 puan kenar demek.
"""
import json,gzip,glob,collections,statistics as ist
CL=collections.defaultdict(list)   # sn -> px  (w=60)
for f in sorted(glob.glob('/home/taygun/Masaüstü/polymarket/data/tape/tape_2026091[3-8]_*.jsonl.gz')):
    try:
        with gzip.open(f,'rt') as fh:
            for ln in fh:
                if '"k":"cl"' not in ln: continue
                try: d=json.loads(ln)
                except Exception: continue
                p=d.get('p') or {}
                if p.get('w')!=60: continue
                s=int(d['src']//1000)
                CL[s].append(float(p['px']))
    except EOFError: pass
S60={s:ist.median(v) for s,v in CL.items()}
print(f"TWAP60 saniye kaydi: {len(S60)}",flush=True)
if not S60: raise SystemExit("veri yok")
lo,hi=min(S60),max(S60)
def at(t):
    for d in range(0,4):
        if t-d in S60: return S60[t-d]
    return None
pencereler=[]
for S in range((lo//300+1)*300,(hi//300)*300,300):
    b=at(S); e=at(S+300)
    if b is None or e is None: continue
    kaz=1 if e>=b else 0     # 1=Up
    sat={}
    for t in (120,150,180,200,210,240,270):
        v=at(S+t)
        sat[t]=None if v is None else (v-b)/b*1e4   # baz puan
    if all(sat[t] is not None for t in sat): pencereler.append((S,kaz,sat))
print(f"tam pencere: {len(pencereler)}\n")
print("### TWAP60 MARJININ ISABETI — sizintisiz, %s pencere" % len(pencereler))
print(f"  {'t':>5} {'esik':>7} {'kapsam':>8} {'isabet':>8} {'hata':>6}")
for t in (120,150,180,200,210,240,270):
    for esik in (0,3,5,8,12,20):
        sec=[(k,s[t]) for S,k,s in pencereler if abs(s[t])>=esik]
        if len(sec)<50: continue
        dog=sum(1 for k,m in sec if (m>=0)==(k==1))
        print(f"  {t:>5} {esik:>5}bp {100*len(sec)/len(pencereler):>7.1f}% {100*dog/len(sec):>7.2f}% {len(sec)-dog:>6}")
    print()
