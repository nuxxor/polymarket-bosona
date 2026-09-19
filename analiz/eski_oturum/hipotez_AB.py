#!/usr/bin/env python3
"""HIPOTEZ: bosona AYNI PENCEREDE hem A (derin) hem B (mid'e yakin) gibi davraniyor.

Gerekce: tamamlama olcumu, tek tarafli kalindiginda ikinci bacagin 0,85 altinda
HIC bulunamadigini gosterdi (0/32 pencere). Yani 'sonradan ucuza tamamlama' yok.
O halde bosona'nin %65 eslesmesi, pencere ACILIRKEN hem yakin hem derin
seviyelerde durmasindan gelmeli: yakin seviyeler kucuk salinimda esleir (cift ~0,95),
derin seviyeler buyuk savrulmada (cift ~0,60) -> ortalama 0,87.

Bizde: kol A YALNIZ derin (cift 0,5745, eslesme %42)
       kol B YALNIZ yakin (cift 0,9767, eslesme %83)
Test: bosona'nin dolum fiyatlarinin, o andaki mid'e gore dagilimi.
"""
import json,gzip,glob,urllib.request,time,collections,statistics as ist
UA={'User-Agent':'python-urllib/3'}
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def jget(u,t=25):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
tr=[];off=0;gor=set()
while off<=15000:
    try: d=jget(f"https://data-api.polymarket.com/trades?user={BOS}&limit=500&offset={off}&takerOnly=false")
    except Exception: break
    if not d: break
    for x in d:
        kk=(x['timestamp'],x['asset'],x['size'],x['price'],x['side'],x['outcomeIndex'])
        if kk not in gor: gor.add(kk); tr.append(x)
    if len(d)<500: break
    off+=500; time.sleep(0.3)
btc=[x for x in tr if x.get('slug','').startswith('btc-updown-5m-') and x['side']=='BUY']
print(f"bosona BTC5m BUY: {len(btc)}")
bas=min(x['timestamp'] for x in btc)*1000-20000; bit=max(x['timestamp'] for x in btc)*1000+20000
ser=collections.defaultdict(list)
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
                    bb,ba=c.get('best_bid'),c.get('best_ask')
                    if bb and ba:
                        try: ser[c['asset_id']].append((ms,(float(bb)+float(ba))/2))
                        except Exception: pass
    except EOFError: pass
for a in ser: ser[a].sort()
def mid_at(a,ms):
    L=ser.get(a)
    if not L: return None
    lo,hi=0,len(L)-1; en=None
    while lo<=hi:
        o=(lo+hi)//2
        if L[o][0]<=ms: en=L[o]; lo=o+1
        else: hi=o-1
    return en[1] if (en and (ms-en[0])/1000.0<=3.0) else None
D=[]
for x in btc:
    m=mid_at(x['asset'],x['timestamp']*1000)
    if m is None: continue
    D.append((m-x['price'],x['size'],x['price'],m))
print(f"mid eslesen dolum: {len(D)} / {sum(x[1] for x in D):.0f} pay\n")
print("### bosona'nin dolumlari MID'E GORE nerede? (+ = mid'in ALTINDA aldi)")
kut=[(-1,0.0,'MID USTU (pahali/taker)'),(0.0,0.03,'mid civari 0-3 kr'),
     (0.03,0.08,'yakin 3-8 kr'),(0.08,0.15,'orta 8-15 kr'),
     (0.15,0.30,'derin 15-30 kr'),(0.30,9,'cok derin >30 kr')]
tp=sum(x[1] for x in D)
for a,b,ad in kut:
    L=[x for x in D if a<=x[0]<b]
    if not L: continue
    pay=sum(x[1] for x in L)
    print(f"  {ad:24s} {len(L):5d} islem {pay:8.0f} pay  %{100*pay/tp:5.1f}  ort fiyat {sum(x[2]*x[1] for x in L)/pay:.3f}")
print()
print("### BIZ — ayni olcu (kol bazinda)")
k=[json.loads(l) for l in open('/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl') if l.strip().startswith('{')]
HAR={int(a):b for a,b in json.load(open('/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad/asset_harita.json')).items()}
KOL={x['S']:x['kol'] for x in k if x['k']=='COZULDU' and x.get('kol')}
for kol in ('A','B'):
    E=[]
    for x in k:
        if x['k']!='dolum' or KOL.get(x.get('S'))!=kol or x['S'] not in HAR: continue
        m=mid_at(HAR[x['S']][x['oi']],x['utc_ms'])
        if m is None: continue
        E.append((m-x['p'],x.get('yeni',0.0),x['p']))
    if not E: continue
    tp2=sum(x[1] for x in E)
    print(f"  kol {kol} ({len(E)} dolum / {tp2:.0f} pay):")
    for a,b,ad in kut:
        L=[x for x in E if a<=x[0]<b]
        if not L: continue
        pay=sum(x[1] for x in L)
        print(f"     {ad:24s} {len(L):4d} islem {pay:7.0f} pay  %{100*pay/tp2:5.1f}")
