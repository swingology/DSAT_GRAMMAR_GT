# Plan: OCR Strategy Benchmark Endpoint

## Context

The OCR integration (Phases 1–8) wired two strategies into the ingest pipeline: **DeepSeek OCR-2** (text extraction → Pass 1) and **Ollama VLM** (fused extraction, skips Pass 1). This plan adds a benchmark endpoint that uploads a single scanned file, runs both strategies, and returns side-by-side results: OCR quality, extraction accuracy, and latency.

One confirmed bug must be fixed first: the Pass 1 LLM extraction overwrites `pass1_json` entirely, silently dropping the `_ocr_meta` that was stored there by the DeepSeek OCR path. Any benchmark timing or provenance audit would be incomplete without this fix.

---

## Data flow

```
POST /ingest/benchmark/ocr
        │
        ├─── _create_ingest_job(strategy="deepseek") ──► QuestionJob A (comparison_group_id)
        │                                                        │
        └─── _create_ingest_job(strategy="ollama")  ──► QuestionJob B (comparison_group_id)
                                                                 │
        asyncio.gather(_run_pipeline_with_session(A),            │
                       _run_pipeline_with_session(B))  ◄─────────┘
                │
                ▼
GET /ingest/benchmark/ocr/{comparison_group_id}
        │
        └─► query QuestionJob WHERE comparison_group_id = X
                └─► OCRBenchmarkResponse {results: [OCRJobResult, OCRJobResult], ready: bool}
```

---

## Part 1 — Bug fix: preserve `_ocr_meta` through Pass 1

**File:** `backend/app/routers/ingest.py` — inside `_run_pipeline()`

Before the Pass 1 `provider.complete()` call:
```python
# Preserve OCR provenance; pass1_json is about to be overwritten by LLM extraction
ocr_meta = (job.pass1_json or {}).get("_ocr_meta")
```

After `job.pass1_json = {**extract_root, "_llm_meta": {...}}`:
```python
if ocr_meta:
    job.pass1_json["_ocr_meta"] = ocr_meta
```

Two lines, no new logic. No DB schema change needed — `pass1_json` is already a JSON column.

---

## Part 2 — Database schema: add `comparison_group_id` to `QuestionJob`

**This is missing from the draft.** The GET endpoint queries jobs by `comparison_group_id`, so the column must exist on `QuestionJob`.

**File:** `backend/app/models/question_job.py` (or wherever `QuestionJob` is defined):
```python
comparison_group_id: str | None = Field(default=None, index=True)
```

**Migration file** (e.g. `backend/alembic/versions/XXXX_add_comparison_group_id.py`):
```python
op.add_column('question_jobs',
    sa.Column('comparison_group_id', sa.String(), nullable=True, index=True))
```

The `ocr_strategy` field likely already exists on `QuestionJob` (used by the existing ingest pipeline). If it does not, add it the same way.

---

## Part 3 — Add `@with_retry` to OCR providers

**File:** `backend/app/llm/ollama_provider.py`

`complete_vision()` is an async method. Decorate it:
```python
@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
async def complete_vision(self, ...):
```

**File:** `backend/app/parsers/ocr.py`

`extract()` may be a standalone async function or a method on an `OCRExtractor` class. If it is a plain function, `@with_retry` must either work as a plain function decorator or you need to wrap the call site instead. Check the decorator signature — if it is implemented as `functools.wraps` over `async def`, it works on both.

```python
from app.llm.retry import with_retry

@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
async def extract(...):
```

---

## Part 4 — Response models

**File:** `backend/app/models/payload.py`

```python
class OCRJobResult(BaseModel):
    job_id: str
    strategy: str                  # "deepseek" | "ollama"
    status: str                    # "approved" | "failed" | "needs_review" | "pending" | ...
    ocr_meta: dict | None          # _ocr_meta from pass1_json (DeepSeek: timings/model; Ollama: None)
    llm_meta: dict | None          # _llm_meta from pass1_json (Pass 1 LLM timings; DeepSeek path only)
    questions_found: int
    questions: list[dict]          # from pass2_json — final extracted questions
    raw_text_preview: str | None   # first 500 chars of OCR text (DeepSeek path); None for Ollama
    validation_errors: list[dict]  # from job.validation_errors or pass2_json["errors"]

class OCRBenchmarkResponse(BaseModel):
    comparison_group_id: str
    results: list[OCRJobResult]
    ready: bool  # True when all jobs are in terminal state
```

**Note on `questions` source:** `pass1_json` holds raw extracted text (DeepSeek) or a fused extraction (Ollama). Final structured questions live in `pass2_json` (or the job's `questions` relationship). Pull `questions` from whatever field the existing status endpoint uses, not `pass1_json`.

**POST response** — use a lightweight inline model or a named one:
```python
class OCRBenchmarkStartResponse(BaseModel):
    comparison_group_id: str
    jobs: list[dict]  # [{"id": ..., "strategy": "deepseek"}, ...]
```

---

## Part 5 — New endpoints

**File:** `backend/app/routers/ingest.py`

### Refactor: extract `_create_ingest_job()`

Pull the asset-save + `QuestionJob` construction out of `ingest_unofficial_file()` into:
```python
async def _create_ingest_job(
    content: bytes,
    mime_type: str,
    filename: str,
    ocr_strategy: str,
    comparison_group_id: str | None,
    db: AsyncSession,
) -> QuestionJob:
```
`ingest_unofficial_file()` calls this helper unchanged — net behavior is the same.

### `POST /ingest/benchmark/ocr`

```python
@router.post("/benchmark/ocr", dependencies=[Depends(admin_required)])
async def benchmark_ocr(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    mime_type = file.content_type
    filename = file.filename
    group_id = str(uuid.uuid4())

    job_ds = await _create_ingest_job(content, mime_type, filename, "deepseek", group_id, db)
    job_ol = await _create_ingest_job(content, mime_type, filename, "ollama",   group_id, db)

    await asyncio.gather(
        _run_pipeline_with_session(job_ds.id),
        _run_pipeline_with_session(job_ol.id),
    )

    return OCRBenchmarkStartResponse(
        comparison_group_id=group_id,
        jobs=[
            {"id": job_ds.id, "strategy": "deepseek"},
            {"id": job_ol.id, "strategy": "ollama"},
        ],
    )
```

**Decision point:** `asyncio.gather()` fires both pipelines concurrently *within the same request*. If pipelines are long-running, this will time out the HTTP connection. If the existing `ingest_unofficial_file()` returns immediately and lets pipelines run in the background, mirror that pattern here — spawn background tasks and return `202 Accepted`.

### `GET /ingest/benchmark/ocr/{comparison_group_id}`

```python
@router.get("/benchmark/ocr/{comparison_group_id}", dependencies=[Depends(admin_required)])
async def get_benchmark_result(
    comparison_group_id: str,
    db: AsyncSession = Depends(get_db),
) -> OCRBenchmarkResponse:
    jobs = await db.execute(
        select(QuestionJob).where(QuestionJob.comparison_group_id == comparison_group_id)
    )
    jobs = jobs.scalars().all()
    if not jobs:
        raise HTTPException(status_code=404)

    terminal = {"approved", "failed", "needs_review"}
    results = [_build_ocr_job_result(j) for j in jobs]
    ready = all(r.status in terminal for r in results)
    return OCRBenchmarkResponse(comparison_group_id=comparison_group_id, results=results, ready=ready)
```

Extract `_build_ocr_job_result(job) -> OCRJobResult` as a private helper to keep the endpoint body clean.

---

## Files to modify

| File | Change |
|---|---|
| `backend/app/routers/ingest.py` | Part 1 bug fix; Part 5 refactor + 2 new endpoints |
| `backend/app/models/question_job.py` | Add `comparison_group_id` column (and `ocr_strategy` if missing) |
| `backend/alembic/versions/XXXX_add_comparison_group_id.py` | New migration |
| `backend/app/llm/ollama_provider.py` | `@with_retry` on `complete_vision()` |
| `backend/app/parsers/ocr.py` | `@with_retry` on `extract()` |
| `backend/app/models/payload.py` | Add `OCRJobResult`, `OCRBenchmarkResponse`, `OCRBenchmarkStartResponse` |
| `backend/tests/test_ocr.py` | Benchmark endpoint tests (status polling, result shape) |
| `backend/tests/test_ingest_router.py` | Test `_ocr_meta` preservation after Pass 1 |

---

## Open question before implementation

**Background vs. synchronous pipelines:** Does `ingest_unofficial_file()` currently return immediately (fire-and-forget via `BackgroundTasks` or similar) or block until the pipeline completes? The benchmark POST must match this pattern. If it is background, the POST returns `202 Accepted` with the `comparison_group_id` and the caller polls with GET. The `asyncio.gather()` pattern above is only correct if pipelines are awaited synchronously.

---

## Verification

```bash
# 1. Run migrations
cd backend && alembic upgrade head

# 2. Run full test suite — should stay at 197+ passed
uv run pytest -x -q

# 3. Manual smoke test (requires live DeepSeek + Ollama)
curl -X POST http://localhost:8000/ingest/benchmark/ocr \
  -H "X-API-Key: admin-key" \
  -F "file=@scanned_test.pdf"
# Returns: {"comparison_group_id": "...", "jobs": [...]}

# 4. Poll until ready=true
curl http://localhost:8000/ingest/benchmark/ocr/<comparison_group_id> \
  -H "X-API-Key: admin-key"
# Expect: ready=true, both results present, ocr_meta populated for deepseek result
```
