#!/usr/bin/env python
"""TASK-05 — build the canonical 1,845-question CB verbal bank JSON.

The three difficulty PDFs partition the pool exactly (611 + 624 + 610 = 1,845,
zero overlap — see ONTOLOGY_REFACTOR_PLAN.md §1.2) and, unlike the 752-item
Bank PDF, each record carries Question Difficulty and Correct Answer. So they
are the sole source; the Bank PDF is used only as a cross-check.

To backfill a new CB export: add its PDF to SOURCES, run audit_labels.py, then
re-run this. Output is keyed and sorted by question_id, so existing records are
unchanged and new ones slot in; downstream ingest upserts on cb_question_id.

Usage: uv run --with pymupdf python build_full_bank.py [-o OUT]
"""
import argparse
import json
import sys
from datetime import date

from extract_cb_bank import extract, validate

SOURCES = [
    "MyPractice - Question Bank - Results - easy.pdf",
    "MyPractice - Question Bank - Results medium.pdf",
    "MyPractice - Question Bank - Results - Verbal Hard.pdf",
]
CROSS_CHECK = "09_2026_New_Verbal_Bank.pdf"

# CB label defect: lowercase 't' appears 3x across MED / HARD / Results11.
SKILL_CANON = {"Cross-text Connections": "Cross-Text Connections"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="09_2026_New_Verbal_Bank_full.json")
    args = ap.parse_args()

    merged: dict[str, dict] = {}
    problems = 0
    for src in SOURCES:
        qs = extract(src)
        print(f"{len(qs):5d}  {src}")
        problems += validate(qs)
        for q in qs:
            q["skill"] = SKILL_CANON.get(q["skill"], q["skill"])
            q["source_pdf"] = src
            if q["question_id"] in merged:
                sys.exit(f"FATAL: duplicate id {q['question_id']} across difficulty PDFs")
            merged[q["question_id"]] = q

    # No pinned total: the bank grows as CB publishes more. Duplicate IDs across
    # sources are the real failure and are caught above; audit_labels.py reports
    # count drift against bank_manifest.json.

    # cross-check: every Bank PDF question must be present with identical labels
    mismatches = []
    for q in extract(CROSS_CHECK):
        m = merged.get(q["question_id"])
        if m is None:
            mismatches.append(f"{q['question_id']} in Bank but not in difficulty union")
        elif (m["domain"], m["skill"]) != (q["domain"], SKILL_CANON.get(q["skill"], q["skill"])):
            mismatches.append(f"{q['question_id']} label mismatch vs Bank PDF")
    if mismatches:
        sys.exit("FATAL cross-check:\n  " + "\n  ".join(mismatches[:20]))

    rows = sorted(merged.values(), key=lambda q: q["question_id"])
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source_pdfs": SOURCES,
                "extracted_at": date.today().isoformat(),
                "question_count": len(rows),
                "questions": rows,
            },
            f, indent=2, ensure_ascii=False,
        )
    print(f"\ncross-check vs {CROSS_CHECK}: OK")
    print(f"wrote {len(rows)} questions -> {args.out}")
    if problems:
        print(f"NOTE: {problems} record(s) tripped a field-level validation warning")


if __name__ == "__main__":
    main()
