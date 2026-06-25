"""Tests for the diagnostic blueprint module (TASK-B01). No DB required."""

import pytest

from app.diagnostic.blueprint import (
    BLUEPRINT_V1,
    DIFFICULTY_TIERS,
    Slot,
    blueprint_coverage,
    tier_for_seq,
    validate_blueprint,
    _PRESENT_GRAMMAR_ROLES,
    _PRESENT_READING_FAMILIES,
    _ABSENT_GRAMMAR_ROLES,
    _ABSENT_READING_FAMILIES,
)
from app.models.ontology import GRAMMAR_ROLE_KEYS, READING_SKILL_FAMILY_KEYS


# ── BLUEPRINT_V1 structure ────────────────────────────────────────────────────

def test_blueprint_length():
    assert len(BLUEPRINT_V1) == 16


def test_blueprint_validates():
    """validate_blueprint must not raise on the canonical blueprint."""
    validate_blueprint(BLUEPRINT_V1)


def test_blueprint_seqs_contiguous():
    seqs = [s.seq for s in BLUEPRINT_V1]
    assert seqs == list(range(1, 17))


def test_difficulty_values_in_tiers():
    for slot in BLUEPRINT_V1:
        assert slot.difficulty in DIFFICULTY_TIERS


def test_ramp_low_then_medium():
    """All low slots come before all medium slots."""
    seen_medium = False
    for slot in BLUEPRINT_V1:
        if slot.difficulty == "medium":
            seen_medium = True
        elif slot.difficulty == "low":
            assert not seen_medium, f"Slot {slot.seq}: low after medium"


def test_low_count_and_medium_count():
    low = sum(1 for s in BLUEPRINT_V1 if s.difficulty == "low")
    medium = sum(1 for s in BLUEPRINT_V1 if s.difficulty == "medium")
    assert low == 6
    assert medium == 10


def test_no_three_consecutive_same_domain():
    domains = [s.domain for s in BLUEPRINT_V1]
    for i in range(2, len(domains)):
        assert not (domains[i] == domains[i - 1] == domains[i - 2]), (
            f"Three consecutive '{domains[i]}' slots at positions {i-2},{i-1},{i}"
        )


def test_all_present_grammar_roles_covered():
    grammar_roles = {s.role_or_skill for s in BLUEPRINT_V1 if s.domain == "grammar"}
    assert _PRESENT_GRAMMAR_ROLES <= grammar_roles


def test_all_present_reading_families_covered():
    reading_families = {s.role_or_skill for s in BLUEPRINT_V1 if s.domain == "reading"}
    assert _PRESENT_READING_FAMILIES <= reading_families


def test_no_absent_grammar_roles_in_blueprint():
    for slot in BLUEPRINT_V1:
        if slot.domain == "grammar":
            assert slot.role_or_skill not in _ABSENT_GRAMMAR_ROLES, (
                f"Slot {slot.seq} uses absent grammar role '{slot.role_or_skill}'"
            )


def test_no_absent_reading_families_in_blueprint():
    for slot in BLUEPRINT_V1:
        if slot.domain == "reading":
            assert slot.role_or_skill not in _ABSENT_READING_FAMILIES, (
                f"Slot {slot.seq} uses absent reading family '{slot.role_or_skill}'"
            )


def test_all_grammar_roles_valid_taxonomy():
    for slot in BLUEPRINT_V1:
        if slot.domain == "grammar":
            assert slot.role_or_skill in GRAMMAR_ROLE_KEYS


def test_all_reading_families_valid_taxonomy():
    for slot in BLUEPRINT_V1:
        if slot.domain == "reading":
            assert slot.role_or_skill in READING_SKILL_FAMILY_KEYS


# ── tier_for_seq ─────────────────────────────────────────────────────────────

def test_tier_for_seq_low_range():
    for seq in range(1, 7):
        assert tier_for_seq(seq) == "low"


def test_tier_for_seq_medium_range():
    for seq in range(7, 17):
        assert tier_for_seq(seq) == "medium"


# ── validate_blueprint error cases ───────────────────────────────────────────

def _make_bp(*slots) -> tuple:
    return tuple(slots)


def test_validate_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        validate_blueprint(())


def test_validate_non_contiguous_seqs_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="sentence_boundary"),
        Slot(seq=3, difficulty="low", domain="reading", role_or_skill="inferences"),  # gap
    )
    with pytest.raises(ValueError, match="contiguous"):
        validate_blueprint(bad)


def test_validate_low_after_medium_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="medium", domain="grammar", role_or_skill="sentence_boundary"),
        Slot(seq=2, difficulty="low", domain="reading", role_or_skill="inferences"),
    )
    with pytest.raises(ValueError, match="ramp order"):
        validate_blueprint(bad)


def test_validate_unknown_grammar_role_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="made_up_role"),
    )
    with pytest.raises(ValueError, match="unknown grammar role"):
        validate_blueprint(bad)


def test_validate_unknown_reading_family_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="low", domain="reading", role_or_skill="invented_family"),
    )
    with pytest.raises(ValueError, match="unknown reading family"):
        validate_blueprint(bad)


def test_validate_absent_grammar_role_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="parallel_structure"),
    )
    with pytest.raises(ValueError, match="absent from the bank"):
        validate_blueprint(bad)


def test_validate_absent_reading_family_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="low", domain="reading", role_or_skill="cross_text_connections"),
    )
    with pytest.raises(ValueError, match="absent from the bank"):
        validate_blueprint(bad)


def test_validate_three_consecutive_domain_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="low", domain="grammar", role_or_skill="sentence_boundary"),
        Slot(seq=2, difficulty="low", domain="grammar", role_or_skill="agreement"),
        Slot(seq=3, difficulty="low", domain="grammar", role_or_skill="verb_form"),
    )
    with pytest.raises(ValueError, match="three consecutive"):
        validate_blueprint(bad)


def test_validate_unknown_domain_raises():
    bad = _make_bp(
        Slot(seq=1, difficulty="low", domain="math", role_or_skill="algebra"),
    )
    with pytest.raises(ValueError, match="unknown domain"):
        validate_blueprint(bad)


def test_validate_missing_grammar_role_raises():
    """A blueprint with only reading slots fails (missing grammar roles).
    Use alternating slots to avoid the 3-in-a-row check."""
    reading_only = (
        Slot(seq=1, difficulty="low", domain="reading", role_or_skill="inferences"),
        Slot(seq=2, difficulty="low", domain="grammar", role_or_skill="sentence_boundary"),
        Slot(seq=3, difficulty="low", domain="reading", role_or_skill="central_ideas_and_details"),
    )
    # Only 1 grammar role present — missing 5 others
    with pytest.raises(ValueError, match="missing required grammar roles"):
        validate_blueprint(reading_only)


def test_validate_missing_reading_family_raises():
    """Blueprint with all grammar roles but only 1 reading family fails."""
    # All 6 required grammar roles + only 1 reading family (need 5)
    mixed = (
        Slot(seq=1, difficulty="low", domain="grammar",  role_or_skill="sentence_boundary"),
        Slot(seq=2, difficulty="low", domain="reading",  role_or_skill="inferences"),
        Slot(seq=3, difficulty="low", domain="grammar",  role_or_skill="agreement"),
        Slot(seq=4, difficulty="low", domain="grammar",  role_or_skill="verb_form"),
        Slot(seq=5, difficulty="low", domain="reading",  role_or_skill="inferences"),
        Slot(seq=6, difficulty="low", domain="grammar",  role_or_skill="modifier"),
        Slot(seq=7, difficulty="low", domain="grammar",  role_or_skill="punctuation"),
        Slot(seq=8, difficulty="low", domain="reading",  role_or_skill="inferences"),
        Slot(seq=9, difficulty="low", domain="grammar",  role_or_skill="expression_of_ideas"),
    )
    with pytest.raises(ValueError, match="missing required reading families"):
        validate_blueprint(mixed)


# ── blueprint_coverage ───────────────────────────────────────────────────────

def test_blueprint_coverage_totals():
    cov = blueprint_coverage(BLUEPRINT_V1)
    assert cov["total"] == 16
    assert sum(cov["by_difficulty"].values()) == 16
    assert sum(cov["by_domain"].values()) == 16
    assert sum(cov["by_role_or_skill"].values()) == 16


def test_blueprint_coverage_domain_split():
    """Grammar-heavy split (~10 grammar / ~6 reading per spec); exact count flexible."""
    cov = blueprint_coverage(BLUEPRINT_V1)
    assert cov["by_domain"]["grammar"] >= 8
    assert cov["by_domain"]["reading"] >= 5
    assert cov["by_domain"]["grammar"] + cov["by_domain"]["reading"] == 16
