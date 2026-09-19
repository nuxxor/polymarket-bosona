"""AYNI CIFT MALIYETINDE: simetrik yapi mi asimetrik yapi mi kazaniyor?
Gerceklesmis zincir verisi, cuzdan-pencere duzeyi (karar birimi)."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
df['kz']=df.start_ts.map(kz)
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares
print(f"{len(df):,} dolum")

g=df.groupby(['wallet','start_ts','outcome_idx']).agg(
    pay=('shares','sum'), mal=('price','mean'), pmin=('price','min'), pmax=('price','max'),
    pnl=('pnl','sum')).unstack()
g=g.fillna(0)
u=pd.DataFrame({'pay0':g[('pay',0)],'pay1':g[('pay',1)],
                'mal0':g[('mal',0)],'mal1':g[('mal',1)],
                'min0':g[('pmin',0)],'min1':g[('pmin',1)],
                'pnl':g[('pnl',0)]+g[('pnl',1)]})
u['toppay']=u.pay0+u.pay1
u=u[(u.pay0>0)&(u.pay1>0)]          # yalniz CIFT kuranlar
u['cift']=np.minimum(u.pay0,u.pay1)
u['cmal']=u.mal0+u.mal1
print(f"cift kuran cuzdan-pencere: {len(u):,}\n")

def ga(s,n=1500):
    v=s.values
    if len(v)<20: return (np.nan,np.nan)
    r=np.random.default_rng(7); b=[np.nanmean(r.choice(v,len(v))) for _ in range(n)]
    return (np.percentile(b,2.5),np.percentile(b,97.5))

# YAPI: iki bacagin fiyat farki
u['fark']=abs(u.mal0-u.mal1)
u['yapi']=np.where(u.fark<0.15,'SIMETRIK (fark<0.15)',
          np.where(u.fark<0.40,'ORTA (0.15-0.40)','ASIMETRIK (fark>=0.40)'))
u['mband']=pd.cut(u.cmal,[0,.70,.85,.95,1.00,1.10,9],
    labels=['0.00-0.70','0.70-0.85','0.85-0.95','0.95-1.00','1.00-1.10','1.10+'])

print("### AYNI CIFT MALIYETI BANDI ICINDE, YAPIYA GORE kr/pay")
print(f"  {'cift mal':<12} {'yapi':<24} {'kayit':>8} {'kr/pay':>8}   {'GA95':>18}")
for mb in u.mband.cat.categories:
    for yp in ['SIMETRIK (fark<0.15)','ORTA (0.15-0.40)','ASIMETRIK (fark>=0.40)']:
        s=u[(u.mband==mb)&(u.yapi==yp)]
        if len(s)<30: continue
        kp=100*s.pnl.sum()/s.toppay.sum()
        lo,hi=ga(100*s.pnl/s.toppay)
        print(f"  {mb:<12} {yp:<24} {len(s):>8,} {kp:>+8.2f}   [{lo:>+6.2f},{hi:>+6.2f}]")

print("\n### BOSONA YAPISI: bir bacak >=0.65, diger bacak <=0.15")
bos=u[((u.mal0>=.65)&(u.mal1<=.15))|((u.mal1>=.65)&(u.mal0<=.15))]
biz=u[(u.mal0<=.40)&(u.mal1<=.40)]
for ad,s in [('bosona yapisi (>=0.65 + <=0.15)',bos),('BIZIM yapi (iki bacak da <=0.40)',biz),('hepsi',u)]:
    if not len(s): continue
    kp=100*s.pnl.sum()/s.toppay.sum(); lo,hi=ga(100*s.pnl/s.toppay)
    print(f"  {ad:<34} {len(s):>7,} kayit | cift mal {s.cmal.mean():.3f} | {kp:>+7.2f} kr/pay [{lo:+.2f},{hi:+.2f}]")
