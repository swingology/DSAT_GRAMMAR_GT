"""Markdown parser — extracts text and optional YAML front matter."""
import re


_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_markdown(text: str) -> dict:
    """Parse markdown text, extracting optional front matter.
    Returns: {"text": str, "front_matter": dict}
    """
    front_matter = {}
    match = _FRONT_MATTER_RE.match(text)
    if match:
        fm_text = match.group(1)
        body = text[match.end():]
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                front_matter[key.strip()] = value.strip()
    else:
        body = text
    return {"text": body, "front_matter": front_matter}