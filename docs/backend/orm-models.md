# ORM Models Reference

This document describes the 10 SQLAlchemy ORM tables in the DSAT backend.

## Table Summary

| Table | Segment | Purpose | Key Relationships |
|---|---|---|---|
| `question_jobs` | A | Ingestion and generation job orchestration | FK to `question_assets`, `questions` |
| `questions` | A (writes), B (reads) | Canonical question identity and current content | FK to `question_annotations`, `question_versions`, self-referential lineage |
| `question_versions` | A | Immutable content snapshots per edit/generation | FK to `questions` |
| `question_annotations` | A | LLM-managed taxonomy metadata and explanations | FK to `questions`, `question_versions` |
| `question_options` | A | Per-option analysis (4 rows per question) | FK to `questions`, `question_versions` |
| `question_assets` | A | Raw source files and extracted artifacts | FK to `questions` |
| `question_relations` | A | Cross-question linking and overlap detection | Self-referential FK to `questions` |
| `llm_evaluations` | A | Beta model comparison scores | FK to `question_jobs`, `questions` |
| `users` | B | Student accounts | One-to-many with `user_progress` |
| `user_progress` | B | Answer attempts and accuracy tracking | FK to `users`, `questions` |

---

## Segment Ownership Model

- **Segment A (corpus)** owns: `question_jobs`, `questions`, `question_versions`, `question_annotations`, `question_options`, `question_assets`, `question_relations`, `llm_evaluations`
- **Segment B (student)** owns: `users`, `user_progress`
- **Segment B may read (never write)** from `questions`, `question_annotations`, `question_versions`, and `question_options` via `question_id`
- **Shared key:** `question_id` (UUID) links both segments

---

## Table Definitions

### `question_jobs`

Staging and orchestration for ingestion and generation.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `job_type` | ENUM | No | — | `ingest`, `generate`, `reannotate`, `overlap_check` |
| `content_origin` | ENUM | No | — | `official`, `unofficial`, `generated` |
| `input_format` | VARCHAR(20) | No | — | `pdf`, `image`, `screenshot`, `markdown`, `json`, `text` |
| `status` | ENUM | No | `pending` | Job state machine value |
| `provider_name` | VARCHAR(50) | No | — | e.g. `anthropic` |
| `model_name` | VARCHAR(100) | No | — | e.g. `claude-sonnet-4-6` |
| `prompt_version` | VARCHAR(20) | No | `v3.0` | — |
| `rules_version` | VARCHAR(100) | No | — | e.g. `rules_agent_dsat_grammar_ingestion_generation_v3` |
| `raw_asset_id` | UUID | Yes | — | FK to `question_assets.id` |
| `pass1_json` | JSONB | Yes | — | Pass 1 extraction output |
| `pass2_json` | JSONB | Yes | — | Pass 2 annotation output |
| `validation_errors_jsonb` | JSONB | Yes | — | Structured error details on failure |
| `comparison_group_id` | UUID | Yes | — | Groups jobs for multi-model comparison |
| `question_id` | UUID | Yes | — | FK to `questions.id` (nullable until job produces a question) |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |
| `updated_at` | TIMESTAMPTZ | No | `utcnow` | Auto-updated on change |

**Relationships:**
- `question` -> `Question` (many-to-one, via `question_id`)

---

### `questions`

Canonical question identity and current user-facing content.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `content_origin` | ENUM | No | — | `official`, `unofficial`, `generated` |
| `source_exam_code` | VARCHAR(20) | Yes | — | Required for official content (e.g. `PT4`) |
| `source_module_code` | VARCHAR(10) | Yes | — | Required for official content (e.g. `M1`) |
| `source_question_number` | INTEGER | Yes | — | Required for official content |
| `stimulus_mode_key` | VARCHAR(30) | Yes | — | V3 controlled value |
| `stem_type_key` | VARCHAR(40) | Yes | — | V3 controlled value |
| `current_question_text` | TEXT | No | — | Prompt / stem text |
| `current_passage_text` | TEXT | Yes | — | Passage text (nullable) |
| `current_correct_option_label` | VARCHAR(1) | No | — | `A`, `B`, `C`, or `D` |
| `current_explanation_text` | TEXT | Yes | — | Composed from annotation |
| `practice_status` | ENUM | No | `draft` | `draft`, `active`, `retired` |
| `official_overlap_status` | ENUM | No | `none` | `none`, `possible`, `confirmed` |
| `canonical_official_question_id` | UUID | Yes | — | Self-referential FK to `questions.id` |
| `derived_from_question_id` | UUID | Yes | — | Self-referential FK to `questions.id` |
| `generation_source_set` | JSONB | Yes | — | Array of `{question_id, focus_key, role}` objects |
| `is_admin_edited` | BOOLEAN | No | `false` | — |
| `metadata_managed_by_llm` | BOOLEAN | No | `true` | — |
| `latest_annotation_id` | UUID | Yes | — | FK to `question_annotations.id` |
| `latest_version_id` | UUID | Yes | — | FK to `question_versions.id` |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |
| `updated_at` | TIMESTAMPTZ | No | `utcnow` | Auto-updated on change |

**Relationships:**
- `jobs` -> `QuestionJob` (one-to-many)
- `versions` -> `QuestionVersion` (one-to-many, ordered by `version_number`)
- `annotations` -> `QuestionAnnotation` (one-to-many)
- `options` -> `QuestionOption` (one-to-many, ordered by `option_label`)
- `assets` -> `QuestionAsset` (one-to-many)
- `outgoing_relations` -> `QuestionRelation` (one-to-many, via `from_question_id`)
- `incoming_relations` -> `QuestionRelation` (one-to-many, via `to_question_id`)
- `progress_records` -> `UserProgress` (one-to-many)

---

### `question_versions`

Immutable snapshots of question content after ingest, generation, or admin edit.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `question_id` | UUID | No | — | FK to `questions.id` |
| `version_number` | INTEGER | No | — | Auto-incremented per question |
| `change_source` | ENUM | No | — | `ingest`, `generate`, `admin_edit`, `reprocess` |
| `question_text` | TEXT | No | — | — |
| `passage_text` | TEXT | Yes | — | — |
| `choices_jsonb` | JSONB | No | — | Array of `{label, text}` objects |
| `correct_option_label` | VARCHAR(1) | No | — | — |
| `explanation_text` | TEXT | Yes | — | — |
| `editor_user_id` | VARCHAR(50) | Yes | — | Nullable admin identifier |
| `change_notes` | TEXT | Yes | — | — |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:**
- `question` -> `Question` (many-to-one)

---

### `question_annotations`

LLM-managed metadata and explanation artifacts tied to a specific question version.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `question_id` | UUID | No | — | FK to `questions.id` |
| `question_version_id` | UUID | No | — | FK to `question_versions.id` |
| `provider_name` | VARCHAR(50) | No | — | e.g. `anthropic` |
| `model_name` | VARCHAR(100) | No | — | e.g. `claude-sonnet-4-6` |
| `prompt_version` | VARCHAR(20) | No | — | e.g. `v3.0` |
| `rules_version` | VARCHAR(100) | No | — | V3 rules version string |
| `annotation_jsonb` | JSONB | No | `{}` | Classification, reasoning, V3 extensions |
| `explanation_jsonb` | JSONB | No | `{}` | `explanation_short`, `explanation_full`, `evidence_span_text` |
| `generation_profile_jsonb` | JSONB | Yes | — | V3 generation profile block |
| `confidence_jsonb` | JSONB | No | `{}` | `annotation_confidence`, `needs_human_review`, `review_notes` |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:**
- `question` -> `Question` (many-to-one)

---

### `question_options`

Per-option analysis fields from V3 rules. One row per option (4 rows per question).

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `question_id` | UUID | No | — | FK to `questions.id` |
| `question_version_id` | UUID | No | — | FK to `question_versions.id` |
| `option_label` | VARCHAR(1) | No | — | `A`, `B`, `C`, `D` |
| `option_text` | TEXT | No | — | — |
| `is_correct` | BOOLEAN | No | — | — |
| `option_role` | VARCHAR(10) | No | — | `correct` or `distractor` |
| `distractor_type_key` | VARCHAR(30) | Yes | — | V3 controlled value |
| `semantic_relation_key` | VARCHAR(40) | Yes | — | V3 controlled value |
| `plausibility_source_key` | VARCHAR(30) | Yes | — | V3 controlled value |
| `option_error_focus_key` | VARCHAR(40) | Yes | — | V3 grammar focus key |
| `why_plausible` | TEXT | Yes | — | — |
| `why_wrong` | TEXT | Yes | — | Nullable for correct option |
| `grammar_fit` | VARCHAR(3) | Yes | — | `yes` or `no` |
| `tone_match` | VARCHAR(3) | Yes | — | `yes` or `no` |
| `precision_score` | SMALLINT | Yes | — | `1`, `2`, or `3` |
| `student_failure_mode_key` | VARCHAR(30) | Yes | — | V3 controlled value (nullable for correct) |
| `distractor_distance` | VARCHAR(10) | Yes | — | `wide`, `moderate`, `tight` |
| `distractor_competition_score` | FLOAT | Yes | — | V3 metric (nullable for correct) |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:**
- `question` -> `Question` (many-to-one)

---

### `question_assets`

Raw source files and extracted artifacts.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `question_id` | UUID | Yes | — | FK to `questions.id` (nullable until linked) |
| `content_origin` | ENUM | No | — | `official`, `unofficial` |
| `asset_type` | ENUM | No | — | `pdf`, `image`, `screenshot`, `markdown`, `json`, `text` |
| `storage_path` | TEXT | No | — | Local path or bucket URL |
| `mime_type` | VARCHAR(100) | Yes | — | — |
| `page_start` | INTEGER | Yes | — | — |
| `page_end` | INTEGER | Yes | — | — |
| `source_url` | TEXT | Yes | — | — |
| `source_name` | VARCHAR(200) | Yes | — | — |
| `source_exam_code` | VARCHAR(20) | Yes | — | — |
| `source_module_code` | VARCHAR(10) | Yes | — | — |
| `source_question_number` | INTEGER | Yes | — | — |
| `checksum` | VARCHAR(64) | Yes | — | SHA-256 for deduplication |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:**
- `question` -> `Question` (many-to-one)

---

### `question_relations`

Cross-question linking (overlap, lineage, derived-from).

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `from_question_id` | UUID | No | — | FK to `questions.id` |
| `to_question_id` | UUID | No | — | FK to `questions.id` |
| `relation_type` | ENUM | No | — | `overlaps_official`, `derived_from`, `near_duplicate`, `generated_from`, `adapted_from` |
| `relation_strength` | FLOAT | Yes | — | Similarity score |
| `detection_method` | VARCHAR(30) | Yes | — | `lexical`, `structural`, `embedding` |
| `is_human_confirmed` | BOOLEAN | No | `false` | — |
| `notes` | TEXT | Yes | — | — |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:**
- `from_question` -> `Question` (many-to-one, via `from_question_id`)
- `to_question` -> `Question` (many-to-one, via `to_question_id`)

---

### `llm_evaluations`

Beta model comparison scores.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | UUID | No | `uuid4()` | Primary key |
| `job_id` | UUID | No | — | FK to `question_jobs.id` |
| `question_id` | UUID | Yes | — | FK to `questions.id` |
| `provider_name` | VARCHAR(50) | No | — | — |
| `model_name` | VARCHAR(100) | No | — | — |
| `task_type` | VARCHAR(20) | No | — | `extraction`, `annotation`, `generation` |
| `score_overall` | FLOAT | Yes | — | — |
| `score_metadata` | FLOAT | Yes | — | — |
| `score_explanation` | FLOAT | Yes | — | — |
| `score_generation` | FLOAT | Yes | — | — |
| `review_notes` | TEXT | Yes | — | — |
| `recommended_for_default` | BOOLEAN | Yes | — | — |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:** None defined on the model.

---

### `users`

Student accounts. Owned by Segment B.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | INTEGER | No | — | Primary key, auto-increment |
| `username` | VARCHAR(100) | No | — | Unique, indexed |
| `created_at` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:**
- `progress_records` -> `UserProgress` (one-to-many)

---

### `user_progress`

Answer attempts and accuracy tracking. Owned by Segment B.

| Column | Type | Nullable | Default | Constraints / Notes |
|---|---|---|---|---|
| `id` | INTEGER | No | — | Primary key, auto-increment |
| `user_id` | INTEGER | No | — | FK to `users.id` |
| `question_id` | UUID | No | — | FK to `questions.id` |
| `is_correct` | BOOLEAN | No | — | — |
| `selected_option_label` | VARCHAR(1) | No | — | `A`, `B`, `C`, or `D` |
| `missed_grammar_focus_key` | VARCHAR(50) | Yes | — | V3 grammar focus key |
| `missed_syntactic_trap_key` | VARCHAR(50) | Yes | — | V3 syntactic trap key |
| `timestamp` | TIMESTAMPTZ | No | `utcnow` | — |

**Relationships:**
- `user` -> `User` (many-to-one)
- `question` -> `Question` (many-to-one)
