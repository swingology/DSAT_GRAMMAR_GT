import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.auth import admin_required
from app.models.db import (
    Question, QuestionAnnotation, QuestionVersion, QuestionOption,
    QuestionRelation, QuestionJob, QuestionAsset, LlmEvaluation, UserProgress,
    QuestionStimulusAsset, ReviewRun, LlmReviewResult,
)
from app.models.ontology import RELATION_TYPES
from app.models.payload import AdminEditRequest, EvaluationScoreRequest
from app.pipeline import amendment_review


class EvaluationCreateRequest(BaseModel):
    job_id: Optional[str] = None
    question_id: Optional[str] = None
    provider_name: str = "ollama"
    model_name: str = "deepseek-v4-pro:cloud"
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


class AmendmentDecisionRequest(BaseModel):
    reviewer: str = "admin"
    notes: str = ""


class RejectQuestionRequest(BaseModel):
    reason: Optional[str] = None


router = APIRouter(prefix="/admin", tags=["admin"])


def _amendment_or_404(result: amendment_review.AmendmentOperationResult):
    if result.ok:
        if result.amendment is None:
            return {"ok": True}
        return result.amendment.to_file_dict()
    status_by_code = {
        "not_found": 404,
        "validation": 422,
        "conflict": 409,
    }
    status_code = status_by_code.get(result.error_code, 409)
    raise HTTPException(
        status_code=status_code,
        detail={"error": result.error, "details": result.details or {}},
    )


@router.get("/amendments")
async def list_amendments(_auth: str = Depends(admin_required)):
    return amendment_review.list_amendments()


@router.get("/amendments/{amendment_id}")
async def get_amendment(amendment_id: str, _auth: str = Depends(admin_required)):
    return _amendment_or_404(amendment_review.load_amendment_by_id(amendment_id))


@router.post("/amendments/{amendment_id}/approve")
async def approve_amendment(
    amendment_id: str,
    body: AmendmentDecisionRequest | None = None,
    _auth: str = Depends(admin_required),
):
    body = body or AmendmentDecisionRequest()
    return _amendment_or_404(
        amendment_review.approve_amendment(amendment_id, reviewer=body.reviewer, notes=body.notes)
    )


@router.post("/amendments/{amendment_id}/reject")
async def reject_amendment(
    amendment_id: str,
    body: AmendmentDecisionRequest | None = None,
    _auth: str = Depends(admin_required),
):
    body = body or AmendmentDecisionRequest()
    return _amendment_or_404(
        amendment_review.reject_amendment(amendment_id, reviewer=body.reviewer, notes=body.notes)
    )


@router.post("/amendments/{amendment_id}/request-more-evidence")
async def request_more_evidence(
    amendment_id: str,
    body: AmendmentDecisionRequest | None = None,
    _auth: str = Depends(admin_required),
):
    body = body or AmendmentDecisionRequest()
    return _amendment_or_404(
        amendment_review.request_more_evidence(amendment_id, reviewer=body.reviewer, notes=body.notes)
    )


@router.post("/amendments/{amendment_id}/promote")
async def promote_amendment(
    amendment_id: str,
    body: AmendmentDecisionRequest | None = None,
    _auth: str = Depends(admin_required),
):
    body = body or AmendmentDecisionRequest()
    return _amendment_or_404(
        amendment_review.promote_amendment(amendment_id, reviewer=body.reviewer, notes=body.notes)
    )


@router.get("/questions")
async def list_questions(
    practice_status: Optional[str] = Query(None, description="Filter by practice_status (draft/active/retired)"),
    content_origin: Optional[str] = Query(None, description="Filter by content_origin (official/generated)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """List questions for admin review. Defaults to draft (pending review) queue."""

    stmt = select(Question)
    if practice_status:
        stmt = stmt.where(Question.practice_status == practice_status)
    if content_origin:
        stmt = stmt.where(Question.content_origin == content_origin)
    stmt = stmt.order_by(Question.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    questions = result.unique().scalars().all()

    # Batch-load annotations and options to avoid N+1 queries.
    ann_ids = [q.latest_annotation_id for q in questions if q.latest_annotation_id]
    if ann_ids:
        ann_rows = await db.execute(select(QuestionAnnotation).where(QuestionAnnotation.id.in_(ann_ids)))
        ann_map = {a.id: a for a in ann_rows.scalars().all()}
    else:
        ann_map = {}

    version_to_qid = {q.latest_version_id: q.id for q in questions if q.latest_version_id}
    if version_to_qid:
        opts_rows = await db.execute(
            select(QuestionOption).where(
                QuestionOption.question_version_id.in_(list(version_to_qid.keys()))
            )
        )
        opts_by_qid: dict = {}
        for opt in opts_rows.scalars().all():
            qid = version_to_qid.get(opt.question_version_id)
            if qid:
                opts_by_qid.setdefault(qid, []).append(
                    {"label": opt.option_label, "text": opt.option_text, "is_correct": opt.is_correct}
                )
    else:
        opts_by_qid = {}

    items = []
    for q in questions:
        ann = ann_map.get(q.latest_annotation_id) if q.latest_annotation_id else None
        annotation = {**ann.annotation_jsonb, **ann.explanation_jsonb} if ann else None
        options = opts_by_qid.get(q.id, [])

        items.append({
            "id": str(q.id),
            "content_origin": q.content_origin,
            "practice_status": q.practice_status,
            "official_overlap_status": q.official_overlap_status,
            "source_exam_code": q.source_exam_code,
            "source_module_code": q.source_module_code,
            "source_question_number": q.source_question_number,
            "current_passage_text": q.current_passage_text,
            "current_question_text": q.current_question_text,
            "current_correct_option_label": q.current_correct_option_label,
            "current_explanation_text": q.current_explanation_text,
            "is_admin_edited": q.is_admin_edited,
            "annotation": annotation,
            "options": options,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })

    return items


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

    # Use explicit query — lazy-loading q.versions fails in async context
    latest_ver_result = await db.execute(
        select(QuestionVersion)
        .where(QuestionVersion.question_id == qid)
        .order_by(QuestionVersion.version_number.desc())
        .limit(1)
    )
    latest_version = latest_ver_result.scalars().first()

    # Load option rows scoped to the current version so we can clone them
    current_version_id = q.latest_version_id
    opts_q = select(QuestionOption).where(QuestionOption.question_id == qid)
    if current_version_id:
        opts_q = opts_q.where(QuestionOption.question_version_id == current_version_id)
    opts_result = await db.execute(opts_q.order_by(QuestionOption.option_label))
    existing_options = opts_result.scalars().all()

    # Build choices_jsonb for the new version snapshot
    new_correct_label = changes.get("correct_option_label", q.current_correct_option_label)
    choices = [
        {"label": o.option_label, "text": o.option_text, "is_correct": o.option_label == new_correct_label}
        for o in existing_options
    ]

    new_version = QuestionVersion(
        id=uuid.uuid4(),
        question_id=qid,
        version_number=(latest_version.version_number + 1) if latest_version else 1,
        change_source="admin_edit",
        question_text=changes.get("question_text", q.current_question_text),
        passage_text=changes.get("passage_text", q.current_passage_text),
        paired_passage_text=changes.get("paired_passage_text", q.current_paired_passage_text),
        underlined_text=changes.get("underlined_text", q.current_underlined_text),
        choices_jsonb=choices,
        correct_option_label=new_correct_label,
        explanation_text=changes.get("explanation_text", q.current_explanation_text),
        change_notes=changes.get("change_notes"),
        created_at=now,
    )
    db.add(new_version)

    # Clone QuestionOption rows for the new version with updated correctness flags
    await db.flush()  # ensure new_version.id is available
    for opt in existing_options:
        db.add(QuestionOption(
            id=uuid.uuid4(),
            question_id=qid,
            question_version_id=new_version.id,
            option_label=opt.option_label,
            option_text=opt.option_text,
            is_correct=opt.option_label == new_correct_label,
            option_role="correct" if opt.option_label == new_correct_label else "distractor",
            distractor_type_key=opt.distractor_type_key,
            semantic_relation_key=opt.semantic_relation_key,
            plausibility_source_key=opt.plausibility_source_key,
            option_error_focus_key=opt.option_error_focus_key,
            why_plausible=opt.why_plausible,
            why_wrong=opt.why_wrong,
            grammar_fit=opt.grammar_fit,
            tone_match=opt.tone_match,
            precision_score=opt.precision_score,
            student_failure_mode_key=opt.student_failure_mode_key,
            distractor_distance=opt.distractor_distance,
            distractor_competition_score=opt.distractor_competition_score,
            created_at=now,
        ))

    if "question_text" in changes:
        q.current_question_text = changes["question_text"]
    if "passage_text" in changes:
        q.current_passage_text = changes["passage_text"]
    if "paired_passage_text" in changes:
        q.current_paired_passage_text = changes["paired_passage_text"]
    if "underlined_text" in changes:
        q.current_underlined_text = changes["underlined_text"]
    if "correct_option_label" in changes:
        q.current_correct_option_label = changes["correct_option_label"]
    if "explanation_text" in changes:
        q.current_explanation_text = changes["explanation_text"]
    q.latest_version_id = new_version.id
    q.is_admin_edited = True
    q.annotation_stale = True
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

    if q.content_origin == "official" and q.official_overlap_status != "none":
        raise HTTPException(
            status_code=409,
            detail="Official questions with unresolved overlap cannot be approved",
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
    body: RejectQuestionRequest = RejectQuestionRequest(),
    db: AsyncSession = Depends(get_db),
    auth_token: str = Depends(admin_required),
):
    """Reject a question without destroying audit evidence.

    Sets `practice_status='rejected'` and records the reason, timestamp,
    and admin token. Annotations, options, options' annotation fields,
    relations, evaluations, and any future review-swarm rows are
    preserved so the question's history remains auditable.
    """
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    now = datetime.now(timezone.utc)
    q.practice_status = "rejected"
    q.rejection_reason = body.reason
    q.rejected_at = now
    q.rejected_by_admin_token = auth_token
    q.updated_at = now

    await db.commit()
    return {
        "id": str(q.id),
        "practice_status": "rejected",
        "rejected_at": now.isoformat(),
        "rejection_reason": body.reason,
    }


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Hard-delete a question and all linked data.

    Keeps job records (audit trail) and asset files on disk.
    Nulls the question_id FK on related jobs and assets rather than deleting them.
    """
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    # Null out incoming self-references from other questions first
    await db.execute(
        update(Question)
        .where(Question.canonical_official_question_id == qid)
        .values(canonical_official_question_id=None)
    )
    await db.execute(
        update(Question)
        .where(Question.derived_from_question_id == qid)
        .values(derived_from_question_id=None)
    )

    # Clear circular / self-referential FKs on the target question
    q.latest_annotation_id = None
    q.latest_version_id = None
    q.canonical_official_question_id = None
    q.derived_from_question_id = None
    await db.flush()

    # Delete linked metadata
    await db.execute(delete(LlmEvaluation).where(LlmEvaluation.question_id == qid))
    await db.execute(delete(QuestionAnnotation).where(QuestionAnnotation.question_id == qid))
    await db.execute(
        delete(QuestionRelation).where(
            (QuestionRelation.from_question_id == qid) | (QuestionRelation.to_question_id == qid)
        )
    )
    await db.execute(delete(UserProgress).where(UserProgress.question_id == qid))
    await db.execute(delete(QuestionOption).where(QuestionOption.question_id == qid))
    await db.execute(delete(QuestionVersion).where(QuestionVersion.question_id == qid))

    # Detach jobs and assets rather than deleting (preserve audit trail / files)
    jobs_result = await db.execute(select(QuestionJob).where(QuestionJob.question_id == qid))
    for job in jobs_result.scalars().all():
        job.question_id = None

    assets_result = await db.execute(select(QuestionAsset).where(QuestionAsset.question_id == qid))
    for asset in assets_result.scalars().all():
        asset.question_id = None

    await db.flush()
    await db.delete(q)
    await db.commit()
    return {"id": question_id, "deleted": True}


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


@router.get("/questions/{question_id}/stimulus-assets")
async def get_stimulus_assets(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    result = await db.execute(
        select(QuestionStimulusAsset)
        .where(QuestionStimulusAsset.question_id == qid)
        .order_by(QuestionStimulusAsset.source_page_number, QuestionStimulusAsset.stimulus_type)
    )
    assets = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "stimulus_type": a.stimulus_type,
            "storage_path": a.storage_path,
            "source_page_number": a.source_page_number,
            "title": a.title,
            "structured_data": a.structured_data_jsonb,
            "render_hints": a.render_hints_jsonb,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assets
    ]


@router.post("/jobs/{job_id}/fail")
async def force_fail_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Mark a stuck in-progress job as failed."""
    _TERMINAL = {"approved", "needs_review", "failed", "rejected"}
    jid = _parse_uuid(job_id)
    job = await db.get(QuestionJob, jid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in _TERMINAL:
        raise HTTPException(status_code=409, detail=f"Job is already in terminal state '{job.status}'")
    job.status = "failed"
    job.validation_errors_jsonb = list(job.validation_errors_jsonb or []) + [
        {"step": "admin_force_fail", "error": "Manually marked as failed by admin"}
    ]
    await db.commit()
    return {"id": str(job.id), "status": "failed"}


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
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
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

    result = await db.execute(stmt.order_by(QuestionRelation.created_at.desc()).offset(offset).limit(limit))
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
    if from_id == to_id:
        raise HTTPException(status_code=400, detail="A question cannot relate to itself")
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


# --- Phase 4: Review swarm endpoints ---------------------------------------------


@router.post("/questions/{question_id}/review-swarm")
async def trigger_review_swarm(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    auth_token: str = Depends(admin_required),
):
    """Trigger a multi-model review swarm for a single generated question.

    Creates a ReviewRun, runs all configured reviewers concurrently, and
    returns the run status with individual reviewer results.

    A new review run is always created — re-reviewing a question produces a
    new `review_run_id` while preserving previous review rows.
    """
    qid = _parse_uuid(question_id)
    question = await db.get(Question, qid)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.content_origin != "generated":
        raise HTTPException(
            status_code=400,
            detail="Review swarm is only available for generated questions",
        )

    from app.review.runner import run_review_swarm
    review_run = await run_review_swarm(
        qid,
        triggered_by="manual_question",
        admin_token=auth_token,
    )

    # Load review results for this run
    result_rows = await db.execute(
        select(LlmReviewResult).where(LlmReviewResult.review_run_id == review_run.id)
    )
    results = result_rows.scalars().all()

    return {
        "review_run_id": str(review_run.id),
        "question_id": str(qid),
        "status": review_run.status,
        "rubric_version": review_run.rubric_version,
        "started_at": review_run.started_at.isoformat() if review_run.started_at else None,
        "completed_at": review_run.completed_at.isoformat() if review_run.completed_at else None,
        "results": [
            {
                "id": str(r.id),
                "provider_name": r.provider_name,
                "model_name": r.model_name,
                "verdict": r.verdict,
                "scores_jsonb": r.scores_jsonb,
                "review_status": r.review_status,
                "latency_ms": r.latency_ms,
                "error_message": r.error_message,
            }
            for r in results
        ],
    }


@router.get("/questions/{question_id}/review-runs")
async def list_review_runs(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """List all review runs for a question, most recent first."""
    qid = _parse_uuid(question_id)
    question = await db.get(Question, qid)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    runs = await db.execute(
        select(ReviewRun)
        .where(ReviewRun.question_id == qid)
        .order_by(ReviewRun.started_at.desc())
    )
    review_runs = runs.scalars().all()

    result_list = []
    for run in review_runs:
        result_rows = await db.execute(
            select(LlmReviewResult).where(LlmReviewResult.review_run_id == run.id)
        )
        results = result_rows.scalars().all()
        result_list.append({
            "review_run_id": str(run.id),
            "status": run.status,
            "triggered_by": run.triggered_by,
            "rubric_version": run.rubric_version,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "results": [
                {
                    "id": str(r.id),
                    "provider_name": r.provider_name,
                    "model_name": r.model_name,
                    "verdict": r.verdict,
                    "scores_jsonb": r.scores_jsonb,
                    "review_status": r.review_status,
                    "latency_ms": r.latency_ms,
                    "error_message": r.error_message,
                }
                for r in results
            ],
        })

    return {"question_id": str(qid), "review_runs": result_list}
