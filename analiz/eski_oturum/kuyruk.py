#!/usr/bin/env python3
"""KUYRUK POZISYONU OLCUMU — son acik soru.

Her emrimiz icin: KOYDUGUMUZ ANDA o fiyatta ONUMUZDE kac pay vardi?
Sonra: onumuzdeki paya gore dolum oranimiz nasil degisiyor?
Kuyruk baglayici kisitsa, onumuzdeki pay arttikca dolum orani COKMELI.

Veri: kendi LOG'umuz (emir fiyati+dolum) + defter kaydi (book + price_change).
"""
import sqlite3, json, sys, collections, bisect
import numpy as np

DB='/home/taygun/Masaüstü/polymarket/data/db/polymarket_orderbook.db'
LOG='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
BASLA=int(sys.argv[1]) if len(sys.argv)>1 else 0   # utc_ms alt sinir

# ---------- 1) kendi emirlerimiz ----------
pen={}; coz=[]
for l in open(LOG):
    try: d=json.loads(l)
    except: continue
    if d.get('k')=='pencere' and d.get('tokens'):
        pen[d['S']]={'tok':d['tokens'],'kol':d.get('kol'),'ms':d['utc_ms']}
    elif d.get('k')=='COZULDU' and d.get('emirler'):
        coz.append(d)
emirler=[]
for c in coz:
    w=pen.get(c['S'])
    if not w or w['ms']<BASLA: continue
    for r in c['emirler']:
        emirler.append({'S':c['S'],'kol':c.get('kol') or w['kol'],'oi':r['oi'],'p':round(r['p'],2),
                        'tok':w['tok'][r['oi']],'ms':w['ms'],'pay':r.get('pay',0.0),
                        'gecikme':r.get('gecikme_ms')})
print(f"emir: {len(emirler)} | pencere: {len({e['S'] for e in emirler})}")
if not emirler: print("defter kaydi baslamadan onceki pencereler - veri yok"); sys.exit(0)

# ---------- 2) defteri emir anina kadar kur ----------
con=sqlite3.connect(DB)
def bid_boyu(tok,T,px):
    """T aninda tok icin px fiyatindaki BID boyu (pay). None = veri yok."""
    row=con.execute("select ts_ms,raw_json from market_events where asset_id=? and event_type='book'"
                    " and ts_ms<=? order by ts_ms desc limit 1",(tok,T)).fetchone()
    if not row: return None
    t0,rj=row
    try: bk=json.loads(rj)
    except: return None
    lv={}
    for b in (bk.get('bids') or bk.get('buys') or []):
        try: lv[round(float(b['price']),2)]=float(b['size'])
        except: pass
    for ts,rj in con.execute("select ts_ms,raw_json from market_events where asset_id=? and"
                             " event_type='price_change' and ts_ms>? and ts_ms<=? order by ts_ms",(tok,t0,T)):
        try: ch=json.loads(rj)
        except: continue
        for c in (ch.get('price_changes') or []):
            if c.get('asset_id')!=tok: continue
            if (c.get('side') or 'BUY').upper() not in ('BUY','BID'): continue
            try: lv[round(float(c['price']),2)]=float(c['size'])
            except: pass
    return lv.get(px,0.0)

for e in emirler:
    e['onde']=bid_boyu(e['tok'],e['ms']+3000,e['p'])   # emrimiz ~3 sn sonra defterde
veri=[e for e in emirler if e['onde'] is not None]
print(f"defter verisi eslesen emir: {len(veri)}/{len(emirler)}\n")
if not veri: sys.exit(0)

# ---------- 3) onumuzdeki paya gore dolum orani ----------
print("### ONUMUZDEKI PAY -> DOLUM ORANI")
print(f"  {'onde (pay)':<16} {'emir':>6} {'dolan':>6} {'dolum %':>9} {'ort dolum payi':>15}")
for lo,hi,ad in [(0,1,'0 (kuyruk BOS)'),(1,25,'1-24'),(25,100,'25-99'),
                 (100,500,'100-499'),(500,2000,'500-1999'),(2000,10**9,'2000+')]:
    s=[e for e in veri if lo<=e['onde']<hi]
    if not s: continue
    d=[e for e in s if e['pay']>0]
    print(f"  {ad:<16} {len(s):>6} {len(d):>6} {100*len(d)/len(s):>8.1f}% "
          f"{np.mean([e['pay'] for e in s]):>14.2f}")
print("\n### KOLA GORE")
for kol in ('A','B'):
    s=[e for e in veri if e['kol']==kol]
    if not s: continue
    d=[e for e in s if e['pay']>0]
    print(f"  kol {kol}: {len(s):>4} emir | dolum %{100*len(d)/len(s):>5.1f} | "
          f"medyan onde {np.median([e['onde'] for e in s]):>8.0f} pay")
print("\n### FIYAT BASAMAGINA GORE")
for px in sorted({e['p'] for e in veri},reverse=True):
    s=[e for e in veri if e['p']==px]; d=[e for e in s if e['pay']>0]
    print(f"  {px:.2f}: {len(s):>4} emir | dolum %{100*len(d)/len(s):>5.1f} | "
          f"medyan onde {np.median([e['onde'] for e in s]):>8.0f} | ort onde {np.mean([e['onde'] for e in s]):>9.0f}")
