# HTTP API Contract

Base path: `/api`

## Create URL analysis

`POST /analyses`

Request:

```json
{"url":"https://example.org/play.html"}
```

Response `202`:

```json
{"analysis_id":"a_opaque_id","state":"queued","progress":{"stage":"queued","percent":0}}
```

## Create PDF analysis

`POST /analyses` with `multipart/form-data`, field `file`.

Response and failure envelope match URL analysis. The server must not retain the uploaded bytes after processing/reset.

## Get analysis

`GET /analyses/{analysis_id}`

Processing response:

```json
{"analysis_id":"a_opaque_id","state":"parsing","progress":{"stage":"Identifying scenes and speakers","percent":70}}
```

Ready response returns `AnalysisResult` as defined in [data-model.md](../data-model.md). A ready response may include notices when the parser produced a best-effort result or found additional plays. Rejected response:

```json
{"analysis_id":"a_opaque_id","state":"rejected","error":{"code":"NOT_PLAYTEXT","message":"We could not establish that this source contains a playtext.","next_action":"Submit a playtext URL or a text-based play PDF."}}
```

The parser MUST reserve rejection for sources with insufficient combined evidence of playtext or no usable character/speaker. Missing conventional act, scene, or character labels MUST be represented as notices in a ready best-effort result when the source otherwise supports playtext analysis. When multiple plays are detected, the ready result MUST contain a notice and data for only the first play.
```

The API must use stable ordering and explicit schema/parser versions. Unknown analysis IDs return `404` without disclosing source details.

## CSV export

`GET /analyses/{analysis_id}/csv` may be implemented as a convenience endpoint. The browser must also be able to generate the CSV from `AnalysisResult`. CSV columns are character identity, scene IDs/labels, presence type, and line counts, with safe escaping and deterministic row/column order.
