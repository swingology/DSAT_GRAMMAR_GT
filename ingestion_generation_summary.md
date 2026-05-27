# Ingestion & Generation Pipeline — Step-by-Step Summary

## Ingestion Pipeline (`_run_pipeline` in `backend/app/routers/ingest.py`)

### Step 1 — Parse (PDF → raw text)
`parse_pdf()` in `parsers/pdf_parser.py` runs pymupdf against the uploaded file and extracts embedded text and per-page renders. If the PDF has embedded text, it's used directly (`_ocr_strategy: "bypassed"`). If mixed (some pages blank), only the empty pages go through OCR.

### Step 2 — OCR (image pages only)
A priority chain: `glm` → `deepseek` → `ollama/anthropic/openai` (VLM fused). Each strategy tries to extract raw text from page renders. GLM/DeepSeek are two-step (OCR → raw text, then pass to Pass 1 LLM). VLM-fused providers skip Pass 1 entirely.

### Step 3 — Extract (Pass 1: raw text → question JSON)
`build_extract_prompt()` wraps raw text in the extraction prompt and calls the LLM. Output is parsed with `extract_json_from_text()`, then normalized via `_normalize_extracted_questions()` (splits passage text from question text, deduplicates, resolves shared passages). 3-attempt retry on JSON parse failures.

### Step 4 — Question number validation
`_validate_question_numbers()` checks: non-null ints, within expected range (verbal 1–33, math 1–22), unique, contiguous. `_verify_qnums_against_ocr()` cross-checks LLM-inferred numbers against raw OCR text. Any warning → `defer_activation = True` → whole job goes to `needs_review`, questions land as `draft`.

### Step 5 — Layout detection (enrichment, non-blocking)
`detect_layout()` in `storage/crop_detector.py` runs if `layout_detection_enabled` and images exist. Fails gracefully — never gates progression.

### Step 6 — Annotate (Pass 2: extracted question → annotation JSON)
`build_annotate_prompt_parts()` builds the annotation prompt with targeted sections from the rules doc. LLM classifies focus keys, failure modes, distractor types, etc. Result merged with extraction via `_merge_for_validation()` — extraction owns structural fields (`options`, `question_text`, `passage_text`, `correct_option_label`).

### Step 7 — Overlap check (unofficial/generated only)
Skipped for official questions. Checks semantic overlap against existing official questions.

### Step 8 — Validate
`validate_question()` checks: `question_text` present, exactly 4 options with unique ABCD labels, correct label in {A,B,C,D}, controlled-vocab key conformance. Unknown vocab keys are recorded non-blocking in `vocabulary/candidates.json` via `record_unknown_field()`. `annotation_sanitizer.py` then difflib-corrects near-miss keys or nulls them.

### Step 9 — Persist
`_persist_single_question()` writes `Question`, `QuestionVersion`, `QuestionAnnotation`, `QuestionOption`, `QuestionSourceSpan` with 3 `db.flush()` calls in a savepoint. UUID5-based deterministic IDs for official questions (idempotent re-ingestion).

---

## Generation Pipeline (`_run_generate_pipeline` in `backend/app/routers/generate.py`)

### Step 1 — Load source examples
`_load_official_source_examples()` fetches the official source questions passed via `source_question_ids` — these seed the generation prompt with real distractor patterns.

### Step 2 — Generate (Pass 1: prompt → question JSON)
`build_generate_prompt_parts()` builds a 3-part cached prompt (static rules, dynamic source examples, user request). LLM call with `temperature=0.7`, `max_tokens=8192`. Output normalized via `_normalize_generated_question()`. 3-attempt JSON retry.

### Step 3 — Annotate (Pass 2: generated question → annotation JSON)
Same `build_annotate_prompt_parts()` as ingestion. 3-attempt retry. Result stored in `pass2_json`.

### Step 4 — Validate
`validate_question()` on `{**generated, **annotate_json}`. Blocking errors → `failed_permanent`. Non-blocking → continues.

### Step 5 — Persist
Creates `Question` (with `practice_status="draft"`, `content_origin="generated"`), `QuestionVersion`, `QuestionAnnotation`, `QuestionOption`. Links to source questions via `generation_source_set`.

### Step 6 — Overlap check
`detect_overlaps()` against official question set. Match → `official_overlap_status="possible"`, job → `needs_review`. No match → `approved`.

### Step 7 — Auto-review swarm (background, if not skipped)
`_run_auto_review_swarm()` fires as an async task post-approval.

---

## Key Structural Differences

| | Ingestion | Generation |
|---|---|---|
| Entry point | PDF upload | API request with `source_question_ids` |
| First step | Parse/OCR | Load source examples |
| Pass 1 | Extract questions from raw text | Generate new question from prompt |
| Pass 2 | Annotate extracted question | Annotate generated question (same function) |
| Overlap check | Skipped for official | Always runs |
| Question IDs | UUID5 (deterministic, idempotent) | UUID4 (random) |
| Initial status | `draft` if warnings, else `approved` | Always starts as `draft` |
| Orchestrator start | `parsing` | `extracting` (skips parsing) |

Both pipelines share the same Pass 2 annotation (`build_annotate_prompt_parts`), validator (`validate_question`), and annotation sanitizer (difflib near-match correction on controlled-vocab keys).
