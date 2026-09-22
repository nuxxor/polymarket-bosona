"""Root-cause regression checks, no network or writes to source directories."""
from decimal import Decimal as D
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

from common import HERE, R, accounting, protected, read, save, timing
import replay as p
from record_ws import selected

TOKENS = ['up', 'down']
START = 1000000
MARKET = dict(feesEnabled=True, feeSchedule=dict(rate=.07, exponent=1))


def snap(age, bid=.4, size=0):
    now = (START+age)*1000
    return dict(received_ms=now, requested_ms=now-100, gap=False,
                books={'up': ([(bid, size)], [(bid+.02, 100)], now-50),
                       'down': ([(.58, size)], [(.60, 100)], now-50)})


def prints(*values):
    return [dict(ts=START+age, token=token, price=price, size=qty) for age,token,price,qty in values]


def run(snaps, trades, mode='queue_back', hedge=False):
    return p.run(snaps, TOKENS, trades, START, mode, '0', hedge, MARKET)


def check():
    protected()
    checks = []
    def passed(name):
        checks.append(name)

    tape = [snap(a) for a in range(30, 901)]
    result = run(tape, prints((31, 'up', .39, 1)))
    assert result['q'][0] == 1 and len(result['fills']) == 1
    passed('one share through price fills at most one share')
    result = run(tape, prints((31, 'up', .4, 2), (32, 'up', .4, 3)))
    assert result['q'][0] == 5 and [x['qty'] for x in result['fills']] == [2, 3]
    passed('partial fills accumulate without inventing volume')
    result = run([snap(a, size=20) for a in range(30, 901)],
                 prints((31, 'up', .4, 12), (32, 'up', .4, 10)))
    assert result['q'][0] == 2
    passed('queue ahead consumes volume before our partial fill')
    result = run([snap(30), snap(35)], prints((32, 'up', .4, 5)))
    assert result['q'][0] == 0 and result['uncertain']
    passed('implicit recording gap remains unknown before fill evaluation')
    result = run(tape, prints(*[(40+i, 'up', .4, 5) for i in range(40)]), hedge=True)
    assert result['cash'] <= 15 and result['max_reserved'] <= 15
    assert any(x['kind'] == 'taker' for x in result['fills'])
    assert all(x['qty'] <= 5 for x in result['fills'])
    passed('repeated hedges reserve cash and keep five share clips')
    s = p.state()
    s.update(q=[D(10), D(10)], cash=D('12.8'))
    up = dict(side=0, left=D(5), limit=D('.4'), active_ms=0, cancel_ms=2000, ahead=D(0))
    dn = dict(up, side=1)
    assert p.reserve(s, up)
    s['quotes'][0] = up
    assert not p.reserve(s, dn)
    passed('two individually affordable orders cannot oversubscribe shared cash')
    p.expire(s, 1999)
    assert not p.reserve(s, dn)
    p.expire(s, 2000)
    assert p.reserve(s, dn)
    passed('cancel request does not release reservation before acknowledgement')
    s = p.state()
    o = dict(side=0, left=D(5), limit=D('.4'), active_ms=1000, cancel_ms=1250, ahead=D(0))
    assert p.reserve(s, o)
    s['quotes'][0] = o
    event = dict(side=0, price=.4, size=1)
    p.consume(s, event, 999, 'queue_front')
    assert not s['fills']
    p.consume(s, event, 1100, 'queue_front')
    assert s['q'][0] == 1
    p.consume(s, event, 1250, 'queue_front')
    assert s['q'][0] == 1
    passed('activation and cancellation clock boundaries')
    result = run([snap(a, bid=.405) for a in range(30, 901)], prints((31, 'up', .405, 1)))
    assert result['fills'][0]['price'] == D('.405')
    passed('touch quote preserves observed subcent price')
    records = {'spot': [(2000, 1000, 10.), (6000, 1000, 999.)]}
    idx = timing.index(records)
    assert timing.at(idx, 'spot', 1000, 5000, corrected=True) == 10.
    try:
        timing.at(idx, 'spot', 1000, 1000, corrected=True)
    except ValueError:
        pass
    else:
        raise AssertionError('future received sample accepted')
    passed('historical event time uses decision receipt deadline')
    x = dict(timestamp=accounting.ref.START, conditionId='a', transactionHash='t', type='MERGE', size=5, usdcSize=5)
    y = dict(x, conditionId='b')
    merged = accounting.merge([dict(complete=True, rows=[x, x, y]), dict(complete=True, rows=[x, y])], condition=True)
    assert len(merged) == 3
    passed('condition identity and genuine equal fill multiplicity')
    result = read(HERE/'results/replay.json')
    for row in result['markets']:
        assert row['economic_pnl'] is None
        for v in row['arms'].values():
            assert D(v['cash']) <= 15 and D(v['max_reserved']) <= 15
            assert D(v['end_worst']) >= -5
            assert abs(D(v['q'][0])-D(v['q'][1])) <= 10
    passed('real tape all paths respect final cash/net/risk and economic gate')
    fills = read(HERE/'results/fills.json')
    old = read(R/'results/fills.json')
    assert len(fills) == len(old) == 14014
    assert sum(D(x['pnl']) for x in fills) == D('13393.820008')
    btc = [x for x in fills if x['group'] == 'btc_15m']
    late = [x for x in btc if x['opening_kind'] == 'add' and 600 <= x['age'] < 900]
    assert len(late) == 1150 and sum(D(x['pnl']) for x in late) == D('3364.652672')
    assert sum(x['role'] == 'maker' for x in late) == 1077
    passed('raw rebuilt cash and corrected late maker phases reconcile')
    markets = {'c': dict(clobTokenIds=json.dumps(TOKENS))}
    assert selected(dict(market='c', event_type='book', asset_id='up'), markets)
    assert not selected(dict(market='foreign', event_type='book', asset_id='up'), markets)
    try:
        selected(dict(market='c', event_type='book', asset_id='foreign'), markets)
    except ValueError:
        pass
    else:
        raise AssertionError('foreign token accepted')
    passed('public recorder retains only verified condition and tokens')
    probe = read(HERE/'results/ws_probe.json')
    folder = Path(probe['path'])
    for name, digest in probe['files'].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == digest
    market = read(folder/'market.json')
    markets = {market['conditionId']: market}
    books, counts, lag, trades, previous = set(), Counter(), [], [], 0
    with gzip.open(folder/'events.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            assert row['monotonic_ns'] >= previous
            previous = row['monotonic_ns']
            for e in row['data'] if isinstance(row['data'], list) else [row['data']]:
                if not selected(e, markets):
                    continue
                counts[e['event_type']] += 1
                lag.append(row['received_ms']-int(e['timestamp']))
                if e['event_type'] == 'book':
                    books.add(e['asset_id'])
                if e['event_type'] == 'price_change':
                    assert all(x['asset_id'] in books for x in e['price_changes'])
                if e['event_type'] == 'last_trade_price':
                    assert e['asset_id'] in books and e['transaction_hash']
                    assert D(e['size']) > 0 and e['side'] in ('BUY', 'SELL')
                    trades.append(e)
    assert len(books) == 2 and trades and not probe['errors']
    save('results/ws_quality.json', dict(counts=counts, initial_books=2,
         receive_minus_server_ms=dict(min=min(lag), median=median(lag), max=max(lag)),
         distinct_trade_hashes=len({x['transaction_hash'] for x in trades}),
         note='Partial-market schema check only. Server timestamp is not yet receipt-validated match time; '
              'L2 does not reveal order ownership or exact queue position.'))
    passed('real websocket probe has initial books, deltas, trade clocks and hashes')
    old_run = read(R/'btc15_followup/raw/books_72h/run.json')
    assert hashlib.sha256((R/'btc15_followup/record_books.py').read_bytes()).hexdigest() == old_run['code_sha256']
    passed('existing REST recorder source still matches its startup hash')
    protected()
    save('results/checks.json', dict(passed=True, checks=checks))
    print(f'{len(checks)} checks passed')


if __name__ == '__main__':
    check()
