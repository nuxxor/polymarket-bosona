"""TAM EV — secim artefakti YOK. Her (p,q) politikasi icin 4506 pencerede
gerceklesmis PnL: cift kurulursa kar, tek bacak kalirsa KAYIP dahil.
Varsayim: fiyat seviyeye degerse doluruz (kuyruk yok sayilir) -> UST SINIR."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
mn=df.groupby(['start_ts','outcome_idx']).price.min().unstack(); mn.columns=['m0','m1']
mn=mn.dropna(); m0=mn.m0.values; m1=mn.m1.values
kv=np.array([kz[s] for s in mn.index]); N=len(mn)
gun=pd.to_datetime(mn.index,unit='s').floor('D').values; G=np.unique(gun)
print(f"pencere: {N} | gun: {len(G)}\n")

def ev(p,q):
    f0=m0<=p; f1=m1<=q                      # her bacak doldu mu
    pnl=np.zeros(N); pay=np.zeros(N)
    up=(kv==0)
    pnl+= f0*(np.where(up,1.0,0.0)-p); pay+=f0*1.0
    pnl+= f1*(np.where(up,0.0,1.0)-q); pay+=f1*1.0
    return pnl,pay
def gunci(pnl,pay,n=2000):
    P=np.array([pnl[gun==g].sum() for g in G]); Q=np.array([pay[gun==g].sum() for g in G])
    r=np.random.default_rng(5)
    b=[100*P[i].sum()/max(Q[i].sum(),1e-9) for i in (r.integers(0,len(G),len(G)) for _ in range(n))]
    return np.percentile(b,2.5),np.percentile(b,97.5)

gr=[round(x,2) for x in np.arange(0.02,0.99,0.03)]
res=[]
for p in gr:
    for q in gr:
        if p+q>=1.0: continue
        pnl,pay=ev(p,q)
        if pay.sum()<1000: continue
        res.append((100*pnl.sum()/pay.sum(),p,q,pay.sum(),(( m0<=p)&(m1<=q)).mean()))
res.sort(reverse=True)
print("### EN IYI 12 POLITIKA (tam EV, essiz bacak kayiplari DAHIL)")
print(f"  {'p(Up)':>6} {'q(Dn)':>6} {'cift':>6} {'cift%':>7} {'kr/pay':>8}   {'gun-kumeli GA95':>20}")
for v,p,q,pay,ul in res[:12]:
    lo,hi=gunci(*ev(p,q))
    print(f"  {p:>6.2f} {q:>6.2f} {p+q:>6.2f} {100*ul:>6.1f}% {v:>+8.2f}   [{lo:>+7.2f},{hi:>+7.2f}]")
print("\n### EN KOTU 5")
for v,p,q,pay,ul in res[-5:]:
    print(f"  {p:>6.2f} {q:>6.2f} {p+q:>6.2f} {100*ul:>6.1f}% {v:>+8.2f}")
print("\n### BELIRLI POLITIKALAR")
for ad,p,q in [('BIZ v2 ust basamak 0.34/0.34',.34,.34),('BIZ derin 0.16/0.16',.16,.16),
               ('bosona 14:25Z 0.80/0.02',.80,.02),('asim 0.80/0.10',.80,.10),
               ('asim 0.70/0.15',.70,.15),('asim 0.50/0.02',.50,.02),('simetrik 0.26/0.26',.26,.26)]:
    pnl,pay=ev(p,q); lo,hi=gunci(pnl,pay)
    print(f"  {ad:<30} cift {p+q:.2f} | {100*pnl.sum()/pay.sum():>+7.2f} kr/pay [{lo:+.2f},{hi:+.2f}] | {pay.sum():,.0f} pay")
