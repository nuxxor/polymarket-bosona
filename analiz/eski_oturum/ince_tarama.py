#!/usr/bin/env python3
"""0.35-0.70 arasi INCE tarama — 0.40-0.50 eksi / 0.50-0.60 arti siniri gercek mi?
Aynalı defterde Up@0.45 = Down@0.55 oldugu icin bu bir FAVORI/ZAYIF asimetrisi
olmali. Keskin bir esik kirilgan olur; yumusak gecis mekanizma isaretidir.
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['pnl']=df.shares*(df.outcome_idx==df.kaz)-df.shares*df.price-df.fee
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
df=df[df.shares<10]        # YALNIZ bizim klip boyu
def olc(d):
    if d.start_ts.nunique()<150: return None
    pz=d.groupby(['gun','start_ts']).agg(p=('pnl','sum'),s=('shares','sum')).reset_index()
    pz['kr']=100*pz.p/pz.s
    g=[x.kr.values for _,x in pz.groupby('gun')]
    r=random.Random(5)
    bs=sorted(np.concatenate([g[r.randrange(len(g))] for _ in g]).mean() for _ in range(1500))
    return pz.kr.mean(),bs[37],bs[1462],pz.start_ts.nunique(),100*(d.outcome_idx==d.kaz).mean(),d.price.mean()
print("### INCE TARAMA — yalniz 1-9 paylik dolumlar (BIZIM KLIP), tum zamanlar")
print(f"  {'fiyat':>11} {'pencere':>8} {'oder':>6} {'kazanir':>8} {'kenar':>7} {'GA95':>18}")
for a in np.arange(0.30,0.72,0.025):
    b=a+0.025
    r=olc(df[(df.price>=a)&(df.price<b)])
    if not r: continue
    m,lo,hi,n,kzo,od=r
    im=' <<<' if lo>0 else (' neg' if hi<0 else '')
    print(f"  {a:.3f}-{b:.3f} {n:>8} {100*od:>6.2f} {kzo:>8.2f} {m:>+7.2f} {('[%+.2f,%+.2f]'%(lo,hi)):>18}{im}")
