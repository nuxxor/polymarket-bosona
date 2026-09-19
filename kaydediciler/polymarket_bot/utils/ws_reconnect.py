from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod

import aiohttp

log = logging.getLogger(__name__)

_BACKOFF_STEPS = [5, 10, 20, 40, 80, 160, 300]


class ReconnectingWS(ABC):
    """Base class for WebSocket connections with exponential backoff reconnection."""

    def __init__(
        self,
        url: str,
        *,
        keepalive_s: float = 120.0,
        inactivity_timeout_s: float | None = None,
    ) -> None:
        self._url = url
        self._keepalive_s = keepalive_s
        self._inactivity_timeout_s = inactivity_timeout_s
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None
        self._reconnect_count = 0
        self._last_close_code: int | None = None
        self._running = False
        self._connected_at = 0.0
        self._last_message_at = 0.0

    @abstractmethod
    async def on_message(self, data: dict) -> None:
        ...

    async def on_reconnect(self) -> None:
        """Override to resubscribe after reconnect."""

    async def _send_json(self, payload: dict) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.send_json(payload)

    async def run(self) -> None:
        self._running = True
        self._connected_at = 0.0
        attempt = 0
        while self._running:
            try:
                await self._connect_and_listen()
                # Reset backoff if connection survived > 60s (was healthy)
                lived = time.time() - self._connected_at if self._connected_at else 0
                if lived > 60:
                    attempt = 0
                # Normal close — still need a delay to avoid tight loop
                delay = max(2, _BACKOFF_STEPS[min(attempt, len(_BACKOFF_STEPS) - 1)])
                log.info(
                    "%s: connection closed normally (close_code=%s, lived=%.0fs), reconnecting in %ds",
                    self.__class__.__name__,
                    self._last_close_code,
                    lived,
                    delay,
                )
                attempt += 1
                self._reconnect_count += 1
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                self._running = False
                raise
            except Exception as exc:
                lived = time.time() - self._connected_at if self._connected_at else 0
                if lived > 60:
                    attempt = 0
                delay = _BACKOFF_STEPS[min(attempt, len(_BACKOFF_STEPS) - 1)]
                log.warning(
                    "%s: connection lost (attempt=%d, last_close=%s, lived=%.0fs, exc=%s), retrying in %ds",
                    self.__class__.__name__,
                    attempt,
                    self._last_close_code,
                    lived,
                    repr(exc),
                    delay,
                )
                attempt += 1
                self._reconnect_count += 1
                await asyncio.sleep(delay)

    async def _connect_and_listen(self) -> None:
        self._session = aiohttp.ClientSession()
        try:
            self._ws = await self._session.ws_connect(self._url, heartbeat=15)
            self._connected_at = time.time()
            self._last_message_at = self._connected_at
            log.info("%s: connected to %s", self.__class__.__name__, self._url)

            # Run subscribe concurrently with reading — don't block the read loop.
            # Server sends book snapshots immediately on subscribe; if we block reading
            # while sending subscribes, the receive buffer fills and server drops us.
            subscribe_task = asyncio.create_task(self._safe_on_reconnect())
            keepalive_task = asyncio.create_task(self._keepalive_loop())
            watchdog_task = (
                asyncio.create_task(self._watchdog_loop())
                if self._inactivity_timeout_s and self._inactivity_timeout_s > 0
                else None
            )
            try:
                async for msg in self._ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._last_message_at = time.time()
                        import json

                        if not msg.data or not msg.data.strip():
                            continue
                        try:
                            raw = json.loads(msg.data)
                        except json.JSONDecodeError:
                            log.debug(
                                "%s: non-JSON message: %s",
                                self.__class__.__name__,
                                msg.data[:200],
                            )
                            continue
                        # Handle batched messages (list of dicts)
                        if isinstance(raw, list):
                            for item in raw:
                                await self.on_message(item)
                        else:
                            await self.on_message(raw)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        log.error(
                            "%s: WS error: %s",
                            self.__class__.__name__,
                            self._ws.exception(),
                        )
                        break
                    elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
                        self._last_close_code = msg.data
                        log.info(
                            "%s: received close frame: code=%s extra=%s",
                            self.__class__.__name__,
                            msg.data,
                            msg.extra,
                        )
                        break
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        self._last_message_at = time.time()
            finally:
                subscribe_task.cancel()
                keepalive_task.cancel()
                if watchdog_task:
                    watchdog_task.cancel()
                wait_tasks = [subscribe_task, keepalive_task]
                if watchdog_task:
                    wait_tasks.append(watchdog_task)
                for t in wait_tasks:
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass
        finally:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            if self._session and not self._session.closed:
                await self._session.close()
            self._ws = None
            self._session = None

    async def _safe_on_reconnect(self) -> None:
        try:
            await self.on_reconnect()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("%s: on_reconnect failed", self.__class__.__name__)

    async def on_keepalive(self) -> None:
        """Override for custom keepalive. Defaults to ping frame."""
        if self._ws and not self._ws.closed:
            await self._ws.ping()

    async def _keepalive_loop(self) -> None:
        while True:
            await asyncio.sleep(self._keepalive_s)
            try:
                await self.on_keepalive()
                log.debug("%s: keepalive sent", self.__class__.__name__)
            except Exception:
                log.exception("%s: keepalive failed", self.__class__.__name__)

    async def _watchdog_loop(self) -> None:
        assert self._inactivity_timeout_s is not None
        check_every = max(2.0, min(10.0, self._inactivity_timeout_s / 3.0))
        while True:
            await asyncio.sleep(check_every)
            if not self._ws or self._ws.closed:
                return
            if self._last_message_at == 0:
                continue
            idle_s = time.time() - self._last_message_at
            if idle_s > self._inactivity_timeout_s:
                log.warning(
                    "%s: no WS messages for %.1fs (timeout=%.1fs), forcing reconnect",
                    self.__class__.__name__,
                    idle_s,
                    self._inactivity_timeout_s,
                )
                await self._ws.close()
                return

    async def stop(self) -> None:
        self._running = False
        if self._ws and not self._ws.closed:
            await self._ws.close()
