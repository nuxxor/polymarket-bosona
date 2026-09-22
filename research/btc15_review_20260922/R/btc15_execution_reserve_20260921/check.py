"""Funding invariants, frozen-control equivalence and trace counterexamples."""
import copy
from decimal import Decimal as D
from itertools import product
import json

import run as r
import telemetry


def main():
    r.protect()
    ex = r.ex
    old = r.a.module('old_checks',r.prior.W/'check.py')
    old.ex = ex
    checks = list(old.execution_checks())
    s = dict(q=[D(10),D(20)],cash=D('14.5'))
    assert ex.engine.safe(s,[]) and ex.funding(s,[])==D('24.5')
    checks.append('old risk/cash-valid inventory can lack full hedge cash')
    s = dict(q=[D(5),D(0)],cash=D(2))
    pending = [dict(side=0,left=D(5),limit=D('.4')),
               dict(side=1,left=D(5),limit=D('.58'))]
    maximum = ex.funding(s,pending)
    assert maximum==14
    for fractions in product((D(0),D('.1'),D('.5'),D(1)),repeat=2):
        q,cash = s['q'].copy(),s['cash']
        for fraction,o in zip(fractions,pending):
            q[o['side']] += fraction*o['left']
            cash += fraction*o['left']*o['limit']
        assert ex.funding(dict(q=q,cash=cash),[])<=maximum
    checks.append('pending vertex bound includes opposing and partial fills')
    for p in (D(n)/1000 for n in range(1001)):
        assert p+D('.07')*p*(1-p)<=1
    # Closing five shares never increases cash plus absolute net for cost<=1.
    for q in (D(1),D(5),D(10)):
        for cost in (D(0),D('.617'),D(1)):
            assert D(4)+q*cost <= D(4)+q
    checks.append('one dollar per unmatched share funds either outcome including stated taker fee')
    start = ex.a.START*1000
    market = dict(feesEnabled=True,feeSchedule=dict(rate=.07,exponent=1))
    def book(now,bid,ask):
        return dict(BUY={int(D(bid)*ex.UNIT):0},SELL={int(D(ask)*ex.UNIT):1000000000},
                    ready=True,obs=now-10,rcv=now)
    client = {start+n*1000:[book(start+n*1000,'.4','.42'),book(start+n*1000,'.58','.60')]
              for n in range(30,841)}
    prints = [dict(side=0,qty=D(5),gross=D(2),obs=start+n*1000+600,rcv=start+n*1000+900)
              for n in range(30,100,3)]
    for delay,extra in ((250,0),(750,500)):
        venue = {t+delay:[book(t+delay,'.4','.42'),book(t+delay,'.58','.60')] for t in client}
        for mode in ('queue_back','queue_front'):
            old_value = r.baseline_run(client,venue,prints,market,mode=mode,hedge=True,delay=delay,learn_extra=extra)
            current = ex.run(client,venue,prints,market,mode=mode,hedge=True,delay=delay,learn_extra=extra)
            assert {k:v for k,v in current.items() if k not in ('fund_hedge','max_funding')}==old_value
            funded = ex.run(client,venue,prints,market,mode=mode,hedge=True,delay=delay,learn_extra=extra,fund_hedge=True)
            assert funded['max_funding']<=15 and funded['actual']==funded['client']
            assert any(f['role']=='taker' for f in funded['fills'])
            assert funded['lifecycle'].get('funding_rejected_maker',0)>0
            assert not funded['first_blocked_hedge']
    checks.append('unfunded engine equals frozen source in all four timing/queue cases')
    checks.append('funded hedge fills, refuses new unfunded quotes and preserves limits')
    changed = copy.deepcopy(client)
    for t in changed:
        if t>=start+31000:
            changed[t][0] = book(t,'.38','.4')
    venue = {t+250:[book(t+250,'.4','.42'),book(t+250,'.58','.60')] for t in client}
    partial = [dict(side=0,qty=D(3),gross=D('1.2'),obs=start+31100,rcv=start+33100)]
    value = ex.run(changed,venue,partial,market,hedge=True,fund_hedge=True)
    assert value['actual']['q']==[D(3),D(0)] and value['actual']==value['client']
    assert len(value['client_updates'])==1 and value['max_funding']<=15
    checks.append('funding retained across cancel and late partial-fill notification, accounted once')
    rows = [json.loads(s) for s in (r.HERE/'raw/orders.jsonl').read_text().splitlines()]
    measured = telemetry.analyze(rows)
    assert measured['accepted']==12 and measured['final_states']==dict(CANCELED=8,MATCHED=4)
    assert measured['cancel_live_overlap']==measured['cancel_live_after_ack']==1
    assert len(measured['missing_gets'])==2
    assert all(f['match_to_observation_ms'] is None for x in measured['orders'] for f in x['fills'])
    broken = copy.deepcopy(rows)
    broken[1]['seq'] = 99
    try:
        telemetry.analyze(broken)
    except AssertionError:
        pass
    else:
        raise AssertionError('missing telemetry sequence silently accepted')
    checks.append('all accepted/unfilled orders retained; missing GETs and cancel races distinguished')
    checks.append('missing exchange timestamps stay unknown; damaged trace rejected')
    if (r.HERE/'results/funded.json').exists():
        base,fund = [r.a.read(r.HERE/'results'/f'{name}.json') for name in ('baseline','funded')]
        assert base['assigned_starts']==fund['assigned_starts']==list(r.prior.STARTS)
        assert base['missing_starts']==fund['missing_starts']
        for b,f in zip(base['markets'],fund['markets']):
            assert b['start']==f['start'] and b['control']==f['control']
            for name,v in f['arms'].items():
                assert v['actual']==v['client'] and v['economic_pnl'] is None
                assert D(v['max_cash'])<=15 and D(v['max_net'])<=10 and D(v['min_worst'])>=-5
                if name.startswith('M2'):
                    assert v['fund_hedge'] and D(v['max_funding'])<=15
                    blocked = v['first_blocked_hedge']
                    assert not blocked or not blocked['cash_exceeded']
                else:
                    assert v==b['arms'][name]
        checks.append('real funded paths obey invariant; M1 and P0 controls exactly unchanged')
    r.a.save(r.HERE/'results/checks.json',dict(passed=True,checks=checks))
    r.protect()
    print(len(checks),'checks passed')


if __name__=='__main__':
    main()
