from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from polymarket_bot.analysis.market_catalog import GroupSummary


_MONTHS = (
    "january|february|march|april|may|june|july|august|september|october|november|december"
)
_DATE_TOKEN_RE = re.compile(
    rf"\b({_MONTHS})\b\s+\d{{1,2}}(?:\s*-\s*(?:{_MONTHS})\s+\d{{1,2}})?(?:,\s*\d{{4}})?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FamilyObservation:
    snapshot_id: str
    snapshot_date: str
    family_type: str
    family_template: str
    cadence: str
    event_title: str
    structure_type: str
    consensus_label: str
    consensus_no: float
    consensus_liquidity: float
    overall_score: float
    risk_flags: tuple[str, ...]
    catalyst_tags: tuple[str, ...]
    market_url: str


@dataclass(frozen=True)
class FamilyAggregate:
    family_key: str
    level: str
    family_type: str
    cadence: str
    snapshots_present: int
    total_instances: int
    templates_present: int
    current_instances: int
    current_sweet: int
    current_sweet_clean: int
    historical_sweet: int
    historical_sweet_clean: int
    current_max_liquidity: float
    current_avg_liquidity: float
    historical_max_liquidity: float
    historical_avg_liquidity: float
    current_avg_score: float
    historical_avg_score: float
    current_top_title: str
    common_risks: tuple[str, ...]
    common_tags: tuple[str, ...]
    recurring_score: float
    note: str


@dataclass(frozen=True)
class PlaybookRow:
    family_key: str
    level: str
    family_type: str
    cadence: str
    live_state: str
    structural_score: float
    live_score: float
    thesis_score: float
    current_sweet_clean: int
    historical_sweet_clean: int
    current_best_title: str
    current_best_label: str
    current_best_no: float
    current_best_liquidity: float
    current_best_url: str
    repricing_model: str
    entry_shape: str
    trade_style: str
    main_blocker: str
    common_risks: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class PolicyRow:
    family_type: str
    cadence: str
    decision: str
    priority_tier: str
    accept_no_low: float
    accept_no_high: float
    accept_min_liquidity: float
    historical_clean_count: int
    current_state: str
    current_best_title: str
    current_best_label: str
    current_best_no: float
    current_best_liquidity: float
    catalyst_window: str
    entry_logic: str
    reject_if: str
    rationale: str


@dataclass(frozen=True)
class WindowStateRow:
    family_type: str
    snapshot_id: str
    cadence: str
    total_count: int
    sweet_count: int
    sweet_clean_count: int
    median_clean_liquidity: float
    best_title: str
    best_label: str
    best_no: float
    best_liquidity: float
    window_state: str
    note: str


def _safe_token(raw: str) -> str:
    token = "".join(ch.lower() if ch.isalnum() else "_" for ch in raw)
    parts = [part for part in token.split("_") if part]
    return "_".join(parts) or "unknown"


def _normalize_title(raw: str) -> str:
    text = (raw or "").strip().lower()
    text = _DATE_TOKEN_RE.sub("<DATE>", text)
    text = re.sub(r"\b20\d{2}\b", "<YEAR>", text)
    text = re.sub(r"\b\d+(?:[.,]\d+)?\b", "<NUM>", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_ticker(title: str) -> str | None:
    match = re.search(r"\(([A-Z]+)\)", title)
    if match:
        return match.group(1).lower()
    return None


def infer_cadence(title: str) -> str:
    low = title.lower()
    if "finish week of" in low or "opening weekend" in low or "week of " in low:
        return "weekly"
    if low.startswith(
        (
            "january inflation",
            "february inflation",
            "march inflation",
            "april inflation",
            "may inflation",
            "june inflation",
            "july inflation",
            "august inflation",
            "september inflation",
            "october inflation",
            "november inflation",
            "december inflation",
        )
    ):
        return "monthly"
    if "monthly inflation" in low:
        return "monthly"
    if "one day after launch" in low:
        return "event_driven"
    if " end of " in low or re.search(r"\bin (january|february|march|april|may|june|july|august|september|october|november|december)\b", low):
        return "monthly"
    if " on " in low and _DATE_TOKEN_RE.search(low):
        return "daily"
    if "before <year>" in _normalize_title(low) or "in <year>" in _normalize_title(low):
        return "annual"
    return "unknown"


def infer_family(summary: GroupSummary) -> tuple[str, str, str] | None:
    title = summary.event_title
    low = title.lower()
    cadence = infer_cadence(title)

    if "highest temperature in " in low:
        city = low.split("highest temperature in ", 1)[1].split(" on ", 1)[0].strip()
        return "weather_daily_temp", f"weather_daily_temp:{_safe_token(city)}", "daily"

    if "tweets" in low:
        if low.startswith("elon musk"):
            return "social_count", "social_count:elon_tweets", "weekly"
        if "truth social posts" in low:
            return "social_count", "social_count:truth_social_posts", "weekly"
        return "social_count", "social_count:other", cadence

    if "opening weekend box office" in low:
        return "opening_weekend_box_office", "opening_weekend_box_office", "weekly"

    if low.startswith("will ") and " finish week of " in low and " above" in low:
        ticker = _extract_ticker(title) or _safe_token(title.split(" finish week", 1)[0].replace("Will ", ""))
        return "weekly_stock_finish_above", f"weekly_stock_finish_above:{ticker}", "weekly"

    if low.startswith("what will ") and " hit in " in low and _extract_ticker(title):
        ticker = _extract_ticker(title) or "unknown"
        return "monthly_stock_hit_barrier", f"monthly_stock_hit_barrier:{ticker}", "monthly"

    if low.startswith("will crude oil (cl) hit"):
        return "commodity_hit_barrier", "commodity_hit_barrier:crude_oil", cadence
    if low.startswith("will silver (si) hit"):
        return "commodity_hit_barrier", "commodity_hit_barrier:silver", cadence
    if low.startswith("will gold (gc) hit"):
        return "commodity_hit_barrier", "commodity_hit_barrier:gold", cadence

    if "fdv above" in low and "one day after launch" in low:
        return "launch_fdv_day1", "launch_fdv_day1", "event_driven"

    if "closing market cap above" in low and "ipo" in low:
        return "ipo_market_cap_threshold", "ipo_market_cap_threshold", "event_driven"

    if "monthly inflation" in low or re.match(rf"^({_MONTHS}) inflation ", low):
        if "us" in low and "annual" in low:
            return "inflation_release_band", "inflation_release_band:us_annual", "monthly"
        if "us" in low and "monthly" in low:
            return "inflation_release_band", "inflation_release_band:us_monthly", "monthly"
        if "argentina" in low and "monthly inflation" in low:
            return "inflation_release_band", "inflation_release_band:argentina_monthly", "monthly"
        return "inflation_release_band", f"inflation_release_band:{summary.structure_type}", "monthly"

    if "annual inflation" in low or "how high will inflation get in " in low:
        prefix = low.split(" annual inflation", 1)[0]
        template = _safe_token(prefix.replace("how high will ", "").replace(" get", "")) or summary.structure_type
        return "annual_inflation_band", f"annual_inflation_band:{template}", "annual"

    if low.startswith("what will fed rate hit"):
        return "macro_rate_barrier", "macro_rate_barrier", cadence

    if "how high will us unemployment go" in low:
        return "macro_band", "macro_band:unemployment", cadence

    if "what will happen before gta vi" in low:
        return "timeline_multi_event", "timeline_multi_event:gta6", "event_driven"

    return None


def build_observations(
    *,
    snapshot_id: str,
    snapshot_date: str,
    summaries: list[GroupSummary],
) -> list[FamilyObservation]:
    out: list[FamilyObservation] = []
    for summary in summaries:
        family = infer_family(summary)
        if family is None:
            continue
        family_type, family_template, cadence = family
        out.append(
            FamilyObservation(
                snapshot_id=snapshot_id,
                snapshot_date=snapshot_date,
                family_type=family_type,
                family_template=family_template,
                cadence=cadence,
                event_title=summary.event_title,
                structure_type=summary.structure_type,
                consensus_label=summary.consensus_label,
                consensus_no=float(summary.consensus_no),
                consensus_liquidity=float(summary.consensus_liquidity),
                overall_score=float(summary.overall_score),
                risk_flags=summary.risk_flags,
                catalyst_tags=summary.catalyst_tags,
                market_url=summary.market_url,
            )
        )
    return out


def _is_sweet(obs: FamilyObservation, *, min_liquidity: float = 5_000.0) -> bool:
    return 0.25 <= obs.consensus_no <= 0.75 and obs.consensus_liquidity >= min_liquidity


def _is_sweet_clean(obs: FamilyObservation, *, min_liquidity: float = 5_000.0) -> bool:
    if not _is_sweet(obs, min_liquidity=min_liquidity):
        return False
    bad = {"immediate_resolve", "wide_spread"}
    return not (bad & set(obs.risk_flags))


def _base_liquidity_floor(family_type: str) -> float:
    if family_type in {"opening_weekend_box_office", "social_count"}:
        return 8_000.0
    if family_type == "commodity_hit_barrier":
        return 15_000.0
    if family_type == "weekly_stock_finish_above":
        return 5_000.0
    if family_type == "launch_fdv_day1":
        return 15_000.0
    if family_type == "weather_daily_temp":
        return 5_000.0
    return 5_000.0


def _aggregate(
    observations: list[FamilyObservation],
    *,
    level: str,
    latest_snapshot_id: str,
) -> list[FamilyAggregate]:
    grouped: dict[str, list[FamilyObservation]] = defaultdict(list)
    for obs in observations:
        key = obs.family_type if level == "type" else obs.family_template
        grouped[key].append(obs)

    aggregates: list[FamilyAggregate] = []
    for key, bucket in grouped.items():
        if not bucket:
            continue
        family_type = bucket[0].family_type
        cadence = bucket[0].cadence
        liq_floor = _base_liquidity_floor(family_type)
        current = [obs for obs in bucket if obs.snapshot_id == latest_snapshot_id]
        if not current:
            continue
        current_sorted = sorted(current, key=lambda obs: (obs.consensus_liquidity, obs.overall_score), reverse=True)
        current_top = current_sorted[0]
        historical_sweet = sum(1 for obs in bucket if _is_sweet(obs, min_liquidity=liq_floor))
        historical_sweet_clean = sum(1 for obs in bucket if _is_sweet_clean(obs, min_liquidity=liq_floor))
        current_sweet = sum(1 for obs in current if _is_sweet(obs, min_liquidity=liq_floor))
        current_sweet_clean = sum(1 for obs in current if _is_sweet_clean(obs, min_liquidity=liq_floor))
        templates_present = len({obs.family_template for obs in bucket})
        snapshots_present = len({obs.snapshot_id for obs in bucket})
        current_avg_liquidity = sum(obs.consensus_liquidity for obs in current) / len(current)
        historical_avg_liquidity = sum(obs.consensus_liquidity for obs in bucket) / len(bucket)
        current_avg_score = sum(obs.overall_score for obs in current) / len(current)
        historical_avg_score = sum(obs.overall_score for obs in bucket) / len(bucket)
        current_max_liquidity = max(obs.consensus_liquidity for obs in current)
        historical_max_liquidity = max(obs.consensus_liquidity for obs in bucket)
        risk_counter = Counter(flag for obs in bucket for flag in obs.risk_flags)
        tag_counter = Counter(tag for obs in bucket for tag in obs.catalyst_tags)
        objective_penalty = 0.0
        if risk_counter["resolution_source_unclear"]:
            objective_penalty += 1.0
        if risk_counter["subjective_resolution"]:
            objective_penalty += 1.0
        if cadence == "event_driven":
            objective_penalty += 0.5
        recurring_score = (
            3.0 * snapshots_present
            + 1.5 * min(10, len(bucket))
            + 2.5 * current_sweet_clean
            + 1.5 * historical_sweet_clean
            + min(4.0, current_max_liquidity / 20_000.0)
            + min(3.0, current_avg_liquidity / 10_000.0)
            + min(2.0, historical_avg_score / 40.0)
            - objective_penalty
        )
        note = (
            f"{cadence} family; current sweet_clean={current_sweet_clean}, "
            f"historical sweet_clean={historical_sweet_clean}, liq_floor={liq_floor:,.0f}"
        )
        aggregates.append(
            FamilyAggregate(
                family_key=key,
                level=level,
                family_type=family_type,
                cadence=cadence,
                snapshots_present=snapshots_present,
                total_instances=len(bucket),
                templates_present=templates_present,
                current_instances=len(current),
                current_sweet=current_sweet,
                current_sweet_clean=current_sweet_clean,
                historical_sweet=historical_sweet,
                historical_sweet_clean=historical_sweet_clean,
                current_max_liquidity=current_max_liquidity,
                current_avg_liquidity=current_avg_liquidity,
                historical_max_liquidity=historical_max_liquidity,
                historical_avg_liquidity=historical_avg_liquidity,
                current_avg_score=current_avg_score,
                historical_avg_score=historical_avg_score,
                current_top_title=current_top.event_title,
                common_risks=tuple(flag for flag, _count in risk_counter.most_common(4)),
                common_tags=tuple(tag for tag, _count in tag_counter.most_common(4)),
                recurring_score=recurring_score,
                note=note,
            )
        )
    aggregates.sort(key=lambda item: item.recurring_score, reverse=True)
    return aggregates


def build_family_aggregates(
    observations: list[FamilyObservation],
    *,
    latest_snapshot_id: str,
) -> tuple[list[FamilyAggregate], list[FamilyAggregate]]:
    type_rows = _aggregate(observations, level="type", latest_snapshot_id=latest_snapshot_id)
    template_rows = _aggregate(observations, level="template", latest_snapshot_id=latest_snapshot_id)
    return type_rows, template_rows


def observation_to_dict(obs: FamilyObservation) -> dict:
    payload = asdict(obs)
    payload["risk_flags"] = ",".join(obs.risk_flags)
    payload["catalyst_tags"] = ",".join(obs.catalyst_tags)
    return payload


def aggregate_to_dict(item: FamilyAggregate) -> dict:
    payload = asdict(item)
    payload["common_risks"] = ",".join(item.common_risks)
    payload["common_tags"] = ",".join(item.common_tags)
    return payload


_FIXED_CADENCE = {"daily", "weekly", "monthly"}
_NON_CRYPTO_FIXED_FAMILIES = {
    "commodity_hit_barrier",
    "weekly_stock_finish_above",
    "monthly_stock_hit_barrier",
    "social_count",
    "opening_weekend_box_office",
    "weather_daily_temp",
    "inflation_release_band",
}


def _repricing_model(family_type: str) -> str:
    if family_type == "commodity_hit_barrier":
        return "Barrier reprices when the commodity drifts toward or away from a strike during the week/month."
    if family_type == "weekly_stock_finish_above":
        return "The weekly close line reprices as the stock migrates toward or away from the threshold into Friday."
    if family_type == "monthly_stock_hit_barrier":
        return "Touch barriers reprice with realized path volatility, but the board is often too thin to monetize."
    if family_type == "social_count":
        return "Post-count middle buckets break when posting cadence accelerates or stalls versus the expected weekly pace."
    if family_type == "opening_weekend_box_office":
        return "Presales, reviews, and Thursday previews shift the consensus weekend range before settle."
    if family_type == "weather_daily_temp":
        return "Forecast revisions move the center temperature bracket, but most ladders stay too thin."
    if family_type == "inflation_release_band":
        return "Consensus CPI/Inflation brackets reprice into the scheduled release as survey expectations move."
    return "Recurring catalyst reprices the consensus line."


def _entry_shape(family_type: str) -> str:
    if family_type in {"commodity_hit_barrier", "weekly_stock_finish_above", "monthly_stock_hit_barrier"}:
        return "Near-mid threshold or barrier, then exit after the line drifts out of the 40/60 to 60/40 zone."
    if family_type in {"social_count", "opening_weekend_box_office", "inflation_release_band"}:
        return "Consensus middle bucket or threshold while the market is still anchored near the expected range."
    if family_type == "weather_daily_temp":
        return "Only touch the most liquid center bracket; avoid anything with a wide spread."
    return "Take the consensus line only while it remains mid-priced and liquid."


def _trade_style(family_type: str, cadence: str) -> str:
    if family_type == "weather_daily_temp":
        return "daily swing"
    if family_type in {"social_count", "opening_weekend_box_office", "weekly_stock_finish_above"}:
        return "weekly swing"
    if family_type in {"commodity_hit_barrier", "inflation_release_band", "monthly_stock_hit_barrier"}:
        return "monthly swing"
    return f"{cadence} swing"


def _entry_window_text(family_type: str) -> str:
    if family_type == "commodity_hit_barrier":
        return "During the month when the underlying sits near an obvious round-number barrier."
    if family_type == "weekly_stock_finish_above":
        return "Early-to-mid week, before Friday close gamma collapses the line."
    if family_type == "monthly_stock_hit_barrier":
        return "Only early in the month if the barrier sits near spot and the board is unusually liquid."
    if family_type == "social_count":
        return "Early in the counting window while the expected posting pace still anchors the middle bucket."
    if family_type == "opening_weekend_box_office":
        return "From presales into Thursday previews, before consensus locks in."
    if family_type == "weather_daily_temp":
        return "Only when forecasts disagree and a center bucket still has real depth."
    if family_type == "inflation_release_band":
        return "In the days before the scheduled release while consensus is still clustered."
    return "While the recurring catalyst has not fully repriced the line."


def _thesis_bonus(family_type: str) -> float:
    return {
        "commodity_hit_barrier": 2.0,
        "weekly_stock_finish_above": 1.8,
        "inflation_release_band": 1.5,
        "social_count": 1.2,
        "opening_weekend_box_office": 1.0,
        "monthly_stock_hit_barrier": 0.6,
        "weather_daily_temp": -0.5,
    }.get(family_type, 0.0)


def _risk_penalty(flags: tuple[str, ...]) -> float:
    penalty = 0.0
    if "subjective_resolution" in flags:
        penalty += 3.0
    if "resolution_source_unclear" in flags:
        penalty += 1.5
    if "thin_liquidity" in flags:
        penalty += 1.25
    if "wide_spread" in flags:
        penalty += 1.0
    if "missing_book" in flags:
        penalty += 0.5
    return penalty


def _pick_best_current(
    current: list[FamilyObservation],
    *,
    liq_floor: float,
) -> FamilyObservation | None:
    if not current:
        return None
    sweet_clean = [obs for obs in current if _is_sweet_clean(obs, min_liquidity=liq_floor)]
    if sweet_clean:
        sweet_clean.sort(
            key=lambda obs: (
                abs(obs.consensus_no - 0.5),
                -obs.consensus_liquidity,
                -obs.overall_score,
            ),
        )
        return sweet_clean[0]
    sweet = [obs for obs in current if _is_sweet(obs, min_liquidity=liq_floor)]
    if sweet:
        sweet.sort(
            key=lambda obs: (
                abs(obs.consensus_no - 0.5),
                -obs.consensus_liquidity,
                -obs.overall_score,
            ),
        )
        return sweet[0]
    return sorted(
        current,
        key=lambda obs: (
            abs(obs.consensus_no - 0.5),
            -obs.consensus_liquidity,
            -obs.overall_score,
        ),
    )[0]


def _live_state(item: FamilyAggregate) -> str:
    if item.current_sweet_clean > 0:
        return "live_now"
    if item.current_sweet > 0:
        return "monitor_spread"
    if item.historical_sweet_clean > 0:
        return "wait_for_entry"
    return "low_quality"


def _main_blocker(item: FamilyAggregate) -> str:
    if item.current_sweet_clean == 0 and item.historical_sweet_clean > 0:
        return "structure repeats, but the live board has no clean sweet spot"
    if "subjective_resolution" in item.common_risks:
        return "resolution is subjective"
    if "resolution_source_unclear" in item.common_risks:
        return "rules or oracle source are not clean enough"
    if "thin_liquidity" in item.common_risks:
        return "sweet lines are too thin"
    if "wide_spread" in item.common_risks:
        return "spread likely kills short-horizon exits"
    return "no major blocker"


def build_playbook_rows(
    observations: list[FamilyObservation],
    *,
    latest_snapshot_id: str,
    level: str = "type",
    fixed_cadence_only: bool = True,
    non_crypto_only: bool = True,
) -> list[PlaybookRow]:
    aggregates = _aggregate(observations, level=level, latest_snapshot_id=latest_snapshot_id)
    current_by_key: dict[str, list[FamilyObservation]] = defaultdict(list)
    for obs in observations:
        if obs.snapshot_id != latest_snapshot_id:
            continue
        key = obs.family_type if level == "type" else obs.family_template
        current_by_key[key].append(obs)

    rows: list[PlaybookRow] = []
    for item in aggregates:
        if fixed_cadence_only and item.cadence not in _FIXED_CADENCE:
            continue
        if non_crypto_only and item.family_type not in _NON_CRYPTO_FIXED_FAMILIES:
            continue
        liq_floor = _base_liquidity_floor(item.family_type)
        best_current = _pick_best_current(current_by_key.get(item.family_key, []), liq_floor=liq_floor)
        if best_current is None:
            continue
        state = _live_state(item)
        cadence_bonus = {"daily": 2.0, "weekly": 1.6, "monthly": 1.2}.get(item.cadence, 0.0)
        structural_score = (
            2.0 * item.snapshots_present
            + 1.25 * min(12, item.historical_sweet_clean)
            + min(4.0, item.historical_max_liquidity / 25_000.0)
            + min(3.0, item.historical_avg_liquidity / 12_000.0)
            + cadence_bonus
            + _thesis_bonus(item.family_type)
            - _risk_penalty(item.common_risks)
        )
        live_score = (
            {"live_now": 4.0, "monitor_spread": 2.0, "wait_for_entry": 0.75, "low_quality": 0.0}[state]
            + min(4.0, best_current.consensus_liquidity / 15_000.0)
            + max(0.0, 2.0 - 5.0 * abs(best_current.consensus_no - 0.5))
            + 0.5 * min(4, item.current_sweet_clean)
        )
        thesis_score = structural_score + live_score
        rows.append(
            PlaybookRow(
                family_key=item.family_key,
                level=level,
                family_type=item.family_type,
                cadence=item.cadence,
                live_state=state,
                structural_score=structural_score,
                live_score=live_score,
                thesis_score=thesis_score,
                current_sweet_clean=item.current_sweet_clean,
                historical_sweet_clean=item.historical_sweet_clean,
                current_best_title=best_current.event_title,
                current_best_label=best_current.consensus_label,
                current_best_no=best_current.consensus_no,
                current_best_liquidity=best_current.consensus_liquidity,
                current_best_url=best_current.market_url,
                repricing_model=_repricing_model(item.family_type),
                entry_shape=_entry_shape(item.family_type),
                trade_style=_trade_style(item.family_type, item.cadence),
                main_blocker=_main_blocker(item),
                common_risks=item.common_risks,
                note=item.note,
            )
        )

    rows.sort(key=lambda item: item.thesis_score, reverse=True)
    return rows


def playbook_to_dict(item: PlaybookRow) -> dict:
    payload = asdict(item)
    payload["common_risks"] = ",".join(item.common_risks)
    return payload


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return ordered[lower]
    weight = pos - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _policy_decision(item: PlaybookRow) -> tuple[str, str]:
    if item.family_type == "commodity_hit_barrier":
        return ("accept", "core")
    if item.family_type in {"social_count", "inflation_release_band"}:
        return ("watch", "secondary")
    if item.family_type == "weekly_stock_finish_above":
        return ("watch", "core_watch")
    if item.family_type == "opening_weekend_box_office":
        return ("watch", "opportunistic")
    if item.family_type in {"monthly_stock_hit_barrier", "weather_daily_temp"}:
        return ("reject", "pass")
    return ("watch", "secondary")


def _reject_if_text(family_type: str) -> str:
    if family_type == "commodity_hit_barrier":
        return "Reject when the line is already outside 0.30-0.70 NO or when rules stay ambiguous."
    if family_type == "weekly_stock_finish_above":
        return "Reject until a real mid-priced weekly close line prints with at least ~10k liquidity."
    if family_type == "social_count":
        return "Reject when the center bucket loses book depth or the rules/oracle page is vague."
    if family_type == "inflation_release_band":
        return "Reject if liquidity is below ~6k or the market has already repriced far from consensus."
    if family_type == "opening_weekend_box_office":
        return "Reject when the best mid bucket is below ~8k liquidity or reviews have already resolved consensus."
    if family_type == "monthly_stock_hit_barrier":
        return "Reject most lines; fake mid prices with tiny books dominate this family."
    if family_type == "weather_daily_temp":
        return "Reject almost all ladders unless a center bracket has unusually deep real bids."
    return "Reject if liquidity and price shape do not match the historical sweet spot."


def build_policy_rows(
    observations: list[FamilyObservation],
    *,
    latest_snapshot_id: str,
) -> list[PolicyRow]:
    playbook_rows = build_playbook_rows(
        observations,
        latest_snapshot_id=latest_snapshot_id,
        level="type",
    )
    current_by_family: dict[str, list[FamilyObservation]] = defaultdict(list)
    historical_by_family: dict[str, list[FamilyObservation]] = defaultdict(list)
    for obs in observations:
        historical_by_family[obs.family_type].append(obs)
        if obs.snapshot_id == latest_snapshot_id:
            current_by_family[obs.family_type].append(obs)

    rows: list[PolicyRow] = []
    for item in playbook_rows:
        family = item.family_type
        liq_floor = _base_liquidity_floor(family)
        hist_bucket = historical_by_family.get(family, [])
        good = [obs for obs in hist_bucket if _is_sweet_clean(obs, min_liquidity=liq_floor)]
        if good:
            no_low = _percentile([obs.consensus_no for obs in good], 0.25)
            no_high = _percentile([obs.consensus_no for obs in good], 0.75)
            min_liq = max(liq_floor, _percentile([obs.consensus_liquidity for obs in good], 0.25))
        else:
            no_low = 0.40
            no_high = 0.60
            min_liq = liq_floor
        decision, tier = _policy_decision(item)
        rationale = (
            f"{item.family_type} is {item.live_state}; historical clean={item.historical_sweet_clean}, "
            f"best live line {item.current_best_label} at NO {item.current_best_no:.3f} with "
            f"liq {item.current_best_liquidity:,.0f}."
        )
        rows.append(
            PolicyRow(
                family_type=family,
                cadence=item.cadence,
                decision=decision,
                priority_tier=tier,
                accept_no_low=round(no_low, 4),
                accept_no_high=round(no_high, 4),
                accept_min_liquidity=round(min_liq, 2),
                historical_clean_count=len(good),
                current_state=item.live_state,
                current_best_title=item.current_best_title,
                current_best_label=item.current_best_label,
                current_best_no=round(item.current_best_no, 4),
                current_best_liquidity=round(item.current_best_liquidity, 2),
                catalyst_window=_entry_window_text(family),
                entry_logic=item.entry_shape,
                reject_if=_reject_if_text(family),
                rationale=rationale,
            )
        )
    rows.sort(
        key=lambda item: (
            {"accept": 0, "watch": 1, "reject": 2}[item.decision],
            {"core": 0, "core_watch": 1, "secondary": 2, "opportunistic": 3, "pass": 4}[item.priority_tier],
            -item.historical_clean_count,
            -item.current_best_liquidity,
        )
    )
    return rows


def policy_to_dict(item: PolicyRow) -> dict:
    return asdict(item)


def build_window_state_rows(
    observations: list[FamilyObservation],
    *,
    fixed_cadence_only: bool = True,
    non_crypto_only: bool = True,
) -> list[WindowStateRow]:
    grouped: dict[tuple[str, str], list[FamilyObservation]] = defaultdict(list)
    for obs in observations:
        if fixed_cadence_only and obs.cadence not in _FIXED_CADENCE:
            continue
        if non_crypto_only and obs.family_type not in _NON_CRYPTO_FIXED_FAMILIES:
            continue
        grouped[(obs.family_type, obs.snapshot_id)].append(obs)

    rows: list[WindowStateRow] = []
    for (family_type, snapshot_id), bucket in sorted(grouped.items()):
        liq_floor = _base_liquidity_floor(family_type)
        sweet = [obs for obs in bucket if _is_sweet(obs, min_liquidity=0.0)]
        sweet_clean = [obs for obs in bucket if _is_sweet_clean(obs, min_liquidity=liq_floor)]
        if sweet_clean:
            best = sorted(
                sweet_clean,
                key=lambda obs: (
                    abs(obs.consensus_no - 0.5),
                    -obs.consensus_liquidity,
                ),
            )[0]
            median_clean_liq = _percentile([obs.consensus_liquidity for obs in sweet_clean], 0.5)
        elif sweet:
            best = sorted(
                sweet,
                key=lambda obs: (
                    abs(obs.consensus_no - 0.5),
                    -obs.consensus_liquidity,
                ),
            )[0]
            median_clean_liq = 0.0
        else:
            best = max(bucket, key=lambda obs: obs.consensus_liquidity)
            median_clean_liq = 0.0

        if len(sweet_clean) >= 2 and median_clean_liq >= liq_floor:
            state = "open"
        elif len(sweet_clean) >= 1:
            state = "narrow"
        elif len(sweet) >= 3:
            state = "fake_mid"
        elif len(sweet) >= 1:
            state = "thin"
        else:
            state = "dead"

        note = (
            f"sweet={len(sweet)}, sweet_clean={len(sweet_clean)}, "
            f"liq_floor={liq_floor:,.0f}, median_clean_liq={median_clean_liq:,.0f}"
        )
        rows.append(
            WindowStateRow(
                family_type=family_type,
                snapshot_id=snapshot_id,
                cadence=bucket[0].cadence,
                total_count=len(bucket),
                sweet_count=len(sweet),
                sweet_clean_count=len(sweet_clean),
                median_clean_liquidity=round(median_clean_liq, 2),
                best_title=best.event_title,
                best_label=best.consensus_label,
                best_no=round(best.consensus_no, 4),
                best_liquidity=round(best.consensus_liquidity, 2),
                window_state=state,
                note=note,
            )
        )
    return rows


def window_state_to_dict(item: WindowStateRow) -> dict:
    return asdict(item)


def snapshot_id_from_path(path: Path) -> str:
    match = re.search(r"(\d{8})", path.name)
    return match.group(1) if match else _safe_token(path.stem)
