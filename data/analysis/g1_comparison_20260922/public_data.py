"""Bounded, cached public-data collection for the frozen R1 cohort; no credentials."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
import json
import time
import urllib.parse
import urllib.error
import urllib.request

OUT = Path(__file__).resolve().parent
RPCS = ('https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org')


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, separators=(',', ':'))+'\n')
    temp.replace(path)


def request(url, payload=None):
    req = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode(),
          headers={'User-Agent': 'BosonaResearch/1', 'Content-Type': 'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 2:
                raise
            retry = error.headers.get('Retry-After', '')
            time.sleep(min(30, max(5, int(retry))) if retry.isdigit() else 5)


def rpc(url, method, params):
    result = request(url, dict(jsonrpc='2.0', id=1, method=method, params=params))
    if result.get('error') or result.get('result') is None:
        raise ValueError('RPC error or absent result')
    return result['result']


def receipt(tx):
    path = OUT/'receipts'/f'{tx}.json'
    if path.exists():
        result = read(path)
    else:
        for n, url in enumerate(RPCS):
            try:
                result = rpc(url, 'eth_getTransactionReceipt', [tx])
                break
            except (OSError, ValueError):
                if n == len(RPCS)-1:
                    raise
                time.sleep(1)
        if result.get('transactionHash') != tx or result.get('status') != '0x1':
            raise ValueError('receipt identity/status')
        save(path, result)
        time.sleep(.15)
    assert result['transactionHash'] == tx and result['status'] == '0x1'
    return dict(kind='receipt', key=tx, logs=len(result['logs']))


def market_activity(item, wallet):
    start, market = item
    path = OUT/'full_activity'/f'{start}.json'
    if not path.exists():
        rows = []
        for offset in range(0, 5001, 500):
            query = urllib.parse.urlencode(dict(user=wallet, market=market['conditionId'],
                    limit=500, offset=offset, sortBy='TIMESTAMP', sortDirection='ASC'))
            batch = request('https://data-api.polymarket.com/activity?'+query)
            assert isinstance(batch, list)
            assert all(r['proxyWallet'].lower() == wallet and r['conditionId'] == market['conditionId'] for r in batch)
            rows.extend(batch)
            if len(batch) < 500:
                save(path, dict(complete=True, pages=offset//500+1, fetched_ms=round(time.time()*1000), rows=rows))
                break
            time.sleep(.5)
        else:
            raise ValueError('activity pagination incomplete')
        time.sleep(2)
    result = read(path)
    assert result['complete']
    return dict(kind='activity', key=start, rows=len(result['rows']))


def main():
    manifest = read(OUT/'manifest.json')
    for name, digest in manifest['input_sha256'].items():
        assert sha256((OUT/name).read_bytes()).hexdigest() == digest
    activity, markets = read(OUT/'activity.json'), read(OUT/'markets.json')
    wallet, = {r['proxyWallet'].lower() for r in activity}
    transactions = sorted({r['transactionHash'] for r in activity if r['type'] == 'TRADE'})
    for folder in ('receipts', 'full_activity'):
        (OUT/folder).mkdir(exist_ok=True)
    started = round(time.time()*1000)
    assert all(rpc(url, 'eth_chainId', []) == '0x89' for url in RPCS)
    failures, completed = [], []
    with ThreadPoolExecutor(max_workers=3) as rp, ThreadPoolExecutor(max_workers=1) as ap:
        jobs = {rp.submit(receipt, tx): ('receipt', tx) for tx in transactions}
        jobs.update({ap.submit(market_activity, item, wallet): ('activity', item[0]) for item in markets.items()})
        for i, future in enumerate(as_completed(jobs), 1):
            kind, key = jobs[future]
            try:
                completed.append(future.result())
            except (OSError, ValueError, AssertionError, KeyError, TypeError) as error:
                failures.append(dict(kind=kind, key=key, error=type(error).__name__, detail=str(error)[:180]))
            if i % 100 == 0 or i == len(jobs):
                print(f'collected {i}/{len(jobs)}; failed {len(failures)}', flush=True)
    cross_checks = []
    # One deterministic transaction per calendar day, second-provider validation.
    days = {}
    for row in sorted(activity, key=lambda r:r['transactionHash']):
        if row['type'] == 'TRADE':
            days.setdefault(row['timestamp']//86400, row['transactionHash'])
    for tx in days.values():
        try:
            first = read(OUT/'receipts'/f'{tx}.json')
            second = rpc(RPCS[1], 'eth_getTransactionReceipt', [tx])
            assert all(first[k] == second[k] for k in ('blockHash', 'transactionHash', 'status', 'logs'))
            cross_checks.append(tx)
        except (OSError, ValueError, AssertionError) as error:
            failures.append(dict(kind='cross_provider', key=tx, error=type(error).__name__))
    save(OUT/'fetch_manifest.json', dict(started_ms=started, finished_ms=round(time.time()*1000),
         transactions_requested=len(transactions), markets_requested=len(markets), failures=failures,
         completed=len(completed), cross_provider_equal=cross_checks,
         collector_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
         files={str(p.relative_to(OUT)): sha256(p.read_bytes()).hexdigest()
                for folder in ('receipts', 'full_activity') for p in (OUT/folder).glob('*.json')}))
    print(f'Collection finished: {len(completed)} successes, {len(failures)} failures', flush=True)


if __name__ == '__main__':
    main()
