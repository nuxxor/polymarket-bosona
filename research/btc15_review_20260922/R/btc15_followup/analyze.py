#!/usr/bin/env python3
"""Frozen-candidate diagnostics and matched BTC15m observations, not executable returns."""
from collections import Counter,defaultdict
import bisect
import json
import math
from pathlib import Path
import statistics as st
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,roc_auc_score,brier_score_loss
from sklearn.preprocessing import StandardScaler

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import research as r  # noqa: E402
import study  # noqa: E402
import candidate as c  # noqa: E402
OUT=HERE/'results'


def summary(rows,pnl='pnl'):
    return dict(n=len(rows),markets=len({x['slug'] for x in rows}),pnl=sum(x[pnl] for x in rows),
        median_price=st.median(x['price'] for x in rows) if rows else None)


def policy_state(row,when):
    s=c.state()
    if row:
        for e in row['events']:
            if e['time']<when:
                assert c.apply(s,e,e['price'],.07,e['time'])
    return s


def bucket(price,remaining,risk):
    return int(price*10+1e-9),min(4,int((remaining-1e-9)//60)),bisect.bisect_right([50,100,200],max(0,risk))


def entry_gate(w,hist,ctx,scenario):
    now=w['S']+180
    h=study.at(hist,now-5)
    f=ctx.get(f'{w["S"]}:{now}')
    if h is None or f is None:
        return dict(reason='decision_data_missing')
    probs=[f['final_up_prob'],1-f['final_up_prob']]
    edges=[probs[i]-c.unit_cost(h['p'][i],.07) for i in (0,1)]
    side=int(edges[1]>edges[0])
    v=dict(side=side,edge=edges[side],price=h['p'][side],probability_pass=edges[side]>=.05,ceiling_pass=h['p'][side]<=.55)
    if not v['probability_pass']:
        return dict(v,reason='probability')
    if not v['ceiling_pass']:
        return dict(v,reason='55c')
    if scenario and scenario['entered']:
        return dict(v,reason='entered')
    return dict(v,reason='execution_proxy_rejected',gaps=scenario['gaps'] if scenario else {})


def comparable(a,b):
    # Coarse cells alone left >$15 mean risk imbalance; fixed matching-quality calipers.
    return abs(a['price']-b['price'])<=.03+1e-9 and abs(a['age']-b['age'])<=30 and abs(a['risk']-b['risk'])<=25


def matched_outcomes(rows):
    cells=defaultdict(list)
    for x in rows:
        cells[bucket(x['price'],900-x['age'],x['risk'])].append(x)
    pairs=[]
    for key,v in sorted(cells.items()):
        winners=sorted((x for x in v if x['win']),key=lambda x:(x['S'],x['ts']))
        losers=[x for x in v if not x['win']]
        # Fixed calipers above, nearest price/time/risk within cell, no reuse.
        for a in winners:
            available=[b for b in losers if b['slug']!=a['slug'] and comparable(a,b)]
            if not available:
                continue
            b=min(available,key=lambda b:abs(a['price']-b['price'])/.1+abs(a['age']-b['age'])/60+abs(a['risk']-b['risk'])/50)
            losers.remove(b)
            pairs.append(dict(cell=key,win=a,loss=b))
    metrics={}
    for feature in ('price','age','risk','cost_basis','discount','momentum','edge','qty','risk_increase'):
        pp=[(p['win'][feature],p['loss'][feature]) for p in pairs if p['win'].get(feature) is not None and p['loss'].get(feature) is not None]
        metrics[feature]=dict(pairs=len(pp),win_mean=st.mean(a for a,b in pp) if pp else None,
            loss_mean=st.mean(b for a,b in pp) if pp else None,paired_mean_difference=st.mean(a-b for a,b in pp) if pp else None)
    return dict(pairs=len(pairs),metrics=metrics,examples=pairs[:12],all_pairs=pairs)


def bootstrap_difference(rows,values,unit):
    by=defaultdict(list)
    for x,v in zip(rows,values):
        by[x['slug'] if unit=='market' else x['S']//86400].append(float(v))
    aa=np.array([[sum(v),len(v)] for v in by.values()])
    rng=np.random.default_rng(20260921)
    ix=rng.integers(0,len(aa),size=(2000,len(aa)))
    sums=aa[ix].sum(axis=1)
    return np.quantile(sums[:,0]/sums[:,1],[.025,.975]).tolist()


def models(grid):
    # Three shared nuisance controls; fixed features, C=1, no grid search.
    common=['price','age','risk_log']
    specs={'base_rate':[], 'shared_controls':common, 'candidate':common+['candidate_time','ceiling_pass','probability_pass','candidate_inventory'],
        'H1_continuous_value':common+['edge','momentum'],
        'H2_inventory_cost':common+['discount','net_log','imbalance']}
    train=[x for x in grid if x['S']<r.SPLIT]
    test=[x for x in grid if r.SPLIT<=x['S']<r.UPDATE]
    yt=np.array([x['add'] for x in train],dtype=int)
    yy=np.array([x['add'] for x in test],dtype=int)
    fitted,predictions={},{}
    for name,features in specs.items():
        if features:
            a=np.array([[x[k] for k in features] for x in train],dtype=float)
            b=np.array([[x[k] for k in features] for x in test],dtype=float)
            scaler=StandardScaler().fit(a)
            model=LogisticRegression(C=1.,max_iter=1000).fit(scaler.transform(a),yt)
            p=model.predict_proba(scaler.transform(b))[:,1]
            fitted[name]=dict(features=features,mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),
                coefficients=model.coef_[0].tolist(),intercept=float(model.intercept_[0]))
        else:
            p=np.full(len(test),yt.mean())
        predictions[name]=p
    result={}
    loss={k:-(yy*np.log(p)+(1-yy)*np.log1p(-p)) for k,p in predictions.items()}
    for name,p in predictions.items():
        delta=loss['candidate']-loss[name]
        result[name]=dict(logloss=log_loss(yy,p),brier=brier_score_loss(yy,p),auc=roc_auc_score(yy,p),
            mean_loss_improvement_vs_candidate=float(delta.mean()),market_ci95=bootstrap_difference(test,delta,'market'),
            day_ci95=bootstrap_difference(test,delta,'day'),by_day={str(day):dict(n=sum(x['S']//86400==day for x in test),
                improvement=float(delta[[x['S']//86400==day for x in test]].mean())) for day in sorted({x['S']//86400 for x in test})})
    r.save(OUT/'hypothesis_models.json',dict(train_n=len(train),test_n=len(test),train_add_rate=float(yt.mean()),test_add_rate=float(yy.mean()),
        results=result,fitted=fitted,scope='Predict observed same-side addition in next30s, conditional on actor inventory. '
        'Use own inventory in future simulation; actor fills are NOT a permissible trigger. Not a profit model.'))
    r.save(OUT/'prediction_rows.json',[dict(slug=x['slug'],S=x['S'],age=x['age'],label=int(yy[i]),**{k:float(p[i]) for k,p in predictions.items()}) for i,x in enumerate(test)])
    return result


def run():
    windows=[w for w in r.read(r.OUT/'windows.json') if w['group']=='btc_15m']
    universe={w['slug']:w for w in r.read(r.OUT/'universe.json') if w['group']=='btc_15m'}
    fills=[f for f in r.read(r.OUT/'fills.json') if f['group']=='btc_15m']
    by=defaultdict(list)
    for f in fills:
        by[f['slug']].append(f)
    for v in by.values():
        v.sort(key=lambda f:(f['ts'],f['tx'],f['side']))
    ctx=r.read(r.RAW/'btc15_context.json')
    hist=study.history_index()
    scenarios={x['slug']:x for x in r.read(r.OUT/'candidate_scenario_rows.json') if x['entry']=='discount' and x['slip']==0 and x['arm']=='managed'}
    entry={s:entry_gate(w,hist[s],ctx,scenarios.get(s)) for s,w in universe.items()}
    late=[f for f in fills if f['opening_kind']=='add' and 600<=f['age']<900]
    diagnostics=[]
    for f in late:
        slug=f['slug']
        s=policy_state(scenarios.get(slug),f['ts']-5)
        net=s['q'][0]-s['q'][1]
        g=dict(slug=slug,S=f['S'],ts=f['ts'],side=f['side'],age=f['age'],price=f['price'],cash_price=f['cash_price'],pnl=f['marginal_cash_pnl'],
            initial=entry[slug],policy_entered=s['entered'],policy_net=net,policy_added=s['added'],
            direction_match=abs(net)>1e-8 and (0 if net>0 else 1)==f['side'],
            exact_clock=f['age']==600,first_30s_late=600<=f['age']<630,
            actual_ceiling_pass=f['price']<=.55,
            risk_pass_if_same_side=c.allowed(s,f['side'],5,c.unit_cost(f['price'],.07)),
            inventory_pass=s['entered'] and abs(net)>1e-8 and not s['added'])
        for lag in (5,10):
            a=ctx.get(f'{f["S"]}:{f["ts"]-lag}')
            h=study.at(hist[slug],f['ts']-lag)
            if a:
                prob=a['final_up_prob'] if f['side']==0 else 1-a['final_up_prob']
                g[f'actual_edge_{lag}']=prob-c.unit_cost(f['price'],.07)
            if a and h:
                g[f'proxy_edge_{lag}']=prob-c.unit_cost(h['p'][f['side']],.07)
                g[f'proxy_ceiling_{lag}']=h['p'][f['side']]<=.55
        diagnostics.append(g)
    gates={}
    for name in ('policy_entered','direction_match','exact_clock','first_30s_late','actual_ceiling_pass','risk_pass_if_same_side','inventory_pass'):
        gates[name]={str(flag):summary([x for x in diagnostics if x[name]==flag]) for flag in (True,False)}
    for lag in (5,10):
        key=f'actual_edge_{lag}'
        gates[key]={label:summary([x for x in diagnostics if (key not in x if label=='missing' else key in x and (x[key]>=.05)==(label=='pass'))]) for label in ('pass','fail','missing')}
    late_slugs={f['slug'] for f in late}
    entry_reasons={reason:dict(markets=sum(entry[s]['reason']==reason for s in late_slugs),
        fills=sum(entry[x['slug']]['reason']==reason for x in late),pnl=sum(x['marginal_cash_pnl'] for x in late if entry[x['slug']]['reason']==reason)) for reason in sorted({entry[s]['reason'] for s in late_slugs})}
    r.save(OUT/'misses.json',dict(total=summary(diagnostics),entry_reasons=entry_reasons,gates=gates,
        candidate_entry_markets=len([x for x in scenarios.values() if x['entered']]),
        candidate_adds=[x for x in scenarios.values() if x['added']],notes='Gates overlap; do not sum them. Raw fill-price gates are hindsight execution diagnostics, not decision inputs.'))
    r.save(OUT/'miss_rows.json',diagnostics)
    r.save(OUT/'entry_rows.json',entry)
    # Collapse one public second/side. This still does not recover order identity.
    bursts=defaultdict(list)
    for f in late:
        if not f['ambiguous']:
            bursts[f['slug'],f['ts'],f['side']].append(f)
    events=[]
    for (slug,ts,side),v in sorted(bursts.items()):
        first=v[0]
        q=sum(x['qty'] for x in v)
        px=sum(x['qty']*x['price'] for x in v)/q
        a=ctx.get(f'{first["S"]}:{ts-5}')
        prob=None if not a else a['final_up_prob'] if side==0 else 1-a['final_up_prob']
        events.append(dict(slug=slug,S=first['S'],ts=ts,side=side,age=first['age'],price=px,qty=q,
            win=side==first['winner'],pnl=sum(x['marginal_cash_pnl'] for x in v),risk=max(0,-first['pre_worst_pnl']),
            risk_increase=first['pre_worst_pnl']-v[-1]['post_worst_pnl'],cost_basis=first['previous_unmatched_price'],
            discount=first['previous_unmatched_price']-px,
            momentum=None if not a else (1 if side==0 else -1)*a['momentum10'],
            edge=None if prob is None else prob-c.unit_cost(px,.07)))
    r.save(OUT/'late_events.json',events)
    matched=matched_outcomes(events)
    r.save(OUT/'matched_win_loss.json',matched)
    # Common risk set includes observed non-actions; no dependence on future fills in features.
    grid=[]
    gaps=Counter()
    for w in windows:
        if w['ambiguous']:
            gaps['ambiguous_window']+=1
            continue
        slug=w['slug']
        ff=by[slug]
        for age in range(600,900,30):
            now=w['S']+age
            pre=[x for x in ff if x['ts']<=now-5]
            if any(now-5<x['ts']<now for x in ff):
                gaps['blind_5s_trade']+=1
                continue
            q=[sum(x['qty'] for x in pre if x['side']==i) for i in (0,1)]
            net=q[0]-q[1]
            if abs(net)<1e-6:
                gaps['no_open_inventory']+=1
                continue
            side=0 if net>0 else 1
            h=study.at(hist[slug],now-5)
            a=ctx.get(f'{w["S"]}:{now}')
            if h is None or a is None:
                gaps['context_missing']+=1
                continue
            cash=sum(x['qty']*x['cash_price'] for x in pre)
            # Reuse FIFO ledger; append a tiny diagnostic buy to expose post-prefix unmatched basis.
            raw=[dict(slug=slug,timestamp=x['ts'],transactionHash=x['tx'],outcomeIndex=x['side'],size=x['qty'],
                      price=x['price'],usdcSize=x['qty']*x['cash_price'],side='BUY') for x in pre]
            raw.append(dict(slug=slug,timestamp=now,transactionHash='zz',outcomeIndex=side,size=1e-7,price=.5,usdcSize=5e-8,side='BUY'))
            probe,_=r.base.ledger(raw,w['winner'])
            basis=probe[-1]['pre_unmatched_cash_cost']/abs(net)
            later=[x for x in ff if now<=x['ts']<now+30]
            add=[x for x in later if x['opening_kind']=='add' and x['side']==side]
            opposite=any(x['side']!=side for x in later)
            px=h['p'][side]
            prob=a['final_up_prob'] if side==0 else 1-a['final_up_prob']
            cs=policy_state(scenarios.get(slug),now)
            cnet=cs['q'][0]-cs['q'][1]
            grid.append(dict(slug=slug,S=w['S'],ts=now,age=age,side=side,price=px,risk=max(0,cash-min(q)),
                risk_log=math.log1p(max(0,cash-min(q))),net_log=math.log1p(abs(net)),imbalance=abs(net)/sum(q),
                cost_basis=basis,discount=basis-px,edge=prob-c.unit_cost(px,.07),momentum=(1 if side==0 else -1)*a['momentum10'],
                candidate_time=age==600,ceiling_pass=px<=.55,probability_pass=prob-c.unit_cost(px,.07)>=.05,
                candidate_inventory=cs['entered'] and not cs['added'] and abs(cnet)>1e-8 and (0 if cnet>0 else 1)==side,
                add=bool(add),no_trade=not later,opposite=opposite,other_action=bool(later) and not add,
                win=side==w['winner'],pnl=5*((side==w['winner'])-c.unit_cost(px,.07)),
                observed_add_pnl=sum(x['marginal_cash_pnl'] for x in add)))
    r.save(OUT/'risk_set.json',grid)
    # Exact strata, contrast added vs no observed trade. Equal weight each retained treated state.
    controls=defaultdict(list)
    for x in grid:
        if x['no_trade']:
            controls[bucket(x['price'],900-x['age'],x['risk'])].append(x)
    pairs=[]
    used=set()
    for x in sorted((x for x in grid if x['add']),key=lambda x:(x['S'],x['age'])):
        candidates=[v for v in controls[bucket(x['price'],900-x['age'],x['risk'])]
                    if v['slug']!=x['slug'] and (v['slug'],v['ts']) not in used and r.period(v['S'])==r.period(x['S']) and comparable(x,v)]
        if not candidates:
            continue
        y=min(candidates,key=lambda v:abs(x['price']-v['price'])/.1+abs(x['age']-v['age'])/60+abs(x['risk']-v['risk'])/50)
        used.add((y['slug'],y['ts']))
        pairs.append(dict(add=x,control=y,delta=x['pnl']-y['pnl']))
    compare={}
    for period in ('discovery','chronological','update'):
        pp=[x for x in pairs if r.period(x['add']['S'])==period]
        if not pp:
            continue
        # Normalize to one 5-share equivalent per treated market; no repeated-state scaling profit.
        by_market=defaultdict(list)
        for x in pp:
            by_market[x['add']['slug']].append(x)
        normalized=[dict(slug=s,S=v[0]['add']['S'],pnl=st.mean(x['delta'] for x in v)) for s,v in by_market.items()]
        compare[period]=dict(pairs=len(pp),add_win_rate=st.mean(x['add']['win'] for x in pp),control_win_rate=st.mean(x['control']['win'] for x in pp),
            matched_proxy_difference_per_market5=study.uncertainty(normalized),
            feature_differences={key:st.mean(x['add'][key]-x['control'][key] for x in pp) for key in ('price','risk','edge','momentum','discount','imbalance')})
    r.save(OUT/'no_add_controls.json',dict(grid_n=len(grid),gaps=dict(gaps),counts={key:sum(x[key] for x in grid) for key in ('add','no_trade','opposite','other_action')},
        matched=compare,pairs=pairs,notes='No observed trade is not no order. Price scenarios include assumed 7% p(1-p) taker fee, lack real historical ask. '
        'Repeated states and controls are dependent; intervals are descriptive, not a randomized causal effect.'))
    fitted=models(grid)
    print(json.dumps(dict(late_rows=len(late),entry_reasons=entry_reasons,matched_win_loss=matched['pairs'],grid=len(grid),models=fitted),ensure_ascii=False),flush=True)


if __name__=='__main__':
    run()
