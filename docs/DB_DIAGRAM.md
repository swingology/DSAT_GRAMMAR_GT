# DSAT Grammar Database — Schema Diagram (LLM-Readable)

## ENUM Types

```sql
CREATE TYPE content_origin_enum AS ENUM ('official', 'unofficial', 'generated');
CREATE TYPE job_type_enum AS ENUM ('ingest', 'generate', 'reannotate', 'overlap_check');
CREATE TYPE job_status_enum AS ENUM ('pending', 'parsing', 'extracting', 'generating', 'annotating', 'overlap_checking', 'validating', 'approved', 'needs_review', 'failed');
CREATE TYPE practice_status_enum AS ENUM ('draft', 'active', 'retired');
CREATE TYPE overlap_status_enum AS ENUM ('none', 'possible', 'confirmed');
CREATE TYPE relation_type_enum AS ENUM ('overlaps_official', 'derived_from', 'near_duplicate', 'generated_from', 'adapted_from');
CREATE TYPE asset_type_enum AS ENUM ('pdf', 'image', 'screenshot', 'markdown', 'json', 'text');
CREATE TYPE change_source_enum AS ENUM ('ingest', 'generate', 'admin_edit', 'reprocess');
```

---

## Table: users

Core user table for the practice system (Segment B). Simple integer PK, no UUID.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | INTEGER | PK, INDEX | Auto-increment |
| username | VARCHAR(100) | NOT NULL, UNIQUE, INDEX | Display name |
| created_at | TIMESTAMPTZ | | Default: now() |

**Relationships:**
- `users.id` <-- `user_progress.user_id` (one-to-many)

---

## Table: questions

Central table — every question lives here regardless of origin (official/unofficial/generated).

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | Default: gen_random_uuid() |
| content_origin | content_origin_enum | NOT NULL | 'official', 'unofficial', or 'generated' |
| source_exam_code | VARCHAR(20) | | e.g. 'PT4', 'PT5' |
| source_module_code | VARCHAR(10) | | e.g. 'M1', 'M2' |
| source_question_number | INTEGER | | Position in exam |
| stimulus_mode_key | VARCHAR(30) | | See ontology for allowed values |
| stem_type_key | VARCHAR(40) | | See ontology for allowed values |
| current_question_text | TEXT | NOT NULL | The question stem |
| current_passage_text | TEXT | | The reading passage (nullable for sentence-only) |
| current_correct_option_label | VARCHAR(1) | NOT NULL | 'A', 'B', 'C', or 'D' |
| current_explanation_text | TEXT | | Short explanation for students |
| practice_status | practice_status_enum | NOT NULL, DEFAULT 'draft' | 'draft' -> 'active' -> 'retired' |
| official_overlap_status | overlap_status_enum | NOT NULL, DEFAULT 'none' | 'none', 'possible', 'confirmed' |
| canonical_official_question_id | UUID | FK -> questions.id | Links generated questions to source |
| derived_from_question_id | UUID | FK -> questions.id | Lineage tracking |
| generation_source_set | JSONB | | Spec used to generate this question |
| is_admin_edited | BOOLEAN | NOT NULL, DEFAULT false | |
| metadata_managed_by_llm | BOOLEAN | NOT NULL, DEFAULT true | |
| latest_annotation_id | UUID | FK -> question_annotations.id | Denormalized pointer |
| latest_version_id | UUID | FK -> question_versions.id | Denormalized pointer |
| created_at | TIMESTAMPTZ | | Default: now() |
| updated_at | TIMESTAMPTZ | | Default: now(), on update: now() |

**Relationships:**
- `questions.id` <-- `question_jobs.question_id`
- `questions.id` <-- `question_versions.question_id`
- `questions.id` <-- `question_annotations.question_id`
- `questions.id` <-- `question_options.question_id`
- `questions.id` <-- `question_assets.question_id`
- `questions.id` <-- `user_progress.question_id`
- `questions.id` <-- `llm_evaluations.question_id`
- `questions.id` <-- `question_relations.from_question_id`
- `questions.id` <-- `question_relations.to_question_id`
- `questions.canonical_official_question_id` --> `questions.id` (self-ref)
- `questions.derived_from_question_id` --> `questions.id` (self-ref)

---

## Table: question_versions

Audit trail for every edit to a question. Created on ingest, admin edit, or reprocess.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | |
| question_id | UUID | FK, NOT NULL | -> questions.id |
| version_number | INTEGER | NOT NULL | Increments per question |
| change_source | change_source_enum | NOT NULL | 'ingest', 'generate', 'admin_edit', 'reprocess' |
| question_text | TEXT | NOT NULL | Snapshot of stem at this version |
| passage_text | TEXT | | Snapshot of passage |
| choices_jsonb | JSONB | NOT NULL | Snapshot of all options |
| correct_option_label | VARCHAR(1) | NOT NULL | |
| explanation_text | TEXT | | |
| editor_user_id | VARCHAR(50) | | Who made the change |
| change_notes | TEXT | | Why the change was made |
| created_at | TIMESTAMPTZ | | Default: now() |

---

## Table: question_annotations

LLM-generated metadata: classification, explanations, confidence scores. Created during Pass 2.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | |
| question_id | UUID | FK, NOT NULL | -> questions.id |
| question_version_id | UUID | FK, NOT NULL | -> question_versions.id |
| provider_name | VARCHAR(50) | NOT NULL | e.g. 'anthropic', 'openai' |
| model_name | VARCHAR(100) | NOT NULL | e.g. 'claude-sonnet-4-6' |
| prompt_version | VARCHAR(20) | NOT NULL | e.g. 'v1', 'v3.0' |
| rules_version | VARCHAR(100) | NOT NULL | e.g. 'rules_agent_dsat_grammar_ingestion_generation_v3' |
| annotation_jsonb | JSONB | NOT NULL | Classification: grammar_role_key, grammar_focus_key, difficulty, etc. |
| explanation_jsonb | JSONB | NOT NULL | explanation_short, explanation_full, evidence_span_text |
| generation_profile_jsonb | JSONB | | Target keys, passage template, frequency band |
| confidence_jsonb | JSONB | NOT NULL | annotation_confidence, needs_human_review |
| created_at | TIMESTAMPTZ | | Default: now() |

---

## Table: question_options

Per-option analysis with distractor taxonomy. Exactly 4 rows per question (A, B, C, D).

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | |
| question_id | UUID | FK, NOT NULL | -> questions.id |
| question_version_id | UUID | FK, NOT NULL | -> question_versions.id |
| option_label | VARCHAR(1) | NOT NULL | 'A', 'B', 'C', or 'D' |
| option_text | TEXT | NOT NULL | |
| is_correct | BOOLEAN | NOT NULL | Exactly one per question |
| option_role | VARCHAR(10) | NOT NULL | 'correct' or 'distractor' |
| distractor_type_key | VARCHAR(30) | | e.g. 'semantic_imprecision', 'grammar_error' |
| semantic_relation_key | VARCHAR(40) | | |
| plausibility_source_key | VARCHAR(30) | | e.g. 'nearest_noun_attraction' |
| option_error_focus_key | VARCHAR(40) | | What grammar error this option tests |
| why_plausible | TEXT | | Why a student might pick this |
| why_wrong | TEXT | | Why this is incorrect |
| grammar_fit | VARCHAR(3) | | 'yes' or 'no' |
| tone_match | VARCHAR(3) | | 'yes' or 'no' |
| precision_score | SMALLINT | | 1-3 scale |
| student_failure_mode_key | VARCHAR(30) | | e.g. 'nearest_noun_reflex', 'comma_fix_illusion' |
| distractor_distance | VARCHAR(10) | | 'wide', 'moderate', 'tight' |
| distractor_competition_score | FLOAT | | 0.0-1.0 |
| created_at | TIMESTAMPTZ | | Default: now() |

---

## Table: question_assets

Raw uploaded files (PDFs, images, markdown) that were ingested to produce questions.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | |
| question_id | UUID | FK -> questions.id | Set after question is created |
| content_origin | content_origin_enum | NOT NULL | |
| asset_type | asset_type_enum | NOT NULL | 'pdf', 'image', 'markdown', etc. |
| storage_path | TEXT | NOT NULL | Filesystem path or S3 URI |
| mime_type | VARCHAR(100) | | e.g. 'application/pdf' |
| page_start | INTEGER | | For multi-page PDFs |
| page_end | INTEGER | | |
| source_url | TEXT | | Original download URL |
| source_name | VARCHAR(200) | | Original filename |
| source_exam_code | VARCHAR(20) | | |
| source_module_code | VARCHAR(10) | | |
| source_question_number | INTEGER | | |
| checksum | VARCHAR(64) | | SHA-256 for dedup |
| created_at | TIMESTAMPTZ | | Default: now() |

---

## Table: question_jobs

Pipeline execution records. Tracks the state of each ingest/generate/reannotate job.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | |
| job_type | job_type_enum | NOT NULL | 'ingest', 'generate', 'reannotate', 'overlap_check' |
| content_origin | content_origin_enum | NOT NULL | |
| input_format | VARCHAR(20) | NOT NULL | e.g. 'pdf', 'spec', 'reannotate' |
| status | job_status_enum | NOT NULL, DEFAULT 'pending' | See state machine below |
| provider_name | VARCHAR(50) | NOT NULL | |
| model_name | VARCHAR(100) | NOT NULL | |
| prompt_version | VARCHAR(20) | NOT NULL | |
| rules_version | VARCHAR(100) | NOT NULL | |
| raw_asset_id | UUID | FK -> question_assets.id | |
| pass1_json | JSONB | | Extraction output |
| pass2_json | JSONB | | Annotation output |
| validation_errors_jsonb | JSONB | | Validation error array |
| comparison_group_id | UUID | | Groups related jobs (e.g. multi-provider) |
| question_id | UUID | FK -> questions.id | Set when question is created |
| created_at | TIMESTAMPTZ | | Default: now() |
| updated_at | TIMESTAMPTZ | | Default: now(), on update: now() |

**Status State Machine:**
```
pending -> parsing -> extracting -> annotating -> overlap_checking -> validating -> approved
                                     |               |                   |
                                     v               v                   v
                                  failed          failed              needs_review

Generate jobs skip 'parsing': pending -> extracting -> generating -> annotating -> ...
Official content skips 'overlap_checking': annotating -> validating
```

---

## Table: question_relations

Tracks relationships between questions: overlaps, derivations, near-duplicates.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | |
| from_question_id | UUID | FK, NOT NULL | -> questions.id |
| to_question_id | UUID | FK, NOT NULL | -> questions.id |
| relation_type | relation_type_enum | NOT NULL | 'overlaps_official', 'derived_from', 'near_duplicate', 'generated_from', 'adapted_from' |
| relation_strength | FLOAT | | 0.0-1.0 similarity |
| detection_method | VARCHAR(30) | | e.g. 'llm', 'embedding', 'manual' |
| is_human_confirmed | BOOLEAN | NOT NULL, DEFAULT false | |
| notes | TEXT | | |
| created_at | TIMESTAMPTZ | | Default: now() |

---

## Table: llm_evaluations

Admin scoring of LLM-generated questions. Human review feedback.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | |
| job_id | UUID | FK, NOT NULL | -> question_jobs.id |
| question_id | UUID | FK -> questions.id | |
| provider_name | VARCHAR(50) | NOT NULL | |
| model_name | VARCHAR(100) | NOT NULL | |
| task_type | VARCHAR(20) | NOT NULL | e.g. 'generate', 'annotate' |
| score_overall | FLOAT | | 0.0-10.0 |
| score_metadata | FLOAT | | 0.0-10.0 |
| score_explanation | FLOAT | | 0.0-10.0 |
| score_generation | FLOAT | | 0.0-10.0 |
| review_notes | TEXT | | |
| recommended_for_default | BOOLEAN | | |
| created_at | TIMESTAMPTZ | | Default: now() |

---

## Table: user_progress

Student answer history. Tracks every answer for analytics.

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | INTEGER | PK, INDEX | Auto-increment |
| user_id | INTEGER | FK, NOT NULL | -> users.id |
| question_id | UUID | FK, NOT NULL | -> questions.id |
| is_correct | BOOLEAN | NOT NULL | |
| selected_option_label | VARCHAR(1) | NOT NULL | 'A'-'D' |
| missed_grammar_focus_key | VARCHAR(50) | | Populated on wrong answers |
| missed_syntactic_trap_key | VARCHAR(50) | | Populated on wrong answers |
| timestamp | TIMESTAMPTZ | | Default: now() |

---

## Entity-Relationship Summary

```
users (1) ---< user_progress (N) >--- (N) questions
questions (1) ---< question_versions (N)
questions (1) ---< question_annotations (N)
questions (1) ---< question_options (N)     [exactly 4]
questions (1) ---< question_assets (N)
questions (1) ---< question_jobs (N)
questions (1) ---< llm_evaluations (N)
questions (1) ---< question_relations (N)   [self-referential: from/to]
questions (1) ---> questions (1)            [canonical_official / derived_from]

question_jobs (1) ---< llm_evaluations (N)
question_assets (1) ---< question_jobs (N)  [via raw_asset_id]
question_versions (1) ---< question_annotations (N)
question_versions (1) ---< question_options (N)

question_jobs (N) ---> (N) question_jobs    [via comparison_group_id]
```

## Foreign Key Map

```
question_jobs.raw_asset_id             -> question_assets.id
question_jobs.question_id              -> questions.id
question_versions.question_id          -> questions.id
question_annotations.question_id       -> questions.id
question_annotations.question_version_id -> question_versions.id
question_options.question_id           -> questions.id
question_options.question_version_id   -> question_versions.id
question_assets.question_id            -> questions.id (deferred)
questions.canonical_official_question_id -> questions.id (deferred, self-ref)
questions.derived_from_question_id     -> questions.id (deferred, self-ref)
questions.latest_annotation_id         -> question_annotations.id (deferred)
questions.latest_version_id            -> question_versions.id (deferred)
question_relations.from_question_id    -> questions.id
question_relations.to_question_id      -> questions.id
llm_evaluations.job_id                 -> question_jobs.id
llm_evaluations.question_id            -> questions.id
user_progress.user_id                  -> users.id
user_progress.question_id              -> questions.id
```

## Controlled Vocabularies (V3 Ontology)

### grammar_role_key (8 roles)
```
sentence_boundary, agreement, verb_form, modifier, punctuation,
parallel_structure, pronoun, expression_of_ideas
```

### grammar_focus_key (grouped by role)
```
sentence_boundary: sentence_fragment, comma_splice, run_on_sentence, sentence_boundary
agreement: subject_verb_agreement, pronoun_antecedent_agreement, noun_countability,
           determiners_articles, affirmative_agreement
verb_form: verb_tense_consistency, verb_form, voice_active_passive, negation
modifier: modifier_placement, comparative_structures, logical_predication, relative_pronouns
punctuation: punctuation_comma, colon_dash_use, semicolon_use, conjunctive_adverb_usage,
             apostrophe_use, possessive_contraction, appositive_punctuation, hyphen_usage,
             quotation_punctuation
parallel_structure: parallel_structure, elliptical_constructions, conjunction_usage
pronoun: pronoun_case, pronoun_clarity, pronoun_antecedent_agreement
expression_of_ideas: redundancy_concision, precision_word_choice, register_style_consistency,
                     logical_relationships, emphasis_meaning_shifts,
                     data_interpretation_claims, transition_logic
```

### syntactic_trap_key (12 values)
```
none, nearest_noun_attraction, garden_path, early_clause_anchor,
nominalization_obscures_subject, interruption_breaks_subject_verb,
long_distance_dependency, pronoun_ambiguity, scope_of_negation,
modifier_attachment_ambiguity, presupposition_trap,
temporal_sequence_ambiguity, multiple
```

### stimulus_mode_key
```
sentence_only, passage_excerpt, prose_single, prose_paired,
prose_plus_table, prose_plus_graph, notes_bullets, poem
```

### stem_type_key
```
complete_the_text, choose_main_idea, choose_main_purpose,
choose_structure_description, choose_sentence_function,
choose_likely_response, choose_best_support, choose_best_quote,
choose_best_completion_from_data, choose_best_grammar_revision,
choose_best_transition, choose_best_notes_synthesis
```

### distractor_type_key
```
semantic_imprecision, logical_mismatch, scope_error, tone_mismatch,
grammar_error, punctuation_error, transition_mismatch, data_misread,
goal_mismatch, partially_supported, overstatement, understatement,
rhetorical_irrelevance, correct
```

### student_failure_mode_key
```
nearest_noun_reflex, comma_fix_illusion, formal_word_bias,
longer_answer_bias, punctuation_intimidation, surface_similarity_bias,
scope_blindness, modifier_hitchhike, chronological_assumption,
extreme_word_trap, overreading, underreading, grammar_fit_only,
register_confusion, pronoun_anchor_error, parallel_shape_bias,
transition_assumption, idiom_memory_pull, false_precision
```

### difficulty
```
low, medium, high
```

### question_family_key
```
conventions_grammar, expression_of_ideas, craft_and_structure, information_and_ideas
```

### passage_architecture_key
```
science_setup_finding_implication, science_hypothesis_method_result,
history_claim_evidence_limitation, history_assumption_revision,
literature_observation_interpretation_shift, literature_character_conflict_reveal,
economics_theory_exception_example, economics_problem_solution_tradeoff,
rhetoric_claim_counterclaim_resolution, notes_fact_selection_contrast
```
