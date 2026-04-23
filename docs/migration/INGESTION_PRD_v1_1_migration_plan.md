# Migration Plan for `INGESTION.PRD` v1.1

**Date:** 2026-04-23  
**References:** [INGESTION.PRD](/home/jb/DSAT_REDUX_MD/INGESTION.PRD), [backend/models.py](/home/jb/DSAT_REDUX_MD/backend/models.py)

## 1. Goal

Translate the revised ingestion PRD into a concrete database migration plan for the current backend.

This plan supports:

- official PDF-only ingest
- flexible unofficial ingest
- generated-question lineage
- overlap tracking against official questions
- LLM-managed annotations and beta evaluation
- admin editing of question content and answers

This plan does not yet add student progress tracking changes beyond preserving compatibility with the existing `user_progress` table.

## 2. Current Baseline

The current backend is simpler than the older migration docs. Today it effectively has:

- `questions` with `id`, `source_type`, `grammar_focus_key`, `content`, `created_at`
- `user_progress`
- no explicit staging jobs, versions, raw assets, annotation snapshots, overlap relations, or evaluation tables in the live backend code

That matters because the migration strategy should extend the current JSON-backed `questions` model rather than reintroducing the older fully normalized ingestion shape all at once.

## 3. Migration Strategy

### 3.1 Compatibility Stance

Use an additive migration strategy.

- Keep `questions` as the canonical production record.
- Keep `questions.content` as the current composite JSON payload.
- Add explicit columns needed for filtering, approval, recall, and lineage.
- Add companion tables for jobs, versions, assets, annotations, relations, and evaluations.
- Do not remove `source_type` in the first migration wave.

### 3.2 Terminology Mapping

The PRD uses `content_origin`. The current backend uses `source_type`.

Plan:

- add `questions.content_origin`
- backfill it from `source_type`
- keep `source_type` temporarily for compatibility
- treat `source_type` as deprecated after app code is updated

Recommended mapping:

| existing `source_type` | new `content_origin` |
|---|---|
| `collegeBoard` | `official` |
| `admin_uploaded` | `unofficial` |
| `llm_generated` | `generated` |

If any rows do not map cleanly, backfill them to `unofficial` and log them for manual review.

### 3.3 Hybrid JSON-in-SQL Remains the Storage Core

The PRD requires broad metadata flexibility and frequent prompt iteration. That is a poor fit for a rigid decomposition-first schema.

The migration plan therefore keeps:

- `questions.content` as the current approved question payload
- `question_annotations.annotation_jsonb` as the full LLM metadata snapshot
- `question_versions` as immutable user-facing content snapshots

Only high-value filter fields are promoted to first-class columns.

## 4. Proposed Migration Sequence

Assuming the current project continues after its latest existing migration number, use the next available migration number. The filenames below use `043+` as placeholders.

### M-043: `043_ingestion_beta_enums_and_helpers.sql`

Create foundational enums and helper functions used by later tables.

Add enums:

- `content_origin_enum`: `official`, `unofficial`, `generated`
- `question_job_type_enum`: `ingest`, `generate`, `reannotate`, `overlap_check`
- `question_job_status_enum`: `uploaded`, `parsed`, `split`, `extracted`, `annotated`, `answer_verified`, `overlap_checked`, `reviewed`, `approved`, `archived`, `rejected`, `failed`
- `question_asset_type_enum`: `pdf`, `image`, `screenshot`, `markdown`, `json`, `text`
- `question_relation_type_enum`: `overlaps_official`, `derived_from`, `near_duplicate`, `generated_from`, `adapted_from`
- `practice_status_enum`: `draft`, `active`, `retired`
- `validation_severity_enum`: `blocking`, `review`, `warning`
- `overlap_status_enum`: `none`, `possible`, `confirmed`

Add helper functions:

- `fn_touch_updated_at()`
- optional `fn_normalize_content_origin(text)`

Why first:

- later migrations can use enums and shared triggers cleanly

### M-044: `044_expand_questions_for_three_origin_corpus.sql`

Expand `questions` rather than replacing it.

Add columns:

- `content_origin content_origin_enum`
- `syntactic_trap_key text`
- `difficulty_overall text`
- `stimulus_mode_key text`
- `question_family_key text`
- `practice_status practice_status_enum not null default 'draft'`
- `official_overlap_status overlap_status_enum not null default 'none'`
- `canonical_official_question_id uuid null references questions(id)`
- `derived_from_question_id uuid null references questions(id)`
- `is_admin_edited boolean not null default false`
- `metadata_managed_by_llm boolean not null default true`
- `latest_annotation_id uuid null`
- `answer_verified boolean not null default false`
- `approved_at timestamptz null`
- `retired_at timestamptz null`
- `updated_at timestamptz not null default now()`

Backfill:

- populate `content_origin` from `source_type`
- default `practice_status='active'` only for already-approved legacy rows if such approval state exists in data; otherwise keep `draft`

Constraints:

- `content_origin` not null after backfill
- official questions may reference themselves nowhere:
  `canonical_official_question_id != id`
- if `content_origin='official'`, then `official_overlap_status='none'`

Indexes:

- `questions(content_origin, practice_status)`
- `questions(grammar_focus_key, content_origin, practice_status)`
- `questions(syntactic_trap_key)`
- `questions(question_family_key, difficulty_overall)`
- `questions(canonical_official_question_id)`

Notes:

- keep `source_type` for one migration cycle
- keep `content` as the current approved full payload

### M-045: `045_question_versions.sql`

Add immutable content versioning for ingest, generation, and admin edits.

Create `question_versions`:

- `id uuid primary key`
- `question_id uuid not null references questions(id) on delete cascade`
- `version_number int not null`
- `change_source text not null check in (`ingest`, `generate`, `admin_edit`, `reprocess`)`
- `question_text text`
- `passage_text text`
- `choices_jsonb jsonb not null`
- `correct_option_label text`
- `explanation_text text`
- `content_jsonb jsonb not null`
- `editor_user_id uuid null`
- `change_notes text null`
- `created_at timestamptz not null default now()`

Constraints:

- unique `(question_id, version_number)`
- `correct_option_label` must be `A|B|C|D` when present

Backfill:

- create version `1` for each existing question using the current `questions.content`

Why early:

- later annotation, approval, and admin-edit flows should point at immutable versions

### M-046: `046_question_jobs.sql`

Replace the PRD’s staging concept with a concrete orchestration table.

Create `question_jobs`:

- `id uuid primary key`
- `job_type question_job_type_enum not null`
- `content_origin content_origin_enum not null`
- `input_format question_asset_type_enum not null`
- `status question_job_status_enum not null`
- `provider_name text null`
- `model_name text null`
- `prompt_version text null`
- `rules_version text null`
- `raw_asset_id uuid null`
- `question_id uuid null references questions(id) on delete set null`
- `question_version_id uuid null references question_versions(id) on delete set null`
- `comparison_group_id uuid null`
- `source_exam_code text null`
- `source_module_code text null`
- `source_question_number int null`
- `source_page_start int null`
- `source_page_end int null`
- `pass1_json jsonb null`
- `pass2_json jsonb null`
- `validation_errors_json jsonb null`
- `job_notes text null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Constraints:

- if `content_origin='official'`, `input_format` must equal `pdf`
- if `content_origin='official'`, source exam/module/question metadata must be present before `status in ('reviewed','approved','archived')`
- if `content_origin='generated'`, `job_type` must be `generate` or `reannotate`

Indexes:

- `question_jobs(status, created_at desc)`
- `question_jobs(content_origin, status)`
- `question_jobs(comparison_group_id)`
- `question_jobs(source_exam_code, source_module_code, source_question_number)`

Compatibility note:

- if `question_ingestion_jobs` already exists in Supabase, do not drop it in this migration wave
- instead create a compatibility view later or plan a separate data-copy migration

### M-047: `047_question_assets.sql`

Store raw assets and extracted source references.

Create `question_assets`:

- `id uuid primary key`
- `question_id uuid null references questions(id) on delete set null`
- `job_id uuid null references question_jobs(id) on delete set null`
- `content_origin content_origin_enum not null`
- `asset_type question_asset_type_enum not null`
- `asset_role text not null check in (`raw_source`, `official_archive`, `derived_image`, `ocr_text_export`)`
- `storage_backend text not null`
- `storage_path text not null`
- `mime_type text null`
- `file_size_bytes bigint null`
- `checksum text null`
- `page_start int null`
- `page_end int null`
- `source_url text null`
- `source_name text null`
- `source_exam_code text null`
- `source_module_code text null`
- `source_question_number int null`
- `created_at timestamptz not null default now()`

Constraints:

- official archive rows require `content_origin='official'`
- `asset_role='official_archive'` requires exam/module/question metadata

Indexes:

- `question_assets(question_id)`
- `question_assets(job_id)`
- `question_assets(content_origin, asset_type)`
- unique partial index on `(checksum)` where checksum is not null for dedupe assistance

Companion non-SQL changes:

- create private bucket for raw assets
- create private bucket for official archives
- add local mirror path for development recovery

### M-048: `048_question_annotations.sql`

Persist LLM-managed metadata snapshots separately from current question content.

Create `question_annotations`:

- `id uuid primary key`
- `question_id uuid not null references questions(id) on delete cascade`
- `question_version_id uuid not null references question_versions(id) on delete cascade`
- `provider_name text not null`
- `model_name text not null`
- `prompt_version text null`
- `rules_version text not null`
- `annotation_jsonb jsonb not null`
- `explanation_jsonb jsonb null`
- `generation_profile_jsonb jsonb null`
- `confidence_jsonb jsonb null`
- `needs_human_review boolean not null default false`
- `created_at timestamptz not null default now()`

Add FK from `questions.latest_annotation_id -> question_annotations(id)` after table creation.

Derived columns on `questions` should be refreshed by app code on annotation approval:

- `grammar_focus_key`
- `syntactic_trap_key`
- `difficulty_overall`
- `stimulus_mode_key`
- `question_family_key`

Why separate this table:

- metadata is LLM-managed and can be regenerated without overwriting the approved content version history

### M-049: `049_question_relations_and_overlap.sql`

Create relation tracking for overlap and lineage.

Create `question_relations`:

- `id uuid primary key`
- `from_question_id uuid not null references questions(id) on delete cascade`
- `to_question_id uuid not null references questions(id) on delete cascade`
- `relation_type question_relation_type_enum not null`
- `relation_strength numeric(5,4) null`
- `detection_method text null`
- `is_human_confirmed boolean not null default false`
- `notes text null`
- `created_at timestamptz not null default now()`

Constraints:

- `from_question_id != to_question_id`
- unique `(from_question_id, to_question_id, relation_type)`

Indexes:

- `question_relations(from_question_id, relation_type)`
- `question_relations(to_question_id, relation_type)`
- partial index for overlap review:
  `(relation_type, is_human_confirmed)` where `relation_type='overlaps_official'`

App synchronization rules:

- when a confirmed `overlaps_official` relation is created, update:
  - `questions.official_overlap_status='confirmed'`
  - `questions.canonical_official_question_id=<official question id>`
- when only a machine match exists, set `official_overlap_status='possible'`

### M-050: `050_llm_evaluations.sql`

Create beta model-comparison storage.

Create `llm_evaluations`:

- `id uuid primary key`
- `job_id uuid not null references question_jobs(id) on delete cascade`
- `question_id uuid null references questions(id) on delete set null`
- `provider_name text not null`
- `model_name text not null`
- `task_type text not null check in (`extract`, `annotate`, `generate`)`
- `prompt_version text null`
- `rules_version text null`
- `latency_ms int null`
- `token_usage_jsonb jsonb null`
- `score_overall numeric(5,2) null`
- `score_metadata numeric(5,2) null`
- `score_explanation numeric(5,2) null`
- `score_generation numeric(5,2) null`
- `pass_fail boolean null`
- `review_notes text null`
- `recommended_for_default boolean not null default false`
- `created_at timestamptz not null default now()`

Indexes:

- `llm_evaluations(task_type, provider_name, model_name)`
- `llm_evaluations(job_id)`
- `llm_evaluations(question_id)`

### M-051: `051_admin_review_and_answer_verification.sql`

Add explicit admin review storage instead of burying review state in generic notes.

Create `question_reviews`:

- `id uuid primary key`
- `question_id uuid not null references questions(id) on delete cascade`
- `question_version_id uuid null references question_versions(id) on delete set null`
- `job_id uuid null references question_jobs(id) on delete set null`
- `review_type text not null check in (`approval`, `answer_verification`, `overlap_confirmation`, `metadata_scoring`)`
- `review_decision text not null check in (`approved`, `rejected`, `flagged`, `confirmed`, `cleared`)`
- `reviewed_by_user_id uuid null`
- `review_notes text null`
- `created_at timestamptz not null default now()`

Add rules:

- official questions cannot move to `questions.practice_status='active'` unless `answer_verified=true`
- generated questions cannot move to `active` while `official_overlap_status in ('possible','confirmed')` unless a review row clears or rejects the overlap

Optional trigger:

- guard updates to official `practice_status='active'` unless `answer_verified=true`

### M-052: `052_indexes_views_and_policies.sql`

Add the retrieval and security layer.

Indexes:

- `questions(content_origin, grammar_focus_key, difficulty_overall, practice_status)`
- `questions(content_origin, official_overlap_status, practice_status)`
- GIN index on `questions.content`
- GIN index on `question_annotations.annotation_jsonb`
- GIN index on `question_versions.content_jsonb`

Views:

- `v_practice_questions`
  - only active questions
  - joins latest version + latest annotation
- `v_official_overlap_queue`
  - unofficial/generated rows with `official_overlap_status='possible'`
- `v_llm_beta_scorecard`
  - aggregate provider/model performance by task type

Policies / RLS:

- official assets admin-only
- review tables admin-only write
- service-role full write on jobs, assets, annotations, relations, evaluations

## 5. Data Backfill Plan

### 5.1 Questions

Backfill `questions` first:

- map `source_type -> content_origin`
- create default `practice_status`
- create derived filter fields from `content` where available

### 5.2 Versions

For each existing `questions` row:

- create `question_versions.version_number = 1`
- copy current content into `content_jsonb`
- extract question text, passage, choices, answer, explanation if available

### 5.3 Annotations

If historical metadata already lives inside `questions.content`, do not attempt a fragile one-shot split during the first migration wave.

Safer plan:

- leave historical metadata in `questions.content`
- only create `question_annotations` for newly processed or explicitly reannotated records
- optionally run a later backfill job once payload shapes are stable

### 5.4 Jobs and Assets

Do not attempt to reconstruct historical jobs unless the source records already exist. New ingestion and generation flows should populate these tables going forward.

## 6. Application Changes Required Alongside Migrations

These migrations are not enough by themselves. The app must change in the same rollout window.

### 6.1 Ingest API

Add endpoints from the PRD:

- `/ingest/official/pdf`
- `/ingest/unofficial/file`
- `/ingest/unofficial/batch`
- `/ingest/reannotate/{question_id}`

### 6.2 Question Write Path

Approval flow should:

1. create or update `questions`
2. append `question_versions`
3. append `question_annotations`
4. update `questions.content` with the approved current payload
5. update promoted filter columns
6. write `question_assets` rows
7. write `question_relations` rows if overlap or lineage exists

### 6.3 Admin Edit Path

Admin content edits should:

1. create a new `question_versions` row
2. mark `questions.is_admin_edited=true`
3. queue `question_jobs(job_type='reannotate')`
4. keep metadata LLM-managed by replacing `latest_annotation_id` only after the reannotation review completes

## 7. Open Design Decisions Before SQL Is Written

These should be resolved before implementing the actual migration files.

### 7.1 Question ID Type

The current SQLAlchemy model uses `String` IDs. The PRD assumes UUIDs.

Recommended:

- standardize on UUID in the database
- if legacy string IDs already exist, use text-compatible bridge logic during backfill

### 7.2 Official Archive Representation

Two valid options:

- represent archives only as `question_assets(asset_role='official_archive')`
- create a separate `official_archives` table

Recommendation:

- use `question_assets`
- avoid a dedicated archive table unless multiple archive formats per question become common

### 7.3 Annotation JSON Shape

The PRD expects flexibility, but app code still needs stable extraction rules for promoted columns.

Recommendation:

- define a small stable extraction contract for:
  - `grammar_focus_key`
  - `syntactic_trap_key`
  - `difficulty_overall`
  - `stimulus_mode_key`
  - `question_family_key`
- leave the rest inside JSON

### 7.4 Generated-Question Approval Rule

The PRD says generated questions too close to official questions must be blocked.

Recommendation:

- block on `confirmed`
- hold for review on `possible`
- only activate after a review row confirms clearance

## 8. Recommended Execution Order

1. M-043 through M-045
2. ship app support for `questions` + `question_versions`
3. M-046 through M-049
4. ship new ingest, overlap, and annotation flows
5. M-050 through M-052
6. enable beta LLM comparison and stricter admin workflows

This reduces rollout risk because the app can start using versioned questions before the full job/evaluation system is complete.

## 9. Summary

The safest path is not a schema rewrite. It is an additive migration program around the existing JSON-backed `questions` table.

That gives the backend:

- three-origin question tracking
- official PDF-only ingest enforcement
- flexible unofficial source storage
- generated-question lineage
- official overlap marking
- immutable question versions
- LLM annotation snapshots
- beta model evaluation storage
- admin editing and answer verification

without forcing a brittle return to the older normalized ingestion design.
