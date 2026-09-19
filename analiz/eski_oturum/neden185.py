"""SIFIR olmasi gereken yerde neden -1.85'teyiz?
Kiyas sinifi: yalniz <=0.40 alan cuzdan-pencereler (+0.01 kr/pay).
Bu sinifi ALT KIRILIMLARA ayir, bizim profilimize en yakin hucreyi bul."""
import pandas as pd, json, numpy as np, random
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['gun']=pd.to_datetime(df.start_ts,unit='s').dt.date
df['mal']=df.shares*df.price; df['kazpay']=df.shares*(df.outcome_idx==df.kaz)
df=df.sort_values(['wallet','start_ts','t_rel_s'])
A=df.groupby(['wallet','start_ts'],sort=False).agg(
    gun=('gun','first'), max_px=('price','max'), min_px=('price','min'),
    ort_px=('price','mean'), ilk_t=('t_rel_s','first'), son_t=('t_rel_s','max'),
    pay=('shares','sum'), mal=('mal','sum'), kazpay=('kazpay','sum'),
    fee=('fee','sum'), n=('shares','size'), medboy=('shares','median'))
s0=df[df.outcome_idx==0].groupby(['wallet','start_ts']).shares.sum().rename('q0')
s1=df[df.outcome_idx==1].groupby(['wallet','start_ts']).shares.sum().rename('q1')
A=A.join(s0,how='left').join(s1,how='left').fillna({'q0':0,'q1':0})
A=A[A.n>=1].copy()
A['pnl']=A.kazpay-A.mal-A.fee
A['cift']=(A.q0>0)&(A.q1>0)
A=A.reset_index()
U=A[A.max_px<=0.40].copy()      # BIZIM SINIF
print(f"kiyas sinifi (yalniz <=0.40): {len(U):,} cuzdan-pencere")
print(f"  toplam: {100*U.pnl.sum()/U.pay.sum():+.2f} kr/pay\n")
def ga(d):
    if d.gun.nunique()<5: return None
    gl=[(x.pnl.sum(),x.pay.sum()) for _,x in d.groupby('gun')]
    r=random.Random(3); b=[]
    for _ in range(1500):
        i=[r.randrange(len(gl)) for _ in range(len(gl))]
        n=sum(gl[j][0] for j in i); dd=sum(gl[j][1] for j in i)
        if dd>0: b.append(100*n/dd)
    b.sort(); return b[37],b[1462]
def blok(baslik,kirilim):
    print(f"### {baslik}")
    for ad,d in kirilim:
        if len(d)<300: continue
        g=ga(d)
        print(f"  {ad:>26}: {len(d):>7,} | {d.pay.sum():>9,.0f} pay | {100*d.pnl.sum()/d.pay.sum():>+7.2f} kr/pay "
              f"{('[%+.2f,%+.2f]'%g) if g else '':>16} | cift %{100*d.cift.mean():.0f}")
    print()
blok("PENCERE BASINA DOLUM SAYISI (biz: 5 rung, cogu kez 1-5 dolum)",
     [(f"{a}-{b} dolum",U[(U.n>=a)&(U.n<=b)]) for a,b in ((1,1),(2,3),(4,6),(7,12),(13,999))])
blok("MEDYAN DOLUM BOYU (biz: 5 pay)",
     [("1-4 pay",U[U.medboy<5]),("5-9 pay (BIZ)",U[(U.medboy>=5)&(U.medboy<10)]),
      ("10-24",U[(U.medboy>=10)&(U.medboy<25)]),("25+",U[U.medboy>=25])])
blok("ILK DOLUM ZAMANI (biz: t=5'te koyuyoruz, t=60'ta kesiyoruz)",
     [("t<30",U[U.ilk_t<30]),("t30-60",U[(U.ilk_t>=30)&(U.ilk_t<60)]),
      ("t60-120",U[(U.ilk_t>=60)&(U.ilk_t<120)]),("t120+",U[U.ilk_t>=120])])
blok("SON DOLUM ZAMANI (biz: t=60 sonrasi YOK)",
     [("hepsi t<60 (BIZ)",U[U.son_t<60]),("t60-150",U[(U.son_t>=60)&(U.son_t<150)]),
      ("t150+",U[U.son_t>=150])])
blok("ORTALAMA FIYAT (biz: ~0.26)",
     [("<0.15",U[U.ort_px<0.15]),("0.15-0.25",U[(U.ort_px>=0.15)&(U.ort_px<0.25)]),
      ("0.25-0.33 (BIZ)",U[(U.ort_px>=0.25)&(U.ort_px<0.33)]),("0.33-0.40",U[U.ort_px>=0.33])])
print("### BIZE EN YAKIN HUCRE: 5-9 pay klip + hepsi t<60 + ort 0.25-0.33")
B=U[(U.medboy>=5)&(U.medboy<10)&(U.son_t<60)&(U.ort_px>=0.25)&(U.ort_px<0.33)]
if len(B)>100:
    g=ga(B)
    print(f"  {len(B):,} kayit | {B.pay.sum():,.0f} pay | {100*B.pnl.sum()/B.pay.sum():+.2f} kr/pay "
          f"{('[%+.2f,%+.2f]'%g) if g else ''} | cift %{100*B.cift.mean():.0f}")
else: print(f"  yetersiz ({len(B)} kayit)")
