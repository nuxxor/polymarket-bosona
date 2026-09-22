#!/usr/bin/env python3
"""Bosona BTC15m fills in markets recorded by F/raw/books_72h, from MY/raw/new_period cache.

Per closed market: fills, roles (fee signature), FIFO phases via frozen ledger(), late adds (age>=600, opening_kind add),
PnL vs official outcome; coverage flag from the book tape (first/last snapshot). Splits S-period (<=1790012700) vs later.
Writes MY/results/new_period_blind.json only."""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
MY = R/'fable_review_20260921'
sys.path.insert(0, str(R))
sys.path.insert(0, str(MY/'code'))
import research as r  # noqa: E402
from role_classifier import role_of_row  # noqa: E402

S_LAST = 1790012700   # last market fully inside the frozen S cut


def tape_bounds():
    first, last = None, None
    for p in sorted((R/'btc15_followup/raw/books_72h').glob('books_*.jsonl.gz')):
        try:
            with gzip.open(p, 'rt') as f:
                for line in f:
                    x = json.loads(line)
                    if x.get('kind') != 'books':
                        continue
                    first = x['received_ms'] if first is None else min(first, x['received_ms'])
                    last = x['received_ms'] if last is None else max(last, x['received_ms'])
        except EOFError:
            pass
    return first, last


def main():
    first_ms, last_ms = tape_bounds()
    rows = []
    for mf in sorted((MY/'raw/new_period/markets').glob('*.json')):
        m = json.load(open(mf))['data']
        meta = r.classify(m)
        assert meta['group'] == 'btc_15m'
        S, end = meta['S'], meta['end']
        try:
            winner = r.base.outcome(m)
        except ValueError:
            winner = None
        pages = json.load(open(MY/'raw/new_period/activity'/(m['slug']+'.json')))['pages']
        acts = [x for p in pages for x in p['rows']]
        trades = [x for x in acts if x['type'] == 'TRADE']
        assert all(x['conditionId'] == m['conditionId'] for x in trades)
        tokens = json.loads(m['clobTokenIds'])
        assert all(x['asset'] == tokens[x['outcomeIndex']] for x in trades)
        ledger, totals = r.base.ledger(trades, winner if winner is not None else 0) if trades else ([], dict(cash_cost_pnl=0.))
        roles = [role_of_row(x) for x in sorted(trades, key=lambda x: (x['timestamp'], x['transactionHash'], x['outcomeIndex']))]
        for f, rl in zip(ledger, roles):
            f['role'] = rl
        late = [f for f in ledger if f['opening_kind'] == 'add' and 600 <= f['age'] < 900]
        q = [sum(float(x['size']) for x in trades if x['outcomeIndex'] == i) for i in (0, 1)]
        cost = sum(float(x['usdcSize']) for x in trades)
        rows.append(dict(slug=m['slug'], S=S, end=end, period='S' if S <= S_LAST else 'after_S', winner=winner,
                         full=first_ms is not None and S*1000 >= first_ms and end*1000 <= last_ms,
                         fills=len(trades), roles=dict(Counter(roles)), qty=q, cost=round(cost, 6),
                         pnl=None if winner is None else round(q[winner]-cost, 6),
                         pnl_by_role=None if winner is None else {rl: round(sum(f['marginal_cash_pnl'] for f in ledger if f['role'] == rl), 4) for rl in ('maker', 'taker')},
                         late_adds=len(late), late_roles=dict(Counter(f['role'] for f in late)),
                         late_pnl=None if winner is None else round(sum(f['marginal_cash_pnl'] for f in late), 6),
                         worst_outcome=round(min(q)-cost, 6), best_outcome=round(max(q)-cost, 6), other_activity=dict(Counter(x['type'] for x in acts if x['type'] != 'TRADE'))))
    out = dict(tape_first_ms=first_ms, tape_last_ms=last_ms, markets=rows)
    for period in ('S', 'after_S'):
        rr = [x for x in rows if x['period'] == period and x['winner'] is not None and x['full']]
        late = [x for x in rr if x['late_adds']]
        out[period] = dict(full_closed=len(rr), traded=sum(x['fills'] > 0 for x in rr), fills=sum(x['fills'] for x in rr),
                           roles=dict(sum((Counter(x['roles']) for x in rr), Counter())), pnl=round(sum(x['pnl'] for x in rr), 4),
                           pnl_by_role={rl: round(sum(x['pnl_by_role'][rl] for x in rr if x['pnl_by_role']), 4) for rl in ('maker', 'taker')},
                           late_markets=len(late), late_fills=sum(x['late_adds'] for x in late), late_pnl=round(sum(x['late_pnl'] for x in late), 4),
                           late_roles=dict(sum((Counter(x['late_roles']) for x in late), Counter())),
                           pending_or_partial=[x['slug'] for x in rows if x['period'] == period and (x['winner'] is None or not x['full'])])
    json.dump(out, open(MY/'results/new_period_blind.json', 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('S', 'after_S', 'tape_first_ms', 'tape_last_ms')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
