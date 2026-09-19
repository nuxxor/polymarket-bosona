from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from polymarket_bot.models import DBRow

log = logging.getLogger(__name__)

SNAPSHOT_OPTIONAL_COLUMNS: dict[str, str] = {
    "binance_best_bid": "REAL",
    "binance_best_ask": "REAL",
    "binance_mid": "REAL",
    "binance_spread_bps": "REAL",
    "binance_trade_count_5s": "INTEGER",
    "binance_buy_notional_5s": "REAL",
    "binance_sell_notional_5s": "REAL",
    "binance_trade_imbalance_5s": "REAL",
    "binance_trade_count_15s": "INTEGER",
    "binance_buy_notional_15s": "REAL",
    "binance_sell_notional_15s": "REAL",
    "binance_trade_imbalance_15s": "REAL",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS markets (
    condition_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    yes_token_id TEXT NOT NULL,
    no_token_id TEXT NOT NULL,
    start_date_ms INTEGER NOT NULL,
    end_date_ms INTEGER NOT NULL,
    resolution_source TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    active INTEGER DEFAULT 1,
    resolved INTEGER DEFAULT 0,
    winning_token_id TEXT,
    discovered_at_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_markets_resolution_window
ON markets(duration_seconds, resolved, end_date_ms, condition_id);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    token_id TEXT NOT NULL,
    condition_id TEXT NOT NULL,
    tau_ms INTEGER NOT NULL,
    vwap_ask_100 REAL,
    vwap_bid_100 REAL,
    spread_100 REAL,
    mid_100 REAL,
    depth_ok INTEGER NOT NULL,
    bid_depth_usd REAL,
    ask_depth_usd REAL,
    imbalance REAL,
    best_bid REAL,
    best_ask REAL,
    tick_size REAL,
    btc_price_binance REAL,
    btc_price_chainlink REAL
);

CREATE INDEX IF NOT EXISTS idx_snap_token_ts ON snapshots(token_id, ts_ms);
CREATE INDEX IF NOT EXISTS idx_snap_tau ON snapshots(tau_ms);
CREATE INDEX IF NOT EXISTS idx_snap_cond ON snapshots(condition_id, ts_ms);

CREATE TABLE IF NOT EXISTS btc_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    source TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_ts ON btc_prices(ts_ms, source);
"""


def _existing_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def ensure_database_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    existing_snapshot_cols = _existing_columns(conn, "snapshots")
    for column_name, column_type in SNAPSHOT_OPTIONAL_COLUMNS.items():
        if column_name in existing_snapshot_cols:
            continue
        conn.execute(
            f"ALTER TABLE snapshots ADD COLUMN {column_name} {column_type}"
        )
        log.info("Added snapshots.%s column via schema migration", column_name)
    conn.commit()


class Database:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def init(self) -> None:
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        # NOTE: check_same_thread=False is safe here because writes are funneled
        # through a single coroutine (DBWriter). Do not introduce parallel writers
        # against this same connection.
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        ensure_database_schema(self._conn)
        log.info("Database initialized at %s", self._db_path)

    def _get_conn(self) -> sqlite3.Connection:
        assert self._conn is not None, "Database not initialized"
        return self._conn

    def insert_market(self, data: dict) -> None:
        conn = self._get_conn()
        cols = list(data.keys())
        placeholders = ",".join("?" for _ in cols)
        col_str = ",".join(cols)
        conn.execute(
            f"INSERT OR REPLACE INTO markets ({col_str}) VALUES ({placeholders})",
            [data[c] for c in cols],
        )
        conn.commit()

    def update_market_resolved(self, condition_id: str, winning_token_id: str | None) -> None:
        conn = self._get_conn()
        conn.execute(
            "UPDATE markets SET resolved=1, active=0, winning_token_id=? WHERE condition_id=?",
            (winning_token_id, condition_id),
        )
        conn.commit()

    def insert_snapshots_batch(self, rows: list[dict]) -> None:
        if not rows:
            return
        conn = self._get_conn()
        cols = list(rows[0].keys())
        placeholders = ",".join("?" for _ in cols)
        col_str = ",".join(cols)
        conn.executemany(
            f"INSERT INTO snapshots ({col_str}) VALUES ({placeholders})",
            [[r[c] for c in cols] for r in rows],
        )
        conn.commit()

    def insert_btc_prices_batch(self, rows: list[dict]) -> None:
        if not rows:
            return
        conn = self._get_conn()
        conn.executemany(
            "INSERT INTO btc_prices (ts_ms, source, price) VALUES (?, ?, ?)",
            [(r["ts_ms"], r["source"], r["price"]) for r in rows],
        )
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def wal_checkpoint(self, mode: str = "PASSIVE") -> None:
        conn = self._get_conn()
        conn.execute(f"PRAGMA wal_checkpoint({mode})")
        conn.commit()


class DBWriter:
    """Single-writer coroutine that drains a queue and batch-inserts to SQLite."""

    def __init__(
        self,
        db: Database,
        batch_size: int = 100,
        flush_interval_s: float = 5.0,
        checkpoint_interval_s: float = 300.0,
    ):
        self._db = db
        self._batch_size = batch_size
        self._flush_interval_s = flush_interval_s
        self._checkpoint_interval_s = max(30.0, checkpoint_interval_s)
        self._last_checkpoint = time.monotonic()

    async def run(self, queue: asyncio.Queue[DBRow]) -> None:
        snapshot_buf: list[dict] = []
        btc_buf: list[dict] = []
        market_buf: list[dict] = []
        last_flush = time.monotonic()

        while True:
            try:
                # Drain up to batch_size items or wait up to flush_interval
                try:
                    row = await asyncio.wait_for(queue.get(), timeout=self._flush_interval_s)
                    self._route(row, snapshot_buf, btc_buf, market_buf)
                except asyncio.TimeoutError:
                    pass

                # Drain any remaining items without blocking
                while not queue.empty():
                    try:
                        row = queue.get_nowait()
                        self._route(row, snapshot_buf, btc_buf, market_buf)
                    except asyncio.QueueEmpty:
                        break

                total = len(snapshot_buf) + len(btc_buf) + len(market_buf)
                elapsed = time.monotonic() - last_flush
                if total >= self._batch_size or (total > 0 and elapsed >= self._flush_interval_s):
                    await self._flush(snapshot_buf, btc_buf, market_buf)
                    last_flush = time.monotonic()
                await self._maybe_checkpoint()

            except asyncio.CancelledError:
                # Drain remaining queue items before final flush
                while not queue.empty():
                    try:
                        row = queue.get_nowait()
                        self._route(row, snapshot_buf, btc_buf, market_buf)
                    except asyncio.QueueEmpty:
                        break
                await self._flush(snapshot_buf, btc_buf, market_buf)
                await self._maybe_checkpoint(force=True)
                log.info(
                    "DBWriter shutdown: drained queue, final flush complete"
                )
                raise
            except Exception:
                log.exception("DBWriter error, retrying")
                await asyncio.sleep(1)

    def _route(
        self,
        row: DBRow,
        snapshot_buf: list[dict],
        btc_buf: list[dict],
        market_buf: list[dict],
    ) -> None:
        if row.table == "snapshots":
            snapshot_buf.append(row.data)
        elif row.table == "btc_prices":
            btc_buf.append(row.data)
        elif row.table == "markets":
            market_buf.append(row.data)

    async def _flush(
        self,
        snapshot_buf: list[dict],
        btc_buf: list[dict],
        market_buf: list[dict],
    ) -> None:
        try:
            if market_buf:
                for m in market_buf:
                    self._db.insert_market(m)
                log.debug("Flushed %d market rows", len(market_buf))
                market_buf.clear()

            if snapshot_buf:
                self._db.insert_snapshots_batch(snapshot_buf)
                log.debug("Flushed %d snapshot rows", len(snapshot_buf))
                snapshot_buf.clear()

            if btc_buf:
                self._db.insert_btc_prices_batch(btc_buf)
                log.debug("Flushed %d btc_price rows", len(btc_buf))
                btc_buf.clear()
        except Exception:
            log.exception("Flush failed — data kept in buffer for retry")

    async def _maybe_checkpoint(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_checkpoint) < self._checkpoint_interval_s:
            return
        try:
            self._db.wal_checkpoint("PASSIVE")
            self._last_checkpoint = now
        except Exception:
            log.exception("WAL checkpoint failed")
