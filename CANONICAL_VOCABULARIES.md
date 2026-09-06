# Canonical Vocabularies — Full Category & Key Listing

Source: `vocabulary/master.json` (schema_version 1). 49 categories.

> Canonical controlled vocabulary. Edit THIS file, then run scripts/gen_vocab.py --generate. ontology.py and the rules-doc VOCAB blocks are generated artefacts — do not hand-edit them.

## Index

- [`CONTENT_ORIGINS`](#content-origins) — Content origin
- [`JOB_TYPES`](#job-types) — Job types
- [`JOB_STATUSES`](#job-statuses) — Job statuses (state machine)
- [`PRACTICE_STATUSES`](#practice-statuses) — Practice status
- [`OVERLAP_STATUSES`](#overlap-statuses) — Overlap status
- [`RELATION_TYPES`](#relation-types) — Relation types
- [`ASSET_TYPES`](#asset-types) — Asset types
- [`CHANGE_SOURCES`](#change-sources) — Change sources
- [`STIMULUS_MODE_KEYS`](#stimulus-mode-keys) — V3 §3.1 stimulus_mode_key
- [`TEST_FORMAT_KEYS`](#test-format-keys) — Rules v8 generation format keys
- [`SOURCE_STATS_FORMAT_KEYS`](#source-stats-format-keys) — Rules v8 source stats format keys
- [`STEM_TYPE_KEYS`](#stem-type-keys) — V3 §3.2 stem_type_key
- [`GRAMMAR_ROLE_KEYS`](#grammar-role-keys) — V3 §5 grammar_role_key
- [`GRAMMAR_FOCUS_BY_ROLE`](#grammar-focus-by-role) — V3 §6 grammar_focus_key (grouped by role)
- [`SYNTACTIC_TRAP_KEYS`](#syntactic-trap-keys) — V3 §9 syntactic_trap_key
- [`SYNTACTIC_TRAP_REQUIRED_ROLES`](#syntactic-trap-required-roles) — Grammar roles that always require a non-null syntactic_trap_key (policy subset of GRAMMAR_ROLE_KEYS)
- [`DISTRACTOR_TYPE_KEYS`](#distractor-type-keys) — V3 §12.1 distractor_type_key (option-level)
- [`REASONING_TRAP_KEYS`](#reasoning-trap-keys) — Reading v2 §10 reasoning_trap_key (question-level)
- [`PLAUSIBILITY_SOURCE_KEYS`](#plausibility-source-keys) — V3 §10.3 plausibility_source_key
- [`ANSWER_MECHANISM_KEYS`](#answer-mechanism-keys) — V3 §3.3 answer_mechanism_key
- [`SOLVER_PATTERN_KEYS`](#solver-pattern-keys) — V3 §3.3 solver_pattern_key
- [`STUDENT_FAILURE_MODE_KEYS`](#student-failure-mode-keys) — V3 §21.3 student_failure_mode_key
- [`DISTRACTOR_DISTANCE_KEYS`](#distractor-distance-keys) — V3 §21.2 distractor_distance
- [`DIFFICULTY_KEYS`](#difficulty-keys) — V3 §3.3 difficulty keys
- [`FREQUENCY_BANDS`](#frequency-bands) — V3 §3.3 frequency bands
- [`TENSE_REGISTER_KEYS`](#tense-register-keys) — V3 §17.6 tense register keys
- [`PASSAGE_ARCHITECTURE_KEYS`](#passage-architecture-keys) — V3 §22 passage_architecture_key
- [`QUESTION_FAMILY_KEYS`](#question-family-keys) — question_family_key
- [`READING_QUESTION_FAMILY_KEYS`](#reading-question-family-keys) — Reading question families (subset of QUESTION_FAMILY_KEYS)
- [`GRAMMAR_QUESTION_FAMILY_KEYS`](#grammar-question-family-keys) — Grammar question families (subset of QUESTION_FAMILY_KEYS)
- [`READING_SKILL_FAMILY_KEYS`](#reading-skill-family-keys) — Reading skill families
- [`READING_FOCUS_BY_SKILL_FAMILY`](#reading-focus-by-skill-family) — Reading v2 reading_focus_key (grouped by skill family)
- [`TEST_CONSTRUCT_KEYS`](#test-construct-keys) — Reading v2 target_test_construct_key
- [`CRAFT_SUBCONSTRUCT_KEYS`](#craft-subconstruct-keys) — Reading v2 target_craft_subconstruct_key
- [`TEXT_RELATIONSHIP_KEYS`](#text-relationship-keys) — Reading v2 cross-text relationship keys
- [`QUANTITATIVE_SUB_PATTERN_KEYS`](#quantitative-sub-pattern-keys) — Reading v2 quantitative_sub_pattern
- [`SENTENCE_FUNCTION_ROLE_KEYS`](#sentence-function-role-keys) — Reading v2 target_sentence_function_role
- [`TRANSITION_SUBTYPE_KEYS`](#transition-subtype-keys) — Grammar v8 transition_subtype_key
- [`SYNTHESIS_GOAL_KEYS`](#synthesis-goal-keys) — Grammar v8 notes synthesis goal keys
- [`AUDIENCE_KNOWLEDGE_KEYS`](#audience-knowledge-keys) — Grammar v8 audience knowledge keys
- [`REQUIRED_CONTENT_KEYS`](#required-content-keys) — Grammar v8 required content keys
- [`SYNTHESIS_DISTRACTOR_FAILURE_KEYS`](#synthesis-distractor-failure-keys) — Grammar v8 synthesis distractor failure keys
- [`TOPIC_BROAD_KEYS`](#topic-broad-keys) — Broad topic keys
- [`REVIEW_TASK_TYPES`](#review-task-types) — Review task types for the generation review swarm
- [`REVIEW_STATUSES`](#review-statuses) — Per-reviewer outcome status
- [`REVIEW_RUN_STATUSES`](#review-run-statuses) — Review run lifecycle status
- [`TRIGGERED_BY_VALUES`](#triggered-by-values) — What triggered a review run
- [`REVIEW_VERDICTS`](#review-verdicts) — Per-reviewer verdict on a generated question
- [`CONSENSUS_VERDICTS`](#consensus-verdicts) — Consensus verdict after multi-model review (Phase 5)

---

## CONTENT_ORIGINS

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 3

_Content origin_

- `official`
- `unofficial`
- `generated`

---

## JOB_TYPES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 4

_Job types_

- `ingest`
- `generate`
- `reannotate`
- `overlap_check`

---

## JOB_STATUSES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 13

_Job statuses (state machine)_

- `pending`
- `parsing`
- `extracting`
- `generating`
- `annotating`
- `overlap_checking`
- `validating`
- `approved`
- `needs_review`
- `failed`
- `failed_transient` — Job failed with a transient error after auto-retry exhaustion (HTTP 429, 5xx, timeout, provider rate limit). Eligible for admin retry via /generate/batches/{id}/retry-failed.
- `failed_permanent` — Job failed with a non-recoverable error (malformed JSON after repair, model refusal, validation failure). Does not auto-retry; admin must regenerate-from-spec.
- `retrying` — Row-level guard set during a retry attempt to prevent duplicate concurrent retries of the same job.

---

## PRACTICE_STATUSES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 4

_Practice status_

- `draft`
- `active`
- `retired`
- `rejected` — Failed quality review; terminal state, audit-preserved. Distinct from retired (post-active removal).

---

## OVERLAP_STATUSES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 3

_Overlap status_

- `none`
- `possible`
- `confirmed`

---

## RELATION_TYPES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 5

_Relation types_

- `overlaps_official`
- `derived_from`
- `near_duplicate`
- `generated_from`
- `adapted_from`

---

## ASSET_TYPES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 6

_Asset types_

- `pdf`
- `image`
- `screenshot`
- `markdown`
- `json`
- `text`

---

## CHANGE_SOURCES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 4

_Change sources_

- `ingest`
- `generate`
- `admin_edit`
- `reprocess`

---

## STIMULUS_MODE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 9

_V3 §3.1 stimulus_mode_key_

- `sentence_only`
- `passage_excerpt`
- `prose_single`
- `prose_paired`
- `prose_plus_table`
- `prose_plus_graph`
- `notes_bullets`
- `notes_summary`
- `poem`

---

## TEST_FORMAT_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 2

_Rules v8 generation format keys_

- `digital_app_adaptive`
- `nondigital_linear_accommodation`

---

## SOURCE_STATS_FORMAT_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 2

_Rules v8 source stats format keys_

- `official_digital`
- `official_nondigital_linear`

---

## STEM_TYPE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 29

_V3 §3.2 stem_type_key_

- `complete_the_text`
- `choose_main_idea`
- `choose_main_purpose`
- `choose_structure_description`
- `choose_sentence_function`
- `choose_likely_response`
- `choose_best_support`
- `choose_best_quote`
- `choose_best_completion_from_data`
- `choose_best_grammar_revision`
- `choose_best_transition`
- `choose_best_notes_synthesis`
- `choose_words_in_context`
- `choose_word_in_context`
- `choose_cross_text_connection`
- `choose_text_relationship`
- `choose_agreement_across_texts`
- `choose_difference_across_texts`
- `choose_best_inference`
- `choose_command_of_evidence_textual`
- `choose_command_of_evidence_quantitative`
- `choose_central_detail`
- `choose_detail`
- `choose_best_illustration`
- `choose_best_weakener`
- `conform_to_standard_english`
- `most_logically_completes`
- `synthesize_information`
- `compare_contributions`

---

## GRAMMAR_ROLE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 8

_V3 §5 grammar_role_key_

- `sentence_boundary`
- `agreement`
- `verb_form`
- `modifier`
- `punctuation`
- `parallel_structure`
- `pronoun`
- `expression_of_ideas`

---

## GRAMMAR_FOCUS_BY_ROLE

**kind:** hierarchical &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 46 &nbsp;·&nbsp; **parent_set:** `GRAMMAR_ROLE_KEYS` &nbsp;·&nbsp; **derived_flat:** `GRAMMAR_FOCUS_KEYS`

_V3 §6 grammar_focus_key (grouped by role)_

- **sentence_boundary**
  - `sentence_fragment`
  - `comma_splice`
  - `run_on_sentence`
  - `sentence_boundary`
- **agreement**
  - `subject_verb_agreement`
  - `pronoun_antecedent_agreement`
  - `noun_countability`
  - `determiners_articles`
  - `affirmative_agreement`
- **verb_form**
  - `verb_tense_consistency`
  - `verb_form`
  - `voice_active_passive`
  - `negation`
- **modifier**
  - `modifier_placement`
  - `comparative_structures`
  - `illogical_comparison`
  - `adjective_adverb_distinction`
  - `logical_predication`
  - `relative_pronouns`
  - `absolute_phrase`
- **punctuation**
  - `punctuation_comma`
  - `colon_dash_use`
  - `semicolon_use`
  - `conjunctive_adverb_usage`
  - `apostrophe_use`
  - `possessive_contraction`
  - `appositive_punctuation`
  - `hyphen_usage`
  - `quotation_punctuation`
  - `unnecessary_internal_punctuation`
  - `end_punctuation_question_statement`
- **parallel_structure**
  - `parallel_structure`
  - `elliptical_constructions`
  - `conjunction_usage`
- **pronoun**
  - `pronoun_case`
  - `pronoun_clarity`
  - `pronoun_antecedent_agreement`
- **expression_of_ideas**
  - `redundancy_concision`
  - `precision_word_choice`
  - `register_style_consistency`
  - `logical_relationships`
  - `emphasis_meaning_shifts`
  - `data_interpretation_claims`
  - `transition_logic`
  - `commonly_confused_words`
  - `preposition_idiom`

---

## SYNTACTIC_TRAP_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 13

_V3 §9 syntactic_trap_key_

- `none`
- `nearest_noun_attraction`
- `garden_path`
- `early_clause_anchor`
- `nominalization_obscures_subject`
- `interruption_breaks_subject_verb`
- `long_distance_dependency`
- `pronoun_ambiguity`
- `scope_of_negation`
- `modifier_attachment_ambiguity`
- `presupposition_trap`
- `temporal_sequence_ambiguity`
- `multiple`

---

## SYNTACTIC_TRAP_REQUIRED_ROLES

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 5

_Grammar roles that always require a non-null syntactic_trap_key (policy subset of GRAMMAR_ROLE_KEYS)_

- `agreement`
- `pronoun`
- `modifier`
- `verb_form`
- `sentence_boundary`

---

## DISTRACTOR_TYPE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 45

_V3 §12.1 distractor_type_key (option-level)_

- `semantic_imprecision`
- `logical_mismatch`
- `scope_error`
- `tone_mismatch`
- `grammar_error`
- `punctuation_error`
- `transition_mismatch`
- `data_misread`
- `goal_mismatch`
- `partially_supported`
- `overstatement`
- `understatement`
- `rhetorical_irrelevance`
- `partial_match`
- `correct`
- `topical_relevance_without_logical_connection`
- `indirect_evidence`
- `inverted_logic`
- `detail_trap`
- `overreach`
- `data_context_mismatch`
- `connotation_mismatch`
- `plausible_synonym`
- `wrong_action_verb`
- `reversed_attribution`
- `confirmed_when_contradicted`
- `wrong_table_row_or_column`
- `wrong_group_comparison`
- `single_measure_focus`
- `local_maximum_trap`
- `same_direction_assumption`
- `absolute_value_confusion`
- `constraint_ignored`
- `individual_inference_from_aggregate_bins`
- `local_semantic_role_mismatch`
- `tone_register_mismatch`
- `rhetorical_scope_shift`
- `author_action_misclassification`
- `evidence_relationship_blend`
- `attribution_blend`
- `agreement_degree_mismatch`
- `cause_effect_misalignment`
- `contradiction`
- `figurative_literal_confusion`
- `false_concession_trap`

---

## REASONING_TRAP_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 49

_Reading v2 §10 reasoning_trap_key (question-level)_

- `topical_relevance_without_logical_connection`
- `partial_match`
- `indirect_evidence`
- `inverted_logic`
- `keyword_matching`
- `single_sector_focus`
- `data_context_mismatch`
- `detail_trap`
- `topic_trap`
- `overreach`
- `contradiction`
- `absolute_language`
- `outside_knowledge`
- `cause_effect_misalignment`
- `scope_extension`
- `overspecification`
- `wrong_time_window`
- `direction_reversal`
- `wrong_table_row_or_column`
- `wrong_group_comparison`
- `single_measure_focus`
- `local_maximum_trap`
- `same_direction_assumption`
- `absolute_value_confusion`
- `constraint_ignored`
- `individual_inference_from_aggregate_bins`
- `common_definition_trap`
- `semantic_relatedness_without_precision`
- `connotation_mismatch`
- `plausible_synonym`
- `also_true_trap`
- `wrong_scope`
- `wrong_action_verb`
- `overstated_position`
- `partial_purpose`
- `reversed_attribution`
- `extreme_language`
- `textual_mimicry`
- `confirmed_when_contradicted`
- `polarity_mismatch`
- `local_semantic_role_mismatch`
- `tone_register_mismatch`
- `rhetorical_scope_shift`
- `author_action_misclassification`
- `evidence_relationship_blend`
- `attribution_blend`
- `agreement_degree_mismatch`
- `figurative_literal_confusion`
- `false_concession_trap`

---

## PLAUSIBILITY_SOURCE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 15

_V3 §10.3 plausibility_source_key_

- `nearest_noun_attraction`
- `punctuation_style_bias`
- `auditory_similarity`
- `grammar_fit_only`
- `formal_register_match`
- `common_idiom_pull`
- `none`
- `passage_vocabulary_overlap`
- `topical_proximity`
- `partial_truth`
- `common_sense_appeal`
- `common_definition_appeal`
- `near_synonym_appeal`
- `rhetorical_surface_similarity`
- `attribution_swap`

---

## ANSWER_MECHANISM_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 10

_V3 §3.3 answer_mechanism_key_

- `rule_application`
- `pattern_matching`
- `evidence_location`
- `inference`
- `data_synthesis`
- `evidence_matching`
- `contextual_substitution`
- `rhetorical_classification`
- `cross_text_comparison`
- `polarity_resolution`

---

## SOLVER_PATTERN_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 16

_V3 §3.3 solver_pattern_key_

- `apply_grammar_rule_directly`
- `locate_error_zone`
- `compare_register`
- `evaluate_transition`
- `synthesize_notes`
- `eliminate_by_boundary`
- `locate_claim_then_match_evidence`
- `read_graphic_then_match_claim`
- `summarize_then_compare`
- `locate_detail_directly`
- `identify_logical_gap`
- `substitute_and_test`
- `classify_rhetorical_move`
- `summarize_both_then_compare`
- `apply_negation_logic`
- `locate_figurative_function`

---

## STUDENT_FAILURE_MODE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 63

_V3 §21.3 student_failure_mode_key_

- `nearest_noun_reflex`
- `comma_fix_illusion`
- `formal_word_bias`
- `longer_answer_bias`
- `punctuation_intimidation`
- `surface_similarity_bias`
- `scope_blindness`
- `modifier_hitchhike`
- `chronological_assumption`
- `extreme_word_trap`
- `overreading`
- `underreading`
- `grammar_fit_only`
- `register_confusion`
- `pronoun_anchor_error`
- `parallel_shape_bias`
- `transition_assumption`
- `idiom_memory_pull`
- `false_precision`
- `negation_blindness`
- `connotation_surface_match`
- `local_role_misread`
- `register_tone_blindness`
- `figurative_meaning_blindness`
- `exact_value_misread`
- `individual_from_aggregate`
- `all_measures_not_checked`
- `wrong_comparison_direction`
- `wrong_group_selected`
- `wrong_row_column_lookup`
- `single_measure_overread`
- `local_maximum_overread`
- `absolute_value_overweighting`
- `constraint_ignored`
- `two_part_claim_partial_match`
- `control_group_misidentification`
- `evidence_scope_mismatch`
- `subgroup_overgeneralization`
- `parenthetical_function_confusion`
- `rhetorical_verb_partial`
- `scope_role_confusion`
- `author_action_overread`
- `attribution_swap`
- `agreement_degree_overread`
- `relationship_simplification`
- `polarity_blindness`
- `tense_proximity_pull`
- `internal_unit_punctuation_insertion`
- `declarative_question_confusion`
- `restrictive_appositive_comma_insertion`
- `title_name_comma_insertion`
- `nonfinite_for_finite`
- `inflected_after_modal`
- `plural_pronoun_for_clause_antecedent`
- `past_tense_for_literary_present`
- `transition_wrong_direction`
- `notes_synthesis_wrong_goal`
- `notes_synthesis_audience_mismatch`
- `adverb_adjective_confusion`
- `illogical_comparison_blindness`
- `confused_word_substitution`
- `preposition_idiom_error`
- `notes_synthesis_content_omission`

---

## DISTRACTOR_DISTANCE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 3

_V3 §21.2 distractor_distance_

- `wide`
- `moderate`
- `tight`

---

## DIFFICULTY_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 3

_V3 §3.3 difficulty keys_

- `low`
- `medium`
- `high`

---

## FREQUENCY_BANDS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 5

_V3 §3.3 frequency bands_

- `very_high`
- `high`
- `medium`
- `low`
- `very_low`

---

## TENSE_REGISTER_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 7

_V3 §17.6 tense register keys_

- `narrative_past`
- `scientific_general_present`
- `historical_past`
- `study_procedure_past`
- `established_finding_present`
- `mixed_with_explicit_shift`
- `literary_present`

---

## PASSAGE_ARCHITECTURE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 25

_V3 §22 passage_architecture_key_

- `science_setup_finding_implication`
- `science_hypothesis_method_result`
- `history_claim_evidence_limitation`
- `history_assumption_revision`
- `literature_observation_interpretation_shift`
- `literature_character_conflict_reveal`
- `economics_theory_exception_example`
- `economics_problem_solution_tradeoff`
- `rhetoric_claim_counterclaim_resolution`
- `notes_fact_selection_contrast`
- `unexpected_finding`
- `cautionary_framing`
- `problem_solution`
- `compare_contrast`
- `chronological_sequence`
- `research_summary`
- `claim_evidence_explanation`
- `analogy_driven_argument`
- `multi_perspective_presentation`
- `qualification_restatement`
- `experiment_hypothesis_control_result`
- `indirect_effect_mediation`
- `alternative_explanation_ruled_out`
- `mechanism_manipulation_test`
- `studied_subgroup_generalization_limit`

---

## QUESTION_FAMILY_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 4

_question_family_key_

- `conventions_grammar`
- `expression_of_ideas`
- `craft_and_structure`
- `information_and_ideas`

---

## READING_QUESTION_FAMILY_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 2

_Reading question families (subset of QUESTION_FAMILY_KEYS)_

- `craft_and_structure`
- `information_and_ideas`

---

## GRAMMAR_QUESTION_FAMILY_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 2

_Grammar question families (subset of QUESTION_FAMILY_KEYS)_

- `conventions_grammar`
- `expression_of_ideas`

---

## READING_SKILL_FAMILY_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 7

_Reading skill families_

- `command_of_evidence_textual`
- `command_of_evidence_quantitative`
- `central_ideas_and_details`
- `inferences`
- `words_in_context`
- `text_structure_and_purpose`
- `cross_text_connections`

---

## READING_FOCUS_BY_SKILL_FAMILY

**kind:** hierarchical &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 38 &nbsp;·&nbsp; **parent_set:** `READING_SKILL_FAMILY_KEYS` &nbsp;·&nbsp; **derived_flat:** `READING_FOCUS_KEYS`

_Reading v2 reading_focus_key (grouped by skill family)_

- **command_of_evidence_textual**
  - `evidence_supports_claim`
  - `evidence_weakens_claim`
  - `evidence_illustrates_claim`
  - `evidence_explains_claim`
  - `evidence_qualifies_claim`
- **command_of_evidence_quantitative**
  - `data_supports_claim`
  - `data_weakens_claim`
  - `data_completes_example`
  - `data_comparison`
  - `data_trend`
- **central_ideas_and_details**
  - `central_idea`
  - `main_purpose`
  - `passage_summary`
  - `supporting_detail`
  - `character_or_author_detail`
- **inferences**
  - `causal_inference`
  - `motivational_inference`
  - `implication_inference`
  - `predictive_inference`
  - `cross_text_inference`
- **words_in_context**
  - `contextual_meaning`
  - `connotation_fit`
  - `precision_fit`
  - `register_fit`
  - `underlined_word_meaning`
  - `polarity_fit`
  - `figurative_language_meaning`
- **text_structure_and_purpose**
  - `overall_purpose`
  - `sentence_function`
  - `structural_pattern`
  - `author_stance`
- **cross_text_connections**
  - `text2_response_to_text1`
  - `both_texts_agree`
  - `texts_disagree`
  - `text2_qualifies_text1`
  - `text2_contradicts_text1`
  - `methodological_critique`
  - `expectation_violation`

---

## TEST_CONSTRUCT_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 7

_Reading v2 target_test_construct_key_

- `contextual_semantic_precision`
- `rhetorical_function_precision`
- `cross_text_relationship_precision`
- `evidence_relation_precision`
- `inference_boundary_control`
- `quantitative_constraint_tracking`
- `figurative_interpretation_precision`

---

## CRAFT_SUBCONSTRUCT_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 9

_Reading v2 target_craft_subconstruct_key_

- `wic_local_semantic_role`
- `wic_tone_register_fit`
- `wic_polarity_logic`
- `tsp_global_rhetorical_purpose`
- `tsp_local_sentence_function`
- `tsp_author_action_precision`
- `ctc_agreement_degree`
- `ctc_attribution_tracking`
- `ctc_response_to_claim`

---

## TEXT_RELATIONSHIP_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 7

_Reading v2 cross-text relationship keys_

- `direct_contradiction`
- `confirmation_with_qualification`
- `expectation_violation`
- `methodological_critique`
- `partial_agreement`
- `broad_support`
- `causal_specification`

---

## QUANTITATIVE_SUB_PATTERN_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 8

_Reading v2 quantitative_sub_pattern_

- `standard`
- `exact_value_lookup`
- `timing_constrained`
- `all_measures`
- `repeated_highest`
- `two_variable_opposite`
- `composition_change`
- `binned_distribution`

---

## SENTENCE_FUNCTION_ROLE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** reading &nbsp;·&nbsp; **count:** 12

_Reading v2 target_sentence_function_role_

- `concession`
- `elaboration`
- `contrast_motivation`
- `parenthetical_definition`
- `example`
- `consequence`
- `hypothesis`
- `counter_evidence`
- `scope_qualification`
- `conventional_approach`
- `obstacle`
- `background_setup`

---

## TRANSITION_SUBTYPE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 24

_Grammar v8 transition_subtype_key_

- `sequence_final_event`
- `contrast_refutation`
- `addition`
- `result_consequence`
- `chronology`
- `alternative`
- `emphasis_support`
- `causal_chain`
- `specificity_elaboration`
- `purpose_action`
- `frequency_difference`
- `simultaneity`
- `similarity`
- `appropriateness`
- `change_over_time`
- `exception`
- `final_realization`
- `converse_opposite`
- `present_continuation`
- `direct_refutation`
- `logical_consequence`
- `concession_qualification`
- `example`
- `restatement_clarification`

---

## SYNTHESIS_GOAL_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 42

_Grammar v8 notes synthesis goal keys_

- `emphasize_similarity`
- `emphasize_difference`
- `explain_advantage`
- `explain_mechanism`
- `present_research`
- `present_theory`
- `introduce_work`
- `describe_work`
- `emphasize_achievement`
- `make_generalization`
- `contrast_quantities`
- `compare_measurements`
- `emphasize_sample`
- `identify_category`
- `identify_profession`
- `identify_setting`
- `identify_title`
- `identify_year`
- `identify_duration`
- `identify_distance`
- `identify_author_pseudonym`
- `contrast_structural_types`
- `present_study_aim`
- `identify_statistical_method`
- `identify_statistical_authorship_method`
- `explain_technique_advantage`
- `explain_misconception_naming`
- `challenge_with_quotation`
- `challenge_explanation_with_quote`
- `present_study_overview`
- `present_methodology`
- `present_study_conclusions`
- `emphasize_significance`
- `explain_format_advantage`
- `emphasize_duration_and_purpose`
- `emphasize_size_similarity`
- `contrast_origins`
- `provide_historical_overview`
- `contrast_formal_structures`
- `contextualize_changing_beliefs`
- `compare_hypothesis_scope`
- `emphasize_age_similarity`

---

## AUDIENCE_KNOWLEDGE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 3

_Grammar v8 audience knowledge keys_

- `audience_familiar`
- `audience_unfamiliar`
- `not_specified`

---

## REQUIRED_CONTENT_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 32

_Grammar v8 required content keys_

- `comparison_needed`
- `definition_needed`
- `background_omit`
- `measurement_values_needed`
- `result_needed`
- `title_and_content_needed`
- `achievement_needed`
- `owner_of_achievement_needed`
- `category_label_needed`
- `sample_location_needed`
- `profession_label_needed`
- `setting_needed`
- `year_needed`
- `duration_needed`
- `distance_needed`
- `author_identity_needed`
- `mechanism_needed`
- `structural_roles_needed`
- `study_aim_needed`
- `statistical_method_needed`
- `misconception_needed`
- `quotation_needed`
- `study_finding_summary_needed`
- `method_needed`
- `conclusion_needed`
- `significance_needed`
- `advantage_needed`
- `purpose_needed`
- `origin_labels_needed`
- `timeline_needed`
- `formal_feature_labels_needed`
- `scope_terms_needed`

---

## SYNTHESIS_DISTRACTOR_FAILURE_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** grammar &nbsp;·&nbsp; **count:** 8

_Grammar v8 synthesis distractor failure keys_

- `wrong_goal`
- `omits_required_content`
- `adds_background_audience_does_not_need`
- `correct_topic_wrong_comparison`
- `omits_unfamiliar_context`
- `wrong_audience_assumption`
- `misstates_required_relationship`
- `irrelevant_background`

---

## TOPIC_BROAD_KEYS

**kind:** flat &nbsp;·&nbsp; **domain:** shared &nbsp;·&nbsp; **count:** 9

_Broad topic keys_

- `science`
- `history`
- `literature`
- `social_studies`
- `humanities`
- `arts`
- `economics`
- `technology`
- `environment`

---

## REVIEW_TASK_TYPES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 1

_Review task types for the generation review swarm_

- `generation_realism_review` — Multi-model quality review of generated DSAT questions

---

## REVIEW_STATUSES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 3

_Per-reviewer outcome status_

- `ok` — Review completed successfully
- `transient_failed` — Review failed due to transient error (rate limit, network)
- `permanent_failed` — Review failed permanently (malformed output, model refusal)

---

## REVIEW_RUN_STATUSES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 4

_Review run lifecycle status_

- `running` — Review run in progress
- `complete` — All reviewers completed successfully
- `partial` — Some reviewers failed but minimum completed
- `failed` — Review run failed entirely

---

## TRIGGERED_BY_VALUES

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 5

_What triggered a review run_

- `auto_on_save` — Automatically triggered when a generated question is saved
- `manual_question` — Admin manually triggered review for a single question
- `manual_batch` — Admin manually triggered review for a batch
- `recalibration` — Re-review triggered by calibration threshold change
- `rubric_bump` — Re-review triggered by rubric version change

---

## REVIEW_VERDICTS

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 3

_Per-reviewer verdict on a generated question_

- `accept` — Question meets all quality thresholds
- `needs_human_review` — Borderline quality; human review recommended
- `reject` — Question fails quality thresholds

---

## CONSENSUS_VERDICTS

**kind:** flat &nbsp;·&nbsp; **domain:** system &nbsp;·&nbsp; **count:** 5

_Consensus verdict after multi-model review (Phase 5)_

- `admin_review_ready` — All thresholds cleared; ready for admin review
- `reject_recommended` — Consensus recommends rejection
- `regenerate_recommended` — Consensus recommends regeneration
- `blocked_overlap` — Unresolved official overlap blocks approval
- `insufficient_reviews` — Fewer than 2 reviewers succeeded

---
