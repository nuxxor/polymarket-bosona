#!/usr/bin/env python3
"""Observe new actor fills against independently recorded books; no policy changes."""
import argparse
import bisect
import gzip
import json
from pathlib import Path

import audit

HERE=Path(__file__).resolve().parent
r=audit.r


def run():
    quality=r.read(HERE/'results/book_quality.json')
    with gzip.open(HERE/'raw/book_validation_prefix.json.gz','rt') as stream:
        tape=json.load(stream)['rows']
    result=[]
    for slug in quality['markets']:
        m=audit.cached('new_period_markets/'+slug+'.json','https://gamma-api.polymarket.com/markets/slug/'+slug)
        meta=r.classify(m)
        assert meta['group']=='btc_15m'
        all_rows=audit.activity('new_period_full/'+slug,r.base.WALLET,market=m['conditionId'],start=meta['S'],end=quality['asof_ms']//1000)
        fills=[x for x in all_rows if x['type']=='TRADE']
        try:
            winner=r.base.outcome(m)
        except ValueError:
            winner=None
        ledger,_=r.base.ledger(fills,0 if winner is None else winner)
        books=[x for x in tape if x['kind']=='books' and x['S']==meta['S']]
        times=[x['received_ms'] for x in books]
        tokens=json.loads(m['clobTokenIds'])
        for f in ledger:
            if f['ts']*1000<quality['first_ms']:
                continue
            row={k:f[k] for k in ('ts','side','price','cash_price','qty','age','pre_net','pre_unmatched_cash_cost','opening_kind','completion_qty','opening_qty')}
            row.update(slug=slug,first_second=f['ts']==ledger[0]['ts'],winner=winner,pnl=None if winner is None else f['qty']*(f['side']==winner)-f['qty']*f['cash_price'])
            for lag in (5,10):
                before=f['ts']*1000-lag*1000
                i=bisect.bisect_right(times,before)-1
                if i<0:
                    row[f'book_{lag}']=dict(missing='recording started later')
                    continue
                event=books[i]
                b=next(x for x in event['books'] if x['asset_id']==tokens[f['side']])
                asks=sorted((float(x['price']),float(x['size'])) for x in b['asks'])
                bids=sorted((float(x['price']),float(x['size'])) for x in b['bids'])
                quote=dict(received_ms=event['received_ms'],observed_ms=int(b['timestamp']),
                    bid=bids[-1][0] if bids else None,ask=asks[0][0] if asks else None,
                    receipt_age_ms=before-event['received_ms'],exchange_age_ms=before-int(b['timestamp']))
                assert quote['received_ms']<=before and quote['observed_ms']<=before
                if not 0<=quote['exchange_age_ms']<=3000:
                    quote['missing']='stale'
                else:
                    try:
                        cost,fee=r.base.ask_cost(dict(asks=asks),m,f['qty'])
                        quote.update(allin_unit_cost_for_actual_qty=(cost+fee)/f['qty'],fee=fee)
                    except ValueError:
                        quote['missing']='insufficient ask depth'
                row[f'book_{lag}']=quote
            result.append(row)
    r.save(HERE/'results/new_period_rows.json',result)
    report=dict(rows=len(result),late_adds=sum(x['opening_kind']=='add' and x['age']>=600 for x in result),
        completion_rows=sum(x['completion_qty']>0 for x in result),resolved_rows=sum(x['winner'] is not None for x in result),
        fresh5=sum('allin_unit_cost_for_actual_qty' in x['book_5'] for x in result),
        note='One short new recording period; no threshold chosen from these rows. Actual size book quote is descriptive, not an order fill guarantee.')
    r.save(HERE/'results/new_period_summary.json',report)
    print(json.dumps(report))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true')
    audit.OFFLINE=parser.parse_args().offline
    run()
