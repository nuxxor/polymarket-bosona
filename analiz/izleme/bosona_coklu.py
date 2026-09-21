#!/usr/bin/env python3
"""Cross-market public fill anatomy; outcomes are labels, never decision inputs."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import statistics
import time
import urllib.parse

import bosona_gec_arastirma as base
import bosona_derin as deep

OUT = base.ROOT/'data/analysis/bosona_coklu_20260921'
START = int(datetime(2026, 9, 13, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 9, 21, 0, 30, tzinfo=timezone.utc).timestamp())
LOOKBACK = START-3*86400


def ts(value):
    return int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp())


def group(slug):
    names = dict(bitcoin='btc', ethereum='eth', solana='sol')
    parts = slug.split('-')
    if len(parts) > 3 and parts[0] in ('btc', 'eth', 'sol') and parts[1] == 'updown' and parts[2] in ('5m', '15m'):
        return parts[0]+'_'+parts[2]
    if parts[0] in names and '-up-or-down-' in slug and slug.endswith('-et') and parts[-2].endswith(('am', 'pm')):
        return names[parts[0]]+'_1h'
    return None


def bounds(m):
    g = group(m['slug'])
    duration = dict(m5m=300, m15m=900, m1h=3600)['m'+g.split('_')[1]]
    end = ts(m['endDate'])
    start = ts(m['eventStartTime'])
    if end-start != duration:
        raise ValueError('unexpected market duration')
    if g.endswith(('5m', '15m')) and int(m['slug'].rsplit('-', 1)[1]) != start:
        raise ValueError('slug/start mismatch')
    return start, end, duration


def fetch():
    cached = [json.loads(p.read_text()) for p in (base.OUT/'activity').glob('*.json')]
    covered = sorted((r['start'], r['end']+1) for r in cached if r.get('complete'))
    until = max(END+1800, int(time.time())-300)
    # Extend earlier full-activity slices; their old BTC filter is not reused.
    needed, cursor = [], LOOKBACK
    for left, right in covered+[(until, until)]:
        if right <= cursor:
            continue
        while cursor < min(left, until):
            stop = min(cursor+21600, left, until)
            needed.append((cursor, stop))
            cursor = stop
        cursor = max(cursor, right)
    def chunk(span):
        left, right = span
        path = OUT/'activity'/f'{left}_{right}.json'
        if path.exists():
            return json.loads(path.read_text())
        rows = []
        for offset in range(0, 5001, 500):
            query = urllib.parse.urlencode(dict(user=base.WALLET, start=left, end=right-1,
                                                limit=500, offset=offset, sortBy='TIMESTAMP', sortDirection='ASC'))
            batch = base.get('https://data-api.polymarket.com/activity?'+query)
            assert isinstance(batch, list)
            assert all(r['proxyWallet'].lower() == base.WALLET and left <= r['timestamp'] < right for r in batch)
            rows.extend(batch)
            if len(batch) < 500:
                result = dict(start=left, end=right-1, rows=rows, complete=True, pages=offset//500+1, fetched_ms=round(time.time()*1000))
                base.save(path, result)
                return result
        raise ValueError(f'pagination exhausted: {left}')
    with ThreadPoolExecutor(max_workers=3) as pool:
        cached += list(pool.map(chunk, needed))
    unique = {base.activity_key(r): r for part in cached for r in part['rows'] if LOOKBACK <= r['timestamp'] < until}
    rows = list(unique.values())
    base.save(OUT/'activity.json', rows)
    slugs = sorted({r['slug'] for r in rows if r['type'] == 'TRADE' and group(r['slug'])})
    def market(slug):
        path = OUT/'markets'/f'{slug}.json'
        if path.exists():
            return
        existing = base.OUT/'markets'/f'{slug}.json'
        m = json.loads(existing.read_text()) if existing.exists() else base.get('https://gamma-api.polymarket.com/markets/slug/'+slug)
        assert m['slug'] == slug
        base.save(path, m)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, _ in enumerate(pool.map(market, slugs)):
            if i % 200 == 0:
                print('market metadata', i, '/', len(slugs), flush=True)
    base.save(OUT/'fetch_manifest.json', dict(start=START, end=END, lookback=LOOKBACK, fetch_until=until,
              new_slices=needed, slices=len(cached), all_activity_rows=len(rows), market_files=len(slugs)))


def med(values):
    return statistics.median(values) if values else None


def aggregate(windows, fills):
    q = sum(r['qty'] for r in fills)
    pnl = sum(w['cash_cost_pnl'] for w in windows)
    days = defaultdict(float)
    for w in windows:
        days[datetime.fromtimestamp(w['S'], timezone.utc).strftime('%Y-%m-%d')] += w['cash_cost_pnl']
    def share(fn):
        return sum(r['qty'] for r in fills if fn(r))/q if q else None
    return dict(markets=len(windows), fills=len(fills), shares=q, pnl=pnl,
                gross_pnl=sum(w['gross_pnl'] for w in windows),
                cents_per_share=100*pnl/q if q else None,
                ex_top3=pnl-sum(sorted((w['cash_cost_pnl'] for w in windows), reverse=True)[:3]),
                equal5_per_window=sum(5*w['cash_cost_pnl']/sum(w['qty']) for w in windows),
                days=dict(days), positive_days=sum(x > 0 for x in days.values()),
                pair_cash_pnl=sum(w['pair_cash_pnl'] for w in windows), residual_cash_pnl=sum(w['residual_cash_pnl'] for w in windows),
                both_sides=sum(min(w['qty']) > 1e-6 for w in windows),
                balanced=sum(abs(w['qty'][0]-w['qty'][1]) <= .02 for w in windows),
                first_age_median=med([w['first_age'] for w in windows]),
                first_fraction_median=med([w['first_age']/w['duration'] for w in windows]),
                first_price_median=med([w['first_price'] for w in windows]),
                first_share_median=med([w['first_qty'] for w in windows]),
                first_paid_above_60=sum(w['first_price'] > .6 for w in windows),
                fill_qty_median=med([r['qty'] for r in fills]),
                paid_average=sum(r['qty']*r['cash_price'] for r in fills)/q if q else None,
                cheap_below30_share=share(lambda r:r['price'] < .3), above60_share=share(lambda r:r['price'] > .6),
                prestart_share=share(lambda r:r['age'] < 0), afterend_share=share(lambda r:r['age'] >= r['duration']),
                last20_share=share(lambda r:0 < r['duration']-r['age'] <= 20),
                lastthird_share=share(lambda r:2/3 <= r['age']/r['duration'] < 1),
                last20_pnl=sum(r['marginal_cash_pnl'] for r in fills if 0 < r['duration']-r['age'] <= 20),
                lastthird_pnl=sum(r['marginal_cash_pnl'] for r in fills if 2/3 <= r['age']/r['duration'] < 1),
                completion_share=sum(r['completion_qty'] for r in fills)/q if q else None,
                add_share=sum(r['opening_qty'] for r in fills if r['opening_kind'] == 'add')/q if q else None,
                ambiguous_windows=sum(w['ambiguous'] for w in windows),
                rules=dict(Counter(w['resolution_source'] for w in windows)))


def analyze():
    activity = json.loads((OUT/'activity.json').read_text())
    grouped = defaultdict(list)
    for r in activity:
        if r['type'] == 'TRADE' and group(r['slug']):
            grouped[r['slug']].append(r)
    windows, fills, excluded = [], [], []
    for slug, trades in sorted(grouped.items()):
        m = json.loads((OUT/'markets'/f'{slug}.json').read_text())
        try:
            S, end, duration = bounds(m)
            if not START <= S < END or end > END:
                continue
            if ts(m['startDate']) < LOOKBACK:
                raise ValueError('market existed before fetched history')
            winner = base.outcome(m)
            # Reuse the exact FIFO accounting; its only BTC-specific assumption is the slug suffix.
            mapped = [dict(r, slug=f'btc-updown-5m-{S}') for r in trades]
            rr, result = base.ledger(mapped, winner)
            first_ts = min(r['timestamp'] for r in trades)
            first = [r for r in trades if r['timestamp'] == first_ts]
            qty = [sum(float(r['size']) for r in trades if r['outcomeIndex'] == side) for side in (0, 1)]
            cost = sum(float(r['usdcSize']) for r in trades)
            assert abs(qty[winner]-cost-result['cash_cost_pnl']) < 1e-5
            assert all(r['conditionId'] == m['conditionId'] and r['outcome'] == ['Up', 'Down'][r['outcomeIndex']] for r in trades)
            assert all(str(r['asset']) == json.loads(m['clobTokenIds'])[r['outcomeIndex']] for r in trades)
            same_second = defaultdict(set)
            for r in trades:
                same_second[r['timestamp']].add(r['outcomeIndex'])
            ambiguous = any(len(sides) > 1 for sides in same_second.values())
            fq = sum(float(r['size']) for r in first)
            w = dict(slug=slug, group=group(slug), S=S, end=end, duration=duration, winner=winner,
                     qty=qty, cost=cost, first_age=first_ts-S, first_price=sum(float(r['usdcSize']) for r in first)/fq,
                     first_qty=fq, first_side=first[0]['outcomeIndex'] if len({r['outcomeIndex'] for r in first}) == 1 else None,
                     ambiguous=ambiguous, resolution_source=m.get('resolutionSource'), **result)
            windows.append(w)
            for r in rr:
                r.update(slug=slug, group=w['group'], duration=duration, winner=winner, ambiguous=ambiguous)
            fills.extend(rr)
        except (ValueError, KeyError) as ex:
            excluded.append(dict(slug=slug, reason=str(ex)))
    groups = sorted({w['group'] for w in windows})
    report = dict(start=START, end=END, groups={}, excluded=excluded,
                  note='Observable fills, cash-cost settlement PnL excluding rebates/fixed costs. FIFO attribution is not strategy proof; '
                       'same-second opposite-side ordering is ambiguous. Paid >.5 does not prove contemporaneous favorite. '
                       'Not a counterfactual fill simulation or holdout study.')
    for g in groups:
        ww, ff = [w for w in windows if w['group'] == g], [r for r in fills if r['group'] == g]
        report['groups'][g] = aggregate(ww, ff)
        report['groups'][g]['unambiguous'] = aggregate([w for w in ww if not w['ambiguous']], [r for r in ff if not r['ambiguous']])
        report['groups'][g]['recent_24h'] = aggregate([w for w in ww if w['S'] >= END-86400], [r for r in ff if r['S'] >= END-86400])
    by_hour = defaultdict(lambda: defaultdict(float))
    for r in fills:
        dt = datetime.fromtimestamp(r['ts'], timezone.utc)
        by_hour[dt.strftime('%Y-%m-%d %H')][r['group']] += r['qty']*r['cash_price']
    report['hourly_cash'] = dict(by_hour)
    base.save(OUT/'windows.json', windows)
    base.save(OUT/'fills.json', fills)
    base.save(OUT/'report.json', report)
    print(json.dumps({g:{k:v for k,v in r.items() if k not in ('unambiguous','recent_24h','rules','days')} for g,r in report['groups'].items()},indent=2))
    print('excluded',len(excluded), Counter(r['reason'] for r in excluded))


def check():
    assert group('eth-updown-15m-123') == 'eth_15m'
    assert group('solana-up-or-down-september-20-2026-8pm-et') == 'sol_1h'
    assert group('sol-updown-4h-123') is None
    assert group('solana-up-or-down-on-september-20-2026') is None
    assert bounds(dict(slug='sol-updown-5m-0', eventStartTime='1970-01-01T00:00:00Z', endDate='1970-01-01T00:05:00Z')) == (0,300,300)
    base.check()
    print('Cross-market mapping, event times and FIFO accounting checks passed')


def candles():
    def one(sym):
        path = OUT/f'{sym}_1m.json'
        if path.exists():
            return
        rows, start = [], (LOOKBACK-3600)*1000
        while start < END*1000:
            batch = base.get('https://api.binance.com/api/v3/klines?'+urllib.parse.urlencode(
                             dict(symbol=sym.upper()+'USDT', interval='1m', startTime=start, endTime=END*1000-1, limit=1000)))
            assert batch and batch[0][0] == start
            assert all(b[0]-a[0] == 60000 for a,b in zip(batch,batch[1:]))
            rows.extend(batch)
            start = batch[-1][0]+60000
        base.save(path, rows)
        print('closed minute bars',sym,len(rows),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, ('btc','eth','sol')))


def context():
    windows = json.loads((OUT/'windows.json').read_text())
    fills = json.loads((OUT/'fills.json').read_text())
    kk = {}
    for sym in ('btc','eth','sol'):
        rows = json.loads((OUT/f'{sym}_1m.json').read_text())
        kk[sym] = [r[6] for r in rows], rows
    for r in fills:
        # Public fill timestamps are not decision timestamps: use -5s and report -10s sensitivity.
        for lag in (5, 10):
            f = deep.candle_features(kk[r['group'].split('_')[0]], (r['ts']-lag)*1000)
            r[f'own_rsi_{lag}'] = f['rsi14'] if r['side'] == 0 else 100-f['rsi14']
            r[f'own_return1_{lag}'] = (1 if r['side'] == 0 else -1)*f['return1']
            r[f'bar_close_{lag}'] = f['bar_close_ms']
            assert f['bar_close_ms']+2000 <= (r['ts']-lag)*1000
    report = dict(groups={}, daily_style={}, night_cash={}, note='Minute-bar context at public fill time minus5s/minus10s. '
                  'Not actual order placement time. Paid-price/RSI match is only a necessary-condition proxy; '
                  'does not establish the 10s Chainlink rebound or quoted favorite rule.')
    for g in sorted({w['group'] for w in windows}):
        rr = [r for r in fills if r['group'] == g]
        detail = {}
        for name, ff in dict(all=rr, first=[r for r in rr if r['opening_kind']=='first'],
                             add=[r for r in rr if r['opening_kind']=='add'],
                             last20_add=[r for r in rr if r['opening_kind']=='add' and 0<r['duration']-r['age']<=20],
                             lastthird_add=[r for r in rr if r['opening_kind']=='add' and 2/3<=r['age']/r['duration']<1]).items():
            q = sum(r['qty'] for r in ff)
            detail[name] = dict(records=len(ff), shares=q, pnl=sum(r['marginal_cash_pnl'] for r in ff),
                                price= sum(r['qty']*r['cash_price'] for r in ff)/q if q else None,
                                rsi_weak_share={str(lag):sum(r['qty'] for r in ff if r[f'own_rsi_{lag}']<40)/q if q else None for lag in (5,10)},
                                cheap_rsi_share={str(lag):sum(r['qty'] for r in ff if r['price']<.5 and r[f'own_rsi_{lag}']<40)/q if q else None for lag in (5,10)},
                                weak_then_minute_turn_share=sum(r['qty'] for r in ff if r['price']<.5 and r['own_rsi_5']<40 and r['own_return1_5']>0)/q if q else None)
        report['groups'][g] = detail
        day_groups=defaultdict(list)
        for w in windows:
            if w['group']==g:
                day_groups[datetime.fromtimestamp(w['S'],timezone.utc).strftime('%Y-%m-%d')].append(w)
        report['daily_style'][g]={day:aggregate(ww,[r for r in rr if datetime.fromtimestamp(r['S'],timezone.utc).strftime('%Y-%m-%d')==day]) for day,ww in day_groups.items()}
    # Cash share by complete calendar days and UTC+3 night (00:00-06:00), not a chosen best hour.
    by=defaultdict(lambda:defaultdict(float))
    for r in fills:
        local=datetime.fromtimestamp(r['ts']+3*3600,timezone.utc)
        key=local.strftime('%Y-%m-%d')+(' night00-06' if local.hour<6 else ' day06-24')
        by[key][r['group']]+=r['qty']*r['cash_price']
    report['night_cash']=dict(by)
    base.save(OUT/'context_fills.json',fills)
    base.save(OUT/'context.json',report)
    print(json.dumps(report['groups'],indent=2))


def validate():
    windows = json.loads((OUT/'windows.json').read_text())
    fills = json.loads((OUT/'fills.json').read_text())
    rows = []
    for g in sorted({w['group'] for w in windows}):
        ww = [w for w in windows if w['group']==g and w['end'] < END-7200]
        rows.extend([min(ww,key=lambda w:w['cash_cost_pnl']), max(ww,key=lambda w:w['cash_cost_pnl'])])
    def one(w):
        m = json.loads((OUT/'markets'/f'{w["slug"]}.json').read_text())
        query=urllib.parse.urlencode(dict(user=base.WALLET,market=m['conditionId'],takerOnly='false',limit=500))
        trades=base.get('https://data-api.polymarket.com/trades?'+query)
        assert len(trades)<500 and all(r['proxyWallet'].lower()==base.WALLET and r['conditionId']==m['conditionId'] for r in trades)
        q=[sum(float(r['size']) for r in trades if r['outcomeIndex']==side) for side in (0,1)]
        assert all(abs(a-b)<1e-5 for a,b in zip(q,w['qty'])),w['slug']
        cash=sum(float(r['size'])*float(r['price']) for r in trades)
        assert abs(q[w['winner']]-cash-w['gross_pnl'])<1e-4,w['slug']
        expected={(r['tx'],r['side'],round(r['qty'],6)) for r in fills if r['slug']==w['slug']}
        observed={(r['transactionHash'],r['outcomeIndex'],round(float(r['size']),6)) for r in trades}
        assert expected==observed,w['slug']
        result=dict(slug=w['slug'],records=len(trades),q=q,gross_pnl=q[w['winner']]-cash,identities_match=True)
        if w['group'].endswith('1h'):
            query=urllib.parse.urlencode(dict(symbol=w['group'].split('_')[0].upper()+'USDT',interval='1h',startTime=w['S']*1000,limit=1))
            k=base.get('https://api.binance.com/api/v3/klines?'+query)[0]
            assert k[0]==w['S']*1000
            winner=0 if float(k[4])>=float(k[1]) else 1
            assert winner==w['winner'],w['slug']
            result['binance_winner']=winner
        return result
    with ThreadPoolExecutor(max_workers=3) as pool:
        checked=list(pool.map(one,rows))
    base.save(OUT/'validation.json',dict(markets=checked,total=18,external_hourly_outcomes=6))
    print('18 extreme win/loss markets: quantities, trade identities and gross PnL matched; 6 Binance hourly outcomes matched')


def matched():
    windows=json.loads((OUT/'windows.json').read_text())
    def cell(w):
        return (w['S']//86400, sum(w['first_price']>=p for p in (.3,.5,.7)),
                sum(w['first_age']/w['duration']>=t for t in (.1,1/3,2/3)))
    btc=defaultdict(list)
    for w in windows:
        if w['group']=='btc_5m':
            btc[cell(w)].append(w)
    result={}
    for group in ('eth_5m','sol_5m'):
        target=defaultdict(list)
        for w in windows:
            if w['group']==group:
                target[cell(w)].append(w)
        common=btc.keys()&target.keys()
        den=sum(min(len(btc[k]),len(target[k])) for k in common)
        rates=[]
        for data in (btc,target):
            rates.append(sum(min(len(btc[k]),len(target[k]))*sum(min(w['qty'])>1e-6 for w in data[k])/len(data[k]) for k in common)/den)
        result[group]=dict(common_cells=len(common),btc_windows=sum(len(btc[k]) for k in common),
                            other_windows=sum(len(target[k]) for k in common),weight=den,
                            matched_both_side_rates=dict(btc=rates[0],other=rates[1]))
    base.save(OUT/'matched.json',dict(results=result,controls='UTC day, first-fill cash price (<.3/.5/.7), first-fill relative age (<.1/one-third/two-thirds)',
                                   caveat='Descriptive overlap weighting. Liquidity, unfilled orders and private inventory intent are not identified.'))
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['fetch','analyze','check','candles','context','validate','matched'])
    args = p.parse_args()
    globals()[args.action]()
