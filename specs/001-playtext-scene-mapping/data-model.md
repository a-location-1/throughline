# Data Model

## PlaytextSubmission

- `submission_id`: opaque request identifier; session-scoped.
- `source_kind`: `url` or `pdf`.
- `source_name`: URL hostname or uploaded filename; no source body is retained.
- `page_count`: PDF page count when available.
- `byte_count`: source size.
- `state`: `queued`, `retrieving`, `extracting`, `parsing`, `ready`, or `rejected`.
- `failure`: structured code and user-facing message when rejected.
- `notices`: ordered user-visible warnings or uncertainty statements that do not prevent a best-effort result.

Validation: exactly one source method; URL must be public and retrievable; PDF must be `application/pdf` or `.pdf`; size <= 10 MB and pages <= 200.

An analysis may be `ready` with notices when conventional act, scene, or speaker attributes are unidentified, when structural evidence is unconventional, or when additional plays were found. A source is rejected only when there is insufficient combined evidence of playtext or no usable character/speaker can be identified.

## Act

- `id`: stable `act-01` style identifier.
- `ordinal`: one-based source order.
- `label`: source heading or deterministic fallback such as `Act I`.
- `scenes`: ordered scenes belonging to the act.

A play without explicit act breaks uses one act when the text is otherwise recognized as a playtext.

## Scene

- `id`: stable `scene-01` style identifier across the whole play.
- `ordinal`: one-based play order.
- `act_id`: owning act.
- `label`: source heading or deterministic fallback.
- `source_span`: normalized text offsets for diagnostics, not source retention.
- `detection`: `supported`, `uncertain`, or `unidentified`, with a reason when the source does not provide a conventional marker.

Repeated headings do not create duplicate scenes unless their normalized source spans contain distinct scene content.

## CharacterOrSpeaker

- `id`: stable slug plus collision suffix generated in first-appearance order.
- `display_name`: visible name, `Unnamed speaker`, or preserved collective/indeterminate label.
- `kind`: `named`, `unnamed`, `collective`, `indeterminate`, or `silent`.
- `first_appearance_scene_id`: first scene in which presence is supported.
- `ambiguity`: optional evidence and unresolved alternatives.

Names are normalized only when formatting differences are sufficiently supported by the source. Unsupported merges remain separate and flagged.

## SceneAppearance

- `scene_id` and `character_id`: relationship key.
- `presence`: `speaking` when at least one attributable spoken line exists, otherwise `non_speaking` when the character's presence is supported without speech.
- `line_count`: identifiable spoken lines, excluding stage directions; zero for `non_speaking` appearances.
- `confidence`: `supported` or `ambiguous` with an explanation when needed.

Presence is intentionally scene-level rather than event-level. Silent entrances, exits, or stage-direction moments in a scene that also contains speech do not produce a separate presence category.

Collective and unnamed speakers retain line counts and remain distinct from named individual characters.

## AnalysisResult

- `schema_version` and `parser_version`.
- `submission` metadata without source contents.
- ordered `acts`, `scenes`, `characters`, and `appearances`.
- ordered `notices` describing multiple-play detection and unidentified or uncertain conventional attributes.
- `ordering`: scene order, first-appearance character order, and supported scene line-count sort.
- `visualization`: ordered IDs, deterministic color assignments, and layout inputs derived from the same appearances.

State transition: `queued -> retrieving/extracting -> parsing -> ready`, or any processing state -> `rejected` with a useful next action.
