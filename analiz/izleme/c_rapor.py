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
# --- KAMU KASETIYLE DOGRULANMIS dolumlar (bot defteri eksik olabilir: dis denetim 09-19) ---
import glob
BIZ=open('/home/taygun/Masaüstü/polymarket/scripts/izleme/.biz_adres').read().strip()
_key=lambda a:f"{a.get('transactionHash')}|{a.get('proxyWallet')}|{a.get('asset')}|{a.get('side')}|{a.get('size')}|{a.get('price')}"
_seen=set(); KAS=collections.defaultdict(lambda:{0:[0.0,0.0],1:[0.0,0.0]})   # S -> oi -> [pay, maliyet]
for f in glob.glob('/home/taygun/Masaüstü/polymarket/data/tape_fills/fills_*.jsonl'):
    for l in open(f):
        try: a=json.loads(l)
        except: continue
        if a.get('proxyWallet','').lower()!=BIZ or not a.get('slug','').startswith('btc-updown-5m-') or a.get('side')!='BUY': continue
        k=_key(a)
        if k in _seen: continue
        _seen.add(k); S=int(a['slug'].split('-')[-1]); oi=0 if a['outcome']=='Up' else 1
        KAS[S][oi][0]+=float(a['size']); KAS[S][oi][1]+=float(a['size'])*float(a['price'])
def kaset_pnl(S):
    c=coz.get(S)
    if not c or S not in KAS: return None
    kz=c['kazanan']; d=KAS[S]; return d[kz][0]-d[0][1]-d[1][1], d[0][0]+d[1][0]
print("\n### KASETLE DOGRULANMIS (kamu dolumlar) — kol bazinda")
for K in ('C','A','B'):
    Ss=[S for S,k in kol.items() if k==K and S in coz and coz[S].get('geri_cekildi') is None]
    v=[kaset_pnl(S) for S in Ss]; v=[x for x in v if x]
    pnl=sum(x[0] for x in v); pay=sum(x[1] for x in v)
    print(f"  kol {K}: {len(Ss)} atanan | kaset PnL ${pnl:+.2f} | pay {pay:.0f} | NET $/ATANAN PENCERE {pnl/len(Ss) if Ss else 0:+.3f} | kr/pay {100*pnl/pay if pay else 0:+.2f}")
print("\n### C pencereleri tek tek")
for S in sorted(S for S,k in kol.items() if k=='C'):
    t=taze.get(S,{}); c=coz.get(S); ds=dol.get(S,[])
    print(f"  {time.strftime('%H:%M',time.gmtime(S))}Z post {t.get('koy','-'):>3} iptal {t.get('iptal','-'):>3} ws_hata {t.get('ws_hata','-')} | dolum {len(ds)} pay {sum(d['yeni'] for d in ds):.1f} "
          f"| fiyatlar {sorted({round(d['p'],2) for d in ds})} | t {sorted(round(d['gecen_sn']) for d in ds)[:6]} | "
          + (f"bot PnL ${c['pnl']:+.2f} | kaset PnL " + (f"${kaset_pnl(S)[0]:+.2f}" if kaset_pnl(S) else "-") + f" | kazanan {'Up' if c['kazanan']==0 else 'Down'}" if c else "cozulmedi"))
Cs=[S for S,k in kol.items() if k=='C']
if Cs:
    print("\n### C dolumlari defterde (kismi mi / seviye yasi) — bacak_anatomisi --S")
    biz=open('/home/taygun/Masaüstü/polymarket/scripts/izleme/.biz_adres').read().strip()
    out=subprocess.run(['python3','/home/taygun/Masaüstü/polymarket/scripts/izleme/bacak_anatomisi.py',str(BASLA),'--biz',biz,'--S',','.join(map(str,Cs))],capture_output=True,text=True,timeout=280).stdout
    for l in out.split('\n'):
        if l.startswith('  HERKES') or l.startswith('  bosona') or l.startswith('  BIZ') or l.startswith('tx ') or l.startswith('defterle'): print(l)
    print("(kaset ~5 dk gecikmeli; son pencere eksik olabilir)")
