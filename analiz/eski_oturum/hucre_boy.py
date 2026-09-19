#!/usr/bin/env python3
"""KAZANAN HUCRELER BIZIM BOYUMUZDA DA GECERLI MI?
Dolum simulasyonu YOK (6 kez yanaltti). Zincir defterinde ayni hucreyi
dolum boyuna gore ayiriyoruz. 1-9 pay = bizim klip.
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['pnl']=df.shares*(df.outcome_idx==df.kaz)-df.shares*df.price-df.fee
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
def olc(d):
    if d.start_ts.nunique()<150: return None
    pz=d.groupby(['gun','start_ts']).agg(p=('pnl','sum'),s=('shares','sum')).reset_index()
    pz['kr']=100*pz.p/pz.s
    g=[x.kr.values for _,x in pz.groupby('gun')]
    r=random.Random(5)
    bs=sorted(np.concatenate([g[r.randrange(len(g))] for _ in g]).mean() for _ in range(2000))
    return pz.kr.mean(),bs[50],bs[1950],pz.start_ts.nunique(),d.shares.sum()
HUC=[((0.60,0.80),(240,301),'GEC FAVORI 0.60-0.80 t>=240'),
     ((0.60,0.80),(180,240),'GEC FAVORI 0.60-0.80 t180-240'),
     ((0.10,0.20),(0,60),  'ERKEN UCUZ 0.10-0.20 t<60'),
     ((0.20,0.30),(0,60),  'ERKEN UCUZ 0.20-0.30 t<60'),
     ((0.50,0.60),(0,301), 'ORTA BANT 0.50-0.60 her zaman'),
     ((0.30,0.40),(240,301),'KONTROL(kotu) 0.30-0.40 t>=240')]
print("### HUCRE x DOLUM BOYU  (1-9 pay = BIZIM KLIP)")
for (pa,pb),(ta,tb),ad in HUC:
    d0=df[(df.price>=pa)&(df.price<pb)&(df.t_rel_s>=ta)&(df.t_rel_s<tb)]
    print(f"\n  {ad}")
    print(f"     {'boy':>10} {'pencere':>8} {'pay':>11} {'kr/pay':>8} {'GA95':>18}")
    for lo,hi,bad in ((0,10,'1-9 (BIZ)'),(10,50,'10-49'),(50,250,'50-249'),(250,10**9,'250+')):
        r=olc(d0[(d0.shares>=lo)&(d0.shares<hi)])
        if not r: print(f"     {bad:>10}    yetersiz ornek"); continue
        m,l,h,n,pay=r
        im='  <<<' if l>0 else ('  (negatif)' if h<0 else '')
        print(f"     {bad:>10} {n:>8} {pay:>11,.0f} {m:>+8.2f} {('[%+.2f,%+.2f]'%(l,h)):>18}{im}")
