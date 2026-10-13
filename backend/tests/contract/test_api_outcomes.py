import json
import logging
from logging.handlers import RotatingFileHandler

from fastapi.testclient import TestClient

from throughline import api
from throughline import logging as application_logging
from throughline.logging import JsonFormatter


def test_rate_limit_returns_safe_response(monkeypatch):
    original = api.store
    api.store = type(original)(rate_limit=0)
    try:
        response = TestClient(api.app).post(
            "/api/analyses", json={"url": "https://example.org/play.html"}
        )
        assert response.status_code == 429
        assert "too many" in response.json()["detail"]["message"].lower()
    finally:
        api.store = original


def test_csv_requires_ready_result():
    response = TestClient(api.app).get("/api/analyses/not-ready/csv")
    assert response.status_code == 404


def test_frontend_log_endpoint_writes_ndjson(tmp_path, monkeypatch):
    path = tmp_path / "frontend.log"
    test_logger = logging.getLogger("test.api.frontend")
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=1)
    handler.setFormatter(JsonFormatter())
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False
    monkeypatch.setattr(application_logging, "frontend_logger", test_logger)

    try:
        response = TestClient(api.app).post(
            "/api/logs",
            json={
                "level": "info",
                "message": "analysis finished",
                "context": {"sourceKind": "pdf", "durationMs": 42},
            },
        )
        handler.flush()

        assert response.status_code == 204
        record = json.loads(path.read_text())
        assert record["level"] == "INFO"
        assert record["logger"] == "test.api.frontend"
        assert record["message"] == (
            'analysis finished context={"durationMs": 42, "sourceKind": "pdf"}'
        )
    finally:
        test_logger.removeHandler(handler)
        handler.close()


def test_frontend_log_endpoint_rejects_unsupported_level():
    response = TestClient(api.app).post(
        "/api/logs", json={"level": "debug", "message": "ignored"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported log level"
