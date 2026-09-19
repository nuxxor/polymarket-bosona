from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from polymarket_bot.storage.database import ensure_database_schema


MARKET_DURATION_MS = 300_000


@dataclass(slots=True)
class OutcomeDatasetConfig:
    min_tau_frac: float = 0.12
    max_tau_frac: float = 0.90
    sample_every_s: int = 5
    limit_conditions: int | None = None
    skip_tail_conditions: int = 0


@dataclass(slots=True)
class WalkForwardFold:
    fold: int
    test_start_ms: int
    test_end_ms: int
    train_conditions: int
    test_conditions: int
    train_rows: int
    test_rows: int


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Analysis queries build temp tables / sorts; keep them in memory so they
    # do not depend on opening extra temp SQLite files in the environment.
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA busy_timeout=5000")
    ensure_database_schema(conn)
    return conn


def infer_winning_token_from_last_snapshot(
    conn: sqlite3.Connection,
    condition_id: str,
    yes_token_id: str,
    no_token_id: str,
) -> str | None:
    q = """
    SELECT token_id, vwap_bid_100, vwap_ask_100, mid_100, best_bid, best_ask
    FROM snapshots
    WHERE condition_id = ?
      AND ts_ms = (SELECT MAX(ts_ms) FROM snapshots WHERE condition_id = ?)
    """
    rows = conn.execute(q, (condition_id, condition_id)).fetchall()
    if not rows:
        return None

    yes_bid = yes_ask = yes_mid = None
    no_bid = no_ask = no_mid = None
    yes_best_bid = yes_best_ask = None
    no_best_bid = no_best_ask = None
    for r in rows:
        token = str(r["token_id"])
        bid = float(r["vwap_bid_100"]) if r["vwap_bid_100"] is not None else None
        ask = float(r["vwap_ask_100"]) if r["vwap_ask_100"] is not None else None
        mid = float(r["mid_100"]) if r["mid_100"] is not None else None
        best_bid = float(r["best_bid"]) if r["best_bid"] is not None else None
        best_ask = float(r["best_ask"]) if r["best_ask"] is not None else None
        if token == yes_token_id:
            yes_bid, yes_ask, yes_mid = bid, ask, mid
            yes_best_bid, yes_best_ask = best_bid, best_ask
        elif token == no_token_id:
            no_bid, no_ask, no_mid = bid, ask, mid
            no_best_bid, no_best_ask = best_bid, best_ask

    if yes_bid is not None and yes_bid >= 0.98:
        return yes_token_id
    if no_bid is not None and no_bid >= 0.98:
        return no_token_id
    if yes_best_bid is not None and yes_best_bid >= 0.98:
        return yes_token_id
    if no_best_bid is not None and no_best_bid >= 0.98:
        return no_token_id
    if no_ask is not None and no_ask <= 0.02:
        return yes_token_id
    if yes_ask is not None and yes_ask <= 0.02:
        return no_token_id
    if no_best_ask is not None and no_best_ask <= 0.02:
        return yes_token_id
    if yes_best_ask is not None and yes_best_ask <= 0.02:
        return no_token_id
    if yes_best_bid is not None and no_best_bid is not None:
        if yes_best_bid >= 0.95 and no_best_bid <= 0.05:
            return yes_token_id
        if no_best_bid >= 0.95 and yes_best_bid <= 0.05:
            return no_token_id
    if yes_mid is not None and no_mid is not None:
        return yes_token_id if yes_mid >= no_mid else no_token_id
    return None


def _slice_condition_window(
    markets: pd.DataFrame,
    *,
    limit_conditions: int | None,
    skip_tail_conditions: int,
) -> pd.DataFrame:
    if markets.empty:
        return markets.copy()
    sliced = markets.copy()
    skip_n = max(0, int(skip_tail_conditions))
    if skip_n > 0:
        if skip_n >= len(sliced):
            return sliced.iloc[0:0].copy()
        sliced = sliced.iloc[:-skip_n].reset_index(drop=True)
    if limit_conditions is not None and limit_conditions > 0:
        sliced = sliced.tail(limit_conditions).reset_index(drop=True)
    return sliced


def _resolved_market_frame(
    conn: sqlite3.Connection,
    limit_conditions: int | None,
    skip_tail_conditions: int = 0,
) -> pd.DataFrame:
    markets = pd.read_sql_query(
        """
        SELECT
            condition_id,
            yes_token_id,
            no_token_id,
            start_date_ms,
            end_date_ms,
            winning_token_id,
            resolved
        FROM markets
        WHERE duration_seconds = 300
          AND resolved = 1
        ORDER BY end_date_ms ASC, condition_id ASC
        """,
        conn,
    )
    if markets.empty:
        return markets
    markets = _slice_condition_window(
        markets,
        limit_conditions=limit_conditions,
        skip_tail_conditions=skip_tail_conditions,
    )
    if markets.empty:
        return markets

    winners: list[str | None] = []
    for row in markets.itertuples(index=False):
        winner = str(row.winning_token_id or "").strip() or None
        if winner is None:
            winner = infer_winning_token_from_last_snapshot(
                conn,
                condition_id=row.condition_id,
                yes_token_id=row.yes_token_id,
                no_token_id=row.no_token_id,
            )
        winners.append(winner)

    markets["effective_winning_token_id"] = winners
    markets = markets[markets["effective_winning_token_id"].notna()].copy()
    markets["target_yes"] = (
        markets["effective_winning_token_id"].astype(str) == markets["yes_token_id"].astype(str)
    ).astype(int)
    return markets.reset_index(drop=True)


def _stage_outcome_markets(conn: sqlite3.Connection, markets: pd.DataFrame) -> None:
    conn.execute("DROP TABLE IF EXISTS temp.outcome_markets")
    conn.execute(
        """
        CREATE TEMP TABLE outcome_markets (
            condition_id TEXT PRIMARY KEY,
            yes_token_id TEXT NOT NULL,
            no_token_id TEXT NOT NULL,
            start_date_ms INTEGER NOT NULL,
            end_date_ms INTEGER NOT NULL,
            target_yes INTEGER NOT NULL
        )
        """
    )
    rows = [
        (
            str(r.condition_id),
            str(r.yes_token_id),
            str(r.no_token_id),
            int(r.start_date_ms),
            int(r.end_date_ms),
            int(r.target_yes),
        )
        for r in markets.itertuples(index=False)
    ]
    conn.executemany(
        """
        INSERT INTO outcome_markets (
            condition_id,
            yes_token_id,
            no_token_id,
            start_date_ms,
            end_date_ms,
            target_yes
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def _paired_snapshot_frame(conn: sqlite3.Connection, cfg: OutcomeDatasetConfig) -> pd.DataFrame:
    min_tau_ms = int(max(0.0, cfg.min_tau_frac) * MARKET_DURATION_MS)
    max_tau_ms = int(min(1.0, cfg.max_tau_frac) * MARKET_DURATION_MS)
    sample_every_s = max(1, int(cfg.sample_every_s))

    return pd.read_sql_query(
        """
        WITH open_pair AS (
            SELECT
                om.condition_id,
                MIN(y.ts_ms) AS open_ts_ms
            FROM outcome_markets om
            JOIN snapshots y
              ON y.condition_id = om.condition_id
             AND y.token_id = om.yes_token_id
            JOIN snapshots n0
              ON n0.condition_id = om.condition_id
             AND n0.token_id = om.no_token_id
             AND n0.ts_ms = y.ts_ms
            WHERE y.depth_ok = 1
              AND n0.depth_ok = 1
            GROUP BY om.condition_id
        )
        SELECT
            y.condition_id,
            y.ts_ms AS snapshot_ts_ms,
            om.start_date_ms,
            om.end_date_ms AS market_end_ms,
            y.tau_ms,
            om.target_yes,
            y.vwap_ask_100 AS yes_ask,
            y.vwap_bid_100 AS yes_bid,
            y.mid_100 AS yes_mid,
            y.spread_100 AS yes_spread,
            y.bid_depth_usd AS yes_bid_depth_usd,
            y.ask_depth_usd AS yes_ask_depth_usd,
            y.imbalance AS yes_imbalance,
            y.best_bid AS yes_best_bid,
            y.best_ask AS yes_best_ask,
            n.vwap_ask_100 AS no_ask,
            n.vwap_bid_100 AS no_bid,
            n.mid_100 AS no_mid,
            n.spread_100 AS no_spread,
            n.bid_depth_usd AS no_bid_depth_usd,
            n.ask_depth_usd AS no_ask_depth_usd,
            n.imbalance AS no_imbalance,
            n.best_bid AS no_best_bid,
            n.best_ask AS no_best_ask,
            COALESCE(y.btc_price_binance, n.btc_price_binance) AS btc_price_binance,
            COALESCE(y.btc_price_chainlink, n.btc_price_chainlink) AS btc_price_chainlink,
            COALESCE(y.binance_best_bid, n.binance_best_bid) AS binance_best_bid,
            COALESCE(y.binance_best_ask, n.binance_best_ask) AS binance_best_ask,
            COALESCE(y.binance_mid, n.binance_mid) AS binance_mid,
            COALESCE(y.binance_spread_bps, n.binance_spread_bps) AS binance_spread_bps,
            COALESCE(y.binance_trade_count_5s, n.binance_trade_count_5s) AS binance_trade_count_5s,
            COALESCE(y.binance_buy_notional_5s, n.binance_buy_notional_5s) AS binance_buy_notional_5s,
            COALESCE(y.binance_sell_notional_5s, n.binance_sell_notional_5s) AS binance_sell_notional_5s,
            COALESCE(y.binance_trade_imbalance_5s, n.binance_trade_imbalance_5s) AS binance_trade_imbalance_5s,
            COALESCE(y.binance_trade_count_15s, n.binance_trade_count_15s) AS binance_trade_count_15s,
            COALESCE(y.binance_buy_notional_15s, n.binance_buy_notional_15s) AS binance_buy_notional_15s,
            COALESCE(y.binance_sell_notional_15s, n.binance_sell_notional_15s) AS binance_sell_notional_15s,
            COALESCE(y.binance_trade_imbalance_15s, n.binance_trade_imbalance_15s) AS binance_trade_imbalance_15s,
            oy.vwap_ask_100 AS anchor_open_yes_ask,
            oy.vwap_bid_100 AS anchor_open_yes_bid,
            oy.mid_100 AS anchor_open_yes_mid,
            on0.vwap_ask_100 AS anchor_open_no_ask,
            on0.vwap_bid_100 AS anchor_open_no_bid,
            on0.mid_100 AS anchor_open_no_mid,
            COALESCE(oy.btc_price_binance, on0.btc_price_binance) AS anchor_open_btc_price_binance,
            COALESCE(oy.btc_price_chainlink, on0.btc_price_chainlink) AS anchor_open_btc_price_chainlink
        FROM outcome_markets om
        JOIN open_pair op
          ON op.condition_id = om.condition_id
        JOIN snapshots oy
          ON oy.condition_id = om.condition_id
         AND oy.token_id = om.yes_token_id
         AND oy.ts_ms = op.open_ts_ms
        JOIN snapshots on0
          ON on0.condition_id = om.condition_id
         AND on0.token_id = om.no_token_id
         AND on0.ts_ms = op.open_ts_ms
        JOIN snapshots y
          ON y.condition_id = om.condition_id
         AND y.token_id = om.yes_token_id
        JOIN snapshots n
          ON n.condition_id = om.condition_id
         AND n.token_id = om.no_token_id
         AND n.ts_ms = y.ts_ms
        WHERE y.depth_ok = 1
          AND n.depth_ok = 1
          AND y.tau_ms BETWEEN ? AND ?
          AND CAST(y.ts_ms / 1000 AS INTEGER) % ? = 0
        ORDER BY y.ts_ms ASC, y.condition_id ASC
        """,
        conn,
        params=(min_tau_ms, max_tau_ms, sample_every_s),
    )


def _vectorized_rsi(diff: pd.Series, period: int) -> pd.Series:
    gains = diff.clip(lower=0.0)
    losses = (-diff.clip(upper=0.0)).astype(float)
    avg_gain = gains.rolling(period, min_periods=period).mean()
    avg_loss = losses.rolling(period, min_periods=period).mean()

    rsi = pd.Series(np.nan, index=diff.index, dtype=float)
    both_zero = (avg_gain <= 1e-12) & (avg_loss <= 1e-12)
    loss_zero = (avg_loss <= 1e-12) & (avg_gain > 1e-12)
    normal = avg_loss > 1e-12
    rsi.loc[both_zero] = 50.0
    rsi.loc[loss_zero] = 100.0
    rs = avg_gain.loc[normal] / avg_loss.loc[normal]
    rsi.loc[normal] = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def _btc_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    btc = (
        df[["snapshot_ts_ms", "btc_price_binance"]]
        .dropna(subset=["btc_price_binance"])
        .drop_duplicates(subset=["snapshot_ts_ms"])
        .sort_values("snapshot_ts_ms")
        .reset_index(drop=True)
    )
    if btc.empty:
        return pd.DataFrame(columns=["snapshot_ts_ms"])

    btc["btc_diff_1s"] = btc["btc_price_binance"].diff()
    short_windows = (6, 10, 20, 30, 60)
    ctx_windows = (90, 120, 180, 300)
    for window_s in (*short_windows, *ctx_windows):
        lookup = btc[["snapshot_ts_ms"]].copy()
        lookup["lag_lookup_ts_ms"] = lookup["snapshot_ts_ms"] - window_s * 1000
        older = btc[["snapshot_ts_ms", "btc_price_binance"]].rename(
            columns={
                "snapshot_ts_ms": "lag_lookup_ts_ms",
                "btc_price_binance": f"_lag_price_{window_s}s",
            }
        )
        merged = pd.merge_asof(
            lookup.sort_values("lag_lookup_ts_ms"),
            older.sort_values("lag_lookup_ts_ms"),
            on="lag_lookup_ts_ms",
            direction="backward",
        )
        lag_values = merged[f"_lag_price_{window_s}s"].values
        if window_s in short_windows:
            btc[f"btc_price_lag_{window_s}s"] = lag_values
            btc[f"btc_delta_{window_s}s"] = btc["btc_price_binance"] - lag_values
            continue
        btc[f"ctx_btc_price_lag_{window_s}s"] = lag_values
        btc[f"ctx_btc_delta_{window_s}s"] = btc["btc_price_binance"] - lag_values
        btc[f"ctx_btc_return_bps_{window_s}s"] = (
            _safe_div(btc[f"ctx_btc_delta_{window_s}s"], btc[f"ctx_btc_price_lag_{window_s}s"])
            * 10_000.0
        )

    btc["btc_rsi_14"] = _vectorized_rsi(btc["btc_diff_1s"], period=14)
    btc["btc_rsi_28"] = _vectorized_rsi(btc["btc_diff_1s"], period=28)
    btc["btc_vol_30s"] = btc["btc_diff_1s"].rolling(30, min_periods=10).std()
    btc["btc_vol_60s"] = btc["btc_diff_1s"].rolling(60, min_periods=20).std()
    btc["ctx_btc_rsi_60"] = _vectorized_rsi(btc["btc_diff_1s"], period=60)
    btc["ctx_btc_vol_120s"] = btc["btc_diff_1s"].rolling(120, min_periods=40).std()
    btc["ctx_btc_vol_300s"] = btc["btc_diff_1s"].rolling(300, min_periods=100).std()
    btc["ctx_btc_vol_ratio_30_120"] = _safe_div(btc["btc_vol_30s"], btc["ctx_btc_vol_120s"])
    btc["ctx_btc_vol_ratio_60_300"] = _safe_div(btc["btc_vol_60s"], btc["ctx_btc_vol_300s"])
    btc["ctx_btc_accel_30_120"] = btc["btc_delta_30s"] - (btc["ctx_btc_delta_120s"] / 4.0)
    btc["ctx_btc_accel_60_300"] = btc["btc_delta_60s"] - (btc["ctx_btc_delta_300s"] / 5.0)
    btc["ctx_btc_mom_vol_120"] = _safe_div(btc["ctx_btc_delta_120s"], btc["ctx_btc_vol_120s"])
    btc["ctx_btc_mom_vol_300"] = _safe_div(btc["ctx_btc_delta_300s"], btc["ctx_btc_vol_300s"])

    return btc.drop(columns=["btc_diff_1s"])


def _condition_temporal_feature_frame(
    df: pd.DataFrame,
    *,
    lag_seconds: tuple[int, ...] = (5, 15, 30),
) -> pd.DataFrame:
    base_cols = [
        "condition_id",
        "snapshot_ts_ms",
        "yes_ask",
        "no_ask",
        "market_implied_yes_mid",
        "yes_no_spread_sum",
        "imbalance_gap",
        "ask_depth_total_usd",
        "bid_depth_total_usd",
        "depth_total_ratio",
    ]
    base = df[base_cols].reset_index(drop=True).copy()
    base["_row_id"] = np.arange(len(base), dtype=int)
    calc = base.sort_values(["condition_id", "snapshot_ts_ms", "_row_id"]).reset_index(drop=True)
    if calc.empty:
        return pd.DataFrame(columns=["_row_id"])

    name_map = {
        "yes_ask": "yes_ask",
        "no_ask": "no_ask",
        "market_implied_yes_mid": "implied_yes_mid",
        "yes_no_spread_sum": "spread_sum",
        "imbalance_gap": "imbalance_gap",
        "ask_depth_total_usd": "ask_depth_total",
        "bid_depth_total_usd": "bid_depth_total",
        "depth_total_ratio": "depth_total_ratio",
    }
    out = calc[["_row_id"]].copy()
    for lag_s in lag_seconds:
        lag_ms = int(lag_s) * 1000
        delta_arrays = {
            name: np.full(len(calc), np.nan, dtype=float) for name in name_map.values()
        }
        for _, grp in calc.groupby("condition_id", sort=False):
            ts = grp["snapshot_ts_ms"].to_numpy(dtype=np.int64)
            lookup = ts - lag_ms
            lag_idx = np.searchsorted(ts, lookup, side="right") - 1
            valid = lag_idx >= 0
            if not valid.any():
                continue
            grp_pos = grp.index.to_numpy(dtype=int)
            valid_pos = grp_pos[valid]
            valid_lag_idx = lag_idx[valid]
            for col, name in name_map.items():
                values = grp[col].to_numpy(dtype=float)
                delta_arrays[name][valid_pos] = (
                    values[valid] - values[valid_lag_idx]
                )
        for name, values in delta_arrays.items():
            out[f"pm_{name}_delta_{lag_s}s"] = values
    return out.sort_values("_row_id").reset_index(drop=True)


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace(0.0, np.nan)
    return num / den


def _market_implied_yes_mid(df: pd.DataFrame) -> pd.Series:
    yes_mid = df["yes_mid"]
    no_mid = df["no_mid"]
    both = yes_mid.notna() & no_mid.notna()
    out = pd.Series(np.nan, index=df.index, dtype=float)
    out.loc[both] = 0.5 * (yes_mid.loc[both] + (1.0 - no_mid.loc[both]))
    out.loc[out.isna() & yes_mid.notna()] = yes_mid.loc[out.isna() & yes_mid.notna()]
    out.loc[out.isna() & no_mid.notna()] = 1.0 - no_mid.loc[out.isna() & no_mid.notna()]
    return out.clip(0.0, 1.0)


def enrich_outcome_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out

    out["tau_frac"] = out["tau_ms"] / MARKET_DURATION_MS
    out["contract_age_frac"] = 1.0 - out["tau_frac"]
    if "target_yes" in out.columns:
        out["target_no"] = 1 - out["target_yes"]

    out["yes_no_mid_sum"] = out["yes_mid"] + out["no_mid"]
    out["yes_no_mid_gap"] = out["yes_no_mid_sum"] - 1.0
    out["yes_no_spread_sum"] = out["yes_spread"] + out["no_spread"]
    out["yes_no_spread_diff"] = out["yes_spread"] - out["no_spread"]
    out["imbalance_gap"] = out["yes_imbalance"] - out["no_imbalance"]
    out["imbalance_abs_sum"] = out["yes_imbalance"].abs() + out["no_imbalance"].abs()
    out["ask_depth_total_usd"] = out["yes_ask_depth_usd"] + out["no_ask_depth_usd"]
    out["bid_depth_total_usd"] = out["yes_bid_depth_usd"] + out["no_bid_depth_usd"]
    out["yes_depth_ratio"] = _safe_div(out["yes_bid_depth_usd"], out["yes_ask_depth_usd"])
    out["no_depth_ratio"] = _safe_div(out["no_bid_depth_usd"], out["no_ask_depth_usd"])
    out["depth_total_ratio"] = _safe_div(out["bid_depth_total_usd"], out["ask_depth_total_usd"])
    out["market_implied_yes_mid"] = _market_implied_yes_mid(out)
    out["market_implied_no_mid"] = 1.0 - out["market_implied_yes_mid"]
    if "target_yes" in out.columns:
        out["edge_yes_mid"] = out["target_yes"] - out["market_implied_yes_mid"]
        out["edge_no_mid"] = out["target_no"] - out["market_implied_no_mid"]

    anchor_mid_cols = {"anchor_open_yes_mid", "anchor_open_no_mid"}
    if anchor_mid_cols.issubset(out.columns):
        anchor_tmp = pd.DataFrame(
            {
                "yes_mid": out["anchor_open_yes_mid"],
                "no_mid": out["anchor_open_no_mid"],
            }
        )
        out["anchor_open_market_implied_yes_mid"] = _market_implied_yes_mid(anchor_tmp)
    if {"btc_price_binance", "anchor_open_btc_price_binance"}.issubset(out.columns):
        out["anchor_btc_delta_open_usd"] = (
            out["btc_price_binance"] - out["anchor_open_btc_price_binance"]
        )
        out["anchor_btc_return_open_bps"] = (
            _safe_div(out["anchor_btc_delta_open_usd"], out["anchor_open_btc_price_binance"])
            * 10_000.0
        )
        out["anchor_btc_abs_return_open_bps"] = out["anchor_btc_return_open_bps"].abs()
        out["anchor_btc_return_open_sign"] = np.sign(out["anchor_btc_return_open_bps"])
    if {"market_implied_yes_mid", "anchor_open_market_implied_yes_mid"}.issubset(out.columns):
        out["anchor_implied_yes_delta_open"] = (
            out["market_implied_yes_mid"] - out["anchor_open_market_implied_yes_mid"]
        )
    if {"yes_ask", "anchor_open_yes_ask"}.issubset(out.columns):
        out["anchor_yes_ask_delta_open"] = out["yes_ask"] - out["anchor_open_yes_ask"]
    if {"no_ask", "anchor_open_no_ask"}.issubset(out.columns):
        out["anchor_no_ask_delta_open"] = out["no_ask"] - out["anchor_open_no_ask"]
    if {"contract_age_frac", "anchor_btc_return_open_bps"}.issubset(out.columns):
        out["anchor_btc_return_open_per_age_bps"] = _safe_div(
            out["anchor_btc_return_open_bps"],
            out["contract_age_frac"],
        )
    if {"contract_age_frac", "anchor_implied_yes_delta_open"}.issubset(out.columns):
        out["anchor_implied_yes_delta_open_per_age"] = _safe_div(
            out["anchor_implied_yes_delta_open"],
            out["contract_age_frac"],
        )
    if {"anchor_implied_yes_delta_open", "anchor_btc_return_open_sign"}.issubset(out.columns):
        out["anchor_implied_yes_dir_align"] = (
            out["anchor_implied_yes_delta_open"] * out["anchor_btc_return_open_sign"]
        )

    if {"binance_buy_notional_5s", "binance_sell_notional_5s"}.issubset(out.columns):
        out["binance_trade_notional_5s"] = (
            out["binance_buy_notional_5s"] + out["binance_sell_notional_5s"]
        )
        out["binance_buy_share_5s"] = _safe_div(
            out["binance_buy_notional_5s"],
            out["binance_trade_notional_5s"],
        )
    if {"binance_buy_notional_15s", "binance_sell_notional_15s"}.issubset(out.columns):
        out["binance_trade_notional_15s"] = (
            out["binance_buy_notional_15s"] + out["binance_sell_notional_15s"]
        )
        out["binance_buy_share_15s"] = _safe_div(
            out["binance_buy_notional_15s"],
            out["binance_trade_notional_15s"],
        )
    if {"binance_trade_imbalance_5s", "binance_trade_imbalance_15s"}.issubset(out.columns):
        out["binance_trade_imbalance_delta"] = (
            out["binance_trade_imbalance_5s"] - out["binance_trade_imbalance_15s"]
        )
    if {"binance_mid", "btc_price_binance"}.issubset(out.columns):
        out["binance_mid_basis_bps"] = (
            _safe_div(out["btc_price_binance"] - out["binance_mid"], out["binance_mid"]) * 10_000.0
        )

    ts_dt = pd.to_datetime(out["snapshot_ts_ms"], unit="ms", utc=True)
    minute_of_day = ts_dt.dt.hour * 60 + ts_dt.dt.minute + ts_dt.dt.second / 60.0
    out["tod_sin"] = np.sin(2.0 * math.pi * minute_of_day / (24.0 * 60.0))
    out["tod_cos"] = np.cos(2.0 * math.pi * minute_of_day / (24.0 * 60.0))

    pm_temporal = _condition_temporal_feature_frame(out)
    if not pm_temporal.empty:
        out = out.reset_index(drop=True)
        pm_temporal = pm_temporal.sort_values("_row_id").reset_index(drop=True)
        out = pd.concat([out, pm_temporal.drop(columns=["_row_id"])], axis=1)

    btc = _btc_feature_frame(out)
    if not btc.empty:
        out = out.merge(btc, on=["snapshot_ts_ms", "btc_price_binance"], how="left")
    return out


def build_outcome_dataset(
    db_path: str,
    cfg: OutcomeDatasetConfig | None = None,
) -> pd.DataFrame:
    cfg = cfg or OutcomeDatasetConfig()
    conn = _connect(db_path)
    try:
        markets = _resolved_market_frame(
            conn,
            limit_conditions=cfg.limit_conditions,
            skip_tail_conditions=cfg.skip_tail_conditions,
        )
        if markets.empty:
            return pd.DataFrame()
        _stage_outcome_markets(conn, markets)
        paired = _paired_snapshot_frame(conn, cfg)
        if paired.empty:
            return paired
        dataset = enrich_outcome_features(paired)
        dataset.sort_values(["snapshot_ts_ms", "condition_id"], inplace=True)
        dataset.reset_index(drop=True, inplace=True)
        return dataset
    finally:
        conn.close()


def build_live_outcome_frame(
    db_path: str,
    min_tau_frac: float = 0.12,
    max_tau_frac: float = 0.90,
    limit_conditions: int | None = None,
) -> pd.DataFrame:
    conn = _connect(db_path)
    try:
        min_tau_ms = int(max(0.0, min_tau_frac) * MARKET_DURATION_MS)
        max_tau_ms = int(min(1.0, max_tau_frac) * MARKET_DURATION_MS)
        limit_sql = ""
        params: list[int | str] = [min_tau_ms, max_tau_ms]
        if limit_conditions is not None and limit_conditions > 0:
            limit_sql = "LIMIT ?"
            params.append(int(limit_conditions))

        frame = pd.read_sql_query(
            f"""
            WITH latest AS (
                SELECT s.condition_id, MAX(s.ts_ms) AS ts_ms
                FROM snapshots s
                JOIN markets m ON m.condition_id = s.condition_id
                WHERE m.duration_seconds = 300
                  AND COALESCE(m.resolved, 0) = 0
                  AND COALESCE(m.active, 1) = 1
                GROUP BY s.condition_id
            ),
            open_pair AS (
                SELECT
                    m.condition_id,
                    MIN(y.ts_ms) AS open_ts_ms
                FROM markets m
                JOIN snapshots y
                  ON y.condition_id = m.condition_id
                 AND y.token_id = m.yes_token_id
                JOIN snapshots n0
                  ON n0.condition_id = m.condition_id
                 AND n0.token_id = m.no_token_id
                 AND n0.ts_ms = y.ts_ms
                WHERE m.duration_seconds = 300
                  AND COALESCE(m.resolved, 0) = 0
                  AND COALESCE(m.active, 1) = 1
                  AND y.depth_ok = 1
                  AND n0.depth_ok = 1
                GROUP BY m.condition_id
            )
            SELECT
                m.question,
                y.condition_id,
                y.ts_ms AS snapshot_ts_ms,
                m.start_date_ms,
                m.end_date_ms AS market_end_ms,
                y.tau_ms,
                y.vwap_ask_100 AS yes_ask,
                y.vwap_bid_100 AS yes_bid,
                y.mid_100 AS yes_mid,
                y.spread_100 AS yes_spread,
                y.bid_depth_usd AS yes_bid_depth_usd,
                y.ask_depth_usd AS yes_ask_depth_usd,
                y.imbalance AS yes_imbalance,
                y.best_bid AS yes_best_bid,
                y.best_ask AS yes_best_ask,
                n.vwap_ask_100 AS no_ask,
                n.vwap_bid_100 AS no_bid,
                n.mid_100 AS no_mid,
                n.spread_100 AS no_spread,
                n.bid_depth_usd AS no_bid_depth_usd,
                n.ask_depth_usd AS no_ask_depth_usd,
                n.imbalance AS no_imbalance,
                n.best_bid AS no_best_bid,
                n.best_ask AS no_best_ask,
                COALESCE(y.btc_price_binance, n.btc_price_binance) AS btc_price_binance,
                COALESCE(y.btc_price_chainlink, n.btc_price_chainlink) AS btc_price_chainlink,
                COALESCE(y.binance_best_bid, n.binance_best_bid) AS binance_best_bid,
                COALESCE(y.binance_best_ask, n.binance_best_ask) AS binance_best_ask,
                COALESCE(y.binance_mid, n.binance_mid) AS binance_mid,
                COALESCE(y.binance_spread_bps, n.binance_spread_bps) AS binance_spread_bps,
                COALESCE(y.binance_trade_count_5s, n.binance_trade_count_5s) AS binance_trade_count_5s,
                COALESCE(y.binance_buy_notional_5s, n.binance_buy_notional_5s) AS binance_buy_notional_5s,
                COALESCE(y.binance_sell_notional_5s, n.binance_sell_notional_5s) AS binance_sell_notional_5s,
                COALESCE(y.binance_trade_imbalance_5s, n.binance_trade_imbalance_5s) AS binance_trade_imbalance_5s,
                COALESCE(y.binance_trade_count_15s, n.binance_trade_count_15s) AS binance_trade_count_15s,
                COALESCE(y.binance_buy_notional_15s, n.binance_buy_notional_15s) AS binance_buy_notional_15s,
                COALESCE(y.binance_sell_notional_15s, n.binance_sell_notional_15s) AS binance_sell_notional_15s,
                COALESCE(y.binance_trade_imbalance_15s, n.binance_trade_imbalance_15s) AS binance_trade_imbalance_15s,
                oy.vwap_ask_100 AS anchor_open_yes_ask,
                oy.vwap_bid_100 AS anchor_open_yes_bid,
                oy.mid_100 AS anchor_open_yes_mid,
                on0.vwap_ask_100 AS anchor_open_no_ask,
                on0.vwap_bid_100 AS anchor_open_no_bid,
                on0.mid_100 AS anchor_open_no_mid,
                COALESCE(oy.btc_price_binance, on0.btc_price_binance) AS anchor_open_btc_price_binance,
                COALESCE(oy.btc_price_chainlink, on0.btc_price_chainlink) AS anchor_open_btc_price_chainlink
            FROM latest l
            JOIN markets m
              ON m.condition_id = l.condition_id
            JOIN open_pair op
              ON op.condition_id = l.condition_id
            JOIN snapshots oy
              ON oy.condition_id = l.condition_id
             AND oy.ts_ms = op.open_ts_ms
             AND oy.token_id = m.yes_token_id
            JOIN snapshots on0
              ON on0.condition_id = l.condition_id
             AND on0.ts_ms = op.open_ts_ms
             AND on0.token_id = m.no_token_id
            JOIN snapshots y
              ON y.condition_id = l.condition_id
             AND y.ts_ms = l.ts_ms
             AND y.token_id = m.yes_token_id
            JOIN snapshots n
              ON n.condition_id = l.condition_id
             AND n.ts_ms = l.ts_ms
             AND n.token_id = m.no_token_id
            WHERE y.depth_ok = 1
              AND n.depth_ok = 1
              AND y.tau_ms BETWEEN ? AND ?
            ORDER BY y.ts_ms DESC, y.condition_id ASC
            {limit_sql}
            """,
            conn,
            params=params,
        )
        if frame.empty:
            return frame
        return enrich_outcome_features(frame)
    finally:
        conn.close()


def default_feature_columns(df: pd.DataFrame) -> list[str]:
    excluded = {
        "condition_id",
        "snapshot_ts_ms",
        "start_date_ms",
        "market_end_ms",
        "tau_ms",
        "target_yes",
        "target_no",
        "edge_yes_mid",
        "edge_no_mid",
    }
    cols: list[str] = []
    for col in df.columns:
        if col in excluded:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            cols.append(col)
    return cols


def iter_purged_walk_forward_splits(
    df: pd.DataFrame,
    n_splits: int,
    embargo_minutes: int,
) -> Iterable[tuple[WalkForwardFold, np.ndarray, np.ndarray]]:
    if df.empty:
        return

    unique_market_ends = np.array(sorted(df["market_end_ms"].dropna().unique()))
    if unique_market_ends.size == 0:
        return
    test_blocks = [block for block in np.array_split(unique_market_ends, n_splits) if len(block) > 0]
    embargo_ms = max(0, int(embargo_minutes)) * 60_000
    market_end = df["market_end_ms"].to_numpy()

    for fold_idx, block in enumerate(test_blocks, start=1):
        test_start_ms = int(block[0])
        test_end_ms = int(block[-1])
        test_mask = np.isin(market_end, block)
        train_mask = market_end < (test_start_ms - embargo_ms)
        if not train_mask.any() or not test_mask.any():
            continue

        train_conditions = int(df.loc[train_mask, "condition_id"].nunique())
        test_conditions = int(df.loc[test_mask, "condition_id"].nunique())
        yield (
            WalkForwardFold(
                fold=fold_idx,
                test_start_ms=test_start_ms,
                test_end_ms=test_end_ms,
                train_conditions=train_conditions,
                test_conditions=test_conditions,
                train_rows=int(train_mask.sum()),
                test_rows=int(test_mask.sum()),
            ),
            train_mask,
            test_mask,
        )
