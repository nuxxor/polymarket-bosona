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

RANGE_SNAPSHOT_OPTIONAL_COLUMNS: dict[str, str] = {
    "tau_ms": "INTEGER",
    "center_order_index": "INTEGER",
    "band_distance": "INTEGER",
    "is_focus": "INTEGER",
    "btc_distance_to_lower": "REAL",
    "btc_distance_to_upper": "REAL",
    "btc_distance_to_band_mid": "REAL",
    "btc_position_in_band": "REAL",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS range_events (
    event_slug TEXT PRIMARY KEY,
    event_title TEXT NOT NULL,
    start_date_ms INTEGER NOT NULL,
    end_date_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    market_count INTEGER NOT NULL,
    resolution_text TEXT,
    source_url TEXT,
    discovered_at_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_range_events_end
ON range_events(end_date_ms);

CREATE TABLE IF NOT EXISTS range_markets (
    condition_id TEXT PRIMARY KEY,
    event_slug TEXT NOT NULL,
    question TEXT NOT NULL,
    group_item_title TEXT NOT NULL,
    yes_token_id TEXT NOT NULL,
    no_token_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    lower_bound REAL,
    upper_bound REAL,
    initial_yes_price REAL,
    initial_no_price REAL,
    capture_date_tsi TEXT NOT NULL,
    discovered_at_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_range_markets_event_order
ON range_markets(event_slug, order_index);

CREATE TABLE IF NOT EXISTS range_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    event_slug TEXT NOT NULL,
    event_title TEXT NOT NULL,
    event_end_ms INTEGER NOT NULL,
    tau_ms INTEGER,
    center_condition_id TEXT NOT NULL,
    center_order_index INTEGER,
    focus_role TEXT NOT NULL,
    focus_rank INTEGER NOT NULL,
    band_distance INTEGER,
    is_focus INTEGER,
    selection_reason TEXT NOT NULL,
    condition_id TEXT NOT NULL,
    question TEXT NOT NULL,
    group_item_title TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    lower_bound REAL,
    upper_bound REAL,
    btc_price_binance REAL,
    btc_distance_to_lower REAL,
    btc_distance_to_upper REAL,
    btc_distance_to_band_mid REAL,
    btc_position_in_band REAL,
    yes_best_bid REAL,
    yes_best_ask REAL,
    yes_mid REAL,
    yes_spread REAL,
    yes_bid_depth_usd REAL,
    yes_ask_depth_usd REAL,
    yes_depth_ok INTEGER NOT NULL,
    no_best_bid REAL,
    no_best_ask REAL,
    no_mid REAL,
    no_spread REAL,
    no_bid_depth_usd REAL,
    no_ask_depth_usd REAL,
    no_depth_ok INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_range_snapshots_event_ts
ON range_snapshots(event_slug, ts_ms);

CREATE INDEX IF NOT EXISTS idx_range_snapshots_center_ts
ON range_snapshots(center_condition_id, ts_ms);

CREATE INDEX IF NOT EXISTS idx_range_snapshots_role_ts
ON range_snapshots(focus_role, ts_ms);

CREATE TABLE IF NOT EXISTS range_focus_orderbooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    event_slug TEXT NOT NULL,
    center_condition_id TEXT NOT NULL,
    condition_id TEXT NOT NULL,
    focus_role TEXT NOT NULL,
    outcome TEXT NOT NULL,
    token_id TEXT NOT NULL,
    book_last_update_ts_ms INTEGER,
    best_bid REAL,
    best_ask REAL,
    bid_levels_json TEXT NOT NULL,
    ask_levels_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_range_focus_orderbooks_ts
ON range_focus_orderbooks(ts_ms, focus_role, outcome);

CREATE TABLE IF NOT EXISTS range_focus_orderbook_deltas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    event_slug TEXT NOT NULL,
    center_condition_id TEXT NOT NULL,
    condition_id TEXT NOT NULL,
    focus_role TEXT NOT NULL,
    outcome TEXT NOT NULL,
    token_id TEXT NOT NULL,
    book_last_update_ts_ms INTEGER,
    best_bid REAL,
    best_ask REAL,
    best_bid_delta REAL,
    best_ask_delta REAL,
    spread REAL,
    spread_delta REAL,
    bid_depth_usd_2c REAL,
    ask_depth_usd_2c REAL,
    bid_depth_delta_2c REAL,
    ask_depth_delta_2c REAL,
    bid_refill_usd_2c REAL,
    ask_refill_usd_2c REAL,
    bid_cancel_usd_2c REAL,
    ask_cancel_usd_2c REAL,
    bid_depth_usd_5c REAL,
    ask_depth_usd_5c REAL,
    bid_depth_delta_5c REAL,
    ask_depth_delta_5c REAL,
    bid_refill_usd_5c REAL,
    ask_refill_usd_5c REAL,
    bid_cancel_usd_5c REAL,
    ask_cancel_usd_5c REAL,
    seconds_since_prev REAL
);

CREATE INDEX IF NOT EXISTS idx_range_focus_orderbook_deltas_ts
ON range_focus_orderbook_deltas(ts_ms, focus_role, outcome);

CREATE TABLE IF NOT EXISTS range_state_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    event_slug TEXT NOT NULL,
    event_title TEXT NOT NULL,
    event_end_ms INTEGER NOT NULL,
    tau_ms INTEGER,
    selection_reason TEXT NOT NULL,
    btc_price_binance REAL,
    center_condition_id TEXT NOT NULL,
    center_label TEXT NOT NULL,
    center_order_index INTEGER NOT NULL,
    center_lower_bound REAL,
    center_upper_bound REAL,
    btc_distance_to_lower REAL,
    btc_distance_to_upper REAL,
    btc_distance_to_band_mid REAL,
    btc_position_in_band REAL,
    lower_condition_id TEXT,
    lower_label TEXT,
    lower_yes_mid REAL,
    lower_no_mid REAL,
    lower_yes_plus_no_mid REAL,
    center_yes_mid REAL,
    center_no_mid REAL,
    center_yes_plus_no_mid REAL,
    upper_condition_id TEXT,
    upper_label TEXT,
    upper_yes_mid REAL,
    upper_no_mid REAL,
    upper_yes_plus_no_mid REAL,
    upper_minus_lower_yes_mid REAL,
    upper_minus_lower_no_mid REAL,
    center_minus_lower_yes_mid REAL,
    upper_minus_center_yes_mid REAL,
    center_minus_lower_no_mid REAL,
    upper_minus_center_no_mid REAL,
    wing_yes_mid_sum REAL,
    wing_no_mid_sum REAL,
    wing_yes_symmetry_abs REAL,
    wing_no_symmetry_abs REAL
);

CREATE INDEX IF NOT EXISTS idx_range_state_features_event_ts
ON range_state_features(event_slug, ts_ms);

CREATE TABLE IF NOT EXISTS collector_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    note_type TEXT NOT NULL,
    status TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    reason_detail TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_collector_notes_ts
ON collector_notes(ts_ms);

CREATE TABLE IF NOT EXISTS btc_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    source TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_prices_ts
ON btc_prices(ts_ms, source);

CREATE TABLE IF NOT EXISTS btc_spot_klines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume_base REAL NOT NULL,
    volume_quote REAL NOT NULL,
    trade_count INTEGER NOT NULL,
    taker_buy_base REAL NOT NULL,
    taker_buy_quote REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_spot_klines_ts
ON btc_spot_klines(ts_ms, symbol, interval);

CREATE TABLE IF NOT EXISTS btc_spot_orderbook_depth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    levels INTEGER NOT NULL,
    last_update_id INTEGER,
    best_bid REAL,
    best_ask REAL,
    mid REAL,
    spread_bps REAL,
    bid_depth_usd_5 REAL,
    ask_depth_usd_5 REAL,
    imbalance_5 REAL,
    bid_depth_usd_10 REAL,
    ask_depth_usd_10 REAL,
    imbalance_10 REAL,
    bid_levels_json TEXT NOT NULL,
    ask_levels_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_spot_orderbook_depth_ts
ON btc_spot_orderbook_depth(ts_ms, symbol);

CREATE TABLE IF NOT EXISTS btc_ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    price REAL,
    best_bid REAL,
    best_ask REAL,
    mid REAL,
    spread_bps REAL,
    trade_count_5s INTEGER NOT NULL,
    buy_notional_5s REAL NOT NULL,
    sell_notional_5s REAL NOT NULL,
    trade_imbalance_5s REAL NOT NULL,
    trade_count_15s INTEGER NOT NULL,
    buy_notional_15s REAL NOT NULL,
    sell_notional_15s REAL NOT NULL,
    trade_imbalance_15s REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_ticks_ts
ON btc_ticks(ts_ms);

CREATE TABLE IF NOT EXISTS btc_futures_open_interest (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    open_interest REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_futures_open_interest_ts
ON btc_futures_open_interest(ts_ms, symbol);

CREATE TABLE IF NOT EXISTS btc_futures_regime_5m (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    period TEXT NOT NULL,
    open_interest_hist_ts_ms INTEGER,
    sum_open_interest REAL,
    sum_open_interest_value REAL,
    global_long_short_ts_ms INTEGER,
    global_long_short_ratio REAL,
    global_long_account REAL,
    global_short_account REAL,
    top_trader_account_ts_ms INTEGER,
    top_trader_account_ratio REAL,
    top_trader_account_long REAL,
    top_trader_account_short REAL,
    top_trader_position_ts_ms INTEGER,
    top_trader_position_ratio REAL,
    top_trader_position_long REAL,
    top_trader_position_short REAL,
    taker_buy_sell_ts_ms INTEGER,
    taker_buy_sell_ratio REAL,
    taker_buy_vol REAL,
    taker_sell_vol REAL
);

CREATE INDEX IF NOT EXISTS idx_btc_futures_regime_5m_ts
ON btc_futures_regime_5m(fetched_ts_ms, symbol, period);

CREATE TABLE IF NOT EXISTS btc_futures_orderbook_depth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    levels INTEGER NOT NULL,
    first_update_id INTEGER,
    final_update_id INTEGER,
    prev_final_update_id INTEGER,
    transaction_ts_ms INTEGER,
    best_bid REAL,
    best_ask REAL,
    mid REAL,
    spread_bps REAL,
    bid_depth_usd_5 REAL,
    ask_depth_usd_5 REAL,
    imbalance_5 REAL,
    bid_depth_usd_10 REAL,
    ask_depth_usd_10 REAL,
    imbalance_10 REAL,
    bid_levels_json TEXT NOT NULL,
    ask_levels_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_futures_orderbook_depth_ts
ON btc_futures_orderbook_depth(ts_ms, symbol);

CREATE TABLE IF NOT EXISTS btc_futures_mark_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    mark_price REAL,
    mark_price_ma REAL,
    index_price REAL,
    estimated_settle_price REAL,
    funding_rate REAL,
    next_funding_time_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_btc_futures_mark_prices_ts
ON btc_futures_mark_prices(ts_ms, symbol);

CREATE TABLE IF NOT EXISTS btc_futures_klines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    open_time_ms INTEGER NOT NULL,
    close_time_ms INTEGER NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume_base REAL NOT NULL,
    volume_quote REAL NOT NULL,
    trade_count INTEGER NOT NULL,
    taker_buy_base REAL NOT NULL,
    taker_buy_quote REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_futures_klines_ts
ON btc_futures_klines(ts_ms, symbol, interval);

CREATE TABLE IF NOT EXISTS btc_futures_micro_ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    price REAL,
    trade_ts_ms INTEGER,
    trade_count_5s INTEGER NOT NULL,
    buy_notional_5s REAL NOT NULL,
    sell_notional_5s REAL NOT NULL,
    trade_imbalance_5s REAL NOT NULL,
    trade_count_15s INTEGER NOT NULL,
    buy_notional_15s REAL NOT NULL,
    sell_notional_15s REAL NOT NULL,
    trade_imbalance_15s REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_btc_futures_micro_ticks_ts
ON btc_futures_micro_ticks(ts_ms, symbol);

CREATE TABLE IF NOT EXISTS btc_futures_liquidations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT,
    order_type TEXT,
    time_in_force TEXT,
    original_qty REAL,
    price REAL,
    average_price REAL,
    status TEXT,
    last_filled_qty REAL,
    filled_qty REAL,
    trade_ts_ms INTEGER,
    notional_usd REAL
);

CREATE INDEX IF NOT EXISTS idx_btc_futures_liquidations_ts
ON btc_futures_liquidations(ts_ms, symbol);

CREATE TABLE IF NOT EXISTS deribit_index_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    source TEXT NOT NULL,
    index_name TEXT NOT NULL,
    index_price REAL,
    estimated_delivery_price REAL
);

CREATE INDEX IF NOT EXISTS idx_deribit_index_prices_ts
ON deribit_index_prices(ts_ms, index_name);

CREATE TABLE IF NOT EXISTS ny_open_gate_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    capture_date_tsi TEXT NOT NULL,
    trade_date_ny TEXT NOT NULL,
    event_slug TEXT,
    event_title TEXT,
    ny_open_ts_ms INTEGER NOT NULL,
    minutes_from_open REAL NOT NULL,
    gate_phase TEXT NOT NULL,
    btc_price_binance REAL NOT NULL,
    nearest_odd_thousand REAL NOT NULL,
    abs_distance_to_odd_thousand REAL NOT NULL,
    return_15m_bps REAL,
    range_15m_abs REAL,
    realized_vol_15m_bps REAL,
    max_abs_excursion_15m_abs REAL,
    return_60m_bps REAL,
    range_60m_abs REAL,
    realized_vol_60m_bps REAL,
    max_abs_excursion_60m_abs REAL,
    return_180m_bps REAL,
    range_180m_abs REAL,
    realized_vol_180m_bps REAL,
    max_abs_excursion_180m_abs REAL,
    spot_best_bid REAL,
    spot_best_ask REAL,
    spot_mid REAL,
    spot_spread_bps REAL,
    trade_count_5s INTEGER NOT NULL,
    buy_notional_5s REAL NOT NULL,
    sell_notional_5s REAL NOT NULL,
    trade_imbalance_5s REAL NOT NULL,
    trade_count_15s INTEGER NOT NULL,
    buy_notional_15s REAL NOT NULL,
    sell_notional_15s REAL NOT NULL,
    trade_imbalance_15s REAL NOT NULL,
    spot_volume_base_1m REAL,
    spot_volume_quote_1m REAL,
    spot_trade_count_1m INTEGER,
    spot_taker_buy_quote_1m REAL,
    spot_taker_buy_ratio_1m REAL,
    spot_volume_quote_5m REAL,
    spot_trade_count_5m INTEGER,
    spot_taker_buy_ratio_5m REAL,
    futures_open_interest REAL,
    futures_open_interest_delta_15m REAL,
    futures_sum_open_interest REAL,
    futures_sum_open_interest_value REAL,
    futures_global_long_short_ratio REAL,
    futures_top_trader_account_ratio REAL,
    futures_top_trader_position_ratio REAL,
    futures_taker_buy_sell_ratio REAL,
    center_label TEXT,
    center_lower_bound REAL,
    center_upper_bound REAL,
    center_yes_mid REAL,
    center_no_mid REAL,
    lower_yes_mid REAL,
    lower_no_mid REAL,
    upper_yes_mid REAL,
    upper_no_mid REAL,
    wing_yes_symmetry_abs REAL,
    wing_no_symmetry_abs REAL,
    btc_distance_to_lower REAL,
    btc_distance_to_upper REAL,
    btc_distance_to_band_mid REAL,
    btc_position_in_band REAL
);

CREATE INDEX IF NOT EXISTS idx_ny_open_gate_snapshots_ts
ON ny_open_gate_snapshots(ts_ms, trade_date_ny);

CREATE TABLE IF NOT EXISTS ny_open_gate_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date_ny TEXT NOT NULL UNIQUE,
    capture_date_tsi TEXT NOT NULL,
    event_slug TEXT,
    event_title TEXT,
    ny_open_ts_ms INTEGER NOT NULL,
    open_price_binance REAL NOT NULL,
    open_center_label TEXT,
    open_center_lower_bound REAL,
    open_center_upper_bound REAL,
    open_center_yes_mid REAL,
    open_center_no_mid REAL,
    open_distance_to_lower REAL,
    open_distance_to_upper REAL,
    max_abs_move_30m REAL,
    max_abs_return_30m_bps REAL,
    range_30m_abs REAL,
    range_30m_bps REAL,
    realized_vol_30m_bps REAL,
    min_distance_to_edge_30m REAL,
    crossed_outside_center_30m INTEGER,
    max_abs_move_60m REAL,
    max_abs_return_60m_bps REAL,
    range_60m_abs REAL,
    range_60m_bps REAL,
    realized_vol_60m_bps REAL,
    min_distance_to_edge_60m REAL,
    crossed_outside_center_60m INTEGER,
    max_abs_move_90m REAL,
    max_abs_return_90m_bps REAL,
    range_90m_abs REAL,
    range_90m_bps REAL,
    realized_vol_90m_bps REAL,
    min_distance_to_edge_90m REAL,
    crossed_outside_center_90m INTEGER
);

CREATE INDEX IF NOT EXISTS idx_ny_open_gate_outcomes_open_ts
ON ny_open_gate_outcomes(ny_open_ts_ms);
"""


def _existing_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


class DailyRangeDatabase:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def init(self) -> None:
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(SCHEMA)
        existing_snapshot_cols = _existing_columns(self._conn, "range_snapshots")
        for column_name, column_type in RANGE_SNAPSHOT_OPTIONAL_COLUMNS.items():
            if column_name in existing_snapshot_cols:
                continue
            self._conn.execute(
                f"ALTER TABLE range_snapshots ADD COLUMN {column_name} {column_type}"
            )
            log.info("Added range_snapshots.%s column via schema migration", column_name)
        self._conn.commit()
        log.info("Daily range database initialized at %s", self._db_path)

    def _get_conn(self) -> sqlite3.Connection:
        assert self._conn is not None, "Database not initialized"
        return self._conn

    def upsert_range_events(self, rows: list[dict]) -> None:
        if not rows:
            return
        conn = self._get_conn()
        conn.executemany(
            """
            INSERT OR REPLACE INTO range_events (
                event_slug,
                event_title,
                start_date_ms,
                end_date_ms,
                capture_date_tsi,
                market_count,
                resolution_text,
                source_url,
                discovered_at_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["event_slug"],
                    row["event_title"],
                    row["start_date_ms"],
                    row["end_date_ms"],
                    row["capture_date_tsi"],
                    row["market_count"],
                    row.get("resolution_text"),
                    row.get("source_url"),
                    row["discovered_at_ms"],
                )
                for row in rows
            ],
        )
        conn.commit()

    def upsert_range_markets(self, rows: list[dict]) -> None:
        if not rows:
            return
        conn = self._get_conn()
        conn.executemany(
            """
            INSERT OR REPLACE INTO range_markets (
                condition_id,
                event_slug,
                question,
                group_item_title,
                yes_token_id,
                no_token_id,
                order_index,
                lower_bound,
                upper_bound,
                initial_yes_price,
                initial_no_price,
                capture_date_tsi,
                discovered_at_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["condition_id"],
                    row["event_slug"],
                    row["question"],
                    row["group_item_title"],
                    row["yes_token_id"],
                    row["no_token_id"],
                    row["order_index"],
                    row.get("lower_bound"),
                    row.get("upper_bound"),
                    row.get("initial_yes_price"),
                    row.get("initial_no_price"),
                    row["capture_date_tsi"],
                    row["discovered_at_ms"],
                )
                for row in rows
            ],
        )
        conn.commit()

    def insert_rows_batch(self, table_name: str, rows: list[dict]) -> None:
        if not rows:
            return
        conn = self._get_conn()
        cols = list(rows[0].keys())
        placeholders = ",".join("?" for _ in cols)
        col_str = ",".join(cols)
        conn.executemany(
            f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})",
            [[row[col] for col in cols] for row in rows],
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


class DailyRangeDBWriter:
    """Single-writer coroutine for the daily BTC range collector."""

    def __init__(
        self,
        db: DailyRangeDatabase,
        batch_size: int = 100,
        flush_interval_s: float = 5.0,
        checkpoint_interval_s: float = 300.0,
    ) -> None:
        self._db = db
        self._batch_size = batch_size
        self._flush_interval_s = flush_interval_s
        self._checkpoint_interval_s = max(30.0, checkpoint_interval_s)
        self._last_checkpoint = time.monotonic()

    async def run(self, queue: asyncio.Queue[DBRow]) -> None:
        event_buf: list[dict] = []
        market_buf: list[dict] = []
        snapshot_buf: list[dict] = []
        focus_orderbook_buf: list[dict] = []
        focus_orderbook_delta_buf: list[dict] = []
        state_feature_buf: list[dict] = []
        note_buf: list[dict] = []
        btc_price_buf: list[dict] = []
        btc_spot_kline_buf: list[dict] = []
        btc_spot_depth_buf: list[dict] = []
        btc_tick_buf: list[dict] = []
        futures_oi_buf: list[dict] = []
        futures_regime_buf: list[dict] = []
        futures_orderbook_depth_buf: list[dict] = []
        futures_mark_price_buf: list[dict] = []
        futures_kline_buf: list[dict] = []
        futures_micro_tick_buf: list[dict] = []
        futures_liquidation_buf: list[dict] = []
        deribit_index_price_buf: list[dict] = []
        gate_snapshot_buf: list[dict] = []
        gate_outcome_buf: list[dict] = []
        last_flush = time.monotonic()

        while True:
            try:
                try:
                    row = await asyncio.wait_for(queue.get(), timeout=self._flush_interval_s)
                    self._route(
                        row,
                        event_buf,
                        market_buf,
                        snapshot_buf,
                        focus_orderbook_buf,
                        focus_orderbook_delta_buf,
                        state_feature_buf,
                        note_buf,
                        btc_price_buf,
                        btc_spot_kline_buf,
                        btc_spot_depth_buf,
                        btc_tick_buf,
                        futures_oi_buf,
                        futures_regime_buf,
                        futures_orderbook_depth_buf,
                        futures_mark_price_buf,
                        futures_kline_buf,
                        futures_micro_tick_buf,
                        futures_liquidation_buf,
                        deribit_index_price_buf,
                        gate_snapshot_buf,
                        gate_outcome_buf,
                    )
                except asyncio.TimeoutError:
                    pass

                while not queue.empty():
                    try:
                        row = queue.get_nowait()
                        self._route(
                            row,
                            event_buf,
                            market_buf,
                            snapshot_buf,
                            focus_orderbook_buf,
                            focus_orderbook_delta_buf,
                            state_feature_buf,
                            note_buf,
                            btc_price_buf,
                            btc_spot_kline_buf,
                            btc_spot_depth_buf,
                            btc_tick_buf,
                            futures_oi_buf,
                            futures_regime_buf,
                            futures_orderbook_depth_buf,
                            futures_mark_price_buf,
                            futures_kline_buf,
                            futures_micro_tick_buf,
                            futures_liquidation_buf,
                            deribit_index_price_buf,
                            gate_snapshot_buf,
                            gate_outcome_buf,
                        )
                    except asyncio.QueueEmpty:
                        break

                total = (
                    len(event_buf)
                    + len(market_buf)
                    + len(snapshot_buf)
                    + len(focus_orderbook_buf)
                    + len(focus_orderbook_delta_buf)
                    + len(state_feature_buf)
                    + len(note_buf)
                    + len(btc_price_buf)
                    + len(btc_spot_kline_buf)
                    + len(btc_spot_depth_buf)
                    + len(btc_tick_buf)
                    + len(futures_oi_buf)
                    + len(futures_regime_buf)
                    + len(futures_orderbook_depth_buf)
                    + len(futures_mark_price_buf)
                    + len(futures_kline_buf)
                    + len(futures_micro_tick_buf)
                    + len(futures_liquidation_buf)
                    + len(deribit_index_price_buf)
                    + len(gate_snapshot_buf)
                    + len(gate_outcome_buf)
                )
                elapsed = time.monotonic() - last_flush
                if total >= self._batch_size or (total > 0 and elapsed >= self._flush_interval_s):
                    await self._flush(
                        event_buf,
                        market_buf,
                        snapshot_buf,
                        focus_orderbook_buf,
                        focus_orderbook_delta_buf,
                        state_feature_buf,
                        note_buf,
                        btc_price_buf,
                        btc_spot_kline_buf,
                        btc_spot_depth_buf,
                        btc_tick_buf,
                        futures_oi_buf,
                        futures_regime_buf,
                        futures_orderbook_depth_buf,
                        futures_mark_price_buf,
                        futures_kline_buf,
                        futures_micro_tick_buf,
                        futures_liquidation_buf,
                        deribit_index_price_buf,
                        gate_snapshot_buf,
                        gate_outcome_buf,
                    )
                    last_flush = time.monotonic()
                await self._maybe_checkpoint()

            except asyncio.CancelledError:
                while not queue.empty():
                    try:
                        row = queue.get_nowait()
                        self._route(
                            row,
                            event_buf,
                            market_buf,
                            snapshot_buf,
                            focus_orderbook_buf,
                            focus_orderbook_delta_buf,
                            state_feature_buf,
                            note_buf,
                            btc_price_buf,
                            btc_spot_kline_buf,
                            btc_spot_depth_buf,
                            btc_tick_buf,
                            futures_oi_buf,
                            futures_regime_buf,
                            futures_orderbook_depth_buf,
                            futures_mark_price_buf,
                            futures_kline_buf,
                            futures_micro_tick_buf,
                            futures_liquidation_buf,
                            deribit_index_price_buf,
                            gate_snapshot_buf,
                            gate_outcome_buf,
                        )
                    except asyncio.QueueEmpty:
                        break
                await self._flush(
                    event_buf,
                    market_buf,
                    snapshot_buf,
                    focus_orderbook_buf,
                    focus_orderbook_delta_buf,
                    state_feature_buf,
                    note_buf,
                    btc_price_buf,
                    btc_spot_kline_buf,
                    btc_spot_depth_buf,
                    btc_tick_buf,
                    futures_oi_buf,
                    futures_regime_buf,
                    futures_orderbook_depth_buf,
                    futures_mark_price_buf,
                    futures_kline_buf,
                    futures_micro_tick_buf,
                    futures_liquidation_buf,
                    deribit_index_price_buf,
                    gate_snapshot_buf,
                    gate_outcome_buf,
                )
                await self._maybe_checkpoint(force=True)
                log.info("DailyRangeDBWriter shutdown complete")
                raise
            except Exception:
                log.exception("DailyRangeDBWriter error, retrying")
                await asyncio.sleep(1)

    def _route(
        self,
        row: DBRow,
        event_buf: list[dict],
        market_buf: list[dict],
        snapshot_buf: list[dict],
        focus_orderbook_buf: list[dict],
        focus_orderbook_delta_buf: list[dict],
        state_feature_buf: list[dict],
        note_buf: list[dict],
        btc_price_buf: list[dict],
        btc_spot_kline_buf: list[dict],
        btc_spot_depth_buf: list[dict],
        btc_tick_buf: list[dict],
        futures_oi_buf: list[dict],
        futures_regime_buf: list[dict],
        futures_orderbook_depth_buf: list[dict],
        futures_mark_price_buf: list[dict],
        futures_kline_buf: list[dict],
        futures_micro_tick_buf: list[dict],
        futures_liquidation_buf: list[dict],
        deribit_index_price_buf: list[dict],
        gate_snapshot_buf: list[dict],
        gate_outcome_buf: list[dict],
    ) -> None:
        if row.table == "range_events":
            event_buf.append(row.data)
        elif row.table == "range_markets":
            market_buf.append(row.data)
        elif row.table == "range_snapshots":
            snapshot_buf.append(row.data)
        elif row.table == "range_focus_orderbooks":
            focus_orderbook_buf.append(row.data)
        elif row.table == "range_focus_orderbook_deltas":
            focus_orderbook_delta_buf.append(row.data)
        elif row.table == "range_state_features":
            state_feature_buf.append(row.data)
        elif row.table == "collector_notes":
            note_buf.append(row.data)
        elif row.table == "btc_prices":
            btc_price_buf.append(row.data)
        elif row.table == "btc_spot_klines":
            btc_spot_kline_buf.append(row.data)
        elif row.table == "btc_spot_orderbook_depth":
            btc_spot_depth_buf.append(row.data)
        elif row.table == "btc_ticks":
            btc_tick_buf.append(row.data)
        elif row.table == "btc_futures_open_interest":
            futures_oi_buf.append(row.data)
        elif row.table == "btc_futures_regime_5m":
            futures_regime_buf.append(row.data)
        elif row.table == "btc_futures_orderbook_depth":
            futures_orderbook_depth_buf.append(row.data)
        elif row.table == "btc_futures_mark_prices":
            futures_mark_price_buf.append(row.data)
        elif row.table == "btc_futures_klines":
            futures_kline_buf.append(row.data)
        elif row.table == "btc_futures_micro_ticks":
            futures_micro_tick_buf.append(row.data)
        elif row.table == "btc_futures_liquidations":
            futures_liquidation_buf.append(row.data)
        elif row.table == "deribit_index_prices":
            deribit_index_price_buf.append(row.data)
        elif row.table == "ny_open_gate_snapshots":
            gate_snapshot_buf.append(row.data)
        elif row.table == "ny_open_gate_outcomes":
            gate_outcome_buf.append(row.data)

    async def _flush(
        self,
        event_buf: list[dict],
        market_buf: list[dict],
        snapshot_buf: list[dict],
        focus_orderbook_buf: list[dict],
        focus_orderbook_delta_buf: list[dict],
        state_feature_buf: list[dict],
        note_buf: list[dict],
        btc_price_buf: list[dict],
        btc_spot_kline_buf: list[dict],
        btc_spot_depth_buf: list[dict],
        btc_tick_buf: list[dict],
        futures_oi_buf: list[dict],
        futures_regime_buf: list[dict],
        futures_orderbook_depth_buf: list[dict],
        futures_mark_price_buf: list[dict],
        futures_kline_buf: list[dict],
        futures_micro_tick_buf: list[dict],
        futures_liquidation_buf: list[dict],
        deribit_index_price_buf: list[dict],
        gate_snapshot_buf: list[dict],
        gate_outcome_buf: list[dict],
    ) -> None:
        try:
            if event_buf:
                self._db.upsert_range_events(event_buf)
                event_buf.clear()
            if market_buf:
                self._db.upsert_range_markets(market_buf)
                market_buf.clear()
            if snapshot_buf:
                self._db.insert_rows_batch("range_snapshots", snapshot_buf)
                snapshot_buf.clear()
            if focus_orderbook_buf:
                self._db.insert_rows_batch("range_focus_orderbooks", focus_orderbook_buf)
                focus_orderbook_buf.clear()
            if focus_orderbook_delta_buf:
                self._db.insert_rows_batch(
                    "range_focus_orderbook_deltas",
                    focus_orderbook_delta_buf,
                )
                focus_orderbook_delta_buf.clear()
            if state_feature_buf:
                self._db.insert_rows_batch("range_state_features", state_feature_buf)
                state_feature_buf.clear()
            if note_buf:
                self._db.insert_rows_batch("collector_notes", note_buf)
                note_buf.clear()
            if btc_price_buf:
                self._db.insert_rows_batch("btc_prices", btc_price_buf)
                btc_price_buf.clear()
            if btc_spot_kline_buf:
                self._db.insert_rows_batch("btc_spot_klines", btc_spot_kline_buf)
                btc_spot_kline_buf.clear()
            if btc_spot_depth_buf:
                self._db.insert_rows_batch("btc_spot_orderbook_depth", btc_spot_depth_buf)
                btc_spot_depth_buf.clear()
            if btc_tick_buf:
                self._db.insert_rows_batch("btc_ticks", btc_tick_buf)
                btc_tick_buf.clear()
            if futures_oi_buf:
                self._db.insert_rows_batch("btc_futures_open_interest", futures_oi_buf)
                futures_oi_buf.clear()
            if futures_regime_buf:
                self._db.insert_rows_batch("btc_futures_regime_5m", futures_regime_buf)
                futures_regime_buf.clear()
            if futures_orderbook_depth_buf:
                self._db.insert_rows_batch(
                    "btc_futures_orderbook_depth",
                    futures_orderbook_depth_buf,
                )
                futures_orderbook_depth_buf.clear()
            if futures_mark_price_buf:
                self._db.insert_rows_batch("btc_futures_mark_prices", futures_mark_price_buf)
                futures_mark_price_buf.clear()
            if futures_kline_buf:
                self._db.insert_rows_batch("btc_futures_klines", futures_kline_buf)
                futures_kline_buf.clear()
            if futures_micro_tick_buf:
                self._db.insert_rows_batch("btc_futures_micro_ticks", futures_micro_tick_buf)
                futures_micro_tick_buf.clear()
            if futures_liquidation_buf:
                self._db.insert_rows_batch(
                    "btc_futures_liquidations",
                    futures_liquidation_buf,
                )
                futures_liquidation_buf.clear()
            if deribit_index_price_buf:
                self._db.insert_rows_batch("deribit_index_prices", deribit_index_price_buf)
                deribit_index_price_buf.clear()
            if gate_snapshot_buf:
                self._db.insert_rows_batch("ny_open_gate_snapshots", gate_snapshot_buf)
                gate_snapshot_buf.clear()
            if gate_outcome_buf:
                self._db.insert_rows_batch("ny_open_gate_outcomes", gate_outcome_buf)
                gate_outcome_buf.clear()
        except Exception:
            log.exception("DailyRangeDBWriter flush failed")

    async def _maybe_checkpoint(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_checkpoint) < self._checkpoint_interval_s:
            return
        try:
            self._db.wal_checkpoint("PASSIVE")
            self._last_checkpoint = now
        except Exception:
            log.exception("DailyRangeDBWriter checkpoint failed")
