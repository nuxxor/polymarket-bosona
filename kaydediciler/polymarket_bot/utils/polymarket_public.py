from __future__ import annotations

import json
import re
from typing import Any, Literal

import requests


BtcUpDownFamily = Literal["daily", "hourly", "range", "unknown"]
BtcUpDownScope = Literal["daily", "hourly", "range", "all"]

_WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
_BTC_UPDOWN_DAILY_RE = re.compile(
    r"^Bitcoin Up or Down on [A-Za-z]+ \d{1,2}(?:,\s*\d{4})?\?$",
    re.IGNORECASE,
)
_BTC_UPDOWN_RANGE_RE = re.compile(
    r"^Bitcoin Up or Down - .+?, "
    r"\d{1,2}(?::\d{2})?[AP]M-\d{1,2}(?::\d{2})?[AP]M ET$",
    re.IGNORECASE,
)
_BTC_UPDOWN_HOURLY_RE = re.compile(
    r"^Bitcoin Up or Down - .+?, \d{1,2}(?::00)?[AP]M ET$",
    re.IGNORECASE,
)


def is_wallet_address(value: str | None) -> bool:
    if not value:
        return False
    return bool(_WALLET_RE.fullmatch(str(value).strip()))


def parse_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
        return parsed if isinstance(parsed, list) else [parsed]
    return [value]


def classify_btc_updown_title(title: str) -> BtcUpDownFamily:
    title = str(title or "").strip()
    if _BTC_UPDOWN_DAILY_RE.fullmatch(title):
        return "daily"
    if _BTC_UPDOWN_RANGE_RE.fullmatch(title):
        return "range"
    if _BTC_UPDOWN_HOURLY_RE.fullmatch(title):
        return "hourly"
    return "unknown"


def matches_btc_updown_family(title: str, scope: BtcUpDownScope) -> bool:
    family = classify_btc_updown_title(title)
    if scope == "all":
        return family in {"daily", "hourly", "range"}
    return family == scope


def session_label_from_btc_updown_title(title: str) -> str:
    title = str(title or "").strip()
    family = classify_btc_updown_title(title)
    if family == "daily":
        return title.removeprefix("Bitcoin Up or Down on ").removesuffix("?")
    if family in {"hourly", "range"}:
        return title.removeprefix("Bitcoin Up or Down - ").strip()
    return title


def _keyset_params(params: dict[str, Any] | None, cursor: str | None) -> dict[str, Any]:
    query = {key: value for key, value in (params or {}).items() if value is not None}
    if cursor:
        query["after_cursor"] = cursor
    return query


def fetch_gamma_keyset_rows_sync(
    session: requests.Session,
    url: str,
    collection_key: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        response = session.get(url, params=_keyset_params(params, cursor), timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            break
        batch = payload.get(collection_key, [])
        if not isinstance(batch, list) or not batch:
            break
        rows.extend(item for item in batch if isinstance(item, dict))
        cursor = payload.get("next_cursor")
        if not cursor:
            break
    return rows


async def fetch_gamma_keyset_rows_async(
    session: Any,
    url: str,
    collection_key: str,
    *,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        async with session.get(url, params=_keyset_params(params, cursor)) as resp:
            resp.raise_for_status()
            payload = await resp.json()
        if not isinstance(payload, dict):
            break
        batch = payload.get(collection_key, [])
        if not isinstance(batch, list) or not batch:
            break
        rows.extend(item for item in batch if isinstance(item, dict))
        cursor = payload.get("next_cursor")
        if not cursor:
            break
    return rows
