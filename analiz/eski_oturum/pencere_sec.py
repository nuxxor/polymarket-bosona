"""KAZANAN PENCERE ONCEDEN BILINEBILIR MI?
Bizim merdivenimizi 4506 pencerede simule et -> pencere basina PnL.
Sonra: PENCERE ACILMADAN ONCE bilinen seylerle ongorulebiliyor mu?
ORNEK DISI (zaman bolunmus) test. Gun-kumeli GA."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','t_rel_s'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]

# --- pencere ozetleri ---
g=df.groupby(['start_ts','outcome_idx']).price
mn=g.min().unstack(); mx=g.max().unstack(); mn.columns=['m0','m1']; mx.columns=['x0','x1']
W=mn.join(mx).dropna()
W['kz']=[kz[s] for s in W.index]
W['savrulma']=(W.x0-W.m0)          # Up fiyatinin pencere ici menzili = savrulma
W=W.sort_index()

KLIP=5.0
def sim(r,W):
    p=np.zeros(len(W)); q=np.zeros(len(W))
    for px in r:
        for oi,col in ((0,'m0'),(1,'m1')):
            f=(W[col].values<=px)
            p+=f*KLIP*((W.kz.values==oi)-px); q+=f*KLIP
    return p,q
IZG=[.34,.30,.26,.22,.20,.16]
W['pnl'],W['pay']=sim(IZG,W)
print(f"pencere {len(W)} | toplam PnL ${W.pnl.sum():+.0f} | {100*W.pnl.sum()/W.pay.sum():+.2f} kr/pay\n")

# --- 1) KAR NE KADAR YOGUN? ---
s=np.sort(W.pnl.values)[::-1]; T=W.pnl.sum()
print("### KAR YOGUNLUGU (bizim merdiven, 4506 pencere)")
for k in (1,5,10,25,50,100,250):
    print(f"  en iyi {k:>4} pencere: ${s[:k].sum():>+8.0f}  = toplamin %{100*s[:k].sum()/T:>6.1f}")
print(f"  artida biten pencere: {(W.pnl>0).sum():,}/{len(W):,} = %{100*(W.pnl>0).mean():.1f}")

# --- 2) KAZANAN PENCERE = SAVRULAN PENCERE MI? ---
print("\n### PENCERE ICI SAVRULMAYA GORE (bu pencere ACILDIKTAN sonra bilinir)")
W['sb']=pd.qcut(W.savrulma,5,labels=['en sakin','2','3','4','en oynak'])
for b in W.sb.cat.categories:
    x=W[W.sb==b]
    print(f"  {b:<9}: {len(x):>4} pen | savrulma {x.savrulma.mean():.3f} | "
          f"${x.pnl.sum():>+7.0f} | {100*x.pnl.sum()/x.pay.sum():>+7.2f} kr/pay | artida %{100*(x.pnl>0).mean():.0f}")

# --- 3) ONCEDEN BILINEBILIR MI? onceki pencerenin savrulmasi ---
W['onceki_savrulma']=W.savrulma.shift(1)
W['onceki_pnl']=W.pnl.shift(1)
W['bosluk']=pd.Series(W.index,index=W.index).diff()
V=W[(W.bosluk==300)].dropna(subset=['onceki_savrulma'])
print(f"\n### ONCEDEN BILINEBILIR MI? (ardisik pencere ciftleri: {len(V):,})")
print(f"  savrulma kaliciligi (Spearman, onceki vs simdiki): "
      f"{pd.Series(V.savrulma).corr(pd.Series(V.onceki_savrulma),method='spearman'):+.3f}")
print(f"  PnL kaliciligi      (Spearman): "
      f"{pd.Series(V.pnl).corr(pd.Series(V.onceki_pnl),method='spearman'):+.3f}")
V['ob']=pd.qcut(V.onceki_savrulma,5,labels=['en sakin','2','3','4','en oynak'])
print("  ONCEKI pencerenin savrulmasina gore BU pencerenin sonucu:")
for b in V.ob.cat.categories:
    x=V[V.ob==b]
    print(f"    {b:<9}: {len(x):>4} pen | ${x.pnl.sum():>+7.0f} | {100*x.pnl.sum()/x.pay.sum():>+7.2f} kr/pay")

# --- 4) ORNEK DISI: ilk yari ogren, ikinci yari test ---
V=V.copy(); n=len(V); tr=V.iloc[:n//2]; te=V.iloc[n//2:]
esik=tr.onceki_savrulma.quantile(0.6)
print(f"\n### ORNEK DISI TEST (ilk yari esik ogrenildi: onceki_savrulma>{esik:.3f})")
for ad,x in [('EGITIM (ilk yari)',tr),('TEST  (ikinci yari)',te)]:
    sec=x[x.onceki_savrulma>esik]; ka=x[x.onceki_savrulma<=esik]
    print(f"  {ad}: SECILEN {len(sec):>4} pen {100*sec.pnl.sum()/max(sec.pay.sum(),1):>+7.2f} kr/pay | "
          f"ELENEN {len(ka):>4} pen {100*ka.pnl.sum()/max(ka.pay.sum(),1):>+7.2f} | "
          f"HEPSI {100*x.pnl.sum()/x.pay.sum():>+7.2f}")

# --- 5) SAATE GORE (tamamen statik, sizinti yok) ---
V['saat']=pd.to_datetime(V.index,unit='s').hour
print("\n### SAATE GORE (UTC) — statik, sizintisiz")
h=V.groupby('saat').apply(lambda x: pd.Series({'pen':len(x),'krpay':100*x.pnl.sum()/max(x.pay.sum(),1)}),include_groups=False)
h=h.sort_values('krpay',ascending=False)
print('  EN IYI 5 SAAT:'); print('   ',h.head(5).to_dict('index'))
print('  EN KOTU 5 SAAT:'); print('   ',h.tail(5).to_dict('index'))
