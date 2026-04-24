"""Pass 2 prompt — annotates extracted question data using V3 rules."""
import os
import json


def _load_v3_rules() -> str:
    """Load the V3 rules file as a string."""
    rules_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     "rules_agent_dsat_grammar_ingestion_generation_v3.md"),
    ]
    for path in rules_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
    return ""


ANNOTATE_SYSTEM_PROMPT = """You are a DSAT question annotation specialist following the rules_agent_dsat_grammar_ingestion_generation_v3.md specification.

Given extracted question data, you must produce a full annotation including:
1. Classification: grammar_role_key, grammar_focus_key, syntactic_trap_key, difficulty fields
2. Options: per-option analysis (distractor_type_key, why_plausible, why_wrong, precision_score)
3. Reasoning: primary_rule, trap_mechanism, correct_answer_reasoning
4. Generation profile: target keys, passage template, frequency band
5. Review: annotation_confidence, needs_human_review

IMPORTANT RULES:
- grammar_focus_key must be from the approved V3 keys
- grammar_role_key must match grammar_focus_key per V3 §17.1 mapping
- Every wrong option must have a distinct option_error_focus_key
- syntactic_trap_key describes the difficulty mechanism, not the rule tested
- Output valid JSON only

{rules_context}"""


def build_annotate_prompt(extract_json: dict, rules_file_path: str = "") -> tuple[str, str]:
    """Build system and user prompts for Pass 2 annotation."""
    rules_path = rules_file_path or _load_v3_rules()
    rules_context = ""
    if rules_path and os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            rules_text = f.read()
        if len(rules_text) > 8000:
            rules_context = f"\nV3 RULES REFERENCE (first 8000 chars):\n{rules_text[:8000]}\n[...truncated for length...]"
        else:
            rules_context = f"\nV3 RULES REFERENCE:\n{rules_text}"

    system = ANNOTATE_SYSTEM_PROMPT.format(rules_context=rules_context)
    user = f"""Annotate the following extracted question data:

{json.dumps(extract_json, indent=2)}"""
    return system, user