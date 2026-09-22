#!/usr/bin/env python3
"""Small runnable negative controls plus exact real-output checks; no network/orders."""
import ast
import copy
from decimal import Decimal
import gzip
import json
import math
from pathlib import Path

import audit as a


def fails(call):
    try:
        call()
    except (ValueError, AssertionError):
        return
    raise AssertionError('invalid case accepted')


def run():
    a.c.check()
    idx = a.index(dict(spot=[(1050, 1000, 100.), (2050, 2000, 101.),
                            (4000, 2000, 999.), (6250, 6000, 105.)]))
    # Old-time receipt is not required; current-time receipt is still mandatory.
    fails(lambda: a.at(idx, 'spot', 1000, 3000, False))
    assert a.at(idx, 'spot', 1000, 3000, True) == 100
    assert a.at(idx, 'spot', 2000, 3000, True) == 101
    fails(lambda: a.at(idx, 'spot', 6000, 6000, True))
    fails(lambda: a.at(idx, 'spot', 10000, 10000, True))
    # Independent numerical Brownian covariance integration, not a TWAP feed replica.
    for remaining in (15, 30, 59, 60, 300):
        span = min(60, remaining)
        dt = span/500
        times = [max(0, remaining-60)+(i+.5)*dt for i in range(500)]
        numerical = sum(min(x, y) for x in times for y in times)*dt*dt/3600
        exact = remaining-40 if remaining >= 60 else remaining**3/10800
        assert math.isclose(numerical, exact, rel_tol=1e-4)
    market = dict(conditionId='right', clobTokenIds='["a","b"]', feesEnabled=True,
                  feeSchedule=dict(exponent=1, rate=.07))
    book = dict(asset_id='a', market='right', requested_ms=180250, received_ms=180300,
                observed_ms=180200, bid=.39, asks=[(.4, 10.)], tick_size='.01', min_order_size='5')
    intent = dict(side=0, qty=5., kind='first')
    context = dict(spot=101., ref=100., final_up_prob=.8, now=180)
    # Deliberately demonstrate missing adapter contracts, without inventing affected fills.
    assert a.c.apply_book(a.c.state(), intent, book, market, 180000, context)
    assert a.c.apply_book(a.c.state(), intent, dict(book, market='wrong'), market, 180000, context)
    assert a.c.apply_book(a.c.state(), dict(intent, qty=3), book, market, 180000, context)
    assert a.c.apply_book(a.c.state(), intent, dict(book, asks=[(.405, 10.)]), market, 180000, context)
    assert a.c.apply_book(a.c.state(), intent, book, market, 180000, dict(context, now=999999))
    regression = dict(frozen_adapter_accepts_wrong_condition=True,
                      frozen_adapter_accepts_under_min_size=True,
                      frozen_adapter_accepts_off_tick_price=True,
                      frozen_adapter_accepts_future_context=True,
                      warning='Synthetic trust-boundary failures; actual candidate actions remain 5 shares.')
    original = a.read(a.HERE/'results.json')
    assert original['historical']['counts']['frozen_valid'] == 20533
    assert original['historical']['counts']['restored_contexts'] == 348
    assert original['s']['counts']['scheduled'] == 168
    assert original['s']['counts']['frozen_joint_valid'] == 155
    assert original['s']['counts']['causal_history_joint_valid'] == 156
    for ref in original['s']['references']:
        assert ref['start_difference'] == 0 and ref['end_difference'] in (0, None)
        assert ref['outcome_agrees'] and 0 <= ref['reference_arrival_ms'] < 180000
    for row in a.read(a.HERE/'s_decisions.json'):
        now = (row['S']+row['age'])*1000
        for ctx in row['contexts'].values():
            if 'missing' not in ctx:
                assert ctx['reference_received_ms'] <= now and ctx['now']*1000 == now
        for action in row['actions']:
            if 'received_ms' in action:
                assert now+250 <= action['requested_ms'] <= action['received_ms'] <= now+3000
    with gzip.open(a.S/'raw/book_validation_prefix.json.gz', 'rt') as stream:
        event = next(x for x in json.load(stream)['rows'] if x['kind'] == 'books')
    market = a.read(a.S/'raw/initial_markets'/f'btc-updown-15m-{event["S"]}.json')
    raw = event['books'][0]
    asks = sorted((Decimal(x['price']), Decimal(x['size'])) for x in raw['asks'])
    left, cost, fee = Decimal(5), Decimal(0), Decimal(0)
    for p, qty in asks:
        take = min(left, qty)
        cost += take*p
        fee += take*Decimal('.07')*p*(1-p)
        left -= take
        if not left:
            break
    actual_cost, actual_fee = a.c.r.base.ask_cost(dict(asks=[(float(p), float(q)) for p, q in asks]), market, 5)
    assert not left and abs(float(cost)-actual_cost) < 1e-12
    assert abs(float(fee.quantize(Decimal('.00001')))-actual_fee) < 1e-12
    replays = a.read(a.HERE/'s_candidate_replay.json')
    assert len(replays) == 84
    for x in replays:
        assert x['cash'] <= 15 and x['peak_risk'] <= 5 and abs(x['q'][0]-x['q'][1]) <= 10
    for variant in ('frozen', 'causal_history'):
        arms = [{x['S'] for x in replays if x['variant'] == variant and x['arm'] == arm and x['entered']}
                for arm in ('entry_only', 'completion_only', 'managed')]
        assert arms[0] == arms[1] == arms[2]
    # Frozen policy observes own inventory only and never reopens after neutralization.
    s = a.c.state()
    assert a.c.apply(s, dict(side=0, qty=5, kind='first'), .4, .07, 180)
    assert a.c.apply(s, dict(side=1, qty=5, kind='complete'), .4, .07, 300)
    before = copy.deepcopy(s)
    assert a.c.decide(s, 600, [.4, .6], context) is None and s == before
    for path, expected in original['protected_sha256'].items():
        assert a.sha(Path(path)) == expected
    for path in a.HERE.glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    a.save('checks.json', dict(status='passed', regression=regression,
                             timing_and_brownian_math=True, real_14market_replay=True,
                             protected_hashes=True, syntax=True))
    print('PASS: historical access/future mutation/current staleness, Brownian covariance, adapter negative controls, '
          '14-market real books, equal entry arms, risk/FIFO/no-reopen, source hashes, syntax')


if __name__ == '__main__':
    run()
