#!/usr/bin/env python3
"""Persistent collector for BTC RTDS prices (Chainlink + Binance).

Subscribes to Polymarket RTDS and writes every BTC price update to a dedicated
SQLite database for causal BTC market replay and timing research.

Independent of the trading bot — runs as its own process.
"""

from __future__ import annotations

import asyncio
import signal
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from polymarket_bot.collectors.rtds_ws import RTDSWebSocket

DB_PATH = ROOT_DIR / "data" / "db" / "chainlink_history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS btc_prices (
  ts_ms INTEGER NOT NULL,
  source TEXT NOT NULL,
  price REAL NOT NULL,
  PRIMARY KEY (ts_ms, source)
);
CREATE INDEX IF NOT EXISTS idx_btc_prices_ts ON btc_prices(ts_ms);
CREATE INDEX IF NOT EXISTS idx_btc_prices_source_ts ON btc_prices(source, ts_ms);
"""


class _NullRawLogger:
    def log(self, _event: dict[str, Any]) -> None:
        return


async def _consume(
    queue: asyncio.Queue,
    con: sqlite3.Connection,
    latest_btc: dict[str, float],
) -> None:
    cur = con.cursor()
    n_total = 0
    n_uncommitted = 0
    last_status = time.time()
    while True:
        row = await queue.get()
        if row is None:
            break
        if row.table != "btc_prices":
            continue
        try:
            cur.execute(
                "INSERT OR IGNORE INTO btc_prices(ts_ms, source, price) VALUES (?, ?, ?)",
                (row.data["ts_ms"], row.data["source"], row.data["price"]),
            )
            n_total += 1
            n_uncommitted += 1
            if n_uncommitted >= 50:
                con.commit()
                n_uncommitted = 0
        except Exception as exc:
            print(f"[chainlink-collector] insert error: {exc}", flush=True)
        now = time.time()
        if now - last_status >= 30:
            con.commit()
            n_uncommitted = 0
            print(
                f"[chainlink-collector] inserts={n_total} "
                f"chainlink={latest_btc.get('chainlink')} "
                f"binance={latest_btc.get('binance')}",
                flush=True,
            )
            last_status = now
    con.commit()


async def main_async() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.executescript(SCHEMA)
    con.commit()

    latest_btc: dict[str, float] = {}
    latest_btc_ts: dict[str, int] = {}
    db_queue: asyncio.Queue = asyncio.Queue(maxsize=10_000)
    raw_logger = _NullRawLogger()
    ws = RTDSWebSocket(latest_btc, latest_btc_ts, raw_logger, db_queue)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_event.set)

    consumer_task = asyncio.create_task(_consume(db_queue, con, latest_btc))
    ws_task = asyncio.create_task(ws.run())

    print(f"[chainlink-collector] started; db={DB_PATH}", flush=True)
    try:
        await stop_event.wait()
    finally:
        print("[chainlink-collector] stopping", flush=True)
        try:
            await ws.stop()
        except Exception:
            pass
        await db_queue.put(None)
        try:
            await asyncio.wait_for(consumer_task, timeout=5.0)
        except asyncio.TimeoutError:
            consumer_task.cancel()
        ws_task.cancel()
        try:
            await ws_task
        except (asyncio.CancelledError, Exception):
            pass
        con.commit()
        con.close()


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass
