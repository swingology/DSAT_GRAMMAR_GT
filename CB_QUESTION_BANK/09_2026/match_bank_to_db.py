#!/usr/bin/env python
"""TASK-07a/07b — match the CB bank against the live DB, then crosstab labels.

READ-ONLY. Never writes to the database.

Matching is two independent signals, both of which must agree:
  text     — normalized passage+stem, compared as ONE string (prose only, from the master)
  choices  — the four answer-choice texts, order-independent

Passage and stem are deliberately concatenated before comparison. The two
sources cut the boundary differently — CB keeps the "The student wants to..."
goal sentence in the stem, the DB stores it in the passage — so scoring them
separately rejects true matches. Requiring the choices to agree is what still
separates "same question" from "sibling question on a shared passage".

Outputs (next to this script):
  db_overlap_full.json   every match with its scores, plus the unmatched IDs
  db_overlap_full.md     summary + CB-skill x DB-annotation calibration crosstab

Usage (from repo root):
  backend/.venv-jb/bin/python CB_QUESTION_BANK/09_2026/match_bank_to_db.py
"""
import argparse
import asyncio
import collections
import difflib
import json
import pathlib
import re

import asyncpg

HERE = pathlib.Path(__file__).resolve().parent
DSN = "postgresql://dsat:dsat_dev@localhost:5437/dsat_dev"
BANK = HERE.parent / "cb_verbal_master.json"  # layout-based master; see build_master.py
TEXT_MIN, CHOICE_MIN = 0.90, 0.90
# Second acceptance path: identical choices carry the match even when the text
# diverges (CB inlines graph axis numbers and table cells into the passage; the DB
# stores those separately). Only trusted when the choices are long enough to be
# distinctive — four one-word options recur across unrelated questions.
IDENTICAL_CHOICES, LOOSE_TEXT_MIN, DISTINCTIVE_CHOICE_CHARS = 0.99, 0.75, 60

SQL = """
select q.id::text, q.cb_question_id, q.source_test_name, q.source_release_year,
       q.source_module_code, q.source_question_number, q.is_admin_edited,
       q.practice_status::text, q.stem_type_key,
       q.current_question_text qt, q.current_passage_text pt,
       q.current_paired_passage_text ppt, v.choices_jsonb::text choices,
       a.annotation_jsonb->>'question_family_key' qf,
       a.annotation_jsonb->>'skill_family_key'    sf,
       a.annotation_jsonb->>'grammar_role_key'    gr,
       a.annotation_jsonb->>'grammar_focus_key'   gf
from questions q
left join question_versions v    on v.id = q.latest_version_id
left join question_annotations a on a.id = q.latest_annotation_id
where q.content_origin = 'official'
"""


def norm(s: str | None) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split())


def shingles(text: str, n: int = 4) -> set[str]:
    w = text.split()
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


def ratio(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


async def load_db() -> list[dict]:
    conn = await asyncpg.connect(DSN)
    try:
        rows = [dict(r) for r in await conn.fetch(SQL)]
    finally:
        await conn.close()
    for r in rows:
        r["_pass"] = norm(" ".join(filter(None, [r["pt"], r["ppt"]])))
        r["_stem"] = norm(r["qt"])
        ch = json.loads(r["choices"]) if r["choices"] else []
        r["_choices"] = " | ".join(sorted(norm(c.get("text")) for c in ch))
    return rows


def from_master(q: dict) -> dict:
    """Master record -> the flat shape the matcher compares.

    Prose only: the database stores neither graph axis numbers nor table cells in the
    passage, so leaving them out brings the two texts closer than the old flat file did.
    """
    s = q["stimulus"]
    prose = list(s["paragraphs"]) + s.get("notes", [])
    for t in s.get("texts", []):
        prose += t["paragraphs"]
    return {"question_id": q["question_id"], "passage": " ".join(prose), "stem": q["question"],
            "choices": q["choices"], "domain": q["domain"], "skill": q["skill"],
            "difficulty": q["difficulty"], "correct_answer": q["correct_answer"],
            "question_family_key": q["domain_key"], "skill_family_key": q["skill_key"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default=str(BANK))
    args = ap.parse_args()

    bank = [from_master(q) for q in json.load(open(args.bank))["questions"]]
    db = asyncio.run(load_db())

    # Block on shared 4-word shingles over passage+stem so we never do the full
    # 1,845 x 1,514 cross product with SequenceMatcher.
    index = collections.defaultdict(set)
    for i, r in enumerate(db):
        for sh in shingles(r["_pass"] + " " + r["_stem"]):
            index[sh].add(i)

    matches, near, unmatched = [], [], []
    for q in bank:
        p, s = norm(q["passage"]), norm(q["stem"])
        c = " | ".join(sorted(norm(v) for v in q["choices"].values()))
        votes = collections.Counter()
        for sh in shingles(p + " " + s):
            for i in index.get(sh, ()):
                votes[i] += 1
        # One-to-many on purpose: the DB holds the same question ingested from
        # several releases (2024 and 2025 copies of one practice test), so a bank
        # question may correspond to 2-4 rows and every copy must be labelled.
        scored = []
        for i, _ in votes.most_common(8):
            r = db[i]
            scored.append((r, ratio(p + " " + s, r["_pass"] + " " + r["_stem"]),
                           ratio(c, r["_choices"])))
        if not scored:
            unmatched.append(q["question_id"])
            continue
        distinctive = len(c) >= DISTINCTIVE_CHOICE_CHARS
        accepted = [x for x in scored if
                    (x[1] >= TEXT_MIN and x[2] >= CHOICE_MIN) or
                    (distinctive and x[2] >= IDENTICAL_CHOICES and x[1] >= LOOSE_TEXT_MIN) or
                    # The DB row lost its question stem: the passage sits in question_text and
                    # passage_text is NULL. Compare against the CB passage alone.
                    (not x[0]["pt"] and x[2] >= CHOICE_MIN and ratio(p, x[0]["_stem"]) >= 0.97)]
        pool = accepted or [max(scored, key=lambda x: min(x[1], x[2]))]
        for r, ts, cs in pool:
          rec = {
            "cb_question_id": q["question_id"], "db_id": r["id"],
            "scores": {"text": round(ts, 4), "choices": round(cs, 4)},
            "cb": {"domain": q["domain"], "skill": q["skill"], "difficulty": q["difficulty"],
                   "question_family_key": q["question_family_key"],
                   "skill_family_key": q["skill_family_key"], "answer": q["correct_answer"]},
            "db": {k: r[k] for k in ("cb_question_id", "source_test_name", "source_release_year",
                                     "source_module_code", "source_question_number",
                                     "is_admin_edited", "practice_status", "stem_type_key",
                                     "qf", "sf", "gr", "gf")},
          }
          if accepted:
            matches.append(rec)
          elif ts >= LOOSE_TEXT_MIN:    # close but unproven -> human review, never auto-filled
            near.append(rec)
          else:
            unmatched.append(q["question_id"])

    # A DB row claimed by two DIFFERENT bank IDs is a genuine error (the reverse,
    # one bank ID on several rows, is the expected duplicate-release case).
    claimed = collections.Counter(m["db_id"] for m in matches)
    collisions = {k: n for k, n in claimed.items() if n > 1}

    bank_matched = len({m["cb_question_id"] for m in matches})
    out = {"bank_total": len(bank), "db_official_total": len(db),
           "bank_questions_matched": bank_matched, "db_rows_matched": len(matches),
           "needs_review": len(near),
           "unmatched": len(unmatched), "db_id_collisions": collisions,
           "thresholds": {"text": TEXT_MIN, "choices": CHOICE_MIN,
                          "identical_choices": IDENTICAL_CHOICES, "loose_text": LOOSE_TEXT_MIN,
                          "distinctive_choice_chars": DISTINCTIVE_CHOICE_CHARS},
           "matches": matches, "needs_review_rows": near, "unmatched_ids": sorted(unmatched)}
    (HERE / "db_overlap_full.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))

    print(f"bank {len(bank)} | db official {len(db)}")
    print(f"bank questions matched {bank_matched} -> {len(matches)} db rows "
          f"| needs review {len(near)} | unmatched (new) {len(unmatched)}")
    print(f"db-id collisions: {len(collisions)}")


if __name__ == "__main__":
    main()
