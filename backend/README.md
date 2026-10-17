# Throughline Backend

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest --cov=throughline --cov-fail-under=81
uvicorn throughline.api:app --reload
```

The parser is deterministic and session-only. It supports public HTTP(S) playtext URLs and selectable-text PDFs up to 10 MB and 200 pages.
URL retrieval uses the host platform's certificate trust store so publicly hosted PDFs with valid platform-trusted certificates can be read directly.

`POST /api/analyses` processes one source synchronously and returns the complete result. The frontend shows staged indeterminate feedback and uses an `AbortController`; there is no polling or server-side result history. CSV is generated in the browser.

For hosting, set `FRONTEND_ORIGINS` to comma-separated allowed frontend origins. The initial low-volume process-local limits are 12 analyses per client per minute and 60 frontend log events per client per minute. Log messages are limited to 1,000 characters and context to 8 KB. These counters are not a global control across multiple workers or instances; use a shared limiter or edge/WAF limits before scaling out.
