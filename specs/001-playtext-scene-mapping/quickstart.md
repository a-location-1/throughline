# Quickstart Validation

## Prerequisites

- Python 3.11+ and a virtual environment.
- Node.js 20+ and npm.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest --cov=throughline --cov-fail-under=81

cd ../frontend
npm install
npm test
npm run build
npm run test:e2e
```

Start the API with `uvicorn throughline.api:app --reload` and the frontend with `npm run dev`.

## Validation scenarios

1. Submit a representative public URL. Progress moves from queued through extraction/parsing to ready; acts, scenes, characters, table, and plot are visible.
2. Upload the equivalent selectable-text PDF. The structured result matches the URL fixture.
3. Submit one-act/no-scene, scene-only, single-speaker, unnamed-speaker, silent-presence, collective-speaker, and ambiguous-identity fixtures. Verify each expected distinction and deterministic ordering.
4. Submit empty, inaccessible, oversized, image-only, malformed, and non-playtext inputs. Verify an explanatory error and a retry/replace-source action.
5. Toggle plot/table, sort a scene by speaking line count, copy the result, and download CSV. Verify the table and plot use the same appearances and the CSV is parseable.
6. Repeat the same input twice and compare serialized result JSON, SVG geometry, IDs, colors, and ordering byte-for-byte.
7. Run Playwright at desktop and mobile widths with reduced motion enabled. Verify keyboard access, status announcements, responsive table/plot scrolling, and no visual regression.
