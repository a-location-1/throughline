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

The backend accepts inputs up to 10 MB and 200 PDF pages. Submitted source bytes and results are session-only and expire from memory.
