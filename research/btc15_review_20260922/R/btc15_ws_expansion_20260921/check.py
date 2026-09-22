"""Run the old lifecycle checks plus new timing/tick/control counterexamples."""
import copy
from decimal import Decimal as D
from unittest.mock import patch

import run as r


def main():
    r.protect()
    ex = r.ex
    old = r.a.module('prior_execution_checks',r.W/'check.py')
    old.ex = ex
    checks = list(old.execution_checks())
    start = ex.a.START*1000
    market = dict(feesEnabled=True,feeSchedule=dict(rate=.07,exponent=1))
    def book(now,bid='.4',ask='.42'):
        return dict(BUY={int(D(bid)*ex.UNIT):0},SELL={int(D(ask)*ex.UNIT):1000000000},
                    ready=True,obs=now-10,rcv=now)
    client = {start+n*1000:[book(start+n*1000),book(start+n*1000,'.58','.60')]
              for n in range(30,841)}
    venue = {t+750:[book(t+750),book(t+750,'.58','.60')] for t in client}
    def trade(ms,qty):
        return dict(side=0,qty=D(qty),gross=D(qty)*D('.4'),obs=start+ms,rcv=start+ms+100)
    value = ex.run(client,venue,[trade(30500,5),trade(30800,2)],market,delay=750,learn_extra=500)
    assert value['actual']['q']==[D(2),D(0)] and value['max_notification_delay_ms']==600
    assert value['client']==value['actual']
    checks.append('750ms scenario rejects preacceptance print and adds 500ms learning delay')
    fractional = {t:[book(t,'.401','.42'),book(t,'.58','.60')] for t in client}
    ticks = {t:[D('.001'),D('.001')] for t in client}
    venue_ticks = {t:[D('.01'),D('.01')] for t in venue}
    value = ex.run(fractional,venue,[],market,delay=750,client_ticks=ticks,exchange_ticks=venue_ticks)
    assert value['lifecycle']['tick_rejected']>0 and not value['fills']
    checks.append('tick change during transmission rejects invalid arrival grid')
    ee = [dict(k='book',rcv=1000,p=dict(asset_id='a',timestamp='990',tick_size='.01')),
          dict(k='tick_size_change',rcv=2000,p=dict(asset_id='a',timestamp='1990',new_tick_size='.001'))]
    ticks = r.ticks_at(ee,['a','b'],[999,1500,2500])
    assert ticks[999]==[None,None] and ticks[1500][0]==D('.01') and ticks[2500][0]==D('.001')
    checks.append('decision tick excludes not-yet-received future tick change')
    initial = [dict(k='book',rcv=start-100,p=dict(asset_id=t,timestamp=str(start-110))) for t in ('a','b')]
    future = [dict(k='book',rcv=start+100,p=dict(asset_id=t,timestamp=str(start+90))) for t in ('a','b')]
    kept,origin = r.book_events(initial+future,['a','b'])
    assert origin==start-100 and kept==initial+future
    checks.append('book initialization never uses a complete snapshot received after market start')
    venue250 = {t+250:[book(t+250),book(t+250,'.58','.60')] for t in client}
    def context(*args):
        age = args[-1]-ex.a.START
        return dict(spot=101.,ref=100.,final_up_prob=.8 if age==180 else .4)
    moved = copy.deepcopy(venue250)
    moved[start+180250][0] = book(start+180250,'.68','.70')
    with patch.object(ex.engine.old,'context',side_effect=context):
        good = r.candidate(client,venue250,market,{}, {},250)
        bad = r.candidate(client,moved,market,{}, {},250)
    assert good['state']['entered'] and not bad['state']['entered']
    assert good['trace'][0]['intent']==bad['trace'][0]['intent']
    assert good['trace'][0]['sent_cash_limit']==bad['trace'][0]['sent_cash_limit']
    assert bad['trace'][0]['execution']=='price_limit_rejected'
    checks.append('P0 future price changes execution only, never the submitted decision or limit')
    with patch.object(ex.engine.old,'context',side_effect=ValueError('missing_reference')):
        missing = r.candidate(client,venue250,market,{}, {},250)
    assert missing['gaps']['missing_reference']==12 and not missing['state']['events']
    checks.append('P0 missing context retained explicitly, not silently scored as no trade')
    path = r.HERE/'results/replay.json'
    if path.exists():
        rows = r.a.read(path)['markets']
        assert tuple(x['start'] for x in rows)==r.STARTS
        assert rows[0]['data_gate']=='MISSING_DATA' and all(x['arms'] for x in rows[1:])
        for row in rows:
            if row['data_gate']!='PASS_OBSERVED_FLOW_GATE':
                assert not row['arms'] and row['economic_pnl'] is None
            for v in row['arms'].values():
                assert v['actual']==v['client'] and v['economic_pnl'] is None
                assert D(v['max_cash'])<=15 and D(v['max_reserved'])<=15
                assert D(v['max_net'])<=10 and D(v['min_worst'])>=-5
                assert all(0<D(f['qty'])<=5 for f in v['fills'])
            for p0 in row['control'].values():
                s = p0['state']
                assert s['cash']<=15.0000001 and abs(s['q'][0]-s['q'][1])<=10.0000001
                assert s['peak_risk']<=5.0000001 and p0['economic_pnl'] is None
        checks.append('all assigned real markets retained and every replay obeys risk and money limits')
    streams,refs = ex.engine.old.chainlink_streams(list((r.HERE/'raw').glob('cld*.gz')))
    contexts = {}
    for start in r.STARTS:
        contexts[start] = [ex.engine.old.context(streams,refs,start,start+900,start+age) for age in range(180,841,60)]
        assert len(contexts[start])==12
        assert all(c['reference_received_ms']<=c['now']*1000 for c in contexts[start])
    checks.append('all 36 planned contexts available with already received opening reference')
    r.a.save(r.HERE/'results/checks.json',dict(passed=True,checks=checks,context_counts={s:len(v) for s,v in contexts.items()}))
    r.protect()
    print(len(checks),'checks passed')


if __name__=='__main__':
    main()
