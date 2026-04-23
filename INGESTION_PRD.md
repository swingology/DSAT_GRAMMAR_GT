# INGESTION.PRD - DSAT Question Corpus Ingestion, Annotation, and Generation Beta

## 1. Purpose

This document specifies the product requirements for the DSAT question backend before student progress tracking. The system must support three linked workflows:

- ingesting official DSAT questions from PDF files
- ingesting unofficial questions from flexible source formats
- generating new DSAT-style questions using official questions plus `rules_agent_dsat_grammar_ingestion_generation_v3.md` as the primary guidance set

The resulting corpus must allow recall of official, unofficial, and generated questions as practice material. Every stored question must have LLM-managed metadata, explanations, and taxonomy fields derived from `rules_agent_dsat_grammar_ingestion_generation_v3.md`.

## 2. Product Goals

1. Build a high-trust official corpus from released DSAT PDF material.
2. Build a flexible unofficial corpus from screenshots, images, Markdown files, PDFs, JSON, and plain text captured from various sources.
3. Build a robust generated-question workflow that uses the official corpus as the gold reference set.
4. Compare multiple LLMs during beta to determine which combination produces the best metadata, explanations, and generated questions.
5. Store all assets, annotations, lineage, and edits in a backend architecture that is sufficient before student progress tracking begins.
6. Allow a human admin to edit question content and answers while keeping metadata generation under LLM control.

## 3. Scope

### 3.1 In-Scope Inputs

- Official PDF exams and official PDF extracts
- Unofficial PDFs
- Markdown files
- Raster images and screenshots (`png`, `jpg`, `jpeg`, `webp`)
- Pre-extracted JSON
- Plain text
- Generated-question requests

### 3.2 Out-of-Scope Inputs

- Video
- Audio
- Handwritten scans that cannot be OCRed
- Public student-facing delivery features
- Student progress tracking

### 3.3 In-Scope Outputs

- staged ingestion and generation jobs
- canonical question records
- private raw asset storage
- official archive records
- LLM metadata and explanation snapshots
- overlap and lineage links across official, unofficial, and generated questions
- evaluation records comparing LLM output quality

## 4. Core Corpus Model

The system no longer uses a binary `official` versus `unofficial` model as the top-level concept. It uses a three-value `content_origin` field:

| `content_origin` | Meaning | Primary Intake |
|---|---|---|
| `official` | Released College Board DSAT questions used as the canonical reference corpus | PDF only |
| `unofficial` | Third-party, adapted, captured, user-provided, or web-sourced questions | PDF, image, screenshot, Markdown, JSON, text |
| `generated` | Questions produced by the generation pipeline | generation request only |

Every question must also carry overlap and lineage metadata:

| Field | Values | Purpose |
|---|---|---|
| `official_overlap_status` | `none`, `possible`, `confirmed` | Tracks whether a non-official question appears to overlap an official item |
| `canonical_official_question_id` | nullable UUID | Points to the matching official question when overlap is confirmed |
| `derived_from_question_id` | nullable UUID | Points to a parent question used in generation or adaptation workflows |
| `generation_source_set` | JSON array | Stores the official and unofficial examples used to generate a new question |

## 5. Corpus Principles

### 5.1 Official Questions Are the Gold Reference Set

Official questions are the highest-trust examples in the system. They serve three roles:

- canonical practice questions
- reference examples for metadata and explanation quality
- grounding examples for future generated questions

The initial official seed set includes released tests `PT01` and `PT04` through `PT11`, as they become available in PDF form.

### 5.2 Unofficial Questions Are Flexible but Must Be Structured

Unofficial questions may come from many sources and in many formats. They are useful for:

- additional practice inventory
- retrieval for generation seeding
- taxonomy coverage expansion
- overlap detection against official material

### 5.3 Generated Questions Must Be Traceable

Generated questions are never standalone artifacts. Each generated item must record:

- which LLM produced it
- which rule-set version was used
- which source questions were used as examples
- whether it is too close to any official question
- whether it passed admin review

## 6. Shared LLM Standard

All three corpus origins use `rules_agent_dsat_grammar_ingestion_generation_v3.md` as the authoritative rule set for metadata and explanation production.

For every stored question, the LLM must produce:

- taxonomy metadata
- distractor analysis
- explanation text
- generation-oriented metadata
- provenance metadata

Metadata is fully LLM-managed. Human admins may review it, flag it, or trigger regeneration, but the system does not treat admin-edited metadata as the primary workflow in beta.

## 7. Ingestion and Generation Pipelines

### 7.1 Official Question Ingestion

Official questions are ingested from PDF only.

Requirements:

- Input format for `official` items is `pdf` only.
- Each uploaded PDF may contain many questions.
- The parser must split the PDF into per-question records.
- Each extracted official question becomes its own staged job.
- Each official question must retain links to its source PDF and source page range.
- Official questions must be archived in private storage and represented in the database as canonical records.
- Official questions must be available for practice recall after approval.

Minimum required source metadata for official ingestion:

- `source_exam_code`
- `source_module_code`
- `source_question_number`
- `source_pdf_path`
- `source_page_start`
- `source_page_end`

Official items may not be approved until the correct answer has been verified by a human admin or by an approved answer-key workflow.

### 7.2 Unofficial Flexible Ingestion

Unofficial ingestion must be as flexible as possible.

Accepted formats:

- PDF
- image
- screenshot
- Markdown
- JSON
- plain text

Requirements:

- The system must preserve the original raw asset whenever possible.
- OCR is required for image and screenshot inputs.
- Markdown front matter may provide optional source hints.
- PDF uploads may contain one or many questions.
- A single unofficial upload may produce multiple staged questions.
- Each unofficial question must be annotated with the same rule set used for official questions.
- Each unofficial question must be recallable for practice unless explicitly retired.

Optional source metadata for unofficial ingestion:

- `source_name`
- `source_url`
- `capture_date`
- `source_author`
- `source_license_notes`

### 7.3 Generated Question Workflow

Generated questions are first-class records in the corpus.

Generation requirements:

- Generated questions must use approved examples from the official corpus as the primary reference set.
- Generated questions may also use selected unofficial items as supplemental style or trap examples.
- Generated questions must use `rules_agent_dsat_grammar_ingestion_generation_v3.md` during generation and annotation.
- Generated questions must be stored with full lineage, including prompt version, model, sampled source examples, and review outcome.
- Generated questions must be recallable as practice questions after approval.
- Generated questions must be checked for overlap against the official corpus before approval.

## 8. Parsing and Extraction by Input Type

### 8.1 PDF

- Use `pdfplumber` for text extraction.
- Use OCR fallback for scanned PDFs.
- Support multiple questions per PDF.
- Preserve page-level segmentation so each question can reference its source pages.

### 8.2 Images and Screenshots

- Use OCR for text extraction.
- Preserve the original image asset.
- Store image dimensions and format metadata.
- If charts, tables, or complex layouts are present, capture `table_data` and `graph_data` when detectable.

### 8.3 Markdown

- Parse front matter when present.
- Treat the remaining body as raw question text.
- Preserve the original Markdown file in raw asset storage.

### 8.4 JSON and Plain Text

- Accept direct structured or semi-structured ingestion.
- Validate that required question fields can be extracted.
- Preserve the raw payload.

## 9. Annotation Pipeline

Every ingested or generated question runs through a two-pass LLM pipeline.

### Pass 1 - Extraction

Goal:

- extract the raw question content
- identify options and answer key
- capture source metadata
- capture `table_data` and `graph_data` when present

The output shape must align with the backend `QuestionExtract` contract, extended to support table and graph fields when needed.

### Pass 2 - Annotation

Goal:

- classify the question using the full DSAT taxonomy
- generate explanations
- analyze distractors
- produce generation-oriented metadata
- produce provenance and overlap cues

The output shape must align with the backend `QuestionAnnotation` contract, extended as needed for overlap and generation beta fields.

### Pass 3 - Optional Comparison Pass

For beta evaluation, the system may run more than one LLM against the same item and store multiple competing annotations or generated outputs for comparison.

This pass is optional per job but required for model benchmarking.

## 10. LLM Beta Evaluation

Beta must support comparing multiple LLMs for three tasks:

- ingestion extraction quality
- annotation and explanation quality
- generated-question quality

Initial beta providers:

- Anthropic Claude Sonnet 4.6 as the default primary candidate
- Ollama `kimi-k2.6`
- OpenAI ChatGPT 5.4

The system must allow per-job or per-batch selection of:

- LLM provider
- model name
- prompt version
- rule-set version

For beta, every evaluation record should store:

- `provider_name`
- `model_name`
- `task_type`
- `prompt_version`
- `rules_version`
- latency
- token usage if available
- admin score
- pass or fail outcome
- notes on metadata quality
- notes on explanation quality
- notes on generated-question quality

## 11. Overlap Detection and Corpus Linking

Unofficial and generated questions must be compared against official questions.

Requirements:

- The system must detect potential overlap with the official corpus.
- Overlap may be lexical, structural, or near-clone similarity.
- Overlap results must be stored in the database.
- Human admins must be able to confirm or reject a possible overlap.
- Confirmed overlaps must link the question to the canonical official question record.

Rules by origin:

- `official`: overlap detection is not needed against other official questions except for duplicate detection.
- `unofficial`: overlap with official questions must be marked if found.
- `generated`: overlap with official questions must block approval when the item is too close.

## 12. Practice Recall

All approved questions, regardless of origin, must be recallable as practice questions.

Recall must support filtering by:

- `content_origin`
- grammar role and focus
- syntactic trap
- difficulty
- question family
- stimulus mode
- source exam
- overlap status
- provider and model used for annotation
- provider and model used for generation

Practice recall must be able to exclude:

- retired questions
- duplicate questions
- generated questions that failed clone or overlap review

## 13. Storage Architecture

The storage solution for beta must be robust enough for backend development before student progress tracking.

The system uses three layers:

### 13.1 Postgres

Postgres is the system of record for:

- canonical questions
- versions
- annotations
- lineage
- overlaps
- admin reviews
- job state
- model evaluation records

### 13.2 Private Object Storage

Private object storage is required for:

- original PDFs
- screenshots and images
- Markdown files
- raw JSON payloads
- archived official source assets

The storage must not expose official material publicly.

### 13.3 Local Dev Archive

Local filesystem archives are allowed for local development and recovery, but private object storage is the primary backend storage requirement for beta.

Recommended defaults:

- private object storage bucket for raw assets
- private object storage bucket for official archives
- local mirror directory for development and disaster recovery

## 14. Data Model

### 14.1 `question_jobs`

Staging and orchestration for ingestion and generation.

Required fields:

- `id`
- `job_type` (`ingest`, `generate`, `reannotate`, `overlap_check`)
- `content_origin`
- `input_format`
- `status`
- `provider_name`
- `model_name`
- `prompt_version`
- `rules_version`
- `raw_asset_id`
- `pass1_json`
- `pass2_json`
- `validation_errors_json`
- `comparison_group_id`
- `created_at`
- `updated_at`

### 14.2 `questions`

Canonical question identity and current user-facing content.

Required fields:

- `id`
- `content_origin`
- `current_question_text`
- `current_passage_text`
- `current_choices_jsonb`
- `current_correct_option_label`
- `current_explanation_text`
- `practice_status` (`active`, `retired`, `draft`)
- `official_overlap_status`
- `canonical_official_question_id`
- `derived_from_question_id`
- `is_admin_edited`
- `metadata_managed_by_llm` default `true`
- `latest_annotation_id`
- `created_at`
- `updated_at`

### 14.3 `question_versions`

Immutable snapshots of question content after ingest, generation, or admin edit.

Required fields:

- `id`
- `question_id`
- `version_number`
- `change_source` (`ingest`, `generate`, `admin_edit`, `reprocess`)
- `question_text`
- `passage_text`
- `choices_jsonb`
- `correct_option_label`
- `explanation_text`
- `editor_user_id` nullable
- `change_notes`
- `created_at`

### 14.4 `question_annotations`

LLM-managed metadata and explanation artifacts tied to a specific question version.

Required fields:

- `id`
- `question_id`
- `question_version_id`
- `provider_name`
- `model_name`
- `prompt_version`
- `rules_version`
- `annotation_jsonb`
- `explanation_jsonb`
- `generation_profile_jsonb`
- `confidence_jsonb`
- `needs_human_review`
- `created_at`

### 14.5 `question_assets`

Raw source files and extracted artifacts.

Required fields:

- `id`
- `question_id` nullable until linkage
- `content_origin`
- `asset_type` (`pdf`, `image`, `screenshot`, `markdown`, `json`, `text`)
- `storage_path`
- `mime_type`
- `page_start`
- `page_end`
- `source_url`
- `source_name`
- `source_exam_code`
- `source_module_code`
- `source_question_number`
- `checksum`
- `created_at`

### 14.6 `question_relations`

Cross-question linking.

Required fields:

- `id`
- `from_question_id`
- `to_question_id`
- `relation_type` (`overlaps_official`, `derived_from`, `near_duplicate`, `generated_from`, `adapted_from`)
- `relation_strength`
- `detection_method`
- `is_human_confirmed`
- `notes`
- `created_at`

### 14.7 `llm_evaluations`

Stores beta comparison results.

Required fields:

- `id`
- `job_id`
- `question_id` nullable
- `provider_name`
- `model_name`
- `task_type`
- `score_overall`
- `score_metadata`
- `score_explanation`
- `score_generation`
- `review_notes`
- `recommended_for_default`
- `created_at`

## 15. Validation Rules

The validator must enforce:

- required question structure
- four answer choices when the question type requires it
- valid correct answer label
- valid taxonomy values from `rules_agent_dsat_grammar_ingestion_generation_v3.md`
- explanation presence
- provenance presence
- source metadata presence for official questions
- generation lineage presence for generated questions
- overlap-review status for generated questions before approval

Validation severity:

- `blocking` errors prevent approval
- `review` errors require admin review
- `warning` errors are stored but do not block approval

Blocking rules:

- official question missing source exam, module, or question number
- official question not answer-verified
- generated question missing lineage
- generated question with confirmed or unresolved high-risk overlap against official corpus

## 16. Admin Editing Workflow

Human admins must be able to edit:

- question text
- passage text
- answer choices
- correct answer
- explanation text

When a human admin edits question content or answers:

- a new `question_versions` record must be created
- the prior version must remain preserved
- a new LLM annotation job must be queued automatically
- the new LLM annotation becomes the latest metadata snapshot after review

Metadata remains LLM-managed. Admins may flag metadata as poor quality, but the primary correction path is reprocessing with the same or another model.

## 17. API Requirements

### 17.1 Ingestion

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest/official/pdf` | Upload official PDF material only |
| `POST` | `/ingest/unofficial/file` | Upload PDF, image, screenshot, Markdown, JSON, or text |
| `POST` | `/ingest/unofficial/batch` | Batch ingest mixed unofficial assets |
| `POST` | `/ingest/reannotate/{question_id}` | Re-run metadata and explanation generation |

### 17.2 Generation

| Method | Path | Description |
|---|---|---|
| `POST` | `/generate/questions` | Generate one or more questions from selected source examples |
| `POST` | `/generate/questions/compare` | Generate with multiple LLMs for side-by-side beta evaluation |
| `GET` | `/generate/runs/{run_id}` | Inspect generation lineage and review state |

### 17.3 Recall

| Method | Path | Description |
|---|---|---|
| `GET` | `/questions/recall` | Recall practice questions across all origins |
| `GET` | `/questions/{question_id}` | Read question, latest annotation, lineage, and overlap state |
| `GET` | `/questions/{question_id}/versions` | Read edit history |

### 17.4 Admin

| Method | Path | Description |
|---|---|---|
| `PATCH` | `/admin/questions/{question_id}` | Edit question content, answers, or explanation |
| `POST` | `/admin/questions/{question_id}/approve` | Approve a question for practice recall |
| `POST` | `/admin/questions/{question_id}/reject` | Reject or retire a question |
| `POST` | `/admin/questions/{question_id}/confirm-overlap` | Confirm overlap with official corpus |
| `POST` | `/admin/questions/{question_id}/clear-overlap` | Reject a false positive overlap |
| `POST` | `/admin/evaluations/{evaluation_id}/score` | Store human evaluation scores for beta model comparison |

## 18. Job Lifecycle

### 18.1 Official Ingest

`uploaded -> parsed -> split -> extracted -> annotated -> answer_verified -> reviewed -> approved -> archived`

### 18.2 Unofficial Ingest

`uploaded -> parsed_or_ocrd -> extracted -> annotated -> overlap_checked -> reviewed -> approved`

### 18.3 Generated Question

`requested -> examples_selected -> generated -> annotated -> overlap_checked -> reviewed -> approved`

## 19. Security and Compliance

- Official source files and official question content must remain in private storage.
- Raw unofficial captures should also default to private storage.
- Official archive access must be admin-only.
- Provider API keys must never be logged.
- Uploaded files must be MIME-checked and size-limited.
- Model outputs used for beta comparison must be auditable by job and provider.

## 20. Configuration

Add to `.env`:

```bash
# Storage
RAW_ASSET_STORAGE_BACKEND=object_storage
RAW_ASSET_BUCKET=question-raw-assets
OFFICIAL_ARCHIVE_BUCKET=official-question-archive
LOCAL_ARCHIVE_MIRROR=./archive

# Official ingest
OFFICIAL_INGEST_ENABLED=true
OFFICIAL_INPUT_FORMATS=pdf
OFFICIAL_REQUIRE_ANSWER_VERIFICATION=true

# Flexible unofficial ingest
UNOFFICIAL_INPUT_FORMATS=pdf,image,screenshot,markdown,json,text
OCR_ENABLED=true

# LLM beta defaults
DEFAULT_ANNOTATION_PROVIDER=anthropic
DEFAULT_ANNOTATION_MODEL=claude-sonnet-4-6
BETA_COMPARE_MODELS=anthropic:claude-sonnet-4-6,ollama:kimi-k2.6,openai:chatgpt-5.4
RULES_VERSION=rules_agent_dsat_grammar_ingestion_generation_v3

# Overlap detection
OVERLAP_CHECK_ENABLED=true
OVERLAP_HIGH_RISK_THRESHOLD=0.85
OVERLAP_REVIEW_THRESHOLD=0.70
```

## 21. Success Metrics

| Metric | Target |
|---|---|
| official extraction accuracy | >= 95% on answer-key-verified sample |
| unofficial ingestion success rate | >= 90% across supported formats |
| metadata completeness for all approved questions | 100% |
| overlap detection recall on known unofficial-official matches | >= 90% |
| generated-question approval rate after admin review | tracked during beta, target improving weekly |
| average admin time to correct question content | < 5 minutes per item |
| beta model comparison coverage | all three initial providers tested on the same evaluation set |

## 22. Beta Decisions to Resolve

The beta program must answer:

1. Which model produces the best metadata quality?
2. Which model produces the best explanations?
3. Which model produces the best generated questions?
4. Which prompt and metadata combination yields the best admin approval rate?
5. Which overlap-detection threshold best protects the official corpus without overblocking?

## 23. Future Work

- embedding-based semantic recall
- automated answer-key import for official PDFs
- richer overlap scoring using embeddings plus structural fingerprints
- student progress tracking
- student-facing delivery APIs
- adaptive practice assembly
- **FUTURE PLANS**: When the full corpus of official tests is in, conduct a human-administered run with LLM support to analyze changes to the rules. The `rules_agent_dsat_grammar_ingestion_generation_v3.md` should have an amendment process where a human admin can add new rules according to changes proposed by analyzing the unofficial corpus (if it is better to run this through an LLM programming chain, leave that process alone).
- **FUTURE PLANS**: Incorporate DeepSeek OCR (1 or 2) as the method of OCR to effectively handle charts and graphs for readings and various layouts that are not intuitive.

---

**Version:** 1.1
**Date:** 2026-04-23
**Status:** Draft
