from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any


POLYMARKET_EVENT_URL = "https://polymarket.com/event/{}"

_RANGE_RE = re.compile(
    r"(?P<lower>\$?-?\d[\d,]*(?:\.\d+)?%?)\s*[-–]\s*(?P<upper>\$?-?\d[\d,]*(?:\.\d+)?%?)"
)
_MONTH_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.IGNORECASE,
)
_UPDOWN_RE = re.compile(r"\bup or down\b", re.IGNORECASE)
_FIRST_TO_HIT_RE = re.compile(r"\b(first to hit|hit .* first)\b", re.IGNORECASE)
_WINNER_RE = re.compile(
    r"\b(winner|who will win|champion|prime minister|leader|nominee|award)\b",
    re.IGNORECASE,
)
_COUNT_RE = re.compile(
    r"\b(how many|number of|less than|more than|at least|over|under)\b",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(
    r"\b(price|btc|bitcoin|eth|ethereum|sol|doge|xrp|oil|gold|silver|nasdaq|s&p|spx|dow|djia|vix|yield|cpi|inflation|temperature)\b",
    re.IGNORECASE,
)
_CRYPTO_RE = re.compile(r"\b(btc|bitcoin|eth|ethereum|sol|doge|xrp|bnb)\b", re.IGNORECASE)
_MACRO_RE = re.compile(
    r"\b(cpi|pce|nfp|nonfarm|jobless claims|fed|fomc|rate decision|inflation|gdp|powell)\b",
    re.IGNORECASE,
)
_ELECTION_RE = re.compile(
    r"\b(election|vote share|popular vote|margin|seat count|house|senate|presidential)\b",
    re.IGNORECASE,
)
_WEATHER_RE = re.compile(
    r"\b(temperature|weather|rain|snow|earthquake|tornado|hurricane)\b",
    re.IGNORECASE,
)
_SPORTS_RE = re.compile(r"\b(vs\.?|match|game|quarter|touchdown|goal|inning)\b", re.IGNORECASE)
_CLOCK_RE = re.compile(r"\b\d{1,2}(?::\d{2})?\s*(am|pm)\s*et\b", re.IGNORECASE)
_DATE_RE = re.compile(
    r"\b(on|by|before)\s+[A-Z][a-z]+\s+\d{1,2}(?:,\s*\d{4})?\b",
    re.IGNORECASE,
)
_IMMEDIATE_RE = re.compile(
    r"\b(immediately resolve|immediately resolves|immediately in favor of)\b",
    re.IGNORECASE,
)
_TOUCH_RE = re.compile(r"\b(hit|touch|reach|dip below|rise above|go above|go below)\b", re.IGNORECASE)
_CLOSE_RE = re.compile(
    r"\b(closing price|close price|settlement price|candlestick that closes at|price at)\b",
    re.IGNORECASE,
)
_CHAINLINK_RE = re.compile(r"\bchainlink\b", re.IGNORECASE)
_BINANCE_RE = re.compile(r"\bbinance\b", re.IGNORECASE)
_SUBJECTIVE_RE = re.compile(
    r"\b(consensus of credible reporting|official website|official results|television broadcast)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MarketRow:
    condition_id: str
    question: str
    slug: str
    market_url: str
    event_id: str
    event_slug: str
    event_title: str
    group_key: str
    group_item_title: str
    yes_price: float
    no_price: float
    best_bid: float
    best_ask: float
    spread: float
    volume24hr: float
    liquidity: float
    neg_risk: bool
    end_date_iso: str
    lower_bound: float | None
    upper_bound: float | None
    resolution_kind: str
    catalyst_tags: tuple[str, ...]
    risk_flags: tuple[str, ...]


@dataclass(frozen=True)
class GroupSummary:
    group_key: str
    event_title: str
    event_slug: str
    market_url: str
    structure_type: str
    outcome_count: int
    consensus_label: str
    consensus_question: str
    consensus_yes: float
    consensus_no: float
    consensus_spread: float
    consensus_volume24hr: float
    consensus_liquidity: float
    tradability_score: float
    catalyst_score: float
    movement_score: float
    entry_score: float
    objectivity_score: float
    overall_score: float
    catalyst_tags: tuple[str, ...]
    risk_flags: tuple[str, ...]
    rationale: str


def _parse_json_list(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_bound_token(raw: str) -> float | None:
    token = (raw or "").strip().lower().replace(",", "").replace("$", "").replace("%", "")
    if not token:
        return None
    multiplier = 1.0
    if token.endswith("k"):
        multiplier = 1_000.0
        token = token[:-1]
    if token.endswith("m"):
        multiplier = 1_000_000.0
        token = token[:-1]
    try:
        return float(token) * multiplier
    except ValueError:
        return None


def _parse_range_bounds(*candidates: str) -> tuple[float | None, float | None]:
    for text in candidates:
        if not text:
            continue
        match = _RANGE_RE.search(text)
        if not match:
            continue
        lower = _normalize_bound_token(match.group("lower"))
        upper = _normalize_bound_token(match.group("upper"))
        if lower is not None and upper is not None:
            lower_raw = match.group("lower")
            upper_raw = match.group("upper")
            decorated = any(token in lower_raw + upper_raw for token in ("$", "%", ",", ".", "k", "K", "m", "M"))
            explicit_range_context = bool(
                re.search(r"\b(between|price|margin|temperature|tweets|posts|share|vote|range)\b", text, re.IGNORECASE)
            )
            season_like = len(lower_raw.replace("$", "").replace("%", "").replace(",", "")) >= 4 and len(
                upper_raw.replace("$", "").replace("%", "").replace(",", "")
            ) <= 2
            date_span_like = _MONTH_RE.search(text) and not explicit_range_context
            if season_like and not decorated:
                continue
            if date_span_like and not decorated:
                continue
            return lower, upper
    return None, None


def _extract_yes_no_prices(market: dict[str, Any]) -> tuple[float, float] | None:
    outcomes = [str(item).strip().lower() for item in _parse_json_list(market.get("outcomes"))]
    prices = _parse_json_list(market.get("outcomePrices"))
    if len(outcomes) < 2 or len(prices) < 2:
        return None
    if "yes" not in outcomes or "no" not in outcomes:
        return None
    yes_index = outcomes.index("yes")
    no_index = outcomes.index("no")
    yes_price = _to_float(prices[yes_index], default=-1.0)
    no_price = _to_float(prices[no_index], default=-1.0)
    if yes_price < 0 or no_price < 0:
        return None
    return yes_price, no_price


def _first_event(market: dict[str, Any]) -> dict[str, Any]:
    events = market.get("events") or []
    if isinstance(events, list) and events and isinstance(events[0], dict):
        return events[0]
    return {}


def _group_key(market: dict[str, Any], event: dict[str, Any]) -> str:
    neg_risk_market_id = str(market.get("negRiskMarketID") or "").strip()
    if neg_risk_market_id:
        return f"neg:{neg_risk_market_id}"
    slug = str(event.get("slug") or market.get("slug") or "").strip()
    if bool(market.get("negRisk")) and slug:
        return f"slug:{slug}"
    return f"condition:{market.get('conditionId', '')}"


def _resolution_text(market: dict[str, Any], event: dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            str(market.get("description") or ""),
            str(market.get("rules") or ""),
            str(event.get("description") or ""),
            str(market.get("resolutionSource") or ""),
            str(event.get("resolutionSource") or ""),
        ]
        if part
    )


def infer_resolution_kind(question: str, text: str) -> str:
    combined = f"{question} {text}"
    if _FIRST_TO_HIT_RE.search(combined):
        return "first_to_hit"
    if _IMMEDIATE_RE.search(combined):
        return "immediate_touch"
    if _TOUCH_RE.search(combined):
        return "intraday_touch"
    if _CLOSE_RE.search(combined):
        return "time_close"
    if _CHAINLINK_RE.search(combined):
        return "oracle_stream"
    return "unknown"


def infer_catalyst_tags(question: str, event_title: str, text: str) -> tuple[str, ...]:
    combined = " ".join(part for part in [question, event_title, text] if part)
    tags: set[str] = set()
    if _CLOCK_RE.search(combined) or _DATE_RE.search(combined):
        tags.add("scheduled_clock")
    if _CRYPTO_RE.search(combined):
        tags.add("crypto")
    if _MACRO_RE.search(combined):
        tags.add("macro")
    if _ELECTION_RE.search(combined):
        tags.add("election")
    if _WEATHER_RE.search(combined):
        tags.add("weather")
    if _SPORTS_RE.search(combined):
        tags.add("sports")
    if "crypto" in tags and "scheduled_clock" in tags:
        tags.add("session_window")
    return tuple(sorted(tags))


def infer_risk_flags(
    *,
    text: str,
    best_bid: float,
    best_ask: float,
    spread: float,
    liquidity: float,
) -> tuple[str, ...]:
    flags: set[str] = set()
    if _IMMEDIATE_RE.search(text):
        flags.add("immediate_resolve")
    if _SUBJECTIVE_RE.search(text) and not (_BINANCE_RE.search(text) or _CHAINLINK_RE.search(text)):
        flags.add("subjective_resolution")
    if not (_BINANCE_RE.search(text) or _CHAINLINK_RE.search(text)) and not _SUBJECTIVE_RE.search(text):
        flags.add("resolution_source_unclear")
    if best_bid <= 0 or best_ask <= 0:
        flags.add("missing_book")
    if spread >= 0.10:
        flags.add("wide_spread")
    if liquidity < 5_000:
        flags.add("thin_liquidity")
    return tuple(sorted(flags))


def normalize_market(market: dict[str, Any]) -> MarketRow | None:
    prices = _extract_yes_no_prices(market)
    if prices is None:
        return None
    question = str(market.get("question") or "").strip()
    condition_id = str(market.get("conditionId") or "").strip()
    slug = str(market.get("slug") or "").strip()
    if not question or not condition_id or not slug:
        return None

    event = _first_event(market)
    event_slug = str(event.get("slug") or slug).strip()
    event_title = str(event.get("title") or question).strip()
    group_item_title = str(market.get("groupItemTitle") or "").strip()
    resolution_text = _resolution_text(market, event)
    lower_bound, upper_bound = _parse_range_bounds(group_item_title, question)
    yes_price, no_price = prices
    best_bid = _to_float(market.get("bestBid"))
    best_ask = _to_float(market.get("bestAsk"))
    spread = _to_float(market.get("spread"))
    liquidity = _to_float(market.get("liquidityClob") or market.get("liquidityNum") or market.get("liquidity"))

    return MarketRow(
        condition_id=condition_id,
        question=question,
        slug=slug,
        market_url=POLYMARKET_EVENT_URL.format(event_slug),
        event_id=str(event.get("id") or ""),
        event_slug=event_slug,
        event_title=event_title,
        group_key=_group_key(market, event),
        group_item_title=group_item_title,
        yes_price=yes_price,
        no_price=no_price,
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        volume24hr=_to_float(market.get("volume24hr")),
        liquidity=liquidity,
        neg_risk=bool(market.get("negRisk")),
        end_date_iso=str(market.get("endDate") or ""),
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        resolution_kind=infer_resolution_kind(question=question, text=resolution_text),
        catalyst_tags=infer_catalyst_tags(question=question, event_title=event_title, text=resolution_text),
        risk_flags=infer_risk_flags(
            text=resolution_text,
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            liquidity=liquidity,
        ),
    )


def normalize_markets(markets: list[dict[str, Any]]) -> list[MarketRow]:
    rows: list[MarketRow] = []
    for market in markets:
        row = normalize_market(market)
        if row is not None:
            rows.append(row)
    return rows


def _infer_structure_type(rows: list[MarketRow]) -> str:
    if not rows:
        return "unknown"
    joined = " ".join(f"{row.group_item_title} {row.question} {row.event_title}" for row in rows)
    parsed_ranges = sum(1 for row in rows if row.lower_bound is not None and row.upper_bound is not None)
    if len(rows) >= 3 and _WINNER_RE.search(joined):
        return "winner_ladder"
    if len(rows) >= 3 and parsed_ranges >= max(2, math.ceil(len(rows) * 0.5)) and _PRICE_RE.search(joined):
        return "range_ladder"
    if len(rows) >= 3 and _COUNT_RE.search(joined):
        return "count_ladder"
    if len(rows) >= 3 and parsed_ranges >= max(2, math.ceil(len(rows) * 0.5)):
        return "numeric_ladder"
    if len(rows) == 1:
        row = rows[0]
        if _UPDOWN_RE.search(joined):
            return "micro_updown"
        if row.resolution_kind in {"immediate_touch", "intraday_touch"}:
            return "barrier_binary"
        if row.resolution_kind == "first_to_hit":
            return "first_to_hit"
        return "single_binary"
    return "multi_binary"


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _score_tradability(consensus: MarketRow) -> float:
    spread_score = 0.3 if consensus.spread <= 0 else _clamp(1.0 - (consensus.spread / 0.12))
    liquidity_score = _clamp(consensus.liquidity / 20_000.0)
    volume_score = _clamp(consensus.volume24hr / 50_000.0)
    book_score = 1.0 if consensus.best_bid > 0 and consensus.best_ask > 0 else 0.0
    return 0.35 * liquidity_score + 0.25 * volume_score + 0.25 * spread_score + 0.15 * book_score


def _score_catalyst(tags: tuple[str, ...]) -> float:
    score = 0.0
    if "scheduled_clock" in tags:
        score += 0.30
    if "session_window" in tags:
        score += 0.25
    if "macro" in tags:
        score += 0.25
    if "election" in tags:
        score += 0.20
    if "crypto" in tags:
        score += 0.15
    if "sports" in tags:
        score += 0.05
    return _clamp(score)


def _score_movement_fit(structure_type: str, resolution_kind: str) -> float:
    base = {
        "range_ladder": 1.0,
        "numeric_ladder": 0.80,
        "count_ladder": 0.60,
        "barrier_binary": 0.40,
        "first_to_hit": 0.35,
        "micro_updown": 0.25,
        "winner_ladder": 0.15,
        "single_binary": 0.10,
        "multi_binary": 0.10,
    }.get(structure_type, 0.0)
    if resolution_kind == "time_close":
        base += 0.10
    if resolution_kind == "immediate_touch":
        base -= 0.15
    return _clamp(base)


def _score_entry(consensus: MarketRow) -> float:
    if 0.10 <= consensus.no_price <= 0.60:
        return 1.0
    if 0.05 <= consensus.no_price < 0.10 or 0.60 < consensus.no_price <= 0.80:
        return 0.70
    return 0.35


def _score_objectivity(risk_flags: tuple[str, ...]) -> float:
    score = 1.0
    if "immediate_resolve" in risk_flags:
        score -= 0.35
    if "subjective_resolution" in risk_flags:
        score -= 0.30
    if "resolution_source_unclear" in risk_flags:
        score -= 0.20
    return _clamp(score)


def _build_rationale(
    *,
    structure_type: str,
    consensus: MarketRow,
    catalyst_tags: tuple[str, ...],
    risk_flags: tuple[str, ...],
) -> str:
    label = consensus.group_item_title or consensus.question
    parts = [
        f"type={structure_type}",
        f"consensus={label}",
        f"yes={consensus.yes_price:.3f}",
        f"no={consensus.no_price:.3f}",
        f"liq={consensus.liquidity:,.0f}",
        f"spread={consensus.spread:.3f}",
    ]
    if catalyst_tags:
        parts.append("tags=" + ",".join(catalyst_tags))
    if risk_flags:
        parts.append("risks=" + ",".join(risk_flags))
    return "; ".join(parts)


def build_group_summaries(rows: list[MarketRow]) -> list[GroupSummary]:
    grouped: dict[str, list[MarketRow]] = defaultdict(list)
    for row in rows:
        grouped[row.group_key].append(row)

    summaries: list[GroupSummary] = []
    for group_key, bucket in grouped.items():
        if not bucket:
            continue
        structure_type = _infer_structure_type(bucket)
        consensus = max(bucket, key=lambda row: row.yes_price)
        catalyst_tags = tuple(sorted({tag for row in bucket for tag in row.catalyst_tags}))
        risk_flags = tuple(sorted({flag for row in bucket for flag in row.risk_flags}))
        tradability_score = _score_tradability(consensus)
        catalyst_score = _score_catalyst(catalyst_tags)
        movement_score = _score_movement_fit(structure_type, consensus.resolution_kind)
        entry_score = _score_entry(consensus)
        objectivity_score = _score_objectivity(risk_flags)
        overall_score = 100.0 * (
            0.30 * movement_score
            + 0.25 * tradability_score
            + 0.20 * catalyst_score
            + 0.15 * entry_score
            + 0.10 * objectivity_score
        )
        rationale = _build_rationale(
            structure_type=structure_type,
            consensus=consensus,
            catalyst_tags=catalyst_tags,
            risk_flags=risk_flags,
        )
        summaries.append(
            GroupSummary(
                group_key=group_key,
                event_title=consensus.event_title,
                event_slug=consensus.event_slug,
                market_url=consensus.market_url,
                structure_type=structure_type,
                outcome_count=len(bucket),
                consensus_label=consensus.group_item_title or consensus.question,
                consensus_question=consensus.question,
                consensus_yes=consensus.yes_price,
                consensus_no=consensus.no_price,
                consensus_spread=consensus.spread,
                consensus_volume24hr=consensus.volume24hr,
                consensus_liquidity=consensus.liquidity,
                tradability_score=tradability_score,
                catalyst_score=catalyst_score,
                movement_score=movement_score,
                entry_score=entry_score,
                objectivity_score=objectivity_score,
                overall_score=overall_score,
                catalyst_tags=catalyst_tags,
                risk_flags=risk_flags,
                rationale=rationale,
            )
        )
    summaries.sort(key=lambda item: item.overall_score, reverse=True)
    return summaries


def shortlist_groups(
    summaries: list[GroupSummary],
    *,
    min_score: float = 55.0,
    min_liquidity: float = 5_000.0,
    allowed_structures: tuple[str, ...] = ("range_ladder", "numeric_ladder", "count_ladder"),
) -> list[GroupSummary]:
    shortlisted: list[GroupSummary] = []
    allowed = set(allowed_structures)
    for summary in summaries:
        if summary.structure_type not in allowed:
            continue
        if summary.consensus_liquidity < min_liquidity:
            continue
        if summary.overall_score < min_score:
            continue
        shortlisted.append(summary)
    return shortlisted


def market_row_to_dict(row: MarketRow) -> dict[str, Any]:
    payload = asdict(row)
    payload["catalyst_tags"] = ",".join(row.catalyst_tags)
    payload["risk_flags"] = ",".join(row.risk_flags)
    return payload


def group_summary_to_dict(summary: GroupSummary) -> dict[str, Any]:
    payload = asdict(summary)
    payload["catalyst_tags"] = ",".join(summary.catalyst_tags)
    payload["risk_flags"] = ",".join(summary.risk_flags)
    return payload
