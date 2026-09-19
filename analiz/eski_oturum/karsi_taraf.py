#!/usr/bin/env python3
"""SALDIRI 3: KARSI TARAF ve BUILDER — defterde hic bakilmamis iki alan.

Sorular:
 a) bosona kimin karsisina geciyor? Kaybeden akis belirli cuzdanlardan mi?
 b) has_builder ne? bosona'nin dolumlarinda var mi, bizimkilerde yok mu?
 c) Kenari ZAMANA gore nerede? (t_rel_s)
 d) Kenari PENCERE SECIMINDEN mi geliyor? (girdigi pencereler farkli mi)
"""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet')
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['pnl']=df.shares*(df.outcome_idx==df.kaz)-df.shares*df.price-df.fee
print("### b) has_builder")
print("  tum maker:",df.has_builder.value_counts().to_dict())
bo=df[df.wallet.str.lower()==BOS]
print("  bosona   :",bo.has_builder.value_counts().to_dict())
for v,d in df.groupby('has_builder'):
    print(f"    has_builder={v}: {d.shares.sum():>12,.0f} pay  {100*d.pnl.sum()/d.shares.sum():+6.2f} kr/pay")
print("\n### c) bosona kenari ZAMANA gore (pencere ici saniye)")
print(f"  {'t araligi':>12} {'pay':>12} {'kr/pay':>8} {'ort fiyat':>10}")
for a,b in ((0,60),(60,120),(120,180),(180,240),(240,270),(270,301)):
    d=bo[(bo.t_rel_s>=a)&(bo.t_rel_s<b)]
    if len(d)<50: continue
    print(f"  {a:>4}-{b:<7} {d.shares.sum():>12,.0f} {100*d.pnl.sum()/d.shares.sum():>+8.2f} {d.price.mean():>10.3f}")
print("\n### a) KARSI TARAF — bosona'nin doldugu takerlar")
kt=bo.groupby('counterparty').agg(pay=('shares','sum'),pnl=('pnl','sum'),n=('shares','size'))
kt['kr']=100*kt.pnl/kt.pay
kt=kt.sort_values('pay',ascending=False)
print(f"  farkli karsi taraf: {len(kt)} | en buyuk 10'un payi %{100*kt.head(10).pay.sum()/kt.pay.sum():.0f}")
print(f"  {'karsi taraf':>12} {'pay':>11} {'bosona kr/pay':>14} {'islem':>7}")
for w,r in kt.head(10).iterrows():
    print(f"  {str(w)[:12]:>12} {r.pay:>11,.0f} {r.kr:>+14.2f} {r.n:>7.0f}")
print("\n  yogunlasma: en buyuk 1 karsi taraf %{:.1f}".format(100*kt.iloc[0].pay/kt.pay.sum()))
print("\n### d) PENCERE SECIMI — bosona hangi pencerelere giriyor?")
tum=set(df.start_ts.unique()); bos_p=set(bo.start_ts.unique())
print(f"  toplam pencere {len(tum)} | bosona {len(bos_p)} (%{100*len(bos_p)/len(tum):.0f})")
gir=df[df.start_ts.isin(bos_p)]; girme=df[~df.start_ts.isin(bos_p)]
for ad,d in (("bosona'nin GIRDIGI",gir),("GIRMEDIGI",girme)):
    if len(d)<100: continue
    print(f"  {ad:>22}: {d.start_ts.nunique():>5} pencere | TUM maker kenari {100*d.pnl.sum()/d.shares.sum():+6.2f} kr/pay")
