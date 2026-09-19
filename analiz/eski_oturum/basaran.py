"""BASARANLAR: iki bacagi da <=0.40'a kuranlar ne yapiyor, bizden farki ne?
Kiyas sinifi: yalniz <=0.40 alim yapan cuzdan-pencereler (bizim kisit)."""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','outcome_idx','side','price','shares','wallet','t_rel_s'])
df=df[df.side.str.upper()=='BUY']; df=df[df.start_ts.isin(kz.keys())]
df['kz']=df.start_ts.map(kz)
df['pnl']=np.where(df.outcome_idx==df.kz,1.0-df.price,-df.price)*df.shares

# KIYAS SINIFI: cuzdan-pencerede HIC 0.40 ustu alim yok (bizim tavan)
mx=df.groupby(['wallet','start_ts']).price.max()
ok=mx[mx<=0.40].index
df=df.set_index(['wallet','start_ts']).loc[ok].reset_index()
print(f"kiyas sinifi (yalniz <=0.40): {df.groupby(['wallet','start_ts']).ngroups:,} cuzdan-pencere")

a=df.groupby(['wallet','start_ts']).agg(
    pay=('shares','sum'), n=('shares','size'), klip=('shares','median'),
    ilk=('t_rel_s','min'), son=('t_rel_s','max'), omur=('t_rel_s',lambda s:s.max()-s.min()),
    pnl=('pnl','sum'))
t=df.groupby(['wallet','start_ts','outcome_idx']).shares.sum().unstack().fillna(0)
a['pay0']=t.get(0,0); a['pay1']=t.get(1,0)
a['cift']=np.minimum(a.pay0,a.pay1)
a['ciftmi']=a.cift>0
print(f"  bunlarin %{100*a.ciftmi.mean():.1f}'i cift kurmus\n")

def ok_(s,lbl):
    if len(s)<50: return
    print(f"  {lbl:<26} {len(s):>7,} | cift %{100*s.ciftmi.mean():>5.1f} | "
          f"{100*s.pnl.sum()/s.pay.sum():>+7.2f} kr/pay | klip {s.klip.median():>5.1f} | "
          f"n {s.n.median():>4.0f} | son t {s.son.median():>5.0f}")

print("### CIFT KURMA ORANI — neye gore degisiyor?")
print("\n[SON DOLUM ZAMANI]  (biz: GEC_KES=200, yani t=200'de kesiyoruz)")
for lo,hi in [(0,60),(60,120),(120,180),(180,240),(240,301)]:
    ok_(a[(a.son>=lo)&(a.son<hi)], f"son dolum t{lo}-{hi}")
print("\n[EMIR SAYISI / PENCERE]  (biz: 6 basamak)")
for lo,hi in [(1,2),(2,4),(4,7),(7,13),(13,10**9)]:
    ok_(a[(a.n>=lo)&(a.n<hi)], f"{lo}-{hi-1} dolum")
print("\n[KLIP BOYU]  (biz: 5 pay)")
for lo,hi in [(1,5),(5,10),(10,25),(25,100),(100,10**9)]:
    ok_(a[(a.klip>=lo)&(a.klip<hi)], f"klip {lo}-{hi-1} pay")
print("\n[PENCEREDE KALIS SURESI: ilk->son dolum]")
for lo,hi in [(0,1),(1,60),(60,120),(120,200),(200,301)]:
    ok_(a[(a.omur>=lo)&(a.omur<hi)], f"omur {lo}-{hi}s")

print("\n### BIZ vs BASARANLAR — dogrudan kiyas")
biz=a[(a.klip>=3)&(a.klip<=9)&(a.son<=120)]
bas=a[a.ciftmi]
for lbl,s in [('BIZ (klip 3-9, son dolum<=120)',biz),('CIFT KURANLAR (hepsi)',bas),
              ('CIFT KURANLAR klip<=9',bas[bas.klip<=9])]:
    if len(s): print(f"  {lbl:<32} {len(s):>7,} | cift %{100*s.ciftmi.mean():>5.1f} | "
        f"{100*s.pnl.sum()/s.pay.sum():>+7.2f} kr/pay | son t medyan {s.son.median():>5.0f} | n {s.n.median():.0f}")
