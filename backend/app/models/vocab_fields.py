"""Shared annotation-field to controlled-vocabulary mappings."""
from __future__ import annotations

BASE_FIELD_TO_VOCAB = {
    "question_family_key": "QUESTION_FAMILY_KEYS",
    "grammar_role_key": "GRAMMAR_ROLE_KEYS",
    "grammar_focus_key": "GRAMMAR_FOCUS_BY_ROLE",
    "stimulus_mode_key": "STIMULUS_MODE_KEYS",
    "stem_type_key": "STEM_TYPE_KEYS",
    "skill_family_key": "READING_SKILL_FAMILY_KEYS",
    "reading_focus_key": "READING_FOCUS_BY_SKILL_FAMILY",
    "distractor_type_key": "DISTRACTOR_TYPE_KEYS",
    "plausibility_source_key": "PLAUSIBILITY_SOURCE_KEYS",
    "student_failure_mode_key": "STUDENT_FAILURE_MODE_KEYS",
    "reasoning_trap_key": "REASONING_TRAP_KEYS",
    "syntactic_trap_key": "SYNTACTIC_TRAP_KEYS",
    "transition_subtype_key": "TRANSITION_SUBTYPE_KEYS",
}

SCANNER_EXTRA_FIELD_TO_VOCAB = {
    "target_grammar_role_key": "GRAMMAR_ROLE_KEYS",
    "target_grammar_focus_key": "GRAMMAR_FOCUS_BY_ROLE",
    "reading_skill_family_key": "READING_SKILL_FAMILY_KEYS",
    "target_reading_skill_family_key": "READING_SKILL_FAMILY_KEYS",
    "target_reading_focus_key": "READING_FOCUS_BY_SKILL_FAMILY",
    "distractor_distance": "DISTRACTOR_DISTANCE_KEYS",
}

SCANNER_FIELD_TO_VOCAB = {
    **BASE_FIELD_TO_VOCAB,
    **SCANNER_EXTRA_FIELD_TO_VOCAB,
}
