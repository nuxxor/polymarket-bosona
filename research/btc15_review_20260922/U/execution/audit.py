#!/usr/bin/env python3
"""Finite, read-only BTC15 timing/context/execution audit. Writes only beside this file."""
import bisect
from collections import Counter, defaultdict
from decimal import Decimal
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import zlib

HERE = Path(__file__).resolve().parent
R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
MAIN = Path('/home/taygun/Masaüstü/polymarket-bosona')
S = R/'btc15_followup/status_20260921_1800'
sys.path.insert(0, str(R))
import candidate as c  # noqa: E402


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    (HERE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index(records):
    streams, by_event, refs = {}, {}, {}
    for name, seq in records.items():
        kept, last = [], -1
        for rcv, obs, px in sorted(set(seq)):
            if obs < last or obs > rcv:
                continue
            last = obs
            kept.append((rcv, obs, float(px)))
            if name == 'twap60' and obs % 900000 == 0:
                refs.setdefault(obs//1000, (rcv, float(px)))
        streams[name] = ([x[0] for x in kept], kept)
        ordered = sorted(kept, key=lambda x: (x[1], x[0]))
        by_event[name] = ([x[1] for x in ordered], ordered)
    return streams, by_event, refs


def at(indices, name, target, decision, corrected=False):
    """Historical event age is relative to target; availability remains <= decision."""
    streams, by_event, _ = indices
    times, seq = (by_event if corrected and target < decision else streams)[name]
    i = bisect.bisect_right(times, target)-1
    if corrected and target < decision:
        while i >= 0 and seq[i][0] > decision:
            i -= 1
    if i < 0:
        raise ValueError('missing_'+name)
    rcv, obs, px = seq[i]
    assert rcv <= decision and obs <= target
    if not 0 <= target-obs <= 3000:
        raise ValueError('event_age_'+name)
    if (not corrected or target == decision) and not 0 <= target-rcv <= 3000:
        raise ValueError('receipt_age_'+name)
    return px


def context(indices, start, now, corrected=False):
    _, _, refs = indices
    if start not in refs:
        raise ValueError('no_recorded_reference')
    rcv, ref = refs[start]
    if rcv > now*1000 or not 0 < now-start < 900:
        raise ValueError('reference_or_time_not_available')
    def price(name, t):
        return at(indices, name, t*1000, now*1000, corrected)
    spot, twap = price('spot', now), price('twap60', now)
    history = [price('spot', now-5*i) for i in range(13)]
    sigma = math.sqrt(sum((a-b)**2 for a, b in zip(history, history[1:]))/60)
    if sigma < 1e-8:
        raise ValueError('zero_volatility')
    remaining = start+900-now
    known = [] if remaining >= 60 else [price('spot', t) for t in range(start+840, now)]
    mean = spot if remaining >= 60 else (sum(known)+(60-len(known))*spot)/60
    variance_time = remaining-40 if remaining >= 60 else remaining**3/10800
    sd = sigma*math.sqrt(variance_time)
    p = .5*(1+math.erf((mean-ref)/max(sd, 1e-8)/math.sqrt(2)))
    return dict(S=start, now=now, ref=ref, reference_received_ms=rcv, spot=spot,
                twap=twap, sigma=sigma, final_up_prob=p, final_mean=mean,
                final_sd=sd, final_known_seconds=len(known))


def load_historical():
    records = defaultdict(list)
    manifest = read(R/'raw/btc15_context_manifest.json')
    excluded = []
    for path, expected in manifest['source_hashes'].items():
        p = Path(path)
        assert sha(p) == expected, str(p)
        try:
            with gzip.open(p, 'rt') as stream:
                if p.parent.name == 'recovered_prices':
                    for which, rcv, obs, px in json.load(stream):
                        if obs <= rcv:
                            records['spot' if which == 0 else 'twap60'].append((rcv, obs, float(px)))
                else:
                    # Match original whole-file exclusion on malformed archived hours.
                    part = [json.loads(line) for line in stream]
                    for x in part:
                        if x['f'] in ('spot', 'twap60') and x['obs']*1000 <= x['rcv']:
                            records[x['f']].append((x['rcv'], x['obs']*1000, float(x['px'])))
        except (OSError, ValueError, EOFError, zlib.error) as exc:
            excluded.append([p.name, type(exc).__name__])
    return index(records), dict(source_count=len(manifest['source_hashes']), excluded=excluded)


def calibration(rows):
    if not rows:
        return dict(n=0)
    bins = []
    for lo in range(0, 10):
        rr = [x for x in rows if lo/10 <= x['p'] and (x['p'] < (lo+1)/10 or lo == 9)]
        if rr:
            bins.append(dict(lo=lo/10, n=len(rr), predicted=statistics.mean(x['p'] for x in rr),
                             actual=statistics.mean(x['y'] for x in rr)))
    return dict(n=len(rows), markets=len({x['S'] for x in rows}),
                brier=statistics.mean((x['p']-x['y'])**2 for x in rows),
                half_brier=.25,
                logloss=statistics.mean(-math.log(max(1e-12, min(1-1e-12, x['p'] if x['y'] else 1-x['p']))) for x in rows),
                mean_p=statistics.mean(x['p'] for x in rows), up_rate=statistics.mean(x['y'] for x in rows), bins=bins)


def historical_audit(indices):
    universe = [w for w in read(R/'results/universe.json') if w['group'] == 'btc_15m']
    fills = [f for f in read(R/'results/fills.json') if f['group'] == 'btc_15m']
    stored = read(R/'raw/btc15_context.json')
    requests = defaultdict(set)
    for w in universe:
        requests[w['S']].update(range(w['S']+120, w['end'], 30))
    for f in fills:
        requests[f['S']].update((f['ts']-5, f['ts']-10))
    counts, changes, calibration_rows, failures = Counter(), [], [], Counter()
    corrected_contexts = {}
    for w in universe:
        start = w['S']
        for now in sorted(requests[start]):
            counts['requests'] += 1
            values = {}
            for corrected in (False, True):
                label = 'causal_history' if corrected else 'frozen'
                try:
                    values[label] = context(indices, start, now, corrected)
                    counts[label+'_valid'] += 1
                except ValueError as exc:
                    failures[label+':'+str(exc)] += 1
            key = f'{start}:{now}'
            old, new = values.get('frozen'), values.get('causal_history')
            assert (old is not None) == (key in stored), key
            if old:
                assert abs(old['final_up_prob']-stored[key]['final_up_prob']) < 1e-10, key
            if new and not old:
                counts['restored_contexts'] += 1
            if new:
                corrected_contexts[key] = new
            if old and new and abs(old['final_up_prob']-new['final_up_prob']) > 1e-10:
                counts['common_probability_changed'] += 1
            age = now-start
            if age in range(180, 841, 60):
                for label in values:
                    counts[label+'_scheduled_valid'] += 1
                    if age == 180:
                        counts[label+'_entry_contexts'] += 1
                if bool(old) != bool(new):
                    changes.append(dict(S=start, age=age, restored=bool(new), original_present=bool(old)))
            if age in (180, 600, 840, 870):
                for label, val in values.items():
                    calibration_rows.append(dict(S=start, age=age, variant=label, period=c.r.period(start),
                                                 p=val['final_up_prob'], y=int(w['winner'] == 0)))
    by = {}
    for label in ('frozen', 'causal_history'):
        for age in (180, 600, 840, 870):
            for period in ('discovery', 'chronological', 'update'):
                rr = [x for x in calibration_rows if (x['variant'], x['age'], x['period']) == (label, age, period)]
                by[f'{label}:{age}:{period}'] = calibration(rr)
    scenario = [x for x in read(R/'results/candidate_scenario_rows.json')
                if x['entry'] == 'discount' and x['slip'] == 0 and x['arm'] == 'managed']
    entry_rows = [x for x in scenario if x['entered']]
    path = dict(eligible=len(scenario), entered=len(entry_rows), added=sum(x['added'] for x in entry_rows),
                completed_before_add=sum(any(e['kind'] == 'complete' and e['time'] < x['S']+600 for e in x['events']) for x in entry_rows),
                neutral_at_end=sum(abs(x['q'][0]-x['q'][1]) < 1e-8 for x in entry_rows),
                events=dict(Counter(e['kind'] for x in entry_rows for e in x['events'])),
                pnl=sum(x['pnl'] for x in entry_rows))
    save('historical_context_changes.json', changes)
    save('calibration.json', by)
    (HERE/'corrected_contexts.json.gz').write_bytes(gzip.compress(json.dumps(corrected_contexts).encode(), mtime=0))
    return dict(counts=dict(counts), failures=dict(failures), frozen_context_exactly_reproduced=True,
                scheduled_total=len(universe)*12, candidate_frozen_price_scenario=path)


def load_s_prices(cutoff):
    frozen = HERE/'s_prices.json.gz'
    if frozen.exists():
        with gzip.open(frozen, 'rt') as stream:
            capture = json.load(stream)
        assert capture['cutoff_ms'] == cutoff
    else:
        rows, sources = [], []
        for hour in range(14, 19):
            path = MAIN/f'data/tape_cl_direct/cld_20260921_{hour:02d}.jsonl.gz'
            count = 0
            with gzip.open(path, 'rt') as stream:
                for line in stream:
                    x = json.loads(line)
                    if x['rcv'] > cutoff:
                        break
                    rows.append(x)
                    count += 1
            sources.append(dict(path=str(path), bytes=path.stat().st_size, mtime_ns=path.stat().st_mtime_ns,
                                prefix_rows=count, note='local original recorder receive clock; repository mirror is a later copy'))
        capture = dict(cutoff_ms=cutoff, rows=rows, sources=sources)
        frozen.write_bytes(gzip.compress(json.dumps(capture).encode(), mtime=0))
    records = defaultdict(list)
    for x in capture['rows']:
        if x['f'] in ('spot', 'twap60'):
            records[x['f']].append((x['rcv'], x['obs']*1000, float(x['px'])))
    return index(records), capture['sources']


def book_for(event, market, side, when):
    token = json.loads(market['clobTokenIds'])[side]
    raw = next(b for b in event['books'] if b['asset_id'] == token)
    asks = sorted((float(x['price']), float(x['size'])) for x in raw['asks'])
    bids = sorted((float(x['price']), float(x['size'])) for x in raw['bids'])
    if raw['market'] != market['conditionId']:
        raise ValueError('condition')
    if not 0 <= when-event['received_ms'] <= 3000 or not 0 <= when-int(raw['timestamp']) <= 3000:
        raise ValueError('stale_book')
    if not asks or not bids:
        raise ValueError('one_sided')
    if not 0 < asks[0][0]-bids[-1][0] <= .0300000001:
        raise ValueError('spread')
    if float(raw['min_order_size']) > 5:
        raise ValueError('min_size')
    c.r.base.ask_cost(dict(asks=asks), market, 5)
    return dict(raw, asks=asks, bid=bids[-1][0], observed_ms=int(raw['timestamp']),
                requested_ms=event['requested_ms'], received_ms=event['received_ms'])


def s_audit(indices, tape):
    windows = [w for w in read(S/'results/windows.json') if w['full'] and w['winner'] is not None]
    books = defaultdict(list)
    for x in tape:
        if x['kind'] == 'books':
            books[x['S']].append(x)
    rows, replays, counts, references = [], [], Counter(), []
    for w in windows:
        start = w['S']
        market = read(S/'raw/initial_markets'/f'{w["slug"]}.json')
        official = read(S/'raw/new_period_markets'/f'{w["slug"]}.json')['data']
        metadata = next(e['eventMetadata'] for e in official['events'] if e['slug'] == w['slug'])
        reference_rcv, reference = indices[2][start]
        end_rcv, end_twap = indices[2][w['end']]
        references.append(dict(S=start, start_difference=reference-metadata['priceToBeat'],
                               end_difference=end_twap-metadata['finalPrice'] if metadata.get('finalPrice') is not None else None,
                               reference_arrival_ms=reference_rcv-start*1000,
                               end_arrival_ms=end_rcv-w['end']*1000,
                               outcome_agrees=int(end_twap < reference) == w['winner'],
                               initial_metadata_received_ms=market['captured_ms']))
        events = books[start]
        received = [x['received_ms'] for x in events]
        requested = [x['requested_ms'] for x in events]
        states = {(v, arm): c.state() for v in ('frozen', 'causal_history') for arm in ('entry_only', 'completion_only', 'managed')}
        for age in range(180, 841, 60):
            now = (start+age)*1000
            row = dict(S=start, age=age, winner=w['winner'], contexts={}, books={}, actions=[])
            i = bisect.bisect_right(received, now)-1
            valid = {}
            for side in (0, 1):
                try:
                    if i < 0:
                        raise ValueError('no_book')
                    valid[side] = book_for(events[i], market, side, now)
                    cash, fee = c.r.base.ask_cost(valid[side], market, 5)
                    row['books'][str(side)] = dict(valid=True, price=cash/5, allin=(cash+fee)/5,
                                                   received_ms=valid[side]['received_ms'], observed_ms=valid[side]['observed_ms'])
                except ValueError as exc:
                    row['books'][str(side)] = dict(valid=False, reason=str(exc))
            counts['scheduled'] += 1
            counts['both_books_valid'] += len(valid) == 2
            counts['one_book_valid'] += len(valid) == 1
            j = bisect.bisect_left(requested, now+250)
            row['execution_delay_ms'] = events[j]['received_ms']-now if j < len(events) else None
            counts['execution_book_within_3s'] += j < len(events) and events[j]['received_ms'] <= now+3000
            for variant in ('frozen', 'causal_history'):
                try:
                    f = context(indices, start, start+age, variant == 'causal_history')
                    row['contexts'][variant] = f
                    counts[variant+'_context_valid'] += 1
                    counts[variant+'_entry_context_valid'] += age == 180
                except ValueError as exc:
                    row['contexts'][variant] = dict(missing=str(exc))
                    counts[variant+':'+str(exc)] += 1
                    continue
                if len(valid) != 2:
                    continue
                counts[variant+'_joint_valid'] += 1
                for arm in ('entry_only', 'completion_only', 'managed'):
                    state = states[variant, arm]
                    prices = [row['books'][str(side)]['price'] for side in (0, 1)]
                    intent = c.decide(state, age, prices, f, arm)
                    if not intent:
                        continue
                    action = dict(variant=variant, arm=arm, intent=intent, pre_q=state['q'].copy(), pre_cash=state['cash'])
                    try:
                        if j >= len(events):
                            raise ValueError('no_execution_book')
                        execution = book_for(events[j], market, intent['side'], events[j]['received_ms'])
                        cost, fee = c.r.base.ask_cost(execution, market, intent['qty'])
                        action.update(execution_price=cost/intent['qty'], execution_fee=fee,
                                      execution_unit_cost=(cost+fee)/intent['qty'])
                        ok = c.apply_book(state, intent, execution, market, now, f, arm)
                        action.update(accepted=ok, post_q=state['q'].copy(), post_cash=state['cash'],
                                      requested_ms=execution['requested_ms'], received_ms=execution['received_ms'])
                    except ValueError as exc:
                        action.update(accepted=False, missing=str(exc))
                    row['actions'].append(action)
            rows.append(row)
        for (variant, arm), state in states.items():
            replays.append(dict(S=start, slug=w['slug'], variant=variant, arm=arm,
                                pnl=state['q'][w['winner']]-state['cash'], **state))
    summary = {}
    for variant in ('frozen', 'causal_history'):
        for arm in ('entry_only', 'completion_only', 'managed'):
            rr = [x for x in replays if (x['variant'], x['arm']) == (variant, arm)]
            summary[variant+':'+arm] = dict(markets=len(rr), entries=sum(x['entered'] for x in rr),
                adds=sum(x['added'] for x in rr), events=dict(Counter(e['kind'] for x in rr for e in x['events'])),
                scenario_pnl=sum(x['pnl'] for x in rr), cash=sum(x['cash'] for x in rr))
    delays = [x['execution_delay_ms'] for x in rows if x['execution_delay_ms'] is not None]
    save('s_decisions.json', rows)
    save('s_candidate_replay.json', replays)
    save('s_reference_checks.json', references)
    return dict(counts=dict(counts), replay=summary, execution_delay_ms=dict(min=min(delays), median=statistics.median(delays), max=max(delays)),
                references=references,
                note='Finite local-source receive-clock replay, not actual orders. PID63900 local original recorder '
                     'and identical 14..17 UTC source/mirror hashes verified separately. Repository mirror is a later copy; '
                     'original tape existed locally. Exact receive-to-flush/consumer latency was not recorded. '
                     'All 14 slots kept. Missing is not a zero signal. No portfolio/day cutoff, no live scheduler.')


def book_constraints(tape):
    counts, ticks, minimums = Counter(), Counter(), Counter()
    markets = {p.stem: read(p) for p in (S/'raw/initial_markets').glob('*.json')}
    for event in tape:
        if event['kind'] != 'books':
            continue
        for b in event['books']:
            ticks[b['tick_size']] += 1
            minimums[b['min_order_size']] += 1
            m = markets[f'btc-updown-15m-{event["S"]}']
            counts['gamma_tick_differs_from_current_book'] += Decimal(str(m['orderPriceMinTickSize'])) != Decimal(b['tick_size'])
    # Descriptive actual-size quote is not an admissible independent order.
    rows = read(S/'results/new_period_rows.json')
    counts['actor_rows'] = len(rows)
    counts['actor_rows_lt5'] = sum(x['qty'] < 5 for x in rows)
    counts['late_actor_rows_lt5'] = sum(x['qty'] < 5 and x['opening_kind'] == 'add' and 600 <= x['age'] < 900 for x in rows)
    full = {x['slug'] for x in read(S/'results/windows.json') if x['full'] and x['winner'] is not None}
    counts['full_closed_actor_rows_lt5'] = sum(x['qty'] < 5 and x['slug'] in full for x in rows)
    counts['full_closed_late_actor_rows_lt5'] = sum(x['qty'] < 5 and x['slug'] in full and x['opening_kind'] == 'add' and 600 <= x['age'] < 900 for x in rows)
    return dict(counts=dict(counts), tick_sizes=dict(ticks), min_order_sizes=dict(minimums))


def run():
    protected = {str(p): sha(p) for p in (R/'candidate.py', R/'protocol.json', R/'btc15_context.py')}
    indices, sources = load_historical()
    historical = historical_audit(indices)
    del indices
    with gzip.open(S/'raw/book_validation_prefix.json.gz', 'rt') as stream:
        tape = json.load(stream)['rows']
    cutoff = max(x['received_ms'] for x in tape)
    indices, s_sources = load_s_prices(cutoff)
    result = dict(historical=historical, historical_sources=sources, s=s_audit(indices, tape),
                  constraints=book_constraints(tape), s_price_sources=s_sources,
                  protected_sha256=protected, s_book_sha256=sha(S/'raw/book_validation_prefix.json.gz'),
                  s_price_prefix_sha256=sha(HERE/'s_prices.json.gz'))
    assert all(sha(Path(p)) == h for p, h in protected.items())
    save('results.json', result)
    print(json.dumps({k: result[k] for k in ('historical', 's', 'constraints')}, indent=2))


if __name__ == '__main__':
    run()
