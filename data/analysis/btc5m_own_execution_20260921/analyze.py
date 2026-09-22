"""Audit calibration identifiability; public fill times are not cancel timestamps."""
from collections import Counter, defaultdict
from decimal import Decimal
from hashlib import sha256
from itertools import groupby
from pathlib import Path
import gzip
import importlib.util
import json
import statistics

from prepare import orders_from, write

OUT=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('m1',OUT.parent/'btc5m_maker_feasibility_20260921/replay.py')
m1=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1)


def read(name):
    return json.loads((OUT/name).read_text())


def stats(values):
    values=sorted(values)
    return dict(n=len(values),min=values[0],median=statistics.median(values),
                p95=values[int(.95*(len(values)-1))],max=values[-1]) if values else dict(n=0)


def book_context(order,events):
    when=order['intent_ms']-100
    books,issues=m1.books_at(events,order['tokens'],[when])
    pair=books[when]
    reasons=[]
    for b in pair:
        if not b['ready'] or not 0<=when-b['rcv']<=3000 or not 0<=when-b['obs']<=3000:
            reasons.append('missing_or_stale_book')
    if issues:
        reasons.extend(issues)
    px=m1.units(order['price'])
    own,other=pair[order['oi']],pair[1-order['oi']]
    ahead=own['BUY'].get(px,0)
    mirror=other['SELL'].get(m1.UNIT-px,0)
    if ahead!=mirror:
        reasons.append('quote_depth_mirror_mismatch')
    return dict(oid=order['oid'],lane=order['lane'],status='missing' if reasons else 'valid',
        reasons=sorted(set(reasons)),when=when,ahead=ahead/m1.UNIT,mirror=mirror/m1.UNIT,
        actual_filled=order['actual_filled'],price=order['price'],
        bid=max(own['BUY'])/m1.UNIT if own['BUY'] else None,
        ask=min(own['SELL'])/m1.UNIT if own['SELL'] else None)


def main():
    for name,digest in read('input_manifest.json').items():
        assert sha256((OUT/name).read_bytes()).hexdigest()==digest
    fetch=read('fetch_manifest.json')
    for name,digest in fetch['files'].items():
        assert sha256((OUT/name).read_bytes()).hexdigest()==digest
    snapshot=json.load(gzip.open(OUT/'snapshot.json.gz','rt'))
    orders=orders_from(snapshot)
    assert orders==read('orders.json')
    by_order={r['oid']:r for r in orders}
    wallet=read('public_wallet.json')['address']
    markets=read('markets.json')
    activity=[]
    for start,market in markets.items():
        record=read('full_activity/'+start+'.json')
        assert record['complete']
        assert all(r['conditionId']==market['conditionId'] and r['proxyWallet'].lower()==wallet for r in record['rows'])
        activity.extend(r for r in record['rows'] if r['type']=='TRADE')
    receipts={}
    fills=[]
    groups={}
    api_reconciled=[]
    for tx in sorted({r['transactionHash'] for r in activity}):
        receipt=read('receipts/'+tx+'.json')
        receipts[tx]=receipt
        decoded=m1.probe.decode(receipt,wallet)
        fills.extend(decoded)
        groups[tx]=m1.matches(receipt)
        public=[r for r in activity if r['transactionHash']==tx]
        for token in {r['asset'] for r in public}|{f['token'] for f in decoded}:
            api=[r for r in public if r['asset']==token]
            chain=[f for f in decoded if f['token']==token]
            assert all(r['side']=='BUY' for r in api) and all(f['side']==0 for f in chain)
            assert abs(sum(Decimal(str(r['size'])) for r in api)-sum(f['qty'] for f in chain)/Decimal(m1.UNIT))<=Decimal('.000001')
            assert abs(sum(Decimal(str(r['usdcSize'])) for r in api)-sum(f['cash_cost'] for f in chain)/Decimal(m1.UNIT))<=Decimal('.00001')
        api_reconciled.append(tx)
    actual=defaultdict(list)
    for fill in fills:
        actual[fill['order_hash']].append(fill)
    assert not (set(actual)-set(by_order)), 'unattributed own order'
    checks=[]
    for order in orders:
        chain=actual[order['oid']]
        quantity=sum(f['qty'] for f in chain)
        cash=sum(f['cash_cost'] for f in chain)
        assert all(f['token']==order['token'] and f['side']==0 for f in chain)
        assert abs(Decimal(str(order['actual_filled']))*m1.UNIT-quantity)<=1
        assert abs(Decimal(str(order['price']))*quantity-cash)<=max(2,len(chain)*2)
        checks.append(dict(oid=order['oid'],qty_units=quantity,cash_units=cash,chain_fills=len(chain)))
    events=defaultdict(list)
    for line in gzip.open(OUT/'trades.jsonl.gz','rt'):
        e=json.loads(line)
        if e['p'].get('transaction_hash') in groups:
            events[e['S']].append(e)
    flows=[]
    flow_errors={}
    for start,evs in events.items():
        found,errors,_=m1.trade_flows(evs,groups,markets[str(start)]['tokens'])
        flows.extend(found)
        if errors:
            flow_errors[str(start)]=errors
    flow_ids={(f['tx'],f['log_index']):f for f in flows}
    assert len(flow_ids)==len(flows)
    timings=[]
    for fill in fills:
        order=by_order[fill['order_hash']]
        flow=flow_ids.get((fill['tx'],fill['log_index']))
        if flow is None:
            timings.append(dict(oid=order['oid'],tx=fill['tx'],log_index=fill['log_index'],status='missing_ws_match'))
            continue
        assert fill['role']=='maker' and flow['side']==order['oi']
        # Ratios amplify micro-cash rounding in tiny partial fills; check money.
        assert abs(Decimal(str(order['price']))*fill['qty']-fill['cash_cost'])<=2
        assert abs(flow['qty']-fill['qty']/m1.UNIT)<=.000001
        # Public source time, not a new authenticated execution timestamp.
        t=flow['obs_hi']
        reasons=[]
        if flow['obs_lo']!=t:
            reasons.append('nonunique_ws_clock')
        if flow['min_delay']<0 or flow['max_delay']>1000:
            reasons.append('ws_receipt_clock')
        if t<order['intent_ms']-100:
            reasons.append('execution_before_intent_clock')
        complete_clock=all((f['tx'],f['log_index']) in flow_ids for f in actual[order['oid']])
        observation=next((x['ms'] for x in order['observed_fills']
                          if sum(y['q'] for y in order['observed_fills'] if y['ms']<=x['ms'])+1e-6 >=
                          sum(f['qty']/m1.UNIT for f in actual[order['oid']]
                              if (z:=flow_ids.get((f['tx'],f['log_index']))) is not None and z['obs_hi']<=t)),None) if complete_clock else None
        if observation is not None and observation<t-100:
            reasons.append('execution_after_discovery_clock')
        timings.append(dict(oid=order['oid'],lane=order['lane'],tx=fill['tx'],log_index=fill['log_index'],
            status='uncertain' if reasons else 'matched',reasons=reasons,qty=fill['qty']/m1.UNIT,
            ws_source_ms=t,ws_received_ms=flow['received'],after_intent_ms=t-order['intent_ms'],
            after_ack_ms=t-order['ack_ms'],discovery_lag_ms=observation-t if observation is not None else None))
    books=[]
    with gzip.open(OUT/'books.jsonl.gz','rt') as stream:
        for oid,rows in groupby(map(json.loads,stream),key=lambda r:r['oid']):
            books.append(book_context(by_order[oid],list(rows)))
    matched=[r for r in timings if r['status']=='matched']
    lanes={}
    for lane in 'DEF':
        sample=[o for o in orders if o['lane']==lane]
        clock=[r for r in matched if r['lane']==lane]
        lanes[lane]=dict(accepted=len(sample),filled_orders=sum(o['actual_filled']>0 for o in sample),
            unfilled_orders=sum(o['actual_filled']==0 for o in sample),shares=sum(o['actual_filled'] for o in sample),
            intent_to_ack_ms=stats([o['ack_ms']-o['intent_ms'] for o in sample]),
            terminal_upper_age_ms=stats([o['terminal_upper']['ms']-o['ack_ms'] for o in sample if o['terminal_upper']]),
            execution_after_intent_ms=stats([r['after_intent_ms'] for r in clock]),
            fill_discovery_lag_ms=stats([r['discovery_lag_ms'] for r in clock if r['discovery_lag_ms'] is not None]))
    london_d_start=next(e['utc_ms'] for e in snapshot['D']['events']
                        if e['k']=='SURUM' and e['kaynak_sha']=='1c29c157c576')
    d_sites={site:stats([o['ack_ms']-o['intent_ms'] for o in orders if o['lane']=='D'
                        and (o['ack_ms']<london_d_start)==local]) for site,local in [('Turkey',True),('London',False)]}
    result=dict(status='NOT_CALIBRATED_MISSING_CANCEL_CLOCKS',lanes=lanes,d_site_intent_to_ack_ms=d_sites,
        accepted_orders=len(orders),filled_orders=sum(o['actual_filled']>0 for o in orders),
        exact_cancel_pairs=sum(o['cancel_request_ms'] is not None and o['cancel_response_ms'] is not None for o in orders),
        confusion_matrix=None,full_lifetime_prediction=None,
        public_markets=len(markets),public_trade_rows=len(activity),receipts=len(receipts),chain_fills=len(fills),
        reconciled_transactions=len(api_reconciled),roles=dict(Counter(f['role'] for f in fills)),
        chain_units=sum(f['qty'] for f in fills),chain_cash_units=sum(f['cash_cost'] for f in fills),
        ws_status=dict(Counter(r['status'] for r in timings)),ws_matched_units=sum(m1.units(r['qty']) for r in matched),
        first_250ms_records=sum(r['after_intent_ms']<250 for r in matched),
        first_250ms_with_100ms_guard=sum(r['after_intent_ms']<150 for r in matched),
        before_ack_records=sum(r['after_ack_ms']<0 for r in matched),
        beyond_M1_1150ms_records=sum(r['after_intent_ms']>1150 for r in matched),
        beyond_1250ms_records=sum(r['after_intent_ms']>1250 for r in matched),
        public_clock_errors=flow_errors,timings=timings,order_reconciliation=checks,
        pre_submission_books=books,book_status=dict(Counter(r['status'] for r in books)),
        source_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.py')},
        reuse_sha256={str(p.relative_to(OUT.parent)):sha256(p.read_bytes()).hexdigest() for p in (
            OUT.parent/'btc5m_maker_feasibility_20260921/replay.py',OUT.parent/'btc5m_order_identity_20260921/check.py')})
    write('report.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('timings','order_reconciliation','pre_submission_books','source_sha256','reuse_sha256')},indent=2))


if __name__=='__main__':
    main()
