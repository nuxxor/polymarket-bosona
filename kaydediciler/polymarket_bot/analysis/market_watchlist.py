from __future__ import annotations

from dataclasses import asdict, dataclass

from polymarket_bot.analysis.market_catalog import GroupSummary


STRICT_CLONE_FAMILIES = {
    "btc_daily_range",
    "eth_daily_range",
    "sol_daily_range",
    "xrp_daily_range",
}

TRIGGER_CLONE_FAMILIES = {
    "btc_daily_above",
    "eth_daily_above",
    "sol_daily_above",
    "xrp_daily_above",
}

SEMI_CLONE_FAMILIES = {
    "crude_settle_range",
    "gold_settle_range",
    "silver_settle_range",
    "spx_settle_range",
    "inflation_range",
    "inflation_ladder",
    "election_margin_ladder",
    "election_count_ladder",
    "fed_cuts_ladder",
    "social_count_ladder",
    "shipping_count_ladder",
    "box_office_count_ladder",
}

FAMILY_LIQUIDITY_MIN = {
    "btc_daily_range": 7_500.0,
    "eth_daily_range": 5_000.0,
    "sol_daily_range": 2_500.0,
    "xrp_daily_range": 2_500.0,
    "btc_daily_above": 15_000.0,
    "eth_daily_above": 15_000.0,
    "sol_daily_above": 8_000.0,
    "xrp_daily_above": 8_000.0,
    "crude_settle_range": 10_000.0,
    "gold_settle_range": 10_000.0,
    "silver_settle_range": 10_000.0,
    "spx_settle_range": 10_000.0,
    "inflation_range": 8_000.0,
    "inflation_ladder": 8_000.0,
    "election_margin_ladder": 10_000.0,
    "election_count_ladder": 10_000.0,
    "fed_cuts_ladder": 20_000.0,
    "social_count_ladder": 10_000.0,
    "shipping_count_ladder": 10_000.0,
    "box_office_count_ladder": 10_000.0,
}


@dataclass(frozen=True)
class WatchCandidate:
    tier: str
    family: str
    actionability: str
    rank_score: float
    overall_score: float
    family_liquidity_min: float
    event_title: str
    market_url: str
    structure_type: str
    consensus_label: str
    consensus_no: float
    consensus_liquidity: float
    catalyst_tags: tuple[str, ...]
    risk_flags: tuple[str, ...]
    blockers: tuple[str, ...]
    note: str


def infer_watch_family(summary: GroupSummary) -> str | None:
    title = summary.event_title.lower()
    if summary.structure_type == "range_ladder":
        if title.startswith("bitcoin price on "):
            return "btc_daily_range"
        if title.startswith("ethereum price on "):
            return "eth_daily_range"
        if title.startswith("solana price on "):
            return "sol_daily_range"
        if title.startswith("xrp price on "):
            return "xrp_daily_range"
        if "crude oil" in title and "settle" in title:
            return "crude_settle_range"
        if "gold" in title and "settle" in title:
            return "gold_settle_range"
        if "silver" in title and "settle" in title:
            return "silver_settle_range"
        if ("s&p 500" in title or "spx" in title) and ("close" in title or "settle" in title):
            return "spx_settle_range"
        if "inflation" in title or "cpi" in title or "pce" in title:
            return "inflation_range"
        return None

    if summary.structure_type == "single_binary":
        if title.startswith("bitcoin above ___ on "):
            return "btc_daily_above"
        if title.startswith("ethereum above ___ on "):
            return "eth_daily_above"
        if title.startswith("solana above ___ on "):
            return "sol_daily_above"
        if title.startswith("xrp above ___ on "):
            return "xrp_daily_above"

    if summary.structure_type not in {"numeric_ladder", "count_ladder"}:
        return None

    if "fed rate cuts" in title:
        return "fed_cuts_ladder"
    if "tweets" in title or "truth social posts" in title:
        return "social_count_ladder"
    if "margin of victory" in title or "popular vote margin" in title:
        return "election_margin_ladder"
    if (
        "seats won" in title
        or "house seats" in title
        or "governors" in title
        or "turnout" in title
        or "popular vote" in title
    ):
        return "election_count_ladder"
    if "inflation" in title or "cpi" in title or "pce" in title:
        return "inflation_ladder"
    if "ships transit" in title or "ships transiting" in title:
        return "shipping_count_ladder"
    if "box office" in title:
        return "box_office_count_ladder"
    return None


def _tier_for_family(family: str) -> str:
    if family in STRICT_CLONE_FAMILIES:
        return "strict_clone"
    if family in TRIGGER_CLONE_FAMILIES:
        return "trigger_clone"
    if family in SEMI_CLONE_FAMILIES:
        return "semi_clone"
    return "ignore"


def _build_blockers(summary: GroupSummary, *, family_liquidity_min: float) -> tuple[str, ...]:
    blockers = list(summary.risk_flags)
    if summary.consensus_liquidity < family_liquidity_min:
        blockers.append("below_family_liquidity_min")
    return tuple(sorted(set(blockers)))


def _actionability(summary: GroupSummary, *, tier: str, blockers: tuple[str, ...]) -> str:
    blocker_set = set(blockers)
    if "immediate_resolve" in blocker_set or "wide_spread" in blocker_set:
        return "avoid"
    if tier == "strict_clone":
        if blocker_set & {
            "missing_book",
            "subjective_resolution",
            "resolution_source_unclear",
            "thin_liquidity",
            "below_family_liquidity_min",
        }:
            return "watch"
        return "actionable"
    if tier == "trigger_clone":
        if blocker_set & {
            "missing_book",
            "subjective_resolution",
            "resolution_source_unclear",
            "thin_liquidity",
            "below_family_liquidity_min",
        }:
            return "watch"
        return "actionable"
    if blocker_set & {"subjective_resolution", "resolution_source_unclear"}:
        return "watch"
    if "below_family_liquidity_min" in blocker_set:
        return "watch"
    return "watch"


def _rank_score(summary: GroupSummary, *, tier: str, actionability: str, blockers: tuple[str, ...]) -> float:
    score = float(summary.overall_score)
    if tier == "strict_clone":
        score += 8.0
    if tier == "trigger_clone":
        score += 6.0
        distance = abs(float(summary.consensus_no) - 0.5)
        if distance <= 0.15:
            score += 6.0
        elif distance <= 0.30:
            score += 2.0
        elif distance >= 0.45:
            score -= 6.0
        elif distance >= 0.35:
            score -= 3.0
    if actionability == "actionable":
        score += 5.0
    elif actionability == "avoid":
        score -= 10.0
    if "below_family_liquidity_min" in blockers:
        score -= 6.0
    if "thin_liquidity" in blockers:
        score -= 4.0
    if "missing_book" in blockers:
        score -= 2.0
    if "resolution_source_unclear" in blockers:
        score -= 4.0
    if "subjective_resolution" in blockers:
        score -= 3.0
    return score


def _note(summary: GroupSummary, *, family: str, actionability: str) -> str:
    if family in {"btc_daily_range", "eth_daily_range", "sol_daily_range", "xrp_daily_range"}:
        base = "Daily crypto close range; same movement-away-from-center setup."
    elif family in {"btc_daily_above", "eth_daily_above", "sol_daily_above", "xrp_daily_above"}:
        base = "Daily crypto threshold close; near-the-line repricing setup with recurring session catalysts."
    elif family in {"crude_settle_range", "gold_settle_range", "silver_settle_range", "spx_settle_range"}:
        base = "Settlement ladder; structurally similar but slower catalyst and rules matter more."
    elif family in {"election_margin_ladder", "election_count_ladder"}:
        base = "Election ladder; usable as a catalyst play, not a BTC-style intraday clone."
    elif family == "fed_cuts_ladder":
        base = "Macro count ladder; catalyst is strong but repricing is slower and more narrative-driven."
    elif family == "social_count_ladder":
        base = "Social-count ladder; repeatable schedule, but rules/objectivity are weaker."
    else:
        base = "Adjacent structure worth watching."
    return f"{actionability}: {base}"


def build_watch_candidates(
    summaries: list[GroupSummary],
) -> list[WatchCandidate]:
    candidates: list[WatchCandidate] = []
    for summary in summaries:
        family = infer_watch_family(summary)
        if family is None:
            continue
        tier = _tier_for_family(family)
        if tier == "ignore":
            continue
        family_liquidity_min = FAMILY_LIQUIDITY_MIN.get(family, 10_000.0)
        blockers = _build_blockers(summary, family_liquidity_min=family_liquidity_min)
        actionability = _actionability(summary, tier=tier, blockers=blockers)
        rank_score = _rank_score(summary, tier=tier, actionability=actionability, blockers=blockers)
        candidates.append(
            WatchCandidate(
                tier=tier,
                family=family,
                actionability=actionability,
                rank_score=rank_score,
                overall_score=float(summary.overall_score),
                family_liquidity_min=family_liquidity_min,
                event_title=summary.event_title,
                market_url=summary.market_url,
                structure_type=summary.structure_type,
                consensus_label=summary.consensus_label,
                consensus_no=float(summary.consensus_no),
                consensus_liquidity=float(summary.consensus_liquidity),
                catalyst_tags=summary.catalyst_tags,
                risk_flags=summary.risk_flags,
                blockers=blockers,
                note=_note(summary, family=family, actionability=actionability),
            )
        )
    candidates.sort(key=lambda item: item.rank_score, reverse=True)
    return candidates


def split_watch_candidates(
    candidates: list[WatchCandidate],
    *,
    top_n_per_tier: int = 20,
) -> tuple[list[WatchCandidate], list[WatchCandidate], list[WatchCandidate]]:
    strict = [item for item in candidates if item.tier == "strict_clone"][:top_n_per_tier]
    trigger = [item for item in candidates if item.tier == "trigger_clone"][:top_n_per_tier]
    semi = [item for item in candidates if item.tier == "semi_clone"][:top_n_per_tier]
    return strict, trigger, semi


def watch_candidate_to_dict(candidate: WatchCandidate) -> dict:
    payload = asdict(candidate)
    payload["catalyst_tags"] = ",".join(candidate.catalyst_tags)
    payload["risk_flags"] = ",".join(candidate.risk_flags)
    payload["blockers"] = ",".join(candidate.blockers)
    return payload
