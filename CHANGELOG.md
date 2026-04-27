# CHANGELOG

All significant changes to this project. Timestamps are commit time (PDT, UTC-7).
Agent: **Claude Sonnet 4.6** (`claude-sonnet-4-6`)

---

## 2026-04-27

### 14:35 — Added missing indexes to SQLAlchemy models
**Commits:** *(pending)*

- Added `Index()` declarations to `models/db.py` `__table_args__` to match migration 005:
  - `Question`: `ix_questions_practice_status`, `ix_questions_content_origin`, `ix_questions_latest_annotation_id`
  - `QuestionJob`: `ix_question_jobs_status`, `ix_question_jobs_created_at`
  - `UserProgress`: `ix_user_progress_user_id`, `ix_user_progress_question_id`
  - `QuestionRelation`: `ix_question_relations_from_question_id`, `ix_question_relations_to_question_id`
- Added `Index` import to `models/db.py`

### Rules — Grammar module expansion and realism rules upgrade

Files changed: `rules/mcq_realism_rules.md`, `rules/rules_grammar_module_outline.md`, `rules/rules_core_generation_outline.md`, `rules/rules_reading_module_outline.md`

**`mcq_realism_rules.md`**

- Added **All-Four-Plausible Rule** section: every answer choice — including all three distractors — must produce plausible English on first read; nothing eliminable by ear-test alone; includes difficulty gradient table (low/medium/high)
- Added **Student Failure Mode Requirement** section: 16 named psychological failure modes (`nearest_noun_reflex`, `comma_fix_illusion`, `formal_word_bias`, `possessive_contraction_confusion`, `tense_proximity_pull`, `parallel_shape_bias`, `pronoun_anchor_error`, `ear_test_pass`, etc.) now mandatory on every distractor via `student_failure_mode_key`
- Added **SEC Distractor Architecture by Grammar Type** section: specific 4-option construction rules for all grammar categories including subject-verb agreement, verb tense, semicolons, apostrophes, modifiers, parallel structure, pronouns, adjective/adverb, illogical comparisons, sentence boundary, subjunctive mood, and transitions
- Added **Step 2 (Syntactic Trap)** to Generator Workflow: trap must be named before distractors are written
- Added **Step 6 (All-Four-Plausible Verification)**: explicit read-aloud check inserted before competitive ranking check
- Added **Hard-Item Validator Checklist**: additional validation layer for `difficulty_overall: high` — no shared failure modes across distractors, correct answer not the only formal-sounding option, ear-test cannot resolve the item

**`rules_grammar_module_outline.md`**

- Converted from planning outline to full operational document
- Full taxonomy tables for all grammar role keys and focus keys
- Added 4 grammar types from research that were absent from the taxonomy:
  - `adjective_adverb_distinction` (proposed key, parent: `modifier`)
  - `illogical_comparison` (proposed key, parent: `modifier`)
  - `commonly_confused_words` (proposed key, parent: `expression_of_ideas`)
  - `subjunctive_mood` (added to `verb_form` family)
- Added correlative conjunction rules under `parallel_structure` (both/and, either/or, neither/nor, not only/but also)
- Added syntactic trap taxonomy table with grammar focus mappings
- Added passage construction templates for every grammar focus key
- Added distractor heuristic tables with `student_failure_mode_key` for every focus key
- Added frequency band table for all focus keys
- Added full grammar validation checklist

**`rules_core_generation_outline.md`**

- Converted from planning outline to full shared infrastructure document
- Added SAT Realism Layer (Section 8): distractor distance, plausible wrong count, answer separation strength, all-four-plausible requirement, realism scoring thresholds
- Added shared distractor engineering rules with `student_failure_mode_key` requirement
- Added anti-clone and diversity controls
- Added provenance and audit trail schema
- Added shared validation lifecycle with core checklist

**`rules_reading_module_outline.md`**

- Added Section 14 with reading-specific `student_failure_mode_key` values: `local_detail_fixation`, `overreach`, `underreach`, `text_label_swap`, `topic_association`, `inverse_logic`, `false_agreement`
- Added realism requirements aligned to core (all-four-plausible requirement for reading items)

---

## 2026-04-25

### 18:10 — Option annotation hydration & metadata lifecycle management
**Commits:** `26ba7e9`

- Added `backend/app/pipeline/option_hydration.py` — shared helpers to extract, apply, and clear the 12 per-option annotation fields (`distractor_type_key`, `semantic_relation_key`, `plausibility_source_key`, `option_error_focus_key`, `why_plausible`, `why_wrong`, `grammar_fit`, `tone_match`, `precision_score`, `student_failure_mode_key`, `distractor_distance`, `distractor_competition_score`) from `annotate_json` to `QuestionOption` rows
- Ingest pipeline (`_run_pipeline`): all `QuestionOption` annotation columns now populated on creation
- Ingest reannotation (`_run_reannotate_pipeline`): existing option rows refreshed with new annotation; `annotation_stale` cleared to `False` on success
- Generate pipeline: identical option annotation hydration on first creation
- `models/db.py` — added `annotation_stale` boolean to `Question`
- Migration `009_add_annotation_stale`: adds `annotation_stale` column with `server_default=false`
- Admin `PATCH /questions/{id}`: sets `annotation_stale=True` on any edit — flags question for reannotation queue
- Admin `POST /questions/{id}/reject`: cascade-deletes `question_annotations`, `llm_evaluations`, `question_relations`; nulls per-option annotation fields; retires question
- Admin `DELETE /questions/{id}` (new endpoint): hard-deletes question and all linked rows in safe FK order; detaches jobs and assets (preserves audit trail and files on disk)

---

### 17:47 — PDF filename typo fix
**Commits:** `7b3f5dd`

- Renamed `Test_10_digitial_sec01_mod02.pdf` → `Test_10_digital_sec01_mod02.pdf` in `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/`

---

### 17:07 — Verbal practice test PDFs added
**Commits:** `bbd5c12` *(pulled from remote)*

- Added 14 verbal section PDFs for Practice Tests 1, 6–11 (both `sec01_mod01` and `sec01_mod02`) to `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/`
- Validated all 18 PDFs: readable, unencrypted, 13–16 pages, 28k–35k chars each
- Note: Test 11 mod01/mod02 have zero embedded images (vector-rendered); all other tests have 14–17 embedded images per file
- Documented canonical test source path in `CLAUDE.md`

---

### 15:45 — DB integrity gap remediation (6 gaps)
**Commits:** `ba88685`

- Migration `004_add_unique_constraints`: `UniqueConstraint` on `question_versions(question_id, version_number)`, `question_options(question_version_id, option_label)`, `question_relations(from_question_id, to_question_id, relation_type)`
- Migration `005_add_performance_indexes`: 9 indexes on hot query columns across `questions`, `question_jobs`, `user_progress`, `question_relations`
- Migration `006_add_check_constraints`: DB-level `CHECK` constraints mirroring Pydantic validation — option labels A–D, LLM scores 0–10, relation strength 0–1
- Migration `007_add_source_section_code_to_assets`: adds `source_section_code` to `question_assets`
- Migration `008_add_server_defaults`: `server_default=now()` on all 12 timestamp columns across all tables
- `models/db.py`: added `UniqueConstraint` `__table_args__` to `QuestionVersion`, `QuestionOption`, `QuestionRelation`; added `source_section_code` to `QuestionAsset`
- `routers/ingest.py`: write `source_section_code` to asset at upload time; backfill from `extract_json` during pipeline link-back
- `migrations/env.py`: fixed `else` branch that silently discarded `-x sqlalchemy.url` override; `run_migrations_online()` now reads URL from config instead of hardcoding `settings.database_url`

---

## 2026-04-24

### 20:09 — User CRUD endpoints
**Commits:** `8e45fa5`

- Added `POST /users`, `GET /users/{id}`, `DELETE /users/{id}` with admin auth

### 20:08 — N+1 query fix in overlap detection
**Commits:** `ff11b72`

- Replaced N+1 annotation queries in `detect_overlaps` with a single JOIN

### 20:07 — V3 ontology key validation
**Commits:** `1586ffc`

- Validator now checks `grammar_role_key`, `grammar_focus_key`, `stimulus_mode_key`, `stem_type_key` against approved V3 keys; `explanation_short` capped at 300 chars

### 20:04 — LLM provider cleanup on shutdown
**Commits:** `e7ca0bb`

- Closed `httpx` clients for all LLM providers on app shutdown via FastAPI lifespan

### 20:01 — Generation provider selection
**Commits:** `bfce92f`

- Caller can now specify `provider_name` and `model_name` in generate requests

### 20:00 — Reannotation request body fix
**Commits:** `09cfb6b`

- Moved `provider_name`/`model_name` from query params to JSON body in reannotate endpoint

### 19:59 — Upload size guard
**Commits:** `55ca86c`

- Check `Content-Length` before reading upload body to avoid loading 50 MB into RAM

### 15:05 — API routers and integration tests
**Commits:** `3d19244`

- Added 5 API routers with 19 endpoints; integration test suite

### 14:18 — Request/response schemas and API docs
**Commits:** `33e8d88`

- Added generation/ingest request schemas, job response model, OpenAPI docs

### 13:11 — Migration order, Docker Postgres, manual test CLI
**Commits:** `ce423ba`

- Fixed migration ordering; added Docker Postgres config; manual test CLI

### 12:35 — Prompts, pipeline orchestrator, validator
**Commits:** `198b7da`

- Extract and annotate prompts; `JobOrchestrator`; question validator

### 12:34 — Parsers
**Commits:** `f845a4c`

- JSON, PDF (pymupdf), image, and markdown extraction parsers

### 12:34 — LLM provider layer
**Commits:** `08b9133`

- Protocol, factory, Anthropic, OpenAI, and Ollama providers

### 12:13 — Initial migration
**Commits:** `b621316`

- Alembic config; 10-table initial schema migration
