Implementation Plan: Playtext Scene Mapping

**Branch**: `001-playtext-scene-mapping` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

## Summary

Build a standalone web application that accepts a public playtext URL or selectable-text PDF, deterministically extracts acts, scenes, speakers, and scene appearances, and presents one shared analysis result as a character-by-scene table and animated reappearance visualization. The backend will be a Python library exposed through FastAPI; the frontend will preserve the structure and visual language of `mockup_copilot_1` and use only the SVG line-drawing animation treatment from `mockup_copilot_2`.

## Technical Context

**Language/Version**: Python 3.11+ backend; TypeScript 5.x frontend

**Primary Dependencies**: FastAPI, Pydantic, httpx, pypdf, BeautifulSoup; Vite and vanilla TypeScript; pytest, pytest-cov, Playwright

**Storage**: In-memory, request-scoped analysis state only; no persistent database or server-side result history

**Testing**: pytest with coverage threshold above 80%, golden parser fixtures, API contract tests, TypeScript tests, and Playwright visual/accessibility checks

**Target Platform**: Modern desktop and mobile browsers with a local/deployed Python web server

**Project Type**: Standalone web application with a library-first Python parser and HTTP API

**Performance Goals**: Begin progress feedback within 2 seconds; remain responsive for inputs up to 200 pages or 10 MB; maintain smooth plot interaction on supported browsers

**Constraints**: Reject over-limit, inaccessible, unreadable, non-PDF, and non-playtext inputs with actionable errors; protect URL retrieval against SSRF, unsafe redirects, timeouts, and oversized responses; do not retain submitted source or results after reset/leave

**Scale/Scope**: One focused single-page workflow, two source methods, one deterministic result schema, one table view, one visualization view, and CSV export

## Security Requirements

- URL retrieval accepts only `http` and `https`, rejects embedded credentials, and validates the destination before every request and redirect. Resolve hostnames and reject loopback, private, link-local, multicast, and cloud-metadata address ranges, including IPv4 and IPv6, to prevent SSRF and DNS-rebinding bypasses.
- Stream URL responses and enforce the 10 MB limit while reading; apply connection/read/total timeouts, a bounded redirect count, response content-type checks, and cancellation for abandoned analyses. Do not follow redirects to a newly disallowed destination.
- PDF uploads are validated by size, extension, declared type, and file signature; browser-provided MIME types and filenames are not trusted. Store temporary data under generated names, never execute or serve uploaded files, and remove temporary bytes after extraction or failure.
- Treat PDFs as hostile input: use a patched `pypdf`, cap page count and extracted text size, and enforce CPU, memory, and wall-clock limits around extraction so malformed files or decompression-heavy content cannot exhaust the service. OCR is not enabled.
- Bound concurrent analyses and expire in-memory analysis state after a short session TTL. Add rate limiting or equivalent deployment protection to submission endpoints and ensure failures clean up tasks, buffers, and temporary files.
- Never log full submitted URLs, query strings, filenames, source text, or extracted text. Return opaque analysis IDs and generic retrieval/parsing errors that do not disclose network details or local paths.
- Render parsed names and source metadata as escaped text in the frontend; never inject submitted HTML or SVG into the document. CSV export must escape formula-leading cell values and quote fields according to the CSV format.

## Accessibility Requirements

- Target WCAG 2.2 AA for the supported desktop and mobile browser workflow. Use semantic landmarks, one logical heading hierarchy, visible keyboard focus, and a skip link to move directly to the analysis content.
- Every URL field, file input, button, tab, toggle, table control, and visualization control MUST have an accessible name and a predictable keyboard operation. The plot/table switch MUST expose its selected state, and interactive controls MUST not depend on hover, drag, or color alone.
- Publish processing progress and copy/download/error outcomes through an `aria-live` status region without stealing focus. When an error requires correction, move focus to the error summary or the first invalid control and provide a direct retry/replace-source action.
- Keep the character-by-scene table as a real HTML table with captions or an accessible name, header associations, and a text alternative for speaking versus non-speaking presence. Preserve usable horizontal scrolling on narrow screens without hiding required data.
- Give the SVG visualization a meaningful accessible name and a concise text summary of scene order and character appearances. The visualization MUST remain understandable from the table and summary when SVG is unavailable or not perceivable.
- Use color combinations that meet contrast requirements and pair speaking/non-speaking/absence encodings with text, patterns, labels, or other non-color distinctions. Do not use color as the only indication of status.
- Respect `prefers-reduced-motion` and provide the same plot geometry with drawing animation disabled. Avoid flashing content and ensure focus indicators remain visible in every view and responsive breakpoint.
- Test keyboard-only navigation, screen-reader-oriented semantics, reduced motion, zoom/reflow, contrast, mobile touch targets, and automated accessibility checks in Playwright for loading, ready, table, visualization, and error states.

## Equity and Supported Scope

The first release is intentionally scoped to primarily English-language, Latin-script playtexts using recognizable Western dramatic conventions. This scope MUST be stated in the interface and documentation as a product boundary, not as a judgment about other performance-text traditions. Within that scope, fixtures and implementation MUST accommodate meaningful variation in formatting, Unicode, diacritics, capitalization, punctuation, honorifics, naming conventions, collective speakers, silent roles, and accessible versus difficult source files.

Preserve source-provided display names for readers while using separate deterministic internal IDs. Do not infer demographic or other personal identity attributes from names, pronouns, roles, or speech. When naming, transliteration, honorific, or formatting evidence is insufficient, preserve and display the ambiguity. Unsupported language, script, or structural forms must produce an explicit limitation or uncertainty state rather than an apparently reliable result.

## Constitution Check

All gates pass with the selected design:

- Principle I: the parser is a standalone, independently testable library; API and UI consume explicit typed models.
- Principle II: unit, boundary, invalid-input, regression, API, and rendering tests are planned with an enforced coverage threshold above 80%.
- Principle III: parser ordering, IDs, colors, layout inputs, and SVG generation are deterministic and protected by invariant and visual regression tests.
- Principle IV: the mockup supplies consistent terminology and responsive controls; every failure state includes a next action and accessible status text.
- Principle V: acquisition and parsing run outside the UI interaction path, limits are enforced early, and representative benchmark coverage is included.
- Domain constraints: ambiguity is represented in the result rather than silently merged or invented.

## Project Structure

```text
backend/
├── pyproject.toml
├── src/throughline/
│   ├── models.py
│   ├── acquisition.py
│   ├── extraction.py
│   ├── parser.py
│   ├── visualization.py
│   ├── state.py
│   ├── errors.py
│   ├── logging.py
│   └── api.py
└── tests/
    ├── fixtures/
    │   ├── valid/
    │   ├── invalid/
    │   ├── sources/
    │   └── expected/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── package.json
├── vite.config.ts
├── src/
│   ├── api.ts
│   ├── state.ts
│   ├── csv.ts
│   ├── render-table.ts
│   ├── render-visualization.ts
│   └── main.ts
└── tests/
    ├── unit/
    └── visual/
```

**Structure Decision**: Use separate `backend/` and `frontend/` projects. The backend owns acquisition, text extraction, deterministic parsing, domain models, visualization data, and API contracts. The frontend is a thin renderer and interaction layer based on `mockup_copilot_1`; it receives one `AnalysisResult` and derives both the table and SVG from that result. The source tree above is the planned implementation layout; the current repository contains the spec and mockups only.

## Golden Fixture Requirements

The implementation MUST create and run a versioned golden-fixture corpus before parser behavior is considered complete. Fixtures are test inputs and expected outputs, not production data.

### Required fixture categories

Create at least one small, hand-verifiable fixture for each category below. Prefer project-authored synthetic text for edge cases and public-domain or permission-cleared excerpts for realistic formatting. Record provenance for every non-synthetic source.

- `explicit-acts-scenes`: multiple acts and scenes with ordered headings.
- `one-act-no-scene-breaks`: one act with no explicit scene headings; verify no fabricated scenes.
- `scene-breaks-no-acts`: scene headings without act headings; verify one default act.
- `no-breaks-recognizable-play`: no act or scene headings but recognizable play structure; verify one act and one scene.
- `unconventional-formatting`: consistent `Scene`, `SCENE`, `Scene:`, `Chapter`, separator, and act-marker variants; verify contextual detection and no dialogue false positives.
- `unconventional-recognizable-play`: playtext without conventional act, scene, or character labels; verify best-effort output with unidentified-attribute notices.
- `unheaded-lyric-play`: recognizable play beginning without act/scene headings, containing strophe/antistrophe labels, and ending at a notes heading; verify one scene, no lyric-label splits, and no notes contamination.
- `roman-scenes-multi-play-pdf`: first play in a multi-play PDF with standalone Roman scene markers and omitted repeated single-speaker labels; verify first-play-only scope and speaker carry-forward.
- `multiple-plays`: anthology source containing at least two plays; verify a warning and first-play-only analysis.
- `non-play`: ordinary non-play source containing incidental words such as "scene"; verify rejection.
- `single-speaker`: one character throughout, including valid first-appearance ordering.
- `unnamed-speaker`: speech that cannot be assigned a supported name; verify an explicit unnamed entry.
- `collective-speaker`: crowd/group attribution with preserved line counts and collective kind.
- `silent-presence`: stage direction or entrance establishes a character without speech; verify `non_speaking` and zero line count.
- `name-variation`: formatting or spelling variation that is safely normalized, plus a distinct ambiguous variation that is not silently merged.
- `unicode-and-names`: Unicode, diacritics, punctuation, capitalization, honorifics, and naming-convention variation; verify source display forms remain intact.
- `group-reference`: collective introduction followed by an individually referenced character, with both supported-resolution and unresolved-ambiguity cases.
- `repeated-headings`: formatting noise or repeated headings that must not duplicate scenes.
- `unsupported-scope`: an out-of-scope language, script, or structural form; verify an explicit limitation or uncertainty result rather than a false successful analysis.
- `invalid-inputs`: empty, malformed, unreadable, non-playtext, image-only PDF, over-page-limit, and over-byte-limit cases.
- `accessibility-and-resources`: fixture and browser scenarios covering keyboard-only use, screen-reader semantics, low-vision zoom/reflow, reduced motion, mobile layout, slow connections, and modest-device resource limits.

### Fixture format and expected outputs

Each case MUST have a stable slug and consist of:

```text
tests/fixtures/
├── sources/<slug>.txt|html|pdf
├── expected/<slug>.json
└── manifest.json
```

`manifest.json` records the slug, source format, provenance/license, scenario category, parser options, and whether the case is expected to be `ready` or `rejected`. Ready-case JSON is a complete serialized `AnalysisResult`; rejected-case JSON records the stable error code and required next-action category. Expected data MUST assert act/scene order, character IDs and kinds, first-appearance order, appearance presence, line counts, ambiguity metadata, and deterministic visualization inputs. It MUST exclude source contents and volatile request IDs.

### Fixture test harness and maintenance rules

- Add a parameterized backend test that loads every manifest entry, runs the parser, and compares canonical JSON to the checked-in expected output.
- Canonicalization may remove only explicitly volatile fields; it MUST NOT sort away meaningful source order.
- Add invariant checks for unique stable IDs, scene order, first-appearance character order, non-speaking line count of zero, collective/unnamed preservation, table/visualization agreement, and byte-identical repeated output.
- Include both text/HTML and PDF forms where extraction differences could affect parsing; the same semantic fixture may have separate expected extraction notes when outputs legitimately differ.
- Any discovered parser defect MUST add or update a focused regression fixture and expected output before the parser fix is accepted.
- Fixture changes require a short explanation in the manifest or test name; do not regenerate all expected files blindly.
- CI MUST run the full fixture corpus, enforce the coverage threshold above 80%, and report scene-detection and character-identification results separately for each fixture category. A passing aggregate percentage MUST NOT hide a failing category.
- Accessibility and resource scenarios MUST be reported separately from parser accuracy, with failures classified by keyboard, screen-reader, low-vision, motion, mobile, connection, or device constraint.

## Phase 0 Research Summary

- Use FastAPI/Pydantic for typed HTTP boundaries and a standalone Python parser library.
- Use guarded `httpx` retrieval, BeautifulSoup HTML extraction, and `pypdf` selectable-text extraction.
- Use explicit, context-aware rule-based parsing with ambiguity metadata, not keyword-only matching or probabilistic inference. Structural markers may vary in case, punctuation, label, or separator, but one consistent convention is assumed within each submission; isolated words in dialogue are not structural evidence.
- Treat play recognition as a combined-evidence decision. Produce a best-effort result with notices when playtext is recognizable but conventional acts, scenes, or speaker labels are absent; reject ordinary non-play content; and warn plus scope to the first play when multiple plays are detected.
- Use vanilla TypeScript/Vite and adapt the existing mockup; import only the mockup 2 draw animation.
- Build the golden fixture corpus before parser completion, with manifest-backed expected JSON, canonical comparison, invariants, and regression additions for every discovered parser defect.
- Keep the initial corpus within the documented English/Latin-script Western-format scope while deliberately varying names, Unicode, formatting, source quality, accessibility conditions, and resource constraints; record out-of-scope cases as explicit rejection/limitation fixtures.
- Validate with the fixture corpus, API tests, deterministic invariants, coverage enforcement, and Playwright visual/accessibility checks.

## Phase 1 Design Summary

The shared `AnalysisResult` contains ordered acts, scenes, characters, appearances, ambiguity metadata, parser/schema versions, and visualization inputs. The API exposes `POST /api/analyses` for URL or PDF submission and `GET /api/analyses/{id}` for progress, ready results, or actionable rejection. CSV may be generated in-browser and can also be exposed as a convenience endpoint. See [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), and [quickstart.md](quickstart.md).

## Post-Design Constitution Check

Pass. The design keeps the parser independently testable, makes all interpretation and visualization inputs deterministic, shares one result contract between table and plot, preserves ambiguity, and includes the required test, accessibility, and performance validation paths. No complexity exception is required.
