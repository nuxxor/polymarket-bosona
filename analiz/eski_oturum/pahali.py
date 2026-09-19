"""0.80+ BANDINDA bosona ne yapiyor da +2.47 aliyor, kalabalik -1.40 aliyor?
GERCEK zincir dolumlari. Simulasyon YOK."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s','fee'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
df['kz']=df.start_ts.map(kz)
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares-df.fee.fillna(0)
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.floor('D')
G=np.unique(df.gun.values)
def ci(s,n=2000):
    d=s.groupby('gun').agg(p=('pnl','sum'),q=('shares','sum'))
    if len(d)<5: return (np.nan,np.nan)
    P=d.p.values;Q=d.q.values;r=np.random.default_rng(4)
    v=[100*P[i].sum()/max(Q[i].sum(),1e-9) for i in (r.integers(0,len(d),len(d)) for _ in range(n))]
    return np.percentile(v,2.5),np.percentile(v,97.5)
def rap(lbl,s,ind=2):
    if len(s)<80: print(f"{' '*ind}{lbl:<34} {len(s):>7,} (az)"); return
    lo,hi=ci(s)
    print(f"{' '*ind}{lbl:<34} {len(s):>7,} dolum {s.shares.sum():>10,.0f} pay  "
          f"{100*s.pnl.sum()/s.shares.sum():>+7.2f} [{lo:+6.2f},{hi:+6.2f}]")

P=df[df.price>=0.80]
b=P[P.wallet.str.lower()==BOS]; o=P[P.wallet.str.lower()!=BOS]
print("### px>=0.80 BANDI")
rap('bosona',b); rap('diger TUM makerlar',o)

print("\n### ZAMANA GORE (t_rel_s)")
for lo,hi in [(0,60),(60,120),(120,180),(180,240),(240,301)]:
    print(f"  t{lo}-{hi}:")
    rap('bosona',b[(b.t_rel_s>=lo)&(b.t_rel_s<hi)],4)
    rap('digerleri',o[(o.t_rel_s>=lo)&(o.t_rel_s<hi)],4)

print("\n### FIYATA GORE")
for lo,hi in [(.80,.86),(.86,.92),(.92,.96),(.96,1.01)]:
    print(f"  px {lo:.2f}-{hi:.2f}:")
    rap('bosona',b[(b.price>=lo)&(b.price<hi)],4)
    rap('digerleri',o[(o.price>=lo)&(o.price<hi)],4)

print("\n### bosona 0.80+ ALIRKEN KARSI TARAFI TUTUYOR MU?")
df2=df.sort_values(['wallet','start_ts','t_rel_s'])
acc={}; karsi=[]
w_=df2.wallet.values;s_=df2.start_ts.values;o_=df2.outcome_idx.values;sh_=df2.shares.values
key=None;a=[0.0,0.0]
for i in range(len(df2)):
    k=(w_[i],s_[i])
    if k!=key: key=k;a=[0.0,0.0]
    karsi.append(a[1-o_[i]]); a[o_[i]]+=sh_[i]
df2['karsi_once']=karsi
P2=df2[df2.price>=0.80]; b2=P2[P2.wallet.str.lower()==BOS]; o2=P2[P2.wallet.str.lower()!=BOS]
for lbl,s in [('bosona',b2),('digerleri',o2)]:
    print(f"  {lbl}:")
    rap('KARSI TARAF VAR',s[s.karsi_once>0],4)
    rap('KARSI TARAF YOK',s[s.karsi_once<=0],4)
