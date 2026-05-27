"""Sanitize LLM-produced annotation dicts before DB writes.

For each controlled-vocabulary field in an annotation, if the LLM output a key
that is not in the active master.json vocabulary:

  1. Try difflib nearest-match (cutoff 0.7) against valid keys for that field.
     - If one match: substitute and record the correction in the annotation under
       ``_key_corrections`` (auditable, never shown to students).
     - If no match: null the field.
  2. Record the original bad value in vocabulary/candidates.json via
     ``record_candidate`` so it can be promoted if it turns out to be legitimate.

Fields sanitized (the annotation fields that map to controlled vocabularies):
  grammar_focus_key, grammar_role_key, question_family_key, stem_type_key,
  stimulus_mode_key, skill_family_key, reading_focus_key, reasoning_trap_key

Fields explicitly NOT sanitized (too many legitimate near-misses / low risk):
  syntactic_trap_key, student_failure_mode_key, distractor_type_key
"""
from __future__ import annotations

import difflib
import logging
from typing import Any

from app.models.ontology import (
    GRAMMAR_FOCUS_KEYS,
    GRAMMAR_ROLE_KEYS,
    QUESTION_FAMILY_KEYS,
    STEM_TYPE_KEYS,
    STIMULUS_MODE_KEYS,
    READING_SKILL_FAMILY_KEYS,
    READING_FOCUS_KEYS,
    REASONING_TRAP_KEYS,
)
from app.models.vocab_candidates import record_candidate

logger = logging.getLogger(__name__)

# Mapping from annotation field → valid key tuple.
# Order matters: grammar_role_key must be sanitized before grammar_focus_key
# so the role is correct when we validate role/focus consistency.
_FIELD_VALID_KEYS: list[tuple[str, tuple[str, ...]]] = [
    ("question_family_key", QUESTION_FAMILY_KEYS),
    ("grammar_role_key", GRAMMAR_ROLE_KEYS),
    ("grammar_focus_key", GRAMMAR_FOCUS_KEYS),
    ("stem_type_key", STEM_TYPE_KEYS),
    ("stimulus_mode_key", STIMULUS_MODE_KEYS),
    ("skill_family_key", READING_SKILL_FAMILY_KEYS),
    ("reading_focus_key", READING_FOCUS_KEYS),
    ("reasoning_trap_key", REASONING_TRAP_KEYS),
]

_VOCAB_NAME: dict[str, str] = {
    "question_family_key": "QUESTION_FAMILY_KEYS",
    "grammar_role_key": "GRAMMAR_ROLE_KEYS",
    "grammar_focus_key": "GRAMMAR_FOCUS_BY_ROLE",
    "stem_type_key": "STEM_TYPE_KEYS",
    "stimulus_mode_key": "STIMULUS_MODE_KEYS",
    "skill_family_key": "READING_SKILL_FAMILY_KEYS",
    "reading_focus_key": "READING_FOCUS_BY_SKILL_FAMILY",
    "reasoning_trap_key": "REASONING_TRAP_KEYS",
}

_CORRECTION_KEY = "_key_corrections"


def sanitize_annotation_keys(
    annotation: dict[str, Any],
    *,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Return a copy of *annotation* with invalid controlled-vocab keys replaced.

    The original annotation dict is never mutated.  If no corrections were
    needed the returned dict is the original object (identity).
    """
    corrections: list[dict[str, str]] = []

    patched: dict[str, Any] | None = None  # lazy copy

    for field, valid_keys in _FIELD_VALID_KEYS:
        value = annotation.get(field)
        if value is None or value == "" or value in valid_keys:
            continue

        # Unknown key — try nearest match
        matches = difflib.get_close_matches(value, valid_keys, n=1, cutoff=0.7)
        replacement = matches[0] if matches else None

        # Record original as candidate regardless of whether we can substitute
        record_candidate(
            _VOCAB_NAME.get(field, field),
            value,
            field=field,
            job_id=job_id,
            context=f"sanitized→{replacement or 'null'}",
        )

        if patched is None:
            patched = dict(annotation)

        if replacement:
            logger.info(
                "annotation sanitizer: %s %r → %r (job=%s)",
                field, value, replacement, job_id,
            )
            patched[field] = replacement
            corrections.append({"field": field, "from": value, "to": replacement})
        else:
            logger.warning(
                "annotation sanitizer: %s %r has no near-match — nulled (job=%s)",
                field, value, job_id,
            )
            patched[field] = None
            corrections.append({"field": field, "from": value, "to": None})

    if patched is None:
        return annotation  # nothing changed — return original

    if corrections:
        existing = patched.get(_CORRECTION_KEY) or []
        patched[_CORRECTION_KEY] = existing + corrections

    return patched
