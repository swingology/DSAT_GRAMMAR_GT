"""Generation prompt — produces new DSAT-style questions from a specification."""
import json


GENERATE_SYSTEM_PROMPT = """You are a DSAT question generation specialist following the rules_agent_dsat_grammar_ingestion_generation_v3.md specification.

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
    user_parts = [f"Generation request:\n{json.dumps(generation_request, indent=2)}"]
    if source_examples:
        user_parts.append(f"\nSource examples for reference:\n{json.dumps(source_examples, indent=2)}")
    user = "\n".join(user_parts)
    return GENERATE_SYSTEM_PROMPT, user