#!/usr/bin/env python3
"""KOL C 1 SAATLIK RAPOR: C vs A+B (ayni donem), C mekanizma gostergeleri.
Kullanim: c_rapor.py [utc_ms_baslangic]"""
import json,sys,time,subprocess,collections,statistics as st
LOG='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
BASLA=int(sys.argv[1]) if len(sys.argv)>1 else 1789851600000   # 21:00Z
ev=[json.loads(l) for l in open(LOG) if l.strip()]
ev=[d for d in ev if d['utc_ms']>=BASLA]
kol={d['S']:d['kol'] for d in ev if d['k']=='pencere'}
taze={d['S']:d for d in ev if d['k']=='taze_bitti'}
coz={d['S']:d for d in ev if d['k']=='COZULDU'}
dol=collections.defaultdict(list)
for d in ev:
    if d['k']=='dolum': dol[d['S']].append(d)
print(f"### KOL C RAPORU  {time.strftime('%H:%MZ',time.gmtime(BASLA/1000))} -> {time.strftime('%H:%MZ',time.gmtime())}")
print(f"acilan pencere: {dict(collections.Counter(kol.values()))}")
for K in ('C','A','B'):
    Ss=[S for S,k in kol.items() if k==K]
    cz=[coz[S] for S in Ss if S in coz and coz[S].get('geri_cekildi') is None]
    pay=sum(c['pay'] for c in cz); pnl=sum(c['pnl'] for c in cz)
    print(f"  kol {K}: {len(Ss)} acildi | {len(cz)} cozuldu | pay {pay:.0f} | PnL ${pnl:+.2f} | {100*pnl/pay if pay else 0:+.2f} kr/pay | artida {sum(1 for c in cz if c['pnl']>0)}/{len(cz)} | dolumlu {sum(1 for c in cz if c['pay']>0)}")
print("\n### C pencereleri tek tek")
for S in sorted(S for S,k in kol.items() if k=='C'):
    t=taze.get(S,{}); c=coz.get(S); ds=dol.get(S,[])
    print(f"  {time.strftime('%H:%M',time.gmtime(S))}Z post {t.get('koy','-'):>3} iptal {t.get('iptal','-'):>3} ws_hata {t.get('ws_hata','-')} | dolum {len(ds)} pay {sum(d['yeni'] for d in ds):.1f} "
          f"| fiyatlar {sorted({round(d['p'],2) for d in ds})} | t {sorted(round(d['gecen_sn']) for d in ds)[:6]} | "
          + (f"PnL ${c['pnl']:+.2f} kazanan {'Up' if c['kazanan']==0 else 'Down'}" if c else "cozulmedi"))
Cs=[S for S,k in kol.items() if k=='C']
if Cs:
    print("\n### C dolumlari defterde (kismi mi / seviye yasi) — bacak_anatomisi --S")
    biz=open('/home/taygun/Masaüstü/polymarket/scripts/izleme/.biz_adres').read().strip()
    out=subprocess.run(['python3','/home/taygun/Masaüstü/polymarket/scripts/izleme/bacak_anatomisi.py',str(BASLA),'--biz',biz,'--S',','.join(map(str,Cs))],capture_output=True,text=True,timeout=280).stdout
    for l in out.split('\n'):
        if l.startswith('  HERKES') or l.startswith('  bosona') or l.startswith('  BIZ') or l.startswith('tx ') or l.startswith('defterle'): print(l)
    print("(kaset ~5 dk gecikmeli; son pencere eksik olabilir)")
