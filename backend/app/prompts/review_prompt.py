"""Review prompt — composes rubric + grammar canon + optional reading rules + question context."""
import json
import os

from app.prompts.generate_prompt import _extract_between, _extract_sections


_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_REVIEW_RULE_FILE = "rules_agent_dsat_review_v1.md"
_GRAMMAR_FILE = "rules_agent_dsat_grammar_ingestion_generation_v8.md"
_READING_FILE = "rules_agent_dsat_reading_v2.md"

RUBRIC_VERSION = "v1"
RULES_VERSIONS = {"grammar": "v8", "reading": "v2"}


def _review_sections(label: str, rules_text: str) -> str:
    """Extract review-relevant sections from grammar and reading rule files.

    For the review rubric itself, return the full text (no section extraction).
    For grammar v8 and reading v2, extract only the sections relevant to
    reviewing — not the generation workflow sections.
    """
    if label == "Review v1":
        # The rubric file is purpose-built for review; include it in full.
        return rules_text

    if label == "Grammar v8":
        return _extract_sections(
            rules_text,
            [
                ("## Purpose", "# PART A"),
                ("# PART A", "# PART B"),
                ("## B.13 Generation Validation Checklist", "## B.14"),
                ("## D.3 Disambiguation Rules", "## D.4"),
                ("## D.5 Syntactic Trap Keys", "## D.6"),
                ("## D.7 Student Failure Mode Keys", "## D.8"),
                ("## D.8 Schema Guardrails and Enforcement", "## D.9"),
                ("# PART E", "## Reference Quick-Index"),
            ],
        )

    if label == "Reading v2":
        return _extract_sections(
            rules_text,
            [
                ("## Purpose", "## Source Authority"),
                ("## 2. Required Output Shape", "## 3."),
                ("## 3. Question Fields", "## 8."),
                ("## 8. Answer Mechanism Keys", "## 13."),
                ("## 14. Difficulty Calibration", "## 15."),
                ("## 17. Disambiguation Rules", "## 18."),
                ("## 19. Student Failure Mode Keys", "## 20."),
                ("## 21. Validator Checklist", None),
            ],
        )

    return rules_text


def _infer_review_domain(question_data: dict, annotation: dict | None = None) -> str:
    """Determine if the question is grammar, reading, or both.

    Checks the question data first, then falls back to annotation keys.
    """
    # Check question data for reading keys
    if any(
        question_data.get(key)
        for key in (
            "target_reading_focus_key",
            "target_skill_family_key",
            "reading_focus_key",
            "reading_skill_family_key",
        )
    ):
        return "reading"

    # Check annotation for reading keys
    if annotation:
        if annotation.get("reading_skill_family_key") or annotation.get("reading_focus_key"):
            return "reading"

    # Check question family for reading
    family = str(question_data.get("question_family_key") or "").lower()
    if family in {"craft_and_structure", "information_and_ideas"}:
        return "reading"

    # Check question data for grammar keys
    if any(
        question_data.get(key)
        for key in (
            "target_grammar_focus_key",
            "target_grammar_role_key",
            "grammar_focus_key",
            "grammar_role_key",
            "target_syntactic_trap_key",
        )
    ):
        return "grammar"

    # Check annotation for grammar keys
    if annotation:
        if annotation.get("grammar_focus_key") or annotation.get("grammar_role_key"):
            return "grammar"

    return "both"


_REVIEW_RULE_FILES = [
    ("Review v1", _REVIEW_RULE_FILE),
    ("Grammar v8", _GRAMMAR_FILE),
    ("Reading v2", _READING_FILE),
]


def _load_review_rule_context(domain: str = "both") -> str:
    """Load and compose review-relevant rule sections based on domain.

    Always loads: review rubric + grammar v8.
    Conditionally loads: reading v2 (when domain is "reading" or "both").
    """
    sections: list[str] = []
    for label, filename in _REVIEW_RULE_FILES:
        if domain == "grammar" and label == "Reading v2":
            continue
        if domain == "reading" and label == "Grammar v8":
            # Grammar v8 is ALWAYS loaded per locked decisions.
            pass
        path = os.path.join(_ROOT_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            rules_text = f.read()
        body = _review_sections(label, rules_text)
        if body.strip():
            sections.append(f"{label} RULES REFERENCE:\n{body}")
    return "\n\n".join(sections)


REVIEW_SYSTEM_PROMPT = """You are a DSAT question quality reviewer following the review rubric and DSAT grammar/reading specifications.

Evaluate the generated question against official DSAT standards. Your output must be a single JSON object with exactly these keys:

1. Seven numeric scores (0–10, one decimal place):
   - realism_score, sat_fidelity_score, difficulty_match_score,
   - distractor_quality_score, taxonomy_match_score,
   - explanation_quality_score, copy_risk_score

2. A verdict: exactly one of "accept", "needs_human_review", or "reject"

3. A reasons object: keys must be a subset of the seven score keys. Every score below its threshold MUST include a reason. Scores meeting threshold may omit reasons.

Rules:
- Copy risk is inverted: higher = more risk. Scores above 5.0 indicate concerning overlap with source examples.
- Evaluate the question on its own merits, not whether you personally agree with the answer.
- Compare against the source official examples for calibration, not for copying.
- Output valid JSON only. No markdown fences, no prose, no commentary."""


def build_review_prompt(
    question_data: dict,
    annotation: dict | None = None,
    source_examples: list | None = None,
    overlap_status: str = "none",
    generation_request: dict | None = None,
    *,
    rubric_version: str = "v1",
) -> tuple[str, str]:
    """Build system and user prompts for question review.

    Args:
        question_data: The generated question payload (question_text,
            passage_text, options, correct_option_label, etc.).
        annotation: The question's annotation JSON (grammar_focus_key,
            reading_skill_family_key, etc.).
        source_examples: Official source questions used during generation.
        overlap_status: Official overlap status ('none', 'possible', 'confirmed').
        generation_request: The original generation request that produced this
            question (target keys, difficulty, etc.).
        rubric_version: The rubric version to use (default: v1).

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    domain = _infer_review_domain(question_data, annotation)
    rules_context = _load_review_rule_context(domain)

    # Compose user message with all review context
    user_parts = []

    # Question payload
    user_parts.append(f"Generated question to review:\n{json.dumps(question_data, indent=2)}")

    # Annotation
    if annotation:
        user_parts.append(f"Question annotation:\n{json.dumps(annotation, indent=2)}")

    # Source examples (official questions for calibration)
    if source_examples:
        user_parts.append(
            "Official source questions for calibration (do NOT copy from these):\n"
            f"{json.dumps(source_examples, indent=2)}"
        )

    # Overlap status
    user_parts.append(f"Official overlap status: {overlap_status}")

    # Original generation request
    if generation_request:
        user_parts.append(
            f"Original generation request:\n{json.dumps(generation_request, indent=2)}"
        )

    user = "\n\n".join(user_parts)
    system = REVIEW_SYSTEM_PROMPT
    if rules_context:
        system = f"{system}\n\n{rules_context}"

    return system, user
