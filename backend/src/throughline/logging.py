"""Redacted application logging helpers."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class IsoFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return (
            datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )


def _configure_logger(name: str, filename: str, *, propagate: bool) -> logging.Logger:
    configured_logger = logging.getLogger(name)
    configured_logger.setLevel(LOG_LEVEL)
    configured_logger.propagate = propagate

    log_path = (LOG_DIR / filename).resolve()
    if not any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename) == log_path
        for handler in configured_logger.handlers
    ):
        file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
        file_handler.setFormatter(IsoFormatter("%(asctime)s %(levelname)s %(message)s"))
        configured_logger.addHandler(file_handler)

    if (not logging.getLogger().handlers or not propagate) and not any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, RotatingFileHandler)
        for handler in configured_logger.handlers
    ):
        terminal_handler = logging.StreamHandler()
        terminal_handler.setFormatter(
            IsoFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        configured_logger.addHandler(terminal_handler)
    return configured_logger


logger = _configure_logger("throughline", "backend.log", propagate=True)
frontend_logger = _configure_logger(
    "throughline.frontend", "frontend.log", propagate=False
)


def log_event(
    event: str, *, analysis_id: str | None = None, code: str | None = None
) -> None:
    logger.info(
        "event=%s analysis_id=%s code=%s",
        event,
        analysis_id or "redacted",
        code or "redacted",
    )


def log_frontend_event(level: str, message: str, context: dict[str, Any]) -> None:
    log_method = getattr(frontend_logger, "warning" if level == "warn" else level)
    log_method("%s context=%s", message, json.dumps(context, sort_keys=True))
