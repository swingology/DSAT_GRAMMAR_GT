# DSAT Migrations Guide

**42 migrations total** | Applied order: 001 → 042

This guide is organized into three operational domains. Each section covers what the migrations build, what tables and columns the LLM pipeline reads and writes, and how the pieces connect at runtime.

---

## Part 1: Backend Operations

*DB infrastructure, schema fundamentals, security, reporting. No LLM involvement.*

---

### Migrations 001-006 — Core Schema

**`001_006_core_schema.sql`**

The foundation every other migration builds on.

#### Exam hierarchy
```
exams → exam_sections → exam_modules
```
Each module is a 27-question test block. `exam_modules.target_composition_jsonb` (added in 021) stores domain/difficulty distribution targets used by the generation pipeline.

#### Lookup tables (15 in this migration)
Controlled vocabulary for question classification. Every `_key` column on `question_classifications` must be a FK into one of these:

| Table | Purpose |
|---|---|
| `lookup_question_family` | Top-level question type (`vocabulary_in_context`, `rhetorical_synthesis`, `conventions_grammar`, etc.) |
| `lookup_stimulus_mode` | How the question presents stimulus (`prose_single`, `paired`, `notes_bullets`, `prose_plus_table`, `prose_plus_graph`, `sentence_only`) |
| `lookup_stem_type` | Stem format (`complete_the_text`, `choose_best_grammar_revision`, `command`, etc.) |
| `lookup_evidence_scope` | Where evidence lives (within-clause → cross-paragraph) |
| `lookup_evidence_location` | Structural location of key evidence in the passage |
| `lookup_answer_mechanism` | How the student locates the answer |
| `lookup_solver_pattern` | Recommended solution strategy |
| `lookup_distractor_type` | Wrong-answer pattern family |
| `lookup_semantic_relation` | Logical relation between options |
| `lookup_plausibility_source` | Why distractors feel correct |
| `lookup_generation_pattern_family` | Template family for AI generation |
| `lookup_clue_distribution` | Where structural clues are distributed |
| `lookup_hidden_clue_type` | Type of hidden/structural clue |
| `lookup_blank_position` | Syntactic position of the insertion blank |
| `lookup_distractor_subtype` | Fine-grained distractor sub-classification |

#### Core question tables
- **`questions`** — passage text, prompt text, paired passage, source reference, `is_active` flag, `content_origin` (official / ai_human_revised), `tokenization_status` (added 040), `generation_run_id`, `seed_question_id` (added 038)
- **`question_classifications`** — ~50 annotation fields: all FK keys into lookup tables, difficulty rating, IRT b-estimate, style fingerprint dimensions (added across migrations 017-032)
- **`question_options`** — 4 rows per question (A/B/C/D), `is_correct` flag, distractor analysis fields

---

### Migrations 007-013 — Extended Schema

**`007_013_extended_schema.sql`**

Reasoning layer, generation templates, vector embeddings, audit triggers, seed data, flat export view.

#### Tables added
- **`question_reasoning`** — solver steps (jsonb), coaching tip, coaching summary (added 034), common student error, evidence-after-blank flag
- **`question_generation_profiles`** — per-question generation constraints and `target_*` style fields (expanded through migrations 026, 031, 032)
- **`generation_templates`** — reusable LLM prompt templates with `constraint_schema.required` fields; 9 templates seeded by migration 038
- **`question_embeddings`** — `vector(1536)` for semantic similarity search; IVFFlat index; populated by the embeddings pipeline post-approval
- ~~`taxonomy_nodes`, `taxonomy_edges`~~ — taxonomy graph (dropped in 028; classification lives entirely in lookup FKs)

#### Seed data
Migration 007-013 inserts all initial lookup key values. When adding new keys (see 041, 042), use `INSERT … ON CONFLICT DO NOTHING`.

#### View: `question_flat_export`
Denormalized JOIN across questions + classifications + reasoning. For data exports and analysis only, not the ingestion pipeline.

#### Trigger: `set_updated_at()`
Applied to all major tables. Every `UPDATE` auto-stamps `updated_at`. Never write `updated_at` manually.

---

### Migrations 015-016 — Reporting & Security

**`015_reporting_views.sql`** — Aggregation views for admin dashboard (question counts by status, domain, difficulty).

**`016_rls_policies.sql`** — Row-level security. Service-role key bypasses RLS; anon key is read-only on non-staging tables. Ingestion jobs are service-role only.

---

### Migrations 027, 028 — Content Hash + Taxonomy Graph Removal

**`027_content_hash.sql`** — Adds `content_hash` (SHA-256 of passage + prompt text) to `questions` for deduplication during ingestion. The pipeline checks this before inserting.

**`028_drop_taxonomy_graph.sql`** — Drops `taxonomy_nodes`, `taxonomy_edges`, `question_taxonomy_links`. Taxonomy expressed entirely through lookup FKs.

---

### Migrations 029, 032 — Constraints

**`029_taxonomy_constraints.sql`** — Adds FK constraints from `question_classifications` lookup key columns to their respective lookup tables. Without these, Pass 2 can write an invalid key without a DB error.

**`032_schema_constraints_cleanup.sql`** — Tightens NOT NULL and CHECK constraints on core tables. Adds `clause_depth` CHECK (0–4) and validates `nominalization_density`, `sentence_length_profile`, `lexical_density` free-text columns. Safe to re-run.

---

### Migrations 036, 037, 038 — Origin Constraints & Backfills

**`036_source_origin_constraint.sql`** — Adds `source_origin` CHECK constraint on `questions`. Enforces consistency: `source_type = 'generated'` requires `content_origin = 'ai_human_revised'`. Official questions must use `content_origin = 'official'`. Generated questions are never committed to production with `content_origin = 'generated'` — the approval path rewrites this.

**`037_backfill_pre014_columns.sql`** — Backfills columns on questions that pre-date the ingestion pipeline.

**`038_fresh_build_context_reconciliation.sql`** — Schema reconciliation pass after backend rebuild. Adds `content_origin`, `generation_run_id`, `seed_question_id` to `question_ingestion_jobs`. Seeds all 9 generation templates. Adds `annotation_confidence` to `question_generation_profiles`.

---

## Part 2: Ingestion with LLM

*Two-pass pipeline: Extract → Annotate → Validate → Human Review → Approve → Upsert.*

---

### System Architecture (FLOW.md)

```
Frontend (/ingest)
    │  POST /ingest or POST /ingest/file
    ▼
Backend: registers job → returns Job ID immediately (BackgroundTask)
    │
    ▼
Background: Two-Pass LLM Pipeline
    ├── Pass 1: raw text → QuestionExtract JSON
    └── Pass 2: extract → QuestionAnnotation JSON (ontology-constrained)
    │
    ▼
Validator: rejects hallucinated keys, enforces structure
    │
    ▼
Staging: question_ingestion_jobs (status: draft or reviewed)
    │
Frontend (/jobs): human opens job, reads Pass 1 + Pass 2 JSON side-by-side
    ├── PATCH /jobs/{id}/status → "reviewed"
    ├── POST /jobs/{id}/rerun  → re-run LLM passes
    └── PATCH /jobs/{id}/status → "approved"
    │
    ▼
Backend: 5-table atomic upsert → production
    │
    ▼
BackgroundTasks (post-approval):
    ├── fn_refresh_irt_b()              → computes difficulty estimate
    ├── fn_refresh_corpus_fingerprint() → updates v_corpus_fingerprint
    └── generate_coaching_for_question() → writes coaching spans
```

**Key design principle (from LLM Ingestion Plan):** The LLM is a structured annotator, not the final source of truth. It fills in classifications; deterministic code enforces correctness.

---

### Migration 014 — Ingestion Jobs

**`014_question_ingestion_jobs.sql`**

Central staging table for the entire ingestion pipeline.

```
question_ingestion_jobs
  id                      uuid PK
  raw_input_text          text          -- PDF/markdown/text as extracted
  source_label            text          -- filename or label
  input_format            text          -- pdf | markdown | json | text | image | generated
  content_origin          text          -- official | generated
  generation_run_id       uuid          -- FK to generation_runs (generated jobs only)
  seed_question_id        uuid          -- FK to questions (generated jobs only)
  status                  text          -- see flow below
  pass1_json              jsonb         -- QuestionExtract output
  pass2_json              jsonb         -- QuestionAnnotation output
  generation_result_jsonb jsonb         -- per-attempt audit: conformance_report, drift_report, snapshot
  validation_errors_json  jsonb         -- field-level validation failures
  created_at / updated_at
```

**Status flow:**
```
pending
  → extracting        (Pass 1 LLM running)
  → annotating        (Pass 2 LLM running)
  → draft             (both passes done, validation complete)
  → reviewed          (human opened and inspected)
  → approved          (triggers upsert to production tables)
  → rejected          (discarded)
  → failed            (LLM or parse error; rerunable via POST /jobs/{id}/rerun)
  → drift_failed      (generated job: critical dimensions drifted; attempt preserved)
  → conformance_failed (generated job: 3 drift attempts exhausted; terminal)
```

On `approved`: orchestrator calls `upsert.py` → writes to `questions`, `question_classifications`, `question_options`, `question_reasoning`, `question_generation_profiles`.

---

### The Ontology Conformity System (LLM_INGESTION_CONFORMITY.md)

Three components enforce ontology conformity in sequence:

```
DB lookup tables (source of truth)
      ↓
app/prompts/ontology_ref.py    — formats valid values into prompt context at request time
      ↓
app/prompts/pass2_annotation.py — instructs LLM: use only these values; defines output schema
      ↓
LLM response (JSON with _key fields)
      ↓
app/pipeline/validator.py      — checks every _key against DB; rejects hallucinations
```

**`ontology_ref.py`** — Reads `app.state.ontology` (loaded from Supabase at startup) and renders all 37 lookup tables into the Pass 2 system prompt as:
```
field_name: value1 | value2 | value3 | ...
```
Values update automatically when new lookup keys are added via migration — no code change required. The server must restart to pick up new values.

**Validator checks 28 classification FK fields**, 5 per-option fields, and 21 generation profile FK fields. Any hallucinated or invalid key → `validation_failed` status → human reviews `validation_errors_json`. Rerunable via `POST /jobs/{id}/rerun`.

---

### Migrations 017-020 — Complexity, Style & Anatomy Lookups

These add the lookup tables that Pass 2 uses for style fingerprinting. The fingerprint accumulated on official questions becomes the ground truth corpus for the generation quality gate.

#### Syntax & Grammar Structure (017) — `lookup_syntactic_complexity`
16 keys: `simple`, `compound`, `complex`, `compound_complex`, `center_embedded`, `heavily_embedded`, `left_branching`, `interrupted_syntax`, `embedded_relative`, `nominalized`, `inverted_syntax`, `phrasal_dominant`, `clausal_dominant`, `right_branching`, `parallel_structure`, `mixed`

**`lookup_syntactic_interruption`** — 13 keys: `none`, `em_dash`, `paired_em_dash`, `parenthetical`, `appositive`, `non_restrictive_relative`, `absolute_phrase`, `participial_phrase`, `delayed_subject`, `multiple`, `reduced_relative_clause`, `fronted_pp`, `interpolated_attribution`

**`lookup_syntactic_trap`** — 21 keys: `none`, `garden_path`, `nearest_noun_attraction`, `scope_of_negation`, `long_distance_dependency`, `modifier_attachment`, `pronoun_ambiguity`, `multiple`, `agentless_passive`, `full_passive_by_phrase`, `object_relative_clause`, `stacked_pps`, `multiple_negation`, `conditional_stacking`, `long_preverbal_subject`, `tough_movement`, `presupposition_trap`, `temporal_sequence_ambiguity`, `interruption_breaks_sv`, `nominalization_obscures_subject`, `early_clause_anchor`

**`lookup_noun_phrase_complexity`** — 8 keys: `np_simple`, `np_adjective_modified`, `np_noun_premodified`, `np_postmodified_prepphrase`, `np_postmodified_nonfinite`, `np_postmodified_relative`, `np_stacked_premodifiers`, `np_multiply_postmodified`

**`lookup_inference_distance`** — 6 keys: `within_clause`, `within_sentence`, `adjacent_sentences`, `paragraph_level`, `cross_paragraph`, `unstated_inference`

Free-form columns (CHECK constraint, not lookup FK): `clause_depth` (int 0-4), `nominalization_density` (low/medium/high), `sentence_length_profile` (short/medium/long/mixed), `lexical_density` (low/medium/high)

#### Vocabulary & Lexical (018)

**`lookup_lexical_tier`** — 6 keys: `general`, `mixed`, `academic`, `domain_specific`, `low_frequency`, `archaic_or_literary`

**`lookup_vocabulary_profile`** — 7 keys: `high_freq_dominant`, `mixed`, `awl_heavy`, `low_freq_heavy`, `domain_specific_heavy`, `high_ttr`, `archaic_or_literary`

#### Discourse & Rhetorical Structure (018-019)

**`lookup_rhetorical_structure`** — 11 keys: `claim_evidence`, `problem_solution`, `compare_contrast`, `cause_effect`, `definition_expansion`, `narrative_sequence`, `concession_rebuttal`, `classification_division`, `extended_analogy`, `description_elaboration`, `mixed`

**`lookup_cohesion_device`** — 8 keys: `lexical_repetition`, `pronoun_chain`, `conjunctive_adverb`, `transitional_phrase`, `ellipsis`, `substitution`, `mixed`, `none`

**`lookup_epistemic_stance`** — 7 keys: `assertive`, `hedged`, `speculative`, `tentative`, `evaluative`, `imperative`, `mixed`

**`lookup_transitional_logic`** — 10 keys: `additive`, `adversative`, `causal`, `concessive`, `temporal`, `exemplification`, `summative`, `clarification`, `conditional`, `none`

**`lookup_evidence_distribution`** — 12 keys: `single_sentence`, `adjacent_sentences`, `front_loaded`, `center_loaded`, `end_loaded`, `distributed`, `sandwich_structure`, `cross_paragraph`, `embedded_in_example`, `visual_data`, `contrapositive`, `suspended_disclosure`

**`lookup_reasoning_demand`** — 6 keys: `literal_retrieval`, `paraphrase`, `local_inference`, `global_inference`, `synthesis`, `evaluation`

**`lookup_evidence_mode`** — 5 keys: `direct`, `indirect`, `implicit`, `contrastive`, `quantitative`

**`lookup_reading_scope`** — 3 keys: `local`, `extended`, `global`

#### Prose Style & Register (020, 024)

**`lookup_prose_register`** — 6 keys: `formal_academic`, `semi_formal_narrative`, `technical_scientific`, `archaic_elevated`, `journalistic_analytical`, `literary_narrative`

**`lookup_prose_tone`** — 8 keys: `analytical`, `narrative`, `persuasive`, `expository`, `descriptive`, `reflective`, `critical`, `mixed`

**`lookup_passage_source_type`** — 7 keys: `academic_journal`, `scientific_report`, `textbook_reference`, `literary_fiction`, `primary_document`, `memoir_personal_essay`, `journalism_analysis`. This is the **most powerful single generation constraint** — `academic_journal` carries an implicit bundle (formal register, hedged assertions, AWL vocabulary, heavy NP complexity) that a generation model already knows.

Free-form columns (CHECK constraint): `narrator_perspective_key` (first_person/third_person/institutional/impersonal), `passage_era_key` (contemporary/modern/historical/timeless), `passage_word_count_band` (very_short/short/medium/long/very_long)

**`craft_signals_array`** — `text[]` allowlist-validated (not FK): `concession`, `qualification`, `irony`, `understatement`, `analogy`, `antithesis`, `exemplification`, `hedged_assertion`

#### Item Anatomy (020)
Adds `grammar_role_key` → `lookup_grammar_role` and `grammar_focus_key` → `lookup_grammar_focus` to `question_classifications`. Also adds passage fingerprint columns: `passage_word_count`, `passage_sentence_count`, `passage_avg_sentence_length`. Table/graph data columns: `table_data_jsonb`, `graph_data_jsonb`, `notes_bullets_jsonb`.

---

### Grammar Focus Lookup: Complete Key Set (Migrations 020, 041, 042)

Maps directly to `DSAT_Grammar_Rules_Complete.md` and `DSAT_Verbal_Master_Taxonomy_v2.md`. Applied at Pass 2 annotation time.

| Key | Grammar Rule |
|---|---|
| `sentence_boundaries` | Part 1: fragments, run-ons, comma splices |
| `subject_verb_agreement` | Part 2.1: simple, intervening phrases, compound, indefinite pronouns, collective nouns, inverted order |
| `pronoun_antecedent` | Part 2.2: number agreement with antecedent |
| `pronoun_case` | Part 2.3: subjective/objective/possessive; who vs. whom |
| `tense_consistency` | Part 3.1: consistent tense within passage context |
| `present_past_perfect` | Part 3.2: has/have + past participle vs. had + past participle |
| `subjunctive_mood` | Part 3.3: contrary-to-fact conditions, demands/requirements |
| `verb_form` | Part 3.4: past participle vs. past tense, irregular forms |
| `misplaced_modifier` | Part 4.1: modifier placement relative to modified noun |
| `dangling_modifier` | Part 4.2: opening phrase must modify the grammatical subject |
| `comparative_superlative` | Part 4.3: -er/-est, double comparatives, illogical comparisons |
| `parallel_structure` | Part 5: parallel items in lists and correlative conjunctions |
| `punctuation_comma` | Part 6: introductory elements, series, nonrestrictive |
| `punctuation_semicolon` | Part 6: joining independent clauses |
| `punctuation_colon` | Part 6: introducing lists/explanations |
| `punctuation_dash` | Part 6: parenthetical, list introduction |
| `punctuation_apostrophe` | Part 6: possessive vs. contraction |
| `voice_active_passive` | Active vs. passive voice (041) |
| `logical_predication` | Predicate logically matches subject (041) |
| `conjunction_usage` | Coordinating vs. subordinating conjunction choice (041) |
| `comparative_structures` | Illogical comparisons: "more X than any other" (041) |
| `noun_countability` | Count vs. non-count nouns (041) |
| `affirmative_agreement` | Double negatives and affirmative phrasing (041) |
| `elliptical_constructions` | Omitted but understood verbs in comparisons (041) |
| `negation` | Scope and placement of negation (041) |
| `relative_pronouns` | Who/which/that; restrictive vs. non-restrictive (042) |
| `possessive_contraction` | its/it's, their/they're, whose/who's (042) |
| `hyphen_usage` | Compound modifiers before vs. after noun (042) |

**Disambiguation priority** (applied when multiple rules could fit, from `ingestion_rules_workflow.md`):

1. `sentence_boundary` > `punctuation` — structural issues take precedence
2. `voice_active_passive` > `verb_form`
3. `logical_predication` > `modifier_placement`
4. `conjunction_usage` > `parallel_structure`
5. `pronoun_case` > `pronoun_antecedent`
6. `comparative_structures` > `modifier_placement`
7. `noun_countability` > `subject_verb_agreement`
8. `negation` > `verb_form`
9. `relative_pronouns` > `modifier_placement`
10. `possessive_contraction` > `punctuation_apostrophe`
11. `hyphen_usage` > `punctuation`

---

### Pass 2: What the LLM Classifies for SEC Questions

For any `domain_key = 'standard_english_conventions'` question:

1. Identify the grammar rule being tested
2. Select `grammar_role_key` from 7 allowed values: `sentence_boundary`, `agreement`, `verb_form`, `modifier`, `punctuation`, `parallel_structure`, `pronoun`
3. Select `grammar_focus_key` from the 27-key list above using disambiguation priority
4. Verify `grammar_role_key` and `grammar_focus_key` are consistent (validator enforces this cross-field check)
5. SEC questions must have `grammar_role_key` populated — validator rejects null for SEC domain

If the question reveals a pattern not covered by the taxonomy: classify with closest matching rule, add `amendment_proposal` to the reasoning section, set `annotation_confidence = "low"`. Proposals are reviewed quarterly and, if approved, trigger a new lookup migration.

---

### Migrations 022-025 — Supporting Infrastructure

**`022_student_performance.sql`** — `question_student_attempts` for real student response tracking. Used to calibrate IRT b-estimates empirically when `n > 500` per item. Not written by LLM pipeline.

**`023_ontology_proposals.sql`** — `ontology_proposals` table: LLM or human can flag missing lookup keys for admin review before a new migration is created.

**`024_style_composition.sql`** — `lookup_craft_signal`, `lookup_passage_source_type`.

**`025_consolidation.sql`** — Adds missing FK columns to `question_classifications` for lookup tables introduced in 017-024.

---

### Migrations 026, 030, 031 — Generation Profile Gap Fills

These add `target_*` mirror columns to `question_generation_profiles` so style fingerprint dimensions collected during ingestion can be used as generation constraints:

| Migration | Columns added to `question_generation_profiles` |
|---|---|
| 026 | `target_syntactic_interruption_key`, `target_syntactic_trap_key`, `target_clause_depth_min/max`, `target_nominalization_density`, `target_lexical_density`, `target_distractor_construction_key`, `target_distractor_difficulty_spread`, `target_prose_register_key`, `target_prose_tone_key`, `target_rhetorical_structure_key`, `target_syntactic_complexity_key`, `target_lexical_tier_key` |
| 030 | Additional lookup keys discovered during initial annotation pass |
| 031 | `target_noun_phrase_complexity_key`, `target_evidence_distribution_key`, `target_sentence_length_profile`, `target_vocabulary_profile_key`, `target_passage_source_type_key` |

---

### Migration 034 — Coaching Annotations

**`034_coaching_annotations.sql`**

Span-level coaching layer. Written by the coaching LLM pass after a question is approved to production.

#### `lookup_coaching_annotation_type`
| Key | UI Color | Purpose |
|---|---|---|
| `syntactic_trap` | red | Structural feature causing misreads |
| `key_evidence` | green | Answer anchor in passage |
| `np_cluster` | blue | Dense noun phrase to unpack |
| `clause_boundary` | purple | Where clause ends/begins (SEC questions) |
| `blank_context` | yellow | Text around the blank |
| `distractor_lure` | orange | Text making wrong answer tempting |
| `rhetorical_move` | teal | Structural pivot in argument |

#### `question_coaching_annotations` — one row per highlighted span
- `span_field`: `passage_text | prompt_text | paired_passage_text`
- `span_start_char`, `span_end_char` — zero-indexed half-open char offsets (primary)
- `span_sentence_index` — fallback when text edits invalidate char offsets
- `annotation_type` → FK into `lookup_coaching_annotation_type`
- `show_condition`: `always | on_error | on_request`

#### Column added to `question_reasoning`
- `coaching_summary` — 2–4 sentence explanation of why the question is hard and the recommended approach

#### View: `v_coaching_panel`
Returns all coaching data for a question in one fetch. App groups by `question_id` after fetch.

---

### Migrations 039-042 — Grammar Tokenization

**`039_grammar_keys_token_annotations.sql`** — Grammar highlighting infrastructure.

- **`grammar_keys`** — registry of grammar concepts with visual styling: `key`, `display_name`, `color_hex`, `bg_light_hex`, `bg_dark_hex`, `sat_rule_short`, `sat_rule_detail`. Initial keys: `subordinate_clause`, `subject`, `main_verb`, `relative_clause`, `subordinating_conj`, `modifier`

- **`question_token_annotations`** — one row per token: `question_id`, `token_index`, `token_text`, `grammar_tags text[]`, `is_blank bool`. Written by Pass 3. `grammar_tags` is an array of `grammar_keys.key` values — tokens can have multiple tags.

**`040_tokenization_status.sql`** — Adds `tokenization_status` (`pending | ready | failed`) to `questions`. Set to `ready` after Pass 3 completes. The practice endpoint returns this field so the frontend knows when token annotations are available.

**`041_new_grammar_focus_categories.sql`** — 8 new `lookup_grammar_focus` keys (voice through negation, sort 140-210).

**`042_additional_grammar_focus_categories.sql`** — 3 final `lookup_grammar_focus` keys (relative_pronouns, possessive_contraction, hyphen_usage, sort 220-240).

---

### Pass 1 → Pass 2 → Validation: What the LLM Writes

**Pass 1 output** (stored in `question_ingestion_jobs.pass1_json`, `QuestionExtract` model):
```json
{
  "stem": "...",
  "passage": "... | null",
  "choices": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "correct_option_label": "A | B | C | D",
  "stimulus_mode_key": "<valid key>",
  "stem_type_key": "<valid key>",
  "source_exam_code": "...",
  "source_module_code": "...",
  "source_question_number": "..."
}
```

**Pass 2 output** (stored in `question_ingestion_jobs.pass2_json`, `QuestionAnnotation` model). Critical FK fields the LLM must fill with valid lookup keys:
```
grammar_focus_key           → lookup_grammar_focus
grammar_role_key            → lookup_grammar_role
syntactic_complexity_key    → lookup_syntactic_complexity
syntactic_trap_key          → lookup_syntactic_trap
inference_distance_key      → lookup_inference_distance
evidence_distribution_key   → lookup_evidence_distribution
lexical_tier_key            → lookup_lexical_tier
noun_phrase_complexity_key  → lookup_noun_phrase_complexity
solver_pattern_key          → lookup_solver_pattern
distractor_type_key         → lookup_distractor_type
prose_register_key          → lookup_prose_register
prose_tone_key              → lookup_prose_tone
passage_source_type_key     → lookup_passage_source_type
rhetorical_structure_key    → lookup_rhetorical_structure
epistemic_stance_key        → lookup_epistemic_stance
```

Special rules:
- `irt_b_estimate` and `irt_b_source`: always output `null` — the DB computes this from classification dimensions via `fn_compute_irt_b_v1()`; the LLM never produces a number
- Prose grammar/style fields describe the PASSAGE, not the stem — set to `null` for sentence-only SEC questions
- `hidden_clue_type_key`: use `"none"` when absent (not `null`) to make absence explicit
- Generated jobs: `source_exam_code`, `source_module_code`, `source_question_number` are null by design — validator skips these checks when `content_origin = 'generated'`

**Pass 3 output** (tokenization): rows written to `question_token_annotations`. `grammar_tags` must be valid `grammar_keys.key` values. Sets `questions.tokenization_status = 'ready'`.

---

## Part 3: Question Generation with LLM

*Lifecycle: Build run → Select seeds → Generate → Detect drift → Gate on corpus conformance → Human review → Approve → Post-approval hooks.*

---

### Migration 021 — Generation Lifecycle

**`021_generation_lifecycle.sql`**

Core generation infrastructure.

#### `generation_runs`
One row per LLM generation batch:
```
id, template_id, model_name, model_params jsonb,
seed_question_ids uuid[],    -- official questions used as exemplars
target_constraints jsonb,    -- full constraint spec sent to LLM
item_count,                  -- how many items requested
status: running | complete | partial_complete | failed | cancelled
```

`target_constraints` JSON groups constraints by linguistic category:
```json
{
  "PASSAGE STYLE":       { "target_passage_source_type_key": "academic_journal", "target_prose_register_key": "formal_academic" },
  "SYNTACTIC STRUCTURE": { "target_syntactic_complexity_key": "complex", "target_syntactic_trap_key": "nearest_noun_attraction" },
  "LEXICAL PROFILE":     { "target_lexical_tier_key": "academic", "target_lexile_min": 1100, "target_lexile_max": 1400 },
  "DISCOURSE & RHETORIC":{ "target_rhetorical_structure_key": "claim_evidence", "target_inference_distance_key": "cross_paragraph" },
  "ITEM MECHANICS":      { "target_difficulty_overall": "hard", "target_blank_position_key": "subject" },
  "GRAMMAR (SEC)":       { "target_grammar_focus_key": "subject_verb_agreement", "target_grammar_role_key": "agreement" },
  "DISTRACTOR DESIGN":   { "target_distractor_construction_key": "nearest_noun_lure" }
}
```
Grouped layout is intentional — LLMs process grouped information more reliably than a flat list. Omit any group with no populated constraints.

#### `generated_questions` (post-approval only)
```
id, run_id, question_id, seed_question_id,
generation_rank,              -- model confidence rank within run
review_status: unreviewed | approved | rejected | needs_revision,
realism_score numeric(3,2),   -- 0.0 to 1.0 (human-assigned at review)
generation_params_snapshot_jsonb,  -- immutable copy of generation_result_jsonb at approval time
generation_model_name, generation_provider
```

**Key constraint:** A generated question cannot be used as a seed for further generation until `review_status = 'approved'`.

#### IRT columns on `question_classifications`
- `irt_b_estimate numeric(4,2)` — difficulty on IRT scale, range [−3, +3], hard ceiling ±4
- `irt_b_source text` — `human_estimate | model_estimate | field_test`

#### `exam_modules.target_composition_jsonb`
```json
{
  "domain_targets": {
    "Standard English Conventions": { "min": 10, "max": 12 }
  },
  "difficulty_distribution": { "easy": 0.33, "medium": 0.34, "hard": 0.33 },
  "grammar_focus_distribution": { "subject_verb_agreement": 3, "sentence_boundaries": 2 }
}
```

#### View: `v_generation_run_summary`
Per-run stats: requested, stored, approved, rejected, needs_revision, unreviewed, avg_realism_score.

---

### Migration 033 — IRT B Rubric

**`033_irt_b_rubric.sql`**

**Design principle:** The LLM classifies linguistic dimensions during Pass 2. The DB computes the IRT b-estimate from those classifications using a fixed formula — never asking the LLM to produce a number directly. Consistent across all LLM providers.

#### `fn_compute_irt_b_v1(question_id uuid) → numeric(4,2)`

| Dimension | Weight | Scale |
|---|---|---|
| `inference_distance_key` | 0.30 | 1-6 (within_clause=1 … unstated_inference=6) |
| `evidence_distribution_key` | 0.20 | 1-6 (single_sentence=1 … suspended_disclosure=6) |
| `syntactic_complexity_key` | 0.20 | 1-5 (simple=1 … center_embedded=5) |
| `lexical_tier_key` | 0.15 | 1-5 (general=1 … archaic_or_literary=5) |
| `syntactic_trap_key` | 0.10 | 0-3 (none=0, named trap=2, multiple=3) |
| `noun_phrase_complexity_key` | 0.05 | 1-6 (np_simple=1 … np_multiply_postmodified=6) |

Formula: `b = (raw − 3.125) / 2.225 × 3`, clamped to [−3, +3].

#### `fn_refresh_irt_b(question_id uuid DEFAULT NULL) → int`
Only overwrites `irt_b_rubric_version IN ('v1', NULL)`. Never touches `'empirical'` or `'manual'` rows.
```sql
SELECT fn_refresh_irt_b();             -- full corpus
SELECT fn_refresh_irt_b('<uuid>');     -- single question
```

`irt_b_rubric_version`: `v1` (computed) | `empirical` (n>500 real student data) | `manual` (human-assigned)

---

### Migration 035 — Generation Traceability

**`035_generated_questions_traceability.sql`**

Columns added to `generated_questions`:
- `generation_params_snapshot_jsonb` — immutable snapshot of all `target_*` params at generation time; never updated after write
- `generation_model_name`, `generation_provider` — item-level model attribution (covers multi-provider runs)

#### View: `v_generation_traceability`
Surfaces `difficulty_drifted` and `syntax_drifted` flags by comparing snapshot targets against the approved question's actual classification. Used for post-approval prompt calibration.

---

### Migration 042 — Corpus Fingerprint (Generation Quality Gate)

**Planned migration** (`042_corpus_fingerprint.sql`) — extends the status constraints and adds the corpus-grounded conformance infrastructure.

#### Status constraint extensions
```sql
-- question_ingestion_jobs: adds drift_failed, conformance_failed
-- generation_runs: adds partial_complete
```

#### `generation_result_jsonb` on `question_ingestion_jobs`
Written for every generation attempt, including `drift_failed` and `conformance_failed` rows — the audit trail that enables prompt calibration:
```json
{
  "attempt_number": 1,
  "drift_report": { "critical_drifts": [...], "soft_drifts": [...], "is_critical": false },
  "conformance_report": { "critical_misses": [...], "corpus_n": 42, "is_conformant": true },
  "model_name": "claude-sonnet-4-6",
  "provider": "anthropic",
  "seed_question_id": "<uuid>",
  "target_constraints_snapshot": { ... }
}
```

At approval time, `upsert.py` copies this into `generated_questions.generation_params_snapshot_jsonb`.

#### Materialized view: `v_corpus_fingerprint`
Aggregates the style fingerprint of all approved official questions per question family:
```sql
SELECT question_family_key, syntactic_complexity_key, prose_register_key,
       lexical_tier_key, rhetorical_structure_key, epistemic_stance_key,
       difficulty_overall, evidence_distribution_key, inference_distance_key,
       blank_position_key, grammar_focus_key, grammar_role_key,
       COUNT(*) AS n, AVG(irt_b_estimate) AS mean_irt_b
FROM question_classifications
JOIN questions ON questions.id = question_classifications.question_id
WHERE is_active = TRUE AND (content_origin IS NULL OR content_origin = 'official')
GROUP BY ... ;
```

Filter: `is_active=TRUE + content_origin='official'`. Questions has no `review_status` column — it lives on `generated_questions`.

#### `fn_refresh_corpus_fingerprint() → void`
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY public.v_corpus_fingerprint;
```
Called from the app layer only — no DB trigger. Called once per approval in `routers/jobs.py`. If concurrent approvals cause `LockNotAvailableError`, the app layer retries once after 200ms or logs-and-skips.

---

### The Corpus Conformance Quality Gate (TASKS_GEN_PIPELINE.md)

**The problem with a subjective LLM realism judge:** Shared blind spots between generator and judge, no calibration baseline, not auditable ("realism_score: 0.82" is uninterpretable).

**The solution:** The ingested official College Board questions are the ground truth. Pass 2 runs the same annotation schema on both official and generated questions — official fingerprints become the measurement standard.

#### How it works at runtime

```
Official CB question ingested
    → Pass 2 annotation runs → fingerprint written to question_classifications
    → Human approves
    → fn_refresh_corpus_fingerprint() called → v_corpus_fingerprint updated

Generated question produced
    → Pass 1 generates text
    → Pass 2 annotation runs (same prompt, same schema)
    → corpus_conformance_score() called:
        for each CRITICAL dimension:
            is the annotated value in the top-3 modal values
            for this question family in the approved corpus?
    → All critical dimensions conform → stage for human review
    → Any critical dimension misses → mark drift_failed, retry (max 3 attempts)
    → Attempt 3 failure → mark conformance_failed, log explanation
```

#### Critical vs. soft dimensions

**Critical for all families** (must conform or trigger rerun):
```python
CRITICAL_DIMENSIONS = {
    "target_difficulty_overall",
    "target_syntactic_complexity_key",
    "target_prose_register_key",
    "target_epistemic_stance_key",
    "target_rhetorical_structure_key",
    "target_evidence_distribution_key",
    "target_inference_distance_key",
    "target_blank_position_key",
}
```

**Critical only for `conventions_grammar` family** (merged into critical set for SEC jobs):
```python
SEC_CRITICAL_DIMENSIONS = {
    "target_grammar_focus_key",   # the tested rule — most important for SEC conformance
    "target_grammar_role_key",
}
```

**Soft** (logged but not rejected):
```python
SOFT_DIMENSIONS = {
    "target_lexical_tier_key",
    "target_passage_source_type_key",
    "target_narrator_perspective_key",
}
```

#### Graceful degradation
When a question family has fewer than 5 approved official questions in the corpus, the conformance gate is bypassed — not enough ground truth yet. Drift detection against the original target constraints still applies. A warning is returned by `POST /generate` as `warning: "corpus_too_small"`.

**Bootstrap requirement:** Ingest at least 5 approved official questions per family before generating for that family.

---

### Drift Detection (pipeline/drift.py)

Runs after Pass 2 annotates a generated job. Compares the annotated classification against the `target_constraints` snapshot that was sent to the LLM.

```python
@dataclass
class DriftReport:
    critical_drifts: list[str]   # dimension names where expected != actual
    soft_drifts: list[str]
    is_critical: bool            # True if any critical dimension drifted
    summary: str                 # stored in generation_result_jsonb

@dataclass
class ConformanceReport:
    critical_misses: list[str]   # dimensions out of corpus norms
    soft_misses: list[str]
    corpus_n: int
    is_conformant: bool
    explanation: str             # stored in generation_result_jsonb
```

Rerun decision: `should_rerun = (report.is_critical OR NOT conformance.is_conformant) AND attempt < 3`

Drift-failed job rows are **never deleted** — preserved with `status='drift_failed'` for prompt calibration analysis via `GET /generate/runs/{run_id}/drift`.

---

### Generation Pipeline Flow

```
POST /generate → create generation_run → BackgroundTask
    │
    ▼
For each item (max 20 per run):
    │
    ├─ select_seed_question() — vector similarity search on question_embeddings
    │  (taxonomy_summary embedding type; round-robin fallback if no embeddings)
    │
    ├─ Build prompt: system (template skeleton) + user (exemplar + grouped constraints + IRT anchor)
    │
    ├─ Attempt loop (max 3 DRIFT attempts; LLM API errors retry separately with backoff):
    │   ├─ LLM call (temperature=0.7) → raw JSON
    │   ├─ INSERT question_ingestion_jobs:
    │   │     content_origin='generated', input_format='generated'
    │   │     pass1_json=<LLM output>, status='annotating' (skip extraction)
    │   │     generation_run_id, seed_question_id set
    │   ├─ process_job() starting at Pass 2 (Pass 1 already in pass1_json)
    │   ├─ detect_drift() → DriftReport
    │   ├─ corpus_conformance_score() → ConformanceReport
    │   ├─ Write generation_result_jsonb to staging job row
    │   └─ If drift/conformance fail and attempt < 3:
    │         mark current job drift_failed (preserve row), create new job, retry
    │
    └─ Final run status: complete | partial_complete | failed

POST /jobs/{id}/status → "approved" (for generated job):
    ├─ SYNCHRONOUS: rewrite content_origin → 'ai_human_revised' before upsert
    │  (migration 036 forbids 'generated' on production questions table)
    ├─ 5-table upsert to production tables
    ├─ BackgroundTask: fn_refresh_irt_b('<question_id>')
    ├─ BackgroundTask: fn_refresh_corpus_fingerprint()
    └─ BackgroundTask: generate_coaching_for_question()
```

**Seed dimension inheritance:** Only explicitly specified `target_*` values from the run request override the seed's generation profile. Unspecified dimensions remain unset — not silently inherited from the seed. This prevents hidden seed-trait bleed-through.

---

### Coaching Pipeline (pipeline/coaching.py + prompts/coaching.py)

Called as BackgroundTask after approval.

1. Load `passage_text`, `stem_text`, `question_options`, `correct_option_label`, existing `question_classifications`
2. LLM call (temperature=0.2) → returns 3-5 span annotations + `coaching_summary`
3. For each annotation: `_find_span()` locates `span_text` in the field to compute `span_start_char`, `span_end_char`, `span_sentence_index` (whitespace-normalized matching; returns `(None, None, None)` on miss — fallback to sentence index in UI)
4. Write rows to `question_coaching_annotations`
5. Write `coaching_summary` to `question_reasoning.coaching_summary`

Coaching LLM output contract:
```json
{
  "annotations": [{
    "span_field": "passage_text | prompt_text | paired_passage_text",
    "span_text": "<exact substring>",
    "annotation_type": "<key from lookup_coaching_annotation_type>",
    "label": "<short UI label>",
    "coaching_note": "<1-3 sentences>",
    "show_condition": "always | on_error | on_request"
  }],
  "coaching_summary": "<2-4 sentences: why hard and how to solve>"
}
```

---

### Generation API Endpoints

| Method | Path | Notes |
|---|---|---|
| `POST` | `/generate` | Start run; returns `run_id` + optional `warning: "corpus_too_small"` |
| `GET` | `/generate/runs` | List runs (filter by status) |
| `GET` | `/generate/runs/{run_id}` | Run detail |
| `GET` | `/generate/runs/{run_id}/questions` | Post-approval generated questions |
| `GET` | `/generate/runs/{run_id}/jobs` | All staging job rows for run (pre-approval; includes drift_failed rows) |
| `GET` | `/generate/templates` | Active templates with `constraint_schema` |
| `PATCH` | `/generate/questions/{id}/status` | Review an already-approved generated question |
| `GET` | `/generate/runs/{run_id}/drift` | Drift + conformance report (dual-source: staging jobs + v_generation_traceability) |

---

## Quick Reference: LLM Pipeline → DB Mapping

| Pass | Writes to | What |
|---|---|---|
| Pass 1 | `question_ingestion_jobs.pass1_json` | Stem, passage, choices, correct answer, stimulus/stem type |
| Pass 2 | `question_ingestion_jobs.pass2_json` | All classification FKs, per-option distractor analysis, generation profile targets |
| Validation | `question_ingestion_jobs.validation_errors_json` | Field-level errors if any FK is invalid |
| Pass 3 (tokenize) | `question_token_annotations`, `questions.tokenization_status` | Token-level grammar tags |
| Approval upsert | `questions`, `question_classifications`, `question_options`, `question_reasoning`, `question_generation_profiles` | All production data |
| Post-approval IRT | `question_classifications.irt_b_estimate` | Computed from Pass 2 dims, not LLM output |
| Post-approval corpus | `v_corpus_fingerprint` | Refreshed via fn_refresh_corpus_fingerprint() |
| Post-approval coaching | `question_coaching_annotations`, `question_reasoning.coaching_summary` | Span-level coaching |

---

## Migration Run Order

Apply strictly in filename order. Each migration uses `IF NOT EXISTS` / `ON CONFLICT DO NOTHING`.

```
001_006_core_schema.sql
007_013_extended_schema.sql
014_question_ingestion_jobs.sql
015_reporting_views.sql
016_rls_policies.sql
017_prose_grammar_complexity.sql
018_writing_style_complexity.sql
019_discourse_generation_factors.sql
020_item_anatomy_passage_fingerprint.sql
021_generation_lifecycle.sql
022_student_performance.sql
023_ontology_proposals.sql
024_style_composition.sql
025_consolidation.sql
026_generation_profile_style_gaps.sql
027_content_hash.sql
028_drop_taxonomy_graph.sql
029_taxonomy_constraints.sql
030_fix_gaps.sql
031_generation_profile_gaps.sql
032_schema_constraints_cleanup.sql
033_irt_b_rubric.sql
034_coaching_annotations.sql
035_generated_questions_traceability.sql
036_source_origin_constraint.sql
037_backfill_pre014_columns.sql
038_fresh_build_context_reconciliation.sql
039_grammar_keys_token_annotations.sql
040_tokenization_status.sql
041_new_grammar_focus_categories.sql
042_additional_grammar_focus_categories.sql
```

After applying all migrations, restart the backend so `app.state.ontology` picks up any new lookup values before the next ingestion run.
