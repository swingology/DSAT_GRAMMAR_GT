# DSAT Ingestion Backend

FastAPI service that ingests SAT Reading & Writing questions from multiple input formats via a two-pass LLM pipeline, stages results for human review, and upserts approved questions into the production Supabase schema.

---

## Quick Start

```bash
cd FULL_PLAN/backend
cp .env.example .env          # fill in SUPABASE_DB_URL and at least one LLM key
uv sync
uv run uvicorn app.main:app --reload
```

Interactive API docs: `http://127.0.0.1:8000/docs`

---

## Setup

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12+ | Managed via `.python-version` |
| [uv](https://docs.astral.sh/uv/) | latest | Package and venv manager |
| Supabase project | — | With migrations 001–014 applied |
| Tesseract | 4.x+ | Only needed for image ingestion — `brew install tesseract` |

At least one LLM API key is required to run ingestions. The DB connection works independently of LLM keys.

---

### 1. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### 2. Clone and enter the backend directory

```bash
cd FULL_PLAN/backend
```

---

### 3. Install dependencies

```bash
uv sync
```

This creates a `.venv` in the backend directory and installs all packages from `pyproject.toml`.

---

### 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

**Required:**
```bash
# Supabase session pooler DSN (port 5432)
SUPABASE_DB_URL=postgresql://postgres.YOURREF:PASSWORD@aws-0-us-west-2.pooler.supabase.com:5432/postgres
```

**At least one LLM key:**
```bash
ANTHROPIC_API_KEY=sk-ant-...     # default provider
OPENAI_API_KEY=sk-...            # if using OpenAI
OPENROUTER_API_KEY=sk-or-...     # if using OpenRouter
# Ollama needs no key — just OLLAMA_BASE_URL=http://localhost:11434
```

**Optional tunables** (defaults are fine to start):
```bash
LLM_PROVIDER=anthropic           # anthropic | openai | ollama | openrouter
LLM_MODEL=claude-sonnet-4-6
MAX_FILE_UPLOAD_MB=20
PASS1_MAX_TOKENS=2048
PASS2_MAX_TOKENS=4096
```

To get your Supabase DSN: go to your Supabase project → **Settings → Database → Connection string → Session mode** (port 5432).

---

### 5. Apply the staging table migration

If you haven't already applied migration 014:

```bash
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"   # macOS — add psql to PATH
PGPASSWORD=yourpassword psql \
  -h aws-0-us-west-2.pooler.supabase.com \
  -p 5432 \
  -U postgres.YOURREF \
  -d postgres \
  -f migrations/014_question_ingestion_jobs.sql
```

Or paste the contents of `migrations/014_question_ingestion_jobs.sql` directly into the Supabase SQL editor.

> Migrations 001–013 (the core schema) must already be applied before running 014. See `FULL_PLAN/dsat_migrations_section_1_001_to_006.sql` and `FULL_PLAN/dsat_migrations_section_2_007_to_013.sql`.

---

### 6. Start the server

**Development (with hot reload):**
```bash
uv run uvicorn app.main:app --reload
```

**Production:**
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server starts at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

---

### 7. Verify

```bash
curl http://127.0.0.1:8000/health
# → {"status":"ok","db":"ok"}

curl http://127.0.0.1:8000/ontology | python3 -m json.tool
# → All 12 lookup tables with their allowed keys
```

If `/health` returns `"db":"error:..."`, check your `SUPABASE_DB_URL` value and that the Supabase project is active.

---

### Tesseract (image ingestion only)

```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt-get install tesseract-ocr

# Verify
tesseract --version
```

Without tesseract, `POST /ingest/file` with an image will return HTTP 422. PDF, Markdown, JSON, and text ingestion work without it.

---

### Ollama (local LLM, no API key)

```bash
# Install Ollama
brew install ollama         # macOS
# or: curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Start Ollama (runs on port 11434 by default)
ollama serve
```

Then set in `.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
```

---

## Pipeline Overview

```
Input (PDF / Image / Markdown / JSON / Text)
    │
    ▼
[Parser]  →  raw_input_text
    │
    ▼
[LLM Pass 1: Extraction]  →  pass1_json (QuestionExtract)
    │
    ▼
[LLM Pass 2: Annotation]  →  pass2_json (QuestionAnnotation)
    │        (ontology injected into system prompt)
    ▼
[Validator]  →  validation_errors_json
    │
    ▼
[Staging table: question_ingestion_jobs]
    │         status: pending → extracting → annotating → draft | reviewed
    ▼
[Human review: PATCH /jobs/{id}/status]
    │         status: reviewed → approved | rejected
    ▼
[Upsert]  →  5 production tables
              questions
              question_classifications
              question_options
              question_reasoning
              question_generation_profiles
```

**Pass 1** extracts the raw question content — stem, passage, answer choices, correct answer, source metadata — without any taxonomy classification. This keeps extraction clean and separable from annotation.

**Pass 2** annotates the extracted question against the full DSAT taxonomy ontology. All allowed lookup key values are injected into the system prompt at startup, preventing hallucinated taxonomy values.

---

## Endpoints

### Ingest

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingest` | Submit raw text or pre-extracted JSON for a single question. Runs full two-pass pipeline synchronously. Returns job record. |
| `POST` | `/ingest/file` | Upload a file (PDF, PNG/JPG, Markdown, JSON). Parser selected by MIME type / file extension. |
| `POST` | `/ingest/batch` | Submit up to 50 raw text blocks. Each becomes its own job. Returns list of job records. |

**`POST /ingest` body:**
```json
{
  "raw_text": "The following text is adapted from...",
  "input_format": "text",
  "source_file": "PT4-M1.pdf",
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-6"
}
```
`llm_provider` and `llm_model` are optional — defaults come from `.env`.

**`POST /ingest/file`** accepts `multipart/form-data`:
- `file` — the uploaded file
- `llm_provider` — optional form field
- `llm_model` — optional form field

---

### Jobs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs` | List all staging jobs. Supports `?status=draft&limit=50&offset=0`. |
| `GET` | `/jobs/{id}` | Get full job record including `pass1_json`, `pass2_json`, and `validation_errors_json`. |
| `PATCH` | `/jobs/{id}/status` | Move job status. `approved` triggers production upsert. |
| `POST` | `/jobs/{id}/rerun` | Re-run both LLM passes on an existing job using its stored `raw_input_text`. |

**Job status flow:**
```
pending → extracting → annotating → draft (has validation errors)
                                  → reviewed (clean)
                                        ↓
                                   approved (upserted to production)
                                   rejected (human decision)
                                   failed   (unrecoverable LLM/parse error)
```

**`PATCH /jobs/{id}/status` body:**
```json
{
  "status": "approved",
  "review_notes": "Looks good, approved for production."
}
```
Valid values: `reviewed`, `approved`, `rejected`.

---

### Ontology

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ontology` | Returns all 12 lookup table key sets loaded from the database at startup. |

Response shape:
```json
{
  "lookup_question_family": ["words_in_context", "main_idea", ...],
  "lookup_stimulus_mode": ["sentence_only", "prose_single", ...],
  ...
}
```

---

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check. Pings DB and returns `{"status":"ok","db":"ok"}`. |

---

## Code Structure

```
app/
├── main.py              App factory, lifespan, router registration
├── config.py            Settings (pydantic-settings, reads .env)
├── database.py          asyncpg connection pool
│
├── models/              Pydantic data models
│   ├── extract.py       QuestionExtract — Pass 1 output shape
│   ├── annotation.py    QuestionAnnotation — Pass 2 output (4 sub-models)
│   ├── payload.py       IngestionPayload, IngestionJobRead, JobStatusUpdate, IngestRequest
│   └── ontology.py      Lookup table names, FIELD_TO_TABLE map, is_valid_key() helper
│
├── llm/                 LLM provider abstraction
│   ├── base.py          LLMProvider ABC + ProviderResponse dataclass
│   ├── anthropic_provider.py   claude-sonnet-4-6 via anthropic SDK
│   ├── openai_provider.py      gpt-4o via openai SDK
│   ├── ollama_provider.py      local models via httpx REST (no key needed)
│   ├── openrouter_provider.py  any model via OpenRouter (openai-compatible)
│   └── factory.py       get_provider(settings, override?) → LLMProvider
│
├── prompts/             LLM prompt templates
│   ├── pass1_extraction.py    System prompt + user template for extraction
│   ├── pass2_annotation.py    Annotation prompt with ontology injection
│   └── ontology_ref.py        render_ontology_reference() — builds compact key list
│
├── parsers/             Input format handlers
│   ├── pdf_parser.py    parse_pdf(bytes) → str via pdfplumber
│   ├── image_parser.py  parse_image(bytes) → str via pytesseract OCR
│   ├── markdown_parser.py  parse_markdown(bytes) → str (passthrough)
│   └── json_parser.py   parse_json(bytes) → dict with basic shape validation
│
├── pipeline/            Core processing logic
│   ├── ingest.py        run_ingestion() — full orchestrator from raw text to staged job
│   ├── validator.py     validate_payload() — field checks, lookup key validation, option constraints
│   └── upsert.py        upsert_question() — 5-table idempotent upsert on approval
│
└── routers/             FastAPI route handlers
    ├── ingest.py        POST /ingest, /ingest/file, /ingest/batch
    ├── jobs.py          GET/PATCH /jobs, GET /jobs/{id}, POST /jobs/{id}/rerun
    └── ontology.py      GET /ontology
```

---

## Models

### `QuestionExtract` (`models/extract.py`)
Pass 1 output. Represents the raw question content before any taxonomy annotation.

| Field | Type | Description |
|-------|------|-------------|
| `stem` | `str` | Question prompt text |
| `passage` | `str \| None` | Accompanying passage |
| `paired_passage` | `str \| None` | Second passage for paired-text questions |
| `notes_bullets` | `list[str] \| None` | Bullet notes for notes-mode questions |
| `choices` | `dict[str, str]` | Exactly `{"A": ..., "B": ..., "C": ..., "D": ...}` |
| `correct_option_label` | `A\|B\|C\|D` | Correct answer |
| `explanation_short` | `str` | One-sentence rationale |
| `explanation_full` | `str` | 2–4 sentence detailed reasoning |
| `evidence_span_text` | `str \| None` | Key supporting span from passage |
| `source_exam_code` | `str \| None` | e.g. `PT4` |
| `source_module_code` | `str \| None` | e.g. `M1` or `M2` |
| `source_question_number` | `int \| None` | Question number within module |
| `stimulus_mode_key` | `str` | Validated against `lookup_stimulus_mode` |
| `stem_type_key` | `str` | Validated against `lookup_stem_type` |

### `QuestionAnnotation` (`models/annotation.py`)
Pass 2 output. Composed of four sub-models:

- **`ClassificationAnnotation`** — domain, skill_family, subskill, all taxonomy lookup keys (question family, evidence scope/location, answer mechanism, solver pattern, difficulty, distractor strength)
- **`OptionAnnotation`** × 4 — per-option analysis: role, distractor type, semantic relation, plausibility source, why plausible/wrong
- **`ReasoningAnnotation`** — solver steps, coaching tip, hidden clue type, clue distribution
- **`GenerationProfileAnnotation`** — generation pattern family, target constraints, reuse flag

### `IngestionJobRead` (`models/payload.py`)
The shape returned by all job endpoints. Includes the full `pass1_json`, `pass2_json`, and `validation_errors_json` columns from the staging table.

---

## LLM Providers

All providers implement the same interface:

```python
class LLMProvider(ABC):
    async def complete(
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,   # always 0 for determinism
        max_tokens: int = 4096,
    ) -> ProviderResponse
```

| Provider | Class | Notes |
|----------|-------|-------|
| Anthropic | `AnthropicProvider` | Default. Uses `anthropic.AsyncAnthropic`. |
| OpenAI | `OpenAIProvider` | Uses `openai.AsyncOpenAI`. |
| Ollama | `OllamaProvider` | Local REST call to `/api/chat`. No API key needed. |
| OpenRouter | `OpenRouterProvider` | OpenAI-compatible client with `base_url` override. |

Provider is selected at request time via `get_provider(settings, override_provider, override_model)`. Each `POST /ingest` call can specify a different provider/model, defaulting to the values in `.env`.

---

## Validation

`pipeline/validator.py` runs deterministic checks after both LLM passes:

- `stem` is non-empty
- `choices` has exactly keys A, B, C, D
- `correct_option_label` exists in `choices`
- `stimulus_mode_key` and `stem_type_key` are valid lookup values
- `question_family_key`, `evidence_scope_key`, `evidence_location_key`, `answer_mechanism_key`, `solver_pattern_key` are valid lookup values
- Exactly 4 options, covering A, B, C, D
- Exactly 1 correct option
- Correct option label matches `extract.correct_option_label`
- Per-option lookup keys (`distractor_type_key`, `semantic_relation_key`, `plausibility_source_key`) are valid
- `clue_distribution_key` and `generation_pattern_family_key` are valid

Errors are written to `validation_errors_json` as `[{"field": "...", "message": "...", "value": ...}]`.

A job with any validation errors is set to `draft` (needs human review before approval). A clean job is set to `reviewed` (can be approved directly).

---

## Production Upsert

`pipeline/upsert.py::upsert_question()` fires when a job is approved. It:

1. Resolves `exam_id`, `section_id`, `module_id` from the source metadata in `pass1_json`
2. Upserts `questions` on `(module_id, source_question_number)`
3. Upserts `question_classifications` on `(question_id)`
4. Deletes and re-inserts `question_options` (4 rows per question)
5. Upserts `question_reasoning` on `(question_id)`
6. Upserts `question_generation_profiles` on `(question_id)`

All upserts are idempotent — re-approving a job updates existing rows rather than creating duplicates.

**Requirement:** `source_exam_code`, `source_module_code`, and `source_question_number` must be present in `pass1_json` for the upsert to resolve the correct module. If they are missing the upsert raises a `ValueError` and the job status is not changed.

---

## Configuration (`.env`)

```bash
# Required
SUPABASE_DB_URL=postgresql://postgres.PROJECTREF:PASSWORD@pooler.supabase.com:5432/postgres

# LLM provider (default)
LLM_PROVIDER=anthropic          # anthropic | openai | ollama | openrouter
LLM_MODEL=claude-sonnet-4-6

# API keys — only the active provider's key is required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...

# Ollama (local, no key needed)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Tunables
MAX_FILE_UPLOAD_MB=20
PASS1_MAX_TOKENS=2048
PASS2_MAX_TOKENS=4096
```

---

## Database

### Staging table (`question_ingestion_jobs`)
Created by `migrations/014_question_ingestion_jobs.sql`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `uuid` | Primary key |
| `source_file` | `text` | Original filename, if uploaded |
| `input_format` | `text` | `pdf \| markdown \| image \| json \| text` |
| `raw_input_text` | `text` | Parser output — stored for reruns |
| `pass1_json` | `jsonb` | `QuestionExtract` from LLM Pass 1 |
| `pass2_json` | `jsonb` | `QuestionAnnotation` from LLM Pass 2 |
| `validation_errors_json` | `jsonb` | Array of error objects |
| `status` | `text` | See status flow above |
| `review_notes` | `text` | Human reviewer notes |
| `llm_provider` | `text` | Provider used |
| `llm_model` | `text` | Model used |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | Auto-updated via trigger |

### Production tables (pre-existing, migrations 001–013)
- `questions` — core question record
- `question_classifications` — taxonomy annotation
- `question_options` — 4 answer choices with distractor analysis
- `question_reasoning` — solver steps and coaching notes
- `question_generation_profiles` — constraints for future question generation

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | Web framework |
| `pydantic-settings` | Settings from `.env` |
| `asyncpg` | Async PostgreSQL driver |
| `anthropic` | Anthropic Claude SDK |
| `openai` | OpenAI + OpenRouter SDK |
| `httpx` | Ollama REST calls |
| `pdfplumber` | PDF text extraction |
| `pillow` + `pytesseract` | Image OCR (requires `tesseract` binary) |
| `python-multipart` | File upload support |

Install all: `uv sync`

> **Tesseract note:** `pytesseract` requires the `tesseract` binary. Install via `brew install tesseract` on macOS. If tesseract is absent, `parse_image()` returns an empty string and the `/ingest/file` endpoint will return a 422 with a message to use a clearer image or install tesseract.
