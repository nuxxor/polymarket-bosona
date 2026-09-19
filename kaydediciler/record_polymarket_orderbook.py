#!/usr/bin/env python3
"""Persistent Polymarket Market WebSocket recorder for BTC Up/Down markets.

Captures every event from the public market channel
(wss://ws-subscriptions-clob.polymarket.com/ws/market) for active BTC 5m
Up/Down markets, writes raw JSON + index metadata to SQLite. Enables future
L3 backtest with real orderbook history.

Event types captured: book (full snapshot), price_change (deltas),
last_trade_price (executions), tick_size_change, market_resolved.

PRO recommendation: start this NOW. Every hour without recorder = lost L3
data, because Polymarket has no full historical orderbook endpoint.

Usage:
  python3 scripts/record_polymarket_orderbook.py
"""

from __future__ import annotations

import asyncio
import json
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from polymarket_bot.config import settings
from polymarket_bot.utils.ws_reconnect import ReconnectingWS
from polymarket_bot.utils.polymarket_public import matches_btc_updown_family, parse_json_list

GAMMA_API = "https://gamma-api.polymarket.com"
DB_PATH = ROOT_DIR / "data" / "db" / "polymarket_orderbook.db"
USER_AGENT = "polymarket-orderbook-recorder/1.0"

SCHEMA = """
CREATE TABLE IF NOT EXISTS market_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_ms INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  asset_id TEXT,
  condition_id TEXT,
  raw_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_market_events_ts ON market_events(ts_ms);
CREATE INDEX IF NOT EXISTS idx_market_events_asset_ts ON market_events(asset_id, ts_ms);
CREATE INDEX IF NOT EXISTS idx_market_events_cid_ts ON market_events(condition_id, ts_ms);
CREATE INDEX IF NOT EXISTS idx_market_events_type_ts ON market_events(event_type, ts_ms);

CREATE TABLE IF NOT EXISTS subscribed_assets (
  asset_id TEXT PRIMARY KEY,
  condition_id TEXT,
  market_title TEXT,
  side TEXT,
  start_ts INTEGER,
  end_ts INTEGER,
  subscribed_at_ms INTEGER NOT NULL
);
"""


def configure_sqlite(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")


def floor_5m(ts: int) -> int:
    return ts - (ts % 300)


def discover_btc_markets(session: requests.Session, now_ts: int, lookahead_buckets: int = 3) -> list[dict[str, Any]]:
    anchor = floor_5m(now_ts)
    rows: list[dict[str, Any]] = []
    for offset in range(-1, lookahead_buckets + 1):
        bucket = anchor + offset * 300
        slug = f"btc-updown-5m-{bucket}"
        try:
            r = session.get(f"{GAMMA_API}/events", params={"slug": slug}, timeout=15)
            if not r.ok:
                continue
            payload = r.json()
        except Exception:
            continue
        if not isinstance(payload, list) or not payload:
            continue
        event = payload[0]
        title = str(event.get("title") or "")
        if not matches_btc_updown_family(title, "range"):
            continue
        for market in event.get("markets") or []:
            outcomes = [str(x).strip() for x in parse_json_list(market.get("outcomes"))]
            token_ids = [str(x) for x in parse_json_list(market.get("clobTokenIds"))]
            if len(outcomes) < 2 or len(token_ids) < 2:
                continue
            try:
                up_idx = outcomes.index("Up")
                down_idx = outcomes.index("Down")
            except ValueError:
                continue
            rows.append({
                "condition_id": str(market.get("conditionId") or ""),
                "title": str(market.get("question") or title),
                "up_token": token_ids[up_idx],
                "down_token": token_ids[down_idx],
                "start_ts": bucket,
                "end_ts": bucket + 300,
            })
    return rows


def db_init() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    configure_sqlite(con)
    con.executescript(SCHEMA)
    con.commit()
    return con


def db_record_subscription(con: sqlite3.Connection, asset_id: str, cid: str,
                            title: str, side: str, start_ts: int, end_ts: int) -> None:
    now_ms = int(time.time() * 1000)
    con.execute(
        "INSERT OR REPLACE INTO subscribed_assets "
        "(asset_id, condition_id, market_title, side, start_ts, end_ts, subscribed_at_ms) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (asset_id, cid, title, side, start_ts, end_ts, now_ms),
    )
    con.commit()


def db_record_event(cur: sqlite3.Cursor, event_type: str, asset_id: str | None,
                    condition_id: str | None, raw: dict[str, Any]) -> None:
    cur.execute(
        "INSERT INTO market_events(ts_ms, event_type, asset_id, condition_id, raw_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (int(time.time() * 1000), event_type, asset_id, condition_id, json.dumps(raw)),
    )


class MarketRecorder(ReconnectingWS):
    def __init__(self, db_path: Path) -> None:
        super().__init__(
            settings.clob_ws_url,
            keepalive_s=settings.ws_keepalive_s,
            inactivity_timeout_s=settings.clob_inactivity_timeout_s,
        )
        self._asset_ids: set[str] = set()
        self._asset_to_cid: dict[str, str] = {}
        self._db_path = db_path
        self._con: sqlite3.Connection | None = None
        self._cur: sqlite3.Cursor | None = None
        self._n_events = 0
        self._n_uncommitted = 0
        self._last_event_mono = time.monotonic()

    async def _subscribe_assets(self, asset_ids: list[str], reason: str) -> None:
        if not asset_ids:
            return
        await self._send_json({
            "type": "subscribe",
            "channel": "market",
            "assets_ids": asset_ids,
        })
        print(f"[recorder] {reason} subscribed {len(asset_ids)} assets in one batch", flush=True)

    def open_db(self) -> None:
        self._con = sqlite3.connect(str(self._db_path))
        configure_sqlite(self._con)
        self._cur = self._con.cursor()

    def close_db(self) -> None:
        if self._con:
            self._con.commit()
            self._con.close()
            self._con = None
            self._cur = None

    async def on_reconnect(self) -> None:
        await self._subscribe_assets(sorted(self._asset_ids), "(re)")

    async def add_assets(self, new_assets: list[tuple[str, str]]) -> int:
        added_assets: list[str] = []
        for asset_id, cid in new_assets:
            if asset_id in self._asset_ids:
                continue
            self._asset_ids.add(asset_id)
            self._asset_to_cid[asset_id] = cid
            added_assets.append(asset_id)
        if not added_assets:
            return 0
        try:
            # The market WS reliably emits snapshots when subscribed as a batch.
            await self._subscribe_assets(sorted(self._asset_ids), "active-set")
        except Exception as exc:
            print(f"[recorder] subscribe error for {len(added_assets)} assets: {exc}", flush=True)
        return len(added_assets)

    async def on_message(self, data: dict) -> None:
        if self._cur is None:
            return
        event_type = str(data.get("event_type") or data.get("type") or "unknown")
        asset_id = data.get("asset_id")
        if not asset_id:
            for change in data.get("price_changes") or []:
                aid = change.get("asset_id")
                if aid:
                    asset_id = aid
                    break
        cid = self._asset_to_cid.get(asset_id) if asset_id else None
        try:
            db_record_event(self._cur, event_type, asset_id, cid, data)
            self._n_events += 1
            self._n_uncommitted += 1
            self._last_event_mono = time.monotonic()
            if self._n_uncommitted >= 50:
                self._con.commit()
                self._n_uncommitted = 0
        except Exception as exc:
            print(f"[recorder] insert error: {exc}", flush=True)


async def discovery_loop(recorder: MarketRecorder, con: sqlite3.Connection, stop_event: asyncio.Event) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    end_by_asset: dict[str, int] = {}
    while not stop_event.is_set():
        try:
            now_ts = int(time.time())
            markets = await asyncio.to_thread(discover_btc_markets, session, now_ts, 3)
            new_assets: list[tuple[str, str]] = []
            for m in markets:
                if m["up_token"] and m["up_token"] not in recorder._asset_ids:
                    new_assets.append((m["up_token"], m["condition_id"]))
                    db_record_subscription(con, m["up_token"], m["condition_id"], m["title"], "Up", m["start_ts"], m["end_ts"])
                if m["down_token"] and m["down_token"] not in recorder._asset_ids:
                    new_assets.append((m["down_token"], m["condition_id"]))
                    db_record_subscription(con, m["down_token"], m["condition_id"], m["title"], "Down", m["start_ts"], m["end_ts"])
            for m in markets:
                for tkn in (m.get("up_token"), m.get("down_token")):
                    if tkn: end_by_asset[tkn] = int(m.get("end_ts") or 0)
            if new_assets:
                added = await recorder.add_assets(new_assets)
                print(f"[discovery] +{added} new assets ({len(markets)} markets in window)", flush=True)
            # 09-19 22:55Z DUZELTME: biten pencereler hic birakilmiyordu -> abonelik 190+ asset'e sisti ve
            # 22:25-22:35Z arasi olaylar KAYBOLDU (22:25Z penceresi 0 olay). Sunucu tarafinda unsubscribe yok;
            # eskileri listeden dusup WS'i kapatiyoruz -> on_reconnect yalniz aktif seti abone eder.
            stale = {a for a in recorder._asset_ids if end_by_asset.get(a, now_ts + 10**6) < now_ts - 120}
            if len(stale) >= 6:
                recorder._asset_ids -= stale
                for a in stale: recorder._asset_to_cid.pop(a, None)
                print(f"[discovery] pruned {len(stale)} stale assets -> {len(recorder._asset_ids)} active; forcing WS reconnect", flush=True)
                if recorder._ws and not recorder._ws.closed:
                    await recorder._ws.close()
        except Exception as exc:
            print(f"[discovery] error: {exc}", flush=True)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            pass


async def status_loop(recorder: MarketRecorder, stop_event: asyncio.Event) -> None:
    last = 0
    while not stop_event.is_set():
        await asyncio.sleep(30)
        delta = recorder._n_events - last
        idle_s = time.monotonic() - recorder._last_event_mono
        print(
            f"[recorder] events_total={recorder._n_events} "
            f"events_last_30s={delta} subs={len(recorder._asset_ids)} idle_s={idle_s:.0f}",
            flush=True,
        )
        if len(recorder._asset_ids) > 0 and idle_s > 600:
            print("[recorder] no market events for >600s; forcing WS reconnect", flush=True)
            if recorder._ws and not recorder._ws.closed:
                await recorder._ws.close()
            recorder._last_event_mono = time.monotonic()
        last = recorder._n_events


async def main_async() -> None:
    con = db_init()
    recorder = MarketRecorder(DB_PATH)
    recorder.open_db()

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_event.set)

    print(f"[recorder] started; db={DB_PATH}", flush=True)
    ws_task = asyncio.create_task(recorder.run())
    disc_task = asyncio.create_task(discovery_loop(recorder, con, stop_event))
    stat_task = asyncio.create_task(status_loop(recorder, stop_event))

    try:
        await stop_event.wait()
    finally:
        print("[recorder] stopping", flush=True)
        try:
            if recorder._ws and not recorder._ws.closed:
                await recorder._ws.close()
        except Exception:
            pass
        ws_task.cancel()
        disc_task.cancel()
        stat_task.cancel()
        for t in (ws_task, disc_task, stat_task):
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        recorder.close_db()
        con.commit()
        con.close()


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass
