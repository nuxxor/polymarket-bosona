#!/usr/bin/env python3
"""Audit observed-action labels and shared-market dependence, without selecting a strategy."""
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics as st
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
F = R / 'btc15_followup'
OUT = HERE / 'statistics'


def read(p):
    return json.loads(p.read_text())


def components(pairs):
    """Include both arms; a shared control market couples treated-market estimates."""
    parent = {}

    def root(x):
        parent.setdefault(x, x)
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in pairs:
        a, b = (root(p[k]['slug']) for k in ('add', 'control'))
        parent[b] = a
    return {x: root(x) for x in parent}


def summarize(pairs):
    by = defaultdict(list)
    for p in pairs:
        by[p['add']['slug']].append(p)
    normalized = {k: st.mean(p['delta'] for p in v) for k, v in by.items()}
    graph = components(pairs)
    sums = defaultdict(float)
    for slug, value in normalized.items():
        sums[graph[slug]] += value
    rng = np.random.default_rng(20260921)
    ci = np.quantile(rng.choice(list(sums.values()), (4000, len(sums))).sum(axis=1), [.025,.975]).tolist() if sums else None
    controls = Counter(p['control']['slug'] for p in pairs)
    days = sorted({p['add']['S']//86400 for p in pairs})
    return dict(pairs=len(pairs),treated_markets=len(by),control_markets=len(controls),
        reused_control_markets=sum(n>1 for n in controls.values()),max_control_states=max(controls.values(),default=0),
        both_arm_markets=len(set(by)&set(controls)),connected_components=len(sums),
        component_market_counts=sorted(Counter(graph.values()).values(),reverse=True),
        cross_day_pairs=sum(p['add']['S']//86400 != p['control']['S']//86400 for p in pairs),
        difference=sum(normalized.values()),ex_top3=sum(sorted(normalized.values(),reverse=True)[3:]),
        connected_market_bootstrap_sum_ci95=ci,
        by_treated_day={str(d):sum(value for slug,value in normalized.items() if by[slug][0]['add']['S']//86400==d) for d in days},
        drop_each_treated_day={str(d):sum(value for slug,value in normalized.items() if by[slug][0]['add']['S']//86400!=d) for d in days},
        warning='Connected-component sensitivity is descriptive; cross-day common shocks remain. Three control days cannot establish stable coverage.')


def rematch(grid, a, same_day=False, unique_markets=False):
    controls = [x for x in grid if x['no_trade']]
    pairs, used_states, used_markets = [], set(), set()
    for x in sorted((x for x in grid if x['add'] and not x['opposite']),key=lambda x:(x['S'],x['age'])):
        if unique_markets and x['slug'] in used_markets:
            continue
        available = [y for y in controls if y['slug'] != x['slug']
            and (y['slug'],y['ts']) not in used_states
            and (not unique_markets or y['slug'] not in used_markets)
            and (not same_day or y['S']//86400 == x['S']//86400)
            and a.bucket(x['price'],900-x['age'],x['risk']) == a.bucket(y['price'],900-y['age'],y['risk'])
            and a.comparable(x,y)]
        if available:
            y = min(available,key=lambda y:abs(x['price']-y['price'])/.1+abs(x['age']-y['age'])/60+abs(x['risk']-y['risk'])/50)
            used_states.add((y['slug'],y['ts']))
            used_markets.update((x['slug'],y['slug']))
            pairs.append(dict(add=x,control=y,delta=x['pnl']-y['pnl']))
    return pairs


def main():
    spec = importlib.util.spec_from_file_location('followup_analyze',F/'analyze.py')
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    grid = read(F/'results/risk_set.json')
    pairs = read(F/'results/no_add_controls.json')['pairs']
    fills = [x for x in read(R/'results/fills.json') if x['group']=='btc_15m']
    windows = [x for x in read(R/'results/windows.json') if x['group']=='btc_15m']
    hist = a.study.history_index()
    contexts = read(R/'raw/btc15_context.json')
    by = defaultdict(list)
    for f in fills:
        by[f['slug']].append(f)
    future_exclusions = []
    for w in windows:
        if not w['ambiguous']:
            continue
        times = defaultdict(set)
        for f in by[w['slug']]:
            times[f['ts']].add(f['side'])
        first_amb = min(t for t,sides in times.items() if len(sides)>1)
        for age in range(600,900,30):
            now = w['S']+age
            ff = by[w['slug']]
            pre = [f for f in ff if f['ts']<=now-5]
            net = sum((1 if f['side']==0 else -1)*f['qty'] for f in pre)
            if now < first_amb and abs(net)>1e-6 and not any(now-5<f['ts']<now for f in ff):
                available = a.study.at(hist[w['slug']],now-5) is not None and f'{w["S"]}:{now}' in contexts
                future_exclusions.append(dict(slug=w['slug'],age=age,first_ambiguous_age=first_amb-w['S'],context_available=available))
    result = dict(seed=20260921,grid=len(grid),markets=len({x['slug'] for x in grid}),
        universe=816,traded=598,counts={k:sum(bool(x[k]) for x in grid) for k in ('add','opposite','no_trade','other_action')},
        mixed_add_opposite=sum(x['add'] and x['opposite'] for x in grid),
        mixed_add_opposite_markets=len({x['slug'] for x in grid if x['add'] and x['opposite']}),
        future_ambiguity_excluded_states=future_exclusions,periods={})
    for period in ('discovery','chronological'):
        pp = [x for x in pairs if a.r.period(x['add']['S'])==period]
        gg = [x for x in grid if a.r.period(x['S'])==period]
        result['periods'][period] = dict(original=summarize(pp),
            remove_mixed=summarize([p for p in pp if not p['add']['opposite']]),
            same_day_exclusive=summarize(rematch(gg,a,same_day=True)),
            one_state_one_market=summarize(rematch(gg,a,same_day=True,unique_markets=True)),
            states=len(gg),adds=sum(x['add'] for x in gg),no_add_accuracy=1-st.mean(x['add'] for x in gg),
            markets=len({x['slug'] for x in gg}))
    # Actual inventory shift, not a model learned from actor positions magically transported to 5 shares.
    actor_net=np.array([np.expm1(x['net_log']) for x in grid])
    result['inventory_shift']=dict(actor_abs_net_quantiles=np.quantile(actor_net,[0,.25,.5,.75,1]).tolist(),
        states_actor_net_above_candidate_max10=int((actor_net>10+1e-6).sum()),
        states_actor_risk_above_candidate_max5=sum(x['risk']>5+1e-6 for x in grid),
        states_candidate_inventory_true=sum(x['candidate_inventory'] for x in grid),
        candidate_max_net=10,candidate_max_loss=5)
    # Equal cash and equal pre-action risk are scaling diagnostics, not counterfactual decisions.
    late=[f for f in fills if f['opening_kind']=='add' and 600<=f['age']<900
          and f['ts']>min(x['ts'] for x in by[f['slug']])]
    late_by=defaultdict(list)
    for f in late:
        late_by[f['slug']].append(f)
    scaled=[]
    for slug,ff in late_by.items():
        pnl=sum(f['marginal_cash_pnl'] for f in ff)
        qty=sum(f['qty'] for f in ff)
        cash=sum(f['qty']*f['cash_price'] for f in ff)
        peak=next(w['peak_worst_loss'] for w in windows if w['slug']==slug)
        scaled.append(dict(slug=slug,S=ff[0]['S'],actual=pnl,equal5shares=5*pnl/qty,
                           equal5cash=5*pnl/cash,equal5whole_market_peak_risk=5*pnl/peak))
    result['corrected_late_scale']={k:dict(total=sum(x[k] for x in scaled),
        ex_top3=sum(sorted((x[k] for x in scaled),reverse=True)[3:]),
        by_day={str(d):sum(x[k] for x in scaled if x['S']//86400==d) for d in sorted({x['S']//86400 for x in scaled})})
        for k in ('actual','equal5shares','equal5cash','equal5whole_market_peak_risk')}
    result['scaling_warning']='Realized market peak risk uses the full observed path: ex-post normalization only, never a sizing rule.'
    reproduced=OUT/'reproduced'
    result['reproduction']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256((F/'results'/p.name).read_bytes()).hexdigest() for p in reproduced.glob('*.json')}
    OUT.mkdir(exist_ok=True)
    (OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'scaled_late_rows.json').write_text(json.dumps(scaled,ensure_ascii=False)+'\n')
    assert result['mixed_add_opposite']==sum(x['add'] for x in grid)-sum(x['add'] and not x['opposite'] for x in grid)
    assert result['reproduction'] and all(result['reproduction'].values())
    # Regression: shared control connects otherwise separate treated markets.
    p=[dict(add=dict(slug='a'),control=dict(slug='c')),dict(add=dict(slug='b'),control=dict(slug='c'))]
    assert len(set(components(p).values()))==1
    print(json.dumps({k:result[k] for k in ('mixed_add_opposite','inventory_shift','periods','reproduction')},ensure_ascii=False))


if __name__=='__main__':
    main()
