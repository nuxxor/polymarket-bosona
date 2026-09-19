#!/usr/bin/env python3
"""OPERATOR SORUSU: pahali tarafi almak mi kotu, yoksa GEC almak mi?

Bizim tavani (0.40) su veriyle koymustuk: 0.40 ustu dolumlarimiz -$50.95.
AMA o zarar kol B'nin MID KOVALAMASINDAN geliyordu (fiyat kactiktan SONRA almak).
bosona pahali tarafi da aliyor ama ERKEN aliyor.

Test: zincir defteri, maker BUY, HAVUZLANMIS tahminci, BIZIM klip boyu (1-9 pay).
Fiyat x ZAMAN kesiti -> pahali bant erken mi gec mi kotu?
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')&(df.shares<10)]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['w']=(df.outcome_idx==df.kaz).astype(float)
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
def olc(d):
    if len(d)<400: return None
    pay=d.shares.sum()
    ken=100*((d.shares*d.w).sum()-(d.shares*d.price).sum()-d.fee.sum())/pay
    g=d.groupby('gun').apply(lambda x:((x.shares*x.w).sum()-(x.shares*x.price).sum()-x.fee.sum(),x.shares.sum()),include_groups=False)
    gl=list(g)
    if len(gl)<5: return (pay,ken,None,None)
    r=random.Random(7); bs=[]
    for _ in range(3000):
        i=[r.randrange(len(gl)) for _ in range(len(gl))]
        n=sum(gl[j][0] for j in i); dd=sum(gl[j][1] for j in i)
        if dd>0: bs.append(100*n/dd)
    bs.sort(); return (pay,ken,bs[75],bs[2925])
print("### HAVUZLANMIS KENAR — fiyat x zaman, 1-9 paylik dolumlar (BIZIM KLIP)")
print(f"  {'fiyat':>11} {'zaman':>9} {'pay':>10} {'kenar':>8} {'GA95':>18}")
for a,b in ((0.20,0.40),(0.40,0.55),(0.55,0.70),(0.70,0.85)):
    for t0,t1,ad in ((0,60,'t<60'),(60,150,'t60-150'),(150,240,'t150-240'),(240,301,'t240+')):
        r=olc(df[(df.price>=a)&(df.price<b)&(df.t_rel_s>=t0)&(df.t_rel_s<t1)])
        if not r: continue
        pay,ken,lo,hi=r
        im='  <<<' if (lo is not None and lo>0) else ('  neg' if (hi is not None and hi<0) else '')
        print(f"  {a:.2f}-{b:.2f} {ad:>9} {pay:>10,.0f} {ken:>+8.2f} {('[%+.2f,%+.2f]'%(lo,hi)) if lo is not None else '':>18}{im}")
    print()
print("### CIFT KURMA: iki tarafi da almak, tavanla vs tavansiz")
d2=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee'])
d2=d2[(d2.role.str.lower()=='maker')&(d2.side.str.upper()=='BUY')&(d2.shares<10)]
d2['kaz']=d2.start_ts.map(kz); d2=d2[d2.kaz.notna()]
for ad,f in (("tavansiz (tum fiyatlar)",d2),("tavan 0.40",d2[d2.price<=0.40])):
    g=f.groupby(['start_ts','outcome_idx']).shares.sum().unstack(fill_value=0.0)
    if 0 not in g or 1 not in g: continue
    iki=((g[0]>0)&(g[1]>0)).mean()
    print(f"  {ad:>24}: {len(g)} pencere, iki tarafi da dolan %{100*iki:.1f}")
