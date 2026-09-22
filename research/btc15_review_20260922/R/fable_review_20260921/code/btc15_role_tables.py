#!/usr/bin/env python3
"""Role x phase decomposition of frozen R/results/fills.json (all groups; BTC15m detail), day split,
late-add concentration, public-history adverse-selection proxy. Writes MY/results/*.json only."""
import bisect
import glob
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from role_classifier import role  # noqa: E402

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
OUT = R/'fable_review_20260921/results'


def phase(f):
    if f['completion_qty'] > 1e-6 and f['opening_qty'] > 1e-6:
        return 'mixed'
    if f['completion_qty'] > 1e-6:
        return 'completion'
    return f['opening_kind']


def main():
    fills = json.load(open(R/'results/fills.json'))
    for f in fills:
        f['role'] = role(f['price'], f['cash_price'], f['qty'])
        f['phase'] = phase(f)
    # all groups
    groups = defaultdict(lambda: defaultdict(lambda: dict(n=0, qty=0., pnl=0., cash=0.)))
    for f in fills:
        for key in (f['role'], 'ALL', f['phase']+'|'+f['role']):
            t = groups[f['group']][key]
            t['n'] += 1
            t['qty'] += f['qty']
            t['pnl'] += f['marginal_cash_pnl']
            t['cash'] += f['qty']*f['cash_price']
    json.dump({g: {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in d.items()} for g, d in groups.items()},
              open(OUT/'all_groups_role_table.json', 'w'), indent=1)
    b15 = [f for f in fills if f['group'] == 'btc_15m']
    tab = defaultdict(lambda: dict(n=0, qty=0., pnl=0., cash=0., markets=set()))
    for f in b15:
        for key in [(f['phase'], f['role']), ('ALL', f['role']), (f['phase'], 'ALL')]:
            t = tab[key]
            t['n'] += 1
            t['qty'] += f['qty']
            t['pnl'] += f['marginal_cash_pnl']
            t['cash'] += f['qty']*f['cash_price']
            t['markets'].add(f['slug'])
    table = {f'{k[0]}|{k[1]}': dict(records=t['n'], shares=round(t['qty'], 3), cash=round(t['cash'], 2), pnl=round(t['pnl'], 2),
                                    markets=len(t['markets']), cents_per_share=round(100*t['pnl']/t['qty'], 3) if t['qty'] else None)
             for k, t in sorted(tab.items(), key=lambda kv: str(kv[0]))}
    day = defaultdict(lambda: defaultdict(float))
    for f in b15:
        d = datetime.fromtimestamp(f['S'], timezone.utc).strftime('%Y-%m-%d')
        day[d][f['role']] += f['marginal_cash_pnl']
        day[d]['n_'+f['role']] += 1
    late = [f for f in b15 if f['opening_kind'] == 'add' and 600 <= f['age'] < 900]
    late_day = defaultdict(lambda: defaultdict(float))
    for f in late:
        d = datetime.fromtimestamp(f['S'], timezone.utc).strftime('%Y-%m-%d')
        late_day[d][f['role']] += f['marginal_cash_pnl']
        late_day[d]['n_'+f['role']] += 1
    conc = {}
    for rl in ('maker', 'taker'):
        by, q = defaultdict(float), defaultdict(float)
        for f in late:
            if f['role'] == rl:
                by[f['slug']] += f['marginal_cash_pnl']
                q[f['slug']] += f['qty']
        vals = sorted(by.values(), reverse=True)
        tot = sum(vals)
        conc[rl] = dict(records=sum(f['role'] == rl for f in late), markets=len(by), pnl=round(tot, 2), ex_top3=round(tot-sum(vals[:3]), 2),
                        ex_top10=round(tot-sum(vals[:10]), 2), positive_markets=sum(v > 0 for v in vals),
                        equal5_per_market=round(sum(5*by[s]/q[s] for s in by), 2))
    wins = [w for w in json.load(open(R/'results/windows.json')) if w['group'] == 'btc_15m']
    vals = sorted((w['cash_cost_pnl'] for w in wins), reverse=True)
    tot = sum(vals)
    total_conc = dict(markets=len(wins), pnl=round(tot, 2), ex_top3=round(tot-sum(vals[:3]), 2), ex_top10=round(tot-sum(vals[:10]), 2),
                      ex_top20=round(tot-sum(vals[:20]), 2), top10_share=round(sum(vals[:10])/tot, 3), positive_markets=sum(v > 0 for v in vals),
                      median_market=round(sorted(vals)[len(vals)//2], 2))
    tc = [f for f in b15 if f['role'] == 'taker' and f['completion_qty'] > 1e-6]
    mc = [f for f in b15 if f['role'] == 'maker' and f['completion_qty'] > 1e-6]
    completions = {rl: dict(records=len(v), pnl=round(sum(f['marginal_cash_pnl'] for f in v), 2),
                            worst_outcome_improvement=round(sum(f['post_worst_pnl']-f['pre_worst_pnl'] for f in v), 2),
                            improved=sum(f['post_worst_pnl'] > f['pre_worst_pnl']+1e-8 for f in v))
                   for rl, v in (('taker', tc), ('maker', mc))}
    # adverse-selection proxy from public 1-minute price samples (NOT asks)
    hist = {}
    for p in glob.glob(str(R/'raw/histories/*.json')):
        for tok, a in json.load(open(p))['response']['history'].items():
            hist[tok] = a
    toks = {}
    for w in wins:
        toks[w['slug']] = json.loads(json.load(open(R/'raw/markets'/(w['slug']+'.json')))['clobTokenIds'])

    def px(tok, when, maxage=90):
        a = hist.get(tok, [])
        ts = [x['t'] for x in a]
        i = bisect.bisect_right(ts, when)-1
        return None if i < 0 or when-ts[i] > maxage else float(a[i]['p'])
    res = defaultdict(list)
    for f in b15:
        tok = toks[f['slug']][f['side']]
        for h in (60, 120, 300):
            after = px(tok, f['ts']+h)
            if after is not None:
                res[(f['role'], f['phase'], h)].append(after-f['price'])
                res[(f['role'], 'ALL', h)].append(after-f['price'])
    adverse = {f'{k[0]}|{k[1]}|{k[2]}': dict(n=len(v), mean_c=round(100*st.mean(v), 3), median_c=round(100*st.median(v), 3)) for k, v in res.items()}
    fee_t = sum((f['cash_price']-f['price'])*f['qty'] for f in b15 if f['role'] == 'taker')
    reb_m = 0.2*0.07*sum(f['qty']*f['price']*(1-f['price']) for f in b15 if f['role'] == 'maker')
    out = dict(table=table, day={d: {k: round(v, 4) for k, v in day[d].items()} for d in sorted(day)},
               late_add_day={d: {k: round(v, 4) for k, v in late_day[d].items()} for d in sorted(late_day)},
               late_add_concentration=conc, total_concentration=total_conc, completions_by_role=completions,
               fees=dict(taker_fees_paid=round(fee_t, 2), maker_rebate_upper_20pct=round(reb_m, 2), taker_rebate_gold_18pct=round(0.18*fee_t, 2)),
               adverse_proxy=adverse, classifier='role_classifier.role (fee-relative tolerance)')
    json.dump(out, open(OUT/'btc15_role_phase_table.json', 'w'), indent=1)
    json.dump([dict(slug=f['slug'], S=f['S'], ts=f['ts'], tx=f['tx'], side=f['side'], qty=f['qty'], price=f['price'], cash_price=f['cash_price'], age=f['age'],
                    role=f['role'], phase=f['phase'], pnl=f['marginal_cash_pnl'], pre_worst=f['pre_worst_pnl'], post_worst=f['post_worst_pnl'], pre_net=f['pre_net'],
                    opening_kind=f['opening_kind'], completion_qty=f['completion_qty'], opening_qty=f['opening_qty']) for f in b15],
              open(OUT/'btc15_fills_with_role.json', 'w'))
    print(json.dumps(dict(all=Counter(f['role'] for f in fills), btc15=Counter(f['role'] for f in b15), late=Counter(f['role'] for f in late),
                          late_conc=conc, total_conc=total_conc, completions=completions, fees=out['fees'])))


if __name__ == '__main__':
    main()
