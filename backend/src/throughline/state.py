"""Ephemeral analysis state, cleanup, concurrency and rate limiting."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass

from .models import AnalysisResult, Failure, Progress, SubmissionState


@dataclass
class StoredAnalysis:
    analysis_id: str
    state: SubmissionState
    progress: Progress
    result: AnalysisResult | None = None
    error: Failure | None = None
    created_at: float = 0.0
    updated_at: float = 0.0


class AnalysisStore:
    def __init__(
        self, ttl_seconds: int = 900, max_active: int = 4, rate_limit: int = 12
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_active = max_active
        self.rate_limit = rate_limit
        self._items: dict[str, StoredAnalysis] = {}
        self._submissions: list[float] = []
        self._lock = threading.RLock()

    def _purge(self) -> None:
        now = time.monotonic()
        expired = [
            key
            for key, item in self._items.items()
            if now - item.updated_at > self.ttl_seconds
        ]
        for key in expired:
            del self._items[key]
        self._submissions = [stamp for stamp in self._submissions if now - stamp < 60]

    def create(self) -> StoredAnalysis:
        with self._lock:
            self._purge()
            if (
                len(
                    [
                        item
                        for item in self._items.values()
                        if item.state
                        not in {SubmissionState.READY, SubmissionState.REJECTED}
                    ]
                )
                >= self.max_active
            ):
                raise RuntimeError("analysis capacity reached")
            if len(self._submissions) >= self.rate_limit:
                raise RuntimeError("submission rate limit reached")
            now = time.monotonic()
            self._submissions.append(now)
            analysis_id = secrets.token_urlsafe(16)
            item = StoredAnalysis(
                analysis_id,
                SubmissionState.QUEUED,
                Progress(stage="queued", percent=0),
                created_at=now,
                updated_at=now,
            )
            self._items[analysis_id] = item
            return item

    def get(self, analysis_id: str) -> StoredAnalysis | None:
        with self._lock:
            self._purge()
            return self._items.get(analysis_id)

    def update(
        self,
        analysis_id: str,
        *,
        state: SubmissionState,
        progress: Progress,
        result: AnalysisResult | None = None,
        error: Failure | None = None,
    ) -> None:
        with self._lock:
            item = self._items.get(analysis_id)
            if item is None:
                return
            item.state, item.progress, item.result, item.error = (
                state,
                progress,
                result,
                error,
            )
            item.updated_at = time.monotonic()

    def reset(self, analysis_id: str) -> None:
        with self._lock:
            self._items.pop(analysis_id, None)
