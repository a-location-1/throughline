import pytest

from throughline.acquisition import MAX_BYTES, RetrievedSource, fetch_url


@pytest.mark.asyncio
async def test_fetch_url_rejects_disallowed_content(monkeypatch):
    class Response:
        is_redirect = False
        headers = {"content-type": "image/png"}
        url = "https://example.org"

        def raise_for_status(self):
            pass

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        class Stream:
            async def __aenter__(self):
                return Response()

            async def __aexit__(self, *args):
                pass

        def stream(self, method, url):
            return self.Stream()

    monkeypatch.setattr(
        "throughline.acquisition.httpx.AsyncClient", lambda **kwargs: Client()
    )
    monkeypatch.setattr(
        "throughline.acquisition._public_host", lambda host: ("93.184.216.34",)
    )
    with pytest.raises(ValueError, match="content type"):
        await fetch_url("https://example.org/play")
