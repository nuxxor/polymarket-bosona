from __future__ import annotations

import asyncio
import logging
import time

import aiohttp

from polymarket_bot.config import settings
from polymarket_bot.features.orderbook import update_book_from_snapshot
from polymarket_bot.models import LocalOrderBook, MarketInfo

log = logging.getLogger(__name__)


class BookRefresher:
    """Periodically fetches full L2 orderbook via REST to correct drift from WS price_change."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def run(
        self,
        active_markets: dict[str, MarketInfo],
        orderbooks: dict[str, LocalOrderBook],
    ) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
        )
        try:
            while True:
                try:
                    await self._refresh_cycle(active_markets, orderbooks)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("Book refresh cycle error")
                    await asyncio.sleep(5)
        finally:
            if self._session and not self._session.closed:
                await self._session.close()

    async def _refresh_cycle(
        self,
        active_markets: dict[str, MarketInfo],
        orderbooks: dict[str, LocalOrderBook],
    ) -> None:
        """Round-robin through active tokens, refreshing each within rate limits."""
        while True:
            tokens_to_refresh: list[str] = []
            for market in list(active_markets.values()):
                if not market.active:
                    continue
                for tid in (market.yes_token_id, market.no_token_id):
                    book = orderbooks.get(tid)
                    if book and book.needs_refresh(settings.book_refresh_interval_s):
                        tokens_to_refresh.append(tid)

            if not tokens_to_refresh:
                await asyncio.sleep(2)
                continue

            for token_id in tokens_to_refresh:
                try:
                    await self._fetch_book(token_id, orderbooks)
                except Exception as e:
                    log.warning("Failed to refresh book for %s: %s", token_id[:12], e)

                # Rate limiting: ~50 req/10s max for Polymarket CLOB
                # Spread requests evenly
                interval = max(0.2, settings.book_refresh_interval_s / max(len(tokens_to_refresh), 1))
                await asyncio.sleep(interval)

    async def _fetch_book(
        self,
        token_id: str,
        orderbooks: dict[str, LocalOrderBook],
    ) -> None:
        assert self._session is not None
        url = f"{settings.clob_api_url}/book?token_id={token_id}"
        async with self._session.get(url) as resp:
            if resp.status == 429:
                log.warning("CLOB rate limited on /book, backing off 10s")
                await asyncio.sleep(10)
                return
            resp.raise_for_status()
            data = await resp.json()

        book = orderbooks.get(token_id)
        if not book:
            book = LocalOrderBook(token_id=token_id)
            orderbooks[token_id] = book

        bids = data.get("bids", [])
        asks = data.get("asks", [])
        update_book_from_snapshot(book, bids, asks)
        log.debug("REST refresh %s: %d bids, %d asks", token_id[:12], len(bids), len(asks))
