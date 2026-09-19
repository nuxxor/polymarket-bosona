#!/usr/bin/env python3
"""HAKEM TESTI: iki tahminciden hangisi BIZIM gerceklesenimizi ongoruyor?

A) HAVUZLANMIS (pay-agirlikli, hucre ici): E[sonuc|doldu] - fiyat
   -> emir birakip bekleyen birinin yasadigi sey BU olmali
B) PENCERE-ESIT: her pencerenin kr/pay'ini esit agirlikla ortala

Kendi 529 dolumumuz hakem. Onlari fiyat bandina gore havuzlayip
iki tahminciyle karsilastiriyoruz.
"""
import pandas as pd, json, numpy as np
D='data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER'
kz={int(k):v for k,v in json.load(open('data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json')).items()}
df=pd.read_parquet(f'{D}/maker.parquet',columns=['start_ts','shares','role','outcome_idx','side','price','fee','t_rel_s'])
df=df[(df.role.str.lower()=='maker')&(df.side.str.upper()=='BUY')]
df['kaz']=df.start_ts.map(kz); df=df[df.kaz.notna()]
df['w']=(df.outcome_idx==df.kaz).astype(float)
df['pnl']=df.shares*df.w-df.shares*df.price-df.fee
kk=df[df.shares<10]      # bizim klip sinifi
# bizim gercek dolumlar
k=[json.loads(l) for l in open('data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl') if l.strip().startswith('{')]
B=[]
for r in [x for x in k if x['k']=='COZULDU']:
    for e in r['emirler']:
        if e['pay']>0: B.append((e['p'],e['pay'],1.0 if e['oi']==r['kazanan'] else 0.0))
bz=pd.DataFrame(B,columns=['price','shares','w'])
print(f"bizim dolum: {len(bz)} / {bz.shares.sum():.0f} pay\n")
print("### HAKEM: bizim gerceklesenimiz hangisine yakin?")
print(f"  {'bant':>11} {'BIZ pay':>8} {'BIZ kenar':>10} | {'A) HAVUZ':>9} {'B) PENCERE-ESIT':>16}")
for a,b in ((0.10,0.20),(0.20,0.30),(0.30,0.40),(0.40,0.50),(0.50,0.60),(0.60,0.80)):
    m=bz[(bz.price>=a)&(bz.price<b)]
    if m.shares.sum()<50: continue
    biz=100*((m.w*m.shares).sum()/m.shares.sum()-(m.price*m.shares).sum()/m.shares.sum())
    d=kk[(kk.price>=a)&(kk.price<b)]
    havuz=100*((d.w*d.shares).sum()-(d.price*d.shares).sum()-d.fee.sum())/d.shares.sum()
    pz=d.groupby('start_ts').agg(p=('pnl','sum'),s=('shares','sum'))
    pe=(100*pz.p/pz.s).mean()
    print(f"  {a:.2f}-{b:.2f} {m.shares.sum():>8.0f} {biz:>+10.2f} | {havuz:>+9.2f} {pe:>+16.2f}")
ha=[];pe_=[];bi=[]
for a,b in ((0.10,0.20),(0.20,0.30),(0.30,0.40),(0.40,0.50),(0.50,0.60),(0.60,0.80)):
    m=bz[(bz.price>=a)&(bz.price<b)]
    if m.shares.sum()<50: continue
    d=kk[(kk.price>=a)&(kk.price<b)]
    pz=d.groupby('start_ts').agg(p=('pnl','sum'),s=('shares','sum'))
    bi.append(100*((m.w*m.shares).sum()/m.shares.sum()-(m.price*m.shares).sum()/m.shares.sum()))
    ha.append(100*((d.w*d.shares).sum()-(d.price*d.shares).sum()-d.fee.sum())/d.shares.sum())
    pe_.append((100*pz.p/pz.s).mean())
bi=np.array(bi);ha=np.array(ha);pe_=np.array(pe_)
print(f"\n  ortalama MUTLAK hata:  A) HAVUZ {np.abs(bi-ha).mean():.2f}   B) PENCERE-ESIT {np.abs(bi-pe_).mean():.2f}")
print(f"  korelasyon:            A) {np.corrcoef(bi,ha)[0,1]:+.3f}        B) {np.corrcoef(bi,pe_)[0,1]:+.3f}")
