#!/usr/bin/env python3
"""KUCUK KLIPLI KAZANANLAR — bizim boyumuzda kim kazaniyor ve nasil?
Sinif: medyan dolum boyu <=15 pay, >=500 pencere, >=50k pay, 19 gun.
Sansi elemek icin GUN-kumeli onyukleme ve gun-bazli tutarlilik.
"""
import pandas as pd, json, random, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['w']=(df.outcome_idx==df.kaz).astype(float)
df['pnl']=df.shares*df.w-df.shares*df.price-df.fee
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
g=df.groupby('wallet').agg(pay=('shares','sum'),pnl=('pnl','sum'),pen=('start_ts','nunique'),
                           boy=('shares','median'),fiyat=('price','mean'),t=('t_rel_s','median'),
                           gun=('gun','nunique'))
g['kr']=100*g.pnl/g.pay
K=g[(g.boy<=15)&(g.pen>=500)&(g.pay>=50000)&(g.gun>=15)].sort_values('kr',ascending=False)
print(f"### KUCUK KLIPLI ISLETMECI (medyan boy<=15, >=500 pencere, >=15 gun): {len(K)}")
print(f"  artida: {(K.kr>0).sum()} / {len(K)}\n")
def gunluk(w):
    d=df[df.wallet==w]
    gg=d.groupby('gun').agg(p=('pnl','sum'),s=('shares','sum'))
    gl=list(zip(gg.p.values,gg.s.values))
    r=random.Random(7); out=[]
    for _ in range(4000):
        i=[r.randrange(len(gl)) for _ in range(len(gl))]
        num=sum(gl[j][0] for j in i); den=sum(gl[j][1] for j in i)
        if den>0: out.append(100*num/den)
    out.sort()
    arti=sum(1 for p,s in gl if p>0)
    return out[100],out[3900],arti,len(gl)
print(f"  {'cuzdan':>12} {'pay':>10} {'pen':>6} {'boy':>4} {'fiyat':>6} {'t':>5} {'kr/pay':>8} {'GA95':>18} {'arti gun':>9}")
for w,r in K.head(10).iterrows():
    lo,hi,ar,ng=gunluk(w)
    print(f"  {w[:12]:>12} {r.pay:>10,.0f} {r.pen:>6.0f} {r.boy:>4.0f} {r.fiyat:>6.3f} {r.t:>5.0f} "
          f"{r.kr:>+8.2f} {('[%+.2f,%+.2f]'%(lo,hi)):>18} {ar:>4}/{ng:<4}")
print(f"\n  ... en kotu 3:")
for w,r in K.tail(3).iterrows():
    lo,hi,ar,ng=gunluk(w)
    print(f"  {w[:12]:>12} {r.pay:>10,.0f} {r.pen:>6.0f} {r.boy:>4.0f} {r.fiyat:>6.3f} {r.t:>5.0f} "
          f"{r.kr:>+8.2f} {('[%+.2f,%+.2f]'%(lo,hi)):>18} {ar:>4}/{ng:<4}")
# EN IYI 3'un fiyat ve zaman profili
print("\n### EN IYI 3'UN PROFILI — fiyat bandina gore")
for w in K.head(3).index:
    d=df[df.wallet==w]
    print(f"\n  {w[:12]} ({d.shares.sum():,.0f} pay, {d.start_ts.nunique()} pencere)")
    for a,b in ((0,.1),(.1,.2),(.2,.3),(.3,.4),(.4,.5),(.5,.6),(.6,.8),(.8,1.01)):
        x=d[(d.price>=a)&(d.price<b)]
        if x.shares.sum()<2000: continue
        print(f"     {a:.2f}-{b:.2f}: {x.shares.sum():>8,.0f} pay (%{100*x.shares.sum()/d.shares.sum():4.1f}) "
              f"{100*x.pnl.sum()/x.shares.sum():>+7.2f} kr/pay  medyan t={x.t_rel_s.median():.0f}")
