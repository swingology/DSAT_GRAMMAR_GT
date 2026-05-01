"""Generation prompt — produces new DSAT-style questions from a specification."""
import json
import os


_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_RULE_SNIPPET_LIMIT = 6000
_GENERATION_RULE_FILES = [
    ("Grammar v7", "rules_agent_dsat_grammar_ingestion_generetion_v7.md"),
    ("Reading v2", "rules_agent_dsat_reading_v2.md"),
]


def _load_generation_rule_context() -> str:
    sections: list[str] = []
    for label, filename in _GENERATION_RULE_FILES:
        path = os.path.join(_ROOT_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            rules_text = f.read()
        if len(rules_text) > _RULE_SNIPPET_LIMIT:
            body = f"{rules_text[:_RULE_SNIPPET_LIMIT]}\n[...truncated for length...]"
        else:
            body = rules_text
        sections.append(f"{label} RULES REFERENCE:\n{body}")
    return "\n\n".join(sections)


GENERATE_SYSTEM_PROMPT = """You are a DSAT question generation specialist following the current DSAT grammar and reading guide specifications.

Generate a complete SAT-style question matching the given specification. Your output must include:
1. question: passage_text, question_text, options (4 labeled A-D), correct_option_label
2. classification: grammar_role_key, grammar_focus_key, syntactic_trap_key, difficulty fields
3. options: per-option analysis with distractor_type_key, why_plausible, why_wrong, precision_score
4. reasoning: primary_rule, trap_mechanism, correct_answer_reasoning
5. generation_profile: target keys, passage_template, frequency_band
6. review: annotation_confidence, needs_human_review

Rules:
- Passage must be 20-40 words for sentence_only items
- Formal academic register, no contractions or slang
- Self-contained meaning (no outside knowledge needed)
- At least one distractor must target the declared syntactic trap
- No two distractors may fail for the exact same grammar reason
- correct option may appear in any position (A-D)
- Output valid JSON only"""


def build_generate_prompt(generation_request: dict, source_examples: list = None) -> tuple[str, str]:
    """Build system and user prompts for question generation."""
    rules_context = _load_generation_rule_context()
    user_parts = [f"Generation request:\n{json.dumps(generation_request, indent=2)}"]
    if source_examples:
        user_parts.append(f"\nSource examples for reference:\n{json.dumps(source_examples, indent=2)}")
    user = "\n".join(user_parts)
    system = GENERATE_SYSTEM_PROMPT
    if rules_context:
        system = f"{system}\n\n{rules_context}"
    return system, user
