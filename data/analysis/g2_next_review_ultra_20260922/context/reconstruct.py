"""Bounded, read-only sample64 context recovery. No network, outcomes used only as labels."""
import bisect
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path('/home/taygun/Masaüstü/polymarket-bosona')
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'data/analysis'
sys.path.insert(0, str(ROOT / 'analiz/izleme'))
import bosona_derin as deep  # noqa: E402  pure import; only read helpers called


def read(path):
    return json.loads(Path(path).read_bytes())


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def label_day(s):
    return datetime.fromtimestamp(s, timezone.utc).strftime('%Y-%m-%d')


def fee(rate, p, q):
    return round(rate * p * (1-p) * q, 5)


def sweep(levels, quantity, rate, buy):
    left, cash, fees = quantity, 0., 0.
    for p, q in sorted(levels, reverse=not buy):
        take = min(left, q)
        cash += take*p
        fees += take*rate*p*(1-p)
        left -= take
        if left <= 1e-8:
            return dict(quantity=quantity, cash=cash + round(fees, 5)*(1 if buy else -1),
                        fee=round(fees, 5))
    return None


def cached_book(b):
    return dict(bid=b[0], ask=b[1], bid_top_q=b[2], ask_top_q=b[3], bid_depth3=b[4],
                ask_depth3=b[5], ask5_fee=b[7], ask5_cash=None if b[6] is None else b[6]+b[7],
                received_ms=b[8], observed_ms=b[9], depth_source='top_and_3cent_aggregate')


def at_book(snaps, s, now):
    if s not in snaps:
        return None
    tt, rows = snaps[s]
    i = bisect.bisect_right(tt, now)-1
    if i < 0 or now-tt[i] > 1250:
        return None
    row = rows[tt[i]]
    return dict(snapshot_ms=tt[i], source=row['source'], books=[
        b if b and 0 <= now-b['received_ms'] <= 3000 and 0 <= now-b['observed_ms'] <= 3000 else None
        for b in row['books']])


def price_at(streams, name, now):
    tt, vv = streams[name]
    i = bisect.bisect_right(tt, now)-1
    if i < 0 or not 0 <= now-tt[i] <= 3000 or not 0 <= now-vv[i][0] <= 3000:
        return None
    return dict(price=float(vv[i][1]), received_ms=tt[i], observed_ms=vv[i][0])


def db_snapshots(con, market, times):
    """Same replay as existing snapshots, retain partial books and full depth, validate reported L1."""
    tokens = json.loads(market['clobTokenIds'])
    s = int(market['slug'].rsplit('-', 1)[1])
    books = {t: dict(BUY={}, SELL={}, ready=False, rcv=0, obs=0) for t in tokens}
    first = min(times)
    last_full = [con.execute("SELECT ts_ms FROM market_events WHERE asset_id=? AND event_type='book' "
        'AND ts_ms BETWEEN ? AND ? ORDER BY ts_ms DESC LIMIT 1', (t, (s-1800)*1000, first)).fetchone()
        for t in tokens]
    begin = min(x[0] for x in last_full) if all(last_full) else (s-1800)*1000
    cursor = iter(con.execute('SELECT ts_ms,raw_json FROM market_events WHERE condition_id=? '
        'AND ts_ms BETWEEN ? AND ? ORDER BY ts_ms,id', (market['conditionId'], begin, max(times))))
    pending, output, stats, trades = next(cursor, None), {}, Counter(), {}
    rate = float(market.get('feeSchedule', {}).get('rate', 0))
    for target in sorted(set(times)):
        while pending and pending[0] <= target:
            rcv, raw = pending
            d = json.loads(raw)
            obs, kind = int(d.get('timestamp', rcv)), d.get('event_type')
            if kind == 'book' and d.get('asset_id') in books:
                b = books[d['asset_id']]
                if obs >= b['obs'] and rcv >= b['rcv']:
                    for side, key in [('BUY', 'bids'), ('SELL', 'asks')]:
                        b[side] = {float(x['price']): float(x['size']) for x in d.get(key, []) if float(x['size']) > 0}
                    b.update(rcv=rcv, obs=obs, ready=True)
            elif kind == 'price_change':
                for change in d.get('price_changes', []):
                    b = books.get(change.get('asset_id'))
                    if b is None or not b['ready'] or obs < b['obs'] or rcv < b['rcv']:
                        continue
                    p, q = float(change['price']), float(change['size'])
                    if q > 0:
                        b[change['side']][p] = q
                    else:
                        b[change['side']].pop(p, None)
                    b.update(rcv=rcv, obs=obs)
                    if b['BUY'] and b['SELL'] and change.get('best_bid') and change.get('best_ask'):
                        if abs(max(b['BUY'])-float(change['best_bid'])) > 1e-8 or abs(min(b['SELL'])-float(change['best_ask'])) > 1e-8:
                            b['ready'] = False
                            stats['l1_mismatch_invalidated'] += 1
            elif kind == 'last_trade_price' and d.get('transaction_hash'):
                trades[d['transaction_hash']] = dict(rcv=rcv, obs=obs)
            stats['events_read'] += 1
            pending = next(cursor, None)
        pair = []
        for t in tokens:
            b = books[t]
            if not b['ready'] or not 0 <= target-b['rcv'] <= 3000 or not 0 <= target-b['obs'] <= 3000:
                pair.append(None)
                continue
            bids, asks = b['BUY'], b['SELL']
            bid, ask = max(bids) if bids else None, min(asks) if asks else None
            if bid is not None and ask is not None and not 0 < bid < ask <= 1:
                pair.append(None)
                continue
            buy5 = sweep(asks.items(), 5., rate, True)
            pair.append(dict(bid=bid, ask=ask, bid_top_q=bids.get(bid), ask_top_q=asks.get(ask),
                bid_depth3=sum(q for p, q in bids.items() if p >= bid-.03-1e-8) if bid else None,
                ask_depth3=sum(q for p, q in asks.items() if p <= ask+.03+1e-8) if ask else None,
                ask5_cash=buy5['cash'] if buy5 else None, bids=sorted(bids.items(), reverse=True),
                asks=sorted(asks.items()), received_ms=b['rcv'], observed_ms=b['obs'], depth_source='full_ladder'))
        output[target] = dict(source='read_only_sqlite_replay', books=pair)
    return output, dict(stats), trades


def quantity_price(book, q, rate, buy):
    if not book or q <= 0:
        return None
    levels = book.get('asks' if buy else 'bids')
    if levels is None and buy and q == 5. and book.get('ask5_cash') is not None:
        return dict(quantity=q, cash=book['ask5_cash'], fee=book.get('ask5_fee'))
    if levels is None:
        p, available = book['ask' if buy else 'bid'], book['ask_top_q' if buy else 'bid_top_q']
        if p is None or available is None or available + 1e-8 < q:
            return None
        levels = [(p, available)]
    return sweep(levels, q, rate, buy)


def context(row, lag, snaps, streams, starts, market, txs, fills):
    now, s = (row['ts']-lag)*1000, row['S']
    prior = [f for f in fills if f['ts']*1000 <= now]
    net = sum((1 if f['outcome'] == 0 else -1)*f['qty'] for f in prior)
    out = dict(now_ms=now, remaining_seconds=s+300-now/1000, net_at_cutoff_units=net,
               inventory_changed_since_cut=net != row['net_before_units'],
               first_fill_age_seconds=now/1000-min(f['ts'] for f in prior) if prior else None,
               last_fill_age_seconds=now/1000-max(f['ts'] for f in prior) if prior else None)
    ref = starts.get(s)
    out['reference'] = dict(price=ref[1], received_ms=ref[0], observed_ms=s*1000) if ref and ref[0] <= now else None
    for name in ('spot', 'twap60'):
        out[name] = price_at(streams, name, now)
        old = price_at(streams, name, now-10000)
        out[name+'_change10'] = out[name]['price']-old['price'] if out[name] and old else None
    clocks = [txs[t] for t in row.get('transactions', []) if t in txs]
    out['matched_public_ws'] = clocks
    out['before_all_matched_ws_observations'] = all(now <= c['obs'] for c in clocks) if clocks else None
    snap = at_book(snaps, s, now)
    out['book'] = snap
    side = row['side']
    held_side = 0 if net > 0 else 1 if net < 0 else None
    out['held_side'] = held_side
    for side_label, idx in [('bought', side), ('held', held_side), ('opposite', 1-held_side if held_side is not None else None)]:
        b = snap['books'][idx] if snap and idx is not None else None
        out[side_label+'_bid'] = b['bid'] if b else None
        out[side_label+'_ask'] = b['ask'] if b else None
        if b:
            out[side_label+'_received_age_ms'] = now-b['received_ms']
            out[side_label+'_observed_age_ms'] = now-b['observed_ms']
        for delta in (5, 10, 30, 60):
            old = at_book(snaps, s, now-delta*1000)
            old_b = old['books'][idx] if old and idx is not None else None
            out[f'{side_label}_bid_change{delta}'] = b['bid']-old_b['bid'] if b and old_b and b['bid'] is not None and old_b['bid'] is not None else None
        if out['reference']:
            for name in ('spot', 'twap60'):
                out[side_label+'_'+name+'_minus_ref'] = (1 if idx == 0 else -1)*(out[name]['price']-ref[1]) if idx is not None and out[name] else None
    rate = float(market.get('feeSchedule', {}).get('rate', 0))
    out['archived_fee_rate_assumption'] = rate
    if held_side is not None and snap:
        held, opposite = snap['books'][held_side], snap['books'][1-held_side]
        for quantity_label, q in [('5', 5.), ('inventory', abs(net)/1e6), ('actor_reducing', row.get('reducing_units', 0)/1e6)]:
            out['opposite_buy_'+quantity_label] = quantity_price(opposite, q, rate, True)
            out['held_sell_'+quantity_label] = quantity_price(held, q, rate, False)
            a, b = out['opposite_buy_'+quantity_label], out['held_sell_'+quantity_label]
            out['opposite_buy_advantage_'+quantity_label] = q-a['cash']-b['cash'] if a and b else None
    if row['kind'] == 'control':
        execution = at_book(snaps, s, now+250)
        if execution and execution['snapshot_ms'] != now+250:
            execution = None
        exheld = execution['books'][held_side] if execution and held_side is not None else None
        exother = execution['books'][1-held_side] if execution and held_side is not None else None
        out['execution250'] = dict(execution_only_not_signal=True, target_ms=now+250,
            book=execution, opposite_buy_5=quantity_price(exother, 5., rate, True),
            held_sell_5=quantity_price(exheld, 5., rate, False))
    return out


def checks(events):
    assert len([r for r in events if r['role'] == 'taker' and r['kind'] == 'reduce']) == 26
    assert sum(r['kind'] != 'control' for r in events) == 262
    for r in events:
        for lag in (5, 10):
            c = r[f'lag{lag}']
            assert c['now_ms'] == (r['ts']-lag)*1000
            for name in ('reference', 'spot', 'twap60'):
                p = c[name]
                if p:
                    assert p['received_ms'] <= c['now_ms'] and p['observed_ms'] <= c['now_ms']
            if c['book']:
                assert c['book']['snapshot_ms'] <= c['now_ms']
                for b in c['book']['books']:
                    if b:
                        assert 0 <= c['now_ms']-b['received_ms'] <= 3000
                        assert 0 <= c['now_ms']-b['observed_ms'] <= 3000
    assert sweep([(0.4, 4)], 5, .07, True) is None
    assert sweep([(0.4, 5)], 5, 0, True)['cash'] == 2.
    fake = {1: ([10], {10: dict(source='test', books=[dict(received_ms=11, observed_ms=9), None])})}
    assert at_book(fake, 1, 10)['books'] == [None, None]


def main():
    manifest = read(DATA/'btc5m_parent_research_20260921/manifest.json')
    sample = set(manifest['cohorts']['representative'])
    original = read(DATA/'g1_selective_exit_20260922/results.json')
    report = read(DATA/'btc5m_parent_research_20260921/report.json')
    events = [dict(r) for r in original['rows'] if r['S'] in sample]
    fills, by_start = defaultdict(list), defaultdict(list)
    for f in report['fills']:
        if f['S'] in sample:
            fills[f['S']].append(f)
    market_results = {r['S']: r for r in report['market_results']}
    for s in sorted(sample):
        for age in (120, 240):
            prior = [f for f in fills[s] if f['ts'] < s+age]
            net = sum((1 if f['outcome'] == 0 else -1)*f['qty'] for f in prior)
            events.append(dict(S=s, ts=s+age, age=age, parent=None, side=1 if net > 0 else 0,
                net_before_units=net, quantity_units=0, reducing_units=0, kind='control', role='fixed_inventory_probe', transactions=[],
                no_observed_reduction=market_results[s]['first_reduction']['status']=='no_reduction'))
    markets = deep.markets()
    for r in events:
        by_start[r['S']].append(r)
        prior = [f for f in fills[r['S']] if f['ts'] < r['ts']]
        r['age_since_first_observed_fill'] = r['ts']-min(f['ts'] for f in prior) if prior else None
        r['age_since_last_observed_fill'] = r['ts']-max(f['ts'] for f in prior) if prior else None
        r['pre_cumulative_buy_cash'] = sum(f['cash_cost'] for f in prior)/1e6
        r['day'] = label_day(r['S'])
        r['outcome_label'] = dict(winner=market_results[r['S']]['winner'], market_pnl=market_results[r['S']]['api_cash_pnl'])
    hours = {datetime.fromtimestamp(s, timezone.utc).strftime('tape_%Y%m%d_%H.jsonl.gz') for s in sample}
    snaps, txs, sources = defaultdict(dict), {}, []
    paths = sorted(p for p in (deep.OUT/'tape_snapshots').glob('*.gz') if p.name in hours)
    for path in paths:
        with gzip.open(path, 'rb') as stream:
            payload = json.load(stream)
        source = read(path.with_name(path.name+'.json'))
        source.update(cache_path=str(path), cache_sha256=sha256(path.read_bytes()).hexdigest())
        raw = deep.TAPE/path.name
        source['raw_exists'] = raw.exists()
        source['raw_size_matches_manifest'] = raw.stat().st_size == source['source_bytes'] if raw.exists() else None
        sources.append(source)
        for s, now, pair in payload['snapshots']:
            if s in sample:
                snaps[s][now] = dict(source=path.name, books=[cached_book(b) for b in pair])
        for s, rcv, obs, p in payload['trades']:
            if s in sample and p.get('transaction_hash'):
                txs[p['transaction_hash']] = dict(rcv=rcv, obs=obs)
    for directory in (deep.base.OUT/'books', deep.base.OUT/'execution_books', deep.OUT/'new_books'):
        for s in sorted(sample):
            path = directory/f'{s}.json'
            if not path.exists():
                continue
            for when, pair in read(path).items():
                if not pair:
                    continue
                books = []
                for b in pair:
                    rate = float(markets[s].get('feeSchedule', {}).get('rate', 0))
                    buy5 = sweep(b['asks'], 5., rate, True)
                    books.append(dict(bid=b['bid'], ask=b['ask'], bid_top_q=None,
                        ask_top_q=b['asks'][0][1], bid_depth3=None,
                        ask_depth3=sum(q for p, q in b['asks'] if p <= b['ask']+.03+1e-8),
                        asks=b['asks'], ask5_cash=buy5['cash'] if buy5 else None,
                        received_ms=b['received_ms'], observed_ms=b['observed_ms'], depth_source='full_ask_no_bid_depth'))
                snaps[s][int(when)] = dict(source=str(path.relative_to(DATA)), books=books)
    print('cached sample markets', len(snaps), 'sample snapshots', sum(map(len, snaps.values())), flush=True)
    db = deep.base.BOOK_DB
    dbstats = {}
    with sqlite3.connect(db.as_uri()+'?mode=ro', uri=True) as con:
        subscribed = {x[0] for x in con.execute("SELECT DISTINCT start_ts FROM subscribed_assets WHERE market_title LIKE '%Bitcoin%' AND end_ts-start_ts=300")}
        for s in sorted(sample & subscribed):
            times = {(r['ts']-lag-delta)*1000 for r in by_start[s] for lag in (5, 10) for delta in (0, 5, 10, 30, 60)
                     if s*1000 < (r['ts']-lag-delta)*1000 < (s+300)*1000}
            times.update((r['ts']-lag)*1000+250 for r in by_start[s] for lag in (5, 10) if r['kind']=='control')
            if not times:
                continue
            replay, stats, trades = db_snapshots(con, markets[s], times)
            for now, snap in replay.items():
                if any(snap['books']) or now not in snaps[s]:
                    snaps[s][now] = snap
            txs.update(trades)
            dbstats[s] = stats
            print('DB', s, stats, flush=True)
    streams, starts, excluded = deep.deep_prices()
    snaps = {s: (sorted(v), v) for s, v in snaps.items()}
    for r in events:
        for lag in (5, 10):
            r[f'lag{lag}'] = context(r, lag, snaps, streams, starts, markets[r['S']], txs, fills[r['S']])
    checks(events)
    save('events.json', events)
    def coverage(rr):
        out = dict(n=len(rr))
        for lag in (5, 10):
            cc = [r[f'lag{lag}'] for r in rr]
            out[f'lag{lag}'] = dict(book_both=sum(bool(c['book'] and all(c['book']['books'])) for c in cc),
                book_any=sum(bool(c['book'] and any(c['book']['books'])) for c in cc),
                spot=sum(c['spot'] is not None for c in cc), reference=sum(c['reference'] is not None for c in cc),
                twap=sum(c['twap60'] is not None for c in cc),
                combined=sum(bool(c['book'] and all(c['book']['books']) and c['spot'] and c['reference'] and c['twap60']) for c in cc),
                matched_public_ws=sum(bool(c['matched_public_ws']) for c in cc),
                after_matched_ws=sum(c['before_all_matched_ws_observations'] is False for c in cc),
                inventory_changed_since_cut=sum(c['inventory_changed_since_cut'] for c in cc),
                buy_inventory_depth=sum(c.get('opposite_buy_inventory') is not None for c in cc),
                sell_inventory_depth=sum(c.get('held_sell_inventory') is not None for c in cc))
        return out
    takers = [r for r in events if r['role']=='taker' and r['kind']=='reduce']
    summary = dict(sample_markets=64, original_classified_parents=262,
        controls_with_no_observed_reduction=sum(r['kind']=='control' and r['no_observed_reduction'] for r in events),
        old_complete_taker_contexts=sum(r.get('context', {}).get('status')=='observed_clock_context' for r in takers),
        by_group={f'{role}_{kind}': coverage([r for r in events if r['role']==role and r['kind']==kind])
                  for role, kind in sorted({(r['role'], r['kind']) for r in events})},
        taker_by_day={d:coverage([r for r in takers if r['day']==d]) for d in sorted({r['day'] for r in takers})},
        taker_early=coverage([r for r in takers if r['age']<=200]), taker_late=coverage([r for r in takers if r['age']>200]),
        db_stats=dbstats, excluded_price_sources=excluded,
        caveats=['Public-second event minus 5/10s is a timestamp sensitivity, not known actor placement time.',
          'exchange_age inherited field is public WS payload timestamp, never exact actor decision time.',
          'Cached older books retain only both-sided valid pairs; missing cache does not prove absent raw.',
          'Pre-window zero inventory is inherited public history assumption; external transfers are not established.',
          'Controls are two fixed times in all original sample markets; no_observed_reduction is an outcome-independent observed behavior cohort label, not decision not to hedge.',
          'Cash execution estimates use archived feeSchedule and displayed depth, no fill guarantee or latency buffer.'])
    summary['missing_taker_contexts'] = [dict(S=r['S'], age=r['age'], parent=r['parent'],
        reason=('before_accessible_raw_archive' if r['S'] < 1789304400 else
                'between_old_tape_end_and_new_DB_start' if 1789768800 <= r['S'] < 1789830600 else
                'recording_outage_first_20Sep_13h_records_at_13_13_47UTC'),
        legacy_available=r['context']['status']) for r in takers if not r['lag5']['spot']]
    save('summary.json', summary)
    raw_paths = sorted(deep.TAPE.glob('*.gz'))
    save('sources.json', dict(code_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        selected_cache_sources=sources, raw_inventory=dict(files=len(raw_paths), bytes=sum(p.stat().st_size for p in raw_paths),
        first=raw_paths[0].name, last=raw_paths[-1].name),
        sqlite=dict(path=str(db), size=db.stat().st_size, sample_subscribed=sorted(sample & subscribed)),
        hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in [DATA/'g1_selective_exit_20260922/results.json',
           DATA/'btc5m_parent_research_20260921/report.json', DATA/'btc5m_parent_research_20260921/manifest.json',
           Path(deep.__file__), Path(deep.base.__file__)]}))
    print(json.dumps(summary['by_group']['taker_reduce'], indent=2))


if __name__ == '__main__':
    main()
