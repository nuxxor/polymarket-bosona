from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass

from polymarket_bot.analysis.recurring_family import (
    FamilyObservation,
    PolicyRow,
    WindowStateRow,
    build_policy_rows,
    build_window_state_rows,
)


DEFAULT_ALERT_FAMILIES = (
    "commodity_hit_barrier",
    "weekly_stock_finish_above",
    "inflation_release_band",
    "social_count",
    "opening_weekend_box_office",
)


def _candidate_key(family_type: str, event_title: str, consensus_label: str) -> str:
    return f"{family_type}|{event_title}|{consensus_label}"


def _delta_key(
    family_type: str,
    previous_snapshot_id: str,
    snapshot_id: str,
    previous_consensus_label: str,
    consensus_label: str,
) -> str:
    return (
        f"{family_type}|{previous_snapshot_id}|{snapshot_id}|"
        f"{previous_consensus_label}|{consensus_label}"
    )


@dataclass(frozen=True)
class AlertRow:
    candidate_key: str
    family_type: str
    snapshot_id: str
    policy_decision: str
    priority_tier: str
    window_state: str
    alert_status: str
    alert_score: float
    event_title: str
    consensus_label: str
    consensus_no: float
    consensus_liquidity: float
    accept_no_low: float
    accept_no_high: float
    accept_min_liquidity: float
    price_gap: float
    liquidity_gap: float
    risk_flags: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class AlertDeltaRow:
    delta_key: str
    family_type: str
    previous_snapshot_id: str
    snapshot_id: str
    transition: str
    previous_alert_status: str
    alert_status: str
    previous_window_state: str
    window_state: str
    delta_score: float
    previous_event_title: str
    previous_consensus_label: str
    previous_consensus_no: float
    previous_consensus_liquidity: float
    event_title: str
    consensus_label: str
    consensus_no: float
    consensus_liquidity: float
    note: str


@dataclass(frozen=True)
class AlertSummaryRow:
    family_type: str
    alert_status: str
    count: int
    top_candidate_key: str
    top_event_title: str
    top_consensus_label: str
    top_alert_score: float


@dataclass(frozen=True)
class DeltaSummaryRow:
    family_type: str
    transition: str
    count: int
    top_delta_key: str
    top_previous_snapshot_id: str
    top_snapshot_id: str
    top_delta_score: float


@dataclass(frozen=True)
class FreshAlertRow:
    candidate_key: str
    change_type: str
    family_type: str
    previous_alert_status: str
    alert_status: str
    previous_window_state: str
    window_state: str
    event_title: str
    consensus_label: str
    consensus_no: float
    consensus_liquidity: float
    note: str


@dataclass(frozen=True)
class FreshDeltaRow:
    delta_key: str
    change_type: str
    family_type: str
    transition: str
    previous_transition: str
    previous_snapshot_id: str
    snapshot_id: str
    note: str


def _status_for_candidate(
    *,
    policy: PolicyRow,
    window: WindowStateRow | None,
    observation: FamilyObservation,
    price_gap: float,
    liquidity_gap: float,
) -> str:
    risks = set(observation.risk_flags)
    if policy.decision == "reject":
        return "reject_family"
    if "immediate_resolve" in risks or "wide_spread" in risks:
        return "blocked"
    if price_gap == 0.0 and liquidity_gap == 0.0:
        if policy.decision == "accept":
            return "accept_now"
        return "watch_live"
    if price_gap <= 0.03 and liquidity_gap <= 0.30 * policy.accept_min_liquidity:
        return "near_miss"
    if window is not None and window.window_state == "fake_mid":
        return "fake_mid"
    if window is not None and window.window_state in {"thin", "dead"}:
        return "thin_board"
    return "wait_window"


def _status_score(status: str) -> float:
    return {
        "accept_now": 100.0,
        "watch_live": 86.0,
        "near_miss": 72.0,
        "wait_window": 56.0,
        "fake_mid": 36.0,
        "thin_board": 22.0,
        "blocked": 14.0,
        "reject_family": 0.0,
    }.get(status, 0.0)


def _alert_score(
    *,
    status: str,
    observation: FamilyObservation,
    price_gap: float,
    liquidity_gap: float,
    liquidity_floor: float,
) -> float:
    score = _status_score(status)
    score += max(0.0, 2.5 - 6.0 * abs(observation.consensus_no - 0.5))
    score += min(8.0, observation.consensus_liquidity / max(1.0, liquidity_floor) * 2.0)
    if liquidity_floor > 0:
        score -= 14.0 * (liquidity_gap / liquidity_floor)
    score -= 60.0 * price_gap
    if "resolution_source_unclear" in observation.risk_flags:
        score -= 2.0
    if "missing_book" in observation.risk_flags:
        score -= 1.0
    if "thin_liquidity" in observation.risk_flags:
        score -= 2.0
    return score


def _candidate_note(
    *,
    policy: PolicyRow,
    window: WindowStateRow | None,
    observation: FamilyObservation,
    price_gap: float,
    liquidity_gap: float,
    status: str,
) -> str:
    parts = [status]
    if window is not None:
        parts.append(f"window={window.window_state}")
    if price_gap > 0:
        parts.append(f"price_gap={price_gap:.3f}")
    if liquidity_gap > 0:
        parts.append(f"liq_gap={liquidity_gap:,.0f}")
    if observation.risk_flags:
        parts.append(f"risks={','.join(observation.risk_flags)}")
    return "; ".join(parts)


def build_alert_rows(
    observations: list[FamilyObservation],
    *,
    latest_snapshot_id: str,
    families: tuple[str, ...] = DEFAULT_ALERT_FAMILIES,
    top_n_per_family: int = 5,
) -> list[AlertRow]:
    policies = {
        row.family_type: row
        for row in build_policy_rows(observations, latest_snapshot_id=latest_snapshot_id)
        if row.family_type in families
    }
    windows = {
        (row.family_type, row.snapshot_id): row
        for row in build_window_state_rows(observations)
        if row.family_type in families
    }
    current_by_family: dict[str, list[FamilyObservation]] = defaultdict(list)
    for obs in observations:
        if obs.snapshot_id == latest_snapshot_id and obs.family_type in families:
            current_by_family[obs.family_type].append(obs)

    out: list[AlertRow] = []
    for family in families:
        policy = policies.get(family)
        if policy is None:
            continue
        window = windows.get((family, latest_snapshot_id))
        ranked: list[AlertRow] = []
        for obs in current_by_family.get(family, []):
            price_gap = 0.0
            if obs.consensus_no < policy.accept_no_low:
                price_gap = policy.accept_no_low - obs.consensus_no
            elif obs.consensus_no > policy.accept_no_high:
                price_gap = obs.consensus_no - policy.accept_no_high
            liquidity_gap = max(0.0, policy.accept_min_liquidity - obs.consensus_liquidity)
            status = _status_for_candidate(
                policy=policy,
                window=window,
                observation=obs,
                price_gap=price_gap,
                liquidity_gap=liquidity_gap,
            )
            score = _alert_score(
                status=status,
                observation=obs,
                price_gap=price_gap,
                liquidity_gap=liquidity_gap,
                liquidity_floor=policy.accept_min_liquidity,
            )
            ranked.append(
                AlertRow(
                    candidate_key=_candidate_key(family, obs.event_title, obs.consensus_label),
                    family_type=family,
                    snapshot_id=latest_snapshot_id,
                    policy_decision=policy.decision,
                    priority_tier=policy.priority_tier,
                    window_state=window.window_state if window else "unknown",
                    alert_status=status,
                    alert_score=score,
                    event_title=obs.event_title,
                    consensus_label=obs.consensus_label,
                    consensus_no=obs.consensus_no,
                    consensus_liquidity=obs.consensus_liquidity,
                    accept_no_low=policy.accept_no_low,
                    accept_no_high=policy.accept_no_high,
                    accept_min_liquidity=policy.accept_min_liquidity,
                    price_gap=price_gap,
                    liquidity_gap=liquidity_gap,
                    risk_flags=obs.risk_flags,
                    note=_candidate_note(
                        policy=policy,
                        window=window,
                        observation=obs,
                        price_gap=price_gap,
                        liquidity_gap=liquidity_gap,
                        status=status,
                    ),
                )
            )
        ranked.sort(key=lambda item: item.alert_score, reverse=True)
        out.extend(ranked[:top_n_per_family])
    out.sort(key=lambda item: item.alert_score, reverse=True)
    return out


def alert_to_dict(item: AlertRow) -> dict:
    payload = asdict(item)
    payload["risk_flags"] = ",".join(item.risk_flags)
    return payload


def _status_rank(status: str) -> int:
    return {
        "accept_now": 7,
        "watch_live": 6,
        "near_miss": 5,
        "wait_window": 4,
        "fake_mid": 3,
        "thin_board": 2,
        "blocked": 1,
        "reject_family": 0,
    }.get(status, -1)


def _window_rank(state: str) -> int:
    return {
        "open": 4,
        "narrow": 3,
        "fake_mid": 2,
        "thin": 1,
        "dead": 0,
        "unknown": -1,
    }.get(state, -1)


def _transition_label(previous: AlertRow, current: AlertRow) -> str:
    if previous.alert_status != "accept_now" and current.alert_status == "accept_now":
        return "upgraded_to_accept"
    if previous.alert_status not in {"watch_live", "near_miss", "accept_now"} and current.alert_status in {
        "watch_live",
        "near_miss",
        "accept_now",
    }:
        return "reopened_live"
    if previous.window_state != "open" and current.window_state == "open":
        return "window_opened"
    if previous.alert_status in {"accept_now", "watch_live", "near_miss"} and current.alert_status in {
        "wait_window",
        "fake_mid",
        "thin_board",
        "blocked",
        "reject_family",
    }:
        return "cooled_off"
    if previous.window_state == "open" and current.window_state in {"fake_mid", "thin", "dead"}:
        return "window_closed"
    if previous.alert_status != current.alert_status:
        return f"status:{previous.alert_status}->{current.alert_status}"
    if previous.window_state != current.window_state:
        return f"window:{previous.window_state}->{current.window_state}"
    return "unchanged"


def _transition_score(previous: AlertRow, current: AlertRow, transition: str) -> float:
    score = 0.0
    score += 8.0 * (_status_rank(current.alert_status) - _status_rank(previous.alert_status))
    score += 4.0 * (_window_rank(current.window_state) - _window_rank(previous.window_state))
    score += current.alert_score - previous.alert_score
    if transition == "upgraded_to_accept":
        score += 20.0
    elif transition == "reopened_live":
        score += 14.0
    elif transition == "window_opened":
        score += 10.0
    elif transition == "cooled_off":
        score -= 14.0
    elif transition == "window_closed":
        score -= 10.0
    return score


def _delta_note(previous: AlertRow, current: AlertRow, transition: str) -> str:
    parts = [transition]
    if previous.alert_status != current.alert_status:
        parts.append(f"status {previous.alert_status}->{current.alert_status}")
    if previous.window_state != current.window_state:
        parts.append(f"window {previous.window_state}->{current.window_state}")
    if previous.consensus_label != current.consensus_label:
        parts.append(
            f"line {previous.consensus_label} -> {current.consensus_label}"
        )
    return "; ".join(parts)


def build_alert_delta_rows(
    observations: list[FamilyObservation],
    *,
    families: tuple[str, ...] = DEFAULT_ALERT_FAMILIES,
    top_n_per_family: int = 5,
    interesting_only: bool = True,
) -> list[AlertDeltaRow]:
    snapshot_ids = sorted({obs.snapshot_id for obs in observations})
    if len(snapshot_ids) < 2:
        return []

    best_by_snapshot: dict[str, dict[str, AlertRow]] = {}
    for snapshot_id in snapshot_ids:
        prefix = [obs for obs in observations if obs.snapshot_id <= snapshot_id]
        alerts = build_alert_rows(
            prefix,
            latest_snapshot_id=snapshot_id,
            families=families,
            top_n_per_family=top_n_per_family,
        )
        by_family: dict[str, AlertRow] = {}
        for alert in alerts:
            if alert.family_type not in by_family:
                by_family[alert.family_type] = alert
        best_by_snapshot[snapshot_id] = by_family

    out: list[AlertDeltaRow] = []
    for prev_snapshot, snapshot_id in zip(snapshot_ids, snapshot_ids[1:]):
        prev_best = best_by_snapshot.get(prev_snapshot, {})
        curr_best = best_by_snapshot.get(snapshot_id, {})
        for family in families:
            previous = prev_best.get(family)
            current = curr_best.get(family)
            if previous is None or current is None:
                continue
            transition = _transition_label(previous, current)
            if interesting_only and transition == "unchanged":
                continue
            out.append(
                AlertDeltaRow(
                    delta_key=_delta_key(
                        family,
                        prev_snapshot,
                        snapshot_id,
                        previous.consensus_label,
                        current.consensus_label,
                    ),
                    family_type=family,
                    previous_snapshot_id=prev_snapshot,
                    snapshot_id=snapshot_id,
                    transition=transition,
                    previous_alert_status=previous.alert_status,
                    alert_status=current.alert_status,
                    previous_window_state=previous.window_state,
                    window_state=current.window_state,
                    delta_score=_transition_score(previous, current, transition),
                    previous_event_title=previous.event_title,
                    previous_consensus_label=previous.consensus_label,
                    previous_consensus_no=previous.consensus_no,
                    previous_consensus_liquidity=previous.consensus_liquidity,
                    event_title=current.event_title,
                    consensus_label=current.consensus_label,
                    consensus_no=current.consensus_no,
                    consensus_liquidity=current.consensus_liquidity,
                    note=_delta_note(previous, current, transition),
                )
            )
    out.sort(key=lambda item: item.delta_score, reverse=True)
    return out


def delta_to_dict(item: AlertDeltaRow) -> dict:
    return asdict(item)


def build_alert_summary_rows(alert_rows: list[AlertRow]) -> list[AlertSummaryRow]:
    grouped: dict[tuple[str, str], list[AlertRow]] = defaultdict(list)
    for row in alert_rows:
        grouped[(row.family_type, row.alert_status)].append(row)
    out: list[AlertSummaryRow] = []
    for (family_type, alert_status), bucket in grouped.items():
        bucket.sort(key=lambda item: item.alert_score, reverse=True)
        top = bucket[0]
        out.append(
            AlertSummaryRow(
                family_type=family_type,
                alert_status=alert_status,
                count=len(bucket),
                top_candidate_key=top.candidate_key,
                top_event_title=top.event_title,
                top_consensus_label=top.consensus_label,
                top_alert_score=top.alert_score,
            )
        )
    out.sort(key=lambda item: (item.family_type, -item.count, item.alert_status))
    return out


def build_delta_summary_rows(delta_rows: list[AlertDeltaRow]) -> list[DeltaSummaryRow]:
    grouped: dict[tuple[str, str], list[AlertDeltaRow]] = defaultdict(list)
    for row in delta_rows:
        grouped[(row.family_type, row.transition)].append(row)
    out: list[DeltaSummaryRow] = []
    for (family_type, transition), bucket in grouped.items():
        bucket.sort(key=lambda item: item.delta_score, reverse=True)
        top = bucket[0]
        out.append(
            DeltaSummaryRow(
                family_type=family_type,
                transition=transition,
                count=len(bucket),
                top_delta_key=top.delta_key,
                top_previous_snapshot_id=top.previous_snapshot_id,
                top_snapshot_id=top.snapshot_id,
                top_delta_score=top.delta_score,
            )
        )
    out.sort(key=lambda item: (item.family_type, -item.count, item.transition))
    return out


def build_fresh_alert_rows(
    alert_rows: list[AlertRow],
    *,
    previous_payload: list[dict[str, str]] | None = None,
) -> list[FreshAlertRow]:
    previous_payload = previous_payload or []
    previous_by_key = {row["candidate_key"]: row for row in previous_payload if row.get("candidate_key")}
    out: list[FreshAlertRow] = []
    for row in alert_rows:
        previous = previous_by_key.get(row.candidate_key)
        if previous is None:
            change_type = "new_candidate"
            prev_status = "missing"
            prev_window = "missing"
        else:
            prev_status = previous.get("alert_status", "unknown")
            prev_window = previous.get("window_state", "unknown")
            if prev_status == row.alert_status and prev_window == row.window_state:
                continue
            change_type = "changed"
        out.append(
            FreshAlertRow(
                candidate_key=row.candidate_key,
                change_type=change_type,
                family_type=row.family_type,
                previous_alert_status=prev_status,
                alert_status=row.alert_status,
                previous_window_state=prev_window,
                window_state=row.window_state,
                event_title=row.event_title,
                consensus_label=row.consensus_label,
                consensus_no=row.consensus_no,
                consensus_liquidity=row.consensus_liquidity,
                note=f"{change_type}: {prev_status}/{prev_window} -> {row.alert_status}/{row.window_state}",
            )
        )
    out.sort(key=lambda item: (_status_rank(item.alert_status), item.consensus_liquidity), reverse=True)
    return out


def build_fresh_delta_rows(
    delta_rows: list[AlertDeltaRow],
    *,
    previous_payload: list[dict[str, str]] | None = None,
) -> list[FreshDeltaRow]:
    previous_payload = previous_payload or []
    previous_by_key = {row["delta_key"]: row for row in previous_payload if row.get("delta_key")}
    out: list[FreshDeltaRow] = []
    for row in delta_rows:
        previous = previous_by_key.get(row.delta_key)
        if previous is None:
            change_type = "new_transition"
            previous_transition = "missing"
        else:
            previous_transition = previous.get("transition", "unknown")
            if previous_transition == row.transition:
                continue
            change_type = "transition_changed"
        out.append(
            FreshDeltaRow(
                delta_key=row.delta_key,
                change_type=change_type,
                family_type=row.family_type,
                transition=row.transition,
                previous_transition=previous_transition,
                previous_snapshot_id=row.previous_snapshot_id,
                snapshot_id=row.snapshot_id,
                note=f"{change_type}: {previous_transition} -> {row.transition}",
            )
        )
    out.sort(key=lambda item: (item.snapshot_id, item.family_type, item.transition), reverse=True)
    return out


def summary_to_dict(item: AlertSummaryRow | DeltaSummaryRow) -> dict:
    return asdict(item)


def fresh_to_dict(item: FreshAlertRow | FreshDeltaRow) -> dict:
    return asdict(item)
