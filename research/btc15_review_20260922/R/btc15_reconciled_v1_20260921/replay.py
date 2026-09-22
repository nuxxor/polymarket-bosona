"""Finite corrected execution scenarios; REST/block timestamps fail economic gate."""
from collections import Counter
from decimal import Decimal as D
from itertools import product

from common import FABLE, INPUTS, S, module, protected, read, save

old = module('fable_replay_source', FABLE/'code/passive_replay.py')
CLIP, CASH, NET, LOSS = D(5), D(15), D(10), D(5)
DELAY = 250


def dec(x):
    v = D(str(x))
    if not v.is_finite():
        raise ValueError('nonfinite amount')
    return v


def state():
    return dict(q=[D(0), D(0)], cash=D(0), fills=[], quotes={}, hedge=None,
                hedging=False, counters=Counter(), uncertain=False, max_reserved=D(0))


def obligations(s):
    return list(s['quotes'].values()) + ([s['hedge']] if s['hedge'] else [])


def safe(s, pending):
    """Every subset of outstanding BUY amounts must respect all three limits."""
    for flags in product((0, 1), repeat=len(pending)):
        q, cash = s['q'].copy(), s['cash']
        for on, o in zip(flags, pending):
            if on:
                q[o['side']] += o['left']
                cash += o['left']*o['limit']
        if cash > CASH or abs(q[0]-q[1]) > NET or cash-min(q) > LOSS:
            return False
    return True


def reserve(s, o):
    if not (o['side'] in (0, 1) and 0 < o['left'] <= CLIP and 0 < o['limit'] <= D('1.1')):
        raise ValueError('invalid pending order')
    pending = obligations(s)+[o]
    if not safe(s, pending):
        s['counters']['reservation_rejected'] += 1
        return False
    s['max_reserved'] = max(s['max_reserved'], s['cash']+sum(x['left']*x['limit'] for x in pending))
    return True


def fill(s, o, qty, price, when, kind):
    qty, price = dec(qty), dec(price)
    if not (0 < qty <= o['left'] and price <= o['limit'] and when >= o['active_ms']):
        raise ValueError('invalid fill quantity/price/time')
    s['q'][o['side']] += qty
    s['cash'] += qty*price
    o['left'] -= qty
    s['fills'].append(dict(side=o['side'], qty=qty, cash=qty*price, price=price,
                           when=when, kind=kind))
    assert safe(s, obligations(s)), 'outstanding-order risk invariant'


def expire(s, when):
    for side, o in list(s['quotes'].items()):
        if o['left'] == 0 or when >= o['cancel_ms']:
            del s['quotes'][side]


def consume(s, p, when, mode):
    """One print supplies at most its quantity; no trade-through free fill."""
    o = s['quotes'].get(p['side'])
    if not o or when < o['active_ms'] or when >= o['cancel_ms'] or dec(p['price']) > o['limit']:
        return
    available = dec(p['size'])
    if available <= 0:
        raise ValueError('nonpositive print')
    if mode == 'queue_back':
        ahead = min(available, o['ahead'])
        o['ahead'] -= ahead
        available -= ahead
    if available:
        qty = min(o['left'], available)
        fill(s, o, qty, o['limit'], when, 'maker')
        s['counters']['partial_fills'] += qty < CLIP


def quote(b, now):
    bids, asks, stamp = b
    if not bids or not asks or not 0 <= now-stamp <= 3000:
        return None
    bid, ask = dec(bids[0][0]), dec(asks[0][0])
    if not 0 < bid < ask < 1 or ask-bid > D('.03'):
        return None
    return bid


def ask_cost(asks, qty, market):
    rate = dec(market['feeSchedule']['rate']) if market.get('feesEnabled') else D(0)
    exponent = market.get('feeSchedule', {}).get('exponent', 1)
    if exponent != 1:
        raise ValueError('unsupported fee exponent')
    left, cash = qty, D(0)
    for p, q in asks:
        p, q = dec(p), dec(q)
        if not 0 < p < 1 or q <= 0:
            raise ValueError('invalid ask')
        take = min(left, q)
        cash += take*(p+rate*p*(1-p))
        left -= take
        if not left:
            return cash/qty
    raise ValueError('insufficient ask depth')


def run(snaps, tokens, prints, start, mode, offset, hedge, market):
    """Diagnostic only: print ts is block time, never claimed as match time."""
    if mode not in ('queue_back', 'queue_front'):
        raise ValueError('unknown queue scenario')
    s, cursor, previous = state(), 0, None
    pp = sorted([dict(p, side=tokens.index(p['token'])) for p in prints if p['token'] in tokens],
                key=lambda p:p['ts'])
    deadline = (start+840)*1000+DELAY
    for snap in snaps:
        now = snap['received_ms']
        gap = snap.get('gap') or (previous is not None and now-previous > 3000)
        # Missing interval is unknown execution, not a free cancellation.
        if gap and obligations(s):
            s['uncertain'] = True
            s['counters']['unobserved_live_interval'] += 1
            break
        while cursor < len(pp) and pp[cursor]['ts']*1000 <= now:
            p = pp[cursor]
            when = p['ts']*1000
            expire(s, when)
            if not gap:
                consume(s, p, when, mode)
            cursor += 1
        expire(s, now)
        previous = now
        if snap.get('gap'):
            continue
        age = now/1000-start
        if s['hedge']:
            o = s['hedge']
            if snap['requested_ms'] >= o['active_ms']:
                side = o['side']
                try:
                    if now-o['decision_ms'] > 3000 or quote(snap['books'][tokens[side]], now) is None:
                        raise ValueError('stale hedge execution')
                    unit = ask_cost(snap['books'][tokens[side]][1], o['left'], market)
                    if unit > o['limit']:
                        raise ValueError('hedge price limit')
                    fill(s, o, o['left'], unit, now, 'taker')
                except ValueError:
                    s['counters']['hedge_execution_rejected'] += 1
                s['hedge'] = None
        net = s['q'][0]-s['q'][1]
        if not net:
            s['hedging'] = False
        if not 30 <= age < 840 or gap:
            for o in s['quotes'].values():
                o['cancel_ms'] = min(o['cancel_ms'], now+DELAY)
            continue
        if hedge and abs(net) >= NET:
            s['hedging'] = True
        if s['hedging']:
            for o in s['quotes'].values():
                o['cancel_ms'] = min(o['cancel_ms'], now+DELAY)
            if not obligations(s) and net:
                side, qty = int(net > 0), min(CLIP, abs(net))
                try:
                    if quote(snap['books'][tokens[side]], now) is None:
                        raise ValueError('invalid hedge decision')
                    unit = ask_cost(snap['books'][tokens[side]][1], qty, market)
                    o = dict(side=side, left=qty, limit=unit, decision_ms=now, active_ms=now+DELAY)
                    if reserve(s, o):
                        s['hedge'] = o
                except ValueError:
                    s['counters']['hedge_depth_missing'] += 1
            continue
        for side in (0, 1):
            b = snap['books'][tokens[side]]
            bid = quote(b, now)
            target = bid-dec(offset) if bid is not None else None
            o = s['quotes'].get(side)
            if o and (target != o['limit'] or target is None):
                o['cancel_ms'] = min(o['cancel_ms'], now+DELAY)
            if o or target is None or target <= 0:
                continue
            o = dict(side=side, left=CLIP, limit=target, active_ms=now+DELAY,
                     cancel_ms=deadline, ahead=sum((dec(q) for p,q in b[0] if dec(p)==target), D(0)))
            if reserve(s, o):
                s['quotes'][side] = o
        assert safe(s, obligations(s))
    if obligations(s) and (previous is None or previous < deadline):
        s['uncertain'] = True
        s['counters']['open_execution_tail'] += 1
    assert safe(s, obligations(s))
    return s


def main():
    protected()
    tape_path = S/'raw/book_validation_prefix.json.gz'
    tape, tails = old.load_tape([tape_path])
    import hashlib
    INPUTS[str(tape_path)] = hashlib.sha256(tape_path.read_bytes()).hexdigest()
    windows = [w for w in read(S/'results/windows.json') if w['full'] and w['winner'] is not None]
    output = []
    for w in windows:
        slug, start = w['slug'], w['S']
        m = read(S/'raw/new_period_markets'/f'{slug}.json')['data']
        assert old.r.classify(m)['group'] == 'btc_15m'
        tokens = old.json.loads(m['clobTokenIds'])
        for suffix in ('true', 'false'):
            read(FABLE/'raw/market_trades'/f'{slug}_taker{suffix}.json')
        pp, stats = old.load_prints(FABLE/'raw/market_trades', slug)
        row = dict(slug=slug, prints=stats, arms={}, economic_pnl=None,
                   gate='MISSING_MATCH_CLOCK_AND_L2_EVENTS')
        for name, offset, hedge in [('touch', '0', False), ('one_cent_back', '.01', False), ('touch_hedge', '0', True)]:
            for mode in ('queue_back', 'queue_front'):
                s = run(tape[start], tokens, pp, start, mode, offset, hedge, m)
                row['arms'][name+':'+mode] = dict(q=s['q'], cash=s['cash'],
                    diagnostic_pnl=None if s['uncertain'] else s['q'][w['winner']]-s['cash'],
                    uncertain=s['uncertain'], fills=s['fills'], counters=s['counters'],
                    max_reserved=s['max_reserved'], end_worst=min(s['q'])-s['cash'])
        output.append(row)
    summary = {}
    for arm in output[0]['arms']:
        values = [x['arms'][arm] for x in output]
        known = [x['diagnostic_pnl'] for x in values if x['diagnostic_pnl'] is not None]
        summary[arm] = dict(markets=len(values), complete_scenarios=len(known),
            diagnostic_pnl=sum(known, D(0)), economic_pnl=None,
            cash_cap_violations=sum(x['cash'] > CASH for x in values),
            worst_cap_violations=sum(x['end_worst'] < -LOSS for x in values),
            fills=sum(len(x['fills']) for x in values),
            max_cash=max(x['cash'] for x in values), max_reserved=max(x['max_reserved'] for x in values))
    save('results/replay.json', dict(markets=output, summary=summary,
        economic_status='MISSING_DATA', open_tapes=tails,
        note='Correction diagnostics only; block-clock prints and 1s snapshots do not validate execution. '
             'Queue scenarios are not mathematical PnL bounds. 250ms is an assumption, not measured latency.'))
    save('results/replay_inputs.json', INPUTS)
    protected()
    print(old.json.dumps(summary, default=str))


if __name__ == '__main__':
    main()
