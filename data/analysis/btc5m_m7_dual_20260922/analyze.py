"""Causal two-feed coverage replay; LTP overlap is not economic fill identity."""
from collections import Counter
from decimal import Decimal
from hashlib import sha256
import gzip
import heapq
import json
from pathlib import Path
import sys


def rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    previous = 0
    with opener(path, 'rt') as file:
        for line in file:
            row = json.loads(line)
            if row.get('channel') == 'market':
                now = row['received']['mono_ns']
                assert now >= previous
                previous = now
                yield row


def feed():
    return dict(books={}, connected=False, connection=None, issues=Counter(),
                last_data=None, gaps=[], trades=[], fingerprints=Counter())


def labeled(path, index):
    for row in rows(path):
        yield row['received']['mono_ns'], index, row


def apply(state, row):
    event, now = row['event'], row['received']['mono_ns']
    if event == 'gap':
        state['gaps'].append(dict(detected=now, uncertain_from=state['last_data'] or now,
                                 recovered=None, code=row.get('close_code')))
    if event in ('gap', 'connection_end', 'rejected'):
        state['books'].clear()
        state['connected'] = False
    if event == 'subscription_sent':
        state.update(books={}, connected=True, connection=row['connection'])
    if event != 'data':
        return
    assert state['connection'] == row['connection']
    state['last_data'] = now
    payload = row['payload']
    kind = payload['event_type']
    if kind == 'last_trade_price':
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        state['fingerprints'][fingerprint] += 1
        state['trades'].append((now, fingerprint))
    if kind not in ('book', 'price_change'):
        return
    source = int(payload['timestamp'])*1_000_000
    changes = [payload] if kind == 'book' else payload['price_changes']
    for change in changes:
        token = change['asset_id']
        book = state['books'].setdefault(token, dict(ready=False, source=0))
        if source < book['source']:
            state['issues']['out_of_order_book'] += 1
            book['ready'] = False
            continue
        if kind == 'book':
            for side, key in [('BUY', 'bids'), ('SELL', 'asks')]:
                book[side] = {Decimal(x['price']):Decimal(x['size']) for x in payload[key]
                              if Decimal(x['size']) > 0}
            book['ready'] = True
        elif book['ready']:
            price, size = Decimal(change['price']), Decimal(change['size'])
            assert 0 < price < 1 and size >= 0
            if size:
                book[change['side']][price] = size
            else:
                book[change['side']].pop(price, None)
        book.update(source=source, received=now)


def fresh(state, tokens, utc, mono, max_age):
    if not state['connected']:
        return False
    for token in tokens:
        book = state['books'].get(token, {})
        if not book.get('ready') or not -100_000_000 <= utc-book['source'] <= max_age:
            return False
        if not 0 <= mono-book['received'] <= max_age:
            return False
    return True


def main(root):
    protocol = json.loads((root.parent/'protocol.json').read_text())
    summaries = [json.loads((root/f'{lane}_done.json').read_text()) for lane in ('A', 'B')]
    assert summaries[0]['pid'] != summaries[1]['pid']
    assert summaries[0]['boot_id'] == summaries[1]['boot_id']
    assert summaries[0]['markets'] == summaries[1]['markets']
    assert summaries[0]['source_sha256'] == summaries[1]['source_sha256']
    assert all(s['open_orders_at_auth_check'] == 0 for s in summaries)
    paths = [next((root/lane).glob('*.jsonl*')) for lane in ('A', 'B')]
    # Existing capture integrity/secret/sequence/snapshot checker is reused unchanged.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'btc5m_m7_20260922'))
    from check_capture import check
    integrity = [check(p, root/f'{lane}_done.json') for p, lane in zip(paths, ('A', 'B'))]
    states = [feed(), feed()]
    merged = heapq.merge(*(labeled(p, i) for i, p in enumerate(paths)), key=lambda x:(x[0], x[1]))
    current = next(merged, None)
    begin = max(s['started']['mono_ns'] for s in summaries)
    end = min(s['ended']['mono_ns'] for s in summaries)
    offset = summaries[0]['started']['utc_ns']-summaries[0]['started']['mono_ns']
    markets = {m['S']:m for m in summaries[0]['markets']}
    counts, active = Counter(), Counter()
    samples = []
    step, max_age = protocol['grid_ms']*1_000_000, protocol['freshness_ms']*1_000_000
    for now in range(begin, end, step):
        while current is not None and current[0] <= now:
            apply(states[current[1]], current[2])
            current = next(merged, None)
        utc = now+offset
        start = utc//300_000_000_000*300
        assert start in markets
        tokens = markets[start]['tokens']
        valid = [fresh(s, tokens, utc, now, max_age) for s in states]
        active[start] += 1
        counts['both_fresh' if all(valid) else 'A_only' if valid[0] else 'B_only' if valid[1] else 'neither_fresh'] += 1
        for i, state in enumerate(states):
            for gap in state['gaps']:
                if gap['recovered'] is None and valid[i]:
                    gap['recovered'] = now
        samples.append((now, valid))
    # Retain trailing records for the whole-log multiset comparison.
    while current is not None:
        apply(states[current[1]], current[2])
        current = next(merged, None)
    gaps = []
    for i, state in enumerate(states):
        for gap in state['gaps']:
            stop = gap['recovered'] or end
            checkpoints = [(t, v) for t, v in samples if gap['detected'] <= t < stop]
            uncertain = [(t, v) for t, v in samples if gap['uncertain_from'] <= t < stop]
            peer = states[1-i]
            observed = Counter(fp for t, fp in peer['trades'] if gap['detected'] <= t < stop)
            # Maximal fingerprint matching is descriptive, never a merged fill ledger.
            absent = sum((observed-state['fingerprints']).values())
            gaps.append(dict(lane='AB'[i], **gap, sampled=len(checkpoints),
                peer_stale=sum(not v[1-i] for _, v in checkpoints),
                conservative_samples=len(uncertain),
                conservative_peer_stale=sum(not v[1-i] for _, v in uncertain),
                peer_ltp=sum(observed.values()), peer_ltp_absent_from_affected_log=absent))
    common = sum((states[0]['fingerprints'] & states[1]['fingerprints']).values())
    assert all(sum(s['fingerprints'].values()) == proof['counts']['market']['last_trade_price']
               for s, proof in zip(states, integrity))
    clean = all(not s['writer_failed'] and not s['reader_alive'] and
                not any(s['stats'][ch].get(k, 0) for ch in ('market', 'user')
                        for k in ('rejected', 'queue_overflow')) for s in summaries)
    result = dict(integrity=integrity, overlap_seconds=(end-begin)/1e9,
        checkpoints=dict(counts), grid_ms=protocol['grid_ms'], active_windows=dict(active),
        issues={lane:dict(s['issues']) for lane, s in zip(('A', 'B'), states)}, gaps=gaps,
        ltp_multiset=dict(A=sum(states[0]['fingerprints'].values()), B=sum(states[1]['fingerprints'].values()),
                          common_occurrences=common,
                          A_unmatched=sum(states[0]['fingerprints'].values())-common,
                          B_unmatched=sum(states[1]['fingerprints'].values())-common),
        coverage_gate=bool(gaps) and clean and len(active) >= 3 and
                      all(g['sampled'] and g['recovered'] and not g['peer_stale'] for g in gaps),
        full_calibration=False, live_failover_deployed=False, economic_fills_merged=False)
    return result


def self_check():
    state = feed()
    def event(kind, when, **fields):
        return dict(event=kind, connection=1, received=dict(mono_ns=when, utc_ns=when), **fields)
    apply(state, event('subscription_sent', 1))
    for token in ('up', 'down'):
        apply(state, event('data', 1_000_000_000, payload=dict(event_type='book', timestamp='1000',
              asset_id=token, bids=[dict(price='.4', size='5')], asks=[dict(price='.6', size='7')])) )
    assert fresh(state, ('up', 'down'), 1_000_000_000, 1_000_000_000, 3_000_000_000)
    assert not fresh(state, ('up', 'next'), 1_000_000_000, 1_000_000_000, 3_000_000_000)
    assert not fresh(state, ('up', 'down'), 5_000_000_000, 5_000_000_000, 3_000_000_000)
    assert not fresh(state, ('up', 'down'), 500_000_000, 500_000_000, 3_000_000_000)
    apply(state, event('data', 1_001_000_000, payload=dict(event_type='price_change', timestamp='1001',
        price_changes=[dict(asset_id='up', side='BUY', price='.4', size='0')])))
    assert state['books']['up']['BUY'] == {} and state['books']['up']['SELL'][Decimal('.6')] == 7
    trade = event('data', 1_002_000_000, payload=dict(event_type='last_trade_price', timestamp='1002'))
    apply(state, trade)
    apply(state, trade)
    assert sum(state['fingerprints'].values()) == 2
    apply(state, event('gap', 1_003_000_000, close_code=1013))
    assert not fresh(state, ('up', 'down'), 1_003_000_000, 1_003_000_000, 3_000_000_000)
    assert state['gaps'][0]['uncertain_from'] == 1_002_000_000
    apply(state, event('subscription_sent', 1_004_000_000))
    assert not state['books']
    print('causal freshness, rollover, delta, duplicate and disconnect checks passed')


if __name__ == '__main__':
    if sys.argv[1] == '--self-check':
        self_check()
    else:
        print(json.dumps(main(Path(sys.argv[1])), indent=2))
