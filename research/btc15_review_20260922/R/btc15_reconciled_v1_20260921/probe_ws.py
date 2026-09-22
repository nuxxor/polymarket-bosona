"""90-second public BTC15 feed probe, foreground only. No wallet, no orders."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

import websocket

from common import HERE, accounting, save


def main():
    start = int(time.time())//900*900
    slug = f'btc-updown-15m-{start}'
    market = accounting.ref.base.get('https://gamma-api.polymarket.com/markets/slug/'+slug,
                                     timeout=5, attempts=1)
    meta = accounting.ref.classify(market)
    assert meta['group'] == 'btc_15m' and meta['S'] == start
    assert meta['mechanism'] == 'chainlink_twap60'
    tokens = json.loads(market['clobTokenIds'])
    directory = HERE/'raw'/('ws_probe_'+str(time.time_ns()))
    directory.mkdir(parents=True)
    endpoint = 'wss://ws-subscriptions-clob.polymarket.com/ws/market'
    subscription = dict(assets_ids=tokens, type='market', custom_feature_enabled=True)
    before = time.time_ns()//1000000
    stop = time.monotonic()+90
    count, errors, socket = Counter(), [], None
    received = []
    try:
        socket = websocket.create_connection(endpoint, timeout=5)
        socket.send(json.dumps(subscription))
        socket.settimeout(1)
        ping = time.monotonic()
        with gzip.open(directory/'events.jsonl.gz', 'xt', compresslevel=3) as stream:
            while time.monotonic() < stop:
                if time.monotonic()-ping > 10:
                    socket.send('PING')
                    ping = time.monotonic()
                try:
                    raw = socket.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                rcv, mono = time.time_ns()//1000000, time.monotonic_ns()
                if not raw:
                    raise OSError('public websocket closed')
                if raw == 'PONG':
                    count['PONG'] += 1
                    continue
                data = json.loads(raw)
                stream.write(json.dumps(dict(received_ms=rcv, monotonic_ns=mono, data=data), separators=(',', ':'))+'\n')
                received.append(rcv)
                for event in data if isinstance(data, list) else [data]:
                    count[event.get('event_type', event.get('type', 'unknown'))] += 1
    except (OSError, ValueError, websocket.WebSocketException) as exc:
        errors.append(type(exc).__name__+': '+str(exc))
    finally:
        if socket:
            socket.close()
        result = dict(endpoint=endpoint, subscription=subscription, slug=slug,
            condition=market['conditionId'], start_ms=before, end_ms=time.time_ns()//1000000,
            duration_limit_seconds=90, counts=dict(count), errors=errors,
            first_receive_ms=min(received) if received else None,
            last_receive_ms=max(received) if received else None,
            note='Finite feed/schema probe; partial market, no strategy PnL. Existing recorders untouched.',
            code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        (directory/'market.json').write_text(json.dumps(market)+'\n')
        result['files'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()}
        (directory/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
        save('results/ws_probe.json', dict(path=str(directory), **result))
        print(json.dumps(result))


if __name__ == '__main__':
    main()
