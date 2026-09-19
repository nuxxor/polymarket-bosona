#!/usr/bin/env python3
"""KANONIK MUHASEBE — tek kesim, tek tanim, tek defter.

PRO denetiminin #1 bulgusu: gun boyunca dort farkli "gun geneli" sayisi dolasti
(-8.65 / -5.15 / +0.45 / -25.38) ve bunlar AYNI DEFTER DEGIL. Bu betik tek
kaynak olur; her rapor buradan uretilir.

TANIMLAR (bir daha degistirilmeyecek):
  pencere PnL  = SUM(kazanan taraf payi) - SUM(pay * fiyat)     [alis-odeme]
  pay          = COZULDU.emirler icindeki pay>0 olanlarin toplami
  kesim        = acikca yazilir; "gun geneli" tek basina kullanilmaz
  cift maliyeti= SUM_oi(ortalama_fiyat_oi) ; yalniz iki taraf da doluysa
  eslesen pay  = 2*min(q0,q1)
"""
import json,sys,time,random,statistics as ist

LOG=sys.argv[1] if len(sys.argv)>1 else '/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
k=[json.loads(l) for l in open(LOG) if l.strip().startswith('{')]
C=[x for x in k if x['k']=='COZULDU']
print(f"LOG olayi: {len(k)}  |  COZULDU: {len(C)}  |  etiketli: {sum(1 for x in C if x.get('kol'))}")
print(f"zaman araligi: {time.strftime('%H:%M',time.gmtime(k[0]['utc_ms']/1000))}Z - {time.strftime('%H:%M',time.gmtime(k[-1]['utc_ms']/1000))}Z\n")

def pencere(r):
    q={0:0.0,1:0.0}; co={0:0.0,1:0.0}
    for e in r['emirler']:
        if e['pay']>0: q[e['oi']]+=e['pay']; co[e['oi']]+=e['pay']*e['p']
    pay=q[0]+q[1]
    if pay<=0: return None
    m=min(q[0],q[1])
    return dict(S=r['S'],kol=r.get('kol'),pay=pay,esl=2*m,
                cift_mal=(sum(co[oi]/q[oi] for oi in (0,1) if q[oi]>0) if m>0 else None),
                pnl=q[r['kazanan']]-(co[0]+co[1]),
                essiz=abs(q[0]-q[1]),
                essiz_kaz=(abs(q[0]-q[1]) if (0 if q[0]>q[1] else 1)==r['kazanan'] else 0.0))
W=[x for x in (pencere(r) for r in C) if x]
sifir=len(C)-len(W)

def blok(ad,L):
    if not L: print(f"  {ad:32s} bos"); return
    pay=sum(x['pay'] for x in L); pnl=sum(x['pnl'] for x in L)
    esl=sum(x['esl'] for x in L); uq=sum(x['essiz'] for x in L); uk=sum(x['essiz_kaz'] for x in L)
    cm=[x['cift_mal'] for x in L if x['cift_mal'] is not None]
    cmw=sum(x['cift_mal']*x['esl'] for x in L if x['cift_mal'] is not None)/max(1e-9,sum(x['esl'] for x in L if x['cift_mal'] is not None))
    p=[x['pnl'] for x in L]; r2=random.Random(11)
    bp=sorted(sum(p[r2.randrange(len(p))] for _ in p) for _ in range(5000)) if len(p)>3 else None
    print(f"  {ad:32s} {len(L):3d} pen {pay:7.1f} pay  PnL {pnl:+8.2f}$  {100*pnl/pay:+6.2f} kr/pay"
          f"{('  GA95[%+.0f,%+.0f]'%(bp[125],bp[4875])) if bp else ''}")
    print(f"  {'':32s}     eslesme %{100*esl/pay:4.1f} | cift mal {cmw:.4f} ({len(cm)} pen)"
          f" | essiz KAZ %{100*uk/max(1e-9,uq):4.1f} ({uq:.0f} pay)")

print("### KESIM 1 — TUM ETIKETLI PENCERELER (dosyanin tamami)")
blok("TUMU",[x for x in W if x['kol']])
for kol in ('A','B'): blok(f"kol {kol}",[x for x in W if x['kol']==kol])
print(f"  (sifir dolumlu/olculemeyen pencere: {sifir})\n")

SIFIR=1789742700   # sayac sifirlanmasi
print(f"### KESIM 2 — SAYAC SIFIRLANMASINDAN SONRA (S>={SIFIR})")
blok("TUMU",[x for x in W if x['kol'] and x['S']>=SIFIR])
for kol in ('A','B'): blok(f"kol {kol}",[x for x in W if x['kol']==kol and x['S']>=SIFIR])
KAPI=1789755300
print(f"\n### KESIM 3 — REJIM KAPISI PILOTU (S>={KAPI}, atanma anina gore)")
blok("TUMU",[x for x in W if x['kol'] and x['S']>=KAPI])
for kol in ('A','B'): blok(f"kol {kol}",[x for x in W if x['kol']==kol and x['S']>=KAPI])

print("\n### BORSA MUTABAKATI (ayri defter — yerelle KARISTIRMA)")
M=[x for x in k if x['k']=='mutabakat']
if M:
    m=M[-1]
    print(f"  son mutabakat {m['t']}Z: borsa PnL {m['pnl']:+.2f}$  yerel {m['yerel']:+.2f}$  pencere {m['pencere']}")
    print(f"  NOT: borsa defteri sayac sifirlanmasindan sonrasini kapsar ve")
    print(f"       mutabakat aninda COZULMEMIS pencereleri icermez.")
print("\n### UYARI")
print("  Yukaridaki uc kesim AYNI SEY DEGIL. Rapor yazarken hangisi kullanildigi")
print("  ACIKCA yazilmali; 'gun geneli' tek basina anlamsizdir.")
