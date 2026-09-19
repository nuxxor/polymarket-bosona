from __future__ import annotations

import logging
from dataclasses import dataclass

from polymarket_bot.models import LocalOrderBook, OrderBookLevel

log = logging.getLogger(__name__)


@dataclass
class DepthMetrics:
    vwap_ask: float | None
    vwap_bid: float | None
    spread: float | None
    mid: float | None
    depth_ok: bool
    bid_depth_usd: float
    ask_depth_usd: float
    imbalance: float
    best_bid: float | None
    best_ask: float | None


def compute_vwap(levels: list[OrderBookLevel], target_usd: float, side: str) -> float | None:
    """Walk price levels accumulating notional to compute VWAP at target_usd depth.

    For asks: sort ascending (cheapest first).
    For bids: sort descending (most expensive first).
    """
    if not levels:
        return None

    if side == "ask":
        sorted_levels = sorted(levels, key=lambda x: x.price)
    else:
        sorted_levels = sorted(levels, key=lambda x: x.price, reverse=True)

    remaining = target_usd
    total_shares = 0.0
    total_cost = 0.0

    for level in sorted_levels:
        if level.price <= 0:
            continue
        max_shares = level.size
        max_cost = level.price * max_shares

        if max_cost <= remaining:
            fill_cost = max_cost
            fill_shares = max_shares
        else:
            fill_shares = remaining / level.price
            fill_cost = remaining

        total_cost += fill_cost
        total_shares += fill_shares
        remaining -= fill_cost

        if remaining <= 0:
            break

    # Couldn't fill 99%+
    if remaining > target_usd * 0.01:
        return None

    if total_shares == 0:
        return None

    return total_cost / total_shares


def compute_total_depth(levels: list[OrderBookLevel]) -> float:
    """Sum total USD notional available across all levels."""
    return sum(lvl.price * lvl.size for lvl in levels if lvl.price > 0)


def compute_depth_metrics(book: LocalOrderBook, target_usd: float) -> DepthMetrics:
    """Compute full depth metrics for an orderbook."""
    vwap_ask = compute_vwap(book.asks, target_usd, "ask")
    vwap_bid = compute_vwap(book.bids, target_usd, "bid")

    bid_depth = compute_total_depth(book.bids)
    ask_depth = compute_total_depth(book.asks)

    best_bid = max((l.price for l in book.bids), default=None) if book.bids else None
    best_ask = min((l.price for l in book.asks), default=None) if book.asks else None

    depth_ok = vwap_ask is not None and vwap_bid is not None

    spread = None
    mid = None
    if vwap_ask is not None and vwap_bid is not None:
        spread = vwap_ask - vwap_bid
        mid = (vwap_ask + vwap_bid) / 2.0

    total_depth = bid_depth + ask_depth
    imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0.0

    return DepthMetrics(
        vwap_ask=vwap_ask,
        vwap_bid=vwap_bid,
        spread=spread,
        mid=mid,
        depth_ok=depth_ok,
        bid_depth_usd=bid_depth,
        ask_depth_usd=ask_depth,
        imbalance=imbalance,
        best_bid=best_bid,
        best_ask=best_ask,
    )


def update_book_from_snapshot(
    book: LocalOrderBook,
    bids: list[dict],
    asks: list[dict],
) -> None:
    """Replace full orderbook from REST or WS snapshot."""
    import time

    book.bids = [
        OrderBookLevel(price=float(b["price"]), size=float(b["size"]))
        for b in bids
        if float(b.get("size", 0)) > 0
    ]
    book.asks = [
        OrderBookLevel(price=float(a["price"]), size=float(a["size"]))
        for a in asks
        if float(a.get("size", 0)) > 0
    ]
    now = time.time()
    book.last_update_ts = now
    book.last_full_refresh_ts = now
