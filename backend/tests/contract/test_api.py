from fastapi.testclient import TestClient
import pytest

from throughline import api
from throughline.acquisition import RetrievedSource
from throughline.extraction import ExtractedText


def test_url_analysis_returns_complete_result(monkeypatch):
    async def fake_fetch(url: str):
        return RetrievedSource(
            b"<h1>SCENE I</h1><p>ALICE</p><p>Hello</p>",
            "text/html",
            "example.org",
        )

    monkeypatch.setattr(api, "fetch_url", fake_fetch)
    response = TestClient(api.app).post(
        "/api/analyses", json={"url": "https://example.org/play.html"}
    )

    assert response.status_code == 200
    assert response.json()["submission"]["state"] == "ready"
    assert response.json()["scenes"][0]["id"] == "scene-01"


@pytest.mark.parametrize(
    ("content", "content_type", "code", "message_fragment"),
    [
        (b"", "text/plain", "SOURCE_EMPTY", "no readable text"),
        (b"<html><body></body></html>", "text/html", "SOURCE_EMPTY", "no readable text"),
        (b"This is an ordinary webpage mentioning a scene.", "text/plain", "NOT_PLAYTEXT", "contains a playtext"),
        (
            b"<html><body>Google<br>Gmail<br>Images<br>Sign in<br>Business Solutions<br>About Google<br>Privacy<br>Terms</body></html>",
            "text/html",
            "NOT_PLAYTEXT",
            "contains a playtext",
        ),
    ],
)
def test_url_failures_return_immediate_error(
    monkeypatch, content, content_type, code, message_fragment
):
    async def fake_fetch(url: str):
        return RetrievedSource(content, content_type, "example.org")

    monkeypatch.setattr(api, "fetch_url", fake_fetch)
    response = TestClient(api.app).post(
        "/api/analyses", json={"url": "https://example.org/source"}
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == code
    assert message_fragment in response.json()["detail"]["message"]


def test_pdf_analysis_returns_complete_result(monkeypatch):
    monkeypatch.setattr(
        api,
        "extract_pdf",
        lambda data, filename: ExtractedText("SCENE I\nALICE\nHello", filename),
    )
    response = TestClient(api.app).post(
        "/api/analyses",
        files={"file": ("source.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["submission"]["source_kind"] == "pdf"


def test_legacy_polling_and_csv_endpoints_are_removed():
    client = TestClient(api.app)
    assert client.get("/api/analyses/unknown").status_code == 404
    assert client.get("/api/analyses/unknown/csv").status_code == 404


def test_invalid_submission_is_rejected():
    assert TestClient(api.app).post("/api/analyses", json={}).status_code == 400


@pytest.mark.parametrize(
    ("extraction_error", "code", "message_fragment"),
    [("image-only PDF", "PDF_NO_TEXT", "no selectable text"), ("too many pages", "PDF_TOO_MANY_PAGES", "200 pages")],
)
def test_pdf_failures_return_immediate_error(
    monkeypatch, extraction_error, code, message_fragment
):
    monkeypatch.setattr(api, "extract_pdf", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError(extraction_error)))
    response = TestClient(api.app).post(
        "/api/analyses",
        files={"file": ("source.pdf", b"%PDF-1.7", "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == code
    assert message_fragment in response.json()["detail"]["message"]
