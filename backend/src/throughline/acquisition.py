"""SSRF-resistant, bounded URL acquisition."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import httpcore
from httpcore._backends.auto import AutoBackend

MAX_BYTES = 10 * 1024 * 1024
MAX_REDIRECTS = 4
TIMEOUT = httpx.Timeout(connect=5, read=20, write=10, pool=5)
REJECT_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".localdomain",
    ".internal",
    ".lan",
    ".home.arpa",
)


def _is_rejected_hostname(hostname: str | None) -> bool:
    if hostname is None:
        return True
    host = hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain", "127.0.0.1", "::1", "0.0.0.0"}:
        return True
    return any(host.endswith(suffix) for suffix in REJECT_HOST_SUFFIXES)


@dataclass
class RetrievedSource:
    content: bytes
    content_type: str
    source_name: str


def _public_host(host: str) -> tuple[str, ...]:
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise ValueError("unresolvable host") from exc
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if (
            parsed.is_private
            or parsed.is_loopback
            or parsed.is_link_local
            or parsed.is_multicast
            or parsed.is_reserved
            or parsed.is_unspecified
            or (
                parsed.version == 4
                and ipaddress.ip_address("100.64.0.0")
                <= parsed
                <= ipaddress.ip_address("100.127.255.255")
            )
        ):
            raise ValueError("disallowed destination")
        if parsed.version == 4 and address.startswith("169.254."):
            raise ValueError("disallowed destination")
    return tuple(addresses)


def validate_url(value: str) -> str:
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("invalid URL")
    if _is_rejected_hostname(parsed.hostname):
        raise ValueError("disallowed destination")
    _public_host(parsed.hostname)
    return value


def _validate_and_resolve(value: str) -> tuple[str, tuple[str, ...]]:
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("invalid URL")
    if _is_rejected_hostname(parsed.hostname):
        raise ValueError("disallowed destination")
    addresses = _public_host(parsed.hostname)
    return value, tuple(addresses)


class _PinnedNetworkBackend(httpcore.AsyncNetworkBackend):
    def __init__(self, addresses: tuple[str, ...]) -> None:
        self._addresses = addresses
        self._backend = AutoBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options=None,
    ):
        return await self._backend.connect_tcp(
            self._addresses[0], port, timeout, local_address, socket_options
        )


class _PinnedResponseStream(httpx.AsyncByteStream):
    def __init__(self, stream) -> None:
        self._stream = stream

    async def __aiter__(self):
        async for chunk in self._stream:
            yield chunk

    async def aclose(self) -> None:
        await self._stream.aclose()


class _PinnedTransport(httpx.AsyncBaseTransport):
    def __init__(self, addresses: tuple[str, ...]) -> None:
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=httpx.create_ssl_context(),
            network_backend=_PinnedNetworkBackend(addresses),
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        core_request = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )
        response = await self._pool.handle_async_request(core_request)
        return httpx.Response(
            status_code=response.status,
            headers=response.headers,
            stream=_PinnedResponseStream(response.stream),
            extensions=response.extensions,
            request=request,
        )

    async def aclose(self) -> None:
        await self._pool.aclose()


async def fetch_url(url: str) -> RetrievedSource:
    current, addresses = _validate_and_resolve(url)
    for _ in range(MAX_REDIRECTS + 1):
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=False,
            trust_env=False,
            transport=_PinnedTransport(addresses),
        ) as client:
            async with client.stream("GET", current) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("unsafe redirect")
                    try:
                        redirect_url = response.url.join(location)
                    except ValueError as exc:
                        raise ValueError("unsafe redirect") from exc
                    parsed_redirect = urlparse(str(redirect_url))
                    if parsed_redirect.scheme.lower() not in {"http", "https"}:
                        raise ValueError("unsafe redirect")
                    current, addresses = _validate_and_resolve(str(redirect_url))
                    continue
                response.raise_for_status()
                content_type = (
                    response.headers.get("content-type", "").split(";", 1)[0].lower()
                )
                if content_type not in {
                    "text/html",
                    "text/plain",
                    "application/pdf",
                } and not content_type.endswith("+html"):
                    raise ValueError("unsupported content type")
                if response.headers.get("content-encoding", "identity").lower() not in {
                    "",
                    "identity",
                }:
                    raise ValueError("compressed source is not supported")
                content_length = response.headers.get("content-length")
                if content_length is not None and int(content_length) > MAX_BYTES:
                    raise ValueError("source too large")
                content = bytearray()
                async for chunk in response.aiter_raw(64 * 1024):
                    content.extend(chunk)
                    if len(content) > MAX_BYTES:
                        raise ValueError("source too large")
                return RetrievedSource(
                    bytes(content), content_type, urlparse(current).hostname or "source"
                )
    raise ValueError("too many redirects")


def fetch_url_sync(url: str) -> RetrievedSource:
    return asyncio.run(fetch_url(url))
