# Database Models

10 SQLAlchemy ORM tables. All primary keys are UUID except `users` and `user_progress`.

---

## Table Overview

| Table | Segment | Purpose |
|---|---|---|
| `question_jobs` | A | Ingestion/generation job orchestration |
| `questions` | A | Canonical question identity and current content |
| `question_versions` | A | Immutable content snapshots |
| `question_annotations` | A | LLM-managed taxonomy metadata |
| `question_options` | A | Per-option analysis (4 rows per question) |
| `question_assets` | A | Raw source files and extracted artifacts |
| `question_relations` | A | Cross-question linking and overlap detection |
| `llm_evaluations` | A | Beta model comparison scores |
| `users` | B | Student accounts |
| `user_progress` | B | Answer attempts and accuracy tracking |

---

## `question_jobs`

Staging and orchestration for ingestion and generation.

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | No | `uuid4()` |
| `job_type` | ENUM | No | — |
| `content_origin` | ENUM | No | — |
| `input_format` | VARCHAR(20) | No | — |
| `status` | ENUM | No | `pending` |
| `provider_name` | VARCHAR(50) | No | — |
| `model_name` | VARCHAR(100) | No | — |
| `prompt_version` | VARCHAR(20) | No | `v3.0` |
| `rules_version` | VARCHAR(100) | No | — |
| `raw_asset_id` | UUID | Yes | FK → `question_assets.id` |
| `pass1_json` | JSONB | Yes | Pass 1 extraction output |
| `pass2_json` | JSONB | Yes | Pass 2 annotation output |
| `validation_errors_jsonb` | JSONB | Yes | Structured error details |
| `comparison_group_id` | UUID | Yes | Multi-model comparison grouping |
| `question_id` | UUID | Yes | FK → `questions.id` |
| `created_at` | TIMESTAMPTZ | No | `utcnow` |
| `updated_at` | TIMESTAMPTZ | No | `utcnow` |

---

## `questions`

Canonical question identity and current user-facing content.

| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | No | `uuid4()` |
| `content_origin` | ENUM | No | — |
| `source_exam_code` | VARCHAR(20) | Yes | — |
| `source_module_code` | VARCHAR(10) | Yes | — |
| `source_question_number` | INTEGER | Yes | — |
| `stimulus_mode_key` | VARCHAR(30) | Yes | V3 controlled |
| `stem_type_key` | VARCHAR(40) | Yes | V3 controlled |
| `current_question_text` | TEXT | No | — |
| `current_passage_text` | TEXT | Yes | — |
| `current_correct_option_label` | VARCHAR(1) | No | `A`/`B`/`C`/`D` |
| `current_explanation_text` | TEXT | Yes | — |
| `practice_status` | ENUM | No | `draft` |
| `official_overlap_status` | ENUM | No | `none` |
| `canonical_official_question_id` | UUID | Yes | Self-referential |
| `derived_from_question_id` | UUID | Yes | Self-referential |
| `generation_source_set` | JSONB | Yes | Array of `{question_id, focus_key, role}` |
| `is_admin_edited` | BOOLEAN | No | `false` |
| `metadata_managed_by_llm` | BOOLEAN | No | `true` |
| `latest_annotation_id` | UUID | Yes | FK → `question_annotations.id` |
| `latest_version_id` | UUID | Yes | FK → `question_versions.id` |
| `created_at` | TIMESTAMPTZ | No | `utcnow` |
| `updated_at` | TIMESTAMPTZ | No | `utcnow` |

**Relationships:**
- `jobs` → `QuestionJob` (one-to-many)
- `versions` → `QuestionVersion` (one-to-many, ordered by `version_number`)
- `annotations` → `QuestionAnnotation` (one-to-many)
- `options` → `QuestionOption` (one-to-many, ordered by `option_label`)
- `assets` → `QuestionAsset` (one-to-many)
- `outgoing_relations` / `incoming_relations` → `QuestionRelation`
- `progress_records` → `UserProgress` (one-to-many)

---

## `question_versions`

Immutable snapshots after ingest, generation, or admin edit.

| Column | Type | Nullable |
|---|---|---|
| `id` | UUID | No |
| `question_id` | UUID | No |
| `version_number` | INTEGER | No |
| `change_source` | ENUM | No |
| `question_text` | TEXT | No |
| `passage_text` | TEXT | Yes |
| `choices_jsonb` | JSONB | No |
| `correct_option_label` | VARCHAR(1) | No |
| `explanation_text` | TEXT | Yes |
| `editor_user_id` | VARCHAR(50) | Yes |
| `change_notes` | TEXT | Yes |
| `created_at` | TIMESTAMPTZ | No |

---

## `question_annotations`

LLM-managed metadata tied to a specific question version.

| Column | Type | Nullable |
|---|---|---|
| `id` | UUID | No |
| `question_id` | UUID | No |
| `question_version_id` | UUID | No |
| `provider_name` | VARCHAR(50) | No |
| `model_name` | VARCHAR(100) | No |
| `prompt_version` | VARCHAR(20) | No |
| `rules_version` | VARCHAR(100) | No |
| `annotation_jsonb` | JSONB | No (`{}`) |
| `explanation_jsonb` | JSONB | No (`{}`) |
| `generation_profile_jsonb` | JSONB | Yes |
| `confidence_jsonb` | JSONB | No (`{}`) |
| `created_at` | TIMESTAMPTZ | No |

**JSONB contents:**
- `annotation_jsonb` — `grammar_role_key`, `grammar_focus_key`, `syntactic_trap_key`, `difficulty_overall`
- `explanation_jsonb` — `explanation_short`, `explanation_full`, `evidence_span_text`
- `confidence_jsonb` — `annotation_confidence`, `needs_human_review`, `review_notes`

---

## `question_options`

Per-option analysis. 4 rows per question.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | No | — |
| `question_id` | UUID | No | FK |
| `question_version_id` | UUID | No | FK |
| `option_label` | VARCHAR(1) | No | `A`/`B`/`C`/`D` |
| `option_text` | TEXT | No | — |
| `is_correct` | BOOLEAN | No | — |
| `option_role` | VARCHAR(10) | No | `correct` or `distractor` |
| `distractor_type_key` | VARCHAR(30) | Yes | V3 controlled |
| `semantic_relation_key` | VARCHAR(40) | Yes | V3 controlled |
| `plausibility_source_key` | VARCHAR(30) | Yes | V3 controlled |
| `option_error_focus_key` | VARCHAR(40) | Yes | V3 grammar focus |
| `why_plausible` | TEXT | Yes | — |
| `why_wrong` | TEXT | Yes | — |
| `grammar_fit` | VARCHAR(3) | Yes | `yes`/`no` |
| `tone_match` | VARCHAR(3) | Yes | `yes`/`no` |
| `precision_score` | SMALLINT | Yes | `1`/`2`/`3` |
| `student_failure_mode_key` | VARCHAR(30) | Yes | V3 controlled |
| `distractor_distance` | VARCHAR(10) | Yes | `wide`/`moderate`/`tight` |
| `distractor_competition_score` | FLOAT | Yes | V3 metric |
| `created_at` | TIMESTAMPTZ | No | — |

---

## `question_assets`

Raw source files and extracted artifacts.

| Column | Type | Nullable |
|---|---|---|
| `id` | UUID | No |
| `question_id` | UUID | Yes |
| `content_origin` | ENUM | No |
| `asset_type` | ENUM | No |
| `storage_path` | TEXT | No |
| `mime_type` | VARCHAR(100) | Yes |
| `page_start` | INTEGER | Yes |
| `page_end` | INTEGER | Yes |
| `source_url` | TEXT | Yes |
| `source_name` | VARCHAR(200) | Yes |
| `source_exam_code` | VARCHAR(20) | Yes |
| `source_module_code` | VARCHAR(10) | Yes |
| `source_question_number` | INTEGER | Yes |
| `checksum` | VARCHAR(64) | Yes | SHA-256 |
| `created_at` | TIMESTAMPTZ | No |

---

## `question_relations`

Cross-question linking.

| Column | Type | Nullable |
|---|---|---|
| `id` | UUID | No |
| `from_question_id` | UUID | No |
| `to_question_id` | UUID | No |
| `relation_type` | ENUM | No |
| `relation_strength` | FLOAT | Yes |
| `detection_method` | VARCHAR(30) | Yes |
| `is_human_confirmed` | BOOLEAN | No | `false` |
| `notes` | TEXT | Yes |
| `created_at` | TIMESTAMPTZ | No |

---

## `llm_evaluations`

Beta model comparison scores.

| Column | Type | Nullable |
|---|---|---|
| `id` | UUID | No |
| `job_id` | UUID | No |
| `question_id` | UUID | Yes |
| `provider_name` | VARCHAR(50) | No |
| `model_name` | VARCHAR(100) | No |
| `task_type` | VARCHAR(20) | No |
| `score_overall` | FLOAT | Yes |
| `score_metadata` | FLOAT | Yes |
| `score_explanation` | FLOAT | Yes |
| `score_generation` | FLOAT | Yes |
| `review_notes` | TEXT | Yes |
| `recommended_for_default` | BOOLEAN | Yes |
| `created_at` | TIMESTAMPTZ | No |

---

## `users`

Student accounts.

| Column | Type | Nullable |
|---|---|---|
| `id` | INTEGER | No | auto-increment |
| `username` | VARCHAR(100) | No | unique, indexed |
| `created_at` | TIMESTAMPTZ | No |

---

## `user_progress`

Answer attempts.

| Column | Type | Nullable |
|---|---|---|
| `id` | INTEGER | No | auto-increment |
| `user_id` | INTEGER | No | FK → `users.id` |
| `question_id` | UUID | No | FK → `questions.id` |
| `is_correct` | BOOLEAN | No | — |
| `selected_option_label` | VARCHAR(1) | No | `A`/`B`/`C`/`D` |
| `missed_grammar_focus_key` | VARCHAR(50) | Yes | V3 |
| `missed_syntactic_trap_key` | VARCHAR(50) | Yes | V3 |
| `timestamp` | TIMESTAMPTZ | No | `utcnow` |
