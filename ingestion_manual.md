# Running the Ingestion Test Manually

This guide covers running the official-verbal ingestion pipeline by hand — useful
for verifying a fix against a single PDF before committing to the full 18-PDF batch
(`backend/run_full_ingestion.sh`).

## Should you run it manually?

**Yes — recommended right now.** The fixes for the all-questions-blocked cascade
(`_merge_for_validation`, `extraction_max_tokens`, the annotate/extract prompt
hardening) are currently **uncommitted** in the working tree and have **not been
re-verified** against a real run. Run one PDF manually first to confirm the fix,
then run the full batch.

A running server loads code **once at startup** — any edit to `backend/app/**`
requires a server restart (or `--reload`) to take effect.

---

## 1. Prerequisites

| Service | Expected | Check |
|---|---|---|
| PostgreSQL | `localhost:5434`, db `dsat_dev` | `PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -c '\q'` |
| Ollama | `localhost:11434` | `curl -s -o /dev/null -w '%{http_code}' http://localhost:11434/` → `200` |
| API server | `localhost:8000` | `curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/` |

If PostgreSQL is down:

```bash
cd /home/jb/DSAT_REDUX_MD
docker compose up -d db
```

Ollama must have the models from `backend/.env` pulled:
`qwen3-vl:235b-instruct-cloud` (extraction + annotation), `qwen3.0-vl` (OCR vision
fallback), `glm-ocr:latest` (layout detection).

---

## 2. Start the API server

```bash
cd /home/jb/DSAT_REDUX_MD/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`--reload` picks up source edits automatically. Leave this running in its own
terminal. Auth keys come from `backend/.env`:
`ADMIN_API_KEYS=admin-test-key`, `STUDENT_API_KEYS=student-test-key`.

---

## 3. Submit one PDF

The canonical PDFs live in
`TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/`, named
`Test_N_digital_sec01_mod01.pdf`. Metadata is parsed from the filename:
`exam=N, subject=verbal, section=01, module=01`.

```bash
cd /home/jb/DSAT_REDUX_MD/backend

PDF="../TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/Test_1_digital_sec01_mod01.pdf"

curl -s -X POST "http://localhost:8000/ingest/official/pdf" \
  -H "X-API-Key: admin-test-key" \
  -F "file=@${PDF}" \
  -F "source_exam_code=1" \
  -F "source_subject_code=verbal" \
  -F "source_section_code=01" \
  -F "source_module_code=01" | python3 -m json.tool
```

Note the `job_id` from the response.

---

## 4. Poll the job to completion

```bash
JOB_ID=<paste job_id>

watch -n 10 "curl -s -H 'X-API-Key: admin-test-key' \
  http://localhost:8000/ingest/jobs/${JOB_ID} \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[\"status\"])'"
```

Terminal statuses: `approved`, `needs_review`, `failed`.
A full module of ~27 questions can take **20+ minutes** — Pass 2 annotates each
question sequentially with a large system prompt.

---

## 5. Inspect the result

```bash
curl -s -H "X-API-Key: admin-test-key" \
  http://localhost:8000/ingest/jobs/${JOB_ID} | python3 -m json.tool
```

Or query the DB directly for validation errors (most informative):

```bash
PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -c \
  "SELECT e->>'step' AS step, count(*)
   FROM question_jobs, jsonb_array_elements(validation_errors_jsonb) e
   WHERE id='${JOB_ID}' GROUP BY 1;"

# Drill into a specific failing question
PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -c \
  "SELECT jsonb_pretty(e)
   FROM question_jobs, jsonb_array_elements(validation_errors_jsonb) e
   WHERE id='${JOB_ID}' AND e->>'step'='validating' LIMIT 1;"
```

**Fix verification:** with `_merge_for_validation` in place, the
`Option labels must be exactly {A, B, C, D}, got ['']` errors should be gone and
the job should reach `approved` or `needs_review` (not `failed` on all questions).

---

## 6. Run the full 18-PDF batch

Once a single PDF verifies clean:

```bash
cd /home/jb/DSAT_REDUX_MD/backend
./run_full_ingestion.sh
```

Per-PDF results land in `/tmp/ingestion_results/`; a pass/fail summary prints at
the end. The script submits every `Test_*_digital_sec*.pdf`, polls each (10-min
cap per job), and tallies `approved / needs_review / failed / timeout`.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `401 Unauthorized` | `X-API-Key` must match `ADMIN_API_KEYS` in `backend/.env` (`admin-test-key`). |
| `SKIP: file not found` | PDF path wrong — confirm `TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/`. |
| Job stuck `extracting` / `annotating` | Ollama slow or model not pulled; `pipeline_timeout_s=1800` aborts hung runs. |
| All questions `failed` validating with `got ['']` | Server is running **stale code** — restart it so `_merge_for_validation` loads. |
| `No valid JSON found … input_len=…` | Extraction output truncated — confirm `extraction_max_tokens` (default 32000) is applied. |
| DB connection refused | Start the `db` service: `docker compose up -d db`. |
