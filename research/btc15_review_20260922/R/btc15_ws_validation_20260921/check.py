"""Small checks for public feed multiplicity, clock and transfer boundaries."""
import copy
from decimal import Decimal as D

from study import HERE, aggregate_api, m1, read, save
import execution as ex


def execution_checks():
    start = ex.a.START*1000
    market = dict(feesEnabled=True,feeSchedule=dict(rate=.07,exponent=1))
    def book(now,bid,ask):
        return dict(BUY={int(D(bid)*1000000):0},SELL={int(D(ask)*1000000):1000000000},
                    ready=True,obs=now-10,rcv=now)
    client = {start+n*1000:[book(start+n*1000,'.4','.42'),book(start+n*1000,'.58','.60')]
              for n in range(30,841)}
    exchange = {start+n*1000+250:[book(start+n*1000+250,'.4','.42'),book(start+n*1000+250,'.58','.60')]
                for n in range(30,841)}
    def trade(ms,qty,delay=100):
        return dict(side=0,qty=D(qty),gross=D(qty)*D('.4'),obs=start+ms,rcv=start+ms+delay)
    r = ex.run(client,exchange,[trade(30500,1,2000)],market)
    assert r['actual']['q']==[D(1),D(0)] and r['client']==r['actual']
    assert r['max_notification_delay_ms']==2000 and r['fills'][0]['scheduled_notification_ms']>r['fills'][0]['exchange_proxy_ms']
    assert r['max_reserved']<=15
    yield 'delayed partial fill keeps reserved cash and separate learning clock'
    r = ex.run(client,exchange,[trade(30100,5)],market)
    assert not r['fills']
    yield 'physical fills cannot precede assumed acceptance'
    moved = copy.deepcopy(exchange)
    moved[start+30250][0] = book(start+30250,'.38','.4')
    r = ex.run(client,moved,[trade(30500,5)],market)
    assert not r['fills'] and r['lifecycle']['post_only_rejected']==1
    yield 'post-only crossing is rejected using arrival book, not decision bid'
    changed = copy.deepcopy(client)
    for now in changed:
        if now>=start+31000:
            changed[now][0] = book(now,'.38','.4')
    r = ex.run(changed,exchange,[trade(31100,5,1200)],market)
    assert r['actual']['q']==[D(5),D(0)] and r['client']==r['actual']
    assert len(r['fills'])==1
    assert r['client_updates'][0]['source']=='cancel_reconciliation'
    assert r['client_updates'][0]['when']<r['fills'][0]['scheduled_notification_ms']
    yield 'fill during cancel transit reconciles once despite later notification'
    r = ex.run(changed,exchange,[trade(31400,5)],market)
    assert not r['fills']
    yield 'cancelled venue order cannot fill while client awaits final status'
    r = ex.run(changed,exchange,[trade(31250,5)],market)
    assert r['unknown']==['source_clock_lifecycle_tie']
    yield 'equal source and lifecycle timestamps remain explicitly uncertain'
    r = ex.run(client,exchange,[trade(n*1000,5) for n in range(31,100,3)],market,hedge=True)
    assert any(f['role']=='taker' for f in r['fills'])
    assert r['max_cash']<=15 and r['max_reserved']<=15 and r['max_net']<=10 and r['min_worst']>=-5
    assert all(f['qty']<=5 for f in r['fills']) and r['client']==r['actual']
    yield 'repeated real-path hedges respect cash, net, loss, clip and reconciliation'
    try:
        ex.run(client,exchange,[trade(30500,1,-1)],market)
    except AssertionError:
        pass
    else:
        raise AssertionError('notification from before the event accepted')
    yield 'invalid notification chronology is rejected before replay'


def main():
    checks = []
    row = dict(transactionHash='tx', proxyWallet='wallet', asset='a', side='BUY', size='5', price='.4')
    a = aggregate_api([row,row])
    assert a[('tx','wallet','a','BUY')]['qty'] == 10000000
    checks.append('genuine identical API fills keep multiplicity')
    book = dict(k='book', rcv=1000, p=dict(asset_id='a', timestamp='990',
        bids=[dict(price='.4',size='20')], asks=[dict(price='.42',size='10')]))
    delta = dict(k='price_change',rcv=1100,p=dict(timestamp='1090',price_changes=[
        dict(asset_id='a',side='BUY',price='.4',size='7')]))
    future = dict(k='price_change',rcv=1200,p=dict(timestamp='1190',price_changes=[
        dict(asset_id='a',side='BUY',price='.4',size='0')]))
    snapshots, issues = m1.books_at([book,delta,future], ['a','b'], [1050,1150,1250])
    assert not issues
    assert snapshots[1050][0]['BUY'][400000] == 20000000
    assert snapshots[1150][0]['BUY'][400000] == 7000000
    assert snapshots[1250][0]['BUY'] == {}
    checks.append('absolute L2 sizes replace levels; future received delta excluded')
    backwards = copy.deepcopy(delta)
    backwards['p']['timestamp'] = '980'
    snapshots, issues = m1.books_at([book,backwards], ['a','b'], [1150])
    assert snapshots[1150][0]['BUY'][400000] == 20000000 and issues['out_of_order_book']==1
    checks.append('out of order source clock is explicit')
    active = dict(token='a',side=0,qty=5000000)
    makers = [dict(token='b',side=0,qty=5000000,cash_cost=3000000,fee=0,log_index=1)]
    group = dict(tx='tx',match_log=2,active=active,makers=makers,gross=2000000)
    message = dict(k='last_trade_price',rcv=2000,p=dict(timestamp='1950',transaction_hash='tx',
        asset_id='a',size='5',price='.4',side='BUY'))
    flows, errors, metrics = m1.trade_flows([message,message], {'tx':[group]}, ['a','b'])
    assert not errors and len(flows)==1 and flows[0]['side']==1 and D(str(flows[0]['qty']))==5
    assert metrics['repeat_messages']==1 and flows[0]['price']==.6
    checks.append('repeated WS match and opposite-token mint do not double volume')
    first = next((HERE/'raw/receipts').glob('*.json'))
    receipt = read(first)['data']
    assert m1.matches(receipt)
    damaged = copy.deepcopy(receipt)
    damaged['logs'].append(copy.deepcopy(damaged['logs'][-1]))
    try:
        m1.matches(damaged)
    except AssertionError:
        pass
    else:
        raise AssertionError('duplicate receipt log accepted')
    checks.append('real receipt reconciles; duplicate log is rejected')
    result = read(HERE/'results/report.json')
    assert result['economic_pnl'] is None
    assert result['start']==1790023500 and result['end']==1790024400
    checks.append('fixed prospective market and economic gate retained')
    a = read(HERE/'results/api_reconciliation.json')
    assert a['true_initial']['rows'] == a['true_confirmed']['rows'] == 932
    assert len(a['true_initial']['differences']) == 4
    assert not a['true_confirmed']['differences'] and not a['false']['differences']
    checks.append('equal API row counts do not conceal duplicate and missing fills')
    probes = read(HERE/'results/quote_probes.json')['rows']
    assert len(probes)==16
    for row in probes:
        assert row['economic_pnl'] is None
        assert row['activation_assumed_ms']-row['decision_ms']==250
        assert row['cancel_assumed_ms']-row['decision_ms']==1250
        if row['status']=='conditional':
            assert 0<=row['queue_back_shares']<=row['queue_front_shares']<=5
            assert row['queue_front_shares']<=row['eligible_shares']
        elif row['status']=='post_only_rejected':
            assert row['price']>=row['arrival_ask']
    checks.append('real independent quote probes conserve volume, clip and fixed lifetime')
    assert sum(row['status']=='post_only_rejected' for row in probes)==1
    checks.append('real price move during assumed activation rejects crossing post-only quote')
    checks.extend(execution_checks())
    for arm in read(HERE/'results/execution.json')['arms'].values():
        assert D(arm['max_cash'])<=15 and D(arm['max_reserved'])<=15
        assert D(arm['max_net'])<=10 and D(arm['min_worst'])>=-5
        assert arm['actual']==arm['client'] and arm['economic_pnl'] is None
    checks.append('six real WS scenarios preserve all money and known/venue ledger limits')
    save(HERE/'results/checks.json', dict(passed=True, checks=checks))
    print(len(checks), 'checks passed')


if __name__ == '__main__':
    main()
