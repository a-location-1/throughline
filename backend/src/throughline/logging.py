"""Redacted application logging helpers."""

import logging

logger = logging.getLogger("throughline")


def log_event(
    event: str, *, analysis_id: str | None = None, code: str | None = None
) -> None:
    logger.info(
        "event=%s analysis_id=%s code=%s",
        event,
        analysis_id or "redacted",
        code or "redacted",
    )
