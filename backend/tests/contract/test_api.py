from fastapi.testclient import TestClient
import pytest

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


@pytest.mark.parametrize(
    ("content", "content_type", "code", "message_fragment"),
    [
        (b"", "text/plain", "SOURCE_EMPTY", "no readable text"),
        (
            b"<html><body></body></html>",
            "text/html",
            "SOURCE_EMPTY",
            "no readable text",
        ),
        (
            b"This is an ordinary webpage mentioning a scene.",
            "text/plain",
            "NOT_PLAYTEXT",
            "contains a playtext",
        ),
    ],
)
def test_url_failures_explain_the_specific_problem(
    monkeypatch, content, content_type, code, message_fragment
):
    async def fake_fetch(url: str):
        return RetrievedSource(content, content_type, "example.org")

    monkeypatch.setattr(api, "fetch_url", fake_fetch)
    client = TestClient(api.app)
    response = client.post("/api/analyses", json={"url": "https://example.org/source"})
    status = client.get(f"/api/analyses/{response.json()['analysis_id']}").json()

    assert status["state"] == "rejected"
    assert status["error"]["code"] == code
    assert message_fragment in status["error"]["message"]


def test_pdf_url_extraction_failure_explains_no_selectable_text(monkeypatch):
    async def fake_fetch(url: str):
        return RetrievedSource(b"%PDF-1.7", "application/pdf", "example.org")

    def fail_extract(*args, **kwargs):
        raise ValueError("image-only PDF")

    monkeypatch.setattr(api, "fetch_url", fake_fetch)
    monkeypatch.setattr(api, "extract_pdf", fail_extract)
    client = TestClient(api.app)
    response = client.post(
        "/api/analyses", json={"url": "https://example.org/source.pdf"}
    )
    status = client.get(f"/api/analyses/{response.json()['analysis_id']}").json()

    assert status["state"] == "rejected"
    assert status["error"]["code"] == "PDF_NO_TEXT"
    assert "selectable text" in status["error"]["message"]


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


@pytest.mark.parametrize(
    ("extraction_error", "code", "message_fragment"),
    [
        (
            "image-only PDF",
            "PDF_NO_TEXT",
            "no selectable text",
        ),
        (
            "too many pages",
            "PDF_TOO_MANY_PAGES",
            "200 pages",
        ),
    ],
)
def test_pdf_rejection_explains_extraction_problem(
    monkeypatch, extraction_error, code, message_fragment
):
    def fail_extract(*args, **kwargs):
        raise ValueError(extraction_error)

    monkeypatch.setattr(api, "extract_pdf", fail_extract)
    client = TestClient(api.app)
    response = client.post(
        "/api/analyses", files={"file": ("source.pdf", b"%PDF-1.7", "application/pdf")}
    )
    analysis_id = response.json()["analysis_id"]
    status = client.get(f"/api/analyses/{analysis_id}").json()

    assert status["state"] == "rejected"
    assert status["error"]["code"] == code
    assert message_fragment in status["error"]["message"]
