# KEYS_MASTER.md — DSAT Controlled Vocabulary Reference

> Auto-generated from `vocabulary/master.json`. Do not hand-edit this file —
> edit `master.json` and run `scripts/gen_vocab.py --generate`, which regenerates
> `backend/app/models/ontology.py`, the rule-doc VOCAB appendix blocks, AND this
> file. This document is the human-readable mirror of the canonical manifest.

> Canonical controlled vocabulary. Edit THIS file, then run scripts/gen_vocab.py --generate. ontology.py and the rules-doc VOCAB blocks are generated artefacts — do not hand-edit them.

## How the vocabulary system works

- **`master.json`** — the compiled enforcement manifest. Every key the extraction
  LLM is allowed to emit lives here, grouped into named vocabularies. This is the
  single source of truth; `ontology.py` and the rule-doc VOCAB blocks are
  generated artefacts and must not be hand-edited.
- **`ontology.py`** — generated from master.json as pure-Python tuples
  (`STEM_TYPE_KEYS`, `GRAMMAR_ROLE_KEYS`, …) imported by the pipeline and the
  prompt builder to constrain LLM output to the controlled vocabulary.
- **`candidates.json`** — the non-blocking review queue: keys the LLM emitted that
  matched no active entry. Candidates are **never promoted directly**. An admin
  approves a canonical replacement in a rule doc, then regenerates. Surface and
  triage them in the admin dashboard under **Vocabulary → Candidate Queue**.
- **`gen_vocab --check`** — CI gate. Fails on drift (ontology.py ≠ master.json) or
  when the unreviewed candidate count exceeds the threshold (10).

## Summary

- **49 vocabularies** · **632 entries** (632 active, 0 retired)
- System / Cross-cutting: 16 vocabularies, 67 entries (67 active)
- Shared Question Ontology: 14 vocabularies, 243 entries (243 active)
- Grammar: 10 vocabularies, 183 entries (183 active)
- Reading & Analysis: 9 vocabularies, 139 entries (139 active)

## Vocabularies at a glance

| Vocab family | Kind | Domain | Entries (active) | Description |
|---|---|---|---|---|
| `CONTENT_ORIGINS` | flat | system | 3 (3) | Content origin |
| `JOB_TYPES` | flat | system | 4 (4) | Job types |
| `JOB_STATUSES` | flat | system | 13 (13) | Job statuses (state machine) |
| `PRACTICE_STATUSES` | flat | system | 4 (4) | Practice status |
| `OVERLAP_STATUSES` | flat | system | 3 (3) | Overlap status |
| `RELATION_TYPES` | flat | system | 5 (5) | Relation types |
| `ASSET_TYPES` | flat | system | 6 (6) | Asset types |
| `CHANGE_SOURCES` | flat | system | 4 (4) | Change sources |
| `STIMULUS_MODE_KEYS` | flat | shared | 9 (9) | V3 §3.1 stimulus_mode_key |
| `TEST_FORMAT_KEYS` | flat | system | 2 (2) | Rules v8 generation format keys |
| `SOURCE_STATS_FORMAT_KEYS` | flat | system | 2 (2) | Rules v8 source stats format keys |
| `STEM_TYPE_KEYS` | flat | shared | 29 (29) | V3 §3.2 stem_type_key |
| `GRAMMAR_ROLE_KEYS` | flat | grammar | 8 (8) | V3 §5 grammar_role_key |
| `GRAMMAR_FOCUS_BY_ROLE` | hierarchical | grammar | 46 (46) | V3 §6 grammar_focus_key (grouped by role) |
| `SYNTACTIC_TRAP_KEYS` | flat | grammar | 13 (13) | V3 §9 syntactic_trap_key |
| `SYNTACTIC_TRAP_REQUIRED_ROLES` | flat | grammar | 5 (5) | Grammar roles that always require a non-null syntactic_trap_key (policy subset of GRAMMAR_ROLE_KEYS) |
| `DISTRACTOR_TYPE_KEYS` | flat | shared | 45 (45) | V3 §12.1 distractor_type_key (option-level) |
| `REASONING_TRAP_KEYS` | flat | reading | 49 (49) | Reading v2 §10 reasoning_trap_key (question-level) |
| `PLAUSIBILITY_SOURCE_KEYS` | flat | shared | 15 (15) | V3 §10.3 plausibility_source_key |
| `ANSWER_MECHANISM_KEYS` | flat | shared | 10 (10) | V3 §3.3 answer_mechanism_key |
| `SOLVER_PATTERN_KEYS` | flat | shared | 16 (16) | V3 §3.3 solver_pattern_key |
| `STUDENT_FAILURE_MODE_KEYS` | flat | shared | 63 (63) | V3 §21.3 student_failure_mode_key |
| `DISTRACTOR_DISTANCE_KEYS` | flat | shared | 3 (3) | V3 §21.2 distractor_distance |
| `DIFFICULTY_KEYS` | flat | shared | 3 (3) | V3 §3.3 difficulty keys |
| `FREQUENCY_BANDS` | flat | shared | 5 (5) | V3 §3.3 frequency bands |
| `TENSE_REGISTER_KEYS` | flat | shared | 7 (7) | V3 §17.6 tense register keys |
| `PASSAGE_ARCHITECTURE_KEYS` | flat | shared | 25 (25) | V3 §22 passage_architecture_key |
| `QUESTION_FAMILY_KEYS` | flat | shared | 4 (4) | question_family_key |
| `READING_QUESTION_FAMILY_KEYS` | flat | reading | 2 (2) | Reading question families (subset of QUESTION_FAMILY_KEYS) |
| `GRAMMAR_QUESTION_FAMILY_KEYS` | flat | grammar | 2 (2) | Grammar question families (subset of QUESTION_FAMILY_KEYS) |
| `READING_SKILL_FAMILY_KEYS` | flat | reading | 7 (7) | Reading skill families |
| `READING_FOCUS_BY_SKILL_FAMILY` | hierarchical | reading | 38 (38) | Reading v2 reading_focus_key (grouped by skill family) |
| `TEST_CONSTRUCT_KEYS` | flat | reading | 7 (7) | Reading v2 target_test_construct_key |
| `CRAFT_SUBCONSTRUCT_KEYS` | flat | reading | 9 (9) | Reading v2 target_craft_subconstruct_key |
| `TEXT_RELATIONSHIP_KEYS` | flat | reading | 7 (7) | Reading v2 cross-text relationship keys |
| `QUANTITATIVE_SUB_PATTERN_KEYS` | flat | reading | 8 (8) | Reading v2 quantitative_sub_pattern |
| `SENTENCE_FUNCTION_ROLE_KEYS` | flat | reading | 12 (12) | Reading v2 target_sentence_function_role |
| `TRANSITION_SUBTYPE_KEYS` | flat | grammar | 24 (24) | Grammar v8 transition_subtype_key |
| `SYNTHESIS_GOAL_KEYS` | flat | grammar | 42 (42) | Grammar v8 notes synthesis goal keys |
| `AUDIENCE_KNOWLEDGE_KEYS` | flat | grammar | 3 (3) | Grammar v8 audience knowledge keys |
| `REQUIRED_CONTENT_KEYS` | flat | grammar | 32 (32) | Grammar v8 required content keys |
| `SYNTHESIS_DISTRACTOR_FAILURE_KEYS` | flat | grammar | 8 (8) | Grammar v8 synthesis distractor failure keys |
| `TOPIC_BROAD_KEYS` | flat | shared | 9 (9) | Broad topic keys |
| `REVIEW_TASK_TYPES` | flat | system | 1 (1) | Review task types for the generation review swarm |
| `REVIEW_STATUSES` | flat | system | 3 (3) | Per-reviewer outcome status |
| `REVIEW_RUN_STATUSES` | flat | system | 4 (4) | Review run lifecycle status |
| `TRIGGERED_BY_VALUES` | flat | system | 5 (5) | What triggered a review run |
| `REVIEW_VERDICTS` | flat | system | 3 (3) | Per-reviewer verdict on a generated question |
| `CONSENSUS_VERDICTS` | flat | system | 5 (5) | Consensus verdict after multi-model review (Phase 5) |

## System / Cross-cutting

_Identifiers, content provenance, and pipeline state shared across every domain._

### `CONTENT_ORIGINS`

- **Kind:** flat
- **Domain:** system
- **Description:** Content origin
- **Entries:** 3

| Value | Status | Added | Description |
|---|---|---|---|
| `generated` | active | 2026-05-18 |  |
| `official` | active | 2026-05-18 |  |
| `unofficial` | active | 2026-05-18 |  |

### `JOB_TYPES`

- **Kind:** flat
- **Domain:** system
- **Description:** Job types
- **Entries:** 4

| Value | Status | Added | Description |
|---|---|---|---|
| `generate` | active | 2026-05-18 |  |
| `ingest` | active | 2026-05-18 |  |
| `overlap_check` | active | 2026-05-18 |  |
| `reannotate` | active | 2026-05-18 |  |

### `JOB_STATUSES`

- **Kind:** flat
- **Domain:** system
- **Description:** Job statuses (state machine)
- **Entries:** 13

| Value | Status | Added | Description |
|---|---|---|---|
| `annotating` | active | 2026-05-18 |  |
| `approved` | active | 2026-05-18 |  |
| `extracting` | active | 2026-05-18 |  |
| `failed` | active | 2026-05-18 |  |
| `failed_permanent` | active | 2026-05-20 | Job failed with a non-recoverable error (malformed JSON after repair, model refusal, validation failure). Does not auto-retry; admin must regenerate-from-spec. |
| `failed_transient` | active | 2026-05-20 | Job failed with a transient error after auto-retry exhaustion (HTTP 429, 5xx, timeout, provider rate limit). Eligible for admin retry via /generate/batches/{id}/retry-failed. |
| `generating` | active | 2026-05-18 |  |
| `needs_review` | active | 2026-05-18 |  |
| `overlap_checking` | active | 2026-05-18 |  |
| `parsing` | active | 2026-05-18 |  |
| `pending` | active | 2026-05-18 |  |
| `retrying` | active | 2026-05-20 | Row-level guard set during a retry attempt to prevent duplicate concurrent retries of the same job. |
| `validating` | active | 2026-05-18 |  |

### `PRACTICE_STATUSES`

- **Kind:** flat
- **Domain:** system
- **Description:** Practice status
- **Entries:** 4

| Value | Status | Added | Description |
|---|---|---|---|
| `active` | active | 2026-05-18 |  |
| `draft` | active | 2026-05-18 |  |
| `rejected` | active | 2026-05-19 | Failed quality review; terminal state, audit-preserved. Distinct from retired (post-active removal). |
| `retired` | active | 2026-05-18 |  |

### `OVERLAP_STATUSES`

- **Kind:** flat
- **Domain:** system
- **Description:** Overlap status
- **Entries:** 3

| Value | Status | Added | Description |
|---|---|---|---|
| `confirmed` | active | 2026-05-18 |  |
| `none` | active | 2026-05-18 |  |
| `possible` | active | 2026-05-18 |  |

### `RELATION_TYPES`

- **Kind:** flat
- **Domain:** system
- **Description:** Relation types
- **Entries:** 5

| Value | Status | Added | Description |
|---|---|---|---|
| `adapted_from` | active | 2026-05-18 |  |
| `derived_from` | active | 2026-05-18 |  |
| `generated_from` | active | 2026-05-18 |  |
| `near_duplicate` | active | 2026-05-18 |  |
| `overlaps_official` | active | 2026-05-18 |  |

### `ASSET_TYPES`

- **Kind:** flat
- **Domain:** system
- **Description:** Asset types
- **Entries:** 6

| Value | Status | Added | Description |
|---|---|---|---|
| `image` | active | 2026-05-18 |  |
| `json` | active | 2026-05-18 |  |
| `markdown` | active | 2026-05-18 |  |
| `pdf` | active | 2026-05-18 |  |
| `screenshot` | active | 2026-05-18 |  |
| `text` | active | 2026-05-18 |  |

### `CHANGE_SOURCES`

- **Kind:** flat
- **Domain:** system
- **Description:** Change sources
- **Entries:** 4

| Value | Status | Added | Description |
|---|---|---|---|
| `admin_edit` | active | 2026-05-18 |  |
| `generate` | active | 2026-05-18 |  |
| `ingest` | active | 2026-05-18 |  |
| `reprocess` | active | 2026-05-18 |  |

### `TEST_FORMAT_KEYS`

- **Kind:** flat
- **Domain:** system
- **Description:** Rules v8 generation format keys
- **Entries:** 2

| Value | Status | Added | Description |
|---|---|---|---|
| `digital_app_adaptive` | active | 2026-05-18 |  |
| `nondigital_linear_accommodation` | active | 2026-05-18 |  |

### `SOURCE_STATS_FORMAT_KEYS`

- **Kind:** flat
- **Domain:** system
- **Description:** Rules v8 source stats format keys
- **Entries:** 2

| Value | Status | Added | Description |
|---|---|---|---|
| `official_digital` | active | 2026-05-18 |  |
| `official_nondigital_linear` | active | 2026-05-18 |  |

### `REVIEW_TASK_TYPES`

- **Kind:** flat
- **Domain:** system
- **Description:** Review task types for the generation review swarm
- **Entries:** 1

| Value | Status | Added | Description |
|---|---|---|---|
| `generation_realism_review` | active | 2026-05-20 | Multi-model quality review of generated DSAT questions |

### `REVIEW_STATUSES`

- **Kind:** flat
- **Domain:** system
- **Description:** Per-reviewer outcome status
- **Entries:** 3

| Value | Status | Added | Description |
|---|---|---|---|
| `ok` | active | 2026-05-20 | Review completed successfully |
| `permanent_failed` | active | 2026-05-20 | Review failed permanently (malformed output, model refusal) |
| `transient_failed` | active | 2026-05-20 | Review failed due to transient error (rate limit, network) |

### `REVIEW_RUN_STATUSES`

- **Kind:** flat
- **Domain:** system
- **Description:** Review run lifecycle status
- **Entries:** 4

| Value | Status | Added | Description |
|---|---|---|---|
| `complete` | active | 2026-05-20 | All reviewers completed successfully |
| `failed` | active | 2026-05-20 | Review run failed entirely |
| `partial` | active | 2026-05-20 | Some reviewers failed but minimum completed |
| `running` | active | 2026-05-20 | Review run in progress |

### `TRIGGERED_BY_VALUES`

- **Kind:** flat
- **Domain:** system
- **Description:** What triggered a review run
- **Entries:** 5

| Value | Status | Added | Description |
|---|---|---|---|
| `auto_on_save` | active | 2026-05-20 | Automatically triggered when a generated question is saved |
| `manual_batch` | active | 2026-05-20 | Admin manually triggered review for a batch |
| `manual_question` | active | 2026-05-20 | Admin manually triggered review for a single question |
| `recalibration` | active | 2026-05-20 | Re-review triggered by calibration threshold change |
| `rubric_bump` | active | 2026-05-20 | Re-review triggered by rubric version change |

### `REVIEW_VERDICTS`

- **Kind:** flat
- **Domain:** system
- **Description:** Per-reviewer verdict on a generated question
- **Entries:** 3

| Value | Status | Added | Description |
|---|---|---|---|
| `accept` | active | 2026-05-20 | Question meets all quality thresholds |
| `needs_human_review` | active | 2026-05-20 | Borderline quality; human review recommended |
| `reject` | active | 2026-05-20 | Question fails quality thresholds |

### `CONSENSUS_VERDICTS`

- **Kind:** flat
- **Domain:** system
- **Description:** Consensus verdict after multi-model review (Phase 5)
- **Entries:** 5

| Value | Status | Added | Description |
|---|---|---|---|
| `admin_review_ready` | active | 2026-05-20 | All thresholds cleared; ready for admin review |
| `blocked_overlap` | active | 2026-05-20 | Unresolved official overlap blocks approval |
| `insufficient_reviews` | active | 2026-05-20 | Fewer than 2 reviewers succeeded |
| `regenerate_recommended` | active | 2026-05-20 | Consensus recommends regeneration |
| `reject_recommended` | active | 2026-05-20 | Consensus recommends rejection |

## Shared Question Ontology

_Keys that apply to both grammar and reading questions — stimulus form, stem shape, difficulty, source metadata._

### `STIMULUS_MODE_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §3.1 stimulus_mode_key
- **Entries:** 9

| Value | Status | Added | Description |
|---|---|---|---|
| `notes_bullets` | active | 2026-05-18 |  |
| `notes_summary` | active | 2026-05-18 |  |
| `passage_excerpt` | active | 2026-05-18 |  |
| `poem` | active | 2026-05-18 |  |
| `prose_paired` | active | 2026-05-18 |  |
| `prose_plus_graph` | active | 2026-05-18 |  |
| `prose_plus_table` | active | 2026-05-18 |  |
| `prose_single` | active | 2026-05-18 |  |
| `sentence_only` | active | 2026-05-18 |  |

### `STEM_TYPE_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §3.2 stem_type_key
- **Entries:** 29

| Value | Status | Added | Description |
|---|---|---|---|
| `choose_agreement_across_texts` | active | 2026-05-18 |  |
| `choose_best_completion_from_data` | active | 2026-05-18 |  |
| `choose_best_grammar_revision` | active | 2026-05-18 |  |
| `choose_best_illustration` | active | 2026-05-18 |  |
| `choose_best_inference` | active | 2026-05-18 |  |
| `choose_best_notes_synthesis` | active | 2026-05-18 |  |
| `choose_best_quote` | active | 2026-05-18 |  |
| `choose_best_support` | active | 2026-05-18 |  |
| `choose_best_transition` | active | 2026-05-18 |  |
| `choose_best_weakener` | active | 2026-05-18 |  |
| `choose_central_detail` | active | 2026-05-18 |  |
| `choose_command_of_evidence_quantitative` | active | 2026-05-18 |  |
| `choose_command_of_evidence_textual` | active | 2026-05-18 |  |
| `choose_cross_text_connection` | active | 2026-05-18 |  |
| `choose_detail` | active | 2026-05-18 |  |
| `choose_difference_across_texts` | active | 2026-05-18 |  |
| `choose_likely_response` | active | 2026-05-18 |  |
| `choose_main_idea` | active | 2026-05-18 |  |
| `choose_main_purpose` | active | 2026-05-18 |  |
| `choose_sentence_function` | active | 2026-05-18 |  |
| `choose_structure_description` | active | 2026-05-18 |  |
| `choose_text_relationship` | active | 2026-05-18 |  |
| `choose_word_in_context` | active | 2026-05-18 |  |
| `choose_words_in_context` | active | 2026-05-18 |  |
| `compare_contributions` | active | 2026-05-18 |  |
| `complete_the_text` | active | 2026-05-18 |  |
| `conform_to_standard_english` | active | 2026-05-18 |  |
| `most_logically_completes` | active | 2026-05-18 |  |
| `synthesize_information` | active | 2026-05-18 |  |

### `DISTRACTOR_TYPE_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §12.1 distractor_type_key (option-level)
- **Entries:** 45

| Value | Status | Added | Description |
|---|---|---|---|
| `absolute_value_confusion` | active | 2026-05-18 |  |
| `agreement_degree_mismatch` | active | 2026-05-18 |  |
| `attribution_blend` | active | 2026-05-18 |  |
| `author_action_misclassification` | active | 2026-05-18 |  |
| `cause_effect_misalignment` | active | 2026-05-18 |  |
| `confirmed_when_contradicted` | active | 2026-05-18 |  |
| `connotation_mismatch` | active | 2026-05-18 |  |
| `constraint_ignored` | active | 2026-05-18 |  |
| `contradiction` | active | 2026-05-18 |  |
| `correct` | active | 2026-05-18 |  |
| `data_context_mismatch` | active | 2026-05-18 |  |
| `data_misread` | active | 2026-05-18 |  |
| `detail_trap` | active | 2026-05-18 |  |
| `evidence_relationship_blend` | active | 2026-05-18 |  |
| `false_concession_trap` | active | 2026-05-18 |  |
| `figurative_literal_confusion` | active | 2026-05-18 |  |
| `goal_mismatch` | active | 2026-05-18 |  |
| `grammar_error` | active | 2026-05-18 |  |
| `indirect_evidence` | active | 2026-05-18 |  |
| `individual_inference_from_aggregate_bins` | active | 2026-05-18 |  |
| `inverted_logic` | active | 2026-05-18 |  |
| `local_maximum_trap` | active | 2026-05-18 |  |
| `local_semantic_role_mismatch` | active | 2026-05-18 |  |
| `logical_mismatch` | active | 2026-05-18 |  |
| `overreach` | active | 2026-05-18 |  |
| `overstatement` | active | 2026-05-18 |  |
| `partial_match` | active | 2026-05-18 |  |
| `partially_supported` | active | 2026-05-18 |  |
| `plausible_synonym` | active | 2026-05-18 |  |
| `punctuation_error` | active | 2026-05-18 |  |
| `reversed_attribution` | active | 2026-05-18 |  |
| `rhetorical_irrelevance` | active | 2026-05-18 |  |
| `rhetorical_scope_shift` | active | 2026-05-18 |  |
| `same_direction_assumption` | active | 2026-05-18 |  |
| `scope_error` | active | 2026-05-18 |  |
| `semantic_imprecision` | active | 2026-05-18 |  |
| `single_measure_focus` | active | 2026-05-18 |  |
| `tone_mismatch` | active | 2026-05-18 |  |
| `tone_register_mismatch` | active | 2026-05-18 |  |
| `topical_relevance_without_logical_connection` | active | 2026-05-18 |  |
| `transition_mismatch` | active | 2026-05-18 |  |
| `understatement` | active | 2026-05-18 |  |
| `wrong_action_verb` | active | 2026-05-18 |  |
| `wrong_group_comparison` | active | 2026-05-18 |  |
| `wrong_table_row_or_column` | active | 2026-05-18 |  |

### `PLAUSIBILITY_SOURCE_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §10.3 plausibility_source_key
- **Entries:** 15

| Value | Status | Added | Description |
|---|---|---|---|
| `attribution_swap` | active | 2026-05-18 |  |
| `auditory_similarity` | active | 2026-05-18 |  |
| `common_definition_appeal` | active | 2026-05-18 |  |
| `common_idiom_pull` | active | 2026-05-18 |  |
| `common_sense_appeal` | active | 2026-05-18 |  |
| `formal_register_match` | active | 2026-05-18 |  |
| `grammar_fit_only` | active | 2026-05-18 |  |
| `near_synonym_appeal` | active | 2026-05-18 |  |
| `nearest_noun_attraction` | active | 2026-05-18 |  |
| `none` | active | 2026-05-18 |  |
| `partial_truth` | active | 2026-05-18 |  |
| `passage_vocabulary_overlap` | active | 2026-05-18 |  |
| `punctuation_style_bias` | active | 2026-05-18 |  |
| `rhetorical_surface_similarity` | active | 2026-05-18 |  |
| `topical_proximity` | active | 2026-05-18 |  |

### `ANSWER_MECHANISM_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §3.3 answer_mechanism_key
- **Entries:** 10

| Value | Status | Added | Description |
|---|---|---|---|
| `contextual_substitution` | active | 2026-05-18 |  |
| `cross_text_comparison` | active | 2026-05-18 |  |
| `data_synthesis` | active | 2026-05-18 |  |
| `evidence_location` | active | 2026-05-18 |  |
| `evidence_matching` | active | 2026-05-18 |  |
| `inference` | active | 2026-05-18 |  |
| `pattern_matching` | active | 2026-05-18 |  |
| `polarity_resolution` | active | 2026-05-18 |  |
| `rhetorical_classification` | active | 2026-05-18 |  |
| `rule_application` | active | 2026-05-18 |  |

### `SOLVER_PATTERN_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §3.3 solver_pattern_key
- **Entries:** 16

| Value | Status | Added | Description |
|---|---|---|---|
| `apply_grammar_rule_directly` | active | 2026-05-18 |  |
| `apply_negation_logic` | active | 2026-05-18 |  |
| `classify_rhetorical_move` | active | 2026-05-18 |  |
| `compare_register` | active | 2026-05-18 |  |
| `eliminate_by_boundary` | active | 2026-05-18 |  |
| `evaluate_transition` | active | 2026-05-18 |  |
| `identify_logical_gap` | active | 2026-05-18 |  |
| `locate_claim_then_match_evidence` | active | 2026-05-18 |  |
| `locate_detail_directly` | active | 2026-05-18 |  |
| `locate_error_zone` | active | 2026-05-18 |  |
| `locate_figurative_function` | active | 2026-05-18 |  |
| `read_graphic_then_match_claim` | active | 2026-05-18 |  |
| `substitute_and_test` | active | 2026-05-18 |  |
| `summarize_both_then_compare` | active | 2026-05-18 |  |
| `summarize_then_compare` | active | 2026-05-18 |  |
| `synthesize_notes` | active | 2026-05-18 |  |

### `STUDENT_FAILURE_MODE_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §21.3 student_failure_mode_key
- **Entries:** 63

| Value | Status | Added | Description |
|---|---|---|---|
| `absolute_value_overweighting` | active | 2026-05-18 |  |
| `adverb_adjective_confusion` | active | 2026-05-18 |  |
| `agreement_degree_overread` | active | 2026-05-18 |  |
| `all_measures_not_checked` | active | 2026-05-18 |  |
| `attribution_swap` | active | 2026-05-18 |  |
| `author_action_overread` | active | 2026-05-18 |  |
| `chronological_assumption` | active | 2026-05-18 |  |
| `comma_fix_illusion` | active | 2026-05-18 |  |
| `confused_word_substitution` | active | 2026-05-18 |  |
| `connotation_surface_match` | active | 2026-05-18 |  |
| `constraint_ignored` | active | 2026-05-18 |  |
| `control_group_misidentification` | active | 2026-05-18 |  |
| `declarative_question_confusion` | active | 2026-05-18 |  |
| `evidence_scope_mismatch` | active | 2026-05-18 |  |
| `exact_value_misread` | active | 2026-05-18 |  |
| `extreme_word_trap` | active | 2026-05-18 |  |
| `false_precision` | active | 2026-05-18 |  |
| `figurative_meaning_blindness` | active | 2026-05-18 |  |
| `formal_word_bias` | active | 2026-05-18 |  |
| `grammar_fit_only` | active | 2026-05-18 |  |
| `idiom_memory_pull` | active | 2026-05-18 |  |
| `illogical_comparison_blindness` | active | 2026-05-18 |  |
| `individual_from_aggregate` | active | 2026-05-18 |  |
| `inflected_after_modal` | active | 2026-05-18 |  |
| `internal_unit_punctuation_insertion` | active | 2026-05-18 |  |
| `local_maximum_overread` | active | 2026-05-18 |  |
| `local_role_misread` | active | 2026-05-18 |  |
| `longer_answer_bias` | active | 2026-05-18 |  |
| `modifier_hitchhike` | active | 2026-05-18 |  |
| `nearest_noun_reflex` | active | 2026-05-18 |  |
| `negation_blindness` | active | 2026-05-18 |  |
| `nonfinite_for_finite` | active | 2026-05-18 |  |
| `notes_synthesis_audience_mismatch` | active | 2026-05-18 |  |
| `notes_synthesis_content_omission` | active | 2026-05-18 |  |
| `notes_synthesis_wrong_goal` | active | 2026-05-18 |  |
| `overreading` | active | 2026-05-18 |  |
| `parallel_shape_bias` | active | 2026-05-18 |  |
| `parenthetical_function_confusion` | active | 2026-05-18 |  |
| `past_tense_for_literary_present` | active | 2026-05-18 |  |
| `plural_pronoun_for_clause_antecedent` | active | 2026-05-18 |  |
| `polarity_blindness` | active | 2026-05-18 |  |
| `preposition_idiom_error` | active | 2026-05-18 |  |
| `pronoun_anchor_error` | active | 2026-05-18 |  |
| `punctuation_intimidation` | active | 2026-05-18 |  |
| `register_confusion` | active | 2026-05-18 |  |
| `register_tone_blindness` | active | 2026-05-18 |  |
| `relationship_simplification` | active | 2026-05-18 |  |
| `restrictive_appositive_comma_insertion` | active | 2026-05-18 |  |
| `rhetorical_verb_partial` | active | 2026-05-18 |  |
| `scope_blindness` | active | 2026-05-18 |  |
| `scope_role_confusion` | active | 2026-05-18 |  |
| `single_measure_overread` | active | 2026-05-18 |  |
| `subgroup_overgeneralization` | active | 2026-05-18 |  |
| `surface_similarity_bias` | active | 2026-05-18 |  |
| `tense_proximity_pull` | active | 2026-05-18 |  |
| `title_name_comma_insertion` | active | 2026-05-18 |  |
| `transition_assumption` | active | 2026-05-18 |  |
| `transition_wrong_direction` | active | 2026-05-18 |  |
| `two_part_claim_partial_match` | active | 2026-05-18 |  |
| `underreading` | active | 2026-05-18 |  |
| `wrong_comparison_direction` | active | 2026-05-18 |  |
| `wrong_group_selected` | active | 2026-05-18 |  |
| `wrong_row_column_lookup` | active | 2026-05-18 |  |

### `DISTRACTOR_DISTANCE_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §21.2 distractor_distance
- **Entries:** 3

| Value | Status | Added | Description |
|---|---|---|---|
| `moderate` | active | 2026-05-18 |  |
| `tight` | active | 2026-05-18 |  |
| `wide` | active | 2026-05-18 |  |

### `DIFFICULTY_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §3.3 difficulty keys
- **Entries:** 3

| Value | Status | Added | Description |
|---|---|---|---|
| `high` | active | 2026-05-18 |  |
| `low` | active | 2026-05-18 |  |
| `medium` | active | 2026-05-18 |  |

### `FREQUENCY_BANDS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §3.3 frequency bands
- **Entries:** 5

| Value | Status | Added | Description |
|---|---|---|---|
| `high` | active | 2026-05-18 |  |
| `low` | active | 2026-05-18 |  |
| `medium` | active | 2026-05-18 |  |
| `very_high` | active | 2026-05-18 |  |
| `very_low` | active | 2026-05-18 |  |

### `TENSE_REGISTER_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §17.6 tense register keys
- **Entries:** 7

| Value | Status | Added | Description |
|---|---|---|---|
| `established_finding_present` | active | 2026-05-18 |  |
| `historical_past` | active | 2026-05-18 |  |
| `literary_present` | active | 2026-05-18 |  |
| `mixed_with_explicit_shift` | active | 2026-05-18 |  |
| `narrative_past` | active | 2026-05-18 |  |
| `scientific_general_present` | active | 2026-05-18 |  |
| `study_procedure_past` | active | 2026-05-18 |  |

### `PASSAGE_ARCHITECTURE_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** V3 §22 passage_architecture_key
- **Entries:** 25

| Value | Status | Added | Description |
|---|---|---|---|
| `alternative_explanation_ruled_out` | active | 2026-05-18 |  |
| `analogy_driven_argument` | active | 2026-05-18 |  |
| `cautionary_framing` | active | 2026-05-18 |  |
| `chronological_sequence` | active | 2026-05-18 |  |
| `claim_evidence_explanation` | active | 2026-05-18 |  |
| `compare_contrast` | active | 2026-05-18 |  |
| `economics_problem_solution_tradeoff` | active | 2026-05-18 |  |
| `economics_theory_exception_example` | active | 2026-05-18 |  |
| `experiment_hypothesis_control_result` | active | 2026-05-18 |  |
| `history_assumption_revision` | active | 2026-05-18 |  |
| `history_claim_evidence_limitation` | active | 2026-05-18 |  |
| `indirect_effect_mediation` | active | 2026-05-18 |  |
| `literature_character_conflict_reveal` | active | 2026-05-18 |  |
| `literature_observation_interpretation_shift` | active | 2026-05-18 |  |
| `mechanism_manipulation_test` | active | 2026-05-18 |  |
| `multi_perspective_presentation` | active | 2026-05-18 |  |
| `notes_fact_selection_contrast` | active | 2026-05-18 |  |
| `problem_solution` | active | 2026-05-18 |  |
| `qualification_restatement` | active | 2026-05-18 |  |
| `research_summary` | active | 2026-05-18 |  |
| `rhetoric_claim_counterclaim_resolution` | active | 2026-05-18 |  |
| `science_hypothesis_method_result` | active | 2026-05-18 |  |
| `science_setup_finding_implication` | active | 2026-05-18 |  |
| `studied_subgroup_generalization_limit` | active | 2026-05-18 |  |
| `unexpected_finding` | active | 2026-05-18 |  |

### `QUESTION_FAMILY_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** question_family_key
- **Entries:** 4

| Value | Status | Added | Description |
|---|---|---|---|
| `conventions_grammar` | active | 2026-05-18 |  |
| `craft_and_structure` | active | 2026-05-18 |  |
| `expression_of_ideas` | active | 2026-05-18 |  |
| `information_and_ideas` | active | 2026-05-18 |  |

### `TOPIC_BROAD_KEYS`

- **Kind:** flat
- **Domain:** shared
- **Description:** Broad topic keys
- **Entries:** 9

| Value | Status | Added | Description |
|---|---|---|---|
| `arts` | active | 2026-05-18 |  |
| `economics` | active | 2026-05-18 |  |
| `environment` | active | 2026-05-18 |  |
| `history` | active | 2026-05-18 |  |
| `humanities` | active | 2026-05-18 |  |
| `literature` | active | 2026-05-18 |  |
| `science` | active | 2026-05-18 |  |
| `social_studies` | active | 2026-05-18 |  |
| `technology` | active | 2026-05-18 |  |

## Grammar

_Conventions of English and expression-of-ideas question ontology._

### `GRAMMAR_ROLE_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** V3 §5 grammar_role_key
- **Entries:** 8

| Value | Status | Added | Description |
|---|---|---|---|
| `agreement` | active | 2026-05-18 |  |
| `expression_of_ideas` | active | 2026-05-18 |  |
| `modifier` | active | 2026-05-18 |  |
| `parallel_structure` | active | 2026-05-18 |  |
| `pronoun` | active | 2026-05-18 |  |
| `punctuation` | active | 2026-05-18 |  |
| `sentence_boundary` | active | 2026-05-18 |  |
| `verb_form` | active | 2026-05-18 |  |

### `GRAMMAR_FOCUS_BY_ROLE`

- **Kind:** hierarchical
- **Domain:** grammar
- **Description:** V3 §6 grammar_focus_key (grouped by role)
- **Entries:** 46

| Value | Status | Added | Description |
|---|---|---|---|
| `absolute_phrase` | active | 2026-05-27 | Nominative absolute construction (noun + participial phrase modifying the whole main clause) |
| `adjective_adverb_distinction` | active | 2026-05-18 |  |
| `affirmative_agreement` | active | 2026-05-18 |  |
| `apostrophe_use` | active | 2026-05-18 |  |
| `appositive_punctuation` | active | 2026-05-18 |  |
| `colon_dash_use` | active | 2026-05-18 |  |
| `comma_splice` | active | 2026-05-18 |  |
| `commonly_confused_words` | active | 2026-05-18 |  |
| `comparative_structures` | active | 2026-05-18 |  |
| `conjunction_usage` | active | 2026-05-18 |  |
| `conjunctive_adverb_usage` | active | 2026-05-18 |  |
| `data_interpretation_claims` | active | 2026-05-18 |  |
| `determiners_articles` | active | 2026-05-18 |  |
| `elliptical_constructions` | active | 2026-05-18 |  |
| `emphasis_meaning_shifts` | active | 2026-05-18 |  |
| `end_punctuation_question_statement` | active | 2026-05-18 |  |
| `hyphen_usage` | active | 2026-05-18 |  |
| `illogical_comparison` | active | 2026-05-18 |  |
| `logical_predication` | active | 2026-05-18 |  |
| `logical_relationships` | active | 2026-05-18 |  |
| `modifier_placement` | active | 2026-05-18 |  |
| `negation` | active | 2026-05-18 |  |
| `noun_countability` | active | 2026-05-18 |  |
| `parallel_structure` | active | 2026-05-18 |  |
| `possessive_contraction` | active | 2026-05-18 |  |
| `precision_word_choice` | active | 2026-05-18 |  |
| `preposition_idiom` | active | 2026-05-18 |  |
| `pronoun_antecedent_agreement` | active | 2026-05-18 |  |
| `pronoun_antecedent_agreement` | active | 2026-05-18 |  |
| `pronoun_case` | active | 2026-05-18 |  |
| `pronoun_clarity` | active | 2026-05-18 |  |
| `punctuation_comma` | active | 2026-05-18 |  |
| `quotation_punctuation` | active | 2026-05-18 |  |
| `redundancy_concision` | active | 2026-05-18 |  |
| `register_style_consistency` | active | 2026-05-18 |  |
| `relative_pronouns` | active | 2026-05-18 |  |
| `run_on_sentence` | active | 2026-05-18 |  |
| `semicolon_use` | active | 2026-05-18 |  |
| `sentence_boundary` | active | 2026-05-18 |  |
| `sentence_fragment` | active | 2026-05-18 |  |
| `subject_verb_agreement` | active | 2026-05-18 |  |
| `transition_logic` | active | 2026-05-18 |  |
| `unnecessary_internal_punctuation` | active | 2026-05-18 |  |
| `verb_form` | active | 2026-05-18 |  |
| `verb_tense_consistency` | active | 2026-05-18 |  |
| `voice_active_passive` | active | 2026-05-18 |  |

### `SYNTACTIC_TRAP_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** V3 §9 syntactic_trap_key
- **Entries:** 13

| Value | Status | Added | Description |
|---|---|---|---|
| `early_clause_anchor` | active | 2026-05-18 |  |
| `garden_path` | active | 2026-05-18 |  |
| `interruption_breaks_subject_verb` | active | 2026-05-18 |  |
| `long_distance_dependency` | active | 2026-05-18 |  |
| `modifier_attachment_ambiguity` | active | 2026-05-18 |  |
| `multiple` | active | 2026-05-18 |  |
| `nearest_noun_attraction` | active | 2026-05-18 |  |
| `nominalization_obscures_subject` | active | 2026-05-18 |  |
| `none` | active | 2026-05-18 |  |
| `presupposition_trap` | active | 2026-05-18 |  |
| `pronoun_ambiguity` | active | 2026-05-18 |  |
| `scope_of_negation` | active | 2026-05-18 |  |
| `temporal_sequence_ambiguity` | active | 2026-05-18 |  |

### `SYNTACTIC_TRAP_REQUIRED_ROLES`

- **Kind:** flat
- **Domain:** grammar
- **Description:** Grammar roles that always require a non-null syntactic_trap_key (policy subset of GRAMMAR_ROLE_KEYS)
- **Entries:** 5

| Value | Status | Added | Description |
|---|---|---|---|
| `agreement` | active | 2026-07-29 |  |
| `modifier` | active | 2026-07-29 |  |
| `pronoun` | active | 2026-07-29 |  |
| `sentence_boundary` | active | 2026-07-29 |  |
| `verb_form` | active | 2026-07-29 |  |

### `GRAMMAR_QUESTION_FAMILY_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** Grammar question families (subset of QUESTION_FAMILY_KEYS)
- **Entries:** 2

| Value | Status | Added | Description |
|---|---|---|---|
| `conventions_grammar` | active | 2026-07-29 |  |
| `expression_of_ideas` | active | 2026-07-29 |  |

### `TRANSITION_SUBTYPE_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** Grammar v8 transition_subtype_key
- **Entries:** 24

| Value | Status | Added | Description |
|---|---|---|---|
| `addition` | active | 2026-05-18 |  |
| `alternative` | active | 2026-05-18 |  |
| `appropriateness` | active | 2026-05-18 |  |
| `causal_chain` | active | 2026-05-18 |  |
| `change_over_time` | active | 2026-05-18 |  |
| `chronology` | active | 2026-05-18 |  |
| `concession_qualification` | active | 2026-05-18 |  |
| `contrast_refutation` | active | 2026-05-18 |  |
| `converse_opposite` | active | 2026-05-18 |  |
| `direct_refutation` | active | 2026-05-18 |  |
| `emphasis_support` | active | 2026-05-18 |  |
| `example` | active | 2026-05-18 |  |
| `exception` | active | 2026-05-18 |  |
| `final_realization` | active | 2026-05-18 |  |
| `frequency_difference` | active | 2026-05-18 |  |
| `logical_consequence` | active | 2026-05-18 |  |
| `present_continuation` | active | 2026-05-18 |  |
| `purpose_action` | active | 2026-05-18 |  |
| `restatement_clarification` | active | 2026-05-18 |  |
| `result_consequence` | active | 2026-05-18 |  |
| `sequence_final_event` | active | 2026-05-18 |  |
| `similarity` | active | 2026-05-18 |  |
| `simultaneity` | active | 2026-05-18 |  |
| `specificity_elaboration` | active | 2026-05-18 |  |

### `SYNTHESIS_GOAL_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** Grammar v8 notes synthesis goal keys
- **Entries:** 42

| Value | Status | Added | Description |
|---|---|---|---|
| `challenge_explanation_with_quote` | active | 2026-05-18 |  |
| `challenge_with_quotation` | active | 2026-05-18 |  |
| `compare_hypothesis_scope` | active | 2026-05-18 |  |
| `compare_measurements` | active | 2026-05-18 |  |
| `contextualize_changing_beliefs` | active | 2026-05-18 |  |
| `contrast_formal_structures` | active | 2026-05-18 |  |
| `contrast_origins` | active | 2026-05-18 |  |
| `contrast_quantities` | active | 2026-05-18 |  |
| `contrast_structural_types` | active | 2026-05-18 |  |
| `describe_work` | active | 2026-05-18 |  |
| `emphasize_achievement` | active | 2026-05-18 |  |
| `emphasize_age_similarity` | active | 2026-05-18 |  |
| `emphasize_difference` | active | 2026-05-18 |  |
| `emphasize_duration_and_purpose` | active | 2026-05-18 |  |
| `emphasize_sample` | active | 2026-05-18 |  |
| `emphasize_significance` | active | 2026-05-18 |  |
| `emphasize_similarity` | active | 2026-05-18 |  |
| `emphasize_size_similarity` | active | 2026-05-18 |  |
| `explain_advantage` | active | 2026-05-18 |  |
| `explain_format_advantage` | active | 2026-05-18 |  |
| `explain_mechanism` | active | 2026-05-18 |  |
| `explain_misconception_naming` | active | 2026-05-18 |  |
| `explain_technique_advantage` | active | 2026-05-18 |  |
| `identify_author_pseudonym` | active | 2026-05-18 |  |
| `identify_category` | active | 2026-05-18 |  |
| `identify_distance` | active | 2026-05-18 |  |
| `identify_duration` | active | 2026-05-18 |  |
| `identify_profession` | active | 2026-05-18 |  |
| `identify_setting` | active | 2026-05-18 |  |
| `identify_statistical_authorship_method` | active | 2026-05-18 |  |
| `identify_statistical_method` | active | 2026-05-18 |  |
| `identify_title` | active | 2026-05-18 |  |
| `identify_year` | active | 2026-05-18 |  |
| `introduce_work` | active | 2026-05-18 |  |
| `make_generalization` | active | 2026-05-18 |  |
| `present_methodology` | active | 2026-05-18 |  |
| `present_research` | active | 2026-05-18 |  |
| `present_study_aim` | active | 2026-05-18 |  |
| `present_study_conclusions` | active | 2026-05-18 |  |
| `present_study_overview` | active | 2026-05-18 |  |
| `present_theory` | active | 2026-05-18 |  |
| `provide_historical_overview` | active | 2026-05-18 |  |

### `AUDIENCE_KNOWLEDGE_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** Grammar v8 audience knowledge keys
- **Entries:** 3

| Value | Status | Added | Description |
|---|---|---|---|
| `audience_familiar` | active | 2026-05-18 |  |
| `audience_unfamiliar` | active | 2026-05-18 |  |
| `not_specified` | active | 2026-05-18 |  |

### `REQUIRED_CONTENT_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** Grammar v8 required content keys
- **Entries:** 32

| Value | Status | Added | Description |
|---|---|---|---|
| `achievement_needed` | active | 2026-05-18 |  |
| `advantage_needed` | active | 2026-05-18 |  |
| `author_identity_needed` | active | 2026-05-18 |  |
| `background_omit` | active | 2026-05-18 |  |
| `category_label_needed` | active | 2026-05-18 |  |
| `comparison_needed` | active | 2026-05-18 |  |
| `conclusion_needed` | active | 2026-05-18 |  |
| `definition_needed` | active | 2026-05-18 |  |
| `distance_needed` | active | 2026-05-18 |  |
| `duration_needed` | active | 2026-05-18 |  |
| `formal_feature_labels_needed` | active | 2026-05-18 |  |
| `measurement_values_needed` | active | 2026-05-18 |  |
| `mechanism_needed` | active | 2026-05-18 |  |
| `method_needed` | active | 2026-05-18 |  |
| `misconception_needed` | active | 2026-05-18 |  |
| `origin_labels_needed` | active | 2026-05-18 |  |
| `owner_of_achievement_needed` | active | 2026-05-18 |  |
| `profession_label_needed` | active | 2026-05-18 |  |
| `purpose_needed` | active | 2026-05-18 |  |
| `quotation_needed` | active | 2026-05-18 |  |
| `result_needed` | active | 2026-05-18 |  |
| `sample_location_needed` | active | 2026-05-18 |  |
| `scope_terms_needed` | active | 2026-05-18 |  |
| `setting_needed` | active | 2026-05-18 |  |
| `significance_needed` | active | 2026-05-18 |  |
| `statistical_method_needed` | active | 2026-05-18 |  |
| `structural_roles_needed` | active | 2026-05-18 |  |
| `study_aim_needed` | active | 2026-05-18 |  |
| `study_finding_summary_needed` | active | 2026-05-18 |  |
| `timeline_needed` | active | 2026-05-18 |  |
| `title_and_content_needed` | active | 2026-05-18 |  |
| `year_needed` | active | 2026-05-18 |  |

### `SYNTHESIS_DISTRACTOR_FAILURE_KEYS`

- **Kind:** flat
- **Domain:** grammar
- **Description:** Grammar v8 synthesis distractor failure keys
- **Entries:** 8

| Value | Status | Added | Description |
|---|---|---|---|
| `adds_background_audience_does_not_need` | active | 2026-05-18 |  |
| `correct_topic_wrong_comparison` | active | 2026-05-18 |  |
| `irrelevant_background` | active | 2026-05-18 |  |
| `misstates_required_relationship` | active | 2026-05-18 |  |
| `omits_required_content` | active | 2026-05-18 |  |
| `omits_unfamiliar_context` | active | 2026-05-18 |  |
| `wrong_audience_assumption` | active | 2026-05-18 |  |
| `wrong_goal` | active | 2026-05-18 |  |

## Reading & Analysis

_Comprehension, craft, and synthesis question ontology._

### `REASONING_TRAP_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading v2 §10 reasoning_trap_key (question-level)
- **Entries:** 49

| Value | Status | Added | Description |
|---|---|---|---|
| `absolute_language` | active | 2026-05-18 |  |
| `absolute_value_confusion` | active | 2026-05-18 |  |
| `agreement_degree_mismatch` | active | 2026-05-18 |  |
| `also_true_trap` | active | 2026-05-18 |  |
| `attribution_blend` | active | 2026-05-18 |  |
| `author_action_misclassification` | active | 2026-05-18 |  |
| `cause_effect_misalignment` | active | 2026-05-18 |  |
| `common_definition_trap` | active | 2026-05-18 |  |
| `confirmed_when_contradicted` | active | 2026-05-18 |  |
| `connotation_mismatch` | active | 2026-05-18 |  |
| `constraint_ignored` | active | 2026-05-18 |  |
| `contradiction` | active | 2026-05-18 |  |
| `data_context_mismatch` | active | 2026-05-18 |  |
| `detail_trap` | active | 2026-05-18 |  |
| `direction_reversal` | active | 2026-05-18 |  |
| `evidence_relationship_blend` | active | 2026-05-18 |  |
| `extreme_language` | active | 2026-05-18 |  |
| `false_concession_trap` | active | 2026-05-18 |  |
| `figurative_literal_confusion` | active | 2026-05-18 |  |
| `indirect_evidence` | active | 2026-05-18 |  |
| `individual_inference_from_aggregate_bins` | active | 2026-05-18 |  |
| `inverted_logic` | active | 2026-05-18 |  |
| `keyword_matching` | active | 2026-05-18 |  |
| `local_maximum_trap` | active | 2026-05-18 |  |
| `local_semantic_role_mismatch` | active | 2026-05-18 |  |
| `outside_knowledge` | active | 2026-05-18 |  |
| `overreach` | active | 2026-05-18 |  |
| `overspecification` | active | 2026-05-18 |  |
| `overstated_position` | active | 2026-05-18 |  |
| `partial_match` | active | 2026-05-18 |  |
| `partial_purpose` | active | 2026-05-18 |  |
| `plausible_synonym` | active | 2026-05-18 |  |
| `polarity_mismatch` | active | 2026-05-18 |  |
| `reversed_attribution` | active | 2026-05-18 |  |
| `rhetorical_scope_shift` | active | 2026-05-18 |  |
| `same_direction_assumption` | active | 2026-05-18 |  |
| `scope_extension` | active | 2026-05-18 |  |
| `semantic_relatedness_without_precision` | active | 2026-05-18 |  |
| `single_measure_focus` | active | 2026-05-18 |  |
| `single_sector_focus` | active | 2026-05-18 |  |
| `textual_mimicry` | active | 2026-05-18 |  |
| `tone_register_mismatch` | active | 2026-05-18 |  |
| `topic_trap` | active | 2026-05-18 |  |
| `topical_relevance_without_logical_connection` | active | 2026-05-18 |  |
| `wrong_action_verb` | active | 2026-05-18 |  |
| `wrong_group_comparison` | active | 2026-05-18 |  |
| `wrong_scope` | active | 2026-05-18 |  |
| `wrong_table_row_or_column` | active | 2026-05-18 |  |
| `wrong_time_window` | active | 2026-05-18 |  |

### `READING_QUESTION_FAMILY_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading question families (subset of QUESTION_FAMILY_KEYS)
- **Entries:** 2

| Value | Status | Added | Description |
|---|---|---|---|
| `craft_and_structure` | active | 2026-05-18 |  |
| `information_and_ideas` | active | 2026-05-18 |  |

### `READING_SKILL_FAMILY_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading skill families
- **Entries:** 7

| Value | Status | Added | Description |
|---|---|---|---|
| `central_ideas_and_details` | active | 2026-05-18 |  |
| `command_of_evidence_quantitative` | active | 2026-05-18 |  |
| `command_of_evidence_textual` | active | 2026-05-18 |  |
| `cross_text_connections` | active | 2026-05-18 |  |
| `inferences` | active | 2026-05-18 |  |
| `text_structure_and_purpose` | active | 2026-05-18 |  |
| `words_in_context` | active | 2026-05-18 |  |

### `READING_FOCUS_BY_SKILL_FAMILY`

- **Kind:** hierarchical
- **Domain:** reading
- **Description:** Reading v2 reading_focus_key (grouped by skill family)
- **Entries:** 38

| Value | Status | Added | Description |
|---|---|---|---|
| `author_stance` | active | 2026-05-18 |  |
| `both_texts_agree` | active | 2026-05-18 |  |
| `causal_inference` | active | 2026-05-18 |  |
| `central_idea` | active | 2026-05-18 |  |
| `character_or_author_detail` | active | 2026-05-18 |  |
| `connotation_fit` | active | 2026-05-18 |  |
| `contextual_meaning` | active | 2026-05-18 |  |
| `cross_text_inference` | active | 2026-05-18 |  |
| `data_comparison` | active | 2026-05-18 |  |
| `data_completes_example` | active | 2026-05-18 |  |
| `data_supports_claim` | active | 2026-05-18 |  |
| `data_trend` | active | 2026-05-18 |  |
| `data_weakens_claim` | active | 2026-05-18 |  |
| `evidence_explains_claim` | active | 2026-05-18 |  |
| `evidence_illustrates_claim` | active | 2026-05-18 |  |
| `evidence_qualifies_claim` | active | 2026-05-18 |  |
| `evidence_supports_claim` | active | 2026-05-18 |  |
| `evidence_weakens_claim` | active | 2026-05-18 |  |
| `expectation_violation` | active | 2026-05-18 |  |
| `figurative_language_meaning` | active | 2026-05-18 |  |
| `implication_inference` | active | 2026-05-18 |  |
| `main_purpose` | active | 2026-05-18 |  |
| `methodological_critique` | active | 2026-05-18 |  |
| `motivational_inference` | active | 2026-05-18 |  |
| `overall_purpose` | active | 2026-05-18 |  |
| `passage_summary` | active | 2026-05-18 |  |
| `polarity_fit` | active | 2026-05-18 |  |
| `precision_fit` | active | 2026-05-18 |  |
| `predictive_inference` | active | 2026-05-18 |  |
| `register_fit` | active | 2026-05-18 |  |
| `sentence_function` | active | 2026-05-18 |  |
| `structural_pattern` | active | 2026-05-18 |  |
| `supporting_detail` | active | 2026-05-18 |  |
| `text2_contradicts_text1` | active | 2026-05-18 |  |
| `text2_qualifies_text1` | active | 2026-05-18 |  |
| `text2_response_to_text1` | active | 2026-05-18 |  |
| `texts_disagree` | active | 2026-05-18 |  |
| `underlined_word_meaning` | active | 2026-05-18 |  |

### `TEST_CONSTRUCT_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading v2 target_test_construct_key
- **Entries:** 7

| Value | Status | Added | Description |
|---|---|---|---|
| `contextual_semantic_precision` | active | 2026-05-18 |  |
| `cross_text_relationship_precision` | active | 2026-05-18 |  |
| `evidence_relation_precision` | active | 2026-05-18 |  |
| `figurative_interpretation_precision` | active | 2026-05-18 |  |
| `inference_boundary_control` | active | 2026-05-18 |  |
| `quantitative_constraint_tracking` | active | 2026-05-18 |  |
| `rhetorical_function_precision` | active | 2026-05-18 |  |

### `CRAFT_SUBCONSTRUCT_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading v2 target_craft_subconstruct_key
- **Entries:** 9

| Value | Status | Added | Description |
|---|---|---|---|
| `ctc_agreement_degree` | active | 2026-05-18 |  |
| `ctc_attribution_tracking` | active | 2026-05-18 |  |
| `ctc_response_to_claim` | active | 2026-05-18 |  |
| `tsp_author_action_precision` | active | 2026-05-18 |  |
| `tsp_global_rhetorical_purpose` | active | 2026-05-18 |  |
| `tsp_local_sentence_function` | active | 2026-05-18 |  |
| `wic_local_semantic_role` | active | 2026-05-18 |  |
| `wic_polarity_logic` | active | 2026-05-18 |  |
| `wic_tone_register_fit` | active | 2026-05-18 |  |

### `TEXT_RELATIONSHIP_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading v2 cross-text relationship keys
- **Entries:** 7

| Value | Status | Added | Description |
|---|---|---|---|
| `broad_support` | active | 2026-05-18 |  |
| `causal_specification` | active | 2026-05-18 |  |
| `confirmation_with_qualification` | active | 2026-05-18 |  |
| `direct_contradiction` | active | 2026-05-18 |  |
| `expectation_violation` | active | 2026-05-18 |  |
| `methodological_critique` | active | 2026-05-18 |  |
| `partial_agreement` | active | 2026-05-18 |  |

### `QUANTITATIVE_SUB_PATTERN_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading v2 quantitative_sub_pattern
- **Entries:** 8

| Value | Status | Added | Description |
|---|---|---|---|
| `all_measures` | active | 2026-05-18 |  |
| `binned_distribution` | active | 2026-05-18 |  |
| `composition_change` | active | 2026-05-18 |  |
| `exact_value_lookup` | active | 2026-05-18 |  |
| `repeated_highest` | active | 2026-05-18 |  |
| `standard` | active | 2026-05-18 |  |
| `timing_constrained` | active | 2026-05-18 |  |
| `two_variable_opposite` | active | 2026-05-18 |  |

### `SENTENCE_FUNCTION_ROLE_KEYS`

- **Kind:** flat
- **Domain:** reading
- **Description:** Reading v2 target_sentence_function_role
- **Entries:** 12

| Value | Status | Added | Description |
|---|---|---|---|
| `background_setup` | active | 2026-05-18 |  |
| `concession` | active | 2026-05-18 |  |
| `consequence` | active | 2026-05-18 |  |
| `contrast_motivation` | active | 2026-05-18 |  |
| `conventional_approach` | active | 2026-05-18 |  |
| `counter_evidence` | active | 2026-05-18 |  |
| `elaboration` | active | 2026-05-18 |  |
| `example` | active | 2026-05-18 |  |
| `hypothesis` | active | 2026-05-18 |  |
| `obstacle` | active | 2026-05-18 |  |
| `parenthetical_definition` | active | 2026-05-18 |  |
| `scope_qualification` | active | 2026-05-18 |  |

---

## Maintenance

1. Add or revise an entry in `vocabulary/master.json` (set `status`, `added`,
   `description`).
2. If adding a brand-new vocabulary, also add a matching REGISTRY entry in
   `scripts/gen_vocab.py` so `--generate` emits it with the right header comment.
   Declaring the constant in master.json alone is not enough — and conversely a
   REGISTRY entry without a master.json vocabulary gets stripped on `--generate`
   (the generator reads ONLY master.json). This was bug-813.
3. Run `scripts/gen_vocab.py --generate` to regenerate ontology.py, the rule-doc
   VOCAB blocks, and this file.
4. Run `scripts/gen_vocab.py --check` — must pass (no drift, candidates ≤ 10).
5. Review any new off-vocab keys in the admin **Vocabulary → Candidate Queue** tab
   and either alias-map them (`_STEM_ALIASES` in `extract_prompt.py`) or promote a
   canonical key via the rule-doc approval flow.

