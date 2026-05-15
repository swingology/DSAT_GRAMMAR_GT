# DSAT Backend — Ingestion Pipeline

This document explains how questions enter the system — from raw file upload through OCR, LLM extraction, annotation, validation, and final persistence in the database.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Ingestion Entry Points](#2-ingestion-entry-points)
3. [Step-by-Step Pipeline](#3-step-by-step-pipeline)
   - [Step 0 — Upload & Asset Storage](#step-0--upload--asset-storage)
   - [Step 1 — PDF Parsing](#step-1--pdf-parsing)
   - [Step 2 — OCR Strategy Selection](#step-2--ocr-strategy-selection)
   - [Step 3 — OCR / Text Extraction](#step-3--ocr--text-extraction)
   - [Step 4 — Pass 1: LLM Extraction](#step-4--pass-1-llm-extraction)
   - [Step 5 — Question Normalization & Deduplication](#step-5--question-normalization--deduplication)
   - [Step 6 — Question Number Validation](#step-6--question-number-validation)
   - [Step 7 — Pass 2: LLM Annotation](#step-7--pass-2-llm-annotation)
   - [Step 8 — Overlap Detection](#step-8--overlap-detection)
   - [Step 9 — Structural Validation](#step-9--structural-validation)
   - [Step 10 — Persistence](#step-10--persistence)
   - [Step 11 — YAML Export](#step-11--yaml-export)
4. [OCR Strategies In Detail](#4-ocr-strategies-in-detail)
5. [Job Status Lifecycle](#5-job-status-lifecycle)
6. [Database Schema](#6-database-schema)
7. [Key Files Reference](#7-key-files-reference)
8. [OCR Benchmark Endpoint](#8-ocr-benchmark-endpoint)
9. [Configuration](#9-configuration)
10. [Error Handling & Retry](#10-error-handling--retry)

---

## 1. Overview

The ingestion pipeline converts a raw source file (scanned PDF, image, plain text, or JSON) into fully structured, annotated DSAT questions stored in PostgreSQL. Every question goes through a two-pass LLM process:

- **Pass 1 (Extract):** Pull raw question data out of the source text or image.
- **Pass 2 (Annotate):** Classify and tag the question according to the DSAT rules specification.

Both passes run asynchronously in a background task — the HTTP endpoint returns immediately with a job ID, and the caller polls for completion.

```mermaid
flowchart TD
    A[HTTP Upload] --> B[Save Asset to disk]
    B --> C[Create QuestionJob record]
    C --> D[Return job_id immediately]
    D -.background task.-> E[_run_pipeline]
    E --> F{Has raw text?}
    F -- No: scanned PDF/image --> G[OCR Gate]
    F -- Yes: text/markdown/JSON --> H[Pass 1: LLM Extraction]
    G --> H
    H --> I[Normalize & Deduplicate]
    I --> J[Question Number Validation]
    J --> K[Pass 2: LLM Annotation per question]
    K --> L{unofficial / generated?}
    L -- Yes --> M[Overlap Detection]
    L -- No --> N[Structural Validation]
    M --> N
    N --> O{Blocking errors?}
    O -- No --> P[Persist to DB]
    O -- Yes --> Q[Skip question, log error]
    P --> R[YAML Export]
    P --> S[Final job status: approved / needs_review / failed]
```

---

## 2. Ingestion Entry Points

There are four HTTP endpoints in `backend/app/routers/ingest.py`, all under the `/ingest` prefix and requiring an admin API key.

| Endpoint | Method | Purpose |
|---|---|---|
| `/ingest/official/pdf` | POST | Official College Board practice test PDFs |
| `/ingest/unofficial/file` | POST | Third-party PDFs, images, markdown, text, JSON |
| `/ingest/text` | POST | Raw text pasted directly (no file upload) |
| `/ingest/unofficial/batch` | POST | Multiple unofficial files in one request |

### Official vs Unofficial distinction

**Official** questions require four metadata fields on upload — `source_exam_code`, `source_subject_code`, `source_section_code`, `source_module_code`. These fields are used to generate a **deterministic UUID5** for each question, making re-ingestion idempotent. The same PT1/verbal/section-01/module-01/question-3 will always produce the same question ID.

**Unofficial** questions receive a random UUID4 and skip the deterministic ID logic.

---

## 3. Step-by-Step Pipeline

### Step 0 — Upload & Asset Storage

**File:** `backend/app/routers/ingest.py` — endpoint handler functions

1. File size is checked against the 50 MB limit.
2. MIME type is validated against the allowed set (`application/pdf`, `image/*`, `text/markdown`, `text/plain`, `application/json`).
3. A SHA-256 checksum is computed. If a `QuestionAsset` with the same checksum already exists, the upload is rejected with HTTP 409 to prevent duplicate ingestion.
4. The raw file is saved to local disk via `save_asset()` (`backend/app/storage/local_store.py`) in either the `official/` or `unofficial/` subfolder of `LOCAL_ARCHIVE_MIRROR`.
5. A `QuestionAsset` row is created in the database recording the storage path, MIME type, checksum, source metadata, and page range.
6. A `QuestionJob` row is created with `status="parsing"` and the raw text / page images stored in `pass1_json`.
7. The HTTP response returns immediately with `{"id": "<job_id>", "status": "parsing"}`.
8. `asyncio.create_task(_run_pipeline_with_session(job_id))` fires the pipeline asynchronously.

```mermaid
sequenceDiagram
    participant Client
    participant Endpoint
    participant Disk
    participant DB

    Client->>Endpoint: POST /ingest/official/pdf (multipart)
    Endpoint->>Endpoint: validate MIME + size
    Endpoint->>Endpoint: compute SHA-256 checksum
    Endpoint->>DB: SELECT QuestionAsset WHERE checksum=X
    DB-->>Endpoint: (none — not duplicate)
    Endpoint->>Disk: save_asset(content, subfolder="official")
    Endpoint->>DB: INSERT QuestionAsset
    Endpoint->>DB: INSERT QuestionJob (status=parsing)
    Endpoint->>Client: 200 {id, status="parsing"}
    Endpoint-->>Endpoint: create_task(_run_pipeline_with_session)
```

---

### Step 1 — PDF Parsing

**File:** `backend/app/parsers/pdf_parser.py`

For PDF uploads, the file is written to a temporary path and parsed with **PyMuPDF (fitz)**. The parser returns a dict of pages, each containing:

- `text` — machine-readable text layer extracted directly from the PDF.
- `images` — a list of embedded images, each with a `b64` encoded PNG/JPEG and dimensions.
- `page_number` — 1-indexed page number.

If the PDF has a **text layer** (digitally created), the `raw_text` is assembled by joining all page texts and stored in `pass1_json.raw_text`. No OCR is needed.

If the PDF is **scanned** (text layer is empty or whitespace-only), page images are saved to disk in `{LOCAL_ARCHIVE_MIRROR}/images/` as `{filename}_p01.png`, `{filename}_p02.png`, etc. Paths are stored in `pass1_json._page_images`. The pipeline then routes through the OCR gate.

#### Current Table / Graph / Chart Behavior

The current routing is **PyMuPDF-first**, not structure-aware:

1. Parse the PDF with PyMuPDF.
2. If PyMuPDF returns non-empty text, use that text directly.
3. If PyMuPDF returns no text, route page images through OCR.

The pipeline does **not** currently do a first-pass visual/layout inspection that asks, "Does this page contain a table, graph, chart, or figure that needs OCR/VLM handling?" As a result, digitally generated PDFs with embedded text will skip GLM-OCR even if they contain tables or charts.

PyMuPDF can usually read the text inside tables, but `page.get_text("text")` often flattens the table into a linear text stream. That means values may be present, but row/column structure is not guaranteed. For example, a table may become plain text such as `Species Bare ground Patches of vegetation Total ...` rather than a structured table object.

The desired future behavior is:

1. Run PyMuPDF for baseline text extraction.
2. Detect pages with tables, graphs, charts, figures, low text density, or suspicious flattened layout.
3. Send only those pages through GLM-OCR or a layout-aware vision model.
4. Merge the OCR/layout output with PyMuPDF text.
5. Run Pass 1 extraction on the merged representation.

Until that smart routing is implemented, GLM-OCR is only automatic for pages/PDFs where PyMuPDF produces no usable text.

#### Robust Version To Implement

The robust ingestion path should treat PyMuPDF as the first signal, not the final authority. The goal is to preserve the speed and accuracy of embedded PDF text while still capturing layout-dependent content from tables, graphs, charts, diagrams, and figure captions.

Recommended flow:

```mermaid
flowchart TD
    A[PDF Upload] --> B[PyMuPDF text + image extraction]
    B --> C[Page diagnostics]
    C --> D{Needs visual/layout pass?}
    D -- No --> E[Use PyMuPDF text]
    D -- Yes --> F[Render page or use extracted page image]
    F --> G[GLM-OCR or layout-aware VLM]
    G --> H[Merge visual output with PyMuPDF text]
    E --> I[Pass 1 LLM extraction]
    H --> I
```

Page diagnostics should mark a page for visual/layout processing when any of these are true:

- PyMuPDF text is empty or very short relative to the page area.
- The page contains embedded images near question content.
- The text contains table-like patterns: repeated numeric columns, percentage rows, aligned labels, or dense short-line clusters.
- The page contains chart/graph cues: axis labels, legends, plotted values, figure titles, or graph-specific prompt wording.
- The extracted text has suspicious ordering, such as answer choices appearing before the stem, table headers separated from values, or fragmented rows.
- The question stem asks about "the table," "the graph," "the chart," "the figure," or "data from the table."

For pages marked as needing a visual/layout pass:

1. Render the full page at a stable DPI, or use the existing extracted page image when available.
2. Run `glm-ocr:latest` for OCR text when the content is primarily text/table based.
3. Use a layout-aware VLM path when the page contains charts, graphs, or visual relationships that plain OCR may flatten.
4. Store page-level provenance in `pass1_json`, including which pages used PyMuPDF only, which used GLM-OCR, which used VLM, and why.
5. Merge outputs into a structured intermediate representation before Pass 1 extraction.

The merged representation should preserve:

- page number
- raw PyMuPDF text
- OCR text, if used
- table blocks, preferably as rows/columns
- chart/graph descriptions, if used
- figure captions or labels
- diagnostic reasons for visual processing

This avoids running OCR on every digitally generated PDF while still preventing table/chart questions from being degraded by flattened PyMuPDF text.

---

### Step 2 — OCR Strategy Selection

**File:** `backend/app/routers/ingest.py` — `_resolve_ocr_strategy()`

The strategy is resolved in priority order:

1. Per-request `ocr_strategy` form field (explicit override).
2. `OCR_STRATEGY` environment variable / settings default.
3. `"auto"` — the pipeline picks the first available strategy based on what is configured.

**Auto-resolution order:** `glm` → `deepseek` → `ollama` → `anthropic` → `openai`

```mermaid
flowchart TD
    A[ocr_strategy request param] --> B{Specified?}
    B -- Yes --> C[Use requested strategy]
    B -- No --> D[Read OCR_STRATEGY from settings]
    D --> E{= auto?}
    E -- No --> C
    E -- Yes --> F{glm_ocr_model configured?}
    F -- Yes --> G[Use glm]
    F -- No --> H{deepseek_ocr_base_url set?}
    H -- Yes --> I[Use deepseek]
    H -- No --> J{ollama available?}
    J -- Yes --> K[Use ollama VLM]
    J -- No --> L{anthropic_api_key set?}
    L -- Yes --> M[Use anthropic]
    L -- No --> N[Use openai]
```

---

### Step 3 — OCR / Text Extraction

**File:** `backend/app/routers/ingest.py` — OCR gate inside `_run_pipeline()`

This step only runs when `raw_text` is empty and `page_images` are present. There are four strategy paths:

#### Strategy A — GLM-OCR (default)

A two-step process. `glm-ocr:latest` runs via Ollama as a pure OCR engine — it returns plain text from the image with no structural extraction. That text is stored in `pass1_json.raw_text` along with `_ocr_meta`. The pipeline then continues to Pass 1 (LLM extraction) using that raw text as input.

**`_ocr_meta` recorded:** `strategy`, `model`, `page_count`, `latency_ms`, `token_usage`

#### Strategy B — DeepSeek OCR-2

Sends page images to a locally hosted DeepSeek OCR-2 model via the `DeepSeekOCRClient` (`backend/app/parsers/ocr.py`). Returns structured text. Same flow as GLM: raw text → Pass 1 extraction.

#### Strategy C — VLM Fused (Ollama / Anthropic / OpenAI)

A single model call handles both OCR and structural extraction at the same time. The vision prompt (`build_vision_extract_prompt()`) asks the VLM to return a structured JSON with `passage_text`, `questions`, options, and correct answers directly. This **skips Pass 1 entirely** — `extract_root` is populated directly from the VLM response and `raw_text` is set to the sentinel `"_vision_fused_"`.

```mermaid
flowchart LR
    IMG[Page Images] --> GLM["GLM-OCR\nglm-ocr:latest"]
    IMG --> DS["DeepSeek OCR-2\n(local vLLM)"]
    IMG --> VLM["VLM Fused\n(Ollama / Anthropic / OpenAI)"]

    GLM -->|raw_text| P1[Pass 1 LLM Extraction]
    DS -->|raw_text| P1
    VLM -->|extract_root JSON| P2[Pass 2 Annotation]

    style VLM fill:#d4edda
    style P2 fill:#d4edda
```

**Fallback:** If `OCR_FALLBACK=true` (default), a failing GLM or DeepSeek strategy automatically falls back to Ollama VLM before erroring the job.

---

### Step 4 — Pass 1: LLM Extraction

**File:** `backend/app/routers/ingest.py` — inside `_run_pipeline()`
**Prompt:** `backend/app/prompts/extract_prompt.py` — `build_extract_prompt()`

The extraction LLM receives the raw text (up to 100,000 characters) and a system prompt that instructs it to return JSON in a specific schema:

```json
{
  "passage_text": "...",
  "source_exam_code": "PT1",
  "source_subject_code": "verbal",
  "source_section_code": "01",
  "source_module_code": "01",
  "questions": [
    {
      "source_question_number": 3,
      "question_text": "...",
      "options": [{"label": "A", "text": "..."}, ...],
      "correct_option_label": "A"
    }
  ]
}
```

The LLM response is parsed by `extract_json_from_text()` (`backend/app/parsers/json_parser.py`), which strips markdown fences and handles partial JSON.

The result is stored in `pass1_json` alongside:
- `_llm_meta` — provider, model, latency, token usage.
- `_ocr_meta` — **preserved from before this call** (the bug fix from OCR_STRATEGY_PLAN.md ensures OCR provenance is not overwritten).
- `_extracted_count` — number of questions extracted (before validation).

The job status advances to `"extracting"` during this step.

---

### Step 5 — Question Normalization & Deduplication

**File:** `backend/app/routers/ingest.py` — `_normalize_extracted_questions()`

Handles two output formats from the LLM:

1. **Batch format** — `{ passage_text, questions: [...] }` — the standard multi-question response.
2. **Legacy flat format** — a single question at the top level.

For each question in the batch:
- Shared `passage_text` and source fields are merged into each question dict.
- Option labels are normalized — `"A)"`, `"A."`, `"a"` → `"A"`.
- `correct_option_label` is normalized the same way.
- **Deduplication by question text** — if two questions share the same `question_text`, the second is silently dropped. VLMs occasionally hallucinate duplicate rows.

If more than one question is extracted, a shared `passage_group_id` UUID is generated so all questions from the same passage can be retrieved together.

---

### Step 6 — Question Number Validation

**File:** `backend/app/routers/ingest.py` — `_validate_question_numbers()` and `_verify_qnums_against_ocr()`

For **official** ingestion only — four checks run in sequence:

1. **Null check** — every question must have a non-null integer `source_question_number`. Null values block UUID5 generation.
2. **Range check** — numbers must fall within the expected DSAT range for the given `subject_code` / `module_code`:
   - `verbal/01`, `verbal/02`: questions 1–27
   - `math/01`, `math/02`: questions 1–22
3. **Duplicate check** — no two questions in the same batch may share a number.
4. **Contiguity check** — the numbers must form a consecutive sequence with no gaps.

Additionally, for GLM/DeepSeek paths where raw OCR text is available, a **cross-check** runs: `_scan_qnums_from_ocr()` scans the OCR text for standalone integers and compares them to the LLM-extracted numbers. Mismatches are recorded as warnings.

These checks produce warning dicts, not hard failures. Warnings are appended to `validation_errors_jsonb` and ingestion continues.

---

### Step 7 — Pass 2: LLM Annotation

**File:** `backend/app/routers/ingest.py` — per-question loop inside `_run_pipeline()`
**Prompt:** `backend/app/prompts/annotate_prompt.py` — `build_annotate_prompt()`

For each extracted question, the annotation LLM receives the full question dict and the DSAT rules specification, and returns a rich classification JSON. This is the most semantically complex step.

The annotation output includes:

| Field group | Examples |
|---|---|
| Grammar classification | `grammar_role_key`, `grammar_focus_key`, `syntactic_trap_key` |
| Reading classification | `reading_focus_key`, `reading_skill_family_key`, `reasoning_trap_key` |
| Explanation | `explanation_short` (≤25 words), `explanation_full` |
| Option analysis | Per-option `distractor_type_key`, `why_wrong`, `plausibility_source_key`, `student_failure_mode_key` |
| Generation profile | `generation_profile` — stored for downstream question generation |
| Confidence | `annotation_confidence` (0.0–1.0), `needs_human_review` (bool) |

After the LLM call:
- `extract_json_from_text()` parses the raw output.
- `normalize_annotation()` (`backend/app/parsers/json_parser.py`) fills in defaults and normalizes key names.
- `enforce_nullability()` hard-enforces domain firewall rules — grammar-only keys are set to `null` on reading questions and vice versa. This prevents LLM hallucinations from bleeding across domains.

The job status is `"annotating"` during this step. This step runs **once per question** in the batch — a 27-question module will make 27 annotation calls.

---

### Step 8 — Overlap Detection

**File:** `backend/app/pipeline/overlap.py` — `detect_overlaps()`

Runs only for **unofficial** and **generated** questions. Not run for official content.

Uses Jaccard similarity to compare the new question's passage text and question text against all existing active official questions in the database. Any pair with similarity above the threshold (default 0.4) is flagged.

If overlaps are found:
- `official_overlap_status` is set to `"possible"` on the new question.
- `QuestionRelation` rows are created linking the unofficial question to each matching official question.

The job status is `"overlap_checking"` during this step.

---

### Step 9 — Structural Validation

**File:** `backend/app/pipeline/validator.py` — `validate_question()`

Each question is validated against a checklist derived from PRD §15:

| Check | Severity |
|---|---|
| `question_text` present | blocking |
| Exactly 4 options | blocking |
| `correct_option_label` is A, B, C, or D | blocking |
| Official: `source_exam_code`, `source_module_code`, `source_question_number` present | blocking |
| Generated: `generation_source_set` or `derived_from_question_id` present | blocking |
| `explanation_short` or `explanation_full` present | review |
| `grammar_focus_key` valid and consistent with `grammar_role_key` | review |
| `reading_focus_key` valid and consistent with `reading_skill_family_key` | review |

**Blocking** errors cause the question to be skipped — it is not persisted and its index and error details are appended to `validation_errors_jsonb`.

**Review** errors allow persistence but flag the question for human review.

The job status is `"validating"` during this step.

---

### Step 10 — Persistence

**File:** `backend/app/routers/ingest.py` — `_persist_single_question()`

For each question that passes validation, four rows are inserted in a single transaction:

```mermaid
erDiagram
    QuestionJob ||--o{ Question : "creates"
    Question ||--|{ QuestionVersion : "has versions"
    Question ||--|{ QuestionAnnotation : "has annotations"
    Question ||--|{ QuestionOption : "has options (A-D)"
    Question }o--o| QuestionAsset : "raw source"
    Question }o--o{ QuestionRelation : "overlap links"

    Question {
        uuid id
        string content_origin
        string source_exam_code
        string practice_status
        uuid latest_annotation_id
        uuid latest_version_id
        uuid passage_group_id
    }

    QuestionVersion {
        uuid id
        int version_number
        text question_text
        text passage_text
        jsonb choices_jsonb
        string correct_option_label
    }

    QuestionAnnotation {
        uuid id
        string provider_name
        string model_name
        jsonb annotation_jsonb
        jsonb generation_profile_jsonb
        jsonb confidence_jsonb
    }

    QuestionOption {
        uuid id
        string option_label
        text option_text
        bool is_correct
        string distractor_type_key
        string student_failure_mode_key
    }
```

**Official question IDs** are deterministic UUID5s derived from `exam:subject:section:module:question_number` using the fixed RFC 4122 URL namespace. The same question ingested twice produces the same ID, and a `UNIQUE` constraint on the canonical identity tuple prevents duplicates at the database level.

**`practice_status`** is set based on origin and configuration:
- `official` + `OFFICIAL_AUTO_ACTIVATE_FOR_TESTING=true` → `"active"`
- `official` + auto-activate off → `"draft"` (requires admin review)
- `unofficial` / `generated` → `"active"`

---

### Step 11 — YAML Export

**File:** `backend/app/storage/yaml_export.py` (via `_export_question()` in `ingest.py`)

After a question is successfully persisted, it is also exported to a YAML file under `LOCAL_ARCHIVE_MIRROR`:

- Official questions: `{archive}/official/{exam_code}/{module_code}/{question_id}.yaml`
- Unofficial/generated: `{archive}/unofficial/{question_id}.yaml`

This provides a portable, version-controllable snapshot of every ingested question outside the database.

---

## 4. OCR Strategies In Detail

| Strategy | Key | Provider | Flow |
|---|---|---|---|
| GLM-OCR | `glm` | Ollama (`glm-ocr:latest`) | Image → raw text → Pass 1 LLM |
| DeepSeek OCR-2 | `deepseek` | Local vLLM/LMDeploy | Image → raw text → Pass 1 LLM |
| Ollama VLM Fused | `ollama` | Ollama (vision model) | Image → structured JSON (skips Pass 1) |
| Anthropic Fused | `anthropic` | Anthropic API | Image → structured JSON (skips Pass 1) |
| OpenAI Fused | `openai` | OpenAI API | Image → structured JSON (skips Pass 1) |

**GLM** is the default (`OCR_STRATEGY=glm`). It is the most accurate for DSAT scans because it separates OCR from extraction — the OCR step is a simple text dump, and the extraction LLM gets clean text as input rather than having to parse both content and structure from pixels simultaneously.

**Fallback chain:** When `OCR_FALLBACK=true`, a failing GLM or DeepSeek run silently falls back to Ollama VLM before reporting failure, so that a transient model crash doesn't kill the entire ingestion job.

---

## 5. Job Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> parsing : job created
    parsing --> extracting : OCR complete (or text already available)
    extracting --> annotating : Pass 1 complete
    annotating --> overlap_checking : annotation complete\n(unofficial/generated only)
    annotating --> validating : annotation complete\n(official)
    overlap_checking --> validating : overlap check complete
    validating --> approved : all questions pass
    validating --> needs_review : official content or review-severity errors
    validating --> failed : all questions have blocking errors
    extracting --> failed : LLM / OCR error
    annotating --> failed : LLM error (all questions)
```

| Status | Meaning |
|---|---|
| `parsing` | File received, job and asset rows created |
| `extracting` | Pass 1 LLM running (or OCR in progress) |
| `annotating` | Pass 2 LLM running |
| `overlap_checking` | Jaccard similarity comparison against official questions |
| `validating` | Structural validation running |
| `approved` | All questions persisted and active |
| `needs_review` | Questions persisted but flagged for human review |
| `failed` | No questions could be persisted |

---

## 6. Database Schema

The 10 core tables involved in ingestion:

| Table | Purpose |
|---|---|
| `question_jobs` | Pipeline job tracker — one row per ingestion request |
| `question_assets` | Raw file metadata and storage path |
| `questions` | One row per question — canonical current state |
| `question_versions` | Full history of every edit to a question |
| `question_annotations` | LLM classification output per version |
| `question_options` | All four answer choices with distractor metadata |
| `question_relations` | Overlap / derivation links between questions |
| `llm_evaluations` | Optional quality scores from evaluation runs |
| `users` | Student accounts |
| `user_progress` | Per-student answer history |

`question_jobs.pass1_json` and `pass2_json` are `JSONB` columns that hold intermediate pipeline state and LLM metadata. `validation_errors_jsonb` holds the full list of warnings and errors encountered during the run.

---

## 7. Key Files Reference

| File | Role |
|---|---|
| `backend/app/routers/ingest.py` | All ingestion endpoints and the `_run_pipeline()` function |
| `backend/app/parsers/pdf_parser.py` | PDF → text + images via PyMuPDF |
| `backend/app/parsers/ocr.py` | DeepSeek OCR-2 client with retry |
| `backend/app/parsers/json_parser.py` | LLM output → Python dict (strips fences, handles malformed JSON) |
| `backend/app/prompts/extract_prompt.py` | Pass 1 system/user prompt builder |
| `backend/app/prompts/annotate_prompt.py` | Pass 2 system/user prompt builder + domain enforcement |
| `backend/app/pipeline/validator.py` | Structural validation rules (PRD §15) |
| `backend/app/pipeline/overlap.py` | Jaccard-based overlap detection |
| `backend/app/pipeline/orchestrator.py` | Job state machine (advance / fail helpers) |
| `backend/app/models/db.py` | All SQLAlchemy ORM models |
| `backend/app/models/payload.py` | HTTP request/response Pydantic models |
| `backend/app/llm/factory.py` | LLM provider factory (caches instances by config) |
| `backend/app/llm/ollama_provider.py` | Ollama LLM + vision provider with retry |
| `backend/app/llm/retry.py` | `@with_retry` decorator — exponential backoff |
| `backend/app/storage/local_store.py` | File save + SHA-256 checksum |
| `backend/app/storage/yaml_export.py` | Post-persistence YAML archive export |
| `backend/app/config.py` | All settings loaded from `.env` |
| `backend/migrations/versions/` | Alembic migration history (001–015) |

---

## 8. OCR Benchmark Endpoint

Two additional endpoints allow side-by-side comparison of OCR strategies on the same file.

### `POST /ingest/benchmark/ocr`

Accepts a single file upload and fires two parallel ingestion jobs — one for each strategy specified (or all available strategies). All jobs share a `comparison_group_id`.

Returns immediately with:

```json
{
  "comparison_group_id": "<uuid>",
  "jobs": [
    {"id": "<job_id>", "strategy": "glm"},
    {"id": "<job_id>", "strategy": "deepseek"}
  ]
}
```

### `GET /ingest/benchmark/ocr/{comparison_group_id}`

Polls the result. Returns `ready: true` when all jobs have reached a terminal state.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB

    Client->>API: POST /ingest/benchmark/ocr (file)
    API->>DB: INSERT QuestionJob (strategy=glm, group_id=X)
    API->>DB: INSERT QuestionJob (strategy=deepseek, group_id=X)
    API->>Client: {comparison_group_id: X, jobs: [...]}

    loop Poll until ready=true
        Client->>API: GET /ingest/benchmark/ocr/X
        API->>DB: SELECT QuestionJob WHERE comparison_group_id=X
        DB-->>API: [job_glm, job_deepseek]
        API->>Client: {ready: false, results: [...]}
    end

    Client->>API: GET /ingest/benchmark/ocr/X
    API->>Client: {ready: true, results: [glm_result, deepseek_result]}
```

---

## 9. Configuration

All settings are loaded from `backend/.env` (see `backend/app/config.py`).

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev` | PostgreSQL connection string |
| `ADMIN_API_KEYS` | `admin-test-key` | Comma-separated admin keys |
| `OCR_STRATEGY` | `glm` | Default OCR strategy (`glm`, `deepseek`, `ollama`, `anthropic`, `openai`, `auto`) |
| `OCR_FALLBACK` | `true` | Fall back to Ollama VLM if primary OCR fails |
| `GLM_OCR_MODEL` | `glm-ocr:latest` | Ollama model name for GLM-OCR |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `DEFAULT_ANNOTATION_PROVIDER` | `ollama` | LLM provider for Pass 2 annotation |
| `DEFAULT_ANNOTATION_MODEL` | `kimi-k2.6:cloud` | Model for Pass 2 annotation |
| `VISION_MAX_IMAGES` | `10` | Max page images passed to VLM |
| `LOCAL_ARCHIVE_MIRROR` | `./archive` | Directory for saved assets and YAML exports |
| `OFFICIAL_AUTO_ACTIVATE_FOR_TESTING` | `true` | Skip `needs_review` and auto-activate official questions |

---

## 10. Error Handling & Retry

### Retry decorator

Both OCR providers and the Ollama LLM provider use the `@with_retry` decorator from `backend/app/llm/retry.py`. Default settings: 3 attempts, 1s base delay, 30s max delay (exponential backoff).

```
backend/app/llm/ollama_provider.py   — complete() and complete_vision()
backend/app/parsers/ocr.py           — DeepSeekOCRClient.extract()
```

### Per-question error isolation

Annotation and validation errors are caught **per question** inside the loop. A single failing question does not abort the rest of the batch. Its errors are logged to `validation_errors_jsonb` and processing continues with the next question.

### Job-level failure

If **all** questions in a batch fail (blocking validation errors or annotation exceptions), the job is marked `"failed"`. If **at least one** succeeds, the job is marked `"approved"` or `"needs_review"`.

### Checksum deduplication

Re-uploading the same file returns HTTP 409 before any processing starts. This prevents duplicate jobs from consuming LLM quota.
