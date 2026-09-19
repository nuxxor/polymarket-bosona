"""KRITIK TEST: 0.20-0.40 bandindaki +1.85 kr/pay maker kenari KUCUK emre de acik mi?

Fable'in verdikti "kenar yok" degil "bize acik degil" olmali. Bunu ayiran sey:
ayni bantta KUCUK dolumlar da kazaniyor mu, yoksa kenar yalniz BUYUK dolumlarda mi?
Bizim klip 5 pay. Zincir defteri her dolumun payini tasiyor.
"""
import pandas as pd, json, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['w']=(df.outcome_idx==df.kaz).astype(float)
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
def ken(d):
    if len(d)<500: return None
    pay=d.shares.sum()
    k=100*((d.shares*d.w).sum()-(d.shares*d.price).sum()-d.fee.sum())/pay
    g=[(( x.shares*x.w).sum()-(x.shares*x.price).sum()-x.fee.sum(), x.shares.sum()) for _,x in d.groupby('gun')]
    if len(g)<5: return (pay,k,None,None)
    r=random.Random(11)
    bp=sorted(100*sum(g[r.randrange(len(g))][0] for _ in g)/sum(g[r.randrange(len(g))][1] for _ in g) for _ in range(2000))
    return (pay,k,bp[50],bp[1950])
print("### 0.20-0.40 BANDI — DOLUM BOYUNA gore maker kenari (19 gun, zincir)")
b=df[(df.price>=0.20)&(df.price<0.40)]
print(f"  bant toplam: {b.shares.sum():,.0f} pay, {len(b):,} dolum")
print(f"  {'dolum boyu':>16} {'pay':>13} {'KENAR':>8} {'GA95':>20}")
for lo,hi,ad in ((0,10,'1-9 pay (BIZ=5)'),(10,25,'10-24'),(25,50,'25-49'),
                 (50,100,'50-99'),(100,250,'100-249'),(250,10**9,'250+')):
    d=b[(b.shares>=lo)&(b.shares<hi)]
    r=ken(d)
    if not r: continue
    pay,k,l,h=r
    print(f"  {ad:>16} {pay:>13,.0f} {k:>+8.2f} {('[%+.2f,%+.2f]'%(l,h)) if l is not None else '':>20}")
print("\n### KONTROL: 0.60-0.80 bandi (piyasa NEGATIF) — ayni ayrim")
b2=df[(df.price>=0.60)&(df.price<0.80)]
for lo,hi,ad in ((0,10,'1-9 pay'),(100,250,'100-249'),(250,10**9,'250+')):
    d=b2[(b2.shares>=lo)&(b2.shares<hi)]
    r=ken(d)
    if not r: continue
    pay,k,l,h=r
    print(f"  {ad:>16} {pay:>13,.0f} {k:>+8.2f} {('[%+.2f,%+.2f]'%(l,h)) if l is not None else '':>20}")
