#!/usr/bin/env python3
"""DOGRU OLCUM: CHAINLINK marji + TAPE mid'i.

Onceki hata: marj Binance spot'tan hesaplandi, ama uzlasma Chainlink TWAP-60.
Ikisi ayrisinca piyasa dogru TWAP'i fiyatliyor, benim sinyalim yanlis oluyor
-> sahte +15 puan.

Bellek: yalnizca t_rel 165-200 araligindaki price_change'ler tutulur.
"""
import json,gzip,glob,collections,statistics as ist
HAR={int(a):b for a,b in json.load(open('/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad/asset_harita.json')).items()}
AS={}
for S,t in HAR.items():
    AS[t[0]]=(S,0); AS[t[1]]=(S,1)
CL=collections.defaultdict(list); MID=collections.defaultdict(list)
for f in sorted(glob.glob('/home/taygun/Masaüstü/polymarket/data/tape/tape_20260918_*.jsonl.gz')):
    try:
        with gzip.open(f,'rt') as fh:
            for ln in fh:
                if '"k":"cl"' in ln:
                    try: d=json.loads(ln)
                    except Exception: continue
                    p=d.get('p') or {}
                    if p.get('w')==60: CL[int(d['src']//1000)].append(float(p['px']))
                elif '"price_change"' in ln:
                    if '"best_bid"' not in ln: continue
                    try: d=json.loads(ln)
                    except Exception: continue
                    ms=d.get('src')
                    if ms is None: continue
                    for c in (d.get('p') or {}).get('price_changes') or []:
                        a=c.get('asset_id')
                        if a not in AS: continue
                        S,oi=AS[a]; tr=ms/1000.0-S
                        if not (165<=tr<=200): continue
                        bb,ba=c.get('best_bid'),c.get('best_ask')
                        if bb and ba:
                            try: MID[(S,oi)].append((tr,(float(bb)+float(ba))/2))
                            except Exception: pass
    except EOFError: pass
S60={s:ist.median(v) for s,v in CL.items()}
print(f"TWAP60 sn {len(S60)} | mid kaydi olan (pencere,taraf) {len(MID)}",flush=True)
def cl(t):
    for d in range(4):
        if t-d in S60: return S60[t-d]
    return None
# kazanan: TWAP60(S+300) vs TWAP60(S)
R=[]
for S in sorted(HAR):
    b=cl(S); e=cl(S+300); v=cl(S+180)
    if None in (b,e,v): continue
    marj=(v-b)/b*1e4
    kz=0 if e>=b else 1                  # 0=Up
    tah=0 if marj>=0 else 1
    if (S,tah) not in MID or not MID[(S,tah)]: continue
    m=min(MID[(S,tah)],key=lambda x:abs(x[0]-180))[1]
    R.append((abs(marj),m,1 if tah==kz else 0))
print(f"olculebilir pencere: {len(R)}\n")
for esik in (0,3,5,8):
    x=[(a,p,o) for a,p,o in R if a>=esik]
    if len(x)<25: continue
    isb=100*sum(o for _,_,o in x)/len(x); fy=100*ist.mean([p for _,p,_ in x])
    print(f"  marj>={esik}bp | n={len(x):>3} | isabet %{isb:.1f} | MID {fy:.1f} | KENAR {isb-fy:+.1f} puan")
print("\n  (MID = gercek alinabilir fiyat, tape'ten. API'nin verdigi son-islem degil.)")
