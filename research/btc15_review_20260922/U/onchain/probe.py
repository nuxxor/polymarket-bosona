"""Finite unauthenticated Polygon reads. --fetch then offline reconciliation."""
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.request

import decoder as dec

OUT = Path(__file__).resolve().parent
ACTOR = '0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
RPCS = dec.RPCS
UNIT = D(1000000)
BATCH = '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'
MERGE = '0x6f13ca62553fcc2bcd2372180a43949c1e4cebba603901ede2f4e14f36b282ca'
USDC_E = '0x2791bca1f2de4661ed88a30c99a7a9449aa84174'


def read(path):
    return json.loads(path.read_text())


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')


def request(url, method, params, path):
    if path.exists():
        return read(path)
    payload = dict(jsonrpc='2.0', id=1, method=method, params=params)
    record = dict(url=url, request=payload, requested_ms=round(time.time()*1000))
    try:
        req = urllib.request.Request(url, json.dumps(payload).encode(),
              headers={'Content-Type': 'application/json', 'User-Agent': 'BosonaResearch/1'})
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read()
            record.update(http_status=response.status, response=json.loads(raw),
                          response_sha256=hashlib.sha256(raw).hexdigest(), raw=raw.decode())
    except Exception as exc:
        record['error'] = type(exc).__name__+': '+str(exc)
    record['received_ms'] = round(time.time()*1000)
    save(path, record)
    return record


def fetch():
    raw = OUT/'raw'
    raw.mkdir(exist_ok=True)
    rows = read(OUT/'activity.json')
    txs = list(dict.fromkeys(r['transactionHash'] for r in rows))
    assert len(txs) <= read(OUT/'selection.json')['max_transactions']
    live = []
    for i, url in enumerate(RPCS):
        r = request(url, 'eth_chainId', [], raw/f'chain_{i}.json')
        if r.get('response', {}).get('result') == '0x89':
            live.append((i, url))
    if not live:
        print('No public provider returned Polygon chainId; raw errors preserved.')
        return
    blocks = set()
    for tx in txs:
        i, url = live[0]
        r = request(url, 'eth_getTransactionReceipt', [tx], raw/f'receipt_{i}_{tx}.json')
        result = r.get('response', {}).get('result')
        if result:
            assert result['transactionHash'] == tx and result['status'] == '0x1'
            blocks.add(result['blockNumber'])
    for i, url in live[1:]:
        request(url, 'eth_getTransactionReceipt', [txs[0]], raw/f'receipt_{i}_{txs[0]}.json')
    i, url = live[0]
    if (OUT/'merge_selection.json').exists():
        assert len(txs)+1 <= read(OUT/'selection.json')['max_transactions']
        tx = read(OUT/'merge_selection.json')['row']['transactionHash']
        r = request(url, 'eth_getTransactionReceipt', [tx], raw/f'merge_{tx}.json')
        if r.get('response', {}).get('result'):
            blocks.add(r['response']['result']['blockNumber'])
    for block in sorted(blocks):
        request(url, 'eth_getBlockByNumber', [block, False], raw/f'block_{block}.json')


def reconcile(api, decoded, market):
    tokens = json.loads(market['clobTokenIds'])
    assert all(r['conditionId'] == market['conditionId'] and r['asset'] == tokens[r['outcomeIndex']]
               for r in api), 'API token/condition mismatch'
    assert all(f['token'] in tokens for f in decoded), 'unexpected actor token'
    for token in set(tokens):
        for api_side, chain_side in [('BUY', 0), ('SELL', 1)]:
            a = [r for r in api if r['asset'] == token and r['side'] == api_side]
            b = [r for r in decoded if r['token'] == token and r['side'] == chain_side]
            aq = sum((D(str(r['size'])) for r in a), D(0))
            ac = sum((D(str(r['usdcSize'])) for r in a), D(0))
            bq = sum((D(r['qty'])/UNIT for r in b), D(0))
            bc = sum((D(r['cash_cost'])/UNIT for r in b), D(0))*(1 if api_side == 'BUY' else -1)
            assert abs(aq-bq) <= D('.000001'), 'API quantity mismatch'
            assert abs(ac-bc) <= D('.00001'), 'API cash mismatch'


def verify_merge(receipt, api, tokens):
    assert receipt['status'] == '0x1' and receipt['transactionHash'] == api['transactionHash']
    cash, total, target, burned, seen = 0, 0, [], defaultdict(int), set()
    for log in receipt['logs']:
        assert log['transactionHash'] == receipt['transactionHash'] and not log.get('removed',False)
        assert log['blockHash'] == receipt['blockHash'] and log['logIndex'] not in seen
        seen.add(log['logIndex'])
        topics, contract = log['topics'], log['address'].lower()
        if contract == USDC_E and topics[0] == dec.TRANSFER:
            amount, = dec.words(log['data'], 1)
            cash += amount*((dec.address(topics[2]) == ACTOR)-(dec.address(topics[1]) == ACTOR))
        if contract == dec.CTF and topics[0] == BATCH and dec.address(topics[2]) == ACTOR:
            assert int(topics[3], 16) == 0, 'merge must burn tokens'
            a = dec.words(log['data'], 8)
            assert a[:3] == [64, 160, 2] and a[5] == 2, 'unsupported batch shape'
            for token, qty in zip(a[3:5], a[6:8]):
                burned[str(token)] += qty
        if contract == dec.CTF and topics[0] == MERGE and dec.address(topics[1]) == ACTOR:
            a = dec.words(log['data'], 6)
            assert a[0] == int(USDC_E, 16) and a[1] == 96 and a[3:] == [2, 1, 2]
            total += a[2]
            if topics[3] == api['conditionId']:
                target.append(a[2])
    amount = int(D(str(api['size']))*UNIT)
    assert target == [amount] and D(str(api['usdcSize']))*UNIT == amount
    assert cash == total and all(burned[t] == amount for t in tokens), 'merge cash/token mismatch'
    return dict(slug=api['slug'], api_ts=api['timestamp'], event_type='MERGE', qty=amount,
                block_number=int(receipt['blockNumber'],16), transaction_index=int(receipt['transactionIndex'],16),
                log_index=-1, cash_asset=USDC_E, condition_cash_credit=str(D(amount)/UNIT),
                entire_transaction_cash_credit=str(D(cash)/UNIT), tx=api['transactionHash'])


def inventory_phases(rows, merges=()):
    """Observed BUY-only cases; unsupported sales fail instead of disappearing."""
    inventory, costs, first, seen, started = {}, {}, {}, set(), set()
    for row in sorted([*rows, *merges], key=lambda r: (r['block_number'], r['transaction_index'], r['log_index'])):
        if row.get('event_type') == 'MERGE':
            q = inventory[row['slug']]
            assert row['qty'] <= min(q), 'merge exceeds acquired pairs'
            q[0] -= row['qty']
            q[1] -= row['qty']
            costs[row['slug']] -= row['qty']
            row.update(post_qty=[str(D(v)/UNIT) for v in q], post_net_cash_cost=str(D(costs[row['slug']])/UNIT))
            continue
        assert row['side'] == 0, 'SELL requires separate inventory replay'
        slug, side, qty = row['slug'], row['outcome'], row['qty']
        q = inventory.setdefault(slug, [0, 0])
        cost = costs.get(slug, 0)
        pre_net = q[0]-q[1]
        close = min(qty, max(0, -pre_net if side == 0 else pre_net))
        opening = qty-close
        kind = None
        if opening:
            kind = 'first' if slug not in started else 'reopen' if close or not pre_net else 'add'
        phase = kind or 'completion'
        key = (slug, row['order_hash'])
        first.setdefault(key, (row['api_ts'], phase))
        if first[key][0] < row['api_ts']:
            origin = 'parent_seen_earlier_second'
        elif key in seen:
            origin = 'same_second_parent_fragment'
        else:
            origin = 'first_observed_parent_fill'
        row.update(pre_qty=[str(D(v)/UNIT) for v in q], pre_cost=str(D(cost)/UNIT),
            pre_net=str(D(pre_net)/UNIT), pre_worst=str(D(min(q)-cost)/UNIT),
            completion_qty=str(D(close)/UNIT), opening_qty=str(D(opening)/UNIT),
            opening_kind=kind, phase=phase, parent_first_ts=first[key][0],
            parent_first_phase=first[key][1], parent_origin=origin)
        q[side] += qty
        costs[slug] = cost+row['cash_cost']
        row.update(post_qty=[str(D(v)/UNIT) for v in q], post_cost=str(D(costs[slug])/UNIT),
                   post_worst=str(D(min(q)-costs[slug])/UNIT))
        seen.add(key)
        started.add(slug)


def analyze():
    activity = read(OUT/'activity.json')
    selected = read(OUT/'selection.json')
    txs = list(dict.fromkeys(r['transactionHash'] for r in activity))
    rows, failures, tx_details = [], [], []
    cross = []
    for tx in txs:
        providers = []
        for i, _ in enumerate(RPCS):
            path = OUT/'raw'/f'receipt_{i}_{tx}.json'
            if path.exists() and read(path).get('response', {}).get('result'):
                providers.append((i, read(path)['response']['result']))
        if not providers:
            failures.append(dict(tx=tx, error='NO_RECEIPT'))
            continue
        receipt = providers[0][1]
        if len(providers) == 2:
            fields = ('transactionHash', 'blockHash', 'status', 'logs')
            assert all(receipt[k] == providers[1][1][k] for k in fields), 'providers disagree'
            cross.append(tx)
        api = [r for r in activity if r['transactionHash'] == tx]
        slug, = {r['slug'] for r in api}
        market = read(OUT/f'{slug}.json')['data']
        try:
            decoded = dec.decode(receipt, ACTOR)
            reconcile(api, decoded, market)
        except AssertionError as exc:
            failures.append(dict(tx=tx, error=str(exc)))
            continue
        timestamp, = {r['timestamp'] for r in api}
        start = int(slug.rsplit('-', 1)[1])
        block_path = OUT/'raw'/f"block_{receipt['blockNumber']}.json"
        block_ts = None
        if block_path.exists():
            block = read(block_path).get('response', {}).get('result')
            if block:
                assert block['hash'] == receipt['blockHash']
                block_ts = int(block['timestamp'], 16)
        for fill in decoded:
            fill.update(slug=slug, api_ts=timestamp, block_ts=block_ts, age=timestamp-start,
                        block_number=int(receipt['blockNumber'], 16),
                        transaction_index=int(receipt['transactionIndex'], 16),
                        outcome=json.loads(market['clobTokenIds']).index(fill['token']))
        rows.extend(decoded)
        tx_details.append(dict(tx=tx, slug=slug, api_rows=len(api), exchange_fills=len(decoded),
                               all_order_filled_events=sum(log['address'].lower() == dec.EXCHANGE
                                   and log['topics'][0] == dec.FILLED for log in receipt['logs']),
                               orders_matched_events=sum(log['address'].lower() == dec.EXCHANGE
                                   and log['topics'][0] == dec.MATCHED for log in receipt['logs']),
                               cash=str(sum(D(str(r['usdcSize'])) for r in api)),
                               api_ts=timestamp, block_ts=block_ts))
    merges = []
    merge_file = OUT/'merge_selection.json'
    if merge_file.exists():
        api_merge = read(merge_file)['row']
        receipt = read(OUT/'raw'/f"merge_{api_merge['transactionHash']}.json")['response']['result']
        block = read(OUT/'raw'/f"block_{receipt['blockNumber']}.json")['response']['result']
        assert block['hash'] == receipt['blockHash'] and int(block['timestamp'], 16) == api_merge['timestamp']
        market = read(OUT/f"{api_merge['slug']}.json")['data']
        merges.append(verify_merge(receipt, api_merge, json.loads(market['clobTokenIds'])))
    inventory_phases(rows, merges)
    parents = defaultdict(list)
    for row in rows:
        parents[(row['slug'], row['order_hash'])].append(row)
    parent_rows = []
    for (slug, parent), group in parents.items():
        group.sort(key=lambda r: (r['api_ts'], r['tx'], r['log_index']))
        parent_rows.append(dict(slug=slug, order_hash=parent, fills=len(group),
            txs=len({r['tx'] for r in group}), first_age=min(r['age'] for r in group),
            last_age=max(r['age'] for r in group), roles=sorted({r['role'] for r in group}),
            shares=str(sum(r['qty'] for r in group)/UNIT),
            cash=str(sum(r['cash_cost'] for r in group)/UNIT),
            first_phase=group[0]['parent_first_phase'],
            phases=sorted({r['phase'] for r in group}),
            spans_600=min(r['age'] for r in group)<600<=max(r['age'] for r in group)))
    windows = []
    for item in selected['markets']:
        w = item['window']
        slug = w['slug']
        group = [r for r in rows if r['slug'] == slug]
        ps = [r for r in parent_rows if r['slug'] == slug]
        api = [r for r in activity if r['slug'] == slug]
        pnl = sum((D(r['qty'])*(r['outcome'] == w['winner'])-D(r['cash_cost']) for r in group), D(0))/UNIT
        windows.append(dict(slug=slug, api_rows=len(api), decoded_rows=len(group), parents=len(ps),
            late_api_rows=sum(r['timestamp']-w['S']>=600 for r in api),
            late_parents=len({r['order_hash'] for r in group if r['age']>=600}),
            shares_by_role={role: str(sum(r['qty'] for r in group if r['role']==role)/UNIT)
                            for role in ['maker','taker']}, pnl=str(pnl), expected_pnl=str(w['pnl']),
            full_reconciled=not any(r['transactionHash'] in {f['tx'] for f in failures} for r in api)))
    late_adds = [r for r in rows if r['age'] >= 600 and r['opening_kind'] == 'add']
    decomposition = {}
    for origin in sorted({r['parent_origin'] for r in late_adds}):
        g = [r for r in late_adds if r['parent_origin'] == origin]
        decomposition[origin] = dict(rows=len(g), shares=str(sum(D(r['opening_qty']) for r in g)),
            parent_count=len({(r['slug'], r['order_hash']) for r in g}))
    result = dict(status='VERIFIED_SELECTED_EXPLORATORY' if not failures else 'INCOMPLETE',
        activity_rows=len(activity), transactions=len(txs), decoded_fills=len(rows),
        parents=len(parent_rows), cross_provider_receipts=cross, failures=failures,
        late_add_origin=decomposition, merge_records=merges,
        windows=windows, parent_orders=parent_rows, rows=rows, tx_details=tx_details,
        limitations=['Selected S cases are known, not blind or representative.',
                     'orderHash identifies signed order, not order placement/cancel time.',
                     'Maker settlement role is not proof of long passive quote lifetime.',
                     'Zero observed fill does not reveal unfilled/cancelled orders.'])
    save(OUT/'results.json', result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','parent_orders','tx_details']},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    if '--fetch' in sys.argv:
        fetch()
    analyze()
