#!/usr/bin/env python3
"""Public-only, isolated research. No order, wallet, SSH or deployment code."""
import argparse
import bisect
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import statistics
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'src'))
import bosona_gec_arastirma as base  # noqa: E402
import bosona_coklu as cross  # noqa: E402
import bosona_derin as deep  # noqa: E402

REPO = Path('/home/taygun/Masaüstü/polymarket-bosona')
RAW, OUT = HERE / 'raw', HERE / 'results'
START, SPLIT, UPDATE, END = (int(datetime(2026, 9, d, h, tzinfo=timezone.utc).timestamp())
                             for d, h in ((13, 0), (18, 0), (21, 0), (21, 12)))
LOOKBACK = START - 3 * 86400
PRIMARY = ['btc_15m', 'btc_1h', 'eth_5m', 'eth_15m', 'eth_1h',
           'sol_5m', 'sol_15m', 'sol_1h']


def read(p):
    return json.loads(p.read_text())


def save(p, obj):
    base.save(p, obj)


def period(s):
    return 'discovery' if s < SPLIT else 'chronological' if s < UPDATE else 'update'


def public(url):
    time.sleep(.15)
    return base.get(url, timeout=30)


def classify(m):
    """Names discover candidates; dates AND contractual source determine the class."""
    s, end = cross.ts(m['eventStartTime']), cross.ts(m['endDate'])
    duration = end-s
    assert json.loads(m['outcomes']) == ['Up', 'Down']
    src, desc = m.get('resolutionSource', '').lower(), m['description'].lower()
    link = re.search(r'/streams/([a-z0-9]+)-usd-(twap-60s-)?streams', src)
    bn = re.search(r'/trade/([a-z0-9]+)_usdt', src)
    if link:
        sym = link[1]
        if link[2]:
            assert 'time-weighted average' in desc and f'{sym}/usd' in desc
            mechanism = 'chainlink_twap60'
        else:
            assert 'chainlink' in desc and f'{sym}/usd' in desc
            mechanism = 'chainlink_spot'
    elif bn:
        sym = bn[1]
        assert f'{sym}/usdt' in desc and 'close' in desc
        if duration == 3600:
            assert 'open' in desc and '1 hour candle' in desc and '1h' in desc
            mechanism = 'binance_candle'
        elif duration == 86400:
            assert '1 minute candle' in desc and '50-50' in desc
            mechanism = 'binance_noon_1m_close_tie_split'
        else:
            raise ValueError('unrecognized Binance duration/rules')
    else:
        raise ValueError('unsupported resolution source: ' + src)
    unit = {300: '5m', 900: '15m', 3600: '1h', 14400: '4h', 86400: '1d'}.get(duration)
    if unit is None:
        raise ValueError('unsupported official duration: ' + str(duration))
    if unit in ('5m', '15m'):
        assert mechanism == 'chainlink_twap60'
    return dict(group=f'{sym}_{unit}', sym=sym, S=s, end=end,
                duration=duration, mechanism=mechanism)


def fetch():
    slices = RAW / 'activity'
    slices.mkdir(exist_ok=True)
    sources = ['bosona_gec_20260921', 'bosona_coklu_20260921', 'shadow_bosona_20260921_1200']
    for name in sources:
        for p in (REPO / 'data/analysis' / name / 'activity').glob('*.json'):
            dest = slices / (name + '_' + p.name)
            if not dest.exists():
                shutil.copyfile(p, dest)
    parts = [read(p) for p in slices.glob('*.json')]
    assert all(r.get('complete') for r in parts)
    cursor = LOOKBACK
    for left, right in sorted((r['start'], r['end']+1) for r in parts):
        if left <= cursor:
            cursor = max(cursor, right)
    assert cursor >= END, ('activity coverage gap', cursor)
    rows, multiplicity = merge_slices(parts)
    assert all(r['proxyWallet'].lower() == base.WALLET for r in rows)
    save(RAW / 'activity.json', rows)
    save(RAW / 'multiplicity.json', multiplicity)

    market_dir = RAW / 'markets'
    market_dir.mkdir(exist_ok=True)
    for name in sources[1:]:
        for p in (REPO / 'data/analysis' / name / 'markets').glob('*.json'):
            if not p.name.startswith('btc-updown-5m-'):
                dest = market_dir / p.name
                if not dest.exists():
                    shutil.copyfile(p, dest)
    # Expected recurring schedule only discovers candidates; missing responses stay missing.
    expected = set()
    for g in PRIMARY:
        sym, unit = g.split('_')
        duration = {'5m': 300, '15m': 900, '1h': 3600}[unit]
        for s in range(START, END, duration):
            if unit != '1h':
                slug = f'{sym}-updown-{unit}-{s}'
            else:
                dt = datetime.fromtimestamp(s, ZoneInfo('America/New_York'))
                name = dict(btc='bitcoin', eth='ethereum', sol='solana')[sym]
                slug = f'{name}-up-or-down-{dt.strftime("%B").lower()}-{dt.day}-{dt.year}-{dt.hour%12 or 12}{"am" if dt.hour<12 else "pm"}-et'
            expected.add(slug)
    traded = {r['slug'] for r in rows if r['type'] == 'TRADE'
              and not r['slug'].startswith('btc-updown-5m-')}
    want = sorted(expected | traded)
    missing = []
    for slug in want:
        p = market_dir / (slug + '.json')
        if not p.exists() or (read(p).get('closed') is not True):
            missing.append(slug)
    failures = []
    for i in range(0, len(missing), 60):
        names = missing[i:i+60]
        q = urllib.parse.urlencode({'slug': names, 'limit': 100, 'closed': 'true'}, doseq=True)
        batch = public('https://gamma-api.polymarket.com/markets?' + q)
        assert isinstance(batch, list) and all(m['slug'] in names for m in batch)
        for m in batch:
            save(market_dir / (m['slug'] + '.json'), m)
        failures.extend(sorted(set(names) - {m['slug'] for m in batch}))
        if i % 600 == 0:
            print('metadata', i, '/', len(missing), 'missing responses', len(failures), flush=True)
    unresolved = []
    for slug in failures:
        if slug not in expected:
            unresolved.append(slug)
            continue
        try:
            m = public('https://gamma-api.polymarket.com/markets/slug/'+slug)
            assert m['slug']==slug
            save(market_dir/(slug+'.json'),m)
        except urllib.error.HTTPError as e:
            if e.code!=404:
                raise
            unresolved.append(slug)
    failures = unresolved
    save(RAW / 'universe.json', dict(expected=sorted(expected), traded=sorted(traded), missing=failures))
    symset = {'btc', 'eth', 'sol'}
    exclusions = []
    for p in market_dir.glob('*.json'):
        try:
            symset.add(classify(read(p))['sym'])
        except (AssertionError, KeyError, ValueError) as e:
            exclusions.append([p.stem, str(e)])
    for sym in sorted(symset):
        p = RAW / (sym + '_1m.json')
        if p.exists():
            continue
        old = REPO / 'data/analysis/bosona_coklu_20260921' / p.name
        bars = read(old) if old.exists() else []
        bars = [r for r in bars if (LOOKBACK-3600)*1000 <= r[0] < END*1000]
        begin = bars[-1][0]+60000 if bars else (LOOKBACK-3600)*1000
        while begin < END*1000:
            q = urllib.parse.urlencode(dict(symbol=sym.upper()+'USDT', interval='1m',
                                      startTime=begin, endTime=END*1000-1, limit=1000))
            batch = public('https://api.binance.com/api/v3/klines?' + q)
            assert batch and batch[0][0] == begin
            bars.extend(batch)
            begin = batch[-1][0]+60000
        assert all(b[0]-a[0] == 60000 for a, b in zip(bars, bars[1:]))
        save(p, bars)
        print('minute bars', sym, len(bars), flush=True)
    save(RAW / 'fetch_manifest.json', dict(start=START, end=END, lookback=LOOKBACK,
         activity_slices=len(parts), activity_rows=len(rows), expected=len(expected),
         missing=failures, metadata_screen_exclusions=exclusions, fetched_ms=round(time.time()*1000)))


def merge_slices(parts):
    # Dedup overlapping downloads, not equal-sized executions in one transaction.
    counts, sample = Counter(), {}
    for p in parts:
        assert p['complete']
        batch = [r for r in p['rows'] if LOOKBACK <= r['timestamp'] < END]
        counts |= Counter(base.activity_key(r) for r in batch)
        sample.update((base.activity_key(r), r) for r in batch)
    rows = [sample[k] for k, n in sorted(counts.items()) for _ in range(n)]
    detail = [dict(slug=sample[k].get('slug'), type=sample[k]['type'],
                   ts=sample[k]['timestamp'], tx=sample[k]['transactionHash'],
                   size=sample[k]['size'], cash=sample[k]['usdcSize'], count=n)
              for k, n in counts.items() if n>1]
    return rows, detail


def fresh_interval():
    previous = read(RAW/'activity.json')
    fresh = []
    for start in range(UPDATE,END,3*3600):
        end = min(start+3*3600,END)
        p = RAW/'activity'/f'fresh_{start}_{end}.json'
        if not p.exists():
            rows = []
            for offset in range(0,5001,500):
                q = dict(user=base.WALLET,start=start,end=end-1,limit=500,offset=offset,
                         sortBy='TIMESTAMP',sortDirection='ASC')
                a = public('https://data-api.polymarket.com/activity?'+urllib.parse.urlencode(q))
                assert isinstance(a,list) and all(start<=x['timestamp']<end and x['proxyWallet'].lower()==base.WALLET for x in a)
                rows.extend(a)
                if len(a)<500:
                    break
            else:
                raise ValueError('fresh interval pagination exhausted')
            save(p,dict(start=start,end=end-1,rows=rows,complete=True,pages=offset//500+1,
                        fetched_ms=round(time.time()*1000)))
        fresh.extend(read(p)['rows'])
    old = Counter(base.activity_key(x) for x in previous if UPDATE<=x['timestamp']<END and x['type']=='TRADE')
    new = Counter(base.activity_key(x) for x in fresh if x['type']=='TRADE')
    save(OUT/'fresh_interval_check.json',dict(start=UPDATE,end=END,old_trades=sum(old.values()),new_trades=sum(new.values()),
         added=list((new-old).items()),removed=list((old-new).items()),
         btc15_trades=sum(x['type']=='TRADE' and x['slug'].startswith('btc-updown-15m-') for x in fresh)))
    print('Fresh interval trade counts',sum(old.values()),sum(new.values()),'diff',sum((new-old).values()),sum((old-new).values()))


def load_bars():
    return {p.stem.split('_')[0]: ([r[6] for r in read(p)], read(p))
            for p in RAW.glob('*_1m.json')}


def features(kk, s, now):
    f = deep.candle_features(kk, now*1000)
    if not f:
        return {}
    i = bisect.bisect_right(kk[0], now*1000-2000)-1
    seq = kk[1][i-20:i+1]
    changes = [math.log(float(b[4])/float(a[4])) for a, b in zip(seq, seq[1:])]
    f['volatility_bp'] = statistics.pstdev(changes)*10000
    f['last_price'] = float(seq[-1][4])
    # The first bar's open is used only after that bar itself has closed.
    j = bisect.bisect_left(kk[0], s*1000+59999)
    if j < len(kk[0]) and kk[1][j][0] == s*1000 and kk[0][j]+2000 <= now*1000:
        f['open_proxy'] = float(kk[1][j][1])
        f['distance_bp'] = math.log(f['last_price']/f['open_proxy'])*10000
    assert f['bar_close_ms']+2000 <= now*1000
    return f


def stat(rows, field='pnl'):
    by = defaultdict(float)
    day = defaultdict(float)
    for r in rows:
        by[r['slug']] += r[field]
        day[datetime.fromtimestamp(r['S'], timezone.utc).strftime('%Y-%m-%d')] += r[field]
    vals = list(by.values())
    total = sum(vals)
    return dict(n=len(rows), markets=len(vals), pnl=total,
                wins=sum(v>1e-8 for v in vals), ex_top3=total-sum(sorted(vals, reverse=True)[:3]),
                days=dict(day), periods={p:sum(r[field] for r in rows if period(r['S'])==p)
                                        for p in ('discovery', 'chronological', 'update')})


def analyze():
    activity = read(RAW / 'activity.json')
    corrections = {p.stem:read(p) for p in (RAW/'activity_checks').glob('*.json')}
    activity = [r for r in activity if r.get('slug') not in corrections]
    activity += [r for part in corrections.values() for r in part if r['timestamp']<END]
    trades, acts = defaultdict(list), defaultdict(list)
    for r in activity:
        if r.get('slug'):
            acts[r['slug']].append(r)
        if r['type'] == 'TRADE' and not r['slug'].startswith('btc-updown-5m-'):
            trades[r['slug']].append(r)
    bars = load_bars()
    windows, fills, universe, excluded, checks, violations = [], [], [], [], [], []
    wanted = set(read(RAW / 'universe.json')['expected']) | set(trades)
    for slug in sorted(wanted):
        path = RAW / 'markets' / (slug+'.json')
        if not path.exists():
            excluded.append(dict(slug=slug, reason='metadata_unavailable', traded=slug in trades))
            continue
        m = read(path)
        try:
            meta = classify(m)
        except (AssertionError, ValueError, KeyError) as e:
            excluded.append(dict(slug=slug, reason='classification:'+str(e), traded=slug in trades))
            continue
        s, end = meta['S'], meta['end']
        if meta['group']=='btc_5m':
            raise AssertionError('BTC5m entered new research')
        if not START <= s < END or end > END:
            if slug in trades:
                excluded.append(dict(slug=slug, reason='outside_cohort', **meta))
            continue
        try:
            winner = base.outcome(m)
        except ValueError:
            excluded.append(dict(slug=slug, reason='unresolved', **meta))
            continue
        tt = sorted(trades[slug], key=lambda r:(r['timestamp'], r['transactionHash'], r['outcomeIndex']))
        universe.append(dict(slug=slug, traded=bool(tt), winner=winner, **meta))
        if not tt:
            continue
        if cross.ts(m['startDate']) < LOOKBACK:
            excluded.append(dict(slug=slug, reason='left_truncated_creation', **meta))
            continue
        if any(r['type'] in ('SPLIT','CONVERSION') for r in acts[slug]):
            excluded.append(dict(slug=slug, reason='unsupported_nontrade_inventory', **meta))
            continue
        assert all(r['side']=='BUY' for r in tt), slug
        tokens = json.loads(m['clobTokenIds'])
        assert all(r['conditionId']==m['conditionId'] and str(r['asset'])==tokens[r['outcomeIndex']]
                   and r['outcome']==['Up','Down'][r['outcomeIndex']] for r in tt), slug
        rr, totals = base.ledger([dict(r, slug=f'btc-updown-5m-{s}') for r in tt], winner)
        first_t = tt[0]['timestamp']
        first = [r for r in tt if r['timestamp']==first_t]
        fq = sum(float(r['size']) for r in first)
        same = defaultdict(set)
        for r in tt:
            same[r['timestamp']].add(r['outcomeIndex'])
        qty = [sum(float(r['size']) for r in tt if r['outcomeIndex']==side) for side in (0,1)]
        cost = sum(float(r['usdcSize']) for r in tt)
        exact = sum(Decimal(str(r['size']))*(r['outcomeIndex']==winner)-Decimal(str(r['usdcSize'])) for r in tt)
        assert abs(float(exact)-totals['cash_cost_pnl'])<1e-5
        merges = sum(float(r['usdcSize']) for r in acts[slug] if r['type']=='MERGE')
        redeems = sum(float(r['usdcSize']) for r in acts[slug] if r['type']=='REDEEM')
        if merges > min(qty)+1e-4 or merges+redeems > qty[winner]+1e-4:
            violations.append(dict(slug=slug,qty=qty,merge=merges,redeem=redeems,winner=winner))
        w = dict(slug=slug, winner=winner, **meta, **totals, qty=qty, cost=cost,
                 first_age=first_t-s, first_qty=fq, first_price=sum(float(r['usdcSize']) for r in first)/fq,
                 first_side=first[0]['outcomeIndex'] if len({r['outcomeIndex'] for r in first})==1 else None,
                 ambiguous=any(len(v)>1 for v in same.values()), merge=merges, redeem=redeems,
                 worst_outcome=min(qty)-cost, best_outcome=max(qty)-cost,
                 residual_qty=abs(qty[0]-qty[1]), condition=m['conditionId'])
        for sec in (5,10):
            package = [r for r in tt if r['timestamp']<=first_t+sec]
            w[f'first{sec}_qty'] = sum(float(r['size']) for r in package)
            w[f'first{sec}_price'] = sum(float(r['usdcSize']) for r in package)/w[f'first{sec}_qty']
        q, c, max_risk, last_price = [0.,0.], 0., 0., [None,None]
        for r in rr:
            side = r['side']
            r.update(slug=slug, winner=winner, **meta, ambiguous=w['ambiguous'], window_pnl=w['cash_cost_pnl'])
            r['pre_payout_pnl'] = [v-c for v in q]
            r['pre_worst_pnl'] = min(q)-c
            r['pre_other_qty'], r['pre_own_qty'] = q[1-side], q[side]
            r['previous_same_price'] = last_price[side]
            r['price_change_same'] = r['cash_price']-last_price[side] if last_price[side] is not None else None
            r['previous_unmatched_price'] = r['pre_unmatched_cash_cost']/abs(r['pre_net']) if abs(r['pre_net'])>1e-6 else None
            r['completion_ratio'] = r['qty']/abs(r['pre_net']) if abs(r['pre_net'])>1e-6 and r['completion_qty']>0 else None
            r['completion_unit_pair_pnl'] = r['pair_cash_pnl']/r['completion_qty'] if r['completion_qty']>1e-6 else None
            for lag in (5,10):
                f = features(bars[meta['sym']], s, r['ts']-lag)
                r[f'context_{lag}'] = f
            q[side] += r['qty']
            c += r['qty']*r['cash_price']
            r['post_worst_pnl'] = min(q)-c
            r['post_payout_pnl'] = [v-c for v in q]
            max_risk = max(max_risk, c-min(q))
            last_price[side] = r['cash_price']
        w['peak_worst_loss'] = max_risk
        w['post_first_worst_loss'] = -min(r['post_worst_pnl'] for r in rr if r['ts']==first_t)
        first_rr = [r for r in rr if r['ts']==first_t]
        w['first5_pnl'] = 5*sum(r['marginal_cash_pnl'] for r in first_rr)/fq
        w['equal5_pnl'] = 5*w['cash_cost_pnl']/sum(qty)
        w['first_context'] = rr[0]['context_5']
        windows.append(w)
        fills.extend(rr)
        checks.append(dict(slug=slug, decimal_pnl=str(exact), official_rule=meta['mechanism'],
                           payout=qty[winner], merge=merges, redeem=redeems))
    save(OUT/'windows.json', windows)
    save(OUT/'fills.json', fills)
    save(OUT/'universe.json', universe)
    save(OUT/'accounting_checks.json', checks)
    save(OUT/'exclusions.json', excluded)
    save(OUT/'payout_violations.json', violations)
    groups = {}
    for g in sorted({w['group'] for w in windows}):
        ww = [w for w in windows if w['group']==g]
        ff = [r for r in fills if r['group']==g]
        agg = cross.aggregate([dict(w,resolution_source=w['mechanism']) for w in ww], ff)
        agg.update(universe=sum(u['group']==g for u in universe),
                   median_peak_risk=statistics.median(w['peak_worst_loss'] for w in ww),
                   maximum_peak_risk=max(w['peak_worst_loss'] for w in ww),
                   median_residual_qty=statistics.median(w['residual_qty'] for w in ww),
                   median_worst_settlement=statistics.median(w['worst_outcome'] for w in ww),
                   first5_pnl=sum(w['first5_pnl'] for w in ww),
                   first5_qty_median=statistics.median(w['first5_qty'] for w in ww),
                   first10_qty_median=statistics.median(w['first10_qty'] for w in ww),
                   periods={p:stat([dict(w,pnl=w['cash_cost_pnl']) for w in ww if period(w['S'])==p])
                            for p in ('discovery','chronological','update')},
                   rules=dict(Counter(w['mechanism'] for w in ww)))
        phases = {}
        for kind in ('first','add','reopen','completion'):
            parts = []
            for r in ff:
                q = r['completion_qty'] if kind=='completion' else r['opening_qty'] if r['opening_kind']==kind else 0.
                if q>1e-6:
                    parts.append(dict(r,part_qty=q,pnl=q*((r['side']==r['winner'])-r['cash_price'])))
            ps = stat(parts)
            ps['qty'] = sum(r['part_qty'] for r in parts)
            ps['paid'] = sum(r['part_qty']*r['cash_price'] for r in parts)/ps['qty'] if ps['qty'] else None
            ps['quantity_wins'] = sum(r['part_qty'] for r in parts if r['side']==r['winner'])/ps['qty'] if ps['qty'] else None
            phases[kind] = ps
        assert abs(sum(v['pnl'] for v in phases.values())-agg['pnl'])<1e-5
        agg['phases'] = phases
        completions = [r for r in ff if r['completion_qty']>1e-6]
        adds = [r for r in ff if r['opening_kind']=='add']
        agg['completions'] = dict(records=len(completions),
            positive_pair=sum(r['pair_cash_pnl']>1e-8 for r in completions),
            positive_pair_qty=sum(r['completion_qty'] for r in completions if r['pair_cash_pnl']>1e-8),
            qty=sum(r['completion_qty'] for r in completions),
            overfill=sum(r['opening_qty']>1e-6 for r in completions),
            exact_within1pct=sum(abs(r['completion_ratio']-1)<=.01 for r in completions),
            pair_pnl_in_losing_windows=sum(r['pair_cash_pnl'] for r in completions if r['window_pnl']<0),
            risk_reduced=sum(r['post_worst_pnl']>r['pre_worst_pnl']+1e-8 for r in completions))
        agg['addition_price'] = {label:stat([dict(r,pnl=r['marginal_cash_pnl']) for r in adds
              if r['price_change_same'] is not None and (r['price_change_same'] < -.005 if label=='cheaper' else
                 r['price_change_same'] > .005 if label=='dearer' else abs(r['price_change_same'])<=.005)])
              for label in ('cheaper','same','dearer')}
        groups[g] = agg
    save(OUT/'summary.json', dict(groups=groups, total_markets=len(windows), total_fills=len(fills),
         universe=len(universe), excluded=dict(Counter(r['reason'] for r in excluded))))
    print(json.dumps({g:{k:v[k] for k in ('markets','pnl','ex_top3','equal5_per_window','first_age_median',
          'first_price_median','both_sides','pair_cash_pnl','residual_cash_pnl')} for g,v in groups.items()},indent=2))


def refresh():
    multiple = read(RAW/'multiplicity.json')
    violations = read(OUT/'payout_violations.json')
    wanted = {r['slug'] for r in multiple+violations if r.get('slug')
              and not r['slug'].startswith('btc-updown-5m-')}
    changes = []
    before = read(RAW/'activity.json')
    for i, slug in enumerate(sorted(wanted)):
        p = RAW/'activity_checks'/(slug+'.json')
        if not p.exists():
            m = read(RAW/'markets'/(slug+'.json'))
            rows = []
            for offset in range(0,5001,500):
                q = dict(user=base.WALLET,market=m['conditionId'],start=1,end=END-1,
                         limit=500,offset=offset,sortBy='TIMESTAMP',sortDirection='ASC')
                batch = public('https://data-api.polymarket.com/activity?'+urllib.parse.urlencode(q))
                assert isinstance(batch,list)
                assert all(r['proxyWallet'].lower()==base.WALLET and r['conditionId']==m['conditionId'] for r in batch)
                rows.extend(batch)
                if len(batch)<500:
                    break
            else:
                raise ValueError('targeted history pagination exhausted')
            save(p, rows)
        old = Counter(base.activity_key(r) for r in before if r.get('slug')==slug)
        new = Counter(base.activity_key(r) for r in read(p) if r['timestamp']<END)
        changes.append(dict(slug=slug,old_rows=sum(old.values()),new_rows=sum(new.values()),
                             removed=list((old-new).items()),added=list((new-old).items())))
        if i%30==0:
            print('fresh activity multiset audit',i,'/',len(wanted),flush=True)
    save(OUT/'refresh_changes.json',changes)


def histories():
    universe = sorted(read(OUT/'universe.json'),key=lambda w:(w['group'],w['S']))
    cached_tokens = {t for p in (RAW/'histories').glob('*.json') for t in read(p)['request']['markets']}
    universe = [w for w in universe if not set(json.loads(read(RAW/'markets'/(w['slug']+'.json'))['clobTokenIds']))<=cached_tokens]
    def one(chunk):
        tokens = [t for w in chunk for t in json.loads(read(RAW/'markets'/(w['slug']+'.json'))['clobTokenIds'])]
        request = dict(markets=tokens,start_ts=min(w['S'] for w in chunk)-120,
                       end_ts=max(w['end'] for w in chunk),fidelity=1)
        key = hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()[:20]
        p = RAW/'histories'/(key+'.json')
        if not p.exists():
            for attempt in range(3):
                try:
                    req = urllib.request.Request('https://clob.polymarket.com/batch-prices-history',
                          data=json.dumps(request).encode(),headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
                    with urllib.request.urlopen(req,timeout=30) as response:
                        result = json.load(response)
                    assert isinstance(result['history'],dict) and set(result['history'])<=set(tokens)
                    save(p,dict(request=request,response=result,fetched_ms=round(time.time()*1000)))
                    time.sleep(.2)
                    break
                except (OSError,ValueError):
                    if attempt==2:
                        raise
                    time.sleep(2+attempt)
        a = read(p)['response']['history']
        return dict(file=p.name,tokens=len(tokens),nonempty=sum(bool(a.get(t)) for t in tokens),
                    points=sum(len(a.get(t,[])) for t in tokens))
    chunks = [universe[i:i+10] for i in range(0,len(universe),10)]
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i,r in enumerate(pool.map(one,chunks)):
            results.append(r)
            if i%100==0:
                print('public price batches',i,'/',len(chunks),flush=True)
    all_results = []
    for p in sorted((RAW/'histories').glob('*.json')):
        a = read(p)
        all_results.append(dict(file=p.name,tokens=len(a['request']['markets']),
             nonempty=sum(bool(a['response']['history'].get(t)) for t in a['request']['markets']),
             points=sum(len(a['response']['history'].get(t,[])) for t in a['request']['markets'])))
    save(RAW/'history_manifest.json',all_results)


def validate():
    windows = read(OUT/'windows.json')
    activity = read(RAW/'activity.json')
    corrections = {p.stem:read(p) for p in (RAW/'activity_checks').glob('*.json')}
    activity = [r for r in activity if r.get('slug') not in corrections]
    activity += [r for part in corrections.values() for r in part if r['timestamp']<END]
    by = defaultdict(list)
    for a in activity:
        if a['type']=='TRADE':
            by[a['slug']].append(a)
    assert not read(OUT/'payout_violations.json')
    selected = {}
    for g in sorted({w['group'] for w in windows}):
        ww = [w for w in windows if w['group']==g]
        if g in PRIMARY or len(ww)>=100:
            for w in [min(ww,key=lambda w:w['cash_cost_pnl']),max(ww,key=lambda w:w['cash_cost_pnl']),
                      min(ww,key=lambda w:hashlib.sha256(w['slug'].encode()).hexdigest())]:
                selected[w['slug']] = w
    for a in read(RAW/'multiplicity.json'):
        if a['type']=='TRADE':
            w = next((w for w in windows if w['slug']==a['slug']),None)
            if w:
                selected[w['slug']] = w
    checks = []
    for i,(slug,w) in enumerate(sorted(selected.items())):
        p = RAW/'trade_checks'/(slug+'.json')
        if not p.exists():
            q = dict(user=base.WALLET,market=w['condition'],takerOnly='false',limit=500)
            time.sleep(.6)
            rows = public('https://data-api.polymarket.com/trades?'+urllib.parse.urlencode(q))
            assert isinstance(rows,list) and len(rows)<500
            save(p,rows)
        rows = read(p)
        assert all(a['proxyWallet'].lower()==base.WALLET and a['conditionId']==w['condition'] for a in rows)
        def key(a):
            return (a['transactionHash'],a['outcomeIndex'],a['side'],round(float(a['size']),6),round(float(a['price']),6))
        assert Counter(map(key,rows))==Counter(map(key,by[slug])), slug
        gross = sum(float(a['size'])*((a['outcomeIndex']==w['winner'])-float(a['price'])) for a in rows)
        assert abs(gross-w['gross_pnl'])<1e-4
        checks.append(dict(slug=slug,n=len(rows),gross_pnl=gross,multiset_match=True))
        if i%10==0:
            print('independent trades checks',i,'/',len(selected),flush=True)
    bars = load_bars()
    rules, missing = [], []
    for u in read(OUT/'universe.json'):
        m = read(RAW/'markets'/(u['slug']+'.json'))
        ev = next((e for e in m.get('events',[]) if e['slug']==u['slug']),{})
        em = ev.get('eventMetadata',{})
        if em.get('priceToBeat') is not None and em.get('finalPrice') is not None:
            predicted = 0 if float(em['finalPrice'])>=float(em['priceToBeat']) else 1
            assert predicted==u['winner'],u['slug']
        else:
            missing.append(u['slug'])
        if u['mechanism']=='binance_candle':
            kk = bars[u['sym']][1]
            ii = {k[0]:k for k in kk}
            assert u['winner']==(0 if float(ii[(u['end']-60)*1000][4])>=float(ii[u['S']*1000][1]) else 1),u['slug']
        elif u['mechanism']=='binance_noon_1m_close_tie_split':
            ii = {k[0]:k for k in bars[u['sym']][1]}
            a,b = float(ii[u['S']*1000][4]),float(ii[u['end']*1000][4])
            assert a!=b and u['winner']==(0 if b>a else 1),u['slug']
        rules.append(dict(slug=u['slug'],mechanism=u['mechanism'],metadata_prices='priceToBeat' in em))
    save(OUT/'api_validation.json',dict(trades=checks,rules=rules,missing_metadata_prices=missing,
                                      outcome_count=len(rules),zero_payout_violations=True))
    print('Validated',len(checks),'trade multisets and',len(rules),'outcomes',flush=True)


def source_audit():
    db = Path('/home/taygun/Masaüstü/polymarket/data/db/polymarket_orderbook.db')
    con = sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=5)
    con.execute('PRAGMA query_only=ON')
    subscriptions = con.execute('SELECT asset_id,condition_id,market_title,start_ts,end_ts FROM subscribed_assets').fetchall()
    checked, present = 0, []
    for u in read(OUT/'universe.json'):
        if u['group'] not in PRIMARY:
            continue
        m = read(RAW/'markets'/(u['slug']+'.json'))
        hit = con.execute('SELECT ts_ms FROM market_events WHERE condition_id=? AND ts_ms BETWEEN ? AND ? LIMIT 1',
                          (m['conditionId'],u['S']*1000,u['end']*1000)).fetchone()
        checked += 1
        if hit:
            present.append(dict(slug=u['slug'],event_ms=hit[0]))
    con.close()
    save(RAW/'local_book_audit.json',dict(db=str(db),readonly=True,markets_checked=checked,present=present,
         subscriptions=len(subscriptions),duration_counts=dict(Counter(str(v[4]-v[3]) for v in subscriptions if v[3] and v[4])),
         title_prefixes=sorted({v[2].split(' - ')[0] for v in subscriptions}),
         note='Audit of this local database, not a claim about every possible remote/private archive.'))
    print('Read-only book availability',checked,'markets;',len(present),'with events')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['fetch','analyze','refresh','histories','validate','fresh_interval','source_audit'])
    globals()[parser.parse_args().action]()
