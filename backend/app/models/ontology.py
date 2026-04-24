"""V3 allowed keys, enums, and constants.
Source: rules_agent_dsat_grammar_ingestion_generation_v3.md
"""

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
    "prose_plus_table", "prose_plus_graph", "notes_bullets", "poem",
)

# --- V3 §3.2 stem_type_key ---
STEM_TYPE_KEYS = (
    "complete_the_text", "choose_main_idea", "choose_main_purpose",
    "choose_structure_description", "choose_sentence_function",
    "choose_likely_response", "choose_best_support", "choose_best_quote",
    "choose_best_completion_from_data", "choose_best_grammar_revision",
    "choose_best_transition", "choose_best_notes_synthesis",
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
        "modifier_placement", "comparative_structures",
        "logical_predication", "relative_pronouns",
    ),
    "punctuation": (
        "punctuation_comma", "colon_dash_use", "semicolon_use",
        "conjunctive_adverb_usage", "apostrophe_use", "possessive_contraction",
        "appositive_punctuation", "hyphen_usage", "quotation_punctuation",
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
        "transition_logic",
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
    "rhetorical_irrelevance", "correct",
)

# --- V3 §10.3 plausibility_source_key ---
PLANSIBILITY_SOURCE_KEYS = (
    "nearest_noun_attraction", "punctuation_style_bias",
    "auditory_similarity", "grammar_fit_only",
    "formal_register_match", "common_idiom_pull", "none",
)

# --- V3 §3.3 answer_mechanism_key ---
ANSWER_MECHANISM_KEYS = (
    "rule_application", "pattern_matching",
    "evidence_location", "inference", "data_synthesis",
)

# --- V3 §3.3 solver_pattern_key ---
SOLVER_PATTERN_KEYS = (
    "apply_grammar_rule_directly", "locate_error_zone",
    "compare_register", "evaluate_transition",
    "synthesize_notes", "eliminate_by_boundary",
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
)

# --- question_family_key ---
QUESTION_FAMILY_KEYS = (
    "conventions_grammar", "expression_of_ideas",
    "craft_and_structure", "information_and_ideas",
)