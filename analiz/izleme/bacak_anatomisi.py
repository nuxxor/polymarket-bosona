#!/usr/bin/env python3
"""BACAK ANATOMISI — maker dolumlari kuyruk/seviye baglaminda (A1 olcumu, 09-19).

Her tx = 1 taker satiri (boyu digerlerinin toplami) + N maker satiri (kaset: data/tape_fills, tekillestirilmis).
Her MAKER dolumu icin canli defterden (data/db/polymarket_orderbook.db):
  onde      : dolumdan hemen once o (token, fiyat) seviyesindeki BID payi (kuyruk)
  dolan     : ayni tx'te o seviyede dolan toplam maker payi
  kismi     : dolan < onde*0.9  -> seviye SUPURULMEDI, dolanlar kuyrugun ONUNDEYDI (sira onemli)
  yas_sn    : seviyenin dolumdan once kesintisiz kac saniyedir >0 oldugu (ms ise HIZ, dk ise ERKEN YERLESIM)
Cuzdan bazinda ozet: bosona, biz, en buyuk 8 maker.
Kullanim: bacak_anatomisi.py [utc_ms_baslangic] [--biz 0x...]
"""
import sqlite3, json, sys, glob, bisect, collections, time, statistics as st
DB='/home/taygun/Masaüstü/polymarket/data/db/polymarket_orderbook.db'
TAPE='/home/taygun/Masaüstü/polymarket/data/tape_fills/fills_*.jsonl'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
args=[a for a in sys.argv[1:] if not a.startswith('--')]
BASLA=int(args[0]) if args else 1789835700000
BIZ=sys.argv[sys.argv.index('--biz')+1].lower() if '--biz' in sys.argv else None
SADECE_BTC='--hepsi' not in sys.argv
SLIST=set(int(x) for x in sys.argv[sys.argv.index('--S')+1].split(',')) if '--S' in sys.argv else None   # yalniz bu pencereler

# ---- 1) kaset: tekil satirlar, tx gruplama, rol ----
key=lambda a:f"{a.get('transactionHash')}|{a.get('proxyWallet')}|{a.get('asset')}|{a.get('side')}|{a.get('size')}|{a.get('price')}"
seen=set(); T=collections.defaultdict(list)
for f in glob.glob(TAPE):
    for l in open(f):
        try: a=json.loads(l)
        except: continue
        if a['timestamp']*1000<BASLA: continue
        if SADECE_BTC and not a.get('slug','').startswith('btc-updown-5m-'): continue
        if SLIST is not None and int(a['slug'].split('-')[-1]) not in SLIST: continue
        k=key(a)
        if k in seen: continue
        seen.add(k); T[a['transactionHash']].append(a)
makers=[]; n_tx=0; n_tak=0
for tx,rows in T.items():
    if len(rows)<2: continue
    tot=sum(float(r['size']) for r in rows); big=max(rows,key=lambda r:float(r['size']))
    if abs(2*float(big['size'])-tot)>0.02*tot+0.5: continue   # taker tanimlanamadi
    n_tx+=1
    for r in rows:
        if r is big: continue
        if r['side']!='BUY': continue   # maker BID dolumlari (bizim oyun)
        makers.append(dict(tx=tx,w=r['proxyWallet'].lower(),tok=r['asset'],p=round(float(r['price']),3),pay=float(r['size']),
                           ts=r['timestamp'],S=int(r['slug'].split('-')[-1]),outcome=r['outcome'],taker=big['proxyWallet'].lower()))
print(f"tx {n_tx} | maker BID dolumu {len(makers)} | pencere {len({m['S'] for m in makers})} | baslangic {time.strftime('%H:%MZ',time.gmtime(BASLA/1000))}")
if not makers: sys.exit(0)

# ---- 2) defter: her token icin seviye tarihcesi (BID) ----
con=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
# tx hash -> CLOB eslesme ani (last_trade_price). Zincir ts CLOB'dan medyan 2,8 sn (p90 3,6) SONRA gelir.
TXMS={}
for ts,rj in con.execute("select ts_ms,raw_json from market_events where event_type='last_trade_price' and ts_ms>=?",(BASLA-60000,)):
    try: h=json.loads(rj).get('transaction_hash')
    except: continue
    if h and h not in TXMS: TXMS[h]=ts
def dolum_ani(m):
    return TXMS[m['tx']]-150 if m['tx'] in TXMS else m['ts']*1000-4500
HIST={}   # tok -> {price: [(ts_ms,size),...]}
def tarihce(tok):
    if tok in HIST: return HIST[tok]
    H=collections.defaultdict(list)
    cur={}
    for ts,et,rj in con.execute("select ts_ms,event_type,raw_json from market_events where asset_id=? and event_type in ('book','price_change') order by ts_ms,id",(tok,)):
        try: d=json.loads(rj)
        except: continue
        if et=='book':
            yeni={}
            for b in d.get('bids') or []:
                try: yeni[round(float(b['price']),3)]=float(b['size'])
                except: pass
            for p in set(cur)|set(yeni):
                if cur.get(p,0)!=yeni.get(p,0): H[p].append((ts,yeni.get(p,0)))
            cur=yeni
        else:
            for c in d.get('price_changes') or []:
                if c.get('asset_id')!=tok or (c.get('side') or '').upper()!='BUY': continue
                try: p=round(float(c['price']),3); s=float(c['size'])
                except: continue
                if cur.get(p,0)!=s: H[p].append((ts,s)); cur[p]=s
    HIST[tok]=H; return H
def seviye(tok,p,T):
    """T (ms) anindaki bid boyu ve seviyenin kesintisiz >0 oldugu suredir (sn). (None,None)=veri yok."""
    L=tarihce(tok).get(p)
    if not L: return None,None
    i=bisect.bisect_right([x[0] for x in L],T)-1
    if i<0: return None,None
    boy=L[i][1]
    j=i
    while j>=0 and L[j][1]>0: j-=1
    bas=L[j+1][0] if j+1<=i else T
    return boy,(T-bas)/1000 if boy>0 else 0

# ---- 3) her maker dolumu icin onde/dolan/kismi/yas ----
lvl=collections.defaultdict(float)
for m in makers: lvl[(m['tx'],m['tok'],m['p'])]+=m['pay']
veri=[]
for m in makers:
    T0=dolum_ani(m)            # hash hizali (CLOB ani -150 ms) ya da zincir ts -4,5 sn
    onde,yas=seviye(m['tok'],m['p'],T0)
    if onde is None: continue
    dolan=lvl[(m['tx'],m['tok'],m['p'])]
    m.update(onde=onde,yas=yas,dolan=dolan,kismi=(dolan<0.9*onde) if onde>0 else False)
    veri.append(m)
print(f"defterle eslesen maker dolumu {len(veri)}/{len(makers)} | hash hizali {sum(1 for m in veri if m['tx'] in TXMS)}")
if not veri: sys.exit(0)

# ---- 4) cuzdan ozetleri ----
def ozet(ad,g):
    if not g: return
    pay=sum(x['pay'] for x in g)
    km=[x for x in g if x['kismi']]
    print(f"  {ad:<12} dolum {len(g):>4} | pay {pay:>7.0f} | KISMI %{100*len(km)/len(g):>4.0f} | onde medyan {st.median([x['onde'] for x in g]):>6.0f} | "
          f"yas medyan {st.median([x['yas'] for x in g]):>6.1f}s (p25 {sorted(x['yas'] for x in g)[len(g)//4]:.1f}) | px medyan {st.median([x['p'] for x in g]):.2f} | "
          f"t medyan {st.median([x['ts']-x['S'] for x in g]):>3.0f}s")
print("\n### CUZDAN OZETI (maker BID dolumlari)   KISMI = seviye supurulmedi, dolan kuyrugun onundeydi")
ozet("HERKES",veri)
ozet("bosona",[x for x in veri if x['w']==BOS])
if BIZ: ozet("BIZ",[x for x in veri if x['w']==BIZ])
V=collections.defaultdict(list)
for x in veri: V[x['w']].append(x)
for w,g in sorted(V.items(),key=lambda kv:-sum(x['pay'] for x in kv[1]))[:8]:
    if w in (BOS,BIZ): continue
    ozet(w[:10],g)
print("\n### KISMI dolumlarda seviye yasi (herkes): ms mi dk mi?")
km=[x for x in veri if x['kismi']]
if km:
    for lo,hi,ad in [(0,1,'<1 sn (HIZ)'),(1,10,'1-10 sn'),(10,60,'10-60 sn'),(60,1e9,'>60 sn (ERKEN YERLESIM)')]:
        g=[x for x in km if lo<=x['yas']<hi]
        if g: print(f"  {ad:<24} {len(g):>4} dolum | pay {sum(x['pay'] for x in g):>7.0f} | bosona payi {sum(x['pay'] for x in g if x['w']==BOS):>6.0f}")
print("\n### bosona dolumlari tek tek")
for x in sorted([x for x in veri if x['w']==BOS],key=lambda x:x['ts']):
    print(f"  {time.strftime('%H:%M:%S',time.gmtime(x['ts']))} t{x['ts']-x['S']:>3} {x['outcome']:<4} px {x['p']:.2f} pay {x['pay']:>6.1f} | onde {x['onde']:>7.0f} dolan {x['dolan']:>7.0f} {'KISMI' if x['kismi'] else 'supurme'} | seviye yasi {x['yas']:.1f}s")
