#!/usr/bin/env python3
"""Frozen forward shadows versus observable Bosona fills in the same market cohorts."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import statistics
import time
import urllib.parse

import bosona_coklu as cross
import bosona_gec_arastirma as base
from shadow_skor import stats

OUT = base.ROOT/'data/analysis/shadow_bosona_20260921_1200'
START, REBOUND, END = 1789946400, 1789951800, 1789992000
LOOKBACK = START-3*86400
PATHS = dict(baseline='polymarket-bosona-research/data/bosona_gec_forward',
             rebound='polymarket-bosona-rebound/data/forward')


def load(path):
    return json.loads(path.read_text())


def logs(name):
    return [json.loads(line) for line in (OUT/'raw'/PATHS[name]/'shadow.jsonl').read_text().splitlines()]


def group(slug):
    if '-updown-' in slug:
        return slug.split('-')[0]+'_'+slug.split('-')[2]
    if '-up-or-down-' in slug:
        sym=dict(bitcoin='btc',ethereum='eth',solana='sol',dogecoin='doge').get(slug.split('-')[0],slug.split('-')[0])
        return sym+('_1d' if '-up-or-down-on-' in slug else '_1h')
    return None


def fetch():
    until=load(OUT/'raw/manifest.json')['captured_ms']//1000
    parts=[load(p) for folder in (base.OUT/'activity',cross.OUT/'activity') for p in folder.glob('*.json')]
    parts=[r for r in parts if r.get('complete') and r['end']>=LOOKBACK and r['start']<until]
    spans=sorted((max(LOOKBACK,r['start']),min(until,r['end']+1)) for r in parts)
    needed=[]
    cursor=LOOKBACK
    for left,right in spans+[(until,until)]:
        while cursor<min(left,until):
            stop=min(cursor+3600,left,until)
            needed.append((cursor,stop))
            cursor=stop
        cursor=max(cursor,right)
    def chunk(span):
        left,right=span
        path=OUT/'activity'/f'{left}_{right}.json'
        if path.exists():
            return load(path)
        rows=[]
        for offset in range(0,5001,500):
            q=dict(user=base.WALLET,start=left,end=right-1,limit=500,offset=offset,
                   sortBy='TIMESTAMP',sortDirection='ASC')
            batch=base.get('https://data-api.polymarket.com/activity?'+urllib.parse.urlencode(q))
            assert isinstance(batch,list)
            assert all(r['proxyWallet'].lower()==base.WALLET and left<=r['timestamp']<right for r in batch)
            rows.extend(batch)
            if len(batch)<500:
                result=dict(start=left,end=right-1,rows=rows,complete=True,pages=offset//500+1)
                base.save(path,result)
                return result
        raise ValueError('activity pagination exhausted')
    with ThreadPoolExecutor(max_workers=3) as pool:
        parts+=list(pool.map(chunk,needed))
    rows=list({base.activity_key(r):r for part in parts for r in part['rows'] if LOOKBACK<=r['timestamp']<until}.values())
    base.save(OUT/'activity.json',rows)
    traded={r['slug'] for r in rows if r['type']=='TRADE' and group(r['slug'])}
    slugs=traded|{f'btc-updown-5m-{r["S"]}' for name in PATHS for r in logs(name)
                  if r['kind'] in ('decision','execution') and r['S']+300<=END}
    def market(slug):
        if '-updown-' in slug and not START<=int(slug.rsplit('-',1)[1])<END:
            return
        path=OUT/'markets'/f'{slug}.json'
        if path.exists():
            return
        if '-updown-' not in slug:
            cached=next((p for p in (cross.OUT/'markets'/f'{slug}.json',base.OUT/'markets'/f'{slug}.json') if p.exists()),None)
            if cached and not START<=cross.ts(load(cached)['eventStartTime'])<END:
                return
        m=base.get('https://gamma-api.polymarket.com/markets/slug/'+slug+'?snapshot='+str(int(time.time())//30))
        assert m['slug']==slug
        if START<=cross.ts(m['eventStartTime'])<END:
            base.save(path,m)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,_ in enumerate(pool.map(market,sorted(slugs))):
            if i%200==0:
                print('market scan',i,'/',len(slugs),flush=True)
    recent=[r for r in rows if START<=r['timestamp']<END]
    manifest=dict(start=START,end=END,lookback=LOOKBACK,fetch_until=until,new_spans=needed,
                  total_rows=len(rows),recent_types=dict(Counter(r['type'] for r in recent)),
                  recent_trade_groups=dict(Counter(group(r['slug']) or 'other' for r in recent if r['type']=='TRADE')),
                  recent_sides=dict(Counter(r['side'] for r in recent if r['type']=='TRADE')),
                  market_files=len(list((OUT/'markets').glob('*.json'))))
    base.save(OUT/'fetch_manifest.json',manifest)
    print(json.dumps(manifest,indent=2))


def dominant(q):
    return None if abs(q[0]-q[1])<1e-6 else int(q[1]>q[0])


def compare(selected,windows,fills,tolerance):
    index={w['S']:w for w in windows if w['group']=='btc_5m'}
    by=defaultdict(list)
    for f in fills:
        if f['group']=='btc_5m':
            by[f['S']].append(f)
    rows=[]
    for s in selected:
        w=index.get(s['S'])
        ff=by[s['S']]
        at=s['S']+s['age']
        near=[r for r in ff if abs(r['ts']-at)<=tolerance]
        past=[r for r in ff if r['ts']<=at]
        q=[sum(r['qty'] for r in near if r['side']==side) for side in (0,1)]
        inv=[sum(r['qty'] for r in past if r['side']==side) for side in (0,1)]
        nearby=dominant(q)
        rows.append(dict(S=s['S'],age=s['age'],shadow_side=s['side'],shadow_price=s['cost']/5,
                         bosona_traded=w is not None,first_side=w['first_side'] if w else None,
                         bosona_first_age=w['first_age'] if w else None,inventory_side=dominant(inv),
                         nearby_side=nearby,nearby_records=len(near),nearby_both=min(q)>0,
                         nearby_paid_price=sum(r['qty']*r['cash_price'] for r in near)/sum(q) if sum(q) else None,
                         bosona_cash_pnl=w['cash_cost_pnl'] if w else None,
                         bosona_equal5=w['cash_cost_pnl']*5/sum(w['qty']) if w else None,
                         shadow_pnl=5*(s['side']==s['winner'])-s['cost']))
    result=dict(shadow_selected=len(rows),bosona_active=sum(r['bosona_traded'] for r in rows),
                near_time_windows=sum(r['nearby_records']>0 for r in rows),
                near_both_sides=sum(r['nearby_both'] for r in rows),tolerance_seconds=tolerance)
    for kind in ('first','inventory','nearby'):
        eligible=[r for r in rows if r[kind+'_side'] is not None]
        result[kind]=dict(comparable=len(eligible),same=sum(r['shadow_side']==r[kind+'_side'] for r in eligible))
    common=[r for r in rows if r['bosona_traded']]
    result['common']=dict(windows=len(common),shadow_pnl=sum(r['shadow_pnl'] for r in common) if common else None,
                         bosona_cash_pnl=sum(r['bosona_cash_pnl'] for r in common) if common else None,
                         bosona_equal5=sum(r['bosona_equal5'] for r in common) if common else None)
    return result,rows


def analyze():
    activity=load(OUT/'activity.json')
    markets={p.stem:load(p) for p in (OUT/'markets').glob('*.json')}
    trades=defaultdict(list)
    for r in activity:
        if r['type']=='TRADE':
            trades[r['slug']].append(r)
    windows,fills,pending=[],[],[]
    for slug,m in sorted(markets.items()):
        tt=trades[slug]
        if not tt:
            continue
        S,end=cross.ts(m['eventStartTime']),cross.ts(m['endDate'])
        assert START<=S<END and cross.ts(m['startDate'])>=LOOKBACK
        assert json.loads(m['outcomes'])==['Up','Down']
        for r in tt:
            assert r['conditionId']==m['conditionId'] and r['outcome']==['Up','Down'][r['outcomeIndex']]
            assert str(r['asset'])==json.loads(m['clobTokenIds'])[r['outcomeIndex']]
        if end>END:
            pending.append(dict(slug=slug,reason='end_after_cutoff'))
            continue
        try:
            winner=base.outcome(m)
        except ValueError:
            pending.append(dict(slug=slug,reason='unresolved'))
            continue
        rr,result=base.ledger([dict(r,slug=f'btc-updown-5m-{S}') for r in tt],winner)
        first_ts=min(r['timestamp'] for r in tt)
        first=[r for r in tt if r['timestamp']==first_ts]
        qty=[sum(float(r['size']) for r in tt if r['outcomeIndex']==side) for side in (0,1)]
        fq=sum(float(r['size']) for r in first)
        same=defaultdict(set)
        for r in tt:
            same[r['timestamp']].add(r['outcomeIndex'])
        w=dict(slug=slug,group=group(slug),S=S,end=end,duration=end-S,winner=winner,qty=qty,
               cost=sum(float(r['usdcSize']) for r in tt),first_age=first_ts-S,
               first_price=sum(float(r['usdcSize']) for r in first)/fq,first_qty=fq,
               first_side=first[0]['outcomeIndex'] if len({r['outcomeIndex'] for r in first})==1 else None,
               ambiguous=any(len(s)>1 for s in same.values()),resolution_source=m.get('resolutionSource'),**result)
        assert abs(qty[winner]-w['cost']-w['cash_cost_pnl'])<1e-5
        windows.append(w)
        for r in rr:
            r.update(slug=slug,group=w['group'],duration=end-S,winner=winner)
        fills.extend(rr)
    report=dict(start=START,rebound_start=REBOUND,end=END,bosona={},shadows={},comparisons={},pending=pending)
    for label,left in [('baseline_period',START),('rebound_period',REBOUND)]:
        ww=[w for w in windows if w['S']>=left]
        ff=[r for r in fills if r['S']>=left]
        report['bosona'][label]={g:cross.aggregate([w for w in ww if w['group']==g],[r for r in ff if r['group']==g]) for g in sorted({w['group'] for w in ww})}
    normalized={}
    for name,folder in PATHS.items():
        manifest=load(OUT/'raw'/folder/'watch_manifest.json')
        records=logs(name)
        assigned=set(range(manifest['start_S'],END,300))
        by_age={}
        for age in manifest['slots']:
            kind='decision' if name=='baseline' else 'execution'
            es=sorted([r for r in records if r['kind']==kind and r['age']==age and r['S'] in assigned],key=lambda r:r['S'])
            gaps=[r for r in records if r['kind']=='gap' and r['age']==age and r['S'] in assigned]
            assert len(es)+len(gaps)==len(assigned)
            assert {r['S'] for r in es+gaps}==assigned
            rules=['favorite','aligned','buffer'] if name=='baseline' else ['rebound','favorite']
            entry=dict(assigned=len(assigned),eligible=len(es),gaps=len(gaps),gap_reasons=dict(Counter(r['reason'] for r in gaps)),rules={})
            for rule in rules:
                rr=[]
                for r in es:
                    m=markets[f'btc-updown-5m-{r["S"]}']
                    try:
                        winner=base.outcome(m)
                    except ValueError:
                        winner=None
                    side=(r['side'] if r['selected'][rule] else None) if name=='baseline' else r[rule]
                    cost=(r['cost']+r['fee'] if name=='baseline' else sum(r['costs'][side])) if side is not None else 0.
                    fee=(r['fee'] if name=='baseline' else r['costs'][side][1]) if side is not None else 0.
                    rr.append(dict(S=r['S'],age=age,side=side,cost=cost,fee=fee,winner=winner))
                    books=[r['execution_book']] if name=='baseline' else r['execution_books']
                    costs=[(r['cost'],r['fee'])] if name=='baseline' else r['costs']
                    for b,c in zip(books,costs):
                        computed=base.ask_cost(b,m)
                        assert all(abs(a-b)<1e-8 for a,b in zip(computed,c))
                entry['rules'][rule]=stats(rr)
                key=f'{name}_{age}_{rule}'
                normalized[key]=rr
                chosen=[r for r in rr if r['side'] is not None and r['winner'] is not None]
                report['comparisons'][key]={}
                for tol in (5,15,30):
                    comp,pairs=compare(chosen,windows,fills,tol)
                    report['comparisons'][key][str(tol)]=comp
                    if tol==15:
                        base.save(OUT/'pairs'/f'{key}.json',pairs)
            by_age[str(age)]=entry
        report['shadows'][name]=dict(start=manifest['start_S'],duration_hours=(END-manifest['start_S'])/3600,by_age=by_age)
    for label,left in [('baseline_period',START),('rebound_period',REBOUND)]:
        ff=[r for r in fills if r['group']=='btc_5m' and r['S']>=left]
        report['bosona'][label]['late_behavior']={}
        for seconds in (100,60,20):
            late=[r for r in ff if 300-seconds<r['age']<300]
            report['bosona'][label]['late_behavior'][str(seconds)]={
                kind:base.summary([r for r in late if r['opening_kind']==kind]) for kind in ('first','add','reopen',None)}
    btc=[w for w in windows if w['group']=='btc_5m']
    report['sizing']=dict(positive_windows=sum(w['cash_cost_pnl']>0 for w in btc),
        negative_windows=sum(w['cash_cost_pnl']<0 for w in btc),
        median_window_shares=statistics.median(sum(w['qty']) for w in btc),
        positive_median_shares=statistics.median(sum(w['qty']) for w in btc if w['cash_cost_pnl']>0),
        negative_median_shares=statistics.median(sum(w['qty']) for w in btc if w['cash_cost_pnl']<0),
        largest_profit_windows=[{k:w[k] for k in ('S','cash_cost_pnl','qty')} for w in sorted(btc,key=lambda w:w['cash_cost_pnl'],reverse=True)[:3]])
    report['rebates_in_clock_interval']={kind:sum(float(r['usdcSize']) for r in activity if r['type']==kind and START<=r['timestamp']<END)
                                         for kind in ('MAKER_REBATE','TAKER_REBATE')}
    report['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for name in ('windows','fills','normalized','report'):
        base.save(OUT/f'{name}.json',locals()[name])
    print(json.dumps(dict(shadows=report['shadows'],bosona=report['bosona']),indent=2))


def validate():
    windows=load(OUT/'windows.json')
    fills=load(OUT/'fills.json')
    activity=load(OUT/'activity.json')
    selected={w['slug']:w for w in windows if w['group']=='btc_5m'}
    for g in {w['group'] for w in windows}:
        ww=[w for w in windows if w['group']==g]
        for w in (min(ww,key=lambda w:w['cash_cost_pnl']),max(ww,key=lambda w:w['cash_cost_pnl'])):
            selected[w['slug']]=w
    def one(w):
        m=load(OUT/'markets'/f'{w["slug"]}.json')
        path=OUT/'trade_checks'/f'{w["slug"]}.json'
        if path.exists():
            tt=load(path)
        else:
            tt=[]
            for offset in range(0,10001,500):
                query=urllib.parse.urlencode(dict(user=base.WALLET,market=m['conditionId'],takerOnly='false',limit=500,offset=offset))
                time.sleep(1)  # Public trades endpoint returned 429 under concurrent verification.
                batch=base.get('https://data-api.polymarket.com/trades?'+query)
                assert all(r['proxyWallet'].lower()==base.WALLET and r['conditionId']==m['conditionId'] for r in batch)
                tt.extend(batch)
                if len(batch)<500:
                    break
            else:
                raise ValueError('trade pagination exhausted')
            base.save(path,tt)
        expected=Counter((r['tx'],r['side'],round(r['qty'],6)) for r in fills if r['slug']==w['slug'])
        actual=Counter((r['transactionHash'],r['outcomeIndex'],round(float(r['size']),6)) for r in tt)
        assert expected==actual,w['slug']
        q=[sum(float(r['size']) for r in tt if r['outcomeIndex']==side) for side in (0,1)]
        gross=sum(float(r['size'])*float(r['price']) for r in tt)
        assert all(abs(a-b)<1e-5 for a,b in zip(q,w['qty']))
        assert abs(q[w['winner']]-gross-w['gross_pnl'])<1e-4
        return dict(slug=w['slug'],records=len(tt),matched=True)
    checked=[one(w) for w in selected.values()]
    raw=load(OUT/'raw/manifest.json')
    for name,entry in raw['files'].items():
        assert hashlib.sha256((OUT/'raw'/name).read_bytes()).hexdigest()==entry['sha256']
    payouts=[]
    for w in windows:
        acts=[r for r in activity if r.get('slug')==w['slug']]
        merges=sum(float(r['usdcSize']) for r in acts if r['type']=='MERGE')
        redeems=sum(float(r['usdcSize']) for r in acts if r['type']=='REDEEM')
        assert merges<=min(w['qty'])+1e-4
        assert merges+redeems<=w['qty'][w['winner']]+1e-4
        payouts.append(dict(slug=w['slug'],potential_payout=w['qty'][w['winner']],merge=merges,redeem=redeems,
                            remaining_payout=w['qty'][w['winner']]-merges-redeems))
    base.save(OUT/'validation.json',dict(trade_checks=checked,markets=len(windows),raw_hashes=len(raw['files']),payouts=payouts))
    print('Independent trade identity/quantity/gross-PnL checks:',len(checked),'markets; merge/redeem bounds:',len(payouts))


def check():
    assert dominant([5,5]) is None and dominant([5,4])==0 and dominant([0,1])==1
    assert group('xrp-updown-5m-123')=='xrp_5m'
    assert stats([])['pnl'] is None
    selection=[dict(S=0,age=240,side=0,cost=2.,winner=0)]
    w=[dict(S=0,group='btc_5m',first_side=1,first_age=50,cash_cost_pnl=10.,qty=[20,10])]
    ff=[dict(S=0,group='btc_5m',ts=50,side=1,qty=10,cash_price=.4),
        dict(S=0,group='btc_5m',ts=241,side=0,qty=20,cash_price=.5)]
    result,_=compare(selection,w,ff,15)
    assert result['first']['same']==0 and result['inventory']['same']==0 and result['nearby']['same']==1
    assert abs(result['common']['bosona_equal5']-5/3)<1e-9
    cross.check()
    print('Same-market, nearest-time, inventory and equal-share comparison checks passed')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['fetch','analyze','validate','check'])
    globals()[p.parse_args().action]()
