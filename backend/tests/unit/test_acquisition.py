import pytest

from throughline.acquisition import _PinnedNetworkBackend, fetch_url, validate_url


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

        class Stream:
            async def __aenter__(self):
                return RedirectResponse()

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
    with pytest.raises(ValueError, match="unsafe redirect|redirect"):
        await fetch_url("https://example.org/start")


def test_cgnat_destination_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "throughline.acquisition.socket.getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("100.100.100.200", 0))],
    )
    with pytest.raises(ValueError, match="disallowed"):
        validate_url("https://metadata.example/play")


@pytest.mark.asyncio
async def test_pinned_backend_uses_validated_address_without_resolving_again():
    calls = []

    class Backend:
        async def connect_tcp(self, host, port, timeout, local_address, socket_options):
            calls.append(host)
            return "stream"

    backend = _PinnedNetworkBackend(("93.184.216.34",))
    backend._backend = Backend()
    await backend.connect_tcp("example.org", 443)
    assert calls == ["93.184.216.34"]
