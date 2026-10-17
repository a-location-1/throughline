# HTTP API Contract

Base path: `/api`

## Create analysis

`POST /analyses` accepts either `{"url":"https://example.org/play.html"}` as JSON or a `multipart/form-data` request with a `file` field.

Response `200` is the complete `AnalysisResult` for either source method. Processing, retrieval, extraction, and parsing occur within the request. The server MUST NOT create a job ID, retain result state, or require a follow-up request.

The frontend MAY show staged indeterminate labels while awaiting the response, but those labels are estimates and MUST NOT be represented as server progress percentages.

Failures return a structured `detail` envelope with a stable failure code, message, and next action. Common statuses are `400`, `413`, `422`, `429`, `502`, and `504`.

## Removed polling and server CSV endpoints

`GET /analyses/{analysis_id}` and `GET /analyses/{analysis_id}/csv` are not part of the active contract. CSV is generated entirely in the browser from `AnalysisResult`, using deterministic ordering and formula-safe escaping.

The API must use stable ordering and explicit schema/parser versions. Initial hosting uses process-local sliding-window limits: 12 analysis submissions per client per 60 seconds and 60 frontend log events per client per 60 seconds. These are suitable only for one low-volume instance; multi-instance hosting requires a shared limiter or edge/WAF enforcement.
