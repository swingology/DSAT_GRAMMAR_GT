from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple
from uuid import UUID

from app.config import get_settings
from app.database import get_db
from app.auth import student_required, admin_or_student_required
from app.models.db import Question, User, UserProgress, QuestionAnnotation, QuestionOption
from app.models.payload import (
    StudentQuestionResponse,
    StudentQuestionsListResponse,
    InventoryMetadata,
    UserProgressCreate,
    UserStats,
)

router = APIRouter(prefix="/api", tags=["student"])


def _build_question_filter_stmt(
    *,
    domain: Optional[str],
    difficulty: Optional[str],
    grammar_role_key: Optional[str],
    grammar_focus_key: Optional[str],
    reading_skill_family_key: Optional[str],
    reading_focus_key: Optional[str],
    stimulus_mode_key: Optional[str],
    origin: Optional[str],
):
    """Return a SELECT(Question) statement with all target filters applied.

    Annotation join is added once only when any annotation-backed filter is present.
    Origin filter maps official/generated to content_origin; mixed (or None) = no filter.
    """
    stmt = select(Question).where(Question.practice_status == "active")

    if origin and origin != "mixed":
        stmt = stmt.where(Question.content_origin == origin)

    if stimulus_mode_key:
        stmt = stmt.where(Question.stimulus_mode_key == stimulus_mode_key)

    needs_ann_join = bool(
        domain or difficulty or grammar_role_key or grammar_focus_key
        or reading_skill_family_key or reading_focus_key
    )
    if needs_ann_join:
        stmt = stmt.join(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
        )
        if domain == "grammar":
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["grammar_role_key"].astext.isnot(None)
            )
        elif domain == "reading":
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["reading_skill_family_key"].astext.isnot(None)
            )
        if difficulty:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["difficulty_overall"].astext == difficulty
            )
        if grammar_role_key:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["grammar_role_key"].astext == grammar_role_key
            )
        if grammar_focus_key:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["grammar_focus_key"].astext == grammar_focus_key
            )
        if reading_skill_family_key:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["reading_skill_family_key"].astext
                == reading_skill_family_key
            )
        if reading_focus_key:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["reading_focus_key"].astext == reading_focus_key
            )

    return stmt


@router.get("/questions", response_model=StudentQuestionsListResponse)
async def student_recall(
    domain: Optional[str] = Query(None, description="Filter by domain: 'grammar' or 'reading'"),
    difficulty: Optional[str] = Query(None),
    grammar_role_key: Optional[str] = Query(None),
    grammar_focus_key: Optional[str] = Query(None),
    reading_skill_family_key: Optional[str] = Query(None),
    reading_focus_key: Optional[str] = Query(None),
    stimulus_mode_key: Optional[str] = Query(None),
    origin: Optional[str] = Query(None, description="'official', 'generated', or 'mixed' (default)"),
    exclude_seen: Optional[bool] = Query(None),
    user_token: Optional[str] = Query(None, description="Required for exclude_seen when student scope"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, str] = Depends(admin_or_student_required),
):
    scope, _ = auth
    settings = get_settings()
    threshold = settings.inventory_sufficient_threshold

    # Determine effective exclude_seen: default True for students, False for admins.
    effective_exclude_seen = exclude_seen if exclude_seen is not None else (scope == "student")

    base_stmt = _build_question_filter_stmt(
        domain=domain,
        difficulty=difficulty,
        grammar_role_key=grammar_role_key,
        grammar_focus_key=grammar_focus_key,
        reading_skill_family_key=reading_skill_family_key,
        reading_focus_key=reading_focus_key,
        stimulus_mode_key=stimulus_mode_key,
        origin=origin,
    )

    # Count total active matching questions before exclude_seen.
    count_total_result = await db.execute(
        select(func.count()).select_from(base_stmt.subquery())
    )
    matching_target_total = count_total_result.scalars().first() or 0

    # Build seen-exclusion subquery if requested.
    filtered_stmt = base_stmt
    if effective_exclude_seen and user_token:
        try:
            token_uuid = UUID(user_token)
        except ValueError:
            token_uuid = None

        if token_uuid is not None:
            user_result = await db.execute(
                select(User).where(User.user_token == token_uuid)
            )
            user = user_result.scalars().first()
            if user is not None:
                resurface_cutoff = datetime.now(timezone.utc) - timedelta(
                    days=settings.self_study_resurface_days
                )
                # Seen = correct answer (ever) OR wrong answer within the resurface window.
                seen_subq = (
                    select(UserProgress.question_id)
                    .where(UserProgress.user_id == user.id)
                    .where(
                        or_(
                            UserProgress.is_correct == True,  # noqa: E712
                            and_(
                                UserProgress.is_correct == False,  # noqa: E712
                                UserProgress.timestamp >= resurface_cutoff,
                            ),
                        )
                    )
                    .distinct()
                )
                filtered_stmt = base_stmt.where(Question.id.not_in(seen_subq))

    # Count unseen-active for inventory metadata.
    count_unseen_result = await db.execute(
        select(func.count()).select_from(filtered_stmt.subquery())
    )
    matching_unseen = count_unseen_result.scalars().first() or 0

    # Fetch questions with pagination.
    fetch_stmt = filtered_stmt.offset(offset).limit(limit)
    result = await db.execute(fetch_stmt)
    questions = result.unique().scalars().all()

    # Batch-load annotations and options to avoid N+1 queries.
    ann_ids = [q.latest_annotation_id for q in questions if q.latest_annotation_id]
    if ann_ids:
        ann_rows = await db.execute(
            select(QuestionAnnotation).where(QuestionAnnotation.id.in_(ann_ids))
        )
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
                    {"label": opt.option_label, "text": opt.option_text}
                )
    else:
        opts_by_qid = {}

    items = []
    includes_generated = False
    for q in questions:
        if q.content_origin == "generated":
            includes_generated = True
        ann = ann_map.get(q.latest_annotation_id) if q.latest_annotation_id else None
        ann_data = ann.annotation_jsonb if ann else {}
        items.append(StudentQuestionResponse(
            id=str(q.id),
            content_origin=q.content_origin,
            current_question_text=q.current_question_text,
            current_passage_text=q.current_passage_text,
            practice_status=q.practice_status,
            grammar_role_key=ann_data.get("grammar_role_key"),
            grammar_focus_key=ann_data.get("grammar_focus_key"),
            reading_skill_family_key=ann_data.get("reading_skill_family_key"),
            reading_focus_key=ann_data.get("reading_focus_key"),
            difficulty_overall=ann_data.get("difficulty_overall"),
            stimulus_mode_key=q.stimulus_mode_key,
            source_exam_code=q.source_exam_code,
            source_subject_code=q.source_subject_code,
            source_section_code=q.source_section_code,
            source_module_code=q.source_module_code,
            options=opts_by_qid.get(q.id, []),
        ))

    inventory = InventoryMetadata(
        matching_target_total=matching_target_total,
        matching_unseen=matching_unseen,
        served=len(items),
        includes_generated=includes_generated,
        below_threshold=matching_unseen < threshold,
        threshold=threshold,
    )

    return StudentQuestionsListResponse(items=items, inventory=inventory)


@router.post("/submit")
async def submit_answer(
    body: UserProgressCreate,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    try:
        qid = UUID(body.question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id")

    try:
        token_uuid = UUID(body.user_token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_token")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    if q.practice_status != "active":
        raise HTTPException(status_code=400, detail="Question is not active")

    # Verify the selected option exists for this question's current version
    option_result = await db.execute(
        select(QuestionOption).where(
            QuestionOption.question_id == qid,
            QuestionOption.question_version_id == q.latest_version_id,
            QuestionOption.option_label == body.selected_option_label,
        )
    )
    if not option_result.scalars().first():
        raise HTTPException(status_code=400, detail="Selected option not found for this question")

    result = await db.execute(select(User).where(User.user_token == token_uuid))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_correct = q.current_correct_option_label == body.selected_option_label

    progress = UserProgress(
        user_id=user.id,
        question_id=qid,
        is_correct=is_correct,
        selected_option_label=body.selected_option_label,
        missed_grammar_focus_key=body.missed_grammar_focus_key,
        missed_syntactic_trap_key=body.missed_syntactic_trap_key,
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return {"id": progress.id, "is_correct": progress.is_correct}


@router.get("/stats/{user_id}", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    result = await db.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    records = result.scalars().all()

    total = len(records)
    correct = sum(1 for r in records if r.is_correct)
    accuracy = correct / total if total > 0 else 0.0

    focus_counts = Counter(r.missed_grammar_focus_key for r in records if r.missed_grammar_focus_key and not r.is_correct)
    trap_counts = Counter(r.missed_syntactic_trap_key for r in records if r.missed_syntactic_trap_key and not r.is_correct)

    return UserStats(
        total_answered=total,
        total_correct=correct,
        accuracy=round(accuracy, 3),
        top_missed_focus_keys=[k for k, _ in focus_counts.most_common(5)],
        top_missed_trap_keys=[k for k, _ in trap_counts.most_common(5)],
    )
