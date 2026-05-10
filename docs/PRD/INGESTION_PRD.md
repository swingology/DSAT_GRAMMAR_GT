# DSAT Backend PRD — Ingestion, Generation, and Student Practice

**Version:** 2.1
**Date:** 2026-05-09
**Status:** Current
**Supersedes:** v2.0 (2026-05-09)
**Changes in v2.1:** Added §8 OCR Strategy (two implementation options); updated §19 config; updated §22 Known Open Gaps.

---

## 1. Purpose

This document specifies the backend product for the DSAT question corpus. The system
supports four linked workflows:

- Ingesting official DSAT questions from PDF files
- Ingesting unofficial questions from flexible source formats
- Generating new DSAT-style questions from the official corpus
- Delivering active questions to students for practice and tracking their progress

The corpus spans two subjects — **Grammar** (Conventions and Expression of Ideas) and
**Reading** (Craft and Structure, Information and Ideas) — and uses two active rule sets:

- `rules_agent_dsat_grammar_ingestion_generation_v7.md` — grammar questions
- `rules_agent_dsat_reading_v2.md` — reading questions

---

## 2. Product Goals

1. Build a high-trust official corpus from released DSAT PDF material.
2. Build a flexible unofficial corpus from screenshots, images, Markdown, JSON, and
   plain text.
3. Build a robust generation workflow using the official corpus as the gold reference.
4. Compare multiple LLMs during beta to determine which combination produces the best
   metadata, explanations, and generated questions.
5. Store all assets, annotations, lineage, and edits in a backend that supports student
   practice tracking.
6. Deliver approved questions to students and record their answer attempts.

---

## 3. Scope

### 3.1 In-Scope Inputs

- Official PDF exams and extracts
- Unofficial PDFs, Markdown files, raster images and screenshots (PNG, JPG, JPEG, WEBP,
  GIF), pre-extracted JSON, plain text
- Generated-question requests

### 3.2 Out-of-Scope

- Video, audio, handwritten scans that cannot be OCR'd
- `table_data` and `graph_data` persistence — these fields are validated by the pipeline
  but have no database columns; storing chart and graph stimulus data is future work
- Public exam material distribution

---

## 4. Content Model

All questions carry a `content_origin` that determines their workflow:

| `content_origin` | Meaning | Primary Intake |
|---|---|---|
| `official` | Released College Board DSAT questions — the canonical reference corpus | PDF only |
| `unofficial` | Third-party, adapted, captured, or user-provided questions | PDF, image, Markdown, JSON, text |
| `generated` | Questions produced by the generation pipeline | Generation request only |

### 4.1 Overlap and Lineage Fields

| Field | Values | Purpose |
|---|---|---|
| `official_overlap_status` | `none` / `possible` / `confirmed` | Whether a non-official question overlaps an official item |
| `canonical_official_question_id` | nullable UUID | Points to the matching official question when overlap is confirmed |
| `derived_from_question_id` | nullable UUID | Points to a parent question used in generation or adaptation |
| `generation_source_set` | JSONB | Official and unofficial examples used to generate a new question |
| `passage_group_id` | nullable UUID | Groups questions that share a common passage |

### 4.2 Practice Status

| `practice_status` | Meaning |
|---|---|
| `draft` | Awaiting admin review; not recallable by students |
| `active` | Approved; recallable by students |
| `retired` | Rejected or withdrawn; not recallable |

---

## 5. Corpus Principles

### 5.1 Official Questions Are the Gold Reference Set

Official questions serve three roles: canonical practice items, metadata quality
references, and grounding examples for generation. The initial seed set covers released
tests PT01 and PT06–PT11.

Official questions are created as `draft` by default. The `OFFICIAL_AUTO_ACTIVATE_FOR_TESTING`
flag (`false` by default) can bypass this during development. There is currently no
admin API path to approve an official question — this is a known open gap.

### 5.2 Unofficial Questions Are Flexible but Structured

Unofficial questions provide additional inventory and taxonomy coverage. They are
processed by the same two-pass LLM pipeline as official questions and must pass the same
validation and overlap checks before being approved for student practice.

### 5.3 Generated Questions Must Be Traceable

Every generated question records:

- which LLM produced it
- which rule-set version was used
- which source questions were used as examples (`generation_source_set`)
- whether it overlaps any official question
- whether it passed admin review

Generated questions with an unresolved official overlap (`official_overlap_status != "none"`)
cannot be approved.

---

## 6. LLM Rule Sets

### 6.1 Grammar Questions

Rule file: `rules_agent_dsat_grammar_ingestion_generation_v7.md`

Grammar questions are classified by:

- `grammar_role_key` — top-level skill category
  (`sentence_boundary`, `agreement`, `verb_form`, `modifier`, `punctuation`,
  `parallel_structure`, `pronoun`, `expression_of_ideas`)
- `grammar_focus_key` — specific grammar concept within the role
  (35+ values, each scoped to a role)
- `syntactic_trap_key` — cognitive distraction in the question
- `difficulty_overall` — `low` / `medium` / `high`

### 6.2 Reading Questions

Rule file: `rules_agent_dsat_reading_v2.md`

Reading questions are classified by:

- `question_family_key` — `craft_and_structure` or `information_and_ideas`
- `reading_skill_family_key` — skill category within the family
  (`command_of_evidence_textual`, `command_of_evidence_quantitative`,
  `central_ideas_and_details`, `inferences`, `words_in_context`,
  `text_structure_and_purpose`, `cross_text_connections`)
- `reading_focus_key` — specific focus within the skill family

### 6.3 Stimulus Modes

All questions carry a `stimulus_mode_key` that describes the passage format:

`sentence_only`, `passage_excerpt`, `prose_single`, `prose_paired`,
`prose_plus_table`, `prose_plus_graph`, `notes_bullets`, `poem`

Cross-text questions (`prose_paired`) require `paired_passage_text`.
Underline-the-word questions require `underlined_text`.
Both fields are persisted in `Question` and `QuestionVersion`.

---

## 7. Ingestion Pipelines

### 7.1 Official PDF Ingestion

- Input: PDF only, uploaded as multipart form data
- Required form fields: `source_exam_code`, `source_module_code`, `source_subject_code`
- Optional: `provider_name`, `model_name`, `ocr_strategy` (`deepseek` / `ollama` / `auto`)
- One upload may contain many questions; each becomes its own job record
- Pipeline: `pending → parsing → extracting → annotating → overlap_checking → validating → needs_review`
- Official questions land as `draft` by default; auto-activation is gated behind
  `OFFICIAL_AUTO_ACTIVATE_FOR_TESTING=true`
- Source metadata required: `source_exam_code`, `source_module_code`, `source_question_number`

### 7.2 Unofficial File Ingestion

Accepted MIME types: `application/pdf`, `image/png`, `image/jpeg`, `image/webp`,
`image/gif`, `text/markdown`, `text/plain`, `application/json`

Max upload size: 50 MB per file

- PDF: extracted via `pdfplumber`; scanned pages trigger the OCR strategy (see §8). Admin may pass `ocr_strategy` to select DeepSeek or Ollama VLM for this job.
- Images/screenshots: always routed through the OCR strategy (see §8). Admin may pass `ocr_strategy` to select provider.
- Markdown: front matter parsed for optional source hints; body treated as raw text
- JSON: direct structured ingestion; required fields validated
- Text: passthrough to extraction pass

Multi-question sources (PDFs) produce multiple jobs, one per extracted question.

**Known gap:** When one asset produces multiple questions, only the first question
is linked to the asset record via `question_assets.question_id`. Subsequent questions
from the same asset are not linked. This is a medium-priority open item.

**Known gap:** Raw ingest text is truncated at 50,000 characters before being stored
in `pass1_json`. Long multi-question sources can lose later content without a
blocking error. This is a medium-priority open item.

### 7.3 Unofficial Batch Ingestion

- Input: up to 10 files per batch request
- Each file is processed independently through the same pipeline as single-file ingest
- Returns a list of job records, one per file

### 7.4 Text Ingestion

- Input: raw text body (`POST /ingest/text`)
- Accepts optional `source_exam_code`, `source_module_code`, `source_subject_code`
- Same two-pass pipeline as file ingest

---

## 8. OCR Strategy

### 8.1 Gap and Context

`parse_pdf()` uses `page.get_text("text")` which works only for PDFs with embedded text
layers. Scanned PDFs and standalone image uploads produce empty `raw_text` — the pipeline
fails with "No raw text available". The current codebase has no OCR step, no multimodal
LLM call, and no image-to-text preprocessing stage.

**Trigger condition:** Any ingest job where `raw_text` is empty or whitespace-only after
the parsing step, and page images are available.

### 8.2 Integration Architecture

The OCR gate is inserted in `_run_pipeline()` before the existing "no raw text" failure:

```
Scanned PDF / Image upload
  → parse_pdf() or parse_image() → no raw_text, images extracted
  → OCR gate (strategy selected by OCR_STRATEGY config)
      → Option A: DeepSeek OCR API → raw_text → Pass 1 extraction (existing)
      → Option B: Ollama VLM → structured JSON (OCR + extraction fused, skips Pass 1)
  → Pass 2 annotation (existing)
  → overlap_checking → validating → needs_review
```

Two provider-level changes are required regardless of option:

1. **`LLMProvider.complete_vision()`** — new optional method on the provider protocol.
   Takes `system: str`, `user: str`, `images: list[ImageContent]`. Default raises
   `NotImplementedError`. Implemented by `AnthropicProvider`, `OpenAIProvider`,
   and `OllamaProvider`.

2. **`app/parsers/ocr.py`** — standalone module for Option A: calls the DeepSeek API
   and returns `raw_text`. Not used in Option B.

---

### 8.3 Option A — DeepSeek OCR (Local — Docker or Ollama)

**Summary:** Run a DeepSeek vision model locally as a dedicated OCR preprocessing step.
Images are sent to the local endpoint, which returns structured Markdown text. That text
feeds into the existing Pass 1 extraction prompt unchanged. No cloud API, no API key,
no data leaves the machine.

**Flow:**
```
Images → DeepSeek VL (local endpoint) → Markdown raw_text → Pass 1 (extract) → Pass 2 (annotate)
```

**Runtime options (admin's choice at setup time):**

| Runtime | How to run | Endpoint |
|---|---|---|
| **Docker** | `docker run --gpus all -p 8001:8000 vllm/vllm-openai --model deepseek-ai/DeepSeek-VL2-Small` | `http://localhost:8001` (OpenAI-compatible) |
| **Ollama** | `ollama pull deepseek-vl2` then `ollama serve` | `http://localhost:11434` (Ollama API) |

Recommended model: **DeepSeek-OCR-2** (~3B params, ~6–8 GB VRAM) — purpose-built document
OCR model, produces Markdown-structured output, has a dedicated vLLM recipe. For general
vision tasks beyond OCR, use DeepSeek-VL2-Tiny (10–16 GB VRAM) instead.

**API integration:** Both runtimes expose an OpenAI-compatible `/v1/chat/completions`
endpoint (Docker via vLLM/SGLang; Ollama natively). A thin `DeepSeekOCRProvider` class
wraps the existing `OpenAIProvider` with a custom `base_url` and no auth header.
Call with image content blocks and a minimal system prompt requesting Markdown text output.

**Implementation steps:**
1. Add `DEEPSEEK_OCR_BASE_URL` and `DEEPSEEK_OCR_MODEL` to `Settings`
2. Create `app/parsers/ocr.py` with `deepseek_ocr(images: list[ImageContent]) -> str`
   — posts to `DEEPSEEK_OCR_BASE_URL/v1/chat/completions`, returns text
3. In `_run_pipeline()`, when `not raw_text and images` and `OCR_STRATEGY == "deepseek"`,
   call `deepseek_ocr()` → store result as `raw_text` → continue with Pass 1 as normal
4. Store provenance in `pass1_json._ocr_meta: {provider: "deepseek", model, runtime, page_count}`

**Accuracy and cost:**

| Dimension | Value |
|---|---|
| Accuracy (clean document) | 96–98% |
| Accuracy (complex layout / tables) | 93–96% |
| Cost per page | $0 — local compute only |
| Latency per page | 2–6s (OCR, GPU) + 2–4s (Pass 1 LLM) = 4–10s total |
| Layout preservation | Good — Markdown with table and column structure |

**Pros:**
- Purpose-built for document OCR; strong on multi-column exam layouts and tables
- Fully local — no API key, no internet, no data residency concern
- OpenAI-compatible API on both runtimes — minimal new HTTP infrastructure
- Output is plain text, so zero changes to Pass 1 prompt or extraction logic
- Docker runtime isolates the model and GPU allocation cleanly

**Cons:**
- Two-pass latency: OCR first, then LLM extraction — slower than vision-fused Option B
- Requires a second GPU allocation (or time-shared with Option B if same Ollama instance)
- Docker setup requires vLLM or SGLang image and CUDA drivers; Ollama requires model pull
- DeepSeek-VL2-Small needs ~5 GB VRAM; full VL2 needs ~20 GB

**Configuration:**

```bash
OCR_STRATEGY=deepseek
DEEPSEEK_OCR_BASE_URL=http://localhost:8001   # Docker/vLLM endpoint
# or for Ollama runtime:
# DEEPSEEK_OCR_BASE_URL=http://localhost:11434
DEEPSEEK_OCR_MODEL=deepseek-vl2-small
```

---

### 8.4 Option B — Ollama VLM (Local, Lightweight)

**Summary:** Use a vision-capable model running locally in Ollama. The VLM reads the
page images and returns structured extraction JSON directly — fusing OCR and Pass 1
extraction into a single call. No intermediate text is produced; the output goes
directly into `pass1_json`.

**Flow:**
```
Images → Ollama VLM (complete_vision) → structured JSON → pass1_json (skips Pass 1)
           → Pass 2 annotation (existing)
```

**Recommended models (in order of preference):**

| Model | Size on disk | Vision quality | RAM required |
|---|---|---|---|
| `qwen2.5-vl:7b` (current default) | ~4.7 GB | Excellent — strong English document OCR | ~6 GB |
| `llava-phi3:latest` | ~2.9 GB | Good — lighter weight, good for clean scans | ~4 GB |
| `minicpm-v:8b` | ~5.5 GB | Very good — multilingual, table-aware | ~7 GB |
| `llava:7b` | ~4.5 GB | Adequate — original LLaVA, good baseline | ~6 GB |

**Implementation steps:**
1. Add `complete_vision()` to `OllamaProvider`: send `POST /api/chat` with
   `images: [base64_str]` in the user message (Ollama's native vision format)
2. Create `build_vision_extract_prompt() -> tuple[str, str]` — same system prompt as
   Pass 1 (EXTRACT_SYSTEM_PROMPT) with a vision-aware user message:
   `"Read the question from the image(s) and extract to JSON per the schema above."`
3. In `_run_pipeline()`, when `not raw_text and images` and
   `OCR_STRATEGY in ("auto", "vision")` and `OCR_VISION_PROVIDER == "ollama"`,
   call `provider.complete_vision(system, user, images)` → parse JSON response →
   store directly as `pass1_json`, set `_ocr_meta: {provider: "ollama", model: ...}`
4. Skip the normal Pass 1 text extraction call — jump directly to Pass 2 annotation

**Accuracy and cost:**

| Dimension | Value |
|---|---|
| Accuracy (clean document) | 94–97% (qwen2.5-vl) |
| Accuracy (complex layout) | 89–94% — degrades on dense multi-column |
| Cost per page | $0 — runs locally on your hardware |
| Latency per page | 4–12s on GPU (qwen2.5-vl:7b on consumer GPU); 20–60s on CPU |
| Layout preservation | Good for single-question pages; weaker on dense layouts |

**Pros:**
- Zero per-page cost — entirely local, no API keys, no internet required
- Data privacy: nothing leaves the machine (important for exam IP)
- Single-pass: OCR + extraction fused into one LLM call — simpler than Option A
- `qwen2.5-vl:7b` is already the configured default (`OCR_VISION_MODEL`)
- Ollama is already in the provider stack — minimal new infrastructure

**Cons:**
- Requires a GPU for reasonable latency; CPU-only is very slow (20–60s/page)
- Ollama must be running and the model must be pulled (`ollama pull qwen2.5-vl:7b`)
- Model must support vision — not all Ollama models do
- Quality on dense, multi-column, or low-resolution scans is lower than DeepSeek
- JSON extraction reliability varies by model — needs schema enforcement via prompt

**Configuration:**

```bash
OCR_STRATEGY=vision
OCR_VISION_PROVIDER=ollama
OCR_VISION_MODEL=qwen2.5-vl:7b
OLLAMA_BASE_URL=http://localhost:11434
OCR_FALLBACK=true                         # fall back to text extraction if vision fails
VISION_MAX_IMAGES=10                      # max images per vision call
```

---

### 8.5 Strategy Comparison

| Dimension | Option A — DeepSeek OCR (local) | Option B — Ollama VLM |
|---|---|---|
| **Accuracy (clean)** | 96–98% | 94–97% |
| **Accuracy (complex layout)** | 93–96% | 89–94% |
| **Cost per page** | $0 — local compute | $0 — local compute |
| **Latency** | 4–10s (OCR pass + Pass 1) | 4–12s (GPU) / 20–60s (CPU) |
| **Data residency** | Local — no external calls | Local — no external calls |
| **Extra API key** | No | No |
| **Infrastructure** | Docker (vLLM) or Ollama + model | Ollama running + model pulled |
| **Pipeline** | Two-pass: OCR → Pass 1 (text) | Single-pass: vision → JSON fused |
| **Best for** | Dense layouts, tables, charts | Clean scans, fast single-page uploads |

### 8.6 Admin Selection at Ingest Time

Both options are configured simultaneously via env vars and are available at all times.
The admin selects the OCR strategy **per-job** by passing an optional `ocr_strategy`
field on any ingest request. If omitted, the server falls back to `OCR_STRATEGY` from
config.

| `ocr_strategy` value | Behavior |
|---|---|
| `deepseek` | Use Option A (DeepSeek OCR API) regardless of config default |
| `ollama` | Use Option B (Ollama VLM) regardless of config default |
| `auto` (default) | Server picks: Ollama if available, DeepSeek if key present, error otherwise |
| omitted | Inherits server default from `OCR_STRATEGY` env var |

**Admin workflow:**
- Upload a scanned PDF via `POST /ingest/official/pdf` or `POST /ingest/unofficial/file`
- Include `ocr_strategy=deepseek` in the form data to force DeepSeek for this job
- Include `ocr_strategy=ollama` to force Ollama VLM for this job
- The selected strategy is recorded in `pass1_json._ocr_meta.strategy` for audit

**Example form data (unofficial file):**

```
POST /ingest/unofficial/file
X-API-Key: admin-key
Content-Type: multipart/form-data

file=<scanned-pdf>
ocr_strategy=deepseek
```

### 8.7 Fallback Chain

```
Per-job resolution (ocr_strategy field or OCR_STRATEGY config):
  "deepseek" → call DeepSeek OCR API
  "ollama"   → call Ollama VLM via complete_vision()
  "auto"     → try Ollama first (if model reachable), then DeepSeek (if key present)

OCR_FALLBACK=true (applies within a strategy, not across strategies):
  - Ollama VLM fails → retry 3× (existing retry decorator) → fail job with clear error
  - DeepSeek API fails → retry 3× → fail job with clear error
  - Cross-strategy fallback requires OCR_STRATEGY=auto or explicit admin selection
```

---

## 9. Two-Pass LLM Pipeline

Every ingested and generated question runs through the same pipeline.

### Pass 1 — Extraction

Extracts raw question content without taxonomy classification:

- `question_text`
- `passage_text`
- `paired_passage_text` (cross-text questions)
- `underlined_text` (words-in-context questions)
- answer options and `correct_option_label`
- source metadata
- `stimulus_mode_key`, `stem_type_key`
- `explanation_short`, `explanation_full`

Output is stored in `question_jobs.pass1_json`.

**Note:** For Option B (Ollama VLM), Pass 1 is fused with OCR. The vision call produces
the same JSON schema as the normal Pass 1 text extraction call. Pass 2 proceeds
unchanged in both cases.

### Pass 2 — Annotation

Classifies the extracted question against the full DSAT taxonomy and produces:

- Grammar taxonomy: `grammar_role_key`, `grammar_focus_key`, `syntactic_trap_key`,
  `difficulty_overall`, `stimulus_mode_key`
- Reading taxonomy: `question_family_key`, `reading_skill_family_key`,
  `reading_focus_key`
- Per-option distractor analysis: `distractor_type_key`, `semantic_relation_key`,
  `plausibility_source_key`, `why_plausible`, `why_wrong`, `distractor_distance`,
  `distractor_competition_score`, `student_failure_mode_key`
- Explanation fields: `explanation_short`, `explanation_full`
- Generation profile: constraints for future generation seeding

Output is stored in `question_jobs.pass2_json` and persisted to `question_annotations`.

### Reannotation

An existing question can be re-run through Pass 2 only via `POST /ingest/reannotate/{question_id}`.
This creates a new annotation and marks the old one stale (`annotation_stale = true`).

---

## 10. Validation

After both LLM passes, the validator enforces:

**Blocking:**
- `question_text` non-empty
- Exactly 4 options with labels A, B, C, D
- `correct_option_label` is A, B, C, or D
- Official question missing `source_exam_code`, `source_module_code`, or
  `source_question_number`
- Generated question missing lineage (`derived_from_question_id` or
  `generation_source_set`)
- Cross-text question (`stem_type_key == "choose_cross_text_connection"`) missing
  `paired_passage_text`
- Quantitative question missing graphic data (validator-level check only; `table_data`
  and `graph_data` are not persisted to the database)

**Taxonomy validation:**
- `grammar_role_key`, `grammar_focus_key`, `syntactic_trap_key`, `stimulus_mode_key`,
  `stem_type_key` checked against the allowed key sets from `ontology.py`

**Note:** `explanation_short` must be ≤ 500 characters. `explanation_full` has no
hard length constraint.

Validation errors are written to `question_jobs.validation_errors_jsonb`. A job with
errors enters `needs_review` status; a clean job also enters `needs_review` (human
review is always required before approval).

---

## 11. Job State Machine

```
pending
  → parsing         (PDF/image being parsed; OCR gate runs here if raw_text is empty)
  → extracting      (Pass 1 LLM, or vision-fused extraction for Option B)
  → generating      (generation Pass 1, if applicable)
  → annotating      (Pass 2 LLM)
  → overlap_checking
  → validating
  → needs_review    (human review required — with or without validation errors)
  → approved        (admin approved; question set to active)
  → failed          (unrecoverable error)
```

Transitions are enforced by the pipeline orchestrator. Not all states are reachable
for every job type.

---

## 12. Generation Workflow

### 12.1 Single Generation

`POST /generate/questions`

Request fields:

| Field | Required | Description |
|---|---|---|
| `target_grammar_role_key` | yes | Grammar role to generate for |
| `target_grammar_focus_key` | yes | Specific grammar focus |
| `target_syntactic_trap_key` | no | Default `none` |
| `difficulty_overall` | no | Default `medium` |
| `source_question_ids` | no | Explicit source examples; auto-selected if omitted |
| `provider_name` | no | Defaults to `DEFAULT_ANNOTATION_PROVIDER` |
| `model_name` | no | Defaults to `DEFAULT_ANNOTATION_MODEL` |

Returns a `JobResponse`. The generation job runs the full two-pass pipeline and
overlap detection.

### 12.2 Multi-Provider Comparison

`POST /generate/questions/compare`

Same request shape as single generation, plus:

| Field | Description |
|---|---|
| `providers` | List of provider name strings; each generates an independent question |

Returns a list of `JobResponse` objects. Each provider's output is a separate job with
the same `comparison_group_id`, enabling side-by-side evaluation.

### 12.3 Inspect Generation Run

`GET /generate/runs/{run_id}`

Returns the job record and linked question (if approved), including lineage and overlap
state.

### 12.4 Overlap Detection

After generation, the system computes passage similarity against all official questions.
A generated question is flagged `official_overlap_status = "possible"` if similarity
exceeds the configured threshold. Generated questions with `official_overlap_status != "none"`
cannot be approved until an admin confirms or clears the overlap.

---

## 13. Admin Workflows

All admin endpoints require the `X-API-Key` header with a key from `ADMIN_API_KEYS`.

### 13.1 Question List

`GET /admin/questions`

Returns questions with their latest annotation and options. Supports filtering by
`practice_status` and `content_origin`, with `limit` (max 200) and `offset` pagination.

### 13.2 Content Editing

`PATCH /admin/questions/{question_id}`

Editable fields: `question_text`, `passage_text`, `paired_passage_text`,
`underlined_text`, `correct_option_label` (A–D), `explanation_text`, `change_notes`

Each edit creates a new `QuestionVersion` and clones the existing `QuestionOption` rows
with updated correctness flags. The `annotation_stale` flag is set to `true` to signal
that re-annotation is needed.

### 13.3 Approval and Rejection

`POST /admin/questions/{question_id}/approve`

Constraints:
- Blocked for `content_origin == "official"` (no automated answer-verification path
  exists — open gap)
- Blocked for `content_origin == "generated"` when `official_overlap_status != "none"`

`POST /admin/questions/{question_id}/reject`

Sets `practice_status = "retired"` and clears linked annotations and evaluations.

`DELETE /admin/questions/{question_id}`

Hard-delete. Preserves job and asset records (audit trail) but removes all question
data. Incoming self-referential FKs on other questions are nulled before deletion.

### 13.4 Overlap Management

`POST /admin/questions/{question_id}/confirm-overlap`

Marks `official_overlap_status = "confirmed"` and links `canonical_official_question_id`
to the matching official question. Requires exactly one official overlap relation.

`POST /admin/questions/{question_id}/clear-overlap`

Marks `official_overlap_status = "none"` and clears `canonical_official_question_id`.
Enables approval of a falsely-flagged generated question.

### 13.5 Question Relations

`GET /admin/relations` — list relations with optional `from_question_id` and
`relation_type` filters; `limit` (max 500) and `offset` supported.

`POST /admin/relations` — create a relation between two distinct questions.
Self-referential relations are rejected (400).

`DELETE /admin/relations/{relation_id}` — remove a relation.

Allowed `relation_type` values: `overlaps_official`, `derived_from`, `near_duplicate`,
`generated_from`, `adapted_from`

### 13.6 LLM Evaluations

`POST /admin/evaluations` — create a manual evaluation record for a job/question pair.

`POST /admin/evaluations/{evaluation_id}/score` — record human scores (0–10 scale):
`score_overall`, `score_metadata`, `score_explanation`, `score_generation`,
plus `review_notes` and `recommended_for_default`.

---

## 14. Practice Recall (Admin)

`GET /questions/recall` — requires admin key.

Returns active questions with annotation metadata. Supports filtering by:

- `grammar_focus` — annotation JSONB `grammar_focus_key`
- `difficulty` — annotation JSONB `difficulty_overall`
- `origin` — `content_origin`
- `limit` (1–100, default 20) and `offset`

`GET /questions/{question_id}` — full detail including all options, latest annotation,
lineage, and overlap state.

`GET /questions/{question_id}/versions` — version history.

---

## 15. Student-Facing API

All student endpoints require the `X-API-Key` header with a key from `STUDENT_API_KEYS`.

### 15.1 Question Recall

`GET /api/questions`

Returns active questions with answer key excluded (`StudentQuestionResponse`). Supports
the same `grammar_focus`, `difficulty`, `origin`, `limit`, and `offset` filters as the
admin recall endpoint.

### 15.2 Answer Submission

`POST /api/submit`

| Field | Type | Description |
|---|---|---|
| `user_id` | int | Registered user |
| `question_id` | UUID | Must be an active question |
| `selected_option_label` | A–D | Student's answer |
| `missed_grammar_focus_key` | optional str | Self-reported focus area missed |
| `missed_syntactic_trap_key` | optional str | Self-reported trap missed |

Correctness is computed server-side (`q.current_correct_option_label == selected_option_label`).
Submissions against non-active questions return 400.

### 15.3 Student Stats

`GET /api/stats/{user_id}`

Returns aggregate stats for a user:

- `total_answered`, `total_correct`, `accuracy`
- `top_missed_focus_keys` — top 5 `grammar_focus_key` values on incorrect answers
- `top_missed_trap_keys` — top 5 `syntactic_trap_key` values on incorrect answers

---

## 16. User Management

### 16.1 Canonical Router (`/users` — admin only)

| Method | Path | Description |
|---|---|---|
| `POST` | `/users` | Create user (`username`: 1–100 chars, unique). Returns 201. |
| `GET` | `/users` | List users with `limit`/`offset`. |
| `GET` | `/users/{user_id}` | Get user by integer ID. |
| `DELETE` | `/users/{user_id}` | Delete user and all progress records. Returns 204. |

### 16.2 Student Router Mirror (`/api/users`)

The student router exposes the same four endpoints at `/api/users`. User creation and
deletion require an admin key; get and list require a student key. This router exists
for client convenience and must remain in sync with the canonical router.

---

## 17. Data Model

### 17.1 `question_jobs`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `job_type` | enum | `ingest` / `generate` / `reannotate` / `overlap_check` |
| `content_origin` | enum | `official` / `unofficial` / `generated` |
| `input_format` | string(20) | `pdf`, `image`, `markdown`, `json`, `text` |
| `status` | enum | See state machine in §11 |
| `provider_name` | string(50) | |
| `model_name` | string(100) | |
| `prompt_version` | string(20) | Default `v3.0` |
| `rules_version` | string(100) | Active rule file name |
| `raw_asset_id` | UUID FK → `question_assets` | nullable |
| `question_id` | UUID FK → `questions` | Set after question is created |
| `pass1_json` | JSONB | Extraction output; includes `_ocr_meta` when OCR was used |
| `pass2_json` | JSONB | Annotation output |
| `validation_errors_jsonb` | JSONB | Array of `{field, message, value}` |
| `comparison_group_id` | UUID | Groups multi-provider compare jobs |
| `created_at`, `updated_at` | timestamptz | |

### 17.2 `questions`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `content_origin` | enum | `official` / `unofficial` / `generated` |
| `source_exam_code` | string(20) | e.g. `PT06` |
| `source_subject_code` | string(10) | `verbal` or `math` |
| `source_section_code` | string(10) | nullable |
| `source_module_code` | string(10) | e.g. `M1`, `M2` |
| `source_question_number` | int | nullable |
| `stimulus_mode_key` | string(30) | nullable |
| `stem_type_key` | string(40) | nullable |
| `current_question_text` | text | |
| `current_passage_text` | text | nullable |
| `current_paired_passage_text` | text | nullable; required for cross-text questions |
| `current_underlined_text` | text | nullable; required for words-in-context questions |
| `current_correct_option_label` | string(1) | A–D |
| `current_explanation_text` | text | nullable |
| `practice_status` | enum | `draft` / `active` / `retired` |
| `official_overlap_status` | enum | `none` / `possible` / `confirmed` |
| `canonical_official_question_id` | UUID FK → `questions` | nullable |
| `derived_from_question_id` | UUID FK → `questions` | nullable |
| `generation_source_set` | JSONB | nullable |
| `is_admin_edited` | bool | |
| `annotation_stale` | bool | Set when edit invalidates existing annotation |
| `passage_group_id` | UUID | nullable; groups shared-passage questions |
| `metadata_managed_by_llm` | bool | Default `true` |
| `latest_annotation_id` | UUID FK → `question_annotations` | nullable |
| `latest_version_id` | UUID FK → `question_versions` | nullable |
| `created_at`, `updated_at` | timestamptz | |

### 17.3 `question_versions`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `question_id` | UUID FK → `questions` | |
| `version_number` | int | Unique per question |
| `change_source` | enum | `ingest` / `generate` / `admin_edit` / `reprocess` |
| `question_text` | text | |
| `passage_text` | text | nullable |
| `paired_passage_text` | text | nullable |
| `underlined_text` | text | nullable |
| `choices_jsonb` | JSONB | Array of `{label, text, is_correct}` |
| `correct_option_label` | string(1) | |
| `explanation_text` | text | nullable |
| `change_notes` | text | nullable |
| `created_at` | timestamptz | |

### 17.4 `question_annotations`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `question_id` | UUID FK → `questions` | |
| `question_version_id` | UUID FK → `question_versions` | |
| `provider_name` | string(50) | |
| `model_name` | string(100) | |
| `prompt_version` | string(20) | |
| `rules_version` | string(100) | |
| `annotation_jsonb` | JSONB | All taxonomy fields |
| `explanation_jsonb` | JSONB | `explanation_full` |
| `generation_profile_jsonb` | JSONB | nullable; generation constraints |
| `confidence_jsonb` | JSONB | `annotation_confidence`, `needs_human_review` |
| `created_at` | timestamptz | |

### 17.5 `question_options`

One row per option (A–D) per version. Scoped to `question_version_id`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `question_id` | UUID FK | |
| `question_version_id` | UUID FK | |
| `option_label` | string(1) | A–D |
| `option_text` | text | |
| `is_correct` | bool | |
| `option_role` | string(10) | `correct` or `distractor` |
| `distractor_type_key` | string(30) | nullable |
| `semantic_relation_key` | string(40) | nullable |
| `plausibility_source_key` | string(30) | nullable |
| `option_error_focus_key` | string(40) | nullable |
| `why_plausible` | text | nullable |
| `why_wrong` | text | nullable |
| `grammar_fit` | string(3) | nullable (`yes`/`no`) |
| `tone_match` | string(3) | nullable |
| `precision_score` | smallint | nullable |
| `student_failure_mode_key` | string(30) | nullable |
| `distractor_distance` | string(10) | `wide`/`moderate`/`tight` |
| `distractor_competition_score` | float | nullable |

### 17.6 `question_assets`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `question_id` | UUID FK → `questions` | nullable; only first question linked in batch |
| `content_origin` | enum | |
| `asset_type` | enum | `pdf`/`image`/`screenshot`/`markdown`/`json`/`text` |
| `storage_path` | text | Absolute path on local archive |
| `mime_type` | string(100) | nullable |
| `page_start`, `page_end` | int | nullable; PDF page range |
| `source_url`, `source_name` | text / string(200) | nullable |
| `source_exam_code`, `source_subject_code`, `source_section_code`, `source_module_code` | string | nullable |
| `source_question_number` | int | nullable |
| `checksum` | string(64) | SHA-256 of raw file content |

### 17.7 `question_relations`

Unique constraint on `(from_question_id, to_question_id, relation_type)`.
Self-referential relations are blocked at the API layer.

### 17.8 `llm_evaluations`

Stores beta comparison scores (0–10 scale per dimension) with `review_notes` and
`recommended_for_default`.

### 17.9 `users` and `user_progress`

`users`: integer PK, `username` (unique, 1–100 chars), `created_at`

`user_progress`: records each answer submission with `user_id`, `question_id`,
`selected_option_label`, `is_correct` (server-computed), optional
`missed_grammar_focus_key` and `missed_syntactic_trap_key`, `timestamp`

---

## 18. Full API Reference

### Ingestion

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/ingest/official/pdf` | admin | Upload official PDF |
| `POST` | `/ingest/unofficial/file` | admin | Upload one unofficial file |
| `POST` | `/ingest/unofficial/batch` | admin | Upload up to 10 files |
| `POST` | `/ingest/text` | admin | Ingest raw text body |
| `POST` | `/ingest/reannotate/{question_id}` | admin | Re-run Pass 2 annotation |
| `GET` | `/ingest/jobs/{job_id}` | admin | Get job record |

### Generation

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/generate/questions` | admin | Generate one question |
| `POST` | `/generate/questions/compare` | admin | Multi-provider comparison |
| `GET` | `/generate/runs/{run_id}` | admin | Inspect generation job |

### Admin Question Management

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/admin/questions` | admin | List questions (filterable) |
| `PATCH` | `/admin/questions/{id}` | admin | Edit content |
| `POST` | `/admin/questions/{id}/approve` | admin | Approve for practice |
| `POST` | `/admin/questions/{id}/reject` | admin | Retire question |
| `DELETE` | `/admin/questions/{id}` | admin | Hard delete |
| `POST` | `/admin/questions/{id}/confirm-overlap` | admin | Confirm official overlap |
| `POST` | `/admin/questions/{id}/clear-overlap` | admin | Clear false-positive overlap |

### Relations and Evaluations

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/admin/relations` | admin | List relations (paginated) |
| `POST` | `/admin/relations` | admin | Create relation |
| `DELETE` | `/admin/relations/{id}` | admin | Delete relation |
| `POST` | `/admin/evaluations` | admin | Create evaluation record |
| `POST` | `/admin/evaluations/{id}/score` | admin | Record human scores |

### Practice Recall (Admin)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/questions/recall` | admin | Filtered active question list |
| `GET` | `/questions/{id}` | admin | Question detail with annotation |
| `GET` | `/questions/{id}/versions` | admin | Version history |

### Student Practice

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/questions` | student | Recall active questions (no answer key) |
| `POST` | `/api/submit` | student | Submit answer; correctness computed server-side |
| `GET` | `/api/stats/{user_id}` | student | Aggregate accuracy and top missed keys |

### User Management

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/users` | admin | Create user (201) |
| `GET` | `/users` | admin | List users (paginated) |
| `GET` | `/users/{id}` | admin | Get user |
| `DELETE` | `/users/{id}` | admin | Delete user + progress (204) |

### System

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | none | Liveness check |

---

## 19. Authentication

API key authentication via `X-API-Key` header. Two key pools:

| Pool | Env var | Access |
|---|---|---|
| Admin | `ADMIN_API_KEYS` | All endpoints |
| Student | `STUDENT_API_KEYS` | `/api/*` endpoints only |

Both vars accept comma-separated lists. Defaults (`admin-key-change-me`,
`student-key-change-me`) are active if env vars are not set. A startup warning
fires when defaults are detected.

---

## 20. Configuration

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Auth
ADMIN_API_KEYS=your-admin-key
STUDENT_API_KEYS=your-student-key

# LLM defaults
DEFAULT_ANNOTATION_PROVIDER=anthropic        # anthropic | openai | ollama
DEFAULT_ANNOTATION_MODEL=claude-sonnet-4-6
DEFAULT_OLLAMA_MODEL=kimi-k2.6:cloud
RULES_VERSION=rules_agent_dsat_grammar_ingestion_generation_v7

# Provider keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Storage
RAW_ASSET_STORAGE_BACKEND=local
LOCAL_ARCHIVE_MIRROR=./archive

# Official ingest
OFFICIAL_AUTO_ACTIVATE_FOR_TESTING=false

# OCR — both options configured simultaneously; admin selects per-job at ingest time
OCR_STRATEGY=auto                           # server default: auto | deepseek | ollama
OCR_FALLBACK=true
VISION_MAX_IMAGES=10

# OCR Option B — Ollama VLM (local, zero cost)
OCR_VISION_PROVIDER=ollama
OCR_VISION_MODEL=qwen2.5-vl:7b             # or llava-phi3, minicpm-v:8b, llava:7b
OLLAMA_BASE_URL=http://localhost:11434

# OCR Option A — DeepSeek OCR (local via Docker/vLLM or Ollama)
DEEPSEEK_OCR_BASE_URL=http://localhost:8001  # vLLM/Docker endpoint; use 11434 for Ollama
DEEPSEEK_OCR_MODEL=deepseek-ai/DeepSeek-OCR-2  # use VL2-Tiny for general vision tasks

# LLM retry
LLM_RETRY_MAX_ATTEMPTS=3
LLM_RETRY_BASE_DELAY_S=1.0
LLM_RETRY_MAX_DELAY_S=30.0

# Logging
LOG_LEVEL=INFO
LOG_JSON=true
```

---

## 21. Known Open Gaps

| # | Severity | Description |
|---|---|---|
| 1 | High | No admin API path to activate an official question. `approve` blocks `content_origin == "official"`. Workaround: `OFFICIAL_AUTO_ACTIVATE_FOR_TESTING=true` flag. |
| 2 | Medium | Raw ingest text silently truncated at 50,000 chars. Long PDFs can lose later questions without error. |
| 3 | Medium | Batch ingest asset provenance: only the first question per asset is linked in `question_assets.question_id`. |
| 4 | Medium | `table_data` and `graph_data` validated by pipeline but not persisted (no DB columns). Quantitative stimulus data is lost. |
| 5 | Medium | OCR strategies (§8) are designed but not yet implemented. Scanned PDFs and image uploads still fail with "No raw text available". |
| 6 | Low | CORS wildcard (`allow_origins=["*"]`) remains enabled. Acceptable for local dev; restrict before deployment. |
| 7 | Low | Student submit does not verify that the submitted option label exists in the current option set for the question. |

---

## 22. LLM Beta Evaluation

Beta providers:

| Provider | Default model |
|---|---|
| Anthropic (default) | `claude-sonnet-4-6` |
| Ollama (local) | `kimi-k2.6:cloud` |
| OpenAI | configurable |

Beta must answer:

1. Which model produces the best metadata quality?
2. Which model produces the best explanations?
3. Which model produces the best generated questions?
4. Which overlap-detection threshold best protects the official corpus?

---

## 23. Future Work

- Official question activation path (answer-verification workflow)
- DB columns for `table_data` and `graph_data` (quantitative stimulus)
- Batch asset provenance: link all questions from one asset
- Implement OCR strategies from §8 (Ollama VLM and DeepSeek options)
- Embedding-based semantic recall and overlap detection
- Adaptive practice assembly
- Automated answer-key import for official PDFs
- Rules amendment workflow for corpus-driven taxonomy updates
