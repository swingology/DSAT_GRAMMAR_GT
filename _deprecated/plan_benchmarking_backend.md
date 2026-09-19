# Plan: backend/benchmark Directory

## Should we do this?

**Yes.** Benchmarking is cross-cutting tooling that doesn't belong in:
- `app/` — production code only
- `tests/` — automated correctness suite, not performance/quality comparison
- `scripts/` — already has ad-hoc utilities; mixing benchmarking in muddies both

A dedicated `backend/benchmark/` directory keeps the comparison harness, results data, and lightweight dashboard self-contained and independently runnable. The existing plan to add `/ingest/benchmark/ocr` API endpoints (`wiggly-shimmying-leaf.md`) complements this — the benchmark scripts call those endpoints; the dashboard visualizes the results.

---

## Proposed Structure

```
backend/benchmark/
├── README.md                  # how to run
├── runners/
│   ├── ocr_strategy.py        # compare deepseek vs. ollama OCR on sample PDFs
│   ├── llm_provider.py        # compare anthropic vs. ollama extraction quality
│   └── ingestion_quality.py   # end-to-end: question count, validation errors, latency
├── results/                   # gitignored JSON/CSV output from runs
│   └── .gitkeep
├── fixtures/                  # small sample PDFs used as benchmark inputs
│   └── .gitkeep
└── dashboard/
    ├── index.html             # HTMX dashboard — loads results, no build step
    └── serve.py               # tiny http.server wrapper to serve dashboard locally
```

---

## Steps

### 1. Create directory skeleton
Create the directory tree above. `results/` and `fixtures/` are gitignored except for `.gitkeep`.

### 2. Implement OCR strategy runner (`runners/ocr_strategy.py`)
- Reads PDFs from `fixtures/` (or accepts a path arg)
- Calls `POST /ingest/benchmark/ocr` (from the planned API endpoint in `wiggly-shimmying-leaf.md`)
- Polls `GET /ingest/benchmark/ocr/{id}` until ready
- Writes results JSON to `results/ocr_YYYYMMDD_HHMMSS.json`

Depends on: the `_ocr_meta` bug fix and benchmark endpoint from the existing plan being implemented first.

### 3. Implement ingestion quality runner (`runners/ingestion_quality.py`)
- Runs a set of sample PDFs through the normal ingest pipeline
- Captures: questions extracted, validation error counts, pass1/pass2 latency from `_llm_meta`
- Writes CSV to `results/ingest_quality_*.csv`

No new API needed — reuses existing `/ingest/file` endpoint.

### 4. HTMX dashboard (`dashboard/index.html`)
- Static HTML + HTMX + a small inline `<script>` for chart rendering (Chart.js CDN)
- On load, fetches the latest JSON files from `results/` via `serve.py`
- Views: OCR side-by-side diff, latency bar chart, question-count over runs
- Zero build tooling — just `python benchmark/dashboard/serve.py`

### 5. Update `.gitignore`
Add `backend/benchmark/results/*.json` and `backend/benchmark/results/*.csv` (keep fixtures in git).

---

## What this is NOT

- Not a FastAPI app — the dashboard server is `http.server`, not uvicorn
- Not replacing `backend/tests/` — correctness tests stay there
- Not blocking the existing `wiggly-shimmying-leaf.md` plan — that plan's API endpoint is a prerequisite for step 2

---

## Order of work

1. Fix `_ocr_meta` bug + add benchmark endpoints (from existing plan)
2. Create directory skeleton + gitignore
3. Implement `runners/ocr_strategy.py`
4. Implement `runners/ingestion_quality.py`
5. Build HTMX dashboard
