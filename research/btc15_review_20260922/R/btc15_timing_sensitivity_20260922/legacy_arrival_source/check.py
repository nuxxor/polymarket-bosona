"""Causal decisions, timing races, unchanged baseline and real risk invariants."""
import copy
from decimal import Decimal as D
from unittest.mock import patch

import run as r


def comparable(value):
    result = {k:v for k,v in value.items() if k not in ('decisions','decisions_sha256','timing')}
    result['lifecycle'] = {k:v for k,v in result['lifecycle'].items() if k!='same_ms_trade_and_lifecycle'}
    return result


def main():
    r.protect()
    ex = r.ex
    old = r.a.module('timing_old_checks',r.W/'check.py')
    old.ex = ex
    checks = list(old.execution_checks())
    start = ex.a.START*1000
    market = dict(feesEnabled=True,feeSchedule=dict(rate=.07,exponent=1))
    def book(now,bid='.4',ask='.42'):
        return dict(BUY={int(D(bid)*ex.UNIT):0},SELL={int(D(ask)*ex.UNIT):1000000000},
                    ready=True,obs=now-10,rcv=now)
    client = {start+n*1000:[book(start+n*1000),book(start+n*1000,'.58','.60')] for n in range(30,841)}
    venues = {d:{t+d:[book(t+d),book(t+d,'.58','.60')] for t in client} for d in (250,750)}
    def trade(ms,qty=5,lag=100):
        return dict(side=0,qty=D(qty),gross=D(qty)*D('.4'),obs=start+ms,rcv=start+ms+lag)
    prints = [trade(n*1000+600) for n in range(30,100,3)]
    for delay,extra in ((250,0),(750,500)):
        for mode in ('queue_back','queue_front'):
            for fund in (False,True):
                args=dict(mode=mode,hedge=True,delay=delay,learn_extra=extra,fund_hedge=fund)
                old_value=r.legacy.run(client,venues[delay],prints,market,**args)
                new=ex.run(client,venues[delay],prints,market,**args)
                assert comparable(new)==old_value
    checks.append('default engine is exactly equivalent to frozen reserve engine in eight timing/queue/funding paths')
    for tie,expected in (('print_first',0),('lifecycle_first',5)):
        v=ex.run(client,venues[250],[trade(30250)],market,tie_order=tie)
        assert v['actual']['q'][0]==expected
    changed=copy.deepcopy(client)
    for t in changed:
        if t>=start+31000:
            changed[t][0]=book(t,'.38','.4')
    for tie,expected in (('print_first',5),('lifecycle_first',0)):
        v=ex.run(changed,venues[250],[trade(31250,lag=1500)],market,tie_order=tie)
        assert v['actual']['q'][0]==expected and v['actual']==v['client']
    checks.append('both same-ms acceptance/cancel orderings are explicit, including late fill reports')
    fast=ex.run(changed,venues[250],[trade(31400)],market,cancel_delay=250)
    slow=ex.run(changed,venues[250],[trade(31400)],market,cancel_delay=750)
    assert not fast['fills'] and slow['actual']['q'][0]==5
    checks.append('cancel delay varies independently of acceptance and can change actual fill')
    v=ex.run(client,venues[250],[trade(30500)],market,learn_extra=500,trace=True)
    at={x['now']:x for x in v['decisions']}
    assert at[start+31000]['q']==[0,0] and at[start+32000]['q']==[5,0]
    early=ex.run(client,venues[250],[trade(30300)],market,trade_shift=-500)
    original=ex.run(client,venues[250],[trade(30300)],market)
    assert not early['fills'] and original['actual']['q'][0]==5
    checks.append('earlier trade proxy changes venue fills without moving the client notification backward')
    future=copy.deepcopy(client)
    for t in future:
        if t>start+40000:
            future[t][0]=book(t,'.35','.37')
    v1=ex.run(client,venues[250],[trade(30500)],market,trace=True)
    v2=ex.run(future,venues[250],[trade(30500),trade(60500)],market,trace=True)
    assert [x for x in v1['decisions'] if x['now']<=start+40000]==[x for x in v2['decisions'] if x['now']<=start+40000]
    checks.append('future books and later trades cannot change prior decisions or known inventory')
    bad=copy.deepcopy(client)
    bad[start+30000][0]['rcv']=start+30001
    try:
        ex.run(bad,venues[250],[],market)
    except AssertionError:
        pass
    else:
        raise AssertionError('future received book accepted by policy')
    checks.append('decision input with future receipt time is rejected')
    def context(*args):
        return dict(spot=101.,ref=100.,final_up_prob=.8 if args[-1]-ex.a.START==180 else .4)
    moved=copy.deepcopy(venues[250])
    moved[start+180250][0]=book(start+180250,'.68','.7')
    with patch.object(r.prior.ex.engine.old,'context',side_effect=context):
        good=r.prior.candidate(client,venues[250],market,{}, {},250)
        bad=r.prior.candidate(client,moved,market,{}, {},250)
    assert good['trace'][0]['intent']==bad['trace'][0]['intent']
    assert good['trace'][0]['sent_cash_limit']==bad['trace'][0]['sent_cash_limit']
    assert good['state']['entered'] and not bad['state']['entered']
    checks.append('frozen P0 decision and 55-cent sent protection survive unfavorable future execution price')
    ticks=r.ticks_with_initial([],['a','b'],[1000,3000],dict(received_ms=2000,data=dict(orderPriceMinTickSize=.01)))
    assert ticks[1000]==[None,None] and ticks[3000]==[D('.01'),D('.01')]
    checks.append('initial metadata tick becomes usable only after its actual receive time')
    rows=r.a.read(r.HERE/'results/cohort.json')['markets']
    assert [x['start'] for x in rows]==r.PROTOCOL['starts']
    assert sum(x['replay_eligible'] for x in rows)==6
    for x in rows:
        if not x['replay_eligible']:
            assert not x.get('arms') and x['economic_pnl'] is None
            continue
        full=r.a.read(r.HERE/'results/markets'/f'{x["start"]}.json')
        for value in full['arms'].values():
            assert value['actual']==value['client'] and value['economic_pnl'] is None
            assert D(value['max_cash'])<=15 and D(value['max_net'])<=10 and D(value['min_worst'])>=-5
            if value['fund_hedge']:
                assert D(value['max_funding'])<=15
            assert all(0<D(f['qty'])<=5 for f in value['fills'])
        for control in full['control'].values():
            s=control['state']
            assert s['cash']<=15.0000001 and s['peak_risk']<=5.0000001 and abs(s['q'][0]-s['q'][1])<=10.0000001
    last=rows[-1]
    assert last['frozen_data_gate']=='MISSING_DATA' and last['offline_status']=='RECONCILED_LATER'
    checks.append('real assigned cohort retains missing markets, later reconciliation labels, all risk caps and null economics')
    clpaths=[r.HERE/'raw/chainlink.jsonl.gz']
    for stage in (r.E,r.Z):
        clpaths.extend(stage/name for name in r.a.read(stage/'raw/chainlink_manifest.json'))
    streams,refs=ex.engine.old.chainlink_streams(clpaths)
    context_count=0
    for row in rows:
        if not row['replay_eligible']:
            continue
        s=row['start']
        for age in range(180,841,60):
            now=s+age
            past={name:([t for t in times if t<=now*1000],values[:sum(t<=now*1000 for t in times)]) for name,(times,values) in streams.items()}
            past_refs={k:v for k,v in refs.items() if v[0]<=now*1000}
            answers=[]
            for ss,rr in ((streams,refs),(past,past_refs)):
                try:
                    answers.append(ex.engine.old.context(ss,rr,s,s+900,now))
                except ValueError as error:
                    answers.append(str(error))
            assert answers[0]==answers[1]
            context_count+=1
    checks.append(f'all {context_count} real P0 contexts are identical after deleting every later received price/reference')
    # Actual old market, all four arms: new default behavior must not re-optimize old policy.
    _,data=r.load(1790028000)
    for d,extra in ((250,0),(750,500)):
        for name,offset,hedge,fund in r.ARMS:
            for mode in r.PROTOCOL['queues']:
                args=dict(mode=mode,offset=offset,hedge=hedge,delay=d,learn_extra=extra,
                          client_ticks=data['ct'],exchange_ticks=data['vt'][d],fund_hedge=fund)
                one=r.legacy.run(data['client'],data['venue'][d],data['prints'],data['market'],**args)
                two=ex.run(data['client'],data['venue'][d],data['prints'],data['market'],**args)
                assert comparable(two)==one
    checks.append('16 actual-market baseline paths match frozen engine exactly before timing interventions')
    profile=r.PROTOCOL['profiles'][0]
    original=r.run_one(data,profile,'queue_back','lifecycle_first',r.ARMS[0])
    data['result']={'outcomePrices':'["0","1"]','eventMetadata':{'priceToBeat':-999},'closed':False}
    data['later_api']={'artificial_future_signal':'buy_everything'}
    mutated=r.run_one(data,profile,'queue_back','lifecycle_first',r.ARMS[0])
    assert original==mutated
    checks.append('altering final result/reference and later API metadata cannot change policy path or fills')
    r.a.save(r.HERE/'results/checks.json',dict(passed=True,checks=checks))
    r.protect()
    print(len(checks),'checks passed')


if __name__=='__main__':
    main()
