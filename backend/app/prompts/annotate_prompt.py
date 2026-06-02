"""Pass 2 prompt — annotates extracted question data using current DSAT rules.

Domain routing:
  Grammar  → grammar_v8 Part A (routing) + Parts C+D (annotation + taxonomy)
  Reading  → reading_v3 §3–14 (question fields through difficulty calibration)
  Unknown  → grammar_v8 Parts C+D + reading_v3 §3–7
"""
import os
import json
from functools import lru_cache

from app.models.ontology import (
    STIMULUS_MODE_KEYS,
    STEM_TYPE_KEYS,
    QUESTION_FAMILY_KEYS,
    GRAMMAR_ROLE_KEYS,
    GRAMMAR_FOCUS_BY_ROLE,
    READING_FOCUS_BY_SKILL_FAMILY,
    REASONING_TRAP_KEYS,
)


def _build_allowed_keys_block() -> str:
    """Render the controlled-vocabulary enums the annotation MUST choose from.

    The LLM otherwise invents descriptive synonyms (e.g. 'analyze_structure'
    instead of 'choose_structure_description') that fail validation.
    """
    lines = [
        "=== ALLOWED KEY VALUES (controlled vocabulary — choose EXACTLY one, verbatim) ===",
        "",
        "question_family_key MUST be one of:",
        "  " + ", ".join(QUESTION_FAMILY_KEYS),
        "  (do NOT use College Board display labels like 'Standard English Conventions'",
        "   or 'Information and Ideas' — use the snake_case key above)",
        "",
        "stimulus_mode_key MUST be one of:",
        "  " + ", ".join(STIMULUS_MODE_KEYS),
        "",
        "stem_type_key MUST be one of:",
        "  " + ", ".join(STEM_TYPE_KEYS),
        "",
        "grammar_role_key (grammar/SEC domain only) MUST be one of:",
        "  " + ", ".join(GRAMMAR_ROLE_KEYS),
        "",
        "grammar_focus_key (grammar/SEC domain only) MUST be one of these, matching the chosen grammar_role_key:",
    ]
    for role, focuses in GRAMMAR_FOCUS_BY_ROLE.items():
        lines.append(f"  {role}: {', '.join(focuses)}")
    lines.append("")
    lines.append(
        "reading_focus_key MUST be one of these, matching the chosen skill_family_key:"
    )
    for family, focuses in READING_FOCUS_BY_SKILL_FAMILY.items():
        lines.append(f"  {family}: {', '.join(focuses)}")
    lines.append("")
    lines.append(
        "reasoning_trap_key (question-level, reading domains) MUST be one of "
        "(per reading_v3 §10 — do NOT use the §12.1 distractor_type_key list here):"
    )
    lines.append("  " + ", ".join(REASONING_TRAP_KEYS))
    lines.append("")
    lines.append(
        "Never invent a synonym or descriptive variant. If none fits perfectly, "
        "pick the closest listed value — do not output an unlisted key."
    )
    return "\n".join(lines)


_ALLOWED_KEYS_BLOCK = _build_allowed_keys_block()

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_GRAMMAR_FILE = "rules_agent_dsat_grammar_ingestion_generation_v8.md"
_READING_FILE = "rules_agent_dsat_reading_v3.md"

# stem_type_key values that unambiguously belong to grammar / SEC domain
_GRAMMAR_STEMS = {
    "complete_the_text",
    "choose_transition",
    "rhetorical_synthesis",
    "choose_conjunction",
    "fix_punctuation",
    "fix_sentence_boundary",
    "no_change",
}

# stem_type_key values that unambiguously belong to reading domains
_READING_STEMS = {
    "vocabulary_in_context",
    "choose_words_in_context",
    "describe_structure",
    "state_main_purpose",
    "state_main_idea",
    "choose_main_idea",
    "identify_main_purpose",
    "support_claim",
    "function_of_part",
    "choose_function",
    "interpret_graph",
    "interpret_data",
    "infer_author_opinion",
    "infer_character",
    "analyze_argument",
    "choose_cross_text_connection",
    "choose_command_of_evidence_textual",
    "choose_command_of_evidence_quantitative",
    "choose_best_support",
    "synthesize_information",
    "present_methods",
    "emphasize_similarity",
    "compare_hypotheses",
    "most_logically_completes",
}

# question text keywords that signal grammar domain for complete_the_text
_GRAMMAR_QUESTION_SIGNALS = {
    "punctuation", "transition", "conjunction", "semicolon", "comma",
    "period", "colon", "dash", "which choice most effectively",
}


@lru_cache(maxsize=2)
def _read_file(filename: str) -> str:
    path = os.path.join(_ROOT_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_between(text: str, start_marker: str, end_marker: str | None = None) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    if end_marker:
        end = text.find(end_marker, start + len(start_marker))
        return text[start:end] if end != -1 else text[start:]
    return text[start:]


@lru_cache(maxsize=1)
def _grammar_context() -> str:
    text = _read_file(_GRAMMAR_FILE)
    if not text:
        return ""
    routing = _extract_between(text, "# PART A", "# PART B")
    annotation = _extract_between(text, "# PART C", "# PART E")
    return f"Grammar v8 RULES REFERENCE:\n=== GRAMMAR v8: MODE ROUTING ===\n{routing}\n\n=== GRAMMAR v8: ANNOTATION + TAXONOMY (Parts C & D) ===\n{annotation}"


@lru_cache(maxsize=1)
def _reading_context() -> str:
    text = _read_file(_READING_FILE)
    if not text:
        return ""
    core = _extract_between(text, "## 3. Question Fields", "## 16. Generation Rules")
    # Always include disambiguation rules and student failure modes
    extra = ""
    for section in ("## 17. Disambiguation Rules", "## 19. Student Failure Mode Keys"):
        chunk = _extract_between(text, section, "##" if section != "## 19. Student Failure Mode Keys" else "## 20.")
        if chunk:
            extra += f"\n{chunk}"
    return f"Reading v3 RULES REFERENCE:\n=== READING v3: ANNOTATION REFERENCE (§3-14 + disambiguation) ===\n{core}{extra}"


@lru_cache(maxsize=1)
def _unknown_context() -> str:
    g = _extract_between(_read_file(_GRAMMAR_FILE), "# PART D", "# PART E")
    r = _reading_context()
    return f"Grammar v8 RULES REFERENCE:\n=== GRAMMAR v8: TAXONOMY (Part D) ===\n{g}\n\n{r}"


def _detect_domain(q_data: dict) -> str:
    stem = (q_data.get("stem_type_key") or "").strip().lower()
    if stem in _GRAMMAR_STEMS:
        # complete_the_text can be vocabulary (reading) — check question text
        if stem == "complete_the_text":
            q_text = (q_data.get("question_text") or "").lower()
            if any(sig in q_text for sig in _GRAMMAR_QUESTION_SIGNALS):
                return "grammar"
            # Has a passage? Likely reading (words in context)
            if q_data.get("passage_text"):
                return "reading"
            # Sentence-only complete_the_text defaults to grammar unless overridden
            return "grammar"
        return "grammar"
    if stem in _READING_STEMS:
        return "reading"
    # Fallback: check stimulus mode
    mode = (q_data.get("stimulus_mode_key") or "").lower()
    if mode in ("graph_data", "table_data"):
        return "reading"
    return "unknown"


# Instructions-only template: rules reference is provided as a SEPARATE cached block.
# Used by build_annotate_prompt_parts() for prompt-cached calls.
_SYSTEM_INSTRUCTIONS_TEMPLATE = """You are a DSAT question annotation specialist. Annotate the given question using the rules reference provided above.

=== HARD ROUTING RULES (override anything in the rules reference) ===

1. DOMAIN SPLIT — determined by what cognitive skill the correct answer requires:
   • Standard English Conventions (SEC) / Expression of Ideas (grammar-adjacent):
     - grammar_focus_key: required, non-null
     - grammar_role_key: required, non-null
     - Use grammar_v8 taxonomy keys only
   • Information and Ideas / Craft and Structure (reading):
     - grammar_focus_key: MUST be null
     - grammar_role_key: MUST be null
     - Use reading_v3 taxonomy keys only

2. complete_the_text DISAMBIGUATION:
   • If the blank tests a TRANSITION WORD or CONJUNCTION → SEC domain
     stem_type_key = "complete_the_text", skill_family = "expression_of_ideas"
   • If the blank tests VOCABULARY / WORD CHOICE and there is a passage → Reading domain
     stem_type_key = "choose_words_in_context", skill_family = "words_in_context"
   • If the blank tests VOCABULARY and stimulus_mode = sentence_only → SEC domain
     stem_type_key = "complete_the_text", skill_family = "expression_of_ideas"

3. NULLABILITY ENFORCEMENT:
   • difficulty_grammar: null for reading-domain questions
   • difficulty_reading: null for grammar-domain questions
   • syntactic_trap_key: null for reading-domain questions unless explicitly applicable

4. DIFFICULTY CALIBRATION — do not default everything to "medium":
   • low: straightforward rule application, no trap
   • medium: one plausible trap, moderate passage complexity
   • high: multiple traps, complex syntax, subtle distinction
   • very_high: expert-level, rare construction, or cross-passage inference

5. OUTPUT: valid JSON only, matching the required output shape from the rules reference.

6. CONTROLLED VOCABULARY: question_family_key, stimulus_mode_key, stem_type_key,
   grammar_role_key, grammar_focus_key, and reading_focus_key must be drawn
   verbatim from the allowed-values list below. Output is rejected if any value
   is not an exact match. Do NOT use descriptive variants, display labels, or
   human-readable synonyms — use the exact snake_case key string listed.

7. AMENDMENT PROPOSALS:
   • Current content_origin: {content_origin}
   • Use existing approved keys for actual annotation. Never put proposed keys in
     production annotation fields.
   • If content_origin is "official" and no existing rule/key fits the official
     item, you may emit reasoning.amendment_proposal.
   • If content_origin is not "official", reasoning.amendment_proposal MUST be
     null or omitted.
   • A proposal must include affected_doc, affected_vocab, proposed_value,
     parent_key when applicable, definition, current_best_fit,
     why_current_rules_are_insufficient, official_evidence, rule_doc_patch, and
     master_json_patch.

{allowed_keys}"""

_SYSTEM_BASE = """You are a DSAT question annotation specialist. Annotate the given question using the rules reference below.

=== HARD ROUTING RULES (override anything in the rules reference) ===

1. DOMAIN SPLIT — determined by what cognitive skill the correct answer requires:
   • Standard English Conventions (SEC) / Expression of Ideas (grammar-adjacent):
     - grammar_focus_key: required, non-null
     - grammar_role_key: required, non-null
     - Use grammar_v8 taxonomy keys only
   • Information and Ideas / Craft and Structure (reading):
     - grammar_focus_key: MUST be null
     - grammar_role_key: MUST be null
     - Use reading_v3 taxonomy keys only

2. complete_the_text DISAMBIGUATION:
   • If the blank tests a TRANSITION WORD or CONJUNCTION → SEC domain
     stem_type_key = "complete_the_text", skill_family = "expression_of_ideas"
   • If the blank tests VOCABULARY / WORD CHOICE and there is a passage → Reading domain
     stem_type_key = "choose_words_in_context", skill_family = "words_in_context"
   • If the blank tests VOCABULARY and stimulus_mode = sentence_only → SEC domain
     stem_type_key = "complete_the_text", skill_family = "expression_of_ideas"

3. NULLABILITY ENFORCEMENT:
   • difficulty_grammar: null for reading-domain questions
   • difficulty_reading: null for grammar-domain questions
   • syntactic_trap_key: null for reading-domain questions unless explicitly applicable

4. DIFFICULTY CALIBRATION — do not default everything to "medium":
   • low: straightforward rule application, no trap
   • medium: one plausible trap, moderate passage complexity
   • high: multiple traps, complex syntax, subtle distinction
   • very_high: expert-level, rare construction, or cross-passage inference

5. OUTPUT: valid JSON only, matching the required output shape from the rules reference.

6. CONTROLLED VOCABULARY: question_family_key, stimulus_mode_key, stem_type_key,
   grammar_role_key, grammar_focus_key, and reading_focus_key must be drawn
   verbatim from the allowed-values list below. Output is rejected if any value
   is not an exact match. Do NOT use descriptive variants, display labels, or
   human-readable synonyms — use the exact snake_case key string listed.

7. AMENDMENT PROPOSALS:
   • Current content_origin: {content_origin}
   • Use existing approved keys for actual annotation. Never put proposed keys in
     production annotation fields.
   • If content_origin is "official" and no existing rule/key fits the official
     item, you may emit reasoning.amendment_proposal.
   • If content_origin is not "official", reasoning.amendment_proposal MUST be
     null or omitted.
   • A proposal must include affected_doc, affected_vocab, proposed_value,
     parent_key when applicable, definition, current_best_fit,
     why_current_rules_are_insufficient, official_evidence, rule_doc_patch, and
     master_json_patch.

{allowed_keys}

{rules_context}"""


def _infer_domain_from_annotation(annotation: dict) -> str:
    """Infer domain from the LLM's annotation output rather than input heuristics.

    Returns "grammar", "reading", or "unknown".
    Checks top-level and 'classification' block.
    """
    def _check(d: dict) -> str | None:
        gfk = d.get("grammar_focus_key")
        domain_str = (d.get("domain") or d.get("domain_key") or "").lower()
        if gfk and gfk not in ("null", "none", ""):
            return "grammar"
        if any(x in domain_str for x in ("standard english", "sec", "expression of ideas", "grammar")):
            return "grammar"
        if any(x in domain_str for x in ("information", "craft", "words in context", "reading")):
            return "reading"
        skill = (d.get("skill_family_key") or d.get("skill_family") or "").lower()
        if any(x in skill for x in ("words in context", "information", "craft", "central ideas", "command of evidence", "inferences", "cross-text")):
            return "reading"
        return None

    result = _check(annotation)
    if result:
        return result
    cls = annotation.get("classification") or {}
    if isinstance(cls, dict):
        result = _check(cls)
        if result:
            return result
    return "unknown"


def enforce_nullability(annotation: dict, domain: str) -> dict:
    """Post-process LLM output to enforce domain nullability rules.

    Grammar domain: grammar_focus_key and grammar_role_key must be non-null;
                    difficulty_reading must be null.
    Reading domain: grammar_focus_key and grammar_role_key must be null;
                    difficulty_grammar must be null.
    Applies at the top level and inside 'classification' if present.

    The `domain` arg is a hint from _detect_domain (pre-annotation); the function
    also infers domain from the annotation itself and uses whichever is more
    specific to avoid false nullifications on ambiguous questions like
    sentence-only complete_the_text.
    """
    result = dict(annotation)

    # Infer from the LLM's own output (more reliable for ambiguous stems)
    inferred = _infer_domain_from_annotation(annotation)
    effective_domain = inferred if inferred != "unknown" else domain

    def _patch(d: dict) -> dict:
        d = dict(d)
        if effective_domain == "reading":
            d["grammar_focus_key"] = None
            d["grammar_role_key"] = None
            d["difficulty_grammar"] = None
            d.pop("secondary_grammar_focus_keys", None)
        elif effective_domain == "grammar":
            d["difficulty_reading"] = None
        return d

    result = _patch(result)
    if "classification" in result and isinstance(result["classification"], dict):
        result["classification"] = _patch(result["classification"])
    return result


_PASSAGE_CHAR_LIMIT = 800
_PAIRED_PASSAGE_CHAR_LIMIT = 600

def _trim_q_data_for_annotation(q_data: dict) -> dict:
    """Return a copy of q_data with large text fields trimmed.

    The annotation LLM needs domain signals (stem type, question text, option
    labels) — not full passage bodies. Sending 3-8K-char passages inflates the
    user payload beyond what most local models handle cleanly and is the
    primary cause of annotation hangs on reading questions.
    """
    trimmed = dict(q_data)
    for field, limit in (
        ("passage_text", _PASSAGE_CHAR_LIMIT),
        ("paired_passage_text", _PAIRED_PASSAGE_CHAR_LIMIT),
    ):
        val = trimmed.get(field)
        if isinstance(val, str) and len(val) > limit:
            trimmed[field] = val[:limit] + " …[truncated for annotation]"
    return trimmed


def build_annotate_prompt_parts(
    q_data: dict | None = None,
    **kwargs,
) -> tuple[str, str, str]:
    """Return (system_static, system_dynamic, user) for prompt-cached annotation calls.

    system_static  — the grammar v8 or reading v3 rules block; mark with cache_control
                     on Anthropic or use as num_keep prefix on Ollama (~10-17K tokens,
                     identical for all questions of the same domain in a job).
    system_dynamic — routing rules + allowed keys + content_origin; fresh each call
                     (~500-700 tokens, changes when content_origin differs).
    user           — per-question JSON; always fresh.
    """
    if q_data is None:
        q_data = kwargs.pop("extract_json", None) or {}
    content_origin = kwargs.pop("content_origin", None) or q_data.get("content_origin") or "unknown"

    domain = _detect_domain(q_data)
    if domain == "grammar":
        system_static = _grammar_context()
    elif domain == "reading":
        system_static = _reading_context()
    else:
        system_static = _unknown_context()

    system_dynamic = _SYSTEM_INSTRUCTIONS_TEMPLATE.format(
        allowed_keys=_ALLOWED_KEYS_BLOCK,
        content_origin=content_origin,
    )
    user = f"Annotate the following extracted question:\n\n{json.dumps(_trim_q_data_for_annotation(q_data), indent=2)}"
    return system_static, system_dynamic, user


def build_annotate_prompt(q_data: dict | None = None, rules_file_path: str = "", **kwargs) -> tuple[str, str]:
    """Build system and user prompts for Pass 2 annotation.

    Args:
        q_data: extracted question dict from Pass 1
        rules_file_path: optional override path to a custom rules file
    """
    if q_data is None:
        q_data = kwargs.pop("extract_json", None)
    if q_data is None:
        q_data = {}
    content_origin = kwargs.pop("content_origin", None) or q_data.get("content_origin") or "unknown"

    if rules_file_path and os.path.exists(rules_file_path):
        with open(rules_file_path, "r", encoding="utf-8") as f:
            rules_context = f"CUSTOM RULES REFERENCE:\n{f.read()}"
    else:
        domain = _detect_domain(q_data)
        if domain == "grammar":
            rules_context = _grammar_context()
        elif domain == "reading":
            rules_context = _reading_context()
        else:
            rules_context = _unknown_context()

    system = _SYSTEM_BASE.format(
        rules_context=rules_context,
        allowed_keys=_ALLOWED_KEYS_BLOCK,
        content_origin=content_origin,
    )
    user = f"Annotate the following extracted question:\n\n{json.dumps(_trim_q_data_for_annotation(q_data), indent=2)}"
    return system, user


def clear_prompt_cache() -> None:
    """Invalidate all cached rules contexts in dependency order.

    Call after updating rules files on disk, or in test teardown.
    Order matters: clear derived caches before the raw file cache.
    """
    _unknown_context.cache_clear()
    _grammar_context.cache_clear()
    _reading_context.cache_clear()
    _read_file.cache_clear()
