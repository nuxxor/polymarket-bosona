"""Small negative regressions against actual frozen BTC15 receipts; no network."""
from copy import deepcopy
from decimal import Decimal as D
import hashlib
import json
import subprocess
import sys

import probe as p
from next_selection import select


def rejects(fn):
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError('invalid evidence accepted')


def main():
    result = p.read(p.OUT/'results.json')
    api = p.read(p.OUT/'activity.json')
    tx = api[0]['transactionHash']
    receipt = p.read(p.OUT/'raw'/f'receipt_0_{tx}.json')['response']['result']
    decoded = p.dec.decode(deepcopy(receipt), p.ACTOR)
    group = [r for r in api if r['transactionHash'] == tx]
    market = p.read(p.OUT/f"{group[0]['slug']}.json")['data']
    p.reconcile(group, decoded, market)
    changed = deepcopy(receipt)
    changed['logs'].append(deepcopy(changed['logs'][0]))
    rejects(lambda: p.dec.decode(changed, p.ACTOR))
    changed = deepcopy(receipt)
    changed['to'] = '0x'+'0'*40
    rejects(lambda: p.dec.decode(changed, p.ACTOR))
    changed = deepcopy(receipt)
    changed['logs'] = [r for r in changed['logs'] if r['topics'][0] != p.dec.MATCHED]
    rejects(lambda: p.dec.decode(changed, p.ACTOR))
    changed = deepcopy(receipt)
    cash = next(r for r in changed['logs'] if r['address'].lower() == p.dec.CASH
                and r['topics'][0] == p.dec.TRANSFER
                and p.ACTOR in [p.dec.address(t) for t in r['topics'][1:3]])
    cash['data'] = '0x'+f"{int(cash['data'],16)+1:064x}"
    rejects(lambda: p.dec.decode(changed, p.ACTOR))
    changed_api = deepcopy(group)
    changed_api[0]['asset'] = '0'
    rejects(lambda: p.reconcile(changed_api, decoded, market))
    rejects(lambda: p.reconcile(group+deepcopy(group), decoded, market))
    taker = next(r for r in result['rows'] if r['role'] == 'taker')
    taker_receipt = p.read(p.OUT/'raw'/f"receipt_0_{taker['tx']}.json")['response']['result']
    real_taker, = p.dec.decode(taker_receipt, p.ACTOR)
    assert real_taker['owner'] == p.ACTOR and real_taker['role'] == 'taker'
    assert any(log['topics'][0] == p.dec.MATCHED and log['topics'][1] == real_taker['order_hash']
               for log in taker_receipt['logs'])
    taker_api = [r for r in api if r['transactionHash'] == taker['tx']]
    taker_market = p.read(p.OUT/f"{taker['slug']}.json")['data']
    # API cash already contains the actual chain fee; charging it again must fail.
    wrong = deepcopy(taker_api)
    wrong[0]['usdcSize'] += taker['fee']/1e6
    rejects(lambda: p.reconcile(wrong, [taker], taker_market))
    same_size = [r for r in result['rows'] if r['qty'] == 300000000
                 and r['slug'].endswith('1790001900')]
    assert len(same_size) == 2 and len({r['order_hash'] for r in same_size}) == 2
    synthetic = deepcopy(same_size)
    synthetic[1].update(tx=synthetic[0]['tx'], api_ts=synthetic[0]['api_ts'])
    p.inventory_phases(synthetic)
    assert all(r['parent_origin'] == 'first_observed_parent_fill' for r in synthetic)
    synthetic[1]['order_hash'] = synthetic[0]['order_hash']
    p.inventory_phases(synthetic)
    assert synthetic[1]['parent_origin'] == 'same_second_parent_fragment'
    synthetic[0]['side'] = 1
    rejects(lambda: p.inventory_phases(synthetic))
    crossing = [r for r in result['rows'] if r['order_hash'] ==
                '0x9caa67c235f26fa5336052bac6d2c97fa44dd0c1637502a2faa9e82bb7469c9f']
    assert len(crossing) == 7 and {r['phase'] for r in crossing} == {'reopen', 'add'}
    assert sum(D(r['completion_qty']) for r in crossing) == D('1.727061')
    assert sum(D(r['opening_qty']) for r in crossing) == D('279.344369')
    assert crossing[0]['pre_qty'] == ['1.727061', '0']
    merge_api = p.read(p.OUT/'merge_selection.json')['row']
    merge_receipt = p.read(p.OUT/'raw'/f"merge_{merge_api['transactionHash']}.json")['response']['result']
    merge_tokens = json.loads(p.read(p.OUT/f"{merge_api['slug']}.json")['data']['clobTokenIds'])
    bad_merge = dict(merge_api, usdcSize=merge_api['usdcSize']+.000001)
    rejects(lambda: p.verify_merge(merge_receipt, bad_merge, merge_tokens))
    rejects(lambda: p.verify_merge(merge_receipt, merge_api, ['0',merge_tokens[1]]))
    universe = [dict(group='btc_15m', S=t, end=t+900, mechanism='chainlink_twap60',
                    slug=f'btc-updown-15m-{t}', winner=1, pnl=123, traded=False)
                for t in range(0, 86400, 900)]
    slices = [dict(start=0, end=86399, complete=True,
                   rows=[dict(type='TRADE', slug=u['slug'], proxyWallet=p.ACTOR) for u in universe[:8]])]
    sample = select(universe, slices, 0, 86400)
    assert sample['status'] == 'UNDERPOWERED' and sample['selected_markets'] == 4
    changed_u = [dict(u, winner=0, pnl=-999, traded=True) for u in reversed(universe)]
    assert select(changed_u, list(reversed(slices)), 0, 86400) == sample
    rejects(lambda: select(universe[:-1], slices, 0, 86400))
    rejects(lambda: select(universe, [dict(slices[0], complete=None)], 0, 86400))
    assert result['status'] == 'VERIFIED_SELECTED_EXPLORATORY'
    assert result['cross_provider_receipts'] and not result['failures']
    assert all(D(w['pnl']) == D(w['expected_pnl']) for w in result['windows'])
    before = hashlib.sha256((p.OUT/'results.json').read_bytes()).hexdigest()
    subprocess.run([sys.executable,str(p.OUT/'probe.py')],check=True,stdout=subprocess.DEVNULL)
    after = hashlib.sha256((p.OUT/'results.json').read_bytes()).hexdigest()
    assert before == after, 'offline reproduction differs'
    checks = dict(negative_checks=12, parent_identity_checks=3, role_and_phase_checks=True,
                  merge_receipt_and_actual_balances=True,
                  selector_outcome_and_order_invariant=True,
                  all_passed=True, offline_result_sha256=after,
                  exact_selected_market_pnl=True, python=sys.version)
    (p.OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks,indent=2))


if __name__ == '__main__':
    main()
