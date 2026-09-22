#!/usr/bin/env python3
"""Deney 4: salt okunur BTC/Chainlink/TWAP kaydi; kimlik/emir yolu yok."""
import argparse
from decimal import Decimal
import fcntl
import json
from pathlib import Path
import signal
import sqlite3
import time

from websockets.sync.client import connect

DATA = Path(__file__).resolve().parents[1] / 'data/d_olcum'
TOPICS = ('crypto_prices', 'crypto_prices_chainlink',
          'crypto_prices_twap_thirty', 'crypto_prices_twap_sixty')


def prices(message, received_ms):
    topic = message.get('topic')
    payload = message.get('payload', {})
    if topic not in TOPICS or message.get('type') != 'update' or not isinstance(payload, dict):
        return []
    symbol = 'btcusdt' if topic == 'crypto_prices' else 'btc/usd'
    if payload.get('symbol', '').lower() != symbol:
        return []
    rows = []
    for point in payload.get('data', [payload]):
        raw = point.get('full_accuracy_value')
        price = (Decimal(str(raw)) / Decimal(10**18) if raw is not None and 'twap' in topic
                 else Decimal(str(point.get('value', point.get('price')))))
        observed = int(point['timestamp'])
        if not price.is_finite() or price <= 0 or observed < 10**12:
            raise ValueError('Gecersiz fiyat/zaman')
        rows.append(dict(source=topic, observed_ms=observed, received_ms=received_ms,
                         published_ms=message.get('timestamp'), price=str(price), parser_version=2))
    return rows


def run(directory, seconds=0):
    directory.mkdir(parents=True, exist_ok=True)
    lock = (directory / '.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stop = directory / 'STOP'
    latest = directory / 'latest.json'
    con = sqlite3.connect(directory / 'prices.db')
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('CREATE TABLE IF NOT EXISTS prices '
                '(received_ms INTEGER, observed_ms INTEGER, source TEXT, price TEXT, raw TEXT)')
    con.execute('CREATE INDEX IF NOT EXISTS received ON prices(received_ms)')
    current = {}
    stopped = False
    deadline = time.monotonic() + seconds if seconds else float('inf')
    def halt(*_):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGINT, halt)
    signal.signal(signal.SIGTERM, halt)
    def active():
        return not stopped and not stop.exists() and time.monotonic() < deadline
    def publish(connected):
        temp = latest.with_suffix('.tmp')
        temp.write_text(json.dumps(dict(received_ms=round(time.time()*1000),
                                       connected=connected, prices=current))+'\n')
        temp.replace(latest)
    subs = [dict(topic=topic, type='*' if topic.endswith('chainlink') else 'update',
                 filters='["btcusdt"]' if topic == 'crypto_prices' else '{"symbol":"btc/usd"}')
            for topic in TOPICS]
    # Sunucu Binance filtresiyle update vermedi; filtresiz akis + yerel BTC filtresi.
    subs[0].pop('filters')
    print('D_OLCUM BASLADI', directory, flush=True)
    try:
        while active():
            try:
                with connect('wss://ws-live-data.polymarket.com', open_timeout=8,
                             close_timeout=2, max_queue=4096) as ws:
                    ws.send(json.dumps(dict(action='subscribe', subscriptions=subs)))
                    ping = 0.0
                    seen = {topic:time.monotonic() for topic in TOPICS}
                    while active():
                        if any(time.monotonic()-stamp>10 for stamp in seen.values()):
                            raise TimeoutError('RTDS fiyat akisi sessiz/bayat')
                        if time.monotonic()-ping >= 5:
                            ws.send('PING')
                            ping = time.monotonic()
                        try:
                            raw = ws.recv(timeout=1)
                        except TimeoutError:
                            continue
                        received = round(time.time()*1000)
                        if raw in ('', 'PONG'):
                            continue
                        message = json.loads(raw)
                        if int(message.get('statusCode', 200)) >= 400:
                            raise ValueError('RTDS aboneligi reddedildi')
                        rows = prices(message, received)
                        for row in rows:
                            con.execute('INSERT INTO prices VALUES (?,?,?,?,?)',
                                        (received, row['observed_ms'], row['source'], row['price'], raw))
                            old = current.get(row['source'])
                            if old is None or row['observed_ms'] > old['observed_ms']:
                                seen[row['source']] = time.monotonic()
                            if old is None or row['observed_ms'] >= old['observed_ms']:
                                current[row['source']] = row
                        if rows:
                            con.commit()
                            publish(True)
            except Exception as exc:
                publish(False)
                print('D_OLCUM YENIDEN_BAGLAN', type(exc).__name__, flush=True)
                for _ in range(5):
                    if not active():
                        break
                    time.sleep(1)
    finally:
        con.commit()
        con.close()
        publish(False)
        lock.close()
        print('D_OLCUM DURDU', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DATA)
    parser.add_argument('--saniye', type=int, default=0)
    args = parser.parse_args()
    if args.saniye < 0:
        parser.error('saniye negatif olamaz')
    run(args.directory, args.saniye)
