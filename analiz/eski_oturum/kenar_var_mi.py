#!/usr/bin/env python3
"""ASIL SORU: sinyal dogru ama PIYASA onu zaten fiyatliyor mu?

t=180'de marj>=8bp -> isabet %94.7. Piyasa o an kac diyor?
  fiyat < isabet  -> KENAR VAR
  fiyat = isabet  -> piyasa zaten biliyor

Varliklari gamma'siz etiketliyoruz: her market'in iki asset'i var; pencere
sonunda mid'i 1'e giden KAZANAN'dir. Chainlink'ten bagimsiz dogrulama.
"""
import json,gzip,glob,collections,statistics as ist
TAPE='/home/taygun/Masaüstü/polymarket/data/tape/tape_2026091[6-8]_*.jsonl.gz'
CL=collections.defaultdict(list); MID=collections.defaultdict(list); PAZ={}
for f in sorted(glob.glob(TAPE)):
    try:
        with gzip.open(f,'rt') as fh:
            for ln in fh:
                if '"k":"cl"' in ln:
                    try: d=json.loads(ln)
                    except Exception: continue
                    p=d.get('p') or {}
                    if p.get('w')==60: CL[int(d['src']//1000)].append(float(p['px']))
                elif '"price_change"' in ln:
                    try: d=json.loads(ln)
                    except Exception: continue
                    p=d.get('p') or {}; ms=d.get('src')
                    if ms is None: continue
                    mk=p.get('market')
                    for c in p.get('price_changes') or []:
                        bb,ba=c.get('best_bid'),c.get('best_ask')
                        if not bb or not ba: continue
                        a=c['asset_id']
                        if mk: PAZ.setdefault(mk,set()).add(a)
                        try: MID[a].append((ms,(float(bb)+float(ba))/2))
                        except Exception: pass
    except EOFError: pass
S60={s:ist.median(v) for s,v in CL.items()}
for a in MID: MID[a].sort()
print(f"TWAP60 sn {len(S60)} | asset {len(MID)} | pazar {len(PAZ)}",flush=True)
def cl_at(t):
    for d in range(4):
        if t-d in S60: return S60[t-d]
    return None
def mid_at(a,ms):
    L=MID.get(a)
    if not L: return None
    lo,hi=0,len(L)-1; en=None
    while lo<=hi:
        o=(lo+hi)//2
        if L[o][0]<=ms: en=L[o]; lo=o+1
        else: hi=o-1
    return en[1] if (en and ms-en[0]<=5000) else None
# pazar -> (S, asset_kazanan, asset_kaybeden): son mid'e gore
R=[]
for mk,assets in PAZ.items():
    if len(assets)!=2: continue
    a1,a2=sorted(assets)
    if not MID[a1] or not MID[a2]: continue
    son1=MID[a1][-1][1]; son2=MID[a2][-1][1]
    if abs(son1-son2)<0.5: continue           # net sonuc yok
    kaz,kyb=(a1,a2) if son1>son2 else (a2,a1)
    # pencere baslangici: ilk gozlem, 300'e yuvarla
    ilk=min(MID[a1][0][0],MID[a2][0][0])//1000
    S=int(ilk//300*300)
    b=cl_at(S)
    if b is None: continue
    for t in (150,180,210,240):
        v=cl_at(S+t)
        if v is None: continue
        marj=(v-b)/b*1e4
        if abs(marj)<8: continue
        # marj Up diyorsa hangi asset? Up'i bilmiyoruz -> tahmin edilen kazanan
        # = marj isaretine gore; ama asset->Up eslesmesi yok. Bunun yerine:
        # TAHMIN DOGRUYSA kazanan asset'in o andaki fiyatina bak.
        mk_=mid_at(kaz,(S+t)*1000)
        if mk_ is None: continue
        R.append((t,abs(marj),mk_))
print(f"\n### t aninda marj>=8bp iken KAZANAN tarafin fiyati ({len(R)} gozlem)")
print(f"  {'t':>5} {'n':>5} {'medyan fiyat':>13} {'%25':>7} {'%75':>7}")
for t in (150,180,210,240):
    x=sorted(m for tt,_,m in R if tt==t)
    if len(x)<30: continue
    print(f"  {t:>5} {len(x):>5} {ist.median(x):>13.3f} {x[len(x)//4]:>7.3f} {x[3*len(x)//4]:>7.3f}")
print("\n  KIYAS: t=180'de marj>=8bp -> isabet %94.7")
print("         kazanan tarafin medyan fiyati bunun ALTINDA ise kenar var")
