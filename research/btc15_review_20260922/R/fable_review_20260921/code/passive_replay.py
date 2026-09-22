#!/usr/bin/env python3
"""Queue-position passive-quote replay on recorded 1s L2 books + public market-wide prints.

Pre-registered in ../plan.md (ÖN KAYIT 2). Finite, offline, no orders. Bounds only:
PESSIMISTIC = nobody ahead of us cancels
OPTIMISTIC = we are first in queue.
Arms: P0 (frozen candidate on real books, taker), P1a touch-maker, P1b touch-1, P2 = P1a + taker hedge.

Usage: python3 passive_replay.py --tape <json.gz with rows|jsonl.gz files...> --markets <dir> --trades <dir> --out <dir>
"""
import argparse
import bisect
import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
MAIN = Path('/home/taygun/Masaüstü/polymarket-bosona')
sys.path.insert(0, str(R))
import research as r  # noqa: E402  (module import only, no writes)
import candidate as c  # noqa: E402

TICK = 0.01
QTY = 5.0
LIMIT_CASH, LIMIT_NET, LIMIT_WORST = 15.0, 10.0, 5.0


# ---------------- data loading ----------------
def load_tape(paths):
    """Return {S: [snapshot,...]} sorted by received_ms; snapshot = dict(received_ms, requested_ms, books{token:(bids desc, asks asc)})."""
    rows = []
    open_ended = []
    for p in paths:
        p = Path(p)
        if p.suffix == '.gz' and p.name.endswith('.json.gz'):
            with gzip.open(p, 'rt') as f:
                rows.extend(json.load(f)['rows'])
        else:
            try:
                with gzip.open(p, 'rt') as f:
                    for line in f:
                        rows.append(json.loads(line))
            except EOFError:
                open_ended.append(str(p))
    by = defaultdict(list)
    for x in rows:
        if x.get('kind') != 'books':
            by[x['S']].append(dict(received_ms=x['received_ms'], requested_ms=x['requested_ms'], gap=True))
            continue
        books = {}
        for b in x['books']:
            bids = sorted(((float(y['price']), float(y['size'])) for y in b['bids']), reverse=True)
            asks = sorted((float(y['price']), float(y['size'])) for y in b['asks'])
            books[b['asset_id']] = (bids, asks, int(b['timestamp']))
        by[x['S']].append(dict(received_ms=x['received_ms'], requested_ms=x['requested_ms'], books=books, gap=False))
    for v in by.values():
        v.sort(key=lambda s: s['received_ms'])
    return by, open_ended


def load_prints(trades_dir, slug):
    """Maker-side BUY prints = (takerOnly=false rows) minus (takerOnly=true rows), multiset by key."""
    def rows(mode):
        d = json.load(open(Path(trades_dir)/f'{slug}_taker{mode}.json'))
        return [x for p in d['pages'] for x in p['rows']]
    def key(x):
        return (x['transactionHash'], x['proxyWallet'], x['asset'], x['side'], str(x['size']), str(x['price']), x['timestamp'])
    allc = Counter(map(key, rows('false')))
    tk = Counter(map(key, rows('true')))
    maker = allc-tk
    missing = sum((tk-allc).values())
    if missing:
        # Pages fetched at different times while post-close prints were still arriving; refetch to clear.
        print(f'warning {slug}: {missing} taker rows absent from the all-rows fetch (page drift); maker set may be incomplete', file=sys.stderr)
    out = []
    for k, n in maker.items():
        tx, wallet, asset, side, size, price, ts = k
        if side == 'BUY':
            out.append(dict(ts=ts, token=asset, price=float(price), size=float(size)*n, wallet=wallet))
    out.sort(key=lambda x: x['ts'])
    return out, dict(all_rows=sum(allc.values()), taker_rows=sum(tk.values()), maker_rows=sum(maker.values()),
                     maker_buy_rows=len(out), taker_rows_missing_in_all=missing)


# ---------------- chainlink context for the candidate control ----------------
def chainlink_streams(cld_files):
    records = defaultdict(list)
    for p in cld_files:
        try:
            with gzip.open(p, 'rt') as f:
                for line in f:
                    x = json.loads(line)
                    if x['f'] in ('spot', 'twap60') and x['obs']*1000 <= x['rcv']:
                        records[x['f']].append((x['rcv'], x['obs']*1000, float(x['px'])))
        except EOFError:
            print('open-ended chainlink file (partial read):', p, file=sys.stderr)
    streams, starts = {}, {}
    for name, seq in records.items():
        times, values, last = [], [], -1
        for rcv, obs, px in sorted(set(seq)):
            if obs < last:
                continue
            last = obs
            times.append(rcv)
            values.append((obs, px))
            if name == 'twap60' and obs % 900000 == 0:
                starts.setdefault(obs//1000, (rcv, px))
        streams[name] = (times, values)
    return streams, starts


def context(streams, starts, S, end, now):
    """Replicates R/btc15_context.py exactly (including the S=end-300 mapping) for one decision time."""
    def price(name, when):
        times, values = streams[name]
        i = bisect.bisect_right(times, when*1000)-1
        if i < 0 or not 0 <= when*1000-times[i] <= 3000 or not 0 <= when*1000-values[i][0] <= 3000:
            raise ValueError('stale_or_missing_'+name)
        return values[i][1]
    if S not in starts:
        raise ValueError('no_recorded_reference')
    rcv, ref = starts[S]
    if rcv > now*1000 or not 0 < now-S < 900:
        raise ValueError('reference_or_time_not_available')
    spot, twap = price('spot', now), price('twap60', now)
    hist = [price('spot', now-i*5) for i in range(13)]
    sigma = math.sqrt(sum((a-b)**2 for a, b in zip(hist, hist[1:]))/60)
    if sigma < 1e-8:
        raise ValueError('zero_volatility')
    f = dict(S=S, now=now, ref=ref, reference_received_ms=rcv, spot=spot, twap=twap, sigma=sigma,
             momentum10=(hist[0]-hist[2])/(sigma*math.sqrt(10)), distance=(spot-ref)/(sigma*math.sqrt(900-(now-S))))
    f.update(r.deep.fair_twap(streams, end-300, now*1000, f))
    return f


# ---------------- accounting ----------------
def state():
    return dict(q=[0., 0.], cash=0., lots=[[], []], fills=[], hedges=[], quotes_placed=0, quotes_cancelled=0, fee=0.)


def apply_fill(s, side, qty, unit_cash, when, kind, role):
    s['q'][side] += qty
    s['cash'] += qty*unit_cash
    left = qty
    while left > 1e-9 and s['lots'][1-side]:
        lot = s['lots'][1-side][0]
        take = min(left, lot[0])
        lot[0] -= take
        left -= take
        if lot[0] < 1e-9:
            s['lots'][1-side].pop(0)
    if left > 1e-9:
        s['lots'][side].append([left, unit_cash])
    s['fills'].append(dict(side=side, qty=qty, unit_cash=unit_cash, when=when, kind=kind, role=role))


def within_limits(s, side, qty, unit_cash):
    q = s['q'].copy()
    q[side] += qty
    cash = s['cash']+qty*unit_cash
    return cash <= LIMIT_CASH+1e-9 and abs(q[0]-q[1]) <= LIMIT_NET+1e-9 and cash-min(q) <= LIMIT_WORST+1e-9


# ---------------- passive arms ----------------
def run_passive(snaps, tokens, prints, S, mode, offset_ticks, hedge, market):
    """mode: 'pess' or 'opt'. offset_ticks: 0 (touch) or 1 (touch-1). hedge: bool (P2)."""
    s = state()
    quotes = {}   # side -> dict(price, placed_ms, queue_ahead, consumed)
    pi = 0
    prev_ms = None
    prints = [p for p in prints if p['token'] in tokens]
    tok_side = {tokens[0]: 0, tokens[1]: 1}
    log = []
    for snap in snaps:
        rms = snap['received_ms']
        age = rms/1000-S
        # prints that happened in (prev_ms/1000, rms/1000] (second resolution: ts <= floor(rms/1000))
        upto = int(rms//1000)
        new_prints = []
        while pi < len(prints) and prints[pi]['ts'] <= upto:
            if prev_ms is None or prints[pi]['ts'] > int(prev_ms//1000):
                new_prints.append(prints[pi])
            pi += 1
        if snap['gap']:
            # Unobserved book: quotes are treated as suspended; prints in this interval never fill us.
            for side in list(quotes):
                del quotes[side]
                s['quotes_cancelled'] += 1
            prev_ms = rms
            continue
        # process fills against existing quotes first (prints occurred before this snapshot)
        for p in new_prints:
            side = tok_side[p['token']]
            qd = quotes.get(side)
            if not qd or p['ts']*1000 < qd['placed_ms']:
                continue
            filled = False
            if p['price'] < qd['price']-1e-9:
                filled = True          # traded through our level
            elif abs(p['price']-qd['price']) < 1e-9:
                qd['consumed'] += p['size']
                filled = (mode == 'opt') or qd['consumed'] >= qd['queue_ahead']+QTY-1e-9
            if filled:
                apply_fill(s, side, QTY, qd['price'], p['ts'], 'passive', 'maker')
                log.append(dict(t=p['ts']-S, side=side, price=qd['price'], queue_ahead=qd['queue_ahead'], consumed=qd['consumed']))
                del quotes[side]
        gap = prev_ms is not None and rms-prev_ms > 3000
        prev_ms = rms
        if age < 30 or age > 840:
            for side in list(quotes):
                del quotes[side]
                s['quotes_cancelled'] += 1
            continue
        net = s['q'][0]-s['q'][1]
        # taker hedge (P2): when |net| >= LIMIT_NET, buy reducing side at ask with fee
        if hedge and abs(net) >= LIMIT_NET-1e-9:
            side = 1 if net > 0 else 0
            bids, asks, _ = snap['books'][tokens[side]]
            try:
                cost, fee = r.base.ask_cost(dict(asks=asks), market, abs(net))
                unit = (cost+fee)/abs(net)
                # Risk-reducing completion is allowed past the cash cap (protocol: "continue pre-budgeted
                # risk-reducing completion"); the cash excess is reported via the market cash total.
                apply_fill(s, side, abs(net), unit, rms/1000, 'hedge', 'taker')
                s['fee'] += fee
                s['hedges'].append(dict(t=age, side=side, qty=abs(net), unit=unit, fee=fee,
                                        cash_after=s['cash'], over_cash_cap=s['cash'] > LIMIT_CASH+1e-9))
                net = 0.
            except ValueError:
                pass
        for side in (0, 1):
            bids, asks, ts_ex = snap['books'][tokens[side]]
            valid = bool(bids) and bool(asks) and 0 < asks[0][0]-bids[0][0] <= 0.03+1e-9 and 0 <= rms-ts_ex <= 3000 and not gap
            target = round(bids[0][0]-offset_ticks*TICK, 2) if valid else None
            allowed = valid and target is not None and target > 0 and within_limits(s, side, QTY, target)
            if allowed and abs(net) >= LIMIT_NET-1e-9 and side == (0 if net > 0 else 1):
                allowed = False   # only the reducing side may quote at the net limit
            qd = quotes.get(side)
            if qd and (not allowed or abs(qd['price']-target) > 1e-9):
                del quotes[side]
                s['quotes_cancelled'] += 1
                qd = None
            if not qd and allowed:
                ahead = sum(sz for px, sz in bids if abs(px-target) < 1e-9)
                quotes[side] = dict(price=target, placed_ms=rms, queue_ahead=ahead, consumed=0.)
                s['quotes_placed'] += 1
    s['quotes_open_at_end'] = len(quotes)
    s['fill_log'] = log
    return s


# ---------------- candidate control on real books ----------------
def run_candidate(snaps, tokens, market, S, end, streams, starts):
    s = c.state()
    gaps = Counter()
    times = [x['received_ms'] for x in snaps]
    for age in range(180, 841, 60):
        now = S+age
        i = bisect.bisect_left(times, now*1000)
        if i >= len(snaps) or snaps[i]['gap'] or snaps[i]['received_ms'] > now*1000+1000:
            gaps['decision_book_missing'] += 1
            continue
        snap = snaps[i]
        try:
            f = context(streams, starts, S, end, now)
        except ValueError as e:
            gaps[str(e)] += 1
            continue
        prices = []
        ok = True
        for side in (0, 1):
            bids, asks, ts_ex = snap['books'][tokens[side]]
            if not bids or not asks or not 0 <= snap['received_ms']-ts_ex <= 3000:
                ok = False
                break
            prices.append(asks[0][0])
        if not ok:
            gaps['decision_book_one_sided_or_stale'] += 1
            continue
        intent = c.decide(s, age, prices, f, 'managed', 'discount')
        if intent is None:
            continue
        decision_ms = snap['received_ms']
        j = bisect.bisect_left([x['requested_ms'] for x in snaps], decision_ms+250)
        if j >= len(snaps) or snaps[j]['gap'] or snaps[j]['received_ms'] > decision_ms+3000:
            gaps['execution_book_missing'] += 1
            continue
        ex = snaps[j]
        bids, asks, ts_ex = ex['books'][tokens[intent['side']]]
        book = dict(asset_id=tokens[intent['side']], requested_ms=ex['requested_ms'], received_ms=ex['received_ms'],
                    observed_ms=ts_ex, bid=bids[0][0] if bids else 0., asks=asks)
        try:
            if not c.apply_book(s, intent, book, market, decision_ms, f, 'managed'):
                gaps['execution_rejected_'+intent['kind']] += 1
        except ValueError as e:
            gaps['execution_invalid_'+str(e).replace(' ', '_')] += 1
    return s, dict(gaps)


def settle(q, cash, winner):
    return q[winner]-cash


def summarize(results, name):
    vals = [x['pnl'] for x in results]
    tot = sum(vals)
    return dict(arm=name, markets=len(results), traded=sum(1 for x in results if x['fills']), fills=sum(x['fills'] for x in results),
                pnl=round(tot, 4), ex_top3=round(tot-sum(sorted(vals, reverse=True)[:3]), 4),
                worst_market=round(min(vals), 4) if vals else None, cash=round(sum(x['cash'] for x in results), 4),
                rebate_upper=round(sum(x['rebate'] for x in results), 4), taker_fee=round(sum(x['fee'] for x in results), 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tape', nargs='+', required=True)
    ap.add_argument('--markets', required=True)
    ap.add_argument('--trades', required=True)
    ap.add_argument('--cld', nargs='*', default=[])
    ap.add_argument('--out', required=True)
    ap.add_argument('--only-full', action='store_true', help='markets whose S>=first snapshot and end<=last snapshot')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tape, open_ended = load_tape(a.tape)
    first_ms = min(v[0]['received_ms'] for v in tape.values())
    last_ms = max(v[-1]['received_ms'] for v in tape.values())
    streams, starts = chainlink_streams(a.cld) if a.cld else ({}, {})
    per_market, arms = [], defaultdict(list)
    for S in sorted(tape):
        slug = f'btc-updown-15m-{S}'
        mp = Path(a.markets)/(slug+'.json')
        if not mp.exists():
            per_market.append(dict(slug=slug, skipped='no_market_metadata'))
            continue
        m = json.load(open(mp))
        m = m.get('data', m)
        meta = r.classify(m)
        assert meta['group'] == 'btc_15m' and meta['S'] == S
        tokens = json.loads(m['clobTokenIds'])
        full = S*1000 >= first_ms and meta['end']*1000 <= last_ms
        try:
            winner = r.base.outcome(m)
        except ValueError:
            winner = None
        if a.only_full and not full:
            per_market.append(dict(slug=slug, skipped='partial_coverage', full=full))
            continue
        if winner is None:
            per_market.append(dict(slug=slug, skipped='unresolved'))
            continue
        tp = Path(a.trades)/f'{slug}_takerfalse.json'
        if not tp.exists():
            per_market.append(dict(slug=slug, skipped='no_public_prints'))
            continue
        prints, pstats = load_prints(a.trades, slug)
        snaps = tape[S]
        row = dict(slug=slug, S=S, winner=winner, snapshots=len(snaps), prints=pstats, full=full, arms={})
        for name, mode, off, hedge in (('P1a_touch_pess', 'pess', 0, False), ('P1a_touch_opt', 'opt', 0, False),
                                       ('P1b_touch1_pess', 'pess', 1, False), ('P1b_touch1_opt', 'opt', 1, False),
                                       ('P2_touch_hedge_pess', 'pess', 0, True), ('P2_touch_hedge_opt', 'opt', 0, True)):
            s = run_passive(snaps, tokens, prints, S, mode, off, hedge, m)
            pnl = settle(s['q'], s['cash'], winner)
            rebate = 0.2*0.07*sum(f['qty']*f['unit_cash']*(1-f['unit_cash']) for f in s['fills'] if f['role'] == 'maker')
            res = dict(pnl=pnl, fills=len(s['fills']), maker_fills=sum(f['role'] == 'maker' for f in s['fills']),
                       hedges=len(s['hedges']), q=s['q'], cash=s['cash'], worst=min(s['q'])-s['cash'], fee=s['fee'], rebate=rebate,
                       quotes_placed=s['quotes_placed'], quotes_cancelled=s['quotes_cancelled'], fill_log=s['fill_log'], hedge_log=s['hedges'])
            row['arms'][name] = res
            arms[name].append(dict(slug=slug, **{k: res[k] for k in ('pnl', 'fills', 'cash', 'fee', 'rebate')}))
        if streams:
            s, gaps = run_candidate(snaps, tokens, m, S, meta['end'], streams, starts)
            pnl = settle(s['q'], s['cash'], winner)
            res = dict(pnl=pnl, fills=len(s['events']), q=s['q'], cash=s['cash'], gaps=gaps, events=s['events'], fee=0., rebate=0.)
            row['arms']['P0_candidate_real_books'] = res
            arms['P0_candidate_real_books'].append(dict(slug=slug, pnl=pnl, fills=len(s['events']), cash=s['cash'], fee=0., rebate=0.))
        per_market.append(row)
    summary = {name: summarize(v, name) for name, v in arms.items()}
    json.dump(dict(first_ms=first_ms, last_ms=last_ms, open_ended_files=open_ended, summary=summary, markets=per_market,
                   note='Bounded queue replay; PESS=no cancels ahead, OPT=first in queue. Not an executed result. Rebate is an upper-bound line, not in pnl.'),
              open(out/'replay.json', 'w'), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
