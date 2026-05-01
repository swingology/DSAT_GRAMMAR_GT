"""Validation rules from PRD §15.
Enforces required question structure, correct labels, source metadata, lineage, and overlap status.
"""
from typing import List, Dict
from app.models.ontology import (
    GRAMMAR_FOCUS_KEYS,
    GRAMMAR_FOCUS_BY_ROLE,
    GRAMMAR_ROLE_KEYS,
    QUESTION_FAMILY_KEYS,
    READING_QUESTION_FAMILY_KEYS,
    READING_SKILL_FAMILY_KEYS,
    READING_FOCUS_BY_SKILL_FAMILY,
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
    question_family = question_data.get("question_family_key")
    if question_family and question_family not in QUESTION_FAMILY_KEYS:
        errors.append({
            "severity": "review",
            "field": "question_family_key",
            "message": f"Unknown question_family_key: {question_family!r}",
        })

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

    if grammar_role and grammar_focus:
        allowed_foci = GRAMMAR_FOCUS_BY_ROLE.get(grammar_role, ())
        if grammar_focus not in allowed_foci:
            errors.append({
                "severity": "review",
                "field": "grammar_focus_key",
                "message": f"grammar_focus_key {grammar_focus!r} does not match grammar_role_key {grammar_role!r}",
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

    skill_family_key = question_data.get("skill_family_key")
    reading_focus_key = question_data.get("reading_focus_key")
    if question_family in READING_QUESTION_FAMILY_KEYS:
        if grammar_role or grammar_focus:
            errors.append({
                "severity": "blocking",
                "field": "grammar_keys",
                "message": "Reading-domain questions must not set grammar_role_key or grammar_focus_key",
            })
        if not skill_family_key:
            errors.append({
                "severity": "blocking",
                "field": "skill_family_key",
                "message": "Reading-domain questions require skill_family_key",
            })
        elif skill_family_key not in READING_SKILL_FAMILY_KEYS:
            errors.append({
                "severity": "blocking",
                "field": "skill_family_key",
                "message": f"Invalid reading skill_family_key: {skill_family_key!r}",
            })
        if not reading_focus_key:
            errors.append({
                "severity": "blocking",
                "field": "reading_focus_key",
                "message": "Reading-domain questions require reading_focus_key",
            })
        elif skill_family_key in READING_FOCUS_BY_SKILL_FAMILY and reading_focus_key not in READING_FOCUS_BY_SKILL_FAMILY[skill_family_key]:
            errors.append({
                "severity": "blocking",
                "field": "reading_focus_key",
                "message": f"reading_focus_key {reading_focus_key!r} is not allowed for skill_family_key {skill_family_key!r}",
            })
        if skill_family_key == "cross_text_connections":
            if stimulus_mode != "prose_paired":
                errors.append({
                    "severity": "blocking",
                    "field": "stimulus_mode_key",
                    "message": "Cross-Text Connections requires stimulus_mode_key='prose_paired'",
                })
            if not question_data.get("paired_passage_text"):
                errors.append({
                    "severity": "blocking",
                    "field": "paired_passage_text",
                    "message": "Cross-Text Connections requires paired_passage_text",
                })
        if skill_family_key == "command_of_evidence_quantitative":
            if stimulus_mode not in ("prose_plus_table", "prose_plus_graph"):
                errors.append({
                    "severity": "blocking",
                    "field": "stimulus_mode_key",
                    "message": "Quantitative Command of Evidence requires prose_plus_table or prose_plus_graph",
                })
            if not question_data.get("table_data") and not question_data.get("graph_data"):
                errors.append({
                    "severity": "blocking",
                    "field": "graphic_data",
                    "message": "Quantitative Command of Evidence requires table_data or graph_data",
                })

    explanation_short = question_data.get("explanation_short", "")
    if explanation_short and len(explanation_short) > 300:
        errors.append({
            "severity": "review",
            "field": "explanation_short",
            "message": f"explanation_short exceeds 300 chars ({len(explanation_short)} chars)",
        })

    return errors
