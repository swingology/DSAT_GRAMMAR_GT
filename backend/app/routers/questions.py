from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.auth import admin_required
from app.models.db import Question, QuestionVersion, QuestionAnnotation, QuestionOption
from app.models.payload import QuestionRecallResponse, QuestionDetailResponse

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/recall", response_model=list[QuestionRecallResponse])
async def recall_questions(
    grammar_focus: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    stmt = select(Question).where(Question.practice_status == "active")

    if origin:
        stmt = stmt.where(Question.content_origin == origin)

    # Join annotations once when any annotation-backed filter is present.
    if grammar_focus or difficulty:
        stmt = stmt.join(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
        )
        if grammar_focus:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["grammar_focus_key"].astext == grammar_focus
            )
        if difficulty:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["difficulty_overall"].astext == difficulty
            )

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    questions = result.unique().scalars().all()

    responses = []
    for q in questions:
        grammar_role_key = None
        grammar_focus_key = None
        difficulty_overall = None
        generation_profile = None
        if q.latest_annotation_id:
            ann = await db.get(QuestionAnnotation, q.latest_annotation_id)
            if ann:
                grammar_role_key = ann.annotation_jsonb.get("grammar_role_key")
                grammar_focus_key = ann.annotation_jsonb.get("grammar_focus_key")
                difficulty_overall = ann.annotation_jsonb.get("difficulty_overall")
                generation_profile = ann.generation_profile_jsonb

        responses.append(QuestionRecallResponse(
            id=str(q.id),
            content_origin=q.content_origin,
            current_question_text=q.current_question_text,
            current_passage_text=q.current_passage_text,
            current_correct_option_label=q.current_correct_option_label,
            practice_status=q.practice_status,
            grammar_role_key=grammar_role_key,
            grammar_focus_key=grammar_focus_key,
            difficulty_overall=difficulty_overall,
            stimulus_mode_key=q.stimulus_mode_key,
            source_exam_code=q.source_exam_code,
            source_subject_code=q.source_subject_code,
            source_section_code=q.source_section_code,
            source_module_code=q.source_module_code,
            generation_profile=generation_profile,
        ))
    return responses


@router.get("/{question_id}", response_model=QuestionDetailResponse)
async def get_question_detail(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    try:
        qid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    latest_annotation = None
    generation_profile = None
    if q.latest_annotation_id:
        ann = await db.get(QuestionAnnotation, q.latest_annotation_id)
        if ann:
            latest_annotation = {**ann.annotation_jsonb, **ann.explanation_jsonb}
            generation_profile = ann.generation_profile_jsonb

    opts_result = await db.execute(
        select(QuestionOption).where(QuestionOption.question_id == qid)
    )
    options = [
        {
            "label": o.option_label,
            "text": o.option_text,
            "is_correct": o.is_correct,
            "role": o.option_role,
            "why_plausible": o.why_plausible,
            "why_wrong": o.why_wrong,
        }
        for o in opts_result.scalars().all()
    ]

    lineage = None
    if q.derived_from_question_id or q.generation_source_set:
        lineage = {
            "derived_from": str(q.derived_from_question_id) if q.derived_from_question_id else None,
            "generation_source_set": q.generation_source_set,
        }

    return QuestionDetailResponse(
        id=str(q.id),
        content_origin=q.content_origin,
        current_question_text=q.current_question_text,
        current_passage_text=q.current_passage_text,
        current_correct_option_label=q.current_correct_option_label,
        current_explanation_text=q.current_explanation_text,
        practice_status=q.practice_status,
        official_overlap_status=q.official_overlap_status,
        is_admin_edited=q.is_admin_edited,
        source_exam_code=q.source_exam_code,
        source_subject_code=q.source_subject_code,
        source_section_code=q.source_section_code,
        source_module_code=q.source_module_code,
        latest_annotation=latest_annotation,
        generation_profile=generation_profile,
        options=options,
        lineage=lineage,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


@router.get("/{question_id}/versions", response_model=list[dict])
async def get_question_versions(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    try:
        qid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    result = await db.execute(
        select(QuestionVersion)
        .where(QuestionVersion.question_id == qid)
        .order_by(QuestionVersion.version_number)
    )
    versions = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "version_number": v.version_number,
            "change_source": v.change_source,
            "question_text": v.question_text,
            "correct_option_label": v.correct_option_label,
            "change_notes": v.change_notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]
