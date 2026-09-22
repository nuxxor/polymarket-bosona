#!/usr/bin/env python3
"""One offline regression check for multiplicity, Decimal costs and phase labels."""
import ast
import difflib
import hashlib
from decimal import Decimal as D
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import audit as a  # noqa: E402


def trade(ts, qty, price, side=0, tx='a', cash=None):
    return dict(timestamp=ts, size=qty, price=price, usdcSize=cash or str(D(qty)*D(price)),
                outcomeIndex=side, side='BUY', transactionHash=tx, asset=str(side),
                type='TRADE', slug='btc-updown-15m-0')


def main():
    x = trade(a.ref.START+1, '10', '.4')
    part = dict(complete=True, rows=[x, x])
    assert len(a.merge([part, part, dict(complete=True, rows=[x])])) == 2
    trades = [trade(650, '5', '.4', tx='a'), trade(650, '5', '.4', tx='b'),
              trade(660, '3', '.3', 1, tx='c'), trade(670, '4', '.2', 1, tx='d')]
    old, total = a.ledger(trades, 0, 0)
    fixed, fixed_total = a.ledger(trades, 0, 0, first_seconds=0)
    assert [x['opening_kind'] for x in old[:2]] == ['first', 'add']
    assert [x['opening_kind'] for x in fixed[:2]] == ['first', 'first']
    assert total == fixed_total and total['pnl'] == D('4.3')
    assert fixed[-1]['completion_qty'] == 4 and fixed[-1]['pre_net'] == 7
    cashrows, cash = a.ledger([trade(1, '10', '.4', cash='4.1')], 0, 0)
    assert cash['pnl'] == D('5.9') and cashrows[0]['cash_price'] == D('.41')
    sell = dict(trades[0], side='SELL')
    try:
        a.ledger([sell], 0, 0)
    except ValueError:
        pass
    else:
        raise AssertionError('SELL silently accepted')
    # Same-second opposite-side order changes attribution, never total cash profit.
    tied = [trade(1, '5', '.4'), trade(2, '10', '.8', tx='b'),
            trade(2, '10', '.3', 1, tx='c')]
    up, ut = a.ledger(tied, 0, 0, 'up_first')
    down, dt = a.ledger(tied, 0, 0, 'down_first')
    assert ut['pnl'] == dt['pnl'] and up[1]['opening_kind'] != down[1]['opening_kind']
    # Pairs redeemed/merged turn token value into cash; adding payout again is wrong.
    q, cost, merged = [D(12), D(8)], D('8.5'), D(5)
    before = [v-cost for v in q]
    after = [v-merged-(cost-merged) for v in q]
    assert before == after
    assert abs(q[0]-q[1])/sum(q) != abs(q[0]-q[1])/(sum(q)-2*merged)
    report = a.read(a.HERE/'result.json')
    assert (report['windows'], report['fills'], report['pnl']) == (3503, 14014, '13393.820008')
    assert report['merge_reproduction']['added'] == report['merge_reproduction']['removed'] == 0
    assert report['status']['pnl'] == '165.630507'
    assert report['status']['late']['pnl'] == '-254.167917'
    assert report['first_second_mislabels']['late']['fills'] == 23
    for path, digest in a.read(a.HERE/'inputs.json').items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
    for item in a.read(a.R/'source_manifest.json').values():
        assert hashlib.sha256(Path(item['copy']).read_bytes()).hexdigest() == item['sha256']
    for name, digest in a.read(a.R/'results/reproduction.json')['after'].items():
        assert hashlib.sha256((a.R/'results'/name).read_bytes()).hexdigest() == digest
    for name, digest in a.read(a.R/'btc15_followup/results/reproduction.json')['sha256'].items():
        assert hashlib.sha256((a.R/'btc15_followup'/name).read_bytes()).hexdigest() == digest
    for name, digest in a.read(a.S/'manifest.json').items():
        assert hashlib.sha256((a.S/name).read_bytes()).hexdigest() == digest
    source = (a.R/'src/bosona_gec_arastirma.py').read_text()
    fixed_source = source.replace('    ever_opened = False\n', '').replace('            ever_opened = True\n', '').replace(
        "label = 'first' if not ever_opened else", "label = 'first' if r['timestamp'] == trades[0]['timestamp'] else")
    assert source != fixed_source
    (a.HERE/'first_batch.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True), fixed_source.splitlines(True),
        fromfile='a/src/bosona_gec_arastirma.py', tofile='b/src/bosona_gec_arastirma.py')))
    # Compile the patch in memory, replacing no shared source and issuing no network IO.
    ns = dict(__name__='fixed_ledger', __file__=str(a.R/'src/bosona_gec_arastirma.py'))
    exec(compile(fixed_source, ns['__file__'], 'exec'), ns)
    frows, ftot = ns['ledger'](trades, 0)
    assert [x['opening_kind'] for x in frows[:2]] == ['first', 'first']
    assert abs(ftot['cash_cost_pnl']-float(total['pnl'])) < 1e-9
    for path in a.HERE.glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    print('PASS: multiplicity, Decimal cash/FIFO, same-second patch, ordering, MERGE, SELL guard, real totals, source hashes, syntax')


if __name__ == '__main__':
    main()
