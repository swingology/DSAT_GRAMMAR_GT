#!/usr/bin/env python
"""Fill questions.skill_key — the universal College Board skill — for every question.

Writes exactly two columns, skill_key and skill_key_source. Never touches
annotation_jsonb, versions, or any other column; a checksum guard aborts the
transaction if anything else moves.

Source, in order of trust:
  cb          questions.cb_skill_key is set -> CB's own label. Command of Evidence
              is split textual / quantitative by the stem.
  annotation  no CB label, but the annotation already carries a legal reading
              skill_family_key -> reuse it.
  map         neither -> vocabulary/mappings/cb_skill_map.json, deterministic rules
              only, in order: stem_type_key, role/focus, role.
Anything still unresolved stays NULL and is listed — never guessed.

DRY RUN BY DEFAULT. Pass --apply to write. Idempotent.

Usage (from repo root):
  backend/.venv-jb/bin/python scripts/fill_skill_key.py [--apply]
"""
import argparse
import asyncio
import collections
import importlib.util
import json
import pathlib
import re
import sys

import asyncpg

REPO = pathlib.Path(__file__).resolve().parent.parent
# Load ontology.py by path: it is a pure constants file, and importing it as
# app.models.ontology drags in app.models -> app.database -> Settings(), which
# rejects unrelated variables in the repo-root .env.
_spec = importlib.util.spec_from_file_location(
    "ontology", REPO / "backend" / "app" / "models" / "ontology.py")
_ont = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ont)
READING_SKILL_FAMILY_KEYS = _ont.READING_SKILL_FAMILY_KEYS
SKILL_FAMILY_BY_QUESTION_FAMILY = _ont.SKILL_FAMILY_BY_QUESTION_FAMILY
SKILL_FAMILY_KEYS = _ont.SKILL_FAMILY_KEYS

DSN = "postgresql://dsat:dsat_dev@localhost:5437/dsat_dev"
MAP = REPO / "vocabulary" / "mappings" / "cb_skill_map.json"
# Same derivation extract_cb_bank.py uses; agreed with existing annotations on
# 174/174 Command of Evidence rows and leaked on 0/144 textual stems.
QUANT_STEM = re.compile(r"\b(graph|table|data in the)\b", re.I)

SELECT = """
select q.id::text, q.cb_skill_key, q.cb_domain_key, q.stem_type_key,
       q.current_question_text stem, q.skill_key, q.skill_key_source,
       a.annotation_jsonb->>'skill_family_key'  sf,
       a.annotation_jsonb->>'grammar_role_key'  gr,
       a.annotation_jsonb->>'grammar_focus_key' gf
from questions q left join question_annotations a on a.id = q.latest_annotation_id
"""
CHECKSUM = """
select md5(string_agg(q.id::text || coalesce(q.current_question_text,'') ||
       coalesce(q.cb_skill_key,'') || q.updated_at::text ||
       coalesce(md5(a.annotation_jsonb::text),''), '' order by q.id))
from questions q left join question_annotations a on a.id = q.latest_annotation_id
"""


def load_rules() -> tuple[dict, dict, dict]:
    m = json.load(open(MAP))
    pick = lambda rs: {r["key"]: r["skill_key"] for r in rs if r["status"] == "deterministic"}
    return pick(m["by_stem_type_key"]), pick(m["by_role_and_focus"]), pick(m["by_role"])


def resolve(r, by_stem, by_focus, by_role) -> tuple[str | None, str | None]:
    if r["cb_skill_key"]:
        k = r["cb_skill_key"]
        if k == "command_of_evidence":
            k += "_quantitative" if QUANT_STEM.search(r["stem"] or "") else "_textual"
        return k, "cb"
    if r["sf"] in READING_SKILL_FAMILY_KEYS:
        return r["sf"], "annotation"
    for table, key in ((by_stem, r["stem_type_key"]),
                       (by_focus, f"{r['gr']}/{r['gf']}"),
                       (by_role, r["gr"])):
        if key in table:
            return table[key], "map"
    return None, None


async def run(apply: bool) -> None:
    by_stem, by_focus, by_role = load_rules()
    conn = await asyncpg.connect(DSN)
    try:
        async with conn.transaction():
            rows = await conn.fetch(SELECT)
            before = await conn.fetchval(CHECKSUM)
            plan, unresolved = [], []
            for r in rows:
                skill, src = resolve(r, by_stem, by_focus, by_role)
                if skill is None:
                    unresolved.append(r)
                    continue
                if skill not in SKILL_FAMILY_KEYS:
                    sys.exit(f"FATAL: {skill!r} is not in SKILL_FAMILY_KEYS (row {r['id']})")
                if r["cb_domain_key"] and skill not in SKILL_FAMILY_BY_QUESTION_FAMILY[r["cb_domain_key"]]:
                    sys.exit(f"FATAL: illegal pair {r['cb_domain_key']}/{skill} (row {r['id']})")
                plan.append((r["id"], skill, src))

            changed = 0
            for qid, skill, src in plan:
                changed += int((await conn.execute(
                    "update questions set skill_key=$2, skill_key_source=$3 where id=$1::uuid "
                    "and (skill_key, skill_key_source) is distinct from ($2, $3)",
                    qid, skill, src)).split()[-1])
            if await conn.fetchval(CHECKSUM) != before:
                sys.exit("FATAL: something other than skill_key changed — rolled back")

            print(f"questions {len(rows)} | resolved {len(plan)} | unresolved {len(unresolved)} "
                  f"| rows changed this run {changed}")
            print("by source:", dict(collections.Counter(s for *_, s in plan)))
            print("by skill :", dict(collections.Counter(k for _, k, _ in plan).most_common()))
            if unresolved:
                why = collections.Counter(
                    (u["stem_type_key"], u["gr"], u["gf"]) for u in unresolved)
                print("unresolved, by (stem_type_key, role, focus):")
                for k, n in why.most_common(12):
                    print(f"   {n:3d}  {k}")
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
