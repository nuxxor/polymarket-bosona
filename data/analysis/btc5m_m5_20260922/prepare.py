"""Freeze every M4v2 accepted order and its recorded SDK lifetime bounds."""
from collections import Counter
from contextlib import closing
from hashlib import sha256
from pathlib import Path
import gzip
import json
import sqlite3

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'btc5m_m4_v2_20260922/final_0112'
DB = Path('/home/taygun/Masaüstü/polymarket/data/db/polymarket_orderbook.db')


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def lifetimes(trace, state, logs):
    assert [r['seq'] for r in trace] == list(range(1, len(trace) + 1))
    requests = {r['attempt']: r for r in trace if r['event'] == 'request'}
    replies = [r for r in trace if r['event'] == 'response']
    assert Counter(requests.keys()) == Counter(r['attempt'] for r in replies)
    assert not any(r['errors'] for r in trace)
    windows = {r['oid']: (int(k.split('|')[1]), w, r)
               for k, w in state['pen'].items() for r in w['emir'] if r.get('oid')}
    result = []
    for reply in replies:
        if reply['op'] != 'post_batch':
            continue
        req = requests[reply['attempt']]
        assert len(reply['reply']['items']) == len(req['meta']['orders']) == 1
        oid = reply['reply']['items'][0].get('oid')
        if not oid:
            continue
        start, window, order = windows[oid]
        tokens, = [r['tokens'] for r in logs if r['k'] == 'pencere' and r.get('S') == start]
        ends = [r for r in replies if r['op'] == 'get_order' and r['reply'].get('oid') == oid
                and r['reply'].get('status') in ('MATCHED', 'CANCELED')]
        assert ends and all(r['reply']['matched'] == order['pay'] for r in ends)
        end = ends[0]
        cancel = [r for r in replies if r['op'] == 'cancel'
                  and any(v['oid'] == oid for v in r['reply']['items'])]
        assert len(cancel) <= 1 and order['durum'] == 'kapali'
        c = cancel[0] if cancel else None
        result.append(dict(oid=oid, S=start, tokens=tokens, oi=order['oi'], price=order['p'],
            size=order['boy'], actual=order['pay'], status=order['borsa_durum'],
            send_ms=reply['begin']['utc_ns']/1e6, ack_ms=reply['end']['utc_ns']/1e6,
            post_duration_ms=reply['duration_ns']/1e6,
            cancel_begin_ms=c['begin']['utc_ns']/1e6 if c else None,
            cancel_end_ms=c['end']['utc_ns']/1e6 if c else None,
            cancel_duration_ms=c['duration_ns']/1e6 if c else None,
            cancel_success=bool(c and c['reply']['items'][0]['canceled']),
            terminal_observed_ms=end['end']['utc_ns']/1e6,
            snapshot_ms=order['snap_ms'], close_reason=order.get('kapanis')))
    assert len(result) == len({r['oid'] for r in result}) == 12
    return result


def main():
    if (OUT / 'input_manifest.json').exists():
        return
    trace = [json.loads(s) for s in (SOURCE / 'LOG_f_emir_iz.jsonl').read_text().splitlines()]
    logs = [json.loads(s) for s in (SOURCE / 'LOG_f.jsonl').read_text().splitlines()]
    orders = lifetimes(trace, read(SOURCE / 'STATE_f.json'), logs)
    write('orders.json', orders)
    write('protocol.json', dict(selection='All 12 accepted M4v2 orders, including all 8 nonfills',
        role='Execution calibration diagnostic; no strategy PnL or threshold tuning',
        clock_guard_ms=100, max_book_age_ms=3000, max_event_delay_ms=1000,
        execution='SDK send/ack bound activation; cancel send/response plus status bounds exit',
        model='Reuse M1 static queue; front/back sensitivity; observed lifetime, not future policy',
        missing='Missing stream/receipt/clock produces null, never a zero fill'))
    events, markets = {}, {}
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as con:
        con.execute('BEGIN')
        maximum = con.execute('select max(id) from market_events').fetchone()[0]
        for start in sorted({o['S'] for o in orders}):
            own = [o for o in orders if o['S'] == start]
            tokens = own[0]['tokens']
            rows = con.execute('select asset_id,condition_id,side from subscribed_assets where start_ts=? and end_ts=?', (start, start+300)).fetchall()
            assert len(rows) == 2 and all(t == tokens[['Up', 'Down'].index(side)] for t, _, side in rows)
            cid, = {r[1] for r in rows}
            markets[str(start)] = dict(conditionId=cid, tokens=tokens)
            lo, hi = int(min(o['send_ms'] for o in own))-100, int(max(o['terminal_observed_ms'] for o in own))+1001
            full = [con.execute("select ts_ms from market_events where asset_id=? and event_type='book' and ts_ms<=? and id<=? order by ts_ms desc,id desc limit 1", (t, lo, maximum)).fetchone() for t in tokens]
            lower = min(r[0] for r in full if r) if any(full) else lo-3000
            rows = con.execute('select id,ts_ms,event_type,raw_json from market_events where condition_id=? and ts_ms between ? and ? and id<=? order by ts_ms,id', (cid, lower, hi, maximum))
            for ident, rcv, kind, raw in rows:
                events[ident] = dict(S=start, id=ident, rcv=rcv, k=kind, p=json.loads(raw))
    write('markets.json', markets)
    with gzip.open(OUT / 'events.jsonl.gz', 'wt') as f:
        for e in sorted(events.values(), key=lambda r: (r['rcv'], r['id'])):
            f.write(json.dumps(e) + '\n')
    txs = sorted({e['p']['transaction_hash'] for e in events.values()
                  if e['k'] == 'last_trade_price' and e['p'].get('transaction_hash')})
    write('transactions.json', txs)
    write('input_manifest.json', dict(db_max_id=maximum, source={str(p.relative_to(OUT.parent)):sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'STATE_f.json', SOURCE/'LOG_f.jsonl', SOURCE/'LOG_f_emir_iz.jsonl']},
        files={n:sha256((OUT/n).read_bytes()).hexdigest() for n in ('orders.json', 'protocol.json', 'markets.json', 'events.jsonl.gz', 'transactions.json')}))
    print(json.dumps(dict(orders=len(orders), markets=len(markets), events=len(events), transactions=len(txs))))


if __name__ == '__main__':
    main()
