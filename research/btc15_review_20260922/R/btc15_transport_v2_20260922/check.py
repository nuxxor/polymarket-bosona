"""Clock race regressions, unchanged policy and frozen real-cohort invariants."""
import copy
from decimal import Decimal as D
import socket
from unittest.mock import patch

import run as r


def main():
    r.protect()
    ex = r.ex
    prior = r.a.module('transport_basic_checks',r.old.W/'check.py')
    prior.ex = ex
    checks = list(prior.execution_checks())
    old_source = (r.T/'execution.py').read_text()
    new_source = (r.HERE/'execution.py').read_text()
    def decision(text):
        return text.split("elif kind=='decision':",1)[1].split("    assert actual['q']",1)[0]
    assert decision(old_source)==decision(new_source)
    checks.append('BTC15 decision branch is unchanged, including entry, repricing, hedge trigger and time limits')
    start = ex.a.START*1000
    market = dict(feesEnabled=True,feeSchedule=dict(rate=.07,exponent=1))

    def book(now,bid='.4',ask='.42'):
        return dict(BUY={int(D(bid)*ex.UNIT):0},SELL={int(D(ask)*ex.UNIT):1000000000},
                    ready=True,obs=now-1,rcv=now)

    client = {start+n*1000:[book(start+n*1000),book(start+n*1000,'.58','.60')] for n in range(30,841)}
    changed = copy.deepcopy(client)
    for when in changed:
        if when>=start+31000:
            changed[when][0] = book(when,'.38','.40')

    def venue(delay):
        return {t+delay:[book(t+delay),book(t+delay,'.58','.60')] for t in client}

    def trade(ms,qty=5):
        return dict(side=0,qty=D(qty),gross=D(qty)*D('.4'),obs=start+ms,rcv=start+ms+20)

    delayed = dict(delay=10,post_ack_ms=2500,cancel_delay=20,cancel_notice_ms=4000,learn_extra=100,trace=True,separate_arrival=True)
    nofill = ex.run(changed,venue(10),[],market,**delayed)
    assert nofill['lifecycle']['cancel_deferred_until_post_ack']>0
    by_time = {d['now']-start:d for d in nofill['decisions']}
    pending = next(o for o in by_time[31000]['pending'] if o[1]==0)
    for ms in (32000,33000,34000,35000,36000):
        assert next(o for o in by_time[ms]['pending'] if o[1]==0)[0]==pending[0]
    assert all(o[0]!=pending[0] for o in by_time[37000]['pending'])
    checks.append('cancel waits for POST order id; reserve survives venue cancellation until observed final status')

    before_ack = ex.run(client,venue(10),[trade(30500)],market,**delayed)
    assert before_ack['fills'][0]['exchange_proxy_ms']==start+30500
    assert before_ack['fills'][0]['scheduled_notification_ms']==start+32500
    at = {d['now']-start:d for d in before_ack['decisions']}
    assert at[32000]['q'][0]==0 and at[33000]['q'][0]==5
    checks.append('venue fill before POST reply is real but not prematurely available to the SDK decision client')

    race = dict(delay=10,post_ack_ms=20,cancel_delay=500,cancel_notice_ms=600,learn_extra=2000,trace=True,separate_arrival=True)
    partial = ex.run(changed,venue(10),[trade(31400,3)],market,**race)
    assert partial['actual']['q']==partial['client']['q']==[3,0]
    assert partial['actual']['cash']==partial['client']['cash']==D('1.2')
    assert len(partial['client_updates'])==1 and partial['client_updates'][0]['source']=='cancel_reconciliation'
    checks.append('partial fill during cancellation and later fill notification debit quantity/cash only once')

    future = copy.deepcopy(client)
    for when in future:
        if when>start+40000:
            future[when][0] = book(when,'.3','.32')
    a = ex.run(client,venue(10),[trade(30500)],market,**delayed)
    b = ex.run(future,venue(10),[trade(30500),trade(60500)],market,**delayed)
    assert [d for d in a['decisions'] if d['now']<=start+40000]==[d for d in b['decisions'] if d['now']<=start+40000]
    checks.append('later book and trade changes cannot alter earlier decisions with split clocks')

    for delay,extra in ((250,0),(750,500)):
        for mode in ('queue_front','queue_back'):
            args = dict(delay=delay,learn_extra=extra,mode=mode,trace=True,separate_arrival=True)
            assert ex.run(client,venue(delay),[trade(30500)],market,**args)==r.old.ex.run(client,venue(delay),[trade(30500)],market,**args)
    checks.append('four synthetic legacy paths remain exactly equal to the frozen engine')
    protocol = r.freeze_profiles()
    assert len(protocol['profiles'])==5
    assert len(protocol['post_samples'])==63 and len(protocol['cancel_samples'])==27
    assert min(protocol['learning_relative_to_public_ms'])<0
    for p in protocol['profiles'][2:]:
        assert p['accept']<=p['post_ack_ms'] and p['cancel']<=p['cancel_notice_ms']
    checks.append('clock profile extraction keeps negative observed ordering and valid causal upper bounds')

    path = r.HERE/'results/cohort.json'
    if path.exists():
        result = r.a.read(path)
        assert len(result['markets'])==8 and result['baseline_paths_identical']==192
        count = 0
        for row in result['markets']:
            if not row['replay_eligible']:
                assert row['economic_pnl'] is None and not row.get('arms')
                continue
            full = r.a.read(r.HERE/'results/markets'/f'{row["start"]}.json')
            for v in full['arms'].values():
                count += 1
                assert v['economic_pnl'] is None and v['actual']==v['client']
                assert D(v['max_cash'])<=15 and D(v['max_net'])<=10 and D(v['min_worst'])>=-5
                if v['fund_hedge']:
                    assert D(v['max_funding'])<=15
        assert count==480
        checks.append('480 real BTC15 paths: all caps, client reconciliation, 192 baseline equivalents and missing-data exclusions intact')
    challenge = r.HERE/'results/challenges.json'
    if challenge.exists():
        rows = r.a.read(challenge)['paths']
        assert len(rows)==288
        for row in rows:
            v = row['result']
            assert v['actual']==v['client'] and v['economic_pnl'] is None
            assert D(v['max_cash'])<=15 and D(v['max_net'])<=10 and D(v['min_worst'])>=-5
            if row['test']=='earlier_trade':
                assert v['timing']['trade_shift_ms']==-500
            else:
                assert v['timing']['cancel_notice_ms']==v['timing']['cancel_ms']+v['timing']['accept_ms']
        checks.append('288 post-result falsification paths preserve policy/risk; only declared clocks differ')
    r.a.save(r.HERE/'results/checks.json',dict(passed=True,offline=True,checks=checks))
    print('PASS:',len(checks),'checks')


if __name__ == '__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('offline only')):
        main()
