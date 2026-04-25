import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth import admin_required
from app.models.db import Question, QuestionVersion, QuestionOption, QuestionRelation, LlmEvaluation
from app.models.ontology import RELATION_TYPES
from app.models.payload import AdminEditRequest, EvaluationScoreRequest


class EvaluationCreateRequest(BaseModel):
    job_id: str
    question_id: Optional[str] = None
    provider_name: str = "anthropic"
    model_name: str = "claude-sonnet-4-6"
    task_type: str = "annotation"
    score_overall: Optional[float] = None
    score_metadata: Optional[float] = None
    score_explanation: Optional[float] = None
    score_generation: Optional[float] = None
    review_notes: Optional[str] = None
    recommended_for_default: Optional[bool] = None


class RelationCreateRequest(BaseModel):
    from_question_id: str
    to_question_id: str
    relation_type: str
    relation_strength: Optional[float] = None
    detection_method: Optional[str] = None
    notes: Optional[str] = None


router = APIRouter(prefix="/admin", tags=["admin"])


def _parse_uuid(item_id: str) -> UUID:
    try:
        return UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")


def _validated_relation_type(relation_type: str) -> str:
    if relation_type not in RELATION_TYPES:
        raise HTTPException(status_code=400, detail="Invalid relation_type")
    return relation_type


@router.patch("/questions/{question_id}")
async def edit_question(
    question_id: str,
    body: AdminEditRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided")

    now = datetime.now(timezone.utc)

    latest_version = None
    if q.versions:
        latest_version = max(q.versions, key=lambda v: v.version_number)

    # Serialize current options into choices_jsonb
    opts_result = await db.execute(
        select(QuestionOption).where(QuestionOption.question_id == qid)
    )
    choices = [
        {"label": o.option_label, "text": o.option_text, "is_correct": o.is_correct}
        for o in opts_result.scalars().all()
    ]
    if "correct_option_label" in changes:
        for choice in choices:
            choice["is_correct"] = choice["label"] == changes["correct_option_label"]

    new_version = QuestionVersion(
        id=uuid.uuid4(),
        question_id=qid,
        version_number=(latest_version.version_number + 1) if latest_version else 1,
        change_source="admin_edit",
        question_text=changes.get("question_text", q.current_question_text),
        passage_text=changes.get("passage_text", q.current_passage_text),
        choices_jsonb=choices,
        correct_option_label=changes.get("correct_option_label", q.current_correct_option_label),
        explanation_text=changes.get("explanation_text", q.current_explanation_text),
        change_notes=changes.get("change_notes"),
        created_at=now,
    )
    db.add(new_version)

    if "question_text" in changes:
        q.current_question_text = changes["question_text"]
    if "passage_text" in changes:
        q.current_passage_text = changes["passage_text"]
    if "correct_option_label" in changes:
        q.current_correct_option_label = changes["correct_option_label"]
    if "explanation_text" in changes:
        q.current_explanation_text = changes["explanation_text"]
    q.latest_version_id = new_version.id
    q.is_admin_edited = True
    q.updated_at = now

    await db.commit()
    return {"id": str(q.id), "version": new_version.version_number, "changes": list(changes.keys())}


@router.post("/questions/{question_id}/approve")
async def approve_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    if q.content_origin == "official":
        raise HTTPException(
            status_code=409,
            detail="Official questions cannot be approved until answer verification is implemented",
        )
    if q.content_origin == "generated" and q.official_overlap_status != "none":
        raise HTTPException(
            status_code=409,
            detail="Generated questions with unresolved official overlap cannot be approved",
        )

    q.practice_status = "active"
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(q.id), "practice_status": "active"}


@router.post("/questions/{question_id}/reject")
async def reject_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.practice_status = "retired"
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(q.id), "practice_status": "retired"}


@router.post("/questions/{question_id}/confirm-overlap")
async def confirm_overlap(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    result = await db.execute(
        select(QuestionRelation)
        .join(Question, Question.id == QuestionRelation.to_question_id)
        .where(
            QuestionRelation.from_question_id == qid,
            QuestionRelation.relation_type.in_(("overlaps_official", "near_duplicate")),
            Question.content_origin == "official",
        )
        .order_by(QuestionRelation.created_at.desc())
    )
    relations = result.scalars().all()
    if not relations:
        raise HTTPException(status_code=409, detail="No official overlap relation found to confirm")
    official_question_ids = {rel.to_question_id for rel in relations}
    if len(official_question_ids) != 1:
        raise HTTPException(status_code=409, detail="Multiple official overlap candidates found; resolve manually")

    q.official_overlap_status = "confirmed"
    q.canonical_official_question_id = relations[0].to_question_id
    for rel in relations:
        rel.is_human_confirmed = True
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "id": str(q.id),
        "official_overlap_status": "confirmed",
        "canonical_official_question_id": str(q.canonical_official_question_id),
    }


@router.post("/questions/{question_id}/clear-overlap")
async def clear_overlap(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.official_overlap_status = "none"
    q.canonical_official_question_id = None
    q.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(q.id), "official_overlap_status": "none"}


@router.post("/evaluations/{evaluation_id}/score")
async def score_evaluation(
    evaluation_id: str,
    body: EvaluationScoreRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    eid = _parse_uuid(evaluation_id)
    ev = await db.get(LlmEvaluation, eid)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if body.score_overall is not None:
        ev.score_overall = body.score_overall
    if body.score_metadata is not None:
        ev.score_metadata = body.score_metadata
    if body.score_explanation is not None:
        ev.score_explanation = body.score_explanation
    if body.score_generation is not None:
        ev.score_generation = body.score_generation
    if body.review_notes is not None:
        ev.review_notes = body.review_notes
    if body.recommended_for_default is not None:
        ev.recommended_for_default = body.recommended_for_default

    await db.commit()
    return {"id": str(ev.id), "score_overall": ev.score_overall}


@router.post("/evaluations")
async def create_evaluation(
    body: EvaluationCreateRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Create a new LLM evaluation record."""
    from app.models.db import QuestionJob

    try:
        jid = uuid.UUID(body.job_id) if body.job_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id UUID")
    if jid:
        job = await db.get(QuestionJob, jid)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

    qid = None
    if body.question_id:
        try:
            qid = uuid.UUID(body.question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question_id UUID")
        question = await db.get(Question, qid)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

    ev = LlmEvaluation(
        id=uuid.uuid4(),
        job_id=jid,
        question_id=qid,
        provider_name=body.provider_name,
        model_name=body.model_name,
        task_type=body.task_type,
        score_overall=body.score_overall,
        score_metadata=body.score_metadata,
        score_explanation=body.score_explanation,
        score_generation=body.score_generation,
        review_notes=body.review_notes,
        recommended_for_default=body.recommended_for_default,
        created_at=datetime.now(timezone.utc),
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return {"id": str(ev.id), "task_type": ev.task_type}


@router.get("/relations")
async def list_relations(
    from_question_id: Optional[str] = None,
    relation_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """List question relations, optionally filtered."""
    stmt = select(QuestionRelation)

    if from_question_id:
        try:
            fqid = uuid.UUID(from_question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_question_id UUID")
        stmt = stmt.where(QuestionRelation.from_question_id == fqid)

    if relation_type:
        stmt = stmt.where(QuestionRelation.relation_type == relation_type)

    result = await db.execute(stmt.order_by(QuestionRelation.created_at.desc()))
    relations = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "from_question_id": str(r.from_question_id),
            "to_question_id": str(r.to_question_id),
            "relation_type": r.relation_type,
            "relation_strength": r.relation_strength,
            "detection_method": r.detection_method,
            "is_human_confirmed": r.is_human_confirmed,
            "notes": r.notes,
            "created_at": r.created_at,
        }
        for r in relations
    ]


@router.post("/relations")
async def create_relation(
    body: RelationCreateRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Create a new question relation."""
    try:
        from_id = uuid.UUID(body.from_question_id)
        to_id = uuid.UUID(body.to_question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID in from_question_id or to_question_id")
    relation_type = _validated_relation_type(body.relation_type)

    # Verify both questions exist
    from_q = await db.get(Question, from_id)
    to_q = await db.get(Question, to_id)
    if not from_q or not to_q:
        raise HTTPException(status_code=404, detail="Source or target question not found")

    # Check for duplicate
    existing = await db.execute(
        select(QuestionRelation).where(
            QuestionRelation.from_question_id == from_id,
            QuestionRelation.to_question_id == to_id,
            QuestionRelation.relation_type == body.relation_type,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Relation already exists")

    rel = QuestionRelation(
        id=uuid.uuid4(),
        from_question_id=from_id,
        to_question_id=to_id,
        relation_type=relation_type,
        relation_strength=body.relation_strength,
        detection_method=body.detection_method,
        notes=body.notes,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return {"id": str(rel.id), "relation_type": rel.relation_type}


@router.delete("/relations/{relation_id}")
async def delete_relation(
    relation_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Delete a question relation."""
    rid = _parse_uuid(relation_id)
    rel = await db.get(QuestionRelation, rid)
    if not rel:
        raise HTTPException(status_code=404, detail="Relation not found")
    await db.delete(rel)
    await db.commit()
    return {"detail": "Relation deleted"}
