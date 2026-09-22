#!/usr/bin/env python3
"""Descriptive hypotheses and chronological controls; sampled prices are NOT asks."""
import argparse
import bisect
from collections import Counter, defaultdict
from datetime import datetime, timezone
import math
import statistics

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

import research as r


def history_index():
    history = {}
    for p in sorted((r.RAW/'histories').glob('*.json')):
        for token, a in r.read(p)['response']['history'].items():
            if token in history:
                assert history[token]==a
            history[token] = a
    result = {}
    for p in (r.RAW/'markets').glob('*.json'):
        m = r.read(p)
        tokens = r.json.loads(m['clobTokenIds'])
        result[p.stem] = [([x['t'] for x in history.get(t,[])], history.get(t,[])) for t in tokens]
    return result


def at(pair, when, age=75):
    result, ages = [], []
    for times, vals in pair:
        i = bisect.bisect_right(times,when)-1
        if i<0 or not 0<=when-times[i]<=age:
            return None
        price = float(vals[i]['p'])
        if not 0<price<1:
            return None
        result.append(price)
        ages.append(when-times[i])
    return dict(p=result, ages=ages)


def uncertainty(rows):
    summary = r.stat(rows)
    by, days = defaultdict(float), defaultdict(float)
    for x in rows:
        by[x['slug']] += x['pnl']
        days[x['S']//86400] += x['pnl']
    rng = np.random.default_rng(20260921)
    for name, values in [('market',list(by.values())),('day',list(days.values()))]:
        if values:
            draws = rng.choice(values,(2000,len(values)),replace=True).sum(axis=1)
            summary[name+'_ci95'] = np.quantile(draws,[.025,.975]).tolist()
    return summary


def section(ff):
    groups = defaultdict(list)
    for f in ff:
        groups[f['slug']].append(f)
    normal = [dict(a[0],pnl=5*sum(x['marginal_cash_pnl'] for x in a)/sum(x['qty'] for x in a))
              for a in groups.values()]
    actual = [dict(f,pnl=f['marginal_cash_pnl']) for f in ff]
    return dict(actual=uncertainty(actual),equal5=uncertainty(normal),
                shares=sum(f['qty'] for f in ff),
                unambiguous=r.stat([x for x in actual if not x['ambiguous']]))


def behavior():
    windows, fills = r.read(r.OUT/'windows.json'), r.read(r.OUT/'fills.json')
    histories = history_index()
    for f in fills:
        for lag in (5,10):
            h = at(histories[f['slug']],f['ts']-lag)
            if h:
                own, opp = h['p'][f['side']],h['p'][1-f['side']]
                f[f'price_context_{lag}'] = dict(own=own,other=opp,
                       favorite=own>opp,price_age=max(h['ages']),paid_gap=f['cash_price']-own)
    groups = {}
    for g in sorted({w['group'] for w in windows}):
        ff = [f for f in fills if f['group']==g]
        ww = [w for w in windows if w['group']==g]
        predicates = {
            'all_add':lambda f:f['opening_kind']=='add',
            'late_third_add':lambda f:f['opening_kind']=='add' and 2/3<=f['age']/f['duration']<1,
            'late_third_rising_add':lambda f:f['opening_kind']=='add' and 2/3<=f['age']/f['duration']<1
                   and (f['price_change_same'] or 0)>.005,
            'late_third_cheaper_add':lambda f:f['opening_kind']=='add' and 2/3<=f['age']/f['duration']<1
                   and (f['price_change_same'] or 0)<-.005,
            'late_third_favorite_add':lambda f:f['opening_kind']=='add' and 2/3<=f['age']/f['duration']<1
                   and f.get('price_context_5',{}).get('favorite') is True,
            'late_third_underdog_add':lambda f:f['opening_kind']=='add' and 2/3<=f['age']/f['duration']<1
                   and f.get('price_context_5',{}).get('favorite') is False,
            'last20_add':lambda f:f['opening_kind']=='add' and 0<f['duration']-f['age']<=20,
        }
        result = {name:section([f for f in ff if fn(f)]) for name,fn in predicates.items()}
        firsts = [f for f in ff if f['ts']==f['S']+next(w['first_age'] for w in ww if w['slug']==f['slug'])]
        first_details = {}
        for lag in (5,10):
            chosen = [f for f in firsts if f.get(f'price_context_{lag}')]
            qty = sum(f['qty'] for f in chosen)
            first_details[str(lag)] = dict(records=len(chosen),shares=qty,
                  favorite_share=sum(f['qty'] for f in chosen if f[f'price_context_{lag}']['favorite'])/qty if qty else None,
                  median_paid_minus_history=statistics.median(f[f'price_context_{lag}']['paid_gap'] for f in chosen) if chosen else None,
                  median_history_age=statistics.median(f[f'price_context_{lag}']['price_age'] for f in chosen) if chosen else None)
        proxy = [f for f in firsts if 'distance_bp' in f['context_5']]
        first_details['spot_proxy'] = dict(records=len(proxy),
              aligned=sum((1 if f['side']==0 else -1)*f['context_5']['distance_bp']>0 for f in proxy),
              momentum1_aligned=sum((1 if f['side']==0 else -1)*f['context_5']['return1']>0 for f in proxy))
        result['first'] = first_details
        completion = [f for f in ff if f['completion_qty']>1e-6]
        comp_bins = {}
        for label,lo,hi in [('cheap_pair',-10,.98),('near_par',.98,1.000001),('costly_pair',1.000001,10)]:
            part = [f for f in completion if lo<=1-f['completion_unit_pair_pnl']<hi]
            comp_bins[label] = dict(n=len(part),markets=len({f['slug'] for f in part}),
                qty=sum(f['completion_qty'] for f in part),pair_pnl=sum(f['pair_cash_pnl'] for f in part),
                losing_markets=len({f['slug'] for f in part if f['window_pnl']<0}),
                overfill=sum(f['opening_qty']>1e-6 for f in part),
                risk_reduced=sum(f['post_worst_pnl']>f['pre_worst_pnl']+1e-8 for f in part))
        result['completion_bins'] = comp_bins
        # Every completed pair improves the worst payoff before overfill, even above par.
        result['cases'] = {kind:[w['slug'] for w in sorted(ww,key=lambda w:w['cash_cost_pnl'],reverse=kind=='best')[:3]]
                           for kind in ('best','worst')}
        result['daily_style'] = {day:dict(n=len(v),both=sum(min(w['qty'])>1e-6 for w in v)/len(v),
                                      pnl=sum(w['cash_cost_pnl'] for w in v))
             for day,v in group_days(ww).items()}
        groups[g] = result
    r.save(r.OUT/'context_fills.json',fills)
    r.save(r.OUT/'behavior.json',groups)
    print('behavior groups',len(groups),'fills',len(fills),flush=True)


def group_days(rows):
    result = defaultdict(list)
    for x in rows:
        result[datetime.fromtimestamp(x['S'],timezone.utc).strftime('%Y-%m-%d')].append(x)
    return result


def model(rows, variants):
    output = {}
    for name, features in variants.items():
        dictionaries = [{key:x[key] for key in features} for x in rows]
        train = np.array([x['S']<r.SPLIT for x in rows])
        vec = DictVectorizer(sparse=False)
        xx = vec.fit_transform([d for d,t in zip(dictionaries,train) if t])
        scaler = StandardScaler().fit(xx)
        xx = scaler.transform(xx)
        y = np.array([x['y'] for x in rows])
        clf = LogisticRegression(C=1,max_iter=1000).fit(xx,y[train])
        xall = scaler.transform(vec.transform(dictionaries))
        predicted = clf.predict_proba(xall)[:,1]
        output[name] = {}
        for p in ('discovery','chronological','update'):
            use = np.array([r.period(x['S'])==p for x in rows])
            output[name][p] = dict(n=int(use.sum()),positive=int(y[use].sum()),
                   logloss=float(log_loss(y[use],predicted[use],labels=[0,1])) if use.sum() else None,
                   brier=float(np.mean((y[use]-predicted[use])**2)) if use.sum() else None,
                   auc=float(roc_auc_score(y[use],predicted[use])) if len(set(y[use]))>1 else None)
        output[name]['by_day'] = {}
        for day in sorted({x['S']//86400 for x in rows}):
            use = np.array([x['S']//86400==day for x in rows])
            output[name]['by_day'][str(day)] = dict(n=int(use.sum()),logloss=float(log_loss(y[use],predicted[use],labels=[0,1])))
    return output


def selection():
    windows = r.read(r.OUT/'windows.json')
    universe = [w for w in r.read(r.OUT/'universe.json') if w['group'] in r.PRIMARY]
    index = {w['slug']:w for w in windows}
    bars = r.load_bars()
    prices = history_index()
    fills = sorted(r.read(r.OUT/'fills.json'),key=lambda f:f['ts'])
    queries = sorted([(w['S']+age-5,w,age) for w in universe
                      for age in (0,w['duration']//3,2*w['duration']//3)],key=lambda x:x[0])
    pointer, inventory = 0, {}
    rows, gaps = [], Counter()
    for when,w,age in queries:
        owned = index.get(w['slug'])
        first_time = owned['S']+owned['first_age'] if owned else math.inf
        if first_time<=when:
            gaps['already_entered'] += 1
            continue
        while pointer<len(fills) and fills[pointer]['ts']<=when:
            f = fills[pointer]
            inv = inventory.setdefault(f['slug'],dict(q=[0.,0.],cost=0.,end=f['end']))
            inv['q'][f['side']] += f['qty']
            inv['cost'] += f['qty']*f['cash_price']
            pointer += 1
        inventory = {k:v for k,v in inventory.items() if v['end']>when}
        f = r.features(bars[w['sym']],w['S'],when)
        h = at(prices[w['slug']],when)
        if not f:
            gaps['bars'] += 1
            continue
        localhour = ((when//3600)+3)%24
        row = dict(slug=w['slug'],S=w['S'],group=w['group'],y=int(first_time< w['S']+age+w['duration']//3),
           age=age/w['duration'],sin_hour=math.sin(localhour*math.pi/12),cos_hour=math.cos(localhour*math.pi/12),
           night=int(localhour<6),volatility=f['volatility_bp'],log_volume=math.log1p(f['volume5']),
           relative_volume=f['volume_ratio'],return1=abs(f['return1']),return5=abs(f['return5']),
           distance=abs(f.get('distance_bp',0.)),missing_distance=int('distance_bp' not in f),
           price_distance=abs(h['p'][0]-h['p'][1]) if h else 0.,missing_price=int(h is None),
           active=len(inventory),risk=math.log1p(sum(max(0.,v['cost']-min(v['q'])) for v in inventory.values())))
        rows.append(row)
    baseline = ['group','age']
    clock = ['sin_hour','cos_hour','night']
    market = ['volatility','log_volume','relative_volume','return1','return5','distance','missing_distance',
              'price_distance','missing_price']
    variants = dict(baseline=baseline,clock=baseline+clock,market=baseline+market,
                    market_inventory=baseline+market+['active','risk'],full=baseline+market+['active','risk']+clock)
    result = model(rows,variants)
    r.save(r.OUT/'selection_rows.json',rows)
    r.save(r.OUT/'selection.json',dict(models=result,gaps=dict(gaps),
           note='First-fill hazard in three risk-set intervals; observational, not order intent. '
                'Inventory only analyzed non-BTC5 cohorts, excludes hidden orders and pre-cohort positions. '
                'Public price samples lag by up to75s, not historical spread/liquidity. Train13-17; no threshold search.'))
    print('selection rows',len(rows),flush=True)
    # Does a shared first-fill profile remove the differences in two-sided behavior?
    styles = []
    for w in windows:
        if w['group'] not in r.PRIMARY or not w['first_context']:
            continue
        f = w['first_context']
        styles.append(dict(slug=w['slug'],S=w['S'],y=int(min(w['qty'])>1e-6),group=w['group'],
               price=w['first_price'],age=w['first_age']/w['duration'],size=math.log1p(w['first_qty']),
               volatility=f['volatility_bp'],return1=abs(f['return1']),volume=math.log1p(f['volume5'])))
    common = ['price','age','size','volatility','return1','volume']
    r.save(r.OUT/'style_models.json',model(styles,dict(shared=common,by_market=common+['group'])))


def check():
    pair = [([100,200],[dict(t=100,p=.4),dict(t=200,p=.9)]),
            ([100,200],[dict(t=100,p=.6),dict(t=200,p=.1)])]
    assert at(pair,150)['p']==[.4,.6]
    assert at(pair,99) is None and at(pair,176) is None
    assert at(pair,200)['p']==[.9,.1]
    a = dict(S=0,slug='a',pnl=1.)
    b = dict(S=0,slug='b',pnl=-2.)
    assert uncertainty([a,b])['markets']==2  # Same start is NOT same market.
    print('Price as-of, stale/future and cross-market clustering checks passed')


def mechanism():
    windows = r.read(r.OUT/'windows.json')
    fills = r.read(r.OUT/'context_fills.json')
    exact = r.read(r.RAW/'btc15_context.json')
    hypotheses = {}
    for lag in (5,10):
        eligible = []
        for f in fills:
            if f['group']!='btc_15m' or f['opening_kind']!='add' or not 600<=f['age']<900:
                continue
            ctx = exact.get(f'{f["S"]}:{f["ts"]-lag}')
            if ctx:
                prob = ctx['final_up_prob'] if f['side']==0 else 1-ctx['final_up_prob']
                eligible.append(dict(f,discount=prob-f['cash_price'],
                                     own_momentum=(1 if f['side']==0 else -1)*ctx['momentum10']))
        hypotheses[str(lag)] = {name:section([f for f in eligible if fn(f)]) for name,fn in {
            'covered':lambda f:True,'prob_discount_ge5c':lambda f:f['discount']>=.05,
            'prob_discount_lt5c':lambda f:f['discount']<.05,
            'momentum_positive':lambda f:f['own_momentum']>0,
            'momentum_nonpositive':lambda f:f['own_momentum']<=0}.items()}
    r.save(r.OUT/'btc15_mechanism.json',hypotheses)
    # Compare choices using public context alone versus the preceding observed inventory.
    choices, seen = [],set()
    for f in fills:
        identity = (f['slug'],f['ts'])
        if f['group'] not in r.PRIMARY or f['ambiguous'] or identity in seen:
            continue
        seen.add(identity)
        c = f['context_5']
        h = f.get('price_context_5')
        if not c or h is None:
            continue
        choices.append(dict(slug=f['slug'],S=f['S'],y=int(f['side']==0),group=f['group'],
            age=f['age']/f['duration'],market_up=h['own'] if f['side']==0 else h['other'],
            momentum=c['return1'],rsi=c['rsi14'],volatility=c['volatility_bp'],
            distance=c.get('distance_bp',0),missing_ref=int('distance_bp' not in c),
            prior_net=math.copysign(math.log1p(abs(f['pre_net'])),f['pre_net']),
            prior_cost=math.log1p(f['pre_unmatched_cash_cost']),floor=f['pre_worst_pnl'],
            first=int(f['ts']==f['S']+next(w['first_age'] for w in windows if w['slug']==f['slug']))))
    external = ['group','age','market_up','momentum','rsi','volatility','distance','missing_ref']
    later = [x for x in choices if not x['first']]
    r.save(r.OUT/'next_side_models.json',model(later,dict(market=external,market_inventory=external+['prior_net','prior_cost','floor'])))
    r.save(r.OUT/'next_side_rows.json',later)
    by = defaultdict(list)
    for f in fills:
        by[f['slug']].append(f)
    conditional = []
    for w in windows:
        if w['group'] not in r.PRIMARY or w['ambiguous'] or w['first_side'] is None:
            continue
        firstside, fp = w['first_side'],w['first_price']
        cost, qty = 5*fp,[0.,0.]
        qty[firstside] = 5.
        hold = qty[w['winner']]-cost
        completion = None
        for f in by[w['slug']]:
            if f['ts']<=w['S']+w['first_age'] or f['side']==firstside:
                continue
            if fp+f['cash_price']<=.98:
                qty[1-firstside] = 5.
                cost += 5*f['cash_price']
                completion = f['ts']
                break
        conditional.append(dict(slug=w['slug'],S=w['S'],group=w['group'],hold=hold,
             complete=qty[w['winner']]-cost,pnl=qty[w['winner']]-cost-hold,completed=completion is not None))
    summaries = {g:dict(delta=uncertainty([x for x in conditional if x['group']==g]),
             hold=sum(x['hold'] for x in conditional if x['group']==g),
             complete=sum(x['complete'] for x in conditional if x['group']==g),
             completed=sum(x['completed'] for x in conditional if x['group']==g)) for g in r.PRIMARY}
    r.save(r.OUT/'conditional_completion.json',dict(groups=summaries,
          note='Actor-conditioned accounting: first batch scaled to5; later actual actor fill price '
               'is an assumed opportunity, not an available ask/our execution. No fees beyond observed cash; '
               'simultaneous opposite-side windows excluded. Does not identify an independent entry rule.'))
    r.save(r.OUT/'conditional_completion_rows.json',conditional)
    print('Exact BTC15 context, later choice prediction and conditional completion checks complete')


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['behavior','selection','mechanism','check'])
    globals()[p.parse_args().action]()
