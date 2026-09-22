"""Small offline regression + actual frozen-data causality/reconciliation checks."""
from copy import deepcopy
from decimal import Decimal
from math import isclose
from unittest.mock import patch
import gzip
import json
import socket

import research as r


def main():
    r.protect()
    checks = []
    fills, grid = r.read('fills.json.gz'), r.read('grid.json.gz')
    assert len({f['id'] for f in fills}) == len(fills)
    assert all(abs(Decimal(str(f['price']))*f['quantity_units']-f['gross_units']) < Decimal('.00001') for f in fills)
    assert all(f['actor'] == (f['owner'] == r.WALLET) and f['qty'] > 0 and f['fee_units'] >= 0 for f in fills)
    assert all(f['fee_units'] == 0 for f in fills if f['actor'])
    parent = {}
    for f in fills:
        ident = f['market'], f['side'], f['owner']
        assert parent.setdefault(f['parent'], ident) == ident
    checks.append('real BUY identity, price, explicit chain role, actor fee and parent consistency')
    for f in fills:
        for shift in r.P['anchor_shifts_ms']:
            for h in r.P['horizons_ms']:
                v = f['anchors'][str(shift)]['markouts'][str(h)]
                if f['rcv']+shift+h >= (f['market']+900)*1000:
                    assert v == {'invalid': 'expiry_censored'}
                if 'invalid' not in v:
                    assert isclose(v['markout'], v['arrival_gap']+v['drift'], abs_tol=1e-10)
    checks.append('real horizons censored, markout decomposition exact')
    toy = {9000: {'mid': [.5, .5]}}
    censored = r.markouts(toy, {'side': 0, 'price': .4}, 9000, 10000)
    assert all(v == {'invalid': 'expiry_censored'} for v in censored.values())
    broken = {9000: {'invalid': 'empty_side'}}
    assert all('invalid' in v for v in r.markouts(broken, {'side': 0, 'price': .4}, 9000, 25000).values())
    checks.append('explicit expiry/empty-book examples never become zero returns')
    chosen = r.read('matches.json')
    altered = deepcopy(fills)
    for f in altered:
        f.update(won=not f['won'], qty=999999, anchors={})
    for caliper in r.P['calipers']:
        assert r.match(altered, caliper) == chosen[caliper['name']]
    checks.append('all real control matches unchanged by outcomes, future prices, size')
    for name, pairs in chosen.items():
        for f in r.pair_rows(fills, pairs):
            c = f['control']
            assert f['market'] == c['market'] and f['side'] == c['side'] and not c['actor']
            assert c['fee_units'] == 0  # Observed selected controls; not the definition of maker.
            assert (f['tx'] == c['tx'] and f['match_log'] == c['match_log']) if name == 'same_match' else f['tx'] != c['tx']
    checks.append('every real pair preserves contract, side, owner and transaction condition')
    test = [dict(market=1, parent='a', qty=1, v=100), dict(market=1, parent='a', qty=1, v=100),
            dict(market=1, parent='b', qty=1, v=0), dict(market=2, parent='c', qty=1, v=-50)]
    s = r.summarize(test, lambda x: x['v'])
    assert s['equal_market'] == 0 and s['mean'] == 37.5 and s['parents'] == 3
    checks.append('parent and market weights do not reward fragmented fills')
    books = [dict(ready=True, obs=1000, rcv=1000, BUY={400000: 5}, SELL={600000: 7}),
             dict(ready=True, obs=1000, rcv=1000, BUY={400000: 7}, SELL={600000: 5})]
    assert r.compact(books, 1000)['mid'] == [.5, .5]
    assert r.compact(books, 4001)['invalid'] == 'unready_or_stale'
    assert r.compact(books, 999)['invalid'] == 'unready_or_stale'
    books[1]['BUY'][400000] += 1
    assert r.compact(books, 1000)['invalid'] == 'complement_mismatch'
    checks.append('stale, future-source and asymmetric-depth books rejected')
    def event(t, token, side, size, tx):
        return dict(k='last_trade_price', rcv=t, p=dict(transaction_hash=tx, asset_id=token,
                    side=side, size=size, price='.5', timestamp=str(t)))
    pressure = r.public_pressure([event(1, 'up', 'BUY', '5', 'a'), event(2, 'up', 'BUY', '5', 'a'),
                                 event(3, 'down', 'SELL', '3', 'b'), event(4, 'up', 'SELL', '2', 'c')], ['up', 'down'])
    assert pressure == ([1, 3, 4], [0, 5000000, 8000000, 6000000])
    checks.append('public direction and retransmission preserve one active-match volume')
    causal_cases = []
    for cov in r.read('coverage.json'):
        if not cov['replay_eligible']:
            continue
        root, _ = r.old.select(cov['start'])
        tokens = json.loads(r.a.read(root/'raw/market_start.json')['data']['clobTokenIds'])
        with gzip.open(cov['input_events'], 'rt') as stream:
            events = [json.loads(line) for line in stream]
        events, _ = r.old.prior.book_events(events, tokens)
        # Two fixed instants per market, both sides, both guard choices.
        for age in (120, 720):
            now = (cov['start']+age)*1000
            times = [now-1000, now-6000, now-5000, now-10000]
            full, _ = r.a.m1.books_at(events, tokens, times)
            full = {t: r.compact(b, t) for t, b in full.items()}
            pressure = r.public_pressure(events, tokens)
            for guard in (1000, 5000):
                cutoff = now-guard
                prefix = [e for e in events if e['rcv'] <= cutoff]
                small, _ = r.a.m1.books_at(prefix, tokens, [cutoff-5000, cutoff])
                small = {t: r.compact(b, t) for t, b in small.items()}
                prefix_pressure = r.public_pressure(prefix, tokens)
                for side in (0, 1):
                    assert r.features(full, pressure, cutoff, side) == r.features(small, prefix_pressure, cutoff, side)
                    causal_cases.append([cov['start'], age, guard, side])
    checks.append('48 real actor-free feature contexts unchanged after deleting all future data')
    assert len(causal_cases) == 48
    assert len(grid) == 6*879*2
    assert all('actor' not in g and 'tx' not in g for g in grid)
    checks.append('10548 actor-free grid contexts, no actor/receipt/fill inputs')
    r.protect()
    r.a.save(r.HERE/'verification.json', dict(checks=checks, causal_cases=causal_cases, passed=len(checks)))
    print(f'{len(checks)} checks passed; 48 actual causal cases')


if __name__ == '__main__':
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network prohibited')):
        main()
