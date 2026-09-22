#!/usr/bin/env python3
"""Level presence before Bosona fills in the frozen S-period tape (1s REST snapshots).

Public activity timestamps are block times, ~2-3s after the exchange match, so the book at
public_ts-1 may already be post-fill. We therefore scan lags 1..10s before the public timestamp for the
first snapshot where a bid level at the fill price with size >= fill qty exists, then measure how long that
level was continuously present (lower bound of order age, 1s resolution)."""
import bisect
import glob
import gzip
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
S = R/'btc15_followup/status_20260921_1800'
OUT = R/'fable_review_20260921/results'


def main():
    tape = json.load(gzip.open(S/'raw/book_validation_prefix.json.gz', 'rt'))['rows']
    books = defaultdict(list)
    for x in tape:
        if x['kind'] == 'books':
            books[x['S']].append(x)
    for v in books.values():
        v.sort(key=lambda x: x['received_ms'])
    rows = json.load(open(OUT/'s_period_fills_role_book.json'))
    mk = {}
    for mf in glob.glob(str(S/'raw/new_period_markets/*.json')):
        m = json.load(open(mf))['data']
        mk[int(m['slug'].rsplit('-', 1)[1])] = json.loads(m['clobTokenIds'])

    def lvl(ev, tok, p):
        b = next(x for x in ev['books'] if x['asset_id'] == tok)
        return sum(float(y['size']) for y in b['bids'] if abs(float(y['price'])-p) < 1e-9)

    def bestbid(ev, tok):
        b = next(x for x in ev['books'] if x['asset_id'] == tok)
        bb = [float(y['price']) for y in b['bids']]
        return max(bb) if bb else None
    out = []
    for r in rows:
        bl = books[r['S']]
        times = [b['received_ms'] for b in bl]
        tok = mk[r['S']][r['side']]
        prof = []
        for lag in range(0, 11):
            i = bisect.bisect_right(times, r['ts']*1000-lag*1000)-1
            prof.append(lvl(bl[i], tok, r['price']) if i >= 0 else None)
        present = [lag for lag in range(1, 11) if prof[lag] is not None and prof[lag] >= r['qty']-1e-6]
        first_present = min(present) if present else None
        age = None
        if first_present is not None:
            i = bisect.bisect_right(times, r['ts']*1000-first_present*1000)-1
            j = i
            age = 0
            while j >= 0 and lvl(bl[j], tok, r['price']) >= r['qty']-1e-6:
                age = (bl[i]['received_ms']-bl[j]['received_ms'])/1000+1
                j -= 1
        i3 = bisect.bisect_right(times, r['ts']*1000-3000)-1
        out.append(dict(slug=r['slug'], ts=r['ts'], age=r['age'], role=r['role'], price=r['price'], qty=r['qty'], profile=prof,
                        first_present_lag=first_present, level_age_from_presence=age, best_bid_t3=bestbid(bl[i3], tok) if i3 >= 0 else None))
    json.dump(out, open(OUT/'s_period_level_age.json', 'w'), indent=0)
    summary = {}
    for role in ('maker', 'taker'):
        rr = [x for x in out if x['role'] == role]
        ages = [x['level_age_from_presence'] for x in rr if x['level_age_from_presence'] is not None]
        summary[role] = dict(n=len(rr), first_present_lag=dict(sorted(Counter(str(x['first_present_lag']) for x in rr).items())),
                             never_present_1_10s=sum(x['first_present_lag'] is None for x in rr),
                             level_age_median=st.median(ages) if ages else None, level_age_p75=sorted(ages)[3*len(ages)//4] if ages else None,
                             level_age_ge5=sum(a >= 5 for a in ages), level_age_ge30=sum(a >= 30 for a in ages),
                             price_eq_best_bid_t3=sum(x['best_bid_t3'] is not None and abs(x['best_bid_t3']-x['price']) < 1e-9 for x in rr),
                             price_le_best_bid_t3=sum(x['best_bid_t3'] is not None and x['price'] <= x['best_bid_t3']+1e-9 for x in rr),
                             presence_share_by_lag=[round(sum(1 for x in rr if x['profile'][k] is not None and x['profile'][k] >= x['qty']-1e-6)/len(rr), 3) for k in range(11)])
    json.dump(summary, open(OUT/'s_period_level_age_summary.json', 'w'), indent=1)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
