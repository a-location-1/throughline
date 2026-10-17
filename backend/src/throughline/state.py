"""Process-local request limits for the initial low-volume deployment."""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Sliding-window limits for one application process.

    This is intentionally not a distributed limiter. Deployments with multiple
    workers or instances must add shared or edge-level rate limiting.
    """

    def __init__(self, limits: dict[str, tuple[int, float]]) -> None:
        self.limits = limits
        self._events: dict[tuple[str, str], list[float]] = {}
        self._lock = threading.RLock()

    def allow(self, client_id: str, bucket: str) -> bool:
        limit, window_seconds = self.limits[bucket]
        now = time.monotonic()
        key = (client_id, bucket)
        with self._lock:
            events = [
                stamp
                for stamp in self._events.get(key, [])
                if now - stamp < window_seconds
            ]
            if len(events) >= limit:
                self._events[key] = events
                return False
            events.append(now)
            self._events[key] = events
            return True
