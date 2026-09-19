from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _logit_clip(p_yes: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(p_yes, dtype=float), 1e-6, 1.0 - 1e-6)
    return np.log(clipped / (1.0 - clipped))


def apply_platt_scaler(scaler: Any, p_yes: np.ndarray) -> np.ndarray:
    if scaler is None:
        return np.asarray(p_yes, dtype=float)
    X = _logit_clip(p_yes).reshape(-1, 1)
    return scaler.predict_proba(X)[:, 1]


def apply_policy(
    frame: pd.DataFrame,
    p_yes: np.ndarray,
    policy: dict[str, Any],
) -> pd.DataFrame:
    p_yes = np.asarray(p_yes, dtype=float)
    p_no = 1.0 - p_yes
    cost_buffer = float(policy.get("cost_buffer", 0.0))
    min_edge_threshold = float(policy.get("min_edge_threshold", 0.0))
    min_aligned_imbalance = float(policy.get("min_aligned_imbalance", 0.0))
    max_spread_sum = float(policy.get("max_spread_sum", float("inf")))

    exp_edge_yes = p_yes - frame["yes_ask"].to_numpy(dtype=float) - cost_buffer
    exp_edge_no = p_no - frame["no_ask"].to_numpy(dtype=float) - cost_buffer

    action = np.full(len(frame), "FLAT", dtype=object)
    choose_yes = (exp_edge_yes >= min_edge_threshold) & (exp_edge_yes >= exp_edge_no)
    choose_no = (exp_edge_no >= min_edge_threshold) & (exp_edge_no > exp_edge_yes)
    action[choose_yes] = "YES"
    action[choose_no] = "NO"

    imbalance_gap = frame["imbalance_gap"].to_numpy(dtype=float)
    spread_sum = frame["yes_no_spread_sum"].to_numpy(dtype=float)
    gate_yes = (action != "YES") | (imbalance_gap >= min_aligned_imbalance)
    gate_no = (action != "NO") | (imbalance_gap <= -min_aligned_imbalance)
    gate_spread = (action == "FLAT") | (spread_sum <= max_spread_sum)
    action[~(gate_yes & gate_no & gate_spread)] = "FLAT"

    chosen_edge = np.where(
        action == "YES",
        exp_edge_yes,
        np.where(action == "NO", exp_edge_no, 0.0),
    )
    out = frame.copy()
    out["p_yes"] = p_yes
    out["p_no"] = p_no
    out["expected_edge_yes"] = exp_edge_yes
    out["expected_edge_no"] = exp_edge_no
    out["chosen_expected_edge"] = chosen_edge
    out["action"] = action
    return out


def load_outcome_artifact(path: str | Path) -> dict[str, Any]:
    try:
        import joblib
    except ImportError as exc:  # pragma: no cover - dependency failure is user-facing
        raise RuntimeError(
            "Missing dependency: joblib. Install project dependencies before loading artifacts."
        ) from exc

    artifact_path = Path(path)
    artifact = joblib.load(artifact_path)
    required = {"model", "feature_columns", "policy"}
    missing = sorted(required - set(artifact))
    if missing:
        raise RuntimeError(
            f"Invalid outcome artifact at {artifact_path}: missing keys {missing}"
        )
    artifact["artifact_path"] = str(artifact_path)
    return artifact


def score_outcome_frame(
    frame: pd.DataFrame,
    artifact: dict[str, Any],
    *,
    sort_output: bool = False,
) -> pd.DataFrame:
    feature_cols = list(artifact["feature_columns"])
    missing = [col for col in feature_cols if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing required feature columns for scoring: {missing}")

    raw_p = artifact["model"].predict_proba(frame[feature_cols])[:, 1]
    p_yes = apply_platt_scaler(artifact.get("platt_scaler"), raw_p)
    scored = apply_policy(frame, p_yes, artifact["policy"])
    if sort_output:
        scored = scored.sort_values(
            ["chosen_expected_edge", "tau_frac", "snapshot_ts_ms"],
            ascending=[False, True, False],
        ).reset_index(drop=True)
    return scored
