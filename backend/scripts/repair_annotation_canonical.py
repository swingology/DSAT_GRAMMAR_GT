"""Deterministic repair pass: canonicalize existing annotation_jsonb rows.

Runs canonicalize_annotation over the latest annotation of every active question
and writes back promoted/repaired top-level fields. No LLM calls — this only
moves valid values that already exist in nested sections up to the top level.

Usage (inside backend container):
    python -m scripts.repair_annotation_canonical          # apply
    python -m scripts.repair_annotation_canonical --dry-run # report only
"""
from __future__ import annotations

import argparse
import asyncio
import sys

sys.path.insert(0, ".")  # make app.* importable when run from backend/

from sqlalchemy import select

from app.database import async_session
from app.models.db import Question, QuestionAnnotation
from app.parsers.json_parser import canonicalize_annotation
from app.prompts.annotate_prompt import enforce_nullability

CANONICAL_FIELDS = [
    "question_family_key", "skill_family_key", "reading_focus_key",
    "grammar_role_key", "grammar_focus_key", "syntactic_trap_key",
    "reasoning_trap_key", "difficulty_overall", "difficulty_reading",
    "difficulty_grammar", "stem_type_key", "stimulus_mode_key",
    "answer_mechanism_key", "evidence_scope_key", "evidence_location_key",
    "solver_pattern_key",
]


async def main(dry_run: bool) -> None:
    async with async_session() as db:
        stmt = (
            select(Question, QuestionAnnotation)
            .join(QuestionAnnotation, QuestionAnnotation.id == Question.latest_annotation_id)
            .where(Question.practice_status == "active")
        )
        rows = (await db.execute(stmt)).all()

        scanned = 0
        changed = 0
        conflicts = 0
        field_repairs: dict[str, int] = {}

        for question, ann in rows:
            scanned += 1
            original = ann.annotation_jsonb or {}
            # Mirror the live ingest pipeline: canonicalize, then enforce nullability
            # so we never promote a cross-domain value the pipeline would strip.
            canonical = enforce_nullability(canonicalize_annotation(original), "unknown")

            # Determine which top-level canonical fields actually changed.
            diffs = {
                f: (original.get(f), canonical.get(f))
                for f in CANONICAL_FIELDS
                if original.get(f) != canonical.get(f)
            }
            quality = canonical.get("_annotation_quality") or {}
            if quality.get("conflicts"):
                conflicts += 1

            if not diffs and "_annotation_quality" not in canonical:
                continue

            changed += 1
            for f in diffs:
                field_repairs[f] = field_repairs.get(f, 0) + 1

            if not dry_run:
                # SQLAlchemy needs a new dict object to detect the JSON change.
                ann.annotation_jsonb = canonical

        if not dry_run:
            await db.commit()

        print(f"scanned active rows : {scanned}")
        print(f"rows changed        : {changed}")
        print(f"rows with conflicts : {conflicts}")
        print("field repairs:")
        for f, n in sorted(field_repairs.items(), key=lambda kv: -kv[1]):
            print(f"  {f}: {n}")
        print("DRY RUN — no writes" if dry_run else "COMMITTED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))
