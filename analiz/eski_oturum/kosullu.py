#!/usr/bin/env python3
"""HIPOTEZ (operator): bosona NET YON varsa tek taraf, yoksa CIFT taraf aliyor.

Test: 19 gunluk zincir defterindeki pencere pozisyonlari x o pencerenin
BTC marji (Binance 1dk, S'ten itibaren hareket).
  - marj buyukse -> dengesizlik buyuk VE marj yonunde mi?
  - marj kucukse -> dengeli mi?
"""
import pandas as pd, json, urllib.request, time, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','wallet','role','outcome_idx','side','price','t_rel_s','fee'])
df=df[(df.side.str.upper()=='BUY')&(df.wallet.str.lower()==BOS)]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
lo,hi=int(df.start_ts.min()),int(df.start_ts.max())
print(f"bosona pencereleri: {df.start_ts.nunique()} | {time.strftime('%m-%d',time.gmtime(lo))} .. {time.strftime('%m-%d',time.gmtime(hi))}",flush=True)
# Binance 1dk klines
K={}
t=lo-600
while t<hi+600:
    u=f"https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&startTime={t*1000}&limit=1500"
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'python-urllib/3'}),timeout=25) as r:
            d=json.loads(r.read())
    except Exception as e:
        print("kline hata",str(e)[:50]); break
    if not d: break
    for c in d: K[int(c[0]//1000)]=(float(c[1]),float(c[2]),float(c[3]),float(c[4]))
    t=int(d[-1][0]//1000)+60
    time.sleep(0.15)
print(f"kline dakika: {len(K)}",flush=True)
def px(ts):
    m=ts//60*60
    for d in range(0,4):
        if m-d*60 in K: return K[m-d*60][3]   # close
    return None
# pencere bazinda bosona pozisyonu + marj
g=df.groupby(['start_ts','outcome_idx']).agg(pay=('shares','sum')).reset_index()
p=g.pivot_table(index='start_ts',columns='outcome_idx',values='pay',fill_value=0.0)
R=[]
for S,r in p.iterrows():
    q0=float(r.get(0,0.0)); q1=float(r.get(1,0.0))
    if q0+q1<=0: continue
    b=px(S)
    if b is None: continue
    sat={'S':S,'q0':q0,'q1':q1,'dg':abs(q0-q1)/(q0+q1),
         'agir':0 if q0>q1 else 1,'kaz':kz[S],'pay':q0+q1}
    ok=True
    for t in (60,120,180,240):
        v=px(S+t)
        if v is None: ok=False; break
        sat[f'marj{t}']=(v-b)/b*1e4
    if ok: R.append(sat)
R=pd.DataFrame(R)
print(f"eslesen pencere: {len(R)}\n")
print("### HIPOTEZ 1 — marj BUYUKKEN dengesizlik buyuyor mu?")
R['am180']=R.marj180.abs()
q=R.am180.quantile([.25,.5,.75]).values
print(f"  {'|marj180| ceyregi':>22} {'pencere':>8} {'ort dengesizlik':>16} {'tam tek tarafli %':>18}")
for ad,f in (("en dusuk",R.am180<q[0]),("2.",(R.am180>=q[0])&(R.am180<q[1])),
             ("3.",(R.am180>=q[1])&(R.am180<q[2])),("en yuksek",R.am180>=q[2])):
    d=R[f]
    print(f"  {ad:>22} {len(d):>8} {d.dg.mean():>16.3f} {100*(d.dg>0.9).mean():>17.1f}%")
print("\n### HIPOTEZ 2 — tek tarafa girdiginde MARJ YONUNDE mi?")
tek=R[R.dg>0.9].copy()
tek['marj_yon']=(tek.marj180>=0).astype(int)   # 1=Up
tek['uyum']=(tek.agir==0)==(tek.marj_yon==1)
print(f"  tam tek tarafli {len(tek)} pencere | agir taraf marj yonuyle UYUMLU: %{100*tek.uyum.mean():.1f}  (sans %50)")
for t in (60,120,180,240):
    tek[f'y{t}']=((tek[f'marj{t}']>=0).astype(int)==(1-tek.agir)).astype(int)
    print(f"    t={t}: uyum %{100*tek[f'y{t}'].mean():.1f}")
print("\n### HIPOTEZ 3 — uyumlu girdiginde KAZANIYOR mu?")
for ad,d in (("marj yonunde (uyumlu)",tek[tek.uyum]),("marj TERSINE",tek[~tek.uyum])):
    if len(d)<30: continue
    print(f"  {ad:>24}: {len(d):>4} pen | agir taraf kazanma %{100*(d.agir==d.kaz).mean():.1f}")
