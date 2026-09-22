#!/usr/bin/env python3
"""Concrete fill paths: pre-decision info -> inventory -> action/role -> risk change -> official outcome.
Historical: win 1789708500, loss 1789564500 (R/results/fills.json + R/raw/btc15_context.json).
New period: 1790001900 (S; -221.93, 18 late adds) and a no-trade window 1790007300 (books only)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from role_classifier import role  # noqa: E402

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
S = R/'btc15_followup/status_20260921_1800'
OUT = R/'fable_review_20260921/results'


def hist_rows(slug):
    fills = [f for f in json.load(open(R/'results/fills.json')) if f['slug'] == slug]
    ctx = json.load(open(R/'raw/btc15_context.json'))
    fills.sort(key=lambda f: (f['ts'], f['tx'], f['side']))
    rows = []
    for f in fills:
        c = ctx.get(f'{f["S"]}:{f["ts"]-5}')
        prob = None if not c else (c['final_up_prob'] if f['side'] == 0 else 1-c['final_up_prob'])
        h = f.get('price_context_5') or {}
        rows.append(dict(age=f['age'], side='Up' if f['side'] == 0 else 'Down', qty=round(f['qty'], 3), price=f['price'], cash_price=round(f['cash_price'], 5),
                         role=role(f['price'], f['cash_price'], f['qty']), kind=f['opening_kind'] or ('completion' if f['completion_qty'] > 1e-6 else None),
                         completion_qty=round(f['completion_qty'], 3), pre_net=round(f['pre_net'], 3), pre_worst=round(f['pre_worst_pnl'], 2), post_worst=round(f['post_worst_pnl'], 2),
                         model_prob_t5=None if prob is None else round(prob, 3), edge_t5=None if prob is None else round(prob-f['price'], 3),
                         public_price_t5=h.get('own'), pnl=round(f['marginal_cash_pnl'], 3), pair_pnl=round(f['pair_cash_pnl'], 3)))
    w = next(x for x in json.load(open(R/'results/windows.json')) if x['slug'] == slug)
    return dict(slug=slug, winner='Up' if w['winner'] == 0 else 'Down', total_pnl=round(w['cash_cost_pnl'], 2), qty=w['qty'], cost=round(w['cost'], 2),
                peak_worst_loss=round(w['peak_worst_loss'], 2), rows=rows)


def new_rows(slug):
    rows = json.load(open(OUT/'s_period_fills_role_book.json'))
    lvl = {(x['ts'], x['price'], x['qty']): x for x in json.load(open(OUT/'s_period_level_age.json'))}
    w = next(x for x in json.load(open(S/'results/windows.json')) if x['slug'] == slug)
    out = []
    q = [0., 0.]
    cash = 0.
    for r in sorted((x for x in rows if x['slug'] == slug), key=lambda x: (x['ts'], x['tx'])):
        pre_worst = min(q)-cash
        q[r['side']] += r['qty']
        cash += r['qty']*r['cash_price']
        la = lvl.get((r['ts'], r['price'], r['qty']), {})
        b = r.get('b5') or {}
        out.append(dict(age=r['age'], side='Up' if r['side'] == 0 else 'Down', qty=round(r['qty'], 3), price=r['price'], role=r['role'],
                        best_bid_t5=b.get('best_bid'), best_ask_t5=b.get('best_ask'), level_first_seen_lag=la.get('first_present_lag'),
                        level_age_s=la.get('level_age_from_presence'), pre_worst=round(pre_worst, 2), post_worst=round(min(q)-cash, 2), pnl=None if r['pnl'] is None else round(r['pnl'], 3)))
    return dict(slug=slug, winner='Up' if w['winner'] == 0 else 'Down', total_pnl=w['pnl'], qty=w['qty'], cost=w['cost'], late_adds=w['late_adds'], late_pnl=w['late_pnl'], rows=out)


def main():
    paths = dict(win=hist_rows('btc-updown-15m-1789708500'), loss=hist_rows('btc-updown-15m-1789564500'),
                 new_period_loss=new_rows('btc-updown-15m-1790001900'), new_period_win=new_rows('btc-updown-15m-1790001000'))
    json.dump(paths, open(OUT/'paths.json', 'w'), indent=1, ensure_ascii=False)
    for k, v in paths.items():
        print('==', k, v['slug'], 'winner', v['winner'], 'pnl', v['total_pnl'], 'n', len(v['rows']))
        for r in v['rows'][:60]:
            print('  ', r)


if __name__ == '__main__':
    main()
