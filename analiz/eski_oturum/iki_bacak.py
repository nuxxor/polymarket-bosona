#!/usr/bin/env python3
"""IKI BACAKLI STRATEJI: ilk bacak paraya yakin, ikinci bacak ucuz.
19 gun zincir defteri. Pencere duzeyinde, CUZDAN BAZLI gercek davranis.

Soru 1: cift kuran cuzdanlar, ilk bacagi KACTAN aliyor?
Soru 2: ilk bacak fiyatina gore cift maliyeti ve PnL ne oluyor?
Soru 3: bizim gibi yalniz <=0.40 alanlar ne kadar cift kurabiliyor?
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
print(f"maker BUY: {len(df):,} dolum / {df.start_ts.nunique()} pencere",flush=True)

# cuzdan x pencere duzeyinde: ilk bacak fiyati, cift kuruldu mu, PnL
g=df.sort_values('t_rel_s').groupby(['wallet','start_ts'])
sat=[]
for (w,S),d in g:
    if len(d)<2: continue
    q0=d[d.outcome_idx==0].shares.sum(); q1=d[d.outcome_idx==1].shares.sum()
    if q0+q1<=0: continue
    ilk=d.iloc[0]
    m0=(d[d.outcome_idx==0].shares*d[d.outcome_idx==0].price).sum()
    m1=(d[d.outcome_idx==1].shares*d[d.outcome_idx==1].price).sum()
    cift = q0>0 and q1>0
    cm = (m0/q0 + m1/q1) if cift else None
    pnl = (q0 if kz[S]==0 else q1) - (m0+m1) - d.fee.sum()
    sat.append((w,S,d.gun.iloc[0],float(ilk.price),float(ilk.t_rel_s),cift,cm,pnl,q0+q1,
                float(d.price.max())))
R=pd.DataFrame(sat,columns=['w','S','gun','ilk_px','ilk_t','cift','cift_mal','pnl','pay','max_px'])
print(f"cuzdan-pencere kaydi: {len(R):,}\n",flush=True)

print("### SORU 1 — ILK BACAK FIYATINA gore cift kurma orani ve sonuc")
print(f"  {'ilk bacak':>12} {'kayit':>8} {'cift%':>7} {'cift mal':>9} {'kr/pay':>8} {'GA95':>18}")
def ga(d):
    if d.gun.nunique()<5: return None
    gl=[(x.pnl.sum(),x.pay.sum()) for _,x in d.groupby('gun')]
    r=random.Random(7); b=[]
    for _ in range(2500):
        i=[r.randrange(len(gl)) for _ in range(len(gl))]
        n=sum(gl[j][0] for j in i); dd=sum(gl[j][1] for j in i)
        if dd>0: b.append(100*n/dd)
    b.sort(); return b[62],b[2437]
for a,b in ((0.0,0.20),(0.20,0.35),(0.35,0.45),(0.45,0.55),(0.55,0.65),(0.65,0.80),(0.80,1.01)):
    d=R[(R.ilk_px>=a)&(R.ilk_px<b)]
    if len(d)<300: continue
    cm=d[d.cift].cift_mal.mean()
    kr=100*d.pnl.sum()/d.pay.sum()
    g95=ga(d)
    print(f"  {a:.2f}-{b:.2f} {len(d):>8,} {100*d.cift.mean():>6.1f}% {cm:>9.3f} {kr:>+8.2f} "
          f"{('[%+.2f,%+.2f]'%g95) if g95 else '':>18}")

print("\n### SORU 2 — BIZIM KISIT: hic 0.40 ustu almayanlar")
ucuz=R[R.max_px<=0.40]; genis=R[R.max_px>0.40]
for ad,d in (("yalniz <=0.40 (BIZ)",ucuz),("0.40 ustu de alan",genis)):
    if len(d)<100: continue
    kr=100*d.pnl.sum()/d.pay.sum(); g95=ga(d)
    print(f"  {ad:>22}: {len(d):>7,} kayit | cift %{100*d.cift.mean():>5.1f} | "
          f"cift mal {d[d.cift].cift_mal.mean():.3f} | {kr:+.2f} kr/pay {('[%+.2f,%+.2f]'%g95) if g95 else ''}")

print("\n### SORU 3 — CIFT KURANLAR vs KURAMAYANLAR")
for ad,d in (("cift kurdu",R[R.cift]),("tek tarafli kaldi",R[~R.cift])):
    kr=100*d.pnl.sum()/d.pay.sum(); g95=ga(d)
    print(f"  {ad:>20}: {len(d):>7,} kayit | {kr:+7.2f} kr/pay {('[%+.2f,%+.2f]'%g95) if g95 else ''}")
