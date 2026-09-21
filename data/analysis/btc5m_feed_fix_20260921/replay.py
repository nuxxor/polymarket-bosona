#!/usr/bin/env python3
"""Replay recorded decision cutoffs; coverage diagnosis only, no hypothetical PnL."""
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT/'analiz/izleme'))
import bosona_rebound_shadow as r  # noqa: E402

OLD = ROOT/'data/analysis/bosona_inventory_20260921/status_1321'
cutoff = json.loads((OLD/'runtime.json').read_text())['captured_ms']
events = [e for line in (OLD/'inventory.jsonl').read_text().splitlines()
          if (e := json.loads(line))['recorded_ms'] <= cutoff]
counts, details = Counter(), []
with tempfile.TemporaryDirectory() as temp:
    db = Path(temp)/'prices.db'
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE prices(received_ms,observed_ms,source,price)')
        con.executemany('INSERT INTO prices VALUES(?,?,?,?)', json.loads((OLD/'prices.json').read_text()))
    for e in events:
        if e['kind'] != 'decision':
            continue
        counts['decisions'] += 1
        counts['old_valid_context'] += e['context_gap'] is None
        when, S = e['feature_cutoff_ms'], e['S']
        candle = next(x['bars'] for x in reversed(events) if x['kind'] == 'bars' and x['recorded_ms'] <= when)
        market = next(x['market'] for x in events if x['kind'] == 'market' and x['S'] == S)
        # Isolate the price-clock change without fabricating executable quotes.
        try:
            r.decide(db, S, when, [dict(bid=.4, ask=.41), dict(bid=.6, ask=.61)], candle, market)
            price_error = None
        except r.ERRORS as ex:
            price_error = str(ex)
        try:
            signal, side, favorite = r.decide(db, S, when, e['books'], candle, market)
            new_error = None
        except r.ERRORS as ex:
            new_error = str(ex)
        if e['context_gap'] is None:
            assert new_error is None, 'previously valid recorded decision regressed'
        counts['new_valid_context_with_recorded_books'] += new_error is None
        if e['context_gap'] == 'incomplete or stale context':
            counts['old_price_gaps'] += 1
            counts['price_gaps_repaired'] += price_error is None
            counts['price_gaps_still_invalid'] += price_error is not None
        details.append(dict(S=S, age=e['age'], old_error=e['context_gap'], new_error=new_error, price_error=price_error))
report = dict(counts=dict(counts), details=details, source_sha256=r.hashes(), cutoff_ms=cutoff,
              limitation='Old missing books cannot be reconstructed; no fill/PnL replay. Current stale prices remain rejected.')
(OUT/'replay.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report['counts']))
