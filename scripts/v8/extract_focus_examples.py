"""Extract official-classification examples per grammar_focus_key.

Reads analysis/calibration/official_classifications.json and writes one JSON
file per focus_key into analysis/v8/focus_evidence/. Each per-focus file
contains the full question records that v7 classified to that focus, sorted
by source_exam_code then source_question_number.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

CALIBRATION = Path("analysis/calibration/official_classifications.json")
OUT_DIR = Path("analysis/v8/focus_evidence")


def main() -> int:
    data = json.loads(CALIBRATION.read_text())
    by_focus: dict[str, list] = defaultdict(list)
    for q in data["questions"]:
        focus = (q.get("classification") or {}).get("grammar_focus_key")
        if focus:
            by_focus[focus].append(q)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for focus, items in by_focus.items():
        items.sort(
            key=lambda q: (
                str(q.get("source_exam_code") or ""),
                str(q.get("source_module_code") or ""),
                q.get("source_question_number") or 0,
            )
        )
        (OUT_DIR / f"{focus}.json").write_text(json.dumps(items, indent=2))

    print(f"Wrote {len(by_focus)} focus files to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
