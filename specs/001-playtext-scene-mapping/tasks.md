---

description: "Task list for implementing Playtext Scene Mapping"
---

# Tasks: Playtext Scene Mapping

**Input**: Design documents from `/specs/001-playtext-scene-mapping/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api.md`, `quickstart.md`

**Testing**: Tests are included because the constitution requires unit, boundary, invalid-input, regression, contract, rendering, accessibility, and coverage validation.

**Path conventions**: Backend code and tests live under `backend/`; frontend code and tests live under `frontend/`.

## Phase 1: Setup

**Purpose**: Establish the separate Python backend and Vite/TypeScript frontend projects.

- [ ] T001 Create the backend package structure from `plan.md` under `backend/src/throughline/` and `backend/tests/`
- [ ] T002 [P] Create the frontend Vite/TypeScript structure under `frontend/src/` and `frontend/tests/`
- [ ] T003 [P] Define backend dependencies and test tooling in `backend/pyproject.toml` for Python 3.11+, FastAPI, Pydantic, httpx, pypdf, BeautifulSoup, pytest, pytest-cov, and coverage above 80%
- [ ] T004 [P] Define frontend scripts and dependencies in `frontend/package.json` for Vite, TypeScript, unit tests, build, and Playwright end-to-end tests
- [ ] T005 [P] Configure backend linting, formatting, pytest, and coverage settings in `backend/pyproject.toml`
- [ ] T006 [P] Configure TypeScript, Vite, and test/build settings in `frontend/tsconfig.json`, `frontend/vite.config.ts`, and `frontend/package.json`
- [ ] T007 [P] Copy the approved mockup 1 visual structure and responsive styles into `frontend/index.html` and `frontend/src/styles.css`, preserving the supported-scope statement and replacing seeded result content with render targets

---

## Phase 2: Foundational

**Purpose**: Implement the shared typed contract, bounded processing, and fixture harness that every story depends on.

**Critical**: User story work begins only after this phase is complete.

- [ ] T008 Define Pydantic domain models and enums for submissions, acts, scenes, characters, appearances, analysis results, progress, failures, ambiguity, and visualization inputs in `backend/src/throughline/models.py`; enforce exactly one source method, `source_kind` values `url`/`pdf`, states `queued`/`retrieving`/`extracting`/`parsing`/`ready`/`rejected`, source size `<= 10 MB`, page count `<= 200`, zero lines for `non_speaking`, and stable schema/parser versions
- [ ] T009 [P] Define the shared TypeScript interfaces and API response discriminated unions matching `contracts/api.md` and `data-model.md` in `frontend/src/api.ts`
- [ ] T010 [P] Implement deterministic canonical serialization, stable IDs, first-appearance ordering, and invariant checks in `backend/src/throughline/models.py` and `backend/tests/unit/test_models.py`
- [ ] T011 [P] Create the manifest-backed fixture harness and canonical expected-result comparison in `backend/tests/conftest.py` and `backend/tests/integration/test_fixture_corpus.py`
- [ ] T012 [P] Add fixture manifest schema and initial fixture directory structure under `backend/tests/fixtures/{sources,expected,valid,invalid}` in `backend/tests/fixtures/manifest.json`, including an `accessibility-and-resources` category entry
- [ ] T013 Implement bounded in-memory analysis state, opaque IDs, short session TTL, state transitions, cleanup, concurrent-analysis limits, and submission rate limiting or equivalent deployment protection in `backend/src/throughline/state.py`; add unit coverage in `backend/tests/unit/test_state.py`
- [ ] T014 Implement API error envelopes, generic user-facing failure codes, logging redaction, and next-action mapping in `backend/src/throughline/errors.py` and `backend/src/throughline/logging.py`; add unit coverage in `backend/tests/unit/test_errors.py` and `backend/tests/unit/test_logging.py`
- [ ] T015 [P] Add shared frontend state transitions, polling cancellation, reset cleanup, and `aria-live` status state in `frontend/src/state.ts`
- [ ] T016 [P] Add a backend test command and frontend test/build command documented in `backend/README.md` and `frontend/README.md`

**Checkpoint**: Typed contracts, bounded state, fixture loading, and test commands are ready; user stories can proceed independently.

---

## Phase 3: User Story 1 - Generate a character-by-scene overview (Priority: P1) 🎯 MVP

**Goal**: Accept a public URL or selectable-text PDF and produce reliable ordered acts, scenes, characters, appearances, and line counts.

**Independent Test**: Run the fixture corpus and submit one representative URL and PDF through the API; verify acts/scenes, first-appearance character order, speaking and non-speaking appearances, line counts, unnamed speakers, and actionable rejection behavior.

### Tests for User Story 1

- [ ] T017 [P] [US1] Add golden sources and expected `AnalysisResult` files for explicit acts/scenes, one-act/no-scene-breaks, scene-breaks/no-acts, no-breaks recognizable play, and single-speaker cases under `backend/tests/fixtures/sources/` and `backend/tests/fixtures/expected/`
- [ ] T018 [P] [US1] Add golden sources and expected outputs for unnamed speakers, collective speakers, silent presence, name variation, Unicode/diacritics, group references, repeated headings, unsupported scope, and accessibility/resource conditions under `backend/tests/fixtures/sources/` and `backend/tests/fixtures/expected/`; record category and provenance in `backend/tests/fixtures/manifest.json`
- [ ] T019 [P] [US1] Add invalid and hostile-input fixtures for empty, malformed, unreadable, non-playtext, image-only PDF, over-page-limit, and over-byte-limit cases under `backend/tests/fixtures/invalid/` and `backend/tests/fixtures/expected/`
- [ ] T020 [P] [US1] Add parser unit tests and parameterized fixture regression/invariant assertions for scene order, unique IDs, first-appearance order, ambiguity preservation, collective/unnamed retention, and non-speaking line count in `backend/tests/unit/test_parser.py` and `backend/tests/integration/test_fixture_corpus.py`
- [ ] T021 [P] [US1] Add acquisition and extraction boundary tests for invalid schemes, embedded credentials, private/loopback/link-local/multicast/metadata addresses, unsafe redirects, timeouts, content type, 10 MB streaming limit, PDF signature, and 200-page limit in `backend/tests/unit/test_acquisition.py` and `backend/tests/unit/test_extraction.py`

### Implementation for User Story 1

- [ ] T022 [P] [US1] Implement guarded URL retrieval with HTTP/HTTPS-only validation, DNS/IP SSRF checks before every request and redirect, bounded redirects, connection/read/total timeouts, streaming byte limits, cancellation, and redacted errors in `backend/src/throughline/acquisition.py`
- [ ] T023 [P] [US1] Implement PDF validation and selectable-text extraction with trusted file signatures, temporary generated filenames, patched `pypdf`, page/text/resource limits, cleanup on success/failure, and image-only rejection in `backend/src/throughline/extraction.py`
- [ ] T024 [P] [US1] Implement HTML text extraction with BeautifulSoup, source metadata normalization, and no submitted HTML retention or injection in `backend/src/throughline/extraction.py`
- [ ] T025 [US1] Implement act and scene heading recognition and normalization in `backend/src/throughline/parser.py`
- [ ] T026 [US1] Implement ordered act/scene segmentation with one-act fallback, scene-only default act, no-break single-scene recognition, and fallback labels in `backend/src/throughline/parser.py`
- [ ] T027 [US1] Implement repeated-heading suppression, stable act/scene IDs, and normalized source spans in `backend/src/throughline/parser.py`
- [ ] T028 [US1] Implement deterministic speaker-block detection and classification for named, unnamed, collective, indeterminate, and silent speakers in `backend/src/throughline/parser.py`
- [ ] T029 [US1] Implement conservative speaker identity normalization and display preservation in `backend/src/throughline/parser.py`, including Unicode, diacritics, punctuation, capitalization, honorifics, ambiguity metadata, and no inferred demographic attributes
- [ ] T030 [US1] Aggregate parsed speaker blocks by scene and count identifiable spoken lines while excluding stage directions in `backend/src/throughline/parser.py`
- [ ] T031 [US1] Classify speaking versus non-speaking presence, preserve collective/unnamed line counts, attach supported/ambiguous confidence, and generate first-appearance character ordering in `backend/src/throughline/parser.py`
- [ ] T032 [US1] Implement library orchestration and rejection when the source lacks both usable playtext structure and at least one character/speaker in `backend/src/throughline/parser.py`
- [ ] T033 [US1] Implement `POST /api/analyses` for URL JSON and PDF multipart requests plus `GET /api/analyses/{analysis_id}` progress, ready, rejected, and unknown-ID responses in `backend/src/throughline/api.py`
- [ ] T034 [US1] Add FastAPI contract tests for URL/PDF submission, queued-to-ready progress, serialized `AnalysisResult`, stable error envelopes, opaque IDs, and `404` behavior in `backend/tests/contract/test_api.py`

**Checkpoint**: The P1 analysis result is independently usable from either source method and all parser distinctions are covered by fixtures.

---

## Phase 4: User Story 2 - Explore character reappearances (Priority: P2)

**Goal**: Show deterministic character reappearances across ordered scenes in a plot and a consistent table using one shared `AnalysisResult`.

**Independent Test**: Render a fixture with repeated and non-speaking appearances; verify scene order, first-appearance character order, deterministic colors/layout inputs, speaking/non-speaking/absence distinctions, and byte-identical repeated results.

### Tests for User Story 2

- [ ] T035 [P] [US2] Add visualization-data invariant tests for scene order, first-appearance order, deterministic color assignment, layout inputs, and table/plot appearance agreement in `backend/tests/unit/test_visualization.py`
- [ ] T036 [P] [US2] Add frontend state and table-render tests for real HTML table semantics, scene line-count sorting, accessible presence text, narrow-screen scrolling, and shared-result derivation in `frontend/tests/unit/render-table.test.ts`
- [ ] T037 [P] [US2] Add frontend SVG-render tests for speaking/non-speaking/absence encodings, labels, text summary, deterministic geometry, and reduced-motion geometry preservation in `frontend/tests/unit/render-visualization.test.ts`

### Implementation for User Story 2

- [ ] T038 [US2] Implement deterministic visualization inputs, color assignments, scene/character ordering, and line-count sort support in `backend/src/throughline/visualization.py`
- [ ] T039 [US2] Implement result-driven responsive character-by-scene table rendering with captions/header associations, speaking/non-speaking text alternatives, scene sorting, and accessible status text in `frontend/src/render-table.ts`
- [ ] T040 [US2] Implement result-driven SVG reappearance visualization with scene order, first-appearance ordering, speaking/non-speaking/absence labels or patterns, concise text summary, and mockup 2 draw animation only in `frontend/src/render-visualization.ts`
- [ ] T041 [US2] Implement the plot/table switch with selected-state semantics, keyboard operation, shared `AnalysisResult` state, and no client-side re-inference in `frontend/src/main.ts`
- [ ] T042 [US2] Add deterministic repeated-run assertions comparing canonical JSON, appearance data, IDs, colors, and visualization layout inputs in `backend/tests/integration/test_determinism.py`

**Checkpoint**: The table and plot are independently reviewable and provably derived from the same deterministic result contract.

---

## Phase 5: User Story 3 - Review, share, and recover from processing outcomes (Priority: P3)

**Goal**: Provide meaningful progress, recovery, copy, and safe CSV export for completed and failed analyses.

**Independent Test**: Exercise valid, invalid, unsupported, inaccessible, and reset flows in a browser; verify progress announcements, actionable errors, copy feedback, deterministic parseable CSV, and source/result cleanup.

### Tests for User Story 3

- [ ] T043 [P] [US3] Add frontend API/state tests for progress polling, cancellation, ready/rejected states, retry/replace-source actions, reset cleanup, and `aria-live` announcements in `frontend/tests/unit/state.test.ts`
- [ ] T044 [P] [US3] Add CSV tests for deterministic row/column order, quoting, formula-leading value escaping, collective/unnamed names, and parseability in `frontend/tests/unit/csv.test.ts`
- [ ] T045 [P] [US3] Add API tests for copy/export metadata, cleanup after reset/expiry, redacted logs, rate/concurrency limits, and generic retrieval/parsing failures in `backend/tests/contract/test_api_outcomes.py`

### Implementation for User Story 3

- [ ] T046 [US3] Implement progress-stage polling and cancellation from queued through retrieving/extracting/parsing to ready/rejected in `frontend/src/api.ts` and `frontend/src/state.ts`
- [ ] T047 [US3] Implement accessible source submission UI for URL/PDF, validation, progress, error summary focus, retry/replace actions, and supported English/Latin-script scope messaging in `frontend/src/main.ts` and `frontend/index.html`
- [ ] T048 [US3] Implement deterministic browser CSV generation for character identity, scene IDs/labels, presence type, and line counts with CSV quoting and formula-leading value escaping in `frontend/src/csv.ts`
- [ ] T049 [US3] Implement copy of the table and visualization summary plus success/failure announcements and download action wiring in `frontend/src/main.ts`
- [ ] T050 [US3] Implement optional `GET /api/analyses/{analysis_id}/csv` convenience export with the same safe escaping and deterministic ordering in `backend/src/throughline/api.py`
- [ ] T051 [US3] Implement page-leave/reset cleanup so submitted source bytes, temporary files, polling, and in-memory results are not retained beyond the session TTL in `frontend/src/main.ts` and `backend/src/throughline/state.py`

**Checkpoint**: Users can understand processing, recover from failures, and copy/download a completed result without confusing an incomplete result for success.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete workflow against accessibility, responsive behavior, performance, security, documentation, and release gates.

- [ ] T052 [P] Add Playwright scenarios for loading, ready, table, visualization, invalid/error, keyboard-only, screen-reader semantics, reduced motion, contrast, zoom/reflow, mobile touch targets, and responsive table/plot scrolling in `frontend/tests/visual/playwright.spec.ts`
- [ ] T053 [P] Add Playwright resource scenarios for slow connections, 200-page/10 MB supported inputs, modest-device responsiveness, cancellation, and no-hover operation in `frontend/tests/visual/resource.spec.ts`
- [ ] T054 [P] Add backend benchmark coverage for representative parsing and visualization workloads, reporting scene detection and character identification separately by fixture category in `backend/tests/integration/test_benchmarks.py`
- [ ] T055 [P] Add security and accessibility documentation, supported-scope limitations, normalization/line-count definitions, fixture provenance, and known unsupported input behavior in `README.md`, `backend/README.md`, and `frontend/README.md`
- [ ] T056 Run the documented quickstart validation from `specs/001-playtext-scene-mapping/quickstart.md`, including `pytest --cov=throughline --cov-fail-under=81`, frontend tests/build, and Playwright tests in `backend/README.md` and `frontend/README.md`
- [ ] T057 Create and verify the CI workflow in `.github/workflows/ci.yml` so every fixture category and accessibility/resource category is reported separately, coverage stays above 80%, deterministic-output checks pass, and no aggregate metric masks a category failure

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; T002-T007 can run in parallel after the project directories exist.
- **Phase 2 (Foundational)**: Depends on Phase 1; T009-T012 and T015-T016 can run in parallel, while T013-T014 depend on the shared model decisions in T008.
- **Phase 3 (US1)**: Depends on Phase 2; acquisition/extraction/parser work can proceed in parallel after T008, while API integration depends on T013-T014 and parser implementation.
- **Phase 4 (US2)**: Depends on the P1 `AnalysisResult` contract and parser output; backend visualization and frontend rendering tests/implementation can proceed in parallel after T034.
- **Phase 5 (US3)**: Depends on the API states from US1 and result/rendering contract from US2; frontend outcome work and backend outcome tests can proceed in parallel.
- **Phase 6 (Polish)**: Depends on the desired stories being complete; browser, benchmark, documentation, and CI work can proceed in parallel before the final quickstart gate.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 and is the MVP; no dependency on another user story.
- **US2 (P2)**: Starts after Phase 2 but requires the stable `AnalysisResult` and API response produced by US1; it remains independently testable from fixture results.
- **US3 (P3)**: Starts after Phase 2 and uses US1 processing states plus US2 result data; it remains independently testable through mocked API outcomes and completed fixtures.

### Parallel Opportunities

- Setup tasks T002-T007 can run in parallel by file ownership.
- Fixture creation T017-T019, acquisition tests T021, and model/API scaffolding can run in parallel after the contract is agreed.
- US1 acquisition, extraction, fixture authoring, and model/parser test work can run in parallel; parser integration follows their contracts.
- US2 backend visualization and frontend renderer work can run in parallel once the result schema exists.
- US3 frontend outcome work, CSV tests, and backend outcome tests can run in parallel.
- Polish browser scenarios, benchmarks, and documentation can run in parallel.

## Parallel Example: User Story 1

```text
Developer A: T017-T020, build the golden fixture corpus and parser invariants.
Developer B: T021-T024, implement acquisition and text/PDF extraction with boundary tests.
Developer C: T025-T032, implement deterministic acts, scenes, speakers, and appearances.
Developer D: T033-T034, wire and test the FastAPI contract after the shared models are available.
```

## Parallel Example: User Story 2

```text
Developer A: T035 and T038, implement and test deterministic visualization inputs.
Developer B: T036 and T039, implement and test the accessible table renderer.
Developer C: T037 and T040-T041, implement and test SVG rendering and view switching.
```

## Parallel Example: User Story 3

```text
Developer A: T043 and T046-T047, implement progress, errors, retry, and accessible submission UI.
Developer B: T044 and T048-T049, implement and test copy and safe CSV download.
Developer C: T045 and T050-T051, implement API outcome handling and lifecycle cleanup.
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational contracts, state, fixtures, and test harness.
3. Complete Phase 3 US1 acquisition, extraction, deterministic parser, and API.
4. Run the fixture corpus and API contract tests independently.
5. Stop for MVP review before adding visualization and sharing workflows.

### Incremental Delivery

1. Deliver Setup + Foundational as the executable project foundation.
2. Deliver US1 as the analysis MVP.
3. Deliver US2 as the deterministic table/visualization increment.
4. Deliver US3 as the progress, recovery, copy, and CSV increment.
5. Run Phase 6 release gates after each increment that changes parser, rendering, accessibility, or performance behavior.

## Format Validation

All implementation tasks use the required `- [ ] T###` checklist format. Setup, foundational, and polish tasks omit story labels; all user-story tasks include `[US1]`, `[US2]`, or `[US3]`. `[P]` appears only on tasks designed for parallel execution. Every task includes one or more concrete file paths.
