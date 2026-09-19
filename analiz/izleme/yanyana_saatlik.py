#!/usr/bin/env python3
"""BIZ vs BOSONA — SAATLIK OZET (ayni bilgi, 24 parca yerine tek blok)."""
import json,sys,time,collections,urllib.request,datetime as dt
D='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5'
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def jget(u,t=12):
    r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(r,timeout=t))
def saat_ozet(t0,t1):
    biz=[]
    for l in open(f'{D}/LOG_ab.jsonl'):
        try: d=json.loads(l)
        except: continue
        if d.get('k')=='COZULDU' and t0<=d['utc_ms']/1000<t1: biz.append(d)
        if d.get('k')=='vol_atla' and t0<=d['utc_ms']/1000<t1: biz.append(d)
    coz=[x for x in biz if x['k']=='COZULDU']; atl=[x for x in biz if x['k']=='vol_atla']
    out=[]
    for kol in ('A','B'):
        s=[x for x in coz if x.get('kol')==kol]
        if not s: continue
        pay=sum(x.get('pay',0) for x in s); pnl=sum(x.get('pnl',0) for x in s)
        cift=sum(1 for x in s if x.get('pay',0)>0 and
                 len({r['oi'] for r in x.get('emirler',[]) if r.get('pay',0)>0})==2)
        out.append(f"{kol}: {len(s)}pen {pay:.0f}pay ${pnl:+.2f} ({100*pnl/pay if pay else 0:+.1f}kr/pay) cift{cift}")
    v=[x['vol'] for x in atl]
    ek=f" | ATLANAN {len(atl)} pen (vol medyan {sorted(v)[len(v)//2]:.1f})" if v else " | atlanan 0"
    # bosona
    b=''
    try:
        tr=jget(f"https://data-api.polymarket.com/trades?user={BOS}&takerOnly=false&limit=500")
        bt=[x for x in tr if t0<=x.get('timestamp',0)<t1]
        if bt:
            pay=sum(float(x.get('size',0)) for x in bt)
            b=f" || BOSONA {len(bt)} islem {pay:.0f} pay"
    except Exception as e: b=f" || bosona: {str(e)[:30]}"
    return " | ".join(out) + ek + b if out else ("BIZ: pencere yok" + ek + b)
while True:
    now=time.time(); t1=now//3600*3600; t0=t1-3600
    time.sleep(max(60, t1+3660-now))
    t1=time.time()//3600*3600; t0=t1-3600
    h=dt.datetime.fromtimestamp(t0,dt.UTC).strftime('%H:%MZ')
    print(f"[SAATLIK {h}] {saat_ozet(t0,t1)}",flush=True)
