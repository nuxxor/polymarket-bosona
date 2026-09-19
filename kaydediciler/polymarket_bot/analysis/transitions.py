from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Price bins: 1-cent buckets [0.00, 0.01), [0.01, 0.02), ..., [0.99, 1.00]
PRICE_BINS = np.arange(0, 1.01, 0.01)
# Tau bins: 15-second buckets
TAU_BIN_S = 15
_ALLOWED_DURATIONS = (300, 900, 1800, 3600)


def build_transition_matrix(db_path: str, min_count: int = 200) -> pd.DataFrame:
    """Build conditional transition matrix: P(price_bin_j | price_bin_i, tau_bin).

    Returns DataFrame with columns: condition_id, token_id, tau_bin, from_bin, to_bin, count, prob
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT s.condition_id, s.token_id, s.ts_ms, s.tau_ms, s.mid_100, "
        "       m.duration_seconds "
        "FROM snapshots s "
        "JOIN markets m ON s.condition_id = m.condition_id "
        "WHERE s.depth_ok=1 AND s.mid_100 IS NOT NULL "
        f"  AND m.duration_seconds IN {_ALLOWED_DURATIONS} "
        "ORDER BY s.token_id, s.ts_ms",
        conn,
    )
    conn.close()

    if df.empty:
        log.warning("No snapshots with depth_ok=1 found")
        return pd.DataFrame()

    # Bin mid_100 into 1-cent buckets
    df["price_bin"] = pd.cut(
        df["mid_100"],
        bins=PRICE_BINS,
        labels=[f"{b:.2f}" for b in PRICE_BINS[:-1]],
        include_lowest=True,
    )

    # Bin tau into 15s buckets
    df["tau_bin_s"] = (df["tau_ms"] // (TAU_BIN_S * 1000)) * TAU_BIN_S

    results = []

    for (cond_id, token_id), group in df.groupby(["condition_id", "token_id"]):
        group = group.sort_values("ts_ms").reset_index(drop=True)
        duration = group.iloc[0]["duration_seconds"]

        for i in range(len(group) - 1):
            from_bin = group.loc[i, "price_bin"]
            to_bin = group.loc[i + 1, "price_bin"]
            tau_bin = group.loc[i, "tau_bin_s"]

            if pd.isna(from_bin) or pd.isna(to_bin):
                continue

            results.append({
                "duration_seconds": int(duration),
                "tau_bin": tau_bin,
                "from_bin": str(from_bin),
                "to_bin": str(to_bin),
            })

    if not results:
        return pd.DataFrame()

    trans_df = pd.DataFrame(results)

    # Count transitions — grouped by market duration to avoid mixing 5min/1h
    counts = (
        trans_df.groupby(["duration_seconds", "tau_bin", "from_bin", "to_bin"])
        .size()
        .reset_index(name="count")
    )

    # Compute probabilities within each (duration, tau_bin, from_bin) group
    totals = counts.groupby(["duration_seconds", "tau_bin", "from_bin"])["count"].transform("sum")
    counts["prob"] = counts["count"] / totals
    counts["sufficient"] = counts["count"] >= min_count

    log.info(
        "Transition matrix: %d cells, %d with n >= %d",
        len(counts),
        counts["sufficient"].sum(),
        min_count,
    )

    return counts


def export_transition_csv(db_path: str, output_path: str, min_count: int = 200) -> None:
    """Build and export transition matrix to CSV."""
    df = build_transition_matrix(db_path, min_count)
    if df.empty:
        log.warning("No data to export")
        return
    df.to_csv(output_path, index=False)
    log.info("Transition matrix exported to %s (%d rows)", output_path, len(df))
