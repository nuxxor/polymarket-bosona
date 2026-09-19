from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import signal
import sqlite3
import time
from collections import deque
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import aiohttp

from polymarket_bot.collectors.binance_futures_depth_ws import BinanceFuturesDepthWebSocket
from polymarket_bot.collectors.binance_ws import BinanceWebSocket
from polymarket_bot.collectors.book_refresher import BookRefresher
from polymarket_bot.collectors.clob_ws import CLOBWebSocket
from polymarket_bot.config import settings
from polymarket_bot.features.orderbook import DepthMetrics, compute_depth_metrics
from polymarket_bot.daily_range_contract import (
    LadderValidationError,
    RangeParseError,
    parse_daily_range_ladder,
    parse_range_label,
    validate_daily_range_rule,
)
from polymarket_bot.models import BinanceMicroState, DBRow, LocalOrderBook, MarketInfo
from polymarket_bot.storage.daily_range_database import DailyRangeDBWriter, DailyRangeDatabase
from polymarket_bot.storage.raw_logger import RawLogger
from polymarket_bot.utils.polymarket_public import fetch_gamma_keyset_rows_async

log = logging.getLogger(__name__)

_ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")
_NEW_YORK_TZ = ZoneInfo("America/New_York")
_BTC_DAILY_RANGE_TITLE = re.compile(
    r"^Bitcoin price on [A-Za-z]+ \d{1,2}(?:,\s*\d{4})?\??$",
    re.IGNORECASE,
)
_BTC_DAILY_RANGE_SLUG = re.compile(r"^bitcoin-price-on-[a-z]+-\d{1,2}(?:-\d{4})?$", re.IGNORECASE)
_SCHEDULE_POLL_INTERVAL_S = 30.0
_GATE_SNAPSHOT_INTERVAL_S = 60.0
_FOCUS_BOOK_LEVEL_LIMIT = 25
_US_MARKET_CLOSED_DATES_2026 = {
    date(2026, 4, 3),
    date(2026, 5, 25),
    date(2026, 6, 19),
    date(2026, 7, 3),
    date(2026, 9, 7),
    date(2026, 11, 26),
    date(2026, 12, 25),
}


@dataclass(frozen=True)
class DailyRangeMarket:
    condition_id: str
    question: str
    group_item_title: str
    yes_token_id: str
    no_token_id: str
    lower_bound: float | None
    upper_bound: float | None
    order_index: int
    initial_yes_price: float | None
    initial_no_price: float | None

    def to_market_info(self, start_date_ms: int, end_date_ms: int) -> MarketInfo:
        return MarketInfo(
            condition_id=self.condition_id,
            question=self.question,
            yes_token_id=self.yes_token_id,
            no_token_id=self.no_token_id,
            start_date_ms=start_date_ms,
            end_date_ms=end_date_ms,
            resolution_source="binance",
            duration_seconds=max(1, (end_date_ms - start_date_ms) // 1000),
            discovered_at_ms=int(time.time() * 1000),
        )


@dataclass(frozen=True)
class DailyRangeEvent:
    event_slug: str
    event_title: str
    start_date_ms: int
    end_date_ms: int
    source_url: str
    resolution_text: str
    markets: tuple[DailyRangeMarket, ...]


@dataclass(frozen=True)
class CollectorScheduleStatus:
    active: bool
    capture_date_tsi: str
    reason_code: str
    reason_detail: str


@dataclass
class ProducerBundle:
    tasks: list[asyncio.Task]
    clob_logger: RawLogger
    binance_logger: RawLogger
    futures_depth_logger: RawLogger
    deribit_logger: RawLogger


def _iso_to_ms(value: str) -> int:
    if not value:
        return 0
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return 0
    return int(dt.timestamp() * 1000)


def _capture_date_tsi(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(_ISTANBUL_TZ)
    return dt.strftime("%Y-%m-%d")


def _schedule_event_trade_date_tsi(ts_ms: int) -> date:
    dt_tsi = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(_ISTANBUL_TZ)
    trade_date = dt_tsi.date()
    if (dt_tsi.hour, dt_tsi.minute, dt_tsi.second, dt_tsi.microsecond) >= (19, 0, 0, 0):
        return trade_date.fromordinal(trade_date.toordinal() + 1)
    return trade_date


def _collector_schedule_status(ts_ms: int, *, allow_weekends: bool = False) -> CollectorScheduleStatus:
    dt_tsi = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(_ISTANBUL_TZ)
    trade_date = _schedule_event_trade_date_tsi(ts_ms)
    capture_date = dt_tsi.strftime("%Y-%m-%d")
    if trade_date.weekday() >= 5 and not allow_weekends:
        return CollectorScheduleStatus(
            active=False,
            capture_date_tsi=capture_date,
            reason_code="weekend_pause",
            reason_detail=f"Paused because the next active event settles on weekend date {trade_date.isoformat()} in TSI.",
        )
    if trade_date.weekday() >= 5 and allow_weekends:
        return CollectorScheduleStatus(
            active=True,
            capture_date_tsi=capture_date,
            reason_code="weekend_collection_enabled",
            reason_detail=f"Weekend collection enabled for event date {trade_date.isoformat()} in TSI.",
        )
    if trade_date in _US_MARKET_CLOSED_DATES_2026:
        return CollectorScheduleStatus(
            active=False,
            capture_date_tsi=capture_date,
            reason_code="us_market_holiday_pause",
            reason_detail=f"Paused because the next active event settles on configured US market holiday {trade_date.isoformat()}.",
        )
    return CollectorScheduleStatus(
        active=True,
        capture_date_tsi=capture_date,
        reason_code="active_session",
        reason_detail=f"Trading day for event date {trade_date.isoformat()}; range collection is enabled.",
    )


def _normalize_numeric(raw: object) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip().lower().replace("$", "").replace(",", "")
    if not text:
        return None
    multiplier = 1.0
    if text.endswith("k"):
        multiplier = 1_000.0
        text = text[:-1]
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def _parse_bounds(group_item_title: str, market: dict) -> tuple[float | None, float | None]:
    lower = _normalize_numeric(market.get("lowerBound"))
    upper = _normalize_numeric(market.get("upperBound"))
    if lower is not None or upper is not None:
        return lower, upper

    label = (group_item_title or "").strip()
    try:
        bucket = parse_range_label(label or str(market.get("question") or ""))
    except RangeParseError:
        return None, None
    return (
        float(bucket.lower) if bucket.lower is not None else None,
        float(bucket.upper) if bucket.upper is not None else None,
    )


def _parse_json_list(raw: object) -> list[object]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _safe_float(raw: object) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _safe_int(raw: object) -> int | None:
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _latest_metric_entry(payload: object) -> dict | None:
    if not isinstance(payload, list):
        return None
    items = [item for item in payload if isinstance(item, dict)]
    if not items:
        return None
    return max(items, key=lambda item: _safe_int(item.get("timestamp")) or -1)


def _build_futures_regime_row(
    *,
    fetched_ts_ms: int,
    capture_date_tsi: str,
    symbol: str,
    period: str,
    open_interest_hist: dict | None,
    global_long_short: dict | None,
    top_trader_account: dict | None,
    top_trader_position: dict | None,
    taker_buy_sell: dict | None,
) -> dict | None:
    rows = [
        open_interest_hist,
        global_long_short,
        top_trader_account,
        top_trader_position,
        taker_buy_sell,
    ]
    if not any(isinstance(row, dict) for row in rows):
        return None

    return {
        "fetched_ts_ms": fetched_ts_ms,
        "capture_date_tsi": capture_date_tsi,
        "source": "binance_usdm_rest",
        "symbol": symbol,
        "period": period,
        "open_interest_hist_ts_ms": (
            _safe_int(open_interest_hist.get("timestamp")) if open_interest_hist else None
        ),
        "sum_open_interest": (
            _safe_float(open_interest_hist.get("sumOpenInterest")) if open_interest_hist else None
        ),
        "sum_open_interest_value": (
            _safe_float(open_interest_hist.get("sumOpenInterestValue"))
            if open_interest_hist
            else None
        ),
        "global_long_short_ts_ms": (
            _safe_int(global_long_short.get("timestamp")) if global_long_short else None
        ),
        "global_long_short_ratio": (
            _safe_float(global_long_short.get("longShortRatio")) if global_long_short else None
        ),
        "global_long_account": (
            _safe_float(global_long_short.get("longAccount")) if global_long_short else None
        ),
        "global_short_account": (
            _safe_float(global_long_short.get("shortAccount")) if global_long_short else None
        ),
        "top_trader_account_ts_ms": (
            _safe_int(top_trader_account.get("timestamp")) if top_trader_account else None
        ),
        "top_trader_account_ratio": (
            _safe_float(top_trader_account.get("longShortRatio")) if top_trader_account else None
        ),
        "top_trader_account_long": (
            _safe_float(top_trader_account.get("longAccount")) if top_trader_account else None
        ),
        "top_trader_account_short": (
            _safe_float(top_trader_account.get("shortAccount")) if top_trader_account else None
        ),
        "top_trader_position_ts_ms": (
            _safe_int(top_trader_position.get("timestamp")) if top_trader_position else None
        ),
        "top_trader_position_ratio": (
            _safe_float(top_trader_position.get("longShortRatio")) if top_trader_position else None
        ),
        "top_trader_position_long": (
            _safe_float(top_trader_position.get("longAccount")) if top_trader_position else None
        ),
        "top_trader_position_short": (
            _safe_float(top_trader_position.get("shortAccount")) if top_trader_position else None
        ),
        "taker_buy_sell_ts_ms": (
            _safe_int(taker_buy_sell.get("timestamp")) if taker_buy_sell else None
        ),
        "taker_buy_sell_ratio": (
            _safe_float(taker_buy_sell.get("buySellRatio")) if taker_buy_sell else None
        ),
        "taker_buy_vol": _safe_float(taker_buy_sell.get("buyVol")) if taker_buy_sell else None,
        "taker_sell_vol": (
            _safe_float(taker_buy_sell.get("sellVol")) if taker_buy_sell else None
        ),
    }


def _futures_regime_signature(row: dict | None) -> tuple[int | None, ...] | None:
    if row is None:
        return None
    return (
        _safe_int(row.get("open_interest_hist_ts_ms")),
        _safe_int(row.get("global_long_short_ts_ms")),
        _safe_int(row.get("top_trader_account_ts_ms")),
        _safe_int(row.get("top_trader_position_ts_ms")),
        _safe_int(row.get("taker_buy_sell_ts_ms")),
    )


def _build_futures_mark_price_rest_row(
    payload: object,
    *,
    fetched_ts_ms: int,
    symbol: str,
) -> dict | None:
    if not isinstance(payload, dict):
        return None
    mark_price = _safe_float(payload.get("markPrice"))
    index_price = _safe_float(payload.get("indexPrice"))
    if mark_price is None and index_price is None:
        return None
    ts_ms = _safe_int(payload.get("time")) or fetched_ts_ms
    return {
        "ts_ms": ts_ms,
        "capture_date_tsi": _capture_date_tsi(ts_ms),
        "source": "binance_usdm_premium_index_rest",
        "symbol": symbol,
        "mark_price": mark_price,
        "mark_price_ma": None,
        "index_price": index_price,
        "estimated_settle_price": _safe_float(payload.get("estimatedSettlePrice")),
        "funding_rate": _safe_float(payload.get("lastFundingRate")),
        "next_funding_time_ms": _safe_int(payload.get("nextFundingTime")),
    }


def _build_futures_kline_rest_row(
    raw: object,
    *,
    symbol: str,
    interval: str,
) -> dict | None:
    if not isinstance(raw, list | tuple) or len(raw) < 11:
        return None
    open_time_ms = _safe_int(raw[0])
    close_time_ms = _safe_int(raw[6])
    if open_time_ms is None or close_time_ms is None:
        return None
    open_price = _safe_float(raw[1])
    high_price = _safe_float(raw[2])
    low_price = _safe_float(raw[3])
    close_price = _safe_float(raw[4])
    volume_base = _safe_float(raw[5])
    volume_quote = _safe_float(raw[7])
    trade_count = _safe_int(raw[8])
    taker_buy_base = _safe_float(raw[9])
    taker_buy_quote = _safe_float(raw[10])
    if (
        open_price is None
        or high_price is None
        or low_price is None
        or close_price is None
        or open_price <= 0
        or high_price <= 0
        or low_price <= 0
        or close_price <= 0
    ):
        return None
    return {
        "ts_ms": close_time_ms,
        "source": "binance_usdm_kline_rest",
        "symbol": symbol,
        "interval": interval,
        "open_time_ms": open_time_ms,
        "close_time_ms": close_time_ms,
        "open_price": open_price,
        "high_price": high_price,
        "low_price": low_price,
        "close_price": close_price,
        "volume_base": volume_base or 0.0,
        "volume_quote": volume_quote or 0.0,
        "trade_count": trade_count or 0,
        "taker_buy_base": taker_buy_base or 0.0,
        "taker_buy_quote": taker_buy_quote or 0.0,
    }


def _ny_open_ts_ms(ts_ms: int) -> int:
    dt_ny = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(_NEW_YORK_TZ)
    open_dt_ny = dt_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    return int(open_dt_ny.astimezone(timezone.utc).timestamp() * 1000)


def _ny_trade_date(ts_ms: int) -> str:
    dt_ny = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(_NEW_YORK_TZ)
    return dt_ny.strftime("%Y-%m-%d")


def _gate_phase(minutes_from_open: float) -> str:
    if minutes_from_open < -60.0:
        return "pre_open"
    if minutes_from_open < 0.0:
        return "near_open"
    if minutes_from_open <= 90.0:
        return "opening_window"
    return "post_open"


def _nearest_odd_thousand(price: float) -> float:
    return round((price - 1000.0) / 2000.0) * 2000.0 + 1000.0


def _price_window_metrics(rows: list[sqlite3.Row]) -> dict[str, float | None]:
    prices = [float(row["price"]) for row in rows if row["price"] is not None and float(row["price"]) > 0]
    if not prices:
        return {
            "return_bps": None,
            "range_abs": None,
            "range_bps": None,
            "realized_vol_bps": None,
            "max_abs_excursion_abs": None,
            "max_abs_excursion_bps": None,
        }
    start_price = prices[0]
    end_price = prices[-1]
    high = max(prices)
    low = min(prices)
    rv = 0.0
    for prev_price, next_price in zip(prices, prices[1:]):
        if prev_price <= 0 or next_price <= 0:
            continue
        rv += math.log(next_price / prev_price) ** 2
    max_abs_excursion_abs = max(abs(price - start_price) for price in prices)
    return {
        "return_bps": ((end_price / start_price) - 1.0) * 10_000.0 if start_price > 0 else None,
        "range_abs": high - low,
        "range_bps": ((high - low) / start_price) * 10_000.0 if start_price > 0 else None,
        "realized_vol_bps": math.sqrt(rv) * 10_000.0,
        "max_abs_excursion_abs": max_abs_excursion_abs,
        "max_abs_excursion_bps": (
            (max_abs_excursion_abs / start_price) * 10_000.0 if start_price > 0 else None
        ),
    }


def _outcome_window_metrics(
    rows: list[sqlite3.Row],
    *,
    open_price: float,
    lower_bound: float | None,
    upper_bound: float | None,
) -> dict[str, float | int | None]:
    prices = [float(row["price"]) for row in rows if row["price"] is not None and float(row["price"]) > 0]
    if not prices or open_price <= 0:
        return {
            "max_abs_move": None,
            "max_abs_return_bps": None,
            "range_abs": None,
            "range_bps": None,
            "realized_vol_bps": None,
            "min_distance_to_edge": None,
            "crossed_outside_center": None,
        }
    rv = 0.0
    for prev_price, next_price in zip(prices, prices[1:]):
        if prev_price <= 0 or next_price <= 0:
            continue
        rv += math.log(next_price / prev_price) ** 2
    max_abs_move = max(abs(price - open_price) for price in prices)
    high = max(prices)
    low = min(prices)
    min_distance_to_edge = None
    if lower_bound is not None or upper_bound is not None:
        distances: list[float] = []
        for price in prices:
            if lower_bound is not None:
                distances.append(abs(price - lower_bound))
            if upper_bound is not None:
                distances.append(abs(upper_bound - price))
        min_distance_to_edge = min(distances) if distances else None
    crossed_outside_center = None
    if lower_bound is not None and upper_bound is not None:
        crossed_outside_center = 1 if any(price < lower_bound or price >= upper_bound for price in prices) else 0
    return {
        "max_abs_move": max_abs_move,
        "max_abs_return_bps": (max_abs_move / open_price) * 10_000.0,
        "range_abs": high - low,
        "range_bps": ((high - low) / open_price) * 10_000.0,
        "realized_vol_bps": math.sqrt(rv) * 10_000.0,
        "min_distance_to_edge": min_distance_to_edge,
        "crossed_outside_center": crossed_outside_center,
    }


def _book_levels_to_json(
    book: LocalOrderBook | None,
    *,
    side: str,
    level_limit: int = _FOCUS_BOOK_LEVEL_LIMIT,
) -> str:
    if book is None:
        return "[]"
    levels = book.asks if side == "ask" else book.bids
    if side == "ask":
        ordered = sorted(levels, key=lambda level: level.price)
    else:
        ordered = sorted(levels, key=lambda level: level.price, reverse=True)
    payload = [
        [float(level.price), float(level.size), float(level.price * level.size)]
        for level in ordered[:level_limit]
        if level.price > 0 and level.size > 0
    ]
    return json.dumps(payload, separators=(",", ":"))


def _best_price(book: LocalOrderBook | None, *, side: str) -> float | None:
    if book is None:
        return None
    levels = book.asks if side == "ask" else book.bids
    if not levels:
        return None
    if side == "ask":
        return min((level.price for level in levels if level.price > 0), default=None)
    return max((level.price for level in levels if level.price > 0), default=None)


def _depth_near_best(book: LocalOrderBook | None, *, side: str, width: float) -> float | None:
    best = _best_price(book, side=side)
    if book is None or best is None:
        return None
    levels = book.asks if side == "ask" else book.bids
    total = 0.0
    for level in levels:
        if level.price <= 0 or level.size <= 0:
            continue
        if side == "ask" and level.price <= best + width:
            total += level.price * level.size
        elif side == "bid" and level.price >= best - width:
            total += level.price * level.size
    return total


def _delta_or_none(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return current - previous


def _positive_or_none(value: float | None) -> float | None:
    return max(value, 0.0) if value is not None else None


def _negative_or_none(value: float | None) -> float | None:
    return max(-value, 0.0) if value is not None else None


def _focus_quote_state(
    *,
    book: LocalOrderBook | None,
    best_bid: float | None,
    best_ask: float | None,
) -> dict[str, float | int | None]:
    spread = best_ask - best_bid if best_bid is not None and best_ask is not None else None
    return {
        "book_last_update_ts_ms": (
            int(book.last_update_ts * 1000) if book and book.last_update_ts > 0 else None
        ),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "bid_depth_usd_2c": _depth_near_best(book, side="bid", width=0.02),
        "ask_depth_usd_2c": _depth_near_best(book, side="ask", width=0.02),
        "bid_depth_usd_5c": _depth_near_best(book, side="bid", width=0.05),
        "ask_depth_usd_5c": _depth_near_best(book, side="ask", width=0.05),
    }


def _build_focus_orderbook_delta_row(
    *,
    ts_ms: int,
    capture_date: str,
    event_slug: str,
    center_condition_id: str,
    condition_id: str,
    focus_role: str,
    outcome: str,
    token_id: str,
    state: dict[str, float | int | None],
    previous_state: dict[str, float | int | None] | None,
) -> dict:
    best_bid_delta = _delta_or_none(
        state.get("best_bid"), previous_state.get("best_bid") if previous_state else None
    )
    best_ask_delta = _delta_or_none(
        state.get("best_ask"), previous_state.get("best_ask") if previous_state else None
    )
    spread_delta = _delta_or_none(
        state.get("spread"), previous_state.get("spread") if previous_state else None
    )
    bid_delta_2c = _delta_or_none(
        state.get("bid_depth_usd_2c"),
        previous_state.get("bid_depth_usd_2c") if previous_state else None,
    )
    ask_delta_2c = _delta_or_none(
        state.get("ask_depth_usd_2c"),
        previous_state.get("ask_depth_usd_2c") if previous_state else None,
    )
    bid_delta_5c = _delta_or_none(
        state.get("bid_depth_usd_5c"),
        previous_state.get("bid_depth_usd_5c") if previous_state else None,
    )
    ask_delta_5c = _delta_or_none(
        state.get("ask_depth_usd_5c"),
        previous_state.get("ask_depth_usd_5c") if previous_state else None,
    )
    previous_ts = previous_state.get("ts_ms") if previous_state else None
    return {
        "ts_ms": ts_ms,
        "capture_date_tsi": capture_date,
        "event_slug": event_slug,
        "center_condition_id": center_condition_id,
        "condition_id": condition_id,
        "focus_role": focus_role,
        "outcome": outcome,
        "token_id": token_id,
        "book_last_update_ts_ms": state.get("book_last_update_ts_ms"),
        "best_bid": state.get("best_bid"),
        "best_ask": state.get("best_ask"),
        "best_bid_delta": best_bid_delta,
        "best_ask_delta": best_ask_delta,
        "spread": state.get("spread"),
        "spread_delta": spread_delta,
        "bid_depth_usd_2c": state.get("bid_depth_usd_2c"),
        "ask_depth_usd_2c": state.get("ask_depth_usd_2c"),
        "bid_depth_delta_2c": bid_delta_2c,
        "ask_depth_delta_2c": ask_delta_2c,
        "bid_refill_usd_2c": _positive_or_none(bid_delta_2c),
        "ask_refill_usd_2c": _positive_or_none(ask_delta_2c),
        "bid_cancel_usd_2c": _negative_or_none(bid_delta_2c),
        "ask_cancel_usd_2c": _negative_or_none(ask_delta_2c),
        "bid_depth_usd_5c": state.get("bid_depth_usd_5c"),
        "ask_depth_usd_5c": state.get("ask_depth_usd_5c"),
        "bid_depth_delta_5c": bid_delta_5c,
        "ask_depth_delta_5c": ask_delta_5c,
        "bid_refill_usd_5c": _positive_or_none(bid_delta_5c),
        "ask_refill_usd_5c": _positive_or_none(ask_delta_5c),
        "bid_cancel_usd_5c": _negative_or_none(bid_delta_5c),
        "ask_cancel_usd_5c": _negative_or_none(ask_delta_5c),
        "seconds_since_prev": (
            (ts_ms - int(previous_ts)) / 1000.0 if previous_ts is not None else None
        ),
    }


def _resolve_yes_no_tokens(market: dict) -> tuple[str, str] | None:
    token_ids = [str(token) for token in _parse_json_list(market.get("clobTokenIds"))]
    outcomes = [str(outcome).strip().lower() for outcome in _parse_json_list(market.get("outcomes"))]
    if len(token_ids) < 2 or len(outcomes) < 2:
        return None
    if "yes" in outcomes and "no" in outcomes:
        return token_ids[outcomes.index("yes")], token_ids[outcomes.index("no")]
    return token_ids[0], token_ids[1]


def _extract_initial_yes_no_prices(market: dict) -> tuple[float | None, float | None]:
    outcomes = [str(outcome).strip().lower() for outcome in _parse_json_list(market.get("outcomes"))]
    prices = _parse_json_list(market.get("outcomePrices"))
    if len(outcomes) < 2 or len(prices) < 2:
        return None, None
    try:
        yes_idx = outcomes.index("yes")
        no_idx = outcomes.index("no")
    except ValueError:
        return None, None
    try:
        return float(prices[yes_idx]), float(prices[no_idx])
    except (TypeError, ValueError):
        return None, None


def _market_sort_key(lower: float | None, upper: float | None) -> tuple[int, float]:
    if lower is None and upper is not None:
        return (0, upper)
    if lower is not None and upper is not None:
        return (1, lower)
    if lower is not None and upper is None:
        return (2, lower)
    return (3, float("inf"))


def _resolve_text(event: dict) -> str:
    parts = [str(event.get("description") or ""), str(event.get("resolutionSource") or "")]
    for market in event.get("markets") or []:
        if not isinstance(market, dict):
            continue
        parts.extend(
            [
                str(market.get("description") or ""),
                str(market.get("rules") or ""),
                str(market.get("resolutionSource") or ""),
            ]
        )
    return " ".join(part for part in parts if part).strip()


def _is_btc_daily_range_event(event: dict) -> bool:
    title = str(event.get("title") or "").strip()
    slug = str(event.get("slug") or "").strip()
    return bool(_BTC_DAILY_RANGE_TITLE.match(title) and _BTC_DAILY_RANGE_SLUG.match(slug))


def _parse_daily_range_event(event: dict) -> DailyRangeEvent | None:
    if not _is_btc_daily_range_event(event):
        return None

    event_slug = str(event.get("slug") or "").strip()
    event_title = str(event.get("title") or "").strip()
    resolution_text = _resolve_text(event)
    validation = validate_daily_range_rule(title=event_title, rule_text=resolution_text)
    if not validation.ok:
        log.warning(
            "Rejected BTC daily range event %s because rule text failed validation: %s",
            event_slug or "?",
            "; ".join(validation.issues),
        )
        return None

    start_date_ms = _iso_to_ms(str(event.get("startDate") or ""))
    end_date_ms = _iso_to_ms(str(event.get("endDate") or ""))
    raw_markets = event.get("markets") or []
    parsed: list[DailyRangeMarket] = []

    for raw_market in raw_markets:
        if not isinstance(raw_market, dict):
            continue
        resolved_tokens = _resolve_yes_no_tokens(raw_market)
        if resolved_tokens is None:
            continue
        group_item_title = str(raw_market.get("groupItemTitle") or "").strip()
        lower_bound, upper_bound = _parse_bounds(group_item_title, raw_market)
        yes_token_id, no_token_id = resolved_tokens
        initial_yes_price, initial_no_price = _extract_initial_yes_no_prices(raw_market)
        parsed.append(
            DailyRangeMarket(
                condition_id=str(raw_market.get("conditionId") or "").strip(),
                question=str(raw_market.get("question") or "").strip(),
                group_item_title=group_item_title,
                yes_token_id=yes_token_id,
                no_token_id=no_token_id,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                order_index=0,
                initial_yes_price=initial_yes_price,
                initial_no_price=initial_no_price,
            )
        )

    parsed = [
        market
        for market in parsed
        if market.condition_id and market.question and market.group_item_title
    ]
    if len(parsed) < 3:
        return None

    try:
        parse_daily_range_ladder(tuple(market.group_item_title for market in parsed))
    except (RangeParseError, LadderValidationError) as exc:
        log.warning(
            "Rejected BTC daily range event %s because ladder labels are not exhaustive/contiguous: %s",
            event_slug or "?",
            exc,
        )
        return None

    ordered = sorted(
        parsed,
        key=lambda market: _market_sort_key(market.lower_bound, market.upper_bound),
    )
    ordered = [
        DailyRangeMarket(
            condition_id=market.condition_id,
            question=market.question,
            group_item_title=market.group_item_title,
            yes_token_id=market.yes_token_id,
            no_token_id=market.no_token_id,
            lower_bound=market.lower_bound,
            upper_bound=market.upper_bound,
            order_index=index,
            initial_yes_price=market.initial_yes_price,
            initial_no_price=market.initial_no_price,
        )
        for index, market in enumerate(ordered)
    ]
    return DailyRangeEvent(
        event_slug=event_slug,
        event_title=event_title,
        start_date_ms=start_date_ms,
        end_date_ms=end_date_ms,
        source_url=f"https://polymarket.com/event/{event_slug}",
        resolution_text=resolution_text,
        markets=tuple(ordered),
    )


def _choose_front_event_meta(events: list[dict], now_ms: int) -> dict | None:
    candidates: list[tuple[int, dict]] = []
    for event in events:
        if not isinstance(event, dict) or not _is_btc_daily_range_event(event):
            continue
        end_date_ms = _iso_to_ms(str(event.get("endDate") or ""))
        if end_date_ms <= now_ms:
            continue
        candidates.append((end_date_ms, event))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _pick_fresh_price(
    latest_btc: dict[str, float],
    latest_btc_ts: dict[str, int],
    source_keys: tuple[str, ...],
    now_ms: int,
    max_age_ms: int,
) -> float | None:
    best_key = None
    best_ts = -1
    for key in source_keys:
        price = latest_btc.get(key)
        ts_ms = latest_btc_ts.get(key)
        if price is None or ts_ms is None:
            continue
        if now_ms - ts_ms > max_age_ms:
            continue
        if ts_ms > best_ts:
            best_ts = ts_ms
            best_key = key
    if best_key is None:
        return None
    return latest_btc.get(best_key)


def _empty_metrics() -> DepthMetrics:
    return DepthMetrics(
        vwap_ask=None,
        vwap_bid=None,
        spread=None,
        mid=None,
        depth_ok=False,
        bid_depth_usd=0.0,
        ask_depth_usd=0.0,
        imbalance=0.0,
        best_bid=None,
        best_ask=None,
    )


def _safe_sub(lhs: float | None, rhs: float | None) -> float | None:
    if lhs is None or rhs is None:
        return None
    return lhs - rhs


def _safe_sum(lhs: float | None, rhs: float | None) -> float | None:
    if lhs is None or rhs is None:
        return None
    return lhs + rhs


def _band_context(market: DailyRangeMarket, btc_price: float | None) -> dict[str, float | None]:
    lower = market.lower_bound
    upper = market.upper_bound
    if btc_price is None:
        return {
            "btc_distance_to_lower": None,
            "btc_distance_to_upper": None,
            "btc_distance_to_band_mid": None,
            "btc_position_in_band": None,
        }

    distance_to_lower = btc_price - lower if lower is not None else None
    distance_to_upper = upper - btc_price if upper is not None else None
    distance_to_band_mid = None
    position_in_band = None
    if lower is not None and upper is not None and upper > lower:
        band_mid = (lower + upper) / 2.0
        distance_to_band_mid = btc_price - band_mid
        position_in_band = (btc_price - lower) / (upper - lower)
    return {
        "btc_distance_to_lower": distance_to_lower,
        "btc_distance_to_upper": distance_to_upper,
        "btc_distance_to_band_mid": distance_to_band_mid,
        "btc_position_in_band": position_in_band,
    }


def _focus_role_for_distance(band_distance: int) -> tuple[str, int, int]:
    if band_distance == -1:
        return "lower", -1, 1
    if band_distance == 0:
        return "center", 0, 1
    if band_distance == 1:
        return "upper", 1, 1
    return "outer", band_distance, 0


def _build_state_feature_row(
    *,
    ts_ms: int,
    capture_date: str,
    event: DailyRangeEvent,
    tau_ms: int,
    btc_price: float | None,
    center_index: int,
    reason: str,
    all_rows: list[dict],
) -> dict:
    rows_by_distance = {int(row["band_distance"]): row for row in all_rows}
    center_row = rows_by_distance[0]
    lower_row = rows_by_distance.get(-1)
    upper_row = rows_by_distance.get(1)

    lower_yes_mid = lower_row["yes_mid"] if lower_row else None
    lower_no_mid = lower_row["no_mid"] if lower_row else None
    center_yes_mid = center_row["yes_mid"]
    center_no_mid = center_row["no_mid"]
    upper_yes_mid = upper_row["yes_mid"] if upper_row else None
    upper_no_mid = upper_row["no_mid"] if upper_row else None

    return {
        "ts_ms": ts_ms,
        "capture_date_tsi": capture_date,
        "event_slug": event.event_slug,
        "event_title": event.event_title,
        "event_end_ms": event.end_date_ms,
        "tau_ms": tau_ms,
        "selection_reason": reason,
        "btc_price_binance": btc_price,
        "center_condition_id": center_row["condition_id"],
        "center_label": center_row["group_item_title"],
        "center_order_index": center_index,
        "center_lower_bound": center_row["lower_bound"],
        "center_upper_bound": center_row["upper_bound"],
        "btc_distance_to_lower": center_row["btc_distance_to_lower"],
        "btc_distance_to_upper": center_row["btc_distance_to_upper"],
        "btc_distance_to_band_mid": center_row["btc_distance_to_band_mid"],
        "btc_position_in_band": center_row["btc_position_in_band"],
        "lower_condition_id": lower_row["condition_id"] if lower_row else None,
        "lower_label": lower_row["group_item_title"] if lower_row else None,
        "lower_yes_mid": lower_yes_mid,
        "lower_no_mid": lower_no_mid,
        "lower_yes_plus_no_mid": _safe_sum(lower_yes_mid, lower_no_mid),
        "center_yes_mid": center_yes_mid,
        "center_no_mid": center_no_mid,
        "center_yes_plus_no_mid": _safe_sum(center_yes_mid, center_no_mid),
        "upper_condition_id": upper_row["condition_id"] if upper_row else None,
        "upper_label": upper_row["group_item_title"] if upper_row else None,
        "upper_yes_mid": upper_yes_mid,
        "upper_no_mid": upper_no_mid,
        "upper_yes_plus_no_mid": _safe_sum(upper_yes_mid, upper_no_mid),
        "upper_minus_lower_yes_mid": _safe_sub(upper_yes_mid, lower_yes_mid),
        "upper_minus_lower_no_mid": _safe_sub(upper_no_mid, lower_no_mid),
        "center_minus_lower_yes_mid": _safe_sub(center_yes_mid, lower_yes_mid),
        "upper_minus_center_yes_mid": _safe_sub(upper_yes_mid, center_yes_mid),
        "center_minus_lower_no_mid": _safe_sub(center_no_mid, lower_no_mid),
        "upper_minus_center_no_mid": _safe_sub(upper_no_mid, center_no_mid),
        "wing_yes_mid_sum": _safe_sum(lower_yes_mid, upper_yes_mid),
        "wing_no_mid_sum": _safe_sum(lower_no_mid, upper_no_mid),
        "wing_yes_symmetry_abs": (
            abs(upper_yes_mid - lower_yes_mid)
            if upper_yes_mid is not None and lower_yes_mid is not None
            else None
        ),
        "wing_no_symmetry_abs": (
            abs(upper_no_mid - lower_no_mid)
            if upper_no_mid is not None and lower_no_mid is not None
            else None
        ),
    }


def _choose_center_index(markets: tuple[DailyRangeMarket, ...], btc_price: float | None) -> tuple[int, str]:
    if not markets:
        raise ValueError("markets cannot be empty")

    if btc_price is not None:
        for index, market in enumerate(markets):
            lower = market.lower_bound
            upper = market.upper_bound
            if lower is None and upper is not None and btc_price < upper:
                return index, "binance_price_in_bracket"
            if lower is not None and upper is None and btc_price >= lower:
                return index, "binance_price_in_bracket"
            if lower is not None and upper is not None and lower <= btc_price < upper:
                return index, "binance_price_in_bracket"

        first_upper = markets[0].upper_bound
        if first_upper is not None and btc_price < first_upper:
            return 0, "binance_price_below_ladder"
        return len(markets) - 1, "binance_price_above_ladder"

    best_index = max(
        range(len(markets)),
        key=lambda index: (
            markets[index].initial_yes_price is not None,
            markets[index].initial_yes_price or float("-inf"),
            -abs(index - (len(markets) // 2)),
        ),
    )
    return best_index, "consensus_yes_fallback"


def _select_focus_markets(
    markets: tuple[DailyRangeMarket, ...],
    btc_price: float | None,
) -> tuple[int, str, list[tuple[str, int, DailyRangeMarket]]]:
    center_index, reason = _choose_center_index(markets, btc_price)
    focus: list[tuple[str, int, DailyRangeMarket]] = []
    if center_index > 0:
        focus.append(("lower", -1, markets[center_index - 1]))
    focus.append(("center", 0, markets[center_index]))
    if center_index + 1 < len(markets):
        focus.append(("upper", 1, markets[center_index + 1]))
    return center_index, reason, focus


class DailyRangeDiscovery:
    def __init__(self, poll_interval_s: float = 60.0) -> None:
        self._poll_interval_s = poll_interval_s
        self._session: aiohttp.ClientSession | None = None
        self._last_signature: tuple[str, tuple[str, ...]] | None = None

    async def run(
        self,
        current_event_ref: dict[str, DailyRangeEvent | None],
        active_markets: dict[str, MarketInfo],
        clob_ws: CLOBWebSocket,
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        try:
            while True:
                try:
                    event = await self._discover_front_event()
                    if event is not None:
                        await self._apply_event(event, current_event_ref, active_markets, clob_ws, db_queue)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("Daily range discovery poll failed")
                await asyncio.sleep(self._poll_interval_s)
        finally:
            if self._session and not self._session.closed:
                await self._session.close()

    async def _discover_front_event(self) -> DailyRangeEvent | None:
        assert self._session is not None
        events = await fetch_gamma_keyset_rows_async(
            self._session,
            f"{settings.gamma_api_url}/events/keyset",
            "events",
            params={"active": "true", "closed": "false", "limit": 500, "order": "endDate", "ascending": "true"},
        )

        front_meta = _choose_front_event_meta(events, int(time.time() * 1000))
        if front_meta is None:
            return None

        slug = str(front_meta.get("slug") or "").strip()
        detail_url = f"{settings.gamma_api_url}/events/slug/{slug}"
        async with self._session.get(detail_url) as resp:
            resp.raise_for_status()
            detail = await resp.json()

        event = _parse_daily_range_event(detail if isinstance(detail, dict) else {})
        if event is None:
            log.warning("Front daily range event %s could not be parsed", slug)
        return event

    async def _apply_event(
        self,
        event: DailyRangeEvent,
        current_event_ref: dict[str, DailyRangeEvent | None],
        active_markets: dict[str, MarketInfo],
        clob_ws: CLOBWebSocket,
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        signature = (event.event_slug, tuple(market.condition_id for market in event.markets))
        if signature == self._last_signature:
            current_event_ref["event"] = event
            return

        previous_ids = set(active_markets.keys())
        next_ids = {market.condition_id for market in event.markets}
        for condition_id in sorted(previous_ids - next_ids):
            await clob_ws.unsubscribe(condition_id)
            active_markets.pop(condition_id, None)

        for market in event.markets:
            market_info = market.to_market_info(event.start_date_ms, event.end_date_ms)
            active_markets[market.condition_id] = market_info
            if market.condition_id not in previous_ids:
                await clob_ws.subscribe(market_info)

        current_event_ref["event"] = event
        self._last_signature = signature
        log.info(
            "Tracking daily range event %s with %d ladder markets",
            event.event_slug,
            len(event.markets),
        )

        discovered_at_ms = int(time.time() * 1000)
        capture_date = _capture_date_tsi(discovered_at_ms)
        try:
            db_queue.put_nowait(
                DBRow(
                    table="range_events",
                    data={
                        "event_slug": event.event_slug,
                        "event_title": event.event_title,
                        "start_date_ms": event.start_date_ms,
                        "end_date_ms": event.end_date_ms,
                        "capture_date_tsi": capture_date,
                        "market_count": len(event.markets),
                        "resolution_text": event.resolution_text,
                        "source_url": event.source_url,
                        "discovered_at_ms": discovered_at_ms,
                    },
                )
            )
            for market in event.markets:
                db_queue.put_nowait(
                    DBRow(
                        table="range_markets",
                        data={
                            "condition_id": market.condition_id,
                            "event_slug": event.event_slug,
                            "question": market.question,
                            "group_item_title": market.group_item_title,
                            "yes_token_id": market.yes_token_id,
                            "no_token_id": market.no_token_id,
                            "order_index": market.order_index,
                            "lower_bound": market.lower_bound,
                            "upper_bound": market.upper_bound,
                            "initial_yes_price": market.initial_yes_price,
                            "initial_no_price": market.initial_no_price,
                            "capture_date_tsi": capture_date,
                            "discovered_at_ms": discovered_at_ms,
                        },
                    )
                )
        except asyncio.QueueFull:
            log.warning("Daily range discovery DB queue full while persisting event metadata")


class BinanceFuturesMetricsPoller:
    def __init__(self, raw_logger: RawLogger) -> None:
        self._raw_logger = raw_logger
        self._session: aiohttp.ClientSession | None = None
        self._last_regime_signature: tuple[int | None, ...] | None = None
        self._last_mark_signature: tuple[int | None, float | None, float | None, float | None] | None = None
        self._last_agg_trade_id: int | None = None
        self._last_kline_close_time_ms: int | None = None
        self._last_rest_warning: dict[str, float] = {}
        self._trades_5s: deque[tuple[int, float, float]] = deque()
        self._trades_15s: deque[tuple[int, float, float]] = deque()
        self._buy_notional_5s = 0.0
        self._sell_notional_5s = 0.0
        self._buy_notional_15s = 0.0
        self._sell_notional_15s = 0.0

    async def run(self, db_queue: asyncio.Queue[DBRow]) -> None:
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        next_oi_poll = 0.0
        next_regime_poll = 0.0
        next_mark_poll = 0.0
        next_agg_trade_poll = 0.0
        next_kline_poll = 0.0
        try:
            while True:
                now_mono = time.monotonic()
                if now_mono >= next_mark_poll:
                    try:
                        await self._poll_mark_price(db_queue)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        log.exception("Binance futures mark price REST fallback failed")
                    next_mark_poll = (
                        now_mono + max(1.0, settings.binance_futures_mark_poll_interval_s)
                    )

                if now_mono >= next_agg_trade_poll:
                    try:
                        await self._poll_agg_trades(db_queue)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        log.exception("Binance futures aggTrade REST fallback failed")
                    next_agg_trade_poll = (
                        now_mono + max(1.0, settings.binance_futures_agg_trade_poll_interval_s)
                    )

                if now_mono >= next_kline_poll:
                    try:
                        await self._poll_kline(db_queue)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        log.exception("Binance futures kline REST fallback failed")
                    next_kline_poll = (
                        now_mono + max(5.0, settings.binance_futures_kline_poll_interval_s)
                    )

                if now_mono >= next_oi_poll:
                    try:
                        await self._poll_open_interest(db_queue)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        log.exception("Binance futures open interest poll failed")
                    next_oi_poll = now_mono + max(5.0, settings.binance_futures_oi_poll_interval_s)

                if now_mono >= next_regime_poll:
                    try:
                        await self._poll_regime(db_queue)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        log.exception("Binance futures regime poll failed")
                    next_regime_poll = (
                        now_mono + max(15.0, settings.binance_futures_regime_poll_interval_s)
                    )

                await asyncio.sleep(1.0)
        finally:
            if self._session and not self._session.closed:
                await self._session.close()

    async def _safe_get_json(self, path: str, params: dict[str, object]) -> object | None:
        assert self._session is not None
        url = f"{settings.binance_usdm_rest_base_url.rstrip('/')}{path}"
        try:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                payload = await resp.json()
            self._raw_logger.log(
                {
                    "ts": time.time(),
                    "src": "binance_futures_rest",
                    "path": path,
                    "params": params,
                    "msg": payload,
                }
            )
            return payload
        except asyncio.CancelledError:
            raise
        except Exception:
            warning_key = f"{path}:{params}"
            now_mono = time.monotonic()
            if now_mono - self._last_rest_warning.get(warning_key, 0.0) >= 60.0:
                log.warning("Binance futures REST request failed: %s params=%s", path, params)
                self._last_rest_warning[warning_key] = now_mono
            return None

    def _refresh_rest_trade_windows(self, now_ms: int) -> None:
        while self._trades_5s and now_ms - self._trades_5s[0][0] > 5_000:
            _ts_ms, buy_notional, sell_notional = self._trades_5s.popleft()
            self._buy_notional_5s -= buy_notional
            self._sell_notional_5s -= sell_notional
        while self._trades_15s and now_ms - self._trades_15s[0][0] > 15_000:
            _ts_ms, buy_notional, sell_notional = self._trades_15s.popleft()
            self._buy_notional_15s -= buy_notional
            self._sell_notional_15s -= sell_notional

    def _build_micro_tick_row_from_rest_agg_trades(
        self,
        payload: object,
        *,
        symbol: str,
    ) -> dict | None:
        if not isinstance(payload, list):
            return None
        items = [item for item in payload if isinstance(item, dict)]
        items.sort(key=lambda item: (_safe_int(item.get("a")) or -1, _safe_int(item.get("T")) or -1))

        latest_price: float | None = None
        latest_ts_ms: int | None = None
        latest_trade_id: int | None = None
        for item in items:
            trade_id = _safe_int(item.get("a"))
            if (
                trade_id is not None
                and self._last_agg_trade_id is not None
                and trade_id <= self._last_agg_trade_id
            ):
                continue
            price = _safe_float(item.get("p"))
            qty = _safe_float(item.get("q"))
            if price is None or qty is None or price <= 0 or qty <= 0:
                continue
            trade_ts_ms = _safe_int(item.get("T")) or _safe_int(item.get("E")) or int(time.time() * 1000)
            notional = price * qty
            sell_notional = notional if bool(item.get("m", False)) else 0.0
            buy_notional = notional if sell_notional == 0.0 else 0.0
            self._trades_5s.append((trade_ts_ms, buy_notional, sell_notional))
            self._trades_15s.append((trade_ts_ms, buy_notional, sell_notional))
            self._buy_notional_5s += buy_notional
            self._sell_notional_5s += sell_notional
            self._buy_notional_15s += buy_notional
            self._sell_notional_15s += sell_notional
            latest_price = price
            latest_ts_ms = trade_ts_ms
            latest_trade_id = trade_id if trade_id is not None else latest_trade_id
            if trade_id is not None:
                self._last_agg_trade_id = trade_id

        if latest_price is None or latest_ts_ms is None:
            return None
        self._refresh_rest_trade_windows(latest_ts_ms)
        total_5s = self._buy_notional_5s + self._sell_notional_5s
        total_15s = self._buy_notional_15s + self._sell_notional_15s
        return {
            "ts_ms": latest_ts_ms,
            "capture_date_tsi": _capture_date_tsi(latest_ts_ms),
            "source": "binance_usdm_aggtrade_rest",
            "symbol": symbol,
            "price": latest_price,
            "trade_ts_ms": latest_ts_ms,
            "trade_count_5s": len(self._trades_5s),
            "buy_notional_5s": max(0.0, self._buy_notional_5s),
            "sell_notional_5s": max(0.0, self._sell_notional_5s),
            "trade_imbalance_5s": (
                (self._buy_notional_5s - self._sell_notional_5s) / total_5s
                if total_5s > 0
                else 0.0
            ),
            "trade_count_15s": len(self._trades_15s),
            "buy_notional_15s": max(0.0, self._buy_notional_15s),
            "sell_notional_15s": max(0.0, self._sell_notional_15s),
            "trade_imbalance_15s": (
                (self._buy_notional_15s - self._sell_notional_15s) / total_15s
                if total_15s > 0
                else 0.0
            ),
        }

    async def _poll_mark_price(self, db_queue: asyncio.Queue[DBRow]) -> None:
        symbol = settings.binance_usdm_symbol.strip().upper()
        fetched_ts_ms = int(time.time() * 1000)
        payload = await self._safe_get_json("/fapi/v1/premiumIndex", {"symbol": symbol})
        row = _build_futures_mark_price_rest_row(
            payload,
            fetched_ts_ms=fetched_ts_ms,
            symbol=symbol,
        )
        if row is None:
            return
        signature = (
            _safe_int(row.get("ts_ms")),
            _safe_float(row.get("mark_price")),
            _safe_float(row.get("index_price")),
            _safe_float(row.get("funding_rate")),
        )
        if signature == self._last_mark_signature:
            return
        try:
            db_queue.put_nowait(DBRow(table="btc_futures_mark_prices", data=row))
            self._last_mark_signature = signature
        except asyncio.QueueFull:
            log.warning("DB queue full while writing futures mark price")

    async def _poll_agg_trades(self, db_queue: asyncio.Queue[DBRow]) -> None:
        symbol = settings.binance_usdm_symbol.strip().upper()
        params: dict[str, object] = {"symbol": symbol, "limit": 1000}
        if self._last_agg_trade_id is not None:
            params["fromId"] = self._last_agg_trade_id + 1
        payload = await self._safe_get_json("/fapi/v1/aggTrades", params)
        row = self._build_micro_tick_row_from_rest_agg_trades(payload, symbol=symbol)
        if row is None:
            return
        try:
            db_queue.put_nowait(DBRow(table="btc_futures_micro_ticks", data=row))
        except asyncio.QueueFull:
            log.warning("DB queue full while writing futures aggTrade micro tick")

    async def _poll_kline(self, db_queue: asyncio.Queue[DBRow]) -> None:
        symbol = settings.binance_usdm_symbol.strip().upper()
        interval = settings.binance_usdm_kline_interval.strip().lower()
        fetched_ts_ms = int(time.time() * 1000)
        payload = await self._safe_get_json(
            "/fapi/v1/klines",
            {"symbol": symbol, "interval": interval, "limit": 3},
        )
        if not isinstance(payload, list):
            return
        closed = [
            item for item in payload
            if isinstance(item, list | tuple)
            and (_safe_int(item[6]) or 0) <= fetched_ts_ms
        ]
        if not closed:
            return
        row = _build_futures_kline_rest_row(closed[-1], symbol=symbol, interval=interval)
        if row is None:
            return
        close_time_ms = _safe_int(row.get("close_time_ms"))
        if (
            close_time_ms is None
            or (
                self._last_kline_close_time_ms is not None
                and close_time_ms <= self._last_kline_close_time_ms
            )
        ):
            return
        try:
            db_queue.put_nowait(DBRow(table="btc_futures_klines", data=row))
            self._last_kline_close_time_ms = close_time_ms
        except asyncio.QueueFull:
            log.warning("DB queue full while writing futures kline")

    async def _poll_open_interest(self, db_queue: asyncio.Queue[DBRow]) -> None:
        symbol = settings.binance_usdm_symbol.strip().upper()
        payload = await self._safe_get_json("/fapi/v1/openInterest", {"symbol": symbol})
        if not isinstance(payload, dict):
            return
        open_interest = _safe_float(payload.get("openInterest"))
        if open_interest is None:
            return
        ts_ms = _safe_int(payload.get("time")) or int(time.time() * 1000)
        capture_date = _capture_date_tsi(ts_ms)
        try:
            db_queue.put_nowait(
                DBRow(
                    table="btc_futures_open_interest",
                    data={
                        "ts_ms": ts_ms,
                        "capture_date_tsi": capture_date,
                        "source": "binance_usdm_rest",
                        "symbol": symbol,
                        "open_interest": open_interest,
                    },
                )
            )
        except asyncio.QueueFull:
            log.warning("DB queue full while writing futures open interest")

    async def _poll_regime(self, db_queue: asyncio.Queue[DBRow]) -> None:
        symbol = settings.binance_usdm_symbol.strip().upper()
        period = settings.binance_futures_regime_period.strip().lower()
        fetch_ts_ms = int(time.time() * 1000)
        capture_date = _capture_date_tsi(fetch_ts_ms)
        params = {"symbol": symbol, "period": period, "limit": 1}
        (
            open_interest_hist_payload,
            global_long_short_payload,
            top_trader_account_payload,
            top_trader_position_payload,
            taker_buy_sell_payload,
        ) = await asyncio.gather(
            self._safe_get_json("/futures/data/openInterestHist", params),
            self._safe_get_json("/futures/data/globalLongShortAccountRatio", params),
            self._safe_get_json("/futures/data/topLongShortAccountRatio", params),
            self._safe_get_json("/futures/data/topLongShortPositionRatio", params),
            self._safe_get_json("/futures/data/takerlongshortRatio", params),
        )

        row = _build_futures_regime_row(
            fetched_ts_ms=fetch_ts_ms,
            capture_date_tsi=capture_date,
            symbol=symbol,
            period=period,
            open_interest_hist=_latest_metric_entry(open_interest_hist_payload),
            global_long_short=_latest_metric_entry(global_long_short_payload),
            top_trader_account=_latest_metric_entry(top_trader_account_payload),
            top_trader_position=_latest_metric_entry(top_trader_position_payload),
            taker_buy_sell=_latest_metric_entry(taker_buy_sell_payload),
        )
        signature = _futures_regime_signature(row)
        if row is None or signature is None or signature == self._last_regime_signature:
            return
        try:
            db_queue.put_nowait(DBRow(table="btc_futures_regime_5m", data=row))
            self._last_regime_signature = signature
        except asyncio.QueueFull:
            log.warning("DB queue full while writing futures regime row")


class DeribitIndexPoller:
    def __init__(self, raw_logger: RawLogger) -> None:
        self._raw_logger = raw_logger
        self._session: aiohttp.ClientSession | None = None
        self._last_signature: dict[str, tuple[float | None, float | None] | None] = {}

    async def run(self, db_queue: asyncio.Queue[DBRow]) -> None:
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        interval_s = max(15.0, settings.deribit_index_poll_interval_s)
        try:
            while True:
                try:
                    await self._poll_indexes(db_queue)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("Deribit public index poll failed")
                await asyncio.sleep(interval_s)
        finally:
            if self._session and not self._session.closed:
                await self._session.close()

    async def _safe_get_index_price(self, index_name: str) -> dict | None:
        assert self._session is not None
        url = f"{settings.deribit_api_base_url.rstrip('/')}/public/get_index_price"
        params = {"index_name": index_name}
        try:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                payload = await resp.json()
            self._raw_logger.log(
                {
                    "ts": time.time(),
                    "src": "deribit_public_rest",
                    "path": "/public/get_index_price",
                    "params": params,
                    "msg": payload,
                }
            )
            result = payload.get("result") if isinstance(payload, dict) else None
            return result if isinstance(result, dict) else None
        except asyncio.CancelledError:
            raise
        except Exception:
            log.warning("Deribit public index request failed: %s", index_name)
            return None

    async def _poll_indexes(self, db_queue: asyncio.Queue[DBRow]) -> None:
        index_names = settings.deribit_index_name_list
        if not index_names:
            return
        fetched_ts_ms = int(time.time() * 1000)
        capture_date = _capture_date_tsi(fetched_ts_ms)
        results = await asyncio.gather(
            *(self._safe_get_index_price(index_name) for index_name in index_names)
        )
        for index_name, result in zip(index_names, results, strict=False):
            if not result:
                continue
            index_price = _safe_float(result.get("index_price"))
            estimated_delivery_price = _safe_float(result.get("estimated_delivery_price"))
            signature = (index_price, estimated_delivery_price)
            if self._last_signature.get(index_name) == signature:
                continue
            try:
                db_queue.put_nowait(
                    DBRow(
                        table="deribit_index_prices",
                        data={
                            "ts_ms": fetched_ts_ms,
                            "capture_date_tsi": capture_date,
                            "source": "deribit_public_rest",
                            "index_name": index_name,
                            "index_price": index_price,
                            "estimated_delivery_price": estimated_delivery_price,
                        },
                    )
                )
                self._last_signature[index_name] = signature
            except asyncio.QueueFull:
                log.warning("DB queue full while writing Deribit index row")


class NYOpenGateCollector:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    async def run(
        self,
        current_event_ref: dict[str, DailyRangeEvent | None],
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout=5000")
        try:
            while True:
                now = time.time()
                next_tick = int(now // _GATE_SNAPSHOT_INTERVAL_S + 1) * _GATE_SNAPSHOT_INTERVAL_S
                await asyncio.sleep(max(0.0, next_tick - now))
                ts_ms = int(time.time() * 1000)
                event = current_event_ref.get("event")
                try:
                    snapshot = self._build_snapshot(ts_ms, event)
                    if snapshot is not None:
                        db_queue.put_nowait(DBRow(table="ny_open_gate_snapshots", data=snapshot))
                    outcome = self._build_outcome(ts_ms, event)
                    if outcome is not None:
                        db_queue.put_nowait(DBRow(table="ny_open_gate_outcomes", data=outcome))
                except asyncio.QueueFull:
                    log.warning("DB queue full while writing NY open gate rows")
                except Exception:
                    log.exception("NY open gate collector tick failed")
        finally:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def _query_one(self, query: str, params: tuple[object, ...]) -> sqlite3.Row | None:
        assert self._conn is not None
        return self._conn.execute(query, params).fetchone()

    def _query_all(self, query: str, params: tuple[object, ...]) -> list[sqlite3.Row]:
        assert self._conn is not None
        return self._conn.execute(query, params).fetchall()

    def _build_snapshot(self, ts_ms: int, event: DailyRangeEvent | None) -> dict | None:
        state = self._query_one(
            """
            SELECT
                ts_ms,
                event_slug,
                event_title,
                center_label,
                center_lower_bound,
                center_upper_bound,
                btc_price_binance,
                btc_distance_to_lower,
                btc_distance_to_upper,
                btc_distance_to_band_mid,
                btc_position_in_band,
                lower_yes_mid,
                lower_no_mid,
                center_yes_mid,
                center_no_mid,
                upper_yes_mid,
                upper_no_mid,
                wing_yes_symmetry_abs,
                wing_no_symmetry_abs
            FROM range_state_features
            WHERE ts_ms <= ?
            ORDER BY ts_ms DESC
            LIMIT 1
            """,
            (ts_ms,),
        )
        tick = self._query_one(
            """
            SELECT
                ts_ms,
                price,
                best_bid,
                best_ask,
                mid,
                spread_bps,
                trade_count_5s,
                buy_notional_5s,
                sell_notional_5s,
                trade_imbalance_5s,
                trade_count_15s,
                buy_notional_15s,
                sell_notional_15s,
                trade_imbalance_15s
            FROM btc_ticks
            WHERE ts_ms <= ?
            ORDER BY ts_ms DESC
            LIMIT 1
            """,
            (ts_ms,),
        )
        if tick is None or tick["price"] is None:
            return None

        latest_kline = self._query_one(
            """
            SELECT
                ts_ms,
                close_price,
                volume_base,
                volume_quote,
                trade_count,
                taker_buy_base,
                taker_buy_quote
            FROM btc_spot_klines
            WHERE ts_ms <= ?
            ORDER BY ts_ms DESC
            LIMIT 1
            """,
            (ts_ms,),
        )
        rows_5m = self._query_all(
            """
            SELECT volume_quote, trade_count, taker_buy_quote
            FROM btc_spot_klines
            WHERE ts_ms > ? AND ts_ms <= ?
            ORDER BY ts_ms ASC
            """,
            (ts_ms - 5 * 60_000, ts_ms),
        )
        oi = self._query_one(
            """
            SELECT ts_ms, open_interest
            FROM btc_futures_open_interest
            WHERE ts_ms <= ?
            ORDER BY ts_ms DESC
            LIMIT 1
            """,
            (ts_ms,),
        )
        oi_prev = self._query_one(
            """
            SELECT ts_ms, open_interest
            FROM btc_futures_open_interest
            WHERE ts_ms <= ?
            ORDER BY ts_ms DESC
            LIMIT 1
            """,
            (ts_ms - 15 * 60_000,),
        )
        regime = self._query_one(
            """
            SELECT
                fetched_ts_ms,
                global_long_short_ratio,
                global_long_account,
                global_short_account,
                top_trader_account_ratio,
                top_trader_position_ratio,
                taker_buy_sell_ratio,
                taker_buy_vol,
                taker_sell_vol,
                sum_open_interest,
                sum_open_interest_value
            FROM btc_futures_regime_5m
            WHERE fetched_ts_ms <= ?
            ORDER BY fetched_ts_ms DESC
            LIMIT 1
            """,
            (ts_ms,),
        )
        price_rows_15m = self._query_all(
            "SELECT ts_ms, price FROM btc_ticks WHERE ts_ms > ? AND ts_ms <= ? ORDER BY ts_ms ASC",
            (ts_ms - 15 * 60_000, ts_ms),
        )
        price_rows_60m = self._query_all(
            "SELECT ts_ms, price FROM btc_ticks WHERE ts_ms > ? AND ts_ms <= ? ORDER BY ts_ms ASC",
            (ts_ms - 60 * 60_000, ts_ms),
        )
        price_rows_180m = self._query_all(
            "SELECT ts_ms, price FROM btc_ticks WHERE ts_ms > ? AND ts_ms <= ? ORDER BY ts_ms ASC",
            (ts_ms - 180 * 60_000, ts_ms),
        )

        price = float(tick["price"])
        odd_thousand = _nearest_odd_thousand(price)
        price_metrics_15m = _price_window_metrics(price_rows_15m)
        price_metrics_60m = _price_window_metrics(price_rows_60m)
        price_metrics_180m = _price_window_metrics(price_rows_180m)
        ny_open_ts_ms = _ny_open_ts_ms(ts_ms)
        minutes_from_open = (ts_ms - ny_open_ts_ms) / 60_000.0

        volume_quote_5m = sum(float(row["volume_quote"] or 0.0) for row in rows_5m)
        trade_count_5m = sum(int(row["trade_count"] or 0) for row in rows_5m)
        taker_buy_quote_5m = sum(float(row["taker_buy_quote"] or 0.0) for row in rows_5m)
        taker_buy_ratio_1m = None
        taker_buy_ratio_5m = None
        if latest_kline is not None and float(latest_kline["volume_quote"] or 0.0) > 0:
            taker_buy_ratio_1m = float(latest_kline["taker_buy_quote"] or 0.0) / float(
                latest_kline["volume_quote"] or 0.0
            )
        if volume_quote_5m > 0:
            taker_buy_ratio_5m = taker_buy_quote_5m / volume_quote_5m

        open_interest_delta_15m = None
        if oi is not None and oi_prev is not None:
            open_interest_delta_15m = float(oi["open_interest"]) - float(oi_prev["open_interest"])

        return {
            "ts_ms": ts_ms,
            "capture_date_tsi": _capture_date_tsi(ts_ms),
            "trade_date_ny": _ny_trade_date(ts_ms),
            "event_slug": str(state["event_slug"]) if state is not None else (event.event_slug if event else None),
            "event_title": str(state["event_title"]) if state is not None else (event.event_title if event else None),
            "ny_open_ts_ms": ny_open_ts_ms,
            "minutes_from_open": minutes_from_open,
            "gate_phase": _gate_phase(minutes_from_open),
            "btc_price_binance": price,
            "nearest_odd_thousand": odd_thousand,
            "abs_distance_to_odd_thousand": abs(price - odd_thousand),
            "return_15m_bps": price_metrics_15m["return_bps"],
            "range_15m_abs": price_metrics_15m["range_abs"],
            "realized_vol_15m_bps": price_metrics_15m["realized_vol_bps"],
            "max_abs_excursion_15m_abs": price_metrics_15m["max_abs_excursion_abs"],
            "return_60m_bps": price_metrics_60m["return_bps"],
            "range_60m_abs": price_metrics_60m["range_abs"],
            "realized_vol_60m_bps": price_metrics_60m["realized_vol_bps"],
            "max_abs_excursion_60m_abs": price_metrics_60m["max_abs_excursion_abs"],
            "return_180m_bps": price_metrics_180m["return_bps"],
            "range_180m_abs": price_metrics_180m["range_abs"],
            "realized_vol_180m_bps": price_metrics_180m["realized_vol_bps"],
            "max_abs_excursion_180m_abs": price_metrics_180m["max_abs_excursion_abs"],
            "spot_best_bid": tick["best_bid"],
            "spot_best_ask": tick["best_ask"],
            "spot_mid": tick["mid"],
            "spot_spread_bps": tick["spread_bps"],
            "trade_count_5s": int(tick["trade_count_5s"] or 0),
            "buy_notional_5s": float(tick["buy_notional_5s"] or 0.0),
            "sell_notional_5s": float(tick["sell_notional_5s"] or 0.0),
            "trade_imbalance_5s": float(tick["trade_imbalance_5s"] or 0.0),
            "trade_count_15s": int(tick["trade_count_15s"] or 0),
            "buy_notional_15s": float(tick["buy_notional_15s"] or 0.0),
            "sell_notional_15s": float(tick["sell_notional_15s"] or 0.0),
            "trade_imbalance_15s": float(tick["trade_imbalance_15s"] or 0.0),
            "spot_volume_base_1m": (float(latest_kline["volume_base"]) if latest_kline else None),
            "spot_volume_quote_1m": (float(latest_kline["volume_quote"]) if latest_kline else None),
            "spot_trade_count_1m": (int(latest_kline["trade_count"]) if latest_kline else None),
            "spot_taker_buy_quote_1m": (
                float(latest_kline["taker_buy_quote"]) if latest_kline else None
            ),
            "spot_taker_buy_ratio_1m": taker_buy_ratio_1m,
            "spot_volume_quote_5m": volume_quote_5m if rows_5m else None,
            "spot_trade_count_5m": trade_count_5m if rows_5m else None,
            "spot_taker_buy_ratio_5m": taker_buy_ratio_5m,
            "futures_open_interest": (float(oi["open_interest"]) if oi else None),
            "futures_open_interest_delta_15m": open_interest_delta_15m,
            "futures_sum_open_interest": (
                float(regime["sum_open_interest"]) if regime and regime["sum_open_interest"] is not None else None
            ),
            "futures_sum_open_interest_value": (
                float(regime["sum_open_interest_value"])
                if regime and regime["sum_open_interest_value"] is not None
                else None
            ),
            "futures_global_long_short_ratio": (
                float(regime["global_long_short_ratio"])
                if regime and regime["global_long_short_ratio"] is not None
                else None
            ),
            "futures_top_trader_account_ratio": (
                float(regime["top_trader_account_ratio"])
                if regime and regime["top_trader_account_ratio"] is not None
                else None
            ),
            "futures_top_trader_position_ratio": (
                float(regime["top_trader_position_ratio"])
                if regime and regime["top_trader_position_ratio"] is not None
                else None
            ),
            "futures_taker_buy_sell_ratio": (
                float(regime["taker_buy_sell_ratio"])
                if regime and regime["taker_buy_sell_ratio"] is not None
                else None
            ),
            "center_label": (str(state["center_label"]) if state is not None else None),
            "center_lower_bound": (state["center_lower_bound"] if state is not None else None),
            "center_upper_bound": (state["center_upper_bound"] if state is not None else None),
            "center_yes_mid": (state["center_yes_mid"] if state is not None else None),
            "center_no_mid": (state["center_no_mid"] if state is not None else None),
            "lower_yes_mid": (state["lower_yes_mid"] if state is not None else None),
            "lower_no_mid": (state["lower_no_mid"] if state is not None else None),
            "upper_yes_mid": (state["upper_yes_mid"] if state is not None else None),
            "upper_no_mid": (state["upper_no_mid"] if state is not None else None),
            "wing_yes_symmetry_abs": (state["wing_yes_symmetry_abs"] if state is not None else None),
            "wing_no_symmetry_abs": (state["wing_no_symmetry_abs"] if state is not None else None),
            "btc_distance_to_lower": (state["btc_distance_to_lower"] if state is not None else None),
            "btc_distance_to_upper": (state["btc_distance_to_upper"] if state is not None else None),
            "btc_distance_to_band_mid": (
                state["btc_distance_to_band_mid"] if state is not None else None
            ),
            "btc_position_in_band": (state["btc_position_in_band"] if state is not None else None),
        }

    def _build_outcome(self, ts_ms: int, event: DailyRangeEvent | None) -> dict | None:
        ny_open_ts_ms = _ny_open_ts_ms(ts_ms)
        if ts_ms < ny_open_ts_ms + 90 * 60_000:
            return None
        trade_date_ny = _ny_trade_date(ts_ms)
        existing = self._query_one(
            """
            SELECT id FROM ny_open_gate_outcomes
            WHERE trade_date_ny = ?
            LIMIT 1
            """,
            (trade_date_ny,),
        )
        if existing is not None:
            return None

        price_rows_90m = self._query_all(
            "SELECT ts_ms, price FROM btc_ticks WHERE ts_ms >= ? AND ts_ms <= ? ORDER BY ts_ms ASC",
            (ny_open_ts_ms, ny_open_ts_ms + 90 * 60_000),
        )
        if not price_rows_90m:
            return None
        open_price = float(price_rows_90m[0]["price"])
        open_state = self._query_one(
            """
            SELECT
                event_slug,
                event_title,
                center_label,
                center_lower_bound,
                center_upper_bound,
                center_yes_mid,
                center_no_mid,
                btc_distance_to_lower,
                btc_distance_to_upper
            FROM range_state_features
            WHERE ts_ms <= ?
            ORDER BY ts_ms DESC
            LIMIT 1
            """,
            (ny_open_ts_ms,),
        )
        if open_state is None and event is None:
            return None
        lower_bound = open_state["center_lower_bound"] if open_state is not None else None
        upper_bound = open_state["center_upper_bound"] if open_state is not None else None
        rows_30m = [row for row in price_rows_90m if int(row["ts_ms"]) <= ny_open_ts_ms + 30 * 60_000]
        rows_60m = [row for row in price_rows_90m if int(row["ts_ms"]) <= ny_open_ts_ms + 60 * 60_000]
        metrics_30m = _outcome_window_metrics(
            rows_30m,
            open_price=open_price,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )
        metrics_60m = _outcome_window_metrics(
            rows_60m,
            open_price=open_price,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )
        metrics_90m = _outcome_window_metrics(
            price_rows_90m,
            open_price=open_price,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )
        return {
            "trade_date_ny": trade_date_ny,
            "capture_date_tsi": _capture_date_tsi(ts_ms),
            "event_slug": (
                str(open_state["event_slug"]) if open_state is not None else (event.event_slug if event else None)
            ),
            "event_title": (
                str(open_state["event_title"]) if open_state is not None else (event.event_title if event else None)
            ),
            "ny_open_ts_ms": ny_open_ts_ms,
            "open_price_binance": open_price,
            "open_center_label": (str(open_state["center_label"]) if open_state is not None else None),
            "open_center_lower_bound": lower_bound,
            "open_center_upper_bound": upper_bound,
            "open_center_yes_mid": (
                float(open_state["center_yes_mid"]) if open_state and open_state["center_yes_mid"] is not None else None
            ),
            "open_center_no_mid": (
                float(open_state["center_no_mid"]) if open_state and open_state["center_no_mid"] is not None else None
            ),
            "open_distance_to_lower": (
                float(open_state["btc_distance_to_lower"])
                if open_state and open_state["btc_distance_to_lower"] is not None
                else None
            ),
            "open_distance_to_upper": (
                float(open_state["btc_distance_to_upper"])
                if open_state and open_state["btc_distance_to_upper"] is not None
                else None
            ),
            "max_abs_move_30m": metrics_30m["max_abs_move"],
            "max_abs_return_30m_bps": metrics_30m["max_abs_return_bps"],
            "range_30m_abs": metrics_30m["range_abs"],
            "range_30m_bps": metrics_30m["range_bps"],
            "realized_vol_30m_bps": metrics_30m["realized_vol_bps"],
            "min_distance_to_edge_30m": metrics_30m["min_distance_to_edge"],
            "crossed_outside_center_30m": metrics_30m["crossed_outside_center"],
            "max_abs_move_60m": metrics_60m["max_abs_move"],
            "max_abs_return_60m_bps": metrics_60m["max_abs_return_bps"],
            "range_60m_abs": metrics_60m["range_abs"],
            "range_60m_bps": metrics_60m["range_bps"],
            "realized_vol_60m_bps": metrics_60m["realized_vol_bps"],
            "min_distance_to_edge_60m": metrics_60m["min_distance_to_edge"],
            "crossed_outside_center_60m": metrics_60m["crossed_outside_center"],
            "max_abs_move_90m": metrics_90m["max_abs_move"],
            "max_abs_return_90m_bps": metrics_90m["max_abs_return_bps"],
            "range_90m_abs": metrics_90m["range_abs"],
            "range_90m_bps": metrics_90m["range_bps"],
            "realized_vol_90m_bps": metrics_90m["realized_vol_bps"],
            "min_distance_to_edge_90m": metrics_90m["min_distance_to_edge"],
            "crossed_outside_center_90m": metrics_90m["crossed_outside_center"],
        }


class DailyRangeSnapshotter:
    def __init__(self) -> None:
        self._drops = 0
        self._last_drop_report = 0.0
        self._focus_quote_event_slug: str | None = None
        self._focus_quote_states: dict[
            tuple[str, str, str],
            dict[str, float | int | None],
        ] = {}

    def _queue_focus_orderbook(
        self,
        *,
        ts_ms: int,
        capture_date: str,
        event_slug: str,
        center_condition_id: str,
        condition_id: str,
        focus_role: str,
        outcome: str,
        token_id: str,
        book: LocalOrderBook | None,
        metrics: DepthMetrics,
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        book_last_update_ts_ms = (
            int(book.last_update_ts * 1000) if book and book.last_update_ts > 0 else None
        )
        db_queue.put_nowait(
            DBRow(
                table="range_focus_orderbooks",
                data={
                    "ts_ms": ts_ms,
                    "capture_date_tsi": capture_date,
                    "event_slug": event_slug,
                    "center_condition_id": center_condition_id,
                    "condition_id": condition_id,
                    "focus_role": focus_role,
                    "outcome": outcome,
                    "token_id": token_id,
                    "book_last_update_ts_ms": book_last_update_ts_ms,
                    "best_bid": metrics.best_bid,
                    "best_ask": metrics.best_ask,
                    "bid_levels_json": _book_levels_to_json(book, side="bid"),
                    "ask_levels_json": _book_levels_to_json(book, side="ask"),
                },
            )
        )
        state = _focus_quote_state(
            book=book,
            best_bid=metrics.best_bid,
            best_ask=metrics.best_ask,
        )
        state["ts_ms"] = ts_ms
        key = (event_slug, token_id, outcome)
        previous_state = self._focus_quote_states.get(key)
        db_queue.put_nowait(
            DBRow(
                table="range_focus_orderbook_deltas",
                data=_build_focus_orderbook_delta_row(
                    ts_ms=ts_ms,
                    capture_date=capture_date,
                    event_slug=event_slug,
                    center_condition_id=center_condition_id,
                    condition_id=condition_id,
                    focus_role=focus_role,
                    outcome=outcome,
                    token_id=token_id,
                    state=state,
                    previous_state=previous_state,
                ),
            )
        )
        self._focus_quote_states[key] = state

    async def run(
        self,
        current_event_ref: dict[str, DailyRangeEvent | None],
        orderbooks: dict[str, LocalOrderBook],
        latest_btc: dict[str, float],
        latest_btc_ts: dict[str, int],
        binance_micro: BinanceMicroState,
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        while True:
            try:
                now = time.time()
                next_tick = int(now) + 1
                await asyncio.sleep(max(0.0, next_tick - now))

                ts_ms = int(time.time() * 1000)
                capture_date = _capture_date_tsi(ts_ms)
                btc_price = _pick_fresh_price(
                    latest_btc,
                    latest_btc_ts,
                    ("binance_ws", "binance"),
                    ts_ms,
                    settings.btc_price_max_age_ms,
                )
                await self._queue_btc_tick(ts_ms, capture_date, btc_price, binance_micro, db_queue)

                event = current_event_ref.get("event")
                if event is None or not event.markets:
                    continue
                if self._focus_quote_event_slug != event.event_slug:
                    self._focus_quote_event_slug = event.event_slug
                    self._focus_quote_states.clear()

                tau_ms = max(0, event.end_date_ms - ts_ms)
                center_index, reason = _choose_center_index(event.markets, btc_price)
                center_market = event.markets[center_index]
                all_rows: list[dict] = []
                for market in event.markets:
                    band_distance = market.order_index - center_index
                    role, rank, is_focus = _focus_role_for_distance(band_distance)
                    yes_book = orderbooks.get(market.yes_token_id)
                    no_book = orderbooks.get(market.no_token_id)
                    yes_metrics = (
                        compute_depth_metrics(yes_book, settings.vwap_target_usd)
                        if yes_book
                        else _empty_metrics()
                    )
                    no_metrics = (
                        compute_depth_metrics(no_book, settings.vwap_target_usd)
                        if no_book
                        else _empty_metrics()
                    )
                    band_context = _band_context(market, btc_price)
                    row = {
                        "ts_ms": ts_ms,
                        "capture_date_tsi": capture_date,
                        "event_slug": event.event_slug,
                        "event_title": event.event_title,
                        "event_end_ms": event.end_date_ms,
                        "tau_ms": tau_ms,
                        "center_condition_id": center_market.condition_id,
                        "center_order_index": center_index,
                        "focus_role": role,
                        "focus_rank": rank,
                        "band_distance": band_distance,
                        "is_focus": is_focus,
                        "selection_reason": reason,
                        "condition_id": market.condition_id,
                        "question": market.question,
                        "group_item_title": market.group_item_title,
                        "order_index": market.order_index,
                        "lower_bound": market.lower_bound,
                        "upper_bound": market.upper_bound,
                        "btc_price_binance": btc_price,
                        "btc_distance_to_lower": band_context["btc_distance_to_lower"],
                        "btc_distance_to_upper": band_context["btc_distance_to_upper"],
                        "btc_distance_to_band_mid": band_context["btc_distance_to_band_mid"],
                        "btc_position_in_band": band_context["btc_position_in_band"],
                        "yes_best_bid": yes_metrics.best_bid,
                        "yes_best_ask": yes_metrics.best_ask,
                        "yes_mid": yes_metrics.mid,
                        "yes_spread": yes_metrics.spread,
                        "yes_bid_depth_usd": yes_metrics.bid_depth_usd,
                        "yes_ask_depth_usd": yes_metrics.ask_depth_usd,
                        "yes_depth_ok": 1 if yes_metrics.depth_ok else 0,
                        "no_best_bid": no_metrics.best_bid,
                        "no_best_ask": no_metrics.best_ask,
                        "no_mid": no_metrics.mid,
                        "no_spread": no_metrics.spread,
                        "no_bid_depth_usd": no_metrics.bid_depth_usd,
                        "no_ask_depth_usd": no_metrics.ask_depth_usd,
                        "no_depth_ok": 1 if no_metrics.depth_ok else 0,
                    }
                    all_rows.append(row)
                    try:
                        db_queue.put_nowait(DBRow(table="range_snapshots", data=row))
                    except asyncio.QueueFull:
                        self._drops += 1
                    if is_focus:
                        try:
                            self._queue_focus_orderbook(
                                ts_ms=ts_ms,
                                capture_date=capture_date,
                                event_slug=event.event_slug,
                                center_condition_id=center_market.condition_id,
                                condition_id=market.condition_id,
                                focus_role=role,
                                outcome="yes",
                                token_id=market.yes_token_id,
                                book=yes_book,
                                metrics=yes_metrics,
                                db_queue=db_queue,
                            )
                            self._queue_focus_orderbook(
                                ts_ms=ts_ms,
                                capture_date=capture_date,
                                event_slug=event.event_slug,
                                center_condition_id=center_market.condition_id,
                                condition_id=market.condition_id,
                                focus_role=role,
                                outcome="no",
                                token_id=market.no_token_id,
                                book=no_book,
                                metrics=no_metrics,
                                db_queue=db_queue,
                            )
                        except asyncio.QueueFull:
                            self._drops += 1

                try:
                    db_queue.put_nowait(
                        DBRow(
                            table="range_state_features",
                            data=_build_state_feature_row(
                                ts_ms=ts_ms,
                                capture_date=capture_date,
                                event=event,
                                tau_ms=tau_ms,
                                btc_price=btc_price,
                                center_index=center_index,
                                reason=reason,
                                all_rows=all_rows,
                            ),
                        )
                    )
                except asyncio.QueueFull:
                    self._drops += 1

                now_mono = time.monotonic()
                if self._drops > 0 and now_mono - self._last_drop_report >= 60:
                    log.warning("Daily range snapshotter dropped %d rows in the last 60s", self._drops)
                    self._drops = 0
                    self._last_drop_report = now_mono

            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Daily range snapshotter error")
                await asyncio.sleep(1)

    async def _queue_btc_tick(
        self,
        ts_ms: int,
        capture_date: str,
        btc_price: float | None,
        binance_micro: BinanceMicroState,
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        book_fresh = (ts_ms - int(binance_micro.book_ts_ms)) <= settings.binance_micro_max_age_ms
        trade_fresh = (ts_ms - int(binance_micro.trade_ts_ms)) <= settings.binance_micro_max_age_ms
        if btc_price is None and not book_fresh and not trade_fresh:
            return
        try:
            db_queue.put_nowait(
                DBRow(
                    table="btc_ticks",
                    data={
                        "ts_ms": ts_ms,
                        "capture_date_tsi": capture_date,
                        "source": "binance_ws",
                        "price": btc_price,
                        "best_bid": binance_micro.best_bid if book_fresh else None,
                        "best_ask": binance_micro.best_ask if book_fresh else None,
                        "mid": binance_micro.mid if book_fresh else None,
                        "spread_bps": binance_micro.spread_bps if book_fresh else None,
                        "trade_count_5s": int(binance_micro.trade_count_5s) if trade_fresh else 0,
                        "buy_notional_5s": float(binance_micro.buy_notional_5s) if trade_fresh else 0.0,
                        "sell_notional_5s": float(binance_micro.sell_notional_5s) if trade_fresh else 0.0,
                        "trade_imbalance_5s": (
                            float(binance_micro.trade_imbalance_5s) if trade_fresh else 0.0
                        ),
                        "trade_count_15s": int(binance_micro.trade_count_15s) if trade_fresh else 0,
                        "buy_notional_15s": float(binance_micro.buy_notional_15s) if trade_fresh else 0.0,
                        "sell_notional_15s": float(binance_micro.sell_notional_15s) if trade_fresh else 0.0,
                        "trade_imbalance_15s": (
                            float(binance_micro.trade_imbalance_15s) if trade_fresh else 0.0
                        ),
                    },
                )
            )
        except asyncio.QueueFull:
            self._drops += 1


def _queue_collector_note(
    db_queue: asyncio.Queue[DBRow],
    *,
    ts_ms: int,
    capture_date_tsi: str,
    note_type: str,
    status: str,
    reason_code: str,
    reason_detail: str,
) -> None:
    try:
        db_queue.put_nowait(
            DBRow(
                table="collector_notes",
                data={
                    "ts_ms": ts_ms,
                    "capture_date_tsi": capture_date_tsi,
                    "note_type": note_type,
                    "status": status,
                    "reason_code": reason_code,
                    "reason_detail": reason_detail,
                },
            )
        )
    except asyncio.QueueFull:
        log.warning("DB queue full while writing collector note: %s", reason_code)


def _clear_runtime_state(
    current_event_ref: dict[str, DailyRangeEvent | None],
    active_markets: dict[str, MarketInfo],
    orderbooks: dict[str, LocalOrderBook],
    latest_btc: dict[str, float],
    latest_btc_ts: dict[str, int],
    binance_micro: BinanceMicroState,
) -> None:
    current_event_ref["event"] = None
    active_markets.clear()
    orderbooks.clear()
    latest_btc.clear()
    latest_btc_ts.clear()
    binance_micro.book_ts_ms = 0
    binance_micro.trade_ts_ms = 0
    binance_micro.best_bid = None
    binance_micro.best_ask = None
    binance_micro.mid = None
    binance_micro.spread_bps = None
    binance_micro.trade_count_5s = 0
    binance_micro.buy_notional_5s = 0.0
    binance_micro.sell_notional_5s = 0.0
    binance_micro.trade_imbalance_5s = 0.0
    binance_micro.trade_count_15s = 0
    binance_micro.buy_notional_15s = 0.0
    binance_micro.sell_notional_15s = 0.0
    binance_micro.trade_imbalance_15s = 0.0


def _start_producers(
    *,
    current_event_ref: dict[str, DailyRangeEvent | None],
    active_markets: dict[str, MarketInfo],
    orderbooks: dict[str, LocalOrderBook],
    latest_btc: dict[str, float],
    latest_btc_ts: dict[str, int],
    binance_micro: BinanceMicroState,
    db_queue: asyncio.Queue[DBRow],
    db_path: str,
    raw_dir: str,
) -> ProducerBundle:
    clob_logger = RawLogger(raw_dir, "clob_orderbook", rotation_tz=_ISTANBUL_TZ)
    binance_logger = RawLogger(raw_dir, "binance_ws", rotation_tz=_ISTANBUL_TZ)
    futures_depth_logger = RawLogger(raw_dir, "binance_usdm_depth_ws", rotation_tz=_ISTANBUL_TZ)
    deribit_logger = RawLogger(raw_dir, "deribit_public_rest", rotation_tz=_ISTANBUL_TZ)

    clob_ws = CLOBWebSocket(orderbooks, clob_logger)
    book_refresher = BookRefresher()
    binance_ws = BinanceWebSocket(
        latest_btc,
        latest_btc_ts,
        binance_logger,
        db_queue=db_queue,
        micro_state=binance_micro,
    )
    futures_depth_ws = BinanceFuturesDepthWebSocket(futures_depth_logger, db_queue)
    futures_poller = BinanceFuturesMetricsPoller(binance_logger)
    deribit_poller = DeribitIndexPoller(deribit_logger)
    ny_open_gate = NYOpenGateCollector(db_path)
    discovery = DailyRangeDiscovery(poll_interval_s=settings.market_poll_interval_s)
    snapshotter = DailyRangeSnapshotter()

    tasks = [
        asyncio.create_task(
            discovery.run(current_event_ref, active_markets, clob_ws, db_queue),
            name="daily_range_discovery",
        ),
        asyncio.create_task(clob_ws.run(), name="clob_ws"),
        asyncio.create_task(book_refresher.run(active_markets, orderbooks), name="book_refresher"),
        asyncio.create_task(binance_ws.run(), name="binance_ws"),
        asyncio.create_task(futures_depth_ws.run(), name="binance_usdm_depth_ws"),
        asyncio.create_task(futures_poller.run(db_queue), name="binance_futures_metrics"),
        asyncio.create_task(deribit_poller.run(db_queue), name="deribit_index_metrics"),
        asyncio.create_task(
            ny_open_gate.run(current_event_ref, db_queue),
            name="ny_open_gate_collector",
        ),
        asyncio.create_task(
            snapshotter.run(
                current_event_ref,
                orderbooks,
                latest_btc,
                latest_btc_ts,
                binance_micro,
                db_queue,
            ),
            name="daily_range_snapshotter",
        ),
    ]
    return ProducerBundle(
        tasks=tasks,
        clob_logger=clob_logger,
        binance_logger=binance_logger,
        futures_depth_logger=futures_depth_logger,
        deribit_logger=deribit_logger,
    )


async def _stop_producers(
    bundle: ProducerBundle | None,
    *,
    current_event_ref: dict[str, DailyRangeEvent | None],
    active_markets: dict[str, MarketInfo],
    orderbooks: dict[str, LocalOrderBook],
    latest_btc: dict[str, float],
    latest_btc_ts: dict[str, int],
    binance_micro: BinanceMicroState,
) -> None:
    if bundle is None:
        _clear_runtime_state(
            current_event_ref,
            active_markets,
            orderbooks,
            latest_btc,
            latest_btc_ts,
            binance_micro,
        )
        return

    for task in bundle.tasks:
        task.cancel()
    await asyncio.gather(*bundle.tasks, return_exceptions=True)
    bundle.clob_logger.close()
    bundle.binance_logger.close()
    bundle.futures_depth_logger.close()
    bundle.deribit_logger.close()
    _clear_runtime_state(
        current_event_ref,
        active_markets,
        orderbooks,
        latest_btc,
        latest_btc_ts,
        binance_micro,
    )


async def run_daily_range_collector(
    db_path: str = "data/db/btc_daily_range.db",
    raw_dir: str = "data/raw/btc_daily_range",
    *,
    allow_weekends: bool = False,
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    current_event_ref: dict[str, DailyRangeEvent | None] = {"event": None}
    active_markets: dict[str, MarketInfo] = {}
    orderbooks: dict[str, LocalOrderBook] = {}
    latest_btc: dict[str, float] = {}
    latest_btc_ts: dict[str, int] = {}
    binance_micro = BinanceMicroState()
    db_queue: asyncio.Queue[DBRow] = asyncio.Queue(maxsize=10_000)

    db = DailyRangeDatabase(db_path)
    await db.init()
    db_writer = DailyRangeDBWriter(db)
    producer_bundle: ProducerBundle | None = None

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        log.info("Daily range collector shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    db_writer_task = asyncio.create_task(db_writer.run(db_queue), name="db_writer")

    log.info("Daily BTC range collector started")
    last_schedule_key: tuple[str, bool, str] | None = None
    try:
        while not stop_event.is_set():
            now_ms = int(time.time() * 1000)
            schedule = _collector_schedule_status(now_ms, allow_weekends=allow_weekends)
            schedule_key = (schedule.capture_date_tsi, schedule.active, schedule.reason_code)

            if schedule_key != last_schedule_key:
                if schedule.active:
                    _queue_collector_note(
                        db_queue,
                        ts_ms=now_ms,
                        capture_date_tsi=schedule.capture_date_tsi,
                        note_type="schedule_transition",
                        status="active",
                        reason_code=schedule.reason_code,
                        reason_detail=schedule.reason_detail,
                    )
                    if producer_bundle is None:
                        producer_bundle = _start_producers(
                            current_event_ref=current_event_ref,
                            active_markets=active_markets,
                            orderbooks=orderbooks,
                            latest_btc=latest_btc,
                            latest_btc_ts=latest_btc_ts,
                            binance_micro=binance_micro,
                            db_queue=db_queue,
                            db_path=db_path,
                            raw_dir=raw_dir,
                        )
                        log.info("Daily range producer tasks started for %s", schedule.capture_date_tsi)
                else:
                    _queue_collector_note(
                        db_queue,
                        ts_ms=now_ms,
                        capture_date_tsi=schedule.capture_date_tsi,
                        note_type="schedule_transition",
                        status="paused",
                        reason_code=schedule.reason_code,
                        reason_detail=schedule.reason_detail,
                    )
                    if producer_bundle is not None:
                        await _stop_producers(
                            producer_bundle,
                            current_event_ref=current_event_ref,
                            active_markets=active_markets,
                            orderbooks=orderbooks,
                            latest_btc=latest_btc,
                            latest_btc_ts=latest_btc_ts,
                            binance_micro=binance_micro,
                        )
                        producer_bundle = None
                        log.info(
                            "Daily range producer tasks paused for %s: %s",
                            schedule.capture_date_tsi,
                            schedule.reason_code,
                        )
                    else:
                        _clear_runtime_state(
                            current_event_ref,
                            active_markets,
                            orderbooks,
                            latest_btc,
                            latest_btc_ts,
                            binance_micro,
                        )
                last_schedule_key = schedule_key

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=_SCHEDULE_POLL_INTERVAL_S)
            except asyncio.TimeoutError:
                continue
    finally:
        log.info("Daily BTC range collector shutting down")
        if producer_bundle is not None:
            await _stop_producers(
                producer_bundle,
                current_event_ref=current_event_ref,
                active_markets=active_markets,
                orderbooks=orderbooks,
                latest_btc=latest_btc,
                latest_btc_ts=latest_btc_ts,
                binance_micro=binance_micro,
            )

    db_writer_task.cancel()
    try:
        await db_writer_task
    except asyncio.CancelledError:
        pass
    finally:
        db.close()


def main() -> None:
    try:
        asyncio.run(run_daily_range_collector())
    except KeyboardInterrupt:
        pass
