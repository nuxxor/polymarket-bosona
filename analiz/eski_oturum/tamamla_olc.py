#!/usr/bin/env python3
"""CIFT TAMAMLAMA karsi-olgusal olcumu — GERCEK defter ask'lariyla.

Soru: TAMAMLA_ACIK=False dogru mu? Kol A'nin 32 tek-tarafli penceresi
-23.07 kr/pay veriyor. Tamamlasaydik ne olurdu?

MODEL (sinirlari acikca):
 - Ilk dolumdan T_TAMAMLA sn sonra denge >=5 pay ise tamamlama denenir.
 - O andaki EKSIK tarafin ASK'i tape'ten okunur (derinlik dahil).
 - Tamamlama yapilirsa: o andan SONRAKI dolumlar DUSULUR (gercek kod da tum
   acik emirleri iptal ediyor). Bu, yaklasimin en zayif yeri: sonraki
   kotasyon davranisini modellemiyor.
 - Tavan taranir; her tavan icin AYRI sonuc.
"""
import json,gzip,glob,sys,collections,statistics as ist,random
sys.path.insert(0,'/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad')
LOG='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
HAR=json.load(open('/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad/asset_harita.json'))
HAR={int(a):b for a,b in HAR.items()}
T_TAMAMLA=15.0; FEE=0.07; MIN_EMIR=5.0

k=[json.loads(l) for l in open(LOG) if l.strip().startswith('{')]
KAZ={x['S']:x['kazanan'] for x in k if x['k']=='COZULDU'}
KOL={x['S']:x['kol'] for x in k if x['k']=='COZULDU' and x.get('kol')}
D=collections.defaultdict(list)
for x in k:
    if x['k']=='dolum' and x.get('S') in KAZ:
        D[x['S']].append((x['utc_ms'],x['oi'],x['p'],x.get('yeni',0.0)))
for S in D: D[S].sort()

# ASK serisi: tape'ten, asset basina (ms, best_ask, derinlik yok -> en iyi ask)
bas=min(v[0][0] for v in D.values())-20000; bit=max(v[-1][0] for v in D.values())+320000
ask=collections.defaultdict(list)
for f in sorted(glob.glob('/home/taygun/Masaüstü/polymarket/data/tape/tape_20260918_*.jsonl.gz')):
    try:
        with gzip.open(f,'rt') as fh:
            for ln in fh:
                if '"price_change"' not in ln: continue
                try: d=json.loads(ln)
                except Exception: continue
                ms=d.get('src')
                if ms is None or ms<bas or ms>bit: continue
                for c in (d.get('p') or {}).get('price_changes') or []:
                    ba=c.get('best_ask')
                    if ba:
                        try: ask[c['asset_id']].append((ms,float(ba)))
                        except Exception: pass
    except EOFError: pass
for a in ask: ask[a].sort()
print(f"ask serisi olan asset: {len(ask)}",flush=True)

def ask_at(a,ms):
    L=ask.get(a)
    if not L: return None
    lo,hi=0,len(L)-1; en=None
    while lo<=hi:
        o=(lo+hi)//2
        if L[o][0]<=ms: en=L[o]; lo=o+1
        else: hi=o-1
    if en is None or (ms-en[0])/1000.0>5.0: return None
    return en[1]

def pnl_of(fl,kaz):
    q={0:0.0,1:0.0}; c=0.0
    for _,oi,p,n in fl: q[oi]+=n; c+=n*p
    return q[kaz]-c, q[0]+q[1]

def senaryo(tavan):
    ger=[];yen=[];uyg=0
    for S,fl in D.items():
        if S not in KOL or S not in HAR: continue
        kz=KAZ[S]; tok=HAR[S]
        a,pa=pnl_of(fl,kz)
        ilk=fl[0][0]; tms=ilk+int(T_TAMAMLA*1000)
        q={0:0.0,1:0.0}
        for ms,oi,p,n in fl:
            if ms>tms: break
            q[oi]+=n
        eksik=abs(q[0]-q[1]); eks=0 if q[1]>q[0] else 1
        yeni=fl
        if eksik>=MIN_EMIR and tavan is not None:
            co={0:0.0,1:0.0}; qq={0:0.0,1:0.0}
            for ms,oi,p,n in fl:
                if ms>tms: break
                qq[oi]+=n; co[oi]+=n*p
            fz=1-eks
            ort=co[fz]/qq[fz] if qq[fz]>0 else None
            axx=ask_at(tok[eks],tms)
            if ort is not None and axx is not None:
                mal=ort+axx+FEE*axx*(1-axx)
                if mal<=tavan:
                    uyg+=1
                    yeni=[x for x in fl if x[0]<=tms]+[(tms,eks,axx+FEE*axx*(1-axx),eksik)]
        b,pb=pnl_of(yeni,kz)
        ger.append((a,pa)); yen.append((b,pb))
    ga=sum(x[0] for x in ger); gp=sum(x[1] for x in ger)
    ya=sum(x[0] for x in yen); yp=sum(x[1] for x in yen)
    f=[y[0]-g[0] for g,y in zip(ger,yen)]
    r2=random.Random(3); bp=sorted(sum(f[r2.randrange(len(f))] for _ in f) for _ in range(5000))
    iy=sum(1 for x in f if x>1e-9); kt=sum(1 for x in f if x<-1e-9)
    sf=sorted(f)
    print(f"  tavan {str(tavan):>5} | uygulanan {uyg:3d} pen | GERCEK {ga:+7.2f}$ -> YENI {ya:+7.2f}$ "
          f"({100*ya/yp:+5.2f} kr/pay) | FARK {ya-ga:+7.2f}$")
    print(f"              iyilesen {iy} / kotulesen {kt} | MEDYAN {ist.median(f):+.2f}$ | "
          f"GA95[{bp[125]:+.1f},{bp[4875]:+.1f}] | en iyi 3 pencere toplamin %{100*sum(sf[-3:])/ (ya-ga) if abs(ya-ga)>1e-9 else 0:.0f}'i")

print("\n### CIFT TAMAMLAMA — tavan taramasi (tum kollar)")
senaryo(None)
for t in (0.85,0.90,0.95,1.00,1.02,1.05):
    senaryo(t)
