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
│   └── api.py
└── tests/
    ├── fixtures/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── package.json
├── vite.config.ts
├── src/
│   ├── api.ts
│   ├── state.ts
│   ├── render-table.ts
│   ├── render-visualization.ts
│   └── main.ts
└── tests/
    ├── unit/
    └── visual/
```

**Structure Decision**: Use separate `backend/` and `frontend/` projects. The backend owns acquisition, text extraction, deterministic parsing, domain models, visualization data, and API contracts. The frontend is a thin renderer and interaction layer based on `mockup_copilot_1`; it receives one `AnalysisResult` and derives both the table and SVG from that result. The source tree above is the planned implementation layout; the current repository contains the spec and mockups only.

## Phase 0 Research Summary

- Use FastAPI/Pydantic for typed HTTP boundaries and a standalone Python parser library.
- Use guarded `httpx` retrieval, BeautifulSoup HTML extraction, and `pypdf` selectable-text extraction.
- Use explicit rule-based parsing with ambiguity metadata, not probabilistic inference.
- Use vanilla TypeScript/Vite and adapt the existing mockup; import only the mockup 2 draw animation.
- Validate with golden fixtures, API tests, deterministic invariants, coverage enforcement, and Playwright visual/accessibility checks.

## Phase 1 Design Summary

The shared `AnalysisResult` contains ordered acts, scenes, characters, appearances, ambiguity metadata, parser/schema versions, and visualization inputs. The API exposes `POST /api/analyses` for URL or PDF submission and `GET /api/analyses/{id}` for progress, ready results, or actionable rejection. CSV may be generated in-browser and can also be exposed as a convenience endpoint. See [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), and [quickstart.md](quickstart.md).

## Post-Design Constitution Check

Pass. The design keeps the parser independently testable, makes all interpretation and visualization inputs deterministic, shares one result contract between table and plot, preserves ambiguity, and includes the required test, accessibility, and performance validation paths. No complexity exception is required.
