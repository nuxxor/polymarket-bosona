#!/usr/bin/env python3
"""Read only the independent recorder; distinguish real book coverage from tradability."""
from collections import Counter
import gzip
import json
from pathlib import Path
import statistics as st
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import research as r  # noqa: E402
import record_books  # noqa: E402


def inspect():
    here=Path(__file__).resolve().parent
    root=here/'raw/books_72h'
    prefix=here/'raw/book_validation_prefix.json.gz'
    if prefix.exists():
        with gzip.open(prefix,'rt') as stream:
            capture=json.load(stream)
        rows,status,open_gzip=capture['rows'],capture['status'],capture['open_gzip']
        files=[]
    else:
        status=r.read(root/'status.json')
        rows=[]
        files=sorted(root.glob('books_*.jsonl.gz'))
    captured=prefix.exists()
    if not captured:
        open_gzip=0
    for p in files:
        try:
            with gzip.open(p,'rt') as stream:
                for line in stream:
                    rows.append(json.loads(line))
        except EOFError:
            if not (p==files[-1] and status['running']):
                raise
            open_gzip+=1
    if not captured:
        with gzip.open(prefix,'xt') as stream:
            json.dump(dict(rows=rows,status=status,open_gzip=open_gzip),stream,separators=(',',':'))
    good=[x for x in rows if x['kind']=='books']
    counts=Counter()
    by=Counter()
    spreads=[]
    fees=[]
    markets={p.stem:r.read(p) for p in (root/'markets').glob('*.json')}
    for x in good:
        slug=f'btc-updown-15m-{x["S"]}'
        m=markets[slug]
        assert r.classify(m)['group']=='btc_15m'
        record_books.validate(x['books'],json.loads(m['clobTokenIds']),m['conditionId'])
        assert x['requested_ms']<=x['received_ms']
        by[slug]+=1
        for book in x['books']:
            age=x['received_ms']-int(book['timestamp'])
            counts['book_sides']+=1
            counts['exchange_age_valid']+=0<=age<=3000
            asks=sorted((float(y['price']),float(y['size'])) for y in book['asks'])
            bids=sorted((float(y['price']),float(y['size'])) for y in book['bids'])
            if not asks or not bids:
                counts['one_sided_or_empty']+=1
                continue
            spread=asks[0][0]-bids[-1][0]
            spreads.append(spread)
            if not 0<spread<=.0300000001 or not 0<=age<=3000:
                counts['wide_crossed_or_stale']+=1
                continue
            try:
                cash,fee=r.base.ask_cost(dict(asks=asks),m,5.)
                fees.append(fee)
                counts['five_share_depth_spread_fresh_valid']+=1
                assert cash>0 and fee>=0
            except ValueError:
                counts['insufficient_depth_or_fee']+=1
    times=[x['received_ms'] for x in rows]
    gaps=[(b-a)/1000 for a,b in zip(times,times[1:])]
    result=dict(asof_ms=times[-1],first_ms=times[0],rows=len(rows),snapshots=len(good),errors=len(rows)-len(good),
        markets=dict(by),counts=dict(counts),median_spread=st.median(spreads),max_interrecord_seconds=max(gaps),
        median_interval_seconds=st.median(gaps),median_five_share_fee=st.median(fees),open_gzip_members=open_gzip,
        planned=r.read(root/'run.json'),status=status,notes='All levels saved. REST sampled, not a WebSocket event tape. '
        'Book timestamp freshness is measured, never inferred from receipt. Partial starting contract excluded from future full-window evaluation.')
    r.save(here/'results/book_quality.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    inspect()
