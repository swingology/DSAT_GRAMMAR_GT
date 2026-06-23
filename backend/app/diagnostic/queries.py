"""Diagnostic question-pool queries and domain classification.

TASK-B0A / bug-761: the live v8 bank classifies reading via ``skill_family_key``
(singular) and leaves ``reading_skill_family_key`` / ``reading_focus_key`` NULL on
every active question. The legacy student ``/questions`` reading filter and
``diagnostic_submit`` domain derivation key off those empty fields, so reading is
effectively unqueryable through that path. The diagnostic uses the helpers here
instead, which read the keys the bank actually populates.
"""

from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.sql import Select

from app.models.db import (
    Question,
    QuestionAnnotation,
    QuestionJob,
    GenerationBatch,
    UserProgress,
)

# Keep in sync with student.py:_DRY_RUN_RELEASE_POLICY
_DRY_RUN_RELEASE_POLICY = "dry_run"


def derive_domain(ann: dict) -> Optional[str]:
    """Classify a question's domain from its annotation_jsonb.

    Uses the keys the v8 ingestion pipeline actually populates:
    reading → ``skill_family_key`` (singular); grammar → ``grammar_role_key``.
    Reading is checked first because a reading question never carries a
    grammar_role_key value in this bank (verified: 0 overlap).
    """
    if not ann:
        return None
    if ann.get("skill_family_key"):
        return "reading"
    if ann.get("grammar_role_key"):
        return "grammar"
    return None


def build_pool_stmt(
    *,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    grammar_role_key: Optional[str] = None,
    skill_family_key: Optional[str] = None,
    stem_type_key: Optional[str] = None,
    exclude_question_ids: Iterable = (),
    exclude_seen_user_id: Optional[int] = None,
) -> Select:
    """Build a ``Select(Question)`` over the diagnostic-eligible pool.

    Filters on the keys the bank actually uses. Always restricts to active,
    non-dry-run questions. ``difficulty`` filters ``difficulty_overall`` only when
    provided (None ⇒ include null-difficulty questions — important for the thin
    official bank). ``exclude_seen_user_id`` removes any question the user already
    has a UserProgress row for.
    """
    stmt = select(Question).where(Question.practice_status == "active")

    # Exclude dry-run generated content (mirrors _build_question_filter_stmt).
    dry_run_exists = (
        select(QuestionJob.id)
        .join(GenerationBatch, GenerationBatch.id == QuestionJob.generation_batch_id)
        .where(
            QuestionJob.question_id == Question.id,
            GenerationBatch.release_policy == _DRY_RUN_RELEASE_POLICY,
        )
        .exists()
    )
    stmt = stmt.where(~dry_run_exists)

    needs_ann = bool(
        domain or difficulty or grammar_role_key or skill_family_key or stem_type_key
    )
    if needs_ann:
        stmt = stmt.join(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
        )
        ann = QuestionAnnotation.annotation_jsonb
        if domain == "grammar":
            stmt = stmt.where(ann["grammar_role_key"].astext.isnot(None))
        elif domain == "reading":
            stmt = stmt.where(ann["skill_family_key"].astext.isnot(None))
        if grammar_role_key:
            stmt = stmt.where(ann["grammar_role_key"].astext == grammar_role_key)
        if skill_family_key:
            stmt = stmt.where(ann["skill_family_key"].astext == skill_family_key)
        if stem_type_key:
            stmt = stmt.where(ann["stem_type_key"].astext == stem_type_key)
        if difficulty:
            stmt = stmt.where(ann["difficulty_overall"].astext == difficulty)

    exclude_ids = [str(qid) for qid in exclude_question_ids]
    if exclude_ids:
        stmt = stmt.where(Question.id.not_in(exclude_ids))

    if exclude_seen_user_id is not None:
        seen_subq = (
            select(UserProgress.question_id)
            .where(UserProgress.user_id == exclude_seen_user_id)
            .distinct()
        )
        stmt = stmt.where(Question.id.not_in(seen_subq))

    return stmt
