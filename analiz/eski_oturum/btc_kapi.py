"""PENCERE SECIMI — BTC oynakligi ile. Pencere ACILMADAN ONCE bilinen bilgi.
Egitim/test ZAMAN bolunmus. Gun-kumeli GA. Sizinti yok."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
g=df.groupby(['start_ts','outcome_idx']).price.min().unstack(); g.columns=['m0','m1']
W=g.dropna().sort_index(); W['kz']=[kz[s] for s in W.index]
KLIP=5.0; IZG=[.34,.30,.26,.22,.20,.16]
p=np.zeros(len(W)); q=np.zeros(len(W))
for px in IZG:
    for oi,c in ((0,'m0'),(1,'m1')):
        f=(W[c].values<=px); p+=f*KLIP*((W.kz.values==oi)-px); q+=f*KLIP
W['pnl']=p; W['pay']=q

# --- BTC oynakligi: pencere ACILMADAN ONCEKI 5 ve 15 dk ---
h=pd.read_parquet('data/analysis/pm_chainlink_history_20260913_v1/HIST_spot.parquet')
h=h[['ts','price']].dropna().sort_values('ts')
ts=h.ts.values.astype(np.int64); pr=h.price.values
def vol(S,gerisi):
    i0=np.searchsorted(ts,S-gerisi); i1=np.searchsorted(ts,S)
    if i1-i0<30: return np.nan
    x=pr[i0:i1]
    return 1e4*(x.max()-x.min())/x[-1]      # bps menzil
S=W.index.values
W['vol5']=[vol(s,300) for s in S]
W['vol15']=[vol(s,900) for s in S]
V=W.dropna(subset=['vol5','vol15']).copy()
V['gun']=pd.to_datetime(V.index,unit='s').floor('D')
print(f"BTC verisi eslesen pencere: {len(V):,} / {len(W):,}  ({V.gun.nunique()} gun)")
print(f"taban: {100*V.pnl.sum()/V.pay.sum():+.2f} kr/pay\n")

print("### ONCEKI 5 DK BTC OYNAKLIGINA GORE (pencere acilmadan ONCE bilinir)")
V['b5']=pd.qcut(V.vol5,5,labels=['en sakin','2','3','4','en oynak'])
for b in V.b5.cat.categories:
    x=V[V.b5==b]
    print(f"  {b:<9}: {len(x):>4} pen | vol {x.vol5.mean():>6.1f} bps | "
          f"{100*x.pnl.sum()/x.pay.sum():>+7.2f} kr/pay | artida %{100*(x.pnl>0).mean():>4.0f}")
print("\n### ONCEKI 15 DK")
V['b15']=pd.qcut(V.vol15,5,labels=['en sakin','2','3','4','en oynak'])
for b in V.b15.cat.categories:
    x=V[V.b15==b]
    print(f"  {b:<9}: {len(x):>4} pen | vol {x.vol15.mean():>6.1f} bps | "
          f"{100*x.pnl.sum()/x.pay.sum():>+7.2f} kr/pay | artida %{100*(x.pnl>0).mean():>4.0f}")

# --- kalicilik: onceki 5dk vol -> pencere ICI BTC menzili ---
W2=W.copy(); W2['ici']=[vol(s+300,300) for s in W2.index.values]   # pencere ici menzil
K=W2.dropna(subset=['vol5','ici'])
print(f"\n### OYNAKLIK KALICI MI? onceki 5dk vol -> pencere ICI menzil")
print(f"  Spearman: {K.vol5.corr(K.ici,method='spearman'):+.3f}  (n={len(K):,})")
print(f"  pencere ICI menzil -> PnL Spearman: {K.ici.corr(K.pnl,method='spearman'):+.3f}")

# --- ORNEK DISI ---
n=len(V); tr=V.iloc[:n//2]; te=V.iloc[n//2:]
print(f"\n### ORNEK DISI (ilk yari {len(tr)} pen -> esik ogren, ikinci yari {len(te)} pen test)")
for qq in (0.5,0.6,0.7,0.8):
    e=tr.vol5.quantile(qq)
    a=tr[tr.vol5>e]; b=tr[tr.vol5<=e]; c=te[te.vol5>e]; d=te[te.vol5<=e]
    fa=100*a.pnl.sum()/max(a.pay.sum(),1)-100*b.pnl.sum()/max(b.pay.sum(),1)
    fc=100*c.pnl.sum()/max(c.pay.sum(),1)-100*d.pnl.sum()/max(d.pay.sum(),1)
    print(f"  esik q{qq:.0%} (vol>{e:>5.1f} bps): EGITIM fark {fa:>+6.2f} | "
          f"TEST secilen {100*c.pnl.sum()/max(c.pay.sum(),1):>+6.2f} elenen {100*d.pnl.sum()/max(d.pay.sum(),1):>+6.2f} "
          f"FARK {fc:>+6.2f}")
