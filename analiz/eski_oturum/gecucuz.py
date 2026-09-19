"""GEC+UCUZ DOLUM: karsi tarafi ZATEN tutuyorken mi, tutmuyorken mi?
Bu ayrim yapilmadan olculmustu (7 dolum, dolum duzeyi). Simdi ayiriyorum."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
df['kz']=df.start_ts.map(kz)
df=df.sort_values(['wallet','start_ts','t_rel_s'])
# O DOLUMDAN ONCE karsi tarafta ne kadar pay vardi?
df['kum']=df.groupby(['wallet','start_ts','outcome_idx']).shares.cumsum()-df.shares
piv=df.pivot_table(index=['wallet','start_ts','t_rel_s','outcome_idx'],values='kum',aggfunc='max')
# daha basit: her satirda, ayni cuzdan-pencerede DAHA ONCE karsi tarafta dolum var mi
df['ters']=1-df.outcome_idx
onceki={}
karsi=np.zeros(len(df))
w_=df.wallet.values; s_=df.start_ts.values; o_=df.outcome_idx.values; sh_=df.shares.values
key=None; acc=[0.0,0.0]
for i in range(len(df)):
    k=(w_[i],s_[i])
    if k!=key: key=k; acc=[0.0,0.0]
    karsi[i]=acc[1-o_[i]]
    acc[o_[i]]+=sh_[i]
df['karsi_once']=karsi
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares
print(f"{len(df):,} dolum\n")

g=df[(df.t_rel_s>=200)&(df.price<=0.25)]
print(f"### GEC (t>=200) + UCUZ (px<=0.25) DOLUMLAR: {len(g):,}")
print(f"  {'durum':<34} {'dolum':>8} {'pay':>11} {'kr/pay':>8}  {'kazanan%':>9}")
for lbl,s in [('KARSI TARAF VAR (cift tamamliyor)',g[g.karsi_once>0]),
              ('KARSI TARAF YOK (ciplak bilet)',  g[g.karsi_once<=0])]:
    if not len(s): continue
    print(f"  {lbl:<34} {len(s):>8,} {s.shares.sum():>11,.0f} "
          f"{100*s.pnl.sum()/s.shares.sum():>+8.2f} {100*(s.outcome_idx==s.kz).mean():>8.1f}%")

print("\n### AYNI AYRIM, GEC_KES ESIGINE GORE (px<=0.25)")
print(f"  {'t esigi':<10} {'KARSI VAR kr/pay':>18} {'n':>9}   {'KARSI YOK kr/pay':>18} {'n':>9}")
for t0 in [120,150,180,200,240,260]:
    s=df[(df.t_rel_s>=t0)&(df.price<=0.25)]
    a=s[s.karsi_once>0]; b=s[s.karsi_once<=0]
    fa=100*a.pnl.sum()/a.shares.sum() if len(a) else np.nan
    fb=100*b.pnl.sum()/b.shares.sum() if len(b) else np.nan
    print(f"  t>={t0:<7} {fa:>+18.2f} {len(a):>9,}   {fb:>+18.2f} {len(b):>9,}")

print("\n### FIYAT BANDINA GORE (t>=200, KARSI TARAF VAR)")
a=g[g.karsi_once>0]
for lo,hi in [(0,.05),(.05,.10),(.10,.15),(.15,.20),(.20,.26)]:
    s=a[(a.price>=lo)&(a.price<hi)]
    if len(s)<30: continue
    print(f"  {lo:.2f}-{hi:.2f}: {len(s):>7,} dolum | {100*s.pnl.sum()/s.shares.sum():>+7.2f} kr/pay | kazanan %{100*(s.outcome_idx==s.kz).mean():.1f}")
