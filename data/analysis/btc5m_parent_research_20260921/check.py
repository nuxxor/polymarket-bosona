"""Run after analyze.py: money/ordering guards and actual sample invariants."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json

import analyze as a


def fill(side, qty, cash, ts, parent='one'):
    return dict(outcome=side, qty=a.units(qty), cash_cost=a.units(cash), ts=ts,
                order_hash=parent, role='maker')


def main():
    first = fill(0, 5, 2, 10)
    close = fill(1, 5, 2.5, 20)
    expected = a.first_reduction([first, close], 1)
    assert expected['delta'] == 2.5 and expected['min_pair_cost'] == .9
    assert a.first_reduction([first, close], 0)['delta'] == -2.5
    assert a.first_reduction([first, close, fill(0, 100, 50, 30)], 1) == expected
    assert a.first_reduction([first], 1)['status'] == 'no_reduction'
    split = [first, fill(1, 3, 1.5, 20), fill(1, 2, 1, 20)]
    assert a.first_reduction(split, 1)['delta'] == 2.5
    split[-1]['order_hash'] = 'two'
    assert a.first_reduction(split, 1)['status'].startswith('ambiguous')
    assert a.first_reduction([first, fill(1, 3, 1.5, 20), fill(1, 3, 1.8, 20)], 1)['status'].startswith('ambiguous')
    assert a.first_reduction([first, fill(0, 1, .4, 20), close], 1)['status'].startswith('ambiguous')
    assert a.first_reduction([first, dict(close, S=-280)], 1)['status'].endswith('after_public_end')
    lots = [fill(0, 5, 1, 10), fill(0, 5, 4, 11), fill(1, 5, 1.5, 20)]
    r = a.first_reduction(lots, 1)
    assert r['min_pair_cost'] == .5 and r['max_pair_cost'] == 1.1
    assert not r['all_lot_pair_cost_over_one']
    bounds = a.continuation_bounds([dict(parent='p',qty=3),dict(parent='p',qty=7)], {'p':[{},{}]})
    assert bounds['records']==[1,1] and bounds['shares']==[3,7]
    bounds = a.continuation_bounds([dict(parent='p',qty=3)], {'p':[{},{}]})
    assert bounds['records']==[0,1] and bounds['shares']==[0,3]

    raw = a.read('activity.json')
    actor, = {r['proxyWallet'].lower() for r in raw}
    tx = next(r['transactionHash'] for r in raw if r['type']=='TRADE')
    receipt = a.read(f'receipts/{tx}.json')
    a.probe.decode(receipt, actor)
    for mutation in ('duplicate', 'missing_match', 'wrong_exchange', 'cash'):
        bad = deepcopy(receipt)
        if mutation == 'duplicate':
            bad['logs'].append(deepcopy(bad['logs'][0]))
        elif mutation == 'missing_match':
            bad['logs'] = [event for event in bad['logs'] if event['topics'][0] != a.probe.MATCHED]
        elif mutation == 'wrong_exchange':
            bad['to'] = '0x'+'0'*40
        else:
            log = next(event for event in bad['logs'] if event['address'].lower()==a.probe.CASH
                       and event['topics'][0]==a.probe.TRANSFER
                       and actor in (a.probe.address(event['topics'][1]), a.probe.address(event['topics'][2])))
            log['data'] = '0x'+format(int(log['data'],16)+1, '064x')
        try:
            a.probe.decode(bad, actor)
        except AssertionError:
            pass
        else:
            raise AssertionError(f'accepted {mutation}')

    report, manifest = a.read('report.json'), a.read('manifest.json')
    assert len(report['market_results']) == len(manifest['selected']) == 137
    assert len({(f['tx'],f['log_index']) for f in report['fills']}) == len(report['fills'])
    assert sum(r['records'] for r in report['market_results']) == 2066
    assert Counter(r['parent_mapping'] for r in report['late20_records']).total() == 271
    assert all(r['matched_records'] <= r['records'] and r['matched_shares'] <= r['shares']+.00001
               for r in report['market_results'])
    assert all(r.get('first_reduction') is None for r in report['market_results'] if r['status']=='missing')
    result = dict(status='PASS', checks='first-reduction/lot/clock guards, four corrupt receipt rejections, actual cohort invariants',
                  report_sha256=sha256((a.OUT/'report.json').read_bytes()).hexdigest(),
                  check_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (a.OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
