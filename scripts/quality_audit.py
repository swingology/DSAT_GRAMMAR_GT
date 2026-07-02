#!/usr/bin/env python3
"""Quality audit for questions used in practice, diagnostic, and practice-test sections.

Checks every active (and optionally draft) question for:
  - Missing or blank question stem
  - Missing correct-answer label
  - Wrong option count (must be exactly 4: A B C D)
  - Blank option text
  - Orphaned correct-answer label (label set but no matching option)
  - Duplicate option texts within the same question
  - Passage questions with suspiciously short passage (< 50 chars)
  - OCR artefacts in stem or passage (replacement char U+FFFD, or >5 consecutive
    non-ASCII bytes — signs of a bad OCR extraction)

Usage (run from backend/ directory):
  cd backend
  uv run python ../scripts/quality_audit.py [options]

Options:
  --statuses     active|draft|all           Which questions to audit (default: active)
  --origin       official|generated|all     Content origin filter  (default: all)
  --dry-run                                 Report only — do not write to DB
  --limit        INT                        Cap number of questions audited
  --verbose                                 Print every question checked
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, ".")  # make app.* importable when run from backend/

from app.models.db import AdminQuestionAuditLog, Question, QuestionOption

import os
DB_DSN = os.getenv("DATABASE_URL", "postgresql+asyncpg://dsat:dsat_dev@localhost:5437/dsat_dev")

AUDIT_ACTION = "quality_audit_flagged"
AUDIT_TOKEN = "quality-audit-script"

# ── quality thresholds ────────────────────────────────────────────────────────
MIN_STEM_LEN = 15           # stems shorter than this are likely truncated
MIN_PASSAGE_LEN = 50        # passage text below this suggests a bad extraction
OCR_GARBAGE_RE = re.compile(r"[�]|[^\x00-\x7F]{6,}")  # replacement char or 6+ consecutive non-ASCII

EXPECTED_LABELS = {"A", "B", "C", "D"}


# ── per-question checks ───────────────────────────────────────────────────────

def check_question(q: Question, options: list[QuestionOption]) -> list[str]:
    """Return a list of human-readable failure strings (empty = pass)."""
    failures: list[str] = []

    stem = (q.current_question_text or "").strip()
    passage = (q.current_passage_text or "").strip()
    correct = q.current_correct_option_label

    # 1. Missing / blank stem
    if not stem:
        failures.append("missing question stem")
    elif len(stem) < MIN_STEM_LEN:
        failures.append(f"stem too short ({len(stem)} chars)")

    # 2. OCR artefacts in stem
    if stem and OCR_GARBAGE_RE.search(stem):
        failures.append("OCR artefacts in question stem")

    # 3. Missing correct-answer label
    if not correct:
        failures.append("missing correct answer label")

    # 4. Passage checks
    if passage:
        if len(passage) < MIN_PASSAGE_LEN:
            failures.append(f"passage too short ({len(passage)} chars)")
        if OCR_GARBAGE_RE.search(passage):
            failures.append("OCR artefacts in passage text")
    elif q.stimulus_mode_key and "passage" in (q.stimulus_mode_key or "").lower():
        # stimulus_mode_key implies there should be a passage but none exists
        failures.append("stimulus_mode_key implies passage but passage text is empty")

    # 5. Option checks
    present_labels = {o.option_label for o in options}
    missing_labels = EXPECTED_LABELS - present_labels
    if missing_labels:
        failures.append(f"missing answer options: {sorted(missing_labels)}")

    blank_options = [o.option_label for o in options if not (o.option_text or "").strip()]
    if blank_options:
        failures.append(f"blank option text for: {sorted(blank_options)}")

    # 6. Correct label exists but no matching option
    if correct and correct not in present_labels:
        failures.append(f"correct label '{correct}' has no matching option row")

    # 7. Duplicate option texts
    texts = [(o.option_text or "").strip().lower() for o in options if (o.option_text or "").strip()]
    if len(texts) != len(set(texts)):
        failures.append("duplicate option texts")

    return failures


# ── DB helpers ────────────────────────────────────────────────────────────────

async def load_options(
    session: AsyncSession, question_ids: list[UUID]
) -> dict[UUID, list[QuestionOption]]:
    """Fetch latest-version options for a batch of question IDs."""
    if not question_ids:
        return {}

    # We need the latest_version_id per question; join via Question
    stmt = (
        select(QuestionOption)
        .join(Question, QuestionOption.question_id == Question.id)
        .where(
            QuestionOption.question_id.in_(question_ids),
            QuestionOption.question_version_id == Question.latest_version_id,
        )
    )
    rows = (await session.execute(stmt)).scalars().all()

    result: dict[UUID, list[QuestionOption]] = {qid: [] for qid in question_ids}
    for opt in rows:
        result[opt.question_id].append(opt)
    return result


async def flag_question(
    session: AsyncSession,
    question: Question,
    failures: list[str],
    dry_run: bool,
) -> None:
    """Set question to draft and append an audit log entry."""
    reason = "; ".join(failures)

    if dry_run:
        return

    now = datetime.now(timezone.utc)

    before_status = question.practice_status

    # Move to draft so it surfaces in the admin review queue
    question.practice_status = "draft"  # type: ignore[assignment]
    question.rejection_reason = f"[quality-audit] {reason}"
    session.add(question)

    log = AdminQuestionAuditLog(
        id=uuid4(),
        question_id=question.id,
        admin_token=AUDIT_TOKEN,
        action=AUDIT_ACTION,
        fields_changed=["practice_status"],
        before_jsonb={"practice_status": before_status},
        after_jsonb={"practice_status": "draft"},
        change_notes=f"Quality audit failures: {reason}",
        question_version_id=question.latest_version_id,
        created_at=now,
    )
    session.add(log)


# ── main ──────────────────────────────────────────────────────────────────────

async def run(args: argparse.Namespace) -> None:
    engine = create_async_engine(DB_DSN, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        # ── load questions ────────────────────────────────────────────────────
        stmt = select(Question)

        if args.statuses == "all":
            pass
        elif args.statuses == "draft":
            stmt = stmt.where(Question.practice_status == "draft")
        else:  # default: active
            stmt = stmt.where(Question.practice_status == "active")

        if args.origin != "all":
            stmt = stmt.where(Question.content_origin == args.origin)

        if args.limit:
            stmt = stmt.limit(args.limit)

        questions: list[Question] = list((await session.execute(stmt)).scalars().all())
        print(f"\nAuditing {len(questions)} questions …\n")

        # ── batch load options ────────────────────────────────────────────────
        BATCH = 500
        all_options: dict[UUID, list[QuestionOption]] = {}
        for i in range(0, len(questions), BATCH):
            batch_ids = [q.id for q in questions[i : i + BATCH]]
            all_options.update(await load_options(session, batch_ids))

        # ── run checks ───────────────────────────────────────────────────────
        flagged: list[tuple[Question, list[str]]] = []
        passed = 0

        for q in questions:
            opts = all_options.get(q.id, [])
            failures = check_question(q, opts)

            if failures:
                flagged.append((q, failures))
                if args.verbose:
                    print(f"  FAIL [{q.content_origin}/{q.practice_status}] {q.id}")
                    for f in failures:
                        print(f"       · {f}")
            else:
                passed += 1
                if args.verbose:
                    print(f"  pass {q.id}")

        # ── report ───────────────────────────────────────────────────────────
        print("=" * 70)
        print(f"  PASSED : {passed}")
        print(f"  FAILED : {len(flagged)}")
        print("=" * 70)

        if flagged:
            # Group by failure category for summary
            category_counts: dict[str, int] = {}
            for _, failures in flagged:
                for f in failures:
                    # Normalise to a category key
                    key = re.sub(r"\(.*?\)", "", f).strip().rstrip(":")
                    category_counts[key] = category_counts.get(key, 0) + 1

            print("\nFailure breakdown:")
            for cat, cnt in sorted(category_counts.items(), key=lambda x: -x[1]):
                print(f"  {cnt:4d}  {cat}")

            print(f"\nFirst 20 failing questions:")
            for q, failures in flagged[:20]:
                print(
                    f"  {q.id}  [{q.source_exam_code or '?'} "
                    f"mod={q.source_module_code or '?'} "
                    f"q#{q.source_question_number or '?'}]"
                )
                for f in failures:
                    print(f"    · {f}")

        # ── apply flags ───────────────────────────────────────────────────────
        if not args.dry_run and flagged:
            print(f"\nFlagging {len(flagged)} questions as draft …")
            for q, failures in flagged:
                await flag_question(session, q, failures, dry_run=False)
            await session.commit()
            print(f"Done. {len(flagged)} questions moved to draft for admin review.")
        elif args.dry_run and flagged:
            print(f"\n[dry-run] Would flag {len(flagged)} questions — no changes written.")
        else:
            print("\nAll questions passed — nothing to flag.")

    await engine.dispose(close=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Quality audit for DSAT questions")
    parser.add_argument(
        "--statuses",
        default="active",
        choices=["active", "draft", "all"],
        help="Which practice_status values to audit (default: active)",
    )
    parser.add_argument(
        "--origin",
        default="all",
        choices=["official", "generated", "unofficial", "all"],
        help="Content origin filter (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report problems but do not write to DB",
    )
    parser.add_argument("--limit", type=int, default=None, help="Audit at most N questions")
    parser.add_argument("--verbose", action="store_true", help="Print result for every question")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
