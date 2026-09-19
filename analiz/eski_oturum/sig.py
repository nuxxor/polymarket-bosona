"""KOL C icin sayilar: bosona'nin ucu (sig izgara) gercek veride ne veriyor?
Kiyas sinifi = cuzdan-pencerede hic >0.50 alim yok."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
df['kz']=df.start_ts.map(kz)
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.floor('D')

# --- TAM EV merdiven simulasyonu (kuyruk yok, UST SINIR) ---
mn=df.groupby(['start_ts','outcome_idx']).price.min().unstack(); mn.columns=['m0','m1']
mn=mn.dropna(); m0=mn.m0.values; m1=mn.m1.values
kv=np.array([kz[s] for s in mn.index]); N=len(mn)
gun=pd.to_datetime(mn.index,unit='s').floor('D').values; G=np.unique(gun)
def sim(r,KLIP=5.0):
    pnl=np.zeros(N);pay=np.zeros(N);mal=np.zeros(N)
    for px in r:
        for oi,m in ((0,m0),(1,m1)):
            f=(m<=px); pnl+=f*KLIP*((kv==oi)-px); pay+=f*KLIP; mal+=f*KLIP*px
    return pnl,pay,mal
def ci(pnl,pay,n=2000):
    P=np.array([pnl[gun==g].sum() for g in G]);Q=np.array([pay[gun==g].sum() for g in G])
    r=np.random.default_rng(9)
    b=[100*P[i].sum()/max(Q[i].sum(),1e-9) for i in (r.integers(0,len(G),len(G)) for _ in range(n))]
    return np.percentile(b,2.5),np.percentile(b,97.5)
print("### MERDIVEN ADAYLARI (TAM EV, essiz bacak kayiplari dahil, KUYRUK YOK=ust sinir)")
for ad,r in [('A CANLI [.34..16]',[.34,.30,.26,.22,.20,.16]),
             ('B CANLI [.20..03]',[.20,.16,.12,.09,.06,.03]),
             ('C sig   [.46..26]',[.46,.42,.38,.34,.30,.26]),
             ('C2 sig  [.48..30]',[.48,.44,.40,.36,.33,.30]),
             ('C3 orta [.42..22]',[.42,.38,.34,.30,.26,.22])]:
    p,q,m=sim(r); lo,hi=ci(p,q)
    print(f"  {ad:<20} {100*p.sum()/q.sum():>+6.2f} [{lo:+.2f},{hi:+.2f}] | {q.sum()/N:>5.1f} pay/pen | "
          f"${p.sum()/N:>+6.3f}/pen | maruz ${m.sum()/N:>5.2f}")

# --- GERCEK: sig bantta oynayanlarin pencere duzeyi sonucu ---
mx=df.groupby(['wallet','start_ts']).price.transform('max')
print("\n### GERCEK DOLUMLAR: cuzdan-pencerede EN YUKSEK alim fiyatina gore")
print(f"  {'en yuksek alim':<20} {'cuzdan-pen':>11} {'kr/pay':>8}   {'GA95':>18}")
for lo,hi in [(0,.25),(.25,.35),(.35,.45),(.45,.55),(.55,.70),(.70,1.01)]:
    s=df[(mx>=lo)&(mx<hi)]
    if len(s)<500: continue
    d=s.groupby('gun').agg(p=('pnl','sum'),q=('shares','sum'))
    r=np.random.default_rng(2)
    b=[100*d.p.values[i].sum()/d.q.values[i].sum() for i in (r.integers(0,len(d),len(d)) for _ in range(1500))]
    n=s.groupby(['wallet','start_ts']).ngroups
    print(f"  {lo:.2f}-{hi:.2f}{'':<12} {n:>11,} {100*s.pnl.sum()/s.shares.sum():>+8.2f}   "
          f"[{np.percentile(b,2.5):>+6.2f},{np.percentile(b,97.5):>+6.2f}]")
