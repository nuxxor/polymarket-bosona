"""Bounded public BTC15 data pilot: two hours / 1 GiB raw / free-space guard."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

import websocket

from common import accounting

ENDPOINT = 'wss://ws-subscriptions-clob.polymarket.com/ws/market'


def selected(event, markets):
    if not isinstance(event, dict):
        raise ValueError('invalid market event')
    market = markets.get(event.get('market'))
    if market is None or event.get('event_type') not in (
            'book', 'price_change', 'last_trade_price', 'tick_size_change', 'market_resolved'):
        return False
    tokens = json.loads(market['clobTokenIds'])
    assets = ([x['asset_id'] for x in event['price_changes']]
              if event['event_type'] == 'price_change' else
              [event['asset_id']] if 'asset_id' in event else event.get('assets_ids', []))
    if not assets or not set(assets) <= set(tokens):
        raise ValueError('wrong/missing token in subscribed condition')
    return True


def record(out, seconds):
    out.mkdir(parents=True, exist_ok=False)
    (out/'markets').mkdir()
    start, stop = time.time(), time.monotonic()+seconds
    run = dict(pid=os.getpid(), endpoint=ENDPOINT, start_ms=round(start*1000),
               end_ms=round((start+seconds)*1000), seconds=seconds,
               max_raw_bytes=1024**3, min_free_bytes=2*1024**3,
               source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'run.json').write_text(json.dumps(run)+'\n')
    counters, markets, subscribed = Counter(), {}, set()
    socket, sink, hour, raw_bytes = None, None, None, 0
    health, ping, next_discovery = 0., 0., 0.
    last_event = None
    reason = 'duration_complete'

    def emit(obj):
        nonlocal sink, hour, raw_bytes
        stamp = time.strftime('%Y%m%d_%H', time.gmtime())
        if stamp != hour:
            if sink:
                sink.close()
            sink = gzip.open(out/f'events_{stamp}.jsonl.gz', 'at', compresslevel=3)
            hour = stamp
        line = json.dumps(obj, separators=(',', ':'))+'\n'
        raw_bytes += len(line.encode())
        sink.write(line)

    def status(running):
        body = dict(run, running=running, received_ms=round(time.time()*1000),
                    counts=dict(counters), last_event_ms=last_event, raw_bytes=raw_bytes,
                    subscribed_tokens=len(subscribed), reason=reason)
        tmp = out/'status.tmp'
        tmp.write_text(json.dumps(body)+'\n')
        os.replace(tmp, out/'status.json')

    try:
        status(True)
        while time.monotonic() < stop:
            if time.monotonic() >= health:
                if sink:
                    sink.flush()
                if raw_bytes >= run['max_raw_bytes'] or shutil.disk_usage(out).free < run['min_free_bytes']:
                    reason = 'storage_limit'
                    break
                status(True)
                health = time.monotonic()+10
            try:
                current = int(time.time())//900*900
                if time.monotonic() >= next_discovery:
                    for s in (current, current+900):
                        slug = f'btc-updown-15m-{s}'
                        if any(m['slug'] == slug for m in markets.values()):
                            continue
                        requested = round(time.time()*1000)
                        m = accounting.ref.base.get('https://gamma-api.polymarket.com/markets/slug/'+slug,
                                                     timeout=5, attempts=1)
                        meta = accounting.ref.classify(m)
                        if meta['group'] != 'btc_15m' or meta['S'] != s or meta['mechanism'] != 'chainlink_twap60':
                            raise ValueError('contract changed')
                        markets[m['conditionId']] = m
                        (out/'markets'/f'{slug}.json').write_text(json.dumps(dict(
                            requested_ms=requested, received_ms=round(time.time()*1000), data=m))+'\n')
                    next_discovery = time.monotonic()+30
                wanted = set(t for m in markets.values() if int(m['slug'].rsplit('-', 1)[1]) >= current-900
                             for t in json.loads(m['clobTokenIds']))
                if socket is None:
                    socket = websocket.create_connection(ENDPOINT, timeout=5)
                    socket.send(json.dumps(dict(assets_ids=sorted(wanted), type='market')))
                    socket.settimeout(1)
                    subscribed = wanted
                    emit(dict(kind='connect', received_ms=round(time.time()*1000), tokens=sorted(wanted)))
                    counters['connections'] += 1
                    ping = time.monotonic()
                if wanted-subscribed:
                    socket.send(json.dumps(dict(assets_ids=sorted(wanted-subscribed), operation='subscribe')))
                if subscribed-wanted:
                    socket.send(json.dumps(dict(assets_ids=sorted(subscribed-wanted), operation='unsubscribe')))
                subscribed = wanted
                if time.monotonic()-ping >= 10:
                    socket.send('PING')
                    ping = time.monotonic()
                try:
                    raw = socket.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if raw == 'PONG':
                    counters['PONG'] += 1
                    continue
                if not raw:
                    raise OSError('websocket closed')
                receive, mono = time.time_ns()//1000000, time.monotonic_ns()
                data = json.loads(raw)
                keep = [e for e in (data if isinstance(data, list) else [data]) if selected(e, markets)]
                if keep:
                    last_event = receive
                    emit(dict(kind='events', received_ms=receive, monotonic_ns=mono, data=keep))
                    counters.update(e['event_type'] for e in keep)
            except (OSError, ValueError, KeyError, websocket.WebSocketException) as exc:
                counters['gaps'] += 1
                emit(dict(kind='gap', received_ms=round(time.time()*1000), error=type(exc).__name__+': '+str(exc)))
                if socket:
                    socket.close()
                socket, subscribed = None, set()
                time.sleep(min(2, max(0, stop-time.monotonic())))
    except Exception:
        reason = 'unexpected_error'
        raise
    finally:
        if socket:
            socket.close()
        if sink:
            sink.close()
        status(False)
        (out/'closed_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                                       for p in out.glob('events_*.gz')})+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=7200)
    args = parser.parse_args()
    if not args.out.is_absolute() or not 1 <= args.seconds <= 7200:
        parser.error('absolute output; duration 1..7200 seconds')
    record(args.out, args.seconds)
