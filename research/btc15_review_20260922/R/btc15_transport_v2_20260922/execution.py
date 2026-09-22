"""BTC15 clock separation; frozen decisions and risk rules retained."""
from collections import Counter
from decimal import Decimal as D
from itertools import product
import heapq
import hashlib
import json

import study as a

engine = a.module('frozen_risk_engine', a.V/'replay.py')
UNIT = D(1000000)


def book_tuple(book):
    return ([(D(p)/UNIT,D(q)/UNIT) for p,q in sorted(book['BUY'].items(),reverse=True)],
            [(D(p)/UNIT,D(q)/UNIT) for p,q in sorted(book['SELL'].items())],book['obs'])


def arrival_valid(book,now):
    """Venue availability is not the policy's pre-send spread filter."""
    return bool(book['ready'] and 0<=now-book['obs']<=3000 and 0<=now-book['rcv']<=3000
                and book['BUY'] and book['SELL'] and 0<max(book['BUY'])<min(book['SELL'])<1000000)


def funding(s, pending):
    """Maximum cash plus full net-close reserve over all possible partial fills."""
    need = D(0)
    for flags in product((0,1),repeat=len(pending)):
        q,cash = s["q"].copy(),s["cash"]
        for on,o in zip(flags,pending):
            if on:
                q[o["side"]] += o["left"]
                cash += o["left"]*o["limit"]
        need = max(need,cash+abs(q[0]-q[1]))
    return need


def run(client_books, exchange_books, prints, market, mode='queue_back', offset=D(0), hedge=False, delay=250, learn_extra=0, client_ticks=None, exchange_ticks=None, fund_hedge=False, cancel_delay=None, trade_shift=0, tie_order='unknown', trace=False, separate_arrival=False, post_ack_ms=None, cancel_notice_ms=None):
    fund_hedge = fund_hedge and hedge
    assert mode in ('queue_back','queue_front')
    cancel_delay = delay if cancel_delay is None else cancel_delay
    split = post_ack_ms is not None
    if split:
        assert all(isinstance(v,int) and v>=0 for v in (delay,learn_extra,cancel_delay,post_ack_ms,cancel_notice_ms))
        assert delay<=post_ack_ms and cancel_delay<=cancel_notice_ms
    else:
        assert delay in (250,750) and learn_extra in (0,500) and cancel_delay in (250,750)
        assert cancel_notice_ms is None
    assert trade_shift in (0,-500)
    assert tie_order in ('unknown','print_first','lifecycle_first')
    decisions, decision_hash = [], hashlib.sha256()
    known = engine.state()
    actual = dict(q=[D(0),D(0)],cash=D(0))
    orders, actual_fills, lifecycle, queue = {}, [], Counter(), []
    blocked_hedge = None
    max_funding = D(0)
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
        nonlocal max_cash,max_net,min_worst,max_notification_delay,max_funding
        if split:
            # The SDK client cannot reconcile an unknown order id before POST returns.
            received = max(received,o['post_ack_at'])
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
        max_funding = max(max_funding,funding(actual,[]))
        if fund_hedge:
            assert funding(actual,[])<=engine.CASH, 'physical hedge cash reserve'
        final = o['executed']==o['quantity']
        if final:
            o['live'] = False
        report(received,o,final)

    def send(side, qty, limit, now, kind, ahead=D(0)):
        nonlocal ident,blocked_hedge
        assert side not in known['quotes']
        ident += 1
        o = dict(id=ident,side=side,left=qty,quantity=qty,limit=limit,active_ms=now+delay,
                 ahead=ahead,executed=D(0),paid=D(0),reported=D(0),reported_cash=D(0),
                 live=False,cancel_requested=False,cancel_ms=None,kind=kind,
                 acknowledged=not split,accepted=False,post_ack_at=now+post_ack_ms if split else None)
        if fund_hedge and funding(known,engine.obligations(known)+[o])>engine.CASH:
            lifecycle['funding_rejected_'+kind] += 1
            reason = 'funding_only_rejected_' if engine.safe(known,engine.obligations(known)+[o]) else 'funding_and_risk_rejected_'
            lifecycle[reason+kind] += 1
            return
        if engine.reserve(known,o):
            known['quotes'][side] = o
            orders[ident] = o
            push(now+delay,0,'accept',ident)
            if split:
                push(o['post_ack_at'],0,'post_ack',ident)
            lifecycle['submitted_'+kind] += 1
        else:
            lifecycle['reservation_rejected_'+kind] += 1
            if kind=='taker' and blocked_hedge is None:
                q = known['q'].copy()
                q[side] += qty
                cash = known['cash']+qty*limit
                blocked_hedge = dict(time_ms=now,q_before=known['q'].copy(),cash_before=known['cash'],
                    side=side,qty=qty,cash_required=qty*limit,cash_after=cash,worst_after=min(q)-cash,
                    cash_exceeded=cash>engine.CASH,net_exceeded=abs(q[0]-q[1])>engine.NET,
                    loss_exceeded=cash-min(q)>engine.LOSS)

    def dispatch_cancel(o, now):
        o['cancel_ms'] = now+cancel_delay
        o['cancel_notice_at'] = now+cancel_notice_ms if split else None
        push(o['cancel_ms'],0,'cancel',o['id'])
        if split:
            lifecycle['cancel_dispatched'] += 1

    def cancel(o, now):
        if not o['cancel_requested']:
            o['cancel_requested'] = True
            lifecycle['cancel_requested'] += 1
            if o['acknowledged']:
                dispatch_cancel(o,now)
            else:
                lifecycle['cancel_deferred_until_post_ack'] += 1

    for p in prints:
        assert p['qty']>0 and 0<=p['gross']<=p['qty']+D('.000002') and p['rcv']>=p['obs']
        shifted = dict(p,obs=p['obs']+trade_shift)
        priority = -1 if tie_order=='print_first' else .5 if tie_order=='lifecycle_first' else 0
        push(shifted['obs'],priority,'print',shifted)
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
            if fund_hedge:
                assert funding(known,engine.obligations(known))<=engine.CASH, 'known hedge cash reserve'
        elif kind=='accept':
            o = orders[data]
            reply_at = o['post_ack_at'] if split else now+delay
            books = exchange_books.get(now)
            valid = books is not None and (arrival_valid(books[o['side']],now) if separate_arrival else engine.quote(book_tuple(books[o['side']]),now) is not None)
            if not valid:
                unknown.add('unobserved_acceptance_book')
                report(reply_at,o,True,'acceptance_status')
                continue
            b = books[o['side']]
            if o['kind']=='maker':
                if o['limit']>=D(min(b['SELL']))/UNIT:
                    lifecycle['post_only_rejected'] += 1
                    report(reply_at,o,True,'acceptance_status')
                    continue
                tick = exchange_ticks[now][o['side']] if exchange_ticks is not None else D('.01')
                if tick is None:
                    unknown.add('unobserved_acceptance_tick')
                    report(reply_at,o,True,'acceptance_status')
                    continue
                if o['limit']%tick:
                    lifecycle['tick_rejected'] += 1
                    report(reply_at,o,True,'acceptance_status')
                    continue
                o['ahead'] = max(o['ahead'],D(b['BUY'].get(int(o['limit']*UNIT),0))/UNIT)
                o['live'] = True
                o['accepted'] = True
                lifecycle['accepted_maker'] += 1
            else:
                try:
                    price = engine.ask_cost(book_tuple(b)[1],o['quantity'],market)
                    if price>o['limit']:
                        raise ValueError('price_limit')
                    o['accepted'] = True
                    physical_fill(o,o['quantity'],price,now,reply_at,'taker')
                except ValueError:
                    lifecycle['hedge_rejected'] += 1
                    report(reply_at,o,True,'acceptance_status')
        elif kind=='post_ack':
            o = orders[data]
            o['acknowledged'] = True
            lifecycle['post_ack_received'] += 1
            if o['cancel_requested'] and o['accepted']:
                dispatch_cancel(o,now)
        elif kind=='cancel':
            o = orders[data]
            o['live'] = False
            # Assumed status reconciliation, not an actual cancel API response.
            report(o['cancel_notice_at'] if split else now+delay,o,True,'cancel_reconciliation')
        elif kind=='print':
            p = data
            o = known['quotes'].get(p['side'])
            if not o or o['kind']!='maker' or p['gross']-o['limit']*p['qty']>D('.000002'):
                continue
            if now==o['active_ms'] or now==o['cancel_ms']:
                lifecycle['same_ms_trade_and_lifecycle'] += 1
                if tie_order=='unknown':
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
                    physical_fill(o,qty,o['limit'],now,p['rcv']+learn_extra,'maker')
        elif kind=='decision':
            bb = client_books[now]
            assert all(b['rcv']<=now and b['obs']<=now for b in bb)
            decision = dict(now=now,q=known['q'].copy(),cash=known['cash'],
                pending=[(o['id'],o['side'],o['left'],o['limit'],o['cancel_requested']) for o in known['quotes'].values()],
                books=[dict(rcv=b['rcv'],obs=b['obs'],bid=max(b['BUY'],default=None),ask=min(b['SELL'],default=None)) for b in bb])
            decision_hash.update(json.dumps(decision,sort_keys=True,default=str).encode())
            if trace:
                decisions.append(decision)
            net = known['q'][0]-known['q'][1]
            if not net:
                known['hedging'] = False
            if now>=(a.START+840)*1000:
                for o in list(known['quotes'].values()):
                    cancel(o,now)
                continue
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
                    tick = client_ticks[now][side] if client_ticks is not None else D('.01')
                    if tick is None:
                        unknown.add('unobserved_decision_tick')
                        continue
                    if target%tick:
                        lifecycle['invalid_decision_tick'] += 1
                        continue
                    ahead = D(bb[side]['BUY'].get(int(target*UNIT),0))/UNIT
                    send(side,engine.CLIP,target,now,'maker',ahead)
    assert actual['q']==known['q'] and actual['cash']==known['cash'], 'final known/actual ledger mismatch'
    assert not known['quotes'], 'unreconciled tail'
    return dict(actual=actual,client=dict(q=known['q'],cash=known['cash']),fills=actual_fills,client_updates=known['fills'],
        lifecycle=dict(lifecycle),reservations=dict(known['counters']),max_reserved=known['max_reserved'],
        max_cash=max_cash,max_net=max_net,min_worst=min_worst,max_notification_delay_ms=max_notification_delay,
        unknown=sorted(unknown),first_blocked_hedge=blocked_hedge,
        fund_hedge=fund_hedge,max_funding=max_funding,
        decisions_sha256=decision_hash.hexdigest(),decisions=decisions,
        timing=dict(accept_ms=delay,cancel_ms=cancel_delay,learn_extra_ms=learn_extra,trade_shift_ms=trade_shift,tie_order=tie_order,
                    **(dict(post_ack_ms=post_ack_ms,cancel_notice_ms=cancel_notice_ms) if split else {})))
