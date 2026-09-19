#!/usr/bin/env python3
"""SALDIRI 1: Boy gradyani PENCERE-ESIT agirlikla da duruyor mu?
   SALDIRI 2: Kac maker artida, ve bosona onlarin neresinde?
19 gun zincir-kesin defter. Bugun ogrendigim ders: PAY-agirlikli sayilar
hacmin yogunlastigi pencerelerden gelir; katilimcinin yasadigi PENCERE-ESIT'tir.
"""
import pandas as pd, json, random, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['pnl']=df.shares*(df.outcome_idx==df.kaz)-df.shares*df.price-df.fee
print(f"maker BUY, sonucu bilinen: {len(df):,} dolum / {df.shares.sum():,.0f} pay / {df.start_ts.nunique()} pencere\n")

print("### SALDIRI 1 — boy gradyani, IKI agirlikla (0.20-0.40 bandi)")
b=df[(df.price>=0.20)&(df.price<0.40)]
print(f"  {'dolum boyu':>14} {'pay':>12} {'PAY-agirlikli':>14} {'PENCERE-esit':>13} {'pencere':>8}")
for lo,hi,ad in ((0,10,'1-9'),(10,25,'10-24'),(25,50,'25-49'),(50,100,'50-99'),
                 (100,250,'100-249'),(250,10**9,'250+')):
    d=b[(b.shares>=lo)&(b.shares<hi)]
    if len(d)<500: continue
    pz=d.groupby('start_ts').agg(p=('pnl','sum'),s=('shares','sum'))
    pz['kr']=100*pz.p/pz.s
    print(f"  {ad:>14} {d.shares.sum():>12,.0f} {100*d.pnl.sum()/d.shares.sum():>+14.2f} {pz.kr.mean():>+13.2f} {len(pz):>8}")

print("\n### SALDIRI 2 — kac cuzdan artida? (>=50.000 pay, 19 gun)")
g=df.groupby('wallet').agg(pay=('shares','sum'),pnl=('pnl','sum'),
                           dolum=('shares','size'),pen=('start_ts','nunique'),
                           fiyat=('price','mean'),t=('t_rel_s','median'),
                           boy=('shares','median'))
g=g[g.pay>=50000].copy()
g['kr']=100*g.pnl/g.pay
g=g.sort_values('kr',ascending=False)
print(f"  50k+ paylik cuzdan: {len(g)} | artida: {(g.kr>0).sum()} (%{100*(g.kr>0).mean():.0f})")
print(f"  toplam pay: {g.pay.sum():,.0f} | toplam PnL: ${g.pnl.sum():,.0f}")
print(f"\n  EN IYI 12:")
print(f"  {'cuzdan':>10} {'pay':>12} {'kr/pay':>8} {'pencere':>8} {'ort fiyat':>10} {'medyan boy':>11} {'medyan t':>9}")
for w,r in g.head(12).iterrows():
    et='<< BOSONA' if w.lower()==BOS else ''
    print(f"  {w[:10]:>10} {r.pay:>12,.0f} {r.kr:>+8.2f} {r.pen:>8.0f} {r.fiyat:>10.3f} {r.boy:>11.0f} {r.t:>9.0f} {et}")
print(f"\n  bosona sirasi: {list(g.index.str.lower()).index(BOS)+1} / {len(g)}")
print(f"\n  EN KOTU 5:")
for w,r in g.tail(5).iterrows():
    print(f"  {w[:10]:>10} {r.pay:>12,.0f} {r.kr:>+8.2f} {r.pen:>8.0f} {r.fiyat:>10.3f} {r.boy:>11.0f} {r.t:>9.0f}")
