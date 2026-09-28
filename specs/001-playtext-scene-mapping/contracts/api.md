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

Ready response returns `AnalysisResult` as defined in [data-model.md](../data-model.md). Rejected response:

```json
{"analysis_id":"a_opaque_id","state":"rejected","error":{"code":"NO_PLAYTEXT_STRUCTURE","message":"We could not identify scenes or speakers in this source.","next_action":"Try a text-based play PDF or another public URL."}}
```

The API must use stable ordering and explicit schema/parser versions. Unknown analysis IDs return `404` without disclosing source details.

## CSV export

`GET /analyses/{analysis_id}/csv` may be implemented as a convenience endpoint. The browser must also be able to generate the CSV from `AnalysisResult`. CSV columns are character identity, scene IDs/labels, presence type, and line counts, with safe escaping and deterministic row/column order.
