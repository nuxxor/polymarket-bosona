from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd
from scipy import signal as sp_signal

log = logging.getLogger(__name__)

# Clip bounds for logit to avoid inf
_CLIP_LO = 0.001
_CLIP_HI = 0.999
_ALLOWED_DURATIONS = (300, 900, 1800, 3600)


def _logit(p: np.ndarray) -> np.ndarray:
    """Logit transform for bounded [0,1] prices."""
    p_clipped = np.clip(p, _CLIP_LO, _CLIP_HI)
    return np.log(p_clipped / (1 - p_clipped))


def compute_cross_correlation(
    db_path: str,
    max_lag_s: int = 60,
    resample_s: int = 1,
) -> dict:
    """Compute cross-correlation between BTC price changes and PM token price changes.

    Uses logit transform for PM prices to handle bounded [0,1] domain.
    """
    conn = sqlite3.connect(db_path)

    # Load PM snapshots
    snap_df = pd.read_sql_query(
        "SELECT s.ts_ms, s.token_id, s.condition_id, s.mid_100 "
        "FROM snapshots s "
        "JOIN markets m ON s.condition_id = m.condition_id "
        "WHERE s.depth_ok=1 AND s.mid_100 IS NOT NULL "
        f"  AND m.duration_seconds IN {_ALLOWED_DURATIONS}",
        conn,
    )

    # Load BTC prices
    btc_df = pd.read_sql_query(
        "SELECT ts_ms, source, price FROM btc_prices ORDER BY ts_ms",
        conn,
    )
    conn.close()

    if snap_df.empty or btc_df.empty:
        log.warning("Insufficient data for correlation analysis")
        return {}

    # Use primary BTC source
    btc = btc_df.copy()
    btc["ts_s"] = (btc["ts_ms"] // (resample_s * 1000)) * resample_s
    btc_resampled = btc.groupby("ts_s")["price"].last().sort_index()
    btc_returns = btc_resampled.pct_change().dropna()

    results = {}

    for (cond_id, token_id), group in snap_df.groupby(["condition_id", "token_id"]):
        g = group.sort_values("ts_ms").copy()
        g["ts_s"] = (g["ts_ms"] // (resample_s * 1000)) * resample_s
        pm_resampled = g.groupby("ts_s")["mid_100"].last().sort_index()

        # Logit transform
        logit_mid = _logit(pm_resampled.values)
        pm_returns = pd.Series(np.diff(logit_mid), index=pm_resampled.index[1:])

        # Align on common timestamps
        common = btc_returns.index.intersection(pm_returns.index)
        if len(common) < 100:
            continue

        r_btc = btc_returns.loc[common].values
        r_pm = pm_returns.loc[common].values

        # Normalize
        r_btc = (r_btc - r_btc.mean()) / (r_btc.std() + 1e-10)
        r_pm = (r_pm - r_pm.mean()) / (r_pm.std() + 1e-10)

        # Cross-correlation at lags
        max_lag_samples = max_lag_s // resample_s
        corr = np.correlate(r_pm, r_btc, mode="full")
        corr = corr / len(r_btc)

        mid = len(corr) // 2
        lag_range = range(-max_lag_samples, max_lag_samples + 1)
        lag_corrs = {}
        for lag in lag_range:
            idx = mid + lag
            if 0 <= idx < len(corr):
                lag_corrs[lag * resample_s] = float(corr[idx])

        # Find peak lag
        if lag_corrs:
            peak_lag = max(lag_corrs, key=lambda k: abs(lag_corrs[k]))
            peak_corr = lag_corrs[peak_lag]
        else:
            peak_lag = 0
            peak_corr = 0.0

        results[f"{cond_id[:12]}_{token_id[:12]}"] = {
            "condition_id": cond_id,
            "token_id": token_id,
            "n_samples": len(common),
            "peak_lag_s": peak_lag,
            "peak_correlation": peak_corr,
            "lag_correlations": lag_corrs,
        }

        log.info(
            "%s/%s: peak_lag=%ds, peak_corr=%.4f (n=%d)",
            cond_id[:12],
            token_id[:12],
            peak_lag,
            peak_corr,
            len(common),
        )

    return results


def compute_basis_distribution(db_path: str) -> pd.DataFrame:
    """Compute |btc_binance - btc_chainlink| distribution over time."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT ts_ms, source, price FROM btc_prices ORDER BY ts_ms",
        conn,
    )
    conn.close()

    if df.empty:
        return pd.DataFrame()

    # Pivot sources
    binance = df[df["source"].isin(["rtds_binance", "binance_ws"])].copy()
    chainlink = df[df["source"] == "rtds_chainlink"].copy()

    if binance.empty or chainlink.empty:
        log.warning("Need both Binance and Chainlink prices for basis")
        return pd.DataFrame()

    binance = binance.sort_values("ts_ms")
    chainlink = chainlink.sort_values("ts_ms")

    # Nearest-join
    merged = pd.merge_asof(
        binance[["ts_ms", "price"]].rename(columns={"price": "binance_price"}),
        chainlink[["ts_ms", "price"]].rename(columns={"price": "chainlink_price"}),
        on="ts_ms",
        tolerance=5000,
        direction="nearest",
    ).dropna()

    if merged.empty:
        return pd.DataFrame()

    merged["basis"] = (merged["binance_price"] - merged["chainlink_price"]).abs()
    merged["basis_bps"] = merged["basis"] / merged["binance_price"] * 10000

    log.info(
        "Basis: mean=%.2f bps, p95=%.2f bps, max=%.2f bps (n=%d)",
        merged["basis_bps"].mean(),
        merged["basis_bps"].quantile(0.95),
        merged["basis_bps"].max(),
        len(merged),
    )

    return merged
