# Throughline: Playtext Scene Visualizer

Throughline is a utility for charting character appearance in scenes over the course of a play. It accepts a public playtext URL or selectable-text PDF and maps character presence across acts and scenes. It preserves ambiguity, distinguishes speaking from non-speaking presence, and derives an accessible table and deterministic SVG visualization from one analysis result.

The first release supports primarily English-language, Latin-script playtexts following recognizable Western dramatic conventions. Results are a reading aid, not a definitive edition; unsupported or ambiguous structures are reported rather than silently invented.

## Run locally

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest --cov=throughline --cov-fail-under=81
uvicorn throughline.api:app --reload

cd ../frontend
npm install
npm test
npm run build
npm run dev
```

The backend accepts inputs up to 10 MB and 200 PDF pages. One synchronous analysis request returns the complete result; source bytes and results are not retained server-side. The frontend shows staged indeterminate feedback, supports cancellation, disables duplicate submissions, and generates CSV locally.

## Deploy with Vercel

The root [`vercel.json`](./vercel.json) configures `backend` and `frontend` as services in one Vercel project. The frontend is public at `/`, while backend requests are public at `/api/*`; the backend remains internal for all other paths. No service binding is required because the frontend uses same-origin `/api` requests and no service calls another service directly.

Use `vercel dev` from the repository root to run both services together locally.
