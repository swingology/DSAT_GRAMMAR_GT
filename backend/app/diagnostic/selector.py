"""Diagnostic blueprint selector — fills a blueprint from the live question bank.

For each Slot the selector applies a fallback ladder (tightest → loosest filter)
until it finds an unseen, active, non-dry-run question that hasn't already been
chosen in this assembly. Bank is thin (~27 grammar / 13 reading), so level-3/4
fallback is expected and acceptable for v1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.diagnostic.blueprint import BLUEPRINT_V1, Slot
from app.diagnostic.queries import build_pool_stmt


@dataclass
class ChosenQuestion:
    slot: Slot
    question_id: str
    fallback_level: int  # 1=tightest, 6=any active (gap)
    gap: bool = False    # True when domain was exhausted


@dataclass
class AssembledDiagnostic:
    questions: list[ChosenQuestion]
    coverage_report: dict


class DiagnosticBankExhaustedError(RuntimeError):
    """Raised when the live question bank cannot fill a diagnostic blueprint."""


async def _fetch_one_id(
    db: AsyncSession,
    *,
    stmt,
    exclude_ids: set[str],
) -> Optional[str]:
    """Execute stmt, skip ids already chosen, return first hit or None."""
    from sqlalchemy import text as sa_text
    result = await db.execute(stmt)
    for row in result.scalars():
        qid = str(row.id) if hasattr(row, "id") else str(row)
        if qid not in exclude_ids:
            return qid
    return None


async def assemble_diagnostic(
    db: AsyncSession,
    *,
    user_id: int,
    blueprint: tuple[Slot, ...] = BLUEPRINT_V1,
    exclude_seen: bool = True,
) -> AssembledDiagnostic:
    """Assemble a full diagnostic module by filling every blueprint slot.

    Applies a 6-level fallback ladder per slot so a thin bank never blocks
    the assembly. Chosen question IDs are tracked across slots to prevent reuse.
    """
    chosen: list[ChosenQuestion] = []
    chosen_ids: set[str] = set()

    exclude_seen_uid = user_id if exclude_seen else None

    for slot in blueprint:
        is_grammar = slot.domain == "grammar"
        role_kwarg = {"grammar_role_key": slot.role_or_skill} if is_grammar else {}
        skill_kwarg = {"skill_family_key": slot.role_or_skill} if not is_grammar else {}

        qid: Optional[str] = None
        fallback_level = 0

        # Level 1: difficulty + domain + role/skill + focus + trap_preference
        #          (focus/trap are soft — we implement soft by just trying with them)
        # Note: build_pool_stmt doesn't support focus/trap filtering yet; treat as level 2.

        # Level 2: difficulty + domain + role/skill (no trap)
        if qid is None:
            fallback_level = 2
            stmt = build_pool_stmt(
                domain=slot.domain,
                difficulty=slot.difficulty,
                exclude_question_ids=chosen_ids,
                exclude_seen_user_id=exclude_seen_uid,
                **role_kwarg,
                **skill_kwarg,
            )
            qid = await _fetch_one_id(db, stmt=stmt, exclude_ids=chosen_ids)

        # Level 3: drop difficulty
        if qid is None:
            fallback_level = 3
            stmt = build_pool_stmt(
                domain=slot.domain,
                difficulty=None,
                exclude_question_ids=chosen_ids,
                exclude_seen_user_id=exclude_seen_uid,
                **role_kwarg,
                **skill_kwarg,
            )
            qid = await _fetch_one_id(db, stmt=stmt, exclude_ids=chosen_ids)

        # Level 4: drop role/skill too — any question in the domain
        if qid is None:
            fallback_level = 4
            stmt = build_pool_stmt(
                domain=slot.domain,
                exclude_question_ids=chosen_ids,
                exclude_seen_user_id=exclude_seen_uid,
            )
            qid = await _fetch_one_id(db, stmt=stmt, exclude_ids=chosen_ids)

        # Level 5: drop seen-filter (allow re-seen questions)
        if qid is None:
            fallback_level = 5
            stmt = build_pool_stmt(
                domain=slot.domain,
                exclude_question_ids=chosen_ids,
            )
            qid = await _fetch_one_id(db, stmt=stmt, exclude_ids=chosen_ids)

        # Level 6: domain exhausted — take any active question (gap)
        gap = False
        if qid is None:
            fallback_level = 6
            gap = True
            stmt = build_pool_stmt(exclude_question_ids=chosen_ids)
            qid = await _fetch_one_id(db, stmt=stmt, exclude_ids=chosen_ids)

        if qid is None:
            raise DiagnosticBankExhaustedError(
                f"Bank exhausted at slot {slot.seq} — not enough active questions"
            )

        chosen_ids.add(qid)
        chosen.append(ChosenQuestion(slot=slot, question_id=qid, fallback_level=fallback_level, gap=gap))

    coverage_report = _build_coverage_report(chosen)
    return AssembledDiagnostic(questions=chosen, coverage_report=coverage_report)


def _build_coverage_report(chosen: list[ChosenQuestion]) -> dict:
    from collections import Counter

    levels: Counter = Counter(c.fallback_level for c in chosen)
    gaps = sum(1 for c in chosen if c.gap)
    return {
        "total": len(chosen),
        "gaps": gaps,
        "fallback_level_distribution": dict(levels),
        "gap_slots": [c.slot.seq for c in chosen if c.gap],
    }
