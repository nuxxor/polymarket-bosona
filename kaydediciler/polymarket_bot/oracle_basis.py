"""Pure parsing and feature helpers for the Predict/Polymarket oracle-basis study.

The module deliberately contains no network, wallet, signing, order, or cancel code.
Feed numerics are decoded as lexical strings and converted to ``Decimal`` only for
derived research features.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


BTC5M_SLUG = re.compile(r"btc-updown-5m-([0-9]{10})\Z")


class OracleBasisProtocolError(ValueError):
    """A public feed violated the frozen Oracle Basis V1 contract."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OracleBasisProtocolError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_loads(raw: str) -> Any:
    """Decode JSON while retaining every source numeric as its lexical text."""

    if not isinstance(raw, str):
        raise TypeError("raw JSON must be text")
    try:
        return json.loads(
            raw,
            parse_int=str,
            parse_float=str,
            parse_constant=lambda value: (_ for _ in ()).throw(
                OracleBasisProtocolError(f"invalid JSON constant: {value}")
            ),
            object_pairs_hook=_unique_object,
        )
    except json.JSONDecodeError as exc:
        raise OracleBasisProtocolError(f"invalid JSON: {exc}") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise OracleBasisProtocolError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise OracleBasisProtocolError(f"{field} must be an array")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise OracleBasisProtocolError(f"{field} must be nonempty text")
    return value


def _decimal(value: Any, field: str, *, allow_zero: bool = True) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, str):
        raise OracleBasisProtocolError(f"{field} must be lexical numeric text")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise OracleBasisProtocolError(f"{field} must be decimal text") from exc
    if not result.is_finite() or result < 0 or (not allow_zero and result == 0):
        raise OracleBasisProtocolError(f"{field} is outside its valid range")
    return result


def _integer_text(value: Any, field: str) -> str:
    text = _text(value, field)
    if not text.isdigit():
        raise OracleBasisProtocolError(f"{field} must be unsigned integer text")
    return text


def _iso_epoch_s(value: Any, field: str) -> int:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OracleBasisProtocolError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise OracleBasisProtocolError(f"{field} must include a timezone")
    return int(parsed.timestamp())


def window_from_slug(slug: str) -> tuple[int, int]:
    match = BTC5M_SLUG.fullmatch(slug)
    if match is None:
        raise OracleBasisProtocolError("not a BTC five-minute Predict slug")
    start = int(match.group(1))
    if start % 300:
        raise OracleBasisProtocolError("Predict slug is not aligned to five minutes")
    return start, start + 300


@dataclass(frozen=True, slots=True)
class PredictMarket:
    slug: str
    market_id: str
    start_epoch_s: int
    end_epoch_s: int
    decimal_precision: int
    taker_fee_bps: str | None
    up_outcome_id: str | None
    down_outcome_id: str | None


@dataclass(frozen=True, slots=True)
class PredictResolution:
    start_price: str | None
    end_price: str | None
    outcome: str | None


def _optional_price(value: Any, field: str) -> str | None:
    if value is None:
        return None
    price = _decimal(value, field, allow_zero=False)
    return format(price, "f")


def _resolution_outcome(market: Mapping[str, Any]) -> str | None:
    resolution = market.get("resolution")
    if isinstance(resolution, Mapping):
        name = str(resolution.get("name") or "").strip().upper()
        if name in {"UP", "DOWN"}:
            return name
    won: list[str] = []
    for node in _outcome_nodes(market.get("outcomes")):
        if str(node.get("status") or "").upper() == "WON":
            name = str(node.get("name") or "").strip().upper()
            if name in {"UP", "DOWN"}:
                won.append(name)
    if len(won) > 1:
        raise OracleBasisProtocolError("multiple Predict outcomes are marked WON")
    return won[0] if won else None


def extract_predict_resolution(raw: str) -> PredictResolution:
    """Extract official Predict start/end and outcome from a category/market response."""

    document = _mapping(strict_json_loads(raw), "response")
    if document.get("success") is not True:
        raise OracleBasisProtocolError("Predict metadata request was not successful")
    data = _mapping(document.get("data"), "response.data")
    start: str | None = None
    end: str | None = None

    variant = data.get("variantData")
    if isinstance(variant, Mapping):
        start = _optional_price(variant.get("startPrice"), "variantData.startPrice")
        end = _optional_price(variant.get("endPrice"), "variantData.endPrice")
    details = data.get("variantDetails")
    if isinstance(details, Mapping) and isinstance(details.get("crypto"), Mapping):
        crypto = details["crypto"]
        start = start or _optional_price(crypto.get("startPrice"), "crypto.startPrice")
        end = end or _optional_price(crypto.get("endPrice"), "crypto.endPrice")
    market_data = data.get("marketData")
    if isinstance(market_data, list) and market_data:
        first = _mapping(market_data[0], "marketData[0]")
        start = start or _optional_price(first.get("startPrice"), "marketData.startPrice")
        end = end or _optional_price(first.get("endPrice"), "marketData.endPrice")

    markets: list[Mapping[str, Any]]
    try:
        markets = _market_objects(data.get("markets"))
    except OracleBasisProtocolError:
        markets = [data]
    outcomes = {outcome for market in markets if (outcome := _resolution_outcome(market))}
    if len(outcomes) > 1:
        raise OracleBasisProtocolError("Predict metadata contains conflicting outcomes")
    outcome = next(iter(outcomes), None)
    if outcome is None and start is not None and end is not None:
        start_value, end_value = Decimal(start), Decimal(end)
        # Equal displayed values are not a safe tie label: Predict may resolve with
        # greater oracle precision than the public display fields retain.
        outcome = "UP" if end_value > start_value else "DOWN" if end_value < start_value else None
    return PredictResolution(start_price=start, end_price=end, outcome=outcome)


def _outcome_nodes(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_mapping(item, "outcomes[]") for item in value]
    mapping = _mapping(value, "outcomes")
    edges = mapping.get("edges")
    if edges is None:
        return []
    result: list[Mapping[str, Any]] = []
    for edge in _list(edges, "outcomes.edges"):
        node = _mapping(edge, "outcomes.edges[]").get("node")
        result.append(_mapping(node, "outcomes.edges[].node"))
    return result


def _market_objects(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, list):
        return [_mapping(item, "markets[]") for item in value]
    if isinstance(value, Mapping) and isinstance(value.get("edges"), list):
        result = []
        for edge in value["edges"]:
            result.append(_mapping(_mapping(edge, "markets.edges[]").get("node"), "market"))
        return result
    raise OracleBasisProtocolError("category markets are missing")


def _market_id(value: Mapping[str, Any]) -> str:
    candidate = value.get("marketId", value.get("id"))
    return _integer_text(candidate, "market.id")


def _precision(value: Mapping[str, Any], fallback: int | None = None) -> int:
    raw = value.get("decimalPrecision")
    if raw is None:
        if fallback is None:
            raise OracleBasisProtocolError("market decimalPrecision is missing")
        return fallback
    text = _integer_text(raw, "market.decimalPrecision")
    precision = int(text)
    if not 0 <= precision <= 9:
        raise OracleBasisProtocolError("market decimalPrecision is outside [0,9]")
    return precision


def _outcome_ids(market: Mapping[str, Any]) -> tuple[str | None, str | None]:
    up_id: str | None = None
    down_id: str | None = None
    for node in _outcome_nodes(market.get("outcomes")):
        name = str(node.get("name") or "").strip().lower()
        raw_id = node.get("onChainId", node.get("id"))
        outcome_id = _text(raw_id, "outcome.id") if raw_id is not None else None
        if name == "up":
            up_id = outcome_id
        elif name == "down":
            down_id = outcome_id
    return up_id, down_id


def parse_category_response(raw: str, expected_slug: str) -> tuple[PredictMarket, ...]:
    document = _mapping(strict_json_loads(raw), "response")
    if document.get("success") is not True:
        raise OracleBasisProtocolError("Predict category request was not successful")
    data = _mapping(document.get("data"), "response.data")
    slug = _text(data.get("slug", data.get("id")), "category.slug")
    if slug != expected_slug:
        raise OracleBasisProtocolError("Predict category slug mismatch")
    slug_start, slug_end = window_from_slug(slug)
    if data.get("startsAt") is not None and _iso_epoch_s(data["startsAt"], "startsAt") != slug_start:
        raise OracleBasisProtocolError("Predict category start disagrees with slug")
    if data.get("endsAt") is not None and _iso_epoch_s(data["endsAt"], "endsAt") != slug_end:
        raise OracleBasisProtocolError("Predict category end disagrees with slug")

    result: list[PredictMarket] = []
    seen: set[str] = set()
    for market in _market_objects(data.get("markets")):
        market_id = _market_id(market)
        if market_id in seen:
            raise OracleBasisProtocolError("duplicate market ID in category")
        seen.add(market_id)
        up_id, down_id = _outcome_ids(market)
        fee = market.get("takerFeeBps", market.get("feeRateBps"))
        fee_text = None if fee is None else _integer_text(fee, "market.takerFeeBps")
        precision_raw = market.get("decimalPrecision")
        precision = 2 if precision_raw is None else _precision(market)
        result.append(
            PredictMarket(
                slug=slug,
                market_id=market_id,
                start_epoch_s=slug_start,
                end_epoch_s=slug_end,
                decimal_precision=precision,
                taker_fee_bps=fee_text,
                up_outcome_id=up_id,
                down_outcome_id=down_id,
            )
        )
    if not result:
        raise OracleBasisProtocolError("Predict category has no markets")
    return tuple(result)


def parse_market_response(raw: str, expected: PredictMarket) -> PredictMarket:
    document = _mapping(strict_json_loads(raw), "response")
    if document.get("success") is not True:
        raise OracleBasisProtocolError("Predict market request was not successful")
    market = _mapping(document.get("data"), "response.data")
    if _market_id(market) != expected.market_id:
        raise OracleBasisProtocolError("Predict market ID mismatch")
    category_slug = market.get("categorySlug")
    if category_slug is not None and _text(category_slug, "categorySlug") != expected.slug:
        raise OracleBasisProtocolError("Predict market/category mismatch")
    up_id, down_id = _outcome_ids(market)
    fee = market.get("takerFeeBps", market.get("feeRateBps"))
    return PredictMarket(
        slug=expected.slug,
        market_id=expected.market_id,
        start_epoch_s=expected.start_epoch_s,
        end_epoch_s=expected.end_epoch_s,
        decimal_precision=_precision(market, expected.decimal_precision),
        taker_fee_bps=(
            expected.taker_fee_bps
            if fee is None
            else _integer_text(fee, "market.takerFeeBps")
        ),
        up_outcome_id=up_id or expected.up_outcome_id,
        down_outcome_id=down_id or expected.down_outcome_id,
    )


@dataclass(frozen=True, slots=True)
class PredictBook:
    market_id: str
    source_epoch_ms: str
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]
    settlements_pending: Mapping[str, Any] | None

    @property
    def up_bid(self) -> str | None:
        return self.bids[0][0] if self.bids else None

    @property
    def up_ask(self) -> str | None:
        return self.asks[0][0] if self.asks else None

    def down_bid(self, precision: int) -> str | None:
        return complement(self.up_ask, precision)

    def down_ask(self, precision: int) -> str | None:
        return complement(self.up_bid, precision)


def _levels(value: Any, field: str, *, ascending: bool) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    previous: Decimal | None = None
    for index, raw_level in enumerate(_list(value, field)):
        level = _list(raw_level, f"{field}[{index}]")
        if len(level) != 2:
            raise OracleBasisProtocolError(f"{field}[{index}] must have price and quantity")
        price = _decimal(level[0], f"{field}[{index}].price")
        _decimal(level[1], f"{field}[{index}].quantity", allow_zero=False)
        if price > 1:
            raise OracleBasisProtocolError(f"{field}[{index}].price exceeds one")
        if previous is not None and ((ascending and price < previous) or (not ascending and price > previous)):
            raise OracleBasisProtocolError(f"{field} is not sorted")
        previous = price
        result.append((str(level[0]), str(level[1])))
    return tuple(result)


def _parse_book_data(data: Mapping[str, Any], expected_market_id: str | None) -> PredictBook:
    market_id = _integer_text(data.get("marketId"), "orderbook.marketId")
    if expected_market_id is not None and market_id != expected_market_id:
        raise OracleBasisProtocolError("Predict orderbook market ID mismatch")
    source_epoch_ms = _integer_text(data.get("updateTimestampMs"), "updateTimestampMs")
    pending_raw = data.get("settlementsPending")
    pending = None if pending_raw is None else _mapping(pending_raw, "settlementsPending")
    return PredictBook(
        market_id=market_id,
        source_epoch_ms=source_epoch_ms,
        bids=_levels(data.get("bids"), "bids", ascending=False),
        asks=_levels(data.get("asks"), "asks", ascending=True),
        settlements_pending=pending,
    )


def parse_orderbook_rest(raw: str, expected_market_id: str | None = None) -> PredictBook:
    document = _mapping(strict_json_loads(raw), "response")
    if document.get("success") is not True:
        raise OracleBasisProtocolError("Predict orderbook request was not successful")
    return _parse_book_data(_mapping(document.get("data"), "response.data"), expected_market_id)


def parse_orderbook_ws(raw: str, expected_market_id: str | None = None) -> PredictBook:
    document = _mapping(strict_json_loads(raw), "message")
    if document.get("type") != "M":
        raise OracleBasisProtocolError("Predict WebSocket frame is not a message")
    topic = _text(document.get("topic"), "message.topic")
    if not topic.startswith("predictOrderbook/"):
        raise OracleBasisProtocolError("Predict WebSocket topic is not an orderbook")
    topic_market_id = _integer_text(topic.split("/", 1)[1], "topic.marketId")
    if expected_market_id is not None and topic_market_id != expected_market_id:
        raise OracleBasisProtocolError("Predict WebSocket topic market ID mismatch")
    return _parse_book_data(_mapping(document.get("data"), "message.data"), topic_market_id)


def parse_ws_envelope(raw: str) -> tuple[str, str | None, Any]:
    document = _mapping(strict_json_loads(raw), "message")
    wire_type = _text(document.get("type"), "message.type")
    if wire_type == "R":
        request_id = _integer_text(document.get("requestId"), "requestId")
        if document.get("success") is not True:
            raise OracleBasisProtocolError("Predict WebSocket request was rejected")
        return "response", request_id, document
    if wire_type != "M":
        raise OracleBasisProtocolError("unsupported Predict WebSocket frame type")
    topic = _text(document.get("topic"), "message.topic")
    return ("heartbeat" if topic == "heartbeat" else "message"), topic, document


def complement(price: str | None, precision: int) -> str | None:
    if price is None:
        return None
    if not 0 <= precision <= 9:
        raise ValueError("precision must be in [0,9]")
    value = _decimal(price, "price")
    if value > 1:
        raise OracleBasisProtocolError("price exceeds one")
    quantum = Decimal(1).scaleb(-precision)
    result = (Decimal(1) - value).quantize(quantum)
    return format(result, f".{precision}f")


def basis_change(
    *,
    predict_live_point: str,
    poly_live_twap: str,
    predict_start_point: str,
    poly_start_twap: str,
) -> str:
    values = [
        _decimal(predict_live_point, "predict_live_point", allow_zero=False),
        _decimal(poly_live_twap, "poly_live_twap", allow_zero=False),
        _decimal(predict_start_point, "predict_start_point", allow_zero=False),
        _decimal(poly_start_twap, "poly_start_twap", allow_zero=False),
    ]
    result = (values[0] - values[1]) - (values[2] - values[3])
    return format(result, "f")


def predict_taker_fee(
    *,
    shares: str,
    price: str,
    fee_bps: str,
    discount_multiplier: str = "1",
) -> str:
    """Return Predict's documented raw taker fee without receipt rounding.

    ``discount_multiplier`` is explicit because account-specific fee discounts must
    never be inferred from public market metadata.
    """

    quantity = _decimal(shares, "shares", allow_zero=False)
    probability = _decimal(price, "price", allow_zero=False)
    bps = _decimal(fee_bps, "fee_bps")
    discount = _decimal(discount_multiplier, "discount_multiplier")
    if probability > 1 or bps > 10_000 or discount > 1:
        raise OracleBasisProtocolError("Predict fee input is outside its valid range")
    fee = bps / Decimal(10_000) * min(probability, Decimal(1) - probability)
    return format(fee * quantity * discount, "f")


def polymarket_crypto_taker_fee(*, shares: str, price: str) -> str:
    """Return the documented crypto taker fee before venue receipt rounding."""

    quantity = _decimal(shares, "shares", allow_zero=False)
    probability = _decimal(price, "price", allow_zero=False)
    if probability > 1:
        raise OracleBasisProtocolError("Polymarket price exceeds one")
    fee = quantity * Decimal("0.07") * probability * (Decimal(1) - probability)
    return format(fee, "f")


def four_state_label(*, predict_up: bool, poly_up: bool) -> str:
    return (
        "PREDICT_UP_POLY_UP"
        if predict_up and poly_up
        else "PREDICT_UP_POLY_DOWN"
        if predict_up
        else "PREDICT_DOWN_POLY_UP"
        if poly_up
        else "PREDICT_DOWN_POLY_DOWN"
    )
