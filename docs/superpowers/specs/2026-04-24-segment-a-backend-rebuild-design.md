# Segment A Backend Rebuild Design

**Date:** 2026-04-24
**Scope:** Full rebuild of the DSAT backend as a single FastAPI service covering corpus ingestion, question generation, practice recall, and student-facing endpoints.
**Replaces:** Existing 4-file backend (`backend/main.py`, `models.py`, `schemas.py`, `database.py`)
**Architecture:** Flat Service — one FastAPI app, flat router structure, shared Postgres database

---

## 1. Architecture Overview

Single FastAPI application with two logical segments sharing one Postgres database:

- **Segment A (corpus):** ingestion, annotation, generation, overlap detection, admin review
- **Segment B (student):** practice recall, answer submission, accuracy stats

Both segments operate on the same `public` schema. Segment A writes to corpus tables; Segment B reads from them. The shared interface is `question_id` (UUID).

### Segment Interface Contract

**Segment B may read (never write):**
- `questions` — question identity, current content, practice status
- `question_annotations` — taxonomy metadata, explanations (via `latest_annotation_id`)
- `question_versions` — edit history (read-only for display)
- `question_options` — per-option analysis fields

**Segment B owns (writes):**
- `users` — student accounts
- `user_progress` — answer attempts, accuracy tracking

**Shared key:** `question_id` (UUID). Every question gets a UUID when it enters the `questions` table. Segment B's `user_progress.question_id` is a FK to `questions.id`.

---

## 2. Data Model — 10 Tables

### 2.1 `question_jobs`

Staging and orchestration for ingestion and generation.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `job_type` | ENUM | `ingest`, `generate`, `reannotate`, `overlap_check` |
| `content_origin` | ENUM | `official`, `unofficial`, `generated` |
| `input_format` | VARCHAR | `pdf`, `image`, `screenshot`, `markdown`, `json`, `text` |
| `status` | ENUM | See job state machine (§5) |
| `provider_name` | VARCHAR | `anthropic`, `openai`, `ollama` |
| `model_name` | VARCHAR | e.g., `claude-sonnet-4-6` |
| `prompt_version` | VARCHAR | e.g., `v3.0` |
| `rules_version` | VARCHAR | e.g., `rules_agent_dsat_grammar_ingestion_generation_v3` |
| `raw_asset_id` | UUID (FK → question_assets) | nullable |
| `pass1_json` | JSONB | Pass 1 extraction output |
| `pass2_json` | JSONB | Pass 2 annotation output |
| `validation_errors_jsonb` | JSONB | Structured error details on failure |
| `comparison_group_id` | UUID | Groups jobs for multi-model comparison |
| `question_id` | UUID (FK → questions) | nullable until job produces a question |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### 2.2 `questions`

Canonical question identity and current user-facing content.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `content_origin` | ENUM | `official`, `unofficial`, `generated` |
| `source_exam_code` | VARCHAR | e.g., `PT4` (required for official) |
| `source_module_code` | VARCHAR | e.g., `M1` (required for official) |
| `source_question_number` | INTEGER | (required for official) |
| `stimulus_mode_key` | VARCHAR | V3 §3.1 controlled values |
| `stem_type_key` | VARCHAR | V3 §3.2 controlled values |
| `current_question_text` | TEXT | Prompt/stem text |
| `current_passage_text` | TEXT | nullable |
| `current_correct_option_label` | VARCHAR(1) | `A`, `B`, `C`, or `D` |
| `current_explanation_text` | TEXT | Composed from annotation |
| `practice_status` | ENUM | `draft`, `active`, `retired` |
| `official_overlap_status` | ENUM | `none`, `possible`, `confirmed` |
| `canonical_official_question_id` | UUID (FK → questions) | nullable |
| `derived_from_question_id` | UUID (FK → questions) | nullable |
| `generation_source_set` | JSONB | Array of `{question_id, focus_key, role}` objects |
| `is_admin_edited` | BOOLEAN | default `false` |
| `metadata_managed_by_llm` | BOOLEAN | default `true` |
| `latest_annotation_id` | UUID (FK → question_annotations) | nullable |
| `latest_version_id` | UUID (FK → question_versions) | nullable |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### 2.3 `question_versions`

Immutable snapshots of question content after ingest, generation, or admin edit.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `question_id` | UUID (FK → questions) | |
| `version_number` | INTEGER | Auto-incremented per question |
| `change_source` | ENUM | `ingest`, `generate`, `admin_edit`, `reprocess` |
| `question_text` | TEXT | |
| `passage_text` | TEXT | nullable |
| `choices_jsonb` | JSONB | `[{label, text}]` |
| `correct_option_label` | VARCHAR(1) | |
| `explanation_text` | TEXT | |
| `editor_user_id` | VARCHAR | nullable |
| `change_notes` | TEXT | nullable |
| `created_at` | TIMESTAMPTZ | |

### 2.4 `question_annotations`

LLM-managed metadata and explanation artifacts tied to a specific question version.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `question_id` | UUID (FK → questions) | |
| `question_version_id` | UUID (FK → question_versions) | |
| `provider_name` | VARCHAR | |
| `model_name` | VARCHAR | |
| `prompt_version` | VARCHAR | |
| `rules_version` | VARCHAR | |
| `annotation_jsonb` | JSONB | classification, reasoning, v3 extensions (§21-29) |
| `explanation_jsonb` | JSONB | explanation_short, explanation_full, evidence_span_text |
| `generation_profile_jsonb` | JSONB | V3 generation_profile block |
| `confidence_jsonb` | JSONB | annotation_confidence, needs_human_review, review_notes |
| `created_at` | TIMESTAMPTZ | |

### 2.5 `question_options`

Per-option analysis fields from V3 rules. One row per option (4 rows per question).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `question_id` | UUID (FK → questions) | |
| `question_version_id` | UUID (FK → question_versions) | |
| `option_label` | VARCHAR(1) | `A`, `B`, `C`, `D` |
| `option_text` | TEXT | |
| `is_correct` | BOOLEAN | |
| `option_role` | VARCHAR | `correct` or `distractor` |
| `distractor_type_key` | VARCHAR | V3 §10.2 controlled values |
| `semantic_relation_key` | VARCHAR | V3 §3.3 controlled values |
| `plausibility_source_key` | VARCHAR | V3 §10.3 controlled values |
| `option_error_focus_key` | VARCHAR | nullable, V3 grammar_focus_key |
| `why_plausible` | TEXT | |
| `why_wrong` | TEXT | nullable for correct option |
| `grammar_fit` | VARCHAR | `yes` or `no` |
| `tone_match` | VARCHAR | `yes` or `no` |
| `precision_score` | SMALLINT | 1, 2, or 3 (V3 §10.4) |
| `student_failure_mode_key` | VARCHAR | V3 §21.3 (nullable for correct) |
| `distractor_distance` | VARCHAR | `wide`, `moderate`, `tight` (V3 §21.2) |
| `distractor_competition_score` | FLOAT | V3 §21.4 (nullable for correct) |
| `created_at` | TIMESTAMPTZ | |

### 2.6 `question_assets`

Raw source files and extracted artifacts.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `question_id` | UUID (FK → questions) | nullable until linked |
| `content_origin` | ENUM | `official`, `unofficial` |
| `asset_type` | ENUM | `pdf`, `image`, `screenshot`, `markdown`, `json`, `text` |
| `storage_path` | TEXT | Local path or bucket URL |
| `mime_type` | VARCHAR | |
| `page_start` | INTEGER | nullable |
| `page_end` | INTEGER | nullable |
| `source_url` | TEXT | nullable |
| `source_name` | VARCHAR | nullable |
| `source_exam_code` | VARCHAR | nullable |
| `source_module_code` | VARCHAR | nullable |
| `source_question_number` | INTEGER | nullable |
| `checksum` | VARCHAR | SHA-256 |
| `created_at` | TIMESTAMPTZ | |

### 2.7 `question_relations`

Cross-question linking (overlap, lineage, derived-from).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `from_question_id` | UUID (FK → questions) | |
| `to_question_id` | UUID (FK → questions) | |
| `relation_type` | ENUM | `overlaps_official`, `derived_from`, `near_duplicate`, `generated_from`, `adapted_from` |
| `relation_strength` | FLOAT | Similarity score |
| `detection_method` | VARCHAR | `lexical`, `structural`, `embedding` |
| `is_human_confirmed` | BOOLEAN | default `false` |
| `notes` | TEXT | nullable |
| `created_at` | TIMESTAMPTZ | |

### 2.8 `llm_evaluations`

Beta model comparison scores.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `job_id` | UUID (FK → question_jobs) | |
| `question_id` | UUID (FK → questions) | nullable |
| `provider_name` | VARCHAR | |
| `model_name` | VARCHAR | |
| `task_type` | VARCHAR | `extraction`, `annotation`, `generation` |
| `score_overall` | FLOAT | nullable |
| `score_metadata` | FLOAT | nullable |
| `score_explanation` | FLOAT | nullable |
| `score_generation` | FLOAT | nullable |
| `review_notes` | TEXT | nullable |
| `recommended_for_default` | BOOLEAN | nullable |
| `created_at` | TIMESTAMPTZ | |

### 2.9 `users` (Segment B)

Student accounts.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER (PK) | |
| `username` | VARCHAR | unique |
| `created_at` | TIMESTAMPTZ | |

### 2.10 `user_progress` (Segment B)

Answer attempts and accuracy tracking.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER (PK) | |
| `user_id` | INTEGER (FK → users) | |
| `question_id` | UUID (FK → questions) | |
| `is_correct` | BOOLEAN | |
| `selected_option_label` | VARCHAR(1) | |
| `missed_grammar_focus_key` | VARCHAR | nullable |
| `missed_syntactic_trap_key` | VARCHAR | nullable |
| `timestamp` | TIMESTAMPTZ | |

---

## 3. V3 Rules Output → Database Mapping

The V3 rules produce a JSON with 6 top-level keys. Here's where each field lands:

| V3 Section | V3 Key | Database Destination |
|---|---|---|
| §3 Question | `source_exam`, `source_section`, `source_module`, `source_question_number` | `questions` columns |
| §3 Question | `stimulus_mode_key`, `stem_type_key` | `questions` columns |
| §3 Question | `prompt_text` | `questions.current_question_text` |
| §3 Question | `passage_text`, `paired_passage_text` | `questions.current_passage_text` |
| §3 Question | `correct_option_label` | `questions.current_correct_option_label` |
| §3 Question | `explanation_short`, `explanation_full`, `evidence_span_text` | `question_annotations.explanation_jsonb` |
| §3 Question | `table_data`, `graph_data` | `question_annotations.annotation_jsonb` (nested) |
| §4 Classification | All classification fields | `question_annotations.annotation_jsonb` (nested under `classification`) |
| §10 Options | Per-option analysis (13 fields) | `question_options` table (one row per option) |
| §2.1 Reasoning | All reasoning fields | `question_annotations.annotation_jsonb` (nested under `reasoning`) |
| §2.1 Generation Profile | All generation_profile fields | `question_annotations.generation_profile_jsonb` |
| §2.1 Review | `annotation_confidence`, `needs_human_review`, `review_notes` | `question_annotations.confidence_jsonb` |
| §21 Distractor Competition | `distractor_distance`, `student_failure_mode_key`, `distractor_competition_score`, `answer_separation_strength`, `plausible_wrong_count` | `question_annotations.annotation_jsonb` (nested under `v3_extensions`) |
| §22 Passage Architecture | `passage_architecture_key` | `question_annotations.annotation_jsonb` (nested under `v3_extensions`) |
| §23 Ground Truth | `official_similarity_score` | `question_annotations.annotation_jsonb` (nested under `v3_extensions`) |
| §24 Anti-Clone | `structural_similarity_score`, `rewrite_required` | `question_annotations.annotation_jsonb` (nested under `v3_extensions`) |
| §25 Empirical Difficulty | `empirical_difficulty_estimate` | `question_annotations.annotation_jsonb` (nested under `v3_extensions`) |
| §26 Human Override | `human_override_log` | `question_annotations.annotation_jsonb` (nested under `v3_extensions`) |
| §27 Provenance | `generation_provenance` | `question_annotations.annotation_jsonb` (nested under `v3_extensions`) |

---

## 4. API Endpoints

### Ingestion (`/ingest/*`)

| Method | Path | Description |
|---|---|---|
| POST | `/ingest/official/pdf` | Upload official PDF, create per-question jobs |
| POST | `/ingest/unofficial/file` | Upload single unofficial asset (PDF, image, MD, JSON, text) |
| POST | `/ingest/unofficial/batch` | Batch upload mixed unofficial assets |
| POST | `/ingest/reannotate/{question_id}` | Re-run Pass 2 with same or different provider |

### Generation (`/generate/*`)

| Method | Path | Description |
|---|---|---|
| POST | `/generate/questions` | Generate questions from source examples |
| POST | `/generate/questions/compare` | Generate with multiple LLMs for side-by-side comparison |
| GET | `/generate/runs/{run_id}` | Inspect generation lineage + review state |

### Questions (`/questions/*`)

| Method | Path | Description |
|---|---|---|
| GET | `/questions/recall` | Filter + paginate practice questions (supports all PRD §12 filters) |
| GET | `/questions/{question_id}` | Full detail: content, annotation, options, lineage, overlap state |
| GET | `/questions/{question_id}/versions` | Edit history |

### Admin (`/admin/*`)

| Method | Path | Description |
|---|---|---|
| PATCH | `/admin/questions/{question_id}` | Edit question content, answers, or explanation |
| POST | `/admin/questions/{question_id}/approve` | Approve for practice recall (sets `practice_status = active`) |
| POST | `/admin/questions/{question_id}/reject` | Reject or retire (sets `practice_status = retired`) |
| POST | `/admin/questions/{question_id}/confirm-overlap` | Confirm overlap with official corpus |
| POST | `/admin/questions/{question_id}/clear-overlap` | Reject a false positive overlap |
| POST | `/admin/evaluations/{evaluation_id}/score` | Store human evaluation scores for beta model comparison |

### Student (`/api/*`) — Segment B

| Method | Path | Description |
|---|---|---|
| GET | `/api/questions` | Practice recall (filters: grammar_focus, difficulty, origin, limit, offset) |
| POST | `/api/submit` | Record answer attempt |
| GET | `/api/stats/{user_id}` | User accuracy stats (top missed focus keys, trap keys) |

---

## 5. Job State Machine

### Official Ingest

```
pending → parsing → extracting → annotating → validating →
  ├→ approved (questions.practice_status = 'draft' → 'active')
  ├→ needs_review (questions.practice_status = 'draft')
  └→ failed (terminal, validation_errors_jsonb populated)
```

### Unofficial Ingest

```
pending → parsing → extracting → annotating → overlap_checking → validating →
  ├→ approved (practice_status = 'active')
  ├→ needs_review (practice_status = 'draft')
  └→ failed
```

### Generated Question

```
pending → extracting → generating → annotating → overlap_checking → validating →
  ├→ approved (practice_status = 'active')
  ├→ needs_review (practice_status = 'draft')
  └→ failed
```

### Failure Handling

Jobs that fail get `status = 'failed'` with structured error info in `validation_errors_jsonb`:

```json
{
  "step": "extract",
  "error_code": "PDF_PARSE_FAILED",
  "message": "No extractable text in pages 3-5",
  "retries": 1,
  "max_retries": 3
}
```

Retries via `POST /ingest/reannotate/{question_id}` or by re-submitting the original upload.

### practice_status Mapping

| Lifecycle State | `practice_status` | Meaning |
|---|---|---|
| Just ingested/generated | `draft` | Not yet approved for practice |
| Admin approved | `active` | Available for practice recall |
| Admin rejected or retired | `retired` | Excluded from practice recall |

---

## 6. LLM Pipeline

### Pass 1 — Extract

- **Input:** raw text from PDF/image/MD/JSON
- **Output:** `QuestionExtract` Pydantic model — question text, passage, options, correct answer, source metadata, table_data, graph_data
- **Storage:** `question_jobs.pass1_json`
- **Provider:** any of the 3 configured LLMs (default from config)

### Pass 2 — Annotate

- **Input:** Pass 1 output
- **Output:** `QuestionAnnotation` Pydantic model — full V3 taxonomy, distractor analysis, reasoning, generation profile, confidence, review flags, V3 §21-29 extensions
- **Storage:** `question_jobs.pass2_json` + rows in `question_annotations`, `question_options`
- **System prompt:** loads `rules_agent_dsat_grammar_ingestion_generation_v3.md`

### Pass 3 — Compare (optional, for beta)

- **Input:** same Pass 1 output
- **Output:** competing annotation from a different provider
- **Storage:** separate `question_annotations` row with different `provider_name`/`model_name`
- **Linking:** grouped by `comparison_group_id` on `question_jobs`

### LLM Providers

All three providers implement the same `LLMProvider` protocol:

```python
class LLMProvider(Protocol):
    async def complete(self, system: str, user: str, ...) -> LLMResponse: ...
```

- `anthropic_provider.py` — Anthropic Claude Sonnet 4.6
- `openai_provider.py` — OpenAI ChatGPT 5.4
- `ollama_provider.py` — Ollama kimi-k2.6

Provider selection via `llm/factory.py: get_provider(settings, provider_name)`.

---

## 7. Authentication

**MVP: API key auth.**

- Admin endpoints: `X-API-Key` header validated against `ADMIN_API_KEYS` env var
- Student endpoints: `X-API-Key` header validated against `STUDENT_API_KEYS` env var
- For beta, admin and student keys may share the same pool
- No user accounts or JWT — API keys are sufficient for a single-admin beta

---

## 8. Storage

**MVP: Local filesystem.**

- Raw assets (PDFs, images, markdown files) stored as files on disk
- `question_assets.storage_path` holds file paths (e.g., `./archive/PT4/sec01_mod01.pdf`)
- Swap to object storage later by changing `storage/local_store.py` to use Supabase Storage REST API
- `storage_path` field supports both local paths and bucket URLs

---

## 9. Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| DB driver | asyncpg (async Postgres) |
| ORM | SQLAlchemy 2.0 (async mode) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Settings | pydantic-settings (`.env` file) |
| LLM SDKs | `anthropic`, `openai`, `httpx` (for Ollama) |
| PDF parsing | pymupdf (`fitz`) |
| Image handling | Pillow |
| Testing | pytest + pytest-asyncio |
| Package mgmt | uv |

---

## 10. Project Structure

```
backend/
├── pyproject.toml
├── .python-version              # 3.12
├── .env.example
├── alembic.ini
├── migrations/                  # Alembic (fresh, starting from 001)
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, lifespan, router registration
│   ├── config.py                # Settings via pydantic-settings
│   ├── database.py              # asyncpg pool + SQLAlchemy async engine
│   ├── auth.py                  # API key validation dependencies
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py              # LLMProvider Protocol + LLMResponse dataclass
│   │   ├── factory.py           # get_provider() → Anthropic/OpenAI/Ollama
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── ollama_provider.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py                # SQLAlchemy ORM models (10 tables)
│   │   ├── ontology.py          # V3 allowed keys, enums, constants
│   │   ├── extract.py           # Pass 1 Pydantic schema (QuestionExtract)
│   │   ├── annotation.py        # Pass 2 Pydantic schema (QuestionAnnotation)
│   │   ├── payload.py           # HTTP request/response models
│   │   └── options.py           # Per-option Pydantic schema
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py        # pymupdf text + image extraction
│   │   ├── image_parser.py      # Image → base64 for multimodal LLM
│   │   ├── markdown_parser.py   # MD text + front matter
│   │   └── json_parser.py      # Robust JSON extraction from LLM output
│   ├── prompts/
│   │   ├── extract_prompt.py    # Pass 1 system prompt
│   │   ├── annotate_prompt.py  # Pass 2 system prompt (loads V3 rules)
│   │   └── generate_prompt.py  # Generation system prompt
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # Job state machine + step routing
│   │   ├── overlap.py           # Overlap detection logic
│   │   └── validator.py        # Validation rules (PRD §15)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── generate.py
│   │   ├── questions.py
│   │   ├── admin.py
│   │   └── student.py
│   └── storage/
│       ├── __init__.py
│       └── local_store.py       # Local filesystem asset storage
└── tests/
    ├── conftest.py
    ├── test_ingest.py
    ├── test_generate.py
    ├── test_recall.py
    ├── test_admin.py
    ├── test_student.py
    └── test_pipeline.py
```

---

## 11. PRD Gaps Resolved by This Design

| Gap | Resolution |
|---|---|
| Backend implements wrong data model | Full rebuild with 10-table schema matching PRD |
| SQLite vs Postgres | Postgres with asyncpg + Alembic |
| Zero API alignment | 19 endpoints across 5 routers matching PRD §17 |
| `generation_source_set` has no schema | Defined as JSONB array of `{question_id, focus_key, role}` |
| `pass1_json` / `pass2_json` undefined | Defined by Pydantic schemas `QuestionExtract` and `QuestionAnnotation` |
| `comparison_group_id` is dangling | Groups jobs for multi-model comparison; no separate table needed |
| No job state machine | §5 defines full state machine with failure handling |
| Overlap detection unimplementable | Deferred: `overlap.py` module, config thresholds, algorithm TBD during implementation |
| `rules_version` has no versioning scheme | String-based for MVP; migration path when V3.1 ships is re-run affected annotations |
| No admin auth model | §7: API key auth for MVP |
| V3 option analysis has no table home | `question_options` table (§2.5) |
| `practice_status` mapping unclear | §5: `draft` → `active` → `retired` |
| No pagination for recall | `GET /questions/recall` supports `limit`/`offset` |
| No file upload spec | Multipart form upload, 50MB max size, MIME validation |
| No concurrency model | Jobs are idempotent by `question_assets.checksum` dedup |
| No error taxonomy | `validation_errors_jsonb` with structured `step`, `error_code`, `message` |
| `recommended_for_default` is a single boolean | Kept as boolean for beta; multi-model ranking deferred to post-beta |

---

## 12. Open Items for Implementation

1. **Overlap detection algorithm** — Need to choose similarity measure (cosine on embeddings, Jaccard on n-grams, or hybrid) and calibrate thresholds
2. **PDF question splitting** — How to detect question boundaries within a multi-question PDF (page breaks, numbered headers, blank lines)
3. **Pass 1/Pass 2 Pydantic schema detail** — Need to enumerate all required/optional fields and validators matching V3 rules
4. **Admin edit → auto-reannotation flow** — When admin edits question content, how quickly does reannotation run? Synchronous or async?
5. **Object storage integration** — Swap `local_store.py` for Supabase Storage when deploying