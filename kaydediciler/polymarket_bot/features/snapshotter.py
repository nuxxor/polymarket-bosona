from __future__ import annotations

import asyncio
import logging
import time

from polymarket_bot.config import settings
from polymarket_bot.features.orderbook import compute_depth_metrics
from polymarket_bot.models import BinanceMicroState, DBRow, LocalOrderBook, MarketInfo

log = logging.getLogger(__name__)


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


class Snapshotter:
    """Produces 1-second feature snapshots for all active tokens."""

    def __init__(self) -> None:
        self._drops = 0
        self._last_drop_report = 0.0
        self._micro_seen_logged = False

    async def run(
        self,
        active_markets: dict[str, MarketInfo],
        orderbooks: dict[str, LocalOrderBook],
        latest_btc: dict[str, float],
        latest_btc_ts: dict[str, int],
        binance_micro: BinanceMicroState,
        db_queue: asyncio.Queue[DBRow],
    ) -> None:
        while True:
            try:
                # Align to wall clock second
                now = time.time()
                next_tick = (int(now) + 1)
                sleep_dur = max(0, next_tick - now)
                await asyncio.sleep(sleep_dur)

                ts_ms = int(time.time() * 1000)
                btc_binance = _pick_fresh_price(
                    latest_btc,
                    latest_btc_ts,
                    ("binance_ws", "binance"),
                    ts_ms,
                    settings.btc_price_max_age_ms,
                )
                btc_chainlink = _pick_fresh_price(
                    latest_btc,
                    latest_btc_ts,
                    ("chainlink",),
                    ts_ms,
                    settings.btc_price_max_age_ms,
                )
                book_fresh = (ts_ms - int(binance_micro.book_ts_ms)) <= settings.binance_micro_max_age_ms
                trade_fresh = (ts_ms - int(binance_micro.trade_ts_ms)) <= settings.binance_micro_max_age_ms
                binance_best_bid = binance_micro.best_bid if book_fresh else None
                binance_best_ask = binance_micro.best_ask if book_fresh else None
                binance_mid = binance_micro.mid if book_fresh else None
                binance_spread_bps = binance_micro.spread_bps if book_fresh else None
                if not self._micro_seen_logged and (book_fresh or trade_fresh):
                    self._micro_seen_logged = True
                    log.info(
                        "Snapshotter observed fresh Binance micro: book_fresh=%d trade_fresh=%d bid=%s trade_count_5s=%d",
                        int(book_fresh),
                        int(trade_fresh),
                        f"{binance_best_bid:.2f}" if binance_best_bid is not None else "None",
                        int(binance_micro.trade_count_5s),
                    )

                count = 0
                for market in list(active_markets.values()):
                    if not market.active:
                        continue

                    for token_id in (market.yes_token_id, market.no_token_id):
                        book = orderbooks.get(token_id)
                        if not book:
                            continue

                        tau_ms = market.end_date_ms - ts_ms

                        # Skip expired or not-yet-started markets
                        if tau_ms < 0:
                            continue
                        max_tau = market.duration_seconds * 1000 + 60000
                        if tau_ms > max_tau:
                            continue

                        metrics = compute_depth_metrics(book, settings.vwap_target_usd)

                        row = DBRow(
                            table="snapshots",
                            data={
                                "ts_ms": ts_ms,
                                "token_id": token_id,
                                "condition_id": market.condition_id,
                                "tau_ms": tau_ms,
                                "vwap_ask_100": metrics.vwap_ask,
                                "vwap_bid_100": metrics.vwap_bid,
                                "spread_100": metrics.spread,
                                "mid_100": metrics.mid,
                                "depth_ok": 1 if metrics.depth_ok else 0,
                                "bid_depth_usd": metrics.bid_depth_usd,
                                "ask_depth_usd": metrics.ask_depth_usd,
                                "imbalance": metrics.imbalance,
                                "best_bid": metrics.best_bid,
                                "best_ask": metrics.best_ask,
                                "tick_size": book.tick_size,
                                "btc_price_binance": btc_binance,
                                "btc_price_chainlink": btc_chainlink,
                                "binance_best_bid": binance_best_bid,
                                "binance_best_ask": binance_best_ask,
                                "binance_mid": binance_mid,
                                "binance_spread_bps": binance_spread_bps,
                                "binance_trade_count_5s": (
                                    int(binance_micro.trade_count_5s) if trade_fresh else 0
                                ),
                                "binance_buy_notional_5s": (
                                    float(binance_micro.buy_notional_5s) if trade_fresh else 0.0
                                ),
                                "binance_sell_notional_5s": (
                                    float(binance_micro.sell_notional_5s) if trade_fresh else 0.0
                                ),
                                "binance_trade_imbalance_5s": (
                                    float(binance_micro.trade_imbalance_5s) if trade_fresh else 0.0
                                ),
                                "binance_trade_count_15s": (
                                    int(binance_micro.trade_count_15s) if trade_fresh else 0
                                ),
                                "binance_buy_notional_15s": (
                                    float(binance_micro.buy_notional_15s) if trade_fresh else 0.0
                                ),
                                "binance_sell_notional_15s": (
                                    float(binance_micro.sell_notional_15s) if trade_fresh else 0.0
                                ),
                                "binance_trade_imbalance_15s": (
                                    float(binance_micro.trade_imbalance_15s) if trade_fresh else 0.0
                                ),
                            },
                        )

                        try:
                            db_queue.put_nowait(row)
                            count += 1
                        except asyncio.QueueFull:
                            self._drops += 1
                            break

                if count > 0:
                    log.debug("Snapshot tick: %d rows queued", count)

                # Periodic drop report
                now_mono = time.monotonic()
                if self._drops > 0 and now_mono - self._last_drop_report >= 60:
                    log.warning(
                        "Snapshotter: %d rows dropped (queue full) in last 60s",
                        self._drops,
                    )
                    self._drops = 0
                    self._last_drop_report = now_mono

            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Snapshotter error")
                await asyncio.sleep(1)
