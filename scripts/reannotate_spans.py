#!/usr/bin/env python3
"""Bulk span-annotate grammar questions that are missing passage_spans.

Usage (must run from backend/ directory):
  cd backend
  uv run python ../scripts/reannotate_spans.py [options]

Options:
  --status        missing|all              Filter by annotation state (default: missing)
  --content-origin official|generated|all  Filter by content origin (default: official)
  --question-id   UUID                     Process a single question only
  --limit         INT                      Max questions to process (default: unlimited)
  --dry-run                                Validate only — do not write to DB
  --concurrency   INT                      Parallel worker count (default: 5)
  --priority      active|all               Process active questions first (default: active)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from uuid import UUID

from sqlalchemy import case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# When run as `cd backend && uv run python ../scripts/reannotate_spans.py`,
# Python's sys.path includes backend/ so app.* imports resolve correctly.
from app.models.db import Question, QuestionAnnotation
from app.services.span_annotator import annotate_spans

# ---------------------------------------------------------------------------
# DB connection — standalone DSN so the script works without the full app
# config/env setup. Matches the dev compose stack.
# ---------------------------------------------------------------------------
DB_DSN = "postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev"


def build_query(
    status: str,
    content_origin: str,
    priority: str,
    limit: int | None,
    question_id: UUID | None,
):
    """Return a SQLAlchemy select statement for questions to annotate."""
    stmt = (
        select(Question)
        .join(QuestionAnnotation, Question.latest_annotation_id == QuestionAnnotation.id)
    )

    # Single-question mode
    if question_id is not None:
        stmt = stmt.where(Question.id == question_id)
        return stmt

    # Grammar family filter: match explicit family OR presence of grammar_focus_key
    # (older annotations may have null/wrong question_family_key but a valid gfk)
    stmt = stmt.where(
        or_(
            QuestionAnnotation.annotation_jsonb["question_family_key"].astext
            == "conventions_grammar",
            QuestionAnnotation.annotation_jsonb["grammar_focus_key"].astext.isnot(None),
        )
    )

    # Status filter
    if status == "missing":
        stmt = stmt.where(QuestionAnnotation.passage_spans.is_(None))
    # status == "all" → no extra filter

    # Content-origin filter
    if content_origin != "all":
        stmt = stmt.where(Question.content_origin == content_origin)

    # Priority ordering: active questions first, then by created_at
    if priority == "active":
        stmt = stmt.order_by(
            case((Question.practice_status == "active", 0), else_=1),
            Question.created_at,
        )
    else:
        stmt = stmt.order_by(Question.created_at)

    if limit:
        stmt = stmt.limit(limit)

    return stmt


async def process_one(
    question_id: UUID,
    session_factory: async_sessionmaker,
    dry_run: bool,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Annotate a single question; return result dict."""
    async with semaphore:
        if dry_run:
            # In dry-run mode: just report what would be done, no LLM call.
            return {
                "question_id": str(question_id),
                "status": "skipped",
                "reason": "dry-run",
            }

        async with session_factory() as db:
            try:
                result = await annotate_spans(question_id, db)
                return {"question_id": str(question_id), **result}
            except ValueError as exc:
                return {
                    "question_id": str(question_id),
                    "status": "failed",
                    "error_type": "value_error",
                    "detail": str(exc),
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "question_id": str(question_id),
                    "status": "failed",
                    "error_type": "unexpected_error",
                    "detail": str(exc),
                }


def _short_label(result: dict) -> str:
    """Return a short human-readable description of the result for logging."""
    if result.get("status") == "ok":
        label = result.get("label", "")
        return label if label else "ok"
    if result.get("status") == "skipped":
        return f"skipped — {result.get('reason', '')}"
    error_type = result.get("error_type") or ", ".join(result.get("error_types", []))
    detail = result.get("detail", "")
    if detail:
        return f"{error_type}: {detail[:80]}"
    return error_type or "failed"


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk span-annotate grammar questions missing passage_spans."
    )
    parser.add_argument(
        "--status",
        choices=["missing", "all"],
        default="missing",
        help="Which questions to process (default: missing)",
    )
    parser.add_argument(
        "--content-origin",
        choices=["official", "generated", "all"],
        default="official",
        help="Filter by content_origin (default: official)",
    )
    parser.add_argument(
        "--question-id",
        default=None,
        metavar="UUID",
        help="Process a single question by UUID",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="INT",
        help="Maximum number of questions to process (default: unlimited)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only — print what would be done but do not call LLM or write to DB",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        metavar="INT",
        help="Number of parallel workers (default: 5)",
    )
    parser.add_argument(
        "--priority",
        choices=["active", "all"],
        default="active",
        help="Order: 'active' puts active questions first (default: active)",
    )
    args = parser.parse_args()

    # Parse optional single-question UUID
    question_id: UUID | None = None
    if args.question_id:
        try:
            question_id = UUID(args.question_id)
        except ValueError:
            print(f"ERROR: --question-id '{args.question_id}' is not a valid UUID", file=sys.stderr)
            sys.exit(1)

    # Build async engine + session factory
    engine = create_async_engine(DB_DSN, echo=False, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Fetch question list
    async with session_factory() as db:
        stmt = build_query(
            status=args.status,
            content_origin=args.content_origin,
            priority=args.priority,
            limit=args.limit,
            question_id=question_id,
        )
        rows = (await db.execute(stmt)).scalars().all()

    question_ids = [q.id for q in rows]
    total = len(question_ids)

    if total == 0:
        print("No questions matched the given filters.")
        await engine.dispose()
        return

    print(f"Found {total} question(s) to process.")
    if args.dry_run:
        print("[dry-run] No LLM calls will be made.")

    semaphore = asyncio.Semaphore(args.concurrency)

    # Kick off all tasks
    tasks = [
        asyncio.create_task(
            process_one(qid, session_factory, args.dry_run, semaphore)
        )
        for qid in question_ids
    ]

    # Counters
    ok_count = 0
    failed_count = 0
    skipped_count = 0
    review_queue_count = 0
    completed = 0

    results: list[dict] = []

    try:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            completed += 1
            results.append(result)

            status = result.get("status", "failed")
            if status == "ok":
                ok_count += 1
            elif status == "skipped":
                skipped_count += 1
            else:
                failed_count += 1
                # annotate_spans logs failures to span_review_queue
                review_queue_count += 1

            label = _short_label(result)
            icon = "[ok]" if status == "ok" else ("[skip]" if status == "skipped" else "[fail]")
            print(f"{icon} {result['question_id']} — {label}")

    except KeyboardInterrupt:
        print("\nInterrupted — partial results follow.")
        # Cancel remaining tasks
        for t in tasks:
            t.cancel()

    await engine.dispose()

    # Summary
    processed = ok_count + failed_count + skipped_count
    total_pct = (ok_count / processed * 100) if processed else 0.0
    fail_pct = (failed_count / processed * 100) if processed else 0.0
    skip_pct = (skipped_count / processed * 100) if processed else 0.0

    print()
    print(f"Total:    {total}")
    print(f"Success:  {ok_count} ({total_pct:.1f}%)")
    print(f"Failed:   {failed_count} ({fail_pct:.1f}%)")
    print(f"Skipped:  {skipped_count} ({skip_pct:.1f}%)")
    print(f"Review queue entries added: {review_queue_count}")


if __name__ == "__main__":
    asyncio.run(main())
