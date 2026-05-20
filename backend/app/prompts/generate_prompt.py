"""Generation prompt — produces new DSAT-style questions from a specification."""
import json
import os


_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_GENERATION_RULE_FILES = [
    ("Grammar v7", "rules_agent_dsat_grammar_ingestion_generation_v7.md"),
    ("Reading v2", "rules_agent_dsat_reading_v2.md"),
]


def _extract_between(text: str, start_marker: str, end_marker: str | None = None) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    if end_marker:
        end = text.find(end_marker, start + len(start_marker))
        return text[start:end] if end != -1 else text[start:]
    return text[start:]


def _extract_sections(text: str, sections: list[tuple[str, str | None]]) -> str:
    return "\n\n".join(
        chunk for start, end in sections if (chunk := _extract_between(text, start, end)).strip()
    )


def _generation_sections(label: str, rules_text: str) -> str:
    if label == "Grammar v7":
        return _extract_sections(
            rules_text,
            [
                ("## Purpose", "# PART A"),
                ("# PART A", "# PART B"),
                ("## B.1 Generation Input Specification", "## B.2"),
                ("## B.2 Step-by-Step Generation Workflow", "## B.3"),
                ("## B.3 Passage Construction Rules by Grammar Focus", "## B.4"),
                ("## B.4 Distractor Generation Heuristics by Grammar Focus", "## B.5"),
                ("## B.5 Transition Subtype Vocabulary", "## B.6"),
                ("## B.6 Notes Synthesis Metadata", "## B.7"),
                ("## B.8 Difficulty Calibration for Generation", "## B.9"),
                ("## B.9 Batch, Deduplication, and Option Ordering", "## B.10"),
                ("## B.10 Explanation Requirements", "## B.11"),
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
                ("## 13. Skill-Specific Annotation Rules", "## 14."),
                ("## 14. Difficulty Calibration", "## 15."),
                ("## 15. Passage Architecture Requirements", "## 16."),
                ("## 16. Generation Rules", "## 17."),
                ("## 17. Disambiguation Rules", "## 18."),
                ("## 19. Student Failure Mode Keys", "## 20."),
                ("## 21. Validator Checklist", None),
            ],
        )
    return rules_text


def _infer_generation_domain(generation_request: dict) -> str:
    if any(
        generation_request.get(key)
        for key in (
            "target_reading_focus_key",
            "target_skill_family_key",
            "reading_focus_key",
            "reading_skill_family_key",
        )
    ):
        return "reading"
    family = str(generation_request.get("question_family_key") or "").lower()
    if family in {"craft_and_structure", "information_and_ideas"}:
        return "reading"
    if any(
        generation_request.get(key)
        for key in (
            "target_grammar_focus_key",
            "target_grammar_role_key",
            "grammar_focus_key",
            "grammar_role_key",
            "target_syntactic_trap_key",
        )
    ):
        return "grammar"
    return "both"


def _load_generation_rule_context(domain: str = "both") -> str:
    sections: list[str] = []
    for label, filename in _GENERATION_RULE_FILES:
        if domain == "grammar" and label != "Grammar v7":
            continue
        if domain == "reading" and label != "Reading v2":
            continue
        path = os.path.join(_ROOT_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            rules_text = f.read()
        body = _generation_sections(label, rules_text)
        sections.append(f"{label} RULES REFERENCE:\n{body}")
    return "\n\n".join(sections)


GENERATE_SYSTEM_PROMPT = """You are a DSAT question generation specialist following the current DSAT grammar and reading guide specifications.

Generate a complete SAT-style question matching the given specification. Your output must include:
1. question: passage_text, question_text, options (4 labeled A-D), correct_option_label
2. classification: domain-appropriate keys and difficulty fields
   - Grammar / Expression of Ideas: grammar_role_key, grammar_focus_key, syntactic_trap_key
   - Reading: question_family_key, reading_skill_family_key, reading_focus_key; grammar keys null
3. options: per-option analysis with distractor_type_key, why_plausible, why_wrong, precision_score
4. reasoning: primary_rule, trap_mechanism, correct_answer_reasoning
5. generation_profile: target keys, passage_template, frequency_band
6. review: annotation_confidence, needs_human_review

Rules:
- Passage must be 20-40 words for sentence_only items
- Formal academic register, no contractions or slang
- Self-contained meaning (no outside knowledge needed)
- At least one grammar distractor must target the declared syntactic trap
- At least one reading distractor must target the declared reasoning trap or test construct
- No two distractors may fail for the exact same reason
- correct option may appear in any position (A-D)
- Output valid JSON only"""


def build_generate_prompt(generation_request: dict, source_examples: list = None) -> tuple[str, str]:
    """Build system and user prompts for question generation."""
    rules_context = _load_generation_rule_context()
    user_parts = [f"Generation request:\n{json.dumps(generation_request, indent=2)}"]
    if source_examples:
        user_parts.append(
            "\nStored official questions are serving as the foundational source for generation. "
            "Use these examples to calibrate DSAT style, taxonomy, passage architecture, "
            "distractor construction, and difficulty. Do not copy passages, stems, or options.\n"
            f"{json.dumps(source_examples, indent=2)}"
        )
    user = "\n".join(user_parts)
    system = GENERATE_SYSTEM_PROMPT
    if rules_context:
        system = f"{system}\n\n{rules_context}"
    return system, user
