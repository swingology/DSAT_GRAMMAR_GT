# DSAT Grammar Backend — Gap Audit Report

Generated: 2026-04-24

---

## CRITICAL — Will break at runtime

### 1. ORM enum name mismatch — `Question` and `QuestionAsset` tables unusable

The migration creates the PG enum type as `content_origin_enum`, but the ORM models use inconsistent names:

| ORM Model | Enum Name | DB Type Exists? |
|-----------|-----------|-----------------|
| `QuestionJob.content_origin` | `content_origin_enum` | ✅ Yes |
| `Question.content_origin` | `content_origin_enum2` | ❌ No |
| `QuestionAsset.content_origin` | `content_origin_enum3` | ❌ No |

When asyncpg resolves these type names at query time, `content_origin_enum2` and `content_origin_enum3` won't be found in `pg_type`. This means any ORM operation against `questions` or `question_assets` tables will fail.

**Fix:** Change the `name` parameter in `app/models/db.py` lines 49 and 151 to `"content_origin_enum"` to match the database.

### 2. Ingest pipeline never creates question rows

`app/routers/ingest.py` — `_run_pipeline` extracts and annotates via LLM, but never persists the results into `questions`, `question_options`, `question_annotations`, or `question_versions`. After a job reaches `"approved"`, there is no corresponding question row. The entire pipeline runs to completion and produces nothing.

**Fix:** After validation passes, `_run_pipeline` must create `Question`, `QuestionOption`, `QuestionAnnotation`, and `QuestionVersion` rows, then update `Job.question_id`.

### 3. Generate pipeline creates orphaned Question

`app/routers/generate.py:67-86` — `_run_generate_pipeline` creates a bare `Question` row but never creates `QuestionVersion`, `QuestionAnnotation`, or `QuestionOption` rows. The question has no options, no annotation metadata, and no version history.

**Fix:** After creating the `Question`, create `QuestionOption` rows from `generated["options"]`, a `QuestionAnnotation` from `annotate_json`, and a `QuestionVersion`.

### 4. Python-side filtering breaks pagination

`app/routers/questions.py:25-44` and `app/routers/student.py:27-59` — Both `recall` endpoints apply `grammar_focus`, `difficulty`, and `origin` filters in Python **after** fetching a fixed SQL `LIMIT`. Requesting `limit=20` may return 0 items if all 20 fetched rows are filtered out. The client receives an empty page with no way to paginate further.

**Fix:** Move filtering into the SQL query with WHERE clauses, or paginate the already-filtered dataset.

### 5. CORS security misconfiguration

`app/main.py:18-19` — `allow_origins=["*"]` with `allow_credentials=True`. Browsers reject this combination per the CORS spec. The `Access-Control-Allow-Origin: *` response will never include `Access-Control-Allow-Credentials: true`.

**Fix:** Either remove `allow_credentials=True` or specify explicit origins instead of `*`.

### 6. Alembic downgrade raises NameError

`migrations/versions/001_initial_schema.py:265-267` — `downgrade()` references `enums` which is a local variable defined only inside `upgrade()`. Running `alembic downgrade` will crash with `NameError: name 'enums' is not defined`.

**Fix:** Move the `enums` list to module level so both `upgrade()` and `downgrade()` can access it.

---

## HIGH — Functional bugs

### 7. Ingest pipeline ignores job's provider_name

`app/routers/ingest.py:36-38` — `_run_pipeline` uses `settings.default_annotation_provider` instead of `job.provider_name`. The `provider_name` and `model_name` passed by the user via Form parameters are stored in the Job but never read back. The generate pipeline (`generate.py:27`) correctly uses `job.provider_name`.

**Fix:** Change `_run_pipeline` to use `job.provider_name` and `job.model_name`.

### 8. Admin edit loses option data

`app/routers/admin.py:50` — `edit_question` hardcodes `choices_jsonb=[]` in the new `QuestionVersion` instead of serializing the question's actual current options. Also never updates `Question.latest_version_id`.

**Fix:** Populate `choices_jsonb` from the question's current `QuestionOption` rows, and update `q.latest_version_id` after adding the new version.

### 9. Wrong field mapping in questions router

`app/routers/questions.py:58` — Maps `stimulus_mode_key=q.stem_type_key` instead of `q.stimulus_mode_key`. The `stimulus_mode_key` in the response will contain the wrong value.

**Fix:** Change to `stimulus_mode_key=q.stimulus_mode_key`.

### 10. Reannotate re-runs extraction

`app/routers/ingest.py:277-328` — The `reannotate` endpoint runs the full pipeline including Pass 1 extraction. Since it already has `pass1_json` from the existing job, it should skip extraction and go straight to annotation.

**Fix:** Create a reannotate-specific pipeline path that skips extraction and proceeds directly to annotation + validation.

### 11. QuestionAsset.question_id never populated

When assets are created during ingestion, `question_id` is not set (no question row exists yet). Even after pipeline completion, the asset is never linked back to the question.

**Fix:** When creating the `Question` row (see gap #2), update the asset's `question_id`.

### 12. `latest_annotation_id` / `latest_version_id` never updated

These FK columns on `Question` are never set by any pipeline step or admin endpoint. They remain `NULL` even after annotations and versions are created.

**Fix:** Update `q.latest_annotation_id` after creating a `QuestionAnnotation`, and `q.latest_version_id` after creating a `QuestionVersion`.

---

## MEDIUM — Design issues & missing features

### 13. No DB health check

`app/routers/health.py:6` — `GET /` returns a static `{"status": "ok"}` without verifying the database is reachable. A dead database gives a false healthy signal.

**Fix:** Add a lightweight `SELECT 1` query to verify the DB connection.

### 14. `prompt_version` inconsistency

`app/models/db.py:31` — ORM default is `"v3.0"`, but all routers hardcode `prompt_version="v1"`:
- `ingest.py:169,245,316`
- `generate.py:107,148`

The version tag doesn't reflect the actual V3 rules being used.

**Fix:** Align on a single version string, ideally from config.

### 15. File read before size check

`app/routers/ingest.py:126-128` — `await file.read()` loads the entire file into memory before the `MAX_FILE_SIZE` check. A 50MB file consumes 50MB RAM then gets checked.

**Fix:** Check `Content-Length` header before reading, or use streaming to read in chunks and abort early.

### 16. No pool_pre_ping

`app/database.py:9` — `create_async_engine` does not set `pool_pre_ping=True`. Stale database connections in the pool will cause cryptic connection errors in production.

**Fix:** Add `pool_pre_ping=True` to the engine constructor.

### 17. Missing overlap detection implementation

The `overlap_check` job type and `question_relations` table exist, but no overlap detection code is implemented anywhere. This leaves a non-functional job type.

### 18. Missing endpoints

No API endpoints exist for:
- `QuestionRelation` CRUD (despite the table and enum types existing)
- `LlmEvaluation` creation (only scoring existing evaluations via `POST /admin/evaluations/{id}/score`)
- `User` creation/management (the `users` table has no CRUD endpoints)
- Job status polling (clients submit ingest/generate jobs but have no way to poll for completion)

### 19. No retry, logging, or tracing

- LLM providers have no retry logic, rate-limit handling, or circuit breakers
- No structured logging (all log output goes to uvicorn's default logger)
- No request ID or correlation ID for tracing requests through the system

### 20. Validator is extremely minimal

`app/pipeline/validator.py` — Only checks for empty `question_text`, exactly 4 options, valid correct label, and explanation presence. Does **not** validate:
- V3 ontology keys (`grammar_focus_key`, `stimulus_mode_key`, `stem_type_key`, etc.)
- Option-level schema correctness
- That exactly one option is marked correct
- Explanation length limits (annotation schema has `max_length=300` for `explanation_short`)

---

## LOW — Cleanup & polish

### 21. `OllamaProvider.close()` exists but is never called

`app/llm/ollama_provider.py:52` — Defines `async close()` to clean up the httpx client, but no lifespan handler calls it. `AnthropicProvider` and `OpenAIProvider` also create httpx clients internally (via their SDKs) with no cleanup.

**Fix:** Add LLM client cleanup to the app lifespan in `main.py`.

### 22. `IngestPdfRequest` Pydantic model defined but unused

`app/models/payload.py:105-109` — The `IngestPdfRequest` model is defined but the ingest endpoints use `Form(...)` parameters directly instead.

### 23. Rules reference truncated at 8000 chars

`app/prompts/annotate_prompt.py:46` — The V3 rules reference is hard-truncated to 8000 characters with no smart chunking, semantic selection, or RAG fallback.

### 24. Empty `__init__.py` files

All `app/*/__init__.py` files are empty. No convenience exports are provided.

### 25. No storage backend abstraction

The `RAW_ASSET_STORAGE_BACKEND` config supports switching backends, but only `local_store.py` is implemented. No S3/GCS abstraction exists.

### 26. `manual_test.py` duplicates pipeline logic

`scripts/manual_test.py` reimplements the ingest pipeline logic instead of calling the router functions directly.

### 27. `image_parser.py` and `markdown_parser.py` unused in production

Both parsers are tested (`test_parsers.py`) but never imported by any production code — no router, pipeline, or other `app/` module calls `parse_image()` or `parse_markdown()`. The ingest router handles images and markdown inline. These files are dead code in production.

---

## Summary

| Severity | Count | Key Issues |
|----------|-------|------------|
| Critical | 6 | ORM enum name mismatch blocks all Question table access; Ingest creates no rows; Generate creates orphaned questions; Pagination broken; CORS misconfigured; Alembic downgrade crashes |
| High | 6 | Provider ignored in pipeline; Admin edit loses data; Wrong field mapping in response; Reannotate runs wrong pipeline; Asset/question_id never linked; Latest FK columns never updated |
| Medium | 8 | No DB health check; prompt_version mismatch; File read before size check; No pool_pre_ping; No overlap detection; 4 missing endpoint groups; No retry/logging/tracing; Minimal validator |
| Low | 7 | OllamaProvider cleanup never called; Unused Pydantic model; Rules truncation; Empty `__init__.py`; No storage abstraction; Duplicated test script; Dead production parsers |

**Single most impactful fix:** Correct the ORM enum names in `app/models/db.py` to match the migration — currently `Question` and `QuestionAsset` tables are completely inaccessible at runtime.

**Next priority:** Implement row creation in the ingest pipeline (gap #2) — without this, the entire ingest feature produces no data.
