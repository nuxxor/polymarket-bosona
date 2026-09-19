#!/usr/bin/env python3
"""BASAMAKLAR NEREYE KONMALI? t<60 ve tavan 0.40 kisitiyla.
Havuzlanmis tahminci, 1-9 paylik dolumlar (bizim klip), 19 gun zincir.
Hem KENAR hem HACIM (ne siklikta dolar) lazim."""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')&(df.shares<10)]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['w']=(df.outcome_idx==df.kaz).astype(float)
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
E=df[df.t_rel_s<60]
TOP=df.start_ts.nunique()
def olc(d):
    if len(d)<200: return None
    pay=d.shares.sum()
    ken=100*((d.shares*d.w).sum()-(d.shares*d.price).sum()-d.fee.sum())/pay
    g=list(d.groupby('gun').apply(lambda x:((x.shares*x.w).sum()-(x.shares*x.price).sum()-x.fee.sum(),x.shares.sum()),include_groups=False))
    if len(g)<5: return (pay,ken,None,None,d.start_ts.nunique())
    r=random.Random(7); bs=[]
    for _ in range(3000):
        i=[r.randrange(len(g)) for _ in range(len(g))]
        n=sum(g[j][0] for j in i); dd=sum(g[j][1] for j in i)
        if dd>0: bs.append(100*n/dd)
    bs.sort(); return (pay,ken,bs[75],bs[2925],d.start_ts.nunique())
print(f"### t<60, 1-9 pay, INCE FIYAT TARAMASI  (toplam {TOP} pencere)")
print(f"  {'fiyat':>12} {'pay':>10} {'pencere':>8} {'kapsam':>7} {'kenar':>7} {'GA95':>18}")
for a in [round(x,3) for x in np.arange(0.16,0.44,0.02)]:
    b=round(a+0.02,3)
    r=olc(E[(E.price>=a)&(E.price<b)])
    if not r: continue
    pay,ken,lo,hi,pen=r
    im='  <<<' if (lo is not None and lo>0) else ''
    print(f"  {a:.2f}-{b:.2f} {pay:>10,.0f} {pen:>8} {100*pen/TOP:>6.0f}% {ken:>+7.2f} {('[%+.2f,%+.2f]'%(lo,hi)) if lo is not None else '':>18}{im}")
print(f"\n### MEVCUT BASAMAKLARIMIZ, t<60'ta")
for px in (0.40,0.30,0.22,0.15,0.10,0.06,0.03):
    d=E[(E.price>=px-0.01)&(E.price<px+0.01)]
    if len(d)<50: print(f"  {px:.2f}: yetersiz veri ({len(d)} dolum)"); continue
    pay=d.shares.sum()
    ken=100*((d.shares*d.w).sum()-(d.shares*d.price).sum()-d.fee.sum())/pay
    print(f"  {px:.2f}: {pay:>9,.0f} pay | {d.start_ts.nunique():>4} pencere (%{100*d.start_ts.nunique()/TOP:.0f}) | kenar {ken:+.2f}")
