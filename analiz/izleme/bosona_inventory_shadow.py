#!/usr/bin/env python3
"""Inventory experiment: public GETs and paper accounting only. No order client."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
from pathlib import Path
import time

import bosona_rebound_shadow as r

base = r.base
SLOTS = list(range(30, 291, 10))
LANES = ('pair_fast', 'pair_250', 'pair_add_fast', 'pair_add_250')
LIMITS = dict(clip=5., unmatched=10., cash=15., loss=5., pair=.98,
              entry_end=200, add_cooldown=20, price_slippage=.01)


def hashes():
    return dict(r.hashes(), **{Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


def position(fills):
    qty, cash, lots = [0., 0.], 0., [[], []]
    for f in fills:
        side, remaining = f['side'], f['qty']
        qty[side] += remaining
        cash += f['cost']
        while remaining > 1e-8 and lots[1-side]:
            lot = lots[1-side][0]
            take = min(remaining, lot[0])
            lot[0] -= take
            remaining -= take
            if lot[0] < 1e-8:
                lots[1-side].pop(0)
        if remaining > 1e-8:
            lots[side].append([remaining, f['cost']/f['qty']])
    return dict(qty=qty, cash=cash, lots=lots, floor=min(qty)-cash)


def affordable(pos, side, qty, cost):
    q = pos['qty'].copy()
    q[side] += qty
    cash = pos['cash']+cost
    return (cash <= LIMITS['cash']+1e-8 and abs(q[0]-q[1]) <= LIMITS['unmatched']+1e-8
            and min(q)-cash >= -LIMITS['loss']-1e-8)


def paired_cost(pos, side, qty):
    remaining, cash = qty, 0.
    for amount, price in pos['lots'][1-side]:
        take = min(amount, remaining)
        cash += take*price
        remaining -= take
        if remaining < 1e-8:
            return cash
    raise ValueError('completion would open opposite risk')


def intent(fills, pair, m, signal_side, age, additions, participate=False):
    pos = position(fills)
    if participate and not fills:
        if not 30 <= age <= LIMITS['entry_end']:
            return None
        costs = {}
        for side, book in enumerate(pair):
            if book is None:
                continue
            try:
                costs[side] = sum(base.ask_cost(book, m, LIMITS['clip']))
            except ValueError:
                continue
        if not costs:
            return None
        side = min(costs, key=lambda side: (costs[side], side))
        if not affordable(pos, side, LIMITS['clip'], costs[side]):
            return None
        return dict(kind='first', side=side, qty=LIMITS['clip'], participation=True,
                    max_cost=costs[side]+LIMITS['price_slippage']*LIMITS['clip'])
    net = pos['qty'][0]-pos['qty'][1]
    held = 0 if net > 1e-8 else 1 if net < -1e-8 else None
    # Completion depends on the actual unmatched lots, never historical average cost.
    if held is not None and pair[1-held] is not None:
        side, qty = 1-held, min(LIMITS['clip'], abs(net))
        try:
            cost = sum(base.ask_cost(pair[side], m, qty))
            cap = LIMITS['pair']*qty-paired_cost(pos, side, qty)
            if cost <= cap+1e-8 and affordable(pos, side, qty, cost):
                return dict(kind='complete', side=side, qty=qty, max_cost=cap)
        except ValueError:
            pass
    if signal_side is None:
        return None
    if held is None:
        if age > LIMITS['entry_end']:
            return None
        kind = 'first' if not fills else 'reopen'
    else:
        if not additions or signal_side != held:
            return None
        if age-fills[-1]['age'] < LIMITS['add_cooldown']:
            return None
        kind = 'add'
    side, qty = signal_side, LIMITS['clip']
    if pair[side] is None:
        return None
    try:
        cost = sum(base.ask_cost(pair[side], m, qty))
    except ValueError:
        return None
    if not affordable(pos, side, qty, cost):
        return None
    return dict(kind=kind, side=side, qty=qty,
                max_cost=cost+LIMITS['price_slippage']*qty)


def execute(order, fills, pair, m, age):
    participation = order.get('participation', False)
    if participation and (fills or order['kind'] != 'first' or not 30 <= age < LIMITS['entry_end']+3):
        raise ValueError('participation exception is only for the first entry')
    side, qty = order['side'], order['qty']
    book = pair[side]
    if book is None:
        raise ValueError('execution book unavailable')
    gross, fee = base.ask_cost(book, m, qty)
    cost = gross+fee
    pos = position(fills)
    if cost > order['max_cost']+1e-8 or not affordable(pos, side, qty, cost):
        raise ValueError('execution price or risk limit')
    if order['kind'] == 'complete':
        if cost+paired_cost(pos, side, qty) > LIMITS['pair']*qty+1e-8:
            raise ValueError('marginal pair cost limit')
    elif not participation and gross/qty >= .5:
        raise ValueError('opening price crossed cheap-side ceiling')
    return dict(kind=order['kind'], side=side, qty=qty, cost=cost, fee=fee, age=age)


books = r.books


def watch(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out/'watch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(args, out)


def run(args, out):
    path = out/'shadow.jsonl'
    mp = out/'watch_manifest.json'
    participate = getattr(args, 'participate', False)
    if mp.exists():
        manifest = json.loads(mp.read_text())
        if manifest['source_sha256'] != hashes() or manifest['prices_db'] != str(args.prices_db.resolve()):
            raise ValueError('frozen source/input changed; use a new experiment')
        if manifest.get('participation', False) != participate:
            raise ValueError('frozen entry policy changed; use a new experiment')
    else:
        S = int(time.time())//300*300+300
        manifest = dict(mode='SHADOW_NO_ORDERS', version='inventory_v2', start_S=S, end_S=S+72*3600,
                        started_ms=r.now_ms(), prices_db=str(args.prices_db.resolve()), source_sha256=hashes(),
                        slots=SLOTS, lanes=LANES, primary='pair_add_250 minus pair_250, per assigned window',
                        entry='rebound: cheaper midpoint or disjoint quote bounds, ask<.50, own RSI14<40, own momentum10>0',
                        feature_clock='observed time; received <= decision cutoff; 3000ms age limit',
                        completion='FIFO unmatched cash cost + current fee-inclusive ask cost <= .98 per pair',
                        addition='same rebound predicate on held side, 20s cooldown, at most 10 unmatched shares',
                        limits=LIMITS, execution='independent fast and >=250ms paper portfolios; HTTP is not a real fill',
                        gate='>=3 days and >=100 selected trades; day/window clustered lower bounds>0; ex-top3>0')
        if participate:
            manifest.update(version='inventory_participation_v1', participation=True,
                            entry='first only: t30..200, every10s; lowest fee-inclusive executable 5-share ask cost; tie Up; no RSI/momentum/.50 gate',
                            required_entry_data='fresh identity-validated ask depth; other indicators are diagnostic for first entry',
                            primary='pair_add_250 versus frozen selective inventory_v2 pair_add_250 on same assigned windows',
                            secondary='pair_add_250 versus pair_250 within this participation experiment',
                            coverage='attempt every assigned window; unavailable depth/data/execution never becomes an assumed fill')
        base.save(mp, manifest)
    attempts, resolved, portfolios = set(), set(), {}
    if path.exists():
        with path.open() as stream:
            for line in stream:
                e = json.loads(line)  # Torn journal fails closed; never reset paper inventory.
                if e['kind'] in ('decision', 'gap'):
                    attempts.add((e['S'], e['age']))
                elif e['kind'] == 'execution':
                    for lane, fill in e['fills'].items():
                        portfolios.setdefault((e['S'], lane), []).append(fill)
                elif e['kind'] == 'resolution':
                    resolved.add(e['S'])

    def emit(kind, **values):
        event = dict(kind=kind, recorded_ms=r.now_ms(), **values)
        with path.open('a') as stream:
            stream.write(json.dumps(event, separators=(',', ':'), allow_nan=False)+'\n')
        print(json.dumps({k: v for k, v in event.items()
                          if k not in ('books', 'signal', 'bars', 'market', 'source_sha256')}, separators=(',', ':')), flush=True)
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
            next_slot = next((age for age in SLOTS if age > age_now), 330)
            if next_slot-age_now > 3 and now-last_prep >= 5:
                last_prep = now
                try:
                    target = max(S, manifest['start_S'])
                    if target < manifest['end_S'] and target not in markets:
                        markets[target] = r.market(target)
                        emit('market', S=target, market=markets[target])
                    if r.bars_due(candle, r.now_ms()):
                        candle = r.bars()
                        emit('bars', bars=candle)
                except r.ERRORS as ex:
                    emit('input_gap', reason=str(ex)[:180])
            if active:
                for age in SLOTS:
                    if (S, age) in attempts or time.time()-S < age:
                        continue
                    attempts.add((S, age))
                    try:
                        if r.now_ms() > (S+age+3)*1000:
                            raise ValueError('missed decision deadline')
                        m = markets[S]
                        tokens = json.loads(m['clobTokenIds'])
                        pair, errors, requested, when = books(pool, tokens)
                        signal, side, context_gap = {}, None, None
                        try:
                            if candle is None:
                                raise ValueError('bars not prepared')
                            signal, side, _ = r.decide(args.prices_db, S, when, pair, candle, m)
                        except r.ERRORS as ex:
                            context_gap = str(ex)[:180]
                        orders = {lane: intent(portfolios.get((S, lane), []), pair, m, side, age, 'add' in lane, participate)
                                  for lane in LANES}
                        computed = r.now_ms()
                        if computed > (S+age+3)*1000:
                            raise ValueError('late decision')
                        emit('decision', S=S, age=age, signal=signal, entry_side=side, context_gap=context_gap,
                             book_errors=errors, books=pair, intents=orders, decision_ms=computed,
                             feature_cutoff_ms=when, request_ms=requested,
                             inventory={lane: position(portfolios.get((S, lane), [])) for lane in LANES})
                        for speed in ('fast', '250'):
                            chosen = {lane: order for lane, order in orders.items() if lane.endswith(speed) and order}
                            if not chosen:
                                continue
                            if speed == '250':
                                time.sleep(max(0., (computed+250-r.now_ms())/1000))
                            quote, errors, sent, received = books(pool, tokens)
                            fills, rejected = {}, {}
                            for lane, order in chosen.items():
                                try:
                                    if received-computed > 3000 or received >= (S+300)*1000:
                                        raise ValueError('late execution quote')
                                    if speed == '250' and sent-computed < 250:
                                        raise ValueError('early delayed quote')
                                    fills[lane] = execute(order, portfolios.get((S, lane), []), quote, m,
                                                          (received-S*1000)/1000)
                                except r.ERRORS as ex:
                                    rejected[lane] = str(ex)[:180]
                            emit('execution', S=S, age=age, speed=speed, books=quote, book_errors=errors,
                                 fills=fills, rejected=rejected, decision_ms=computed,
                                 request_ms=sent, execution_ms=received, delay_ms=received-computed)
                            for lane, fill in fills.items():
                                portfolios.setdefault((S, lane), []).append(fill)
                    except r.ERRORS as ex:
                        emit('gap', S=S, age=age, reason=str(ex)[:180])
            if age_now < 20 and now-last_grade >= 60:
                last_grade = now
                for old in sorted({s for s, _ in attempts}-resolved)[:3]:
                    if old+330 > now:
                        continue
                    try:
                        m = base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{old}?snapshot={int(now)//30}',
                                     timeout=3, attempts=1)
                        if m['slug'] != f'btc-updown-5m-{old}':
                            raise ValueError('resolution identity mismatch')
                        winner = base.outcome(m)
                        positions = {lane: position(portfolios.get((old, lane), [])) for lane in LANES}
                        emit('resolution', S=old, winner=winner, condition=m['conditionId'], positions=positions,
                             pnl={lane: pos['qty'][winner]-pos['cash'] for lane, pos in positions.items()},
                             attempted_slots=sum(s == old for s, _ in attempts), expected_slots=len(SLOTS))
                        resolved.add(old)
                    except r.ERRORS as ex:
                        emit('resolution_pending', S=old, reason=str(ex)[:180])
            if now-last_health >= 60:
                last_health = now
                emit('health', attempts=len(attempts), resolved=len(resolved),
                     fills={lane: sum(len(f) for (s, name), f in portfolios.items() if name == lane) for lane in LANES},
                     end_S=manifest['end_S'])
            time.sleep(.05)
    emit('stop', reason='stop_file' if (out/'STOP_SHADOW').exists() else 'duration',
         pending=sorted({s for s, _ in attempts}-resolved))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prices-db', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--participate', action='store_true', help='separate experiment: try one initial entry in every window')
    args = parser.parse_args()
    if not args.prices_db.is_file():
        parser.error('existing public prices database required')
    watch(args)
