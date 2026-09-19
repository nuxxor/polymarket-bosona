"""IZGARA OPTIMUMU: cift maliyeti ucuzsa kar buyuk ama NADIR.
Her pencerede iki tarafin da islem gordugu EN DUSUK fiyatlari bul ->
hangi (p,q) ciftlerinin ULASILABILIR oldugunu say -> beklenen degeri hesapla."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','t_rel_s'])
df=df[df.side.str.upper()=='BUY']
df=df[df.start_ts.isin(kz.keys())]
# her pencere x taraf icin EN DUSUK islem goren fiyat (maker alis = o fiyata inildi)
mn=df.groupby(['start_ts','outcome_idx']).price.min().unstack()
mn.columns=['m0','m1']; mn=mn.dropna()
N=len(mn)
print(f"pencere: {N}\n")
print("### (p,q) CIFTI ULASILABILIRLIGI ve BEKLENEN DEGER")
print("  Up'a p, Down'a q koyarsan; cift ancak m0<=p VE m1<=q ise kurulur")
print(f"  {'p=q':>6} {'cift mal':>9} {'ulasilabilir':>13} {'cift kari':>10} {'BEKLENEN':>10}")
en=[]
for px in [round(x,2) for x in np.arange(0.20,0.51,0.02)]:
    ul=((mn.m0<=px)&(mn.m1<=px)).mean()
    cm=2*px
    kar=(1.0-cm)/2*100      # pay basina kurus
    bek=ul*kar
    en.append((bek,px,ul,cm,kar))
    print(f"  {px:.2f} {cm:>9.2f} {100*ul:>12.1f}% {kar:>+9.2f} {bek:>+10.2f}")
b=max(en)
print(f"\n  OPTIMUM (simetrik): p=q={b[1]:.2f} -> cift {b[3]:.2f}, ulasilirlik %{100*b[2]:.0f}, beklenen {b[0]:+.2f} kr/pay")
print(f"  BIZIM en ust basamak 0.34 -> ulasilirlik %{100*((mn.m0<=0.34)&(mn.m1<=0.34)).mean():.1f}")
print(f"  ESKI en ust basamak 0.40 -> ulasilirlik %{100*((mn.m0<=0.40)&(mn.m1<=0.40)).mean():.1f}")
print(f"  bosona ~0.435 ort      -> ulasilirlik %{100*((mn.m0<=0.435)&(mn.m1<=0.435)).mean():.1f}")
print("\n### ASIMETRIK: farkli p ve q")
print(f"  {'p (Up)':>7} {'q (Down)':>9} {'cift':>6} {'ulasil':>8} {'BEKLENEN':>10}")
iyi=[]
for p in [round(x,2) for x in np.arange(0.24,0.56,0.04)]:
    for q in [round(x,2) for x in np.arange(0.24,0.56,0.04)]:
        ul=((mn.m0<=p)&(mn.m1<=q)).mean(); cm=p+q
        if cm>=1.0: continue
        bek=ul*(1.0-cm)/2*100
        iyi.append((bek,p,q,cm,ul))
iyi.sort(reverse=True)
for bek,p,q,cm,ul in iyi[:6]:
    print(f"  {p:>7.2f} {q:>9.2f} {cm:>6.2f} {100*ul:>7.1f}% {bek:>+10.2f}")
