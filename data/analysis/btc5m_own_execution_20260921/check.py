"""Small executable checks for lifecycle, exact cash, missing clocks and actual data."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import gzip
import json

from analyze import book_context, m1, stats
from flow_probe import eligible
from prepare import orders_from

OUT=Path(__file__).resolve().parent


def rejects(function):
    try:
        function()
    except (AssertionError,ValueError):
        return
    raise AssertionError('invalid evidence accepted')


def main():
    snapshot=json.load(gzip.open(OUT/'snapshot.json.gz','rt'))
    orders=orders_from(snapshot)
    assert len(orders)==624 and sum(o['actual_filled']==0 for o in orders)==454
    # Duplicate inherited windows do not become duplicate orders. Missing intent
    # or extra acceptance must fail, rather than silently selecting another time.
    bad=deepcopy(snapshot)
    accept=next(e for e in bad['D']['events'] if e['k']=='taze_koy')
    bad['D']['events'].append(accept)
    rejects(lambda:orders_from(bad))
    bad=deepcopy(snapshot)
    first=orders[0]
    bad['D']['events']=[e for e in bad['D']['events'] if not(e['k']=='D_NIYET' and e['utc_ms']==first['intent_ms'])]
    rejects(lambda:orders_from(bad))
    assert all(o['cancel_request_ms'] is None and o['cancel_response_ms'] is None for o in orders)
    assert stats([1,2,100])==dict(n=3,min=1,median=2,p95=2,max=100)
    # Integer cash rounding in the real 0.022728-share partial at a .56 limit.
    assert eligible(dict(price=12728/22728,qty=.022728),.56)
    assert not eligible(dict(price=.561,qty=5),.56)
    assert eligible(dict(price=.55,qty=5),.56)
    assert m1.queue_fill(100,5,104)==(0,4)
    assert m1.queue_fill(100,5,99)==(1,0)
    # A received future book cannot influence the pre-intent snapshot.
    fake=dict(oid='o',lane='D',tokens=['u','d'],oi=0,price=.4,quantity=5,
              actual_filled=0,intent_ms=2000)
    events=[dict(k='book',rcv=1800,p=dict(asset_id=t,timestamp='1790',
        bids=[dict(price=b,size='10')],asks=[dict(price=a,size='10')]))
        for t,b,a in [('u','.4','.41'),('d','.59','.6')]]
    before=book_context(fake,events)
    assert before['status']=='valid' and before['ahead']==10
    events.append(dict(k='price_change',rcv=2001,p=dict(timestamp='2000',
        price_changes=[dict(asset_id='u',side='BUY',price='.4',size='999')])) )
    assert book_context(fake,events)==before
    stale={**fake,'intent_ms':6000}
    assert book_context(stale,events)['status']=='missing'
    report=json.loads((OUT/'report.json').read_text())
    assert report['confusion_matrix'] is None and report['full_lifetime_prediction'] is None
    assert report['exact_cancel_pairs']==0 and report['reconciled_transactions']==203
    assert report['chain_units']==sum(m1.units(o['actual_filled']) for o in orders)==840474039
    assert report['roles']=={'maker':203}
    assert sum(report['ws_status'].values())==report['chain_fills']==203
    assert len(report['pre_submission_books'])==36 and report['book_status']=={'valid':36}
    assert len({r['oid'] for r in report['order_reconciliation']})==624
    for row in report['order_reconciliation']:
        o=next(o for o in orders if o['oid']==row['oid'])
        assert abs(Decimal(str(o['price']))*row['qty_units']-row['cash_units'])<=max(2,row['chain_fills']*2)
    flow=json.loads((OUT/'flow_probe/report.json').read_text())
    assert len(flow['rows'])==flow['assigned']==14
    for row in flow['rows']:
        assert abs(sum(Decimal(str(f['qty'])) for f in row['backing'])-Decimal(str(row['eligible_flow'])))<Decimal('.000001')
        if row['predicted'] is not None:
            expected=min(Decimal(5),max(Decimal(0),Decimal(str(row['eligible_flow']))-Decimal(str(row['ahead']))))
            assert abs(expected-Decimal(str(row['predicted'])))<Decimal('.000001')
    print('PASS: lifecycle, duplicate/missing intent rejection, causal books, money rounding, real receipts and diagnostic replay')


if __name__=='__main__':
    main()
