import json
import logging
from logging.handlers import RotatingFileHandler

from throughline.logging import JsonFormatter, _configure_logger, log_event


def test_logging_does_not_include_source_details(caplog):
    with caplog.at_level(logging.INFO, logger="throughline"):
        log_event("rejected", analysis_id="opaque-id", code="SOURCE_UNREADABLE")
    assert "opaque-id" in caplog.text
    assert "https://" not in caplog.text


def test_logger_uses_stream_without_file_by_default(monkeypatch):
    monkeypatch.setattr("throughline.logging.LOG_TO_FILE", False)
    test_logger = _configure_logger("test.stream-only", "unused.log", propagate=False)
    try:
        assert any(
            isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, RotatingFileHandler)
            for handler in test_logger.handlers
        )
        assert not any(isinstance(handler, RotatingFileHandler) for handler in test_logger.handlers)
    finally:
        for handler in test_logger.handlers[:]:
            test_logger.removeHandler(handler)
            handler.close()


def test_json_formatter_writes_one_json_object_per_line(tmp_path):
    path = tmp_path / "events.log"
    test_logger = logging.getLogger("test.ndjson")
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=1)
    handler.setFormatter(JsonFormatter())
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)
    try:
        test_logger.info("hello %s", "world")
        handler.flush()
        lines = path.read_text().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0]) == {
            "level": "INFO",
            "logger": "test.ndjson",
            "message": "hello world",
            "timestamp": json.loads(lines[0])["timestamp"],
        }
        assert lines[0].count("\n") == 0
    finally:
        test_logger.removeHandler(handler)
        handler.close()


def test_rotating_file_handler_keeps_backup(tmp_path):
    path = tmp_path / "rotating.log"
    test_logger = logging.getLogger("test.rotation")
    handler = RotatingFileHandler(path, maxBytes=100, backupCount=1)
    handler.setFormatter(JsonFormatter())
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)
    try:
        for index in range(5):
            test_logger.info("entry-%s-%s", index, "x" * 80)
        handler.flush()
        assert path.exists()
        assert path.with_name("rotating.log.1").exists()
        assert all(json.loads(line) for line in path.read_text().splitlines())
        assert all(
            json.loads(line)
            for line in path.with_name("rotating.log.1").read_text().splitlines()
        )
    finally:
        test_logger.removeHandler(handler)
        handler.close()
