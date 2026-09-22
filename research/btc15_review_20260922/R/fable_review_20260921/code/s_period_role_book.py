#!/usr/bin/env python3
"""S-period (frozen 14:25-18:05 UTC) Bosona BTC15m fills: fee-signature role vs real L2 book.

Read-only. Uses S/raw/book_validation_prefix.json.gz and S/raw/new_period_full/*.json.
For each fill: role from fee signature; book at t-1s/t-5s (last snapshot received before);
best bid/ask on the fill token; size resting at fill price on bid side; whether fill price
is at/below best bid (consistent with passive fill) or at/above best ask (taker).
"""
import gzip
import json
import bisect
from collections import Counter, defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from role_classifier import role  # noqa: E402

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
S = R/'btc15_followup/status_20260921_1800'
OUT = R/'fable_review_20260921/results'
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with gzip.open(S/'raw/book_validation_prefix.json.gz', 'rt') as f:
        tape = json.load(f)['rows']
    books = defaultdict(list)
    for x in tape:
        if x['kind'] == 'books':
            books[x['S']].append(x)
    for v in books.values():
        v.sort(key=lambda x: x['received_ms'])
    rows = []
    for mf in sorted((S/'raw/new_period_markets').glob('*.json')):
        m = json.load(open(mf))['data']
        slug = m['slug']
        s = int(slug.rsplit('-', 1)[1])
        tokens = json.loads(m['clobTokenIds'])
        winner = None
        try:
            pr = list(map(float, json.loads(m['outcomePrices'])))
            if m.get('closed') and sorted(pr) == [0., 1.]:
                winner = pr.index(1.)
        except Exception:
            pass
        acts = []
        for p in sorted((S/'raw/new_period_full').glob(slug+'_*.json')):
            acts.extend(json.load(open(p))['data'])
        trades = [a for a in acts if a['type'] == 'TRADE']
        bl = books.get(s, [])
        times = [b['received_ms'] for b in bl]
        for a in sorted(trades, key=lambda a: (a['timestamp'], a['transactionHash'])):
            q = float(a['size'])
            p = float(a['price'])
            cp = float(a['usdcSize'])/q
            side = a['outcomeIndex']
            tok = tokens[side]
            assert a['asset'] == tok
            r = dict(slug=slug, S=s, ts=a['timestamp'], age=a['timestamp']-s, side=side, price=p,
                     cash_price=cp, qty=q, role=role(p, cp, q), tx=a['transactionHash'],
                     winner=winner, pnl=None if winner is None else q*(side == winner)-float(a['usdcSize']))
            for lag in (1, 5):
                before = a['timestamp']*1000-lag*1000
                i = bisect.bisect_right(times, before)-1
                if i < 0:
                    r[f'b{lag}'] = None
                    continue
                ev = bl[i]
                b = next(x for x in ev['books'] if x['asset_id'] == tok)
                bids = sorted(((float(x['price']), float(x['size'])) for x in b['bids']), reverse=True)
                asks = sorted((float(x['price']), float(x['size'])) for x in b['asks'])
                bid_at = sum(sz for px, sz in bids if abs(px-p) < 1e-9)
                ask_at = sum(sz for px, sz in asks if abs(px-p) < 1e-9)
                r[f'b{lag}'] = dict(age_ms=before-ev['received_ms'], best_bid=bids[0][0] if bids else None,
                                   best_ask=asks[0][0] if asks else None, bid_size_at_price=bid_at,
                                   ask_size_at_price=ask_at,
                                   depth_bid_ge_price=sum(sz for px, sz in bids if px >= p-1e-9))
            # after-fill book: first snapshot received >= ts*1000+1000
            j = bisect.bisect_left(times, a['timestamp']*1000+1000)
            if j < len(bl):
                ev = bl[j]
                b = next(x for x in ev['books'] if x['asset_id'] == tok)
                r['after1_bid_size_at_price'] = sum(float(x['size']) for x in b['bids'] if abs(float(x['price'])-p) < 1e-9)
            rows.append(r)
    json.dump(rows, open(OUT/'s_period_fills_role_book.json', 'w'), ensure_ascii=False, indent=0)
    roles = Counter(r['role'] for r in rows)
    print('fills', len(rows), 'roles', dict(roles))
    for rl in ('maker', 'taker'):
        rr = [r for r in rows if r['role'] == rl and r['b1']]
        le_bid = sum(r['b1']['best_bid'] is not None and r['price'] <= r['b1']['best_bid']+1e-9 for r in rr)
        eq_bid = sum(r['b1']['best_bid'] is not None and abs(r['price']-r['b1']['best_bid']) < 1e-9 for r in rr)
        ge_ask = sum(r['b1']['best_ask'] is not None and r['price'] >= r['b1']['best_ask']-1e-9 for r in rr)
        bidsz = sum(r['b1']['bid_size_at_price'] >= r['qty']-1e-6 for r in rr)
        print(f'{rl}: n={len(rr)} price<=best_bid(t-1)={le_bid} ==best_bid={eq_bid} price>=best_ask(t-1)={ge_ask} bid_size_at_price>=qty={bidsz}')
        # distribution of price - best_bid
        d = Counter(round(r['price']-r['b1']['best_bid'], 2) for r in rr if r['b1']['best_bid'] is not None)
        print('  price-best_bid dist:', sorted(d.items())[:12])
        d = Counter(round(r['price']-r['b1']['best_ask'], 2) for r in rr if r['b1']['best_ask'] is not None)
        print('  price-best_ask dist:', sorted(d.items())[:12])
    late = [r for r in rows if 600 <= r['age'] < 900 and r['winner'] is not None]
    print('late(600+) fills', len(late), 'roles', Counter(r['role'] for r in late),
          'pnl by role', {k: round(sum(r['pnl'] for r in late if r['role'] == k), 2) for k in ('maker', 'taker')})
    for r in rows:
        if r['role'] == 'other':
            print('OTHER', r['slug'], r['ts'], r['price'], r['cash_price'], r['qty'])


if __name__ == '__main__':
    main()
