#!/usr/bin/env python3
"""Bosona BTC5m: public, replayable research. No wallet keys or order submission."""
import argparse
import bisect
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import sqlite3
import time
import urllib.parse
import urllib.request
import zlib

from muhasebe import totals

SOURCE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/analysis/bosona_gec_20260921'
WALLET = '0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
BOOK_DB = Path('/home/taygun/Masaüstü/polymarket/data/db/polymarket_orderbook.db')
START = int(datetime(2026, 9, 13, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 9, 20, 22, 30, tzinfo=timezone.utc).timestamp())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')))
    temp.replace(path)


def get(url, timeout=20, attempts=3):
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (OSError, ValueError):
            if attempt == attempts-1:
                raise
            time.sleep(attempt + 1)


def activity_key(r):
    return tuple(str(r.get(k, '')) for k in ('transactionHash', 'timestamp', 'type',
                 'asset', 'outcomeIndex', 'side', 'size', 'price', 'usdcSize'))


def fetch():
    """Disjoint time slices; a failed/truncated slice never becomes an empty slice."""
    def chunk(start):
        path = OUT / 'activity' / f'{start}.json'
        end = min(start + 21600 - 1, END - 1)
        if path.exists():
            return json.loads(path.read_text())
        rows = []
        for offset in range(0, 5001, 500):
            query = dict(user=WALLET, start=start, end=end, limit=500, offset=offset,
                         sortBy='TIMESTAMP', sortDirection='ASC')
            batch = get('https://data-api.polymarket.com/activity?' + urllib.parse.urlencode(query))
            if not isinstance(batch, list):
                raise ValueError('activity response is not a list')
            for row in batch:
                assert row['proxyWallet'].lower() == WALLET
                assert start <= row['timestamp'] <= end
            rows.extend(batch)
            if len(batch) < 500:
                result = dict(start=start, end=end, rows=rows, pages=offset // 500 + 1,
                              fetched_ms=round(time.time()*1000), complete=True)
                save(path, result)
                return result
            time.sleep(.2)
        raise ValueError(f'activity pagination exhausted: {start}')
    all_rows = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i, part in enumerate(pool.map(chunk, range(START-86400, END, 21600))):
            all_rows.extend(part['rows'])
            if i % 8 == 0:
                print('activity slices', i+1, 'rows', len(all_rows), flush=True)
    unique = {activity_key(r): r for r in all_rows}
    rows = [r for r in unique.values() if r.get('slug', '').startswith('btc-updown-5m-')
            and START <= int(r['slug'].rsplit('-', 1)[1]) < END]
    save(OUT/'activity.json', rows)
    slugs = sorted({r['slug'] for r in rows if r['type'] == 'TRADE'})
    def market(slug):
        path = OUT/'markets'/f'{slug}.json'
        if path.exists():
            return json.loads(path.read_text())
        m = get('https://gamma-api.polymarket.com/markets/slug/' + slug)
        assert m['slug'] == slug
        save(path, m)
        time.sleep(.15)
        return m
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, _ in enumerate(pool.map(market, slugs)):
            if i % 100 == 0:
                print('markets', i+1, '/', len(slugs), flush=True)
    save(OUT/'fetch_manifest.json', dict(start=START, end=END, raw_rows=len(all_rows),
         unique_rows=len(unique), btc_rows=len(rows), markets=len(slugs), skipped_slices=0))


def outcome(m):
    names = json.loads(m['outcomes'])
    prices = list(map(float, json.loads(m['outcomePrices'])))
    if not m.get('closed') or sorted(prices) != [0., 1.] or names != ['Up', 'Down']:
        raise ValueError('unresolved or unexpected outcomes')
    return prices.index(1.)


def ledger(trades, winner):
    """Causal FIFO pairing. Attribution is accounting, never a causal profit claim."""
    trades = sorted(trades, key=lambda r: (r['timestamp'], r['transactionHash'], r['outcomeIndex']))
    lots = [deque(), deque()]
    rows = []
    ever_opened = False
    pair_pnl = pair_cash_pnl = 0.
    for r in trades:
        if r['side'] != 'BUY':
            raise ValueError('SELL requires separate inventory accounting')
        q, p, side = float(r['size']), float(r['price']), int(r['outcomeIndex'])
        if not math.isfinite(q) or q <= 0 or not math.isfinite(p) or not 0 <= p <= 1 or side not in (0, 1):
            raise ValueError('invalid quantity/price/outcome')
        cash_price = float(r['usdcSize']) / q
        if not math.isfinite(cash_price) or cash_price < 0:
            raise ValueError('invalid cash cost')
        other = 1-side
        pre_net = sum(a[0] for a in lots[0]) - sum(a[0] for a in lots[1])
        pre_cash = sum(a[0]*a[2] for side_lots in lots for a in side_lots)
        remaining = q
        paired = 0.
        pair_change = pair_cash_change = 0.
        while remaining > 1e-8 and lots[other]:
            lot = lots[other][0]
            take = min(remaining, lot[0])
            pair_change += take*(1-p-lot[1])
            pair_cash_change += take*(1-cash_price-lot[2])
            lot[0] -= take
            remaining -= take
            paired += take
            if lot[0] < 1e-8:
                lots[other].popleft()
        if remaining > 1e-8:
            label = 'first' if not ever_opened else ('add' if side == (0 if pre_net > 0 else 1)
                     and abs(pre_net) > 1e-8 else 'reopen')
            lots[side].append([remaining, p, cash_price])
            ever_opened = True
        else:
            label = None
        S = int(r['slug'].rsplit('-', 1)[1])
        row = dict(S=S, ts=r['timestamp'], tx=r['transactionHash'], side=side, qty=q, price=p,
                   cash_price=cash_price, age=r['timestamp']-S, pre_net=pre_net,
                   pre_unmatched_cash_cost=pre_cash,
                   completion_qty=paired, opening_qty=max(0., remaining), opening_kind=label,
                   pair_pnl=pair_change, pair_cash_pnl=pair_cash_change,
                   marginal_pnl=q*((side == winner)-p),
                   marginal_cash_pnl=q*(side == winner)-float(r['usdcSize']))
        pair_pnl += pair_change
        pair_cash_pnl += pair_cash_change
        rows.append(row)
    residual = sum(lot[0]*((side == winner)-lot[1]) for side in (0, 1) for lot in lots[side])
    residual_cash = sum(lot[0]*((side == winner)-lot[2]) for side in (0, 1) for lot in lots[side])
    independent = totals(trades, winner)
    assert abs(pair_pnl+residual-independent['pnl']) < 1e-5
    assert abs(sum(r['marginal_pnl'] for r in rows)-independent['pnl']) < 1e-5
    assert abs(sum(r['marginal_cash_pnl'] for r in rows)-pair_cash_pnl-residual_cash) < 1e-5
    return rows, dict(gross_pnl=independent['pnl'], cash_cost_pnl=pair_cash_pnl+residual_cash,
                     pair_pnl=pair_pnl, residual_pnl=residual,
                     pair_cash_pnl=pair_cash_pnl, residual_cash_pnl=residual_cash)


def load_prices():
    records = defaultdict(list)
    excluded = []
    price_root = OUT/'price_snapshot' if (OUT/'price_files_manifest.json').exists() else ROOT/'data/tape_cl_direct'
    for p in sorted(price_root.glob('cld_202609*.gz')):
        try:
            with gzip.open(p, 'rt') as stream:
                part = [json.loads(line) for line in stream]
        except (OSError, ValueError, EOFError, zlib.error) as ex:
            excluded.append([p.name, type(ex).__name__])
            continue
        for r in part:
            if r['f'] in ('spot', 'twap60'):
                records[r['f']].append((r['rcv'], r['obs']*1000, r['px']))
    streams = {}
    starts = {}
    for name, seq in records.items():
        times, values = [], []
        last_obs = -1
        for rcv, obs, px in sorted(set(seq)):
            if obs < last_obs or obs > rcv:
                continue
            last_obs = obs
            times.append(rcv)
            values.append((obs, px))
            if name == 'twap60' and obs % 300000 == 0:
                starts.setdefault(obs//1000, (rcv, px))
        streams[name] = times, values
    return streams, starts, excluded


def signals(streams, starts, S, now_ms):
    rcv, ref = starts[S]
    ref = float(ref)
    if not math.isfinite(ref) or ref <= 0:
        raise ValueError('invalid reference')
    if rcv > now_ms or not 0 < now_ms-S*1000 < 300000:
        raise ValueError('reference/time unavailable')
    def at(name, when):
        times, values = streams[name]
        i = bisect.bisect_right(times, when)-1
        if i < 0:
            raise ValueError('missing history')
        obs, price = values[i]
        if not 0 <= when-times[i] <= 3000 or not 0 <= when-obs <= 3000:
            raise ValueError('stale price')
        price = float(price)
        if not math.isfinite(price) or price <= 0:
            raise ValueError('invalid price')
        return price
    spot, twap = at('spot', now_ms), at('twap60', now_ms)
    history = [at('spot', now_ms-i*5000) for i in range(13)]
    sigma = math.sqrt(sum((a-b)**2 for a, b in zip(history, history[1:]))/60)
    if sigma < 1e-8:
        raise ValueError('zero volatility')
    scale = sigma*math.sqrt(S+300-now_ms/1000)
    return dict(ref=ref, reference_received_ms=rcv, spot=spot, twap=twap, sigma=sigma,
                spot_z=(spot-ref)/scale, twap_z=(twap-ref)/scale,
                momentum=(spot-history[2])/(sigma*math.sqrt(10)), decision_ms=now_ms)


def summary(rows, field='marginal_cash_pnl'):
    by_window = defaultdict(float)
    for r in rows:
        by_window[r['S']] += r[field]
    values = list(by_window.values())
    total = sum(values)
    top = sorted(values, reverse=True)
    rng = random.Random(20260921)
    boot = sorted(sum(rng.choices(values, k=len(values))) for _ in range(2000)) if values else []
    days = defaultdict(float)
    for S, pnl in by_window.items():
        days[datetime.fromtimestamp(S, timezone.utc).strftime('%Y-%m-%d')] += pnl
    day_values = list(days.values())
    day_boot = sorted(sum(rng.choices(day_values, k=len(day_values))) for _ in range(2000)) if day_values else []
    return dict(records=len(rows), windows=len(values), shares=sum(r.get('qty', 0) for r in rows),
                pnl=total, positive_windows=sum(v > 1e-8 for v in values), days=dict(days),
                excluding_top3=total-sum(top[:3]), top1=top[0] if top else None,
                day_bootstrap_ci95=[day_boot[50], day_boot[1949]] if day_boot else None,
                window_bootstrap_ci95=[boot[50], boot[1949]] if boot else None)


def snapshots(con, m, times):
    """Replay both assets, including the second asset in batched price_change events."""
    tokens = json.loads(m['clobTokenIds'])
    S = int(m['slug'].rsplit('-', 1)[1])
    books = {t: {'BUY': {}, 'SELL': {}, 'rcv': 0, 'obs': 0, 'initialized': False} for t in tokens}
    # Start with the last complete book for each asset, then replay incremental changes.
    latest_full = [con.execute("SELECT ts_ms FROM market_events WHERE asset_id=? AND event_type='book' "
                  'AND ts_ms BETWEEN ? AND ? ORDER BY ts_ms DESC LIMIT 1',
                  (token, (S-1800)*1000, min(times))).fetchone() for token in tokens]
    begin = min(row[0] for row in latest_full) if all(latest_full) else (S-1800)*1000
    cursor = iter(con.execute('SELECT ts_ms,raw_json FROM market_events WHERE condition_id=? '
                             'AND ts_ms BETWEEN ? AND ? ORDER BY ts_ms,id',
                             (m['conditionId'], begin, max(times))))
    pending = next(cursor, None)
    result = {}
    for target in sorted(set(times)):
        while pending and pending[0] <= target:
            rcv, raw = pending
            d = json.loads(raw)
            obs = int(d.get('timestamp', rcv))
            kind = d.get('event_type')
            if kind == 'book' and d.get('asset_id') in books:
                b = books[d['asset_id']]
                if obs >= b['obs']:
                    for side, key in [('BUY', 'bids'), ('SELL', 'asks')]:
                        b[side] = {float(x['price']): float(x['size']) for x in d.get(key, []) if float(x['size']) > 0}
                    b.update(rcv=rcv, obs=obs, initialized=True)
            elif kind == 'price_change':
                for change in d.get('price_changes', []):
                    b = books.get(change.get('asset_id'))
                    if b is None or not b['initialized'] or obs < b['obs']:
                        continue
                    p, q = float(change['price']), float(change['size'])
                    side = change['side']
                    if q > 0:
                        b[side][p] = q
                    else:
                        b[side].pop(p, None)
                    b.update(rcv=rcv, obs=obs)
            pending = next(cursor, None)
        pair = []
        for token in tokens:
            b = books[token]
            if not b['initialized'] or not 0 <= target-b['rcv'] <= 3000 or not 0 <= target-b['obs'] <= 3000:
                pair = []
                break
            bids, asks = b['BUY'], b['SELL']
            if not bids or not asks or not 0 < max(bids) < min(asks) <= 1:
                pair = []
                break
            pair.append(dict(bid=max(bids), ask=min(asks), asks=sorted(asks.items()),
                             received_ms=b['rcv'], observed_ms=b['obs']))
        result[target] = pair or None
    return result


def rules(signal, books):
    mids = [(b['bid']+b['ask'])/2 for b in books]
    if abs(mids[0]-mids[1]) < 1e-9:
        return None, {'favorite': False, 'aligned': False, 'buffer': False}
    side = 0 if mids[0] > mids[1] else 1
    sign = 1 if side == 0 else -1
    aligned = signal['spot_z']*sign > 0 and signal['twap_z']*sign > 0
    return side, dict(favorite=True, aligned=aligned,
                     buffer=aligned and signal['twap_z']*sign >= 1.)


def ask_cost(book, m, qty=5.):
    schedule = m.get('feeSchedule')
    if m.get('feesEnabled') and (not schedule or schedule.get('exponent') != 1):
        raise ValueError('unsupported fee schedule')
    rate = float(schedule['rate']) if m.get('feesEnabled') else 0.
    cost = fee = 0.
    remaining = qty
    for p, available in book['asks']:
        take = min(available, remaining)
        cost += take*p
        fee += take*rate*p*(1-p)
        remaining -= take
        if remaining < 1e-8:
            return cost, round(fee, 5)
    raise ValueError('insufficient ask depth')


def analyze():
    activity = json.loads((OUT/'activity.json').read_text())
    markets = {p.stem: json.loads(p.read_text()) for p in (OUT/'markets').glob('*.json')}
    grouped = defaultdict(list)
    for r in activity:
        if r['type'] == 'TRADE':
            grouped[r['slug']].append(r)
    streams, starts, excluded = load_prices()
    rows, windows = [], []
    missing = Counter()
    for slug, trades in sorted(grouped.items()):
        m = markets[slug]
        try:
            winner = outcome(m)
            if 'btc-usd-twap-60s-streams' not in m['description']:
                raise ValueError('different settlement rule')
            records, result = ledger(trades, winner)
        except ValueError as e:
            missing[str(e)] += 1
            continue
        S = int(slug.rsplit('-', 1)[1])
        reference = next((e.get('eventMetadata', {}).get('priceToBeat') for e in m.get('events', [])
                          if e.get('slug') == slug), None)
        mismatch = S in starts and reference is not None and abs(starts[S][1]-float(reference)) > 1e-6
        if mismatch:
            missing['reference_mismatch'] += 1
        by_second = defaultdict(set)
        for r in records:
            by_second[r['ts']].add(r['side'])
        ambiguous = any(len(v) > 1 for v in by_second.values())
        for r in records:
            r['winner'] = winner
            r['ordering_ambiguous'] = ambiguous
            for lag in (5, 10):
                try:
                    if mismatch:
                        raise ValueError('reference mismatch')
                    r[f'signal_{lag}'] = signals(streams, starts, S, (r['ts']-lag)*1000)
                except (KeyError, ValueError):
                    r[f'signal_{lag}'] = None
            rows.append(r)
        windows.append(dict(S=S, slug=slug, winner=winner, records=len(records),
                            qty=sum(r['qty'] for r in records), ordering_ambiguous=ambiguous, **result))
    save(OUT/'fill_ledger.json', rows)
    save(OUT/'windows.json', windows)
    report = dict(missing=dict(missing), excluded_price_files=excluded,
                  all=summary(rows), late=summary([r for r in rows if 200 < r['age'] < 300]),
                  early=summary([r for r in rows if r['age'] <= 200]),
                  timestamp_after_end=summary([r for r in rows if r['age'] >= 300]),
                  gross_pnl=sum(w['gross_pnl'] for w in windows),
                  cash_cost_pnl=sum(w['cash_cost_pnl'] for w in windows),
                  pair_cash_pnl=sum(w['pair_cash_pnl'] for w in windows),
                  residual_cash_pnl=sum(w['residual_cash_pnl'] for w in windows),
                  features_5s=sum(r['signal_5'] is not None for r in rows),
                  features_10s=sum(r['signal_10'] is not None for r in rows),
                  ambiguous_windows=sum(w['ordering_ambiguous'] for w in windows))
    report['behavior'] = {}
    report['late_behavior'] = {}
    for label in ('first', 'add', 'completion', 'reopen'):
        parts = []
        for r in rows:
            q = r['completion_qty'] if label == 'completion' else r['opening_qty'] if r['opening_kind'] == label else 0.
            if q:
                parts.append({**r, 'qty': q, 'marginal_cash_pnl': r['marginal_cash_pnl']*q/r['qty']})
        report['behavior'][label] = summary(parts)
        report['late_behavior'][label] = summary([r for r in parts if 200 < r['age'] < 300])
    late_adds = [r for r in rows if 200 < r['age'] < 300 and r['opening_kind'] == 'add' and abs(r['pre_net']) > 1e-8]
    report['exploratory_late_add_basis'] = {
        label: summary([r for r in late_adds if
            (r['cash_price'] < r['pre_unmatched_cash_cost']/abs(r['pre_net'])) == below])
        for label, below in [('below_existing_cost', True), ('at_or_above_existing_cost', False)]}
    report['late_features'] = {}
    for lag in (5, 10):
        for split in ('discovery', 'check'):
            cohort = [r for r in rows if 200 < r['age'] < 300 and r[f'signal_{lag}']
                      and (r['S'] < 1789689600) == (split == 'discovery')]
            for rule in ('all', 'aligned', 'buffer'):
                chosen = []
                for r in cohort:
                    sig = r[f'signal_{lag}']
                    sign = 1 if r['side'] == 0 else -1
                    aligned = sig['spot_z']*sign > 0 and sig['twap_z']*sign > 0
                    if rule == 'all' or (aligned and (rule == 'aligned' or sig['twap_z']*sign >= 1)):
                        chosen.append(r)
                report['late_features'][f'{split}_{lag}s_{rule}'] = summary(chosen)
    save(OUT/'report.json', report)
    print('ledger complete', len(windows), 'windows', len(rows), 'fills; price matches', report['features_5s'], flush=True)

    con = sqlite3.connect(BOOK_DB.as_uri()+'?mode=ro', uri=True)
    available = list(con.execute("SELECT DISTINCT start_ts,condition_id FROM subscribed_assets "
                     "WHERE market_title LIKE 'Bitcoin Up or Down%' AND end_ts-start_ts=300 "
                     "AND start_ts>=? AND end_ts<=? ORDER BY start_ts", (START, END)))
    policy, coverage = [], Counter()
    for i, (S, cid) in enumerate(available):
        targets = {}
        for age in (210, 240, 270):
            try:
                targets[age] = signals(streams, starts, S, (S+age)*1000)
            except (KeyError, ValueError):
                coverage['missing_prices'] += 1
        if not targets:
            continue
        slug = f'btc-updown-5m-{S}'
        if slug not in markets:
            path = OUT/'markets'/f'{slug}.json'
            m = get('https://gamma-api.polymarket.com/markets/slug/'+slug)
            save(path, m)
            markets[slug] = m
        m = markets[slug]
        assert m['conditionId'] == cid
        winner = outcome(m)
        reference = next((e.get('eventMetadata', {}).get('priceToBeat') for e in m.get('events', [])
                          if e.get('slug') == slug), None)
        if reference is None or abs(starts[S][1]-float(reference)) > 1e-6:
            coverage['missing_or_mismatched_reference'] += len(targets)
            continue
        moments = [int((S+age)*1000+lag) for age in targets for lag in (0, 250)]
        snap_path = OUT/'books'/f'{S}.json'
        if snap_path.exists():
            snaps = {int(k): v for k, v in json.loads(snap_path.read_text()).items()}
        else:
            snaps = snapshots(con, m, moments)
            save(snap_path, snaps)
        for age, sig in targets.items():
            now = (S+age)*1000
            decision, execution = snaps[now], snaps[now+250]
            if not decision or not execution:
                coverage['missing_books'] += 1
                continue
            side, selections = rules(sig, decision)
            if side is None:
                coverage['tie'] += 1
                continue
            try:
                cost, fee = ask_cost(execution[side], m)
            except ValueError as e:
                coverage[str(e)] += 1
                continue
            coverage['eligible'] += 1
            for name, selected in selections.items():
                pnl = 5*(side == winner)-cost-fee if selected else 0.
                policy.append(dict(S=S, age=age, rule=name, selected=selected, side=side,
                                   qty=5. if selected else 0., marginal_cash_pnl=pnl,
                                   cost=cost, fee=fee, signal=sig,
                                   books_received_ms=[b['received_ms'] for b in decision],
                                   execution_ms=now+250, execution_book_ms=execution[side]['received_ms']))
        if i % 30 == 0:
            print('policy markets', i+1, '/', len(available), dict(coverage), flush=True)
    con.close()
    save(OUT/'policy.json', policy)
    report['policy_coverage'] = dict(coverage)
    report['policy'] = {f'{age}_{name}': summary([r for r in policy if r['age'] == age and r['rule'] == name])
                        for age in (210, 240, 270) for name in ('favorite', 'aligned', 'buffer')}
    report['policy_selected'] = {f'{age}_{name}': sum(r['selected'] for r in policy if r['age'] == age and r['rule'] == name)
                                for age in (210, 240, 270) for name in ('favorite', 'aligned', 'buffer')}
    report['source_sha256'] = SOURCE_SHA
    report['data_semantics'] = ('cash_cost_pnl uses public activity usdcSize and final token payout; '
        'not wallet cash flow or full net income. Rebates/fixed costs excluded. '
        'Behavioral categories are accounting, not independent skill attribution. '
        'Policy rows include valid no-signal windows as zero, missing data separately. '
        'Only 19–20 September has overlapping usable order-book data; no pristine holdout claim.')
    save(OUT/'report.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('late_features', 'behavior')}, indent=2), flush=True)


def audit():
    """Separate observed fills from a pre-fill quoted-price benchmark; no simulated maker fills."""
    fills = json.loads((OUT/'fill_ledger.json').read_text())
    wanted = {r['tx'] for r in fills if 200 < r['age'] < 300}
    con = sqlite3.connect(BOOK_DB.as_uri()+'?mode=ro', uri=True)
    earliest = con.execute('SELECT ts_ms FROM market_events ORDER BY ts_ms LIMIT 1').fetchone()[0]
    matched = {}
    for rcv, raw in con.execute("SELECT ts_ms,raw_json FROM market_events WHERE event_type='last_trade_price' "
                                'AND ts_ms BETWEEN ? AND ? ORDER BY ts_ms', (earliest, END*1000+10000)):
        d = json.loads(raw)
        tx = d.get('transaction_hash')
        if tx in wanted and tx not in matched:
            matched[tx] = dict(rcv=rcv, obs=int(d['timestamp']), **d)
    print('transaction-aligned', len(matched), '/', len(wanted), flush=True)
    grouped = defaultdict(list)
    for r in fills:
        if r['tx'] in matched and 200 < r['age'] < 300:
            grouped[r['S']].append(r)
    result, missing = [], Counter()
    for i, (S, rows) in enumerate(sorted(grouped.items())):
        m = json.loads((OUT/'markets'/f'btc-updown-5m-{S}.json').read_text())
        times = [min(matched[r['tx']]['rcv'], matched[r['tx']]['obs'])-250 for r in rows]
        path = OUT/'execution_books'/f'{S}.json'
        if path.exists():
            snapshots_by_time = {int(k): v for k, v in json.loads(path.read_text()).items()}
        else:
            snapshots_by_time = snapshots(con, m, times)
            save(path, snapshots_by_time)
        for r, at_ms in zip(rows, times):
            pair = snapshots_by_time[at_ms]
            if not pair:
                missing['book'] += 1
                continue
            book = pair[r['side']]
            mid = (book['bid']+book['ask'])/2
            try:
                cost, fee = ask_cost(book, m)
            except ValueError:
                missing['depth_or_fee'] += 1
                continue
            result.append(dict(S=S, tx=r['tx'], qty=r['qty'], actual_cash_price=r['cash_price'],
                 decision_ms=at_ms, trade_ms=matched[r['tx']]['obs'], book=book,
                 actual_pnl=r['marginal_cash_pnl'],
                 direction_mid_component=r['qty']*((r['side'] == r['winner'])-mid),
                 price_mid_component=r['qty']*(mid-r['cash_price']),
                 five_share_actor_price_pnl=5*((r['side'] == r['winner'])-r['cash_price']),
                 five_share_quoted_ask_pnl=5*(r['side'] == r['winner'])-cost-fee,
                 prior_quote_discount=r['cash_price']-book['ask']))
        if i % 30 == 0:
            print('execution markets', i+1, '/', len(grouped), flush=True)
    con.close()
    for r in result:
        assert r['book']['received_ms'] <= r['decision_ms'] < r['trade_ms']
        assert abs(r['actual_pnl']-r['direction_mid_component']-r['price_mid_component']) < 1e-6
    normalized = [{**r, 'qty': 5.} for r in result]
    report = dict(matched_transactions=len(matched), requested_transactions=len(wanted), missing=dict(missing),
                  actual=summary(result, 'actual_pnl'),
                  direction_mid_component=sum(r['direction_mid_component'] for r in result),
                  price_mid_component=sum(r['price_mid_component'] for r in result),
                  five_share_actor_price=summary(normalized, 'five_share_actor_price_pnl'),
                  five_share_prior_ask=summary(normalized, 'five_share_quoted_ask_pnl'),
                  caveat='Paired pre-fill quote benchmark, not a tradable backtest. Actor-selected times; '
                         'price is API VWAP; five-share comparison weights each activity record equally. '
                         'Midpoint is not executable. No inferred cancellations/queue rank/maker role.')
    save(OUT/'execution_audit_rows.json', result)
    save(OUT/'execution_audit.json', report)
    print(json.dumps(report, indent=2), flush=True)


def completion_path(trades, winner):
    lots = [deque(), deque()]
    qty = [0., 0.]
    cost = baseline = late_qty = late_cost = 0.
    baseline_risk = None
    for a in sorted(trades, key=lambda a: (a['timestamp'], a['transactionHash'], a['outcomeIndex'])):
        if a['side'] != 'BUY':
            raise ValueError('BUY-only experiment')
        S = int(a['slug'].rsplit('-', 1)[1])
        age = a['timestamp']-S
        if age >= 300:
            continue
        side, remaining = a['outcomeIndex'], float(a['size'])
        cash = float(a['usdcSize'])/remaining
        if age <= 200:
            qty[side] += remaining
            cost += remaining*cash
            baseline += remaining*((side == winner)-cash)
            while remaining > 1e-8 and lots[1-side]:
                lot = lots[1-side][0]
                take = min(remaining, lot[0])
                lot[0] -= take
                remaining -= take
                if lot[0] < 1e-8:
                    lots[1-side].popleft()
            if remaining > 1e-8:
                lots[side].append([remaining, cash])
        else:
            if baseline_risk is None:
                baseline_risk = max(0., cost-min(qty))
            while remaining > 1e-8 and lots[1-side] and lots[1-side][0][1]+cash <= .98+1e-10:
                lot = lots[1-side][0]
                take = min(remaining, lot[0])
                lot[0] -= take
                remaining -= take
                qty[side] += take
                cost += take*cash
                late_qty += take
                late_cost += take*cash
                if lot[0] < 1e-8:
                    lots[1-side].popleft()
    pnl = qty[winner]-cost
    delta = pnl-baseline
    if abs(delta) < 1e-8:
        delta = 0.
    risk = max(0., cost-min(qty))
    assert baseline_risk is None or risk <= baseline_risk+1e-6
    return dict(S=S, qty=late_qty, marginal_cash_pnl=delta, baseline_pnl=baseline,
                variant_pnl=pnl, late_cost=late_cost, baseline_risk=baseline_risk, final_risk=risk)


def counterfactual():
    grouped = defaultdict(list)
    for r in json.loads((OUT/'activity.json').read_text()):
        if r['type'] == 'TRADE':
            grouped[r['slug']].append(r)
    rows = []
    for slug, trades in sorted(grouped.items()):
        m = json.loads((OUT/'markets'/f'{slug}.json').read_text())
        rows.append(completion_path(trades, outcome(m)))
    report = dict(description='Exploratory, conditional on observed fills. Not an executable backtest. '
                  'Early fills unchanged; late completion only, FIFO cash cap .98. Same-second order uncertain.',
                  delta=summary(rows), affected=summary([r for r in rows if r['qty'] > 0]),
                  improved=sum(r['marginal_cash_pnl'] > 1e-8 for r in rows),
                  worse=sum(r['marginal_cash_pnl'] < -1e-8 for r in rows),
                  baseline_pnl=sum(r['baseline_pnl'] for r in rows),
                  variant_pnl=sum(r['variant_pnl'] for r in rows), windows=rows)
    ambiguous = {w['S'] for w in json.loads((OUT/'windows.json').read_text()) if w['ordering_ambiguous']}
    report['excluding_ambiguous_order'] = summary([r for r in rows if r['S'] not in ambiguous])
    save(OUT/'completion_counterfactual.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'windows'}, indent=2))


def live_signal(db, S, now_ms):
    with sqlite3.connect(db.resolve().as_uri()+'?mode=ro', uri=True, timeout=1) as con:
        ref = con.execute('SELECT received_ms,price FROM prices WHERE source=? AND observed_ms=? '
                          'AND received_ms BETWEEN ? AND ? ORDER BY received_ms LIMIT 1',
                          ('crypto_prices_twap_sixty', S*1000, S*1000, now_ms)).fetchone()
        if ref is None:
            raise ValueError('exact-start reference missing')
        rows = con.execute('SELECT received_ms,observed_ms,source,price FROM prices '
                           'WHERE received_ms BETWEEN ? AND ? ORDER BY received_ms', (now_ms-65000, now_ms))
        names = {'crypto_prices_chainlink': 'spot', 'crypto_prices_twap_sixty': 'twap60'}
        streams = {s: ([], []) for s in names.values()}
        for rcv, obs, name, price in rows:
            if name not in names or obs > rcv:
                continue
            times, values = streams[names[name]]
            if values and obs < values[-1][0]:
                continue
            times.append(rcv)
            values.append((obs, price))
    return signals(streams, {S: ref}, S, now_ms)


def public_book(token):
    d = get('https://clob.polymarket.com/book?token_id='+token, timeout=3, attempts=1)
    now = round(time.time()*1000)
    if str(d.get('asset_id')) != token or not 0 <= now-int(d['timestamp']) <= 3000:
        raise ValueError('stale or mismatched public book')
    bids = [(float(x['price']), float(x['size'])) for x in d['bids'] if float(x['size']) > 0]
    asks = [(float(x['price']), float(x['size'])) for x in d['asks'] if float(x['size']) > 0]
    if not bids or not asks or any(not math.isfinite(p) or not math.isfinite(q) or not 0 < p <= 1 for p, q in bids+asks):
        raise ValueError('empty/invalid public book')
    bid, ask = max(p for p, _ in bids), min(p for p, _ in asks)
    if bid >= ask:
        raise ValueError('crossed book')
    return dict(bid=bid, ask=ask, asks=sorted(asks), received_ms=now,
                observed_ms=int(d['timestamp']), hash=d.get('hash'))


def watch(args):
    """24h public-data recorder. Hypothetical taker costs; never submits orders."""
    import fcntl
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    lock = (out/'watch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest_path = out/'watch_manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['source_sha256'] != source_hash:
            raise ValueError('frozen source hash changed')
    else:
        S = int(time.time())//300*300+300
        manifest = dict(start_S=S, end_S=S+args.minutes*60, source_sha256=source_hash,
                        mode='SHADOW_NO_ORDERS', clip=5, slots=[210, 240, 270],
                        rules=['favorite', 'aligned', 'buffer'], primary_slot=240,
                        cost='public ask depth after >=250ms + market taker fee; no rebate assumed',
                        gate='>=3 days and >=100 windows; both cluster CI lower bounds >0; ex-top3 >0',
                        prices_db=str(args.prices_db), started_ms=round(time.time()*1000))
        save(manifest_path, manifest)
    path = out/'shadow.jsonl'
    history = [json.loads(line) for line in path.open()] if path.exists() else []
    attempted = {(e['S'], e['age']) for e in history if e['kind'] in ('decision', 'gap')}
    decided = {e['S'] for e in history if e['kind'] == 'decision'}
    graded = {e['S'] for e in history if e['kind'] == 'resolution'}
    markets = {}
    def emit(kind, **values):
        event = dict(kind=kind, recorded_ms=round(time.time()*1000), **values)
        with path.open('a') as stream:
            stream.write(json.dumps(event, separators=(',', ':'))+'\n')
        print(json.dumps({k: v for k, v in event.items() if k not in ('books', 'execution_book', 'signal')},
                         separators=(',', ':')), flush=True)
    emit('start', **manifest)
    last_health = last_grade = 0.
    while time.time() < manifest['end_S']+1500 and not (out/'STOP_SHADOW').exists():
        now = time.time()
        S = int(now)//300*300
        age_now = now-S
        if manifest['start_S'] <= S < manifest['end_S']:
            for age in manifest['slots']:
                if (S, age) in attempted or age_now < age:
                    continue
                attempted.add((S, age))
                try:
                    if age_now-age > 3:
                        raise ValueError('missed decision deadline')
                    if S not in markets:
                        markets[S] = get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{S}', timeout=5, attempts=1)
                    m = markets[S]
                    if m.get('closed') or 'btc-usd-twap-60s-streams' not in m['description']:
                        raise ValueError('closed or unsupported market')
                    tokens = json.loads(m['clobTokenIds'])
                    if json.loads(m['outcomes']) != ['Up', 'Down']:
                        raise ValueError('outcome mapping')
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        books = list(pool.map(public_book, tokens))
                    decision_ms = round(time.time()*1000)
                    if decision_ms > (S+age+3)*1000:
                        raise ValueError('late book response')
                    signal = live_signal(args.prices_db, S, decision_ms)
                    official = next((e.get('eventMetadata', {}).get('priceToBeat') for e in m.get('events', [])
                                     if e.get('slug') == m['slug']), None)
                    if official is not None and abs(float(official)-signal['ref']) > 1e-6:
                        raise ValueError('reference mismatch')
                    side, selections = rules(signal, books)
                    if side is None:
                        raise ValueError('no favorite')
                    time.sleep(.25)
                    execution = public_book(tokens[side])
                    if execution['received_ms']-decision_ms > 3000:
                        raise ValueError('late execution quote')
                    cost, fee = ask_cost(execution, m)
                    emit('decision', S=S, age=age, side=side, selected=selections, signal=signal,
                         books=books, execution_book=execution, cost=cost, fee=fee,
                         qty=5., fee_schedule=m.get('feeSchedule'), model_source_sha256=source_hash)
                    decided.add(S)
                except (OSError, ValueError, KeyError, sqlite3.Error) as ex:
                    emit('gap', S=S, age=age, error=type(ex).__name__, reason=str(ex)[:180])
        if now-last_grade >= 60:
            last_grade = now
            for old in sorted(decided-graded):
                if old+1500 > now:
                    continue
                try:
                    m = get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{old}?snapshot={int(now)//30}', timeout=5, attempts=1)
                    emit('resolution', S=old, winner=outcome(m), condition=m['conditionId'])
                    graded.add(old)
                except (OSError, ValueError, KeyError) as ex:
                    emit('resolution_pending', S=old, error=type(ex).__name__)
        if now-last_health >= 60:
            last_health = now
            emit('health', slots_attempted=len(attempted), windows_recorded=len(decided),
                 windows_graded=len(graded), end_S=manifest['end_S'])
        time.sleep(.2)
    emit('stop', pending=sorted(decided-graded), reason='stop_file' if (out/'STOP_SHADOW').exists() else 'duration')


def check():
    def r(side, price, qty, ts):
        return dict(side='BUY', size=qty, price=price, outcomeIndex=side,
                    usdcSize=price*qty, timestamp=ts, transactionHash=str(ts),
                    slug='btc-updown-5m-0')
    trades = [r(0, .3, 5, 1), r(1, .6, 5, 2), r(0, .6, 5, 3), r(1, .53, 5, 4)]
    rows, result = ledger(trades, 0)
    assert abs(result['gross_pnl']+.15) < 1e-8
    assert rows[2]['opening_kind'] == 'reopen'
    assert ledger(trades, 0) == (rows, result)  # No mutation on a repeated call.
    rows, result = ledger([r(0, .2, 5, 1), r(1, .7, 8, 2)], 1)
    assert rows[1]['completion_qty'] == 5 and rows[1]['opening_qty'] == 3
    assert abs(result['gross_pnl']-1.4) < 1e-8
    example = [r(0, .2, 5, 10), r(1, .7, 5, 250)]
    assert abs(completion_path(example, 0)['marginal_cash_pnl']+3.5) < 1e-8
    assert abs(completion_path(example, 1)['marginal_cash_pnl']-1.5) < 1e-8
    con = sqlite3.connect(':memory:')
    con.execute('CREATE TABLE market_events (id INTEGER,ts_ms INTEGER,condition_id TEXT,raw_json TEXT,asset_id TEXT,event_type TEXT)')
    m = dict(slug='btc-updown-5m-0', conditionId='test', clobTokenIds='["a","b"]',
             feesEnabled=True, feeSchedule={'rate': .07, 'exponent': 1})
    for i, token in enumerate(('a', 'b')):
        event = dict(event_type='book', asset_id=token, timestamp='200000',
                     bids=[dict(price='.49', size='10')], asks=[dict(price='.51', size='10')])
        con.execute('INSERT INTO market_events VALUES(?,?,?,?,?,?)', (i, 200010, 'test', json.dumps(event), token, 'book'))
    event = dict(event_type='price_change', timestamp='200100', price_changes=[
        dict(asset_id='a', side='SELL', price='.51', size='7'),
        dict(asset_id='b', side='SELL', price='.51', size='4')])
    con.execute('INSERT INTO market_events VALUES(?,?,?,?,?,?)', (2, 200110, 'test', json.dumps(event), 'a', 'price_change'))
    snaps = snapshots(con, m, [200050, 200150, 204000])
    later = snapshots(con, m, [199999, 200150])
    assert later[199999] is None and later[200150] == snaps[200150]
    assert snaps[200050][1]['asks'] == [(.51, 10.)]
    assert snaps[200150][1]['asks'] == [(.51, 4.)]  # Both assets in one message.
    assert snaps[204000] is None
    cost, fee = ask_cost(snaps[200050][0], m)
    assert abs(cost-2.55) < 1e-8 and fee == .08747
    try:
        ask_cost(snaps[200150][1], m)
        raise AssertionError('insufficient depth accepted')
    except ValueError:
        pass
    ss = {name: (list(range(100000, 200001, 1000)), [(v, 100+v/10000) for v in range(100000, 200001, 1000)])
          for name in ('spot', 'twap60')}
    before = signals(ss, {0: (0, 100)}, 0, 200000)
    for times, values in ss.values():
        times.append(200001)
        values.append((200001, 999999))
    assert signals(ss, {0: (0, 100)}, 0, 200000) == before
    text_prices = {name: (times, [(obs, str(price)) for obs, price in values]) for name, (times, values) in ss.items()}
    assert signals(text_prices, {0: (0, '100')}, 0, 200000) == before
    con.close()
    print('FIFO, repeated calls, batched book updates, stale/future data, fees and depth checks passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['fetch', 'check', 'analyze', 'audit', 'counterfactual', 'watch'])
    parser.add_argument('--out', type=Path, default=OUT/'forward')
    parser.add_argument('--prices-db', type=Path)
    parser.add_argument('--minutes', type=int, default=1440)
    args = parser.parse_args()
    if args.action == 'watch':
        if args.prices_db is None or not args.prices_db.is_file() or not 1 <= args.minutes <= 1440:
            parser.error('watch requires an existing read-only prices database and 1..1440 minutes')
        watch(args)
    else:
        globals()[args.action]()
