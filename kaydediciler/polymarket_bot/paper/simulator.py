from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Level:
    price: float
    size: float


@dataclass
class FillResult:
    requested_shares: float
    requested_notional: float
    filled_shares: float
    filled_notional: float
    avg_price: float | None
    levels_touched: int

    @property
    def fill_ratio(self) -> float:
        if self.requested_shares > 0:
            return self.filled_shares / self.requested_shares
        if self.requested_notional > 0:
            return self.filled_notional / self.requested_notional
        return 0.0


@dataclass
class OrderBook:
    bids: list[Level]
    asks: list[Level]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> OrderBook:
        bids = [
            Level(price=float(x["price"]), size=float(x["size"]))
            for x in payload.get("bids", [])
            if float(x.get("size", 0)) > 0 and float(x.get("price", 0)) > 0
        ]
        asks = [
            Level(price=float(x["price"]), size=float(x["size"]))
            for x in payload.get("asks", [])
            if float(x.get("size", 0)) > 0 and float(x.get("price", 0)) > 0
        ]
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)
        return cls(bids=bids, asks=asks)

    @property
    def best_bid(self) -> float | None:
        if not self.bids:
            return None
        return self.bids[0].price

    @property
    def best_ask(self) -> float | None:
        if not self.asks:
            return None
        return self.asks[0].price

    @property
    def mid(self) -> float | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return (self.best_bid + self.best_ask) / 2.0

    def simulate_buy_notional(
        self,
        requested_notional: float,
        max_price: float,
    ) -> FillResult:
        if requested_notional <= 0:
            return FillResult(0.0, 0.0, 0.0, 0.0, None, 0)

        remaining = requested_notional
        filled_shares = 0.0
        filled_notional = 0.0
        levels_touched = 0

        for ask in self.asks:
            if ask.price > max_price:
                break
            if ask.price <= 0 or ask.size <= 0:
                continue
            levels_touched += 1
            max_level_notional = ask.price * ask.size
            take_notional = min(remaining, max_level_notional)
            take_shares = take_notional / ask.price
            filled_shares += take_shares
            filled_notional += take_notional
            remaining -= take_notional
            if remaining <= 1e-9:
                break

        avg_price = None
        if filled_shares > 0:
            avg_price = filled_notional / filled_shares

        return FillResult(
            requested_shares=0.0,
            requested_notional=requested_notional,
            filled_shares=filled_shares,
            filled_notional=filled_notional,
            avg_price=avg_price,
            levels_touched=levels_touched,
        )

    def simulate_buy_shares(
        self,
        requested_shares: float,
        max_price: float,
    ) -> FillResult:
        if requested_shares <= 0:
            return FillResult(0.0, 0.0, 0.0, 0.0, None, 0)

        remaining_shares = requested_shares
        filled_shares = 0.0
        filled_notional = 0.0
        levels_touched = 0

        for ask in self.asks:
            if ask.price > max_price:
                break
            if ask.price <= 0 or ask.size <= 0:
                continue
            levels_touched += 1
            take_shares = min(remaining_shares, ask.size)
            take_notional = take_shares * ask.price
            filled_shares += take_shares
            filled_notional += take_notional
            remaining_shares -= take_shares
            if remaining_shares <= 1e-9:
                break

        avg_price = None
        if filled_shares > 0:
            avg_price = filled_notional / filled_shares

        return FillResult(
            requested_shares=requested_shares,
            requested_notional=0.0,
            filled_shares=filled_shares,
            filled_notional=filled_notional,
            avg_price=avg_price,
            levels_touched=levels_touched,
        )

    def simulate_sell_shares(
        self,
        requested_shares: float,
        min_price: float,
    ) -> FillResult:
        if requested_shares <= 0:
            return FillResult(0.0, 0.0, 0.0, 0.0, None, 0)

        remaining_shares = requested_shares
        filled_shares = 0.0
        filled_notional = 0.0
        levels_touched = 0

        for bid in self.bids:
            if bid.price < min_price:
                break
            if bid.price <= 0 or bid.size <= 0:
                continue
            levels_touched += 1
            take_shares = min(remaining_shares, bid.size)
            take_notional = take_shares * bid.price
            filled_shares += take_shares
            filled_notional += take_notional
            remaining_shares -= take_shares
            if remaining_shares <= 1e-9:
                break

        avg_price = None
        if filled_shares > 0:
            avg_price = filled_notional / filled_shares

        return FillResult(
            requested_shares=requested_shares,
            requested_notional=0.0,
            filled_shares=filled_shares,
            filled_notional=filled_notional,
            avg_price=avg_price,
            levels_touched=levels_touched,
        )
