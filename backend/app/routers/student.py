import asyncio
import logging
import math
import uuid as _uuid_module
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, or_, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config import get_settings
from app.database import get_db
from app.auth import student_required, admin_or_student_required
from app.models.db import (
    Question, User, UserProgress, QuestionAnnotation, QuestionOption,
    GenerationBatch, QuestionJob,
)
from app.models.payload import (
    StudentQuestionResponse,
    StudentQuestionsListResponse,
    InventoryMetadata,
    UserProgressCreate,
    UserStats,
    WeaknessTarget,
    StudyRecommendationsRequest,
    StudyRecommendationsResponse,
    StudyGenerationRequest,
    StudyGenerationResponse,
    StudyBatchStatusResponse,
    GenerationBatchRequest,
)
from app.models.ontology import GRAMMAR_FOCUS_BY_ROLE, READING_FOCUS_BY_SKILL_FAMILY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["student"])

_GRAMMAR_ROLE_BY_FOCUS = {
    focus: role
    for role, focus_keys in GRAMMAR_FOCUS_BY_ROLE.items()
    for focus in focus_keys
}

_READING_SKILL_FAMILY_BY_FOCUS = {
    focus: family
    for family, focus_keys in READING_FOCUS_BY_SKILL_FAMILY.items()
    for focus in focus_keys
}

_READING_TEST_CONSTRUCT_BY_FAMILY = {
    "command_of_evidence_textual": "evidence_relation_precision",
    "command_of_evidence_quantitative": "quantitative_constraint_tracking",
    "central_ideas_and_details": "evidence_relation_precision",
    "inferences": "inference_boundary_control",
    "words_in_context": "contextual_semantic_precision",
    "text_structure_and_purpose": "rhetorical_function_precision",
    "cross_text_connections": "cross_text_relationship_precision",
}

_READING_STEM_BY_FOCUS = {
    "evidence_supports_claim": "choose_best_support",
    "evidence_weakens_claim": "choose_best_weakener",
    "evidence_illustrates_claim": "choose_best_illustration",
    "evidence_explains_claim": "choose_command_of_evidence_textual",
    "evidence_qualifies_claim": "choose_command_of_evidence_textual",
    "data_supports_claim": "choose_command_of_evidence_quantitative",
    "data_weakens_claim": "choose_command_of_evidence_quantitative",
    "data_completes_example": "choose_best_completion_from_data",
    "data_comparison": "choose_command_of_evidence_quantitative",
    "data_trend": "choose_command_of_evidence_quantitative",
    "central_idea": "choose_main_idea",
    "main_purpose": "choose_main_purpose",
    "passage_summary": "choose_main_idea",
    "supporting_detail": "choose_detail",
    "character_or_author_detail": "choose_central_detail",
    "causal_inference": "choose_best_inference",
    "motivational_inference": "choose_best_inference",
    "implication_inference": "choose_best_inference",
    "predictive_inference": "choose_best_inference",
    "cross_text_inference": "choose_cross_text_connection",
    "contextual_meaning": "choose_words_in_context",
    "connotation_fit": "choose_words_in_context",
    "precision_fit": "choose_words_in_context",
    "register_fit": "choose_words_in_context",
    "underlined_word_meaning": "choose_word_in_context",
    "polarity_fit": "choose_words_in_context",
    "figurative_language_meaning": "choose_words_in_context",
    "overall_purpose": "choose_main_purpose",
    "sentence_function": "choose_sentence_function",
    "structural_pattern": "choose_structure_description",
    "author_stance": "choose_main_purpose",
    "text2_response_to_text1": "choose_cross_text_connection",
    "both_texts_agree": "choose_agreement_across_texts",
    "texts_disagree": "choose_difference_across_texts",
    "text2_qualifies_text1": "choose_text_relationship",
    "text2_contradicts_text1": "choose_text_relationship",
    "methodological_critique": "choose_text_relationship",
    "expectation_violation": "choose_text_relationship",
}

_READING_FOCUS_ALIASES = {
    "main_idea": "central_idea",
}

_READING_SKILL_FAMILIES = set(READING_FOCUS_BY_SKILL_FAMILY.keys())

_DRY_RUN_RELEASE_POLICY = "dry_run"


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

    # Auto-populate denormalized Phase 8 target fields from the question annotation.
    ann_data: dict = {}
    if q.latest_annotation_id:
        ann_result = await db.execute(
            select(QuestionAnnotation).where(QuestionAnnotation.id == q.latest_annotation_id)
        )
        ann = ann_result.scalars().first()
        if ann:
            ann_data = ann.annotation_jsonb or {}

    question_domain = (
        "reading" if ann_data.get("reading_skill_family_key") or ann_data.get("reading_focus_key")
        else ("grammar" if ann_data.get("grammar_role_key") or ann_data.get("grammar_focus_key") else None)
    )
    question_difficulty = ann_data.get("difficulty_overall")

    missed_reading_focus_key = (
        body.missed_reading_focus_key or ann_data.get("reading_focus_key")
        if question_domain == "reading" else None
    )
    missed_reading_skill_family_key = (
        body.missed_reading_skill_family_key
        or ann_data.get("reading_skill_family_key")
        or ann_data.get("skill_family_key")
        if question_domain == "reading" else None
    )

    progress = UserProgress(
        user_id=user.id,
        question_id=qid,
        is_correct=is_correct,
        selected_option_label=body.selected_option_label,
        missed_grammar_focus_key=body.missed_grammar_focus_key or ann_data.get("grammar_focus_key"),
        missed_syntactic_trap_key=body.missed_syntactic_trap_key,
        missed_reading_focus_key=missed_reading_focus_key,
        missed_reading_skill_family_key=missed_reading_skill_family_key,
        question_domain=question_domain,
        question_difficulty=question_difficulty,
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


# ---------------------------------------------------------------------------
# Phase 8: Self-study agent helpers
# ---------------------------------------------------------------------------

def _weakness_score(miss_count: int, attempt_count: int, days_since_last: float) -> float:
    """Compute the weakness score for one target bucket."""
    if attempt_count == 0:
        return 0.0
    miss_rate = miss_count / attempt_count
    recency_weight = math.exp(-days_since_last / 14.0)
    volume_floor = math.sqrt(attempt_count)
    return miss_rate * recency_weight * volume_floor


async def _resolve_user_by_token(user_token: str, db: AsyncSession) -> User:
    """Raise 400/404 if user_token is invalid or not found."""
    try:
        token_uuid = UUID(user_token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_token")
    result = await db.execute(select(User).where(User.user_token == token_uuid))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _compute_weakness_targets(
    user: User,
    db: AsyncSession,
    settings,
) -> list[WeaknessTarget]:
    """Compute the top-K weakness targets from the student's recent progress.

    Only UserProgress rows with a denormalized `question_domain` (populated
    at Phase 8 submit time) contribute. Historical rows without it are skipped
    gracefully.
    """
    lookback_cutoff = datetime.now(timezone.utc) - timedelta(
        days=settings.self_study_lookback_days
    )
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.timestamp >= lookback_cutoff,
            UserProgress.question_domain.isnot(None),
        )
    )
    records = result.scalars().all()

    # Build buckets keyed by (domain, focus_key, difficulty).
    # For grammar: focus_key = missed_grammar_focus_key
    # For reading: focus_key = missed_reading_focus_key
    BucketKey = tuple  # (domain, focus_key, difficulty)
    buckets: dict[BucketKey, dict] = defaultdict(lambda: {
        "miss_count": 0,
        "attempt_count": 0,
        "last_timestamp": None,
        "grammar_role_key": None,
        "skill_family_key": None,
    })

    for r in records:
        domain = r.question_domain
        difficulty = r.question_difficulty or "medium"
        if domain == "grammar":
            focus_key = r.missed_grammar_focus_key
        elif domain == "reading":
            focus_key = r.missed_reading_focus_key
        else:
            continue
        if not focus_key:
            continue

        key: BucketKey = (domain, focus_key, difficulty)
        bucket = buckets[key]
        bucket["attempt_count"] += 1
        if not r.is_correct:
            bucket["miss_count"] += 1
        ts = r.timestamp
        if ts and (bucket["last_timestamp"] is None or ts > bucket["last_timestamp"]):
            bucket["last_timestamp"] = ts
        if domain == "reading" and r.missed_reading_skill_family_key:
            bucket["skill_family_key"] = r.missed_reading_skill_family_key

    min_attempts = settings.self_study_min_attempts_per_target

    scored: list[tuple[float, BucketKey, dict]] = []
    for key, bucket in buckets.items():
        if bucket["attempt_count"] < min_attempts:
            continue
        last_ts = bucket["last_timestamp"]
        if last_ts is None:
            days_since = float(settings.self_study_lookback_days)
        else:
            days_since = max(0.0, (now - last_ts).total_seconds() / 86400.0)
        score = _weakness_score(
            bucket["miss_count"], bucket["attempt_count"], days_since
        )
        scored.append((score, key, bucket, days_since))

    # Sort descending by weakness score.
    scored.sort(key=lambda x: x[0], reverse=True)

    # Apply top-K and at-most-2-same-focus-key constraint.
    top_k = settings.self_study_top_k
    focus_key_count: dict[str, int] = defaultdict(int)
    targets: list[WeaknessTarget] = []

    for score, key, bucket, days_since in scored:
        if len(targets) >= top_k:
            break
        domain, focus_key, difficulty = key
        if focus_key_count[focus_key] >= 2:
            continue

        miss_count = bucket["miss_count"]
        attempt_count = bucket["attempt_count"]
        miss_rate = miss_count / attempt_count if attempt_count else 0.0

        targets.append(WeaknessTarget(
            domain=domain,
            focus_key=focus_key,
            skill_family_key=bucket.get("skill_family_key"),
            grammar_role_key=None,  # not tracked; the generator will select
            difficulty=difficulty,
            weakness_score=round(score, 4),
            miss_count=miss_count,
            attempt_count=attempt_count,
            miss_rate=round(miss_rate, 4),
            days_since_last_attempt=round(days_since, 2),
            inventory_unseen=0,  # filled in by caller
            inventory_below_threshold=True,  # filled in by caller
        ))
        focus_key_count[focus_key] += 1

    return targets


async def _inventory_for_target(
    user: User,
    target: WeaknessTarget,
    db: AsyncSession,
    settings,
) -> tuple[int, bool]:
    """Return (unseen_count, below_threshold) for a weakness target."""
    threshold = settings.inventory_sufficient_threshold

    # Build active-question filter for this target.
    stmt = select(Question).where(Question.practice_status == "active")

    if target.domain == "grammar":
        stmt = stmt.join(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
        ).where(
            QuestionAnnotation.annotation_jsonb["grammar_focus_key"].astext == target.focus_key,
            QuestionAnnotation.annotation_jsonb["difficulty_overall"].astext == target.difficulty,
        )
    else:
        stmt = stmt.join(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
        ).where(
            QuestionAnnotation.annotation_jsonb["reading_focus_key"].astext == target.focus_key,
            QuestionAnnotation.annotation_jsonb["difficulty_overall"].astext == target.difficulty,
        )

    # Exclude seen questions (all-time correct; wrong within resurface window).
    resurface_cutoff = datetime.now(timezone.utc) - timedelta(
        days=settings.self_study_resurface_days
    )
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
    stmt = stmt.where(Question.id.not_in(seen_subq))

    count_result = await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )
    unseen = count_result.scalars().first() or 0
    return unseen, unseen < threshold


async def _pending_batch_exists_for_target(
    user: User,
    target: WeaknessTarget,
    db: AsyncSession,
) -> bool:
    """True if a live (non-terminal) batch for this student+target already exists."""
    pending_statuses = ("pending", "generating", "reviewing", "admin_review_ready")
    focus_json_key = (
        "target_grammar_focus_key"
        if target.domain == "grammar"
        else "target_reading_focus_key"
    )
    result = await db.execute(
        select(GenerationBatch).where(
            GenerationBatch.student_id == user.id,
            GenerationBatch.status.in_(pending_statuses),
            GenerationBatch.request_jsonb[focus_json_key].astext == target.focus_key,
        )
    )
    return result.scalars().first() is not None


async def _target_on_cooldown(
    user: User,
    target: WeaknessTarget,
    settings,
    db: AsyncSession,
) -> bool:
    """True if a batch for this target was created within the cooldown window."""
    cooldown_cutoff = datetime.now(timezone.utc) - timedelta(
        hours=settings.self_study_target_cooldown_hours
    )
    focus_json_key = (
        "target_grammar_focus_key"
        if target.domain == "grammar"
        else "target_reading_focus_key"
    )
    result = await db.execute(
        select(GenerationBatch).where(
            GenerationBatch.student_id == user.id,
            GenerationBatch.created_at >= cooldown_cutoff,
            GenerationBatch.request_jsonb[focus_json_key].astext == target.focus_key,
        )
    )
    return result.scalars().first() is not None


async def _daily_gen_count(user: User, db: AsyncSession) -> int:
    """Count questions generated for this student today (UTC)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.sum(
            GenerationBatch.requested_count
        )).where(
            GenerationBatch.student_id == user.id,
            GenerationBatch.created_at >= today_start,
            GenerationBatch.requested_by == "self_study_agent",
        )
    )
    return result.scalars().first() or 0


async def _pending_batch_count(user: User, db: AsyncSession) -> int:
    """Count non-terminal batches for this student."""
    pending_statuses = ("pending", "generating", "reviewing", "admin_review_ready")
    result = await db.execute(
        select(func.count()).where(
            GenerationBatch.student_id == user.id,
            GenerationBatch.status.in_(pending_statuses),
            GenerationBatch.requested_by == "self_study_agent",
        )
    )
    return result.scalars().first() or 0


def _self_study_generation_request_payload(
    target: WeaknessTarget,
    requested_count: int,
) -> dict[str, Any]:
    """Build a strict GenerationBatchRequest-compatible payload."""
    if target.domain == "grammar":
        grammar_role = (
            target.grammar_role_key
            or _GRAMMAR_ROLE_BY_FOCUS.get(target.focus_key)
            or "expression_of_ideas"
        )
        payload: dict[str, Any] = {
            "requested_count": requested_count,
            "release_policy": "admin_review_required",
            "difficulty_overall": target.difficulty,
            "target_grammar_role_key": grammar_role,
            "target_grammar_focus_key": target.focus_key,
            "target_syntactic_trap_key": "none",
            "target_frequency_band": "medium",
            "test_format_key": "digital_app_adaptive",
            "stimulus_mode_key": "sentence_only",
            "stem_type_key": "complete_the_text",
        }
        if target.focus_key == "transition_logic":
            payload.update({
                "target_transition_subtype_key": "contrast",
                "distractor_transition_subtypes": ["cause_effect", "addition", "sequence"],
            })
        if target.focus_key == "choose_best_notes_synthesis":
            payload.update({
                "stem_type_key": "choose_best_notes_synthesis",
                "target_synthesis_goal_key": "emphasize_shared_conclusion",
                "target_audience_knowledge_key": "general_reader",
                "target_required_content_key": "include_relevant_note",
                "distractor_synthesis_failures": [
                    "irrelevant_detail",
                    "misstates_goal",
                    "omits_required_content",
                ],
            })
        return payload

    reading_focus = _READING_FOCUS_ALIASES.get(target.focus_key, target.focus_key)
    target_skill_family = (
        target.skill_family_key
        if target.skill_family_key in _READING_SKILL_FAMILIES
        else None
    )
    skill_family = (
        target_skill_family
        or _READING_SKILL_FAMILY_BY_FOCUS.get(reading_focus)
        or "central_ideas_and_details"
    )
    payload = {
        "requested_count": requested_count,
        "release_policy": "admin_review_required",
        "difficulty_overall": target.difficulty,
        "target_skill_family_key": skill_family,
        "target_reading_skill_family_key": skill_family,
        "target_reading_focus_key": reading_focus,
        "target_test_construct_key": _READING_TEST_CONSTRUCT_BY_FAMILY.get(
            skill_family,
            "evidence_relation_precision",
        ),
        "target_reasoning_trap_key": "topical_relevance_without_logical_connection",
        "target_distractor_pattern": ["too_broad", "too_narrow", "unsupported"],
        "passage_structure_pattern": "research_summary",
        "stimulus_mode_key": "prose_single",
        "stem_type_key": _READING_STEM_BY_FOCUS.get(reading_focus, "choose_best_support"),
    }
    if reading_focus == "polarity_fit":
        payload["polarity_context"] = "contrast_or_negation"
    if reading_focus == "sentence_function":
        payload["target_sentence_function_role"] = "local_rhetorical_function"
    if skill_family == "command_of_evidence_quantitative":
        payload["quantitative_sub_pattern"] = "standard"
        payload["stimulus_mode_key"] = "table_or_graph"
    if reading_focus == "evidence_illustrates_claim":
        payload["two_part_claim"] = False
    return payload


def _row_int(row: Any, *names: str) -> int:
    for name in names:
        value = getattr(row, name, None)
        if value is not None:
            return int(value)
    try:
        index = 0 if not names or names[0].endswith("accepted") else 1
        value = row[index]
    except (TypeError, KeyError, IndexError):
        value = None
    if value is not None:
        return int(value)
    return 0


async def _batch_decision_counts(batch: GenerationBatch, db: AsyncSession) -> tuple[int, int]:
    """Return accepted/rejected counts from persisted generated questions.

    Old tests and historical batches may only expose frozen batch counters;
    keep that fallback when no batch id is available.
    """
    batch_id = getattr(batch, "id", None)
    if batch_id is None:
        return (
            int(getattr(batch, "accepted_count", 0) or 0),
            int(getattr(batch, "rejected_count", 0) or 0),
        )

    result = await db.execute(
        select(
            func.sum(case((Question.practice_status == "active", 1), else_=0)).label("accepted"),
            func.sum(case((Question.practice_status == "rejected", 1), else_=0)).label("rejected"),
        )
        .select_from(QuestionJob)
        .join(Question, Question.id == QuestionJob.question_id)
        .where(
            QuestionJob.generation_batch_id == batch_id,
            Question.content_origin == "generated",
        )
    )
    row = result.first()
    if row is None:
        return 0, 0
    return _row_int(row, "accepted"), _row_int(row, "rejected")


async def _on_quality_cooldown(user: User, settings, db: AsyncSession) -> bool:
    """True if >=2 of the last 3 completed self-study batches had reject_rate >= 0.5."""
    result = await db.execute(
        select(GenerationBatch)
        .where(
            GenerationBatch.student_id == user.id,
            GenerationBatch.requested_by == "self_study_agent",
            GenerationBatch.status == "completed",
        )
        .order_by(GenerationBatch.created_at.desc())
        .limit(3)
    )
    recent = result.scalars().all()
    if len(recent) < 2:
        return False

    poor_count = 0
    for batch in recent:
        accepted_count, rejected_count = await _batch_decision_counts(batch, db)
        total = accepted_count + rejected_count
        if total > 0 and rejected_count / total >= 0.5:
            poor_count += 1

    return poor_count >= 2


async def _create_self_study_batch(
    user: User,
    target: WeaknessTarget,
    requested_count: int,
    settings,
    db: AsyncSession,
) -> str:
    """Create a GenerationBatch + QuestionJobs for the self-study target.

    Returns the new batch ID. Forces release_policy='admin_review_required'.
    Kicks off the batch pipeline in the background.
    """
    # Lazy import to avoid circular dependency at module level.
    from app.routers.generate import (
        _domain_for_batch,
        _run_batch_pipeline,
        _select_source_question_ids_for_batch,
    )
    from app.job_limits import run_with_job_limit

    now = datetime.now(timezone.utc)
    batch_id = _uuid_module.uuid4()

    request_payload = _self_study_generation_request_payload(target, requested_count)
    batch_request = GenerationBatchRequest.model_validate(request_payload)
    domain = _domain_for_batch(batch_request)
    selected_source_ids = await _select_source_question_ids_for_batch(
        db,
        batch_request,
        domain,
        [],
    )

    request_jsonb = batch_request.model_dump()
    request_jsonb.update({
        "requested_by": "self_study_agent",
        "student_id": user.id,
        "requested_by_user_token": str(user.user_token),
    })

    batch = GenerationBatch(
        id=batch_id,
        requested_count=requested_count,
        request_jsonb=request_jsonb,
        requested_by="self_study_agent",
        student_id=user.id,
        requested_by_user_token=user.user_token,
        release_policy=batch_request.release_policy,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(batch)
    await db.flush()

    # Create one QuestionJob per requested question.
    provider_name = settings.default_annotation_provider
    model_name = settings.default_annotation_model

    job_ids = []
    for job_index in range(requested_count):
        job_id = _uuid_module.uuid4()
        job_request = {
            **request_jsonb,
            "source_question_ids": (
                selected_source_ids[job_index]
                if job_index < len(selected_source_ids)
                else []
            ),
            "provider_name": provider_name,
            "model_name": model_name,
            "seed": job_id.int % 2_147_483_647,
            "temperature": 0.7,
            "retry_attempt": 0,
        }
        job_request.pop("requested_count", None)
        job = QuestionJob(
            id=job_id,
            job_type="generate",
            content_origin="generated",
            input_format="spec",
            status="pending",
            provider_name=provider_name,
            model_name=model_name,
            prompt_version="v3.0",
            rules_version=settings.rules_version,
            generation_batch_id=batch_id,
            generation_request_jsonb=job_request,
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        job_ids.append(job_id)

    await db.commit()

    # Kick off the batch pipeline in a background task.
    def _log_task_exception(task: asyncio.Task) -> None:
        if not task.cancelled() and task.exception():
            logger.error(
                "Self-study batch pipeline failed (batch %s)",
                batch_id,
                exc_info=task.exception(),
            )

    asyncio.create_task(
        run_with_job_limit(lambda bid=batch_id: _run_batch_pipeline(bid))
    ).add_done_callback(_log_task_exception)

    return str(batch_id)


async def _fetch_pool_questions(
    user: User,
    target: WeaknessTarget,
    limit: int,
    db: AsyncSession,
    settings,
) -> list[StudentQuestionResponse]:
    """Fetch active unseen questions for a target (student-facing, no answer key)."""
    stmt = _build_question_filter_stmt(
        domain=target.domain,
        difficulty=target.difficulty,
        grammar_role_key=None,
        grammar_focus_key=target.focus_key if target.domain == "grammar" else None,
        reading_skill_family_key=target.skill_family_key if target.domain == "reading" else None,
        reading_focus_key=target.focus_key if target.domain == "reading" else None,
        stimulus_mode_key=None,
        origin=None,
    )

    resurface_cutoff = datetime.now(timezone.utc) - timedelta(
        days=settings.self_study_resurface_days
    )
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
    stmt = stmt.where(Question.id.not_in(seen_subq)).limit(limit)

    result = await db.execute(stmt)
    questions = result.unique().scalars().all()

    ann_ids = [q.latest_annotation_id for q in questions if q.latest_annotation_id]
    ann_map = {}
    if ann_ids:
        ann_rows = await db.execute(
            select(QuestionAnnotation).where(QuestionAnnotation.id.in_(ann_ids))
        )
        ann_map = {a.id: a for a in ann_rows.scalars().all()}

    items = []
    for q in questions:
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
            options=[],  # Loaded separately if needed; omit here for speed.
        ))
    return items


# ---------------------------------------------------------------------------
# Phase 8: Study endpoints
# ---------------------------------------------------------------------------


@router.post("/study/recommendations", response_model=StudyRecommendationsResponse)
async def study_recommendations(
    body: StudyRecommendationsRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Compute a student's weakness profile and return the top-K target recommendations.

    Does NOT create generation batches or trigger any LLM calls. Safe to call
    repeatedly as a read-only weakness-profile probe.
    """
    settings = get_settings()
    user = await _resolve_user_by_token(body.user_token, db)
    targets = await _compute_weakness_targets(user, db, settings)

    # Enrich each target with live inventory data.
    for target in targets:
        unseen, below = await _inventory_for_target(user, target, db, settings)
        target.inventory_unseen = unseen
        target.inventory_below_threshold = below

    return StudyRecommendationsResponse(
        user_id=user.id,
        top_targets=targets,
        threshold=settings.inventory_sufficient_threshold,
    )


@router.post("/study/generation-requests", response_model=StudyGenerationResponse)
async def study_generation_request(
    body: StudyGenerationRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Self-study agent main entry point.

    Computes the weakness profile, checks active inventory per target, serves
    existing pool questions, and creates generation batches only when inventory
    is low and all rate caps allow. Forced to admin_review_required regardless
    of any future caller-supplied policy.
    """
    settings = get_settings()
    user = await _resolve_user_by_token(body.user_token, db)
    targets = await _compute_weakness_targets(user, db, settings)

    # Cap checks shared across all targets in this call.
    daily_gen = await _daily_gen_count(user, db)
    pending_batches = await _pending_batch_count(user, db)
    quality_cooldown = await _on_quality_cooldown(user, settings, db)

    new_batch_ids: list[str] = []
    skip_reasons: dict[str, str] = {}
    all_questions: list[StudentQuestionResponse] = []
    seen_question_ids: set = set()
    includes_generated = False
    targets_with_new_batch = 0

    # Limit questions served per target to avoid bloat.
    _PER_TARGET_SERVE_LIMIT = 5

    for target in targets:
        unseen, below_threshold = await _inventory_for_target(user, target, db, settings)
        target.inventory_unseen = unseen
        target.inventory_below_threshold = below_threshold

        # Serve existing pool questions for this target.
        pool_qs = await _fetch_pool_questions(
            user, target, _PER_TARGET_SERVE_LIMIT, db, settings
        )
        for q in pool_qs:
            if q.id not in seen_question_ids:
                seen_question_ids.add(q.id)
                all_questions.append(q)
                if q.content_origin == "generated":
                    includes_generated = True

        if not below_threshold:
            continue  # Sufficient inventory — no generation needed.

        # Check whether a batch for this target is already pending.
        if await _pending_batch_exists_for_target(user, target, db):
            skip_reasons[f"{target.domain}:{target.focus_key}:{target.difficulty}"] = (
                "pending_batch_exists"
            )
            continue

        # Rate/quality caps.
        target_key = f"{target.domain}:{target.focus_key}:{target.difficulty}"
        if quality_cooldown:
            skip_reasons[target_key] = "quality_cooldown"
            continue
        if pending_batches >= settings.self_study_max_pending_batches_per_student:
            skip_reasons[target_key] = "max_pending_batches"
            continue
        if daily_gen >= settings.self_study_gen_per_student_per_day:
            skip_reasons[target_key] = "daily_cap_reached"
            continue
        if await _target_on_cooldown(user, target, settings, db):
            skip_reasons[target_key] = "target_cooldown"
            continue

        # Check pending questions in flight for this target.
        focus_json_key = (
            "target_grammar_focus_key"
            if target.domain == "grammar"
            else "target_reading_focus_key"
        )
        pending_q_result = await db.execute(
            select(func.sum(GenerationBatch.requested_count)).where(
                GenerationBatch.student_id == user.id,
                GenerationBatch.status.in_(
                    ("pending", "generating", "reviewing", "admin_review_ready")
                ),
                GenerationBatch.request_jsonb[focus_json_key].astext == target.focus_key,
            )
        )
        pending_for_target = pending_q_result.scalars().first() or 0
        if pending_for_target >= settings.self_study_max_pending_per_target:
            skip_reasons[target_key] = "max_pending_per_target"
            continue

        # How many questions to generate.
        threshold = settings.inventory_sufficient_threshold
        requested = max(
            settings.self_study_min_gen_batch_size,
            threshold - unseen,
        )
        # Clamp so we don't blow the daily cap.
        remaining_daily = settings.self_study_gen_per_student_per_day - daily_gen
        requested = min(requested, remaining_daily)
        if requested <= 0:
            skip_reasons[target_key] = "daily_cap_reached"
            continue

        batch_id = await _create_self_study_batch(user, target, requested, settings, db)
        new_batch_ids.append(batch_id)
        targets_with_new_batch += 1
        daily_gen += requested
        pending_batches += 1

    inventory = InventoryMetadata(
        matching_target_total=sum(t.inventory_unseen + (1 if not t.inventory_below_threshold else 0) for t in targets),
        matching_unseen=len(all_questions),
        served=len(all_questions),
        includes_generated=includes_generated,
        below_threshold=all(t.inventory_below_threshold for t in targets) if targets else True,
        threshold=settings.inventory_sufficient_threshold,
    )

    return StudyGenerationResponse(
        user_id=user.id,
        questions=all_questions,
        inventory=inventory,
        new_batch_ids=new_batch_ids,
        targets_analyzed=len(targets),
        targets_with_new_batch=targets_with_new_batch,
        skip_reasons=skip_reasons,
    )


@router.get("/study/generation-requests/{batch_id}", response_model=StudyBatchStatusResponse)
async def get_study_batch_status(
    batch_id: str,
    user_token: str = Query(..., description="Student user token for ownership verification"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return status of a self-study generation batch.

    Only the student who created the batch can view it.
    """
    try:
        bid = UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch_id")

    user = await _resolve_user_by_token(user_token, db)

    result = await db.execute(
        select(GenerationBatch).where(GenerationBatch.id == bid)
    )
    batch = result.scalars().first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Students can only see their own batches.
    if batch.student_id != user.id:
        raise HTTPException(status_code=403, detail="Batch does not belong to this student")

    return StudyBatchStatusResponse(
        batch_id=str(batch.id),
        status=batch.status,
        requested_count=batch.requested_count,
        created_count=batch.created_count or 0,
        accepted_count=batch.accepted_count or 0,
        rejected_count=batch.rejected_count or 0,
        failed_count=batch.failed_count or 0,
        needs_review_count=batch.needs_review_count or 0,
        release_policy=batch.release_policy,
        requested_by=batch.requested_by,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )
