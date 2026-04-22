# DSAT Ingestion Backend — Completion Reference

**Branch:** `alpha-v3-codex`  
**Test suite:** 324 passing  
**Database:** Supabase PostgreSQL (migrations 001–040)  
**Base path:** `FULL_PLAN/backend/`

This document describes every finished component: what it does, what triggers it, and how data flows through it.

---

## Table of Contents

1. [Application Bootstrap](#1-application-bootstrap)
2. [Authentication](#2-authentication)
3. [Ingestion Pipeline (Pass 1 + Pass 2)](#3-ingestion-pipeline-pass-1--pass-2)
4. [Job Management](#4-job-management)
5. [Validation](#5-validation)
6. [Upsert (Approval Write)](#6-upsert-approval-write)
7. [Pass 3: Token Annotation](#7-pass-3-token-annotation)
8. [IRT Refresh](#8-irt-refresh)
9. [Coaching Annotation](#9-coaching-annotation)
10. [Embeddings](#10-embeddings)
11. [Drift Detection](#11-drift-detection)
12. [Generation Pipeline](#12-generation-pipeline)
13. [Grammar Practice Endpoint](#13-grammar-practice-endpoint)
14. [Semantic Search](#14-semantic-search)
15. [Ontology + Proposals](#15-ontology--proposals)
16. [Questions Read API](#16-questions-read-api)
17. [File Parsers](#17-file-parsers)
18. [Data Models](#18-data-models)

---

## 1. Application Bootstrap

**Files:** `app/main.py`, `app/config.py`, `app/database.py`

### Startup sequence

`create_app()` builds the FastAPI application and registers all routers. On first request (or server start), the `lifespan` async context manager runs:

1. **`get_settings()`** — reads `Settings` from `.env` via `pydantic-settings`. Singleton cached in `_settings`. Fields: `supabase_db_url`, `llm_provider`, `llm_model`, `api_key`, LLM API keys, `pass1_max_tokens`, `pass2_max_tokens`, `max_file_upload_mb`.
2. **`create_pool(dsn)`** — creates an `asyncpg` connection pool. `_init_connection` sets `pgvector` codec on each connection so `vector` columns return Python lists.
3. **`_load_ontology(conn)`** — fetches all lookup table keys from Supabase (`SELECT key FROM public.lookup_*`) and stores them in `app.state.ontology` dict. Also loads `skill_family_domain_map` for cross-field taxonomy validation.

### Router registration

All routers are registered with `dependencies=[Depends(require_api_key)]` except `/health`:

| Prefix | Router file |
|--------|-------------|
| `/ingest` | `app/routers/ingest.py` |
| `/jobs` | `app/routers/jobs.py` |
| `/questions` | `app/routers/questions.py` |
| `/ontology` | `app/routers/ontology.py` |
| `/search` | `app/routers/search.py` |
| `/generate` | `app/routers/generate.py` |
| `/health` | inline in `main.py` — public |

---

## 2. Authentication

**File:** `app/auth.py`  
**Triggered by:** every request to a protected router

### `require_api_key(x_api_key)`

FastAPI dependency injected via `Header(default=None)`. Reads the `X-API-Key` header.

| Condition | Response |
|-----------|----------|
| `settings.api_key == ""` | Pass-through (dev mode, auth disabled) |
| Header missing | `401 Missing X-API-Key header` |
| Header present but wrong | `403 Invalid API key` |
| Header matches `settings.api_key` | Passes through to route handler |

**Config:** `API_KEY` in `.env`. Empty string disables auth (local dev). `fake.api_key = ""` in `tests/conftest.py` keeps all tests auth-free.

---

## 3. Ingestion Pipeline (Pass 1 + Pass 2)

**Files:** `app/routers/ingest.py`, `app/pipeline/ingest.py`

### Entry points

#### `POST /ingest` — text or JSON input
Accepts `raw_text` (string) or `json_data` (dict). Creates a job row and immediately runs `process_job` as a `BackgroundTask`.

#### `POST /ingest/file` — PDF, image, or markdown upload
1. Reads file bytes, enforces `max_file_upload_mb` limit.
2. Sniffs content type → routes to parser:
   - `pdf` → `parse_pdf()` via `asyncio.to_thread` (non-blocking)
   - `image/*` → `parse_image()` via `asyncio.to_thread`
   - `.md` → raw text passthrough
   - `.json` → parsed as dict
3. Creates job, runs `process_job` as `BackgroundTask`.

#### `POST /ingest/batch` — multiple text items
Creates one job per item, runs each `process_job` as a separate `BackgroundTask`. Returns all job records.

### `create_job(conn, source_file, input_format, raw_text, status, llm_provider, llm_model)`

Inserts a row into `public.question_ingestion_jobs` with status `'extracting'`. Returns `job_id` (UUID).

### `process_job(pool, settings, ontology, job_id, raw_text, provider, model, content_origin)`

The core two-pass LLM pipeline:

**Pass 1 — Extraction**
- For `content_origin='generated'` jobs where `pass1_json` is already set: skips LLM call, decodes existing JSON.
- Otherwise: calls `provider.complete(system=PASS1_SYSTEM, user=raw_text)` — LLM extracts question stem, A-D choices, correct answer, explanation, stimulus mode, stem type, source metadata.
- Strips markdown fences, parses JSON, stores result in `pass1_json` column.
- On failure: sets status `'failed'`, writes error to `validation_errors_json`, returns.

**Pass 2 — Annotation**
- Calls `provider.complete(system=build_pass2_system_prompt(ontology), user=pass1_json)` — LLM classifies the question across ~55 taxonomy dimensions (domain, skill family, syntactic complexity, rhetorical structure, distractor types, generation profile targets, etc.).
- Strips fences, parses JSON, stores in `pass2_json`.
- On failure: sets status `'failed'`, returns.

**Validation**
- Constructs `QuestionExtract` and `QuestionAnnotation` Pydantic models from JSON.
- Calls `validate_payload(extract, annotation, ontology, content_origin=content_origin)`.
- Runs duplicate detection: hashes question content, checks `public.questions.content_hash`.
- Collects unknown lookup values into `ontology_proposals` table via `collect_ontology_proposals` + `upsert_proposals`.
- Sets status `'reviewed'` if no errors, `'draft'` if validation errors present.

---

## 4. Job Management

**File:** `app/routers/jobs.py`

### `GET /jobs`
Lists `question_ingestion_jobs` with optional `status`, `source_file`, `limit`, `offset` filters. Returns `IngestionJobRead` schema (id, status, pass1_json, pass2_json, validation_errors_json, timestamps, linked question_id).

### `GET /jobs/{job_id}`
Fetches a single job by UUID.

### `PATCH /jobs/{job_id}/status`

The approval endpoint. Accepts `{"status": "approved" | "rejected" | "draft", "review_notes": "..."}`.

**Approval flow:**
1. Validates `pass1_json` and `pass2_json` are present.
2. Re-validates `QuestionExtract` + `QuestionAnnotation` Pydantic models.
3. Opens `asyncpg` transaction:
   - `upsert_question(conn, extract, annotation, content_origin=job_content_origin)` — writes question + all downstream rows.
   - Updates job: `status='approved'`, `review_notes`, `question_id`.
   - Resets `questions.tokenization_status='pending'` — invalidates any prior tokenization.
4. After transaction commits, registers `BackgroundTask`s:
   - `_refresh_irt(pool, question_id)` — corpus-wide IRT refresh.
   - `tokenize_question(pool, settings, question_id)` — Pass 3 token annotation.
   - `generate_coaching_for_question(pool, settings, question_id)` — only for `content_origin='generated'`.

### `POST /jobs/{job_id}/rerun`
Resets job to `'pending'`, re-runs `process_job` as `BackgroundTask` with the stored LLM provider/model.

---

## 5. Validation

**File:** `app/pipeline/validator.py`  
**Called by:** `process_job` after Pass 2

### `validate_payload(extract, annotation, ontology, *, content_origin='official')`

Returns `list[ValidationError]`. Empty list = clean.

**Pass 1 checks:**
- `stem` non-empty
- `choices` has exactly keys A, B, C, D
- `correct_option_label` in choices
- `stimulus_mode_key`, `stem_type_key` valid against ontology

**Pass 2 classification checks (30+ fields):**
All `*_key` fields in `QuestionAnnotation.classification` checked via `is_valid_key(ontology, field, value)` — looks up `ontology["lookup_{field_table}"]`.

**Cross-field checks:**
- `skill_family_key` must belong to `domain_key` per `skill_family_domain_map`
- `generation_profile.target_skill_family_key` must match `target_domain_key`

**Options checks:**
- Exactly 4 options covering A, B, C, D
- Exactly 1 correct option
- Each option's `distractor_type_key`, `semantic_relation_key`, `plausibility_source_key` valid

**Reasoning + generation profile checks:**
- `clue_distribution_key`, `hidden_clue_type_key` valid
- 10+ generation target `*_key` fields valid

---

## 6. Upsert (Approval Write)

**File:** `app/pipeline/upsert.py`  
**Called by:** `PATCH /jobs/{id}/status` approval path, inside transaction

### `upsert_question(conn, extract, annotation, *, content_origin='official')`

Writes to 5 tables atomically (inside the caller's transaction):

**Official questions** (`content_origin='official'`):
- Requires `source_exam_code`, `source_module_code`, `source_question_number`.
- Resolves `exam_id`, `section_id`, `module_id` via JOIN on `exams → exam_sections → exam_modules`.

**Generated questions** (`content_origin='generated'`):
- Skips source lookup entirely.
- Stores `exam_id=NULL`, `section_id=NULL`, `module_id=NULL`, `source_type='generated'`, `is_official=false`.

**Writes (in order):**
1. `public.questions` — UPSERT on `(module_id, source_question_number)`. All core fields including `prompt_text`, `passage_text`, `correct_option_label`, `explanation_short/full`, `content_hash`. Returns `question_id`.
2. `public.question_classifications` — all ~55 taxonomy annotation fields.
3. `public.question_options` — 4 rows (A–D) with `option_text`, `is_correct`, distractor metadata.
4. `public.question_reasoning` — coaching summary, common error, clue distribution, evidence flags.
5. `public.question_generation_profiles` — all `target_*` fields, annotation confidence, reuse flag.

Returns `question_id` UUID.

---

## 7. Pass 3: Token Annotation

**Files:** `app/pipeline/tokenize.py`, `app/prompts/pass3_tokenization.py`  
**Triggered by:** `BackgroundTask` after job approval

### `tokenize_question(pool, settings, question_id)`

Non-fatal: all exceptions logged, never raised. Designed for fire-and-forget.

**Flow:**
1. Fetches `prompt_text` + `correct_option_label` from `public.questions`.
2. If row missing: logs warning, returns early (no status change).
3. Fetches `option_text` for the correct answer from `public.question_options`.
4. Fetches grammar key registry: `SELECT id, description FROM public.grammar_keys ORDER BY id`.
5. Calls `build_pass3_system_prompt(key_rows)` — assembles LLM system prompt with grammar registry sourced from DB (not hardcoded). Registry drives both prompt and validation.
6. Calls LLM: `provider.complete(system=system_prompt, user=build_pass3_user_prompt(prompt_text, correct_answer), temperature=0.0, max_tokens=1024)`.
7. Strips markdown fences, parses JSON array of token objects.
8. **Validates token contract:**
   - All fields present and typed: `token_index` (int), `token_text` (str), `is_blank` (bool), `grammar_tags` (list[str])
   - No duplicate `token_index` values
   - All `grammar_tags` must be in `valid_tags` (fetched from DB)
   - Exactly 1 token with `is_blank=True`
9. On validation failure: calls `_set_status(pool, question_id, 'failed')`, returns.
10. **Atomic write** via `asyncpg` transaction:
    - `DELETE FROM public.question_token_annotations WHERE question_id=$1`
    - `executemany INSERT INTO public.question_token_annotations (question_id, token_index, token_text, is_blank, grammar_tags)`
    - `UPDATE public.questions SET tokenization_status='ready' WHERE id=$1`
11. On any exception in write: `_set_status(pool, question_id, 'failed')`.

### `_set_status(pool, question_id, status)`
Helper: acquires pool connection, updates `questions.tokenization_status`. Used for both `'ready'` (inline in transaction) and `'failed'` (on error).

### `build_pass3_system_prompt(key_rows)`
Assembles system prompt from `_PASS3_PREAMBLE` + dynamic registry lines (`- {id}: {description}` per row) + `_PASS3_SUFFIX` (rules + output format). Tag list matches DB exactly.

---

## 8. IRT Refresh

**File:** `app/routers/jobs.py` (`_refresh_irt`)  
**Triggered by:** `BackgroundTask` after job approval (concurrent with Pass 3)

### `_refresh_irt(pool, question_id)`

Calls `SELECT public.fn_refresh_irt_b(NULL::uuid)` — the corpus-wide form of the IRT function. Refreshes b-estimates for all questions where `irt_b_rubric_version = 'v1'` or not yet set. Using `NULL` (rather than the per-question UUID form) ensures that batch approval sequences — where many jobs are approved sequentially — are fully covered in one pass.

Non-fatal: exceptions caught and silently swallowed.

**Function defined in:** migration `033_irt_b_rubric.sql`. Applies a weighted rubric (difficulty, syntactic complexity, reasoning demand, etc.) to compute a difficulty parameter proxy. Empirical values will overwrite at scale.

---

## 9. Coaching Annotation

**File:** `app/pipeline/coaching.py`  
**Triggered by:** `BackgroundTask` after approval of `content_origin='generated'` jobs only

### `generate_coaching_for_question(pool, settings, question_id)`

Generates character-offset span annotations linking coaching notes to specific text locations.

**Flow:**
1. Fetches question row + coaching summary from `question_reasoning`.
2. Locates spans: `_find_span(text, span_text)` searches `prompt_text` and `passage_text` for coaching-relevant substrings, returns `(start_char, end_char, sentence_index)`.
3. Writes to `public.question_coaching_annotations`: coaching text, `span_start_char`, `span_end_char`, `span_sentence_index` (fallback when char offsets are stale).

Non-fatal: exceptions logged.

---

## 10. Embeddings

**File:** `app/pipeline/embeddings.py`  
**Triggered by:** generation pipeline and semantic search

### `build_embedding_texts(row)`

Constructs up to 5 weighted text representations from a question row:
- `passage_only` — full passage text (primary for semantic similarity)
- `style_fingerprint` — concatenates prose register, tone, source type, topic domain, syntactic complexity (primary for style-targeted retrieval)
- `stem_only` — question stem text
- `distractor_profile` — distractor type + semantic relation patterns
- `full_context` — all of the above combined

### `get_embedding(text)` / `get_embeddings_batch(texts)`

Calls OpenAI `text-embedding-3-small` (1536 dimensions). Batch form for efficiency.

### Storage

Embeddings stored in `public.question_embeddings` using `pgvector` (`vector(1536)`) with IVFFlat index. `fn_rebuild_embedding_index()` rebuilds the index (call at 500+ rows for meaningful ANN performance).

---

## 11. Drift Detection

**File:** `app/pipeline/drift.py`  
**Called by:** generation pipeline after Pass 2 re-classification of a generated question

### `compute_expected_fingerprint(snapshot)`

Converts `target_*` columns from `question_generation_profiles` into an expected taxonomy fingerprint dict.

### `detect_drift(expected, actual)`

Compares expected vs actual classification on key style dimensions. Returns a `DriftReport` dataclass:
- `drifted_fields: list[str]` — dimensions where LLM didn't match the spec
- `drift_score: float` — fraction of dimensions that drifted
- `difficulty_drifted: bool`
- `syntax_drifted: bool`

### `should_rerun(report, attempt)`

Returns `True` if `drift_score > threshold` and `attempt < 3`. Controls the 3-attempt retry loop in the generation pipeline.

---

## 12. Generation Pipeline

**Files:** `app/routers/generate.py`, `app/pipeline/generate.py`

### Entry point: `POST /generate`

Accepts `target_question_family_key`, `count`, `seed_question_id` (optional), and generation parameters. Creates a run record, starts `process_generation_run` as a `BackgroundTask`. Returns `run_id` immediately.

### `create_generation_run(pool, settings, ontology, ...)`

Inserts a row into `public.generation_runs` with status `'queued'`. Returns `run_id`.

### `select_seed_question(conn, target_*, ...)`

If no `seed_question_id` supplied: queries `public.question_embeddings` using cosine similarity against the target style fingerprint to find the best matching exemplar question. Uses IVFFlat ANN search.

### `_load_seed_content(conn, question_id)` / `_load_generation_profile(conn, question_id)`

Fetches full question content and generation target spec from Supabase to build the generation prompt.

### `process_generation_run(pool, settings, ontology, run_id, ...)`

Main generation loop. For each item (up to `count`):

**Attempt loop (max 3):**
1. Builds generation prompt from seed question content + target spec.
2. Calls LLM to generate a new question JSON.
3. Calls LLM again for realism scoring — assigns `realism_score` (0–1) and flags `fatal_issues`.
4. If score below threshold or fatal issues: logs and retries.
5. Writes generated question to `public.question_ingestion_jobs` with `content_origin='generated'`, `pass1_json` pre-filled.
6. Calls `process_job(...)` — runs Pass 2 annotation + validation against ontology.
7. Runs drift detection: `detect_drift(expected_fingerprint, actual_classification)`.
8. If `should_rerun(drift_report, attempt)`: retries.
9. On success: records drift flags in `public.generated_questions`.

**Status tracking:** Run status transitions `queued → running → completed/failed`. Per-item status in `public.generated_questions`.

### Read endpoints

- `GET /generate/runs` — list all generation runs
- `GET /generate/runs/{run_id}` — single run status
- `GET /generate/runs/{run_id}/questions` — all generated questions for a run
- `GET /generate/runs/{run_id}/drift` — drift report for a run
- `GET /generate/templates` — available generation templates
- `PATCH /generate/questions/{question_id}/status` — approve/reject a generated question (triggers full approval flow)

---

## 13. Grammar Practice Endpoint

**File:** `app/routers/questions.py`  
**Triggered by:** frontend requesting interactive practice data for a specific question

### `GET /questions/{question_id}/practice`

Returns the full data shape needed to render `grammar-app.html`.

**Queries (single connection, sequential):**
1. `SELECT ... FROM public.questions WHERE id=$1` — core question fields including `tokenization_status`.
2. `SELECT ... FROM public.question_options WHERE question_id=$1 ORDER BY option_label` — 4 options.
3. `SELECT token_index, token_text, is_blank, grammar_tags FROM public.question_token_annotations WHERE question_id=$1 ORDER BY token_index` — word-level tokens.
4. `SELECT id, label, color, light_bg, mid_bg, description, sat_rule FROM public.grammar_keys ORDER BY id` — full grammar key registry.

**Response shape:**
```json
{
  "id": "uuid",
  "prompt_text": "...",
  "correct_option_label": "B",
  "tokenization_status": "ready | pending | failed",
  "options": [{"id": "A", "text": "...", "correct": false, "explanation": "..."}],
  "tokens": [{"token_index": 0, "text": "Although", "is_blank": false, "tags": ["subordinating_conj"]}],
  "grammar_keys": [{"id": "subordinating_conj", "label": "...", "color": "#...", "lightBg": "...", "midBg": "...", "description": "...", "rule": "..."}]
}
```

`tokenization_status` fallback: `q["tokenization_status"] or "pending"` — handles legacy rows with no column set.

---

## 14. Semantic Search

**File:** `app/routers/search.py`  
**Triggered by:** `POST /search`

### `search_questions(body, request)`

Accepts `SearchRequest`: `query` (text), `limit` (default 10), optional `embedding_type` (`passage_only` | `style_fingerprint` | `full_context`).

**Flow:**
1. Fetches embedding for `query` via `get_embedding(query)` (OpenAI call).
2. Queries `public.question_embeddings` using pgvector cosine distance operator `<=>`.
3. JOINs with `public.questions` to return question metadata alongside similarity score.

**Returns:** `list[SearchResult]` — question id, prompt_summary, exam_code, module_code, question_number, similarity score.

---

## 15. Ontology + Proposals

**Files:** `app/routers/ontology.py`, `app/pipeline/proposals.py`

### `GET /ontology`

Returns `app.state.ontology` dict (loaded at startup). Maps table name → list of valid keys for all 41 lookup tables. Used by frontend to populate dropdowns without a DB call.

### `POST /ontology/reload`

Re-runs `_load_ontology(conn)` and replaces `app.state.ontology`. Use after adding new lookup values via migration.

### Proposals system

During Pass 2 validation, `collect_ontology_proposals(extract, annotation, ontology)` compares LLM output against the known registry. Any unknown value that looks plausible (not empty, not a formatting artifact) is collected as a `OntologyProposal`.

`upsert_proposals(conn, proposals, job_id)` writes to `public.ontology_proposals`. Each proposal records: `field_name`, `proposed_value`, `source_job_id`, `status` (`pending`).

**Review endpoints:**
- `GET /ontology/proposals` — list proposals, filter by `status`
- `GET /ontology/proposals/{id}` — single proposal
- `PATCH /ontology/proposals/{id}/status` — accept (`accepted`) or reject (`rejected`)
- `GET /ontology/proposals/stats` — counts by status and field

Accepting a proposal does not auto-migrate — it signals to the operator that a new lookup value should be added via migration.

---

## 16. Questions Read API

**File:** `app/routers/questions.py`

### `GET /questions`

Lists questions with optional `exam_code`, `module_code` filters. Returns id, exam/module context, stem type, prompt summary, correct label, created timestamp.

### `GET /questions/{question_id}`

Full question detail: all content fields + classification + 4 options + reasoning + generation profile. Joins `exams`, `exam_sections`, `exam_modules`.

---

## 17. File Parsers

**Files:** `app/parsers/pdf_parser.py`, `app/parsers/image_parser.py`

### `parse_pdf(data: bytes) → str`

Uses `pdfplumber`. Opens PDF bytes, iterates pages, calls `page.extract_text()`. Prepends `[Page N]` headers. Returns all pages concatenated with double newlines. Works on text-layer PDFs (standard CB practice test PDFs). Does not OCR embedded images.

### `parse_image(data: bytes, use_ocr=True) → str`

Uses `Pillow` + `pytesseract` (Tesseract OCR). Opens image bytes as PIL Image, calls `pytesseract.image_to_string()`. Returns empty string if Tesseract not installed (caller detects and routes to vision LLM). Non-fatal.

### `image_to_base64(data: bytes) → str`

Converts image bytes to base64 string for vision-capable LLM APIs (not yet wired into main pipeline).

---

## 18. Data Models

**Files:** `app/models/`

| Model | File | Purpose |
|-------|------|---------|
| `Settings` | `config.py` | Pydantic-settings; reads `.env`; singleton via `get_settings()` |
| `QuestionExtract` | `models/extract.py` | Pass 1 output: stem, choices, source metadata, content_hash |
| `QuestionAnnotation` | `models/annotation.py` | Pass 2 output: classification, options, reasoning, generation profile |
| `QuestionClassification` | `models/annotation.py` | All ~55 taxonomy fields nested in QuestionAnnotation |
| `GenerationProfile` | `models/annotation.py` | All `target_*` fields for generation targeting |
| `ValidationError` | `models/payload.py` | `field`, `message`, `value` — returned in `validation_errors_json` |
| `IngestionJobRead` | `models/payload.py` | Full job row for API responses |
| `SearchRequest/Result` | `models/payload.py` | Semantic search I/O |
| `LOOKUP_TABLES` | `models/ontology.py` | Authoritative list of 41 lookup table names used by validator and ontology loader |

---

## Execution Flow Summary

```
User uploads PDF / text
        │
        ▼
POST /ingest → create_job() → BackgroundTask
        │
        ▼
process_job()
  ├── Pass 1: LLM extracts question JSON
  ├── Pass 2: LLM classifies ~55 taxonomy fields
  ├── validate_payload() → errors list
  ├── collect_ontology_proposals() → upsert_proposals()
  └── status: 'reviewed' (clean) | 'draft' (errors)
        │
        ▼ (human reviews in UI)
PATCH /jobs/{id}/status {"status":"approved"}
        │
        ├── upsert_question() ──► questions + 4 downstream tables
        ├── reset tokenization_status = 'pending'
        │
        └── BackgroundTasks (fire-and-forget):
              ├── _refresh_irt()         → fn_refresh_irt_b(NULL)
              ├── tokenize_question()    → question_token_annotations + status='ready'
              └── generate_coaching()   → question_coaching_annotations (generated only)
        │
        ▼
GET /questions/{id}/practice
  └── tokens + grammar_keys → grammar-app.html renders interactive UI
```
