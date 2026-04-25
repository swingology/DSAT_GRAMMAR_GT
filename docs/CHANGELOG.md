# Project Changelog

This file records high-signal project-level changes, audits, and database/ontology state reviews.

Migration-by-migration implementation history still lives in [docs/CHANGELOG.md](docs/CHANGELOG.md).

## 2026-04-24 — Backend Gap Fixes (27 gaps closed)

**Branch:** `main`
**Type:** bug fix, schema correction, pipeline completion
**Model:** `claude-sonnet-4-6` (Claude)

### Schema & Migrations

| Change | Reason | File(s) |
|--------|--------|---------|
| **Fix ORM enum name mismatch** — `Question.content_origin` renamed from `content_origin_enum2` to `content_origin_enum`; same for `QuestionAsset` (`_enum3` → `_enum`) | asyncpg failed at runtime resolving type OIDs — `questions` and `question_assets` tables were completely inaccessible through the ORM | `app/models/db.py:49,151` |
| **Fix Alembic downgrade** — `ENUMS` list moved from inside `upgrade()` to module level | `downgrade()` referenced undefined local variable `enums`, causing `NameError` | `migrations/001_initial_schema.py` |
| **Add `pool_pre_ping=True`** to async engine | Stale connections from pool caused cryptic production errors | `app/database.py:9` |

### Ingest Pipeline

| Change | Reason | File(s) |
|--------|--------|---------|
| **Persist `Question` + `QuestionVersion` + `QuestionAnnotation` + 4× `QuestionOption` rows** after successful LLM pipeline | Pipeline ran to completion but never created any DB rows — ingest produced no data | `app/routers/ingest.py:90-175` |
| **Use `job.provider_name` instead of `settings.default_annotation_provider`** | User-specified provider at upload time was stored but ignored | `app/routers/ingest.py:36-38` |
| **Set `QuestionAsset.question_id`, `Question.latest_annotation_id`, `Question.latest_version_id`** | These FK columns were never populated, remaining NULL | `app/routers/ingest.py:160-170` |

### Generate Pipeline

| Change | Reason | File(s) |
|--------|--------|---------|
| **Persist `QuestionVersion`, `QuestionAnnotation`, 4× `QuestionOption` rows** alongside Question | Bare Question row was created without options, annotation, or version history — orphaned data | `app/routers/generate.py:67-145` |
| **Set `latest_annotation_id` and `latest_version_id`** | Same FK gap as ingest pipeline | `app/routers/generate.py:133-134` |

### Reannotation

| Change | Reason | File(s) |
|--------|--------|---------|
| **New `_run_reannotate_pipeline`** skips extraction, goes straight to annotate | Previous code re-ran full pipeline including Pass 1 extraction despite already having `pass1_json` | `app/routers/ingest.py:346-415` |
| **Creates new `QuestionVersion` + `QuestionAnnotation` + updates `latest_*` pointers** | Reannotations now produce proper versioned audit trail | `app/routers/ingest.py:380-410` |

### Router Bug Fixes

| Change | Reason | File(s) |
|--------|--------|---------|
| **Remove `allow_credentials=True` from CORS** | `allow_origins=["*"]` + `allow_credentials=True` rejected by all browsers | `app/main.py:19` |
| **Fix `stimulus_mode_key` field mapping** (`stem_type_key` → `stimulus_mode_key`) | Wrong DB column mapped to response field in recall endpoints | `app/routers/questions.py:107`, `student.py:88` |
| **Fix pagination** — filters moved from Python to SQL WHERE clauses with JSONB queries | Python-side filtering after SQL LIMIT broke pagination (empty pages possible) | `app/routers/questions.py`, `student.py` |
| **Fix admin `edit_question`** — `choices_jsonb` now serializes actual options; `latest_version_id` updated | Option data was lost in version snapshots; latest_version_id never set | `app/routers/admin.py:44-67` |

### Other

| Change | Reason | File(s) |
|--------|--------|---------|
| **Add DB health check to `GET /`** (runs `SELECT 1`) | Health endpoint returned static OK even when DB was unreachable | `app/routers/health.py` |
| **Align `prompt_version`** from `"v1"` to `"v3.0"` | Routers said `"v1"` while ORM default was `"v3.0"` — inconsistent | `app/routers/ingest.py`, `generate.py`, `manual_test.py` |
| **Add exports to all 7 `__init__.py` files** | Previously empty, required deep imports | `app/models/__init__.py`, `app/routers/__init__.py`, `app/llm/__init__.py`, `app/parsers/__init__.py`, `app/pipeline/__init__.py`, `app/prompts/__init__.py`, `app/storage/__init__.py` |
| **Remove unused `IngestPdfRequest` model** | Defined but never used — endpoints use `Form(...)` directly | `app/models/payload.py` |

---

## 2026-04-21 - CB Exam Ingestion & Analysis Architecture Designed

**Branch:** `main`
**Type:** architecture design, feature spec

### Scope

Designed the full CB practice exam ingestion and corpus analysis system. Spec saved to `docs/BACKEND_ARCHITECTURE_DESIGN.md`.

### Key Decisions

- **`POST /ingest/exam`** — new endpoint triggers LLM Pass 0 (exam splitter) on full exam PDF; extracts passages, question blocks, and stable external IDs (`PT1-M1-Q07`) before existing 2-pass pipeline
- **Normalized `passages` table** — one row per unique passage; questions reference via `passage_id` FK; deduplication on passage text hash
- **`exam_form_specs` table** — comprehensive per-module distribution spec (10 dimensions: grammar_focus with CB frequency bands, question_family, stimulus_mode, domain, difficulty with IRT b-means, passage stats, answer_mechanism, distractor profile, lexical_tier, syntactic_complexity, co-occurrence patterns)
- **Ollama support for Pass 0** — same LLMProvider abstraction; PDF chunked if needed; JSON repair + retry loop for weaker local model output
- **Three-point drift prevention** — (1) ingestion-time conformance check against GROUND_TRUTH frequency bands + co-occurrence matrix; (2) generation-time hard quota enforcement, IRT banding, passage fingerprint check, rolling distribution correction; (3) standing DB views (`v_corpus_distribution`, `v_form_spec_deviation`, `v_cooccurrence_matrix`)
- **Two-track approval system** — CB PDF questions (`content_origin = 'ingested_cb'`) auto-approve if clean; agent reruns on validation errors (3 attempts); persistent failures go to `agent_failed` triage queue. Admin-entered and generated questions always require human approval.
- **Admin question entry** — `POST /admin/questions` bypasses LLM ingestion; optional Pass 2 annotation; full lookup key validation; tagged `content_origin = 'admin_entry'`
- **Corpus analysis job** — triggered at 80% and 100% approval; computes `exam_form_specs`; cross-exam aggregate spec (`exam_code = 'ALL'`) rebuilt after each exam completes
- **New status values** — `auto_approved`, `agent_failed` added to `question_ingestion_jobs` status enum

---

## 2026-04-21 - Migrations PRD v2 Rebuild: 23 Gap Fixes Applied

**Branch:** `main`
**Type:** schema correction, authority alignment, safety hardening

### Scope

Applied fixes for all 23 gaps identified in the Migrations PRD v2 gap analysis (`docs/superpowers/specs/2026-04-20-migrations-prd-v2-gap-analysis.md`). All changes to `docs/Migrations_PRD_v2_rebuild.md`.

### Authority Decision

**GROUND_TRUTH_GRAMMAR v1.2** is the authoritative source for grammar rule mappings, disambiguation priorities, frequency data, syntactic trap keys, and passage tense register — overriding Taxonomy v2.6 wherever they conflict. Rationale: GROUND_TRUTH's logical consistency produces the most realistic DSAT question generation for traps, writing style, consistency, topic, and grammar rule focus.

### Critical Fixes (4)

- **C1 — Deployment order bug:** M-022/M-023/M-026 must run before M-005/M-006 (NOT NULL FK seeds required before first INSERT). Added explicit dependency rules.
- **C2 — No rollback plan:** All 49 INSERT statements now use `ON CONFLICT (key) DO NOTHING`. Re-running after partial failure no longer produces duplicate key violations.
- **C3 — No data migration path:** Documented as re-ingestion requirement in app-layer section.
- **C4 — No concurrent migration safety:** Added `schema_migrations` tracking table + `fn_acquire_migration_lock()` advisory lock function in M-001.

### High-Priority Fixes (8)

- **H1 — Grammar role mapping errors:** `elliptical_constructions` moved from `verb_form` to `parallel_structure` (GROUND_TRUTH §3.6). `preposition_idiom` moved from `verb_form` to `parallel_structure` (GROUND_TRUTH §3.8, priority 12 chain).
- **H2 — Disambiguation priority collision:** `pronoun_antecedent_agreement` priority changed from 5 to 6 (GROUND_TRUTH §4.5: pronoun_case > pronoun_antecedent_agreement).
- **H3 — Missing CHECK constraints:** Added `chk_span_char_order` and `chk_span_has_anchor` to `question_coaching_annotations` (M-015).
- **H4 — 12 analytical views missing:** Added all 12 views (v_question_distribution, v_distractor_effectiveness, v_embedding_coverage, v_ingestion_pipeline_summary, v_prose_complexity_profile, v_style_complexity_distribution, v_style_composition_profile, v_item_anatomy_profile, v_option_anatomy_distribution, v_distractor_pick_analysis, v_generation_run_summary, v_module_form_spec) + `fn_rebuild_embedding_index()` to M-020.
- **H5 — RLS on only 4 tables:** Expanded from 4 to 20 tables with read_authenticated + write_service_role policies.
- **H6 — Non-idempotent DDL/DML:** All INSERT statements now have `ON CONFLICT` guards.
- **H7 — Under-seeded IRT lookup tables:** Replaced 5 ordinal syntactic_trap keys (none/minor/moderate/significant/extreme) with 13 GROUND_TRUTH Part 7 diagnostic keys (nearest_noun_attraction, garden_path, early_clause_anchor, etc.). Updated `fn_compute_irt_b_v1()` CASE to map all 13 keys to ordinal scores 1-5.
- **H8 — Supabase-specific gaps:** Documented PgBouncer, Storage, and pgvector notes in deployment section.

### Moderate Fixes (8)

- **M1 —** `sentence_boundary` frequency label changed from `medium` to `high` (GROUND_TRUTH Part 5).
- **M2 —** Added `fn_rebuild_embedding_index()` to M-020.
- **M3 —** Added composite indexes: `(domain_key, difficulty_overall)`, standalone `grammar_focus_key`, `(question_id, annotation_type)`, `(status)` on generation_runs + ontology_proposals, `(is_active, retirement_status)` on questions, partial index on `show_condition='on_error'`, severity index on `lookup_dimension_compatibility`.
- **M4 —** M-004 title renamed from "Seed All Lookup Tables" to "Seed Critical Lookup Tables (Grammar, Domain, Topic, Annotation)".
- **M5 —** Comment block updated: 4 verb_form + 4 parallel_structure (including elliptical_constructions + preposition_idiom).
- **M6 —** Added `chk_passage_word_count` CHECK (1-800) to M-005.
- **M7 —** File naming convention noted in deployment section.
- **M8 —** Added `grammar_focus_frequency_evidence` table to M-003 for provenance tracking.

### Low Fixes (3)

- **L1 —** `negation` frequency label harmonized from `very_low` to `not_tested` (consistent with `affirmative_agreement` at 0.00 avg_questions_per_module).
- **L2 —** Added `passage_tense_register_key` FK to `questions` (M-005) and `question_classifications` (M-006). Added `lookup_passage_tense_register` table (M-003) + seed data (M-004) with 5 entries (past/present/historical/future/mixed) per GROUND_TRUTH §8.4.
- **L3 —** `preposition_idiom` role documented as `parallel_structure` with GROUND_TRUTH authority.

---

## 2026-03-23 - Database, Generation Quality, and Ontology Audit

**Branch:** `backend-alpha-v2`  
**Type:** architecture review, schema continuity review, generation-quality assessment

### Scope

This entry captures the current state of:

- the database schema on `backend-alpha-v2`
- the seeded pilot question bank
- the LLM generation support represented by the schema and pipeline
- the question ontology, with special focus on grammar, writing style, and complexity
- the boundary between lookup-backed ontology and JSONB-based style metadata

### Executive Summary

`backend-alpha-v2` is the strongest ontology and generation branch in the repository. The schema is substantially more expressive than the older MVP line and is clearly designed for controlled SAT-style generation rather than simple tagging.

The current limitation is not the schema. The limitation is continuity between schema, seed data, and runtime scripts:

- the expanded grammar/style/discourse/item-anatomy ontology exists in the database and model layer
- the current pilot seed SQL still populates the older, narrower annotation shape
- the embedding generation script remains partially out of sync with the newer schema
- style ontology is partly normalized and partly stored in JSONB, with two different levels of rigor

### What Is Established in the Schema

The branch now contains a strong normalized ontology for question organization and generation control.

#### Core normalized ontology already established

The following dimensions are lookup-backed or otherwise strongly constrained and should be treated as the canonical question ontology surface:

- question family
- stimulus mode
- stem type
- evidence scope and evidence location
- answer mechanism
- solver pattern
- distractor type
- semantic relation
- plausibility source
- generation pattern family
- syntactic complexity
- syntactic interruption
- evidence distribution
- syntactic trap
- lexical tier
- rhetorical structure
- noun phrase complexity
- vocabulary profile
- cohesion device
- epistemic stance
- inference distance
- transitional logic
- grammar focus
- distractor construction
- passage topic domain
- argument role

These dimensions are defined across the migration and validation layers and are the strongest organizational ontology in the project.

#### Grammar, writing style, and complexity coverage

The branch moves beyond broad difficulty labels and now has real structural descriptors for:

- sentence/clause architecture
- interruption type
- evidence placement pattern
- common syntactic trap pattern
- lexical tier and vocabulary profile
- rhetorical structure
- noun phrase complexity
- cohesion and discourse logic
- inference distance
- grammar-focus targeting for generation

This is a significant ontology improvement because it separates:

- what skill is being tested
- what makes the question cognitively difficult
- what stylistic or rhetorical profile the passage has
- what generation constraints should be preserved in a synthetic item

### Style Ontology Boundary: Normalized vs JSONB

The style ontology is only partially established in JSONB. The project currently has two distinct style layers:

#### 1. Strong style ontology: normalized fields

These should be treated as the authoritative style ontology because they are lookup-backed, validated, and queryable:

- `lexical_tier_key`
- `rhetorical_structure_key`
- `noun_phrase_complexity_key`
- `vocabulary_profile_key`
- `cohesion_device_key`
- `epistemic_stance_key`
- `inference_distance_key`
- `transitional_logic_key`

These fields are suitable for:

- search
- reporting
- generation constraints
- distribution balancing
- bank analysis
- future calibration

#### 2. Semi-controlled style metadata: `style_traits_jsonb`

`style_traits_jsonb` is not a fully normalized lookup-table ontology, but it is not free-form either.

At the model layer, the corresponding `style_traits` list is validated against a fixed tag set. That makes it a controlled tag surface stored in JSONB rather than an unconstrained blob.

Current examples of this controlled style-trait layer include tags such as:

- `heavy_nominalization`
- `multi_level_embedding`
- `center_embedding`
- `inverted_syntax`
- `parallel_structure`
- `hedging`
- `concession`
- `formal_register`
- `literary_prose`
- `scientific_register`
- `high_lexical_density`
- `domain_specific_vocabulary`

This layer is useful for:

- compositional tagging
- fast annotation expansion without a new migration for every micro-feature
- descriptive clustering
- future ontology proposal discovery

It is less suitable as the sole authoritative ontology for reporting or generation targeting because it is not normalized in SQL.

#### 3. Descriptive profile metadata: `style_profile_jsonb`

`style_profile_jsonb` is the weakest ontology surface of the three.

It has an expected structure in the prompt/model contract, but it remains semi-structured metadata rather than a canonical ontology. It is closer to an annotation profile than to a durable normalized taxonomy.

It currently carries concepts like:

- hedging presence
- craft signals
- subordination depth
- sentence variety
- cohesion type

This makes it useful for:

- descriptive downstream analysis
- human review context
- richer prompt context

It is weaker for:

- hard validation
- stable querying
- consistent distribution targets
- strict generation control

### Recommended Ontology Policy

The style system should be treated in three layers going forward:

#### Keep normalized in lookup-backed columns

These concepts are stable, reusable, and important enough to preserve as first-class ontology:

- lexical tier
- rhetorical structure
- noun phrase complexity
- vocabulary profile
- cohesion device
- epistemic stance
- inference distance
- transitional logic
- grammar focus

#### Keep in `style_traits_jsonb`

These concepts work well as composable controlled tags because they are numerous, overlapping, and may evolve:

- micro-syntactic signatures
- interruption subtypes already captured as stylistic tags
- register flavor tags
- rhetorical craft signals
- lexical density or nominalization traits when used descriptively rather than as primary axes

#### Consider promoting out of `style_profile_jsonb`

Any field that becomes important for:

- filtering
- balancing
- generation constraints
- analytics dashboards
- approval criteria

should be promoted to a normalized column or lookup-backed key.

The strongest candidates for future promotion are:

- subordination depth
- sentence variety
- cohesion type
- craft-signal families if they become operationally important

### Current Seed Database State

The current pilot seed bank is structurally usable but ontologically behind the schema.

#### Confirmed seeded corpus snapshot

- 66 total seeded questions across the two pilot SQL packs
- all 66 are marked `reuse_for_generation = true`
- difficulty distribution is concentrated in `medium`
- `answer_confidence` is effectively saturated at `1.0000` for all 66 seed questions

Dominant generation patterns in the current seed bank:

- `context_precision_complete_text`
- `interruption_then_new_sentence`
- `notes_goal_filtered_synthesis`
- `transition_discourse_relation`

Dominant question families in the current seed bank:

- `conventions_grammar`
- `words_in_context`
- `rhetorical_synthesis`
- `transitions`

#### Most important limitation

The seed SQL does not currently populate the richer `backend-alpha-v2` ontology.

The pilot seed files still write the older shape for:

- `question_classifications`
- `question_options`
- `question_generation_profiles`

As a result, the newer schema dimensions for grammar/style/discourse/item anatomy exist mainly as empty capacity unless they are backfilled through re-annotation or new seed generation.

### LLM Generation Quality Assessment

#### Infrastructure quality

Generation infrastructure quality is high at the schema level.

Reasons:

- generation-target fields are substantially richer than in the older MVP schema
- item anatomy and passage fingerprinting improve prompt precision
- option anatomy improves distractor control
- generation lifecycle tables support lineage and review
- student performance tables support eventual calibration
- ontology proposal tables support iterative taxonomy refinement

#### Realized generation quality from current seeded DB

Realized generation quality is only moderate today because the seeded data does not fully instantiate the schema.

Main reasons:

- most new ontology fields are not backfilled on the current seeded question bank
- retrieval and embedding continuity is incomplete
- confidence scoring is not informative because the seed values are saturated
- a few seed annotations remain internally contradictory without breaking schema

#### Continuity gap in runtime

The generation/retrieval stack is not yet fully aligned with the database.

Most notably:

- the embedding generator still selects `gp.annotation_confidence` from `question_generation_profiles`
- that field is not present there in the current schema contract
- the embedding path therefore remains partially out of sync with the newer branch design

This means the branch has better generation ontology than it currently has reliable end-to-end operational continuity.

### Question Ontology Assessment

If the goal is the best organizational ontology for SAT-style questions, `backend-alpha-v2` is the best current branch.

Why:

- it preserves the older taxonomy dimensions
- it adds grammar-complexity axes
- it adds writing-style and lexical-complexity axes
- it adds discourse and inference axes
- it adds item-anatomy and distractor-construction axes
- it adds generation targets aligned to those axes
- it adds calibration and proposal workflows to evolve the ontology over time

This is a better foundation than the older MVP line for:

- organizing a question bank
- selecting exemplars for generation
- balancing forms
- auditing gaps
- improving realism of generated items

### Risks and Open Issues

The most important current issues are:

- richer schema than seeded data
- partial script/schema drift in embedding generation
- over-saturated confidence values in seeds
- some annotation inconsistencies that do not break schema but reduce trust in derived analytics

These do not invalidate the branch. They do mean the project should not treat the current seeded DB as a fully mature realization of the ontology yet.

### Recommended Next Actions

1. Fix schema drift in the embedding generation path.
2. Run the planned re-annotation step to populate the newer grammar/style/discourse fields on existing questions.
3. Rebuild and reseed a fresh database from the current branch once the DB-related fixes are complete.
4. Regenerate embeddings only after the richer annotation fields are actually populated.
5. Promote any repeatedly-used `style_profile_jsonb` concepts into normalized columns if they become operational generation constraints.

### Signed Assessment

The project now has a credible generation-oriented ontology, especially for grammar, writing style, and complexity. The remaining work is mostly continuity and backfill, not ontology invention.

Signed: Codex54
