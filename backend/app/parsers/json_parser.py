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
    for candidate in [stripped, braced] + _extract_fenced_blocks(stripped):
        if not candidate:
            continue
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

    if "kimi" in model_key or ("ollama" == provider_key and "kimi" in model_key):
        parsed = _extract_with_kimi_strategy(text)
        if parsed is not None:
            return parsed

    parsed = _extract_with_default_strategies(text)
    if parsed is not None:
        return parsed

    raise ValueError("No valid JSON found in text")


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
    "grammar_focus_key", "grammar_role_key", "stimulus_mode_key", "stem_type_key",
    "explanation_short", "explanation_full", "annotation_confidence", "needs_human_review",
}


def normalize_annotation(data: dict) -> dict:
    """Flatten nested annotation dicts from non-compliant LLMs (e.g. Qwen nesting under 'classification').

    Claude and OpenAI already return flat output so this is a no-op for them.
    Any key in _FLAT_ANNOTATION_KEYS found inside a nested dict is bubbled up
    to the top level; existing top-level keys are never overwritten.
    """
    # Preserve the original top-level shape for downstream metadata storage
    # while also bubbling up commonly queried fields for flat access.
    flat = dict(data)
    for v in data.values():
        if isinstance(v, dict):
            for key, val in v.items():
                if key in _FLAT_ANNOTATION_KEYS and key not in flat:
                    flat[key] = val
    return flat
