from __future__ import annotations

import asyncio
import logging
import signal
import sqlite3
import sys
import time

from polymarket_bot.collectors.binance_ws import BinanceWebSocket
from polymarket_bot.collectors.book_refresher import BookRefresher
from polymarket_bot.collectors.clob_ws import CLOBWebSocket
from polymarket_bot.collectors.market_discovery import MarketDiscovery
from polymarket_bot.collectors.rtds_ws import RTDSWebSocket
from polymarket_bot.config import settings
from polymarket_bot.features.snapshotter import Snapshotter
from polymarket_bot.models import BinanceMicroState, DBRow, LocalOrderBook, MarketInfo
from polymarket_bot.storage.database import DBWriter, Database
from polymarket_bot.storage.raw_logger import RawLogger

log = logging.getLogger(__name__)


def _bootstrap_active_markets_from_db(db_path: str) -> list[MarketInfo]:
    """Recover near-term BTC micro markets from SQLite so restarts can resubscribe fast."""
    now_ms = int(time.time() * 1000)
    past_grace_ms = 60 * 60 * 1000
    future_horizon_ms = 36 * 60 * 60 * 1000
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT
                condition_id,
                question,
                yes_token_id,
                no_token_id,
                start_date_ms,
                end_date_ms,
                resolution_source,
                duration_seconds,
                active,
                resolved,
                winning_token_id,
                discovered_at_ms
            FROM markets
            WHERE active = 1
              AND resolved = 0
              AND duration_seconds IN (300, 900, 1800, 3600)
              AND question LIKE 'Bitcoin Up or Down - %'
              AND end_date_ms BETWEEN ? AND ?
            ORDER BY end_date_ms ASC
            """,
            (now_ms - past_grace_ms, now_ms + future_horizon_ms),
        ).fetchall()
    finally:
        conn.close()

    bootstrapped: list[MarketInfo] = []
    for row in rows:
        bootstrapped.append(
            MarketInfo(
                condition_id=row[0],
                question=row[1],
                yes_token_id=row[2],
                no_token_id=row[3],
                start_date_ms=int(row[4]),
                end_date_ms=int(row[5]),
                resolution_source=str(row[6] or "unknown"),
                duration_seconds=int(row[7]),
                active=bool(row[8]),
                resolved=bool(row[9]),
                winning_token_id=row[10],
                discovered_at_ms=int(row[11] or 0),
            )
        )
    return bootstrapped


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Shared state
    active_markets: dict[str, MarketInfo] = {}
    orderbooks: dict[str, LocalOrderBook] = {}
    latest_btc: dict[str, float] = {}
    latest_btc_ts: dict[str, int] = {}
    binance_micro = BinanceMicroState()
    db_queue: asyncio.Queue[DBRow] = asyncio.Queue(maxsize=10_000)

    # Storage
    db = Database(settings.db_path)
    await db.init()
    db_writer = DBWriter(db)
    try:
        bootstrapped = _bootstrap_active_markets_from_db(settings.db_path)
    except Exception:
        log.exception("Failed to bootstrap active markets from DB")
        bootstrapped = []
    for market in bootstrapped:
        active_markets[market.condition_id] = market
    if bootstrapped:
        log.info("Bootstrapped %d active markets from DB", len(bootstrapped))

    # Raw loggers
    clob_logger = RawLogger(settings.raw_dir, "clob_orderbook")
    rtds_logger = RawLogger(settings.raw_dir, "rtds_prices")
    binance_logger = RawLogger(settings.raw_dir, "binance_ws")

    # Collectors
    discovery = MarketDiscovery()
    clob_ws = CLOBWebSocket(orderbooks, clob_logger)
    refresher = BookRefresher()
    rtds_ws = RTDSWebSocket(latest_btc, latest_btc_ts, rtds_logger, db_queue)
    binance_ws = BinanceWebSocket(
        latest_btc,
        latest_btc_ts,
        binance_logger,
        db_queue,
        micro_state=binance_micro,
    )
    snapshotter = Snapshotter()

    # Track which markets are subscribed to WS
    subscribed_markets: set[str] = set()

    # Wire up: when discovery finds new market → subscribe only if near-term
    async def on_new_market(market: MarketInfo) -> None:
        now_ms = int(time.time() * 1000)
        window_ms = settings.subscribe_window_s * 1000
        if market.end_date_ms - now_ms <= window_ms:
            await clob_ws.subscribe(market)
            subscribed_markets.add(market.condition_id)

    async def on_market_resolved(condition_id: str) -> None:
        await clob_ws.unsubscribe(condition_id)
        subscribed_markets.discard(condition_id)

    async def subscription_promoter() -> None:
        """Periodically promote markets into WS subscription as they enter the time window."""
        while True:
            try:
                now_ms = int(time.time() * 1000)
                window_ms = settings.subscribe_window_s * 1000
                promoted = 0
                for market in list(active_markets.values()):
                    if not market.active:
                        continue
                    if market.condition_id in subscribed_markets:
                        continue
                    if market.end_date_ms - now_ms <= window_ms:
                        await clob_ws.subscribe(market)
                        subscribed_markets.add(market.condition_id)
                        promoted += 1
                if promoted > 0:
                    log.info("Promoted %d markets into WS subscription", promoted)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Subscription promoter error")
            await asyncio.sleep(30)

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        log.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    tasks = [
        asyncio.create_task(
            discovery.run(active_markets, db_queue, on_new=on_new_market, on_resolved=on_market_resolved),
            name="discovery",
        ),
        asyncio.create_task(clob_ws.run(), name="clob_ws"),
        asyncio.create_task(refresher.run(active_markets, orderbooks), name="book_refresher"),
        asyncio.create_task(rtds_ws.run(), name="rtds_ws"),
        asyncio.create_task(binance_ws.run(), name="binance_ws"),
        asyncio.create_task(
            snapshotter.run(
                active_markets,
                orderbooks,
                latest_btc,
                latest_btc_ts,
                binance_micro,
                db_queue,
            ),
            name="snapshotter",
        ),
        asyncio.create_task(db_writer.run(db_queue), name="db_writer"),
        asyncio.create_task(subscription_promoter(), name="promoter"),
    ]

    log.info("All collectors started. Press Ctrl+C to stop.")

    # Wait for stop signal
    await stop_event.wait()

    log.info("Shutting down gracefully...")

    # Phase 1: cancel producers first so no new data enters the queue
    producer_tasks = [t for t in tasks if t.get_name() != "db_writer"]
    db_writer_task = next(t for t in tasks if t.get_name() == "db_writer")

    for t in producer_tasks:
        t.cancel()
    producer_results = await asyncio.gather(*producer_tasks, return_exceptions=True)
    for t, r in zip(producer_tasks, producer_results):
        if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
            log.error("Task %s failed: %s", t.get_name(), r)

    # Phase 2: cancel db_writer — it will drain remaining queue items before exiting
    db_writer_task.cancel()
    try:
        await db_writer_task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log.error("db_writer failed: %s", e)

    # Cleanup
    clob_logger.close()
    rtds_logger.close()
    binance_logger.close()
    db.close()
    log.info("Shutdown complete.")


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
