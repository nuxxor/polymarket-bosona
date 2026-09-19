"""BTC OYNAKLIK KAPISI — gun-kumeli GA + hacim etkisi + kol B ile de test."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
g=df.groupby(['start_ts','outcome_idx']).price.min().unstack(); g.columns=['m0','m1']
W=g.dropna().sort_index(); W['kz']=[kz[s] for s in W.index]
h=pd.read_parquet('data/analysis/pm_chainlink_history_20260913_v1/HIST_spot.parquet')[['ts','price']].dropna().sort_values('ts')
ts=h.ts.values.astype(np.int64); pr=h.price.values
def vol(S,g_=300):
    i0=np.searchsorted(ts,S-g_); i1=np.searchsorted(ts,S)
    if i1-i0<30: return np.nan
    x=pr[i0:i1]; return 1e4*(x.max()-x.min())/x[-1]
W['vol5']=[vol(s) for s in W.index.values]
W=W.dropna(subset=['vol5']).copy()
W['gun']=pd.to_datetime(W.index,unit='s').floor('D')
KLIP=5.0
def sim(r):
    p=np.zeros(len(W)); q=np.zeros(len(W))
    for px in r:
        for oi,c in ((0,'m0'),(1,'m1')):
            f=(W[c].values<=px); p+=f*KLIP*((W.kz.values==oi)-px); q+=f*KLIP
    return p,q
def ci(sub,pcol,qcol,n=4000):
    d=sub.groupby('gun').agg(p=(pcol,'sum'),q=(qcol,'sum'))
    if len(d)<5: return (np.nan,np.nan)
    P=d.p.values;Q=d.q.values;r=np.random.default_rng(13)
    v=[100*P[i].sum()/max(Q[i].sum(),1e-9) for i in (r.integers(0,len(d),len(d)) for _ in range(n))]
    return np.percentile(v,2.5),np.percentile(v,97.5)
G=len(W.gun.unique())
for ad,IZG in [('KOL A [.34..16]',[.34,.30,.26,.22,.20,.16]),('KOL B [.20..03]',[.20,.16,.12,.09,.06,.03])]:
    W['pnl'],W['pay']=sim(IZG)
    print(f"\n########## {ad}   ({len(W):,} pencere / {G} gun)")
    print(f"  KAPISIZ (hepsi): {100*W.pnl.sum()/W.pay.sum():+.2f} kr/pay "
          f"[{ci(W,'pnl','pay')[0]:+.2f},{ci(W,'pnl','pay')[1]:+.2f}] | ${W.pnl.sum()/G:+.2f}/gun*")
    for e in (12,15,19,25):
        s=W[W.vol5>e]; k=W[W.vol5<=e]
        lo,hi=ci(s,'pnl','pay')
        print(f"  vol5>{e:>2} bps: SECILEN {len(s):>4} pen (%{100*len(s)/len(W):>4.1f}) "
              f"{100*s.pnl.sum()/s.pay.sum():>+6.2f} [{lo:+.2f},{hi:+.2f}] | "
              f"ELENEN {100*k.pnl.sum()/k.pay.sum():>+6.2f} | ${s.pnl.sum()/G:>+6.2f}/gun*")
print("\n* gun basina $ = 19 gunluk zincir orneginin gunluk ortalamasi (bizim tek pazar, 5 pay klip)")
print("  NOT: bu simulasyon 'fiyat degerse doluruz' varsayar -> MUTLAK sayilar ust sinir.")
print("       Kapinin degeri MUTLAK degil, SECILEN-ELENEN FARKINDA.")
