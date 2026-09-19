from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MarketInfo(BaseModel):
    condition_id: str
    question: str
    yes_token_id: str
    no_token_id: str
    start_date_ms: int
    end_date_ms: int
    resolution_source: Literal["chainlink", "binance", "unknown"] = "unknown"
    duration_seconds: int
    active: bool = True
    resolved: bool = False
    winning_token_id: str | None = None
    discovered_at_ms: int = 0


class OrderBookLevel(BaseModel):
    price: float
    size: float


class LocalOrderBook(BaseModel):
    token_id: str
    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)
    last_update_ts: float = 0.0
    last_full_refresh_ts: float = 0.0
    tick_size: float = 0.01

    def needs_refresh(self, max_age_s: float = 15.0) -> bool:
        import time

        if self.last_full_refresh_ts == 0.0:
            return True
        return (time.time() - self.last_full_refresh_ts) > max_age_s


class BinanceMicroState(BaseModel):
    book_ts_ms: int = 0
    trade_ts_ms: int = 0
    best_bid: float | None = None
    best_ask: float | None = None
    mid: float | None = None
    spread_bps: float | None = None
    trade_count_5s: int = 0
    buy_notional_5s: float = 0.0
    sell_notional_5s: float = 0.0
    trade_imbalance_5s: float = 0.0
    trade_count_15s: int = 0
    buy_notional_15s: float = 0.0
    sell_notional_15s: float = 0.0
    trade_imbalance_15s: float = 0.0


class FeatureSnapshot(BaseModel):
    token_id: str
    condition_id: str
    ts_ms: int
    tau_ms: int
    vwap_ask_100: float | None = None
    vwap_bid_100: float | None = None
    spread_100: float | None = None
    mid_100: float | None = None
    depth_ok: bool = False
    bid_depth_usd: float = 0.0
    ask_depth_usd: float = 0.0
    imbalance: float = 0.0
    best_bid: float | None = None
    best_ask: float | None = None
    tick_size: float = 0.01
    btc_price_binance: float | None = None
    btc_price_chainlink: float | None = None
    binance_best_bid: float | None = None
    binance_best_ask: float | None = None
    binance_mid: float | None = None
    binance_spread_bps: float | None = None
    binance_trade_count_5s: int = 0
    binance_buy_notional_5s: float = 0.0
    binance_sell_notional_5s: float = 0.0
    binance_trade_imbalance_5s: float = 0.0
    binance_trade_count_15s: int = 0
    binance_buy_notional_15s: float = 0.0
    binance_sell_notional_15s: float = 0.0
    binance_trade_imbalance_15s: float = 0.0


class BTCPrice(BaseModel):
    ts_ms: int
    price: float
    source: Literal["rtds_binance", "rtds_chainlink", "binance_ws"]


class DBRow(BaseModel):
    """Wrapper for queuing DB inserts."""

    table: str
    data: dict
