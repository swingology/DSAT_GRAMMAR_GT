import asyncio
import logging
import math
import uuid as _uuid_module
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, or_, text, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config import get_settings
from app.database import get_db
from app.diagnostic.queries import derive_domain
from app.diagnostic.selector import DiagnosticBankExhaustedError, assemble_diagnostic
from app.diagnostic.blueprint import BLUEPRINT_V1
from app.auth import student_required, admin_or_student_required, student_jwt_required, admin_or_student_jwt_required
from app.models.db import (
    Question, User, UserProgress, QuestionAnnotation, QuestionOption, TestSessionResults,
    GenerationBatch, QuestionJob, DiagnosticSession, SpacedRepetitionState,
)
from app.models.payload import (
    StudentQuestionResponse,
    StudentQuestionsListResponse,
    InventoryMetadata,
    UserProgressCreate,
    UserStats,
    ActivityDayCount,
    WeaknessTarget,
    StudyRecommendationsRequest,
    StudyRecommendationsResponse,
    StudyGenerationRequest,
    StudyGenerationResponse,
    StudyBatchStatusResponse,
    GenerationBatchRequest,
    MissedQuestionItem,
    MissedQuestionsResponse,
    DiagnosticSessionStartRequest,
    DiagnosticSessionStartResponse,
    DiagnosticStartV1Request,
    DiagnosticStartV1Response,
    DiagnosticQuestionPayload,
    DiagnosticOptionPayload,
    CorrectTotal,
    DiagnosticBreakdown,
    DiagnosticAnswerRequest,
    DiagnosticAnswerResponse,
    DiagnosticSessionResult,
    DiagnosticHistoryItem,
    DiagnosticHistoryResponse,
    DiagnosticQuestionResult,
    DiagnosticSessionDetailResponse,
    SRReviewRequest,
    SRReviewResponse,
    SRDueQuestion,
    SRDueQuestionsResponse,
    SRProgressResponse,
    TrapMetric,
    TrapImprovement,
    TrapSusceptibilityResponse,
    QuestionTypeMetric,
    QuestionTypePerformanceResponse,
    TrapDetailExample,
    TrapDetailResponse,
    DailyAccuracyPoint,
    ProgressTrendResponse,
    DomainTrendResponse,
    FocusAreaStat,
    FocusSummaryResponse,
    Module1CompleteRequest,
    Module1CompleteResponse,
    Module2BlueprintResponse,
    Module2BlueprintQuestion,
    TestSessionHistoryItem,
    TestSessionHistoryResponse,
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


def _unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        value = value.strip()
        if not value or value == "none" or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _annotation_highlight_tags(ann_data: dict[str, Any]) -> list[str]:
    values: list[Any] = [
        ann_data.get("grammar_role_key"),
        ann_data.get("grammar_focus_key"),
        ann_data.get("syntactic_trap_key"),
    ]
    secondary_focus = ann_data.get("secondary_grammar_focus_keys")
    if isinstance(secondary_focus, list):
        values.extend(secondary_focus)
    return _unique_strings(values)


def _find_span(passage: str, span: str) -> tuple[int, int] | None:
    span = span.strip()
    if not span:
        return None

    start = passage.find(span)
    if start == -1:
        start = passage.lower().find(span.lower())
    if start == -1:
        return None
    return start, start + len(span)


def _fallback_passage_tokens(
    question: Question,
    ann_data: dict[str, Any],
    annotation: "QuestionAnnotation | None" = None,
) -> list[dict[str, Any]] | None:
    """Build minimal student highlight tokens when Pass 2 did not provide them."""
    # Step 0: prefer stored passage_spans — word-level, anatomy + concept_tags
    if annotation is not None and annotation.passage_spans:
        tokens = annotation.passage_spans.get("tokens", [])
        if tokens:
            result = []
            for t in tokens:
                merged_tags = list(t.get("anatomy", [])) + list(t.get("concept_tags", []))
                result.append({
                    "text":         t["text"],
                    "tags":         merged_tags,
                    "anatomy":      t.get("anatomy", []),
                    "concept_tags": t.get("concept_tags", []),
                    "is_blank":     t.get("is_blank", False),
                })
            return result

    passage_tokens = ann_data.get("passage_tokens")
    if isinstance(passage_tokens, list) and passage_tokens:
        return passage_tokens

    passage = getattr(question, "current_passage_text", None)
    if not passage:
        return passage_tokens if isinstance(passage_tokens, list) else None

    tags = _annotation_highlight_tags(ann_data)
    if not tags:
        return passage_tokens if isinstance(passage_tokens, list) else None

    span_candidates = [
        getattr(question, "current_underlined_text", None),
        ann_data.get("evidence_span_text"),
    ]
    for candidate in span_candidates:
        if not isinstance(candidate, str):
            continue
        match = _find_span(passage, candidate)
        if not match:
            continue
        start, end = match
        tokens: list[dict[str, Any]] = []
        if start > 0:
            tokens.append({"text": passage[:start], "tags": []})
        tokens.append({"text": passage[start:end], "tags": tags})
        if end < len(passage):
            tokens.append({"text": passage[end:], "tags": []})
        return tokens

    return [{"text": passage, "tags": tags}]


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
    source_release_year: Optional[int] = None,
    source_test_name: Optional[str] = None,
    source_exam_code: Optional[str] = None,
    sort_by_source: bool = False,
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

    if source_release_year is not None:
        stmt = stmt.where(Question.source_release_year == source_release_year)
    if source_test_name:
        stmt = stmt.where(Question.source_test_name == source_test_name)
    if source_exam_code:
        stmt = stmt.where(Question.source_exam_code == source_exam_code)

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
                QuestionAnnotation.annotation_jsonb["skill_family_key"].astext.isnot(None)
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
                QuestionAnnotation.annotation_jsonb["skill_family_key"].astext
                == reading_skill_family_key
            )
        if reading_focus_key:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["reading_focus_key"].astext == reading_focus_key
            )

    if sort_by_source:
        stmt = stmt.order_by(
            Question.source_release_year.asc().nullslast(),
            Question.source_test_name.asc().nullslast(),
            Question.source_exam_code.asc().nullslast(),
            Question.source_subject_code.asc().nullslast(),
            Question.source_section_code.asc().nullslast(),
            Question.source_module_code.asc().nullslast(),
            Question.source_question_number.asc().nullslast(),
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
    source_release_year: Optional[int] = Query(None),
    source_test_name: Optional[str] = Query(None),
    source_exam_code: Optional[str] = Query(None),
    sort_by_source: bool = Query(False, description="Sort by release/test/exam/module/question order"),
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
        source_release_year=source_release_year,
        source_test_name=source_test_name,
        source_exam_code=source_exam_code,
        sort_by_source=sort_by_source,
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
                opts_by_qid.setdefault(qid, []).append(opt)
    else:
        opts_by_qid = {}

    items = []
    includes_generated = False
    for q in questions:
        if q.content_origin == "generated":
            includes_generated = True
        ann = ann_map.get(q.latest_annotation_id) if q.latest_annotation_id else None
        ann_data = ann.annotation_jsonb if ann else {}

        # Merge per-option annotation data (distractor analysis) keyed by option_label.
        # Omit distractor_type_key=="correct" so the answer is not revealed before submission.
        ann_opts = {o["option_label"]: o for o in ann_data.get("options", []) if isinstance(o, dict) and "option_label" in o}
        enriched_options = []
        for opt in opts_by_qid.get(q.id, []):
            ao = ann_opts.get(opt.option_label, {})
            d_key = ao.get("distractor_type_key")
            enriched_options.append({
                "label": opt.option_label,
                "text": opt.option_text,
                "distractor_type_key": d_key if d_key and d_key != "correct" else None,
                "why_wrong": ao.get("why_wrong") or None,
                "why_plausible": ao.get("why_plausible") or None,
            })

        items.append(StudentQuestionResponse(
            id=str(q.id),
            content_origin=q.content_origin,
            current_question_text=q.current_question_text,
            current_passage_text=q.current_passage_text,
            passage_tokens=_fallback_passage_tokens(q, ann_data, annotation=ann),
            passage_spans={
                "label":            ann.passage_spans.get("label"),
                "anatomy_present":  ann.passage_spans.get("anatomy_present", []),
                "concepts_present": ann.passage_spans.get("concepts_present", []),
            } if ann is not None and ann.passage_spans else None,
            practice_status=q.practice_status,
            grammar_role_key=ann_data.get("grammar_role_key"),
            grammar_focus_key=ann_data.get("grammar_focus_key"),
            syntactic_trap_key=ann_data.get("syntactic_trap_key"),
            skill_family_key=ann_data.get("skill_family_key"),
            reading_focus_key=ann_data.get("reading_focus_key"),
            difficulty_overall=ann_data.get("difficulty_overall"),
            stimulus_mode_key=q.stimulus_mode_key,
            source_release_year=q.source_release_year,
            source_test_name=q.source_test_name,
            source_exam_code=q.source_exam_code,
            source_subject_code=q.source_subject_code,
            source_section_code=q.source_section_code,
            source_module_code=q.source_module_code,
            options=enriched_options,
            source_question_number=q.source_question_number,
            question_family_key=ann_data.get("question_family_key"),
            reasoning_trap_key=ann_data.get("reasoning_trap_key"),
            explanation_short=ann_data.get("explanation_short"),
            solver_pattern_key=ann_data.get("solver_pattern_key"),
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

    # bug-761: the v8 bank classifies reading via skill_family_key (singular);
    # reading_skill_family_key/reading_focus_key are NULL, so derive_domain reads
    # the keys the bank actually populates.
    question_domain = derive_domain(ann_data)
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
        source_type=body.source_type or "unknown",
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
    return {
        "id": progress.id,
        "is_correct": progress.is_correct,
        "correct_option_label": q.current_correct_option_label,
    }


@router.get("/stats/{user_id}", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_or_student_required),
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


@router.get("/stats/{user_id}/activity", response_model=list[ActivityDayCount])
async def get_user_activity(
    user_id: int,
    days: int = Query(365, ge=1, le=400),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_or_student_required),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            cast(UserProgress.timestamp, Date).label("day"),
            func.count().label("count"),
        )
        .where(UserProgress.user_id == user_id, UserProgress.timestamp >= cutoff)
        .group_by(cast(UserProgress.timestamp, Date))
        .order_by(cast(UserProgress.timestamp, Date))
    )
    return [
        ActivityDayCount(date=row.day.isoformat(), count=row.count)
        for row in result.all()
    ]


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
            prompt_version="v8.0",
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
        source_release_year=None,
        source_test_name=None,
        source_exam_code=None,
        sort_by_source=False,
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
            passage_tokens=_fallback_passage_tokens(q, ann_data, annotation=ann),
            passage_spans={
                "label":            ann.passage_spans.get("label"),
                "anatomy_present":  ann.passage_spans.get("anatomy_present", []),
                "concepts_present": ann.passage_spans.get("concepts_present", []),
            } if ann is not None and ann.passage_spans else None,
            practice_status=q.practice_status,
            grammar_role_key=ann_data.get("grammar_role_key"),
            grammar_focus_key=ann_data.get("grammar_focus_key"),
            syntactic_trap_key=ann_data.get("syntactic_trap_key"),
            skill_family_key=ann_data.get("skill_family_key"),
            reading_focus_key=ann_data.get("reading_focus_key"),
            difficulty_overall=ann_data.get("difficulty_overall"),
            stimulus_mode_key=q.stimulus_mode_key,
            source_release_year=q.source_release_year,
            source_test_name=q.source_test_name,
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


@router.get("/study/missed", response_model=MissedQuestionsResponse)
async def get_missed_questions(
    user_token: str = Query(..., description="Student user token"),
    domain: Optional[str] = Query(None, description="Filter by domain: 'grammar' or 'reading'"),
    sort_by: str = Query("date", description="Sort field: 'date', 'miss_count', or 'domain'"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return questions the student has missed, grouped by question with miss counts."""
    user = await _resolve_user_by_token(user_token, db)

    stmt = (
        select(
            UserProgress.question_id,
            func.count(UserProgress.id).label("miss_count"),
            func.max(UserProgress.timestamp).label("last_missed_at"),
            func.max(UserProgress.missed_grammar_focus_key).label("focus_key_grammar"),
            func.max(UserProgress.missed_reading_focus_key).label("focus_key_reading"),
            func.max(UserProgress.question_domain).label("question_domain"),
            func.max(UserProgress.question_difficulty).label("question_difficulty"),
            func.max(UserProgress.selected_option_label).label("last_selected"),
        )
        .where(
            UserProgress.user_id == user.id,
            UserProgress.is_correct == False,  # noqa: E712
        )
        .group_by(UserProgress.question_id)
    )

    if domain:
        stmt = stmt.where(UserProgress.question_domain == domain)

    if sort_by == "miss_count":
        stmt = stmt.order_by(func.count(UserProgress.id).desc())
    elif sort_by == "domain":
        stmt = stmt.order_by(func.max(UserProgress.question_domain).asc(), func.max(UserProgress.timestamp).desc())
    else:
        stmt = stmt.order_by(func.max(UserProgress.timestamp).desc())

    stmt = stmt.limit(limit)

    rows = (await db.execute(stmt)).all()

    if not rows:
        return MissedQuestionsResponse(user_id=user.id, items=[], total=0)

    question_ids = [r.question_id for r in rows]
    q_result = await db.execute(
        select(Question).where(Question.id.in_(question_ids))
    )
    questions_by_id = {q.id: q for q in q_result.scalars().all()}

    # Fetch explanations from annotations for each question
    ann_result = await db.execute(
        select(QuestionAnnotation).where(
            QuestionAnnotation.question_id.in_(question_ids)
        )
    )
    annotations_by_question: dict = {}
    for ann in ann_result.scalars().all():
        annotations_by_question.setdefault(ann.question_id, ann)

    items: list[MissedQuestionItem] = []
    for row in rows:
        q = questions_by_id.get(row.question_id)
        if not q:
            continue
        ann = annotations_by_question.get(row.question_id)
        explanation: Optional[str] = None
        if ann:
            expl = ann.explanation_jsonb or {}
            explanation = (
                expl.get("explanation_short")
                or expl.get("short")
                or expl.get("explanation")
                or (ann.annotation_jsonb or {}).get("explanation_short")
            )

        domain_val = row.question_domain
        focus_key = row.focus_key_grammar if domain_val == "grammar" else row.focus_key_reading

        items.append(MissedQuestionItem(
            question_id=str(row.question_id),
            question_text=q.current_question_text,
            domain=domain_val,
            focus_key=focus_key,
            difficulty=row.question_difficulty,
            user_answer=row.last_selected,
            correct_answer=q.current_correct_option_label,
            explanation=explanation,
            miss_count=row.miss_count,
            last_missed_at=row.last_missed_at,
        ))

    return MissedQuestionsResponse(user_id=user.id, items=items, total=len(items))


# ── Diagnostic Session Endpoints ─────────────────────────────────────────────

# 16 questions × ~71 seconds each ≈ 19 minutes
DIAGNOSTIC_TIME_LIMIT_SECONDS = 1140


async def _build_diagnostic_question_payload(
    q,
    ann_data: dict,
    ann,
    seq: int,
    db: AsyncSession,
) -> DiagnosticQuestionPayload:
    """Build a DiagnosticQuestionPayload (no answer key) for one question."""
    # Fetch options for this question (latest version)
    opts_res = await db.execute(
        select(QuestionOption)
        .where(QuestionOption.question_id == q.id)
        .where(QuestionOption.question_version_id == q.latest_version_id)
        .order_by(QuestionOption.option_label)
    )
    raw_opts = opts_res.scalars().all()

    # Build option list — omit correctness markers
    ann_opts = {
        o["option_label"]: o
        for o in ann_data.get("options", [])
        if isinstance(o, dict) and "option_label" in o
    }
    options = []
    for opt in raw_opts:
        ao = ann_opts.get(opt.option_label, {})
        d_key = ao.get("distractor_type_key")
        options.append(DiagnosticOptionPayload(
            label=opt.option_label,
            text=opt.option_text,
            distractor_type_key=d_key if d_key and d_key != "correct" else None,
        ))

    domain = derive_domain(ann_data)
    passage_spans = (
        {
            "label": ann.passage_spans.get("label"),
            "anatomy_present": ann.passage_spans.get("anatomy_present", []),
            "concepts_present": ann.passage_spans.get("concepts_present", []),
        }
        if ann is not None and ann.passage_spans else None
    )

    return DiagnosticQuestionPayload(
        id=str(q.id),
        seq=seq,
        current_question_text=q.current_question_text,
        current_passage_text=q.current_passage_text,
        passage_spans=passage_spans,
        options=options,
        domain=domain,
        grammar_role_key=ann_data.get("grammar_role_key"),
        grammar_focus_key=ann_data.get("grammar_focus_key"),
        skill_family_key=ann_data.get("skill_family_key"),
        reading_focus_key=ann_data.get("reading_focus_key"),
        difficulty_overall=ann_data.get("difficulty_overall"),
        question_family_key=ann_data.get("question_family_key"),
        stimulus_mode_key=q.stimulus_mode_key,
    )


@router.post("/diagnostic/start")
async def diagnostic_start(
    body: DiagnosticStartV1Request,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Create a new diagnostic session.

    When diagnostic_type=='blueprint_v1' (default), assembles a full 16-question
    blueprint module, persists question_ids in slot order, and returns all question
    payloads in one shot (no answer key). Legacy types fall through to the old
    minimal-start behaviour.
    """
    user = await _resolve_user_by_token(body.user_token, db)

    if body.diagnostic_type == "blueprint_v1":
        try:
            assembled = await assemble_diagnostic(db, user_id=user.id, blueprint=BLUEPRINT_V1)
        except DiagnosticBankExhaustedError as exc:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Not enough active questions are available to start the diagnostic. "
                    "Restore or reingest the question bank, then try again."
                ),
            ) from exc

        question_ids_ordered = [cq.question_id for cq in assembled.questions]
        session = DiagnosticSession(
            user_id=user.id,
            started_at=datetime.now(timezone.utc),
            diagnostic_type="blueprint_v1",
            focus_areas=[],
            question_ids=question_ids_ordered,
            total_questions=len(question_ids_ordered),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Fetch all questions + annotations in bulk
        from uuid import UUID as _UUID

        q_uuids = [_UUID(qid) for qid in question_ids_ordered]
        q_res = await db.execute(
            select(Question).where(Question.id.in_(q_uuids))
        )
        q_map = {str(q.id): q for q in q_res.scalars().all()}

        ann_ids = [q.latest_annotation_id for q in q_map.values() if q.latest_annotation_id]
        ann_map: dict = {}
        if ann_ids:
            ann_res = await db.execute(
                select(QuestionAnnotation).where(QuestionAnnotation.id.in_(ann_ids))
            )
            ann_map = {str(a.id): a for a in ann_res.scalars().all()}

        payloads = []
        for cq in assembled.questions:
            q = q_map.get(cq.question_id)
            if not q:
                continue
            ann = ann_map.get(str(q.latest_annotation_id)) if q.latest_annotation_id else None
            ann_data = ann.annotation_jsonb if ann else {}
            payload = await _build_diagnostic_question_payload(q, ann_data, ann, cq.slot.seq, db)
            payloads.append(payload)

        return DiagnosticStartV1Response(
            session_id=str(session.id),
            total_questions=len(payloads),
            time_limit_seconds=DIAGNOSTIC_TIME_LIMIT_SECONDS,
            questions=payloads,
            coverage_report=assembled.coverage_report,
        )

    # Legacy fallback — minimal start (existing behaviour for other diagnostic types)
    session = DiagnosticSession(
        user_id=user.id,
        started_at=datetime.now(timezone.utc),
        diagnostic_type=body.diagnostic_type or "standard",
        focus_areas=[],
        question_ids=[],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return DiagnosticSessionStartResponse(session_id=str(session.id))


@router.post("/diagnostic/{session_id}/submit", response_model=DiagnosticAnswerResponse)
async def diagnostic_submit(
    session_id: str,
    body: DiagnosticAnswerRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Submit one answer within a diagnostic session."""
    try:
        sess_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = await db.get(DiagnosticSession, sess_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Diagnostic session not found")
    if session.completed_at:
        raise HTTPException(status_code=400, detail="Session already completed")

    user = await _resolve_user_by_token(body.user_token, db)
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    try:
        qid = UUID(body.question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id")

    q = await db.get(Question, qid)
    if not q or q.practice_status != "active":
        raise HTTPException(status_code=404, detail="Question not found or inactive")

    # Fetch annotation for denormalized fields
    ann_data: dict = {}
    if q.latest_annotation_id:
        ann_res = await db.execute(
            select(QuestionAnnotation).where(QuestionAnnotation.id == q.latest_annotation_id)
        )
        ann = ann_res.scalars().first()
        if ann:
            ann_data = ann.annotation_jsonb or {}

    # bug-761: the v8 bank classifies reading via skill_family_key (singular);
    # reading_skill_family_key/reading_focus_key are NULL, so derive_domain reads
    # the keys the bank actually populates.
    question_domain = derive_domain(ann_data)
    question_difficulty = ann_data.get("difficulty_overall")

    is_correct = q.current_correct_option_label == body.selected_option_label

    progress = UserProgress(
        user_id=user.id,
        question_id=qid,
        diagnostic_session_id=sess_uuid,
        is_correct=is_correct,
        selected_option_label=body.selected_option_label,
        source_type="diagnostic",
        missed_grammar_focus_key=body.missed_grammar_focus_key or (None if is_correct else ann_data.get("grammar_focus_key")),
        missed_syntactic_trap_key=body.missed_syntactic_trap_key if not is_correct else None,
        missed_reading_focus_key=body.missed_reading_focus_key or (None if is_correct else ann_data.get("reading_focus_key")),
        missed_reading_skill_family_key=body.missed_reading_skill_family_key or (None if is_correct else ann_data.get("reading_skill_family_key")),
        question_domain=question_domain,
        question_difficulty=question_difficulty,
    )
    db.add(progress)

    # Update session counters.
    # Blueprint sessions pre-seed question_ids at start — don't duplicate.
    qids = list(session.question_ids or [])
    if str(qid) not in qids:
        qids.append(str(qid))
        session.question_ids = qids
    if is_correct:
        session.correct_count = (session.correct_count or 0) + 1

    # Always update total_questions to reflect pre-seeded set or running tally
    session.total_questions = session.total_questions or len(qids)

    await db.commit()
    await db.refresh(progress)

    return DiagnosticAnswerResponse(
        is_correct=is_correct,
        progress_id=progress.id,
        question_number=len(qids),
        total_questions=session.total_questions,
        correct_so_far=session.correct_count,
    )


@router.post("/diagnostic/{session_id}/complete", response_model=DiagnosticSessionResult)
async def diagnostic_complete(
    session_id: str,
    body: DiagnosticSessionStartRequest,  # reuse: only needs user_token
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Mark a diagnostic session complete and return results."""
    try:
        sess_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = await db.get(DiagnosticSession, sess_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Diagnostic session not found")

    user = await _resolve_user_by_token(body.user_token, db)
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    now = datetime.now(timezone.utc)
    session.completed_at = now
    session.accuracy = (
        round(session.correct_count / session.total_questions, 4)
        if session.total_questions > 0 else 0.0
    )

    await db.commit()
    await db.refresh(session)

    # Compute weakest focus areas + breakdown from progress records
    prog_res = await db.execute(
        select(UserProgress).where(UserProgress.diagnostic_session_id == sess_uuid)
    )
    records = prog_res.scalars().all()
    miss_counts: dict = {}
    by_family: dict = {}
    by_difficulty: dict = {}
    by_trap: dict = {}

    for rec in records:
        # Weakest focus keys
        if not rec.is_correct:
            key = rec.missed_grammar_focus_key or rec.missed_reading_focus_key
            if key:
                miss_counts[key] = miss_counts.get(key, 0) + 1

        # Breakdown by question_domain (used as "family" proxy here)
        domain_key = rec.question_domain or "unknown"
        if domain_key not in by_family:
            by_family[domain_key] = CorrectTotal(correct=0, total=0)
        by_family[domain_key].total += 1
        if rec.is_correct:
            by_family[domain_key].correct += 1

        # Breakdown by difficulty
        diff_key = rec.question_difficulty or "unknown"
        if diff_key not in by_difficulty:
            by_difficulty[diff_key] = CorrectTotal(correct=0, total=0)
        by_difficulty[diff_key].total += 1
        if rec.is_correct:
            by_difficulty[diff_key].correct += 1

        # Breakdown by syntactic trap
        trap_key = rec.missed_syntactic_trap_key
        if trap_key and not rec.is_correct:
            if trap_key not in by_trap:
                by_trap[trap_key] = CorrectTotal(correct=0, total=0)
            by_trap[trap_key].total += 1

    weakest_raw = sorted(
        [
            {
                "area_key": k,
                "domain": "grammar" if "grammar" in k or any(
                    k in v for v in [
                        "sentence_boundary", "agreement", "verb_form", "modifier",
                        "punctuation", "expression_of_ideas", "parallel_structure", "pronoun",
                    ]
                ) else "reading",
                "miss_count": v,
            }
            for k, v in miss_counts.items()
        ],
        key=lambda x: x["miss_count"],
        reverse=True,
    )[:5]

    weakest = [{"focus_key": w["area_key"], "miss_count": w["miss_count"]} for w in weakest_raw]

    breakdown = DiagnosticBreakdown(
        by_family=by_family,
        by_difficulty=by_difficulty,
        by_trap=by_trap,
        weakest_areas=weakest_raw,
    )

    duration = None
    if session.started_at:
        duration = int((now - session.started_at).total_seconds())

    return DiagnosticSessionResult(
        session_id=str(session.id),
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        accuracy=session.accuracy,
        duration_seconds=duration,
        weakest_focus_areas=weakest,
        breakdown=breakdown,
    )


@router.get("/diagnostic/history", response_model=DiagnosticHistoryResponse)
async def diagnostic_history(
    user_token: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return all diagnostic sessions for a user, most recent first."""
    user = await _resolve_user_by_token(user_token, db)

    result = await db.execute(
        select(DiagnosticSession)
        .where(DiagnosticSession.user_id == user.id)
        .where(DiagnosticSession.is_archived == False)  # noqa: E712
        .order_by(DiagnosticSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()

    count_res = await db.execute(
        select(func.count()).select_from(DiagnosticSession).where(DiagnosticSession.user_id == user.id)
    )
    total = count_res.scalars().first() or 0

    items = []
    accuracies = []
    for s in sessions:
        duration = None
        if s.started_at and s.completed_at:
            duration = int((s.completed_at - s.started_at).total_seconds())
        items.append(DiagnosticHistoryItem(
            session_id=str(s.id),
            created_at=s.created_at,
            completed_at=s.completed_at,
            accuracy=s.accuracy,
            total_questions=s.total_questions,
            correct_count=s.correct_count,
            diagnostic_type=s.diagnostic_type,
            duration_seconds=duration,
        ))
        if s.accuracy is not None:
            accuracies.append(s.accuracy)

    avg_accuracy = round(sum(accuracies) / len(accuracies), 4) if accuracies else None

    # Simple improvement trend: compare first half vs second half accuracy
    improvement_trend = None
    if len(accuracies) >= 4:
        mid = len(accuracies) // 2
        # sessions are newest-first, so recent = first half
        recent_avg = sum(accuracies[:mid]) / mid
        older_avg = sum(accuracies[mid:]) / (len(accuracies) - mid)
        improvement_trend = round(recent_avg - older_avg, 4)

    return DiagnosticHistoryResponse(
        sessions=items,
        total_sessions=total,
        average_accuracy=avg_accuracy,
        improvement_trend=improvement_trend,
    )


@router.get("/diagnostic/{session_id}", response_model=DiagnosticSessionDetailResponse)
async def diagnostic_detail(
    session_id: str,
    user_token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return full detail for one diagnostic session."""
    try:
        sess_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = await db.get(DiagnosticSession, sess_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user = await _resolve_user_by_token(user_token, db)
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    prog_res = await db.execute(
        select(UserProgress)
        .where(UserProgress.diagnostic_session_id == sess_uuid)
        .order_by(UserProgress.timestamp.asc())
    )
    records = prog_res.scalars().all()

    question_results = []
    focus_breakdown: dict = {}
    for i, rec in enumerate(records):
        focus = rec.missed_grammar_focus_key or rec.missed_reading_focus_key
        question_results.append(DiagnosticQuestionResult(
            question_number=i + 1,
            question_id=str(rec.question_id),
            selected_option=rec.selected_option_label,
            is_correct=rec.is_correct,
            focus_area=focus,
        ))
        if focus:
            entry = focus_breakdown.setdefault(focus, {"attempted": 0, "correct": 0})
            entry["attempted"] += 1
            if rec.is_correct:
                entry["correct"] += 1

    return DiagnosticSessionDetailResponse(
        session_id=str(session.id),
        user_id=session.user_id,
        created_at=session.created_at,
        completed_at=session.completed_at,
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        accuracy=session.accuracy,
        question_results=question_results,
        focus_breakdown=focus_breakdown,
    )


# ── Spaced Repetition Helpers ────────────────────────────────────────────────

def _sm2_update(sr: SpacedRepetitionState, quality: int, now: datetime) -> None:
    """Apply SM-2 algorithm to update spaced repetition state in-place.

    quality: 0-5 (0=complete blackout, 5=perfect recall)
    SM-2 spec: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-super-memo-method
    """
    sr.total_attempts += 1
    if quality >= 3:
        sr.correct_attempts += 1

    if quality >= 3:
        if sr.repetition_count == 0:
            new_interval = 1.0
        elif sr.repetition_count == 1:
            new_interval = 6.0
        else:
            new_interval = round(sr.interval_days * sr.easiness_factor, 2)
        sr.interval_days = new_interval
        sr.repetition_count += 1
    else:
        # Incorrect recall — reset the repetition count and interval
        sr.repetition_count = 0
        sr.interval_days = 1.0

    # Update easiness factor (EF); clamp to [1.3, 5.0]
    new_ef = sr.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    sr.easiness_factor = max(1.3, min(5.0, round(new_ef, 4)))

    sr.last_reviewed_at = now
    sr.next_review_at = now + timedelta(days=sr.interval_days)


def _sr_confidence_level(sr: SpacedRepetitionState) -> str:
    """Classify the confidence level based on SM-2 state."""
    ef = sr.easiness_factor
    reps = sr.repetition_count
    if ef >= 3.5 and reps >= 5:
        return "mastered"
    elif ef >= 2.5 and reps >= 3:
        return "proficient"
    elif reps >= 1:
        return "developing"
    return "novice"


# ── Spaced Repetition Endpoints ──────────────────────────────────────────────

@router.post("/spaced-repetition/{question_id}/review", response_model=SRReviewResponse)
async def sr_review(
    question_id: str,
    body: SRReviewRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Record a review result and update SM-2 state for a question."""
    try:
        qid = UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id")

    user = await _resolve_user_by_token(body.user_token, db)

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    # Get or create SR state for this (user, question) pair
    existing = await db.execute(
        select(SpacedRepetitionState).where(
            SpacedRepetitionState.user_id == user.id,
            SpacedRepetitionState.question_id == qid,
        )
    )
    sr = existing.scalars().first()

    now = datetime.now(timezone.utc)
    if sr is None:
        sr = SpacedRepetitionState(
            user_id=user.id,
            question_id=qid,
        )
        db.add(sr)

    _sm2_update(sr, body.quality, now)
    await db.commit()
    await db.refresh(sr)

    return SRReviewResponse(
        question_id=question_id,
        next_review_at=sr.next_review_at,
        interval_days=sr.interval_days,
        easiness_factor=sr.easiness_factor,
        repetition_count=sr.repetition_count,
        confidence_level=_sr_confidence_level(sr),
    )


@router.get("/spaced-repetition/due", response_model=SRDueQuestionsResponse)
async def sr_due_questions(
    user_token: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    domain: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return questions due for spaced repetition review, ordered by most overdue first."""
    user = await _resolve_user_by_token(user_token, db)
    now = datetime.now(timezone.utc)

    stmt = (
        select(SpacedRepetitionState)
        .where(
            SpacedRepetitionState.user_id == user.id,
            SpacedRepetitionState.next_review_at <= now,
        )
        .order_by(SpacedRepetitionState.next_review_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    due = result.scalars().all()

    # Count total due across all records (ignoring the limit)
    count_res = await db.execute(
        select(func.count()).select_from(SpacedRepetitionState).where(
            SpacedRepetitionState.user_id == user.id,
            SpacedRepetitionState.next_review_at <= now,
        )
    )
    total_due = count_res.scalars().first() or 0

    items = []
    for sr in due:
        days_overdue = max(0.0, (now - sr.next_review_at).total_seconds() / 86400)

        # Fetch annotation metadata for focus area and domain classification
        ann_data: dict = {}
        q = await db.get(Question, sr.question_id)
        if q and q.latest_annotation_id:
            ann_res = await db.execute(
                select(QuestionAnnotation).where(QuestionAnnotation.id == q.latest_annotation_id)
            )
            ann = ann_res.scalars().first()
            if ann:
                ann_data = ann.annotation_jsonb or {}

        focus = ann_data.get("grammar_focus_key") or ann_data.get("reading_focus_key")
        q_domain = (
            "reading" if (ann_data.get("reading_skill_family_key") or ann_data.get("reading_focus_key"))
            else ("grammar" if ann_data.get("grammar_focus_key") else None)
        )

        # Apply optional domain filter; skip items that don't match
        if domain and q_domain != domain:
            continue

        items.append(SRDueQuestion(
            question_id=str(sr.question_id),
            days_overdue=round(days_overdue, 2),
            confidence_level=_sr_confidence_level(sr),
            last_reviewed_at=sr.last_reviewed_at,
            next_review_at=sr.next_review_at,
            focus_area=focus,
            domain=q_domain,
        ))

    # Rough time estimate: 3 minutes per question, bounded [5, 20] minutes
    suggested = min(20, max(5, len(items) * 3))

    return SRDueQuestionsResponse(
        due_questions=items,
        total_due=total_due,
        suggested_session_length_minutes=suggested,
    )


@router.get("/spaced-repetition/progress", response_model=SRProgressResponse)
async def sr_progress(
    user_token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return spaced repetition progress summary for a user."""
    user = await _resolve_user_by_token(user_token, db)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(SpacedRepetitionState).where(SpacedRepetitionState.user_id == user.id)
    )
    records = result.scalars().all()

    if not records:
        return SRProgressResponse(
            total_tracked=0,
            mastered_count=0,
            proficient_count=0,
            developing_count=0,
            novice_count=0,
            due_for_review=0,
            average_easiness_factor=2.5,
            retention_rate=0.0,
        )

    mastered = proficient = developing = novice = due = 0
    total_attempts = total_correct = 0

    for sr in records:
        level = _sr_confidence_level(sr)
        if level == "mastered":
            mastered += 1
        elif level == "proficient":
            proficient += 1
        elif level == "developing":
            developing += 1
        else:
            novice += 1
        if sr.next_review_at and sr.next_review_at <= now:
            due += 1
        total_attempts += sr.total_attempts
        total_correct += sr.correct_attempts

    avg_ef = round(sum(r.easiness_factor for r in records) / len(records), 4)
    retention = round(total_correct / total_attempts, 4) if total_attempts > 0 else 0.0

    return SRProgressResponse(
        total_tracked=len(records),
        mastered_count=mastered,
        proficient_count=proficient,
        developing_count=developing,
        novice_count=novice,
        due_for_review=due,
        average_easiness_factor=avg_ef,
        retention_rate=retention,
    )


@router.get("/student/trap-susceptibility", response_model=TrapSusceptibilityResponse)
async def get_trap_susceptibility(
    user_token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return per-trap fall rates and improvement trends for the authenticated user."""
    user = await _resolve_user_by_token(user_token, db)

    result = await db.execute(
        select(
            UserProgress.missed_syntactic_trap_key,
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .where(
            UserProgress.user_id == user.id,
            UserProgress.missed_syntactic_trap_key.isnot(None),
        )
        .group_by(UserProgress.missed_syntactic_trap_key)
    )
    rows = result.all()

    trap_encounters: dict[str, int] = {}
    trap_correct_counts: dict[str, int] = {}
    trap_fall_rates: dict[str, float] = {}

    for row in rows:
        trap_type = row.missed_syntactic_trap_key
        total = row.total
        correct = int(row.correct or 0)
        trap_encounters[trap_type] = total
        trap_correct_counts[trap_type] = correct
        trap_fall_rates[trap_type] = round(1.0 - correct / total, 4) if total > 0 else 0.0

    def _severity(fall_rate: float) -> str:
        if fall_rate >= 0.8:
            return "critical"
        if fall_rate >= 0.6:
            return "high"
        if fall_rate >= 0.4:
            return "moderate"
        return "low"

    all_metrics = [
        TrapMetric(
            trap_type=t,
            fall_rate=trap_fall_rates[t],
            occurrences=trap_encounters[t],
            correct_count=trap_correct_counts[t],
            severity=_severity(trap_fall_rates[t]),
        )
        for t in trap_encounters
    ]
    most_susceptible = sorted(all_metrics, key=lambda m: m.fall_rate, reverse=True)[:5]

    # Improvement trends: compare first 5 vs last 5 attempts per trap
    improvement: dict[str, TrapImprovement] = {}
    overcoming: list[TrapMetric] = []
    persistent: list[TrapMetric] = []

    for metric in all_metrics:
        trap_type = metric.trap_type

        early_rows = await db.execute(
            select(UserProgress.is_correct)
            .where(UserProgress.user_id == user.id, UserProgress.missed_syntactic_trap_key == trap_type)
            .order_by(UserProgress.timestamp.asc())
            .limit(5)
        )
        early = early_rows.scalars().all()

        late_rows = await db.execute(
            select(UserProgress.is_correct)
            .where(UserProgress.user_id == user.id, UserProgress.missed_syntactic_trap_key == trap_type)
            .order_by(UserProgress.timestamp.desc())
            .limit(5)
        )
        late = late_rows.scalars().all()

        first_acc = sum(1 for x in early if x) / len(early) if early else 0.0
        recent_acc = sum(1 for x in late if x) / len(late) if late else 0.0
        trend = round(recent_acc - first_acc, 4)
        improvement[trap_type] = TrapImprovement(
            first_accuracy=round(first_acc, 4),
            recent_accuracy=round(recent_acc, 4),
            trend=trend,
        )

        if recent_acc >= 0.6 and recent_acc > first_acc:
            overcoming.append(metric)
        elif recent_acc < 0.4 and metric.fall_rate > 0.6:
            persistent.append(metric)

    total_attempted_result = await db.execute(
        select(func.count()).select_from(UserProgress).where(UserProgress.user_id == user.id)
    )
    total_attempted = total_attempted_result.scalars().first() or 0

    return TrapSusceptibilityResponse(
        user_id=user.id,
        total_questions_attempted=total_attempted,
        trap_encounters=trap_encounters,
        trap_fall_rates=trap_fall_rates,
        trap_correct_counts=trap_correct_counts,
        most_susceptible_traps=most_susceptible,
        overcoming_traps=overcoming,
        persistent_traps=persistent,
        trap_improvement=improvement,
    )


@router.get("/student/question-type-performance", response_model=QuestionTypePerformanceResponse)
async def get_question_type_performance(
    user_token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return accuracy broken down by question stem_type_key."""
    user = await _resolve_user_by_token(user_token, db)

    result = await db.execute(
        select(
            Question.stem_type_key,
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .join(Question, UserProgress.question_id == Question.id)
        .where(
            UserProgress.user_id == user.id,
            Question.stem_type_key.isnot(None),
        )
        .group_by(Question.stem_type_key)
    )
    rows = result.all()

    metrics: list[QuestionTypeMetric] = []
    for row in rows:
        total = row.total
        correct = int(row.correct or 0)
        metrics.append(QuestionTypeMetric(
            question_type=row.stem_type_key,
            total_attempts=total,
            correct_count=correct,
            accuracy=round(correct / total, 4) if total > 0 else 0.0,
        ))

    metrics.sort(key=lambda m: m.accuracy, reverse=True)
    easiest = [m.question_type for m in metrics[:3]]
    hardest = [m.question_type for m in reversed(metrics[-3:])]

    total_attempted_r = await db.execute(
        select(func.count()).select_from(UserProgress).where(UserProgress.user_id == user.id)
    )
    total_attempted = total_attempted_r.scalars().first() or 0

    return QuestionTypePerformanceResponse(
        user_id=user.id,
        total_attempts=total_attempted,
        by_question_type=metrics,
        easiest_types=easiest,
        hardest_types=hardest,
    )


@router.get("/student/trap-details/{trap_type}", response_model=TrapDetailResponse)
async def get_trap_details(
    trap_type: str,
    user_token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return detailed breakdown and examples for a specific trap type."""
    user = await _resolve_user_by_token(user_token, db)

    rows_r = await db.execute(
        select(UserProgress)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.missed_syntactic_trap_key == trap_type,
        )
        .order_by(UserProgress.timestamp.asc())
    )
    rows = rows_r.scalars().all()

    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No data found for trap: {trap_type}")

    total = len(rows)
    correct = sum(1 for r in rows if r.is_correct)
    fall_rate = round(1.0 - correct / total, 4)

    early = rows[:5]
    late = rows[-5:]
    first_acc = round(sum(1 for r in early if r.is_correct) / len(early), 4)
    recent_acc = round(sum(1 for r in late if r.is_correct) / len(late), 4)

    def _severity(fr: float) -> str:
        if fr >= 0.8:
            return "critical"
        if fr >= 0.6:
            return "high"
        if fr >= 0.4:
            return "moderate"
        return "low"

    # Collect up to 5 wrong-answer examples
    examples: list[TrapDetailExample] = []
    for row in rows:
        if not row.is_correct and len(examples) < 5:
            q = await db.get(Question, row.question_id)
            examples.append(TrapDetailExample(
                question_text=(q.current_question_text or q.current_passage_text or "")[:300] if q else "",
                selected_option=row.selected_option_label or "",
                is_correct=False,
                grammar_focus=row.missed_grammar_focus_key,
            ))

    return TrapDetailResponse(
        trap_type=trap_type,
        user_encounters=total,
        user_fall_rate=fall_rate,
        first_accuracy=first_acc,
        recent_accuracy=recent_acc,
        trend=round(recent_acc - first_acc, 4),
        severity=_severity(fall_rate),
        example_mistakes=examples,
    )


# ── Phase 3: Progress Analytics ──────────────────────────────────────────────

def _streak(daily_points: list[DailyAccuracyPoint]) -> int:
    """Count consecutive trailing days that have at least 1 attempt."""
    from datetime import date as date_type, timedelta as td
    today = datetime.now(timezone.utc).date()
    streak = 0
    dates_with_attempts = {p.date for p in daily_points if p.attempts > 0}
    check = today
    while str(check) in dates_with_attempts:
        streak += 1
        check -= td(days=1)
    return streak


@router.get("/progress/trend", response_model=ProgressTrendResponse)
async def get_progress_trend(
    user_token: str = Query(...),
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Daily accuracy trend for the last N days."""
    user = await _resolve_user_by_token(user_token, db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            cast(UserProgress.timestamp, Date).label("day"),
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .where(UserProgress.user_id == user.id, UserProgress.timestamp >= cutoff)
        .group_by(cast(UserProgress.timestamp, Date))
        .order_by(cast(UserProgress.timestamp, Date))
    )
    rows = result.all()

    points = [
        DailyAccuracyPoint(
            date=str(row.day),
            attempts=row.total,
            correct=int(row.correct or 0),
            accuracy=round(int(row.correct or 0) / row.total, 4) if row.total else 0.0,
        )
        for row in rows
    ]

    total_att = sum(p.attempts for p in points)
    total_cor = sum(p.correct for p in points)
    overall = round(total_cor / total_att, 4) if total_att else 0.0

    return ProgressTrendResponse(
        user_id=user.id,
        days=days,
        points=points,
        overall_accuracy=overall,
        total_attempts=total_att,
        streak_days=_streak(points),
    )


@router.get("/progress/domain-trend", response_model=DomainTrendResponse)
async def get_domain_trend(
    user_token: str = Query(...),
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Daily accuracy split by domain (grammar / reading) for the last N days."""
    user = await _resolve_user_by_token(user_token, db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            cast(UserProgress.timestamp, Date).label("day"),
            UserProgress.question_domain,
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .where(
            UserProgress.user_id == user.id,
            UserProgress.timestamp >= cutoff,
            UserProgress.question_domain.isnot(None),
        )
        .group_by(cast(UserProgress.timestamp, Date), UserProgress.question_domain)
        .order_by(cast(UserProgress.timestamp, Date))
    )
    rows = result.all()

    grammar: list[DailyAccuracyPoint] = []
    reading: list[DailyAccuracyPoint] = []
    for row in rows:
        point = DailyAccuracyPoint(
            date=str(row.day),
            attempts=row.total,
            correct=int(row.correct or 0),
            accuracy=round(int(row.correct or 0) / row.total, 4) if row.total else 0.0,
        )
        if row.question_domain == "grammar":
            grammar.append(point)
        elif row.question_domain in ("reading", "verbal"):
            reading.append(point)

    return DomainTrendResponse(user_id=user.id, days=days, grammar=grammar, reading=reading)


@router.get("/progress/focus-summary", response_model=FocusSummaryResponse)
async def get_focus_summary(
    user_token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Accuracy per grammar/reading focus key across all time."""
    user = await _resolve_user_by_token(user_token, db)

    # Grammar focus keys
    g_result = await db.execute(
        select(
            UserProgress.missed_grammar_focus_key.label("focus_key"),
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .where(
            UserProgress.user_id == user.id,
            UserProgress.missed_grammar_focus_key.isnot(None),
        )
        .group_by(UserProgress.missed_grammar_focus_key)
    )

    # Reading focus keys
    r_result = await db.execute(
        select(
            UserProgress.missed_reading_focus_key.label("focus_key"),
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .where(
            UserProgress.user_id == user.id,
            UserProgress.missed_reading_focus_key.isnot(None),
        )
        .group_by(UserProgress.missed_reading_focus_key)
    )

    all_stats: list[FocusAreaStat] = []
    for row in g_result.all():
        total = row.total
        correct = int(row.correct or 0)
        all_stats.append(FocusAreaStat(
            focus_key=row.focus_key,
            domain="grammar",
            total_attempts=total,
            correct_count=correct,
            accuracy=round(correct / total, 4) if total else 0.0,
        ))
    for row in r_result.all():
        total = row.total
        correct = int(row.correct or 0)
        all_stats.append(FocusAreaStat(
            focus_key=row.focus_key,
            domain="reading",
            total_attempts=total,
            correct_count=correct,
            accuracy=round(correct / total, 4) if total else 0.0,
        ))

    all_stats.sort(key=lambda s: s.total_attempts, reverse=True)
    top = all_stats[:8]
    qualified = [s for s in all_stats if s.total_attempts >= 3]
    weakest = sorted(qualified, key=lambda s: s.accuracy)[:5]

    return FocusSummaryResponse(
        user_id=user.id,
        top_focus_areas=top,
        weakest_focus_areas=weakest,
    )


# ── Phase 4: Adaptive Module 2 Routing ───────────────────────────────────────

def _route_module_2(accuracy: float, duration_seconds: int | None) -> tuple[str, str]:
    """
    Return (difficulty, rationale).
    Threshold: >= 0.70 accuracy → "higher", else → "lower".
    """
    if accuracy >= 0.70:
        rationale = f"Accuracy {accuracy:.0%} ≥ 70% threshold — routing to higher difficulty"
        return "higher", rationale
    else:
        rationale = f"Accuracy {accuracy:.0%} < 70% threshold — routing to lower difficulty"
        return "lower", rationale


@router.post("/test-session/module-1-complete", response_model=Module1CompleteResponse)
async def module_1_complete(
    body: Module1CompleteRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Record module 1 results and determine module 2 difficulty."""
    user = await _resolve_user_by_token(body.user_token, db)

    difficulty, rationale = _route_module_2(
        body.module_1_accuracy, body.module_1_duration_seconds
    )

    session = TestSessionResults(
        user_id=user.id,
        module_1_results=body.focus_breakdown or {},
        module_1_accuracy=round(body.module_1_accuracy, 4),
        module_1_duration_seconds=body.module_1_duration_seconds,
        module_2_difficulty=difficulty,
        routing_rationale=rationale,
        test_mode=body.test_mode,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return Module1CompleteResponse(
        test_session_id=str(session.id),
        module_2_difficulty=difficulty,
        routing_rationale=rationale,
        module_1_accuracy=body.module_1_accuracy,
    )


@router.get("/test-session/{test_session_id}/module-2-blueprint", response_model=Module2BlueprintResponse)
async def module_2_blueprint(
    test_session_id: str,
    user_token: str = Query(...),
    limit: int = Query(default=27, ge=5, le=40),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return a set of questions for module 2 based on routed difficulty."""
    from fastapi import HTTPException
    import uuid as _uuid

    user = await _resolve_user_by_token(user_token, db)

    try:
        session_uuid = _uuid.UUID(test_session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid test_session_id format")

    session_r = await db.execute(
        select(TestSessionResults).where(
            TestSessionResults.id == session_uuid,
            TestSessionResults.user_id == user.id,
        )
    )
    session = session_r.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # For "higher" difficulty: prioritise focus areas where user accuracy is lowest
    # For "lower" difficulty: serve a balanced active question set
    # Both paths pull from active questions the user hasn't answered recently.
    recently_answered_r = await db.execute(
        select(UserProgress.question_id)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.timestamp >= datetime.now(timezone.utc) - timedelta(days=3),
        )
    )
    recently_answered = {str(r) for r in recently_answered_r.scalars().all()}

    if session.module_2_difficulty == "higher":
        # Pull questions tied to the user's weakest focus areas (target their gaps)
        weak_focus_r = await db.execute(
            select(
                UserProgress.missed_grammar_focus_key,
                func.count().label("total"),
                func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
            )
            .where(
                UserProgress.user_id == user.id,
                UserProgress.missed_grammar_focus_key.isnot(None),
            )
            .group_by(UserProgress.missed_grammar_focus_key)
            .order_by(func.sum(case((UserProgress.is_correct == True, 1), else_=0)).asc())
            .limit(5)
        )
        weak_focus_keys = [r.missed_grammar_focus_key for r in weak_focus_r.all()]
    else:
        weak_focus_keys = []

    # Fetch active questions, prefer weak focus areas first
    q_result = await db.execute(
        select(Question)
        .join(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
            isouter=True,
        )
        .where(
            Question.practice_status == "active",
            Question.id.notin_(
                [_uuid.UUID(qid) for qid in recently_answered if _is_valid_uuid(qid)]
            ) if recently_answered else True,
        )
        .order_by(
            # Prioritise weak focus area matches for "higher" difficulty
            case(
                *[(QuestionAnnotation.grammar_focus_key == fk, i) for i, fk in enumerate(weak_focus_keys)],
                else_=len(weak_focus_keys),
            ) if weak_focus_keys else func.random(),
            func.random(),
        )
        .limit(limit)
    )
    questions = q_result.scalars().all()

    # Load options for each question
    if questions:
        q_ids = [q.id for q in questions]
        opts_r = await db.execute(
            select(QuestionOption)
            .where(
                QuestionOption.question_id.in_(q_ids),
                QuestionOption.version_id == Question.latest_version_id,
            )
        )
        opts_by_q: dict[str, list] = {}
        for opt in opts_r.scalars().all():
            qid = str(opt.question_id)
            opts_by_q.setdefault(qid, []).append({"label": opt.label, "text": opt.text})
    else:
        opts_by_q = {}

    blueprint_questions = [
        Module2BlueprintQuestion(
            id=str(q.id),
            current_question_text=q.current_question_text,
            current_passage_text=q.current_passage_text,
            options=sorted(opts_by_q.get(str(q.id), []), key=lambda o: o["label"]),
        )
        for q in questions
    ]

    return Module2BlueprintResponse(
        test_session_id=test_session_id,
        module_2_difficulty=session.module_2_difficulty,
        routing_rationale=session.routing_rationale or "",
        question_count=len(blueprint_questions),
        questions=blueprint_questions,
    )


def _is_valid_uuid(s: str) -> bool:
    try:
        import uuid as _u
        _u.UUID(s)
        return True
    except ValueError:
        return False


@router.get("/test-session/history", response_model=TestSessionHistoryResponse)
async def test_session_history(
    user_token: str = Query(...),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Return the user's past adaptive test sessions."""
    user = await _resolve_user_by_token(user_token, db)

    result = await db.execute(
        select(TestSessionResults)
        .where(TestSessionResults.user_id == user.id)
        .order_by(TestSessionResults.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    return TestSessionHistoryResponse(
        user_id=user.id,
        sessions=[
            TestSessionHistoryItem(
                test_session_id=str(s.id),
                module_1_accuracy=s.module_1_accuracy,
                module_2_difficulty=s.module_2_difficulty,
                estimated_score=s.estimated_score,
                test_mode=s.test_mode,
                created_at=s.created_at.isoformat(),
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
            )
            for s in sessions
        ],
    )
