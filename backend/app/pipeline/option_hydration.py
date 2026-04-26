"""Utilities for populating QuestionOption annotation fields from annotate_json.

The LLM annotation pass returns per-option analysis under an "options" key.
These helpers extract and map those fields so they can be written directly to
QuestionOption rows rather than being buried in annotation_jsonb.
"""
from typing import Optional


# All QuestionOption columns that come from annotation (not from extraction).
OPTION_ANNOTATION_FIELDS = [
    "distractor_type_key",
    "semantic_relation_key",
    "plausibility_source_key",
    "option_error_focus_key",
    "why_plausible",
    "why_wrong",
    "grammar_fit",
    "tone_match",
    "precision_score",
    "student_failure_mode_key",
    "distractor_distance",
    "distractor_competition_score",
]


def option_analyses_by_label(annotate_json: dict) -> dict:
    """Return {label: analysis_dict} from the annotation's options list.

    Handles both 'option_label' and 'label' key names for robustness across
    LLM providers.  Only A–D labels are kept.
    """
    result: dict = {}
    for opt in annotate_json.get("options", []):
        label = opt.get("option_label") or opt.get("label")
        if label in ("A", "B", "C", "D"):
            result[label] = opt
    return result


def option_annotation_fields(analysis: dict) -> dict:
    """Extract annotation-specific fields from a per-option analysis dict.

    Returns a dict safe to pass as **kwargs to QuestionOption() or to
    setattr() when updating existing rows.
    """
    return {field: analysis.get(field) for field in OPTION_ANNOTATION_FIELDS}


def apply_option_annotations(option_row, analysis: dict) -> None:
    """Set all annotation fields on an existing QuestionOption ORM instance in-place."""
    for field, value in option_annotation_fields(analysis).items():
        setattr(option_row, field, value)


def clear_option_annotations(option_row) -> None:
    """Null out all annotation fields on a QuestionOption ORM instance in-place."""
    for field in OPTION_ANNOTATION_FIELDS:
        setattr(option_row, field, None)
