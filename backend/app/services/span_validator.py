"""Validate LLM-produced token arrays against the passage text and vocabulary.

All 6 checks run to completion — errors are collected, not short-circuited,
so the review queue gets the full picture on each failure.
"""
from dataclasses import dataclass

from app.services.span_vocab import ANATOMY_KEYS, CONCEPT_KEYS, blank_anatomy_for


@dataclass
class SpanValidationError:
    error_type: str   # matches span_review_queue.error_type values
    error_detail: str


def validate_tokens(
    tokens: list[dict],
    passage_text: str,
    grammar_focus_key: str | None,
) -> list[SpanValidationError]:
    errors: list[SpanValidationError] = []

    # 1. concat_mismatch — reconstructed text must equal passage_text exactly
    reconstructed = "".join(t.get("text", "") for t in tokens)
    if reconstructed != passage_text:
        preview_len = 60
        errors.append(SpanValidationError(
            error_type="concat_mismatch",
            error_detail=(
                f"Expected ({len(passage_text)} chars): {passage_text[:preview_len]!r}  "
                f"Got ({len(reconstructed)} chars): {reconstructed[:preview_len]!r}"
            ),
        ))

    # 2. invalid_anatomy — any anatomy value not in approved set
    bad_anatomy: list[str] = []
    for t in tokens:
        for key in t.get("anatomy", []):
            if key not in ANATOMY_KEYS:
                bad_anatomy.append(key)
    if bad_anatomy:
        errors.append(SpanValidationError(
            error_type="invalid_anatomy",
            error_detail=f"Unknown anatomy keys: {sorted(set(bad_anatomy))}",
        ))

    # 3. invalid_concept — any concept_tags value not in approved set
    bad_concept: list[str] = []
    for t in tokens:
        for key in t.get("concept_tags", []):
            if key not in CONCEPT_KEYS:
                bad_concept.append(key)
    if bad_concept:
        errors.append(SpanValidationError(
            error_type="invalid_concept",
            error_detail=f"Unknown concept keys: {sorted(set(bad_concept))}",
        ))

    # 4. missing_primary_concept — grammar_focus_key absent from all concept_tags
    if grammar_focus_key:
        has_primary = any(
            grammar_focus_key in t.get("concept_tags", []) for t in tokens
        )
        if not has_primary:
            errors.append(SpanValidationError(
                error_type="missing_primary_concept",
                error_detail=f"focus_key '{grammar_focus_key}' not found in any token's concept_tags",
            ))

    # 5. missing_blank_token — passage has blank placeholder but no is_blank token
    has_blank_text = "_______" in passage_text or "[blank]" in passage_text.lower()
    has_blank_token = any(t.get("is_blank") for t in tokens)
    if has_blank_text and not has_blank_token:
        errors.append(SpanValidationError(
            error_type="missing_blank_token",
            error_detail="Passage contains blank placeholder but no token has is_blank=true",
        ))

    # 6. wrong_blank_anatomy — blank token's anatomy doesn't match expected mapping
    expected_blank_anatomy = blank_anatomy_for(grammar_focus_key)
    for t in tokens:
        if t.get("is_blank"):
            actual = sorted(t.get("anatomy", []))
            expected = sorted(expected_blank_anatomy)
            if actual != expected:
                errors.append(SpanValidationError(
                    error_type="wrong_blank_anatomy",
                    error_detail=(
                        f"Blank token anatomy mismatch. "
                        f"Expected {expected}, got {actual}"
                    ),
                ))
            break  # only check the first blank token

    return errors


def derive_summaries(tokens: list[dict]) -> tuple[list[str], list[str]]:
    """Return (anatomy_present, concepts_present) — deduplicated sorted lists."""
    anatomy: set[str] = set()
    concepts: set[str] = set()
    for t in tokens:
        anatomy.update(t.get("anatomy", []))
        concepts.update(t.get("concept_tags", []))
    return sorted(anatomy), sorted(concepts)


def is_valid(errors: list[SpanValidationError]) -> bool:
    return len(errors) == 0
