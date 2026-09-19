"""TAM (p,q) UZAYI — tavani 0.40'ta kesmeden. bosona (0.80,0.02) bolgesi dahil."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','t_rel_s'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
mn=df.groupby(['start_ts','outcome_idx']).price.min().unstack()
mn.columns=['m0','m1']; mn=mn.dropna()
m0=mn.m0.values; m1=mn.m1.values; N=len(mn)
kzv=np.array([kz[s] for s in mn.index])   # kazanan taraf (0=Up,1=Down)
print(f"pencere: {N}\n")

gr=[round(x,2) for x in np.arange(0.02,0.99,0.02)]
res=[]
for p in gr:
    a=(m0<=p)
    for q in gr:
        if p+q>=1.0: continue
        ul=(a&(m1<=q)).mean()
        res.append((ul*(1.0-p-q)/2*100, p,q,p+q,ul))
res.sort(reverse=True)
print("### TAM UZAY — EN IYI 15 (p=Up basamagi, q=Down basamagi)")
print(f"  {'p':>5} {'q':>5} {'cift':>6} {'ulasil':>8} {'BEKLENEN':>10}")
for b,p,q,cm,ul in res[:15]:
    print(f"  {p:.2f} {q:.2f} {cm:>6.2f} {100*ul:>7.1f}% {b:>+10.2f}")

print("\n### SIMETRIK KOSEGEN (tam menzil)")
print(f"  {'p=q':>6} {'cift':>6} {'ulasil':>8} {'BEKLENEN':>10}")
for p in [0.10,0.20,0.26,0.30,0.34,0.40,0.45,0.48]:
    ul=((m0<=p)&(m1<=p)).mean()
    print(f"  {p:.2f} {2*p:>6.2f} {100*ul:>7.1f}% {ul*(1-2*p)/2*100:>+10.2f}")

print("\n### BELIRLI NOKTALAR")
for ad,p,q in [('BIZ v2 (0.34/0.34)',0.34,0.34),('BIZ v2 en derin (0.16/0.16)',0.16,0.16),
               ('bosona 14:25Z (0.80/0.02)',0.80,0.02),('bosona 14:20Z (0.90/0.25)',0.90,0.25),
               ('asimetrik (0.80/0.10)',0.80,0.10),('asimetrik (0.70/0.20)',0.70,0.20),
               ('asimetrik (0.90/0.05)',0.90,0.05),('asimetrik (0.60/0.30)',0.60,0.30)]:
    ul=((m0<=p)&(m1<=q)).mean()
    print(f"  {ad:<28} cift {p+q:.2f} | ulasil %{100*ul:>5.1f} | BEKLENEN {ul*(1-p-q)/2*100:>+7.2f}")

print("\n### ASIMETRIK CIFT: hangi bacak kazanir?")
# p yuksek (Up pahali) + q dusuk (Down bedava) -> Up kazanir mi?
for p,q in [(0.80,0.02),(0.80,0.10),(0.70,0.20)]:
    s=(m0<=p)&(m1<=q)
    if s.sum(): print(f"  ({p},{q}): {s.sum()} pencere, Up kazanma %{100*(kzv[s]==0).mean():.1f}")
