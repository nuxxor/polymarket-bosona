import json,urllib.request,time,random
UA={'User-Agent':'python-urllib/3'}
def jget(u,t=30):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
tr=[];off=0;gor=set()
while off<=15000:
    try: d=jget(f"https://data-api.polymarket.com/trades?user={BOS}&limit=500&offset={off}")
    except Exception as e: print("dur:",str(e)[:40]); break
    if not d: break
    for x in d:
        kk=(x['timestamp'],x['asset'],x['size'],x['price'],x['side'])
        if kk not in gor: gor.add(kk); tr.append(x)
    if len(d)<500: break
    off+=500; time.sleep(0.35)
btc=[x for x in tr if x.get('slug','').startswith('btc-updown-5m-')]
k=[json.loads(l) for l in open('/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl') if l.strip().startswith('{')]
KAZ={x['S']:x['kazanan'] for x in k if x['k']=='COZULDU'}
def S_(x): return int(x['slug'].rsplit('-',1)[1])
B=[x for x in btc if x['side']=='BUY' and S_(x) in KAZ]
print(f"bosona BTC5m BUY, sonucu bilinen: {len(B)} islem / {len({S_(x) for x in B})} pencere")
def oz(ad,L):
    if not L: print(f"  {ad:22s} yok"); return
    pay=sum(x['size'] for x in L); mal=sum(x['size']*x['price'] for x in L)
    kaz=sum(x['size'] for x in L if x['outcomeIndex']==KAZ[S_(x)])
    pl=[x['size']*((1 if x['outcomeIndex']==KAZ[S_(x)] else 0)-x['price']) for x in L]
    r2=random.Random(9)
    bp=sorted(100*sum(pl[r2.randrange(len(pl))] for _ in pl)/pay for _ in range(3000)) if len(pl)>4 else None
    ga=f"GA95[{bp[75]:+.1f},{bp[2925]:+.1f}]" if bp else ""
    print(f"  {ad:22s} {len(L):>4} islem {pay:>8.0f} pay  fiyat {mal/pay:.3f}  KAZ %{100*kaz/pay:5.1f}  {100*(kaz-mal)/pay:>+7.2f} kr/pay  {ga}")
print("\n### PENCERE ICI ZAMAN KUSAGINA GORE")
for a,b in ((0,60),(60,120),(120,180),(180,240),(240,270),(270,301)):
    oz(f"t {a}-{b}",[x for x in B if a<=x['timestamp']-S_(x)<b])
print("\n### GEC + PAHALI (maker tarafi suphesi)")
oz("t>=240 & px>=0.60",[x for x in B if x['timestamp']-S_(x)>=240 and x['price']>=0.60])
oz("t>=240 & px<0.60", [x for x in B if x['timestamp']-S_(x)>=240 and x['price']<0.60])
oz("t<240  & px>=0.60",[x for x in B if x['timestamp']-S_(x)<240 and x['price']>=0.60])
oz("t<240  & px<0.60", [x for x in B if x['timestamp']-S_(x)<240 and x['price']<0.60])
L=[x for x in B if x['timestamp']-S_(x)>=240 and x['price']>=0.60]
print(f"\n  gec+pahali islemler ({len(L)}):")
for x in sorted(L,key=lambda y:y['timestamp']):
    print(f"     S={S_(x)} t={x['timestamp']-S_(x):>3} px={x['price']:.3f} {x['size']:>7.1f} {x['outcome']:>5} -> {'KAZANDI' if x['outcomeIndex']==KAZ[S_(x)] else 'kaybetti'}")
