from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone, tzinfo
from typing import Callable

log = logging.getLogger(__name__)


class RawLogger:
    """Append-only JSONL event logger with daily rotation."""

    def __init__(
        self,
        base_dir: str,
        stream_name: str,
        *,
        rotation_tz: tzinfo = timezone.utc,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._base_dir = base_dir
        self._stream_name = stream_name
        self._rotation_tz = rotation_tz
        self._now_fn = now_fn or (lambda: datetime.now(self._rotation_tz))
        self._current_date: str = ""
        self._fp = None
        self._buffer: list[str] = []
        self._last_flush = time.monotonic()
        self._flush_count = 50
        self._flush_interval_s = 1.0

    def _rotate_if_needed(self) -> None:
        today = self._now_fn().astimezone(self._rotation_tz).strftime("%Y-%m-%d")
        if today != self._current_date:
            self._close()
            self._current_date = today
            dir_path = os.path.join(self._base_dir, today)
            os.makedirs(dir_path, exist_ok=True)
            path = os.path.join(dir_path, f"{self._stream_name}.jsonl")
            self._fp = open(path, "a", encoding="utf-8")
            log.info("RawLogger rotated to %s", path)

    def log(self, event: dict) -> None:
        self._rotate_if_needed()
        line = json.dumps(event, ensure_ascii=False, default=str) + "\n"
        self._buffer.append(line)

        now = time.monotonic()
        if (
            len(self._buffer) >= self._flush_count
            or (now - self._last_flush) >= self._flush_interval_s
        ):
            self.flush()

    def flush(self) -> None:
        if not self._buffer or not self._fp:
            return
        try:
            self._fp.writelines(self._buffer)
            self._fp.flush()
        except Exception:
            log.exception("RawLogger flush failed")
        finally:
            self._buffer.clear()
            self._last_flush = time.monotonic()

    def _close(self) -> None:
        if self._buffer:
            self.flush()
        if self._fp:
            self._fp.close()
            self._fp = None

    def close(self) -> None:
        self._close()
