# OCR Flow

## Pipeline Overview

When a PDF or image is submitted for ingestion, the pipeline decides whether OCR is needed based on whether the source has embedded text.

### Embedded-Text Path (OCR Bypassed)

If the PDF contains selectable text (most digital SAT practice tests), OCR is skipped entirely:

```
PDF → PyMuPDF text extraction → raw_text → Pass 1 LLM extraction → Pass 2 annotation → validation → persist
```

The default extraction model (`qwen3-vl:235b-instruct-cloud` via Ollama) is used for the Pass 1 extraction call in this path.

### Scanned-Image Path (OCR Required)

When no embedded text is found and page images are available, the OCR gate activates. The pipeline builds an ordered fallback chain of OCR strategies and tries each one until one succeeds.

## OCR Strategy Chain

`_build_ocr_chain()` determines the ordered sequence. The resolved strategy runs first; remaining available strategies follow, with **two-step strategies preferred over fused VLM strategies** as fallbacks.

### Default Chain (`ocr_strategy=auto`)

| Order | Strategy | Mode | OCR Step | Extraction Step |
|-------|----------|------|----------|-----------------|
| 1 | `glm` | Two-step | `glm-ocr:latest` via Ollama vision → raw text | `qwen3-vl:235b-instruct-cloud` via Ollama |
| 2 | `deepseek` | Two-step | DeepSeek OCR-2 → raw text | `qwen3-vl:235b-instruct-cloud` via Ollama |
| 3 | `anthropic` | Fused | Claude does OCR + JSON extraction in one call | *(skipped — extraction done)* |
| 4 | `openai` | Fused | GPT does OCR + JSON extraction in one call | *(skipped — extraction done)* |
| 5 | `ollama` | Fused | Local `qwen3.0-vl` does OCR + JSON extraction in one call | *(skipped — extraction done)* |

A strategy is only included if its required configuration is present (model available, API key set, base URL configured). Fallback can be disabled by setting `ocr_fallback=false`.

### Strategy Modes

**Two-step** (`glm`, `deepseek`):
1. OCR model extracts raw text from page images
2. Raw text is passed to the extraction LLM (`deepseek-v4-pro:cloud`) which produces structured JSON
3. Structured JSON proceeds to Pass 2 annotation

**Fused** (`ollama`, `anthropic`, `openai`):
1. VLM receives page images and the extraction prompt in a single call
2. The model simultaneously performs OCR and produces structured JSON
3. A sentinel value `_vision_fused_` replaces `raw_text` to skip the separate Pass 1 extraction step

## Two-Step Extraction Model

After any successful two-step OCR (`glm` or `deepseek`), the extracted raw text is sent to `qwen3-vl:235b-instruct-cloud` for structured JSON extraction. This is the same model used for embedded-text extraction, but it only receives the OCR'd raw text rather than the full PDF content.

**Important:** The `qwen3-vl:235b-instruct-cloud` model is now the extraction model for both embedded-text and two-step OCR paths.

## Pass 1: LLM Extraction

Regardless of the OCR path, Pass 1 takes the raw text and produces structured JSON containing:
- `questions[]` — array of question objects with `question_text`, `passage_text`, `options[]`, `correct_option_label`
- `source_exam_code`, `source_subject_code`, `source_section_code`, `source_module_code`
- `paired_passage_text`, `underlined_text` (for cross-text and complete-the-text questions)

The extraction prompt is built by `build_extract_prompt()` (for text) or `build_vision_extract_prompt()` (for fused VLM).

Pass 1 has a 3-attempt retry loop with exponential backoff on JSON parse failures (`ValueError`). On final failure, the job is marked `failed`.

## Pass 2: LLM Annotation

After successful extraction, Pass 2 annotates each question with:
- `grammar_focus_key`, `grammar_focus_name`
- `difficulty_overall`, `difficulty_time`
- `syntactic_trap_keys`, `stimulus_mode_key`
- `explanation_short`, `explanation_full`
- `annotation_confidence`, `needs_human_review`

Pass 2 also has a 3-attempt retry loop with backoff.

## Validation

After annotation, `validate_question()` checks:
- Required fields present (`question_text`, `options`, `correct_option_label`)
- Option labels are exactly `{A, B, C, D}`
- `correct_option_label` exists in the option labels
- `passage_text` present for reading comprehension items

Blocking validation errors → `needs_review` status. All others → `approved` status.

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `ocr_strategy` | `glm` | Primary OCR strategy: `glm`, `deepseek`, `ollama`, `anthropic`, `openai`, `auto` |
| `ocr_fallback` | `true` | Enable fallback to next strategy on failure |
| `ocr_vision_provider` | `ollama` | Provider for VLM fused path |
| `ocr_vision_model` | `qwen3.0-vl` | Model for VLM fused path |
| `glm_ocr_model` | `glm-ocr:latest` | Model for GLM-OCR two-step path |
| `deepseek_ocr_base_url` | *(empty)* | Base URL for DeepSeek OCR server |
| `deepseek_ocr_model` | `deepseek-ai/DeepSeek-OCR-2` | Model for DeepSeek two-step path |
| `vision_max_images` | `10` | Max page images sent to VLM |
| `default_annotation_provider` | `ollama` | Provider for Pass 1 + Pass 2 when OCR is bypassed |
| `default_annotation_model` | `deepseek-v4-pro:cloud` | Model for Pass 1 + Pass 2 when OCR is bypassed and for generation when a request omits `model_name` |

## Job State Machine

```
pending → parsing → extracting → annotating → validating → approved
                                              └→ needs_review
                     └→ failed (at any stage)
```

For `content_origin in ("unofficial", "generated")`, an `overlap_checking` step runs between `annotating` and `validating`.

## Error Handling

- **OCR failures**: Each strategy in the chain is tried in order. If all fail, the job is marked `failed` with the last error.
- **LLM extraction failures**: 3-attempt retry with backoff. On final failure, the job is marked `failed`.
- **JSON parse failures**: 3-attempt retry within the extraction loop.
- **Structural validation**: If JSON parses but produces no valid questions (empty `question_text`), a `ValueError` is raised, triggering the retry loop.
- **Timeouts**: Pipeline-level timeout (default 1800s) via `asyncio.wait_for`. Text LLM calls have 300s timeout; vision calls have 600s.
- **Stuck job recovery**: On server restart, jobs in non-terminal states are marked `failed` with a `startup_recovery` error.
