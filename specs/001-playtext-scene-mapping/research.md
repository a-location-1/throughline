# Research: Playtext Scene Mapping

## Decision: Python library behind FastAPI

Use Python 3.11+, with a standalone parser library and FastAPI/Pydantic at the HTTP boundary. Keep acquisition, extraction, parsing, aggregation, and visualization-data generation independent from request handlers.

Rationale: Python satisfies the organizational constraint, FastAPI provides typed request/response validation and clear API tests, and library-first separation makes parser behavior independently reviewable.

Alternatives considered: Flask is viable but offers less built-in contract structure. A Node backend would align with a TypeScript frontend but does not fit the requested review constraint.

## Decision: Rule-based deterministic parsing

Use ordered, explicit heuristics and a state machine for act/scene headings, speaker attribution, stage directions, collective speakers, unnamed speakers, and conservative identity normalization. Preserve ambiguity metadata whenever evidence is insufficient.

Rationale: the constitution requires repeatability and the spec requires identical results for repeated runs. Probabilistic NLP or an LLM would make ordering and interpretation harder to explain and test.

Alternatives considered: spaCy or an LLM may support future enrichment, but they are not appropriate for the first release's deterministic contract.

## Decision: Guarded source acquisition and selectable-text extraction

Use `httpx` for URL retrieval with scheme/host validation, timeout, redirect, content-type, and 10 MB response limits. Use BeautifulSoup for HTML text extraction and `pypdf` for selectable-text PDFs. Reject image-only PDFs and inputs over 200 pages or 10 MB.

Rationale: these dependencies are small, established, and sufficient for the stated first-release scope. Acquisition must fail clearly rather than silently producing partial analysis.

Alternatives considered: PyMuPDF may extract difficult PDFs better, but adds a larger dependency and is deferred until representative fixtures demonstrate a need. OCR is explicitly out of scope.

## Decision: Vanilla TypeScript/Vite frontend based on mockup 1

Keep the light paper, red/green accent palette, serif display typography, source panel, analysis controls, table/plot toggle, About section, responsive layout, copy feedback, and CSV action from `mockup_copilot_1`. Replace seeded sample data with API state and generated rendering.

Use only `mockup_copilot_2`'s SVG line-drawing treatment (`stroke-dasharray`/draw animation), with `prefers-reduced-motion` disabling animation while preserving the same geometry.

Rationale: this is the smallest change that turns the existing visual direction into a working product and preserves the user's explicit mockup guidance.

Alternatives considered: React is unnecessary for the current single-page workflow and would require restructuring the mockup. A full rewrite of mockup 2 would lose the requested visual language.

## Decision: One shared result contract

The backend returns one ordered `AnalysisResult` containing acts, scenes, characters, appearances, ambiguity metadata, and deterministic visualization inputs. The frontend never independently infers presence or character identity; table and visualization derive from the same response.

Rationale: this directly enforces FR-014 and the deterministic visualization constitution principle.

## Decision: Fixture-led validation

Create golden fixtures for ordinary plays, one-act/no-scene inputs, scene-only inputs, single speakers, unnamed and collective speakers, silent presence, formatting variation, ambiguity, malformed input, and oversized/unreadable sources. Add API contract tests, frontend state/render tests, coverage enforcement above 80%, and Playwright snapshots for plot/table/loading/error/mobile/reduced-motion states.

Rationale: parser variability is the dominant risk; fixed fixtures make supported behavior and regressions visible.

## Decision: Synchronous FastAPI request for initial serverless hosting (2026-10-17)

Replace the initial `POST` plus background task plus polling workflow with one synchronous `POST /api/analyses` that returns the complete `AnalysisResult`. Keep FastAPI as the backend entry point so the parser, acquisition safeguards, typed models, and existing contract-test approach remain reusable for Vercel's Python runtime.

Rationale: the current parser is fast enough that server-reported progress no longer provides enough value to justify process-local job state. The old design relies on `BackgroundTasks` and an in-memory `AnalysisStore`, neither of which is durable across serverless invocations, cold starts, multiple workers, or separate Vercel instances. A direct request also eliminates repeated polling traffic and the need to expose result lookup by opaque ID. The frontend instead shows staged indeterminate feedback, disables duplicate submission, supports `AbortController` cancellation, and renders the response when the request completes.

The initial deployment assumes low volume and one synchronous function instance. A process-local sliding-window limiter is explicit for analysis submissions and frontend logs, with bounded upload and log payloads. If the service scales to multiple instances, rate limiting must move to a shared store or an edge/WAF control. This is a deployment constraint, not a claim that in-memory limits are globally enforceable.

Alternatives considered: Server-Sent Events would preserve authoritative progress but add streaming and proxy complexity without meaningful benefit for fast parsing. A durable queue, object storage, and worker would be more resilient for workloads exceeding function duration, but is deferred until deployed benchmarks show the synchronous limits are insufficient. Client-side parsing would improve privacy and eliminate backend CPU use but requires a substantial parser/PDF port.

## Hosting validation still required

Before production Vercel hosting, test the Python build and runtime with representative 10 MB/200-page PDFs, the `pypdf` version, and the `httpx`/`httpcore`/TLS trust stack in the actual Vercel build environment. Verify function duration, memory, request-body limits, cold starts, outbound URL behavior, and configured CORS. The synchronous design must retain smaller internal timeouts and all SSRF, redirect, content, page, text, and byte limits.

## Decision: Layered Vercel request and abuse protection (2026-10-17)

The FastAPI application now buffers only up to a bounded request-body limit before handing the request to Starlette. `POST /api/analyses` is capped at 11 MiB, allowing a 10 MiB PDF plus multipart overhead; `POST /api/logs` is capped at 16 KiB. The source and log field limits remain enforced separately after parsing.

Vercel Firewall/WAF protection is complementary and must be configured in the Vercel project Firewall dashboard or API rather than committed as application code. Configure custom rate-limit rules for `POST /api/analyses` and `POST /api/logs`, enable managed rulesets and Bot Protection where available, and use the application limits as defense in depth. The initial suggested thresholds are 12 analysis requests per IP per 60 seconds and 60 log requests per IP per 60 seconds. Vercel platform DDoS mitigation is automatic, but it does not replace endpoint-specific limits.

The WAF configuration is intentionally not represented in `vercel.json`: the repository can define function behavior and headers, but Vercel Firewall rules are project/account configuration and may vary by plan and deployment. After enabling them, verify the rules against preview and production domains, confirm that legitimate frontend requests remain allowed, and monitor Firewall events before tightening actions from challenge to deny.
