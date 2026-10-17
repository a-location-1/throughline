import json
import logging
from logging.handlers import RotatingFileHandler

from fastapi.testclient import TestClient

from throughline import api
from throughline import logging as application_logging
from throughline.logging import JsonFormatter


def test_rate_limit_returns_safe_response(monkeypatch):
    monkeypatch.setattr(api.rate_limiter, "limits", {"analysis": (0, 60), "logs": (60, 60)})
    response = TestClient(api.app).post(
        "/api/analyses", json={"url": "https://example.org/play.html"}
    )
    assert response.status_code == 429
    assert "too many" in response.json()["detail"]["message"].lower()
    assert response.headers["retry-after"] == "60"


def test_frontend_log_endpoint_writes_ndjson(tmp_path, monkeypatch):
    path = tmp_path / "frontend.log"
    test_logger = logging.getLogger("test.api.frontend")
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=1)
    handler.setFormatter(JsonFormatter())
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False
    monkeypatch.setattr(application_logging, "frontend_logger", test_logger)

    response = TestClient(api.app).post(
        "/api/logs",
        json={"level": "info", "message": "analysis finished", "context": {"sourceKind": "pdf", "durationMs": 42}},
    )
    handler.flush()
    try:
        assert response.status_code == 204
        record = json.loads(path.read_text())
        assert record["level"] == "INFO"
        assert record["logger"] == "test.api.frontend"
    finally:
        test_logger.removeHandler(handler)
        handler.close()


def test_frontend_log_endpoint_bounds_message_and_context():
    client = TestClient(api.app)
    assert client.post("/api/logs", json={"level": "info", "message": "x" * 1001}).status_code == 422
    assert client.post("/api/logs", json={"level": "info", "message": "x", "context": {"x": "y" * 9000}}).status_code == 413
