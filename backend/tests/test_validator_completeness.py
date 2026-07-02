"""Tests for validate_annotation_completeness — the domain-aware taxonomy gate."""
from app.pipeline.validator import validate_annotation_completeness


def _blocking(errors):
    return [e for e in errors if e["severity"] == "blocking"]


def _fields(errors, severity=None):
    return {e["field"] for e in errors if severity is None or e["severity"] == severity}


# --- Grammar domain ---

def test_grammar_complete_has_no_blocking():
    ann = {
        "question_family_key": "conventions_grammar",
        "grammar_role_key": "agreement",
        "grammar_focus_key": "subject_verb_agreement",
        "syntactic_trap_key": "nearest_noun_attraction",
        "difficulty_overall": "medium",
    }
    assert _blocking(validate_annotation_completeness(ann)) == []


def test_grammar_missing_focus_key_blocks():
    ann = {
        "question_family_key": "conventions_grammar",
        "grammar_role_key": "agreement",
        "grammar_focus_key": None,
        "syntactic_trap_key": "nearest_noun_attraction",
        "difficulty_overall": "medium",
    }
    assert "grammar_focus_key" in _fields(validate_annotation_completeness(ann), "blocking")


def test_grammar_required_role_with_none_trap_blocks():
    # agreement is in SYNTACTIC_TRAP_REQUIRED_ROLES → "none" not allowed
    ann = {
        "question_family_key": "conventions_grammar",
        "grammar_role_key": "agreement",
        "grammar_focus_key": "subject_verb_agreement",
        "syntactic_trap_key": "none",
        "difficulty_overall": "medium",
    }
    assert "syntactic_trap_key" in _fields(validate_annotation_completeness(ann), "blocking")


def test_grammar_nonrequired_role_with_none_trap_ok():
    # punctuation is NOT in SYNTACTIC_TRAP_REQUIRED_ROLES → "none" allowed
    ann = {
        "question_family_key": "conventions_grammar",
        "grammar_role_key": "punctuation",
        "grammar_focus_key": "quotation_punctuation",
        "syntactic_trap_key": "none",
        "difficulty_overall": "low",
    }
    assert "syntactic_trap_key" not in _fields(validate_annotation_completeness(ann))


def test_grammar_with_skill_family_key_flagged_review():
    ann = {
        "question_family_key": "conventions_grammar",
        "grammar_role_key": "punctuation",
        "grammar_focus_key": "quotation_punctuation",
        "syntactic_trap_key": "none",
        "difficulty_overall": "low",
        "skill_family_key": "words_in_context",  # reading-only field on grammar row
    }
    assert "skill_family_key" in _fields(validate_annotation_completeness(ann), "review")


# --- Reading domain ---

def test_reading_complete_has_no_blocking():
    ann = {
        "question_family_key": "craft_and_structure",
        "skill_family_key": "words_in_context",
        "reading_focus_key": "precision_fit",
        "difficulty_overall": "medium",
        "reasoning_trap_key": "topical_relevance_without_logical_connection",
    }
    assert _blocking(validate_annotation_completeness(ann)) == []


def test_reading_missing_skill_family_blocks():
    ann = {
        "question_family_key": "information_and_ideas",
        "reading_focus_key": "supporting_detail",
        "difficulty_overall": "low",
    }
    assert "skill_family_key" in _fields(validate_annotation_completeness(ann), "blocking")


def test_reading_with_grammar_keys_blocks():
    ann = {
        "question_family_key": "craft_and_structure",
        "skill_family_key": "words_in_context",
        "reading_focus_key": "precision_fit",
        "difficulty_overall": "medium",
        "grammar_role_key": "agreement",  # must be null on reading
    }
    assert "grammar_keys" in _fields(validate_annotation_completeness(ann), "blocking")


def test_reading_missing_reasoning_trap_is_review_not_blocking():
    ann = {
        "question_family_key": "craft_and_structure",
        "skill_family_key": "words_in_context",
        "reading_focus_key": "precision_fit",
        "difficulty_overall": "medium",
    }
    errors = validate_annotation_completeness(ann)
    assert "reasoning_trap_key" in _fields(errors, "review")
    assert "reasoning_trap_key" not in _fields(errors, "blocking")


# --- Shared ---

def test_missing_question_family_blocks_immediately():
    ann = {"grammar_role_key": "agreement"}
    errors = validate_annotation_completeness(ann)
    assert "question_family_key" in _fields(errors, "blocking")


def test_missing_difficulty_overall_blocks():
    ann = {
        "question_family_key": "conventions_grammar",
        "grammar_role_key": "punctuation",
        "grammar_focus_key": "quotation_punctuation",
        "syntactic_trap_key": "none",
    }
    assert "difficulty_overall" in _fields(validate_annotation_completeness(ann), "blocking")
