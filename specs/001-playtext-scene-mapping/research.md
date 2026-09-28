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
