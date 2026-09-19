from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Callable, Awaitable

import aiohttp

from polymarket_bot.config import settings
from polymarket_bot.models import DBRow, MarketInfo

log = logging.getLogger(__name__)

_BTC_MARKER = re.compile(r"\b(BTC|Bitcoin)\b", re.IGNORECASE)
_ALLOWED_MICRO_DURATIONS_S = {300, 900, 1800, 3600}
_RESOLVE_GRACE_MS = 120_000

# "Bitcoin Up or Down - February 14, 2:30PM-2:45PM ET"
_UP_DOWN_PATTERN = re.compile(r"Bitcoin Up or Down", re.IGNORECASE)

# "2:30PM-2:45PM" or "11:35AM-11:40AM" — extract time range to compute slot duration
_TIME_RANGE = re.compile(
    r"(\d{1,2}):(\d{2})\s*(AM|PM)\s*[-–—]\s*(\d{1,2}):(\d{2})\s*(AM|PM)",
    re.IGNORECASE,
)

# Legacy patterns (in case Polymarket reverts naming)
_TIME_MARKERS_LEGACY = re.compile(
    r"(5[\s-]?[Mm]inute|15[\s-]?[Mm]inute|30[\s-]?[Mm]inute|1[\s-]?[Hh]our)",
)


def _parse_duration_from_question(question: str) -> int:
    """Extract slot duration in seconds from market question text.

    Handles both:
    - "Bitcoin Up or Down - Feb 14, 2:30PM-2:45PM ET" → 15min = 900s
    - Legacy "5-Minute BTC" → 300s
    """
    # Try time range pattern first: "2:30PM-2:45PM"
    m = _TIME_RANGE.search(question)
    if m:
        h1, m1, ap1, h2, m2, ap2 = m.groups()
        t1_min = (_to_24h(int(h1), ap1.upper()) * 60) + int(m1)
        t2_min = (_to_24h(int(h2), ap2.upper()) * 60) + int(m2)
        diff = t2_min - t1_min
        if diff <= 0:
            # Cross-midnight markets: 11:55PM-12:00AM should be treated as +5 minutes.
            diff += 24 * 60
        if diff > 0:
            return diff * 60
        return 0

    # Legacy: "5-Minute", "1-Hour"
    m = re.search(r"(\d+)[\s-]?[Mm]inute", question)
    if m:
        return int(m.group(1)) * 60
    if re.search(r"1[\s-]?[Hh]our", question):
        return 3600
    return 0


def _to_24h(hour: int, ampm: str) -> int:
    if ampm == "AM":
        return 0 if hour == 12 else hour
    else:
        return hour if hour == 12 else hour + 12


def _detect_resolution_source(description: str) -> str:
    desc_lower = description.lower()
    if "chainlink" in desc_lower:
        return "chainlink"
    if "binance" in desc_lower:
        return "binance"
    return "unknown"


def _parse_clob_token_ids(raw: str | list) -> list[str]:
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _is_btc_micro_market(market: dict) -> bool:
    question = market.get("question", "")
    if not _BTC_MARKER.search(question):
        return False
    # Only keep short-horizon micro markets (5m/15m/30m/1h).
    if (_UP_DOWN_PATTERN.search(question) and _TIME_RANGE.search(question)) or _TIME_MARKERS_LEGACY.search(question):
        duration = _parse_duration_from_question(question)
        return duration in _ALLOWED_MICRO_DURATIONS_S
    return False


def _resolve_yes_no_tokens(market: dict, token_ids: list[str]) -> tuple[str, str] | None:
    """Map token_ids to (yes_token_id, no_token_id) using the outcomes field.

    Gamma API returns `outcomes` as '["Yes","No"]' or '["No","Yes"]' (JSON string or list).
    The order of outcomes matches clobTokenIds order.
    Falls back to positional [0]=YES, [1]=NO only if outcomes field is missing.
    """
    raw_outcomes = market.get("outcomes")
    if raw_outcomes is None:
        log.warning(
            "Market %s has no outcomes field — assuming token_ids[0]=YES",
            market.get("conditionId", "?")[:12],
        )
        return token_ids[0], token_ids[1]

    if isinstance(raw_outcomes, str):
        try:
            outcomes = json.loads(raw_outcomes)
        except (json.JSONDecodeError, TypeError):
            outcomes = []
    else:
        outcomes = raw_outcomes

    if not isinstance(outcomes, list) or len(outcomes) < 2:
        log.warning(
            "Market %s has malformed outcomes: %s — assuming token_ids[0]=YES",
            market.get("conditionId", "?")[:12],
            raw_outcomes,
        )
        return token_ids[0], token_ids[1]

    # Build outcome→token mapping
    # Polymarket BTC micro-markets use "Up"/"Down" instead of "Yes"/"No"
    # Map: Up → yes_token (positive outcome), Down → no_token
    outcome_lower = [str(o).strip().lower() for o in outcomes]

    # Try Yes/No first
    if "yes" in outcome_lower and "no" in outcome_lower:
        yes_idx = outcome_lower.index("yes")
        no_idx = outcome_lower.index("no")
        return token_ids[yes_idx], token_ids[no_idx]

    # Try Up/Down
    if "up" in outcome_lower and "down" in outcome_lower:
        up_idx = outcome_lower.index("up")
        down_idx = outcome_lower.index("down")
        return token_ids[up_idx], token_ids[down_idx]

    log.warning(
        "Market %s outcomes %s don't contain Yes/No or Up/Down — assuming positional",
        market.get("conditionId", "?")[:12],
        outcomes,
    )
    return token_ids[0], token_ids[1]


def _parse_market(market: dict) -> MarketInfo | None:
    question = market.get("question", "")
    token_ids = _parse_clob_token_ids(market.get("clobTokenIds", []))
    if len(token_ids) < 2:
        return None

    resolved = _resolve_yes_no_tokens(market, token_ids)
    if resolved is None:
        return None
    yes_token_id, no_token_id = resolved

    end_date_str = market.get("endDate", market.get("end_date_iso", ""))
    start_date_str = market.get("startDate", market.get("start_date_iso", ""))

    # Parse ISO dates to epoch ms
    from datetime import datetime, timezone

    def iso_to_ms(s: str) -> int:
        if not s:
            return 0
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except (ValueError, TypeError):
            return 0

    end_ms = iso_to_ms(end_date_str)
    start_ms = iso_to_ms(start_date_str)

    duration = _parse_duration_from_question(question)
    if duration == 0 and start_ms and end_ms:
        duration_from_dates = max(0, (end_ms - start_ms) // 1000)
        if duration_from_dates in _ALLOWED_MICRO_DURATIONS_S:
            duration = duration_from_dates
    if duration not in _ALLOWED_MICRO_DURATIONS_S:
        return None

    description = market.get("description", "") or market.get("rules", "") or ""
    resolution_source = _detect_resolution_source(description)

    condition_id = market.get("conditionId", market.get("condition_id", ""))
    if not condition_id:
        return None

    return MarketInfo(
        condition_id=condition_id,
        question=question,
        yes_token_id=yes_token_id,
        no_token_id=no_token_id,
        start_date_ms=start_ms,
        end_date_ms=end_ms,
        resolution_source=resolution_source,
        duration_seconds=duration,
        discovered_at_ms=int(time.time() * 1000),
    )


class MarketDiscovery:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def run(
        self,
        active_markets: dict[str, MarketInfo],
        db_queue: asyncio.Queue[DBRow],
        on_new: Callable[[MarketInfo], Awaitable[None]] | None = None,
        on_resolved: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
        )
        try:
            while True:
                try:
                    await self._poll(active_markets, db_queue, on_new, on_resolved)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("Market discovery poll failed")
                await asyncio.sleep(settings.market_poll_interval_s)
        finally:
            if self._session and not self._session.closed:
                await self._session.close()

    async def _poll(
        self,
        active_markets: dict[str, MarketInfo],
        db_queue: asyncio.Queue[DBRow],
        on_new: Callable[[MarketInfo], Awaitable[None]] | None,
        on_resolved: Callable[[str], Awaitable[None]] | None,
    ) -> None:
        assert self._session is not None
        all_markets: list[dict] = []
        offset = 0
        limit = 100

        while True:
            url = (
                f"{settings.gamma_api_url}/markets"
                f"?active=true&closed=false&limit={limit}&offset={offset}"
            )
            async with self._session.get(url) as resp:
                if resp.status == 429:
                    log.warning("Gamma API rate limited, backing off 30s")
                    await asyncio.sleep(30)
                    continue
                resp.raise_for_status()
                batch = await resp.json()

            if not batch:
                break
            all_markets.extend(batch)
            if len(batch) < limit:
                break
            offset += limit

        # Filter for BTC micro-markets with end_date in the future
        now_ms = int(time.time() * 1000)
        btc_markets = [m for m in all_markets if _is_btc_micro_market(m)]
        discovered_ids = set()

        for raw in btc_markets:
            info = _parse_market(raw)
            if not info:
                continue
            # Skip expired markets
            if info.end_date_ms > 0 and info.end_date_ms < now_ms:
                continue
            discovered_ids.add(info.condition_id)

            if info.condition_id not in active_markets:
                market_row = DBRow(
                    table="markets",
                    data={
                        "condition_id": info.condition_id,
                        "question": info.question,
                        "yes_token_id": info.yes_token_id,
                        "no_token_id": info.no_token_id,
                        "start_date_ms": info.start_date_ms,
                        "end_date_ms": info.end_date_ms,
                        "resolution_source": info.resolution_source,
                        "duration_seconds": info.duration_seconds,
                        "active": 1,
                        "resolved": 0,
                        "winning_token_id": None,
                        "discovered_at_ms": info.discovered_at_ms,
                    },
                )
                try:
                    await asyncio.wait_for(db_queue.put(market_row), timeout=5.0)
                except asyncio.TimeoutError:
                    # Don't add to active_markets — next poll will retry
                    log.error(
                        "DB queue full for 5s — market %s skipped, will retry next poll",
                        info.condition_id[:12],
                    )
                    continue
                active_markets[info.condition_id] = info
                log.info("New market: %s — %s", info.condition_id[:12], info.question)
                if on_new:
                    await on_new(info)

        # Detect resolved markets
        for cid in list(active_markets.keys()):
            if cid not in discovered_ids and active_markets[cid].active:
                end_ms = active_markets[cid].end_date_ms
                if end_ms <= 0 or end_ms > now_ms + _RESOLVE_GRACE_MS:
                    # Gamma pagination/order can be inconsistent between polls.
                    # Avoid false "resolved" flips for not-yet-expired markets.
                    continue
                active_markets[cid].active = False
                active_markets[cid].resolved = True
                # Persist resolved state to DB
                resolve_row = DBRow(
                    table="markets",
                    data={
                        "condition_id": cid,
                        "question": active_markets[cid].question,
                        "yes_token_id": active_markets[cid].yes_token_id,
                        "no_token_id": active_markets[cid].no_token_id,
                        "start_date_ms": active_markets[cid].start_date_ms,
                        "end_date_ms": active_markets[cid].end_date_ms,
                        "resolution_source": active_markets[cid].resolution_source,
                        "duration_seconds": active_markets[cid].duration_seconds,
                        "active": 0,
                        "resolved": 1,
                        "winning_token_id": active_markets[cid].winning_token_id,
                        "discovered_at_ms": active_markets[cid].discovered_at_ms,
                    },
                )
                try:
                    db_queue.put_nowait(resolve_row)
                except asyncio.QueueFull:
                    log.warning("Queue full — resolved state for %s not persisted", cid[:12])
                log.info("Market resolved: %s", cid[:12])
                if on_resolved:
                    await on_resolved(cid)

        log.debug(
            "Discovery: %d total, %d BTC micro, %d active",
            len(all_markets),
            len(btc_markets),
            sum(1 for m in list(active_markets.values()) if m.active),
        )
