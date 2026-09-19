from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)
_ALLOWED_DURATIONS = (300, 900, 1800, 3600)


def scan_arbitrage(
    db_path: str,
    tolerance_ms: int = 500,
    estimated_fee_rate: float = 0.02,
) -> pd.DataFrame:
    """Scan for YES+NO < $1 structural arbitrage opportunities.

    Uses nearest-join (±tolerance_ms) to pair YES and NO snapshots.
    Computes fee-adjusted net edge.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT s.ts_ms, s.token_id, s.condition_id, s.vwap_ask_100, s.vwap_bid_100, "
        "       s.best_ask, s.depth_ok, m.yes_token_id, m.no_token_id "
        "FROM snapshots s "
        "JOIN markets m ON s.condition_id = m.condition_id "
        "WHERE s.depth_ok = 1 AND s.vwap_ask_100 IS NOT NULL "
        f"  AND m.duration_seconds IN {_ALLOWED_DURATIONS}",
        conn,
    )
    conn.close()

    if df.empty:
        log.warning("No depth-ok snapshots for arbitrage scan")
        return pd.DataFrame()

    # Split into YES and NO
    yes_df = df[df["token_id"] == df["yes_token_id"]].copy()
    no_df = df[df["token_id"] == df["no_token_id"]].copy()

    if yes_df.empty or no_df.empty:
        log.warning("Missing YES or NO data")
        return pd.DataFrame()

    yes_df = yes_df.sort_values("ts_ms").reset_index(drop=True)
    no_df = no_df.sort_values("ts_ms").reset_index(drop=True)

    # Nearest-join by condition_id + ts_ms within tolerance
    yes_df = yes_df.rename(columns={
        "vwap_ask_100": "vwap_ask_yes",
        "vwap_bid_100": "vwap_bid_yes",
        "best_ask": "best_ask_yes",
    })
    no_df = no_df.rename(columns={
        "vwap_ask_100": "vwap_ask_no",
        "vwap_bid_100": "vwap_bid_no",
        "best_ask": "best_ask_no",
    })

    results = []
    for cond_id in yes_df["condition_id"].unique():
        y = yes_df[yes_df["condition_id"] == cond_id][["ts_ms", "vwap_ask_yes", "vwap_bid_yes", "best_ask_yes"]].copy()
        n = no_df[no_df["condition_id"] == cond_id][["ts_ms", "vwap_ask_no", "vwap_bid_no", "best_ask_no"]].copy()

        if y.empty or n.empty:
            continue

        # merge_asof requires sorted keys
        merged = pd.merge_asof(
            y.sort_values("ts_ms"),
            n.sort_values("ts_ms"),
            on="ts_ms",
            tolerance=tolerance_ms,
            direction="nearest",
        )
        merged = merged.dropna(subset=["vwap_ask_no"])
        merged["condition_id"] = cond_id
        results.append(merged)

    if not results:
        return pd.DataFrame()

    paired = pd.concat(results, ignore_index=True)

    # Compute pair cost and fee-adjusted edge
    paired["pair_cost"] = paired["vwap_ask_yes"] + paired["vwap_ask_no"]

    # Slippage estimate: VWAP - best_ask per side
    paired["slippage_yes"] = (paired["vwap_ask_yes"] - paired["best_ask_yes"]).clip(lower=0)
    paired["slippage_no"] = (paired["vwap_ask_no"] - paired["best_ask_no"]).clip(lower=0)

    # Fees (per-side taker fee)
    paired["fee_yes"] = paired["vwap_ask_yes"] * estimated_fee_rate
    paired["fee_no"] = paired["vwap_ask_no"] * estimated_fee_rate

    paired["net_edge"] = (
        1.0
        - paired["pair_cost"]
        - paired["fee_yes"]
        - paired["fee_no"]
        - paired["slippage_yes"]
        - paired["slippage_no"]
    )

    # Only report positive edge
    opportunities = paired[paired["net_edge"] > 0].copy()

    if opportunities.empty:
        log.info("No fee-adjusted arbitrage opportunities found")
    else:
        log.info(
            "Found %d arb windows: avg_edge=%.4f, max_edge=%.4f",
            len(opportunities),
            opportunities["net_edge"].mean(),
            opportunities["net_edge"].max(),
        )

    return paired  # Return all for analysis, not just positive


def export_arbitrage_report(db_path: str, output_path: str) -> None:
    """Run arbitrage scan and export results."""
    df = scan_arbitrage(db_path)
    if df.empty:
        log.warning("No data for arbitrage report")
        return
    df.to_csv(output_path, index=False)
    log.info("Arbitrage report exported to %s (%d rows)", output_path, len(df))
