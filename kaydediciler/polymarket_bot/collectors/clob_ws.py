from __future__ import annotations

import asyncio
import logging
import time

from polymarket_bot.config import settings
from polymarket_bot.features.orderbook import update_book_from_snapshot
from polymarket_bot.models import LocalOrderBook, MarketInfo, OrderBookLevel
from polymarket_bot.storage.raw_logger import RawLogger
from polymarket_bot.utils.ws_reconnect import ReconnectingWS

log = logging.getLogger(__name__)

_SUBSCRIBE_DELAY = 0.05  # seconds between individual subscribe messages


class CLOBWebSocket(ReconnectingWS):
    """CLOB orderbook WebSocket — subscribes to YES+NO tokens for active markets."""

    def __init__(
        self,
        orderbooks: dict[str, LocalOrderBook],
        raw_logger: RawLogger,
    ) -> None:
        super().__init__(
            settings.clob_ws_url,
            keepalive_s=settings.ws_keepalive_s,
            inactivity_timeout_s=settings.clob_inactivity_timeout_s,
        )
        self._orderbooks = orderbooks
        self._raw_logger = raw_logger
        self._subscribed_tokens: set[str] = set()
        # condition_id → set of token_ids for cleanup on unsubscribe
        self._market_tokens: dict[str, set[str]] = {}

    async def subscribe(self, market: MarketInfo) -> None:
        """Subscribe to both YES and NO tokens for a market."""
        tokens = []
        for token_id in (market.yes_token_id, market.no_token_id):
            if token_id not in self._orderbooks:
                self._orderbooks[token_id] = LocalOrderBook(token_id=token_id)
            self._subscribed_tokens.add(token_id)
            tokens.append(token_id)
        self._market_tokens[market.condition_id] = set(tokens)
        # One token per subscribe message (Polymarket WS requirement)
        for token_id in tokens:
            await self._send_json(
                {"type": "subscribe", "channel": "market", "assets_ids": [token_id]}
            )
        log.info(
            "Subscribed to market %s (YES=%s, NO=%s)",
            market.condition_id[:12],
            market.yes_token_id[:12],
            market.no_token_id[:12],
        )

    async def unsubscribe(self, condition_id: str) -> None:
        """Remove resolved market tokens from subscription set."""
        removed = self._market_tokens.pop(condition_id, set())
        self._subscribed_tokens -= removed
        if removed:
            log.info("Unsubscribed %s: removed %d tokens", condition_id[:12], len(removed))

    async def on_reconnect(self) -> None:
        """Resubscribe all tracked tokens one by one with small delay."""
        tokens = list(self._subscribed_tokens)
        if not tokens:
            return
        for token_id in tokens:
            await self._send_json(
                {"type": "subscribe", "channel": "market", "assets_ids": [token_id]}
            )
            await asyncio.sleep(_SUBSCRIBE_DELAY)
        log.info("Resubscribed %d tokens", len(tokens))

    async def on_keepalive(self) -> None:
        """Resubscribe ALL tokens to prevent subscription TTL expiry."""
        tokens = list(self._subscribed_tokens)
        if not tokens:
            return
        for token_id in tokens:
            await self._send_json(
                {"type": "subscribe", "channel": "market", "assets_ids": [token_id]}
            )
            await asyncio.sleep(_SUBSCRIBE_DELAY)
        log.info("Keepalive: resubscribed %d tokens", len(tokens))

    async def on_message(self, data: dict) -> None:
        self._raw_logger.log({"ts": time.time(), "src": "clob_ws", "msg": data})

        event_type = data.get("event_type") or data.get("type", "")

        if event_type == "book":
            self._handle_book_snapshot(data.get("asset_id", ""), data)
        elif event_type == "price_change":
            self._handle_price_change(data)
        elif event_type == "tick_size_change":
            self._handle_tick_size_change(data.get("asset_id", ""), data)
        elif event_type == "last_trade_price":
            pass  # logged in raw, no local state update needed

    def _handle_book_snapshot(self, asset_id: str, data: dict) -> None:
        if not asset_id:
            return
        book = self._orderbooks.get(asset_id)
        if not book:
            book = LocalOrderBook(token_id=asset_id)
            self._orderbooks[asset_id] = book

        # Current feed uses bids/asks; keep buys/sells compatibility for feed variants.
        bids = data.get("bids") or data.get("buys") or []
        asks = data.get("asks") or data.get("sells") or []
        update_book_from_snapshot(book, bids, asks)
        log.debug("Book snapshot %s: %d bids, %d asks", asset_id[:12], len(bids), len(asks))

    def _handle_price_change(self, data: dict) -> None:
        # New format: {"price_changes":[...]} ; old format had root asset_id + "changes":[...]
        changes = data.get("price_changes")
        if changes is None:
            root_asset_id = data.get("asset_id", "")
            changes = []
            for c in data.get("changes", []):
                cc = dict(c)
                cc.setdefault("asset_id", root_asset_id)
                changes.append(cc)

        for change in changes or []:
            asset_id = change.get("asset_id", "")
            book = self._orderbooks.get(asset_id)
            if not book:
                continue

            side = str(change.get("side", "")).upper()
            try:
                price = float(change.get("price", 0))
                size = float(change.get("size", 0))
            except (TypeError, ValueError):
                continue
            if side == "BUY":
                self._upsert_level(book.bids, price, size)
            elif side == "SELL":
                self._upsert_level(book.asks, price, size)

            book.last_update_ts = time.time()

    def _upsert_level(self, levels: list[OrderBookLevel], price: float, size: float) -> None:
        """Update existing level or add new one. Remove if size is 0."""
        for i, lvl in enumerate(levels):
            if abs(lvl.price - price) < 1e-9:
                if size <= 0:
                    levels.pop(i)
                else:
                    levels[i] = OrderBookLevel(price=price, size=size)
                return
        if size > 0:
            levels.append(OrderBookLevel(price=price, size=size))

    def _handle_tick_size_change(self, asset_id: str, data: dict) -> None:
        book = self._orderbooks.get(asset_id)
        if not book:
            return
        new_tick = data.get("tick_size")
        if new_tick is not None:
            book.tick_size = float(new_tick)
            log.info("Tick size changed for %s: %s", asset_id[:12], new_tick)
