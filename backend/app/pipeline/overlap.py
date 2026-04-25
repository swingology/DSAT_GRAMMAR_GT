"""Overlap detection between unofficial/generated questions and official questions.

Compares annotation data (grammar focus, passage text, question text) to detect
potential overlaps with existing official questions in the database.
"""
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Question, QuestionAnnotation, QuestionRelation


def _word_set(text: Optional[str]) -> set:
    """Tokenize text into a set of lowercase words for comparison."""
    if not text:
        return set()
    return set(text.lower().split())


def _jaccard_similarity(a: set, b: set) -> float:
    """Jaccard similarity between two sets."""
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union) if union else 0.0


async def detect_overlaps(
    question_id: uuid.UUID,
    annotation_jsonb: dict,
    passage_text: Optional[str],
    question_text: str,
    db: AsyncSession,
    threshold: float = 0.4,
) -> List[Dict]:
    """Compare a question against all active official questions to detect overlaps.

    Uses a single JOIN to load annotations alongside questions, avoiding N+1 queries.
    Returns: [{"official_question_id": UUID, "relation_type": str, "strength": float, "detection_method": str}]
    """
    stmt = (
        select(Question, QuestionAnnotation)
        .outerjoin(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
        )
        .where(
            Question.content_origin == "official",
            Question.practice_status == "active",
        )
    )
    rows = (await db.execute(stmt)).all()

    overlaps = []
    new_passage_words = _word_set(passage_text)
    new_question_words = _word_set(question_text)
    new_focus = annotation_jsonb.get("grammar_focus_key")

    for oq, official_ann in rows:
        if oq.id == question_id:
            continue

        official_annotation = official_ann.annotation_jsonb if official_ann else None

        strength = 0.0
        detection_signals = []

        # Compare passage text
        if new_passage_words and oq.current_passage_text:
            official_passage_words = _word_set(oq.current_passage_text)
            passage_sim = _jaccard_similarity(new_passage_words, official_passage_words)
            if passage_sim > 0.3:
                strength = max(strength, passage_sim)
                detection_signals.append(f"passage_similarity={passage_sim:.2f}")

        # Compare question text
        if new_question_words:
            official_question_words = _word_set(oq.current_question_text)
            question_sim = _jaccard_similarity(new_question_words, official_question_words)
            if question_sim > 0.3:
                strength = max(strength, question_sim)
                detection_signals.append(f"question_similarity={question_sim:.2f}")

        # Compare grammar focus
        if official_annotation and new_focus:
            official_focus = official_annotation.get("grammar_focus_key")
            if official_focus == new_focus:
                strength = max(strength, 0.3)
                detection_signals.append("grammar_focus_match")

        if strength >= threshold:
            relation_type = "overlaps_official" if strength > 0.6 else "near_duplicate"
            overlaps.append({
                "official_question_id": oq.id,
                "relation_type": relation_type,
                "strength": round(strength, 3),
                "detection_method": "; ".join(detection_signals) if detection_signals else "automated",
            })

    return overlaps


async def persist_overlap_relations(
    question_id: uuid.UUID,
    overlaps: List[Dict],
    db: AsyncSession,
) -> None:
    """Persist overlap results as QuestionRelation rows for an existing question."""
    now = datetime.now(timezone.utc)

    for overlap in overlaps:
        existing = await db.execute(
            select(QuestionRelation).where(
                QuestionRelation.from_question_id == question_id,
                QuestionRelation.to_question_id == overlap["official_question_id"],
                QuestionRelation.relation_type == overlap["relation_type"],
            )
        )
        if existing.scalars().first():
            continue

        db.add(QuestionRelation(
            id=uuid.uuid4(),
            from_question_id=question_id,
            to_question_id=overlap["official_question_id"],
            relation_type=overlap["relation_type"],
            relation_strength=overlap["strength"],
            detection_method=overlap["detection_method"],
            is_human_confirmed=False,
            created_at=now,
        ))


async def run_overlap_check(
    question_id: uuid.UUID,
    annotation_jsonb: dict,
    passage_text: Optional[str],
    question_text: str,
    db: AsyncSession,
) -> List[Dict]:
    """Run overlap detection and persist results as QuestionRelation rows.

    Returns the list of created overlap records.
    """
    overlaps = await detect_overlaps(
        question_id=question_id,
        annotation_jsonb=annotation_jsonb,
        passage_text=passage_text,
        question_text=question_text,
        db=db,
    )
    await persist_overlap_relations(question_id=question_id, overlaps=overlaps, db=db)
    await db.commit()
    return overlaps
