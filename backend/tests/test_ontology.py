from app.models.ontology import (
    CONTENT_ORIGINS, JOB_TYPES, JOB_STATUSES, PRACTICE_STATUSES,
    OVERLAP_STATUSES, RELATION_TYPES, ASSET_TYPES, CHANGE_SOURCES,
    GRAMMAR_ROLE_KEYS, GRAMMAR_FOCUS_KEYS, SYNTACTIC_TRAP_KEYS,
    STIMULUS_MODE_KEYS, STEM_TYPE_KEYS, DISTRACTOR_TYPE_KEYS,
    PLANSIBILITY_SOURCE_KEYS, ANSWER_MECHANISM_KEYS, SOLVER_PATTERN_KEYS,
    READING_SKILL_FAMILY_KEYS, READING_FOCUS_KEYS,
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
