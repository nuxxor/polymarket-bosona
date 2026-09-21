#!/usr/bin/env python3
"""Exploratory, public-data research. Never imports a wallet or submits orders."""
import argparse
import bisect
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import statistics
import zlib

import orjson

import bosona_gec_arastirma as base

OUT = base.ROOT/'data/analysis/bosona_derin_20260921'
TAPE = Path('/home/taygun/Masaüstü/polymarket/data/tape')
SOURCE = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def read(path):
    return orjson.loads(path.read_bytes())


def markets():
    result = {}
    for directory in (base.OUT/'markets', OUT/'markets'):
        for p in directory.glob('btc-updown-5m-*.json'):
            result[int(p.stem.rsplit('-', 1)[1])] = read(p)
    return result


def fetch():
    existing = markets()
    missing = [S for S in range(base.START, base.END, 300) if S not in existing]
    def one(S):
        m = base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{S}')
        assert m['slug'] == f'btc-updown-5m-{S}'
        base.outcome(m)
        base.save(OUT/'markets'/f'{m["slug"]}.json', m)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, _ in enumerate(pool.map(one, missing)):
            if i % 50 == 0:
                print('extra markets', i, '/', len(missing), flush=True)


def book_view(b, target):
    if not b['ready'] or not 0 <= target-b['rcv'] <= 3000 or not 0 <= target-b['obs'] <= 3000:
        return None
    bids, asks = b['BUY'], b['SELL']
    if not bids or not asks:
        return None
    bid, ask = max(bids), min(asks)
    if not 0 < bid < ask <= 1:
        return None
    left, cost, fee = 5., 0., 0.
    for p, q in sorted(asks.items()):
        take = min(left, q)
        cost += take*p
        fee += take*b['rate']*p*(1-p)
        left -= take
        if left <= 1e-8:
            break
    if left > 1e-8:
        cost = fee = None
    return [bid, ask, bids[bid], asks[ask], sum(q for p, q in bids.items() if p >= bid-.03-1e-8),
            sum(q for p, q in asks.items() if p <= ask+.03+1e-8), cost,
            round(fee, 5) if fee is not None else None, b['rcv'], b['obs']]


def extract_file(path_text):
    """Single pass over each old tape; retain causal snapshots, not the giant raw tape."""
    path = Path(path_text)
    cache = OUT/'tape_snapshots'/path.name
    manifest_path = OUT/'tape_snapshots'/f'{path.name}.json'
    if manifest_path.exists():
        return read(manifest_path)
    stamp = datetime.strptime(path.name[5:16], '%Y%m%d_%H').replace(tzinfo=timezone.utc)
    hour = int(stamp.timestamp())
    mm = {S: m for S, m in markets().items() if hour <= S < hour+3600}
    rows = read(base.OUT/'fill_ledger.json')
    targets = {S: set((S+age)*1000+lag for age in range(10, 300) for lag in (0, 250)) for S in mm}
    for r in rows:
        if r['S'] in targets:
            targets[r['S']].update(r['ts']*1000+lag for lag in (-10000, -5000, -1000, 1000, 5000, 10000)
                                    if r['S']*1000 < r['ts']*1000+lag < (r['S']+300)*1000)
    targets = {S: sorted(t) for S, t in targets.items()}
    books, mapping = {}, {}
    for S, m in mm.items():
        tokens = json.loads(m['clobTokenIds'])
        schedule = m.get('feeSchedule', {})
        assert not m.get('feesEnabled') or schedule.get('exponent') == 1
        mapping[m['conditionId']] = S
        books[S] = {t: dict(BUY={}, SELL={}, ready=False, rcv=0, obs=0,
                           rate=float(schedule.get('rate', 0))) for t in tokens}
    indices = Counter()
    stats = Counter()
    output, txs, external = [], [], []
    latest_external = {}
    def flush(S, until, inclusive=False):
        times = targets[S]
        i = indices[S]
        while i < len(times) and (times[i] <= until if inclusive else times[i] < until):
            pair = [book_view(b, times[i]) for b in books[S].values()]
            if all(pair):
                output.append([S, times[i], pair])
            else:
                stats['missing_snapshot'] += 1
            i += 1
        indices[S] = i
    try:
        with gzip.open(path, 'rb') as stream:
            for line in stream:
                d = orjson.loads(line)
                kind, rcv = d.get('k'), d.get('rcv')
                if rcv is None:
                    continue
                p = d.get('p') or {}
                if kind in ('fbt', 'bnb', 'bn'):
                    # Keep one causal quote per second; trades retain all volume observations.
                    second = int(rcv//1000)
                    if kind == 'bn' or latest_external.get(kind) != second:
                        external.append([kind, rcv, d.get('src'), p])
                        latest_external[kind] = second
                    continue
                S = mapping.get(p.get('market'))
                if S is None:
                    continue
                flush(S, rcv)
                obs = int(p.get('timestamp', d.get('src') or rcv))
                if kind == 'pm:last_trade_price':
                    txs.append([S, rcv, obs, p])
                elif kind == 'pm:book' and p.get('asset_id') in books[S]:
                    b = books[S][p['asset_id']]
                    if obs < b['obs'] or rcv < b['rcv']:
                        stats['out_of_order'] += 1
                        continue
                    for side, key in [('BUY', 'bids'), ('SELL', 'asks')]:
                        b[side] = {float(x['price']): float(x['size']) for x in p.get(key, [])
                                   if float(x['size']) > 0}
                    b.update(rcv=rcv, obs=obs, ready=True)
                elif kind == 'pm:price_change':
                    for c in p.get('price_changes', []):
                        b = books[S].get(c.get('asset_id'))
                        if b is None or not b['ready'] or obs < b['obs'] or rcv < b['rcv']:
                            continue
                        px, q = float(c['price']), float(c['size'])
                        if q > 0:
                            b[c['side']][px] = q
                        else:
                            b[c['side']].pop(px, None)
                        b.update(rcv=rcv, obs=obs)
                        if b['BUY'] and b['SELL'] and c.get('best_bid') and c.get('best_ask'):
                            if abs(max(b['BUY'])-float(c['best_bid'])) > 1e-8 or abs(min(b['SELL'])-float(c['best_ask'])) > 1e-8:
                                b['ready'] = False
                                stats['book_mismatch'] += 1
        for S in mm:
            flush(S, (hour+3600)*1000, True)
    except (OSError, EOFError, zlib.error, orjson.JSONDecodeError) as e:
        # No successful-looking prefix from a corrupt source hour.
        stats['corrupt_source'] += 1
        output, txs, external = [], [], []
        stats[type(e).__name__] += 1
    payload = dict(snapshots=output, trades=txs, external=external)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache, 'wb') as stream:
        stream.write(orjson.dumps(payload))
    manifest = dict(file=path.name, source_bytes=path.stat().st_size, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    snapshots=len(output), trades=len(txs), external=len(external), stats=dict(stats), source=SOURCE)
    base.save(manifest_path, manifest)
    return manifest


def extract():
    files = sorted(TAPE.glob('*.gz'))
    with ProcessPoolExecutor(max_workers=3) as pool:
        for i, result in enumerate(pool.map(extract_file, map(str, files))):
            print('tape', i+1, '/', len(files), result['file'], result['snapshots'], result['stats'], flush=True)


def new_books():
    mm = markets()
    grouped = defaultdict(list)
    for r in read(base.OUT/'fill_ledger.json'):
        if 200 < r['age'] < 300:
            grouped[r['S']].append(r)
    con = sqlite3.connect(base.BOOK_DB.as_uri()+'?mode=ro', uri=True)
    available = con.execute('SELECT DISTINCT start_ts FROM subscribed_assets WHERE market_title LIKE ? '
                            'AND start_ts>=? AND start_ts<? AND end_ts-start_ts=300 ORDER BY start_ts',
                            ('%Bitcoin%', base.START, base.END)).fetchall()
    for i, (S,) in enumerate(available):
        if S not in mm:
            continue
        path = OUT/'new_books'/f'{S}.json'
        if path.exists():
            continue
        times = {(S+age)*1000+lag for age in range(180, 300) for lag in (0, 250)}
        for r in grouped[S]:
            times.update(r['ts']*1000+lag for lag in (-10000, -5000, -1000, 1000, 5000, 10000)
                         if (S+150)*1000 < r['ts']*1000+lag < (S+300)*1000)
        base.save(path, base.snapshots(con, mm[S], times))
        if i % 30 == 0:
            print('new books', i+1, '/', len(available), flush=True)
    con.close()


def new_times():
    wanted = {r['tx'] for r in read(base.OUT/'fill_ledger.json') if 200 < r['age'] < 300}
    con = sqlite3.connect(base.BOOK_DB.as_uri()+'?mode=ro', uri=True)
    result = {}
    for rcv, raw in con.execute("SELECT ts_ms,raw_json FROM market_events WHERE event_type='last_trade_price' "
                               'AND ts_ms>=? AND ts_ms<? ORDER BY ts_ms', (base.START*1000, base.END*1000)):
        p = orjson.loads(raw)
        tx = p.get('transaction_hash')
        if tx in wanted and tx not in result:
            result[tx] = dict(rcv=rcv, obs=int(p['timestamp']), **p)
    con.close()
    base.save(OUT/'new_trade_times.json', result)
    print('new matched times', len(result), flush=True)


def recover_one(path_text):
    path = Path(path_text)
    dest = OUT/'recovered_prices'/path.name
    if dest.exists():
        return path.name
    rows = []
    try:
        with gzip.open(path, 'rb') as stream:
            for line in stream:
                if b'"k":"cl"' not in line:
                    continue
                d = orjson.loads(line)
                p = d['p']
                if p.get('w') in (0, 60) and d.get('src') and d.get('rcv'):
                    rows.append([p['w'], d['rcv'], d['src'], p['px']])
    except (OSError, EOFError, zlib.error, orjson.JSONDecodeError):
        rows = []
    dest.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(dest, 'wb') as stream:
        stream.write(orjson.dumps(rows))
    return path.name


def recover_prices():
    with ProcessPoolExecutor(max_workers=2) as pool:
        for i, name in enumerate(pool.map(recover_one, map(str, sorted(TAPE.glob('*.gz'))))):
            if i % 10 == 0:
                print('recovered CL', i+1, name, flush=True)


def deep_prices():
    streams, starts, excluded = base.load_prices()
    records = {name: [(rcv, *value) for rcv, value in zip(times, values)] for name, (times, values) in streams.items()}
    for p in sorted((OUT/'recovered_prices').glob('*.gz')):
        with gzip.open(p, 'rb') as stream:
            for w, rcv, obs, px in orjson.loads(stream.read()):
                if obs <= rcv:
                    records['spot' if w == 0 else 'twap60'].append((rcv, obs, px))
    starts = {}
    for name, seq in records.items():
        ts, values, last = [], [], -1
        for rcv, obs, px in sorted(set(seq)):
            if obs < last:
                continue
            last = obs
            ts.append(rcv)
            values.append((obs, px))
            if name == 'twap60' and obs % 300000 == 0:
                starts.setdefault(obs//1000, (rcv, px))
        streams[name] = ts, values
    # Never mix a different start reference into this market's fair-value calculation.
    for S, m in markets().items():
        reference = next((e.get('eventMetadata', {}).get('priceToBeat') for e in m.get('events', [])
                          if e.get('slug') == m['slug']), None)
        if S in starts and reference is not None and abs(starts[S][1]-float(reference)) > 1e-6:
            del starts[S]
            excluded.append([S, 'reference_mismatch'])
    return streams, starts, excluded


def candles():
    path = OUT/'binance_1m.json'
    if path.exists():
        return read(path)
    result = []
    start = (base.START-3600)*1000
    while start < base.END*1000:
        batch = base.get(f'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&startTime={start}&endTime={base.END*1000-1}&limit=1000')
        assert batch and batch[0][0] == start
        assert all(b[0]-a[0] == 60000 for a, b in zip(batch, batch[1:]))
        result.extend(batch)
        start = batch[-1][0]+60000
    base.save(path, result)
    return result


def candle_features(kk, now):
    # Only fully closed bars, with a fixed additional 2 seconds publication lag.
    i = bisect.bisect_right(kk[0], now-2000)-1
    if i < 20 or now-kk[0][i] > 62000:
        return {}
    a = kk[1][i-20:i+1]
    if a[-1][0]-a[0][0] != 20*60000:
        return {}
    changes = [float(y[4])-float(x[4]) for x, y in zip(a, a[1:])]
    gains = sum(max(0, d) for d in changes[-14:])
    losses = sum(max(0, -d) for d in changes[-14:])
    vols = [float(x[5]) for x in a]
    v5 = sum(vols[-5:])
    close = float(a[-1][4])
    mean = statistics.mean(float(x[4]) for x in a[-20:])
    sd = statistics.pstdev(float(x[4]) for x in a[-20:])
    return dict(rsi14=100*gains/(gains+losses) if gains+losses else 50.,
                volume_ratio=vols[-1]/max(statistics.mean(vols[-20:-1]), 1e-8),
                taker_buy_fraction=sum(float(x[9]) for x in a[-5:])/max(v5, 1e-8),
                volume5=v5, return1=changes[-1]/close*1e4,
                return5=(close-float(a[-6][4]))/close*1e4,
                return15=(close-float(a[-16][4]))/close*1e4,
                bollinger_z=(close-mean)/sd if sd > 0 else 0., bar_close_ms=kk[0][i])


def spot_at(streams, when):
    times, values = streams['spot']
    i = bisect.bisect_right(times, when)-1
    if i < 0 or not 0 <= when-times[i] <= 3000 or not 0 <= when-values[i][0] <= 3000:
        raise ValueError('spot history unavailable')
    return float(values[i][1])


def fair_twap(streams, S, now, sig):
    """Martingale approximation for the final 60s average, not calibrated odds."""
    remaining = S+300-now/1000
    spot, sigma = sig['spot'], sig['sigma']
    if remaining >= 60:
        expected = spot
        variance_time = remaining-40
        known_seconds = 0
    else:
        # Riemann sum of already observable prices in the final averaging window.
        times = list(range((S+240)*1000, int(now)//1000*1000, 1000))
        known = [spot_at(streams, t) for t in times]
        known_seconds = len(known)
        expected = (sum(known)+(60-known_seconds)*spot)/60
        variance_time = remaining**3/(3*60**2)
    sd = sigma*math.sqrt(variance_time)
    z = (expected-sig['ref'])/max(sd, 1e-8)
    drift = (spot-spot_at(streams, now-10000))/10
    exposure = remaining-30 if remaining >= 60 else remaining**2/120
    drift_z = (expected+drift*exposure-sig['ref'])/max(sd, 1e-8)
    return dict(final_mean=expected, final_z=z, final_up_prob=.5*(1+math.erf(z/math.sqrt(2))),
                final_drift_up_prob=.5*(1+math.erf(drift_z/math.sqrt(2))),
                final_known_seconds=known_seconds, final_sd=sd, final_drift_shift=drift*exposure)


def context_features(streams, starts, kk, S, now):
    result = candle_features(kk, now)
    try:
        sig = base.signals(streams, starts, S, now)
        result.update(sig)
        hist = [spot_at(streams, now-i*5000) for i in range(13)]
        result.update(momentum30=(hist[0]-hist[6])/(sig['sigma']*math.sqrt(30)),
                      momentum60=(hist[0]-hist[12])/(sig['sigma']*math.sqrt(60)),
                      spot_twap_gap=(sig['spot']-sig['twap'])/(sig['sigma']*math.sqrt(60)),
                      range60=(max(hist)-min(hist))/(sig['sigma']*math.sqrt(60)))
        result.update(fair_twap(streams, S, now, sig))
    except (KeyError, ValueError):
        pass
    return result


def compact_summary(rows):
    by = defaultdict(float)
    eq = defaultdict(float)
    days = defaultdict(float)
    for r in rows:
        by[r['S']] += r['pnl']
        eq[r['S']] += r['pnl']/r['q'] if r['q'] else 0
        days[datetime.fromtimestamp(r['S'], timezone.utc).strftime('%m-%d')] += r['pnl']
    q = sum(r['q'] for r in rows)
    pnl = sum(by.values())
    return dict(records=len(rows), windows=len(by), shares=q, pnl=pnl,
                edge_cents=100*pnl/q if q else None, equal5_pnl=5*sum(eq.values()),
                excluding_top3=pnl-sum(sorted(by.values(), reverse=True)[:3]),
                equal5_excluding_top3=5*(sum(eq.values())-sum(sorted(eq.values(), reverse=True)[:3])),
                days=dict(days), positive_days=sum(v > 0 for v in days.values()),
                win_share=sum(r['q']*r['win'] for r in rows)/q if q else None,
                average_cost=sum(r['q']*r['cost'] for r in rows)/q if q else None)


def load_snapshots():
    snaps, txs = defaultdict(dict), {}
    wanted = {r['tx'] for r in read(base.OUT/'fill_ledger.json') if 200 < r['age'] < 300}
    coverage = []
    for path in sorted((OUT/'tape_snapshots').glob('*.gz')):
        with gzip.open(path, 'rb') as stream:
            d = orjson.loads(stream.read())
        for S, when, pair in d['snapshots']:
            if when >= (S+180)*1000:
                snaps[S][when] = pair
        for S, rcv, obs, p in d['trades']:
            tx = p.get('transaction_hash')
            if tx in wanted and tx not in txs:
                txs[tx] = dict(S=S, rcv=rcv, obs=obs, **p)
        coverage.append(read(path.with_name(path.name+'.json')))
    # The newer verified snapshots cover 19–20 September, but have no bid depth.
    mm = markets()
    for directory in (base.OUT/'books', base.OUT/'execution_books', OUT/'new_books'):
        for path in directory.glob('*.json'):
            S = int(path.stem)
            m = mm[S]
            for when, pair in read(path).items():
                if not pair:
                    continue
                converted = []
                for b in pair:
                    try:
                        cost, fee = base.ask_cost(b, m)
                    except ValueError:
                        cost = fee = None
                    converted.append([b['bid'], b['ask'], None, b['asks'][0][1], None,
                                      sum(q for p, q in b['asks'] if p <= b['ask']+.03+1e-8),
                                      cost, fee, b['received_ms'], b['observed_ms']])
                snaps[S][int(when)] = converted
    if (OUT/'new_trade_times.json').exists():
        txs.update(read(OUT/'new_trade_times.json'))
    return {S: (sorted(v), v) for S, v in snaps.items()}, txs, coverage


def quote_at(snaps, S, when, max_age=1250):
    # ponytail: actor-aligned quotes use a <=1.25s grid; exact replay is needed for latency claims.
    if S not in snaps:
        return None
    times, values = snaps[S]
    i = bisect.bisect_right(times, when)-1
    if i < 0 or when-times[i] > max_age:
        return None
    pair = values[times[i]]
    if any(not 0 <= when-b[8] <= 3000 or not 0 <= when-b[9] <= 3000 for b in pair):
        return None
    return pair


def book_features(pair, side, previous=None):
    b, other = pair[side], pair[1-side]
    mid = (b[0]+b[1])/2
    r = dict(mid=mid, spread=b[1]-b[0], ask=b[1], bid=b[0],
             ask_depth3=b[5], pair_asks=b[1]+other[1], favorite=mid > (other[0]+other[1])/2)
    if b[2] is not None:
        r.update(bid_depth3=b[4], imbalance=(b[2]-b[3])/max(b[2]+b[3], 1e-8),
                 depth_imbalance=(b[4]-b[5])/max(b[4]+b[5], 1e-8))
    if previous:
        r['mid_change10'] = mid-(previous[side][0]+previous[side][1])/2
    return r


def micro_data():
    quotes = defaultdict(list)
    trades = []
    for path in sorted((OUT/'tape_snapshots').glob('*.gz')):
        with gzip.open(path, 'rb') as stream:
            records = orjson.loads(stream.read())['external']
        for kind, rcv, obs, p in records:
            if kind in ('fbt', 'bnb'):
                if 0 < float(p['b']) < float(p['a']):
                    quotes[kind].append((rcv, float(p['b']), float(p['a']), float(p['B']), float(p['A'])))
            elif kind == 'bn' and obs <= rcv:
                trades.append((rcv, float(p['q']), float(p['q'])*(0 if p['m'] else 1)))
    streams = {name: (sorted(r[0] for r in seq), sorted(seq)) for name, seq in quotes.items()}
    trades.sort()
    times, volume, buys = [], [0.], [0.]
    for rcv, q, buy in trades:
        times.append(rcv)
        volume.append(volume[-1]+q)
        buys.append(buys[-1]+buy)
    return streams, (times, volume, buys)


def micro_features(data, now, sign, chainlink=None):
    quotes, (times, vol, buys) = data
    out = {}
    for name, (tt, values) in quotes.items():
        i, j = bisect.bisect_right(tt, now)-1, bisect.bisect_right(tt, now-10000)-1
        if i < 0 or now-tt[i] > 3000:
            continue
        _, bid, ask, bq, aq = values[i]
        mid = (bid+ask)/2
        out[name+'_imbalance'] = sign*(bq-aq)/max(bq+aq, 1e-8)
        out[name+'_spread_bps'] = (ask-bid)/mid*1e4
        if chainlink:
            out[name+'_basis_bps'] = sign*(mid-chainlink)/chainlink*1e4
        if j >= 0 and now-10000-tt[j] <= 3000:
            before = (values[j][1]+values[j][2])/2
            out[name+'_return10'] = sign*(mid-before)/before*1e4
    i, j, k = [bisect.bisect_right(times, now-seconds*1000) for seconds in (0, 10, 60)]
    if i > j > k and now-times[i-1] <= 3000:
        # Observed trade flow, not a claim of a gap-free exchange-wide tape.
        v10, v60 = vol[i]-vol[j], vol[i]-vol[k]
        if v10 > 0 and v60 > 0:
            fraction = (buys[i]-buys[j])/v10
            out.update(micro_flow10=fraction if sign > 0 else 1-fraction,
                       micro_volume10=v10, micro_volume_spike=6*v10/v60)
    return out


def feature_rows():
    fills = read(base.OUT/'fill_ledger.json')
    streams, starts, excluded = deep_prices()
    ks = candles()
    kk = [r[6] for r in ks], ks
    snaps, txs, coverage = load_snapshots()
    micro = micro_data()
    grouped = defaultdict(list)
    for r in fills:
        grouped[r['S']].append(r)
    result = []
    for S, records in sorted(grouped.items()):
        records.sort(key=lambda r: (r['ts'], r['tx'], r['side']))
        first = records[0]
        prior = []
        for r in records:
            if 200 < r['age'] < 300:
                side = r['side']
                sign = 1 if side == 0 else -1
                now = (r['ts']-5)*1000
                row = dict(S=S, tx=r['tx'], side=side, age=r['age'], q=r['qty'], cost=r['cash_price'],
                           price=r['price'], pnl=r['marginal_cash_pnl'], win=side == r['winner'],
                           kind=r['opening_kind'], completion_qty=r['completion_qty'],
                           ordering_ambiguous=r['ordering_ambiguous'], now=now,
                           inventory=abs(r['pre_net']), first_age=first['age'],
                           first_price=first['price'], same_as_first=side == first['side'],
                           prior_count=len(prior), prior_same_count=sum(x['side'] == side for x in prior),
                           seconds_since_fill=r['ts']-prior[-1]['ts'] if prior else None,
                           size_to_inventory=r['qty']/abs(r['pre_net']) if abs(r['pre_net']) > 1e-8 else None,
                           below_basis=r['cash_price'] < r['pre_unmatched_cash_cost']/abs(r['pre_net']) if abs(r['pre_net']) > 1e-8 else None,
                           basis_gap=r['cash_price']-r['pre_unmatched_cash_cost']/abs(r['pre_net']) if abs(r['pre_net']) > 1e-8 else None,
                           prior_volume10=sum(x['qty'] for x in prior if x['ts'] >= r['ts']-10),
                           utc_hour=(S%86400)/3600)
                pre_qty = [sum(x['qty'] for x in prior if x['side'] == s) for s in (0, 1)]
                pre_cost = sum(x['qty']*x['cash_price'] for x in prior)
                row['pre_floor'] = min(pre_qty)-pre_cost
                pre_qty[side] += r['qty']
                row['post_floor'] = min(pre_qty)-pre_cost-r['qty']*r['cash_price']
                row.update(context_features(streams, starts, kk, S, now))
                row.update(micro_features(micro, now, sign, row.get('spot')))
                for name in ['spot_z', 'twap_z', 'momentum', 'momentum30', 'momentum60',
                             'spot_twap_gap', 'return1', 'return5', 'return15', 'bollinger_z']:
                    if name in row:
                        row['own_'+name] = sign*row[name]
                row['own_rsi'] = row['rsi14'] if side == 0 else 100-row['rsi14']
                row['own_taker_flow'] = row['taker_buy_fraction'] if side == 0 else 1-row['taker_buy_fraction']
                if 'final_up_prob' in row:
                    row['fair_prob'] = row['final_up_prob'] if side == 0 else 1-row['final_up_prob']
                    row['fair_edge_paid'] = row['fair_prob']-row['cost']
                    row['fair_drift_prob'] = row['final_drift_up_prob'] if side == 0 else 1-row['final_drift_up_prob']
                    row['fair_drift_edge_paid'] = row['fair_drift_prob']-row['cost']
                pair = quote_at(snaps, S, now)
                if pair:
                    row.update(book_features(pair, side, quote_at(snaps, S, now-10000)))
                    row['paid_minus_mid'] = row['cost']-row['mid']
                    if 'fair_prob' in row:
                        row['fair_edge_ask'] = row['fair_prob']-pair[side][1]-.07*pair[side][1]*(1-pair[side][1])
                        if all(b[6] is not None for b in pair):
                            own_edge = row['fair_drift_prob']-(pair[side][6]+pair[side][7])/5
                            other_edge = 1-row['fair_drift_prob']-(pair[1-side][6]+pair[1-side][7])/5
                            row['fair_drift_edge_ask'] = own_edge
                            row['drift_choice_is_actor'] = own_edge >= .03 and own_edge >= other_edge
                if r['tx'] in txs:
                    row['exchange_age'] = (txs[r['tx']]['obs']-S*1000)/1000
                    row['public_delay_s'] = r['ts']-txs[r['tx']]['obs']/1000
                # Future quotes are labels only. They never enter context_features.
                row['markouts'] = {}
                for seconds in (1, 5, 10):
                    later = quote_at(snaps, S, r['ts']*1000+seconds*1000)
                    if later:
                        row['markouts'][str(seconds)] = (later[side][0]+later[side][1])/2-row['cost']
                result.append(row)
            prior.append(r)
    base.save(OUT/'features.json', result)
    base.save(OUT/'coverage.json', dict(tape=coverage, price_excluded=excluded,
              late_rows=len(result), book_rows=sum('mid' in r for r in result),
              fair_rows=sum('fair_prob' in r for r in result), matched_times=sum('exchange_age' in r for r in result)))
    return result


def screen():
    rows = feature_rows()
    adds = [r for r in rows if r['kind'] == 'add']
    end = base.START+5*86400
    features = ['age', 'price', 'q', 'inventory', 'first_age', 'first_price', 'same_as_first',
                'prior_count', 'prior_same_count', 'seconds_since_fill', 'size_to_inventory',
                'below_basis', 'basis_gap', 'prior_volume10', 'utc_hour', 'own_spot_z', 'own_twap_z',
                'own_momentum', 'own_momentum30', 'own_momentum60', 'own_spot_twap_gap',
                'sigma', 'range60', 'own_rsi', 'volume_ratio', 'volume5', 'own_taker_flow',
                'own_return1', 'own_return5', 'own_return15', 'own_bollinger_z',
                'fair_prob', 'fair_edge_paid', 'fair_drift_prob', 'fair_drift_edge_paid',
                'fair_edge_ask', 'fair_drift_edge_ask', 'drift_choice_is_actor',
                'pre_floor', 'post_floor', 'spread', 'ask_depth3', 'bid_depth3',
                'pair_asks', 'favorite', 'imbalance', 'depth_imbalance', 'mid_change10', 'paid_minus_mid',
                'fbt_imbalance', 'fbt_spread_bps', 'fbt_basis_bps', 'fbt_return10',
                'bnb_imbalance', 'bnb_spread_bps', 'bnb_basis_bps', 'bnb_return10',
                'micro_flow10', 'micro_volume10', 'micro_volume_spike']
    report = dict(all_adds=compact_summary(adds), scan={})
    for feature in features:
        discovery = sorted(float(r[feature]) for r in adds if r['S'] < end and r.get(feature) is not None)
        if not discovery:
            continue
        cuts = sorted(set(discovery[min(len(discovery)-1, int(len(discovery)*q))] for q in (.25, .5, .75)))
        bins = defaultdict(list)
        for r in adds:
            if r.get(feature) is not None:
                bins[bisect.bisect_right(cuts, float(r[feature]))].append(r)
        report['scan'][feature] = dict(cuts=cuts, covered=sum(map(len, bins.values())), bins={str(k): {
            'discovery': compact_summary([r for r in v if r['S'] < end]),
            'later': compact_summary([r for r in v if r['S'] >= end]),
            'all': compact_summary(v)} for k, v in bins.items()})
    report['late20_by_kind'] = {kind: compact_summary([r for r in rows if r['age'] >= 280 and r['kind'] == kind])
                                for kind in ('first', 'add', 'reopen', None)}
    report['time_sensitivity'] = {str(t): compact_summary([r for r in adds if r['age'] >= t]) for t in (270, 275, 280, 285, 290)}
    report['exchange_late20'] = compact_summary([r for r in adds if r.get('exchange_age', 0) >= 280])
    report['source'] = SOURCE
    base.save(OUT/'screen.json', report)
    print('screen', len(adds), 'adds;', len(features), 'metrics;', report['late20_by_kind']['add'], flush=True)


def policy():
    snaps, _, _ = load_snapshots()
    streams, starts, _ = deep_prices()
    ks = candles()
    kk = [r[6] for r in ks], ks
    mm = markets()
    calibration = read(OUT/'forecast.json') if (OUT/'forecast.json').exists() else None
    result, coverage = [], Counter()
    for S in sorted(mm):
        winner = base.outcome(mm[S])
        for age in (210, 240, 270, 280, 290):
            now = (S+age)*1000
            pair, execution = quote_at(snaps, S, now, 0), quote_at(snaps, S, now+250, 0)
            if not pair or not execution or any(b[6] is None for b in execution):
                coverage['book_missing'] += 1
                continue
            f = context_features(streams, starts, kk, S, now)
            if 'final_up_prob' not in f or 'rsi14' not in f:
                coverage['features_missing'] += 1
                continue
            coverage['eligible'] += 1
            mids = [(b[0]+b[1])/2 for b in pair]
            fav = 0 if mids[0] > mids[1] else 1
            baseline_prob = .5*(1+math.erf(f['spot_z']/math.sqrt(2)))
            previous = quote_at(snaps, S, now-10000)
            policies = dict(favorite=fav, twap_value=None, twap_drift_value=None, twap_fitted_value=None, twap_empirical_value=None,
                            spot_value=None, rebound=None, rebound_divergence=None)
            details = {}
            probs = [('twap_value', f['final_up_prob']), ('twap_drift_value', f['final_drift_up_prob']), ('spot_value', baseline_prob)]
            if calibration:
                fit = calibration[str(age)]
                scale = fit['discovery']['scores']['fitted_on_discovery']['normalized_rmse']
                z = (f['final_mean']+fit['momentum_coefficient']*f['final_drift_shift']-f['ref'])/(f['final_sd']*scale)
                probs.append(('twap_fitted_value', .5*(1+math.erf(z/math.sqrt(2)))))
                if 'training_residuals' in fit:
                    residuals = fit['training_residuals']
                    threshold = (f['ref']-f['final_mean']-fit['momentum_coefficient']*f['final_drift_shift'])/f['final_sd']
                    prob = (len(residuals)-bisect.bisect_left(residuals, threshold)+.5)/(len(residuals)+1)
                    probs.append(('twap_empirical_value', prob))
            for name, prob in probs:
                edges = [(prob if side == 0 else 1-prob)-(pair[side][6]+pair[side][7])/5 for side in (0, 1)]
                best = 0 if edges[0] > edges[1] else 1
                policies[name] = best if edges[best] >= .03 else None
                details[name] = edges[best]
            cheap = 0 if mids[0] < mids[1] else 1
            sign = 1 if cheap == 0 else -1
            own_rsi = f['rsi14'] if cheap == 0 else 100-f['rsi14']
            rebound = sign*f['momentum'] > 0 and own_rsi < 40 and pair[cheap][1] < .5
            policies['rebound'] = cheap if rebound else None
            divergence = previous is not None and mids[cheap] <= (previous[cheap][0]+previous[cheap][1])/2
            policies['rebound_divergence'] = cheap if rebound and divergence else None
            for name, side in policies.items():
                cost = execution[side][6]+execution[side][7] if side is not None else 0.
                win = side == winner if side is not None else False
                result.append(dict(S=S, age=age, rule=name, side=side, selected=side is not None,
                       q=5. if side is not None else 0., pnl=5*win-cost, win=win, cost=cost/5,
                       signal=f, decision_ms=now, execution_ms=now+250, edge=details.get(name)))
    report = dict(coverage=dict(coverage), rules={}, source=SOURCE,
        caveat='Exploratory comparison after seeing the same days. Three cent edge is fixed, not optimized. '
               'Models are uncalibrated; post-outcome fill selection is absent. No simulated maker fills. '
               'Every eligible no-signal window counts as zero; each age is a separate paper strategy.')
    end = base.START+5*86400
    for age in (210, 240, 270, 280, 290):
        for rule in ('favorite', 'twap_value', 'twap_drift_value', 'twap_fitted_value', 'twap_empirical_value', 'spot_value', 'rebound', 'rebound_divergence'):
            rr = [r for r in result if r['age'] == age and r['rule'] == rule]
            report['rules'][f'{age}_{rule}'] = dict(selected=sum(r['selected'] for r in rr),
                all=compact_summary(rr), discovery=compact_summary([r for r in rr if r['S'] < end]),
                later=compact_summary([r for r in rr if r['S'] >= end]))
    base.save(OUT/'policy_rows.json', result)
    base.save(OUT/'policy.json', report)
    print(json.dumps(report, indent=2), flush=True)


def mechanism():
    rows = read(OUT/'features.json')
    adds = [r for r in rows if r['kind'] == 'add']
    snaps, _, _ = load_snapshots()
    mm = markets()
    result = dict(conditions={}, markouts={}, delayed_quote={}, source=SOURCE)
    late = [r for r in adds if r['age'] >= 280]
    conditions = dict(all=lambda r: True,
        unambiguous=lambda r: not r['ordering_ambiguous'],
        price_below_30c=lambda r: r['price'] < .3,
        price_above_50c=lambda r: r['price'] >= .5,
        favorite=lambda r: r.get('favorite') is True,
        underdog=lambda r: r.get('favorite') is False,
        pre_floor_positive=lambda r: r['pre_floor'] >= 0,
        pre_floor_negative=lambda r: r['pre_floor'] < 0,
        spot_support=lambda r: r.get('own_spot_z', 0) > 0,
        spot_against=lambda r: r.get('own_spot_z', 0) < 0,
        twap_lags_spot=lambda r: r.get('own_twap_z', 0) < 0 < r.get('own_spot_z', 0),
        rebound=lambda r: r.get('own_momentum', 0) > 0 and r.get('own_rsi', 100) < 40,
        fair_edge=lambda r: r.get('fair_edge_paid', 0) >= .03,
        fair_drift_edge=lambda r: r.get('fair_drift_edge_paid', 0) >= .03)
    end = base.START+5*86400
    for name, fn in conditions.items():
        rr = [r for r in late if fn(r)]
        result['conditions'][name] = dict(all=compact_summary(rr),
             discovery=compact_summary([r for r in rr if r['S'] < end]),
             later=compact_summary([r for r in rr if r['S'] >= end]))
    for label, rr in [('all_adds', adds), ('late20', late)]:
        result['markouts'][label] = {}
        for seconds in ('1', '5', '10'):
            available = [r for r in rr if seconds in r['markouts']]
            q = sum(r['q'] for r in available)
            result['markouts'][label][seconds] = dict(records=len(available), windows=len({r['S'] for r in available}),
                cents_per_share=100*sum(r['q']*r['markouts'][seconds] for r in available)/q if q else None)
        for delay in (1, 5, 10):
            actual, quoted = [], []
            for r in rr:
                when = (r['S']+r['age']+delay)*1000
                if when >= (r['S']+300)*1000:
                    continue
                pair = quote_at(snaps, r['S'], when, 0)
                if not pair or pair[r['side']][6] is None:
                    continue
                b = pair[r['side']]
                cost = b[6]+b[7]
                actual.append({**r, 'q': 5., 'pnl': 5*(r['win']-r['cost'])})
                quoted.append({**r, 'q': 5., 'cost': cost/5, 'pnl': 5*r['win']-cost})
            result['delayed_quote'][f'{label}_{delay}'] = dict(actor_same_rows=compact_summary(actual),
                delayed=compact_summary(quoted))
    actual_clock = [r for r in adds if r.get('exchange_age', 0) >= 280]
    result['exchange_late20'] = compact_summary(actual_clock)
    result['public_late20_with_exchange_time'] = compact_summary([r for r in late if 'exchange_age' in r])
    result['delay_quantiles'] = [statistics.quantiles([r['public_delay_s'] for r in adds if 'public_delay_s' in r], n=10)[i]
                                 for i in (0, 4, 8)]
    # Equal market-weight removes the dependence on the number of split activity records.
    by = defaultdict(list)
    for r in late:
        by[r['S']].append(r)
    equal_market = []
    for S, rr in by.items():
        qty = sum(r['q'] for r in rr)
        cost = sum(r['q']*r['cost'] for r in rr)/qty
        pnl = 5*sum(r['pnl'] for r in rr)/qty
        equal_market.append(dict(S=S, q=5., pnl=pnl, cost=cost,
                                 win=sum(r['q']*r['win'] for r in rr)/qty))
    result['late20_equal_market'] = compact_summary(equal_market)
    fields = ['S', 'side', 'age', 'exchange_age', 'q', 'cost', 'pnl', 'win', 'inventory', 'pre_floor',
              'favorite', 'mid', 'spread', 'own_spot_z', 'own_twap_z', 'own_momentum', 'own_rsi',
              'fair_prob', 'fair_drift_prob', 'markouts', 'first_age', 'first_price']
    ordered = sorted(late, key=lambda r: r['pnl'])
    result['examples'] = [{**{k: r.get(k) for k in fields}, 'url': f'https://polymarket.com/event/{mm[r["S"]]["slug"]}'}
                          for r in ordered[:6]+ordered[-6:]]
    base.save(OUT/'mechanism.json', result)
    print('mechanism', result['exchange_late20'], flush=True)


def forecast():
    """Check the proposed mechanism against final oracle prices, without selecting actor fills."""
    streams, starts, _ = deep_prices()
    rows = []
    for S, m in sorted(markets().items()):
        meta = next((e.get('eventMetadata', {}) for e in m.get('events', []) if e['slug'] == m['slug']), {})
        if meta.get('finalPrice') is None:
            continue
        for age in (210, 240, 270, 280, 290):
            try:
                sig = base.signals(streams, starts, S, (S+age)*1000)
                f = fair_twap(streams, S, (S+age)*1000, sig)
            except (KeyError, ValueError):
                continue
            rows.append(dict(S=S, age=age, final=meta['finalPrice'], ref=sig['ref'], **f))
    report = {}
    split = base.START+5*86400
    for age in (210, 240, 270, 280, 290):
        rr = [r for r in rows if r['age'] == age]
        train = [r for r in rr if r['S'] < split]
        xs = [r['final_drift_shift']/r['final_sd'] for r in train]
        ys = [(r['final']-r['final_mean'])/r['final_sd'] for r in train]
        coefficient = sum(x*y for x, y in zip(xs, ys))/sum(x*x for x in xs)
        subsets = {}
        for label, subset in [('discovery', train), ('later', [r for r in rr if r['S'] >= split])]:
            scores = {}
            for name, coef in [('static', 0.), ('full_drift', 1.), ('fitted_on_discovery', coefficient)]:
                errors = [r['final_mean']+coef*r['final_drift_shift']-r['final'] for r in subset]
                normalized = [e/r['final_sd'] for e, r in zip(errors, subset)]
                predictions = [r['final_mean']+coef*r['final_drift_shift'] >= r['ref'] for r in subset]
                scores[name] = dict(rmse_usd=math.sqrt(statistics.mean(e*e for e in errors)),
                      normalized_rmse=math.sqrt(statistics.mean(e*e for e in normalized)),
                      direction_accuracy=statistics.mean(p == (r['final'] >= r['ref']) for p, r in zip(predictions, subset)))
            subsets[label] = dict(windows=len(subset), scores=scores)
        report[str(age)] = dict(momentum_coefficient=coefficient,
                               training_residuals=sorted(y-coefficient*x for x, y in zip(xs, ys)), **subsets)
    base.save(OUT/'forecast_rows.json', rows)
    base.save(OUT/'forecast.json', report)
    print(json.dumps(report, indent=2), flush=True)


def verify_quotes():
    """Independent L1 check: compare replayed levels to the tape's reported best quotes."""
    mm, checked = markets(), []
    for name in ('tape_20260913_15.jsonl.gz', 'tape_20260916_10.jsonl.gz', 'tape_20260918_00.jsonl.gz'):
        with gzip.open(OUT/'tape_snapshots'/name, 'rb') as f:
            samples = [r for r in orjson.loads(f.read())['snapshots'] if r[1]-r[0]*1000 in (240000, 280000)]
        samples.sort(key=lambda r: r[1])
        latest, cursor = {}, 0
        with gzip.open(TAPE/name, 'rb') as stream:
            for line in stream:
                d = orjson.loads(line)
                rcv = d.get('rcv')
                if rcv is None:
                    continue
                while cursor < len(samples) and samples[cursor][1] < rcv:
                    S, when, pair = samples[cursor]
                    for token, b in zip(json.loads(mm[S]['clobTokenIds']), pair):
                        expected = latest[token]
                        assert expected[0] <= when and abs(expected[2]-b[0]) < 1e-8 and abs(expected[3]-b[1]) < 1e-8, (name, S, when, b, expected)
                    checked.append([name, S, when])
                    cursor += 1
                if cursor == len(samples):
                    break
                p = d.get('p') or {}
                obs = int(p.get('timestamp', d.get('src') or rcv))
                if d.get('k') == 'pm:book':
                    bids = [float(x['price']) for x in p.get('bids', []) if float(x['size']) > 0]
                    asks = [float(x['price']) for x in p.get('asks', []) if float(x['size']) > 0]
                    token = p['asset_id']
                    if bids and asks and obs >= latest.get(token, (0, 0))[1]:
                        latest[token] = (rcv, obs, max(bids), min(asks))
                elif d.get('k') == 'pm:price_change':
                    for c in p.get('price_changes', []):
                        token = c['asset_id']
                        if c.get('best_bid') is not None and c.get('best_ask') is not None and obs >= latest.get(token, (0, 0))[1]:
                            latest[token] = (rcv, obs, float(c['best_bid']), float(c['best_ask']))
        assert cursor == len(samples) and samples
    base.save(OUT/'quote_validation.json', dict(checked=len(checked), samples=checked, passed=True))
    print('independent quote checks passed', len(checked), flush=True)


def check():
    b = dict(BUY={.49: 10.}, SELL={.51: 10.}, ready=True, rcv=1000, obs=999, rate=.07)
    v = book_view(b, 1100)
    assert abs(v[6]-2.55) < 1e-9 and v[7] == .08747
    assert book_view(b, 4100) is None and book_view(b, 900) is None
    b['SELL'] = {.51: 2.}
    assert book_view(b, 1100)[6] is None
    seq = [(t*1000, 100+t/1000) for t in range(400)]
    streams = {'spot': ([x[0] for x in seq], seq)}
    sig = dict(spot=100.285, sigma=.1, ref=100.27)
    before = fair_twap(streams, 0, 285000, sig)
    streams['spot'][0].append(500000)
    streams['spot'][1].append((500000, 1000000))
    assert fair_twap(streams, 0, 285000, sig) == before
    assert before['final_known_seconds'] == 45
    assert before['final_drift_up_prob'] > before['final_up_prob']
    bars = [[i*60000, '100', '101', '99', str(100+i), '2', i*60000+59999,
             '200', 3, '1', '100', '0'] for i in range(25)]
    kk = [r[6] for r in bars], bars
    f = candle_features(kk, 24*60000+1000)
    assert f['bar_close_ms'] == 23*60000-1  # last just-closed bar is still inside publication delay
    sample = [dict(S=0, q=5, pnl=1, cost=.8, win=True), dict(S=300, q=5, pnl=-2, cost=.4, win=False)]
    assert compact_summary(sample)['pnl'] == -1
    print('deep checks passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['fetch', 'extract', 'new_books', 'new_times', 'recover_prices', 'check', 'screen', 'policy', 'mechanism', 'forecast', 'verify_quotes'])
    args = parser.parse_args()
    globals()[args.action]()
