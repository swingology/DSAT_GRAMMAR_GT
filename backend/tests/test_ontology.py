from app.models.ontology import (
    CONTENT_ORIGINS, JOB_TYPES, JOB_STATUSES, PRACTICE_STATUSES,
    OVERLAP_STATUSES, RELATION_TYPES, ASSET_TYPES, CHANGE_SOURCES,
    GRAMMAR_ROLE_KEYS, GRAMMAR_FOCUS_KEYS, SYNTACTIC_TRAP_KEYS,
    STIMULUS_MODE_KEYS, STEM_TYPE_KEYS, DISTRACTOR_TYPE_KEYS,
    PLAUSIBILITY_SOURCE_KEYS, ANSWER_MECHANISM_KEYS, SOLVER_PATTERN_KEYS,
    READING_SKILL_FAMILY_KEYS, READING_FOCUS_KEYS,
    PASSAGE_ARCHITECTURE_KEYS, STUDENT_FAILURE_MODE_KEYS,
    TEST_CONSTRUCT_KEYS, CRAFT_SUBCONSTRUCT_KEYS, TEXT_RELATIONSHIP_KEYS,
    QUANTITATIVE_SUB_PATTERN_KEYS, SENTENCE_FUNCTION_ROLE_KEYS,
    TRANSITION_SUBTYPE_KEYS, SYNTHESIS_GOAL_KEYS, AUDIENCE_KNOWLEDGE_KEYS,
    REQUIRED_CONTENT_KEYS, SYNTHESIS_DISTRACTOR_FAILURE_KEYS, TOPIC_BROAD_KEYS,
)


def test_content_origins():
    assert set(CONTENT_ORIGINS) == {"official", "unofficial", "generated"}


def test_job_statuses():
    assert "pending" in JOB_STATUSES
    assert "failed" in JOB_STATUSES
    assert "approved" in JOB_STATUSES


def test_grammar_role_keys():
    assert "sentence_boundary" in GRAMMAR_ROLE_KEYS
    assert "agreement" in GRAMMAR_ROLE_KEYS
    assert "expression_of_ideas" in GRAMMAR_ROLE_KEYS


def test_grammar_focus_by_role():
    from app.models.ontology import GRAMMAR_FOCUS_BY_ROLE
    assert "subject_verb_agreement" in GRAMMAR_FOCUS_BY_ROLE["agreement"]
    assert "punctuation_comma" in GRAMMAR_FOCUS_BY_ROLE["punctuation"]


def test_syntactic_trap_keys():
    assert "nearest_noun_attraction" in SYNTACTIC_TRAP_KEYS
    assert "none" in SYNTACTIC_TRAP_KEYS


def test_v7_grammar_focus_keys():
    assert "adjective_adverb_distinction" in GRAMMAR_FOCUS_KEYS
    assert "illogical_comparison" in GRAMMAR_FOCUS_KEYS
    assert "commonly_confused_words" in GRAMMAR_FOCUS_KEYS
    assert "preposition_idiom" in GRAMMAR_FOCUS_KEYS


def test_reading_taxonomy_keys():
    assert "command_of_evidence_textual" in READING_SKILL_FAMILY_KEYS
    assert "cross_text_connections" in READING_SKILL_FAMILY_KEYS
    assert "polarity_fit" in READING_FOCUS_KEYS
    assert "text2_response_to_text1" in READING_FOCUS_KEYS


def test_reading_v2_mechanism_and_solver_keys():
    assert "evidence_matching" in ANSWER_MECHANISM_KEYS
    assert "contextual_substitution" in ANSWER_MECHANISM_KEYS
    assert "polarity_resolution" in ANSWER_MECHANISM_KEYS
    assert "locate_claim_then_match_evidence" in SOLVER_PATTERN_KEYS
    assert "apply_negation_logic" in SOLVER_PATTERN_KEYS
    assert "locate_figurative_function" in SOLVER_PATTERN_KEYS


def test_reading_v2_option_analysis_keys():
    assert "topical_relevance_without_logical_connection" in DISTRACTOR_TYPE_KEYS
    assert "wrong_table_row_or_column" in DISTRACTOR_TYPE_KEYS
    assert "figurative_literal_confusion" in DISTRACTOR_TYPE_KEYS
    assert "passage_vocabulary_overlap" in PLAUSIBILITY_SOURCE_KEYS
    assert "near_synonym_appeal" in PLAUSIBILITY_SOURCE_KEYS
    assert "rhetorical_surface_similarity" in PLAUSIBILITY_SOURCE_KEYS
    assert "figurative_meaning_blindness" in STUDENT_FAILURE_MODE_KEYS
    assert "subgroup_overgeneralization" in STUDENT_FAILURE_MODE_KEYS


def test_reading_v2_generation_profile_keys():
    assert "figurative_interpretation_precision" in TEST_CONSTRUCT_KEYS
    assert "ctc_attribution_tracking" in CRAFT_SUBCONSTRUCT_KEYS
    assert "causal_specification" in TEXT_RELATIONSHIP_KEYS
    assert "binned_distribution" in QUANTITATIVE_SUB_PATTERN_KEYS
    assert "scope_qualification" in SENTENCE_FUNCTION_ROLE_KEYS


def test_v7_grammar_generation_keys():
    assert "restatement_clarification" in TRANSITION_SUBTYPE_KEYS
    assert "challenge_explanation_with_quote" in SYNTHESIS_GOAL_KEYS
    assert "audience_unfamiliar" in AUDIENCE_KNOWLEDGE_KEYS
    assert "scope_terms_needed" in REQUIRED_CONTENT_KEYS
    assert "misstates_required_relationship" in SYNTHESIS_DISTRACTOR_FAILURE_KEYS
    assert "humanities" in TOPIC_BROAD_KEYS


def test_shared_passage_architectures_include_guardrail_additions():
    assert "analogy_driven_argument" in PASSAGE_ARCHITECTURE_KEYS
    assert "experiment_hypothesis_control_result" in PASSAGE_ARCHITECTURE_KEYS
    assert "studied_subgroup_generalization_limit" in PASSAGE_ARCHITECTURE_KEYS
