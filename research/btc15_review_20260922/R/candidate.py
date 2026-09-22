#!/usr/bin/env python3
"""BTC15m local policy, no network/orders. History replay is a price scenario, not fills."""
import argparse
import bisect
from collections import Counter
import math

import research as r
import study


def unit_cost(price, rate):
    if not math.isfinite(price) or not 0<price<1 or not 0<=rate<=1:
        raise ValueError('invalid public quote/fee')
    return price+rate*price*(1-price)


def state():
    return dict(q=[0.,0.],cash=0.,lots=[[],[]],entered=False,added=False,events=[],peak_risk=0.)


def complete_cost(s, side, qty, new_cost):
    left, cost = qty, 0.
    for q,p in s['lots'][1-side]:
        take = min(left,q)
        cost += take*(p+new_cost)
        left -= take
        if left<1e-8:
            return cost/qty
    raise ValueError('completion exceeds unmatched inventory')


def allowed(s,side,qty,cost):
    q = s['q'].copy()
    q[side] += qty
    cash = s['cash']+qty*cost
    return cash<=15+1e-8 and abs(q[0]-q[1])<=10+1e-8 and cash-min(q)<=5+1e-8


def decide(s, age, prices, f, arm='managed', entry='discount', rate=.07):
    """Only predecision prices/context/own inventory. No winner or actor fills."""
    if len(prices)!=2 or not all(math.isfinite(p) and 0<p<1 for p in prices):
        return None
    if not all(math.isfinite(f[k]) for k in ('spot','ref','final_up_prob')) or not 0<=f['final_up_prob']<=1:
        return None
    costs = [unit_cost(p,rate) for p in prices]
    net = s['q'][0]-s['q'][1]
    if s['entered'] and arm!='entry_only' and abs(net)>1e-6 and age<=840:
        side = 1 if net>0 else 0
        qty = min(5.,abs(net))
        if complete_cost(s,side,qty,costs[side])<=.98 and allowed(s,side,qty,costs[side]):
            return dict(side=side,qty=qty,kind='complete')
    if not s['entered'] and age==180:
        if entry=='cheaper':
            side = int(prices[1]<prices[0])
        elif entry=='aligned':
            side = int(f['spot']<f['ref'])
        else:
            probs = [f['final_up_prob'],1-f['final_up_prob']]
            side = int(probs[1]-costs[1]>probs[0]-costs[0])
            if probs[side]-costs[side]<.05:
                return None
        if prices[side]>.55 or not allowed(s,side,5.,costs[side]):
            return None
        return dict(side=side,qty=5.,kind='first')
    if s['entered'] and not s['added'] and age==600 and arm in ('managed','unfiltered_add') and abs(net)>1e-6:
        side = 0 if net>0 else 1
        prob = f['final_up_prob'] if side==0 else 1-f['final_up_prob']
        if arm=='managed' and (prob-costs[side]<.05 or prices[side]>.55):
            return None
        if allowed(s,side,5.,costs[side]):
            return dict(side=side,qty=5.,kind='add')
    return None


def apply(s, intent, price, rate, when, quoted_unit_cost=None):
    side,qty = intent['side'],intent['qty']
    if side not in (0,1) or not math.isfinite(qty) or qty<=0 or intent['kind'] not in ('first','add','complete'):
        raise ValueError('invalid local intent')
    cost = unit_cost(price,rate) if quoted_unit_cost is None else quoted_unit_cost
    if not math.isfinite(cost) or cost<price:
        raise ValueError('invalid fee-inclusive cash cost')
    if intent['kind']=='complete' and complete_cost(s,side,qty,cost)>.98+1e-9:
        return False
    if not allowed(s,side,qty,cost):
        return False
    s['q'][side] += qty
    s['cash'] += qty*cost
    left = qty
    while left>1e-8 and s['lots'][1-side]:
        lot = s['lots'][1-side][0]
        take = min(left,lot[0])
        lot[0] -= take
        left -= take
        if lot[0]<1e-8:
            s['lots'][1-side].pop(0)
    if left>1e-8:
        s['lots'][side].append([left,cost])
    s['entered'] = True
    if intent['kind']=='add':
        s['added'] = True
    s['peak_risk'] = max(s['peak_risk'],s['cash']-min(s['q']))
    s['events'].append(dict(intent,price=price,cost=qty*cost,time=when))
    return True


def apply_book(s,intent,book,market,decision_ms,context,arm='managed'):
    """Finite public-book replay adapter; validates causal quote/depth, never sends an order."""
    side = intent['side']
    token = r.json.loads(market['clobTokenIds'])[side]
    if book.get('asset_id')!=token or book['requested_ms']<decision_ms+250:
        raise ValueError('wrong token or predecision execution book')
    received,observed = book['received_ms'],book['observed_ms']
    if not book['requested_ms']<=received<=decision_ms+3000 or not 0<=received-observed<=3000:
        raise ValueError('stale execution book')
    asks = book['asks']
    if not asks or any(not math.isfinite(p) or not math.isfinite(q) or not 0<p<1 or q<=0 for p,q in asks):
        raise ValueError('invalid execution depth')
    if asks!=sorted(asks) or not 0<book['bid']<asks[0][0] or asks[0][0]-book['bid']>.03+1e-9:
        raise ValueError('invalid/wide execution spread')
    cost,fee = r.base.ask_cost(book,market,intent['qty'])
    price,cash = cost/intent['qty'],(cost+fee)/intent['qty']
    if intent['kind']=='first' or (intent['kind']=='add' and arm=='managed'):
        prob = context['final_up_prob'] if side==0 else 1-context['final_up_prob']
        if price>.55 or prob-cash<.05:
            return False
    return apply(s,intent,price,0.,received/1000,quoted_unit_cost=cash)


def replay():
    universe = [w for w in r.read(r.OUT/'universe.json') if w['group']=='btc_15m']
    context = r.read(r.RAW/'btc15_context.json')
    histories = study.history_index()
    rows, coverage = [],Counter()
    for w in universe:
        market = r.read(r.RAW/'markets'/(w['slug']+'.json'))
        assert market.get('feesEnabled') and market['feeSchedule']['exponent']==1 and market['feeSchedule']['rate']==.07
        pair = histories[w['slug']]
        for entry in ('cheaper','aligned','discount'):
            for slip in (0.,.02,.05):
                for arm in ('entry_only','completion_only','managed','unfiltered_add'):
                    s, blocked_until = state(),0
                    gaps, eligible = Counter(),False
                    for age in range(180,841,60):
                        now = w['S']+age
                        if now<blocked_until:
                            gaps['waiting_execution_sample'] += 1
                            continue
                        h = study.at(pair,now-5)
                        f = context.get(f'{w["S"]}:{now}')
                        if h is None or f is None:
                            gaps['decision_data'] += 1
                            continue
                        if age==180:
                            eligible = True
                        prices = [min(.999,p+slip) for p in h['p']]
                        intent = decide(s,age,prices,f,arm,entry)
                        if intent is None:
                            continue
                        side = intent['side']
                        times, values = pair[side]
                        i = bisect.bisect_left(times,now+.25)
                        if i>=len(times) or times[i]>min(now+90,w['end']-1):
                            gaps['execution_sample'] += 1
                            continue
                        px = min(.999,float(values[i]['p'])+slip)
                        if not 0<px<1:
                            gaps['invalid_execution_sample'] += 1
                            continue
                        # Freeze the decision's value ceiling; do not accept arbitrary subsequent prices.
                        if intent['kind'] in ('first','add'):
                            if entry=='discount' and (intent['kind']=='first' or arm!='unfiltered_add'):
                                prob = f['final_up_prob'] if side==0 else 1-f['final_up_prob']
                                if prob-unit_cost(px,.07)<.05:
                                    gaps['execution_value_lost'] += 1
                                    continue
                            if (intent['kind']=='first' or arm=='managed') and px>.55:
                                gaps['execution_price_limit'] += 1
                                continue
                        blocked_until = times[i]
                        if not apply(s,intent,px,.07,times[i]):
                            gaps['execution_risk_or_pair_limit'] += 1
                    if eligible:
                        rows.append(dict(slug=w['slug'],S=w['S'],entry=entry,slip=slip,arm=arm,
                            pnl=s['q'][w['winner']]-s['cash'],**s,gaps=dict(gaps)))
                    else:
                        coverage[f'{entry}:{slip}:{arm}:ineligible'] += 1
    summaries = {}
    for entry in ('cheaper','aligned','discount'):
        for slip in (0.,.02,.05):
            for arm in ('entry_only','completion_only','managed','unfiltered_add'):
                rr = [x for x in rows if x['entry']==entry and x['slip']==slip and x['arm']==arm]
                result = study.uncertainty(rr)
                result.update(entries=sum(x['entered'] for x in rr),adds=sum(x['added'] for x in rr),
                        completions=sum(e['kind']=='complete' for x in rr for e in x['events']),
                        period_entries={p:sum(x['entered'] for x in rr if r.period(x['S'])==p)
                                        for p in ('discovery','chronological','update')},
                        max_peak_risk=max((x['peak_risk'] for x in rr),default=0),
                        cash=sum(x['cash'] for x in rr))
                summaries[f'{entry}:{slip}:{arm}'] = result
    for entry in ('cheaper','aligned','discount'):
        for slip in (0.,.02,.05):
            entries = [{x['slug'] for x in rows if x['entry']==entry and x['slip']==slip and x['arm']==arm and x['entered']}
                       for arm in ('entry_only','completion_only','managed','unfiltered_add')]
            assert all(a==entries[0] for a in entries), 'Control arms must share entry executions'
    fixed = {}
    for entry in ('cheaper','aligned','discount'):
        cohort = [x for x in rows if x['entry']==entry and x['slip']==0. and x['arm']=='entry_only' and x['entered']]
        fixed[entry] = {}
        for slip in (0.,.02,.05):
            normalized = []
            for x in cohort:
                original = x['events'][0]
                price = min(.999,original['price']+slip)
                extra = 5*unit_cost(price,.07)-original['cost']
                normalized.append(dict(x,pnl=x['pnl']-extra))
            fixed[entry][str(slip)] = study.uncertainty(normalized)
    r.save(r.OUT/'candidate_price_scenarios.json',dict(summary=summaries,missing=dict(coverage),
         fixed_zero_slippage_entry_cohort=fixed,
         disclaimer='Not an executable historical backtest. 1m sampled CLOB prices, no ask/spread/depth; '
                    'first subsequent sample+0/2/5c and fee is a sensitivity scenario. Normal TWAP probability '
                    'is an uncalibrated mechanism model. 36 exploratory combinations, no clean holdout.'))
    r.save(r.OUT/'candidate_scenario_rows.json',rows)
    print('Local price scenarios',len(rows),'rows',flush=True)


def check():
    s = state()
    f = dict(spot=101.,ref=100.,final_up_prob=.8)
    first = decide(s,180,[.4,.6],f)
    assert first==dict(side=0,qty=5.,kind='first')
    assert apply(s,first,.4,.07,180.3)
    partial = dict(side=1,qty=3.,kind='complete')
    assert apply(s,partial,.5,.07,240.3)
    assert s['q']==[5.,3.] and abs(s['lots'][0][0][0]-2)<1e-9
    c = decide(s,300,[.6,.35],f)
    assert c==dict(side=1,qty=2.,kind='complete')
    assert apply(s,c,.35,.07,300.3) and not any(s['lots'])
    assert decide(s,600,[.4,.6],f) is None  # No artificial reopen after neutralization.
    assert max(s['q'])<=10 and s['peak_risk']<=5
    s = state()
    assert apply(s,dict(side=0,qty=5.,kind='first'),.49,.07,180)
    assert not allowed(s,0,5.,.51)
    assert not apply(s,dict(side=1,qty=5.,kind='complete'),.70,.07,240)
    assert s['q']==[5.,0.]
    for bad in (float('nan'),float('inf'),0,1):
        try:
            unit_cost(bad,.07)
            raise AssertionError('invalid quote accepted')
        except ValueError:
            pass
    # Causal policy cannot inspect a future winner: no outcome is present in its inputs.
    assert decide(state(),180,[.4,.6],f)==first
    m = dict(clobTokenIds='["a","b"]',feesEnabled=True,feeSchedule=dict(exponent=1,rate=.07))
    book = dict(asset_id='a',requested_ms=180250,received_ms=180300,observed_ms=180200,
                bid=.39,asks=[(.4,2.),(.41,3.)])
    s = state()
    assert apply_book(s,first,book,m,180000,f)
    cost,fee = r.base.ask_cost(book,m,5)
    assert abs(s['cash']-cost-fee)<1e-9
    for bad in (dict(book,asks=[(.4,4.)]),dict(book,requested_ms=179999),
                dict(book,observed_ms=175000),dict(book,asset_id='wrong')):
        try:
            apply_book(state(),first,bad,m,180000,f)
            raise AssertionError('invalid book accepted')
        except ValueError:
            pass
    print('Policy: FIFO partial completion, no overcompletion/reopen, fees, price/risk limits passed')


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['check','replay'])
    globals()[p.parse_args().action]()
