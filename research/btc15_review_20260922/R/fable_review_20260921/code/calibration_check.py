#!/usr/bin/env python3
"""Brier score of the uncalibrated TWAP model (final_up_prob) vs the public market price sample at t-5,
by remaining time bucket, over all 20,533 recorded BTC15m contexts (R/raw/btc15_context.json)."""
import json
import sys
from collections import defaultdict
from pathlib import Path

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
sys.path.insert(0, str(R))
import study  # noqa: E402

OUT = R/'fable_review_20260921/results'


def main():
    ctx = json.load(open(R/'raw/btc15_context.json'))
    uni = {u['S']: u for u in json.load(open(R/'results/universe.json')) if u['group'] == 'btc_15m'}
    hist = study.history_index()
    acc = defaultdict(lambda: dict(n=0, b_model=0., b_market=0., b_drift=0., b_half=0., hits_model=0, hits_market=0))
    seen = set()
    for key, f in ctx.items():
        S, now = map(int, key.split(':'))
        u = uni.get(S)
        if not u or (S, now) in seen:
            continue
        seen.add((S, now))
        h = study.at(hist[u['slug']], now-5)
        if h is None:
            continue
        y = 1 if u['winner'] == 0 else 0
        pm, pk, pd = f['final_up_prob'], h['p'][0], f['final_drift_up_prob']
        rem = u['end']-now
        b = '720-600' if rem > 600 else '600-300' if rem > 300 else '300-60' if rem > 60 else '<60'
        for bb in (b, 'ALL'):
            a = acc[bb]
            a['n'] += 1
            a['b_model'] += (pm-y)**2
            a['b_market'] += (pk-y)**2
            a['b_drift'] += (pd-y)**2
            a['b_half'] += .25
            a['hits_model'] += (pm >= .5) == (y == 1)
            a['hits_market'] += (pk >= .5) == (y == 1)
    out = {k: dict(n=v['n'], brier_model=round(v['b_model']/v['n'], 4), brier_market=round(v['b_market']/v['n'], 4), brier_drift=round(v['b_drift']/v['n'], 4),
                   brier_coinflip=0.25, hit_model=round(v['hits_model']/v['n'], 3), hit_market=round(v['hits_market']/v['n'], 3)) for k, v in acc.items()}
    json.dump(out, open(OUT/'calibration_check.json', 'w'), indent=1)
    for k in ('720-600', '600-300', '300-60', '<60', 'ALL'):
        print(k, out.get(k))


if __name__ == '__main__':
    main()
