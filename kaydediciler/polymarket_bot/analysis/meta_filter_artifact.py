from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


_SPARSE_DIRECTIONAL_FEATURE_COLS = [
    "feat_anchor_implied_yes_delta_open_per_age",
    "feat_pm_implied_yes_mid_delta_5s",
    "feat_pm_implied_yes_mid_delta_15s",
    "feat_pm_imbalance_gap_delta_15s",
    "feat_pm_imbalance_gap_delta_30s",
    "feat_btc_delta_20s",
    "feat_btc_delta_30s",
    "feat_ctx_btc_delta_120s",
    "feat_ctx_btc_delta_300s",
]

_BRIDGE_DIRECTIONAL_FEATURE_COLS = [
    *_SPARSE_DIRECTIONAL_FEATURE_COLS,
    "feat_anchor_implied_yes_dir_align",
    "feat_pm_imbalance_gap_delta_5s",
    "feat_btc_delta_10s",
    "feat_ctx_btc_delta_90s",
]

_SPARSE_RETURNS_DIRECTIONAL_FEATURE_COLS = [
    *_SPARSE_DIRECTIONAL_FEATURE_COLS,
    "feat_anchor_btc_return_open_bps",
    "feat_anchor_btc_return_open_per_age_bps",
    "feat_anchor_implied_yes_delta_open",
    "feat_imbalance_gap",
    "feat_ctx_btc_return_bps_90s",
    "feat_ctx_btc_return_bps_120s",
    "feat_ctx_btc_return_bps_300s",
]

_SPARSE_CONTEXT_DIRECTIONAL_FEATURE_COLS = [
    *_SPARSE_DIRECTIONAL_FEATURE_COLS,
    "feat_btc_delta_60s",
    "feat_ctx_btc_delta_90s",
    "feat_ctx_btc_return_bps_90s",
    "feat_ctx_btc_return_bps_120s",
    "feat_ctx_btc_return_bps_300s",
]


def _meta_artifact_type(artifact: dict[str, Any]) -> str:
    return str(artifact.get("artifact_type") or artifact.get("type") or "single_v1")


def load_meta_filter_artifact(path: str | Path) -> dict[str, Any]:
    try:
        import joblib
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency: joblib") from exc

    artifact_path = Path(path)
    artifact = joblib.load(artifact_path)
    _validate_meta_filter_artifact(artifact, artifact_path=artifact_path)
    artifact["artifact_path"] = str(artifact_path)
    return artifact


def _validate_meta_filter_artifact(
    artifact: dict[str, Any],
    *,
    artifact_path: Path,
) -> None:
    artifact_type = _meta_artifact_type(artifact)
    if artifact_type == "switch_v1":
        required = {"selected_threshold", "switch_gate", "primary_artifact", "secondary_artifact"}
        missing = sorted(required - set(artifact))
        if missing:
            raise RuntimeError(
                f"Invalid switch meta-filter artifact at {artifact_path}: missing keys {missing}"
            )
        _validate_meta_filter_artifact(dict(artifact["primary_artifact"]), artifact_path=artifact_path)
        _validate_meta_filter_artifact(dict(artifact["secondary_artifact"]), artifact_path=artifact_path)
        return

    required = {"model", "feature_columns", "fill_values", "selected_threshold"}
    missing = sorted(required - set(artifact))
    if missing:
        raise RuntimeError(
            f"Invalid meta-filter artifact at {artifact_path}: missing keys {missing}"
        )


def build_meta_feature_row(
    *,
    outcome_row: dict[str, Any],
    side: str,
    signal: float,
    accel: float | None,
    feature_profile: str = "baseline",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "entry_signal": float(signal),
        "entry_accel": float(accel) if accel is not None else np.nan,
        "entry_side_yes": 1 if side == "YES" else 0,
        "entry_side_no": 1 if side == "NO" else 0,
    }
    outcome_action = str(outcome_row.get("action", "") or "")
    row["entry_outcome_action_yes"] = 1 if outcome_action == "YES" else 0
    row["entry_outcome_action_no"] = 1 if outcome_action == "NO" else 0
    row["entry_outcome_action_flat"] = 1 if outcome_action == "FLAT" else 0
    snapshot_ts_ms = outcome_row.get("snapshot_ts_ms")
    try:
        ts = pd.to_datetime(float(snapshot_ts_ms), unit="ms", utc=True)
    except Exception:
        ts = pd.NaT
    if not pd.isna(ts):
        hour = float(ts.hour)
        weekday = float(ts.weekday())
        angle = 2.0 * np.pi * hour / 24.0
        row["entry_hour_utc_sin"] = float(np.sin(angle))
        row["entry_hour_utc_cos"] = float(np.cos(angle))
        row["entry_weekday_utc"] = weekday
        row["entry_is_weekend"] = 1 if weekday >= 5 else 0
    for key, value in outcome_row.items():
        if isinstance(value, (int, float)) and not pd.isna(value):
            row[f"feat_{key}"] = float(value)
    if feature_profile == "side_aware_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
        )
    elif feature_profile == "side_aware_clean_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=False,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
        )
    elif feature_profile == "side_aware_sparse_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
            directional_cols=_SPARSE_DIRECTIONAL_FEATURE_COLS,
        )
    elif feature_profile == "side_aware_sparse_returns_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
            directional_cols=_SPARSE_RETURNS_DIRECTIONAL_FEATURE_COLS,
        )
    elif feature_profile == "side_aware_sparse_context_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
            directional_cols=_SPARSE_CONTEXT_DIRECTIONAL_FEATURE_COLS,
        )
    elif feature_profile == "side_aware_bridge_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
            directional_cols=_BRIDGE_DIRECTIONAL_FEATURE_COLS,
        )
    elif feature_profile == "side_aware_sparse_regime_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
            directional_cols=_SPARSE_DIRECTIONAL_FEATURE_COLS,
        )
        _apply_directional_regime_gate_row(row)
    elif feature_profile == "side_aware_regime_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=True,
        )
        _apply_directional_regime_gate_row(row)
    elif feature_profile == "signed_directional_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=False,
            include_market_edge=False,
            include_expected_edge=False,
            include_directional_signed=True,
        )
    elif feature_profile == "signed_directional_clean_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=False,
            include_side_probability=False,
            include_market_edge=False,
            include_expected_edge=False,
            include_directional_signed=True,
        )
    elif feature_profile == "signed_directional_sparse_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=False,
            include_side_probability=False,
            include_market_edge=False,
            include_expected_edge=False,
            include_directional_signed=True,
            directional_cols=_SPARSE_DIRECTIONAL_FEATURE_COLS,
        )
    elif feature_profile == "signed_directional_regime_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=False,
            include_side_probability=False,
            include_market_edge=False,
            include_expected_edge=False,
            include_directional_signed=True,
            directional_cols=_SPARSE_DIRECTIONAL_FEATURE_COLS,
        )
        _apply_directional_regime_gate_row(row)
    elif feature_profile == "switch_v1":
        pass
    elif feature_profile == "signed_core_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=False,
            include_market_edge=False,
            include_expected_edge=False,
            include_directional_signed=False,
        )
    elif feature_profile == "side_prob_v1":
        _augment_side_aware_row(
            row,
            include_action_alignment=True,
            include_side_probability=True,
            include_market_edge=True,
            include_expected_edge=True,
            include_directional_signed=False,
        )
    elif feature_profile != "baseline":
        raise RuntimeError(f"Unsupported meta-filter feature profile: {feature_profile}")
    return row


def _maybe_float(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_directional_regime_strength(
    *,
    signal: float,
    accel: float | None,
    values: dict[str, Any],
) -> float:
    signal_abs = abs(float(signal))
    accel_abs = abs(float(accel)) if accel is not None else 0.0
    vol_ratio_30_120 = _maybe_float(values, "feat_ctx_btc_vol_ratio_30_120")
    if vol_ratio_30_120 is None:
        vol_ratio_30_120 = _maybe_float(values, "ctx_btc_vol_ratio_30_120") or 0.0
    vol_ratio_60_300 = _maybe_float(values, "feat_ctx_btc_vol_ratio_60_300")
    if vol_ratio_60_300 is None:
        vol_ratio_60_300 = _maybe_float(values, "ctx_btc_vol_ratio_60_300") or 0.0
    vol_component = float(np.clip(max(vol_ratio_30_120, vol_ratio_60_300) - 1.0, 0.0, 1.0))
    signal_component = float(np.clip(signal_abs / 25.0, 0.0, 1.0))
    accel_component = float(np.clip(accel_abs / 8.0, 0.0, 1.0))
    return float(np.clip(0.5 * signal_component + 0.3 * accel_component + 0.2 * vol_component, 0.0, 1.0))


def _apply_directional_regime_gate_row(row: dict[str, Any]) -> None:
    strength = compute_directional_regime_strength(
        signal=_maybe_float(row, "entry_signal") or 0.0,
        accel=_maybe_float(row, "entry_accel"),
        values=row,
    )
    row["entry_directional_regime_strength"] = strength
    row["entry_directional_regime_active"] = 1 if strength >= 0.5 else 0
    for key in [name for name in row if name.startswith("entry_side_signed_")]:
        value = _maybe_float(row, key)
        if value is None:
            continue
        row[key] = value * strength


def _augment_side_aware_row(
    row: dict[str, Any],
    *,
    include_action_alignment: bool,
    include_side_probability: bool,
    include_market_edge: bool,
    include_expected_edge: bool,
    include_directional_signed: bool,
    directional_cols: list[str] | None = None,
) -> None:
    side_yes = int(row.get("entry_side_yes", 0)) == 1
    side_sign = 1.0 if side_yes else -1.0
    outcome_sign = 1.0 if int(row.get("entry_outcome_action_yes", 0)) == 1 else (
        -1.0 if int(row.get("entry_outcome_action_no", 0)) == 1 else 0.0
    )
    signal = _maybe_float(row, "entry_signal") or 0.0
    accel = _maybe_float(row, "entry_accel") or 0.0

    row["entry_side_sign"] = side_sign
    row["entry_signal_abs"] = abs(signal)
    row["entry_signal_signed"] = signal * side_sign
    row["entry_accel_abs"] = abs(accel)
    row["entry_accel_signed"] = accel * side_sign
    if include_action_alignment:
        row["entry_outcome_action_alignment"] = outcome_sign * side_sign
        row["entry_outcome_action_match"] = 1 if outcome_sign == side_sign else 0
        row["entry_outcome_action_oppose"] = 1 if outcome_sign == -side_sign else 0
        row["entry_outcome_action_nonflat"] = 1 if outcome_sign != 0.0 else 0

    p_yes = _maybe_float(row, "feat_p_yes")
    p_no = _maybe_float(row, "feat_p_no")
    if include_side_probability and p_yes is not None and p_no is not None:
        entry_side_prob = p_yes if side_yes else p_no
        opp_side_prob = p_no if side_yes else p_yes
        row["entry_side_prob"] = entry_side_prob
        row["entry_side_prob_centered"] = entry_side_prob - 0.5
        row["entry_side_prob_advantage"] = entry_side_prob - opp_side_prob
        row["entry_side_prob_x_signal_abs"] = entry_side_prob * row["entry_signal_abs"]

    implied_yes = _maybe_float(row, "feat_market_implied_yes_mid")
    if include_market_edge and implied_yes is not None:
        implied_no = _maybe_float(row, "feat_market_implied_no_mid")
        if implied_no is None:
            implied_no = 1.0 - implied_yes
        entry_side_implied = implied_yes if side_yes else implied_no
        row["entry_side_market_implied_prob"] = entry_side_implied
        row["entry_side_market_implied_centered"] = entry_side_implied - 0.5
        if "entry_side_prob" in row:
            row["entry_side_prob_edge_vs_market"] = row["entry_side_prob"] - entry_side_implied

    edge_yes = _maybe_float(row, "feat_expected_edge_yes")
    edge_no = _maybe_float(row, "feat_expected_edge_no")
    if include_expected_edge and edge_yes is not None and edge_no is not None:
        entry_side_edge = edge_yes if side_yes else edge_no
        opp_side_edge = edge_no if side_yes else edge_yes
        row["entry_side_expected_edge"] = entry_side_edge
        row["entry_side_expected_edge_opp"] = opp_side_edge
        row["entry_side_expected_edge_net"] = entry_side_edge - opp_side_edge
        row["entry_side_expected_edge_x_signal_abs"] = entry_side_edge * row["entry_signal_abs"]

    if include_directional_signed:
        directional_feature_cols = directional_cols or [
            "feat_anchor_btc_return_open_bps",
            "feat_anchor_btc_return_open_per_age_bps",
            "feat_anchor_implied_yes_delta_open",
            "feat_anchor_implied_yes_delta_open_per_age",
            "feat_anchor_implied_yes_dir_align",
            "feat_imbalance_gap",
            "feat_pm_implied_yes_mid_delta_5s",
            "feat_pm_implied_yes_mid_delta_15s",
            "feat_pm_implied_yes_mid_delta_30s",
            "feat_pm_imbalance_gap_delta_5s",
            "feat_pm_imbalance_gap_delta_15s",
            "feat_pm_imbalance_gap_delta_30s",
            "feat_btc_delta_10s",
            "feat_btc_delta_20s",
            "feat_btc_delta_30s",
            "feat_btc_delta_60s",
            "feat_ctx_btc_delta_90s",
            "feat_ctx_btc_delta_120s",
            "feat_ctx_btc_delta_300s",
            "feat_ctx_btc_return_bps_90s",
            "feat_ctx_btc_return_bps_120s",
            "feat_ctx_btc_return_bps_300s",
        ]
        for col in directional_feature_cols:
            value = _maybe_float(row, col)
            if value is None:
                continue
            row[f"entry_side_signed_{col.removeprefix('feat_')}"] = value * side_sign


def score_meta_filter_row(
    *,
    artifact: dict[str, Any],
    outcome_row: dict[str, Any],
    side: str,
    signal: float,
    accel: float | None,
) -> float:
    artifact_type = _meta_artifact_type(artifact)
    if artifact_type == "switch_v1":
        gate = dict(artifact.get("switch_gate") or {})
        mode = str(gate.get("mode") or "directional_regime_strength_v1")
        if mode != "directional_regime_strength_v1":
            raise RuntimeError(f"Unsupported switch gate mode: {mode}")
        strength_threshold = float(gate.get("strength_threshold", 0.5))
        strength = compute_directional_regime_strength(
            signal=signal,
            accel=accel,
            values=outcome_row,
        )
        selected_artifact = artifact["secondary_artifact"] if strength >= strength_threshold else artifact["primary_artifact"]
        return score_meta_filter_row(
            artifact=selected_artifact,
            outcome_row=outcome_row,
            side=side,
            signal=signal,
            accel=accel,
        )

    feature_cols = list(artifact["feature_columns"])
    base = build_meta_feature_row(
        outcome_row=outcome_row,
        side=side,
        signal=signal,
        accel=accel,
        feature_profile=str(artifact.get("feature_profile", "baseline")),
    )
    fill_values = {str(k): float(v) for k, v in dict(artifact["fill_values"]).items()}
    payload = {col: base.get(col, fill_values.get(col, 0.0)) for col in feature_cols}
    frame = pd.DataFrame([payload], columns=feature_cols)
    prob = artifact["model"].predict_proba(frame)[0, 1]
    return float(prob)
