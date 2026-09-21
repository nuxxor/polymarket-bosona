#!/usr/bin/env python3
"""Reproduce the bounded inventory diagnostic from frozen public-data snapshots."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
paths = dict(historical=ROOT/'data/analysis/bosona_gec_20260921/fill_ledger.json',
             latest=ROOT/'data/analysis/shadow_bosona_20260921_1200/fills.json',
             features=ROOT/'data/analysis/bosona_derin_20260921/features.json')
result = dict(source_sha256={k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()})
for label in ('historical', 'latest'):
    rows = json.loads(paths[label].read_text())
    if label == 'latest':
        rows = [r for r in rows if r['group'] == 'btc_5m']
    result[label] = dict(first_S=min(r['S'] for r in rows), last_S=max(r['S'] for r in rows))
    for kind in ('first', 'add', 'completion', 'reopen'):
        rs = [r for r in rows if (r['completion_qty'] > 0 if kind == 'completion' else r['opening_kind'] == kind)]
        windows = defaultdict(float)
        for r in rs:
            windows[r['S']] += r['marginal_cash_pnl']
        result[label][kind] = dict(records=len(rs), windows=len(windows),
                                  age_median=statistics.median(r['age'] for r in rs),
                                  cash_price_median=statistics.median(r['cash_price'] for r in rs),
                                  marginal_pnl=sum(windows.values()), ex_top3=sum(sorted(windows.values())[:-3]),
                                  pair_contribution=sum(r['pair_cash_pnl'] for r in rs),
                                  positive_pair_records=sum(r['pair_cash_pnl'] > 0 for r in rs))
features = json.loads(paths['features'].read_text())
result['historical_add_fair_edge'] = {}
for name, pred in [('all_with_context', lambda r: True),
                   ('edge_ge_3c', lambda r: r['fair_edge_paid'] >= .03),
                   ('edge_lt_3c', lambda r: r['fair_edge_paid'] < .03)]:
    rs = [r for r in features if r['kind'] == 'add' and 'fair_edge_paid' in r and pred(r)]
    windows = defaultdict(float)
    for r in rs:
        windows[r['S']] += r['pnl']
    result['historical_add_fair_edge'][name] = dict(records=len(rs), windows=len(windows),
                                                 pnl=sum(windows.values()), ex_top3=sum(sorted(windows.values())[:-3]),
                                                 equal5_per_fill=sum(5*r['pnl']/r['q'] for r in rs))
assert result['historical']['last_S'] < result['latest']['first_S']
result['caveat'] = ('Fill-conditioned descriptive accounting, not an executable backtest or a blind holdout. '
                    'Completion and reopening groups can overlap; do not sum them. No hidden order intent inferred.')
Path(__file__).with_name('inventory_research.json').write_text(json.dumps(result, indent=2)+'\n')
print('Research reproduced; source hashes and non-overlapping cohort dates checked.')
