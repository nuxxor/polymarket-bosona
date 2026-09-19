#!/usr/bin/env python3
"""MAKER KENARI FIYAT BOLGESINE GORE — 19 gun, zincir-kesin, TUM cuzdanlar.

Soru: derin bolgede (bizim kol A) maker kenari var mi, paraya yakinda var mi?
Olcu: pay-agirlikli kazanma orani EKSI pay-agirlikli odenen fiyat.
Adil piyasada fark 0 olmali. Fark = o bolgedeki maker'in yapisal kenari.
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['w']=(df.outcome_idx==df.kaz).astype(float)
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
print(f"maker BUY kaydi: {len(df):,} | pay {df.shares.sum():,.0f} | gun {df.gun.nunique()}")
kut=[(0.00,0.10),(0.10,0.20),(0.20,0.30),(0.30,0.40),(0.40,0.45),(0.45,0.50),
     (0.50,0.55),(0.55,0.60),(0.60,0.70),(0.70,0.80),(0.80,0.90),(0.90,1.00)]
def ga(d):
    g=d.groupby('gun').apply(lambda x:((x.shares*x.w).sum()-(x.shares*x.price).sum()-x.fee.sum(),x.shares.sum()),include_groups=False)
    gl=list(g)
    if len(gl)<5: return None,None
    r=random.Random(9)
    bp=sorted(100*sum(gl[r.randrange(len(gl))][0] for _ in gl)/sum(gl[r.randrange(len(gl))][1] for _ in gl) for _ in range(2000))
    return bp[50],bp[1950]
print(f"\n### TUM MAKER'LAR — kenar = kazanma% - odenen fiyat")
print(f"  {'fiyat':>11} {'pay':>13} {'oder':>7} {'kazanir':>8} {'KENAR':>8}  {'GA95':>18}")
for a,b in kut:
    d=df[(df.price>=a)&(df.price<b)]
    if len(d)<1000: continue
    pay=d.shares.sum(); od=100*(d.shares*d.price).sum()/pay; kz2=100*(d.shares*d.w).sum()/pay
    ken=kz2-od-100*d.fee.sum()/pay
    lo,hi=ga(d)
    print(f"  {a:.2f}-{b:.2f} {pay:>13,.0f} {od:>7.2f} {kz2:>8.2f} {ken:>+8.2f}  "
          f"{('[%+.2f,%+.2f]'%(lo,hi)) if lo is not None else '':>18}")
print(f"\n### BOSONA tek basina")
bo=df[df.wallet.str.lower()==BOS]
for a,b in kut:
    d=bo[(bo.price>=a)&(bo.price<b)]
    if len(d)<200: continue
    pay=d.shares.sum(); od=100*(d.shares*d.price).sum()/pay; kz2=100*(d.shares*d.w).sum()/pay
    print(f"  {a:.2f}-{b:.2f} {pay:>13,.0f} {od:>7.2f} {kz2:>8.2f} {kz2-od-100*d.fee.sum()/pay:>+8.2f}")
