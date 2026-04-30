# CHANGELOG

All significant changes to this project. Timestamps are commit time (PDT, UTC-7).
Agent: **Claude Sonnet 4.6** (`claude-sonnet-4-6`)

---

## 2026-04-29

### Rules — Grammar v7 taxonomy audit and corrections
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Created `rules_agent_dsat_grammar_ingestion_generetion_v7.md` — taxonomy
corrections and additions derived from a cross-referenced audit of the v6
taxonomy against official College Board documentation (Assessment Framework,
Sample Questions PDF, score report skill labels), Khan Academy, The Critical
Reader, PrepScholar, Test Innovators, Albert.io, and released PT1–PT11.

#### Amendment Table

| Amendment | Type | Section | Detail |
|---|---|---|---|
| `skill_family` corrected to official CB names | **Fix** | C.1.3, A.3, B.12 | Replaced non-official values (`Sentence Boundaries`, `Agreement`, `Punctuation`, `Craft and Structure`) with the two official SEC skill names: `Boundaries` and `Form, Structure, and Sense`. All 10 official R&W skill families now enumerated, grouped by domain. |
| `skill_family` example in A.3 schema | **Fix** | A.3 | Example value corrected from `"Agreement"` → `"Form, Structure, and Sense"` |
| `skill_family` in Example A (B.12) | **Fix** | B.12 | Corrected from `"Agreement"` → `"Form, Structure, and Sense"` |
| `stem_type_key` expanded | **Addition** | C.1.2 | Added 5 missing official question types: `choose_words_in_context` (Words in Context — most frequent type, ~28% of section), `choose_cross_text_connection` (Cross-Text Connections), `choose_best_inference` (Inferences), `choose_command_of_evidence_textual` (Command of Evidence textual), `choose_command_of_evidence_quantitative` (Command of Evidence quantitative). Total: 12 → 17 values. Legacy aliases noted for `choose_best_support`, `choose_best_quote`, `choose_best_completion_from_data`. |
| `topic_broad` expanded | **Addition** | C.1.3 | Added `humanities` — official College Board fourth content area alongside Literature, History/Social Studies, and Science. Clarified that `arts`, `economics`, `technology`, `environment` are project-internal sub-tags, not official CB labels. |
| `stimulus_mode_key` descriptions | **Clarification** | C.1.1 | Added inline descriptions for all 8 values. `prose_plus_graph` now lists all confirmed graphic subtypes: bar chart, line graph, scatterplot (with or without line of best fit), pie chart, map. |
| `restatement_clarification` transition | **Addition** | B.5.2 | Added 24th `transition_subtype_key`: `restatement_clarification` — covers "in other words / that is / i.e." transitions that rephrase rather than add or contrast. |
| `adjective_adverb_distinction` promoted | **Promotion** | D.2.5 | Moved from pending (D.2.9) to production under `modifier`. Covers adjective vs. adverb selection after linking verbs ("feel bad" not "feel badly"). Added to D.8.1 role→focus mapping and D.8.3 frequency table at `medium`. |
| `illogical_comparison` promoted | **Promotion** | D.2.5 | Moved from pending (D.2.9) to production under `modifier`. Covers comparing nouns to dissimilar categories ("results of Study 1 were better than Study 2"). Distinct from `comparative_structures` (formal parallelism) — this error is logical. Added to D.8.1 and D.8.3 at `medium`. |
| `commonly_confused_words` promoted | **Promotion** | D.2.8 | Moved from pending (D.2.9) to production under `expression_of_ideas`. Covers non-homophone semantic confusion pairs (affect/effect, allusion/illusion, elicit/illicit, principle/principal). Homophone possession confusion remains under `possessive_contraction`. Added to D.8.3 at `low`. |
| `preposition_idiom` added | **Addition** | D.2.8 | New production focus key under `expression_of_ideas`. Covers verb-preposition and adjective-preposition collocations where the correct preposition is idiomatic (responsible *for*, different *from*, composed *of*, interested *in*). Added to D.8.1 mapping and D.8.3 at `low`. |
| `affirmative_agreement` flagged | **Confidence flag** | D.2.2, D.8.3 | Marked `dsat_confidence: low`. so/neither inversion and tag questions appear primarily in ACT conventions. Retained in taxonomy for completeness but excluded from generation weighting. |
| `negation` flagged | **Confidence flag** | D.2.4, D.8.3 | Marked `dsat_confidence: low`. Double negatives and hardly/scarcely inversions are ACT patterns. Key retained only for scope-of-negation coverage ("not all" vs "all not"); excluded from generation profiles. |
| D.2.9 pending keys updated | **Housekeeping** | D.2.9 | Removed three promoted keys. Only `subjunctive_mood` remains pending (too rare for standalone key; documented as `verb_form` sub-pattern). |
| D.8.1 role→focus mapping updated | **Update** | D.8.1 | `modifier` row extended with `illogical_comparison` and `adjective_adverb_distinction`. `expression_of_ideas` row extended with `commonly_confused_words` and `preposition_idiom`. |
| D.8.2 domain separation table updated | **Update** | D.8.2 | Added official skill family column showing the 10 CB skill names by domain. |
| D.8.3 frequency table updated | **Update** | D.8.3 | New keys placed: `adjective_adverb_distinction` and `illogical_comparison` at `medium`; `commonly_confused_words` and `preposition_idiom` at `low`; `affirmative_agreement` and `negation` marked ⚠️ at `very_low`. |
| `model_version` bumped | **Housekeeping** | A.3, B.12 | All `model_version` fields updated from `rules_agent_v6.0` → `rules_agent_v7.0`. |

**Sources consulted:** College Board Assessment Framework PDF, Digital SAT Sample Questions PDF, Khan Academy DSAT R&W course, The Critical Reader grammar analysis, PrepScholar SAT grammar guide, Test Innovators skill breakdown, Albert.io quantitative evidence review, dsat16.com transitions guide.

---

### Rules — Grammar v6 reorganization and gap fixes
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Created `rules_agent_dsat_grammar_ingestion_generetion_v6.md` — a structural
reorganization of v5 for generation-first LLM navigation.

**Structural changes:**

- Reorganized into five explicit parts: A (Mode Routing) → B (Generation) →
  C (Annotation) → D (Taxonomy Reference) → E (Quality Protocols)
- Generation workflow (Part B) now precedes annotation workflow (Part C)
- §20 megasection decomposed into 15 focused B.x subsections
- §30 (Transition Subtypes) and §31 (Notes Synthesis) integrated inline into
  Part B rather than appended as addenda

**Gaps fixed:**

- Broken `§20.5` reference replaced with two complete inline JSON generation
  examples (B.12): `subject_verb_agreement` medium-difficulty and
  `transition_logic` medium-difficulty
- Missing `classification` schema added to formal schemas (A.3)
- `synthesis_distractor_failure` field name standardized: per-option
  annotation uses `synthesis_distractor_failure` (singular string);
  generation input uses `distractor_synthesis_failures` (plural array)
- Mode-routing section added (A.2) with explicit generation vs annotation
  trigger conditions
- Four proposed focus keys documented with pending status in D.2.9:
  `adjective_adverb_distinction`, `illogical_comparison`,
  `commonly_confused_words`, `subjunctive_mood`
- `transition_subtype_key` vs `target_transition_subtype_key` naming
  clarified in B.5.1: stored annotation field vs generation request field

---

### Rules — CB PT4–PT11 gap analysis and v3.1 / v1.1 rule addenda
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Cross-referenced official College Board answer explanations for Practice Tests 4–11
(sourced from `CB_ANSWERS_QUESTIONS_ANALYSIS.md`) against both production rule files.
Created two new addendum files covering every identified gap.

**Files created:**

- `rules_agent_dsat_grammar_ingestion_generation_v3_1.md`
- `rules_agent_dsat_reading_v1_1.md`

---

**`rules_agent_dsat_grammar_ingestion_generation_v3_1.md`**

*Addendum to `rules_agent_dsat_grammar_ingestion_generation_v3.md`*

- Added punctuation focus key `unnecessary_internal_punctuation` — covers
  absence-of-punctuation cases inside subject–verb, verb–object,
  preposition–complement, and integrated relative clause units (PT4, PT5,
  PT6, PT7, PT9, PT11)
- Added punctuation focus key `end_punctuation_question_statement` — period
  on indirect questions vs question mark on direct questions (PT6, PT11)
- Extended `appositive_punctuation` with three sub-patterns: restrictive
  appositive (no punctuation), title/role before proper name (no punctuation),
  coordinated restrictive appositive (no punctuation) (PT5, PT8, PT9)
- Added three named verb form generation patterns with passage templates and
  distractor constraints: `finite_verb_in_relative_clause`,
  `finite_verb_in_main_clause`, `modal_plus_plain_form` (PT5, PT8, PT9)
- Added `singular_event_reference` pronoun generation pattern — singular
  pronoun referring to a whole preceding clause or event, not a noun (PT5)
- Added `literary_present` to `passage_tense_register_key` — simple present
  when discussing events inside literary works (PT10)
- Added `transition_subtype_key` field with 23 named subtypes covering every
  transition word pattern observed in PT4–PT11; required on generation profiles
  and wrong-option annotations
- Added three metadata fields for notes synthesis generation:
  `synthesis_goal_key` (41 values), `audience_knowledge_key` (3 values),
  `required_content_key` (30 values); added `synthesis_distractor_failure`
  for wrong-option annotation
- Added `test_format_key` field distinguishing `digital_app_adaptive` (27 Qs)
  from `nondigital_linear_accommodation` (33 Qs) with validated
  domain-boundary position bands
- Added 11 grammar-specific `student_failure_mode_key` values
- Added 8 new validator checklist items (checks 18–25)

---

**`rules_agent_dsat_reading_v1_1.md`**

*Addendum to `rules_agent_dsat_reading_v1.md`*

- Added `polarity_fit` Words in Context focus key — for items where a negator
  or concessive ("by no means," "not atypical") reverses required word polarity
  (PT4, PT5, PT6); includes generation rule requiring all four options to
  remain viable after applying the negator
- Added `polarity_mismatch` reasoning trap key
- Added phrase-level WIC generation note — when the correct answer is a
  multi-word phrase, all options must match in length and structure
- Added 12 named functional roles for `sentence_function` items (concession,
  elaboration, contrast_motivation, parenthetical_definition, example,
  consequence, hypothesis, counter_evidence, scope_qualification,
  conventional_approach, obstacle, background_setup); `target_sentence_function_role`
  now required in generation profiles
- Added parenthetical-definition generation constraint — correct answer must
  identify term clarification, not broader passage purpose (PT7, PT11)
- Added 8 named quantitative sub-patterns with primary distractor traps:
  `exact_value_lookup`, `timing_constrained`, `all_measures`, `repeated_highest`,
  `two_variable_opposite`, `composition_change`, `binned_distribution`, `standard`
- Added 5 new quantitative reasoning trap keys: `wrong_row_or_column`,
  `wrong_time_window`, `all_measures_not_checked`, `individual_from_aggregate`,
  `direction_reversal`
- Added all 5 experimental passage architectures:
  `experiment_hypothesis_control_result`, `indirect_effect_mediation`,
  `alternative_explanation_ruled_out`, `mechanism_manipulation_test`,
  `studied_subgroup_generalization_limit`
- Added `study_design_isolation_limit` inference pattern — when passage design
  prevents isolating a causal variable (PT6, PT10)
- Added `subgroup_overgeneralization` inference pattern with generation
  template (PT11)
- Added two-part claim annotation rule for quote-illustration items — at least
  one distractor must satisfy exactly one of two required elements
- Added control-group distractor pattern for experimental architecture items
- Added `confirmation_with_qualification` generation note for cross-text items
- Added 10 new student failure mode keys
- Added 9 new validator checklist items

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
