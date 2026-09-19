from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from polymarket_bot.config import settings
from polymarket_bot.models import BinanceMicroState, DBRow
from polymarket_bot.storage.raw_logger import RawLogger
from polymarket_bot.utils.ws_reconnect import ReconnectingWS

log = logging.getLogger(__name__)

# Binance WS has 24h connection limit — proactively reconnect at 23h
_BINANCE_RECONNECT_S = 23 * 3600
_WINDOW_5S_MS = 5_000
_WINDOW_15S_MS = 15_000
_ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")


def _capture_date_tsi(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(_ISTANBUL_TZ)
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


class BinanceWebSocket(ReconnectingWS):
    """Combined Binance WS for BTCUSDT kline, aggTrade, and bookTicker."""

    def __init__(
        self,
        latest_btc: dict[str, float],
        latest_btc_ts: dict[str, int] | None,
        raw_logger: RawLogger,
        db_queue=None,
        micro_state: BinanceMicroState | None = None,
    ) -> None:
        super().__init__(settings.effective_binance_ws_url, keepalive_s=60.0)
        self._latest_btc = latest_btc
        self._latest_btc_ts = latest_btc_ts if latest_btc_ts is not None else {}
        self._raw_logger = raw_logger
        self._db_queue = db_queue
        self._micro_state = micro_state if micro_state is not None else BinanceMicroState()
        self._connect_time = 0.0
        self._drops = 0
        self._last_drop_report = 0.0
        self._trades_5s: deque[tuple[int, float, float]] = deque()
        self._trades_15s: deque[tuple[int, float, float]] = deque()
        self._buy_notional_5s = 0.0
        self._sell_notional_5s = 0.0
        self._buy_notional_15s = 0.0
        self._sell_notional_15s = 0.0

    async def on_reconnect(self) -> None:
        self._connect_time = time.monotonic()
        log.info("Binance WS connected: %s", settings.effective_binance_ws_url)

    def _refresh_trade_windows(self, now_ms: int) -> None:
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
        self._micro_state.trade_count_5s = len(self._trades_5s)
        self._micro_state.buy_notional_5s = max(0.0, self._buy_notional_5s)
        self._micro_state.sell_notional_5s = max(0.0, self._sell_notional_5s)
        self._micro_state.trade_imbalance_5s = (
            (self._buy_notional_5s - self._sell_notional_5s) / total_5s if total_5s > 0 else 0.0
        )
        self._micro_state.trade_count_15s = len(self._trades_15s)
        self._micro_state.buy_notional_15s = max(0.0, self._buy_notional_15s)
        self._micro_state.sell_notional_15s = max(0.0, self._sell_notional_15s)
        self._micro_state.trade_imbalance_15s = (
            (self._buy_notional_15s - self._sell_notional_15s) / total_15s if total_15s > 0 else 0.0
        )

    def _update_latest_price(self, source_key: str, price: float, ts_ms: int) -> None:
        if price <= 0:
            return
        self._latest_btc[source_key] = price
        self._latest_btc_ts[source_key] = ts_ms

    def _handle_book_ticker(self, payload: dict) -> None:
        first_book = self._micro_state.book_ts_ms == 0
        bid = float(payload.get("b") or 0.0)
        ask = float(payload.get("a") or 0.0)
        if bid <= 0 or ask <= 0:
            return
        event_ts_ms = int(payload.get("E") or (time.time() * 1000))
        mid = (bid + ask) / 2.0
        spread_bps = ((ask - bid) / mid) * 10_000.0 if mid > 0 else None
        self._micro_state.book_ts_ms = event_ts_ms
        self._micro_state.best_bid = bid
        self._micro_state.best_ask = ask
        self._micro_state.mid = mid
        self._micro_state.spread_bps = spread_bps
        self._update_latest_price("binance_ws", mid, event_ts_ms)
        self._refresh_trade_windows(event_ts_ms)
        if first_book:
            log.info(
                "Binance micro book initialized: bid=%.2f ask=%.2f spread_bps=%.4f",
                bid,
                ask,
                spread_bps or 0.0,
            )

    def _handle_partial_depth(self, payload: dict) -> None:
        bids = _parse_depth_levels(payload.get("bids") or payload.get("b"), reverse=True)
        asks = _parse_depth_levels(payload.get("asks") or payload.get("a"), reverse=False)
        if not bids or not asks or not self._db_queue:
            return
        ts_ms = int(payload.get("E") or time.time() * 1000)
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid = (best_bid + best_ask) / 2.0
        spread_bps = ((best_ask - best_bid) / mid) * 10_000.0 if mid > 0 else None
        bid_depth_5 = _sum_notional(bids, 5)
        ask_depth_5 = _sum_notional(asks, 5)
        bid_depth_10 = _sum_notional(bids, 10)
        ask_depth_10 = _sum_notional(asks, 10)
        levels = max(5, int(settings.binance_spot_depth_levels))
        try:
            self._db_queue.put_nowait(
                DBRow(
                    table="btc_spot_orderbook_depth",
                    data={
                        "ts_ms": ts_ms,
                        "capture_date_tsi": _capture_date_tsi(ts_ms),
                        "source": "binance_spot_depth_ws",
                        "symbol": settings.binance_symbol.strip().upper(),
                        "levels": levels,
                        "last_update_id": payload.get("lastUpdateId"),
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
                    },
                )
            )
        except asyncio.QueueFull:
            self._drops += 1

    def _handle_agg_trade(self, payload: dict) -> None:
        first_trade = self._micro_state.trade_ts_ms == 0
        price = float(payload.get("p") or 0.0)
        qty = float(payload.get("q") or 0.0)
        if price <= 0 or qty <= 0:
            return
        event_ts_ms = int(payload.get("E") or payload.get("T") or (time.time() * 1000))
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
        self._micro_state.trade_ts_ms = event_ts_ms
        self._update_latest_price("binance_ws", price, event_ts_ms)
        self._refresh_trade_windows(event_ts_ms)
        if first_trade:
            log.info(
                "Binance micro trade initialized: price=%.2f notional=%.4f trade_count_5s=%d",
                price,
                notional,
                int(self._micro_state.trade_count_5s),
            )

    def _handle_kline(self, payload: dict) -> None:
        kline = payload.get("k")
        if not kline:
            return
        open_price = float(kline.get("o", 0) or 0.0)
        high_price = float(kline.get("h", 0) or 0.0)
        low_price = float(kline.get("l", 0) or 0.0)
        close_price = float(kline.get("c", 0) or 0.0)
        volume_base = float(kline.get("v", 0) or 0.0)
        volume_quote = float(kline.get("q", 0) or 0.0)
        taker_buy_base = float(kline.get("V", 0) or 0.0)
        taker_buy_quote = float(kline.get("Q", 0) or 0.0)
        trade_count = int(kline.get("n", 0) or 0)
        if close_price <= 0 or open_price <= 0 or high_price <= 0 or low_price <= 0:
            return

        event_ts_ms = int(payload.get("E") or (time.time() * 1000))
        self._update_latest_price("binance_ws", close_price, event_ts_ms)
        self._refresh_trade_windows(event_ts_ms)

        is_final = kline.get("x", False)
        if is_final and self._db_queue:
            ts_ms = int(kline.get("T", time.time() * 1000))
            try:
                self._db_queue.put_nowait(
                    DBRow(
                        table="btc_prices",
                        data={"ts_ms": ts_ms, "source": "binance_ws", "price": close_price},
                    )
                )
                self._db_queue.put_nowait(
                    DBRow(
                        table="btc_spot_klines",
                        data={
                            "ts_ms": ts_ms,
                            "source": "binance_ws",
                            "symbol": settings.binance_symbol.strip().upper(),
                            "interval": settings.binance_kline_interval.strip().lower(),
                            "open_price": open_price,
                            "high_price": high_price,
                            "low_price": low_price,
                            "close_price": close_price,
                            "volume_base": volume_base,
                            "volume_quote": volume_quote,
                            "trade_count": trade_count,
                            "taker_buy_base": taker_buy_base,
                            "taker_buy_quote": taker_buy_quote,
                        },
                    )
                )
            except asyncio.QueueFull:
                self._drops += 1
                now_mono = time.monotonic()
                if now_mono - self._last_drop_report >= 60:
                    log.warning("Binance: %d btc_price/kline rows dropped in last 60s", self._drops)
                    self._drops = 0
                    self._last_drop_report = now_mono

    async def on_message(self, data: dict) -> None:
        stream = str(data.get("stream") or "")
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        self._raw_logger.log({"ts": time.time(), "src": "binance_ws", "stream": stream, "msg": payload})

        event_type = str(payload.get("e") or "")
        if "k" in payload:
            self._handle_kline(payload)
            return
        if "lastUpdateId" in payload and ("bids" in payload or "b" in payload):
            self._handle_partial_depth(payload)
            return
        if stream.endswith("@bookTicker") or {"u", "b", "B", "a", "A"}.issubset(payload.keys()):
            self._handle_book_ticker(payload)
            return
        if event_type == "bookTicker":
            self._handle_book_ticker(payload)
            return
        if event_type == "aggTrade":
            self._handle_agg_trade(payload)
            return

    async def run(self) -> None:
        """Override to add proactive 23h reconnect."""
        self._running = True
        while self._running:
            try:
                reconnect_task = asyncio.create_task(self._proactive_reconnect_timer())
                try:
                    await self._connect_and_listen()
                finally:
                    reconnect_task.cancel()
                    try:
                        await reconnect_task
                    except asyncio.CancelledError:
                        pass
                log.info("Binance WS: normal close, reconnecting in 2s")
                self._reconnect_count += 1
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                self._running = False
                raise
            except Exception:
                log.warning("Binance WS disconnected, reconnecting in 5s")
                self._reconnect_count += 1
                await asyncio.sleep(5)

    async def _proactive_reconnect_timer(self) -> None:
        """Close connection proactively before Binance's 24h limit."""
        await asyncio.sleep(_BINANCE_RECONNECT_S)
        log.info("Binance WS: proactive 23h reconnect")
        if self._ws and not self._ws.closed:
            await self._ws.close()
