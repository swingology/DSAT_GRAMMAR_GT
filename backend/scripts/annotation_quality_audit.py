"""Annotation quality audit — fails when active questions have incomplete taxonomy.

Run after ingest / re-annotation and before generated-question release. Reports:
  - missing canonical fields (question_family, difficulty, grammar trap, reading focus)
  - per-row completeness via validate_annotation_completeness
  - recoverable-from-nested vs genuinely-missing split (so you know repair vs reannotate)

Usage (inside backend container):
    python -m scripts.annotation_quality_audit            # report, exit 1 if blocking gaps
    python -m scripts.annotation_quality_audit --soft     # report only, always exit 0
"""
from __future__ import annotations

import argparse
import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import select

from app.database import async_session
from app.models.db import Question, QuestionAnnotation
from app.parsers.json_parser import canonicalize_annotation
from app.pipeline.validator import validate_annotation_completeness


async def run(soft: bool) -> int:
    async with async_session() as db:
        stmt = (
            select(Question, QuestionAnnotation)
            .join(QuestionAnnotation, QuestionAnnotation.id == Question.latest_annotation_id)
            .where(Question.practice_status == "active")
        )
        rows = (await db.execute(stmt)).all()

        total = len(rows)
        missing_qfamily = 0
        missing_difficulty = 0
        grammar_missing_trap = 0
        reading_missing_focus = 0
        recoverable_from_nested = 0
        rows_with_blocking = 0
        blocking_examples: list[str] = []

        for question, ann in rows:
            a = ann.annotation_jsonb or {}
            family = a.get("question_family_key")

            if not family:
                missing_qfamily += 1
                # Would a canonicalize repair fix it?
                if canonicalize_annotation(a).get("question_family_key"):
                    recoverable_from_nested += 1
            if not a.get("difficulty_overall"):
                missing_difficulty += 1
            if family in ("conventions_grammar", "expression_of_ideas") and not a.get("syntactic_trap_key"):
                grammar_missing_trap += 1
            if family in ("information_and_ideas", "craft_and_structure") and not a.get("reading_focus_key"):
                reading_missing_focus += 1

            blocking = [e for e in validate_annotation_completeness(a) if e["severity"] == "blocking"]
            if blocking:
                rows_with_blocking += 1
                if len(blocking_examples) < 10:
                    label = f"{question.source_exam_code}/Q{question.source_question_number}"
                    fields = ", ".join(e["field"] for e in blocking)
                    blocking_examples.append(f"  {label}: {fields}")

        print("=" * 60)
        print("ANNOTATION QUALITY AUDIT (active questions)")
        print("=" * 60)
        print(f"total active rows          : {total}")
        print(f"missing question_family    : {missing_qfamily}  (recoverable from nested: {recoverable_from_nested})")
        print(f"missing difficulty_overall : {missing_difficulty}")
        print(f"grammar missing trap       : {grammar_missing_trap}")
        print(f"reading missing focus      : {reading_missing_focus}")
        print(f"rows failing completeness  : {rows_with_blocking}")
        if blocking_examples:
            print("\nfirst blocking rows:")
            print("\n".join(blocking_examples))
        print("=" * 60)

        if recoverable_from_nested:
            print(f"HINT: {recoverable_from_nested} rows are repairable with "
                  f"`python -m scripts.repair_annotation_canonical` (no LLM calls).")

        gate_fail = rows_with_blocking > 0
        if gate_fail and not soft:
            print("RESULT: FAIL — blocking completeness gaps present.")
            return 1
        print("RESULT: PASS" if not gate_fail else "RESULT: PASS (soft mode)")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--soft", action="store_true", help="report only, always exit 0")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.soft)))
