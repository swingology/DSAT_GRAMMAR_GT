"""Robust JSON extraction from LLM output text.
Handles markdown code fences, leading/trailing text, and nested objects.
"""
import json
import re


def extract_json_from_text(text: str) -> dict:
    """Extract a JSON object from text that may contain markdown fences or surrounding prose."""
    # Try 1: Direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try 2: Extract from markdown code fence (```json ... ```)
    fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
    match = fence_pattern.search(text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try 3: Find first { ... } using brace counting
    first_brace = text.find("{")
    if first_brace != -1:
        depth = 0
        for i in range(first_brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[first_brace : i + 1])
                    except json.JSONDecodeError:
                        break

    raise ValueError("No valid JSON found in text")