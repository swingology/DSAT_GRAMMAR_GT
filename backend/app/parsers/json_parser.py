"""Robust JSON extraction from LLM output text.
Handles markdown code fences, leading/trailing text, and nested objects.
"""
import ast
import json
import re


def _parse_direct_json(text: str):
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def _extract_fenced_blocks(text: str) -> list[str]:
    fence_pattern = re.compile(r"```(?:[a-zA-Z0-9_-]+)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
    return [match.group(1).strip() for match in fence_pattern.finditer(text)]


def _extract_last_braced_candidate(text: str) -> str | None:
    """Find the last complete JSON object in text.

    Useful when a reasoning model emits a long thinking preamble followed by
    the actual JSON answer — the standard first-brace scan picks up the wrong
    opening brace inside the reasoning text.
    """
    last_close = text.rfind("}")
    if last_close == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    quote_char = ""
    for i in range(last_close, -1, -1):
        ch = text[i]
        if escape:
            escape = False
            continue
        if in_string:
            if ch == "\\" :
                escape = True
            elif ch == quote_char:
                in_string = False
            continue
        if ch in {'"', "'"}:
            in_string = True
            quote_char = ch
            continue
        if ch == "}":
            depth += 1
        elif ch == "{":
            depth -= 1
            if depth == 0:
                return text[i : last_close + 1]
    return None


def _extract_first_braced_candidate(text: str) -> str | None:
    in_string = False
    escape = False
    quote_char = ""
    first_brace = text.find("{")
    if first_brace == -1:
        return None
    depth = 0
    for i in range(first_brace, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote_char:
                in_string = False
            continue
        if ch in {'"', "'"}:
            in_string = True
            quote_char = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[first_brace : i + 1]
    return None


def _strip_reasoning_wrappers(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"<think>.*?</think>", "", stripped, flags=re.DOTALL | re.IGNORECASE)
    stripped = re.sub(r"<thinking>.*?</thinking>", "", stripped, flags=re.DOTALL | re.IGNORECASE)
    stripped = re.sub(r"<analysis>.*?</analysis>", "", stripped, flags=re.DOTALL | re.IGNORECASE)
    stripped = re.sub(r"^\s*(analysis|reasoning)\s*:\s*", "", stripped, flags=re.IGNORECASE)
    return stripped.strip()


def _normalize_quotes_and_commas(text: str) -> str:
    replacements = str.maketrans({
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u00a0": " ",
    })
    normalized = text.translate(replacements)
    normalized = re.sub(r",(\s*[}\]])", r"\1", normalized)
    return normalized


def _quote_bare_keys(text: str) -> str:
    return re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)', r'\1"\2"\3', text)


def _repair_json_like_object(text: str) -> str:
    repaired = _normalize_quotes_and_commas(text)
    repaired = _quote_bare_keys(repaired)
    repaired = re.sub(r":\s*'([^'\\]*(?:\\.[^'\\]*)*)'", lambda m: ': ' + json.dumps(m.group(1)), repaired)
    return repaired


def _parse_python_literal_object(text: str):
    candidate = _normalize_quotes_and_commas(text)
    candidate = _quote_bare_keys(candidate)
    candidate = re.sub(r"\btrue\b", "True", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bfalse\b", "False", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bnull\b", "None", candidate, flags=re.IGNORECASE)
    try:
        parsed = ast.literal_eval(candidate)
    except (ValueError, SyntaxError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_with_default_strategies(text: str) -> dict | None:
    candidates = [text, _strip_reasoning_wrappers(text)]
    for candidate in candidates:
        parsed = _parse_direct_json(candidate)
        if isinstance(parsed, dict):
            return parsed

    for block in _extract_fenced_blocks(text):
        parsed = _parse_direct_json(block)
        if isinstance(parsed, dict):
            return parsed

    braced = _extract_first_braced_candidate(text)
    if braced:
        parsed = _parse_direct_json(braced)
        if isinstance(parsed, dict):
            return parsed
    return None


def _extract_with_kimi_strategy(text: str) -> dict | None:
    parsed = _extract_with_default_strategies(text)
    if parsed is not None:
        return parsed

    stripped = _strip_reasoning_wrappers(text)
    braced = _extract_first_braced_candidate(stripped)
    # Also try the last braced candidate — handles reasoning models that emit a
    # long thinking preamble before the actual JSON answer.
    last_braced = _extract_last_braced_candidate(stripped)
    candidates = [c for c in [stripped, braced, last_braced] + _extract_fenced_blocks(stripped) if c]
    for candidate in candidates:
        repaired = _repair_json_like_object(candidate)
        parsed = _parse_direct_json(repaired)
        if isinstance(parsed, dict):
            return parsed
        parsed = _parse_python_literal_object(candidate)
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_json_from_text(
    text: str,
    provider_name: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Extract a JSON object from model output.

    Uses a strict default strategy and allows model-specific repair paths for
    providers that are known to emit JSON-adjacent rather than valid JSON.
    """
    model_key = (model_name or "").lower()
    provider_key = (provider_name or "").lower()

    if provider_key == "ollama" or "kimi" in model_key:
        parsed = _extract_with_kimi_strategy(text)
        if parsed is not None:
            return parsed

    parsed = _extract_with_default_strategies(text)
    if parsed is not None:
        return parsed

    # Universal fallback: repair path for any provider that the strict path couldn't handle
    if not (provider_key == "ollama" or "kimi" in model_key):
        parsed = _extract_with_kimi_strategy(text)
        if parsed is not None:
            return parsed

    preview = text[:200].replace("\n", " ")
    raise ValueError(
        f"No valid JSON found in text "
        f"(provider={provider_name!r}, model={model_name!r}, "
        f"input_len={len(text)}, preview={preview!r})"
    )


def extract_json_array_from_text(text: str) -> list:
    """Extract a JSON array from text that may contain markdown fences or surrounding prose.

    Useful when an LLM returns a raw ``[{...}, {...}]`` array instead of a
    wrapped ``{questions: [...]}`` object. Falls back to extracting a single
    object and wrapping it in a list.
    """
    # Try 1: Direct parse as array
    try:
        result = json.loads(text.strip())
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try 2: Extract from markdown fence
    fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
    match = fence_pattern.search(text)
    if match:
        try:
            result = json.loads(match.group(1).strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Try 3: Find first [ ... ] using bracket counting
    first_bracket = text.find("[")
    if first_bracket != -1:
        depth = 0
        for i in range(first_bracket, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        result = json.loads(text[first_bracket : i + 1])
                        if isinstance(result, list):
                            return result
                    except json.JSONDecodeError:
                        break

    # Fallback: single object wrapped in a list
    return [extract_json_from_text(text)]


_FLAT_ANNOTATION_KEYS = {
    # Grammar
    "grammar_focus_key", "grammar_role_key",
    # Shared structural
    "stimulus_mode_key", "stem_type_key", "question_family_key",
    # Reading domain
    "skill_family_key", "reading_focus_key",
    "difficulty_overall", "difficulty_reading", "difficulty_grammar",
    "reasoning_trap_key", "syntactic_trap_key",
    "answer_mechanism_key", "evidence_scope_key", "evidence_location_key",
    "solver_pattern_key",
    # Utility
    "explanation_short", "explanation_full", "annotation_confidence", "needs_human_review",
}

# Some LLMs output the reading skill family as a human-readable display name
# (e.g. "Words in Context") instead of the snake_case key ("words_in_context").
# Map display name → canonical key so normalize_annotation can promote it.
_SKILL_FAMILY_DISPLAY_TO_KEY: dict[str, str] = {
    "words in context": "words_in_context",
    "central ideas and details": "central_ideas_and_details",
    "command of evidence - textual": "command_of_evidence_textual",
    "command of evidence textual": "command_of_evidence_textual",
    "command of evidence - quantitative": "command_of_evidence_quantitative",
    "command of evidence quantitative": "command_of_evidence_quantitative",
    "command of evidence": "command_of_evidence_textual",
    "inferences": "inferences",
    "text structure and purpose": "text_structure_and_purpose",
    "cross-text connections": "cross_text_connections",
    "cross text connections": "cross_text_connections",
}


def normalize_annotation(data: dict) -> dict:
    """Flatten nested annotation dicts from non-compliant LLMs (e.g. Qwen nesting under 'classification').

    Claude and OpenAI already return flat output so this is a no-op for them.
    Any key in _FLAT_ANNOTATION_KEYS found inside a nested dict is bubbled up
    to the top level; existing top-level keys are never overwritten.

    Also handles the case where the LLM outputs reading skill family as a
    human-readable display name under 'skill_family' instead of the snake_case
    'skill_family_key' — converts and promotes it if skill_family_key is absent.
    """
    flat = dict(data)
    for v in data.values():
        if not isinstance(v, dict):
            continue
        for key, val in v.items():
            if key in _FLAT_ANNOTATION_KEYS and key not in flat:
                flat[key] = val
        # Promote skill_family (display name) → skill_family_key if needed
        if "skill_family_key" not in flat and "skill_family_key" not in v:
            display = (v.get("skill_family") or "").strip().lower()
            if display:
                canonical = _SKILL_FAMILY_DISPLAY_TO_KEY.get(display)
                if canonical:
                    flat["skill_family_key"] = canonical
    return flat


# Nested sections the canonicalizer scans for promotable canonical fields, in
# precedence order (earlier sections win on conflict among nested sources).
_CANONICAL_NESTED_SECTIONS = (
    "classification", "question", "review", "reasoning", "generation_profile",
)

# Alias map: non-canonical field name → canonical top-level field name.
_FIELD_ALIASES = {
    "reading_skill_family_key": "skill_family_key",
}

# A top-level value that equals one of these is treated as "absent" and is
# eligible to be filled from a valid nested value.
_EMPTY_SENTINELS = (None, "", "none", "null", "n/a")


def _is_empty_value(value) -> bool:
    """True when a top-level value should be treated as missing for canonicalization."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in _EMPTY_SENTINELS:
        return True
    return False


def _canonical_value(field: str, value):
    """Apply field-specific normalization to a promotable value (e.g. display→key)."""
    if field == "skill_family_key" and isinstance(value, str):
        canonical = _SKILL_FAMILY_DISPLAY_TO_KEY.get(value.strip().lower())
        return canonical or value
    return value


def canonicalize_annotation(raw: dict) -> dict:
    """Deterministically reconcile nested LLM annotation shape with the flat schema.

    This is the single canonicalization step for all annotation paths (official
    ingest, re-annotation, generation). It is intentionally stricter than
    ``normalize_annotation``: it fills empty/null/``"none"`` top-level values from
    valid nested values, and it surfaces — rather than silently resolves —
    disagreements between a non-empty top-level value and a different nested value.

    Behavior:
    - Promotes ``_FLAT_ANNOTATION_KEYS`` from nested sections to top level.
    - Fills a missing / null / empty-string / ``"none"`` top-level value from a
      non-empty nested value.
    - Conflict policy: when top-level and nested are both non-empty AND differ,
      the top-level value is KEPT, a record is added to
      ``_annotation_quality.conflicts``, and ``needs_human_review`` is set true.
      No value is ever silently overwritten in the multi-LLM case.
    - Normalizes aliases (e.g. ``reading_skill_family_key`` → ``skill_family_key``)
      and ``skill_family`` display names → ``skill_family_key``.
    - Copies ``classification.passage_tokens`` → top-level ``passage_tokens`` as a
      soft fallback only (Pass 3 span annotation remains authoritative).
    - Lifts ``review.annotation_confidence`` / ``review.needs_human_review``.
    - Records all repairs/conflicts under ``_annotation_quality``.
    """
    if not isinstance(raw, dict):
        return raw

    out = dict(raw)
    promoted: list[str] = []
    repaired: list[str] = []
    conflicts: list[dict] = []

    def _consider(field: str, nested_value, source: str) -> None:
        nested_value = _canonical_value(field, nested_value)
        if _is_empty_value(nested_value):
            return
        if field not in out or field not in raw:
            # Field absent at top level → straightforward promotion.
            if field not in out:
                out[field] = nested_value
                promoted.append(field)
                return
        current = out.get(field)
        if _is_empty_value(current):
            # Top-level present but empty/null/"none" → repair from nested.
            out[field] = nested_value
            repaired.append(field)
        elif current != nested_value:
            # Both non-empty and different → keep top-level, flag for review.
            conflicts.append({
                "field": field,
                "kept_top_level": current,
                "nested_value": nested_value,
                "nested_source": source,
            })

    for section_name in _CANONICAL_NESTED_SECTIONS:
        section = raw.get(section_name)
        if not isinstance(section, dict):
            continue
        for key, value in section.items():
            target = _FIELD_ALIASES.get(key, key)
            if target in _FLAT_ANNOTATION_KEYS:
                _consider(target, value, f"{section_name}.{key}")
            elif key == "skill_family":
                _consider("skill_family_key", value, f"{section_name}.skill_family")

    # Top-level alias normalization (reading_skill_family_key → skill_family_key).
    for alias, canonical in _FIELD_ALIASES.items():
        if alias in raw and not _is_empty_value(raw.get(alias)):
            _consider(canonical, raw[alias], alias)

    # passage_tokens soft fallback from classification.
    classification = raw.get("classification")
    if (
        isinstance(classification, dict)
        and isinstance(classification.get("passage_tokens"), list)
        and not out.get("passage_tokens")
    ):
        out["passage_tokens"] = classification["passage_tokens"]
        promoted.append("passage_tokens")

    if conflicts:
        out["needs_human_review"] = True

    if promoted or repaired or conflicts:
        quality = dict(out.get("_annotation_quality") or {})
        if promoted:
            quality["promoted_fields"] = sorted(set(promoted))
        if repaired:
            quality["repaired_from_nested"] = sorted(set(repaired))
        if conflicts:
            quality["conflicts"] = conflicts
        out["_annotation_quality"] = quality

    return out
