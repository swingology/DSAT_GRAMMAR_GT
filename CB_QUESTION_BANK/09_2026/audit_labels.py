#!/usr/bin/env python
"""TASK-04 — re-runnable label-integrity audit for the CB verbal PDFs.

Re-parses every verbal PDF with logic independent of extract_cb_bank.py and
asserts the nine invariants recorded in ONTOLOGY_REFACTOR_PLAN.md §1.
Exit 0 if all hold, 1 otherwise. Run after adding or replacing any source PDF.

Usage: uv run --with pymupdf python audit_labels.py [-v]
"""
import argparse
import collections
import itertools
import pathlib
import re
import sys

import pymupdf

ROOT = pathlib.Path(__file__).resolve().parent.parent  # CB_QUESTION_BANK/
PDFS = [
    "09_2026/09_2026_New_Verbal_Bank.pdf",
    "09_2026/09_2026_New_Verbal_Bank  - Questions ONLY.pdf",
    "09_2026/MyPractice - Question Bank - Results - easy.pdf",
    "09_2026/MyPractice - Question Bank - Results medium.pdf",
    "09_2026/MyPractice - Question Bank - Results - Verbal Hard.pdf",
    "MyPractice - Question Bank - Results - exclude active.pdf",
    "MyPractice - Question Bank - Results part 2.pdf",
    "MyPractice - Question Bank - Results11.pdf",
    "MyPractice - Question Bank - part 1 page 1-5.pdf",
]
DIFFICULTY_SPLITS = PDFS[2:5]
EXPECTED_UNIQUE = 1845
EXPECTED_ROWS = 4465
# The 10 legal (Domain, Skill) pairs — DOMAINS_SKILLS.md is the source of truth.
LEGAL_PAIRS = {
    ("Craft and Structure", "Cross-Text Connections"),
    ("Craft and Structure", "Text Structure and Purpose"),
    ("Craft and Structure", "Words in Context"),
    ("Expression of Ideas", "Rhetorical Synthesis"),
    ("Expression of Ideas", "Transitions"),
    ("Information and Ideas", "Central Ideas and Details"),
    ("Information and Ideas", "Command of Evidence"),
    ("Information and Ideas", "Inferences"),
    ("Standard English Conventions", "Boundaries"),
    ("Standard English Conventions", "Form, Structure, and Sense"),
}
# Known CB label defect: lowercase 't', 3 occurrences (MED, HARD, Results11).
SKILL_CANON = {"Cross-text Connections": "Cross-Text Connections"}
EXPECTED_CASING_DEFECTS = 3

# Labels sit alone on a line; the value wraps over the following lines.
STOP_LABELS = {"Question ID", "ID", "Assessment", "Test", "Domain", "Skill",
               "Difficulty", "Question Difficulty:", "Correct Answer:", "Rationale", "Answer"}


def norm(s: str) -> str:
    return " ".join(s.replace("\xa0", " ").split())


def field(lines: list[str], label: str, maxjoin: int = 3) -> str:
    for i, ln in enumerate(lines):
        if ln.strip() == label:
            parts = []
            for j in range(i + 1, min(i + 1 + maxjoin, len(lines))):
                s = lines[j].strip()
                if not s or s in STOP_LABELS or s.startswith("ID: "):
                    break
                parts.append(s)
            return norm(" ".join(parts))
    return ""


def parse(path: pathlib.Path) -> list[dict]:
    doc = pymupdf.open(path)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    rows = []
    for block in re.split(r"(?=Question ID [0-9a-f]{8})", text)[1:]:
        block = block.replace("\xa0", " ")
        lines = block.split("\n")
        diff = re.search(r"Question Difficulty:\s*(\w+)", block)
        ans = re.search(r"Correct Answer:\s*([A-D])", block)
        rows.append({
            "qid": re.match(r"Question ID ([0-9a-f]{8})", lines[0]).group(1),
            "domain": field(lines, "Domain"),
            "skill_raw": field(lines, "Skill"),
            "difficulty": diff.group(1) if diff else "",
            "correct": ans.group(1) if ans else "",
            "assessment": field(lines, "Assessment", 1),
            "test": field(lines, "Test", 2),
        })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    per_pdf, rows = {}, []
    for rel in PDFS:
        path = ROOT / rel
        if not path.exists():
            sys.exit(f"FATAL: missing source PDF {rel}")
        recs = parse(path)
        per_pdf[rel] = recs
        rows.extend(recs)
        if args.verbose:
            print(f"{len(recs):5d}  {rel}")

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}{'  — ' + detail if detail else ''}")
        if not ok:
            failures.append(name)

    ids = {p: {r["qid"] for r in recs} for p, recs in per_pdf.items()}
    union = set().union(*(ids[p] for p in DIFFICULTY_SPLITS))
    all_ids = {r["qid"] for r in rows}

    print("\nCB verbal label audit\n" + "-" * 60)
    check("1. row count", len(rows) == EXPECTED_ROWS, f"{len(rows)} (expected {EXPECTED_ROWS})")
    check("2. unique question IDs", len(all_ids) == EXPECTED_UNIQUE,
          f"{len(all_ids)} (expected {EXPECTED_UNIQUE})")
    overlaps = [(a, b, len(ids[a] & ids[b])) for a, b in itertools.combinations(DIFFICULTY_SPLITS, 2)]
    check("3. EASY/MED/HARD are disjoint", all(n == 0 for *_, n in overlaps),
          "; ".join(f"{a.split('- ')[-1]}∩{b.split('- ')[-1]}={n}" for a, b, n in overlaps if n))
    check("4. difficulty union covers every ID", all_ids == union,
          f"{len(all_ids - union)} outside the union")

    conflicts = {}
    for f in ("domain", "difficulty", "correct"):
        seen = collections.defaultdict(set)
        for r in rows:
            if r[f]:
                seen[r["qid"]].add(r[f])
        conflicts[f] = [q for q, v in seen.items() if len(v) > 1]
    skill_seen = collections.defaultdict(set)
    for r in rows:
        skill_seen[r["qid"]].add(SKILL_CANON.get(r["skill_raw"], r["skill_raw"]))
    conflicts["skill"] = [q for q, v in skill_seen.items() if len(v) > 1]
    for f in ("domain", "skill", "difficulty", "correct"):
        check(f"5.{f} — no cross-PDF conflicts", not conflicts[f],
              f"{len(conflicts[f])} conflicting: {conflicts[f][:5]}")

    check("6. no blank Domain or Skill",
          all(r["domain"] and r["skill_raw"] for r in rows),
          f"{sum(1 for r in rows if not r['domain'] or not r['skill_raw'])} blank")
    check("7. every ID has difficulty and a correct answer",
          all(any(r["difficulty"] for r in rows if r["qid"] == q) for q in union) and
          all(q in {r['qid'] for r in rows if r['correct']} for q in all_ids),
          "")

    pairs = {(r["domain"], SKILL_CANON.get(r["skill_raw"], r["skill_raw"])) for r in rows}
    check("8. exactly the 10 legal Domain x Skill pairs", pairs == LEGAL_PAIRS,
          f"unexpected={sorted(pairs - LEGAL_PAIRS)} missing={sorted(LEGAL_PAIRS - pairs)}")
    check("9. SAT Reading and Writing only",
          {(r["assessment"], r["test"]) for r in rows} == {("SAT", "Reading and Writing")},
          str(collections.Counter((r["assessment"], r["test"]) for r in rows)))

    defects = sum(1 for r in rows if r["skill_raw"] in SKILL_CANON)
    check(f"10. casing defects == {EXPECTED_CASING_DEFECTS}", defects == EXPECTED_CASING_DEFECTS,
          f"found {defects}")

    if args.verbose:
        print("\nDomain x Skill over the canonical pool:")
        canon = {r["qid"]: (r["domain"], SKILL_CANON.get(r["skill_raw"], r["skill_raw"])) for r in rows}
        for pair, n in sorted(collections.Counter(canon.values()).items()):
            print(f"  {n:5d}  {pair[0]} | {pair[1]}")

    print("-" * 60)
    if failures:
        print(f"{len(failures)} FAILED: {', '.join(failures)}")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
