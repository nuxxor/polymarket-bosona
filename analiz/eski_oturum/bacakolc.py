import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
df['mal']=df.shares*df.price
df['kazpay']=df.shares*(df.outcome_idx==df.kaz)
print(f"{len(df):,} dolum",flush=True)
df=df.sort_values(['wallet','start_ts','t_rel_s'])
A=df.groupby(['wallet','start_ts'],sort=False).agg(
    gun=('gun','first'), ilk_px=('price','first'), max_px=('price','max'),
    pay=('shares','sum'), mal=('mal','sum'), kazpay=('kazpay','sum'),
    fee=('fee','sum'), n=('shares','size'))
s0=df[df.outcome_idx==0].groupby(['wallet','start_ts']).agg(q0=('shares','sum'),m0=('mal','sum'))
s1=df[df.outcome_idx==1].groupby(['wallet','start_ts']).agg(q1=('shares','sum'),m1=('mal','sum'))
A=A.join(s0,how='left').join(s1,how='left')
A[['q0','m0','q1','m1']]=A[['q0','m0','q1','m1']].fillna(0.0)
A=A[A.n>=2].copy()
A['pnl']=A.kazpay-A.mal-A.fee
A['cift']=(A.q0>0)&(A.q1>0)
o0=np.divide(A.m0.values,A.q0.values,out=np.zeros(len(A)),where=A.q0.values>0)
o1=np.divide(A.m1.values,A.q1.values,out=np.zeros(len(A)),where=A.q1.values>0)
A['cift_mal']=np.where(A.cift.values,o0+o1,np.nan)
A=A.reset_index()
print(f"cuzdan-pencere (>=2 dolum): {len(A):,}\n",flush=True)
def ga(d):
    if d.gun.nunique()<5: return None
    gl=[(x.pnl.sum(),x.pay.sum()) for _,x in d.groupby('gun')]
    r=random.Random(7); b=[]
    for _ in range(2000):
        i=[r.randrange(len(gl)) for _ in range(len(gl))]
        n=sum(gl[j][0] for j in i); dd=sum(gl[j][1] for j in i)
        if dd>0: b.append(100*n/dd)
    b.sort(); return b[50],b[1950]
print("### 1 — ILK BACAK FIYATINA gore")
print(f"  {'ilk bacak':>12} {'kayit':>9} {'cift%':>7} {'cift mal':>9} {'kr/pay':>8} {'GA95':>18}")
for a,b in ((0.0,0.20),(0.20,0.35),(0.35,0.45),(0.45,0.55),(0.55,0.65),(0.65,0.80),(0.80,1.01)):
    d=A[(A.ilk_px>=a)&(A.ilk_px<b)]
    if len(d)<300: continue
    g=ga(d)
    print(f"  {a:.2f}-{b:.2f} {len(d):>9,} {100*d.cift.mean():>6.1f}% {d.cift_mal.mean():>9.3f} "
          f"{100*d.pnl.sum()/d.pay.sum():>+8.2f} {('[%+.2f,%+.2f]'%g) if g else '':>18}")
print("\n### 2 — BIZIM KISIT (hic 0.40 ustu almamis) vs digerleri")
for ad,d in (("yalniz <=0.40 (BIZ)",A[A.max_px<=0.40]),("0.40 ustu de alan",A[A.max_px>0.40])):
    if len(d)<200: continue
    g=ga(d)
    print(f"  {ad:>22}: {len(d):>8,} | cift %{100*d.cift.mean():>5.1f} | cift mal {d.cift_mal.mean():.3f} | "
          f"{100*d.pnl.sum()/d.pay.sum():+7.2f} kr/pay {('[%+.2f,%+.2f]'%g) if g else ''}")
print("\n### 3 — CIFT vs TEK")
for ad,d in (("cift kurdu",A[A.cift]),("tek tarafli",A[~A.cift])):
    g=ga(d)
    print(f"  {ad:>14}: {len(d):>8,} | {100*d.pnl.sum()/d.pay.sum():>+7.2f} kr/pay {('[%+.2f,%+.2f]'%g) if g else ''}")
print("\n### 4 — CIFT KURANLAR: cift maliyetine gore")
c=A[A.cift]
for a,b in ((0,0.70),(0.70,0.85),(0.85,0.95),(0.95,1.00),(1.00,1.10),(1.10,9)):
    d=c[(c.cift_mal>=a)&(c.cift_mal<b)]
    if len(d)<200: continue
    g=ga(d)
    print(f"  cift mal {a:.2f}-{b:.2f}: {len(d):>7,} | {100*d.pnl.sum()/d.pay.sum():>+7.2f} kr/pay {('[%+.2f,%+.2f]'%g) if g else ''}")
