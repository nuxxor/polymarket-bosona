#!/usr/bin/env python3
"""bosona TAKER kenari, 19 gun. (takerOnly=true tek basina yeterli — maker kumesi gerekmez.)"""
import json,os,urllib.request,collections,time,random,math,concurrent.futures as cf
UA={'User-Agent':'Mozilla/5.0'}
tak=json.load(open('bos_tak_derin.json'))
T5=[x for x in tak if '-updown-5m-' in (x.get('slug') or '')]
sl=sorted({x['slug'] for x in T5})
C=json.load(open('taker_kaz.json')) if os.path.exists('taker_kaz.json') else {}
todo=[s for s in sl if C.get(s) is None]
print(f"taker 5m islem {len(T5)}, pencere {len(sl)}, etiket eksik {len(todo)}")
def kaz(s):
    for u in (f"https://gamma-api.polymarket.com/events?slug={s}", f"https://gamma-api.polymarket.com/markets?slug={s}"):
        try:
            d=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read())
            ms=[m for e in d for m in e.get('markets',[])] if 'events?' in u else d
            for m in ms:
                if m.get('slug')!=s: continue
                op=[float(z) for z in json.loads(m.get('outcomePrices') or '[]')]
                if op==[1.0,0.0]: return s,0
                if op==[0.0,1.0]: return s,1
        except Exception: pass
    return s,None
if todo:
    with cf.ThreadPoolExecutor(12) as ex:
        for i,(s,k) in enumerate(ex.map(kaz,todo)):
            C[s]=k
            if i%300==0: print('  ',i,flush=True)
    json.dump(C,open('taker_kaz.json','w'))
ucret=lambda p: 0.07*p*(1-p)
A=[]
for x in T5:
    s=x['slug']
    if C.get(s) is None or x.get('side')!='BUY': continue
    S=int(s.rsplit('-',1)[1])
    A.append({'sym':s.split('-')[0],'S':S,'oi':int(x['outcomeIndex']),'p':float(x['price']),
              'q':float(x['size']),'kz':C[s],'t':int(x.get('timestamp') or 0)-S})
Q=sum(a['q'] for a in A)
net=sum(a['q']*((1.0 if a['oi']==a['kz'] else 0.0)-a['p']-ucret(a['p'])) for a in A)
print(f"\n=== BOSONA TAKER ALIMLARI, 19 GUN ===")
print(f"islem {len(A)} | pay {Q:,.0f} | NET ${net:+,.0f} | {100*net/Q:+.2f} kr/pay")
gun=collections.defaultdict(lambda:[0.0,0.0,0])
for a in A:
    d=time.strftime('%m-%d',time.gmtime(a['S'])); g=gun[d]
    g[0]+=a['q']*((1.0 if a['oi']==a['kz'] else 0.0)-a['p']-ucret(a['p'])); g[1]+=a['q']; g[2]+=1
print(f"\n{'gun':>7} {'islem':>6} {'pay':>8} {'NET $':>9} {'kr/pay':>8}")
art=0
for d in sorted(gun):
    g=gun[d]
    if g[1]<=0: continue
    k=100*g[0]/g[1]; art+= (1 if g[0]>0 else 0)
    print(f"{d:>7} {g[2]:6} {g[1]:8,.0f} {g[0]:+9.1f} {k:+8.2f}")
print(f"\nartida gun: {art}/{len(gun)}")
gb={d:(v[0],v[1]) for d,v in gun.items() if v[1]>0}
rnd=random.Random(3); o=[]
ad=list(gb)
for _ in range(4000):
    s=[gb[rnd.choice(ad)] for _ in ad]
    aa=sum(x[0] for x in s); bb=sum(x[1] for x in s)
    if bb>0: o.append(100*aa/bb)
o.sort()
print(f"gun-kumeli bootstrap %95 GA: [{o[int(.025*len(o))]:+.2f}, {o[int(.975*len(o))]:+.2f}] kr/pay")
# buyuk islem kirilimi
for lo,hi,adet in ((0,50,'<50'),(50,200,'50-200'),(200,1e9,'>=200')):
    g=[a for a in A if lo<=a['q']<hi]
    if not g: continue
    qq=sum(a['q'] for a in g); nn=sum(a['q']*((1.0 if a['oi']==a['kz'] else 0.0)-a['p']-ucret(a['p'])) for a in g)
    w=sum(a['q'] for a in g if a['oi']==a['kz'])
    print(f"  boyut {adet:>7}: {len(g):4} islem {qq:8,.0f} pay {100*nn/qq:+7.2f} kr/pay isabet %{100*w/qq:.1f}")
