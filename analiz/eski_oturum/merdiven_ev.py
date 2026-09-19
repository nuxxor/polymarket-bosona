"""GERCEK MERDIVEN SIMULASYONU: 6 basamak x 5 pay, iki taraf, 4506 pencere.
Essiz bacak kayiplari DAHIL. Gun-kumeli GA. Kuyruk yok sayilir (ust sinir)."""
import pandas as pd, json, numpy as np, itertools
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
mn=df.groupby(['start_ts','outcome_idx']).price.min().unstack(); mn.columns=['m0','m1']
mn=mn.dropna(); m0=mn.m0.values; m1=mn.m1.values
kv=np.array([kz[s] for s in mn.index]); N=len(mn)
gun=pd.to_datetime(mn.index,unit='s').floor('D').values; G=np.unique(gun)
KLIP=5.0

def sim(rungs):
    r=np.array(rungs)
    pnl=np.zeros(N); pay=np.zeros(N); mal=np.zeros(N)
    for px in r:
        for oi,m in ((0,m0),(1,m1)):
            f=(m<=px)
            kaz=(kv==oi).astype(float)
            pnl+=f*KLIP*(kaz-px); pay+=f*KLIP; mal+=f*KLIP*px
    return pnl,pay,mal
def ci(pnl,pay,n=2000):
    P=np.array([pnl[gun==g].sum() for g in G]); Q=np.array([pay[gun==g].sum() for g in G])
    r=np.random.default_rng(9)
    b=[100*P[i].sum()/max(Q[i].sum(),1e-9) for i in (r.integers(0,len(G),len(G)) for _ in range(n))]
    return np.percentile(b,2.5),np.percentile(b,97.5)
def rap(ad,rungs):
    pnl,pay,mal=sim(rungs); lo,hi=ci(pnl,pay)
    reb=0.014*sum(1 for _ in rungs)  # yer tutucu degil: asagida gercek hesap
    # gercek rebate: 0.014*q*p*(1-p) her dolum icin
    rb=0.0
    for px in rungs:
        for m in (m0,m1): rb+=((m<=px)*KLIP).sum()*0.014*px*(1-px)
    print(f"  {ad:<34} {100*pnl.sum()/pay.sum():>+7.2f} kr/pay [{lo:+.2f},{hi:+.2f}] | "
          f"{pay.sum()/N:>5.1f} pay/pen | ${pnl.sum()/N:>+6.3f}/pen | rebate +{100*rb/pay.sum():.2f} kr/pay | "
          f"maruz ${mal.sum()/N:>5.2f}")
print(f"pencere {N} | gun {len(G)} | klip {KLIP}\n")
print("### MEVCUT ve ADAY MERDIVENLER  (her basamak iki tarafa da)")
rap('v2 CANLI [.34 .30 .26 .22 .20 .16]',[.34,.30,.26,.22,.20,.16])
rap('v1 eski  [.40 .34 .28 .22 .16 .10]',[.40,.34,.28,.22,.16,.10])
rap('DERIN-A  [.26 .22 .18 .14 .10 .06]',[.26,.22,.18,.14,.10,.06])
rap('DERIN-B  [.24 .20 .16 .12 .08 .04]',[.24,.20,.16,.12,.08,.04])
rap('DERIN-C  [.20 .16 .12 .09 .06 .03]',[.20,.16,.12,.09,.06,.03])
rap('COK DERIN[.14 .11 .08 .06 .04 .02]',[.14,.11,.08,.06,.04,.02])
rap('GENIS    [.30 .24 .18 .12 .07 .03]',[.30,.24,.18,.12,.07,.03])
rap('tek bas. [.20]',[.20])
rap('tek bas. [.08]',[.08])
rap('iki bas. [.20 .08]',[.20,.08])
rap('uc bas.  [.22 .14 .07]',[.22,.14,.07])
print("\n### BASAMAK BASINA MARJINAL KATKI (v2 CANLI tabanindan)")
tb=[.34,.30,.26,.22,.20,.16]
pnl0,pay0,_=sim(tb)
for px in tb:
    alt=[x for x in tb if x!=px]
    p1,q1,_=sim(alt)
    print(f"  {px:.2f} basamagi cikarilinca: {100*p1.sum()/q1.sum():>+7.2f} kr/pay "
          f"(taban {100*pnl0.sum()/pay0.sum():+.2f}) -> basamagin katkisi {100*pnl0.sum()/pay0.sum()-100*p1.sum()/q1.sum():>+6.2f}")
