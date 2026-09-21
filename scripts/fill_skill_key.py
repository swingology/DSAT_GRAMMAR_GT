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

The resolution logic lives in backend/app/pipeline/skill_key.py, which the ingest,
generate and reannotate pipelines call too; this script is its whole-table driver.
Rows whose skill_key_source is 'manual' are never touched.

Usage (run from backend/, like the other DB scripts, so Settings reads backend/.env):
  cd backend && .venv-jb/bin/python ../scripts/fill_skill_key.py [--apply]
"""
import argparse
import asyncio
import collections
import pathlib
import sys

import asyncpg

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))
from app.models.ontology import SKILL_FAMILY_BY_QUESTION_FAMILY, SKILL_FAMILY_KEYS  # noqa: E402
from app.pipeline.skill_key import resolve_skill_key  # noqa: E402

DSN = "postgresql://dsat:dsat_dev@localhost:5437/dsat_dev"

SELECT = """
select q.id::text, q.cb_skill_key, q.cb_domain_key, q.stem_type_key,
       q.current_question_text stem, q.skill_key, q.skill_key_source,
       a.annotation_jsonb->>'skill_family_key'  sf,
       a.annotation_jsonb->>'grammar_role_key'  gr,
       a.annotation_jsonb->>'grammar_focus_key' gf,
       a.annotation_jsonb->>'stem_type_key'     ann_stem
from questions q left join question_annotations a on a.id = q.latest_annotation_id
"""
CHECKSUM = """
select md5(string_agg(q.id::text || coalesce(q.current_question_text,'') ||
       coalesce(q.cb_skill_key,'') || q.updated_at::text ||
       coalesce(md5(a.annotation_jsonb::text),''), '' order by q.id))
from questions q left join question_annotations a on a.id = q.latest_annotation_id
"""


async def run(apply: bool) -> None:
    conn = await asyncpg.connect(DSN)
    try:
        async with conn.transaction():
            rows = await conn.fetch(SELECT)
            before = await conn.fetchval(CHECKSUM)
            plan, unresolved = [], []
            for r in rows:
                if r["skill_key_source"] == "manual":
                    continue
                skill, src = resolve_skill_key(
                    cb_skill_key=r["cb_skill_key"], stem_text=r["stem"],
                    stem_type_key=r["stem_type_key"],
                    annotation={"skill_family_key": r["sf"], "grammar_role_key": r["gr"],
                                "grammar_focus_key": r["gf"], "stem_type_key": r["ann_stem"]})
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
                    "and skill_key_source is distinct from 'manual' "
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
