"""BOSONA'nin maker kenari HANGI FIYAT BANDINDA? Bizim 0.40 tavanimiz onu disliyor mu?"""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s','fee'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
df['kz']=df.start_ts.map(kz)
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares-df.fee.fillna(0)
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.floor('D')
b=df[df.wallet.str.lower()==BOS]
print(f"bosona maker ALIS: {len(b):,} dolum | {b.shares.sum():,.0f} pay | {b.gun.nunique()} gun")
def ci(s,n=3000):
    d=s.groupby('gun').agg(p=('pnl','sum'),q=('shares','sum'))
    if len(d)<5: return (np.nan,np.nan)
    P=d.p.values;Q=d.q.values;r=np.random.default_rng(3)
    v=[100*P[i].sum()/Q[i].sum() for i in (r.integers(0,len(d),len(d)) for _ in range(n))]
    return (np.percentile(v,2.5),np.percentile(v,97.5))
def sat(lbl,s):
    if len(s)<50: print(f"  {lbl:<26} {len(s):>7,} dolum  (az)"); return
    lo,hi=ci(s)
    print(f"  {lbl:<26} {len(s):>7,} dolum {s.shares.sum():>10,.0f} pay  "
          f"{100*s.pnl.sum()/s.shares.sum():>+7.2f} kr/pay [{lo:+.2f},{hi:+.2f}]")
print("\n### BOSONA, FIYAT BANDINA GORE")
sat('HEPSI',b)
for lo,hi in [(0,.20),(.20,.40),(.40,.60),(.60,.80),(.80,1.01)]:
    sat(f'px {lo:.2f}-{hi:.2f}', b[(b.price>=lo)&(b.price<hi)])
print("\n### BIZIM KISITIMIZ ICINDE / DISINDA")
sat('px<=0.40 (BIZE ACIK)', b[b.price<=0.40])
sat('px >0.40 (BIZE KAPALI)', b[b.price>0.40])
print("\n### AYNI AYRIM, CUZDAN-PENCERE duzeyinde (>0.40 alan pencereler)")
mx=b.groupby('start_ts').price.max()
ic=b[b.start_ts.isin(mx[mx<=0.40].index)]; dis=b[b.start_ts.isin(mx[mx>0.40].index)]
sat('pencere tamamen <=0.40', ic); sat('pencerede >0.40 var', dis)
print("\n### KIYAS: ayni bantlarda TUM makerlar")
for lo,hi in [(0,.40),(.40,.60),(.60,.80),(.80,1.01)]:
    s=df[(df.price>=lo)&(df.price<hi)]
    print(f"  tum makerlar px {lo:.2f}-{hi:.2f}: {100*s.pnl.sum()/s.shares.sum():>+7.2f} kr/pay ({s.shares.sum():,.0f} pay)")
