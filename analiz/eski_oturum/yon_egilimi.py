#!/usr/bin/env python3
"""YON EGILIMI: dengesiz pozisyonun AGIR TARAFI, fiyatinin ima ettiginden
daha sik kaziniyor mu? Hafizadaki "kar tek tarafli yon envanterinden" iddiasinin
19 gunluk zincir verisiyle sinanmasi.

Olcu: agir tarafin pay-agirlikli kazanma orani EKSI pay-agirlikli odenen fiyat.
Adil ise 0. Pozitifse gercek yon kenari var.
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee'])
df=df[df.side.str.upper()=='BUY']
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
def analiz(d,ad):
    g=d.groupby(['gun','start_ts','outcome_idx']).agg(pay=('shares','sum'),mal=('price','sum')).reset_index()
    g['mal']=d.groupby(['gun','start_ts','outcome_idx']).apply(lambda x:(x.shares*x.price).sum(),include_groups=False).values
    p=g.pivot_table(index=['gun','start_ts'],columns='outcome_idx',values=['pay','mal'],fill_value=0.0)
    R=[]
    for (gun,S),r in p.iterrows():
        q0,q1=r[('pay',0)] if ('pay',0) in r else 0.0, r[('pay',1)] if ('pay',1) in r else 0.0
        m0,m1=r[('mal',0)] if ('mal',0) in r else 0.0, r[('mal',1)] if ('mal',1) in r else 0.0
        if q0+q1<=0: continue
        ag=0 if q0>q1 else 1
        essiz=abs(q0-q1)
        if essiz<1: continue
        ort=(m0/q0 if ag==0 and q0>0 else (m1/q1 if q1>0 else 0))
        R.append((gun,essiz,ort,1.0 if ag==kz[S] else 0.0,abs(q0-q1)/(q0+q1)))
    if len(R)<100: print(f"  {ad}: yetersiz"); return
    dfr=pd.DataFrame(R,columns=['gun','essiz','fiyat','kazandi','dengesizlik'])
    pay=dfr.essiz.sum()
    od=100*(dfr.essiz*dfr.fiyat).sum()/pay
    kzo=100*(dfr.essiz*dfr.kazandi).sum()/pay
    gl=[( (x.essiz*x.kazandi).sum()-(x.essiz*x.fiyat).sum(), x.essiz.sum()) for _,x in dfr.groupby('gun')]
    r=random.Random(7); bs=[]
    for _ in range(4000):
        i=[r.randrange(len(gl)) for _ in range(len(gl))]
        n=sum(gl[j][0] for j in i); dd=sum(gl[j][1] for j in i)
        if dd>0: bs.append(100*n/dd)
    bs.sort()
    print(f"  {ad}: {len(dfr)} pencere | essiz {pay:,.0f} pay | oder {od:.2f} | kazanir {kzo:.2f} "
          f"| KENAR {kzo-od:+.2f} GA95[{bs[100]:+.2f},{bs[3900]:+.2f}]")
print("### AGIR TARAF (essiz bacak) fiyatinin ima ettiginden fazla kazaniyor mu?")
analiz(df[df.wallet.str.lower()==BOS],"bosona     ")
analiz(df,"TUM piyasa ")
print("\n### bosona — DENGESIZLIK DERECESINE gore")
d=df[df.wallet.str.lower()==BOS]
g=d.groupby(['gun','start_ts','outcome_idx']).agg(pay=('shares','sum')).reset_index()
g['mal']=d.groupby(['gun','start_ts','outcome_idx']).apply(lambda x:(x.shares*x.price).sum(),include_groups=False).values
p=g.pivot_table(index=['gun','start_ts'],columns='outcome_idx',values=['pay','mal'],fill_value=0.0)
R=[]
for (gun,S),r in p.iterrows():
    q0=r.get(('pay',0),0.0); q1=r.get(('pay',1),0.0)
    m0=r.get(('mal',0),0.0); m1=r.get(('mal',1),0.0)
    if q0+q1<=0: continue
    ag=0 if q0>q1 else 1; essiz=abs(q0-q1)
    if essiz<1: continue
    ort=(m0/q0 if ag==0 and q0>0 else (m1/q1 if q1>0 else 0))
    R.append((abs(q0-q1)/(q0+q1),essiz,ort,1.0 if ag==kz[S] else 0.0))
dfr=pd.DataFrame(R,columns=['dg','essiz','fiyat','kazandi'])
for lo,hi,ad in ((0,.3,'hafif <%30'),(.3,.6,'orta %30-60'),(.6,.9,'agir %60-90'),(.9,1.01,'TAM tek tarafli >%90')):
    x=dfr[(dfr.dg>=lo)&(dfr.dg<hi)]
    if len(x)<40: continue
    pay=x.essiz.sum()
    print(f"  {ad:>22}: {len(x):>4} pen {pay:>9,.0f} pay  oder {100*(x.essiz*x.fiyat).sum()/pay:>5.2f}  "
          f"kazanir {100*(x.essiz*x.kazandi).sum()/pay:>5.2f}  KENAR {100*((x.essiz*x.kazandi).sum()-(x.essiz*x.fiyat).sum())/pay:+6.2f}")
