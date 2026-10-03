import pytest

from throughline.acquisition import fetch_url, validate_url


def test_url_requires_public_http_scheme():
    with pytest.raises(ValueError):
        validate_url("file:///tmp/play.txt")
    with pytest.raises(ValueError):
        validate_url("https://user:pass@example.org/play")


def test_localhost_is_rejected():
    with pytest.raises(ValueError):
        validate_url("http://127.0.0.1/play")


def test_local_hostname_variants_are_rejected():
    for value in [
        "http://localhost/play",
        "http://localhost.localdomain/play",
        "http://internal.local/play",
        "http://example.internal/play",
        "http://home.arpa/play",
    ]:
        with pytest.raises(ValueError):
            validate_url(value)


@pytest.mark.asyncio
async def test_fetch_url_rejects_unsafe_redirect_targets(monkeypatch):
    class RedirectResponse:
        is_redirect = True
        headers = {"location": "javascript:alert(1)"}
        url = "https://example.org/start"

        def raise_for_status(self):
            pass

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return RedirectResponse()

    monkeypatch.setattr(
        "throughline.acquisition.httpx.AsyncClient", lambda **kwargs: Client()
    )
    monkeypatch.setattr("throughline.acquisition._public_host", lambda host: None)
    with pytest.raises(ValueError, match="unsafe redirect|redirect"):
        await fetch_url("https://example.org/start")
