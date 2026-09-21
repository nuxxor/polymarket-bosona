#!/usr/bin/env python3
"""Run with python3: real schedulers, simulated public inputs; no network/orders."""
import argparse
from collections import Counter
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
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


def loop_check(module, partial=False, quiet=False, participation=False):
    S = 1800000000
    clock = [S+(225.6 if module is r else -10.)]
    with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
        out = Path(temp)
        args = argparse.Namespace(out=out, prices_db=out/'public.db', participate=participation)
        if module is r:
            # Reproduce the observed phase: last preparation at t225.6, resume in this window.
            base.save(out/'watch_manifest.json', dict(mode='SHADOW_NO_ORDERS', start_S=S,
                      end_S=S+72*3600, source_sha256=module.hashes(), prices_db=str(args.prices_db.resolve())))
        stop_at = [S+((51 if participation else 81) if module is inv else 1603)]
        quote_calls = Counter()

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

        def public_book(token, require_bid=True, require_ask=True):
            age = clock[0]%300
            b = book(.2 if token == '1' else (.8 if age < 60 else .4), round(clock[0]*1000))
            if quiet:
                key = int(clock[0])//10, token
                quote_calls[key] += 1
                if 30 <= age < 40:
                    b['observed_ms'] -= 4000  # No fabricated first fill; retry next slot.
                elif 40 <= age < 50 and token == '1' and quote_calls[key] > 1:
                    b = book(.4, round(clock[0]*1000))  # Both speed lanes reject worse execution.
            if partial and module is r:
                if token == '1':
                    b['bid'] = None
                else:
                    b.update(bid=.79, ask=None, asks=[])
            return b

        def inputs(db, start, when):
            times = list(range(when-65000, when+1, 1000))
            values = [(t, 100+(t-when)/100000*(-1 if quiet else 1)) for t in times]
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
            if partial and module is r:
                assert all(e['rebound'] == 0 and e['costs'][0] and e['costs'][1] is None for e in executions)
                for e in events:
                    if e['kind'] == 'resolution':
                        assert all(v['favorite'] is None and v['rebound'] > 0 for v in e['pnl'].values())
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
                if quiet:
                    assert all(e['entry_side'] is None for e in decisions)
                    if participation:
                        firsts = Counter((s, lane) for (s, lane), fs in portfolios.items() for f in fs if f['kind'] == 'first')
                        assert firsts == Counter({(s, lane): 1 for s in (S, S+300) for lane in inv.LANES})
                        assert all(50 <= f['age'] < 51 for fs in portfolios.values() for f in fs if f['kind'] == 'first')
                        assert kinds == {'first', 'complete'}  # Participation does not leak into additions/reopening.
                        assert any(e['age'] == 40 and len(e['rejected']) == 2 and not e['fills'] for e in executions)
                    else:
                        assert not portfolios
                else:
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
            if participation:
                args.participate = False
                try:
                    module.watch(args)
                    raise AssertionError('entry policy changed on resume')
                except ValueError:
                    pass
    return dict(module=module.__name__, participation=participation, quiet=quiet,
                slots=len(decisions), executions=len(executions), resume_duplicates=0,
                first_window_bar_receipts=[round(e['bars']['received_ms']/1000-S, 3) for e in events
                                           if e['kind'] == 'bars' and S*1000 <= e['recorded_ms'] < (S+300)*1000])


def context_check():
    S, when = 1800000000, 1800000280600
    minute = when//60000*60000
    rows = [[minute+i*60000, '101', '102', '98', str(100-i*.1), '10',
             minute+(i+1)*60000-1, '1000', 10, '5'] for i in range(-29, 0)]
    candle = dict(rows=rows, received_ms=when-1000)
    pair = [dict(book(.2, when), bid=None), dict(book(.8, when), ask=None, asks=[])]
    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp)/'prices.db'
        with sqlite3.connect(db) as con:
            con.execute('CREATE TABLE prices(received_ms, observed_ms, source, price)')
            con.execute('INSERT INTO prices VALUES(?,?,?,?)', (S*1000+2350, S*1000, 'crypto_prices_twap_sixty', 99.8))
            for obs in range(S*1000+210000, when, 1000):
                lag = 3200 if obs == S*1000+268000 else 2350
                for name in ('crypto_prices_chainlink', 'crypto_prices_twap_sixty'):
                    con.execute('INSERT INTO prices VALUES(?,?,?,?)', (obs+lag, obs, name, 100+(obs-S*1000)/100000))
            # Neither a report arriving after this decision nor a future event may be used.
            con.execute('INSERT INTO prices VALUES(?,?,?,?)', (when+100, when-100, 'crypto_prices_chainlink', 999))
            con.execute('INSERT INTO prices VALUES(?,?,?,?)', (when-10, when+100, 'crypto_prices_chainlink', 888))
        streams, starts = base.live_inputs(db, S, when)
        old = r.deep.context_features(streams, starts, ([a[6] for a in rows], rows), S, when)
        assert 'final_up_prob' not in old  # Receipt-time history reproduces the real false gap.
        signal, selected, favorite = r.decide(db, S, when, pair, candle, M)
        assert signal['spot'] == 102.78 and signal['momentum'] > 0
        assert (selected, favorite) == (0, 1)
        # Full books keep their existing midpoint ordering and predicate.
        assert r.decide(db, S, when, [book(.2), book(.8)], candle, M)[1:] == (0, 1)
        for bad in ([book(.2), None], [dict(book(.2), bid=None), dict(book(.3), bid=None)]):
            try:
                r.decide(db, S, when, bad, candle, M)
                raise AssertionError('unknown quote ordering accepted')
            except ValueError:
                pass
        with sqlite3.connect(db) as con:
            con.execute('DELETE FROM prices WHERE source=? AND observed_ms>?', ('crypto_prices_chainlink', when-4000))
        try:
            r.decide(db, S, when, pair, candle, M)
            raise AssertionError('stale current price accepted')
        except ValueError:
            pass


def check():
    # Participation is a first-entry-only exception, with unchanged cash/risk/slippage guards.
    pair = [book(.51), book(.52)]
    assert inv.intent([], pair, M, None, 30, True) is None
    seed = inv.intent([], pair, M, None, 30, True, participate=True)
    assert seed['kind'] == 'first' and seed['side'] == 0 and seed['participation']
    first = inv.execute(seed, [], pair, M, 30.3)
    assert first['qty'] == 5 and first['cost'] > 2.55
    assert inv.intent([first], pair, M, None, 60, True, participate=True) is None
    assert inv.intent([fill(0, .2), fill(1, .7)], pair, M, None, 60, True, participate=True) is None
    for bad_fills, bad_order in (([first], seed), ([], dict(seed, kind='add'))):
        try:
            inv.execute(bad_order, bad_fills, pair, M, 31)
            raise AssertionError('participation exception reused')
        except ValueError:
            pass
    assert inv.intent([], [None, None], M, None, 30, True, True) is None
    assert inv.intent([], [book(.2, qty=4), None], M, None, 30, True, True) is None
    assert inv.intent([], pair, M, None, 210, True, True) is None
    assert inv.intent([], [book(.6), book(.3)], M, None, 30, True, True)['side'] == 1
    assert inv.intent([], [book(.5), book(.5)], M, None, 30, True, True)['side'] == 0
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
    assert inv.intent([], [book(.2, qty=4), book(.8)], M, 0, 40, True) is None
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
        response.update(bids=[dict(price='.7', size='5')], asks=[])
        b = base.public_book('1', False, False)
        assert b['bid'] == .7 and b['ask'] is None and b['asks'] == []
        try:
            base.ask_cost(b, M)
            raise AssertionError('missing asks became a paper fill')
        except ValueError:
            pass
        response.update(asks=[dict(price='.6', size='5')])
        try:
            base.public_book('1', False, False)
            raise AssertionError('crossed partial book accepted')
        except ValueError:
            pass
    context_check()
    results = [loop_check(r), loop_check(inv), loop_check(r, partial=True),
               loop_check(inv, quiet=True), loop_check(inv, quiet=True, participation=True)]
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
