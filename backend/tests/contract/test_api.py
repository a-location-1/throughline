from fastapi.testclient import TestClient

from throughline import api
from throughline.acquisition import RetrievedSource


def test_url_analysis_contract(monkeypatch):
    async def fake_fetch(url: str):
        return RetrievedSource(
            b"<h1>SCENE I</h1><p>ALICE</p><p>Hello</p>", "text/html", "example.org"
        )

    monkeypatch.setattr(api, "fetch_url", fake_fetch)
    client = TestClient(api.app)
    response = client.post(
        "/api/analyses", json={"url": "https://example.org/play.html"}
    )
    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]
    result = client.get(f"/api/analyses/{analysis_id}")
    assert result.status_code == 200
    assert result.json()["state"] == "ready"
    assert result.json()["result"]["scenes"][0]["id"] == "scene-01"


def test_unknown_analysis_is_not_disclosing():
    response = TestClient(api.app).get("/api/analyses/unknown")
    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"


def test_invalid_submission_is_rejected():
    response = TestClient(api.app).post("/api/analyses", json={})
    assert response.status_code == 400


def test_pdf_rejection_and_csv_export(monkeypatch):
    async def fake_fetch(url: str):
        return RetrievedSource(b"ALICE\nHello", "text/plain", "example.org")

    monkeypatch.setattr(api, "fetch_url", fake_fetch)
    client = TestClient(api.app)
    response = client.post(
        "/api/analyses", json={"url": "https://example.org/play.txt"}
    )
    analysis_id = response.json()["analysis_id"]
    csv_response = client.get(f"/api/analyses/{analysis_id}/csv")
    assert csv_response.status_code == 200
    assert "character,scene_id" in csv_response.text

    rejected = client.post(
        "/api/analyses", files={"file": ("bad.pdf", b"not pdf", "application/pdf")}
    )
    assert rejected.status_code == 202
    rejected_status = client.get(f"/api/analyses/{rejected.json()['analysis_id']}")
    assert rejected_status.json()["state"] == "rejected"
