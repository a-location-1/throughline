from fastapi.testclient import TestClient

from throughline import api


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
