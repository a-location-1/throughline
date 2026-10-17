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

The frontend makes one synchronous `POST /api/analyses` request and receives the complete result. It shows staged indeterminate feedback, disables duplicate submission while the request is active, and cancels the request when the user clears the source. No polling or server-side CSV endpoint is used.

For separate frontend/backend deployments, set `VITE_API_ROOT` in the frontend to the backend API prefix (for example `https://api.example.com/api`) and set `FRONTEND_ORIGINS` in the backend to a comma-separated list of allowed frontend origins. The default backend origin is `http://localhost:5173`.

The initial process-local limits are 10 MB uploads, 10 MB URL responses, 200 PDF pages, 12 analysis submissions per client per 60 seconds, 60 frontend log events per client per 60 seconds, 1,000 characters per log message, and 8 KB serialized log context. These limits are enforced server-side; the browser checks are only a user experience aid.

## Validation scenarios

1. Submit a representative public URL. Staged indeterminate feedback appears while the single request runs; acts, scenes, characters, table, and plot are visible when it completes.
2. Upload the equivalent selectable-text PDF. The structured result matches the URL fixture.
3. Submit one-act/no-scene, Act I or Scene I opening excerpts, scene-only, single-speaker, unnamed-speaker, silent-presence, collective-speaker, and ambiguous-identity fixtures. Verify opening excerpts produce best-effort results with notices, while later-act or later-scene excerpts are rejected.
4. Submit empty, inaccessible, oversized, image-only, malformed, and non-playtext inputs. Verify an explanatory error and a retry/replace-source action.
5. Toggle plot/table, sort a scene by speaking line count, copy the result, and download the client-generated CSV. Verify the table and plot use the same appearances and the CSV is parseable.
6. Repeat the same input twice and compare serialized result JSON, SVG geometry, IDs, colors, and ordering byte-for-byte.
7. Run Playwright at desktop and mobile widths with reduced motion enabled. Verify keyboard access, status announcements, responsive table/plot scrolling, and no visual regression.
