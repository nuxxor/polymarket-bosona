"""One-market conditional event replay with separate exchange and known inventory."""
from collections import Counter
from decimal import Decimal as D
import heapq
import json

import study as a

engine = a.module('frozen_risk_engine', a.V/'replay.py')
UNIT = D(1000000)


def book_tuple(book):
    return ([(D(p)/UNIT,D(q)/UNIT) for p,q in sorted(book['BUY'].items(),reverse=True)],
            [(D(p)/UNIT,D(q)/UNIT) for p,q in sorted(book['SELL'].items())],book['obs'])


def run(client_books, exchange_books, prints, market, mode='queue_back', offset=D(0), hedge=False):
    assert mode in ('queue_back','queue_front')
    known = engine.state()
    actual = dict(q=[D(0),D(0)],cash=D(0))
    orders, actual_fills, lifecycle, queue = {}, [], Counter(), []
    seq, ident = 0, 0
    unknown = set()
    max_cash, max_net, min_worst, max_notification_delay = D(0),D(0),D(0),0

    def push(when, priority, kind, data):
        nonlocal seq
        seq += 1
        heapq.heappush(queue,(when,priority,seq,kind,data))

    def report(when, order, final, source='fill_notification'):
        push(when,1,'learn',(order['id'],order['executed'],order['paid'],final,source))

    def physical_fill(o, qty, price, when, received, role):
        nonlocal max_cash,max_net,min_worst,max_notification_delay
        assert qty>0 and o['executed']+qty<=o['quantity'] and price<=o['limit']
        o['executed'] += qty
        o['paid'] += qty*price
        actual['q'][o['side']] += qty
        actual['cash'] += qty*price
        actual_fills.append(dict(order=o['id'],side=o['side'],qty=qty,cash=qty*price,
                                exchange_proxy_ms=when,scheduled_notification_ms=received,role=role))
        max_cash = max(max_cash,actual['cash'])
        max_net = max(max_net,abs(actual['q'][0]-actual['q'][1]))
        min_worst = min(min_worst,min(actual['q'])-actual['cash'])
        max_notification_delay = max(max_notification_delay,received-when)
        assert engine.safe(actual,[]), 'physical risk limit'
        final = o['executed']==o['quantity']
        if final:
            o['live'] = False
        report(received,o,final)

    def send(side, qty, limit, now, kind, ahead=D(0)):
        nonlocal ident
        assert side not in known['quotes']
        ident += 1
        o = dict(id=ident,side=side,left=qty,quantity=qty,limit=limit,active_ms=now+250,
                 ahead=ahead,executed=D(0),paid=D(0),reported=D(0),reported_cash=D(0),
                 live=False,cancel_requested=False,cancel_ms=None,kind=kind)
        if engine.reserve(known,o):
            known['quotes'][side] = o
            orders[ident] = o
            push(now+250,0,'accept',ident)
            lifecycle['submitted_'+kind] += 1

    def cancel(o, now):
        if not o['cancel_requested']:
            o['cancel_requested'] = True
            o['cancel_ms'] = now+250
            push(now+250,0,'cancel',o['id'])
            lifecycle['cancel_requested'] += 1

    for p in prints:
        assert p['qty']>0 and 0<=p['gross']<=p['qty']+D('.000002') and p['rcv']>=p['obs']
        push(p['obs'],0,'print',p)
    for age in range(30,841):
        push((a.START+age)*1000,2,'decision',None)

    while queue:
        now, _, _, kind, data = heapq.heappop(queue)
        if kind=='learn':
            order_id, qty, cash, final, source = data
            o = orders[order_id]
            if qty<o['reported']:
                lifecycle['older_cumulative_report_ignored'] += 1
                continue
            delta, cost = qty-o['reported'],cash-o['reported_cash']
            if delta:
                engine.fill(known,o,delta,cost/delta,now,o['kind'])
                known['fills'][-1].update(order=order_id,source=source)
                o['reported'],o['reported_cash'] = qty,cash
            else:
                assert cost==0
            if final and known['quotes'].get(o['side']) is o:
                del known['quotes'][o['side']]
                lifecycle['final_status_reconciled'] += 1
            assert engine.safe(known,engine.obligations(known))
        elif kind=='accept':
            o = orders[data]
            books = exchange_books.get(now)
            if books is None or engine.quote(book_tuple(books[o['side']]),now) is None:
                unknown.add('unobserved_acceptance_book')
                report(now+250,o,True,'acceptance_status')
                continue
            b = books[o['side']]
            if o['kind']=='maker':
                if o['limit']>=D(min(b['SELL']))/UNIT:
                    lifecycle['post_only_rejected'] += 1
                    report(now+250,o,True,'acceptance_status')
                    continue
                o['ahead'] = max(o['ahead'],D(b['BUY'].get(int(o['limit']*UNIT),0))/UNIT)
                o['live'] = True
                lifecycle['accepted_maker'] += 1
            else:
                try:
                    price = engine.ask_cost(book_tuple(b)[1],o['quantity'],market)
                    if price>o['limit']:
                        raise ValueError('price_limit')
                    physical_fill(o,o['quantity'],price,now,now+250,'taker')
                except ValueError:
                    lifecycle['hedge_rejected'] += 1
                    report(now+250,o,True,'acceptance_status')
        elif kind=='cancel':
            o = orders[data]
            o['live'] = False
            # Assumed status reconciliation, not an actual cancel API response.
            report(now+250,o,True,'cancel_reconciliation')
        elif kind=='print':
            p = data
            o = known['quotes'].get(p['side'])
            if not o or o['kind']!='maker' or p['gross']-o['limit']*p['qty']>D('.000002'):
                continue
            if now==o['active_ms'] or now==o['cancel_ms']:
                unknown.add('source_clock_lifecycle_tie')
                continue
            if not o['live']:
                continue
            available = p['qty']
            if mode=='queue_back':
                before = min(o['ahead'],available)
                o['ahead'] -= before
                available -= before
            if available:
                qty = min(o['quantity']-o['executed'],available)
                if qty:
                    physical_fill(o,qty,o['limit'],now,p['rcv'],'maker')
        elif kind=='decision':
            net = known['q'][0]-known['q'][1]
            if not net:
                known['hedging'] = False
            if now>=(a.START+840)*1000:
                for o in list(known['quotes'].values()):
                    cancel(o,now)
                continue
            bb = client_books[now]
            if hedge and abs(net)>=engine.NET:
                known['hedging'] = True
            if known['hedging']:
                for o in list(known['quotes'].values()):
                    if o['kind']=='maker':
                        cancel(o,now)
                if not known['quotes'] and net:
                    side,qty = int(net>0),min(engine.CLIP,abs(net))
                    if engine.quote(book_tuple(bb[side]),now) is not None:
                        try:
                            limit = engine.ask_cost(book_tuple(bb[side])[1],qty,market)
                            send(side,qty,limit,now,'taker')
                        except ValueError:
                            lifecycle['missing_hedge_depth'] += 1
                continue
            for side in (0,1):
                bid = engine.quote(book_tuple(bb[side]),now)
                target = bid-offset if bid is not None else None
                o = known['quotes'].get(side)
                if o:
                    if target!=o['limit']:
                        cancel(o,now)
                    continue
                if target is not None and 0<target<1:
                    assert target%D('.01')==0, 'this fixed-cohort probe requires observed cent tick'
                    ahead = D(bb[side]['BUY'].get(int(target*UNIT),0))/UNIT
                    send(side,engine.CLIP,target,now,'maker',ahead)
    assert actual['q']==known['q'] and actual['cash']==known['cash'], 'final known/actual ledger mismatch'
    assert not known['quotes'], 'unreconciled tail'
    return dict(actual=actual,client=dict(q=known['q'],cash=known['cash']),fills=actual_fills,client_updates=known['fills'],
        lifecycle=dict(lifecycle),reservations=dict(known['counters']),max_reserved=known['max_reserved'],
        max_cash=max_cash,max_net=max_net,min_worst=min_worst,max_notification_delay_ms=max_notification_delay,
        unknown=sorted(unknown))


def main():
    a.verify_inputs()
    assert a.sha(a.V/'replay.py')==a.read(a.V/'results/reproduction.json')['sources']['replay.py']
    audit = a.read(a.HERE/'results/report.json')
    assert audit['data_gate']=='PASS_OBSERVED_FLOW_GATE'
    ee = a.events()
    market = a.read(a.HERE/'raw/market_start.json')['data']
    tokens = json.loads(market['clobTokenIds'])
    # ponytail: one observed cent-tick cohort; reject changes until event-time tick support is added.
    ticks = {e['p']['asset_id']:e['p']['tick_size'] for e in ee
             if e['k']=='book' and e['p'].get('tick_size') and e['rcv']<=a.START*1000}
    assert set(ticks)==set(tokens) and set(ticks.values())=={'0.01'}
    assert not any(e['k']=='tick_size_change' for e in ee)
    client,_ = a.m1.books_at(ee,tokens,[(a.START+n)*1000 for n in range(30,841)])
    source = sorted([dict(e,rcv=int(e['p']['timestamp'])) for e in ee if e['k'] in ('book','price_change')],key=lambda e:e['rcv'])
    exchange,_ = a.m1.books_at(source,tokens,[(a.START+n)*1000+250 for n in range(30,841)])
    groups = {p.stem:a.m1.matches(a.read(p)['data']) for p in (a.HERE/'raw/receipts').glob('*.json')}
    flows,errors,_ = a.m1.trade_flows(ee,groups,tokens)
    assert not errors
    prints = []
    for f in flows:
        maker = next(m for g in groups[f['tx']] for m in g['makers'] if m['log_index']==f['log_index'])
        gross = maker['cash_cost']-maker['fee'] if maker['side']==0 else -maker['cash_cost']+maker['fee']
        cash = gross if maker['side']==0 else maker['qty']-gross
        assert f['obs_lo']==f['obs_hi'] and f['received']>=f['obs_lo']
        prints.append(dict(side=f['side'],qty=D(maker['qty'])/UNIT,gross=D(cash)/UNIT,
                           obs=f['obs_lo'],rcv=f['received']))
    outcome = a.accounting.ref.base.outcome(a.read(a.HERE/'raw/market_result.json')['data'])
    results = {}
    for name,offset,hedge in (('M1_bid',D(0),False),('M1_bid_minus_cent',D('.01'),False),('M2_bid_hedge',D(0),True)):
        for mode in ('queue_back','queue_front'):
            result = run(client,exchange,prints,market,mode,offset,hedge)
            result['conditional_pnl'] = result['actual']['q'][outcome]-result['actual']['cash'] if not result['unknown'] else None
            result['economic_pnl'] = None
            results[name+':'+mode] = result
    a.save(a.HERE/'results/execution.json',dict(arms=results,status='CONDITIONAL_MODEL_UNCALIBRATED',
        assumptions=dict(policy_interval_ms=1000,acceptance_ms=250,cancel_effective_ms=250,
            reconciliation_after_cancel_ms=250,hedge_learning_ms=250,
            maker_learning='observed public WS receipt; proxy for unknown private fill notification',
            queue='static visible ahead, no cancellation credit; alternative first in queue',
            impact='hypothetical five-share orders do not change subsequent observed market'),
        limits='One observed cent-tick market. Conditional scenarios only; not calibrated or profitable-policy proof.',
        sources={str(p):a.sha(p) for p in (a.HERE/'execution.py',a.V/'replay.py')},
        inputs={str(a.HERE/'results'/n):a.sha(a.HERE/'results'/n) for n in ('report.json','flows.json')}))
    print(json.dumps({k:{x:v[x] for x in ('conditional_pnl','lifecycle','max_reserved','unknown')} for k,v in results.items()},default=str))


if __name__=='__main__':
    main()
