"""SSRF-resistant, bounded URL acquisition."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

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


def _public_host(host: str) -> None:
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
        ):
            raise ValueError("disallowed destination")
        if parsed.version == 4 and address.startswith("169.254."):
            raise ValueError("disallowed destination")


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


async def fetch_url(url: str) -> RetrievedSource:
    current = validate_url(url)
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            response = await client.get(current)
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
                current = str(redirect_url)
                validate_url(current)
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
            content = bytearray()
            async for chunk in response.aiter_bytes(64 * 1024):
                content.extend(chunk)
                if len(content) > MAX_BYTES:
                    raise ValueError("source too large")
            return RetrievedSource(
                bytes(content), content_type, urlparse(current).hostname or "source"
            )
    raise ValueError("too many redirects")


def fetch_url_sync(url: str) -> RetrievedSource:
    return asyncio.run(fetch_url(url))
