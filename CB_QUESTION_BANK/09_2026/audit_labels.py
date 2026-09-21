#!/usr/bin/env python
"""TASK-04 — re-runnable label-integrity audit for the CB verbal PDFs.

Re-parses every verbal PDF found under CB_QUESTION_BANK/ with logic independent
of extract_cb_bank.py, then checks two different kinds of thing:

  STRUCTURAL INVARIANTS — must hold for any CB export, at any corpus size.
  A violation is a hard failure (exit 1).

  SNAPSHOT COUNTS — totals as of the last accepted corpus, kept in
  bank_manifest.json. Growth is expected: new PDFs and rising counts are
  REPORTED, not failed. Re-run with --accept to record the new snapshot.

That split is what makes this safe to re-run as College Board publishes more
questions. Pinning the totals would turn every future export into a red build.

Usage:
  uv run --with pymupdf python audit_labels.py [-v]
  uv run --with pymupdf python audit_labels.py --accept   # after adding PDFs
"""
import argparse
import collections
import json
import pathlib
import re
import sys

import pymupdf

ROOT = pathlib.Path(__file__).resolve().parent.parent  # CB_QUESTION_BANK/
MANIFEST = pathlib.Path(__file__).resolve().parent / "bank_manifest.json"
# Verbal only. NEW_QUESTION_SETS/VERBAL duplicates 09_2026 byte-for-byte, and
# macOS AppleDouble sidecars (._name) are not real PDFs.
EXCLUDE_DIRS = {"Math", "NEW_QUESTION_SETS"}


def discover() -> list[str]:
    """Every verbal source PDF under CB_QUESTION_BANK/, newest exports included."""
    found = []
    for path in sorted(ROOT.rglob("*.pdf")):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in rel.parts) or path.name.startswith("._"):
            continue
        found.append(str(rel))
    return found

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
    ap.add_argument("--accept", action="store_true",
                    help="record the current corpus as the new snapshot in bank_manifest.json")
    args = ap.parse_args()

    pdfs = discover()
    if not pdfs:
        sys.exit("FATAL: no verbal PDFs found under CB_QUESTION_BANK/")

    per_pdf, rows = {}, []
    for rel in pdfs:
        path = ROOT / rel
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
    all_ids = {r["qid"] for r in rows}
    prev = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

    print("\nCB verbal label audit — STRUCTURAL INVARIANTS\n" + "-" * 60)
    check("1. no duplicate IDs within a single PDF",
          all(len(ids[p]) == len(per_pdf[p]) for p in pdfs),
          "; ".join(f"{p}: {len(per_pdf[p]) - len(ids[p])} dup" for p in pdfs
                    if len(ids[p]) != len(per_pdf[p])))
    # Every ID must be resolvable to a difficulty and an answer by SOME pdf in the
    # corpus. Which PDF supplies it is not fixed, so no filename is hardcoded.
    have_diff = {r["qid"] for r in rows if r["difficulty"]}
    have_ans = {r["qid"] for r in rows if r["correct"]}
    check("2. every ID resolves to a difficulty somewhere", all_ids == have_diff,
          f"{len(all_ids - have_diff)} without difficulty in any PDF")
    check("3. every ID resolves to a correct answer somewhere", all_ids == have_ans,
          f"{len(all_ids - have_ans)} without an answer in any PDF")

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
        check(f"4.{f} — no cross-PDF conflicts", not conflicts[f],
              f"{len(conflicts[f])} conflicting: {conflicts[f][:5]}")

    check("5. no blank Domain or Skill",
          all(r["domain"] and r["skill_raw"] for r in rows),
          f"{sum(1 for r in rows if not r['domain'] or not r['skill_raw'])} blank")

    pairs = {(r["domain"], SKILL_CANON.get(r["skill_raw"], r["skill_raw"])) for r in rows}
    # Subset, not equality: a partial export may legitimately lack some pairs.
    # An UNKNOWN pair is the real failure — it means CB changed the taxonomy and
    # DOMAINS_SKILLS.md plus the ontology need revisiting before ingest.
    check("6. no Domain x Skill pair outside the 10 known", not (pairs - LEGAL_PAIRS),
          f"unexpected={sorted(pairs - LEGAL_PAIRS)}")
    if pairs != LEGAL_PAIRS:
        print(f"  [note] pairs absent from this corpus: {sorted(LEGAL_PAIRS - pairs)}")
    check("7. SAT Reading and Writing only",
          {(r["assessment"], r["test"]) for r in rows} == {("SAT", "Reading and Writing")},
          str(collections.Counter((r["assessment"], r["test"]) for r in rows)))

    print("\nSNAPSHOT — growth is expected, these never fail the run\n" + "-" * 60)
    defects = sum(1 for r in rows if r["skill_raw"] in SKILL_CANON)
    cur = {"pdfs": {p: len(per_pdf[p]) for p in pdfs}, "rows": len(rows),
           "unique_ids": len(all_ids), "casing_defects": defects}
    if not prev:
        print("  no manifest yet — run with --accept to record this corpus as the baseline")
    else:
        for label, key in (("rows", "rows"), ("unique IDs", "unique_ids"),
                           ("casing defects", "casing_defects")):
            was, now = prev.get(key), cur[key]
            mark = "same" if was == now else ("+%d" % (now - was) if now > was else "%d" % (now - was))
            print(f"  {label}: {was} -> {now} ({mark})")
        added = sorted(set(cur["pdfs"]) - set(prev.get("pdfs", {})))
        removed = sorted(set(prev.get("pdfs", {})) - set(cur["pdfs"]))
        changed = [p for p in cur["pdfs"] if p in prev.get("pdfs", {})
                   and prev["pdfs"][p] != cur["pdfs"][p]]
        for p in added:
            print(f"  NEW    {p} ({cur['pdfs'][p]} questions)")
        for p in removed:
            print(f"  GONE   {p} (was {prev['pdfs'][p]})")
        for p in changed:
            print(f"  CHANGED {p}: {prev['pdfs'][p]} -> {cur['pdfs'][p]}")
        if not (added or removed or changed):
            print("  corpus unchanged since the recorded snapshot")

    if args.accept:
        MANIFEST.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n")
        print(f"\n  recorded snapshot -> {MANIFEST.name}")

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
