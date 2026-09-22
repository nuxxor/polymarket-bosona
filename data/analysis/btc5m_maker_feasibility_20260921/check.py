"""Small deterministic checks for the actual money, clock and queue paths."""
from copy import deepcopy
from hashlib import sha256
import json

import replay as r


def main():
    assert r.queue_fill(10,5,8)==(2,0)
    assert r.queue_fill(10,5,12)==(0,2)
    assert r.queue_fill(10,5,30)==(0,5)
    assert r.queue_fill(0,5,2)==(0,2)
    config=r.read(r.OUT/'protocol_v2.json')
    start,age=1000,120
    now=(start+age)*1000
    def event(kind,payload,offset):
        return dict(k=kind,p=payload,rcv=now+offset)
    def book(token,bid,ask,extra):
        return event('book',dict(asset_id=token,timestamp=str(now-50),
            bids=[dict(price=bid,size='5')]+extra,asks=[dict(price=ask,size='5')]),-20)
    events=[book('a','0.49','0.50',[dict(price='.48',size='10')]),book('b','.50','.51',[])]
    events[1]['p']['asks'].append(dict(price='.52',size='10'))
    trade=event('last_trade_price',dict(asset_id='a',side='SELL',size='20',price='.48',
                                      timestamp=str(now+500),transaction_hash='tx'),540)
    events+=[trade,event('price_change',dict(timestamp=str(now+980),price_changes=[]),1000)]
    maker=dict(token='a',side=0,qty=20000000,cash_cost=9600000,fee=0,log_index=1)
    group=dict(tx='tx',match_log=2,active=dict(token='a',side=1,qty=20000000),gross=9600000,makers=[maker])
    groups={'tx':[group]}
    market=dict(clobTokenIds='["a","b"]',orderPriceMinTickSize='.01',closed=True,outcomePrices='["1","0"]')
    def tested(ev=events,gg=groups):
        rows,flows=r.evaluate(start,age,ev,market,gg,config)
        return rows,flows
    rows,flows=tested()
    quote=next(x for x in rows if x['side']==0 and x['ticks_behind']==1)
    assert quote['price']==.48 and quote['ahead']==10 and quote['back_shares']==5
    assert abs(quote['back_pnl']-2.6)<1e-10
    copied=events[:3]+[dict(trade,rcv=now+550)]+events[3:]
    assert tested(copied)[0][0]['back_shares']==5 and len(tested(copied)[1])==1
    without_trade=[e for e in events if e['k']!='last_trade_price']
    # Price touching/cancelling visible depth is not an execution.
    touch=event('price_change',dict(timestamp=str(now+480),price_changes=[dict(asset_id='a',side='BUY',price='.48',size='0')]),500)
    assert tested(without_trade[:2]+[touch]+without_trade[2:])[0][0]['back_shares']==0
    early=deepcopy(events)
    early[2]['p']['timestamp']=str(now+200)
    assert tested(early)[0][0]['back_shares']==0
    late=deepcopy(events)
    late[2]['p']['timestamp']=str(now+1200)
    late[2]['rcv']=now+1240
    late.sort(key=lambda e:e['rcv'])
    assert tested(late)[0][0]['back_shares']==0
    wrong=deepcopy(groups)
    wrong['tx'][0]['active']['qty']+=1
    assert tested(gg=wrong)[0][0]['status']=='missing'
    future=deepcopy(events)
    future[2]['rcv']=now+400
    assert tested(future)[0][0]['status']=='missing'
    # Full snapshots may be old if valid subsequent deltas refresh both books.
    old=deepcopy(events)
    for e in old[:2]:
        e['rcv']=now-4000
        e['p']['timestamp']=str(now-4050)
    fresh=event('price_change',dict(timestamp=str(now-60),price_changes=[dict(asset_id=t,side='BUY',price=p,size='5') for t,p in [('a','.49'),('b','.50')]]),-20)
    assert tested(old[:2]+[fresh]+old[2:])[0][0]['status']=='valid'
    one_sided=deepcopy(events)
    one_sided[0]['p']['asks']=[]
    one_sided[1]['p']['bids']=[]
    one=tested(one_sided)[0]
    assert one[0]['status']=='valid' and one[2]['status']=='no_quote_no_bid'
    assert one[2]['back_shares']==0
    two_levels=deepcopy(groups)
    two_levels['tx'][0]['gross']=9620000
    two_levels['tx'][0]['makers']=[dict(maker,qty=18000000,cash_cost=8640000),dict(maker,log_index=3,qty=2000000,cash_cost=980000)]
    assert len(tested(gg=two_levels)[1])==2
    flipped={**market,'outcomePrices':'["0","1"]'}
    original=tested()[0]
    reverse=r.evaluate(start,age,events,flipped,groups,config)[0]
    assert [[x[k] for k in ('price','ahead','back_shares','front_shares')] for x in original]==[[x[k] for k in ('price','ahead','back_shares','front_shares')] for x in reverse]
    sample=next((r.OUT.parent/'btc5m_parent_research_20260921/receipts').glob('*.json'))
    actual=r.read(sample)
    assert r.matches(actual)
    bad=deepcopy(actual)
    bad['logs'].append(deepcopy(bad['logs'][0]))
    try:
        r.matches(bad)
    except AssertionError:
        pass
    else:
        raise AssertionError('duplicate exchange log accepted')
    print('PASS: real receipt + corrupt log, queue, causal clock, complementary book, duplicate WS, old-snapshot/new-delta guards')
    if (r.OUT/'report.json').exists():
        report=r.read(r.OUT/'report.json')
        assert report['assigned_contexts']==384
        assert len({(x['S'],x['age']) for x in report['results']})==384
        assert all(x.get('back_shares',0)<=x.get('front_shares',0)<=5 for x in report['results'])
        assert all('back_pnl' not in x for x in report['results'] if x['status']=='missing')
        for row in report['results']:
            if row['status']!='valid':
                continue
            assert len({tuple(v) for v in row['flow_ids']})==len(row['flow_ids'])
            assert row['back_shares']<=max(0,row['eligible_flow']-row['ahead'])+1e-8
            assert row['front_shares']<=row['eligible_flow']+1e-8
            for model in ('back','front'):
                expected=r.Decimal(str(row[model+'_shares']))*(r.Decimal(row['side']==row['winner'])-r.Decimal(str(row['price'])))
                assert abs(expected-r.Decimal(str(row[model+'_pnl'])))<r.Decimal('.00000001')
        verification=dict(status='PASS',report_sha256=sha256((r.OUT/'report.json').read_bytes()).hexdigest())
        (r.OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')


if __name__=='__main__':
    main()
