#!/usr/bin/env python3
"""Read-only accounting audit. Cache new public responses only in this directory."""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import urllib.parse
import urllib.error

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import research as r  # noqa: E402
import muhasebe as accounting  # noqa: E402
RAW,OUT=HERE/'raw',HERE/'results'
OFFLINE=False


def cached(name,url):
    p=RAW/name
    if not p.exists():
        if OFFLINE:
            raise FileNotFoundError('offline cache missing: '+str(p))
        for attempt in range(6):
            try:
                time.sleep(1)
                data=r.base.get(url,timeout=25,attempts=1)
                r.save(p,dict(url=url,fetched_ms=round(time.time()*1000),data=data))
                break
            except urllib.error.HTTPError as e:
                if e.code!=429 or attempt==5:
                    raise
                time.sleep(max(10,min(30,int(e.headers.get('Retry-After','15')))))
    return r.read(p)['data']


def activity(name,wallet,**query):
    rows=[]
    for offset in range(0,5001,500):
        q=dict(user=wallet,limit=500,offset=offset,sortBy='TIMESTAMP',sortDirection='ASC',**query)
        data=cached(f'{name}_{offset}.json','https://data-api.polymarket.com/activity?'+urllib.parse.urlencode(q))
        assert isinstance(data,list) and all(x['proxyWallet'].lower()==wallet for x in data)
        rows.extend(data)
        if len(data)<500:
            return rows
    raise ValueError('pagination exhausted')


def exact(rows,winner):
    assert all(x['side']=='BUY' for x in rows)
    q=[sum((D(str(x['size'])) for x in rows if x['outcomeIndex']==i),D(0)) for i in (0,1)]
    cash=sum((D(str(x.get('usdcSize',D(str(x['size']))*D(str(x['price']))))) for x in rows),D(0))
    gross=sum((D(str(x['size']))*D(str(x['price'])) for x in rows),D(0))
    return dict(rows=len(rows),q=list(map(float,q)),cash=float(cash),pnl=float(q[winner]-cash),gross_pnl=float(q[winner]-gross))


def run():
    multi=[x for x in r.read(r.RAW/'multiplicity.json') if x['slug'].startswith('btc-updown-5m-')]
    for name in ('activity','windows'):
        dest=RAW/f'original_btc5_{name}.json'
        if not dest.exists():
            shutil.copyfile(r.REPO/f'data/analysis/bosona_gec_20260921/{name}.json',dest)
    original=r.read(RAW/'original_btc5_activity.json')
    old_by=defaultdict(list)
    for x in original:
        old_by[x['slug']].append(x)
    max_by=defaultdict(list)
    for x in r.read(r.RAW/'activity.json'):
        if x.get('slug','').startswith('btc-updown-5m-'):
            max_by[x['slug']].append(x)
    slugs=sorted({x['slug'] for x in multi})
    def one(slug):
        m=cached('btc5/markets/'+slug+'.json','https://gamma-api.polymarket.com/markets/slug/'+slug)
        assert r.classify(m)['group']=='btc_5m'
        rows=activity('btc5/activity/'+slug,r.base.WALLET,market=m['conditionId'],start=r.LOOKBACK,end=r.END-1)
        assert all(x['slug']==slug for x in rows)
        return slug,m,rows
    changes=[]
    nontrade=[]
    with ThreadPoolExecutor(max_workers=1) as pool:
        for slug,m,rows in pool.map(one,slugs):
            winner=r.base.outcome(m)
            trades=[x for x in rows if x['type']=='TRADE']
            collapsed=list({r.base.activity_key(x):x for x in trades}.values())
            a,b=exact(collapsed,winner),exact(trades,winner)
            if a!=b:
                check=cached('btc5/trades/'+slug+'.json','https://data-api.polymarket.com/trades?'+urllib.parse.urlencode(dict(user=r.base.WALLET,market=m['conditionId'],takerOnly='false',limit=500,offset=0)))
                assert len(check)<500 and Counter(accounting.key(x) for x in trades)==Counter(accounting.key(x) for x in check)
                old=[x for x in old_by[slug] if x['type']=='TRADE']
                assert not old or Counter(r.base.activity_key(x) for x in old)==Counter(r.base.activity_key(x) for x in collapsed)
                extra=Counter(r.base.activity_key(x) for x in trades)-Counter(r.base.activity_key(x) for x in collapsed)
                detail=[dict(x,multiplicity=Counter(r.base.activity_key(y) for y in trades)[r.base.activity_key(x)]) for x in collapsed if r.base.activity_key(x) in extra]
                _,lf=r.base.ledger(trades,winner)
                _,lo=r.base.ledger(collapsed,winner)
                changes.append(dict(slug=slug,S=r.classify(m)['S'],winner=winner,published_cohort=bool(old),old=a,corrected=b,
                    delta={k:b[k]-a[k] for k in ('rows','cash','pnl','gross_pnl')},extra_fills=detail,
                    fifo_delta={k:lf[k]-lo[k] for k in lf}))
            newcounts=Counter(r.base.activity_key(x) for x in rows if x['type']!='TRADE')
            cachedcounts=Counter(r.base.activity_key(x) for x in max_by[slug] if x['type']!='TRADE')
            if newcounts!=cachedcounts:
                nontrade.append(dict(slug=slug,cached_count=sum(cachedcounts.values()),fresh_count=sum(newcounts.values())))
    published=r.read(RAW/'original_btc5_windows.json')
    total=sum(x['cash_cost_pnl'] for x in published)
    cohort=[x for x in changes if x['published_cohort']]
    r.save(OUT/'btc5_audit.json',dict(changes=changes,checked_markets=len(slugs),nontrade_artifacts=nontrade,
        published=dict(markets=len(published),old_pnl=total,corrected_pnl=total+sum(x['delta']['pnl'] for x in cohort),
                       missing_fills=sum(x['delta']['rows'] for x in cohort),missing_cash=sum(x['delta']['cash'] for x in cohort),delta_pnl=sum(x['delta']['pnl'] for x in cohort)),
        scope='Only accounting, no BTC5 strategy replay. All suspicious keys checked against fresh public APIs.'))
    # Public execution snapshot contains public wallet identity; no key/config read.
    for n in ('kaynak','rapor'):
        dst=RAW/f'own_{n}.json'
        if not dst.exists():
            shutil.copyfile(r.REPO/f'data/referans/muhasebe_20260920_{n}.json',dst)
    snap=r.read(RAW/'own_kaynak.json')
    report=r.read(RAW/'own_rapor.json')
    wallet={x['proxyWallet'].lower() for x in snap['islemler']}
    assert len(wallet)==1
    wallet=wallet.pop()
    assert hashlib.sha256(wallet.encode()).hexdigest()==snap['cuzdan_sha256']
    fresh=[]
    for s in range(snap['baslangic'],snap['son'],10800):
        fresh.extend(activity(f'own/activity/{s}',wallet,start=s,end=min(s+10800,snap['son'])-1))
    changes_own=[]
    diffs=[]
    for w in report['pencereler']:
        slug=f'btc-updown-5m-{w["S"]}'
        rr=[x for x in fresh if x.get('slug')==slug and x['type']=='TRADE']
        collapsed=list({accounting.key(x):x for x in rr}.values())
        a,b=accounting.totals(collapsed,w['kazanan']),accounting.totals(rr,w['kazanan'])
        if len(rr)!=len(collapsed):
            changes_own.append(dict(slug=slug,kol=w['kol'],old=a,corrected=b,delta_pnl=b['pnl']-a['pnl'],extra_rows=len(rr)-len(collapsed)))
        if abs(b['pnl']-w['api']['pnl'])>1e-5:
            diffs.append(dict(slug=slug,kol=w['kol'],published=w['api']['pnl'],fresh=b['pnl'],delta_pnl=b['pnl']-w['api']['pnl']))
    r.save(OUT/'own_btc5_audit.json',dict(start=snap['baslangic'],end=snap['son'],windows=len(report['pencereler']),
        raw_activity=len(fresh),trade_rows=sum(x['type']=='TRADE' for x in fresh),multiplicity_changes=changes_own,all_differences=diffs,
        caveat='This covers the available 20Sep reconciliation snapshot only, not uncollected London D/E runtime. '
        'muhasebe.py API/tape dictionary keys remain structurally vulnerable. Bot order-state accounting uses cumulative size_matched per order, a different path.'))
    print(json.dumps({'bosona':r.read(OUT/'btc5_audit.json')['published'],'own':r.read(OUT/'own_btc5_audit.json')},ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true')
    OFFLINE=parser.parse_args().offline
    run()
