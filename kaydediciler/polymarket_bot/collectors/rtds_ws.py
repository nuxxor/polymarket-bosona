from __future__ import annotations

import asyncio
import logging
import time

from polymarket_bot.config import settings
from polymarket_bot.models import DBRow
from polymarket_bot.storage.raw_logger import RawLogger
from polymarket_bot.utils.ws_reconnect import ReconnectingWS

log = logging.getLogger(__name__)


class RTDSWebSocket(ReconnectingWS):
    """Polymarket Real-Time Data Stream for BTC prices (Binance + Chainlink feeds)."""

    def __init__(
        self,
        latest_btc: dict[str, float],
        latest_btc_ts: dict[str, int] | None,
        raw_logger: RawLogger,
        db_queue=None,
    ) -> None:
        super().__init__(
            settings.rtds_ws_url,
            keepalive_s=settings.ws_keepalive_s,
            inactivity_timeout_s=settings.rtds_inactivity_timeout_s,
        )
        self._latest_btc = latest_btc
        self._latest_btc_ts = latest_btc_ts if latest_btc_ts is not None else {}
        self._raw_logger = raw_logger
        self._db_queue = db_queue
        self._schema_version = 1
        self._drops = 0
        self._last_drop_report = 0.0
        # RTDS filters changed over time; rotate through known-valid subscription profiles
        # until we receive real price messages, then keep the working profile.
        self._profiles = [
            [
                {"topic": "crypto_prices", "type": "update", "filters": "[\"btcusdt\"]"},
                {"topic": "crypto_prices_chainlink", "type": "*", "filters": "{\"symbol\":\"btc/usd\"}"},
            ],
            [
                {"topic": "crypto_prices", "type": "update", "filters": "btcusdt"},
                {"topic": "crypto_prices_chainlink", "type": "*", "filters": ""},
            ],
            [
                {"topic": "crypto_prices", "type": "update", "filters": "{\"symbols\":[\"btcusdt\"]}"},
                {"topic": "crypto_prices_chainlink", "type": "*", "filters": "{\"symbols\":[\"btc/usd\"]}"},
            ],
            [
                {"topic": "crypto_prices", "type": "update"},
                {"topic": "crypto_prices_chainlink", "type": "*"},
            ],
        ]
        self._next_profile_idx = 0
        self._active_profile_idx = 0
        self._has_price_data = False

    async def on_reconnect(self) -> None:
        if self._has_price_data:
            idx = self._active_profile_idx
        else:
            idx = self._next_profile_idx % len(self._profiles)
            self._next_profile_idx += 1
            self._active_profile_idx = idx

        await self._send_json(
            {
                "action": "subscribe",
                "subscriptions": self._profiles[idx],
            }
        )
        log.info("RTDS: subscribed with profile=%d", idx)

    async def on_message(self, data: dict) -> None:
        # Log raw with schema version tag for discovery phase
        self._raw_logger.log({
            "ts": time.time(),
            "src": "rtds",
            "_schema_version": self._schema_version,
            "msg": data,
        })

        # Server-side subscription/schema validation errors
        status_code = data.get("statusCode")
        if status_code and int(status_code) >= 400:
            self._has_price_data = False
            log.warning(
                "RTDS server error on profile=%d: %s",
                self._active_profile_idx,
                data,
            )
            # Force fast reconnect to try next profile.
            if self._ws and not self._ws.closed:
                asyncio.create_task(self._ws.close())
            return

        # Attempt to extract BTC price — schema may vary, handle gracefully
        try:
            self._extract_price(data)
        except Exception:
            log.debug("RTDS: couldn't parse price from message: %s", str(data)[:200])

    def _extract_price(self, data: dict) -> None:
        topic = str(data.get("topic", "")).lower()
        # New RTDS format uses payload.value; keep data/flat fallbacks.
        payload = data.get("payload")
        if payload is None:
            payload = data.get("data", data)

        if not isinstance(payload, dict):
            return

        symbol = str(payload.get("symbol") or data.get("symbol") or "").strip()
        price_raw = payload.get("value")
        ts_raw = payload.get("timestamp") or data.get("timestamp")

        # Some RTDS snapshots carry a list under payload.data; use the most recent point.
        if price_raw is None:
            data_points = payload.get("data")
            if isinstance(data_points, list) and data_points:
                last = data_points[-1]
                if isinstance(last, dict):
                    price_raw = last.get("value")
                    if price_raw is None:
                        price_raw = last.get("price")
                    if last.get("timestamp") is not None:
                        ts_raw = last.get("timestamp")
        if price_raw is None:
            price_raw = payload.get("price")
        if price_raw is None:
            price_raw = data.get("value")
        if price_raw is None:
            price_raw = data.get("price")
        if price_raw is None:
            return

        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            return
        if price <= 0:
            return

        symbol_l = symbol.lower()
        if symbol and "btc" not in symbol_l:
            return

        ts_ms = int(time.time() * 1000)
        if ts_raw is not None:
            try:
                ts_val = float(ts_raw)
                ts_ms = int(ts_val * 1000) if ts_val < 1e12 else int(ts_val)
            except (TypeError, ValueError):
                pass

        if "chainlink" in topic:
            source = "rtds_chainlink"
            self._latest_btc["chainlink"] = price
            self._latest_btc_ts["chainlink"] = ts_ms
        elif "crypto_prices" in topic:
            source = "rtds_binance"
            self._latest_btc["binance"] = price
            self._latest_btc_ts["binance"] = ts_ms
        else:
            # Unknown topic — ignore without polluting btc_prices.
            return

        self._has_price_data = True

        if self._db_queue:
            try:
                self._db_queue.put_nowait(
                    DBRow(table="btc_prices", data={"ts_ms": ts_ms, "source": source, "price": price})
                )
            except asyncio.QueueFull:
                self._drops += 1
                now_mono = time.monotonic()
                if now_mono - self._last_drop_report >= 60:
                    log.warning("RTDS: %d btc_price rows dropped in last 60s", self._drops)
                    self._drops = 0
                    self._last_drop_report = now_mono
