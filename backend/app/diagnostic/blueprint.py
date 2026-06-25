"""Diagnostic test blueprint — official-bank v1 (16 slots, low→medium ramp).

Bank reality (TASK-B00, 2026-06-23): 60 active official questions, all
content_origin='official'. Usable classified: 27 grammar + 13 reading.
Missing grammar roles: parallel_structure, pronoun.
Missing reading families: command_of_evidence_quantitative, cross_text_connections.
Hence v1 = 16 slots (10 grammar + 6 reading), low→medium ramp, no 'high'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.ontology import GRAMMAR_ROLE_KEYS, READING_SKILL_FAMILY_KEYS

# --- Difficulty tiers present in the live bank ---
DIFFICULTY_TIERS = ("low", "medium")  # null-difficulty treated as medium

# Grammar roles verified present in the bank
_PRESENT_GRAMMAR_ROLES = frozenset({
    "expression_of_ideas",
    "punctuation",
    "agreement",
    "modifier",
    "sentence_boundary",
    "verb_form",
})
# Explicitly absent — do NOT put in blueprint
_ABSENT_GRAMMAR_ROLES = frozenset({"parallel_structure", "pronoun"})

# Reading skill families verified present in the bank (as skill_family_key)
_PRESENT_READING_FAMILIES = frozenset({
    "inferences",
    "text_structure_and_purpose",
    "central_ideas_and_details",
    "command_of_evidence_textual",
    "words_in_context",
})
# Explicitly absent
_ABSENT_READING_FAMILIES = frozenset({
    "command_of_evidence_quantitative",
    "cross_text_connections",
})


@dataclass(frozen=True)
class Slot:
    seq: int               # 1..16
    difficulty: str        # "low" | "medium"
    domain: str            # "grammar" | "reading"
    role_or_skill: str     # grammar_role_key (grammar) OR skill_family_key (reading)
    focus: Optional[str] = None           # soft filter
    trap_preference: Optional[str] = None  # soft filter


# fmt: off
BLUEPRINT_V1: tuple[Slot, ...] = (
    # --- LOW tier: slots 1-6 (alternating domain) ---
    Slot(seq=1,  difficulty="low", domain="grammar",  role_or_skill="sentence_boundary"),
    Slot(seq=2,  difficulty="low", domain="reading",  role_or_skill="inferences"),
    Slot(seq=3,  difficulty="low", domain="grammar",  role_or_skill="agreement"),
    Slot(seq=4,  difficulty="low", domain="reading",  role_or_skill="central_ideas_and_details"),
    Slot(seq=5,  difficulty="low", domain="grammar",  role_or_skill="punctuation"),
    Slot(seq=6,  difficulty="low", domain="reading",  role_or_skill="words_in_context"),

    # --- MEDIUM tier: slots 7-16 (rotate domain, no 3-in-a-row) ---
    Slot(seq=7,  difficulty="medium", domain="grammar",  role_or_skill="expression_of_ideas"),
    Slot(seq=8,  difficulty="medium", domain="reading",  role_or_skill="text_structure_and_purpose"),
    Slot(seq=9,  difficulty="medium", domain="grammar",  role_or_skill="verb_form"),
    Slot(seq=10, difficulty="medium", domain="grammar",  role_or_skill="modifier"),
    Slot(seq=11, difficulty="medium", domain="reading",  role_or_skill="command_of_evidence_textual"),
    Slot(seq=12, difficulty="medium", domain="grammar",  role_or_skill="expression_of_ideas"),
    Slot(seq=13, difficulty="medium", domain="reading",  role_or_skill="inferences"),
    Slot(seq=14, difficulty="medium", domain="grammar",  role_or_skill="expression_of_ideas"),
    Slot(seq=15, difficulty="medium", domain="reading",  role_or_skill="text_structure_and_purpose"),
    Slot(seq=16, difficulty="medium", domain="grammar",  role_or_skill="punctuation"),
)
# fmt: on


def tier_for_seq(seq: int) -> str:
    """Return difficulty tier for a slot sequence number."""
    if seq <= 6:
        return "low"
    return "medium"


def validate_blueprint(bp: tuple[Slot, ...]) -> None:
    """Raise ValueError if the blueprint violates any structural constraint."""
    if len(bp) == 0:
        raise ValueError("Blueprint is empty")

    seqs = [s.seq for s in bp]
    expected = list(range(1, len(bp) + 1))
    if sorted(seqs) != expected:
        raise ValueError(f"Slot seqs must be contiguous 1..{len(bp)}, got {sorted(seqs)}")

    seen_keys: set[str] = set()
    low_ended = False

    for i, slot in enumerate(bp):
        # Difficulty ramp: no 'low' after 'medium'
        if slot.difficulty == "medium":
            low_ended = True
        elif slot.difficulty == "low" and low_ended:
            raise ValueError(
                f"Slot {slot.seq}: 'low' after 'medium' violates ramp order"
            )

        # Known difficulty tiers
        if slot.difficulty not in DIFFICULTY_TIERS:
            raise ValueError(
                f"Slot {slot.seq}: unknown difficulty '{slot.difficulty}'"
            )

        # Validate taxonomy keys
        if slot.domain == "grammar":
            if slot.role_or_skill not in GRAMMAR_ROLE_KEYS:
                raise ValueError(
                    f"Slot {slot.seq}: unknown grammar role '{slot.role_or_skill}'"
                )
            if slot.role_or_skill in _ABSENT_GRAMMAR_ROLES:
                raise ValueError(
                    f"Slot {slot.seq}: grammar role '{slot.role_or_skill}' is absent from the bank"
                )
        elif slot.domain == "reading":
            if slot.role_or_skill not in READING_SKILL_FAMILY_KEYS:
                raise ValueError(
                    f"Slot {slot.seq}: unknown reading family '{slot.role_or_skill}'"
                )
            if slot.role_or_skill in _ABSENT_READING_FAMILIES:
                raise ValueError(
                    f"Slot {slot.seq}: reading family '{slot.role_or_skill}' is absent from the bank"
                )
        else:
            raise ValueError(f"Slot {slot.seq}: unknown domain '{slot.domain}'")

        # 3-in-a-row domain check
        if i >= 2 and bp[i].domain == bp[i - 1].domain == bp[i - 2].domain:
            raise ValueError(
                f"Slot {slot.seq}: three consecutive '{slot.domain}' slots"
            )

        seen_keys.add(slot.role_or_skill)

    # All 6 present grammar roles must appear
    missing_grammar = _PRESENT_GRAMMAR_ROLES - seen_keys
    if missing_grammar:
        raise ValueError(
            f"Blueprint missing required grammar roles: {sorted(missing_grammar)}"
        )

    # All 5 present reading families must appear
    missing_reading = _PRESENT_READING_FAMILIES - seen_keys
    if missing_reading:
        raise ValueError(
            f"Blueprint missing required reading families: {sorted(missing_reading)}"
        )


def blueprint_coverage(bp: tuple[Slot, ...]) -> dict:
    """Return a summary dict of blueprint composition."""
    from collections import Counter

    by_difficulty: Counter = Counter()
    by_domain: Counter = Counter()
    by_role: Counter = Counter()

    for slot in bp:
        by_difficulty[slot.difficulty] += 1
        by_domain[slot.domain] += 1
        by_role[slot.role_or_skill] += 1

    return {
        "total": len(bp),
        "by_difficulty": dict(by_difficulty),
        "by_domain": dict(by_domain),
        "by_role_or_skill": dict(by_role),
    }
