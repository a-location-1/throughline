# Throughline Backend

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest --cov=throughline --cov-fail-under=81
uvicorn throughline.api:app --reload
```

The parser is deterministic and session-only. It supports public HTTP(S) playtext URLs and selectable-text PDFs up to 10 MB and 200 pages.
