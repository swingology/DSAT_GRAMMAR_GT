#!/usr/bin/env python
"""Deposit College Board's labels into the questions.cb_* columns.

Source: db_overlap_full.json (from match_bank_to_db.py). Writes exactly four
columns — cb_question_id, cb_domain_key, cb_skill_key, cb_difficulty — on every DB
row matched to a CB bank question, including duplicate copies of one question.
Touches nothing else: not annotation_jsonb, not versions, not updated_at.

DRY RUN BY DEFAULT. Pass --apply to write. One transaction; any failed safety
check rolls the whole thing back. Idempotent — re-running changes 0 rows — so it
is also the backfill step after a new CB export: re-run the matcher, then this.

Usage (from repo root):
  backend/.venv-jb/bin/python CB_QUESTION_BANK/09_2026/fill_cb_columns.py [--apply]
"""
import argparse
import asyncio
import collections
import json
import pathlib
import sys

import asyncpg

HERE = pathlib.Path(__file__).resolve().parent
DSN = "postgresql://dsat:dsat_dev@localhost:5437/dsat_dev"

# CB's 10 skills. Command of Evidence stays ONE key here: the textual/quantitative
# split is this project's refinement, not College Board's, so it does not belong in
# a column whose whole point is to record what CB said.
SKILL_KEY = {
    "Cross-Text Connections": "cross_text_connections",
    "Text Structure and Purpose": "text_structure_and_purpose",
    "Words in Context": "words_in_context",
    "Rhetorical Synthesis": "rhetorical_synthesis",
    "Transitions": "transitions",
    "Central Ideas and Details": "central_ideas_and_details",
    "Command of Evidence": "command_of_evidence",
    "Inferences": "inferences",
    "Boundaries": "boundaries",
    "Form, Structure, and Sense": "form_structure_and_sense",
}
DOMAIN_OF = {  # the 10 legal pairs from DOMAINS_SKILLS.md, as keys
    "cross_text_connections": "craft_and_structure",
    "text_structure_and_purpose": "craft_and_structure",
    "words_in_context": "craft_and_structure",
    "rhetorical_synthesis": "expression_of_ideas",
    "transitions": "expression_of_ideas",
    "central_ideas_and_details": "information_and_ideas",
    "command_of_evidence": "information_and_ideas",
    "inferences": "information_and_ideas",
    "boundaries": "conventions_grammar",
    "form_structure_and_sense": "conventions_grammar",
}
DIFFICULTIES = {"easy", "medium", "hard"}

UPDATE = """
update questions
   set cb_question_id = $2, cb_domain_key = $3, cb_skill_key = $4, cb_difficulty = $5
 where id = $1::uuid
   and (cb_question_id, cb_domain_key, cb_skill_key, cb_difficulty)
       is distinct from ($2, $3, $4, $5)
"""


def build_rows() -> list[tuple]:
    matches = json.load(open(HERE / "db_overlap_full.json"))["matches"]
    rows, owner = [], {}
    for m in matches:
        cb = m["cb"]
        skill = SKILL_KEY.get(cb["skill"])
        if skill is None:
            sys.exit(f"FATAL: unknown CB skill {cb['skill']!r} on {m['cb_question_id']}")
        domain = cb["question_family_key"]
        if DOMAIN_OF[skill] != domain:
            sys.exit(f"FATAL: illegal pair {domain}/{skill} on {m['cb_question_id']}")
        diff = cb["difficulty"].lower()
        if diff not in DIFFICULTIES:
            sys.exit(f"FATAL: bad difficulty {cb['difficulty']!r} on {m['cb_question_id']}")
        if owner.setdefault(m["db_id"], m["cb_question_id"]) != m["cb_question_id"]:
            sys.exit(f"FATAL: DB row {m['db_id']} matched to two different CB questions")
        rows.append((m["db_id"], m["cb_question_id"], domain, skill, diff))
    return rows


async def run(apply: bool) -> None:
    rows = build_rows()
    conn = await asyncpg.connect(DSN)
    try:
        async with conn.transaction():
            # never silently replace a CB ID someone already stored
            stored = {str(r["id"]): r["cb_question_id"] for r in await conn.fetch(
                "select id, cb_question_id from questions where cb_question_id is not null")}
            clash = [(d, stored[d], c) for d, c, *_ in rows if d in stored and stored[d] != c]
            if clash:
                sys.exit(f"FATAL: {len(clash)} rows already hold a different cb_question_id: {clash[:5]}")

            before = await conn.fetchval(
                "select md5(string_agg(id::text || coalesce(current_question_text,'') || "
                "coalesce(latest_annotation_id::text,'') || updated_at::text, '' order by id)) from questions")
            changed = 0
            for r in rows:
                changed += int((await conn.execute(UPDATE, *r)).split()[-1])
            after = await conn.fetchval(
                "select md5(string_agg(id::text || coalesce(current_question_text,'') || "
                "coalesce(latest_annotation_id::text,'') || updated_at::text, '' order by id)) from questions")
            if before != after:
                sys.exit("FATAL: a non-cb column changed — rolled back")

            filled = await conn.fetchrow(
                "select count(*) n, count(distinct cb_question_id) q from questions "
                "where cb_question_id is not null")
            print(f"rows to label {len(rows)} | distinct CB questions "
                  f"{len({r[1] for r in rows})} | rows changed this run {changed}")
            print(f"after: {filled['n']} rows carry CB labels, {filled['q']} distinct CB questions")
            print("by cb_skill_key:", dict(collections.Counter(r[3] for r in rows).most_common()))
            if not apply:
                raise _DryRun
    except _DryRun:
        print("\nDRY RUN — rolled back, nothing written. Re-run with --apply.")
    finally:
        await conn.close()
    if apply:
        print("\nAPPLIED.")


class _DryRun(Exception):
    pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    asyncio.run(run(ap.parse_args().apply))
