#!/usr/bin/env python
"""Report where existing annotations disagree with College Board's own labels.

READ-ONLY. Compares the cb_* columns (College Board) with annotation_jsonb (LLM). Nothing
is corrected: fixing an annotation is a rewrite and needs the owner's sign-off. Writes
analysis/cb_annotation_conflicts.md and .json (every conflicting row, for whoever reviews).

Usage: cd backend && .venv-jb/bin/python ../scripts/cb_conflict_report.py
"""
import asyncio
import collections
import json
import pathlib

import asyncpg

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "analysis"
DSN = "postgresql://dsat:dsat_dev@localhost:5437/dsat_dev"
READING = {"craft_and_structure", "information_and_ideas"}
CB_DIFF = {"easy": "low", "medium": "medium", "hard": "high"}

SQL = """
select q.id::text, q.practice_status::text status, q.cb_question_id, q.cb_domain_key, q.cb_skill_key,
       q.cb_difficulty, q.skill_key, q.is_admin_edited,
       a.annotation_jsonb->>'question_family_key' qf, a.annotation_jsonb->>'skill_family_key' sf,
       a.annotation_jsonb->>'grammar_role_key' gr, a.annotation_jsonb->>'grammar_focus_key' gf,
       a.annotation_jsonb->>'difficulty_overall' diff
from questions q join question_annotations a on a.id = q.latest_annotation_id
where q.cb_question_id is not null
"""


def coe(k):
    return "command_of_evidence" if k and k.startswith("command_of_evidence") else k


async def main() -> None:
    conn = await asyncpg.connect(DSN)
    rows = [dict(r) for r in await conn.fetch(SQL)]
    await conn.close()

    kinds = collections.defaultdict(list)
    for r in rows:
        if r["qf"] and r["qf"] != r["cb_domain_key"]:
            kinds["domain: question_family_key differs from College Board"].append(r)
        if not r["qf"]:
            kinds["domain: question_family_key missing"].append(r)
        if r["cb_domain_key"] in READING:
            if r["sf"] and coe(r["sf"]) != r["cb_skill_key"]:
                kinds["reading skill: skill_family_key differs from College Board"].append(r)
            if not r["sf"]:
                kinds["reading skill: skill_family_key missing"].append(r)
            if r["gr"]:
                kinds["routing: a reading question carries a grammar_role_key (served as grammar)"].append(r)
        elif r["sf"]:
            kinds["routing: a grammar question carries skill_family_key (served as reading)"].append(r)
        if r["diff"] and CB_DIFF[r["cb_difficulty"]] != r["diff"]:
            kinds["difficulty: difficulty_overall differs from College Board"].append(r)

    OUT.mkdir(exist_ok=True)
    (OUT / "cb_annotation_conflicts.json").write_text(json.dumps(
        {k: [{f: r[f] for f in ("id", "status", "cb_question_id", "cb_domain_key", "cb_skill_key",
                                "cb_difficulty", "qf", "sf", "gr", "gf", "diff", "is_admin_edited")}
             for r in v] for k, v in kinds.items()}, indent=1) + "\n")

    n = len(rows)
    md = [f"# Annotations vs College Board — conflict report\n",
          f"Read-only. {n} official questions carry College Board labels; each is compared with its "
          "latest annotation. **Nothing here has been changed.** Correcting an annotation is a "
          "rewrite, so it is the owner's decision. Row-level detail: `cb_annotation_conflicts.json`.\n",
          "| Conflict | Rows | Active | Hand-edited |", "|---|---|---|---|"]
    for k, v in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        md.append(f"| {k} | {len(v)} | {sum(r['status'] == 'active' for r in v)} | "
                  f"{sum(bool(r['is_admin_edited']) for r in v)} |")
    for k in ("domain: question_family_key differs from College Board",
              "reading skill: skill_family_key differs from College Board",
              "difficulty: difficulty_overall differs from College Board"):
        f = {"domain": ("qf", "cb_domain_key"), "reading": ("sf", "cb_skill_key"),
             "difficulty": ("diff", "cb_difficulty")}[k.split(" ")[0].rstrip(":")]
        md += [f"\n## {k}\n", "| annotation says | College Board says | rows |", "|---|---|---|"]
        for (a, b), c in collections.Counter((r[f[0]], r[f[1]]) for r in kinds[k]).most_common(12):
            md.append(f"| `{a}` | `{b}` | {c} |")
    md.append("\n## What acting on this would mean\n\n"
              "- **Routing rows are live bugs**: those questions are served in the wrong practice pool "
              "today, because the app routes on which annotation key is present.\n"
              "- `questions.skill_key` already holds College Board's skill for every row here, so a "
              "reader that uses `skill_key` is unaffected by the annotation errors.\n"
              "- Overwriting `difficulty_overall` would change adaptive module selection and the "
              "diagnostic pool; `cb_difficulty` is available without touching it.\n")
    (OUT / "cb_annotation_conflicts.md").write_text("\n".join(md) + "\n")
    print(f"{n} CB-labelled rows")
    for k, v in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(v):5d}  {k}")


if __name__ == "__main__":
    asyncio.run(main())
