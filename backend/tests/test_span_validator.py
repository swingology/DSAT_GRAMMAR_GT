"""TASK-025 — span_validator.py unit tests.

Covers all 6 validation checks and derive_summaries.
No DB or LLM required — pure unit tests.
"""
import pytest
from app.services.span_validator import (
    validate_tokens,
    derive_summaries,
    SpanValidationError,
    is_valid,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def tok(text: str, anatomy=None, concept_tags=None, is_blank=False):
    t = {"text": text}
    if anatomy is not None:
        t["anatomy"] = anatomy
    if concept_tags is not None:
        t["concept_tags"] = concept_tags
    if is_blank:
        t["is_blank"] = True
    return t


def passage(*texts):
    return "".join(texts)


# ---------------------------------------------------------------------------
# 1. concat_mismatch
# ---------------------------------------------------------------------------

class TestConcatMismatch:
    def test_exact_match_no_error(self):
        tokens = [tok("Hello "), tok("world")]
        errors = validate_tokens(tokens, "Hello world", None)
        types = [e.error_type for e in errors]
        assert "concat_mismatch" not in types

    def test_short_reconstruction_raises(self):
        tokens = [tok("Hello")]
        errors = validate_tokens(tokens, "Hello world", None)
        assert any(e.error_type == "concat_mismatch" for e in errors)

    def test_extra_character_raises(self):
        tokens = [tok("Hello world ")]
        errors = validate_tokens(tokens, "Hello world", None)
        assert any(e.error_type == "concat_mismatch" for e in errors)


# ---------------------------------------------------------------------------
# 2. invalid_anatomy
# ---------------------------------------------------------------------------

class TestInvalidAnatomy:
    def test_valid_anatomy_keys_pass(self):
        tokens = [tok("Students", anatomy=["subject"]), tok(" run", anatomy=["main_verb"])]
        errors = validate_tokens(tokens, "Students run", None)
        assert not any(e.error_type == "invalid_anatomy" for e in errors)

    def test_unknown_anatomy_key_raises(self):
        tokens = [tok("thing", anatomy=["noun_phrase_blah"])]
        errors = validate_tokens(tokens, "thing", None)
        assert any(e.error_type == "invalid_anatomy" for e in errors)
        detail = next(e for e in errors if e.error_type == "invalid_anatomy").error_detail
        assert "noun_phrase_blah" in detail

    def test_empty_anatomy_is_fine(self):
        tokens = [tok("word")]
        errors = validate_tokens(tokens, "word", None)
        assert not any(e.error_type == "invalid_anatomy" for e in errors)


# ---------------------------------------------------------------------------
# 3. invalid_concept
# ---------------------------------------------------------------------------

class TestInvalidConcept:
    def test_valid_concept_passes(self):
        tokens = [tok("_______", concept_tags=["subject_verb_agreement"], is_blank=True,
                      anatomy=["main_verb"])]
        errors = validate_tokens(tokens, "_______", "subject_verb_agreement")
        assert not any(e.error_type == "invalid_concept" for e in errors)

    def test_unknown_concept_raises(self):
        tokens = [tok("word", concept_tags=["not_a_real_key"])]
        errors = validate_tokens(tokens, "word", None)
        assert any(e.error_type == "invalid_concept" for e in errors)


# ---------------------------------------------------------------------------
# 4. missing_primary_concept
# ---------------------------------------------------------------------------

class TestMissingPrimaryConceptError:
    def test_focus_key_present_in_token_passes(self):
        tokens = [tok("_______", concept_tags=["subject_verb_agreement"], is_blank=True,
                      anatomy=["main_verb"])]
        errors = validate_tokens(tokens, "_______", "subject_verb_agreement")
        assert not any(e.error_type == "missing_primary_concept" for e in errors)

    def test_focus_key_absent_raises(self):
        tokens = [tok("The quick brown fox", concept_tags=["modifier_placement"])]
        errors = validate_tokens(tokens, "The quick brown fox", "subject_verb_agreement")
        assert any(e.error_type == "missing_primary_concept" for e in errors)

    def test_none_focus_key_skipped(self):
        tokens = [tok("word")]
        errors = validate_tokens(tokens, "word", None)
        assert not any(e.error_type == "missing_primary_concept" for e in errors)


# ---------------------------------------------------------------------------
# 5. missing_blank_token
# ---------------------------------------------------------------------------

class TestMissingBlankToken:
    def test_blank_placeholder_with_blank_token_passes(self):
        tokens = [tok("The "), tok("_______", is_blank=True, anatomy=["main_verb"],
                                   concept_tags=["subject_verb_agreement"])]
        errors = validate_tokens(tokens, "The _______", "subject_verb_agreement")
        assert not any(e.error_type == "missing_blank_token" for e in errors)

    def test_blank_placeholder_without_blank_token_raises(self):
        tokens = [tok("The "), tok("_______")]
        errors = validate_tokens(tokens, "The _______", "subject_verb_agreement")
        assert any(e.error_type == "missing_blank_token" for e in errors)

    def test_no_placeholder_no_check(self):
        tokens = [tok("The cat sat")]
        errors = validate_tokens(tokens, "The cat sat", None)
        assert not any(e.error_type == "missing_blank_token" for e in errors)


# ---------------------------------------------------------------------------
# 6. wrong_blank_anatomy
# ---------------------------------------------------------------------------

class TestWrongBlankAnatomy:
    def test_correct_blank_anatomy_passes(self):
        # subject_verb_agreement blank → expects ["main_verb", "verb_form", "verb_tense_consistency"]
        tokens = [tok("_______", is_blank=True,
                      anatomy=["main_verb", "verb_form", "verb_tense_consistency"],
                      concept_tags=["subject_verb_agreement"])]
        errors = validate_tokens(tokens, "_______", "subject_verb_agreement")
        assert not any(e.error_type == "wrong_blank_anatomy" for e in errors)

    def test_wrong_blank_anatomy_raises(self):
        tokens = [tok("_______", is_blank=True, anatomy=["subject"],
                      concept_tags=["subject_verb_agreement"])]
        errors = validate_tokens(tokens, "_______", "subject_verb_agreement")
        assert any(e.error_type == "wrong_blank_anatomy" for e in errors)

    def test_no_blank_token_skips_check(self):
        tokens = [tok("runs")]
        errors = validate_tokens(tokens, "runs", "subject_verb_agreement")
        assert not any(e.error_type == "wrong_blank_anatomy" for e in errors)


# ---------------------------------------------------------------------------
# All errors collected (no short-circuit)
# ---------------------------------------------------------------------------

class TestAllErrorsCollected:
    def test_multiple_errors_all_returned(self):
        # concat_mismatch + invalid_anatomy both present
        tokens = [tok("bad_text", anatomy=["definitely_not_valid"])]
        errors = validate_tokens(tokens, "different_text", None)
        types = {e.error_type for e in errors}
        assert "concat_mismatch" in types
        assert "invalid_anatomy" in types


# ---------------------------------------------------------------------------
# is_valid / derive_summaries
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_is_valid_empty_errors(self):
        assert is_valid([]) is True

    def test_is_valid_nonempty_errors(self):
        assert is_valid([SpanValidationError("x", "y")]) is False

    def test_derive_summaries_basic(self):
        tokens = [
            tok("Students", anatomy=["subject"], concept_tags=["subject_verb_agreement"]),
            tok(" run", anatomy=["main_verb"]),
            tok(" fast", anatomy=[], concept_tags=["subject_verb_agreement"]),
        ]
        anatomy_present, concepts_present = derive_summaries(tokens)
        assert sorted(anatomy_present) == ["main_verb", "subject"]
        assert concepts_present == ["subject_verb_agreement"]

    def test_derive_summaries_empty_tokens(self):
        anatomy_present, concepts_present = derive_summaries([])
        assert anatomy_present == []
        assert concepts_present == []

    def test_derive_summaries_deduplicates(self):
        tokens = [
            tok("a", anatomy=["subject"], concept_tags=["subject_verb_agreement"]),
            tok("b", anatomy=["subject"], concept_tags=["subject_verb_agreement"]),
        ]
        anatomy_present, concepts_present = derive_summaries(tokens)
        assert anatomy_present == ["subject"]
        assert concepts_present == ["subject_verb_agreement"]
