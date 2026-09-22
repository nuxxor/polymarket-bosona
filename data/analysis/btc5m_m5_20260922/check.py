"""Check frozen telemetry, chain reconciliation, null clocks and queue mismatch."""
from copy import deepcopy
import json

from prepare import OUT, SOURCE, lifetimes, read
from analyze import eligible

trace = [json.loads(s) for s in (SOURCE/'LOG_f_emir_iz.jsonl').read_text().splitlines()]
logs = [json.loads(s) for s in (SOURCE/'LOG_f.jsonl').read_text().splitlines()]
state = read(SOURCE/'STATE_f.json')
assert lifetimes(trace, state, logs) == read(OUT/'orders.json')
for bad in (trace[:-2]+trace[-1:], trace+[trace[-1]]):
    try:
        lifetimes(bad, state, logs)
    except AssertionError:
        pass
    else:
        raise AssertionError('Missing or duplicate telemetry was accepted')
bad = deepcopy(state)
for w in bad['pen'].values():
    for order in w['emir']:
        if order.get('oid') == read(OUT/'orders.json')[0]['oid']:
            order['pay'] = 1
try:
    lifetimes(trace, bad, logs)
except AssertionError:
    pass
else:
    raise AssertionError('State/exchange quantity mismatch was accepted')
assert eligible(dict(side=0, price=.5000001, qty=5), dict(oi=0, price=.5))
assert not eligible(dict(side=0, price=.501, qty=5), dict(oi=0, price=.5))
assert not eligible(dict(side=1, price=.4, qty=5), dict(oi=0, price=.5))
report = read(OUT/'report.json')
rows, summary = report['rows'], report['summary']
assert summary['accepted'] == 12 and summary['own_chain_shares'] == 20
assert summary['own_chain_fills'] == 5 and summary['cancel_calls'] == 9
assert summary['confirmed_cancel_calls'] == 8
assert sum(r['static_queue'] is None for r in rows) == 1
assert sum(r['actual']==0 and r['static_queue'] is not None and r['static_queue'][0]>0 for r in rows) == 2
assert sum(r['actual']>0 and r['static_queue'] is not None and r['static_queue'][1]==0 for r in rows) == 2
assert summary['status'] == 'NOT_CALIBRATED_CLOCK_AND_QUEUE_MISMATCH'
print('M5: telemetry, money, role, clock-null and per-order mismatch checks passed')
