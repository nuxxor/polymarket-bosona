#!/usr/bin/env python3
"""FIYAT x ZAMAN haritasi — DUZELTILMIS onyukleme.
Hata: nokta tahmini PENCERE-esit, onyukleme DOLUM-esit hesapliyordu ->
aralik nokta tahminini kapsamiyordu. Artik ikisi de ayni istatistik:
gunleri yeniden ornekle, her ornekte PENCERE-esit ortalamayi hesapla.
"""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['pnl']=df.shares*(df.outcome_idx==df.kaz)-df.shares*df.price-df.fee
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
PB=[(0.0,0.10),(0.10,0.20),(0.20,0.30),(0.30,0.40),(0.40,0.50),(0.50,0.60),(0.60,0.80),(0.80,1.01)]
TB=[(-10**9,0,'ONCE'),(0,60,'0-60'),(60,120,'60-120'),(120,180,'120-180'),(180,240,'180-240'),(240,301,'240+')]
out=[]
for a,b in PB:
    for t0,t1,ad in TB:
        d=df[(df.price>=a)&(df.price<b)&(df.t_rel_s>=t0)&(df.t_rel_s<t1)]
        if d.start_ts.nunique()<300: continue
        # pencere seviyesine indir, gune etiketle
        pz=d.groupby(['gun','start_ts']).agg(p=('pnl','sum'),s=('shares','sum')).reset_index()
        pz['kr']=100*pz.p/pz.s
        nok=pz.kr.mean()
        gruplar=[x.kr.values for _,x in pz.groupby('gun')]
        r=random.Random(11); bs=[]
        for _ in range(3000):
            sec=np.concatenate([gruplar[r.randrange(len(gruplar))] for _ in gruplar])
            bs.append(sec.mean())
        bs.sort()
        out.append((nok,bs[75],bs[2925],f"{a:.2f}-{b:.2f}",ad,pz.start_ts.nunique(),d.shares.sum()))
print("### MAKER KENARI — fiyat x zaman, PENCERE-esit, GA da PENCERE-esit (duzeltildi)")
print(f"  {'fiyat':>11} {'zaman':>9} {'kr/pay':>8} {'GA95':>18} {'pencere':>8} {'pay':>12}")
for nok,lo,hi,fy,ad,n,pay in sorted(out,reverse=True):
    im='  <<<' if lo>0 else ('  (negatif, kesin)' if hi<0 else '')
    print(f"  {fy:>11} {ad:>9} {nok:>+8.2f} {('[%+.2f,%+.2f]'%(lo,hi)):>18} {n:>8} {pay:>12,.0f}{im}")
