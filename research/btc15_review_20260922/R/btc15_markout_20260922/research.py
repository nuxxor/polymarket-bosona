"""Offline filled-order markouts and fixed controls; no orders or economic replay."""
from bisect import bisect_right
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from statistics import mean, median
from unittest.mock import patch
import gzip
import json
import socket
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parent
T = R/'btc15_timing_sensitivity_20260922'
sys.path.insert(0, str(T))
import run as old  # noqa: E402

a = old.a
P = a.read(HERE/'protocol.json')
WALLET = '0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
UNIT = 1000000


def save(name, value):
    path = HERE/'results'/name
    path.parent.mkdir(exist_ok=True)
    content = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
    path.write_bytes(gzip.compress(content, mtime=0) if name.endswith('.gz') else content)


def read(name):
    path = HERE/'results'/name
    return json.loads(gzip.decompress(path.read_bytes()) if name.endswith('.gz') else path.read_bytes())


def protect():
    a.protected()
    assert a.sha(HERE/'protocol.json') == (HERE/'protocol.sha256').read_text().strip()
    assert a.sha(HERE/'design_frozen.md') == P['design_sha256']
    paths = {R/'candidate.py', R/'protocol.json', Path(a.__file__), Path(a.m1.__file__),
             Path(a.m1.probe.__file__), Path(old.__file__), Path(old.prior.__file__)}
    for root in (T, old.N, old.Z):
        manifest = root/'delivery_manifest.json'
        paths.add(manifest)
        for name, digest in a.read(manifest)['sha256'].items():
            assert a.sha(root/name) == digest, str(root/name)
    for name, digest in a.read(old.E/'dependencies.json').items():
        assert a.sha(Path(name)) == digest, name
        paths.add(Path(name))
    current = {str(p): a.sha(p) for p in sorted(paths)}
    manifest = HERE/'sources.json'
    if not manifest.exists():
        a.save(manifest, current)
    assert a.read(manifest) == current


def compact(books, now):
    """Two-token integrity precedes any mid-price calculation; no spread selection."""
    if any(not b['ready'] or not 0 <= now-b['obs'] <= 3000
           or not 0 <= now-b['rcv'] <= 3000 for b in books):
        return {'invalid': 'unready_or_stale'}
    if any(not b['BUY'] or not b['SELL'] for b in books):
        return {'invalid': 'empty_side'}
    if any(not 0 < max(b['BUY']) < min(b['SELL']) < UNIT for b in books):
        return {'invalid': 'crossed_or_invalid_price'}
    if any(books[s]['BUY'] != {UNIT-p: q for p, q in books[1-s]['SELL'].items()}
           for s in (0, 1)):
        return {'invalid': 'complement_mismatch'}
    return {'mid': [(max(b['BUY'])+min(b['SELL']))/(2*UNIT) for b in books],
            'bid': [max(b['BUY'])/UNIT for b in books],
            'ask': [min(b['SELL'])/UNIT for b in books],
            'last_received': [b['rcv'] for b in books], 'last_source': [b['obs'] for b in books]}


def public_pressure(events, tokens):
    """Only received public fields: no actor IDs, future chain roles or quantities."""
    seen, times, totals, running = set(), [], [0], 0
    for e in events:
        if e['k'] != 'last_trade_price':
            continue
        p = e['p']
        key = tuple(p[k] for k in ('transaction_hash', 'asset_id', 'side', 'size', 'price'))
        if key in seen:
            continue
        seen.add(key)
        sign = (1 if tokens.index(p['asset_id']) == 0 else -1)*(1 if p['side'] == 'BUY' else -1)
        running += sign*a.m1.units(p['size'])
        times.append(e['rcv'])
        totals.append(running)
    assert times == sorted(times)
    return times, totals


def features(books, pressure, now, side):
    """May run on any public-clock instant; does not accept a Bosona fill."""
    recent, before = books[now], books[now-P['feature_lookback_ms']]
    if 'invalid' in recent or 'invalid' in before:
        return {'invalid': 'missing_predecision_book'}
    times, totals = pressure
    i, j = bisect_right(times, now-P['feature_lookback_ms']), bisect_right(times, now)
    flow = (totals[j]-totals[i])*(1 if side == 0 else -1)/UNIT
    momentum = round(100*(recent['mid'][side]-before['mid'][side]), 10)
    return {'H1': (momentum > 0)-(momentum < 0), 'H2': (flow > 0)-(flow < 0),
            'momentum_cents': momentum, 'flow_shares': flow,
            'mid': recent['mid'][side], 'bid': recent['bid'][side],
            'spread_cents': 100*(recent['ask'][side]-recent['bid'][side])}


def markouts(books, row, anchor, end):
    base = books[anchor]
    result = {}
    for horizon in P['horizons_ms']:
        when = anchor+horizon
        if when >= end:
            result[str(horizon)] = {'invalid': 'expiry_censored'}
        elif 'invalid' in base or 'invalid' in books[when]:
            result[str(horizon)] = {'invalid': 'base_'+base['invalid'] if 'invalid' in base
                                   else 'horizon_'+books[when]['invalid']}
        else:
            mid, initial = books[when]['mid'][row['side']], base['mid'][row['side']]
            result[str(horizon)] = {'markout': 100*(mid-row['price']),
                'arrival_gap': 100*(initial-row['price']), 'drift': 100*(mid-initial)}
    return result


def extract():
    protect()
    all_fills, all_grid, coverage = [], [], []
    for start in P['starts']:
        root, gate = old.select(start)
        gate.pop('economic_pnl')
        coverage.append(gate)
        if not gate['replay_eligible']:
            print(start, 'excluded by frozen gate', flush=True)
            continue
        path = old.N/'channels/A/events.jsonl.gz' if start == 1790031600 else root/'raw/events.jsonl.gz'
        with gzip.open(path, 'rt') as f:
            events = [json.loads(line) for line in f]
        market = a.read(root/'raw/market_start.json')['data']
        tokens = json.loads(market['clobTokenIds'])
        events, origin = old.prior.book_events(events, tokens)
        assert all(events[i]['rcv'] <= events[i+1]['rcv'] for i in range(len(events)-1))
        groups = {p.stem: a.m1.matches(a.read(p)['data']) for p in sorted((root/'raw/receipts').glob('*.json'))}
        flows, errors, metrics = a.m1.trade_flows(events, groups, tokens)
        assert not errors, errors
        rp = T/'raw/market_result_1790031600.json' if start == 1790031600 else root/'raw/market_result.json'
        result = a.read(rp)['data']
        for m in (market, result):
            meta = a.accounting.ref.classify(m)
            assert (meta['group'], meta['S'], meta['end'], meta['mechanism']) == ('btc_15m', start, start+900, 'chainlink_twap60')
            assert json.loads(m['clobTokenIds']) == tokens
        winner = a.accounting.ref.base.outcome(result)
        assert winner in (0, 1)
        makers = {(tx, m['log_index']): (m, g) for tx, gg in groups.items() for g in gg for m in g['makers']}
        rows, omitted = [], Counter()
        for f in sorted(flows, key=lambda f: (f['received'], f['tx'], f['log_index'])):
            m, g = makers[f['tx'], f['log_index']]
            assert f['obs_lo'] == f['obs_hi'] <= f['received']
            if not start*1000 <= f['received'] < (start+900)*1000:
                omitted['outside_received_window'] += 1
                continue
            if not start*1000 <= f['obs_lo'] < (start+900)*1000:
                omitted['outside_source_window'] += 1
                continue
            if m['side'] != 0:
                omitted['maker_sell'] += 1
                continue
            assert m['role'] == 'maker' and m['qty'] > 0
            price = Decimal(m['cash_cost']-m['fee'])/m['qty']
            assert 0 < price < 1
            side = tokens.index(m['token'])
            rows.append(dict(id=f"{f['tx']}:{m['log_index']}", parent=m['owner']+':'+m['order_hash'],
                owner=m['owner'], actor=m['owner'] == WALLET, market=start, side=side,
                tx=f['tx'], match_log=g['match_log'], log=m['log_index'], rcv=f['received'],
                obs=f['obs_lo'], qty=m['qty']/UNIT, quantity_units=m['qty'],
                gross_units=m['cash_cost']-m['fee'], fee_units=m['fee'], price=float(price),
                remaining_seconds=start+900-f['received']/1000, won=side == winner))
        assert len({r['id'] for r in rows}) == len(rows)
        checks = set()
        for r in rows:
            for shift in P['anchor_shifts_ms']:
                anchor = r['rcv']+shift
                checks.add(anchor)
                checks.update(anchor+h for h in P['horizons_ms'] if anchor+h < (start+900)*1000)
                for guard in P['feature_guards_ms']:
                    checks.update((anchor-guard, anchor-guard-P['feature_lookback_ms']))
        grid_times = [(start+n)*1000 for n in range(11, 890)]
        for now in grid_times:
            checks.update((now, now+10000, now-1000, now-6000, now-5000, now-10000))
        # Existing audited state reconstruction; retain only compact observations here.
        snapshots, issues = a.m1.books_at(events, tokens, sorted(checks))
        assert not issues.get('future_source_clock') and not issues.get('out_of_order_book')
        books = {t: compact(b, t) for t, b in snapshots.items()}
        del snapshots
        pressure = public_pressure(events, tokens)
        assert len(pressure[0]) == metrics['matches'], 'public pressure multiplicity does not reconcile'
        for r in rows:
            r['anchors'] = {}
            for shift in P['anchor_shifts_ms']:
                anchor = r['rcv']+shift
                r['anchors'][str(shift)] = {
                    'markouts': markouts(books, r, anchor, (start+900)*1000),
                    'features': {str(g): features(books, pressure, anchor-g, r['side']) for g in P['feature_guards_ms']}}
        for now in grid_times:
            for side in (0, 1):
                b, future = books[now], books[now+10000]
                all_grid.append(dict(market=start, now=now, side=side,
                    drift=None if 'invalid' in b or 'invalid' in future else 100*(future['mid'][side]-b['mid'][side]),
                    features={str(g): features(books, pressure, now-g, side) for g in P['feature_guards_ms']}))
        all_fills.extend(rows)
        gate.update(book_origin=origin, winner=winner, flow_metrics=metrics, omitted=dict(omitted),
            buy_fills=len(rows), buy_parents=len({r['parent'] for r in rows}),
            actor_fills=sum(r['actor'] for r in rows),
            actor_parents=len({r['parent'] for r in rows if r['actor']}),
            all_requested_points=len(books), invalid_points=dict(Counter(b['invalid'] for b in books.values() if 'invalid' in b)),
            input_events=str(path), input_events_sha256=a.sha(path),
            source_delay_ms={'median': median(r['rcv']-r['obs'] for r in rows), 'max': max(r['rcv']-r['obs'] for r in rows)})
        print(start, 'BUY', len(rows), 'Bosona', gate['actor_fills'], 'parents', gate['actor_parents'], flush=True)
    save('fills.json.gz', all_fills)
    save('grid.json.gz', all_grid)
    save('coverage.json', coverage)
    protect()


def summarize(rows, value, valid=None):
    """Equal fills inside parent, equal parents inside market, equal markets."""
    valid = valid or (lambda r: True)
    selected = [(r, value(r)) for r in rows if valid(r)]
    selected = [(r, v) for r, v in selected if v is not None]
    if not selected:
        return {'n': 0, 'parents': 0, 'markets': 0, 'mean': None, 'equal_market': None}
    parent = defaultdict(list)
    for r, v in selected:
        parent[(r['market'], r['parent'])].append(v)
    markets = defaultdict(list)
    for (market, _), values in parent.items():
        markets[market].append(mean(values))
    market_values = {str(k): mean(v) for k, v in sorted(markets.items())}
    loo = [mean(v for k, v in market_values.items() if k != excluded) for excluded in market_values] if len(markets) > 1 else []
    return {'n': len(selected), 'parents': len(parent), 'markets': len(markets),
            'mean': mean(v for _, v in selected), 'median': median(v for _, v in selected),
            'share_weighted': sum(r['qty']*v for r, v in selected)/sum(r['qty'] for r, _ in selected),
            'equal_parent': mean(mean(v) for v in parent.values()),
            'equal_market': mean(market_values.values()), 'by_market': market_values,
            'leave_one_market_out': [min(loo), max(loo)] if loo else None,
            'positive_fills': sum(v > 0 for _, v in selected)}


def metric(r, horizon=10000, key='markout', shift=0):
    return r['anchors'][str(shift)]['markouts'][str(horizon)].get(key)


def stage1():
    rows = read('fills.json.gz')
    output = {}
    for shift in P['anchor_shifts_ms']:
        for who in ('actor', 'other'):
            for subset in ('all', 'won', 'lost'):
                selected = [r for r in rows if r['actor'] == (who == 'actor') and (subset == 'all' or r['won'] == (subset == 'won'))]
                key = f'{shift}:{who}:{subset}'
                output[key] = {'raw_fills': len(selected), 'parents': len({r['parent'] for r in selected}), 'horizons': {}}
                for h in P['horizons_ms']:
                    output[key]['horizons'][str(h)] = {
                        field: summarize(selected, lambda r: metric(r, h, field, shift)) for field in ('markout', 'arrival_gap', 'drift')}
                    output[key]['horizons'][str(h)]['missing'] = dict(Counter(
                        r['anchors'][str(shift)]['markouts'][str(h)]['invalid'] for r in selected
                        if 'invalid' in r['anchors'][str(shift)]['markouts'][str(h)]))
    save('stage1_markouts.json', output)
    charged = [r for r in rows if r['fee_units']]
    save('fee_audit.json', {'maker_with_nonzero_fee': len(charged),
        'actor_with_nonzero_fee': sum(r['actor'] for r in charged),
        'total_fee_units': sum(r['fee_units'] for r in charged),
        'owners': len({r['owner'] for r in charged}),
        'records': [{k: r[k] for k in ('id', 'market', 'owner', 'quantity_units', 'gross_units', 'fee_units')} for r in charged]})


def match(rows, caliper, same_match=False):
    pairs = []
    for r in rows:
        if not r['actor']:
            continue
        eligible = [c for c in rows if not c['actor'] and c['market'] == r['market'] and c['side'] == r['side']
                    and (c['tx'] == r['tx'] and c['match_log'] == r['match_log'] if same_match else c['tx'] != r['tx'])
                    and abs(c['price']-r['price']) <= caliper['price']+1e-12
                    and abs(c['rcv']-r['rcv']) <= caliper['ms']]
        if not eligible:
            pairs.append({'actor_id': r['id'], 'control_id': None, 'eligible': 0})
            continue
        c = min(eligible, key=lambda c: (abs(c['price']-r['price'])/caliper['price']+abs(c['rcv']-r['rcv'])/caliper['ms'], c['rcv'], c['tx'], c['log']))
        pairs.append({'actor_id': r['id'], 'control_id': c['id'], 'eligible': len(eligible),
                      'price_difference_cents': 100*(r['price']-c['price']), 'time_difference_ms': r['rcv']-c['rcv']})
    return pairs


def pair_rows(rows, pairs):
    by_id = {r['id']: r for r in rows}
    return [dict(by_id[p['actor_id']], control=by_id[p['control_id']]) for p in pairs if p['control_id'] is not None]


def difference(r, h, field, shift):
    first, second = metric(r, h, field, shift), metric(r['control'], h, field, shift)
    return None if first is None or second is None else first-second


def stage2():
    rows = read('fills.json.gz')
    output, matching = {}, {}
    specs = [(c['name'], c, False) for c in P['calipers']]+[('same_match', P['calipers'][0], True)]
    for name, caliper, simultaneous in specs:
        pairs = match(rows, caliper, simultaneous)
        matching[name] = pairs
        paired = pair_rows(rows, pairs)
        reused = Counter(r['control']['parent'] for r in paired)
        output[name] = {'matched_fills': len(paired), 'unmatched_fills': len(pairs)-len(paired),
            'actor_parents': len({r['parent'] for r in paired}), 'control_parents': len(reused),
            'control_owners': len({r['control']['owner'] for r in paired}),
            'max_control_parent_reuse': max(reused.values(), default=0),
            'control_parent_reuse': dict(reused),
            'median_absolute_price_gap_cents': median(abs(p['price_difference_cents']) for p in pairs if p['control_id']) if paired else None,
            'median_absolute_time_gap_ms': median(abs(p['time_difference_ms']) for p in pairs if p['control_id']) if paired else None,
            'effects': {}}
        for shift in P['anchor_shifts_ms']:
            for h in P['horizons_ms']:
                for field in ('markout', 'arrival_gap', 'drift'):
                    key = f'{shift}:{h}:{field}'
                    output[name]['effects'][key] = summarize(paired, lambda r: difference(r, h, field, shift))
        output[name]['outcome_groups'] = {label: summarize([r for r in paired if r['won'] == won],
            lambda r: difference(r, 10000, 'markout', 0)) for label, won in [('won', True), ('lost', False)]}
        output[name]['leave_one_parent_out'] = {parent: summarize([r for r in paired if r['parent'] != parent],
            lambda r: difference(r, 10000, 'markout', 0))['equal_market'] for parent in sorted({r['parent'] for r in paired})}
    save('matches.json', matching)
    save('stage2_controls.json', output)


def get_feature(r, guard, hypothesis, shift=0):
    return r['anchors'][str(shift)]['features'][str(guard)].get(hypothesis)


def stage3():
    rows, grid = read('fills.json.gz'), read('grid.json.gz')
    paired = pair_rows(rows, read('matches.json')['primary'])
    output = {}
    for shift in P['anchor_shifts_ms']:
        for guard in P['feature_guards_ms']:
            for hyp in ('H1', 'H2'):
                key = f'{shift}:{guard}:{hyp}'
                o = output[key] = {'filled_context': {}, 'same_feature_pairs': {}, 'different_feature_pairs': {}}
                for who in ('actor', 'other'):
                    rr = [r for r in rows if r['actor'] == (who == 'actor')]
                    o['filled_context'][who] = {}
                    for label, sign in [('negative', -1), ('neutral', 0), ('positive', 1), ('missing', None)]:
                        subset = [r for r in rr if get_feature(r, guard, hyp, shift) == sign]
                        o['filled_context'][who][label] = {'raw_fills': len(subset),
                            'markout': summarize(subset, lambda r: metric(r, shift=shift)),
                            'drift': summarize(subset, lambda r: metric(r, key='drift', shift=shift))}
                o['positive_minus_negative_same_markets'] = {}
                for who in ('actor', 'other'):
                    negative = o['filled_context'][who]['negative']['drift'].get('by_market', {})
                    positive = o['filled_context'][who]['positive']['drift'].get('by_market', {})
                    effects = {m: positive[m]-negative[m] for m in positive if m in negative}
                    o['positive_minus_negative_same_markets'][who] = {
                        'by_market': effects, 'mean': mean(effects.values()) if effects else None}
                o['positive_feature_prevalence_difference'] = summarize(paired, lambda r:
                    None if get_feature(r, guard, hyp, shift) is None or get_feature(r['control'], guard, hyp, shift) is None
                    else int(get_feature(r, guard, hyp, shift) == 1)-int(get_feature(r['control'], guard, hyp, shift) == 1))
                for sign in (-1, 0, 1):
                    same = [r for r in paired if get_feature(r, guard, hyp, shift) == sign
                            and get_feature(r['control'], guard, hyp, shift) == sign]
                    o['same_feature_pairs'][str(sign)] = summarize(same, lambda r: difference(r, 10000, 'markout', shift))
                for first in (-1, 0, 1):
                    for second in (-1, 0, 1):
                        rr = [r for r in paired if get_feature(r, guard, hyp, shift) == first
                              and get_feature(r['control'], guard, hyp, shift) == second]
                        o['different_feature_pairs'][f'{first}:{second}'] = summarize(rr, lambda r: difference(r, 10000, 'drift', shift))
    # Actor-free grid: each second both tokens, never presumed filled quotes.
    grid_output = {}
    for guard in P['feature_guards_ms']:
        for hyp in ('H1', 'H2'):
            grid_output[f'{guard}:{hyp}'] = {}
            for label, sign in [('negative', -1), ('neutral', 0), ('positive', 1), ('missing', None)]:
                rr = [dict(r, parent=str(r['now'])+':'+str(r['side']), qty=1) for r in grid
                      if r['features'][str(guard)].get(hyp) == sign]
                grid_output[f'{guard}:{hyp}'][label] = summarize(rr, lambda r: r['drift'])
    save('stage3_hypotheses.json', output)
    save('stage3_actor_free_grid.json', grid_output)
    examples = []
    for won in (True, False):
        for hyp in ('H1', 'H2'):
            for sign in (-1, 0, 1):
                rr = [r for r in rows if r['actor'] and r['won'] == won and get_feature(r, 1000, hyp) == sign and metric(r) is not None]
                if rr:
                    # Explicitly outcome-selected illustrations, never inference sample filters.
                    examples.append({'won': won, 'hypothesis': hyp, 'sign': sign,
                        'lowest_markout': min(rr, key=lambda r: (metric(r), r['id'])),
                        'highest_markout': max(rr, key=lambda r: (metric(r), r['id']))})
    save('counterexamples.json', examples)


def reproduce():
    extract()
    stage1()
    stage2()
    stage3()


if __name__ == '__main__':
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline analysis attempted network')):
        {'extract': extract, 'stage1': stage1, 'stage2': stage2, 'stage3': stage3, 'protect': protect, 'all': reproduce}[sys.argv[1]]()
