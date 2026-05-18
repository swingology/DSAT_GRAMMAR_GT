"""Allowed keys, enums, and constants for the current DSAT ruleset."""

# --- Content origin ---
CONTENT_ORIGINS = ("official", "unofficial", "generated")

# --- Job types ---
JOB_TYPES = ("ingest", "generate", "reannotate", "overlap_check")

# --- Job statuses (state machine) ---
JOB_STATUSES = (
    "pending", "parsing", "extracting", "generating",
    "annotating", "overlap_checking", "validating",
    "approved", "needs_review", "failed",
)

# --- Practice status ---
PRACTICE_STATUSES = ("draft", "active", "retired")

# --- Overlap status ---
OVERLAP_STATUSES = ("none", "possible", "confirmed")

# --- Relation types ---
RELATION_TYPES = (
    "overlaps_official", "derived_from", "near_duplicate",
    "generated_from", "adapted_from",
)

# --- Asset types ---
ASSET_TYPES = ("pdf", "image", "screenshot", "markdown", "json", "text")

# --- Change sources ---
CHANGE_SOURCES = ("ingest", "generate", "admin_edit", "reprocess")

# --- V3 §3.1 stimulus_mode_key ---
STIMULUS_MODE_KEYS = (
    "sentence_only", "passage_excerpt", "prose_single", "prose_paired",
    "prose_plus_table", "prose_plus_graph", "notes_bullets", "notes_summary",
    "poem",
)

# --- Rules v7 generation format keys ---
TEST_FORMAT_KEYS = ("digital_app_adaptive", "nondigital_linear_accommodation")

SOURCE_STATS_FORMAT_KEYS = ("official_digital", "official_nondigital_linear")

# --- V3 §3.2 stem_type_key ---
STEM_TYPE_KEYS = (
    "complete_the_text", "choose_main_idea", "choose_main_purpose",
    "choose_structure_description", "choose_sentence_function",
    "choose_likely_response", "choose_best_support", "choose_best_quote",
    "choose_best_completion_from_data", "choose_best_grammar_revision",
    "choose_best_transition", "choose_best_notes_synthesis",
    "choose_words_in_context", "choose_word_in_context", "choose_cross_text_connection",
    "choose_text_relationship", "choose_agreement_across_texts",
    "choose_difference_across_texts", "choose_best_inference",
    "choose_command_of_evidence_textual", "choose_command_of_evidence_quantitative",
    "choose_central_detail", "choose_detail", "choose_best_illustration",
    "choose_best_weakener",
    # --- Additional stem types observed from LLM output (rules v7 / reading v2) ---
    "conform_to_standard_english",    # grammar v7: SEC complete_the_text with standard English convention
    "most_logically_completes",      # reading v2: "Which choice most logically completes the text?"
    "synthesize_information",         # reading v2: synthesize from notes/data
    "compare_contributions",          # reading v2: compare contributions across texts
)

# --- V3 §5 grammar_role_key ---
GRAMMAR_ROLE_KEYS = (
    "sentence_boundary", "agreement", "verb_form", "modifier",
    "punctuation", "parallel_structure", "pronoun", "expression_of_ideas",
)

# --- V3 §6 grammar_focus_key (grouped by role) ---
GRAMMAR_FOCUS_BY_ROLE = {
    "sentence_boundary": (
        "sentence_fragment", "comma_splice", "run_on_sentence", "sentence_boundary",
    ),
    "agreement": (
        "subject_verb_agreement", "pronoun_antecedent_agreement",
        "noun_countability", "determiners_articles", "affirmative_agreement",
    ),
    "verb_form": (
        "verb_tense_consistency", "verb_form", "voice_active_passive", "negation",
    ),
    "modifier": (
        "modifier_placement", "comparative_structures", "illogical_comparison",
        "adjective_adverb_distinction",
        "logical_predication", "relative_pronouns",
    ),
    "punctuation": (
        "punctuation_comma", "colon_dash_use", "semicolon_use",
        "conjunctive_adverb_usage", "apostrophe_use", "possessive_contraction",
        "appositive_punctuation", "hyphen_usage", "quotation_punctuation",
        "unnecessary_internal_punctuation", "end_punctuation_question_statement",
    ),
    "parallel_structure": (
        "parallel_structure", "elliptical_constructions", "conjunction_usage",
    ),
    "pronoun": (
        "pronoun_case", "pronoun_clarity", "pronoun_antecedent_agreement",
    ),
    "expression_of_ideas": (
        "redundancy_concision", "precision_word_choice",
        "register_style_consistency", "logical_relationships",
        "emphasis_meaning_shifts", "data_interpretation_claims",
        "transition_logic", "commonly_confused_words", "preposition_idiom",
    ),
}

# Flat set of all grammar focus keys
GRAMMAR_FOCUS_KEYS = tuple(
    k for keys in GRAMMAR_FOCUS_BY_ROLE.values() for k in keys
)

# --- V3 §9 syntactic_trap_key ---
SYNTACTIC_TRAP_KEYS = (
    "none", "nearest_noun_attraction", "garden_path",
    "early_clause_anchor", "nominalization_obscures_subject",
    "interruption_breaks_subject_verb", "long_distance_dependency",
    "pronoun_ambiguity", "scope_of_negation",
    "modifier_attachment_ambiguity", "presupposition_trap",
    "temporal_sequence_ambiguity", "multiple",
)

# --- V3 §10.2 distractor_type_key ---
DISTRACTOR_TYPE_KEYS = (
    "semantic_imprecision", "logical_mismatch", "scope_error",
    "tone_mismatch", "grammar_error", "punctuation_error",
    "transition_mismatch", "data_misread", "goal_mismatch",
    "partially_supported", "overstatement", "understatement",
    "rhetorical_irrelevance", "partial_match", "correct",
    # --- Reading v2 option-level distractor types ---
    "topical_relevance_without_logical_connection", "indirect_evidence",
    "inverted_logic", "detail_trap", "overreach", "data_context_mismatch",
    "connotation_mismatch", "plausible_synonym", "wrong_action_verb",
    "reversed_attribution", "confirmed_when_contradicted",
    "wrong_table_row_or_column", "wrong_group_comparison",
    "single_measure_focus", "local_maximum_trap", "same_direction_assumption",
    "absolute_value_confusion", "constraint_ignored",
    "individual_inference_from_aggregate_bins", "local_semantic_role_mismatch",
    "tone_register_mismatch", "rhetorical_scope_shift",
    "author_action_misclassification", "evidence_relationship_blend",
    "attribution_blend", "agreement_degree_mismatch",
    "cause_effect_misalignment", "contradiction",
    "figurative_literal_confusion", "false_concession_trap",
)

# --- Reading v2 §10 reasoning_trap_key (question-level wrong-answer mechanism) ---
# Distinct from DISTRACTOR_TYPE_KEYS (§12.1, option-level). The two vocabularies
# overlap but are not interchangeable. §10 was deduplicated: wrong_row_or_column,
# individual_from_aggregate, and all_measures_not_checked were merged into
# wrong_table_row_or_column, individual_inference_from_aggregate_bins, and
# single_measure_focus respectively.
REASONING_TRAP_KEYS = (
    # --- §10.1 Information and Ideas ---
    "topical_relevance_without_logical_connection", "partial_match",
    "indirect_evidence", "inverted_logic", "keyword_matching",
    "single_sector_focus", "data_context_mismatch", "detail_trap",
    "topic_trap", "overreach", "contradiction", "absolute_language",
    "outside_knowledge", "cause_effect_misalignment", "scope_extension",
    "overspecification", "wrong_time_window", "direction_reversal",
    "wrong_table_row_or_column", "wrong_group_comparison", "single_measure_focus",
    "local_maximum_trap", "same_direction_assumption", "absolute_value_confusion",
    "constraint_ignored", "individual_inference_from_aggregate_bins",
    # --- §10.2 Craft and Structure ---
    "common_definition_trap", "semantic_relatedness_without_precision",
    "connotation_mismatch", "plausible_synonym", "also_true_trap",
    "wrong_scope", "wrong_action_verb", "overstated_position", "partial_purpose",
    "reversed_attribution", "extreme_language", "textual_mimicry",
    "confirmed_when_contradicted", "polarity_mismatch",
    "local_semantic_role_mismatch", "tone_register_mismatch",
    "rhetorical_scope_shift", "author_action_misclassification",
    "evidence_relationship_blend", "attribution_blend",
    "agreement_degree_mismatch", "figurative_literal_confusion",
    "false_concession_trap",
)

# --- V3 §10.3 plausibility_source_key ---
PLANSIBILITY_SOURCE_KEYS = (
    "nearest_noun_attraction", "punctuation_style_bias",
    "auditory_similarity", "grammar_fit_only",
    "formal_register_match", "common_idiom_pull", "none",
    # --- Reading v2 plausibility sources ---
    "passage_vocabulary_overlap", "topical_proximity", "partial_truth",
    "common_sense_appeal", "common_definition_appeal", "near_synonym_appeal",
    "rhetorical_surface_similarity", "attribution_swap",
)

# --- V3 §3.3 answer_mechanism_key ---
ANSWER_MECHANISM_KEYS = (
    "rule_application", "pattern_matching",
    "evidence_location", "inference", "data_synthesis",
    # --- Reading v2 mechanisms ---
    "evidence_matching", "contextual_substitution",
    "rhetorical_classification", "cross_text_comparison",
    "polarity_resolution",
)

# --- V3 §3.3 solver_pattern_key ---
SOLVER_PATTERN_KEYS = (
    "apply_grammar_rule_directly", "locate_error_zone",
    "compare_register", "evaluate_transition",
    "synthesize_notes", "eliminate_by_boundary",
    # --- Reading v2 solver patterns ---
    "locate_claim_then_match_evidence", "read_graphic_then_match_claim",
    "summarize_then_compare", "locate_detail_directly",
    "identify_logical_gap", "substitute_and_test",
    "classify_rhetorical_move", "summarize_both_then_compare",
    "apply_negation_logic", "locate_figurative_function",
)

# --- V3 §21.3 student_failure_mode_key ---
STUDENT_FAILURE_MODE_KEYS = (
    "nearest_noun_reflex", "comma_fix_illusion", "formal_word_bias",
    "longer_answer_bias", "punctuation_intimidation",
    "surface_similarity_bias", "scope_blindness",
    "modifier_hitchhike", "chronological_assumption",
    "extreme_word_trap", "overreading", "underreading",
    "grammar_fit_only", "register_confusion",
    "pronoun_anchor_error", "parallel_shape_bias",
    "transition_assumption", "idiom_memory_pull",
    "false_precision",
    # --- Reading v2 student failure modes ---
    "negation_blindness", "connotation_surface_match", "local_role_misread",
    "register_tone_blindness", "figurative_meaning_blindness",
    "exact_value_misread", "individual_from_aggregate",
    "all_measures_not_checked", "wrong_comparison_direction",
    "wrong_group_selected", "wrong_row_column_lookup",
    "single_measure_overread", "local_maximum_overread",
    "absolute_value_overweighting", "constraint_ignored",
    "two_part_claim_partial_match", "control_group_misidentification",
    "evidence_scope_mismatch", "subgroup_overgeneralization",
    "parenthetical_function_confusion", "rhetorical_verb_partial",
    "scope_role_confusion", "author_action_overread",
    "attribution_swap", "agreement_degree_overread",
    "relationship_simplification",
    # --- Reading v2 §19 approved synonym ---
    "polarity_blindness",                 # reading v2 §19.1/§19.7: synonym of negation_blindness
    # --- Grammar v7 §D.7 grammar-specific failure modes (mandatory on every distractor) ---
    "tense_proximity_pull", "internal_unit_punctuation_insertion",
    "declarative_question_confusion", "restrictive_appositive_comma_insertion",
    "title_name_comma_insertion", "nonfinite_for_finite",
    "inflected_after_modal", "plural_pronoun_for_clause_antecedent",
    "past_tense_for_literary_present", "transition_wrong_direction",
    "notes_synthesis_wrong_goal", "notes_synthesis_audience_mismatch",
    "adverb_adjective_confusion", "illogical_comparison_blindness",
    "confused_word_substitution", "preposition_idiom_error",
    "notes_synthesis_content_omission",
)

# --- V3 §21.2 distractor_distance ---
DISTRACTOR_DISTANCE_KEYS = ("wide", "moderate", "tight")

# --- V3 §3.3 difficulty keys ---
DIFFICULTY_KEYS = ("low", "medium", "high")

# --- V3 §3.3 frequency bands ---
FREQUENCY_BANDS = ("very_high", "high", "medium", "low", "very_low")

# --- V3 §17.6 tense register keys ---
TENSE_REGISTER_KEYS = (
    "narrative_past", "scientific_general_present",
    "historical_past", "study_procedure_past",
    "established_finding_present", "mixed_with_explicit_shift",
    "literary_present",
)

# --- V3 §22 passage_architecture_key ---
PASSAGE_ARCHITECTURE_KEYS = (
    "science_setup_finding_implication", "science_hypothesis_method_result",
    "history_claim_evidence_limitation", "history_assumption_revision",
    "literature_observation_interpretation_shift",
    "literature_character_conflict_reveal",
    "economics_theory_exception_example",
    "economics_problem_solution_tradeoff",
    "rhetoric_claim_counterclaim_resolution",
    "notes_fact_selection_contrast",
    # --- Reading v2 general passage architectures ---
    "unexpected_finding", "cautionary_framing", "problem_solution",
    "compare_contrast", "chronological_sequence", "research_summary",
    "claim_evidence_explanation", "analogy_driven_argument",
    "multi_perspective_presentation", "qualification_restatement",
    # --- Rules v7 / reading v2 experimental architectures ---
    "experiment_hypothesis_control_result", "indirect_effect_mediation",
    "alternative_explanation_ruled_out", "mechanism_manipulation_test",
    "studied_subgroup_generalization_limit",
)

# --- question_family_key ---
QUESTION_FAMILY_KEYS = (
    "conventions_grammar", "expression_of_ideas",
    "craft_and_structure", "information_and_ideas",
)

READING_QUESTION_FAMILY_KEYS = ("craft_and_structure", "information_and_ideas")

READING_SKILL_FAMILY_KEYS = (
    "command_of_evidence_textual",
    "command_of_evidence_quantitative",
    "central_ideas_and_details",
    "inferences",
    "words_in_context",
    "text_structure_and_purpose",
    "cross_text_connections",
)

READING_FOCUS_BY_SKILL_FAMILY = {
    "command_of_evidence_textual": (
        "evidence_supports_claim", "evidence_weakens_claim",
        "evidence_illustrates_claim", "evidence_explains_claim",
        "evidence_qualifies_claim",
    ),
    "command_of_evidence_quantitative": (
        "data_supports_claim", "data_weakens_claim",
        "data_completes_example", "data_comparison", "data_trend",
    ),
    "central_ideas_and_details": (
        "central_idea", "main_purpose", "passage_summary",
        "supporting_detail", "character_or_author_detail",
    ),
    "inferences": (
        "causal_inference", "motivational_inference",
        "implication_inference", "predictive_inference",
        "cross_text_inference",
    ),
    "words_in_context": (
        "contextual_meaning", "connotation_fit", "precision_fit",
        "register_fit", "underlined_word_meaning", "polarity_fit",
        "figurative_language_meaning",
    ),
    "text_structure_and_purpose": (
        "overall_purpose", "sentence_function", "structural_pattern",
        "author_stance",
    ),
    "cross_text_connections": (
        "text2_response_to_text1", "both_texts_agree", "texts_disagree",
        "text2_qualifies_text1", "text2_contradicts_text1",
        "methodological_critique", "expectation_violation",
    ),
}

READING_FOCUS_KEYS = tuple(
    k for keys in READING_FOCUS_BY_SKILL_FAMILY.values() for k in keys
)

# --- Reading v2 target_test_construct_key ---
TEST_CONSTRUCT_KEYS = (
    "contextual_semantic_precision", "rhetorical_function_precision",
    "cross_text_relationship_precision", "evidence_relation_precision",
    "inference_boundary_control", "quantitative_constraint_tracking",
    "figurative_interpretation_precision",
)

# --- Reading v2 target_craft_subconstruct_key ---
CRAFT_SUBCONSTRUCT_KEYS = (
    "wic_local_semantic_role", "wic_tone_register_fit", "wic_polarity_logic",
    "tsp_global_rhetorical_purpose", "tsp_local_sentence_function",
    "tsp_author_action_precision", "ctc_agreement_degree",
    "ctc_attribution_tracking", "ctc_response_to_claim",
)

# --- Reading v2 cross-text relationship keys ---
TEXT_RELATIONSHIP_KEYS = (
    "direct_contradiction", "confirmation_with_qualification",
    "expectation_violation", "methodological_critique", "partial_agreement",
    "broad_support", "causal_specification",
)

# --- Reading v2 quantitative_sub_pattern ---
QUANTITATIVE_SUB_PATTERN_KEYS = (
    "standard", "exact_value_lookup", "timing_constrained", "all_measures",
    "repeated_highest", "two_variable_opposite", "composition_change",
    "binned_distribution",
)

# --- Reading v2 target_sentence_function_role ---
SENTENCE_FUNCTION_ROLE_KEYS = (
    "concession", "elaboration", "contrast_motivation",
    "parenthetical_definition", "example", "consequence", "hypothesis",
    "counter_evidence", "scope_qualification", "conventional_approach",
    "obstacle", "background_setup",
)

# --- Grammar v7 transition_subtype_key ---
TRANSITION_SUBTYPE_KEYS = (
    "sequence_final_event", "contrast_refutation", "addition",
    "result_consequence", "chronology", "alternative", "emphasis_support",
    "causal_chain", "specificity_elaboration", "purpose_action",
    "frequency_difference", "simultaneity", "similarity", "appropriateness",
    "change_over_time", "exception", "final_realization",
    "converse_opposite", "present_continuation", "direct_refutation",
    "logical_consequence", "concession_qualification", "example",
    "restatement_clarification",
)

# --- Grammar v7 notes synthesis keys ---
SYNTHESIS_GOAL_KEYS = (
    "emphasize_similarity", "emphasize_difference", "explain_advantage",
    "explain_mechanism", "present_research", "present_theory",
    "introduce_work", "describe_work", "emphasize_achievement",
    "make_generalization", "contrast_quantities", "compare_measurements",
    "emphasize_sample", "identify_category", "identify_profession",
    "identify_setting", "identify_title", "identify_year",
    "identify_duration", "identify_distance", "identify_author_pseudonym",
    "contrast_structural_types", "present_study_aim",
    "identify_statistical_method", "identify_statistical_authorship_method",
    "explain_technique_advantage", "explain_misconception_naming",
    "challenge_with_quotation", "challenge_explanation_with_quote",
    "present_study_overview", "present_methodology",
    "present_study_conclusions", "emphasize_significance",
    "explain_format_advantage", "emphasize_duration_and_purpose",
    "emphasize_size_similarity", "contrast_origins",
    "provide_historical_overview", "contrast_formal_structures",
    "contextualize_changing_beliefs", "compare_hypothesis_scope",
    "emphasize_age_similarity",
)

AUDIENCE_KNOWLEDGE_KEYS = (
    "audience_familiar", "audience_unfamiliar", "not_specified",
)

REQUIRED_CONTENT_KEYS = (
    "comparison_needed", "definition_needed", "background_omit",
    "measurement_values_needed", "result_needed", "title_and_content_needed",
    "achievement_needed", "owner_of_achievement_needed",
    "category_label_needed", "sample_location_needed",
    "profession_label_needed", "setting_needed", "year_needed",
    "duration_needed", "distance_needed", "author_identity_needed",
    "mechanism_needed", "structural_roles_needed", "study_aim_needed",
    "statistical_method_needed", "misconception_needed", "quotation_needed",
    "study_finding_summary_needed", "method_needed", "conclusion_needed",
    "significance_needed", "advantage_needed", "purpose_needed",
    "origin_labels_needed", "timeline_needed", "formal_feature_labels_needed",
    "scope_terms_needed",
)

SYNTHESIS_DISTRACTOR_FAILURE_KEYS = (
    "wrong_goal", "omits_required_content",
    "adds_background_audience_does_not_need",
    "correct_topic_wrong_comparison", "omits_unfamiliar_context",
    "wrong_audience_assumption", "misstates_required_relationship",
    "irrelevant_background",
)

TOPIC_BROAD_KEYS = (
    "science", "history", "literature", "social_studies", "humanities",
    "arts", "economics", "technology", "environment",
)
