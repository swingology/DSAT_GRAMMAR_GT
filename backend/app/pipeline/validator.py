"""Validation rules from PRD §15.
Enforces required question structure, correct labels, source metadata, lineage, and overlap status.
"""
from typing import List, Dict
from app.models.ontology import (
    GRAMMAR_FOCUS_KEYS,
    GRAMMAR_ROLE_KEYS,
    STIMULUS_MODE_KEYS,
    STEM_TYPE_KEYS,
)


def validate_question(question_data: dict, content_origin: str = "official") -> List[Dict]:
    """Validate a question dict against PRD rules.
    Returns a list of error dicts: [{"severity": "blocking"|"review"|"warning", "field": str, "message": str}]
    """
    errors = []

    # Required question structure
    if not question_data.get("question_text"):
        errors.append({"severity": "blocking", "field": "question_text", "message": "Question text is required"})

    # Four answer choices
    options = question_data.get("options", [])
    if len(options) != 4:
        errors.append({"severity": "blocking", "field": "options", "message": f"Expected 4 options, got {len(options)}"})

    # Valid correct answer label
    correct = question_data.get("correct_option_label", "")
    if correct not in ("A", "B", "C", "D"):
        errors.append({"severity": "blocking", "field": "correct_option_label", "message": f"Invalid correct_option_label: {correct}"})

    # Explanation presence
    if not question_data.get("explanation_short") and not question_data.get("explanation_full"):
        errors.append({"severity": "review", "field": "explanation", "message": "No explanation text provided"})

    # Official-specific: source metadata required
    if content_origin == "official":
        for field in ["source_exam_code", "source_module_code", "source_question_number"]:
            if not question_data.get(field):
                errors.append({"severity": "blocking", "field": field, "message": f"Official questions require {field}"})

    # Generated-specific: lineage required
    if content_origin == "generated":
        if not question_data.get("generation_source_set") and not question_data.get("derived_from_question_id"):
            errors.append({"severity": "blocking", "field": "lineage", "message": "Generated questions require generation lineage"})

    # V3 ontology key validation (review severity — LLM may return near-miss keys)
    grammar_role = question_data.get("grammar_role_key")
    if grammar_role and grammar_role not in GRAMMAR_ROLE_KEYS:
        errors.append({
            "severity": "review",
            "field": "grammar_role_key",
            "message": f"Unknown grammar_role_key: {grammar_role!r}. Valid: {list(GRAMMAR_ROLE_KEYS)}",
        })

    grammar_focus = question_data.get("grammar_focus_key")
    if grammar_focus and grammar_focus not in GRAMMAR_FOCUS_KEYS:
        errors.append({
            "severity": "review",
            "field": "grammar_focus_key",
            "message": f"Unknown grammar_focus_key: {grammar_focus!r}",
        })

    stimulus_mode = question_data.get("stimulus_mode_key")
    if stimulus_mode and stimulus_mode not in STIMULUS_MODE_KEYS:
        errors.append({
            "severity": "review",
            "field": "stimulus_mode_key",
            "message": f"Unknown stimulus_mode_key: {stimulus_mode!r}",
        })

    stem_type = question_data.get("stem_type_key")
    if stem_type and stem_type not in STEM_TYPE_KEYS:
        errors.append({
            "severity": "review",
            "field": "stem_type_key",
            "message": f"Unknown stem_type_key: {stem_type!r}",
        })

    explanation_short = question_data.get("explanation_short", "")
    if explanation_short and len(explanation_short) > 300:
        errors.append({
            "severity": "review",
            "field": "explanation_short",
            "message": f"explanation_short exceeds 300 chars ({len(explanation_short)} chars)",
        })

    return errors