from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque

from polymarket_bot.config import settings
from polymarket_bot.models import DBRow
from polymarket_bot.storage.raw_logger import RawLogger
from polymarket_bot.utils.ws_reconnect import ReconnectingWS

log = logging.getLogger(__name__)
_WINDOW_5S_MS = 5_000
_WINDOW_15S_MS = 15_000


def _capture_date_tsi(ts_ms: int) -> str:
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(
        ZoneInfo("Europe/Istanbul")
    )
    return dt.strftime("%Y-%m-%d")


def _parse_depth_levels(raw_levels: object, *, reverse: bool) -> list[tuple[float, float, float]]:
    if not isinstance(raw_levels, list):
        return []
    levels: list[tuple[float, float, float]] = []
    for raw in raw_levels:
        if not isinstance(raw, list | tuple) or len(raw) < 2:
            continue
        try:
            price = float(raw[0])
            qty = float(raw[1])
        except (TypeError, ValueError):
            continue
        if price <= 0 or qty <= 0:
            continue
        levels.append((price, qty, price * qty))
    return sorted(levels, key=lambda item: item[0], reverse=reverse)


def _sum_notional(levels: list[tuple[float, float, float]], limit: int) -> float | None:
    if len(levels) < limit:
        return None
    return sum(level[2] for level in levels[:limit])


def _imbalance(bid_depth: float | None, ask_depth: float | None) -> float | None:
    if bid_depth is None or ask_depth is None:
        return None
    total = bid_depth + ask_depth
    return (bid_depth - ask_depth) / total if total > 0 else None


def _levels_json(levels: list[tuple[float, float, float]], limit: int) -> str:
    return json.dumps(
        [[price, qty, notional] for price, qty, notional in levels[:limit]],
        separators=(",", ":"),
    )


class BinanceFuturesDepthWebSocket(ReconnectingWS):
    """Binance USD-M futures partial depth stream for BTCUSDT spread/depth regime data."""

    def __init__(
        self,
        raw_logger: RawLogger,
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        super().__init__(
            settings.effective_binance_usdm_depth_ws_url,
            keepalive_s=60.0,
            inactivity_timeout_s=30.0,
        )
        self._raw_logger = raw_logger
        self._db_queue = db_queue
        self._drops = 0
        self._last_drop_report = 0.0
        self._trades_5s: deque[tuple[int, float, float]] = deque()
        self._trades_15s: deque[tuple[int, float, float]] = deque()
        self._buy_notional_5s = 0.0
        self._sell_notional_5s = 0.0
        self._buy_notional_15s = 0.0
        self._sell_notional_15s = 0.0
        self._last_micro_emit_s = 0

    async def on_reconnect(self) -> None:
        log.info("Binance USD-M futures public WS connected: %s", self._url)

    async def on_message(self, data: dict) -> None:
        stream = str(data.get("stream") or "")
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        if not isinstance(payload, dict):
            return

        self._raw_logger.log(
            {"ts": time.time(), "src": "binance_usdm_depth_ws", "stream": stream, "msg": payload}
        )
        rows = self._build_rows(stream, payload)
        if not rows:
            return
        for table_name, row in rows:
            try:
                self._db_queue.put_nowait(DBRow(table=table_name, data=row))
            except asyncio.QueueFull:
                self._drops += 1
        if self._drops:
            now_mono = time.monotonic()
            if now_mono - self._last_drop_report >= 60:
                log.warning("Binance futures public: %d rows dropped in last 60s", self._drops)
                self._drops = 0
                self._last_drop_report = now_mono

    def _build_rows(self, stream: str, payload: dict) -> list[tuple[str, dict]]:
        event_type = str(payload.get("e") or "")
        if event_type == "depthUpdate" or stream.endswith("@depth10@500ms") or (
            "b" in payload and "a" in payload and "lastUpdateId" not in payload
        ):
            row = self._build_depth_row(payload)
            return [("btc_futures_orderbook_depth", row)] if row else []
        if event_type == "markPriceUpdate":
            row = self._build_mark_price_row(payload)
            return [("btc_futures_mark_prices", row)] if row else []
        if event_type == "aggTrade":
            row = self._handle_agg_trade(payload)
            return [("btc_futures_micro_ticks", row)] if row else []
        if "k" in payload:
            row = self._build_kline_row(payload)
            return [("btc_futures_klines", row)] if row else []
        if event_type == "forceOrder":
            row = self._build_liquidation_row(payload)
            return [("btc_futures_liquidations", row)] if row else []
        return []

    def _build_depth_row(self, payload: dict) -> dict | None:
        bids = _parse_depth_levels(payload.get("b"), reverse=True)
        asks = _parse_depth_levels(payload.get("a"), reverse=False)
        if not bids or not asks:
            return None

        ts_ms = int(payload.get("E") or time.time() * 1000)
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid = (best_bid + best_ask) / 2.0
        spread_bps = ((best_ask - best_bid) / mid) * 10_000.0 if mid > 0 else None
        bid_depth_5 = _sum_notional(bids, 5)
        ask_depth_5 = _sum_notional(asks, 5)
        bid_depth_10 = _sum_notional(bids, 10)
        ask_depth_10 = _sum_notional(asks, 10)
        levels = max(5, int(settings.binance_usdm_depth_levels))

        return {
            "ts_ms": ts_ms,
            "capture_date_tsi": _capture_date_tsi(ts_ms),
            "source": "binance_usdm_depth_ws",
            "symbol": str(payload.get("s") or settings.binance_usdm_symbol).upper(),
            "levels": levels,
            "first_update_id": payload.get("U"),
            "final_update_id": payload.get("u"),
            "prev_final_update_id": payload.get("pu"),
            "transaction_ts_ms": payload.get("T"),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": mid,
            "spread_bps": spread_bps,
            "bid_depth_usd_5": bid_depth_5,
            "ask_depth_usd_5": ask_depth_5,
            "imbalance_5": _imbalance(bid_depth_5, ask_depth_5),
            "bid_depth_usd_10": bid_depth_10,
            "ask_depth_usd_10": ask_depth_10,
            "imbalance_10": _imbalance(bid_depth_10, ask_depth_10),
            "bid_levels_json": _levels_json(bids, levels),
            "ask_levels_json": _levels_json(asks, levels),
        }

    def _build_mark_price_row(self, payload: dict) -> dict | None:
        ts_ms = int(payload.get("E") or time.time() * 1000)
        symbol = str(payload.get("s") or settings.binance_usdm_symbol).upper()
        return {
            "ts_ms": ts_ms,
            "capture_date_tsi": _capture_date_tsi(ts_ms),
            "source": "binance_usdm_mark_price_ws",
            "symbol": symbol,
            "mark_price": _safe_float(payload.get("p")),
            "mark_price_ma": _safe_float(payload.get("P")),
            "index_price": _safe_float(payload.get("i")),
            "estimated_settle_price": _safe_float(payload.get("sP")),
            "funding_rate": _safe_float(payload.get("r")),
            "next_funding_time_ms": _safe_int(payload.get("T")),
        }

    def _refresh_trade_windows(self, now_ms: int) -> tuple[int, float, float, float, int, float, float, float]:
        while self._trades_5s and now_ms - self._trades_5s[0][0] > _WINDOW_5S_MS:
            _ts_ms, buy_notional, sell_notional = self._trades_5s.popleft()
            self._buy_notional_5s -= buy_notional
            self._sell_notional_5s -= sell_notional
        while self._trades_15s and now_ms - self._trades_15s[0][0] > _WINDOW_15S_MS:
            _ts_ms, buy_notional, sell_notional = self._trades_15s.popleft()
            self._buy_notional_15s -= buy_notional
            self._sell_notional_15s -= sell_notional
        total_5s = self._buy_notional_5s + self._sell_notional_5s
        total_15s = self._buy_notional_15s + self._sell_notional_15s
        return (
            len(self._trades_5s),
            max(0.0, self._buy_notional_5s),
            max(0.0, self._sell_notional_5s),
            (self._buy_notional_5s - self._sell_notional_5s) / total_5s if total_5s > 0 else 0.0,
            len(self._trades_15s),
            max(0.0, self._buy_notional_15s),
            max(0.0, self._sell_notional_15s),
            (
                (self._buy_notional_15s - self._sell_notional_15s) / total_15s
                if total_15s > 0
                else 0.0
            ),
        )

    def _handle_agg_trade(self, payload: dict) -> dict | None:
        price = _safe_float(payload.get("p"))
        qty = _safe_float(payload.get("q"))
        if price is None or qty is None or price <= 0 or qty <= 0:
            return None
        event_ts_ms = int(payload.get("E") or payload.get("T") or time.time() * 1000)
        notional = price * qty
        # Binance aggTrade `m=true` => buyer is maker => seller was aggressive.
        sell_notional = notional if bool(payload.get("m", False)) else 0.0
        buy_notional = notional if sell_notional == 0.0 else 0.0
        self._trades_5s.append((event_ts_ms, buy_notional, sell_notional))
        self._trades_15s.append((event_ts_ms, buy_notional, sell_notional))
        self._buy_notional_5s += buy_notional
        self._sell_notional_5s += sell_notional
        self._buy_notional_15s += buy_notional
        self._sell_notional_15s += sell_notional
        (
            trade_count_5s,
            buy_notional_5s,
            sell_notional_5s,
            trade_imbalance_5s,
            trade_count_15s,
            buy_notional_15s,
            sell_notional_15s,
            trade_imbalance_15s,
        ) = self._refresh_trade_windows(event_ts_ms)
        emit_s = event_ts_ms // 1000
        if emit_s == self._last_micro_emit_s:
            return None
        self._last_micro_emit_s = emit_s
        return {
            "ts_ms": event_ts_ms,
            "capture_date_tsi": _capture_date_tsi(event_ts_ms),
            "source": "binance_usdm_aggtrade_ws",
            "symbol": str(payload.get("s") or settings.binance_usdm_symbol).upper(),
            "price": price,
            "trade_ts_ms": _safe_int(payload.get("T")),
            "trade_count_5s": trade_count_5s,
            "buy_notional_5s": buy_notional_5s,
            "sell_notional_5s": sell_notional_5s,
            "trade_imbalance_5s": trade_imbalance_5s,
            "trade_count_15s": trade_count_15s,
            "buy_notional_15s": buy_notional_15s,
            "sell_notional_15s": sell_notional_15s,
            "trade_imbalance_15s": trade_imbalance_15s,
        }

    def _build_kline_row(self, payload: dict) -> dict | None:
        kline = payload.get("k")
        if not isinstance(kline, dict) or not bool(kline.get("x", False)):
            return None
        close_price = _safe_float(kline.get("c"))
        open_price = _safe_float(kline.get("o"))
        high_price = _safe_float(kline.get("h"))
        low_price = _safe_float(kline.get("l"))
        if not all(value is not None and value > 0 for value in (open_price, high_price, low_price, close_price)):
            return None
        return {
            "ts_ms": int(kline.get("T") or payload.get("E") or time.time() * 1000),
            "source": "binance_usdm_kline_ws",
            "symbol": str(payload.get("s") or kline.get("s") or settings.binance_usdm_symbol).upper(),
            "interval": str(kline.get("i") or settings.binance_usdm_kline_interval).lower(),
            "open_time_ms": int(kline.get("t") or 0),
            "close_time_ms": int(kline.get("T") or 0),
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "close_price": close_price,
            "volume_base": float(kline.get("v") or 0.0),
            "volume_quote": float(kline.get("q") or 0.0),
            "trade_count": int(kline.get("n") or 0),
            "taker_buy_base": float(kline.get("V") or 0.0),
            "taker_buy_quote": float(kline.get("Q") or 0.0),
        }

    def _build_liquidation_row(self, payload: dict) -> dict | None:
        order = payload.get("o")
        if not isinstance(order, dict):
            return None
        ts_ms = int(payload.get("E") or order.get("T") or time.time() * 1000)
        avg_price = _safe_float(order.get("ap")) or _safe_float(order.get("p"))
        filled_qty = _safe_float(order.get("z"))
        return {
            "ts_ms": ts_ms,
            "capture_date_tsi": _capture_date_tsi(ts_ms),
            "source": "binance_usdm_force_order_ws",
            "symbol": str(order.get("s") or settings.binance_usdm_symbol).upper(),
            "side": order.get("S"),
            "order_type": order.get("o"),
            "time_in_force": order.get("f"),
            "original_qty": _safe_float(order.get("q")),
            "price": _safe_float(order.get("p")),
            "average_price": avg_price,
            "status": order.get("X"),
            "last_filled_qty": _safe_float(order.get("l")),
            "filled_qty": filled_qty,
            "trade_ts_ms": _safe_int(order.get("T")),
            "notional_usd": avg_price * filled_qty if avg_price is not None and filled_qty is not None else None,
        }


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
