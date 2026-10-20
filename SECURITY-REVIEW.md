# Security Review

**Review date:** 2026-10-19

## Summary

The analyzer endpoint is an unauthenticated URL-fetching service. A remote
caller can submit a public HTTP(S) URL and cause the Vercel backend to issue an
outbound `GET` request from Vercel infrastructure. This creates a request
laundering and light scraping/traffic-generation risk.

This is a **medium-severity** finding with **high confidence**. It is not
currently an unrestricted internal-network SSRF because the acquisition layer
rejects private and special-use destinations.

## Finding

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| 1 | 🟡 MEDIUM | [`backend/src/throughline/api.py`](backend/src/throughline/api.py#L220-L261) | 220-261 | Unauthenticated `POST /api/analyses` accepts an attacker-selected public URL and makes an outbound request from Vercel infrastructure. The process-local limiter is not a reliable production abuse-control boundary across Vercel instances. | 10/10 |
| 2 | 🟡 MEDIUM | [`backend/src/throughline/api.py`](backend/src/throughline/api.py#L261-L293) | 261-293 | URL fetching, extraction, and parsing did not previously share a request-wide deadline. Stacked HTTP timeouts and redirect hops could extend work up to the deployment limit, creating denial-of-wallet risk. | 9/10 |

### Impact

An attacker can use the endpoint to fetch third-party public content with the
server's source IP and reputation, or generate requests against a destination
selected by the attacker. CORS does not prevent this because non-browser
clients can call the endpoint directly. The in-process limit of 12 requests
per client per minute is not distributed and can be bypassed across serverless
instances.

### Existing protections

The current acquisition implementation provides meaningful SSRF and resource
controls:

- Only `http` and `https` URLs are accepted.
- Userinfo, localhost names, local suffixes, and unresolved hosts are rejected.
- DNS results are checked against private, loopback, link-local, multicast,
  reserved, unspecified, and carrier-grade NAT ranges.
- Validated addresses are pinned for the connection to reduce DNS-rebinding
  risk.
- Redirects are disabled in the HTTP client, manually limited to four hops,
  and revalidated at every hop.
- Ambient proxy environment variables are disabled.
- Connection, read, write, and pool timeouts are configured.
- Response bodies are limited to 10 MiB by both declared length and streamed
  byte count.
- Only HTML, plain text, and PDF responses are accepted.
- Logs avoid including submitted URLs and user-controlled response content.

These controls should be retained. They reduce SSRF and resource-exhaustion
risk but do not prevent public request laundering.

## Recommended remediation

Before production exposure, put `POST /api/analyses` behind a real abuse
control boundary:

1. Prefer authentication, an API key, or a signed short-lived request.
2. Add distributed or Vercel/edge-enforced rate limiting and a concurrency
   cap; do not rely on the process-local limiter as the production control.
3. If anonymous use is a product requirement, add bot protection or
   challenges, per-user or per-origin quotas, and monitoring for destination
   abuse. Document that the endpoint is not a general-purpose fetch service.
4. Continue testing IPv4 and IPv6 special ranges, redirects to private
   addresses, DNS rebinding, and redirect chains.

Authentication and deployment-level rate limiting require a product and
deployment decision. The timeout portion of this finding has been remediated
in code.

## Implemented timeout remediation

`backend/src/throughline/api.py` now applies a single 55-second
`asyncio.timeout()` around URL fetching, extraction, and parsing. This is
shorter than the 60-second Vercel `maxDuration`, so the application deadline
fires before the platform limit. Existing error handling and response
semantics are preserved.

The focused regression test in
`backend/tests/contract/test_api.py` uses a hanging URL fetch and verifies the
existing `422 SOURCE_UNREADABLE` error response. The implementation retains
`asyncio.to_thread()` for synchronous extraction and parsing. Worker threads
remain non-cancellable when the await is cancelled; a larger follow-up using
process-based execution or cooperative cancellation is required to ensure
timed-out CPU work itself is terminated.

## Validation

The following targeted tests passed:

```text
cd backend && .venv/bin/pytest -q \
  tests/unit/test_acquisition.py \
  tests/unit/test_acquisition_limits.py \
  tests/contract/test_api.py

21 passed, 1 deprecation warning
```

The focused timeout and acquisition tests also passed:

```text
cd backend && .venv/bin/pytest -q \
  tests/contract/test_api.py \
  tests/unit/test_api_async_boundaries.py \
  tests/unit/test_acquisition.py \
  tests/unit/test_acquisition_limits.py

24 passed, 1 warning
```
