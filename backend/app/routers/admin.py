import asyncio
import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete, update, func, and_, case, text, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Any, Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.auth import admin_required
from app.models.db import (
    Question, QuestionAnnotation, QuestionVersion, QuestionOption,
    QuestionRelation, QuestionJob, QuestionAsset, LlmEvaluation, UserProgress,
    QuestionStimulusAsset, GenerationBatch, ReviewRun, LlmReviewResult,
    ConsensusVerdict, ReviewerAdminOverride, AutoReleaseAuditLog,
    AdminQuestionAuditLog, User,
)
from app.config import get_settings
from app.models.ontology import RELATION_TYPES
from app.models.payload import (
    AdminEditRequest, EvaluationScoreRequest, GenerationBatchRequest,
    GeneratorModelStats, ReviewerModelStats, BatchAggregates, TokenUsageByProvider,
    GenerationTrendPoint, RejectionReasonCount,
    GenerationAnalyticsResponse, ReviewAnalyticsResponse,
    BatchAnalyticsResponse, TrendAnalyticsResponse,
    QuestionMissRate, FocusAreaMissRate, CohortWeakSpotsResponse,
    AccuracyBucket, DomainPerformance, CohortSummaryResponse,
    TrapCohortStat, CohortTrapAnalyticsResponse,
    TestSummary,
)
from app.pipeline import amendment_review


REGENERATE_MAX_ATTEMPTS_PER_QUESTION = 3


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
    source_release_year: Optional[int] = Query(None, description="Filter by official release year"),
    source_test_name: Optional[str] = Query(None, description="Filter by source test name"),
    source_exam_code: Optional[str] = Query(None, description="Filter by source exam code"),
    sort_by_source: bool = Query(False, description="Sort by release/test/exam/module/question order"),
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
    if source_release_year is not None:
        stmt = stmt.where(Question.source_release_year == source_release_year)
    if source_test_name:
        stmt = stmt.where(Question.source_test_name == source_test_name)
    if source_exam_code:
        stmt = stmt.where(Question.source_exam_code == source_exam_code)

    if sort_by_source:
        stmt = stmt.order_by(
            Question.source_release_year.asc().nullslast(),
            Question.source_test_name.asc().nullslast(),
            Question.source_exam_code.asc().nullslast(),
            Question.source_subject_code.asc().nullslast(),
            Question.source_section_code.asc().nullslast(),
            Question.source_module_code.asc().nullslast(),
            Question.source_question_number.asc().nullslast(),
            Question.created_at.desc(),
        )
    else:
        stmt = stmt.order_by(Question.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)

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
                    {
                        "id": str(opt.id),
                        "option_label": opt.option_label,
                        "option_text": opt.option_text,
                        "is_correct": opt.is_correct,
                    }
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
            "source_release_year": q.source_release_year,
            "source_test_name": q.source_test_name,
            "source_exam_code": q.source_exam_code,
            "source_subject_code": q.source_subject_code,
            "source_section_code": q.source_section_code,
            "source_module_code": q.source_module_code,
            "source_question_number": q.source_question_number,
            "current_passage_text": q.current_passage_text,
            "current_question_text": q.current_question_text,
            "current_correct_option_label": q.current_correct_option_label,
            "current_explanation_text": q.current_explanation_text,
            "is_admin_edited": q.is_admin_edited,
            "annotation_stale": q.annotation_stale,
            "annotation": annotation,
            "options": options,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })

    return items


@router.get("/tests", response_model=list[TestSummary])
async def list_tests(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Aggregate questions by source test/section/module for the admin test explorer."""
    stmt = (
        select(
            Question.source_release_year,
            Question.source_test_name,
            Question.source_exam_code,
            Question.source_subject_code,
            Question.source_section_code,
            Question.source_module_code,
            func.count(Question.id).label("question_count"),
            func.count(
                case((Question.practice_status.in_(("active", "approved")), 1))
            ).label("approved_count"),
        )
        .group_by(
            Question.source_release_year,
            Question.source_test_name,
            Question.source_exam_code,
            Question.source_subject_code,
            Question.source_section_code,
            Question.source_module_code,
        )
        .order_by(
            Question.source_release_year.asc().nullslast(),
            Question.source_test_name.asc().nullslast(),
            Question.source_section_code.asc().nullslast(),
            Question.source_module_code.asc().nullslast(),
        )
    )
    result = await db.execute(stmt)
    return [
        TestSummary(
            source_release_year=r.source_release_year,
            source_test_name=r.source_test_name,
            source_exam_code=r.source_exam_code,
            source_subject_code=r.source_subject_code,
            source_section_code=r.source_section_code,
            source_module_code=r.source_module_code,
            question_count=r.question_count,
            approved_count=r.approved_count,
        )
        for r in result.all()
    ]


def _parse_uuid(item_id: str) -> UUID:
    try:
        return UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")


def _validated_relation_type(relation_type: str) -> str:
    if relation_type not in RELATION_TYPES:
        raise HTTPException(status_code=400, detail="Invalid relation_type")
    return relation_type


def _admin_override_direction(reviewer_verdict: str, admin_verdict: str) -> str:
    if reviewer_verdict == admin_verdict:
        return "reviewer_correct"
    if admin_verdict == "accept":
        return "reviewer_too_harsh"
    return "reviewer_too_lenient"


async def _latest_review_results_for_admin_override(
    qid: UUID,
    db: AsyncSession,
) -> list[LlmReviewResult]:
    run_result = await db.execute(
        select(ReviewRun)
        .where(
            ReviewRun.question_id == qid,
            ReviewRun.status.in_(("complete", "partial")),
        )
        .order_by(ReviewRun.completed_at.desc().nullslast(), ReviewRun.started_at.desc())
        .limit(1)
    )
    review_run = run_result.scalars().first()
    if review_run is None:
        return []

    result = await db.execute(
        select(LlmReviewResult)
        .where(LlmReviewResult.review_run_id == review_run.id)
        .order_by(LlmReviewResult.provider_name, LlmReviewResult.model_name)
    )
    return result.scalars().all()


async def _write_admin_audit(
    *,
    qid,
    admin_token: str,
    action: str,
    before: dict | None,
    after: dict | None,
    fields_changed: list[str] | None = None,
    change_notes: str | None = None,
    question_version_id=None,
    db,
) -> None:
    """Append one row to admin_question_audit_logs. Always call before db.commit()."""
    db.add(AdminQuestionAuditLog(
        id=uuid.uuid4(),
        question_id=qid,
        admin_token=admin_token,
        action=action,
        fields_changed=fields_changed,
        before_jsonb=before,
        after_jsonb=after,
        change_notes=change_notes,
        question_version_id=question_version_id,
    ))


async def _write_reviewer_admin_overrides(
    *,
    qid: UUID,
    admin_verdict: str,
    admin_token: str | None,
    admin_notes: str | None,
    db: AsyncSession,
) -> tuple[UUID, int]:
    review_results = await _latest_review_results_for_admin_override(qid, db)
    admin_decision_id = uuid.uuid4()
    for review_result in review_results:
        db.add(
            ReviewerAdminOverride(
                id=uuid.uuid4(),
                admin_decision_id=admin_decision_id,
                question_id=qid,
                llm_review_result_id=review_result.id,
                reviewer_verdict=review_result.verdict,
                admin_verdict=admin_verdict,
                override_direction=_admin_override_direction(
                    review_result.verdict,
                    admin_verdict,
                ),
                admin_token=admin_token,
                admin_notes=admin_notes,
                created_at=datetime.now(timezone.utc),
            )
        )
    return admin_decision_id, len(review_results)


def _json_safe(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _annotation_domain(annotation: dict[str, Any] | None) -> str | None:
    if not annotation:
        return None
    if annotation.get("reading_skill_family_key") or annotation.get("reading_focus_key"):
        return "reading"
    if annotation.get("grammar_role_key") or annotation.get("grammar_focus_key"):
        return "grammar"
    return None


def _source_ids_for_candidate(
    question: Question,
    job: QuestionJob | None,
) -> list[str]:
    source_ids = []
    if job and isinstance(job.generation_request_jsonb, dict):
        source_ids = job.generation_request_jsonb.get("source_question_ids") or []
    if not source_ids and isinstance(question.generation_source_set, dict):
        source_ids = question.generation_source_set.get("source_question_ids") or []
    return [str(item) for item in source_ids]


async def _latest_generation_batch_for_question(
    qid: UUID,
    db: AsyncSession,
) -> GenerationBatch | None:
    job_result = await db.execute(
        select(QuestionJob)
        .where(
            QuestionJob.question_id == qid,
            QuestionJob.job_type == "generate",
        )
        .order_by(QuestionJob.created_at.desc())
        .limit(1)
    )
    job = job_result.scalars().first()
    if not job or not job.generation_batch_id:
        return None
    return await db.get(GenerationBatch, job.generation_batch_id)


def _review_token_expr(primary_key: str, legacy_key: str):
    return cast(
        func.coalesce(
            LlmReviewResult.token_usage_jsonb[primary_key].astext,
            LlmReviewResult.token_usage_jsonb[legacy_key].astext,
        ),
        Float,
    )


async def _serialize_generated_candidates(
    questions: list[Question],
    db: AsyncSession,
) -> list[dict[str, Any]]:
    if not questions:
        return []

    qids = [q.id for q in questions]

    ann_ids = [q.latest_annotation_id for q in questions if q.latest_annotation_id]
    ann_map = {}
    if ann_ids:
        ann_rows = await db.execute(select(QuestionAnnotation).where(QuestionAnnotation.id.in_(ann_ids)))
        ann_map = {ann.id: ann for ann in ann_rows.scalars().all()}

    version_to_qid = {q.latest_version_id: q.id for q in questions if q.latest_version_id}
    opts_by_qid: dict[UUID, list[QuestionOption]] = {}
    if version_to_qid:
        opt_rows = await db.execute(
            select(QuestionOption)
            .where(QuestionOption.question_version_id.in_(list(version_to_qid.keys())))
            .order_by(QuestionOption.question_id, QuestionOption.option_label)
        )
        for opt in opt_rows.scalars().all():
            qid = version_to_qid.get(opt.question_version_id)
            if qid:
                opts_by_qid.setdefault(qid, []).append(opt)

    job_rows = await db.execute(
        select(QuestionJob)
        .where(QuestionJob.question_id.in_(qids))
        .order_by(QuestionJob.question_id, QuestionJob.created_at.desc())
    )
    latest_job_by_qid: dict[UUID, QuestionJob] = {}
    for job in job_rows.scalars().all():
        latest_job_by_qid.setdefault(job.question_id, job)

    batch_ids = [
        job.generation_batch_id
        for job in latest_job_by_qid.values()
        if job.generation_batch_id
    ]
    batch_by_id = {}
    if batch_ids:
        batch_rows = await db.execute(select(GenerationBatch).where(GenerationBatch.id.in_(batch_ids)))
        batch_by_id = {batch.id: batch for batch in batch_rows.scalars().all()}

    consensus_rows = await db.execute(
        select(ConsensusVerdict)
        .where(ConsensusVerdict.question_id.in_(qids))
        .order_by(ConsensusVerdict.question_id, ConsensusVerdict.created_at.desc())
    )
    latest_consensus_by_qid: dict[UUID, ConsensusVerdict] = {}
    for verdict in consensus_rows.scalars().all():
        latest_consensus_by_qid.setdefault(verdict.question_id, verdict)

    run_rows = await db.execute(
        select(ReviewRun)
        .where(ReviewRun.question_id.in_(qids))
        .order_by(ReviewRun.question_id, ReviewRun.started_at.desc())
    )
    latest_run_by_qid: dict[UUID, ReviewRun] = {}
    for run in run_rows.scalars().all():
        latest_run_by_qid.setdefault(run.question_id, run)

    review_results_by_run: dict[UUID, list[LlmReviewResult]] = {}
    run_ids = [run.id for run in latest_run_by_qid.values()]
    if run_ids:
        review_rows = await db.execute(
            select(LlmReviewResult)
            .where(LlmReviewResult.review_run_id.in_(run_ids))
            .order_by(LlmReviewResult.provider_name, LlmReviewResult.model_name)
        )
        for review in review_rows.scalars().all():
            review_results_by_run.setdefault(review.review_run_id, []).append(review)

    source_ids: set[UUID] = set()
    for question in questions:
        job = latest_job_by_qid.get(question.id)
        for raw_id in _source_ids_for_candidate(question, job):
            try:
                source_ids.add(UUID(raw_id))
            except ValueError:
                continue

    source_by_id: dict[UUID, Question] = {}
    if source_ids:
        source_rows = await db.execute(select(Question).where(Question.id.in_(source_ids)))
        source_by_id = {source.id: source for source in source_rows.scalars().all()}

    items = []
    for question in questions:
        annotation_row = ann_map.get(question.latest_annotation_id) if question.latest_annotation_id else None
        annotation = annotation_row.annotation_jsonb if annotation_row else None
        explanation = annotation_row.explanation_jsonb if annotation_row else None
        job = latest_job_by_qid.get(question.id)
        batch = batch_by_id.get(job.generation_batch_id) if job and job.generation_batch_id else None
        consensus = latest_consensus_by_qid.get(question.id)
        review_run = latest_run_by_qid.get(question.id)
        review_results = review_results_by_run.get(review_run.id, []) if review_run else []

        item_source_examples = []
        for raw_id in _source_ids_for_candidate(question, job):
            try:
                source = source_by_id.get(UUID(raw_id))
            except ValueError:
                source = None
            if source:
                item_source_examples.append({
                    "id": str(source.id),
                    "source_release_year": source.source_release_year,
                    "source_test_name": source.source_test_name,
                    "source_exam_code": source.source_exam_code,
                    "source_subject_code": source.source_subject_code,
                    "source_section_code": source.source_section_code,
                    "source_module_code": source.source_module_code,
                    "source_question_number": source.source_question_number,
                    "question_text": source.current_question_text,
                    "passage_text": source.current_passage_text,
                    "correct_option_label": source.current_correct_option_label,
                })
            else:
                item_source_examples.append({"id": raw_id})

        items.append({
            "id": str(question.id),
            "content_origin": question.content_origin,
            "practice_status": question.practice_status,
            "official_overlap_status": question.official_overlap_status,
            "domain": _annotation_domain(annotation),
            "question_text": question.current_question_text,
            "passage_text": question.current_passage_text,
            "paired_passage_text": question.current_paired_passage_text,
            "underlined_text": question.current_underlined_text,
            "source_release_year": question.source_release_year,
            "source_test_name": question.source_test_name,
            "source_exam_code": question.source_exam_code,
            "source_subject_code": question.source_subject_code,
            "source_section_code": question.source_section_code,
            "source_module_code": question.source_module_code,
            "source_question_number": question.source_question_number,
            "correct_option_label": question.current_correct_option_label,
            "explanation_text": question.current_explanation_text,
            "annotation": annotation,
            "annotation_explanation": explanation,
            "options": [
                {
                    "label": opt.option_label,
                    "text": opt.option_text,
                    "is_correct": opt.is_correct,
                    "distractor_type_key": opt.distractor_type_key,
                    "why_plausible": opt.why_plausible,
                    "why_wrong": opt.why_wrong,
                    "student_failure_mode_key": opt.student_failure_mode_key,
                }
                for opt in opts_by_qid.get(question.id, [])
            ],
            "job": None if not job else {
                "id": str(job.id),
                "status": job.status,
                "provider_name": job.provider_name,
                "model_name": job.model_name,
                "generation_request_jsonb": _json_safe(job.generation_request_jsonb or {}),
                "validation_errors_jsonb": _json_safe(job.validation_errors_jsonb or []),
                "created_at": job.created_at.isoformat() if job.created_at else None,
            },
            "batch": None if not batch else {
                "id": str(batch.id),
                "requested_by": batch.requested_by,
                "student_id": batch.student_id,
                "requested_by_user_token": str(batch.requested_by_user_token) if batch.requested_by_user_token else None,
                "release_policy": batch.release_policy,
                "status": batch.status,
            },
            "consensus": None if not consensus else {
                "id": str(consensus.id),
                "review_run_id": str(consensus.review_run_id),
                "reviewer_count": consensus.reviewer_count,
                "average_realism": consensus.average_realism,
                "average_sat_fidelity": consensus.average_sat_fidelity,
                "average_difficulty_match": consensus.average_difficulty_match,
                "average_distractor_quality": consensus.average_distractor_quality,
                "average_taxonomy_match": consensus.average_taxonomy_match,
                "max_copy_risk": consensus.max_copy_risk,
                "accept_votes": consensus.accept_votes,
                "needs_review_votes": consensus.needs_review_votes,
                "reject_votes": consensus.reject_votes,
                "reviewer_disagreement": consensus.reviewer_disagreement,
                "high_disagreement_flag": consensus.high_disagreement_flag,
                "consensus_verdict": consensus.consensus_verdict,
                "reasons_jsonb": _json_safe(consensus.reasons_jsonb or []),
                "created_at": consensus.created_at.isoformat() if consensus.created_at else None,
            },
            "review_run": None if not review_run else {
                "id": str(review_run.id),
                "status": review_run.status,
                "triggered_by": review_run.triggered_by,
                "rubric_version": review_run.rubric_version,
                "started_at": review_run.started_at.isoformat() if review_run.started_at else None,
                "completed_at": review_run.completed_at.isoformat() if review_run.completed_at else None,
            },
            "review_results": [
                {
                    "id": str(review.id),
                    "provider_name": review.provider_name,
                    "model_name": review.model_name,
                    "scores_jsonb": _json_safe(review.scores_jsonb or {}),
                    "verdict": review.verdict,
                    "review_notes": review.review_notes,
                    "review_status": review.review_status,
                    "error_message": review.error_message,
                    "latency_ms": review.latency_ms,
                }
                for review in review_results
            ],
            "source_examples": item_source_examples,
            "created_at": question.created_at.isoformat() if question.created_at else None,
            "updated_at": question.updated_at.isoformat() if question.updated_at else None,
            "rejection_reason": question.rejection_reason,
            "rejected_at": question.rejected_at.isoformat() if question.rejected_at else None,
        })

    return items


def _parse_optional_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {raw!r}")


@router.get("/generated-questions")
async def list_generated_questions(
    generation_batch_id: Optional[str] = None,
    requested_by: Optional[str] = None,
    student_id: Optional[int] = None,
    domain: Optional[str] = None,
    grammar_role_key: Optional[str] = None,
    grammar_focus_key: Optional[str] = None,
    reading_skill_family_key: Optional[str] = None,
    reading_focus_key: Optional[str] = None,
    difficulty: Optional[str] = None,
    generator_provider: Optional[str] = None,
    generator_model: Optional[str] = None,
    reviewer_provider: Optional[str] = None,
    reviewer_model: Optional[str] = None,
    min_average_realism: Optional[float] = None,
    consensus_verdict: Optional[str] = None,
    min_reviewer_disagreement: Optional[float] = None,
    overlap_status: Optional[str] = None,
    practice_status: Optional[str] = Query("draft"),
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    stmt = select(Question).where(Question.content_origin == "generated")
    joined_annotation = False
    joined_job = False
    joined_batch = False
    joined_consensus = False
    joined_review = False

    latest_consensus = (
        select(
            ConsensusVerdict.question_id.label("question_id"),
            func.max(ConsensusVerdict.created_at).label("created_at"),
        )
        .group_by(ConsensusVerdict.question_id)
        .subquery()
    )

    def ensure_annotation():
        nonlocal stmt, joined_annotation
        if not joined_annotation:
            stmt = stmt.join(
                QuestionAnnotation,
                Question.latest_annotation_id == QuestionAnnotation.id,
            )
            joined_annotation = True

    def ensure_job():
        nonlocal stmt, joined_job
        if not joined_job:
            stmt = stmt.join(QuestionJob, QuestionJob.question_id == Question.id)
            joined_job = True

    def ensure_batch():
        nonlocal stmt, joined_batch
        ensure_job()
        if not joined_batch:
            stmt = stmt.join(GenerationBatch, GenerationBatch.id == QuestionJob.generation_batch_id)
            joined_batch = True

    def ensure_consensus():
        nonlocal stmt, joined_consensus
        if not joined_consensus:
            stmt = stmt.outerjoin(latest_consensus, latest_consensus.c.question_id == Question.id)
            stmt = stmt.outerjoin(
                ConsensusVerdict,
                and_(
                    ConsensusVerdict.question_id == Question.id,
                    ConsensusVerdict.created_at == latest_consensus.c.created_at,
                ),
            )
            joined_consensus = True

    if practice_status:
        stmt = stmt.where(Question.practice_status == practice_status)
    if overlap_status:
        stmt = stmt.where(Question.official_overlap_status == overlap_status)
    created_from_dt = _parse_optional_datetime(created_from)
    created_to_dt = _parse_optional_datetime(created_to)
    if created_from_dt:
        stmt = stmt.where(Question.created_at >= created_from_dt)
    if created_to_dt:
        stmt = stmt.where(Question.created_at <= created_to_dt)

    if generation_batch_id:
        ensure_job()
        try:
            stmt = stmt.where(QuestionJob.generation_batch_id == UUID(generation_batch_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid generation_batch_id")
    if generator_provider:
        ensure_job()
        stmt = stmt.where(QuestionJob.provider_name == generator_provider)
    if generator_model:
        ensure_job()
        stmt = stmt.where(QuestionJob.model_name == generator_model)
    if requested_by:
        ensure_batch()
        stmt = stmt.where(GenerationBatch.requested_by == requested_by)
    if student_id is not None:
        ensure_batch()
        stmt = stmt.where(GenerationBatch.student_id == student_id)

    if domain or grammar_role_key or grammar_focus_key or reading_skill_family_key or reading_focus_key or difficulty:
        ensure_annotation()
    if domain == "grammar":
        stmt = stmt.where(QuestionAnnotation.annotation_jsonb["grammar_role_key"].astext.isnot(None))
    elif domain == "reading":
        stmt = stmt.where(QuestionAnnotation.annotation_jsonb["reading_skill_family_key"].astext.isnot(None))
    elif domain not in (None, ""):
        raise HTTPException(status_code=400, detail="domain must be grammar or reading")
    if grammar_role_key:
        stmt = stmt.where(QuestionAnnotation.annotation_jsonb["grammar_role_key"].astext == grammar_role_key)
    if grammar_focus_key:
        stmt = stmt.where(QuestionAnnotation.annotation_jsonb["grammar_focus_key"].astext == grammar_focus_key)
    if reading_skill_family_key:
        stmt = stmt.where(QuestionAnnotation.annotation_jsonb["reading_skill_family_key"].astext == reading_skill_family_key)
    if reading_focus_key:
        stmt = stmt.where(QuestionAnnotation.annotation_jsonb["reading_focus_key"].astext == reading_focus_key)
    if difficulty:
        stmt = stmt.where(QuestionAnnotation.annotation_jsonb["difficulty_overall"].astext == difficulty)

    if consensus_verdict or min_average_realism is not None or min_reviewer_disagreement is not None:
        ensure_consensus()
    if consensus_verdict:
        stmt = stmt.where(ConsensusVerdict.consensus_verdict == consensus_verdict)
    if min_average_realism is not None:
        stmt = stmt.where(ConsensusVerdict.average_realism >= min_average_realism)
    if min_reviewer_disagreement is not None:
        stmt = stmt.where(ConsensusVerdict.reviewer_disagreement >= min_reviewer_disagreement)

    if reviewer_provider or reviewer_model:
        ensure_consensus()
        if not joined_review:
            stmt = stmt.join(LlmReviewResult, LlmReviewResult.review_run_id == ConsensusVerdict.review_run_id)
            joined_review = True
        if reviewer_provider:
            stmt = stmt.where(LlmReviewResult.provider_name == reviewer_provider)
        if reviewer_model:
            stmt = stmt.where(LlmReviewResult.model_name == reviewer_model)

    ensure_consensus()
    risk_rank = case(
        (ConsensusVerdict.consensus_verdict == "blocked_overlap", 0),
        (ConsensusVerdict.consensus_verdict == "reject_recommended", 1),
        (ConsensusVerdict.consensus_verdict == "regenerate_recommended", 2),
        (ConsensusVerdict.consensus_verdict == "insufficient_reviews", 3),
        (ConsensusVerdict.high_disagreement_flag.is_(True), 4),
        else_=5,
    )
    stmt = (
        stmt.order_by(risk_rank, ConsensusVerdict.reviewer_disagreement.desc().nullslast(), Question.created_at.desc())
        .offset(offset)
        .limit(limit + 1)
    )
    result = await db.execute(stmt)
    questions = result.unique().scalars().all()
    has_more = len(questions) > limit
    questions = questions[:limit]
    items = await _serialize_generated_candidates(questions, db)
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "next_offset": offset + limit if has_more else None,
    }


@router.get("/generated-questions/{question_id}")
async def get_generated_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    qid = _parse_uuid(question_id)
    question = await db.get(Question, qid)
    if not question or question.content_origin != "generated":
        raise HTTPException(status_code=404, detail="Generated question not found")
    items = await _serialize_generated_candidates([question], db)
    return items[0]


@router.post("/generated-questions/{question_id}/approve")
async def approve_generated_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    return await approve_question(question_id, db=db, _auth=_auth)


@router.post("/generated-questions/{question_id}/reject")
async def reject_generated_question(
    question_id: str,
    body: RejectQuestionRequest = RejectQuestionRequest(),
    db: AsyncSession = Depends(get_db),
    auth_token: str = Depends(admin_required),
):
    return await reject_question(question_id, body=body, db=db, auth_token=auth_token)


@router.post("/generated-questions/{question_id}/regenerate")
async def regenerate_generated_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    from app.routers import generate as generate_router

    qid = _parse_uuid(question_id)
    question = await db.get(Question, qid)
    if not question or question.content_origin != "generated":
        raise HTTPException(status_code=404, detail="Generated question not found")

    child_result = await db.execute(
        select(Question.id).where(Question.derived_from_question_id == qid)
    )
    child_count = len(child_result.scalars().all())
    queued_result = await db.execute(
        select(QuestionJob.id).where(
            QuestionJob.job_type == "generate",
            QuestionJob.question_id.is_(None),
            QuestionJob.status.in_(
                (
                    "pending",
                    "generating",
                    "retrying",
                    "extracting",
                    "annotating",
                    "overlap_checking",
                    "validating",
                )
            ),
            QuestionJob.generation_request_jsonb["derived_from_question_id"].astext == str(qid),
        )
    )
    queued_count = len(queued_result.scalars().all())
    if child_count + queued_count >= REGENERATE_MAX_ATTEMPTS_PER_QUESTION:
        raise HTTPException(
            status_code=409,
            detail=(
                "Regenerate limit reached for this question "
                f"({REGENERATE_MAX_ATTEMPTS_PER_QUESTION} attempts)"
            ),
        )

    job_result = await db.execute(
        select(QuestionJob)
        .where(QuestionJob.question_id == qid)
        .order_by(QuestionJob.created_at.desc())
        .limit(1)
    )
    source_job = job_result.scalars().first()
    if source_job is None or not isinstance(source_job.generation_request_jsonb, dict):
        raise HTTPException(status_code=409, detail="No generation request snapshot available")
    source_request = dict(source_job.generation_request_jsonb)
    if isinstance(question.generation_source_set, dict):
        source_request.update(question.generation_source_set)

    now = datetime.now(timezone.utc)
    source_request.pop("source_question_ids", None)
    source_request["requested_count"] = 1
    source_request.setdefault("release_policy", "admin_review_required")
    source_request["provider_name"] = source_request.get("provider_name") or source_job.provider_name
    source_request["model_name"] = source_request.get("model_name") or source_job.model_name
    try:
        batch_request = GenerationBatchRequest.model_validate(source_request)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error": "Stored generation request is no longer valid", "message": str(exc)},
        )

    domain = generate_router._domain_for_batch(batch_request)
    selected_source_ids = await generate_router._select_source_question_ids_for_batch(
        db,
        batch_request,
        domain,
        [],
    )

    request_jsonb = batch_request.model_dump()
    request_jsonb["requested_by"] = "admin"
    request_jsonb["student_id"] = None
    request_jsonb["requested_by_user_token"] = None

    batch = GenerationBatch(
        id=uuid.uuid4(),
        requested_count=1,
        request_jsonb=request_jsonb,
        requested_by="admin",
        student_id=None,
        requested_by_user_token=None,
        release_policy=request_jsonb["release_policy"],
        regenerate_source_batch_id=source_job.generation_batch_id,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(batch)

    retry_request = dict(request_jsonb)
    retry_request.pop("requested_count", None)
    retry_request["source_question_ids"] = selected_source_ids[0] if selected_source_ids else []
    retry_request["retry_attempt"] = 0
    retry_request["provider_name"] = retry_request.get("provider_name") or source_job.provider_name
    retry_request["model_name"] = retry_request.get("model_name") or source_job.model_name
    retry_request["requested_by"] = "admin"
    retry_request["student_id"] = None
    retry_request["requested_by_user_token"] = None
    retry_request["derived_from_question_id"] = str(qid)
    retry_request["seed"] = uuid.uuid4().int % 2_147_483_647
    retry_request.setdefault("temperature", 0.7)

    job = QuestionJob(
        id=uuid.uuid4(),
        job_type="generate",
        content_origin="generated",
        input_format="spec",
        status="pending",
        provider_name=retry_request["provider_name"],
        model_name=retry_request["model_name"],
        prompt_version=source_job.prompt_version,
        rules_version=source_job.rules_version,
        generation_batch_id=batch.id,
        generation_request_jsonb=retry_request,
        retry_count=0,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(generate_router._run_batch_pipeline(batch.id)).add_done_callback(
        generate_router._log_task_exception
    )

    return {
        "source_question_id": str(qid),
        "batch_id": str(batch.id),
        "job_id": str(job.id),
        "status": batch.status,
    }


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

    audit_before = {
        "question_text": q.current_question_text,
        "passage_text": q.current_passage_text,
        "correct_option_label": q.current_correct_option_label,
        "explanation_text": q.current_explanation_text,
        "practice_status": q.practice_status,
    }
    audit_after = {k: changes[k] for k in changes if k != "change_notes"}
    await _write_admin_audit(
        qid=qid,
        admin_token=_auth,
        action="edit",
        before=audit_before,
        after=audit_after,
        fields_changed=list(audit_after.keys()),
        change_notes=changes.get("change_notes"),
        question_version_id=new_version.id,
        db=db,
    )

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
    if q.content_origin == "generated":
        generation_batch = await _latest_generation_batch_for_question(qid, db)
        if generation_batch and generation_batch.release_policy == "dry_run":
            raise HTTPException(
                status_code=409,
                detail="Dry-run generated questions cannot be approved",
            )

    prev_status = q.practice_status
    q.practice_status = "active"
    q.updated_at = datetime.now(timezone.utc)
    admin_decision_id, override_count = await _write_reviewer_admin_overrides(
        qid=qid,
        admin_verdict="accept",
        admin_token=_auth,
        admin_notes=None,
        db=db,
    )
    await _write_admin_audit(
        qid=qid,
        admin_token=_auth,
        action="approve",
        before={"practice_status": prev_status},
        after={"practice_status": "active"},
        fields_changed=["practice_status"],
        db=db,
    )
    await db.commit()
    return {
        "id": str(q.id),
        "practice_status": "active",
        "admin_decision_id": str(admin_decision_id),
        "reviewer_admin_override_count": override_count,
    }


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
    prev_status = q.practice_status
    q.practice_status = "rejected"
    q.rejection_reason = body.reason
    q.rejected_at = now
    q.rejected_by_admin_token = auth_token
    q.updated_at = now
    admin_decision_id, override_count = await _write_reviewer_admin_overrides(
        qid=qid,
        admin_verdict="reject",
        admin_token=auth_token,
        admin_notes=body.reason,
        db=db,
    )
    await _write_admin_audit(
        qid=qid,
        admin_token=auth_token,
        action="reject",
        before={"practice_status": prev_status},
        after={"practice_status": "rejected", "rejection_reason": body.reason},
        fields_changed=["practice_status", "rejection_reason"],
        change_notes=body.reason,
        db=db,
    )

    await db.commit()
    return {
        "id": str(q.id),
        "practice_status": "rejected",
        "rejected_at": now.isoformat(),
        "rejection_reason": body.reason,
        "admin_decision_id": str(admin_decision_id),
        "reviewer_admin_override_count": override_count,
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

    prev_status = q.official_overlap_status
    q.official_overlap_status = "confirmed"
    q.canonical_official_question_id = relations[0].to_question_id
    for rel in relations:
        rel.is_human_confirmed = True
    q.updated_at = datetime.now(timezone.utc)
    await _write_admin_audit(
        qid=qid,
        admin_token=_auth,
        action="confirm_overlap",
        before={"official_overlap_status": prev_status},
        after={"official_overlap_status": "confirmed",
               "canonical_official_question_id": str(relations[0].to_question_id)},
        fields_changed=["official_overlap_status", "canonical_official_question_id"],
        db=db,
    )
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
    prev_status = q.official_overlap_status
    q.official_overlap_status = "none"
    q.canonical_official_question_id = None
    q.updated_at = datetime.now(timezone.utc)
    await _write_admin_audit(
        qid=qid,
        admin_token=_auth,
        action="clear_overlap",
        before={"official_overlap_status": prev_status},
        after={"official_overlap_status": "none"},
        fields_changed=["official_overlap_status"],
        db=db,
    )
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


# ---------------------------------------------------------------------------
# Phase 9: Generation Quality Analytics endpoints
# ---------------------------------------------------------------------------


def _days_cutoff(days: int):
    from datetime import timedelta
    return datetime.now(timezone.utc) - timedelta(days=days)


@router.get("/analytics/generation", response_model=GenerationAnalyticsResponse)
async def generation_analytics(
    days: int = Query(30, ge=1, le=365, description="Lookback window in days"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Overall generation quality metrics for the admin dashboard."""
    cutoff = _days_cutoff(days)
    settings = get_settings()

    # --- Question status counts ---
    status_rows = await db.execute(
        select(Question.practice_status, func.count().label("cnt"))
        .where(
            Question.content_origin == "generated",
            Question.created_at >= cutoff,
        )
        .group_by(Question.practice_status)
    )
    status_counts: dict[str, int] = {row.practice_status: row.cnt for row in status_rows.all()}
    approved_count = status_counts.get("active", 0)
    rejected_count = status_counts.get("rejected", 0)
    draft_count = status_counts.get("draft", 0)
    generated_count = sum(status_counts.values())
    total_decided = approved_count + rejected_count
    acceptance_rate = round(approved_count / total_decided, 4) if total_decided else 0.0

    # --- Reviewed count (questions with at least one completed review run) ---
    reviewed_result = await db.execute(
        select(func.count(func.distinct(ReviewRun.question_id)))
        .join(Question, Question.id == ReviewRun.question_id)
        .where(
            Question.content_origin == "generated",
            ReviewRun.status.in_(("complete", "partial")),
            ReviewRun.started_at >= cutoff,
        )
    )
    reviewed_count = reviewed_result.scalars().first() or 0

    # --- Failed count (jobs that hit failed_permanent without a saved question) ---
    failed_result = await db.execute(
        select(func.count())
        .select_from(QuestionJob)
        .where(
            QuestionJob.status == "failed_permanent",
            QuestionJob.question_id.is_(None),
            QuestionJob.created_at >= cutoff,
        )
    )
    failed_count = failed_result.scalars().first() or 0

    # --- Copy-risk failures (consensus_verdict = reject_recommended from copy risk) ---
    copy_risk_result = await db.execute(
        select(func.count(func.distinct(ConsensusVerdict.question_id)))
        .join(Question, Question.id == ConsensusVerdict.question_id)
        .where(
            Question.content_origin == "generated",
            ConsensusVerdict.consensus_verdict == "reject_recommended",
            ConsensusVerdict.max_copy_risk >= settings.generation_max_copy_risk_score,
            ConsensusVerdict.created_at >= cutoff,
        )
    )
    copy_risk_failures = copy_risk_result.scalars().first() or 0

    # --- Average reviewer disagreement ---
    disagreement_result = await db.execute(
        select(func.avg(ConsensusVerdict.reviewer_disagreement))
        .join(Question, Question.id == ConsensusVerdict.question_id)
        .where(
            Question.content_origin == "generated",
            ConsensusVerdict.reviewer_disagreement.isnot(None),
            ConsensusVerdict.created_at >= cutoff,
        )
    )
    avg_disagreement_raw = disagreement_result.scalars().first()
    avg_reviewer_disagreement = round(float(avg_disagreement_raw), 4) if avg_disagreement_raw is not None else None

    # --- Acceptance rate by generator provider/model ---
    gen_model_rows = await db.execute(
        select(
            QuestionJob.provider_name,
            QuestionJob.model_name,
            func.count().label("total"),
            func.sum(case((Question.practice_status == "active", 1), else_=0)).label("approved"),
            func.sum(case((Question.practice_status == "rejected", 1), else_=0)).label("rejected"),
        )
        .join(Question, Question.id == QuestionJob.question_id)
        .where(
            Question.content_origin == "generated",
            QuestionJob.created_at >= cutoff,
        )
        .group_by(QuestionJob.provider_name, QuestionJob.model_name)
    )
    by_generator_model = []
    for row in gen_model_rows.all():
        decided = row.approved + row.rejected
        by_generator_model.append(GeneratorModelStats(
            provider_name=row.provider_name,
            model_name=row.model_name,
            generated_count=row.total,
            approved_count=row.approved,
            rejected_count=row.rejected,
            acceptance_rate=round(row.approved / decided, 4) if decided else 0.0,
        ))

    # --- Rejection reason distribution ---
    reason_rows = await db.execute(
        select(Question.rejection_reason, func.count().label("cnt"))
        .where(
            Question.content_origin == "generated",
            Question.practice_status == "rejected",
            Question.created_at >= cutoff,
        )
        .group_by(Question.rejection_reason)
        .order_by(func.count().desc())
    )
    rejection_reasons = [
        RejectionReasonCount(reason=row.rejection_reason, count=row.cnt)
        for row in reason_rows.all()
    ]

    return GenerationAnalyticsResponse(
        days=days,
        generated_count=generated_count,
        reviewed_count=reviewed_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        failed_count=failed_count,
        acceptance_rate=acceptance_rate,
        copy_risk_failures=copy_risk_failures,
        avg_reviewer_disagreement=avg_reviewer_disagreement,
        by_generator_model=by_generator_model,
        rejection_reasons=rejection_reasons,
    )


@router.get("/analytics/review", response_model=ReviewAnalyticsResponse)
async def review_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Per-reviewer-model quality and admin override rate metrics."""
    cutoff = _days_cutoff(days)

    # --- Per-reviewer average scores ---
    reviewer_rows = await db.execute(
        select(
            LlmReviewResult.provider_name,
            LlmReviewResult.model_name,
            func.count().label("review_count"),
            func.avg(
                cast(LlmReviewResult.scores_jsonb["realism_score"].astext, Float)
            ).label("avg_realism"),
            func.avg(
                cast(LlmReviewResult.scores_jsonb["sat_fidelity_score"].astext, Float)
            ).label("avg_sat_fidelity"),
            func.avg(
                cast(LlmReviewResult.scores_jsonb["difficulty_match_score"].astext, Float)
            ).label("avg_difficulty_match"),
            func.avg(
                cast(LlmReviewResult.scores_jsonb["distractor_quality_score"].astext, Float)
            ).label("avg_distractor_quality"),
            func.avg(
                cast(LlmReviewResult.scores_jsonb["taxonomy_match_score"].astext, Float)
            ).label("avg_taxonomy_match"),
        )
        .where(
            LlmReviewResult.review_status == "ok",
            LlmReviewResult.created_at >= cutoff,
        )
        .group_by(LlmReviewResult.provider_name, LlmReviewResult.model_name)
    )
    reviewer_score_map: dict = {}
    for row in reviewer_rows.all():
        key = (row.provider_name, row.model_name)
        reviewer_score_map[key] = {
            "review_count": row.review_count,
            "avg_realism": round(float(row.avg_realism), 4) if row.avg_realism is not None else None,
            "avg_sat_fidelity": round(float(row.avg_sat_fidelity), 4) if row.avg_sat_fidelity is not None else None,
            "avg_difficulty_match": round(float(row.avg_difficulty_match), 4) if row.avg_difficulty_match is not None else None,
            "avg_distractor_quality": round(float(row.avg_distractor_quality), 4) if row.avg_distractor_quality is not None else None,
            "avg_taxonomy_match": round(float(row.avg_taxonomy_match), 4) if row.avg_taxonomy_match is not None else None,
        }

    # --- Admin override rate per reviewer model ---
    override_rows = await db.execute(
        select(
            LlmReviewResult.provider_name,
            LlmReviewResult.model_name,
            func.count().label("total"),
            func.sum(
                case((ReviewerAdminOverride.override_direction == "reviewer_correct", 1), else_=0)
            ).label("correct_count"),
        )
        .join(ReviewerAdminOverride, ReviewerAdminOverride.llm_review_result_id == LlmReviewResult.id)
        .where(ReviewerAdminOverride.created_at >= cutoff)
        .group_by(LlmReviewResult.provider_name, LlmReviewResult.model_name)
    )
    override_map: dict = {}
    for row in override_rows.all():
        key = (row.provider_name, row.model_name)
        override_rate = round(1.0 - (row.correct_count / row.total), 4) if row.total else 0.0
        override_map[key] = {
            "total_overrides": row.total,
            "correct_count": row.correct_count,
            "override_rate": override_rate,
        }

    # Merge reviewer stats
    all_keys = set(reviewer_score_map.keys()) | set(override_map.keys())
    by_reviewer_model = []
    for key in sorted(all_keys):
        scores = reviewer_score_map.get(key, {})
        overrides = override_map.get(key, {})
        provider, model = key
        by_reviewer_model.append(ReviewerModelStats(
            provider_name=provider,
            model_name=model,
            review_count=scores.get("review_count", 0),
            avg_realism=scores.get("avg_realism"),
            avg_sat_fidelity=scores.get("avg_sat_fidelity"),
            avg_difficulty_match=scores.get("avg_difficulty_match"),
            avg_distractor_quality=scores.get("avg_distractor_quality"),
            avg_taxonomy_match=scores.get("avg_taxonomy_match"),
            override_rate=overrides.get("override_rate"),
            total_overrides=overrides.get("total_overrides", 0),
            correct_count=overrides.get("correct_count", 0),
        ))

    # --- Token usage by provider ---
    token_rows = await db.execute(
        select(
            LlmReviewResult.provider_name,
            func.count().label("review_count"),
            func.sum(
                _review_token_expr("input", "input_tokens")
            ).label("input_tokens"),
            func.sum(
                _review_token_expr("output", "output_tokens")
            ).label("output_tokens"),
        )
        .where(
            LlmReviewResult.token_usage_jsonb.isnot(None),
            LlmReviewResult.created_at >= cutoff,
        )
        .group_by(LlmReviewResult.provider_name)
    )
    token_usage = [
        TokenUsageByProvider(
            provider_name=row.provider_name,
            review_count=row.review_count,
            total_input_tokens=int(row.input_tokens or 0),
            total_output_tokens=int(row.output_tokens or 0),
        )
        for row in token_rows.all()
    ]

    return ReviewAnalyticsResponse(
        days=days,
        by_reviewer_model=by_reviewer_model,
        token_usage=token_usage,
    )


@router.get("/analytics/batches", response_model=BatchAnalyticsResponse)
async def batch_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Batch-level aggregate metrics: requested vs created, review latency, token usage."""
    cutoff = _days_cutoff(days)

    # --- Batch aggregates ---
    agg_result = await db.execute(
        select(
            func.count().label("batch_count"),
            func.sum(GenerationBatch.requested_count).label("total_requested"),
            func.sum(GenerationBatch.created_count).label("total_created"),
            func.sum(GenerationBatch.failed_count).label("total_failed"),
        )
        .where(GenerationBatch.created_at >= cutoff)
    )
    agg = agg_result.first()  # may be None when DB is empty

    decision_result = await db.execute(
        select(
            func.sum(case((Question.practice_status == "active", 1), else_=0)).label("total_accepted"),
            func.sum(case((Question.practice_status == "rejected", 1), else_=0)).label("total_rejected"),
        )
        .select_from(GenerationBatch)
        .join(QuestionJob, QuestionJob.generation_batch_id == GenerationBatch.id)
        .join(Question, Question.id == QuestionJob.question_id)
        .where(
            GenerationBatch.created_at >= cutoff,
            Question.content_origin == "generated",
        )
    )
    decided = decision_result.first()

    # --- Average review latency (ms) ---
    latency_result = await db.execute(
        select(
            func.avg(
                func.extract("epoch", ReviewRun.completed_at - ReviewRun.started_at) * 1000
            ).label("avg_ms")
        )
        .where(
            ReviewRun.status.in_(("complete", "partial")),
            ReviewRun.completed_at.isnot(None),
            ReviewRun.started_at >= cutoff,
        )
    )
    avg_latency_raw = latency_result.scalars().first()
    avg_review_latency_ms = round(float(avg_latency_raw), 1) if avg_latency_raw is not None else None

    aggregates = BatchAggregates(
        batch_count=getattr(agg, "batch_count", None) or 0,
        total_requested=int(getattr(agg, "total_requested", None) or 0),
        total_created=int(getattr(agg, "total_created", None) or 0),
        total_accepted=int(getattr(decided, "total_accepted", None) or 0),
        total_rejected=int(getattr(decided, "total_rejected", None) or 0),
        total_failed=int(getattr(agg, "total_failed", None) or 0),
        avg_review_latency_ms=avg_review_latency_ms,
    )

    # --- Token usage by provider (same query as review analytics) ---
    token_rows = await db.execute(
        select(
            LlmReviewResult.provider_name,
            func.count().label("review_count"),
            func.sum(
                _review_token_expr("input", "input_tokens")
            ).label("input_tokens"),
            func.sum(
                _review_token_expr("output", "output_tokens")
            ).label("output_tokens"),
        )
        .where(
            LlmReviewResult.token_usage_jsonb.isnot(None),
            LlmReviewResult.created_at >= cutoff,
        )
        .group_by(LlmReviewResult.provider_name)
    )
    token_usage = [
        TokenUsageByProvider(
            provider_name=row.provider_name,
            review_count=row.review_count,
            total_input_tokens=int(row.input_tokens or 0),
            total_output_tokens=int(row.output_tokens or 0),
        )
        for row in token_rows.all()
    ]

    return BatchAnalyticsResponse(
        days=days,
        aggregates=aggregates,
        token_usage=token_usage,
    )


@router.get("/analytics/trends", response_model=TrendAnalyticsResponse)
async def trend_analytics(
    days: int = Query(30, ge=7, le=365),
    granularity: str = Query("week", pattern="^(day|week)$"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Generation quality trend over time, bucketed by day or week."""
    cutoff = _days_cutoff(days)
    trunc = "week" if granularity == "week" else "day"

    trend_rows = await db.execute(
        select(
            func.date_trunc(trunc, Question.created_at).label("period"),
            func.count().label("generated"),
            func.sum(case((Question.practice_status == "active", 1), else_=0)).label("approved"),
            func.sum(case((Question.practice_status == "rejected", 1), else_=0)).label("rejected"),
        )
        .where(
            Question.content_origin == "generated",
            Question.created_at >= cutoff,
        )
        .group_by(text("1"))
        .order_by(text("1"))
    )

    points = []
    for row in trend_rows.all():
        decided = row.approved + row.rejected
        points.append(GenerationTrendPoint(
            period=row.period.isoformat() if row.period else "",
            generated=row.generated,
            approved=row.approved,
            rejected=row.rejected,
            acceptance_rate=round(row.approved / decided, 4) if decided else 0.0,
        ))

    return TrendAnalyticsResponse(days=days, granularity=granularity, points=points)


@router.get("/analytics/export")
async def analytics_export(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Full analytics export as JSON for offline analysis."""
    cutoff = _days_cutoff(days)

    # Fetch all generated questions with their job info for export
    rows = await db.execute(
        select(
            Question.id,
            Question.practice_status,
            Question.content_origin,
            Question.official_overlap_status,
            Question.rejection_reason,
            Question.rejected_at,
            Question.created_at,
            QuestionJob.provider_name,
            QuestionJob.model_name,
        )
        .outerjoin(QuestionJob, and_(
            QuestionJob.question_id == Question.id,
            QuestionJob.job_type == "generate",
        ))
        .where(
            Question.content_origin == "generated",
            Question.created_at >= cutoff,
        )
        .order_by(Question.created_at.desc())
    )

    questions_export = []
    for row in rows.all():
        # Get latest consensus verdict for this question
        cv_result = await db.execute(
            select(ConsensusVerdict)
            .where(ConsensusVerdict.question_id == row.id)
            .order_by(ConsensusVerdict.created_at.desc())
            .limit(1)
        )
        cv = cv_result.scalars().first()

        questions_export.append({
            "question_id": str(row.id),
            "practice_status": row.practice_status,
            "overlap_status": row.official_overlap_status,
            "rejection_reason": row.rejection_reason,
            "rejected_at": row.rejected_at.isoformat() if row.rejected_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "generator_provider": row.provider_name,
            "generator_model": row.model_name,
            "consensus_verdict": cv.consensus_verdict if cv else None,
            "avg_realism": cv.average_realism if cv else None,
            "max_copy_risk": cv.max_copy_risk if cv else None,
            "reviewer_disagreement": cv.reviewer_disagreement if cv else None,
            "high_disagreement": cv.high_disagreement_flag if cv else None,
        })

    return {
        "days": days,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "question_count": len(questions_export),
        "questions": questions_export,
    }


# ---------------------------------------------------------------------------
# Phase 10: Controlled auto-release kill switch and status
# ---------------------------------------------------------------------------

@router.get("/generation/auto-release/status")
async def get_auto_release_status(_admin=Depends(admin_required)):
    """Return current auto-release configuration and runtime state."""
    from app.review import auto_release as ar
    settings = get_settings()
    return {
        "config_enabled": settings.generation_auto_release_enabled,
        "runtime_disabled": ar._auto_release_disabled,
        "effective_enabled": settings.generation_auto_release_enabled and not ar._auto_release_disabled,
        "min_reviews_required": settings.generation_auto_release_min_reviews,
        "min_accept_rate": settings.generation_auto_release_min_accept_rate,
        "allowed_targets_raw": settings.generation_auto_release_allowed_targets,
    }


@router.post("/generation/auto-release/disable")
async def disable_auto_release(_admin=Depends(admin_required)):
    """Runtime kill switch: immediately disable auto-release in this process.

    Takes effect instantly without a restart. Set
    GENERATION_AUTO_RELEASE_ENABLED=false in your environment file to
    persist the change across restarts.
    """
    from app.review import auto_release as ar
    ar._auto_release_disabled = True
    return {
        "status": "disabled",
        "message": (
            "Auto-release disabled for this process. "
            "Set GENERATION_AUTO_RELEASE_ENABLED=false to persist across restarts."
        ),
    }


@router.post("/generation/auto-release/enable")
async def enable_auto_release(_admin=Depends(admin_required)):
    """Re-enable auto-release after a runtime disable.

    Note: the global config flag ``GENERATION_AUTO_RELEASE_ENABLED`` must
    also be true for auto-release to actually fire.
    """
    from app.review import auto_release as ar
    ar._auto_release_disabled = False
    settings = get_settings()
    return {
        "status": "enabled",
        "effective_enabled": settings.generation_auto_release_enabled,
        "message": (
            "Runtime override cleared. Auto-release will fire if "
            "GENERATION_AUTO_RELEASE_ENABLED is also true."
        ),
    }


@router.get("/generation/auto-release/audit")
async def list_auto_release_audit(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=500),
    _admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """List recent auto-release events for auditing."""
    cutoff = _days_cutoff(days)
    result = await db.execute(
        select(AutoReleaseAuditLog)
        .where(AutoReleaseAuditLog.released_at >= cutoff)
        .order_by(AutoReleaseAuditLog.released_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return {
        "days": days,
        "count": len(rows),
        "events": [
            {
                "id": str(r.id),
                "question_id": str(r.question_id),
                "generation_batch_id": str(r.generation_batch_id) if r.generation_batch_id else None,
                "generator_provider_name": r.generator_provider_name,
                "generator_model_name": r.generator_model_name,
                "generator_accept_count": r.generator_accept_count,
                "generator_total_count": r.generator_total_count,
                "generator_accept_rate": r.generator_accept_rate,
                "release_policy": r.release_policy,
                "reasons_jsonb": r.reasons_jsonb,
                "released_at": r.released_at.isoformat() if r.released_at else None,
            }
            for r in rows
        ],
    }


# ── Phase 5: Cohort Analytics ─────────────────────────────────────────────────

@router.get("/analytics/weak-spots", response_model=CohortWeakSpotsResponse)
async def cohort_weak_spots(
    limit: int = Query(default=20, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    System-wide question and focus-area miss rates across all students.
    Returns the top N most-missed questions and all focus areas ranked by miss rate.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Per-question miss rates
    q_result = await db.execute(
        select(
            UserProgress.question_id,
            UserProgress.question_domain,
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == False, 1), else_=0)).label("misses"),  # noqa: E712
        )
        .group_by(UserProgress.question_id, UserProgress.question_domain)
        .having(func.count() >= 3)  # minimum 3 attempts to surface
        .order_by(
            (func.sum(case((UserProgress.is_correct == False, 1), else_=0)) /
             cast(func.count(), Float)).desc()
        )
        .limit(limit)
    )
    q_rows = q_result.all()

    # Pull focus keys for those questions via annotation join
    question_ids = [str(r.question_id) for r in q_rows]
    focus_map: dict[str, str] = {}
    if question_ids:
        ann_result = await db.execute(
            select(Question.id, QuestionAnnotation.annotation_jsonb)
            .join(QuestionAnnotation, Question.latest_annotation_id == QuestionAnnotation.id)
            .where(Question.id.in_([r.question_id for r in q_rows]))
        )
        for qid, annotation_jsonb in ann_result.all():
            annotation = annotation_jsonb or {}
            focus_map[str(qid)] = (
                annotation.get("grammar_focus_key")
                or annotation.get("reading_focus_key")
                or ""
            )

    question_misses = [
        QuestionMissRate(
            question_id=str(r.question_id),
            focus_key=focus_map.get(str(r.question_id)),
            domain=r.question_domain,
            total_attempts=r.total,
            miss_count=int(r.misses or 0),
            miss_rate=round(int(r.misses or 0) / r.total, 4) if r.total else 0.0,
            rank=i + 1,
        )
        for i, r in enumerate(q_rows)
    ]

    # Per-focus-area miss rates (grammar)
    g_result = await db.execute(
        select(
            UserProgress.missed_grammar_focus_key,
            func.count().label("total"),
            func.count(UserProgress.user_id.distinct()).label("unique_students"),
            func.sum(case((UserProgress.is_correct == False, 1), else_=0)).label("misses"),  # noqa: E712
        )
        .where(UserProgress.missed_grammar_focus_key.isnot(None))
        .group_by(UserProgress.missed_grammar_focus_key)
    )

    r_result = await db.execute(
        select(
            UserProgress.missed_reading_focus_key,
            func.count().label("total"),
            func.count(UserProgress.user_id.distinct()).label("unique_students"),
            func.sum(case((UserProgress.is_correct == False, 1), else_=0)).label("misses"),  # noqa: E712
        )
        .where(UserProgress.missed_reading_focus_key.isnot(None))
        .group_by(UserProgress.missed_reading_focus_key)
    )

    focus_misses: list[FocusAreaMissRate] = []
    for row in g_result.all():
        total = row.total
        misses = int(row.misses or 0)
        focus_misses.append(FocusAreaMissRate(
            focus_key=row.missed_grammar_focus_key,
            domain="grammar",
            total_attempts=total,
            unique_students=row.unique_students,
            miss_count=misses,
            miss_rate=round(misses / total, 4) if total else 0.0,
        ))
    for row in r_result.all():
        total = row.total
        misses = int(row.misses or 0)
        focus_misses.append(FocusAreaMissRate(
            focus_key=row.missed_reading_focus_key,
            domain="reading",
            total_attempts=total,
            unique_students=row.unique_students,
            miss_count=misses,
            miss_rate=round(misses / total, 4) if total else 0.0,
        ))
    focus_misses.sort(key=lambda f: f.miss_rate, reverse=True)

    return CohortWeakSpotsResponse(
        generated_at=now,
        question_wise_misses=question_misses,
        focus_area_misses=focus_misses,
    )


@router.get("/analytics/student-cohort-summary", response_model=CohortSummaryResponse)
async def student_cohort_summary(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    High-level cohort health: student counts, accuracy distribution, domain breakdown.
    """
    now = datetime.now(timezone.utc)

    # Total distinct students with any progress
    total_r = await db.execute(
        select(func.count(UserProgress.user_id.distinct()))
    )
    total_students = total_r.scalars().first() or 0

    # Active this week
    week_ago = now - __import__("datetime").timedelta(days=7)
    active_r = await db.execute(
        select(func.count(UserProgress.user_id.distinct()))
        .where(UserProgress.timestamp >= week_ago)
    )
    active_this_week = active_r.scalars().first() or 0

    # Per-student accuracy — needed for distribution
    per_student_r = await db.execute(
        select(
            UserProgress.user_id,
            func.count().label("total"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .group_by(UserProgress.user_id)
    )
    per_student = per_student_r.all()

    accuracies = [
        int(r.correct or 0) / r.total for r in per_student if r.total > 0
    ]
    avg_accuracy = round(sum(accuracies) / len(accuracies), 4) if accuracies else 0.0

    buckets_def = [
        ("0–50%", 0.0, 0.5),
        ("50–60%", 0.5, 0.6),
        ("60–70%", 0.6, 0.7),
        ("70–80%", 0.7, 0.8),
        ("80–90%", 0.8, 0.9),
        ("90–100%", 0.9, 1.01),
    ]
    distribution = [
        AccuracyBucket(
            range=label,
            student_count=sum(1 for a in accuracies if lo <= a < hi),
        )
        for label, lo, hi in buckets_def
    ]

    # Domain breakdown
    domain_r = await db.execute(
        select(
            UserProgress.question_domain,
            func.count().label("total"),
            func.count(UserProgress.user_id.distinct()).label("unique_students"),
            func.sum(case((UserProgress.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .where(UserProgress.question_domain.isnot(None))
        .group_by(UserProgress.question_domain)
    )
    domain_perf: dict[str, DomainPerformance] = {}
    for row in domain_r.all():
        total = row.total
        correct = int(row.correct or 0)
        domain_perf[row.question_domain] = DomainPerformance(
            accuracy=round(correct / total, 4) if total else 0.0,
            attempts=total,
            unique_students=row.unique_students,
        )

    return CohortSummaryResponse(
        generated_at=now.isoformat(),
        total_students=total_students,
        active_this_week=active_this_week,
        average_accuracy=avg_accuracy,
        accuracy_distribution=distribution,
        domain_performance=domain_perf,
    )


@router.get("/analytics/trap-analytics", response_model=CohortTrapAnalyticsResponse)
async def cohort_trap_analytics(
    min_encounters: int = Query(default=5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    System-wide trap effectiveness: which distractor traps catch the most students.
    Returns most common traps by volume and most effective traps by fall rate.
    """
    now = datetime.now(timezone.utc).isoformat()

    result = await db.execute(
        select(
            UserProgress.missed_syntactic_trap_key,
            func.count().label("encounters"),
            func.count(UserProgress.user_id.distinct()).label("unique_students"),
            func.sum(case((UserProgress.is_correct == False, 1), else_=0)).label("falls"),  # noqa: E712
        )
        .where(UserProgress.missed_syntactic_trap_key.isnot(None))
        .group_by(UserProgress.missed_syntactic_trap_key)
    )
    rows = result.all()

    stats: list[TrapCohortStat] = []
    for row in rows:
        encounters = row.encounters
        falls = int(row.falls or 0)
        stats.append(TrapCohortStat(
            trap_type=row.missed_syntactic_trap_key,
            total_encounters=encounters,
            unique_students=row.unique_students,
            total_fall_count=falls,
            fall_rate=round(falls / encounters, 4) if encounters else 0.0,
        ))

    total_encounters = sum(s.total_encounters for s in stats)

    most_common = sorted(stats, key=lambda s: s.total_encounters, reverse=True)[:10]
    most_effective = sorted(
        [s for s in stats if s.total_encounters >= min_encounters],
        key=lambda s: s.fall_rate,
        reverse=True,
    )[:10]

    return CohortTrapAnalyticsResponse(
        generated_at=now,
        total_trap_encounters=total_encounters,
        most_common_traps=most_common,
        most_effective_traps=most_effective,
    )


@router.post("/questions/{question_id}/annotate-spans")
async def trigger_span_annotation(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(admin_required),
):
    """Run Pass 3 span annotation for a single grammar question.

    Tokenizes the passage, assigns anatomy + concept_tag arrays to each token,
    validates the result, and writes passage_spans to question_annotations.
    On validation failure the question is added to span_review_queue.
    """
    from app.services.span_annotator import annotate_spans
    qid = _parse_uuid(question_id)
    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    try:
        result = await annotate_spans(qid, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result.get("status") == "failed":
        raise HTTPException(status_code=422, detail=result)
    return result
