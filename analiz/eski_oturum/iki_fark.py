#!/usr/bin/env python3
"""IKI KALAN FARK: eslesme orani ve hacim. Nedensel mi, yan urun mu?

takerOnly=false ZORUNLU (09-18 bulgusu). Pencere duzeyinde bagimlilik korunur.
"""
import json,urllib.request,time,random,statistics as ist
UA={'User-Agent':'python-urllib/3'}
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def jget(u,t=25):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
k=[json.loads(l) for l in open('/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl') if l.strip().startswith('{')]
KAZ={x['S']:x['kazanan'] for x in k if x['k']=='COZULDU'}
tr=[];off=0;gor=set()
while off<=15000:
    try: d=jget(f"https://data-api.polymarket.com/trades?user={BOS}&limit=500&offset={off}&takerOnly=false")
    except Exception as e: print("akis dur:",str(e)[:40]); break
    if not d: break
    for x in d:
        kk=(x['timestamp'],x['asset'],x['size'],x['price'],x['side'],x['outcomeIndex'])
        if kk not in gor: gor.add(kk); tr.append(x)
    if len(d)<500: break
    off+=500; time.sleep(0.3)
btc=[x for x in tr if x.get('slug','').startswith('btc-updown-5m-')]
print(f"bosona TAM akis: {len(tr)} islem, BTC5m {len(btc)}")

P={}
for x in btc:
    S=int(x['slug'].rsplit('-',1)[1])
    if S not in KAZ: continue
    w=P.setdefault(S,{0:[0.0,0.0],1:[0.0,0.0],'n':0,'sv':set(),'t':[],'sat':0})
    oi=x['outcomeIndex']; sz=x['size']*(1 if x['side']=='BUY' else -1)
    w[oi][0]+=sz; w[oi][1]+=sz*x['price']; w['n']+=1
    w['sv'].add((oi,round(x['price'],2))); w['t'].append(x['timestamp']-S)
    if x['side']=='SELL': w['sat']+=1
R=[]
for S,w in P.items():
    pay=w[0][0]+w[1][0]
    if pay<=0: continue
    m=min(w[0][0],w[1][0])
    R.append(dict(S=S,pay=pay,esl=2*m/pay,n=w['n'],sv=len(w['sv']),sat=w['sat'],
                  pnl=w[KAZ[S]][0]-(w[0][1]+w[1][1]),
                  iki_taraf=(w[0][0]>0 and w[1][0]>0),
                  t_med=(ist.median(w['t']) if w['t'] else None)))
print(f"olculebilir pencere: {len(R)}\n")

def grup(ad,L):
    if not L: print(f"  {ad:30s} bos"); return
    pay=sum(x['pay'] for x in L); pnl=sum(x['pnl'] for x in L)
    p=[x['pnl'] for x in L]; r2=random.Random(7)
    bp=sorted(100*sum(p[r2.randrange(len(p))] for _ in p)/pay for _ in range(4000)) if len(p)>3 else None
    ga=f"GA95[{bp[100]:+.1f},{bp[3900]:+.1f}]" if bp else ""
    print(f"  {ad:30s} {len(L):3d} pen {pay:8.0f} pay {100*pnl/pay:+7.2f} kr/pay  esl%{100*sum(x['esl']*x['pay'] for x in L)/pay:4.1f}  {ga}")

print("### SORU 1 — HACIM kenar YARATIYOR mu, yoksa sadece OLCEKLIYOR mu?")
q=sorted(x['pay'] for x in R); c1,c2,c3=q[len(q)//4],q[len(q)//2],q[3*len(q)//4]
print(f"  pencere basina pay ceyrekleri: %25={c1:.0f}  medyan={c2:.0f}  %75={c3:.0f}  max={max(q):.0f}")
grup(f"en KUCUK ceyrek (<{c1:.0f})",[x for x in R if x['pay']<c1])
grup(f"2. ceyrek",[x for x in R if c1<=x['pay']<c2])
grup(f"3. ceyrek",[x for x in R if c2<=x['pay']<c3])
grup(f"en BUYUK ceyrek (>={c3:.0f})",[x for x in R if x['pay']>=c3])
print("  -> kr/pay ceyrekler arasi ARTIYORSA hacim kenar yaratir; DUZSE sadece olcekler\n")

print("### SORU 2 — ESLESME kenar YARATIYOR mu?")
e=sorted(x['esl'] for x in R); e1,e2=e[len(e)//3],e[2*len(e)//3]
grup(f"dusuk eslesme (<{e1:.2f})",[x for x in R if x['esl']<e1])
grup(f"orta eslesme",[x for x in R if e1<=x['esl']<e2])
grup(f"yuksek eslesme (>={e2:.2f})",[x for x in R if x['esl']>=e2])
grup("TEK TARAFLI pencereler",[x for x in R if not x['iki_taraf']])
grup("IKI TARAFLI pencereler",[x for x in R if x['iki_taraf']])
print()
print("### YAPISI — biz neyi farkli yapiyoruz")
print(f"  pencere basina ISLEM sayisi: medyan {ist.median([x['n'] for x in R]):.0f}  (biz ~5)")
print(f"  pencere basina FARKLI (taraf,fiyat) hucresi: medyan {ist.median([x['sv'] for x in R]):.0f}  (biz A'da 7+7=14 konur, ~3 dolar)")
print(f"  SATIS iceren pencere: {sum(1 for x in R if x['sat']>0)}/{len(R)}  (biz HIC satmiyoruz)")
tt=[x['t_med'] for x in R if x['t_med'] is not None]
print(f"  islem zamani (pencere ici sn) medyani: {ist.median(tt):.0f}")
print(f"  iki tarafi da alan pencere: {sum(1 for x in R if x['iki_taraf'])}/{len(R)} = %{100*sum(1 for x in R if x['iki_taraf'])/len(R):.0f}")
