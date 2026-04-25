import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.auth import admin_required
from app.config import get_settings
from app.models.db import QuestionJob, Question, QuestionVersion, QuestionAnnotation, QuestionOption
from app.parsers.json_parser import extract_json_from_text, normalize_annotation
from app.pipeline.validator import validate_question
from app.models.payload import GenerationRequest, GenerationCompareRequest, JobResponse

router = APIRouter(prefix="/generate", tags=["generate"])


async def _run_generate_pipeline(job: QuestionJob, db: AsyncSession, request_data: dict):
    from app.llm.factory import get_provider
    from app.prompts.generate_prompt import build_generate_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
        base_url=settings.ollama_base_url,
        default_model=job.model_name,
    )

    # Generate
    system, user = build_generate_prompt(generation_request=request_data)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192, temperature=0.7)
        generated = extract_json_from_text(result.raw_text)
        job.pass1_json = {**generated, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
        job.status = "annotating"
        await db.commit()
    except Exception as e:
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "generating", "error": str(e)}]
        await db.commit()
        return

    # Annotate
    system, user = build_annotate_prompt(generated)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192)
        annotate_json = normalize_annotation(extract_json_from_text(result.raw_text))
        job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": str(e)}]
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

    # Create Question
    correct_label = generated.get("correct_option_label", "")
    question = Question(
        id=question_id,
        content_origin="generated",
        current_question_text=generated.get("question_text", ""),
        current_passage_text=generated.get("passage_text"),
        current_correct_option_label=correct_label,
        current_explanation_text=annotate_json.get("explanation_short", ""),
        practice_status="draft",
        official_overlap_status="none",
        generation_source_set=request_data,
        is_admin_edited=False,
        metadata_managed_by_llm=True,
        created_at=now,
        updated_at=now,
    )
    db.add(question)

    # Create QuestionVersion
    db.add(QuestionVersion(
        id=version_id,
        question_id=question_id,
        version_number=1,
        change_source="generate",
        question_text=generated.get("question_text", ""),
        passage_text=generated.get("passage_text"),
        choices_jsonb=generated.get("options", []),
        correct_option_label=generated.get("correct_option_label", ""),
        explanation_text=annotate_json.get("explanation_short"),
        created_at=now,
    ))

    # Create QuestionAnnotation
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
        generation_profile_jsonb=None,
        confidence_jsonb={"annotation_confidence": annotate_json.get("annotation_confidence", 0.0), "needs_human_review": annotate_json.get("needs_human_review", False)},
        created_at=now,
    ))
    await db.flush()
    question.latest_annotation_id = annotation_id
    question.latest_version_id = version_id

    # Create QuestionOption rows
    for opt in generated.get("options", []):
        db.add(QuestionOption(
            id=uuid.uuid4(),
            question_id=question_id,
            question_version_id=version_id,
            option_label=opt.get("label", ""),
            option_text=opt.get("text", ""),
            is_correct=opt.get("label", "") == correct_label,
            option_role="correct" if opt.get("label", "") == correct_label else "distractor",
            created_at=now,
        ))

    job.question_id = question_id
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
    asyncio.create_task(_run())

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
        job_id = uuid.uuid4()
        job = QuestionJob(
            id=job_id,
            job_type="generate",
            content_origin="generated",
            input_format="spec",
            status="extracting",
            provider_name=provider_name,
            model_name=settings.default_annotation_model,
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
        jid = uuid.UUID(resp.id)

        async def _run(jid=jid):
            async with async_session() as db2:
                j = await db2.get(QuestionJob, jid)
                if j:
                    await _run_generate_pipeline(j, db2, request_data)
        asyncio.create_task(_run())

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
    }
