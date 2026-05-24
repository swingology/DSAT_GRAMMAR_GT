"""Validate sub-pattern citation format in v8 markdown.

Citation format spec:
  (PT{exam} M{module} Q{number}: "short quote")
  e.g. (PT7 M2 Q14: "a toxin that is deadly to nematodes that comes...")

Also accepts:
  [NO PT EVIDENCE — source: <web source name>]

Counts sub-patterns per focus key and fails if any focus key has > 3.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

V8 = Path("rules_agent_dsat_grammar_ingestion_generation_v8.md")

CITATION_RE = re.compile(r'\(PT(\d{1,2}) M(\d) Q(\d{1,2}): "[^"]+"\)')
NO_EVIDENCE_RE = re.compile(r"\[NO PT EVIDENCE — source: [^\]]+\]")
SUBPATTERN_RE = re.compile(r"^\*\*Sub-pattern — ([^*]+)\*\*", re.MULTILINE)
FOCUS_HEADER_RE = re.compile(r"^### `([a-z_]+)`(?:\s*/\s*`[a-z_]+`)?(?:\s*\([^)]+\))?\s*$", re.MULTILINE)


def main() -> int:
    text = V8.read_text()

    errors: list[str] = []
    # Restrict the scan to §B.3 only. Focus keys are repeated in B.4, D.2, etc.,
    # but sub-patterns live only in B.3 by design.
    B3_RE = re.compile(r"^## B\.3 Passage Construction Rules.*?(?=^## B\.4 )",
                       re.MULTILINE | re.DOTALL)
    b3_match = B3_RE.search(text)
    b3_text = b3_match.group(0) if b3_match else text
    sections = FOCUS_HEADER_RE.split(b3_text)
    counts: dict[str, int] = defaultdict(int)
    for i in range(1, len(sections), 2):
        focus = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""
        subpatterns = SUBPATTERN_RE.findall(body)
        counts[focus] += len(subpatterns)
        if counts[focus] > 3:
            errors.append(f"{focus}: {counts[focus]} sub-patterns (cap is 3)")
        # re.split with a capturing group yields [pre, name1, body1, name2, body2, ...]
        # Skip the pre-region and the name-regions; only check the body regions.
        sp_regions = re.split(SUBPATTERN_RE, body)
        for idx, name in enumerate(subpatterns):
            region = sp_regions[2 + idx * 2] if (2 + idx * 2) < len(sp_regions) else ""
            if not CITATION_RE.search(region) and not NO_EVIDENCE_RE.search(region):
                errors.append(
                    f"{focus} / {name.strip()}: missing citation or NO PT EVIDENCE marker"
                )

    print(f"Scanned {sum(counts.values())} sub-patterns across {len([k for k, v in counts.items() if v > 0])} focus keys (in §B.3)")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        return 1
    print("All sub-patterns have valid citations or NO PT EVIDENCE markers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
