"""Review swarm runner — orchestrates multi-model review of generated questions."""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session
from app.llm.factory import get_provider
from app.llm.retry import with_retry
from app.models.db import (
    Question, QuestionAnnotation, QuestionOption, QuestionVersion,
    QuestionJob, GenerationBatch, ReviewRun, LlmReviewResult,
)
from app.models.ontology import (
    REVIEW_RUN_STATUSES, REVIEW_STATUSES, REVIEW_VERDICTS, TRIGGERED_BY_VALUES,
)
from app.prompts.review_prompt import (
    build_review_prompt, RUBRIC_VERSION, RULES_VERSIONS,
)
from app.review.parser import parse_review_json, ReviewParseError

logger = logging.getLogger(__name__)

# Maximum JSON tokens for review output (7 scores + verdict + reasons is compact).
_REVIEW_MAX_TOKENS = 4096
_REVIEW_TEMPERATURE = 0.2


def _provider_config(provider_name: str, settings) -> tuple[str, str]:
    """Return (api_key, model) for a review provider."""
    if provider_name == "openai":
        return settings.openai_api_key, settings.generation_review_openai_model
    if provider_name == "anthropic":
        return settings.anthropic_api_key, settings.generation_review_anthropic_model
    if provider_name == "ollama":
        return "", settings.generation_review_ollama_model
    raise ValueError(f"Unknown review provider: {provider_name}")


def _review_providers(settings) -> list[tuple[str, str]]:
    """Return list of (provider_name, model_name) tuples from config."""
    provider_list = [p.strip() for p in settings.generation_review_providers.split(",") if p.strip()]
    result = []
    for provider_name in provider_list:
        _, model_name = _provider_config(provider_name, settings)
        result.append((provider_name, model_name))
    return result


def _exclude_generator_provider(
    providers: list[tuple[str, str]],
    generator_provider_name: str | None,
) -> list[tuple[str, str]]:
    """Remove the generating provider from the review swarm."""
    if not generator_provider_name:
        return providers
    return [
        (provider_name, model_name)
        for provider_name, model_name in providers
        if provider_name != generator_provider_name
    ]


async def _load_question_for_review(
    question_id: uuid.UUID,
    db: AsyncSession,
) -> dict | None:
    """Load question, annotation, options, and overlap status for review.

    Returns a dict with question_data, annotation, source_examples, overlap_status,
    generation_request, and version_id — or None if the question doesn't exist
    or is not a generated question.
    """
    question = await db.get(Question, question_id)
    if question is None or question.content_origin != "generated":
        return None

    # Load latest annotation
    annotation = None
    if question.latest_annotation_id:
        annotation = await db.get(QuestionAnnotation, question.latest_annotation_id)
    ann_dict = {}
    if annotation and isinstance(annotation.annotation_jsonb, dict):
        ann_dict = annotation.annotation_jsonb

    # Load options from latest version
    options = []
    if question.latest_version_id:
        opt_result = await db.execute(
            select(QuestionOption)
            .where(QuestionOption.question_version_id == question.latest_version_id)
            .order_by(QuestionOption.option_label)
        )
        options = [
            {
                "label": opt.option_label,
                "text": opt.option_text,
                "is_correct": opt.is_correct,
                "distractor_type_key": opt.distractor_type_key,
            }
            for opt in opt_result.scalars().all()
        ]

    # Build question_data payload for the review prompt
    question_data = {
        "question_text": question.current_question_text or "",
        "passage_text": question.current_passage_text,
        "paired_passage_text": question.current_paired_passage_text,
        "underlined_text": question.current_underlined_text,
        "correct_option_label": question.current_correct_option_label,
        "explanation": question.current_explanation_text,
        "options": options,
    }
    # Include annotation fields the review prompt reads
    for key in (
        "question_family_key", "grammar_role_key", "grammar_focus_key",
        "reading_skill_family_key", "reading_focus_key", "difficulty_overall",
        "stem_type_key", "stimulus_mode_key",
    ):
        if ann_dict.get(key):
            question_data[key] = ann_dict[key]

    # Load generation request from the job that created this question
    generation_request = None
    job_result = await db.execute(
        select(QuestionJob).where(QuestionJob.question_id == question_id)
        .order_by(QuestionJob.created_at.desc())
    )
    job = job_result.scalars().first()
    if job and job.generation_request_jsonb:
        generation_request = job.generation_request_jsonb

    # Load fresh source examples. Reviewers should judge against the official
    # target space, not the exact examples that seeded generation.
    source_examples = []
    source_ids = []
    if isinstance(generation_request, dict):
        try:
            from app.models.payload import GenerationBatchRequest
            from app.routers.generate import (
                _domain_for_batch,
                _select_source_question_ids_for_batch,
            )

            review_request = dict(generation_request)
            review_request["requested_count"] = 1
            batch_request = GenerationBatchRequest.model_validate(review_request)
            domain = _domain_for_batch(batch_request)
            selections = await _select_source_question_ids_for_batch(
                db,
                batch_request,
                domain,
                [],
            )
            source_ids = selections[0] if selections else []
        except Exception:
            logger.exception("Failed to select fresh review source examples for question %s", question_id)

    if not source_ids and generation_request:
        source_ids = generation_request.get("source_question_ids", [])
    if not source_ids and isinstance(question.generation_source_set, dict):
        source_ids = question.generation_source_set.get("source_question_ids", [])

    if source_ids:
        from app.routers.generate import _load_official_source_examples
        source_examples = await _load_official_source_examples(db, source_ids)

    return {
        "question_data": question_data,
        "annotation": ann_dict if ann_dict else None,
        "source_examples": source_examples,
        "overlap_status": question.official_overlap_status or "none",
        "generation_request": generation_request,
        "version_id": str(question.latest_version_id) if question.latest_version_id else None,
    }


async def _call_review_provider(
    provider_name: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    settings,
) -> tuple[str, int, dict | None]:
    """Call a single LLM provider for review. Returns (raw_text, latency_ms, token_usage).

    Retries transient errors using the configured review retry limit.
    """
    api_key, model = _provider_config(provider_name, settings)
    provider = get_provider(
        provider_name,
        api_key=api_key,
        base_url=settings.ollama_base_url if provider_name == "ollama" else "",
        default_model=model,
    )
    start = time.monotonic()

    async def _complete_once():
        return await provider.complete(
            system=system_prompt,
            user=user_prompt,
            model=model,
            max_tokens=_REVIEW_MAX_TOKENS,
            temperature=_REVIEW_TEMPERATURE,
        )

    retrying_complete = with_retry(
        max_attempts=settings.generation_review_max_retries,
        base_delay=1.0,
        max_delay=15.0,
    )(_complete_once)
    result = await retrying_complete()
    latency_ms = int((time.monotonic() - start) * 1000)
    token_usage = None
    if result.token_usage:
        token_usage = dict(result.token_usage)
    return result.raw_text, latency_ms, token_usage


async def _run_single_reviewer(
    review_run_id: uuid.UUID,
    question_id: uuid.UUID,
    job_id: uuid.UUID | None,
    generation_batch_id: uuid.UUID | None,
    provider_name: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    settings,
) -> LlmReviewResult | None:
    """Run one reviewer and persist the result. Returns the LlmReviewResult or None on failure."""
    result_status = "ok"
    error_message = None
    scores_jsonb = {}
    verdict = "reject"  # Default to reject on failure
    review_notes = None
    raw_response_jsonb = None
    latency_ms = None
    token_usage_jsonb = None

    try:
        raw_text, latency_ms, token_usage_jsonb = await _call_review_provider(
            provider_name, model_name, system_prompt, user_prompt, settings,
        )
        parsed = parse_review_json(raw_text, provider_name=provider_name, model_name=model_name)
        scores_jsonb = parsed["scores_jsonb"]
        verdict = parsed["verdict"]
        review_notes = parsed["review_notes"]
        raw_response_jsonb = parsed["raw_response_jsonb"]
    except ReviewParseError as exc:
        result_status = "permanent_failed"
        error_message = str(exc)
        logger.warning("Review parse error (%s/%s, q=%s): %s", provider_name, model_name, question_id, exc)
    except Exception as exc:
        from app.routers.generate import _is_transient_error
        if _is_transient_error(exc):
            result_status = "transient_failed"
        else:
            result_status = "permanent_failed"
        error_message = f"{type(exc).__name__}: {exc}"
        logger.error("Review call failed (%s/%s, q=%s): %s", provider_name, model_name, question_id, exc)

    async with async_session() as db:
        review_result = LlmReviewResult(
            id=uuid.uuid4(),
            question_id=question_id,
            job_id=job_id,
            generation_batch_id=generation_batch_id,
            review_run_id=review_run_id,
            provider_name=provider_name,
            model_name=model_name,
            task_type="generation_realism_review",
            rubric_version=RUBRIC_VERSION,
            rules_versions_jsonb=dict(RULES_VERSIONS),
            scores_jsonb=scores_jsonb,
            verdict=verdict,
            review_notes=review_notes,
            raw_response_jsonb=raw_response_jsonb,
            latency_ms=latency_ms,
            token_usage_jsonb=token_usage_jsonb,
            review_status=result_status,
            error_message=error_message,
        )
        db.add(review_result)
        await db.commit()
        return review_result


async def run_review_swarm(
    question_id: uuid.UUID,
    *,
    triggered_by: str = "manual_question",
    admin_token: str | None = None,
    generation_batch_id: uuid.UUID | None = None,
) -> ReviewRun:
    """Orchestrate multi-model review for a generated question.

    Creates a ReviewRun, runs all configured reviewers concurrently with
    a semaphore, and finalizes the run status.

    Returns the ReviewRun with status set to 'complete', 'partial', or 'failed'.
    """
    settings = get_settings()
    providers = _review_providers(settings)
    max_concurrent = settings.generation_review_max_concurrent

    # Create review run
    review_run_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with async_session() as db:
        review_run = ReviewRun(
            id=review_run_id,
            question_id=question_id,
            generation_batch_id=generation_batch_id,
            triggered_by=triggered_by,
            triggered_by_admin_token=admin_token,
            rubric_version=RUBRIC_VERSION,
            rules_versions_jsonb=dict(RULES_VERSIONS),
            status="running",
            started_at=now,
        )
        db.add(review_run)
        await db.commit()

    # Load question context
    async with async_session() as db:
        context = await _load_question_for_review(question_id, db)
    if context is None:
        async with async_session() as db:
            review_run = await db.get(ReviewRun, review_run_id)
            review_run.status = "failed"
            review_run.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return review_run

    # Build review prompt
    system_prompt, user_prompt = build_review_prompt(
        question_data=context["question_data"],
        annotation=context["annotation"],
        source_examples=context["source_examples"],
        overlap_status=context["overlap_status"],
        generation_request=context["generation_request"],
    )

    # Load job_id and generator provider for audit and self-grading exclusion.
    job_id = None
    generator_provider_name = None
    async with async_session() as db:
        job_result = await db.execute(
            select(QuestionJob).where(QuestionJob.question_id == question_id)
            .order_by(QuestionJob.created_at.desc())
        )
        job = job_result.scalars().first()
        if job:
            job_id = job.id
            generator_provider_name = job.provider_name

    providers = _exclude_generator_provider(providers, generator_provider_name)

    # Run reviewers concurrently with semaphore
    semaphore = asyncio.Semaphore(max_concurrent)
    async def _bounded_review(provider_name: str, model_name: str):
        async with semaphore:
            return await _run_single_reviewer(
                review_run_id=review_run_id,
                question_id=question_id,
                job_id=job_id,
                generation_batch_id=generation_batch_id,
                provider_name=provider_name,
                model_name=model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                settings=settings,
            )

    tasks = [
        asyncio.create_task(_bounded_review(pn, mn))
        for pn, mn in providers
    ]
    for t in tasks:
        t.add_done_callback(lambda task: None if task.exception() is None else logger.error("Review task failed: %s", task.exception()))
    await asyncio.gather(*tasks, return_exceptions=True)

    # Collect results from tasks
    task_results = []
    for t in tasks:
        try:
            task_results.append(t.result())
        except Exception:
            task_results.append(None)

    # Finalize review run status
    ok_count = sum(1 for r in task_results if r and r.review_status == "ok")
    total_count = len(providers)

    async with async_session() as db:
        review_run = await db.get(ReviewRun, review_run_id)
        if review_run is None:
            return review_run

        if ok_count == total_count and total_count > 0:
            review_run.status = "complete"
        elif ok_count > 0:
            review_run.status = "partial"
        else:
            review_run.status = "failed"
        review_run.completed_at = datetime.now(timezone.utc)
        await db.commit()

    # Compute and save consensus verdict (Phase 5). This runs even when
    # all reviewers failed so the admin queue has an insufficient_reviews row.
    from app.review.consensus import save_consensus
    review_results = [r for r in task_results if r is not None]
    async with async_session() as db:
        question = await db.get(Question, question_id)
        overlap_status = getattr(question, "official_overlap_status", "none") if question else "none"
        await save_consensus(
            question_id=question_id,
            review_run_id=review_run_id,
            review_results=review_results,
            overlap_status=overlap_status,
            generation_batch_id=generation_batch_id,
            db=db,
        )

    return review_run


async def run_batch_review_swarm(
    batch_id: uuid.UUID,
    *,
    triggered_by: str = "manual_batch",
    admin_token: str | None = None,
) -> list[dict]:
    """Run review swarm for all questions in a batch that have been generated
    (have a question_id) but haven't been reviewed yet.

    Returns a list of dicts with question_id, review_run_id, and status.
    """
    async with async_session() as db:
        batch = await db.get(GenerationBatch, batch_id)
        if batch is None:
            raise ValueError(f"GenerationBatch {batch_id} not found")

        # Find all jobs in the batch that have a question_id
        result = await db.execute(
            select(QuestionJob).where(
                QuestionJob.generation_batch_id == batch_id,
                QuestionJob.question_id.isnot(None),
            )
        )
        jobs = result.scalars().all()

        if not jobs:
            return []

        question_ids = [j.question_id for j in jobs]

        # Filter out questions that already have a completed review run
        existing_result = await db.execute(
            select(ReviewRun).where(
                ReviewRun.question_id.in_(question_ids),
                ReviewRun.status.in_(["complete", "partial"]),
            )
        )
        already_reviewed = {r.question_id for r in existing_result.scalars().all()}
        to_review = [qid for qid in question_ids if qid not in already_reviewed]

    review_results = []
    for question_id in to_review:
        try:
            run = await run_review_swarm(
                question_id,
                triggered_by=triggered_by,
                admin_token=admin_token,
                generation_batch_id=batch_id,
            )
            review_results.append({
                "question_id": str(question_id),
                "review_run_id": str(run.id),
                "status": run.status,
            })
        except Exception as exc:
            logger.error("Batch review failed for question %s: %s", question_id, exc)
            review_results.append({
                "question_id": str(question_id),
                "review_run_id": None,
                "status": "failed",
            })

    return review_results
