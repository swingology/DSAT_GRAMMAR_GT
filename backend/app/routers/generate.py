import uuid
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("Background generate task failed", exc_info=task.exception(), extra={"task": task.get_name()})

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.auth import admin_required
from app.config import get_settings
from app.job_limits import run_with_job_limit
from app.llm.errors import error_payload
from app.models.db import QuestionJob, Question, QuestionVersion, QuestionAnnotation, QuestionOption
from app.parsers.json_parser import extract_json_from_text, normalize_annotation
from app.pipeline.validator import validate_question
from app.pipeline.option_hydration import option_analyses_by_label, option_annotation_fields
from app.pipeline.overlap import detect_overlaps, persist_overlap_relations
from app.models.payload import GenerationRequest, GenerationCompareRequest, JobResponse

router = APIRouter(prefix="/generate", tags=["generate"])

_SOURCE_SET_OPERATIONAL_KEYS = {"provider_name", "model_name"}


def _generation_profile_payload(*sources: dict | None) -> dict | None:
    """Build the stored generation profile from model output and request metadata."""
    merged: dict = {}
    _operational_keys = {"provider_name", "model_name"}
    for source in sources:
        if not isinstance(source, dict):
            continue
        profile = source.get("generation_profile")
        if isinstance(profile, dict):
            merged.update(profile)
    # Merge the last source (request spec) but exclude provider/model operational fields
    # so they don't pollute generation_profile_jsonb.
    if isinstance(sources[-1], dict):
        merged.update({k: v for k, v in sources[-1].items() if k not in _operational_keys})
    return merged or None


def _provider_api_key(settings, provider_name: str) -> str:
    if provider_name == "anthropic":
        return settings.anthropic_api_key
    if provider_name == "openai":
        return settings.openai_api_key
    return ""


async def _run_generate_pipeline(job: QuestionJob, db: AsyncSession, request_data: dict):
    from app.llm.factory import get_provider
    from app.prompts.generate_prompt import build_generate_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=_provider_api_key(settings, job.provider_name),
        base_url=settings.ollama_base_url,
        default_model=job.model_name,
    )

    # Generate — 3-attempt retry on malformed JSON
    system, user = build_generate_prompt(generation_request=request_data)
    generated = None
    _last_err: Exception | None = None
    for _attempt in range(3):
        try:
            result = await provider.complete(system=system, user=user, max_tokens=8192, temperature=0.7)
            generated = extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
            job.pass1_json = {**generated, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
            job.status = "annotating"
            await db.commit()
            break
        except ValueError as _json_err:
            _last_err = _json_err
            logger.warning("Generate JSON parse failed (attempt %d/3, job %s): %s", _attempt + 1, job.id, _json_err)
            if _attempt < 2:
                await asyncio.sleep(0.5 * (2 ** _attempt))
        except Exception as _exc:
            _last_err = _exc
            break
    if generated is None:
        job.status = "failed"
        job.validation_errors_jsonb = [error_payload("generating", _last_err or Exception("unknown"))]
        await db.commit()
        return

    # Annotate — 3-attempt retry on malformed JSON
    system, user = build_annotate_prompt(generated)
    annotate_json = None
    _last_err = None
    for _attempt in range(3):
        try:
            result = await provider.complete(system=system, user=user, max_tokens=8192)
            annotate_json = normalize_annotation(
                extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
            )
            job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
            break
        except ValueError as _json_err:
            _last_err = _json_err
            logger.warning("Annotate JSON parse failed (attempt %d/3, job %s): %s", _attempt + 1, job.id, _json_err)
            if _attempt < 2:
                await asyncio.sleep(0.5 * (2 ** _attempt))
        except Exception as _exc:
            _last_err = _exc
            break
    if annotate_json is None:
        job.status = "failed"
        job.validation_errors_jsonb = [error_payload("annotating", _last_err or Exception("unknown"))]
        await db.commit()
        return

    # Validate and create question
    merged = {**generated, **annotate_json, "generation_source_set": request_data}
    errors = validate_question(merged, content_origin="generated")
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "needs_review"
        await db.commit()
        return

    job.status = "approved"

    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Persist inside a savepoint so a DB error only rolls back this question,
    # leaving the session valid for the status update that follows.
    try:
        async with db.begin_nested():
            correct_label = generated.get("correct_option_label", "")
            question = Question(
                id=question_id,
                content_origin="generated",
                current_question_text=generated.get("question_text", ""),
                current_passage_text=generated.get("passage_text"),
                current_paired_passage_text=generated.get("paired_passage_text"),
                current_underlined_text=generated.get("underlined_text"),
                current_correct_option_label=correct_label,
                current_explanation_text=annotate_json.get("explanation_short", ""),
                practice_status="draft",
                official_overlap_status="none",
                generation_source_set={k: v for k, v in request_data.items() if k not in _SOURCE_SET_OPERATIONAL_KEYS},
                is_admin_edited=False,
                metadata_managed_by_llm=True,
                created_at=now,
                updated_at=now,
            )
            db.add(question)

            db.add(QuestionVersion(
                id=version_id,
                question_id=question_id,
                version_number=1,
                change_source="generate",
                question_text=generated.get("question_text", ""),
                passage_text=generated.get("passage_text"),
                paired_passage_text=generated.get("paired_passage_text"),
                underlined_text=generated.get("underlined_text"),
                choices_jsonb=generated.get("options", []),
                correct_option_label=generated.get("correct_option_label", ""),
                explanation_text=annotate_json.get("explanation_short"),
                created_at=now,
            ))

            generation_profile = _generation_profile_payload(generated, annotate_json, request_data)
            db.add(QuestionAnnotation(
                id=annotation_id,
                question_id=question_id,
                question_version_id=version_id,
                provider_name=job.provider_name,
                model_name=job.model_name,
                prompt_version=job.prompt_version,
                rules_version=job.rules_version,
                annotation_jsonb=annotate_json,
                explanation_jsonb={"explanation_full": annotate_json.get("explanation_full", "")},
                generation_profile_jsonb=generation_profile,
                confidence_jsonb={"annotation_confidence": annotate_json.get("annotation_confidence", 0.0), "needs_human_review": annotate_json.get("needs_human_review", False)},
                created_at=now,
            ))
            await db.flush()
            question.latest_annotation_id = annotation_id
            question.latest_version_id = version_id

            opt_analyses = option_analyses_by_label(annotate_json)
            for opt in generated.get("options", []):
                label = opt.get("label", "")
                db.add(QuestionOption(
                    id=uuid.uuid4(),
                    question_id=question_id,
                    question_version_id=version_id,
                    option_label=label,
                    option_text=opt.get("text", ""),
                    is_correct=label == correct_label,
                    option_role="correct" if label == correct_label else "distractor",
                    created_at=now,
                    **option_annotation_fields(opt_analyses.get(label, {})),
                ))

            job.question_id = question_id
        await db.commit()
    except Exception as _persist_err:
        logger.error("Generate persist failed (job %s): %s", job.id, _persist_err)
        job.status = "failed"
        job.validation_errors_jsonb = [error_payload("persisting", _persist_err)]
        await db.commit()
        return

    # Run overlap detection against official questions and update status if found
    job.status = "overlap_checking"
    await db.commit()
    overlaps = await detect_overlaps(
        question_id=question_id,
        annotation_jsonb=annotate_json,
        passage_text=generated.get("passage_text"),
        question_text=generated.get("question_text", ""),
        db=db,
    )
    if overlaps:
        await persist_overlap_relations(question_id=question_id, overlaps=overlaps, db=db)
        q_created = await db.get(Question, question_id)
        if q_created:
            q_created.official_overlap_status = "possible"
        await db.commit()

    # Export to YAML after successful commit
    from app.storage.yaml_export import export_generated_question

    export_generated_question(
        question_id=str(question_id),
        extract_json=generated,
        annotate_json=annotate_json,
        generation_source_set=request_data,
        base_dir=settings.local_archive_mirror,
    )


@router.post("/questions", response_model=JobResponse)
async def generate_questions(
    body: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    settings = get_settings()
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    job = QuestionJob(
        id=job_id,
        job_type="generate",
        content_origin="generated",
        input_format="spec",
        status="extracting",
        provider_name=body.provider_name or settings.default_annotation_provider,
        model_name=body.model_name or settings.default_annotation_model,
        prompt_version="v3.0",
        rules_version=settings.rules_version,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    request_data = body.model_dump()

    async def _run():
        async with async_session() as db2:
            j = await db2.get(QuestionJob, job_id)
            if j:
                await _run_generate_pipeline(j, db2, request_data)
    asyncio.create_task(run_with_job_limit(_run)).add_done_callback(_log_task_exception)

    return JobResponse(id=str(job_id), job_type="generate", status="extracting", created_at=now)


@router.post("/questions/compare", response_model=list[JobResponse])
async def generate_compare(
    body: GenerationCompareRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    settings = get_settings()
    comparison_group = uuid.uuid4()
    results = []
    now = datetime.now(timezone.utc)

    for provider_name in body.providers:
        if provider_name == "ollama":
            model_name = settings.default_ollama_model
        elif provider_name == "openai" and settings.default_annotation_provider != "openai":
            model_name = "gpt-4o"
        elif provider_name == "anthropic" and settings.default_annotation_provider != "anthropic":
            model_name = "claude-sonnet-4-6"
        else:
            model_name = settings.default_annotation_model
        job_id = uuid.uuid4()
        job = QuestionJob(
            id=job_id,
            job_type="generate",
            content_origin="generated",
            input_format="spec",
            status="extracting",
            provider_name=provider_name,
            model_name=model_name,
            prompt_version="v3.0",
            rules_version=settings.rules_version,
            comparison_group_id=comparison_group,
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        results.append(JobResponse(id=str(job_id), job_type="generate", status="extracting", created_at=now))

    await db.commit()

    request_data = body.model_dump()
    for resp in results:
        # Each provider closure needs its own copy so mutations inside
        # _run_generate_pipeline don't leak across jobs.
        jid = uuid.UUID(resp.id)
        job_data = dict(request_data)

        async def _run(jid=jid, job_data=job_data):
            async with async_session() as db2:
                j = await db2.get(QuestionJob, jid)
                if j:
                    await _run_generate_pipeline(j, db2, job_data)
        asyncio.create_task(run_with_job_limit(_run)).add_done_callback(_log_task_exception)

    return results


@router.get("/runs/{run_id}")
async def get_generation_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    result = await db.execute(
        select(QuestionJob).where(QuestionJob.id == rid)
    )
    job = result.scalars().first()

    if not job:
        result = await db.execute(
            select(QuestionJob).where(QuestionJob.comparison_group_id == rid)
        )
        jobs = result.scalars().all()
        if not jobs:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "comparison_group_id": str(rid),
            "jobs": [
                {
                    "id": str(j.id),
                    "status": j.status,
                    "provider_name": j.provider_name,
                    "question_id": str(j.question_id) if j.question_id else None,
                    "validation_errors": j.validation_errors_jsonb,
                }
                for j in jobs
            ],
        }

    return {
        "id": str(job.id),
        "status": job.status,
        "provider_name": job.provider_name,
        "question_id": str(job.question_id) if job.question_id else None,
        "comparison_group_id": str(job.comparison_group_id) if job.comparison_group_id else None,
        "validation_errors": job.validation_errors_jsonb,
        "pass1_json": job.pass1_json,
        "pass2_json": job.pass2_json,
    }
