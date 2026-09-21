#!/usr/bin/env python3
"""Run with python3: real schedulers, simulated public inputs; no network/orders."""
import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import bosona_inventory_shadow as inv

r, base = inv.r, inv.base
M = dict(slug='btc-updown-5m-1800000000', feesEnabled=True,
         feeSchedule=dict(rate=.07, exponent=1), clobTokenIds='["1","2"]', outcomes='["Up","Down"]', events=[])


def book(p, now=1800000000000, qty=100):
    return dict(bid=p-.01, ask=p, asks=[(p, qty)], received_ms=now, observed_ms=now)


def fill(side, price, qty=5, age=30):
    return dict(side=side, qty=qty, cost=qty*price, fee=0., age=age)


def loop_check(module):
    S = 1800000000
    clock = [S+(225.6 if module is r else -10.)]
    with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
        out = Path(temp)
        args = argparse.Namespace(out=out, prices_db=out/'public.db')
        if module is r:
            # Reproduce the observed phase: last preparation at t225.6, resume in this window.
            base.save(out/'watch_manifest.json', dict(mode='SHADOW_NO_ORDERS', start_S=S,
                      end_S=S+72*3600, source_sha256=module.hashes(), prices_db=str(args.prices_db.resolve())))
        stop_at = [S+(81 if module is inv else 1603)]

        def sleep(seconds):
            clock[0] += max(.001, seconds)
            if clock[0] >= stop_at[0]:
                (out/'STOP_SHADOW').touch()

        def get(url, **kwargs):
            clock[0] += .08  # Receipt occurs AFTER last_prep; essential to reproduce the old cache bug.
            if 'binance' in url:
                minute = int(clock[0])//60*60000
                return [[minute+i*60000, '101', '102', '98', str(100-i*.1), '10',
                         minute+(i+1)*60000-1, '1000', 10, '5'] for i in range(-29, 1)]
            old = int(url.split('btc-updown-5m-')[1].split('?')[0])
            return dict(M, slug=f'btc-updown-5m-{old}', closed=True,
                        outcomePrices='["1","0"]', conditionId='condition')

        def public_book(token, require_bid=True):
            age = clock[0]%300
            return book(.2 if token == '1' else (.8 if age < 60 else .4), round(clock[0]*1000))

        def inputs(db, start, when):
            times = list(range(when-65000, when+1, 1000))
            values = [(t, 100+(t-when)/100000) for t in times]
            return {name: (times, values) for name in ('spot', 'twap60')}, {start: (start*1000, 99.8)}

        with (patch.object(r.time, 'time', side_effect=lambda: clock[0]),
              patch.object(r.time, 'sleep', side_effect=sleep),
              patch.object(base, 'get', side_effect=get),
              patch.object(base, 'public_book', side_effect=public_book),
              patch.object(base, 'live_inputs', side_effect=inputs),
              patch.object(r, 'market', side_effect=lambda s: dict(M, slug=f'btc-updown-5m-{s}'))):
            module.watch(args)
            if module is inv:
                # Resume while still holding inventory, then finish this and the next window.
                (out/'STOP_SHADOW').unlink()
                stop_at[0] = S+610
                module.watch(args)
            events = [json.loads(line) for line in (out/'shadow.jsonl').read_text().splitlines()]
            decisions = [e for e in events if e['kind'] == 'decision' and e['S'] == S]
            assert [e['age'] for e in decisions] == module.SLOTS
            for age in (270, 280):
                e = next(e for e in decisions if e['age'] == age)
                assert e['signal']['bar_close_ms'] == (S+240)*1000-1
                assert e['signal']['decision_ms'] <= e['decision_ms']
            assert not [e for e in events if e['kind'] == 'gap']
            assert any(e['kind'] == 'resolution' and e['S'] == S for e in events), [e for e in events if e['kind'] == 'resolution_pending'][-3:]
            executions = [e for e in events if e['kind'] == 'execution']
            if module is inv:
                portfolios = {}
                kinds = set()
                for e in executions:
                    for lane, f in e['fills'].items():
                        kinds.add(f['kind'])
                        history = portfolios.setdefault((e['S'], lane), [])
                        if f['kind'] == 'complete':
                            assert inv.paired_cost(inv.position(history), f['side'], f['qty'])+f['cost'] <= .98*f['qty']+1e-8
                        history.append(f)
                        p = inv.position(history)
                        assert p['cash'] <= 15+1e-8 and p['floor'] >= -5-1e-8
                        assert abs(p['qty'][0]-p['qty'][1]) <= 10+1e-8
                    assert e['request_ms'] >= e['decision_ms']+(250 if e['speed'] == '250' else 0)
                assert {'first', 'add', 'complete', 'reopen'} <= kinds
                for e in events:
                    if e['kind'] == 'resolution':
                        for lane, pnl in e['pnl'].items():
                            history = portfolios.get((e['S'], lane), [])
                            expected = sum(f['qty']*(f['side'] == e['winner'])-f['cost'] for f in history)
                            assert abs(pnl-expected) < 1e-8
            module.watch(args)
            resumed = [json.loads(line) for line in (out/'shadow.jsonl').read_text().splitlines()]
            assert sum(e['kind'] == 'execution' for e in resumed) == len(executions)
            assert (out/'watch_manifest.json').exists()
    return dict(module=module.__name__, slots=len(decisions), executions=len(executions), resume_duplicates=0,
                first_window_bar_receipts=[round(e['bars']['received_ms']/1000-S, 3) for e in events
                                           if e['kind'] == 'bars' and S*1000 <= e['recorded_ms'] < (S+300)*1000])


def check():
    # Previously matched profits cannot subsidize a bad new pair.
    history = [fill(0, .30), fill(1, .60), fill(0, .60)]
    assert inv.intent(history, [book(.4), book(.53)], M, None, 240, True) is None
    order = inv.intent([fill(0, .20)], [book(.2), book(.75)], M, None, 240, False)
    assert order['side'] == 1 and order['kind'] == 'complete' and order['qty'] == 5
    executed = inv.execute(order, [fill(0, .20)], [None, book(.75)], M, 240.3)
    assert inv.position([fill(0, .20), executed])['floor'] > 0
    # Partial imbalance completes only that amount, with no accidental opposite entry.
    partial = [fill(0, .20, 3)]
    order = inv.intent(partial, [None, book(.70, qty=3)], M, None, 280, True)
    assert order['qty'] == 3
    assert inv.position(partial+[inv.execute(order, partial, [None, book(.7, qty=3)], M, 280)])['qty'] == [3, 3]
    assert inv.intent([], [book(.2), book(.8)], M, 0, 210, True) is None
    assert inv.intent([fill(0, .2)], [book(.2), book(.8)], M, 0, 50, False) is None
    assert inv.intent([fill(0, .2)], [book(.2), book(.8)], M, 0, 40, True) is None
    assert inv.intent([fill(0, .2)], [book(.2), book(.8)], M, 0, 50, True)['kind'] == 'add'
    assert inv.intent([fill(0, .2, 10)], [book(.2), book(.8)], M, 0, 280, True) is None
    assert inv.intent([fill(0, .2), fill(1, .7)], [book(.2), book(.8)], M, None, 90, True) is None
    assert not inv.affordable(inv.position([fill(0, .8)]), 0, 5, 2)
    order = inv.intent([], [book(.49), book(.51)], M, 0, 40, True)
    try:
        inv.execute(order, [], [book(.50), book(.5)], M, 40.3)
        raise AssertionError('late expensive entry accepted')
    except ValueError:
        pass
    response = dict(asset_id='1', timestamp=r.now_ms(), bids=[], asks=[dict(price='.7', size='5')])
    with patch.object(base, 'get', return_value=response):
        assert base.public_book('1', require_bid=False)['bid'] is None
        try:
            base.public_book('1')
            raise AssertionError('strict original entry accepted missing bids')
        except ValueError:
            pass
    results = [loop_check(r), loop_check(inv)]
    with patch.object(r, 'bars_due', side_effect=lambda candle, when: candle is None or when-candle['received_ms'] >= 30000):
        try:
            loop_check(r)
        except AssertionError:
            pass
        else:
            raise AssertionError('full-loop regression did not detect original cache bug')
    r.check()
    print(json.dumps(dict(checks='PASS', loops=results)))


if __name__ == '__main__':
    check()
