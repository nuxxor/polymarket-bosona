"""DERIN BASAMAK GEC + KARSI TARAF ELDEYKEN — attigim rung'lar aslinda CIFT
TAMAMLAYICI olarak mi kullaniliyor? 19 gun zincir, cuzdan-pencere."""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
df=df.sort_values(['wallet','start_ts','t_rel_s'])
# her dolum icin: o ana kadar KARSI tarafta pay var mi?
df['ck']=df.groupby(['wallet','start_ts','outcome_idx']).shares.cumsum()-df.shares
tot=df.pivot_table(index=['wallet','start_ts','t_rel_s'],columns='outcome_idx',values='shares',aggfunc='sum')
# basit yol: cuzdan-pencere icinde karsi tarafin ILK dolum zamani
ilk=df.groupby(['wallet','start_ts','outcome_idx']).t_rel_s.min().unstack()
ilk.columns=['t0','t1']
df=df.join(ilk,on=['wallet','start_ts'])
df['karsi_t']=np.where(df.outcome_idx==0,df.t1,df.t0)
df['karsi_var']=df.karsi_t.notna()&(df.karsi_t<df.t_rel_s)   # karsi taraf ONCE dolmus
df['w']=(df.outcome_idx==df.kaz).astype(float)
df['pnl']=df.shares*df.w-df.shares*df.price-df.fee
print(f"{len(df):,} dolum\n",flush=True)
def ga(d):
    if d.gun.nunique()<5: return None
    gl=[(x.pnl.sum(),x.shares.sum()) for _,x in d.groupby('gun')]
    r=random.Random(5); b=[]
    for _ in range(1500):
        i=[r.randrange(len(gl)) for _ in range(len(gl))]
        n=sum(gl[j][0] for j in i); dd=sum(gl[j][1] for j in i)
        if dd>0: b.append(100*n/dd)
    b.sort(); return b[37],b[1462]
print("### DERIN BASAMAKLAR (<=0.10) — bagimsiz mi, cift tamamlayici mi?")
print(f"  {'durum':>34} {'pay':>11} {'kr/pay':>8} {'GA95':>18}")
d0=df[(df.price<=0.10)&(df.shares<10)]
for ad,f in (("KARSI TARAF YOK, t<60",(~d0.karsi_var)&(d0.t_rel_s<60)),
             ("KARSI TARAF YOK, t>=120",(~d0.karsi_var)&(d0.t_rel_s>=120)),
             ("KARSI TARAF VAR, t<120",(d0.karsi_var)&(d0.t_rel_s<120)),
             ("KARSI TARAF VAR, t>=120",(d0.karsi_var)&(d0.t_rel_s>=120)),
             ("KARSI TARAF VAR, t>=180",(d0.karsi_var)&(d0.t_rel_s>=180))):
    d=d0[f]
    if len(d)<300: continue
    g=ga(d)
    print(f"  {ad:>34} {d.shares.sum():>11,.0f} {100*d.pnl.sum()/d.shares.sum():>+8.2f} {('[%+.2f,%+.2f]'%g) if g else '':>18}")
print("\n### AYNI SEY, 0.10-0.20 bandi")
d1=df[(df.price>0.10)&(df.price<=0.20)&(df.shares<10)]
for ad,f in (("KARSI YOK, t<60",(~d1.karsi_var)&(d1.t_rel_s<60)),
             ("KARSI VAR, t>=120",(d1.karsi_var)&(d1.t_rel_s>=120))):
    d=d1[f]
    if len(d)<300: continue
    g=ga(d)
    print(f"  {ad:>34} {d.shares.sum():>11,.0f} {100*d.pnl.sum()/d.shares.sum():>+8.2f} {('[%+.2f,%+.2f]'%g) if g else '':>18}")
