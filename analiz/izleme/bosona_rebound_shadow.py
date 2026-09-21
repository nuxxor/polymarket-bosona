#!/usr/bin/env python3
"""Independent frozen rebound experiment. Public GETs and read-only prices; no orders."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time

import bosona_derin as deep
import bosona_gec_arastirma as base

ERRORS = (OSError, ValueError, KeyError, TypeError, IndexError, sqlite3.Error)
SLOTS = [240, 270, 280]


def now_ms():
    return round(time.time()*1000)


def hashes():
    return {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('bosona_rebound_shadow.py', 'bosona_derin.py',
                         'bosona_gec_arastirma.py', 'muhasebe.py')}


def bars():
    started = now_ms()
    rows = base.get('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=30',
                    timeout=3, attempts=1)
    received = now_ms()
    if not isinstance(rows, list) or len(rows) < 22:
        raise ValueError('missing Binance bars')
    if any(b[0]-a[0] != 60000 for a, b in zip(rows, rows[1:])):
        raise ValueError('noncontiguous Binance bars')
    if any(not math.isfinite(float(r[i])) or float(r[i]) <= 0 for r in rows for i in (1, 2, 3, 4)):
        raise ValueError('invalid Binance prices')
    # Never retain a partial bar and later mislabel that old snapshot as a closed bar.
    rows = [r for r in rows if r[6]+2000 <= received]
    return dict(request_ms=started, received_ms=received, rows=rows)


def bars_due(candle, when):
    # Refresh on publication of a NEW closed minute, not on cache receipt age.
    latest_closed = (when-2000)//60000*60000-1
    return candle is None or not candle['rows'] or candle['rows'][-1][6] < latest_closed


def market(S):
    m = base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{S}',
                 timeout=3, attempts=1)
    if m.get('slug') != f'btc-updown-5m-{S}' or m.get('closed') or not m.get('acceptingOrders'):
        raise ValueError('wrong/closed market')
    if 'btc-usd-twap-60s-streams' not in m['description'] or json.loads(m['outcomes']) != ['Up', 'Down']:
        raise ValueError('unsupported market rules')
    tokens = json.loads(m['clobTokenIds'])
    if len(tokens) != 2 or tokens[0] == tokens[1] or any(not str(t).isdigit() for t in tokens):
        raise ValueError('invalid outcome tokens')
    base.ask_cost({'asks': [(.5, 5)]}, m)  # Fee schedule must be supported before any decision.
    return m


def books(pool, tokens):
    started = now_ms()
    pair = list(pool.map(base.public_book, tokens))
    received = now_ms()
    if any(not 0 <= received-b[k] <= 3000 for b in pair for k in ('received_ms', 'observed_ms')):
        raise ValueError('stale paired books')
    return pair, started, received


def decide(db, S, when, pair, candle, m):
    if candle['received_ms'] > when:
        raise ValueError('future bar response')
    rows = candle['rows']
    streams, starts = base.live_inputs(db, S, when)
    signal = deep.context_features(streams, starts, ([r[6] for r in rows], rows), S, when)
    if 'final_up_prob' not in signal or 'rsi14' not in signal:
        raise ValueError('incomplete or stale context')
    official = next((e.get('eventMetadata', {}).get('priceToBeat') for e in m.get('events', [])
                     if e.get('slug') == m['slug']), None)
    if official is not None and abs(float(official)-signal['ref']) > 1e-6:
        raise ValueError('reference mismatch')
    for b in pair:
        base.ask_cost(b, m)
    quotes = [(b['bid'], b['ask']) for b in pair]
    selected = deep.rebound_side(signal, quotes)
    favorite = 0 if sum(quotes[0]) > sum(quotes[1]) else 1
    return signal, selected, favorite


def settle(event, winner):
    results = {}
    for rule in ('rebound', 'favorite'):
        side = event[rule]
        results[rule] = 0. if side is None else 5.*(side == winner)-sum(event['costs'][side])
    return results


def watch(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out/'watch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(args, out)


def run(args, out):
    manifest_path = out/'watch_manifest.json'
    source = hashes()
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['source_sha256'] != source or manifest['prices_db'] != str(args.prices_db.resolve()):
            raise ValueError('frozen source or input changed; do not mix experiments')
    else:
        S = int(time.time())//300*300+300
        manifest = dict(mode='SHADOW_NO_ORDERS', start_S=S, end_S=S+72*3600,
                        started_ms=now_ms(), source_sha256=source, qty=5., slots=SLOTS, primary_slot=280,
                        rule='cheaper midpoint; ask<.50, own simple RSI14<40, own momentum10>0',
                        baseline='favorite at each identical eligible slot, separate paper strategies',
                        execution_delay_ms=250, max_age_ms=3000, bar_publication_lag_ms=2000,
                        prices_db=str(args.prices_db.resolve()),
                        cost='5 shares, ask depth + market fee; no rebate or maker fill assumed',
                        gate='>=3 days, >=100 eligible windows AND >=100 selected trades; both cluster CI lower bounds>0; ex-top3>0')
        base.save(manifest_path, manifest)
    path = out/'shadow.jsonl'
    # A torn JSONL is an error, never silently reset a trial or duplicate a decision.
    history = [json.loads(line) for line in path.open()] if path.exists() else []
    attempts = {(e['S'], e['age']) for e in history if e['kind'] in ('decision', 'gap')}
    executions = {(e['S'], e['age']): e for e in history if e['kind'] == 'execution'}
    resolutions = {e['S'] for e in history if e['kind'] == 'resolution'}

    def emit(kind, **values):
        event = dict(kind=kind, recorded_ms=now_ms(), **values)
        with path.open('a') as stream:
            stream.write(json.dumps(event, separators=(',', ':'), allow_nan=False)+'\n')
        print(json.dumps({k: v for k, v in event.items()
                          if k not in ('books', 'execution_books', 'signal', 'bars', 'market')},
                         separators=(',', ':')), flush=True)
        return event

    emit('start', **manifest)
    markets, candle = {}, None
    last_prep = last_health = last_grade = 0.
    with ThreadPoolExecutor(max_workers=2) as pool:
        while time.time() < manifest['end_S']+1500 and not (out/'STOP_SHADOW').exists():
            now = time.time()
            S = int(now)//300*300
            age_now = now-S
            active = manifest['start_S'] <= S < manifest['end_S']
            # Fetch slow metadata/bars away from the decision slots, including before the first window.
            if (age_now < 230 or 245 <= age_now < 260) and now-last_prep >= 15:
                last_prep = now
                try:
                    target = max(S, manifest['start_S'])
                    if target < manifest['end_S'] and target not in markets:
                        markets[target] = market(target)
                        emit('market', S=target, market=markets[target])
                    if bars_due(candle, now_ms()):
                        candle = bars()
                        emit('bars', bars=candle)
                except ERRORS as ex:
                    emit('input_gap', error=type(ex).__name__, reason=str(ex)[:180])
            if active:
                for age in SLOTS:
                    if (S, age) in attempts or time.time()-S < age:
                        continue
                    attempts.add((S, age))
                    phase = 'decision'
                    try:
                        if now_ms() > (S+age+3)*1000:
                            raise ValueError('missed decision deadline')
                        m = markets[S]
                        if candle is None:
                            raise ValueError('bars not prepared')
                        tokens = json.loads(m['clobTokenIds'])
                        pair, requested, when = books(pool, tokens)
                        signal, side, favorite = decide(args.prices_db, S, when, pair, candle, m)
                        computed = now_ms()
                        if computed > (S+age+3)*1000:
                            raise ValueError('late decision')
                        emit('decision', S=S, age=age, rebound=side, favorite=favorite, signal=signal,
                             books=pair, decision_ms=computed, feature_cutoff_ms=when,
                             request_ms=requested, http_ms=when-requested, schedule_lag_ms=computed-(S+age)*1000,
                             bars_received_ms=candle['received_ms'])
                        phase = 'execution'
                        time.sleep(max(0., (computed+250-now_ms())/1000))
                        execution, requested, received = books(pool, tokens)
                        if received-computed > 3000 or requested-computed < 250:
                            raise ValueError('execution delay outside bounds')
                        costs = [base.ask_cost(b, m) for b in execution]
                        e = emit('execution', S=S, age=age, rebound=side, favorite=favorite,
                                 execution_books=execution, costs=costs, execution_ms=received,
                                 request_ms=requested, delay_ms=received-computed, http_ms=received-requested,
                                 fee_schedule=m.get('feeSchedule'), qty=5.)
                        executions[S, age] = e
                    except ERRORS as ex:
                        emit('gap', S=S, age=age, phase=phase, error=type(ex).__name__, reason=str(ex)[:180])
            # Bounded grading cannot occupy the late-window decision interval.
            if age_now < 180 and now-last_grade >= 60:
                last_grade = now
                pending = sorted({s for s, _ in executions}-resolutions)
                for old in pending[:3]:
                    if old+1500 > now:
                        continue
                    try:
                        m = base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{old}?snapshot={int(now)//30}',
                                     timeout=3, attempts=1)
                        winner = base.outcome(m)
                        values = {str(age): settle(e, winner) for (s, age), e in executions.items() if s == old}
                        emit('resolution', S=old, winner=winner, condition=m['conditionId'], pnl=values)
                        resolutions.add(old)
                    except ERRORS as ex:
                        emit('resolution_pending', S=old, error=type(ex).__name__)
            if now-last_health >= 60:
                last_health = now
                emit('health', attempts=len(attempts), executions=len(executions),
                     resolved=len(resolutions), end_S=manifest['end_S'])
            time.sleep(.05)
    emit('stop', pending=sorted({s for s, _ in executions}-resolutions),
         reason='stop_file' if (out/'STOP_SHADOW').exists() else 'duration')


def check():
    from contextlib import redirect_stdout
    import io
    import tempfile
    from unittest.mock import patch
    pair = [(.19, .20), (.79, .80)]
    assert deep.rebound_side(dict(rsi14=39, momentum=.1), pair) == 0
    assert deep.rebound_side(dict(rsi14=61, momentum=-.1), pair[::-1]) == 1
    for rsi, momentum in ((40, .1), (39, 0), (39, -.1)):
        assert deep.rebound_side(dict(rsi14=rsi, momentum=momentum), pair) is None
    assert deep.rebound_side(dict(rsi14=39, momentum=1), [(.49, .5), (.50, .51)]) is None
    event = dict(rebound=0, favorite=1, costs=[[1., .056], [4., .056]])
    assert abs(settle(event, 0)['rebound']-3.944) < 1e-9
    assert abs(settle(event, 0)['favorite']+4.056) < 1e-9
    event['rebound'] = None
    assert settle(event, 1)['rebound'] == 0
    minute = now_ms()//60000*60000
    rows = [[minute+i*60000, '1', '1', '1', '1', '1', minute+(i+1)*60000-1, '0', 1, '1']
            for i in range(-29, 1)]
    with patch.object(base, 'get', return_value=rows):
        closed = bars()
    assert all(r[6]+2000 <= closed['received_ms'] for r in closed['rows'])
    assert rows[-1] not in closed['rows']
    cached = dict(received_ms=225600, rows=[[0]*6+[179999]])
    assert not bars_due(cached, 240000)
    assert bars_due(cached, 245000)  # only 19.4 seconds old, but missing the new closed bar
    with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
        out = Path(temp)
        (out/'STOP_SHADOW').touch()
        args = argparse.Namespace(out=out, prices_db=out/'public.db')
        watch(args)
        frozen = (out/'watch_manifest.json').read_bytes()
        watch(args)
        assert (out/'watch_manifest.json').read_bytes() == frozen
        with (out/'watch.lock').open('a') as other:
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                watch(args)
                raise AssertionError('second writer accepted')
            except BlockingIOError:
                pass
        manifest = json.loads(frozen)
        assert manifest['end_S']-manifest['start_S'] == 72*3600
        manifest['source_sha256']['bosona_rebound_shadow.py'] = 'changed'
        base.save(out/'watch_manifest.json', manifest)
        try:
            watch(args)
            raise AssertionError('changed source accepted')
        except ValueError:
            pass
    base.check()
    deep.check()
    print('Rebound, boundaries, fees, closed bars, lock, resume, frozen source and causal checks passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['watch', 'check'])
    parser.add_argument('--prices-db', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.action == 'check':
        check()
    else:
        if args.prices_db is None or not args.prices_db.is_file() or args.out is None:
            parser.error('watch requires an existing read-only prices database and separate output directory')
        watch(args)
