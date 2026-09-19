#!/usr/bin/env python3
"""FIYAT x ZAMAN HARITASI — maker kenari, PENCERE-ESIT agirlikla.
Kazanan profiller farkli (t=-8, t=28, t=147). Nerede durulmali?
Pencere-esit agirlik ZORUNLU: pay-agirlikli sayilar hacim yogunlugundan gelir.
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['pnl']=df.shares*(df.outcome_idx==df.kaz)-df.shares*df.price-df.fee
PB=[(0.0,0.10),(0.10,0.20),(0.20,0.30),(0.30,0.40),(0.40,0.50),(0.50,0.60),(0.60,0.80),(0.80,1.01)]
TB=[(-10**9,0,'ONCE'),(0,30,'0-30'),(30,60,'30-60'),(60,120,'60-120'),
    (120,180,'120-180'),(180,240,'180-240'),(240,301,'240+')]
print("### MAKER KENARI: fiyat x zaman, PENCERE-ESIT agirlik (kr/pay)")
print("    (hucrede <200 pencere varsa bos birakildi)")
hdr="  fiyat      "+"".join(f"{ad:>9}" for _,_,ad in TB)
print(hdr)
for a,b in PB:
    sat=f"  {a:.2f}-{b:.2f} "
    for t0,t1,ad in TB:
        d=df[(df.price>=a)&(df.price<b)&(df.t_rel_s>=t0)&(df.t_rel_s<t1)]
        if d.start_ts.nunique()<200: sat+=f"{'':>9}"; continue
        pz=d.groupby('start_ts').agg(p=('pnl','sum'),s=('shares','sum'))
        sat+=f"{100*(pz.p/pz.s).mean():>+9.1f}"
    print(sat)
print("\n### AYNI HUCRELER — kac PENCERE (guc kontrolu)")
print(hdr)
for a,b in PB:
    sat=f"  {a:.2f}-{b:.2f} "
    for t0,t1,ad in TB:
        d=df[(df.price>=a)&(df.price<b)&(df.t_rel_s>=t0)&(df.t_rel_s<t1)]
        n=d.start_ts.nunique()
        sat+=f"{(n if n>=200 else ''):>9}"
    print(sat)
# en iyi hucreler GA ile
print("\n### EN IYI HUCRELER (gun-kumeli GA95)")
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
sonuc=[]
for a,b in PB:
    for t0,t1,ad in TB:
        d=df[(df.price>=a)&(df.price<b)&(df.t_rel_s>=t0)&(df.t_rel_s<t1)]
        if d.start_ts.nunique()<200: continue
        pz=d.groupby('start_ts').agg(p=('pnl','sum'),s=('shares','sum'))
        m=(pz.p/pz.s).mean()*100
        gg=d.groupby('gun').apply(lambda x:((x.pnl/x.shares).mean()*100),include_groups=False)
        gl=list(gg.values)
        r=random.Random(3)
        bp=sorted(np.mean([gl[r.randrange(len(gl))] for _ in gl]) for _ in range(2000))
        sonuc.append((m,bp[50],bp[1950],f"{a:.2f}-{b:.2f}",ad,d.start_ts.nunique(),d.shares.sum()))
sonuc.sort(reverse=True)
print(f"  {'fiyat':>11} {'zaman':>9} {'kr/pay':>8} {'GA95':>18} {'pencere':>8} {'pay':>12}")
for m,lo,hi,fy,ad,n,pay in sonuc[:8]:
    print(f"  {fy:>11} {ad:>9} {m:>+8.2f} {('[%+.2f,%+.2f]'%(lo,hi)):>18} {n:>8} {pay:>12,.0f}")
print("  ...")
for m,lo,hi,fy,ad,n,pay in sonuc[-4:]:
    print(f"  {fy:>11} {ad:>9} {m:>+8.2f} {('[%+.2f,%+.2f]'%(lo,hi)):>18} {n:>8} {pay:>12,.0f}")
