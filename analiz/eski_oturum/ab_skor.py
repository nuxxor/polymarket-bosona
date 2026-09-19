#!/usr/bin/env python3
"""A/B SKORKART: kol A (v2 izgara) vs kol B (v3 DERIN-C). Yalniz 09-19 15:10Z sonrasi."""
import json,sys,collections
D='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5'
BASLA=int(sys.argv[1]) if len(sys.argv)>1 else 1789830600   # 15:10Z
kol={}; coz=[]
for l in open(f'{D}/LOG_ab.jsonl'):
    try: d=json.loads(l)
    except: continue
    if d.get('k')=='pencere' and d.get('S',0)>=BASLA: kol[d['S']]=d.get('kol')
    if d.get('k')=='COZULDU' and d.get('S',0)>=BASLA: coz.append(d)
agg=collections.defaultdict(lambda:{'n':0,'pay':0.0,'pnl':0.0,'cift':0,'bos':0,'mal':0.0})
for d in coz:
    k=d.get('kol') or kol.get(d['S']) or '?'
    a=agg[k]; a['n']+=1; a['pay']+=d.get('pay',0); a['pnl']+=d.get('pnl',0) if 'pnl' in d else 0
    a['mal']+=d.get('maliyet',0)
    if d.get('pay',0)<=0: a['bos']+=1
out=[]
for k in sorted(agg):
    a=agg[k]
    kp=100*a['pnl']/a['pay'] if a['pay'] else 0
    out.append(f"{k}: {a['n']:>3} pen | {a['pay']:>6.0f} pay ({a['pay']/max(a['n'],1):>4.1f}/pen) | "
               f"${a['pnl']:>+7.2f} ({kp:>+6.2f} kr/pay) | bos {a['bos']} | maliyet ${a['mal']:.0f}")
print(" || ".join(out) if out else "henuz cozulmus pencere yok")
