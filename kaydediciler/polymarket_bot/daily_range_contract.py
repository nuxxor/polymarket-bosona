"""Polymarket BTC daily range market semantics.

The BTC daily range ladder settles on the Binance BTCUSDT 1-minute candle
close at 12:00 America/New_York. This module keeps that contract logic
separate from BTC movement features such as post-open expansion windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from zoneinfo import ZoneInfo


NY_TZ = ZoneInfo("America/New_York")
SETTLEMENT_TIME_ET = time(hour=12, minute=0)


class MarketFamily(str, Enum):
    DAILY_RANGE = "daily_range"
    DAILY_ABOVE = "daily_above"
    MONTHLY_TOUCH = "monthly_touch"
    UP_DOWN = "up_down"
    UNKNOWN = "unknown"


class BucketKind(str, Enum):
    LOWER_TAIL = "lower_tail"
    FINITE = "finite"
    UPPER_TAIL = "upper_tail"


@dataclass(frozen=True)
class RuleValidation:
    ok: bool
    issues: tuple[str, ...]


@dataclass(frozen=True)
class RangeBucket:
    raw_label: str
    kind: BucketKind
    lower: Decimal | None
    upper: Decimal | None

    def contains(self, close: Decimal) -> bool:
        """Return True when close resolves to this bucket."""
        if self.kind is BucketKind.LOWER_TAIL:
            if self.upper is None:
                raise ValueError("lower-tail bucket is missing upper bound")
            return close < self.upper
        if self.kind is BucketKind.UPPER_TAIL:
            if self.lower is None:
                raise ValueError("upper-tail bucket is missing lower bound")
            return close >= self.lower
        if self.lower is None or self.upper is None:
            raise ValueError("finite bucket is missing a bound")
        return self.lower <= close < self.upper


class RangeParseError(ValueError):
    pass


class LadderValidationError(ValueError):
    pass


_DASHES = str.maketrans({"–": "-", "—": "-", "−": "-"})
_AMOUNT_RE = re.compile(
    r"\$?\s*(?P<num>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(?P<suffix>[kKmM])?"
)


def settlement_datetime_utc(session_date: date) -> datetime:
    """Return the UTC open time for the settlement candle."""
    local_dt = datetime.combine(session_date, SETTLEMENT_TIME_ET, tzinfo=NY_TZ)
    return local_dt.astimezone(timezone.utc)


def classify_btc_market(title: str = "", rule_text: str = "") -> MarketFamily:
    """Classify common BTC Polymarket market families by title/rule text."""
    text = _normal_text(f"{title} {rule_text}")

    if "up or down" in text or "chainlink" in text:
        return MarketFamily.UP_DOWN
    if "what price will bitcoin hit" in text or (
        "during the month" in text and (" high " in f" {text} " or " low " in f" {text} ")
    ):
        return MarketFamily.MONTHLY_TOUCH
    if "bitcoin above" in text or "higher than the price specified" in text:
        return MarketFamily.DAILY_ABOVE
    if "bitcoin price on" in text and _looks_like_daily_range_rule(text):
        return MarketFamily.DAILY_RANGE

    return MarketFamily.UNKNOWN


def validate_daily_range_rule(title: str = "", rule_text: str = "") -> RuleValidation:
    """Validate that title/rule text matches the BTC daily range contract."""
    text = _normal_text(f"{title} {rule_text}")
    issues: list[str] = []

    if classify_btc_market(title=title, rule_text=rule_text) is not MarketFamily.DAILY_RANGE:
        issues.append("market text is not classified as a BTC daily range ladder")
    if "binance" not in text:
        issues.append("settlement source is not Binance")
    if not re.search(r"\bbtc\s*/?\s*usdt\b|\bbtcusdt\b", text):
        issues.append("settlement pair is not BTC/USDT")
    if not re.search(r"\b1\s*(?:minute|min|m)\b|1m", text):
        issues.append("settlement candle is not explicitly 1-minute")
    if "close" not in text:
        issues.append("settlement field is not close")
    if not _mentions_noon_et(text):
        issues.append("settlement time is not explicitly 12:00 ET/noon")
    if not ("higher range bracket" in text or "higher bracket" in text):
        issues.append("exact-boundary rule does not resolve to the higher bracket")
    if "chainlink" in text:
        issues.append("rule text mentions Chainlink, which is not daily-range settlement")
    if re.search(r"\bhigh price\b|\blow price\b|any .* candle", text):
        issues.append("rule text looks like a touch/high-low market, not daily range")

    return RuleValidation(ok=not issues, issues=tuple(issues))


def parse_range_label(label: str) -> RangeBucket:
    """Parse a Polymarket BTC range/tail label or child-market question."""
    normalized = _normal_label(label)

    between = re.search(r"\bbetween\b(?P<body>.+?)\bon\b", normalized)
    if between:
        normalized = between.group("body")
    elif "between" in normalized:
        normalized = normalized.split("between", 1)[1]

    amounts = _find_amounts(normalized)
    if not amounts:
        raise RangeParseError(f"could not find a numeric boundary in label: {label!r}")

    lower_tail_prefix = normalized.startswith(("<", "less than", "below", "under"))
    upper_tail_prefix = normalized.startswith((">", "greater than", "more than", "above", "over"))

    if lower_tail_prefix and len(amounts) == 1:
        return RangeBucket(
            raw_label=label,
            kind=BucketKind.LOWER_TAIL,
            lower=None,
            upper=amounts[0],
        )
    if upper_tail_prefix and len(amounts) == 1:
        return RangeBucket(
            raw_label=label,
            kind=BucketKind.UPPER_TAIL,
            lower=amounts[0],
            upper=None,
        )
    if normalized.endswith("+") and len(amounts) == 1:
        return RangeBucket(
            raw_label=label,
            kind=BucketKind.UPPER_TAIL,
            lower=amounts[0],
            upper=None,
        )

    if len(amounts) >= 2:
        lower, upper = amounts[0], amounts[1]
        if lower >= upper:
            raise RangeParseError(f"range lower bound must be below upper bound: {label!r}")
        return RangeBucket(
            raw_label=label,
            kind=BucketKind.FINITE,
            lower=lower,
            upper=upper,
        )

    raise RangeParseError(f"could not classify range label: {label!r}")


def parse_daily_range_ladder(labels: list[str] | tuple[str, ...]) -> tuple[RangeBucket, ...]:
    """Parse and validate a complete daily range ladder."""
    buckets = [parse_range_label(label) for label in labels]
    lower_tails = [bucket for bucket in buckets if bucket.kind is BucketKind.LOWER_TAIL]
    upper_tails = [bucket for bucket in buckets if bucket.kind is BucketKind.UPPER_TAIL]
    finite = sorted(
        (bucket for bucket in buckets if bucket.kind is BucketKind.FINITE),
        key=lambda bucket: bucket.lower if bucket.lower is not None else Decimal("-Infinity"),
    )

    if len(lower_tails) != 1:
        raise LadderValidationError(f"expected exactly one lower tail, found {len(lower_tails)}")
    if len(upper_tails) != 1:
        raise LadderValidationError(f"expected exactly one upper tail, found {len(upper_tails)}")
    if not finite:
        raise LadderValidationError("expected at least one finite bucket")

    lower_tail = lower_tails[0]
    upper_tail = upper_tails[0]
    if lower_tail.upper != finite[0].lower:
        raise LadderValidationError("lower tail boundary does not match first finite bucket")
    for left, right in zip(finite, finite[1:]):
        if left.upper != right.lower:
            raise LadderValidationError(
                f"gap or overlap between buckets {left.raw_label!r} and {right.raw_label!r}"
            )
    if finite[-1].upper != upper_tail.lower:
        raise LadderValidationError("last finite bucket boundary does not match upper tail")

    return tuple([lower_tail, *finite, upper_tail])


def winning_bucket(close: Decimal | float | int | str, buckets: tuple[RangeBucket, ...]) -> RangeBucket:
    """Return the single bucket that wins for a Binance settlement close."""
    close_decimal = _to_decimal(close)
    winners = [bucket for bucket in buckets if bucket.contains(close_decimal)]
    if len(winners) != 1:
        raise LadderValidationError(
            f"expected exactly one winning bucket for close {close_decimal}, found {len(winners)}"
        )
    return winners[0]


def winning_label(close: Decimal | float | int | str, labels: list[str] | tuple[str, ...]) -> str:
    """Parse labels and return the raw label that wins for close."""
    return winning_bucket(close, parse_daily_range_ladder(labels)).raw_label


def _looks_like_daily_range_rule(text: str) -> bool:
    return (
        "binance" in text
        and re.search(r"\bbtc\s*/?\s*usdt\b|\bbtcusdt\b", text) is not None
        and "close" in text
        and _mentions_noon_et(text)
    )


def _mentions_noon_et(text: str) -> bool:
    return bool(
        re.search(r"(?:12:00|12\s*pm|noon)", text)
        and re.search(r"\bet\b|eastern", text)
    )


def _normal_text(text: str) -> str:
    return " ".join(text.translate(_DASHES).lower().split())


def _normal_label(label: str) -> str:
    return _normal_text(label).replace(",", "")


def _find_amounts(text: str) -> list[Decimal]:
    return [_parse_amount(match.group("num"), match.group("suffix")) for match in _AMOUNT_RE.finditer(text)]


def _parse_amount(raw_num: str, suffix: str | None) -> Decimal:
    try:
        amount = Decimal(raw_num.replace(",", ""))
    except InvalidOperation as exc:
        raise RangeParseError(f"invalid numeric boundary: {raw_num!r}") from exc

    if suffix and suffix.lower() == "k":
        amount *= Decimal("1000")
    elif suffix and suffix.lower() == "m":
        amount *= Decimal("1000000")
    return amount


def _to_decimal(value: Decimal | float | int | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))
