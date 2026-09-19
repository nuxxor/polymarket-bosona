"""bosona 0.80+ alirken CIFT MALIYETI kac? <1 ise kopyalanabilir cift tamamlama."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
cols=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s','fee']
mk=pd.read_parquet(f'{D}/maker.parquet',columns=cols); mk['rol']='M'
tk=pd.read_parquet(f'{D}/taker.parquet',columns=cols); tk['rol']='T'
df=pd.concat([mk,tk],ignore_index=True)
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
df['kz']=df.start_ts.map(kz)
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares-df.fee.fillna(0)
b=df[df.wallet.str.lower()==BOS].sort_values(['start_ts','t_rel_s'])
print(f"bosona TUM alimlari (maker+taker): {len(b):,} dolum, {b.shares.sum():,.0f} pay")
print(f"  rol dagilimi: {b.groupby('rol').shares.sum().to_dict()}\n")

# pencere basina: her tarafin agirlikli ort fiyati ve payi
g=b.groupby(['start_ts','outcome_idx']).apply(
    lambda s: pd.Series({'pay':s.shares.sum(),'ort':(s.price*s.shares).sum()/s.shares.sum()}),
    include_groups=False).unstack()
g=g.dropna()
g.columns=['pay0','pay1','ort0','ort1']
g['cift']=np.minimum(g.pay0,g.pay1)
g['cmal']=g.ort0+g.ort1
g['pahali']=(g.ort0>=0.80)|(g.ort1>=0.80)
pn=b.groupby('start_ts').pnl.sum(); tp=b.groupby('start_ts').shares.sum()
g['pnl']=pn.reindex(g.index); g['toppay']=tp.reindex(g.index)
print(f"iki tarafli pencereleri: {len(g):,}")
print(f"  cift maliyeti MEDYAN {g.cmal.median():.4f} | ORT {g.cmal.mean():.4f}")
print(f"  cift maliyeti <1.00 olan pencere orani: %{100*(g.cmal<1.0).mean():.1f}\n")

print("### 0.80+ BACAGI OLAN PENCERELER vs OLMAYANLAR")
for lbl,s in [('bir bacagi >=0.80',g[g.pahali]),('ikisi de <0.80',g[~g.pahali])]:
    print(f"  {lbl:<22} {len(s):>5} pencere | cift mal medyan {s.cmal.median():.4f} | "
          f"<1.00 orani %{100*(s.cmal<1.0).mean():>5.1f} | {100*s.pnl.sum()/s.toppay.sum():>+7.2f} kr/pay")

print("\n### 0.80+ ALIMLARIN ROLU (maker mi taker mi?)")
p=b[b.price>=0.80]
for rol in ('M','T'):
    s=p[p.rol==rol]
    if len(s): print(f"  {rol}: {len(s):>6,} dolum {s.shares.sum():>9,.0f} pay | "
                     f"{100*s.pnl.sum()/s.shares.sum():>+7.2f} kr/pay | medyan t={s.t_rel_s.median():.0f}")
print("\n### KIYAS: <=0.40 alimlarin rolu")
q=b[b.price<=0.40]
for rol in ('M','T'):
    s=q[q.rol==rol]
    if len(s): print(f"  {rol}: {len(s):>6,} dolum {s.shares.sum():>9,.0f} pay | "
                     f"{100*s.pnl.sum()/s.shares.sum():>+7.2f} kr/pay | medyan t={s.t_rel_s.median():.0f}")
