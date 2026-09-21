"""Finite public-receipt probe, not a trading lane. Default: cached validation.

python3 check.py --fetch   # only unauthenticated public JSON-RPC reads
python3 check.py           # decode and reconcile the frozen seven-row example
V2 schema: github.com/Polymarket/ctf-exchange-v2, ITrading.sol / Trading.sol.
"""
from collections import defaultdict
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
import json
import sys
import time
import urllib.request

OUT = Path(__file__).resolve().parent
EXCHANGE = '0xe111180000d2663c0091e4f400237545b87b996b'
CASH = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
CTF = '0x4d97dcd97ec945f40cf65f87097ace5ea0476045'
FILLED = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
MATCHED = '0x174b3811690657c217184f89418266767c87e4805d09680c39fc9c031c0cab7c'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
SINGLE = '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
RPCS = ('https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org')
UNIT = D(1000000)


def read(path):
    return json.loads(path.read_text())


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2)+'\n')


def words(data, count):
    assert data.startswith('0x') and len(data) == 2+64*count, 'wrong V2 event size'
    return [int(data[i:i+64], 16) for i in range(2, len(data), 64)]


def address(topic):
    assert len(topic) == 66 and int(topic[2:26], 16) == 0, 'invalid address topic'
    return '0x'+topic[-40:]


def rpc(url, method, params):
    request = urllib.request.Request(
        url, json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'BosonaResearch/1'})
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.load(response)
    assert 'error' not in result and result.get('result') is not None, 'RPC missing result'
    return result['result']


def fetch(activity):
    directory = OUT/'receipts'
    directory.mkdir(exist_ok=True)
    checks = {}
    for url in RPCS:
        checks[url] = rpc(url, 'eth_chainId', [])
        assert checks[url] == '0x89', 'not Polygon mainnet'
    # Unique transactions fetch receipts once; all activity rows/logs remain intact.
    for tx in dict.fromkeys(row['transactionHash'] for row in activity):
        path = directory/f'{tx}.json'
        if not path.exists():
            result = rpc(RPCS[0], 'eth_getTransactionReceipt', [tx])
            assert result['transactionHash'] == tx and result['status'] == '0x1'
            save(path, result)
    first = activity[0]['transactionHash']
    other = rpc(RPCS[1], 'eth_getTransactionReceipt', [first])
    first_receipt = read(directory/f'{first}.json')
    for key in ('transactionHash', 'blockHash', 'status', 'logs'):
        assert other[key] == first_receipt[key], f'providers disagree: {key}'
    save(OUT/'fetch_manifest.json', dict(fetched_ms=round(time.time()*1000),
         chain_ids=checks, cross_provider_tx=first, cross_provider_logs_equal=True,
         receipts={p.name: sha256(p.read_bytes()).hexdigest() for p in directory.glob('*.json')}))


def decode(receipt, actor):
    assert receipt['status'] == '0x1' and receipt['to'].lower() == EXCHANGE
    fills, pending, identities = [], [], set()
    cash_out, token_net = 0, defaultdict(int)
    for log in receipt['logs']:
        assert not log.get('removed', False)
        assert log['transactionHash'] == receipt['transactionHash']
        assert log['blockHash'] == receipt['blockHash']
        identity = (log['transactionHash'], int(log['logIndex'], 16))
        assert identity not in identities, 'duplicate event identity'
        identities.add(identity)
        topic, contract = log['topics'], log['address'].lower()
        if contract == CASH and topic[0] == TRANSFER:
            amount, = words(log['data'], 1)
            cash_out += amount*((address(topic[1]) == actor)-(address(topic[2]) == actor))
        if contract == CTF and topic[0] == SINGLE:
            token, amount = words(log['data'], 2)
            token_net[str(token)] += amount*((address(topic[3]) == actor)-(address(topic[2]) == actor))
        if contract != EXCHANGE:
            continue
        if topic[0] == FILLED:
            assert len(topic) == 4
            data = words(log['data'], 7)
            assert data[0] in (0, 1)
            pending.append(dict(order_hash=topic[1], owner=address(topic[2]),
                                counterparty=address(topic[3]), data=data,
                                tx=identity[0], log_index=identity[1]))
        elif topic[0] == MATCHED:
            assert len(topic) == 3
            matched = words(log['data'], 4)
            active = [f for f in pending if f['order_hash'] == topic[1]]
            assert len(active) == 1 and active[0]['owner'] == address(topic[2])
            assert active[0]['data'][:4] == matched
            assert active[0]['counterparty'] == EXCHANGE
            for fill in pending:
                is_active = fill is active[0]
                assert is_active or fill['counterparty'] == address(topic[2])
                if fill['owner'] == actor:
                    side, token, making, taking, fee, _, _ = fill.pop('data')
                    fill.update(role='taker' if is_active else 'maker', side=side,
                                token=str(token), qty=taking if side == 0 else making,
                                cash_cost=making+fee if side == 0 else -(taking-fee), fee=fee)
                    fills.append(fill)
            pending = []
    assert not pending, 'unmatched OrderFilled events'
    assert fills and sum(f['cash_cost'] for f in fills) == cash_out, 'cash transfer mismatch'
    expected = defaultdict(int)
    for fill in fills:
        expected[fill['token']] += fill['qty']*(1 if fill['side'] == 0 else -1)
    assert {k:v for k,v in token_net.items() if v} == dict(expected), 'token transfer mismatch'
    return fills


def main():
    activity = read(OUT/'activity_burst.json')
    assert len(activity) == 7 and sum(D(str(r['size'])) for r in activity) == 297
    if '--fetch' in sys.argv:
        fetch(activity)
    market = read(OUT/'market.json')
    tokens = json.loads(market['clobTokenIds'])
    actor, = {row['proxyWallet'].lower() for row in activity}
    rows, receipts = [], {}
    for tx in dict.fromkeys(row['transactionHash'] for row in activity):
        receipt = read(OUT/'receipts'/f'{tx}.json')
        assert receipt['transactionHash'] == tx
        group = [r for r in activity if r['transactionHash'] == tx]
        assert all(r['conditionId'] == market['conditionId'] and r['side'] == 'BUY'
                   and r['asset'] == tokens[r['outcomeIndex']] for r in group)
        decoded = decode(receipt, actor)
        assert all(f['side'] == 0 for f in decoded)
        for token in {r['asset'] for r in group} | {f['token'] for f in decoded}:
            api_qty = sum(D(str(r['size'])) for r in group if r['asset'] == token)
            api_cash = sum(D(str(r['usdcSize'])) for r in group if r['asset'] == token)
            actual = [f for f in decoded if f['token'] == token]
            assert abs(api_qty-sum(f['qty'] for f in actual)/UNIT) <= D('.000001')
            assert abs(api_cash-sum(f['cash_cost'] for f in actual)/UNIT) <= D('.00001')
        rows.extend(decoded)
        receipts[tx] = dict(block=receipt['blockNumber'], block_hash=receipt['blockHash'])
    groups = defaultdict(list)
    for row in rows:
        groups[row['order_hash']].append(row)
    result = dict(mode='OFFLINE_ACTOR_CONDITIONAL_NO_ORDERS', activity_records=len(activity),
        transactions=len(receipts), exchange_fills=len(rows), distinct_actor_orders=len(groups),
        shares=str(sum(r['qty'] for r in rows)/UNIT),
        roles={role: str(sum(r['qty'] for r in rows if r['role'] == role)/UNIT)
               for role in ('maker', 'taker')},
        parent_orders={key: dict(fills=len(g), shares=str(sum(r['qty'] for r in g)/UNIT),
                       roles=sorted({r['role'] for r in g})) for key,g in groups.items()},
        cash_and_token_transfers_reconciled=True, rows=rows, receipts=receipts,
        limits='One selected burst. No placement/cancel time, full order lifetime or general frequency inferred.')
    save(OUT/'report.json', result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','receipts')}, indent=2))


if __name__ == '__main__':
    main()
