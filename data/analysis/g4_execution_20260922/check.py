"""Small time/identity checks plus complete frozen-data reproduction."""
from copy import deepcopy
from hashlib import sha256
import json

from analyze import HERE, analyze, cancel_relation, quote_at

qs = [dict(karar_ms=10000, bb=.4, ba=.42, defter_yasi=.1),
      dict(karar_ms=11000, bb=.8, ba=.82, defter_yasi=.1)]
assert abs(quote_at(qs, 10500, 20000)['mid']-.41) < 1e-12
assert quote_at(qs, 9999, 20000) is None
assert quote_at(qs, 13000, 20000) is None
assert quote_at(qs, 11000, 11000) is None
bad = deepcopy(qs)
bad[-1]['defter_yasi'] = 4
assert quote_at(bad, 11000, 20000) is None
cancel = dict(begin=dict(utc_ns=10_000_000_000, mono_ns=5_000_000_000),
              end=dict(utc_ns=10_040_000_000, mono_ns=5_040_000_000))
fill = dict(received_mono_ns=4_999_000_000, exchange_ms=10020)
assert cancel_relation(fill, cancel) == 'fill_seen_before_cancel'
fill['received_mono_ns'] = 5_030_000_000
assert cancel_relation(fill, cancel) == 'reported_clock_overlaps_cancel_call'
fill['exchange_ms'] = 9500
assert cancel_relation(fill, cancel) == 'reported_fill_before_cancel'
fill['exchange_ms'] = None
assert cancel_relation(fill, cancel) == 'execution_clock_missing'
assert cancel_relation(fill, None) == 'no_cancel_request'

expected = json.loads((HERE/'results.json').read_text())
actual = analyze(HERE/'capture.jsonl.gz')
assert json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True)
assert actual['raw_private_matches'] == 2*actual['unique_trade_parent']
assert all(r['lanes'] == ['A', 'B'] for r in actual['rows'])
assert sorted(w['S'] for w in actual['windows']) == actual['manifest']['assigned']
assert actual['accepted_parents'] == actual['filled_parents']+actual['unfilled_parents']
assert abs(sum(w['qty'][0]+w['qty'][1] for w in actual['windows'])-actual['shares']) < 1e-6
print(json.dumps(dict(status='PASS', actual_fills=actual['unique_trade_parent'],
                      accepted_parents=actual['accepted_parents'], all_quantities_reconciled=True,
                      byte_identical_result=True,
                      results_sha256=sha256((HERE/'results.json').read_bytes()).hexdigest())))
