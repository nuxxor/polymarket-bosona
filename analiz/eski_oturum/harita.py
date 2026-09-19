"""KESIN TARAMA: maker ALIS dolumlari, (fiyat x zaman) hucreleri.
HAVUZLANMIS kr/pay + GUN-KUMELI bootstrap (esli pay/pnl cekimi).
Kiyas sinifi = bizim kisitimiz: cuzdan-pencerede hic >0.40 alim yok."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
mx=df.groupby(['wallet','start_ts']).price.transform('max')
df=df[mx<=0.40]
df['kz']=df.start_ts.map(kz)
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.floor('D')
print(f"kiyas sinifi: {len(df):,} dolum | {df.gun.nunique()} gun | {df.shares.sum():,.0f} pay")
print(f"TABAN (hepsi): {100*df.pnl.sum()/df.shares.sum():+.2f} kr/pay\n")

gun=df.gun.values; G=np.unique(gun)
def ci(s,n=2000):
    if len(s)<200: return (np.nan,np.nan,0)
    d=s.groupby('gun').agg(p=('pnl','sum'),q=('shares','sum'))
    if len(d)<5: return (np.nan,np.nan,len(d))
    P=d.p.values; Q=d.q.values; r=np.random.default_rng(11); b=[]
    for _ in range(n):
        i=r.integers(0,len(d),len(d))          # ESLI cekim
        b.append(100*P[i].sum()/Q[i].sum())
    return (np.percentile(b,2.5),np.percentile(b,97.5),len(d))

PB=[(0.00,0.10),(0.10,0.16),(0.16,0.22),(0.22,0.28),(0.28,0.34),(0.34,0.41)]
TB=[(0,60),(60,120),(120,180),(180,240),(240,301)]
print("### HUCRE HARITASI — havuzlanmis kr/pay [gun-kumeli GA95]")
print(f"{'fiyat':<12}"+"".join(f"{f't{a}-{b}':>22}" for a,b in TB))
anl=[]
for p0,p1 in PB:
    sat=f"{p0:.2f}-{p1:.2f}  "
    for t0,t1 in TB:
        s=df[(df.price>=p0)&(df.price<p1)&(df.t_rel_s>=t0)&(df.t_rel_s<t1)]
        if len(s)<200: sat+=f"{'-':>22}"; continue
        v=100*s.pnl.sum()/s.shares.sum(); lo,hi,ng=ci(s)
        yz='*' if (lo==lo and (lo>0 or hi<0)) else ' '
        sat+=f"{v:>+7.2f}[{lo:>+6.2f},{hi:>+6.2f}]{yz}"
        if lo==lo and lo>0: anl.append((v,lo,hi,p0,p1,t0,t1,s.shares.sum(),ng))
    print(sat)
print("\n(* = GA sifiri dislıyor)")
print("\n### SIFIRDAN AYRISAN ARTI HUCRELER")
if not anl: print("  YOK — ulasabildigimiz uzayda hicbir hucre sifirdan ayrismiyor.")
for v,lo,hi,p0,p1,t0,t1,pay,ng in sorted(anl,reverse=True):
    print(f"  px {p0:.2f}-{p1:.2f} & t{t0}-{t1}: {v:+.2f} [{lo:+.2f},{hi:+.2f}] | {pay:,.0f} pay | {ng} gun")
