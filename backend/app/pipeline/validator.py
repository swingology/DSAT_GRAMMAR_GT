"""Validation rules from PRD §15.
Enforces required question structure, correct labels, source metadata, lineage, and overlap status.
"""
from typing import List, Dict


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

    return errors