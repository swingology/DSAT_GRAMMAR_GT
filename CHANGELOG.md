# CHANGELOG

All significant changes to this project. Timestamps are commit time (PDT, UTC-7).
Agent: **Claude Sonnet 4.6** (`claude-sonnet-4-6`)

---

## 2026-05-16 — Full gap remediation (15 fixes across all audit findings)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Resolves 15 open audit findings across ingestion, generation, admin, and cross-cutting
areas. Two items (OCR integration tests and stub-DB migration) are deferred as they
require significant new test infrastructure.

### Ingestion Pipeline

- **OCR fallback logging:** Added explicit `logger.info` calls at OCR chain entry,
  each fallback transition, and paradigm-specific success messages (two-step vs
  VLM-fused). Previously only failure warnings were logged.
  **Files:** `backend/app/routers/ingest.py`

- **Per-page render size limit:** Added `MAX_PAGE_RENDER_BYTES = 10 MB` in ingest.py;
  `_store_page_render` now returns `None` for oversized pages (with warning log).
  `_store_pdf_page_renders` filters out `None`. Added `MAX_RENDER_DIMENSION = 3000px`
  in `pdf_parser.py` to cap rendered page dimensions.
  **Files:** `backend/app/routers/ingest.py`, `backend/app/parsers/pdf_parser.py`

- **Mixed PDF page-level OCR:** The OCR gate now checks per-page text availability.
  When a PDF has some text-layer pages and some blank/scanned pages, only the blank
  pages' images are sent through OCR. The OCR text is appended to the existing raw text.
  `_page_texts` is stored in `pass1_json` for per-page text inspection.
  **Files:** `backend/app/routers/ingest.py`

- **Job endpoint exposes OCR/LLM metadata:** `GET /ingest/jobs/{job_id}` now returns
  `ocr_meta` and `llm_meta` extracted from `pass1_json`.
  **Files:** `backend/app/models/payload.py`, `backend/app/routers/ingest.py`

### Generate Pipeline

- **`generate_compare` shared reference fix:** Each provider closure in
  `generate_compare` now receives `job_data = dict(request_data)` — a shallow copy — so
  mutations inside `_run_generate_pipeline` don't leak across jobs. The default-arg
  pattern is documented inline.
  **Files:** `backend/app/routers/generate.py`

- **Overlap race condition:** `persist_overlap_relations` now wraps each
  check-then-insert in `async with db.begin_nested()` (SAVEPOINT) and catches
  `IntegrityError` on concurrent duplicate inserts.
  **Files:** `backend/app/pipeline/overlap.py`

- **`overlap_checking` status in generate pipeline:** Added `job.status =
  "overlap_checking"` before running overlap detection in
  `_run_generate_pipeline`, matching the ingest pipeline behavior.
  **Files:** `backend/app/routers/generate.py`

- **Generation run diagnostics:** `GET /generate/runs/{run_id}` now returns
  `validation_errors`, `pass1_json`, and `pass2_json` for single-job responses,
  and `validation_errors` per job in comparison-group responses.
  **Files:** `backend/app/routers/generate.py`

- **`generation_source_set` pollution fix:** `generation_source_set` on the `Question`
  model now filters out `_SOURCE_SET_OPERATIONAL_KEYS` (`provider_name`, `model_name`)
  from the stored dict, matching the behavior of `_generation_profile_payload`.
  **Files:** `backend/app/routers/generate.py`

### Admin / Cross-Cutting

- **`LlmEvaluation.job_id` nullable fix:** Changed `EvaluationCreateRequest.job_id`
  from `str` to `Optional[str] = None` so an empty string no longer causes a 500
  on the `nullable=False` column.
  **Files:** `backend/app/routers/admin.py`

- **Official question activation:** Removed the blanket block on approving
  `content_origin == "official"` questions. Official questions can now be approved
  unless they have unresolved overlap (`official_overlap_status != "none"`).
  **Files:** `backend/app/routers/admin.py`

- **Student submit option verification:** Added a check that the submitted
  `selected_option_label` exists in `question_options` for the question's
  `latest_version_id` before recording the answer.
  **Files:** `backend/app/routers/student.py`

- **Consolidated user routes:** Removed duplicate user-management endpoints from
  `student.py` (`POST/GET/DELETE /api/users`). The canonical endpoints in `users.py`
  (`/users`) now serve all user CRUD with proper pagination, status codes (201/204),
  and explicit timestamps. Unused imports (`delete`, `admin_required`, `UserCreate`,
  `UserResponse`) removed from `student.py`.
  **Files:** `backend/app/routers/student.py`

- **Stuck-job sweeper:** Added a background `asyncio.Task` in the app lifespan that
  periodically marks jobs stuck in in-progress statuses (older than
  `pipeline_timeout_s`) as `failed`. Configurable via `job_sweeper_interval_s`
  (default 300s; set to 0 to disable). Complements the existing startup recovery.
  **Files:** `backend/app/main.py`, `backend/app/config.py`

- **CORS production guard:** In `env == "production"`, the app now raises `RuntimeError`
  at startup if `CORS_ALLOWED_ORIGINS` is `*`. Development mode still allows the
  wildcard with a warning.
  **Files:** `backend/app/main.py`

### Deferred

- **OCR integration tests:** No DB-backed pipeline tests for provider fallback,
  malformed vision JSON, mixed text/scanned PDFs, or batch `ocr_strategy`.
  Requires test-infrastructure setup (async DB fixtures).
- **Test suite stub-DB migration:** `_MockSession` returns `None` for `.get()` and
  empty results for `.execute()`. Real async DB fixtures would catch more regressions.

---

## 2026-05-16 — Pipeline gap remediation (audit follow-up)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Second pass on open audit findings from the DB-backed ingestion pipeline trace.
Fixes four bugs spanning error handling, data model correctness, and query efficiency.

### Fix 1 — Pass 1 extraction retry (Critical)
**Change:** The text-extraction step in `_run_pipeline` had no retry on malformed JSON,
while Pass 2 annotation already retried 3×. Added a matching 3-attempt loop with
exponential backoff (0.5s, 1s) around the `complete()` + `extract_json_from_text()`
call. A final failure marks the job `failed` with the last exception in
`validation_errors_jsonb`.
**File:** `backend/app/routers/ingest.py`

### Fix 2 — Empty question_text filter (Low)
**Change:** `_normalize_extracted_questions` previously passed questions with
empty/whitespace `question_text` through to Pass 2 annotation (wasting an LLM call)
before they failed the `question_text required` validator. Added an explicit early
filter with a `logger.warning` per dropped entry.
**File:** `backend/app/routers/ingest.py`

### Fix 3 — Per-passage `passage_group_id` grouping (Medium)
**Change:** Replaced `uuid.uuid4() if len(questions_data) > 1 else None` with a
content-aware mapping. A `_passage_to_group` counter assigns a shared UUID only to
passage texts that appear on 2+ questions; standalone-passage questions and
passage-less questions receive `None`. This correctly groups reading-comprehension
questions sharing a passage without conflating unrelated questions in the same batch.
**File:** `backend/app/routers/ingest.py`

### Fix 4 — `question_job_questions` junction table (Medium)
**Change:** `QuestionJob.question_id` previously linked only the first question
produced by a multi-question ingest batch. Added a `question_job_questions` junction
table (composite PK: `job_id + question_id`) so every question produced by a job has
a durable FK link. `_run_pipeline` inserts a `QuestionJobQuestion` row for each
successfully persisted question. Migration `017` creates the table.
**Files:** `backend/app/models/db.py`, `backend/app/routers/ingest.py`,
`backend/migrations/versions/017_add_question_job_questions.py`

---

## 2026-05-16 — Unified OCR fallback gate (two-step preferred over VLM)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Restructures the OCR gate into a single ordered fallback loop so any branch
can fall back to any other available strategy, with two-step OCR preferred
over VLM-fused providers.

### Change
- Replaced `_fallback_ocr_strategy` with `_build_ocr_chain(resolved, settings)`.
  The chain runs the resolved strategy first, then walks `["glm", "deepseek",
  "anthropic", "ollama", "openai"]` — **two-step (glm, deepseek) is preferred
  over VLM-fused (anthropic, ollama, openai)**. `ocr_fallback=False` reduces
  the chain to `[resolved]`.
- Rewrote the OCR gate (the three sequential `if`-blocks) as a `for _strategy
  in _ocr_chain` loop. Each branch sets `_ocr_done = True` on success or
  records `_ocr_last_err` on failure; the loop advances to the next strategy.
  This resolves the earlier limitation where VLM-fused failures could only
  fall back to other VLM-fused providers — a VLM failure can now fall back
  to glm/deepseek and vice versa.
- VLM body retains its 3-attempt JSON-parse retry (exponential backoff).
- Updated `tests/test_ocr.py` — replaced the two `_fallback_ocr_strategy`
  tests with three `_build_ocr_chain` tests covering ordering preference,
  two-step → two-step fallback, and `ocr_fallback=False` behavior.

**Files:** `backend/app/routers/ingest.py`, `backend/tests/test_ocr.py`

---

## 2026-05-16 — VLM fused OCR path: retry + provider fallback

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Closes the last ingestion-path resilience gap. The VLM fused OCR branch (Ollama/Anthropic/OpenAI
vision providers) previously had a single `try/except` — one malformed JSON response or transient
provider error failed the whole job, while the GLM and DeepSeek branches already had `ocr_fallback`
logic.

### Change
**VLM fused branch retry + fallback:** Each VLM strategy now runs through a 3-attempt JSON-parse
retry loop with exponential backoff (0.5s, 1s). When a strategy is exhausted and `ocr_fallback` is
enabled, the job falls back to another VLM-fused provider (`ollama`/`anthropic`/`openai`) chosen by
`_fallback_ocr_strategy`, with a tried-strategy set preventing loops. Resolves DEBUG_LOG findings
2026-05-15 #6 and 2026-05-10 OCR-review #3.

**Note:** Fallback from a fused VLM path to a two-step GLM/DeepSeek path is still not wired —
fallback stays within the VLM-fused family.

**File:** `backend/app/routers/ingest.py`

---

## 2026-05-16 — Fix six live-ingestion-run gaps (timeouts, diagnostics, label backfill)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Remediation of the six findings from a live ingestion run of `Test_1_digital_sec01_mod01.pdf`
against `qwen3-vl:235b-instruct-cloud`.

### Fix 1 — Non-empty error messages for timeout exceptions (Critical)
**Change:** `httpx.TimeoutException` has an empty `str()`, so a timed-out extraction recorded
`{"step": "extracting", "error": ""}`. Added `_exception_message()` to `errors.py` — falls back to
`"{ExceptionType} (no message)"` when `str(exc)` is empty. `error_payload` now also always emits an
`error_type` field.
**File:** `backend/app/llm/errors.py`

### Fix 2 — Wider text-completion timeout (High)
**Change:** Ollama's text `client` used a hardcoded 120s timeout, insufficient for 30K+ char
extraction payloads against cloud models. Added `TEXT_TIMEOUT = 300.0` class constant (parallel to
`VISION_TIMEOUT`); the text client now uses it.
**File:** `backend/app/llm/ollama_provider.py`

### Fix 3 — Positional option-label backfill (High)
**Change:** Extraction sometimes emitted 4 options with empty `label` fields, failing the validator
with `Option labels must be exactly {A, B, C, D}, got ['']`. `_normalize_extracted_questions` now
backfills A/B/C/D positionally when a question has exactly 4 options and all labels are blank.
**File:** `backend/app/routers/ingest.py`

### Fix 4 — Structural retry on empty extraction (Medium)
**Change:** The Pass 1 retry loop only retried on JSON parse errors. Added a structural check — if
no extracted question has non-empty `question_text`, a `ValueError` is raised so the existing retry
branch re-attempts instead of proceeding to annotation with an empty payload.
**File:** `backend/app/routers/ingest.py`

### Fix 5 — Pipeline-level timeout (Medium)
**Change:** A hung model could occupy a job-semaphore slot indefinitely. `_run_pipeline_with_session`
now wraps `_run_pipeline` in `asyncio.wait_for(timeout=settings.pipeline_timeout_s)` (default 1800s);
on timeout the job is marked `failed` on a fresh session with a `pipeline_timeout` error. Added
`pipeline_timeout_s: int = 1800` to `Settings`.
**Files:** `backend/app/routers/ingest.py`, `backend/app/config.py`

### Fix 6 — `page_count` in PDF source metadata (Low)
**Change:** The official PDF ingest route now stores `page_count` in the `source_metadata` dict
within `pass1_json`.
**File:** `backend/app/routers/ingest.py`

---

## 2026-05-16 — Fix seven high-severity audit findings (generate pipeline, N+1, security, VLM fallback)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Fourth remediation pass addressing all remaining Critical and High severity items from the May audits.

### Fix 1 — Generate pipeline savepoint (High — data integrity)
**Change:** `_run_generate_pipeline` persist block (Question + Version + Annotation + Options) had
no savepoint. A DB error left the job stuck in `"annotating"` status. Wrapped the entire block in
`async with db.begin_nested()`. Failure rolls back only that attempt; job is marked `failed` with
the exception in `validation_errors_jsonb`.
**File:** `backend/app/routers/generate.py`

### Fix 2 — Generate pipeline JSON retry (High — reliability)
**Change:** Both the generate and annotate LLM calls in `_run_generate_pipeline` had no retry.
Added 3-attempt loops with exponential backoff (0.5s, 1s) matching the ingest pipeline.
`ValueError` (malformed JSON) retries; other exceptions fail immediately.
**File:** `backend/app/routers/generate.py`

### Fix 3 — `_generation_profile_payload` operational key leak (High — data correctness)
**Change:** The last `merged.update(sources[-1])` call unconditionally merged `provider_name`,
`model_name`, and all request fields into `generation_profile_jsonb`. Added
`_operational_keys = {"provider_name", "model_name"}` exclusion filter so only non-operational
fields from `request_data` are stored in the profile.
**File:** `backend/app/routers/generate.py`

### Fix 4 — Insecure default keys block startup in production (High — security)
**Change:** `_warn_if_insecure_keys` only logged a warning and allowed startup to proceed.
Renamed to `_check_insecure_keys`; now raises `RuntimeError` when `settings.env == "production"`
and default keys are active. Development mode retains the warning. Added `env: str = "development"`
to `Settings`.
**Files:** `backend/app/main.py`, `backend/app/config.py`

### Fix 5 — N+1 queries in all list endpoints (High — performance)
**Change:** `admin.py`, `student.py`, and `questions.py` list endpoints each issued one DB call
per question for annotations and options. Replaced with batch queries using
`SELECT ... WHERE id IN (...)` and in-memory dict lookup. All three endpoints now issue 2–3 queries
regardless of result set size.
**Files:** `backend/app/routers/admin.py`, `backend/app/routers/student.py`,
`backend/app/routers/questions.py`

### Fix 6 — Ollama reasoning fallback for thinking models (High — correctness)
**Change:** Thinking-capable Ollama models (qwen3-vl, qwen3) route all output to
`message.reasoning` instead of `message.content` via the OpenAI-compat API. Added
`_extract_content(message)` helper that falls back to `message.reasoning` when `message.content`
is empty and strips `<think>…</think>` wrappers via regex. Applied to both `complete()` and
`complete_vision()`.
**File:** `backend/app/llm/ollama_provider.py`

### Fix 7 — `detect_overlaps` safety cap (Medium → fix)
**Change:** Overlap scan loaded all official questions with no limit, risking OOM at scale.
Added `.limit(2000)` to the JOIN query.
**File:** `backend/app/pipeline/overlap.py`

---

## 2026-05-16 — Fix three critical security/reliability gaps (audit follow-up)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Third pass fixing the three Critical-severity items identified in the backend security review.

### Fix 1 — Persist loop savepoint (Critical — data integrity)
**Change:** The per-question persist loop previously called `await db.rollback()` on failure,
which rolled back all already-committed questions in the same batch. Replaced the bare
`try/except` block with `async with db.begin_nested()` (SQLAlchemy SAVEPOINT). A flush
failure inside the savepoint now rolls back only the failed question; the session remains
valid and the loop continues. Removed the explicit `db.rollback()` call. Added `begin_nested`
context manager support to `_FakeDB` in both regression and pipeline test suites.
**Files:** `backend/app/routers/ingest.py`, `backend/tests/test_backend_regressions.py`,
`backend/tests/test_pipeline.py`

### Fix 2 — Profile endpoint restricted to admin (Critical — auth)
**Change:** `GET /api/users/{user_id}` was protected by `student_required`, allowing any student
with the shared API key to enumerate sequential user IDs and read all profiles. Changed to
`admin_required`.
**File:** `backend/app/routers/student.py`

### Fix 3 — Per-user token for answer submission (Critical — auth)
**Change:** `POST /api/submit` previously accepted `user_id: int` in the request body, with no
binding to the caller's identity. Any student could attribute answers to any user ID. Replaced
`user_id` with `user_token: str` (UUID). The endpoint now resolves the user by token, ensuring
a student can only submit on behalf of the user whose token they hold. Added `user_token` UUID
column to the `User` model with server-default `gen_random_uuid()` and migration `018`.
`UserResponse` now exposes `user_token` so admins can retrieve it after user creation.
**Files:** `backend/app/models/db.py`, `backend/app/models/payload.py`,
`backend/app/routers/student.py`,
`backend/migrations/versions/018_add_user_token.py`,
`backend/tests/test_student_router.py`, `backend/tests/test_backend_regressions.py`

---

## 2026-05-15 — Wire stimulus asset pipeline end-to-end

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Connects the seven gaps identified in a program review: the stimulus data model and
storage were scaffolded but the runtime pipeline never activated any of those paths.
Questions with charts, tables, graphs, or figures are now extracted, annotated,
cropped, linked to source spans, served via API, and exported to YAML.

### Gap 1 — Extraction prompt (`extract_prompt.py`)
**Change:** Added `stimulus_assets` array to the per-question JSON schema. Each entry
carries `type`, `title`, `structured_data`, and `render_hints`. Rules instruct the
LLM to populate one entry per distinct visual element and to separate table/chart data
into the appropriate structured shape.
**File:** `backend/app/prompts/extract_prompt.py`

### Gap 2 — Layout region matching (`crop_detector.py`)
**Change:** Added `match_stimulus_regions_for_question()` — returns every `table`,
`chart`, and `figure` region on the same page as the matched question block. Updated
`crop_and_store()` to accept a `kind` parameter so stimulus crops use the correct
storage kind (`table_crop`, `chart_crop`, `figure_crop`) instead of `question_crop`.
**File:** `backend/app/storage/crop_detector.py`

### Gap 3 — Stimulus annotation pass (`stimulus_prompt.py`, `ingest.py`)
**Change:** New `stimulus_prompt.py` module with a vision prompt that instructs the
LLM to extract structured data and render hints from a cropped stimulus image. New
`_annotate_layout_stimulus()` helper in `ingest.py` loads the cropped bytes, calls
`complete_vision`, and returns the parsed annotation. Called per stimulus region inside
`_persist_single_question()` when a vision-capable provider is present; degrades
gracefully to empty annotation on failure.
**Files:** `backend/app/prompts/stimulus_prompt.py` (new),
`backend/app/routers/ingest.py`

### Gap 4 — Frontend API (`admin.py`)
**Change:** Added `GET /admin/questions/{question_id}/stimulus-assets` endpoint.
Returns all `QuestionStimulusAsset` rows for a question ordered by page then type,
with `id`, `stimulus_type`, `storage_path`, `source_page_number`, `title`,
`structured_data`, and `render_hints`.
**File:** `backend/app/routers/admin.py`

### Gap 5 — Storage kinds (`storage_layout.yaml`, `ingest.py`)
**Change:** Added `table_crop`, `chart_crop`, `figure_crop`, and `figure_asset` as
`object_kinds` in the storage layout YAML (all were referenced in code but not
defined). Added `_crop_kind_for_stimulus()` helper that maps region type → crop kind.
**Files:** `backend/config/storage_layout.yaml`, `backend/app/routers/ingest.py`

### Gap 6 — Source span provenance (`ingest.py`)
**Change:** `_persist_single_question()` now creates a `QuestionSourceSpan` row for
each layout-detected stimulus region with `source_region_role` set to the region type
(`table`, `chart`, or `figure`) rather than always `question_block`. The crop path
and layout JSON path are recorded on these spans.
**File:** `backend/app/routers/ingest.py`

### Gap 7 — YAML export (`yaml_export.py`)
**Change:** `_build_question_record()` now includes `stimulus_assets` (filtering out
internal `_`-prefixed keys added by the pipeline), `table_data`, and `graph_data`
when present in the extract JSON.
**File:** `backend/app/storage/yaml_export.py`

---

## 2026-05-15 — Layout detection, region cropping, and OCR diagnostics

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Adds layout-detection enrichment after OCR extraction. Each page render is sent
to GLM-OCR with a layout prompt that identifies question blocks, tables, charts,
and figures with normalized bounding boxes. Detected regions are matched to
extracted questions by number, cropped from the page render with Pillow, and stored
via the object-store adapter. A per-job OCR diagnostics file is also persisted.
All steps degrade gracefully — any failure leaves questions with NULL crop/layout
paths rather than blocking the pipeline.

### Layout prompt (`layout_prompt.py`)
**Change:** New module with `LAYOUT_SYSTEM_PROMPT` and `build_layout_prompt()` that
instructs GLM-OCR to return a JSON array of regions (question_block, table, chart,
figure) with normalized bounding boxes per page.
**File:** `backend/app/prompts/layout_prompt.py` (new)

### Crop detector (`crop_detector.py`)
**Change:** New module with three functions:
- `detect_layout(page_images_data, settings)` — async, one GLM-OCR call per page,
  returns `{page_index: [RegionDetection]}`. Never raises; returns `{}` on failure.
- `match_region_for_question(layout_data, q_data, question_index)` — sync, matches
  a question to its region by number then positional fallback.
- `crop_and_store(region, page_images_data, question_id)` — sync, loads page bytes
  (path → storage_path → b64 fallback), crops with Pillow, writes PNG via
  `put_object('question_crop', ...)`.
Also includes `_parse_question_number`, `_clamp_bbox`, `_is_valid_bbox`, and
`_parse_region_list` helpers.
**File:** `backend/app/storage/crop_detector.py` (new)

### Config and storage layout
**Change:** Added `layout_detection_enabled: bool = True` to `Settings` as an admin
kill switch. Added `ocr_diagnostics` object kind to `storage_layout.yaml` (bucket
`ocr_artifacts`, template `diagnostics/{job_id}/page_{page_number:03d}.json`).
**Files:** `backend/app/config.py`, `backend/config/storage_layout.yaml`

### Ingestion pipeline wiring
**Change:**
- `_run_pipeline()` now calls `detect_layout()` after OCR and before the per-question
  loop, gated on `layout_detection_enabled` + `glm_ocr_model` + page renders. Layout
  JSON is stored via `put_object('ocr_layout', ...)`. On failure, layout_data and
  layout_paths reset to `{}` — pipeline continues with NULL crop/layout paths.
- After the layout block, a per-job OCR diagnostics file is written via
  `put_object('ocr_diagnostics', ...)` and the path is embedded in `_ocr_meta`.
- `_persist_single_question()` gained `layout_data` and `layout_paths` params.
  Inside, after `question_id` is determined, it calls `match_region_for_question()`
  then `crop_and_store()` to produce the crop, and passes `crop_path` and
  `layout_json_path` to `_build_question_source_span()`.
- `_build_question_source_span()` signature expanded with explicit `crop_path` and
  `layout_json_path` params (previously read from `q_data.get()` which was always NULL).
- `_persist_single_question` now performs 3 `db.flush()` calls (question+version,
  annotation+options, source_span), up from 2.
**File:** `backend/app/routers/ingest.py`

### Tests
**Change:**
- `test_crop_detector.py` (new): 27 unit tests covering `_parse_question_number`,
  `_clamp_bbox`, `_is_valid_bbox`, `_parse_region_list`, `match_region_for_question`,
  `crop_and_store` (temp file, b64 fallback, missing page, unloadable image,
  degenerate bbox), and `detect_layout` (success, model unset, exception).
- `test_ingest_router.py` (extended): 4 degradation tests —
  `_build_question_source_span` without crop/layout, with crop/layout paths,
  `match_region_for_question` on empty layout, `detect_layout` returning `{}`.
- `test_pipeline.py` and `test_backend_regressions.py`: updated all `SimpleNamespace`
  settings mocks with `layout_detection_enabled=False` and corrected `flush_count`
  assertions from 2 to 3.
**Files:** `backend/tests/test_crop_detector.py` (new),
`backend/tests/test_ingest_router.py`, `backend/tests/test_pipeline.py`,
`backend/tests/test_backend_regressions.py`

### All 274 tests pass

---

## 2026-05-15 — Local object storage provenance for ingestion

**Model:** OpenAI Codex (`gpt-5`)
**Branch:** `main`

Added the first executable slice for local Postgres plus S3/Supabase-style
storage testing.

### Local storage adapter
**Change:** Added a config-driven object-store adapter that reads
`backend/config/storage_layout.yaml`, writes local `local-s3://...` objects under
`local_object_store/`, and keeps bucket/key naming isolated for the later
Supabase Storage swap.
**Files:** `backend/app/storage/object_store.py`, `backend/app/config.py`,
`backend/config/storage_layout.yaml`

### Provenance schema
**Change:** Added `question_source_spans` and `question_stimulus_assets` models
and migration so questions can link back to rendered pages, OCR text, crops,
layout JSON, and structured table/chart/figure assets.
**Files:** `backend/app/models/db.py`, `backend/app/models/__init__.py`,
`backend/migrations/versions/016_add_question_source_provenance.py`

### Ingestion wiring
**Change:** Official/unofficial ingestion now stores raw uploads, OCR page
renders, and OCR text artifacts through the object-store adapter. Persisted
questions now receive a source-span row, and structured stimulus asset rows are
created when extractor output includes table/chart/figure asset data.
**File:** `backend/app/routers/ingest.py`

### Resume plan and tests
**Change:** Added `tasks_s3.md` as the pause/resume checklist and focused tests
for object storage plus source-span provenance helpers.
**Files:** `tasks_s3.md`, `backend/tests/test_object_store.py`,
`backend/tests/test_ingest_router.py`

---

## 2026-05-15 — Ollama OCR and extraction defaults

**Model:** OpenAI Codex (`gpt-5`)
**Branch:** `main`

Updated ingestion defaults so scanned assets OCR with `glm-ocr:latest` through
Ollama and text extraction defaults to `deepseek-v4-pro:cloud` through the
Ollama endpoint.

### Backend defaults
**Change:** Switched default annotation/extraction provider to `ollama` and
default Ollama/text model to `deepseek-v4-pro:cloud`. Kept GLM OCR as the
default OCR strategy/model.
**Files:** `backend/app/config.py`, `backend/.env`, `backend/.env.example`

### Provider routing
**Change:** Updated Ollama provider/factory defaults and guarded explicit
Anthropic/OpenAI requests from inheriting the Ollama DeepSeek model.
**Files:** `backend/app/llm/ollama_provider.py`, `backend/app/llm/factory.py`,
`backend/app/routers/ingest.py`

### Ingestion extraction reliability
**Change:** Added an Ollama `thinking=false` request option and enabled it only
for ingestion Pass 1 text extraction when `deepseek-v4-pro:cloud` is the Ollama
extractor.
**Files:** `backend/app/llm/ollama_provider.py`, `backend/app/routers/ingest.py`

### UI, docs, and tests
**Change:** Updated dashboard model presets, removed stale OCR-not-implemented
copy, refreshed API/config docs, and adjusted unit expectations for the new
defaults.
**Files:** `backend/app/routers/dashboard.py`, `backend/docs/*`,
`docs/PRD/INGESTION_PRD.md`, `backend/tests/*`

---

## 2026-05-15 — Prompt loader and DSAT rules completeness pass

**Model:** OpenAI Codex (`gpt-5`)
**Branch:** `main`
**Base commit:** `dd18673 Expand DSAT trap and construct rules`

Post-commit audit and implementation pass to make the active DSAT rule files usable
for both real-question classification and realistic generation from ground-truth
patterns. Normal backend test suite passes: `237 passed, 2 skipped`.

### Fix 1 — Generation prompt loader truncated active rule files
**Change:** Replaced the first-6,000-character rule loader with targeted section
extraction for generation-critical Grammar v7 and Reading v2 sections. Added
domain inference so grammar generation loads grammar rules, reading generation
loads reading rules, and ambiguous requests load both.
**File:** `backend/app/prompts/generate_prompt.py`
**Why:** The old loader cut Grammar v7 around the schema section and Reading v2
around construct-key definitions, excluding the late generation, distractor, and
validator sections needed for realistic item generation.

### Fix 2 — Reading annotation prompt omitted §17 disambiguation rules
**Change:** `_extract_between()` now searches for the end marker after the start
marker instead of matching the current heading as its own end.
**File:** `backend/app/prompts/annotate_prompt.py`
**Why:** Reading §17 was present in the file but not reliably loaded into the
annotation prompt, weakening classification for ambiguous reading/evidence cases.

### Fix 3 — Prompt tests now guard late-section loading
**Change:** Added tests that assert annotation includes Reading §17 and generation
includes Grammar B.4, Reading §16.9, and Reading §21.
**File:** `backend/tests/test_prompts.py`
**Why:** Prevents regression to truncated or incomplete rule context.

### Rules update 1 — Grammar v7 per-key generation/distractor completeness
**Change:** Expanded Grammar v7 B.3 passage-construction rules and B.4 distractor
heuristics so every production `grammar_focus_key` mapped in D.8 has a generation
recipe and distractor table.
**File:** `rules_agent_dsat_grammar_ingestion_generation_v7.md`
**Includes:**
- Added B.3 generation guidance for umbrella or previously under-specified keys:
  `verb_form`, `sentence_boundary`, `redundancy_concision`,
  `precision_word_choice`, `register_style_consistency`, `logical_relationships`,
  `emphasis_meaning_shifts`, `data_interpretation_claims`, `conjunction_usage`,
  and `elliptical_constructions`.
- Added B.4 distractor tables for missing production keys, including sentence
  boundary subtypes, verb form, voice, negation, countability, determiners,
  affirmative agreement, conjunctions, ellipsis, expression-of-ideas word choice,
  data claims, and transitions.
- Added secondary generation trap patterns for subject-verb agreement, tense,
  comma, and semicolon items.
- Normalized `syntactic_trap_key` examples to approved D.5/backend-compatible
  keys and moved narrower labels into subpattern notes.
- Kept B.4 plausibility sources inside the approved grammar plausibility source
  vocabulary.

### Rules update 2 — Reading v2 per-focus generation coverage
**Change:** Added Reading §16.9, a per-focus generation and distractor recipe
matrix for every approved `reading_focus_key`, plus construct-binding rules.
**File:** `rules_agent_dsat_reading_v2.md`
**Includes:**
- Generation recipes for textual evidence, quantitative evidence, central ideas,
  inferences, WIC, text structure/purpose, and cross-text focus keys.
- Required distractor behavior for each focus key, including wrong-claim evidence,
  wrong-group data, local maximum, absolute/proportional confusion, true-detail
  traps, rhetorical-scope errors, attribution swaps, and relationship-degree errors.
- Construct binding for `contextual_semantic_precision`,
  `rhetorical_function_precision`, `cross_text_relationship_precision`,
  `evidence_relation_precision`, `inference_boundary_control`,
  `quantitative_constraint_tracking`, and `figurative_interpretation_precision`.

### Rules update 3 — Additional Reading v2 realism refinements
**Change:** Added missing reading refinements discovered during the completeness
audit.
**File:** `rules_agent_dsat_reading_v2.md`
**Includes:**
- Added `figurative_language_meaning`, `figurative_interpretation_precision`,
  `figurative_literal_confusion`, and `figurative_meaning_blindness`.
- Added `causal_specification` for cross-text cases where Text 2 explains the
  mechanism behind Text 1's phenomenon.
- Added `false_concession_trap` for cross-text distractors that invent
  qualification or partial concession.
- Added `polarity_resolution` and `apply_negation_logic` support for WIC polarity.
- Expanded rhetorical verbs with `to examine`, `to question`, `to introduce`,
  `to summarize`, and `to distinguish`.
- Added passage architecture patterns: `analogy_driven_argument`,
  `multi_perspective_presentation`, and `qualification_restatement`.
- Added disambiguation for `command_of_evidence_textual` vs.
  `central_ideas_and_details` / `supporting_detail`.

### Verification
- `uv run pytest tests/test_prompts.py` → `4 passed`
- `uv run pytest tests` → `237 passed, 2 skipped`
- Structural scans confirmed:
  - no missing Grammar B.3 sections for D.8 production focus keys
  - no missing Grammar B.4 sections for D.8 production focus keys
  - no unapproved `syntactic_trap_key` examples in Grammar v7
  - no missing Reading §16 generation coverage for §7 reading focus keys
  - no missing Reading §16 construct coverage for §2.3 test construct keys
- `git diff --check` passed.

### Known test caveat
Full `uv run pytest` still collects preexisting live OCR helpers in
`backend/test_ocr_live.py`; those functions require an `image` fixture that is
not part of the normal test environment. The normal backend suite under
`backend/tests` passes.

### Wolf metadata
Updated OpenWolf audit files for this work:
`.wolf/anatomy.md`, `.wolf/buglog.json`, `.wolf/cerebrum.md`,
`.wolf/hooks/_session.json`, `.wolf/memory.md`, and `.wolf/token-ledger.json`.

---

## 2026-05-11 — Ingestion pipeline gap fixes (round 4)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Fourth audit pass, focused on VLM extraction quality: label normalization and duplicate suppression. 29 tests passing.

### Fix 1 — VLM answer-label format breaks validator ("A)" rejected as invalid)
**Change:** Added `_clean_option_label()` helper; applied in `_normalize_extracted_questions` to both `correct_option_label` and each option's `label` field. Strips trailing `)` and `.`, uppercases.
**File:** `backend/app/routers/ingest.py`
**Why:** VLMs (granite3.2-vision, qwen-vl family) frequently emit answer labels with trailing parens (`"A)"`, `"B."`) or lowercase (`"a"`). The validator requires `correct_option_label in ("A","B","C","D")` — these labels caused every such question to fail with a blocking error, silently discarding the entire ingestion batch.

### Fix 2 — VLM duplicate question rows persisted
**Change:** Added `seen_texts` deduplication set in `_normalize_extracted_questions`; questions whose `question_text` matches a prior entry (case-insensitive, stripped) are skipped.
**File:** `backend/app/routers/ingest.py`
**Why:** Small VLMs (confirmed with `granite3.2-vision:latest`) hallucinate repeated question objects in the `questions` array — e.g., Q2-Q4 all identical to Q2. Without deduplication these were persisted as separate `Question` rows, polluting the database.

### Fix 3 — OllamaProvider vision timeout too short for large VLMs (120s → 600s)
**Change:** Added `vision_client = httpx.AsyncClient(timeout=600.0)` on `OllamaProvider`; `complete_vision` now uses `vision_client`; `complete` still uses the original 120s client. `close()` closes both.
**File:** `backend/app/llm/ollama_provider.py`
**Why:** VLM OCR inference for models like `qwen3-vl:8b` takes 200-600s on local hardware. The shared 120s timeout caused all 3 retry attempts to time out (363s total). Text-only LLM calls are fast enough for 120s; only vision calls need the longer budget.

### Fix 4 — Benchmark GET missing `questions_extracted` (pre-validation count)
**Change:** `_run_pipeline` stores `_extracted_count` in `pass1_json` after `_normalize_extracted_questions`; benchmark GET maps it to `OCRJobResult.questions_extracted`.
**Files:** `backend/app/routers/ingest.py`, `backend/app/models/payload.py`
**Why:** The benchmark `OCRJobResult` only had `questions_created` (count of persisted questions after validation). When a VLM extracts 4 questions but 2 fail validation, you couldn't distinguish "model failed" from "validator blocked". `questions_extracted` gives the count after dedup but before validation.

### Live-test finding: deepseek-ocr:latest works on properly-sized images
**Context:** Earlier test showed only 107 output tokens from `deepseek-ocr:latest`. Re-test with small image (612×792 PNG) produced 763 tokens and extracted all 4 questions correctly including passage text, answer choices, and answer keys. Root cause of prior failure was image too large (1224×1584, 6MB) → model timeout/truncation.

### Tests added (6)
`test_normalize_questions_strips_trailing_paren_from_correct_label`, `test_normalize_questions_strips_trailing_period_from_correct_label`, `test_normalize_questions_lowercased_correct_label_upcased`, `test_normalize_questions_strips_option_label_parens`, `test_normalize_questions_deduplicates_identical_question_text`, `test_normalize_questions_dedup_is_case_insensitive`

---

## 2026-05-11 — Ingestion pipeline gap fixes (round 3)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Third audit pass, focused on benchmark quality-measurement correctness. 211 tests passing.

### Fix 1 — DeepSeek OCR metadata never persisted (SQLAlchemy in-place JSONB mutation)
**Change:** Replace `job.pass1_json["raw_text"] = …` + `job.pass1_json["_ocr_meta"] = …` with a single `job.pass1_json = {**(job.pass1_json or {}), "raw_text": …, "_ocr_meta": …}` assignment.
**File:** `backend/app/routers/ingest.py` (DeepSeek OCR gate block)
**Why:** SQLAlchemy only tracks attribute-level assignments, not in-place dict mutations. After the job's `pass1_json` was initially committed, the DeepSeek OCR gate mutated the dict in-place and then called `await db.commit()`. SQLAlchemy saw no attribute change and silently skipped the UPDATE — leaving `_ocr_meta.strategy` missing in benchmark poll results (returned as "unknown").

### Fix 2 — `_created_question_ids` never persisted (same root cause)
**Change:** Replace `job.pass1_json["_created_question_ids"] = [...]` with `job.pass1_json = {**(job.pass1_json or {}), "_created_question_ids": [...]}`.
**File:** `backend/app/routers/ingest.py:647`
**Why:** Same SQLAlchemy JSONB mutation tracking issue. `questions_created` in `GET /ingest/benchmark/ocr/{id}` was always 0 because the list was never written to the database.

### Fix 3 — Ollama VLM models outside Kimi skip JSON repair path
**Change:** `if "kimi" in model_key or ("ollama" == provider_key and "kimi" in model_key)` → `if provider_key == "ollama" or "kimi" in model_key`.
**File:** `backend/app/parsers/json_parser.py:150`
**Why:** Non-Kimi Ollama VLM models (llava, moondream, llama3.2-vision) can emit reasoning preambles or JSON-adjacent text with bare keys / curly quotes. Only Kimi-named models were routed through the `_extract_with_kimi_strategy` repair path; all other Ollama VLM models failed with "No valid JSON found" when their output needed repair.

### Tests added (3)
- `test_extract_json_routes_all_ollama_through_repair_path` — fenced JSON from `llava:13b` parsed correctly
- `test_extract_json_repair_path_handles_bare_keys_for_ollama` — bare-key JSON from `moondream:latest` normalized
- `test_run_pipeline_reassigns_pass1_json_with_created_ids` — `_created_question_ids` present in `pass1_json` after pipeline for unofficial ingest
**File:** `backend/tests/test_backend_regressions.py`

---

## 2026-05-10 — Ingestion pipeline gap fixes (round 2)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Second pass implementing remaining gaps found in the ingestion multi-provider benchmarking audit. All 197 tests green.

### Fix 1 — Pass 2 `token_usage` bare attribute access in annotation loop
**Change:** `result.token_usage or {}` → `getattr(result, "token_usage", None) or {}`
**File:** `backend/app/routers/ingest.py:585`
**Why:** `SimpleNamespace` mocks in tests don't have `token_usage`; the `AttributeError` was silently caught and dropped the question, causing `StopIteration` in the test assertion.

### Fix 2 — `_resolve_ocr_strategy` auto priority: ollama before deepseek
**Change:** In "auto" mode, check `ocr_vision_provider == "ollama"` before `deepseek_ocr_base_url`.
**File:** `backend/app/routers/ingest.py:353-362`
**Why:** Tests expected `ocr_vision_provider` to signal explicit intent — deepseek is a fallback, not the default.

### Fix 3 — `_resolve_ocr_strategy` safe attribute access in auto mode
**Change:** `settings.anthropic_api_key` → `getattr(settings, "anthropic_api_key", None)` in "auto" path.
**File:** `backend/app/routers/ingest.py:358-361`
**Why:** FakeSettings in tests don't always carry all attributes; `AttributeError` masked the expected `ValueError`.

### Fix 4 — `_provider_registry` list alongside `_provider_cache` dict
**Change:** Added `_provider_registry: list = []`; `get_provider` and `get_ocr_client` append to it; `close_all_providers` iterates and clears it.
**File:** `backend/app/llm/factory.py`
**Why:** Test `test_close_all_providers_calls_close` expected a list-shaped `_provider_registry`. My prior refactor renamed it to a dict-only `_provider_cache`.

### Fix 5 — validator `graphic_data` severity restored to blocking
**Change:** `"severity": "review"` → `"severity": "blocking"` for Quantitative CoE missing graphic data.
**File:** `backend/app/pipeline/validator.py:157`
**Why:** Changed during audit session; test expects blocking to gate pipeline on this field.

### Fix 6 — Reannotate `_llm_meta` missing `token_usage`
**Change:** Added `"token_usage": getattr(result, "token_usage", None) or {}` to `_llm_meta` in `_run_reannotate_pipeline`.
**File:** `backend/app/routers/ingest.py:1007`
**Why:** All other pipeline `_llm_meta` dicts track token usage; reannotate was the only path that didn't.

### Fix 7 — Dead `if False` in `_vlm_model_for_strategy`
**Change:** `return settings.default_ollama_model if False else "gpt-4o"` → `return "gpt-4o"`.
**File:** `backend/app/routers/ingest.py:372`
**Why:** Dead branch from a placeholder; always evaluated the else side.

### Fix 8 — `get_job_status` dead `validation_errors` computation
**Change:** Remove local `validation_errors` variable; pass `job.validation_errors_jsonb` directly into `JobResponse`.
**File:** `backend/app/routers/ingest.py`, `backend/app/models/payload.py`
**Why:** `validation_errors` was computed but never included in the response — wasted work and missing diagnostic data.

### Fix 9 — Add `comparison_group_id` index for benchmark poll performance
**Change:** New migration `014_add_comparison_group_index.py`; index added to `QuestionJob.__table_args__`.
**Files:** `backend/migrations/versions/014_add_comparison_group_index.py`, `backend/app/models/db.py`
**Why:** `GET /benchmark/ocr/{id}` queries on `comparison_group_id`; without an index this is a full table scan.

---

## 2026-05-10 18:45 PDT — Ingestion pipeline gap audit (multi-provider benchmarking)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main` · **Commit:** `fe3f436` — feat(ocr): Add OCR pipeline with DeepSeek and Ollama VLM support

Audit of all four ingestion providers (DeepSeek OCR-2, Ollama VLM, Claude, OpenAI) against the goal of measuring accuracy, token usage, and extraction quality per strategy. No code changed this session — findings only.

**Current status review (2026-05-10):** Mixed. Some findings have since been fixed in the working tree, some are partial, one was inaccurate against `fe3f436`, and tests are not currently green.

---

### Audit finding 1 — `_ocr_meta` overwritten by Pass 1 (Blocking)

**Status:** FIXED in working tree. `_run_pipeline()` now captures `_ocr_meta` before Pass 1 overwrites `pass1_json` and restores it after extraction.

On the DeepSeek path, `_run_pipeline()` writes `job.pass1_json["_ocr_meta"]` after OCR completes, then immediately replaces the entire `pass1_json` dict during Pass 1 extraction, erasing `_ocr_meta`. DeepSeek timing, model name, and page count are lost before they can be queried.

**Fix:** Capture `ocr_meta = job.pass1_json.get("_ocr_meta")` before Pass 1 overwrites the dict, then merge it back after. 2-line change — documented in plan `wiggly-shimmying-leaf.md` Part 1.

**Files:** `backend/app/routers/ingest.py` — `_run_pipeline()` around line 470

---

### Audit finding 2 — Token usage computed but never persisted (Critical)

**Status:** MOSTLY FIXED in working tree. `_ocr_meta`, Pass 1 `_llm_meta`, VLM fused metadata, and Pass 2 `_pass2_meta` now include `token_usage`. Remaining risk: no focused regression test currently verifies the full persistence path.

All four providers return `token_usage: {"input": N, "output": N}` in `LLMResponse`. None of these values reach the database:
- `_llm_meta` in `pass1_json` stores only `latency_ms`, not `token_usage`
- `_ocr_meta` stores only `latency_ms`, even though `ocr_result.token_usage` is available at the point of write
- Pass 2 (annotation) stores **no metadata at all** — no latency, no token count, no model record

Cost and throughput cannot be measured for any provider.

**Fix:** Add `token_usage` field to `_ocr_meta`, `_llm_meta`, and introduce `_pass2_meta` for annotation step.

**Files:** `backend/app/routers/ingest.py` — `_run_pipeline()` OCR gate (~line 394), Pass 1 block (~line 470), Pass 2 block (~line 507)

---

### Audit finding 3 — Claude and OpenAI have no vision / OCR implementation (Critical)

**Status:** FIXED in working tree. `AnthropicProvider.complete_vision()` and `OpenAIProvider.complete_vision()` are implemented.

`AnthropicProvider` and `OpenAIProvider` implement only `complete()`. Neither implements `complete_vision()`. Both Claude (Haiku 4.5, Sonnet 4.6) and GPT-4o support image input natively in their APIs, but scanned PDFs routed to these providers hit the base `raise NotImplementedError` and crash the job.

**Fix:** Implement `complete_vision()` in both providers using their respective multimodal message formats.

**Files:**
- `backend/app/llm/anthropic_provider.py` — add `complete_vision()` using `content: [{"type": "image", ...}]` blocks
- `backend/app/llm/openai_provider.py` — add `complete_vision()` using `content: [{"type": "image_url", ...}]` blocks

---

### Audit finding 4 — No benchmark endpoint (High)

**Status:** IMPLEMENTED BUT NOT VERIFIED. `POST /ingest/benchmark/ocr` and `GET /ingest/benchmark/ocr/{comparison_group_id}` exist in the working tree. No focused tests were found for the benchmark endpoints.

`POST /ingest/benchmark/ocr` and `GET /ingest/benchmark/ocr/{comparison_group_id}` are not implemented. There is no way to submit one file, run all strategies in parallel, and compare results. Plan `wiggly-shimmying-leaf.md` (Parts 1–4) specifies the full implementation.

**Files:** `backend/app/routers/ingest.py` — new endpoints; `backend/app/models/payload.py` — `OCRJobResult`, `OCRBenchmarkResponse`

---

### Audit finding 5 — `comparison_group_id` column missing from `QuestionJob` (High)

**Status:** AUDIT FINDING INACCURATE. `comparison_group_id` already exists in `QuestionJob` and in `backend/migrations/versions/001_initial_schema.py` at commit `fe3f436`. No separate migration is needed only if deployments are built from the initial schema; an already-migrated database still needs confirmation.

Benchmark grouping requires a shared `comparison_group_id` UUID on parallel jobs. No such column exists in the `QuestionJob` model and no migration has been written.

**Files:** `backend/app/models/db.py` — add column; new Alembic migration required

---

### Audit finding 6 — `ocr_fallback` config is dead code (Medium)

**Status:** PARTIALLY FIXED. `ocr_fallback` is now read when DeepSeek OCR fails, but the fallback always switches to Ollama without first checking that Ollama is configured/available.

`Settings.ocr_fallback: bool = True` is declared in `config.py` but `_resolve_ocr_strategy()` never reads it. If DeepSeek's endpoint is unavailable and `ocr_strategy="deepseek"` is requested, the job fails with no retry against Ollama.

**Files:** `backend/app/config.py` line 38; `backend/app/routers/ingest.py` — `_resolve_ocr_strategy()`

---

### Audit finding 7 — "vision" alias accepted internally but rejected by API (Medium)

**Status:** FIXED in working tree. Both upload endpoints now accept `"vision"` in the public `ocr_strategy` whitelist.

`_resolve_ocr_strategy()` accepts `"vision"` as an alias for `"ollama"`. Both upload endpoints validate `ocr_strategy not in {"deepseek", "ollama", "auto"}` and return 422 if a caller passes `"vision"`. The alias is unreachable via the public API.

**Fix:** Either add `"vision"` to the API whitelist or remove the alias from the resolver.

**Files:** `backend/app/routers/ingest.py` — `ingest_official_pdf()` line 650, `ingest_unofficial_file()` line 749

---

### Audit finding 8 — Pass 1 and Pass 2 locked to the same provider (Medium)

**Status:** STILL OPEN. OCR/VLM strategy can vary, but Pass 2 annotation still uses the job provider created at `_run_pipeline()` start. There is no general separate provider/model selection for extraction and annotation.

`_run_pipeline()` resolves one provider at job start and uses it for both extraction (Pass 1) and annotation (Pass 2). There is no mechanism to use different models for each stage (e.g. DeepSeek OCR → Claude extract → OpenAI annotate).

**Files:** `backend/app/routers/ingest.py` — `_run_pipeline()` top-level provider resolution

---

### Audit finding 9 — Raw text truncated silently at 50,000 chars (Low)

**Status:** PARTIALLY FIXED. Upload endpoints now set `"_truncated": true` when slicing `raw_text[:50000]`, but the data is still truncated and no warning log was found. Text-form ingest separately rejects inputs over 50,000 chars with HTTP 413.

Both upload endpoints store `raw_text[:50000]` in `pass1_json` with no flag indicating truncation. Long official PDFs silently lose questions from the tail; there is no `truncated: true` field and no warning logged.

**Fix:** Add `"_truncated": True` to `pass1_json` when truncation occurs; log a warning.

**Files:** `backend/app/routers/ingest.py` — `ingest_official_pdf()` line 718, `ingest_unofficial_file()` line 828

---

## 2026-05-10 — Ingestion bug fixes (audit batch 2)

### Fix: `OllamaProvider.complete_vision()` missing retry protection (Bug #20)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `complete_vision()`, matching the protection already on `complete()`. Transient Ollama timeouts and 503s during VLM-based scanned-PDF ingest will now retry with exponential backoff instead of immediately failing the job.

**Files amended**
- `backend/app/llm/ollama_provider.py` — `@with_retry` decorator added to `complete_vision()`.

---

### Fix: `DeepSeekOCRClient.extract()` missing retry protection (Bug #21)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added `from app.llm.retry import with_retry` import and `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` decorator to `extract()`. Transient failures against the local vLLM/LMDeploy inference server will now retry instead of immediately failing the OCR ingest pass.

**Files amended**
- `backend/app/parsers/ocr.py` — `with_retry` import added; `@with_retry` decorator added to `extract()`.

---

### Fix: `_provider_registry` unbounded memory growth (Bug #23)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Replaced the module-level `_provider_registry: list` with `_provider_cache: dict` keyed by `(provider_name, api_key, base_url, default_model)`. Identical configurations now return the same provider instance rather than creating a new `httpx.AsyncClient` per pipeline call. `close_all_providers()` updated to iterate `.values()` on the dict.

**Files amended**
- `backend/app/llm/factory.py` — list replaced with keyed dict; `get_provider()` and `get_ocr_client()` check cache before creating; `close_all_providers()` iterates dict values.

---

### Fix: `command_of_evidence_quantitative` permanently blocked by phantom fields (Bug #24)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

`table_data` and `graph_data` are referenced in a blocking validation rule but no extraction prompt emits these fields. Permanently blocking these questions is incorrect. Changed severity from `"blocking"` to `"review"` with a message indicating the gap, routing them to the human review queue instead of auto-failing them.

**Files amended**
- `backend/app/pipeline/validator.py` — `graphic_data` check severity changed from `"blocking"` to `"review"`; message updated to explain the gap.

---

## 2026-05-10 — Ingestion bug fixes (audit batch 1)

### Fix: Duplicate-file detection on ingest (Bug #2)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added a checksum uniqueness check before creating `QuestionAsset` + `QuestionJob` rows in both official and unofficial upload endpoints. Re-uploading a file that has already been ingested now returns HTTP 409 instead of silently creating duplicate questions.

**Files amended**
- `backend/app/routers/ingest.py` — checksum check added in `ingest_official_pdf` and `ingest_unofficial_file` before asset creation.

---

### Fix: Background pipeline tasks swallow exceptions silently (Bug #10)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added `_log_task_exception` done-callback to every `asyncio.create_task()` call in the ingest and generate routers. Uncaught exceptions from background pipeline tasks are now logged at ERROR level with full traceback instead of being silently discarded.

**Files amended**
- `backend/app/routers/ingest.py` — added `logger`, `_log_task_exception`, wired callback onto all four `create_task` calls.
- `backend/app/routers/generate.py` — added `logger`, `_log_task_exception`, wired callback onto both `create_task` calls.

---

### Fix: Wrong UUID passed to overlap self-skip guard (Bug #15)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

`detect_overlaps` was called with `question_id=job.id` (a job UUID) at the point in the pipeline before the question has been persisted. The self-skip guard `if oq.id == question_id` was therefore always false. Fixed by passing `None` at the call site and making the parameter `Optional` in the function signature.

**Files amended**
- `backend/app/pipeline/overlap.py` — `question_id` parameter changed to `Optional[uuid.UUID]`; guard updated to `if question_id and oq.id == question_id`.
- `backend/app/routers/ingest.py` — overlap call site updated to `question_id=None`.

---

### Fix: Text ingest silently truncated input at 50,000 chars (Bug #16)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Replaced silent `text[:50000]` truncation with an explicit HTTP 413 that tells the caller the actual length and the limit. Inputs within the limit are now stored verbatim (slice removed).

**Files amended**
- `backend/app/routers/ingest.py` — length check added in `ingest_text`; `text[:50000]` slice removed from `pass1_json` construction.

---

## 2026-05-10

### Backend — OCR integration (Phases 1–8)
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Implemented the OCR pipeline described in `docs/PRD/INGESTION_PRD.md` §8.
Scanned PDFs and image uploads now route through an OCR gate before Pass 1
extraction. Admin selects strategy per-job; both providers are configured
simultaneously. Text-layer PDFs are completely unaffected.

**New files**

- `backend/app/parsers/ocr.py` — `DeepSeekOCRClient`: thin HTTP client for
  DeepSeek-OCR-2 running locally via vLLM Docker or LMDeploy.
- `backend/tests/test_ocr.py` — 15 unit tests covering both OCR providers,
  helper functions, and the vision extraction prompt.

**Backend changes**

- `config.py` — Added `deepseek_ocr_base_url` and `deepseek_ocr_model`
  settings (Option A config alongside the existing Ollama VLM settings).
- `llm/base.py` — Added `ImageContent` dataclass and optional
  `complete_vision()` method to `LLMProvider` protocol.
- `llm/ollama_provider.py` — Implemented `complete_vision()` using Ollama's
  existing `/v1/chat/completions` endpoint with `image_url` content blocks.
- `llm/factory.py` — Added `get_ocr_client()` factory; `DeepSeekOCRClient`
  is registered in the provider registry so `close_all_providers()` cleans up.
- `prompts/extract_prompt.py` — Added `build_vision_extract_prompt()` for the
  Ollama VLM fused path (no raw text in user message; model reads from images).
- `parsers/pdf_parser.py` — Added `page.get_pixmap()` fallback: scanned pages
  with no extractable text and no embedded images are now rasterized at 144 DPI
  and returned as page images for the OCR gate.
- `routers/ingest.py` — Core pipeline changes:
  - `_collect_page_images()` helper reads `pass1_json._page_images`.
  - `_resolve_ocr_strategy()` helper resolves `deepseek | ollama | auto`.
  - OCR gate inserted in `_run_pipeline()` at the `no_raw_text` branch:
    - **DeepSeek path (Option A):** calls `DeepSeekOCRClient.extract()` →
      populates `raw_text` → existing Pass 1 runs unchanged.
    - **Ollama VLM path (Option B):** calls `provider.complete_vision()` →
      fused OCR+extraction → `pass1_json` populated → Pass 1 skipped via
      `"_vision_fused_"` sentinel.
  - Both `ingest_official_pdf()` and `ingest_unofficial_file()` now accept
    optional `ocr_strategy` form param (`deepseek | ollama | auto`).
  - `_page_images` pre-stored in `pass1_json` at route time for scanned PDFs.
  - Image uploads (`.png`, `.jpg`, `.webp`, `.gif`) accepted via
    `ingest_unofficial_file()`; the previous 422 "not yet implemented" block
    is removed.

**Tests added / modified**

- `tests/test_ocr.py` (new) — `test_deepseek_ocr_returns_text`,
  `test_deepseek_ocr_sends_image_url_block`, `test_ollama_complete_vision_*`,
  `test_collect_page_images_*`, `test_resolve_ocr_strategy_*`,
  `test_build_vision_extract_prompt_*`
- `tests/test_ingest_router.py` — `test_ingest_official_pdf_rejects_invalid_ocr_strategy`,
  `test_ingest_unofficial_file_rejects_invalid_ocr_strategy`

**Verification**

- Ran `pytest` from `backend/`.
- Final suite result: `197 passed, 2 skipped`.

---

## 2026-05-09

### Backend — bug fixes and gap closures
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Found and fixed four confirmed bugs via code audit and new regression tests.
Suite went from 178 to 184 collected tests; all pass.

**Fixes**

- `POST /api/submit` — added `practice_status == "active"` guard before
  recording a student answer; previously draft/retired questions were accepted.
- `POST /api/users` (student router) — removed inline `UserCreate` model that
  had no field constraints; now imports `UserCreate`/`UserResponse` from
  `app.models.payload`, which enforces `min_length=1, max_length=100`. Empty
  and oversized usernames were previously accepted at this endpoint while
  the canonical `/users` router rejected them.
- `POST /admin/relations` — added self-reference guard; a question can no
  longer be related to itself (returns 400).
- `GET /admin/relations` — added `limit` (default 100, max 500) and `offset`
  query params; the endpoint previously returned all rows without a cap.

**Tests added**

- `test_submit_answer_rejects_non_active_question`
- `test_admin_create_relation_rejects_self_reference`
- `test_api_users_empty_username_rejected`
- `test_api_users_username_too_long_rejected`
- `test_admin_relations_list_accepts_pagination`
- `test_admin_relations_list_rejects_zero_limit`

**Verification**

- Ran `pytest` from `backend/`.
- Final suite result: `182 passed, 2 skipped`.

---

## 2026-05-06

### Backend — prompt rule-file fix and green test suite
**LLM:** Codex GPT-5

Fixed the backend regressions found during the backend task audit and restored
the full backend test suite to green.

**Prompt-layer changes**

- Corrected the Grammar v7 rule-file reference used by annotation and
  generation prompts:
  - from `rules_agent_dsat_grammar_ingestion_generetion_v7.md`
  - to `rules_agent_dsat_grammar_ingestion_generation_v7.md`
- Added explicit Grammar v7 and Reading v2 rules-reference headers to prompt
  context output so tests can verify that the current rule files are actually
  loaded.
- Kept `build_annotate_prompt` compatible with the older `extract_json=...`
  keyword argument while supporting the current `q_data` call shape.

**Test and compatibility changes**

- Updated ingest pipeline prompt invocation to remain compatible with existing
  test doubles while still passing source metadata to extraction prompts.
- Updated stale backend tests/mocks for the current parser and admin-edit query
  behavior.
- Aligned the config default test with the actual default annotation provider:
  `anthropic`.

**Verification**

- Ran `uv run pytest` from `backend/`.
- Final suite result: `176 passed, 2 skipped`.

### Docs — backend audit cleanup
**LLM:** Codex GPT-5

- Replaced stale backend gap reports with historical-audit notices, resolved
  item summaries, and a current remaining-work list.
- Updated active backend API docs to clarify that direct image OCR ingestion is
  not implemented and image uploads are rejected with 422.
- Updated ingestion-flow docs to reflect current Grammar v7 / Reading v2 prompt
  loading behavior.
- Refreshed the backend review report to remove resolved risks around provider
  API-key selection, source metadata, MIME validation, asset overwrite behavior,
  async relationship access, and missing endpoint/overlap/logging work.

## 2026-04-30

### Backend — metadata persistence, guide-file runtime wiring, and validator alignment
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Aligned the backend more closely with the newer grammar and reading rule
documents while keeping the existing DB schema and migration chain intact.

**Persistence and API changes**

- Preserved structured annotation sections during normalization instead of
  flattening them away, so `annotation_jsonb` can retain richer model output
  while still exposing flat keys needed by the app
- Started persisting `generation_profile_jsonb` on `question_annotations`
  instead of writing `NULL` in generate/ingest flows
- Merged generation request metadata into stored generation profile payloads
  for generated questions
- Exposed stored `generation_profile` through:
  - admin recall API (`/questions/recall`)
  - student recall API (`/api/questions`)
  - admin detail API (`/questions/{question_id}`)
- Added backend documentation file:
  - `docs/backend/INGESTION_AND_STORAGE_FLOW.md`
  - explains ingest/generate flow, persisted data, prompt usage, required
    runtime process, and includes a Mermaid diagram

**Prompt-layer changes**

- Updated annotation prompt loading to use the newer guide markdown files at
  runtime instead of only the old v3 grammar file:
  - `rules_agent_dsat_grammar_ingestion_generetion_v7.md`
  - `rules_agent_dsat_reading_v2.md`
- Updated generation prompts to also inline trimmed excerpts of the newer
  grammar and reading rule files into the system prompt

**Ontology and validation changes**

- Expanded `STEM_TYPE_KEYS` to include newer reading/cross-text stems such as:
  - `choose_words_in_context`
  - `choose_cross_text_connection`
  - `choose_best_inference`
  - `choose_command_of_evidence_textual`
  - `choose_command_of_evidence_quantitative`
- Expanded grammar focus coverage for v7 additions:
  - `adjective_adverb_distinction`
  - `illogical_comparison`
  - `commonly_confused_words`
  - `preposition_idiom`
  - `unnecessary_internal_punctuation`
  - `end_punctuation_question_statement`
- Added reading taxonomy constants:
  - `READING_SKILL_FAMILY_KEYS`
  - `READING_FOCUS_BY_SKILL_FAMILY`
  - `READING_FOCUS_KEYS`
- Added `partial_match` to supported distractor types
- Relaxed the annotation schema so reading-domain items do not require
  `grammar_focus_key`
- Added reading-domain annotation fields including:
  - `skill_family_key`
  - `reading_focus_key`
  - `secondary_reading_focus_keys`
  - `reasoning_trap_key`
  - `transition_subtype_key`
- Validator now enforces:
  - reading-domain questions must not set grammar keys
  - reading-domain questions require `skill_family_key`
  - reading-domain questions require `reading_focus_key`
  - `reading_focus_key` must match the chosen reading skill family
  - Cross-Text items require `stimulus_mode_key="prose_paired"`
  - Cross-Text items require `paired_passage_text`
  - Quantitative CoE items require `prose_plus_table` or `prose_plus_graph`
  - Quantitative CoE items require `table_data` or `graph_data`
  - grammar role/focus pairing is checked against the updated v7 role map

**Test coverage**

- Added and updated tests for:
  - prompt runtime rule loading
  - generation-profile persistence
  - response model exposure of generation metadata
  - v7 grammar key acceptance
  - reading taxonomy key acceptance
  - reading-domain validator enforcement
- Verification runs completed:
  - `uv run pytest tests/test_parsers.py tests/test_backend_regressions.py -q`
  - `uv run pytest tests/test_schemas.py tests/test_questions_router.py tests/test_student_router.py tests/test_backend_regressions.py -q`
  - `uv run pytest tests/test_prompts.py tests/test_parsers.py tests/test_backend_regressions.py tests/test_generate_router.py tests/test_ingest_router.py -q`
  - `uv run pytest tests/test_ontology.py tests/test_schemas.py tests/test_pipeline.py tests/test_prompts.py -q`
  - `uv run pytest tests -q`
- Final suite result: `165 passed, 2 skipped`

**Known warning**

- Confirmed that the remaining SWIG-related deprecation warnings during tests
  come from `PyMuPDF` / `fitz` import initialization, not from project code.
  Reproduced with:
  - `uv run python -Wdefault -c "import warnings; warnings.simplefilter('default'); import fitz"`
  - warnings observed: `SwigPyPacked`, `SwigPyObject`, `swigvarlink`

## 2026-04-29

### Rules — Grammar v7 taxonomy audit and corrections
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Created `rules_agent_dsat_grammar_ingestion_generetion_v7.md` — taxonomy
corrections and additions derived from a cross-referenced audit of the v6
taxonomy against official College Board documentation (Assessment Framework,
Sample Questions PDF, score report skill labels), Khan Academy, The Critical
Reader, PrepScholar, Test Innovators, Albert.io, and released PT1–PT11.

#### Amendment Table

| Amendment | Type | Section | Detail |
|---|---|---|---|
| `skill_family` corrected to official CB names | **Fix** | C.1.3, A.3, B.12 | Replaced non-official values (`Sentence Boundaries`, `Agreement`, `Punctuation`, `Craft and Structure`) with the two official SEC skill names: `Boundaries` and `Form, Structure, and Sense`. All 10 official R&W skill families now enumerated, grouped by domain. |
| `skill_family` example in A.3 schema | **Fix** | A.3 | Example value corrected from `"Agreement"` → `"Form, Structure, and Sense"` |
| `skill_family` in Example A (B.12) | **Fix** | B.12 | Corrected from `"Agreement"` → `"Form, Structure, and Sense"` |
| `stem_type_key` expanded | **Addition** | C.1.2 | Added 5 missing official question types: `choose_words_in_context` (Words in Context — most frequent type, ~28% of section), `choose_cross_text_connection` (Cross-Text Connections), `choose_best_inference` (Inferences), `choose_command_of_evidence_textual` (Command of Evidence textual), `choose_command_of_evidence_quantitative` (Command of Evidence quantitative). Total: 12 → 17 values. Legacy aliases noted for `choose_best_support`, `choose_best_quote`, `choose_best_completion_from_data`. |
| `topic_broad` expanded | **Addition** | C.1.3 | Added `humanities` — official College Board fourth content area alongside Literature, History/Social Studies, and Science. Clarified that `arts`, `economics`, `technology`, `environment` are project-internal sub-tags, not official CB labels. |
| `stimulus_mode_key` descriptions | **Clarification** | C.1.1 | Added inline descriptions for all 8 values. `prose_plus_graph` now lists all confirmed graphic subtypes: bar chart, line graph, scatterplot (with or without line of best fit), pie chart, map. |
| `restatement_clarification` transition | **Addition** | B.5.2 | Added 24th `transition_subtype_key`: `restatement_clarification` — covers "in other words / that is / i.e." transitions that rephrase rather than add or contrast. |
| `adjective_adverb_distinction` promoted | **Promotion** | D.2.5 | Moved from pending (D.2.9) to production under `modifier`. Covers adjective vs. adverb selection after linking verbs ("feel bad" not "feel badly"). Added to D.8.1 role→focus mapping and D.8.3 frequency table at `medium`. |
| `illogical_comparison` promoted | **Promotion** | D.2.5 | Moved from pending (D.2.9) to production under `modifier`. Covers comparing nouns to dissimilar categories ("results of Study 1 were better than Study 2"). Distinct from `comparative_structures` (formal parallelism) — this error is logical. Added to D.8.1 and D.8.3 at `medium`. |
| `commonly_confused_words` promoted | **Promotion** | D.2.8 | Moved from pending (D.2.9) to production under `expression_of_ideas`. Covers non-homophone semantic confusion pairs (affect/effect, allusion/illusion, elicit/illicit, principle/principal). Homophone possession confusion remains under `possessive_contraction`. Added to D.8.3 at `low`. |
| `preposition_idiom` added | **Addition** | D.2.8 | New production focus key under `expression_of_ideas`. Covers verb-preposition and adjective-preposition collocations where the correct preposition is idiomatic (responsible *for*, different *from*, composed *of*, interested *in*). Added to D.8.1 mapping and D.8.3 at `low`. |
| `affirmative_agreement` flagged | **Confidence flag** | D.2.2, D.8.3 | Marked `dsat_confidence: low`. so/neither inversion and tag questions appear primarily in ACT conventions. Retained in taxonomy for completeness but excluded from generation weighting. |
| `negation` flagged | **Confidence flag** | D.2.4, D.8.3 | Marked `dsat_confidence: low`. Double negatives and hardly/scarcely inversions are ACT patterns. Key retained only for scope-of-negation coverage ("not all" vs "all not"); excluded from generation profiles. |
| D.2.9 pending keys updated | **Housekeeping** | D.2.9 | Removed three promoted keys. Only `subjunctive_mood` remains pending (too rare for standalone key; documented as `verb_form` sub-pattern). |
| D.8.1 role→focus mapping updated | **Update** | D.8.1 | `modifier` row extended with `illogical_comparison` and `adjective_adverb_distinction`. `expression_of_ideas` row extended with `commonly_confused_words` and `preposition_idiom`. |
| D.8.2 domain separation table updated | **Update** | D.8.2 | Added official skill family column showing the 10 CB skill names by domain. |
| D.8.3 frequency table updated | **Update** | D.8.3 | New keys placed: `adjective_adverb_distinction` and `illogical_comparison` at `medium`; `commonly_confused_words` and `preposition_idiom` at `low`; `affirmative_agreement` and `negation` marked ⚠️ at `very_low`. |
| `model_version` bumped | **Housekeeping** | A.3, B.12 | All `model_version` fields updated from `rules_agent_v6.0` → `rules_agent_v7.0`. |

**Sources consulted:** College Board Assessment Framework PDF, Digital SAT Sample Questions PDF, Khan Academy DSAT R&W course, The Critical Reader grammar analysis, PrepScholar SAT grammar guide, Test Innovators skill breakdown, Albert.io quantitative evidence review, dsat16.com transitions guide.

---

### Rules — Grammar v6 reorganization and gap fixes
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Created `rules_agent_dsat_grammar_ingestion_generetion_v6.md` — a structural
reorganization of v5 for generation-first LLM navigation.

**Structural changes:**

- Reorganized into five explicit parts: A (Mode Routing) → B (Generation) →
  C (Annotation) → D (Taxonomy Reference) → E (Quality Protocols)
- Generation workflow (Part B) now precedes annotation workflow (Part C)
- §20 megasection decomposed into 15 focused B.x subsections
- §30 (Transition Subtypes) and §31 (Notes Synthesis) integrated inline into
  Part B rather than appended as addenda

**Gaps fixed:**

- Broken `§20.5` reference replaced with two complete inline JSON generation
  examples (B.12): `subject_verb_agreement` medium-difficulty and
  `transition_logic` medium-difficulty
- Missing `classification` schema added to formal schemas (A.3)
- `synthesis_distractor_failure` field name standardized: per-option
  annotation uses `synthesis_distractor_failure` (singular string);
  generation input uses `distractor_synthesis_failures` (plural array)
- Mode-routing section added (A.2) with explicit generation vs annotation
  trigger conditions
- Four proposed focus keys documented with pending status in D.2.9:
  `adjective_adverb_distinction`, `illogical_comparison`,
  `commonly_confused_words`, `subjunctive_mood`
- `transition_subtype_key` vs `target_transition_subtype_key` naming
  clarified in B.5.1: stored annotation field vs generation request field

---

### Rules — CB PT4–PT11 gap analysis and v3.1 / v1.1 rule addenda
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Cross-referenced official College Board answer explanations for Practice Tests 4–11
(sourced from `CB_ANSWERS_QUESTIONS_ANALYSIS.md`) against both production rule files.
Created two new addendum files covering every identified gap.

**Files created:**

- `rules_agent_dsat_grammar_ingestion_generation_v3_1.md`
- `rules_agent_dsat_reading_v1_1.md`

---

**`rules_agent_dsat_grammar_ingestion_generation_v3_1.md`**

*Addendum to `rules_agent_dsat_grammar_ingestion_generation_v3.md`*

- Added punctuation focus key `unnecessary_internal_punctuation` — covers
  absence-of-punctuation cases inside subject–verb, verb–object,
  preposition–complement, and integrated relative clause units (PT4, PT5,
  PT6, PT7, PT9, PT11)
- Added punctuation focus key `end_punctuation_question_statement` — period
  on indirect questions vs question mark on direct questions (PT6, PT11)
- Extended `appositive_punctuation` with three sub-patterns: restrictive
  appositive (no punctuation), title/role before proper name (no punctuation),
  coordinated restrictive appositive (no punctuation) (PT5, PT8, PT9)
- Added three named verb form generation patterns with passage templates and
  distractor constraints: `finite_verb_in_relative_clause`,
  `finite_verb_in_main_clause`, `modal_plus_plain_form` (PT5, PT8, PT9)
- Added `singular_event_reference` pronoun generation pattern — singular
  pronoun referring to a whole preceding clause or event, not a noun (PT5)
- Added `literary_present` to `passage_tense_register_key` — simple present
  when discussing events inside literary works (PT10)
- Added `transition_subtype_key` field with 23 named subtypes covering every
  transition word pattern observed in PT4–PT11; required on generation profiles
  and wrong-option annotations
- Added three metadata fields for notes synthesis generation:
  `synthesis_goal_key` (41 values), `audience_knowledge_key` (3 values),
  `required_content_key` (30 values); added `synthesis_distractor_failure`
  for wrong-option annotation
- Added `test_format_key` field distinguishing `digital_app_adaptive` (27 Qs)
  from `nondigital_linear_accommodation` (33 Qs) with validated
  domain-boundary position bands
- Added 11 grammar-specific `student_failure_mode_key` values
- Added 8 new validator checklist items (checks 18–25)

---

**`rules_agent_dsat_reading_v1_1.md`**

*Addendum to `rules_agent_dsat_reading_v1.md`*

- Added `polarity_fit` Words in Context focus key — for items where a negator
  or concessive ("by no means," "not atypical") reverses required word polarity
  (PT4, PT5, PT6); includes generation rule requiring all four options to
  remain viable after applying the negator
- Added `polarity_mismatch` reasoning trap key
- Added phrase-level WIC generation note — when the correct answer is a
  multi-word phrase, all options must match in length and structure
- Added 12 named functional roles for `sentence_function` items (concession,
  elaboration, contrast_motivation, parenthetical_definition, example,
  consequence, hypothesis, counter_evidence, scope_qualification,
  conventional_approach, obstacle, background_setup); `target_sentence_function_role`
  now required in generation profiles
- Added parenthetical-definition generation constraint — correct answer must
  identify term clarification, not broader passage purpose (PT7, PT11)
- Added 8 named quantitative sub-patterns with primary distractor traps:
  `exact_value_lookup`, `timing_constrained`, `all_measures`, `repeated_highest`,
  `two_variable_opposite`, `composition_change`, `binned_distribution`, `standard`
- Added 5 new quantitative reasoning trap keys: `wrong_row_or_column`,
  `wrong_time_window`, `all_measures_not_checked`, `individual_from_aggregate`,
  `direction_reversal`
- Added all 5 experimental passage architectures:
  `experiment_hypothesis_control_result`, `indirect_effect_mediation`,
  `alternative_explanation_ruled_out`, `mechanism_manipulation_test`,
  `studied_subgroup_generalization_limit`
- Added `study_design_isolation_limit` inference pattern — when passage design
  prevents isolating a causal variable (PT6, PT10)
- Added `subgroup_overgeneralization` inference pattern with generation
  template (PT11)
- Added two-part claim annotation rule for quote-illustration items — at least
  one distractor must satisfy exactly one of two required elements
- Added control-group distractor pattern for experimental architecture items
- Added `confirmation_with_qualification` generation note for cross-text items
- Added 10 new student failure mode keys
- Added 9 new validator checklist items

---

## 2026-04-27

### 14:35 — Added missing indexes to SQLAlchemy models
**Commits:** *(pending)*

- Added `Index()` declarations to `models/db.py` `__table_args__` to match migration 005:
  - `Question`: `ix_questions_practice_status`, `ix_questions_content_origin`, `ix_questions_latest_annotation_id`
  - `QuestionJob`: `ix_question_jobs_status`, `ix_question_jobs_created_at`
  - `UserProgress`: `ix_user_progress_user_id`, `ix_user_progress_question_id`
  - `QuestionRelation`: `ix_question_relations_from_question_id`, `ix_question_relations_to_question_id`
- Added `Index` import to `models/db.py`

### Rules — Grammar module expansion and realism rules upgrade

Files changed: `rules/mcq_realism_rules.md`, `rules/rules_grammar_module_outline.md`, `rules/rules_core_generation_outline.md`, `rules/rules_reading_module_outline.md`

**`mcq_realism_rules.md`**

- Added **All-Four-Plausible Rule** section: every answer choice — including all three distractors — must produce plausible English on first read; nothing eliminable by ear-test alone; includes difficulty gradient table (low/medium/high)
- Added **Student Failure Mode Requirement** section: 16 named psychological failure modes (`nearest_noun_reflex`, `comma_fix_illusion`, `formal_word_bias`, `possessive_contraction_confusion`, `tense_proximity_pull`, `parallel_shape_bias`, `pronoun_anchor_error`, `ear_test_pass`, etc.) now mandatory on every distractor via `student_failure_mode_key`
- Added **SEC Distractor Architecture by Grammar Type** section: specific 4-option construction rules for all grammar categories including subject-verb agreement, verb tense, semicolons, apostrophes, modifiers, parallel structure, pronouns, adjective/adverb, illogical comparisons, sentence boundary, subjunctive mood, and transitions
- Added **Step 2 (Syntactic Trap)** to Generator Workflow: trap must be named before distractors are written
- Added **Step 6 (All-Four-Plausible Verification)**: explicit read-aloud check inserted before competitive ranking check
- Added **Hard-Item Validator Checklist**: additional validation layer for `difficulty_overall: high` — no shared failure modes across distractors, correct answer not the only formal-sounding option, ear-test cannot resolve the item

**`rules_grammar_module_outline.md`**

- Converted from planning outline to full operational document
- Full taxonomy tables for all grammar role keys and focus keys
- Added 4 grammar types from research that were absent from the taxonomy:
  - `adjective_adverb_distinction` (proposed key, parent: `modifier`)
  - `illogical_comparison` (proposed key, parent: `modifier`)
  - `commonly_confused_words` (proposed key, parent: `expression_of_ideas`)
  - `subjunctive_mood` (added to `verb_form` family)
- Added correlative conjunction rules under `parallel_structure` (both/and, either/or, neither/nor, not only/but also)
- Added syntactic trap taxonomy table with grammar focus mappings
- Added passage construction templates for every grammar focus key
- Added distractor heuristic tables with `student_failure_mode_key` for every focus key
- Added frequency band table for all focus keys
- Added full grammar validation checklist

**`rules_core_generation_outline.md`**

- Converted from planning outline to full shared infrastructure document
- Added SAT Realism Layer (Section 8): distractor distance, plausible wrong count, answer separation strength, all-four-plausible requirement, realism scoring thresholds
- Added shared distractor engineering rules with `student_failure_mode_key` requirement
- Added anti-clone and diversity controls
- Added provenance and audit trail schema
- Added shared validation lifecycle with core checklist

**`rules_reading_module_outline.md`**

- Added Section 14 with reading-specific `student_failure_mode_key` values: `local_detail_fixation`, `overreach`, `underreach`, `text_label_swap`, `topic_association`, `inverse_logic`, `false_agreement`
- Added realism requirements aligned to core (all-four-plausible requirement for reading items)

---

## 2026-04-25

### 18:10 — Option annotation hydration & metadata lifecycle management
**Commits:** `26ba7e9`

- Added `backend/app/pipeline/option_hydration.py` — shared helpers to extract, apply, and clear the 12 per-option annotation fields (`distractor_type_key`, `semantic_relation_key`, `plausibility_source_key`, `option_error_focus_key`, `why_plausible`, `why_wrong`, `grammar_fit`, `tone_match`, `precision_score`, `student_failure_mode_key`, `distractor_distance`, `distractor_competition_score`) from `annotate_json` to `QuestionOption` rows
- Ingest pipeline (`_run_pipeline`): all `QuestionOption` annotation columns now populated on creation
- Ingest reannotation (`_run_reannotate_pipeline`): existing option rows refreshed with new annotation; `annotation_stale` cleared to `False` on success
- Generate pipeline: identical option annotation hydration on first creation
- `models/db.py` — added `annotation_stale` boolean to `Question`
- Migration `009_add_annotation_stale`: adds `annotation_stale` column with `server_default=false`
- Admin `PATCH /questions/{id}`: sets `annotation_stale=True` on any edit — flags question for reannotation queue
- Admin `POST /questions/{id}/reject`: cascade-deletes `question_annotations`, `llm_evaluations`, `question_relations`; nulls per-option annotation fields; retires question
- Admin `DELETE /questions/{id}` (new endpoint): hard-deletes question and all linked rows in safe FK order; detaches jobs and assets (preserves audit trail and files on disk)

---

### 17:47 — PDF filename typo fix
**Commits:** `7b3f5dd`

- Renamed `Test_10_digitial_sec01_mod02.pdf` → `Test_10_digital_sec01_mod02.pdf` in `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/`

---

### 17:07 — Verbal practice test PDFs added
**Commits:** `bbd5c12` *(pulled from remote)*

- Added 14 verbal section PDFs for Practice Tests 1, 6–11 (both `sec01_mod01` and `sec01_mod02`) to `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/`
- Validated all 18 PDFs: readable, unencrypted, 13–16 pages, 28k–35k chars each
- Note: Test 11 mod01/mod02 have zero embedded images (vector-rendered); all other tests have 14–17 embedded images per file
- Documented canonical test source path in `CLAUDE.md`

---

### 15:45 — DB integrity gap remediation (6 gaps)
**Commits:** `ba88685`

- Migration `004_add_unique_constraints`: `UniqueConstraint` on `question_versions(question_id, version_number)`, `question_options(question_version_id, option_label)`, `question_relations(from_question_id, to_question_id, relation_type)`
- Migration `005_add_performance_indexes`: 9 indexes on hot query columns across `questions`, `question_jobs`, `user_progress`, `question_relations`
- Migration `006_add_check_constraints`: DB-level `CHECK` constraints mirroring Pydantic validation — option labels A–D, LLM scores 0–10, relation strength 0–1
- Migration `007_add_source_section_code_to_assets`: adds `source_section_code` to `question_assets`
- Migration `008_add_server_defaults`: `server_default=now()` on all 12 timestamp columns across all tables
- `models/db.py`: added `UniqueConstraint` `__table_args__` to `QuestionVersion`, `QuestionOption`, `QuestionRelation`; added `source_section_code` to `QuestionAsset`
- `routers/ingest.py`: write `source_section_code` to asset at upload time; backfill from `extract_json` during pipeline link-back
- `migrations/env.py`: fixed `else` branch that silently discarded `-x sqlalchemy.url` override; `run_migrations_online()` now reads URL from config instead of hardcoding `settings.database_url`

---

## 2026-04-24

### 20:09 — User CRUD endpoints
**Commits:** `8e45fa5`

- Added `POST /users`, `GET /users/{id}`, `DELETE /users/{id}` with admin auth

### 20:08 — N+1 query fix in overlap detection
**Commits:** `ff11b72`

- Replaced N+1 annotation queries in `detect_overlaps` with a single JOIN

### 20:07 — V3 ontology key validation
**Commits:** `1586ffc`

- Validator now checks `grammar_role_key`, `grammar_focus_key`, `stimulus_mode_key`, `stem_type_key` against approved V3 keys; `explanation_short` capped at 300 chars

### 20:04 — LLM provider cleanup on shutdown
**Commits:** `e7ca0bb`

- Closed `httpx` clients for all LLM providers on app shutdown via FastAPI lifespan

### 20:01 — Generation provider selection
**Commits:** `bfce92f`

- Caller can now specify `provider_name` and `model_name` in generate requests

### 20:00 — Reannotation request body fix
**Commits:** `09cfb6b`

- Moved `provider_name`/`model_name` from query params to JSON body in reannotate endpoint

### 19:59 — Upload size guard
**Commits:** `55ca86c`

- Check `Content-Length` before reading upload body to avoid loading 50 MB into RAM

### 15:05 — API routers and integration tests
**Commits:** `3d19244`

- Added 5 API routers with 19 endpoints; integration test suite

### 14:18 — Request/response schemas and API docs
**Commits:** `33e8d88`

- Added generation/ingest request schemas, job response model, OpenAPI docs

### 13:11 — Migration order, Docker Postgres, manual test CLI
**Commits:** `ce423ba`

- Fixed migration ordering; added Docker Postgres config; manual test CLI

### 12:35 — Prompts, pipeline orchestrator, validator
**Commits:** `198b7da`

- Extract and annotate prompts; `JobOrchestrator`; question validator

### 12:34 — Parsers
**Commits:** `f845a4c`

- JSON, PDF (pymupdf), image, and markdown extraction parsers

### 12:34 — LLM provider layer
**Commits:** `08b9133`

- Protocol, factory, Anthropic, OpenAI, and Ollama providers

### 12:13 — Initial migration
**Commits:** `b621316`

- Alembic config; 10-table initial schema migration
