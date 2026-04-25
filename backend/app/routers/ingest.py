import uuid
import asyncio
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.auth import admin_required
from app.config import get_settings
from app.models.db import (
    QuestionJob, QuestionAsset, Question, QuestionVersion,
    QuestionAnnotation, QuestionOption,
)
from app.storage.local_store import save_asset, compute_checksum
from app.parsers.pdf_parser import parse_pdf
from app.parsers.json_parser import extract_json_from_text, normalize_annotation
from app.pipeline.orchestrator import JobOrchestrator
from app.pipeline.validator import validate_question
from app.models.payload import JobResponse, ReannotateRequest

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_MIME = {
    "application/pdf", "image/png", "image/jpeg", "image/webp",
    "text/markdown", "text/plain", "application/json",
}
IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def _run_pipeline(job: QuestionJob, db: AsyncSession):
    from app.llm.factory import get_provider
    from app.prompts.extract_prompt import build_extract_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
        base_url=settings.ollama_base_url,
        default_model=job.model_name,
    )
    orch = JobOrchestrator(str(job.id), job.content_origin, job.job_type)

    raw_text = (job.pass1_json or {}).get("raw_text", "")
    if not raw_text:
        orch.fail("extracting", "no_raw_text", "No raw text available")
        job.status = "failed"
        await db.commit()
        return

    # Pass 1: Extract
    orch.advance()
    job.status = "extracting"
    await db.commit()

    system, user = build_extract_prompt(raw_text[:30000])
    try:
        result = await provider.complete(system=system, user=user)
        extract_json = extract_json_from_text(result.raw_text)
        job.pass1_json = {**extract_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        orch.fail("extracting", "llm_error", str(e))
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "extracting", "error": str(e)}]
        await db.commit()
        return

    # Pass 2: Annotate
    orch.advance()
    job.status = "annotating"
    await db.commit()

    system, user = build_annotate_prompt(extract_json)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192)
        annotate_json = normalize_annotation(extract_json_from_text(result.raw_text))
        job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        orch.fail("annotating", "llm_error", str(e))
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": str(e)}]
        await db.commit()
        return

    overlaps = []

    # Overlap check for unofficial/generated content
    if job.content_origin in ("unofficial", "generated"):
        orch.advance()
        job.status = "overlap_checking"
        await db.commit()

        from app.pipeline.overlap import detect_overlaps

        question_text = extract_json.get("question_text", "")
        passage_text = extract_json.get("passage_text")

        overlaps = await detect_overlaps(
            question_id=job.id,
            annotation_jsonb=annotate_json,
            passage_text=passage_text,
            question_text=question_text,
            db=db,
        )

    # Validate
    orch.advance()
    job.status = "validating"
    merged = {**extract_json, **annotate_json}
    errors = validate_question(merged, content_origin=job.content_origin)
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "needs_review"
        await db.commit()
        return

    # Official questions require human answer-key verification before active use.
    # Job ends in needs_review (not approved) so the admin queue can surface them.
    job.status = "needs_review" if job.content_origin == "official" else "approved"

    # Persist question, options, annotation, and version
    now = datetime.now(timezone.utc)
    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()

    practice_status = "draft" if job.content_origin == "official" else "active"
    overlap_status = "possible" if overlaps else "none"

    question = Question(
        id=question_id,
        content_origin=job.content_origin,
        source_exam_code=extract_json.get("source_exam_code"),
        source_section_code=extract_json.get("source_section_code"),
        source_module_code=extract_json.get("source_module_code"),
        source_question_number=extract_json.get("source_question_number"),
        stimulus_mode_key=extract_json.get("stimulus_mode_key"),
        stem_type_key=extract_json.get("stem_type_key"),
        current_question_text=extract_json.get("question_text", ""),
        current_passage_text=extract_json.get("passage_text"),
        current_correct_option_label=extract_json.get("correct_option_label", ""),
        current_explanation_text=annotate_json.get("explanation_short", ""),
        practice_status=practice_status,
        official_overlap_status=overlap_status,
        is_admin_edited=False,
        metadata_managed_by_llm=True,
        created_at=now,
        updated_at=now,
    )
    db.add(question)

    question_version = QuestionVersion(
        id=version_id,
        question_id=question_id,
        version_number=1,
        change_source="ingest",
        question_text=extract_json.get("question_text", ""),
        passage_text=extract_json.get("passage_text"),
        choices_jsonb=extract_json.get("options", []),
        correct_option_label=extract_json.get("correct_option_label", ""),
        explanation_text=annotate_json.get("explanation_short"),
        created_at=now,
    )
    db.add(question_version)

    # Flush so version_id is visible to subsequent rows that FK to it
    await db.flush()

    question_annotation = QuestionAnnotation(
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
    )
    db.add(question_annotation)

    # Flush so annotation_id is visible to the question FK update below
    await db.flush()

    question.latest_annotation_id = annotation_id
    question.latest_version_id = version_id

    for opt in extract_json.get("options", []):
        db.add(QuestionOption(
            id=uuid.uuid4(),
            question_id=question_id,
            question_version_id=version_id,
            option_label=opt.get("label", ""),
            option_text=opt.get("text", ""),
            is_correct=opt.get("label", "") == extract_json.get("correct_option_label", ""),
            option_role="correct" if opt.get("label", "") == extract_json.get("correct_option_label", "") else "distractor",
            created_at=now,
        ))

    # Link asset to question and backfill source_section_code if not already set
    if job.raw_asset_id:
        asset = await db.get(QuestionAsset, job.raw_asset_id)
        if asset:
            asset.question_id = question_id
            if not asset.source_section_code and section_code:
                asset.source_section_code = section_code

    if overlaps:
        from app.pipeline.overlap import persist_overlap_relations

        await persist_overlap_relations(question_id=question_id, overlaps=overlaps, db=db)

    job.question_id = question_id
    await db.commit()

    # Export to YAML after successful commit
    from app.storage.yaml_export import export_official_question, export_generated_question

    source_meta = (job.pass1_json or {}).get("source_metadata", {})
    exam_code = extract_json.get("source_exam_code") or source_meta.get("source_exam_code")
    section_code = extract_json.get("source_section_code") or source_meta.get("source_section_code")
    module_code = extract_json.get("source_module_code") or source_meta.get("source_module_code")

    if job.content_origin == "official" and exam_code and module_code:
        export_official_question(
            question_id=str(question_id),
            exam_code=exam_code,
            module_code=module_code,
            question_number=extract_json.get("source_question_number"),
            extract_json=extract_json,
            annotate_json=annotate_json,
            section_code=section_code,
            base_dir=settings.local_archive_mirror,
        )
    elif job.content_origin in ("unofficial", "generated"):
        export_generated_question(
            question_id=str(question_id),
            extract_json=extract_json,
            annotate_json=annotate_json,
            base_dir=settings.local_archive_mirror,
        )


async def _run_pipeline_with_session(job_id: uuid.UUID):
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if job:
            await _run_pipeline(job, db)


async def _safe_read(file: UploadFile, max_bytes: int) -> bytes:
    """Check Content-Length before reading to avoid loading oversized files into RAM."""
    cl = file.headers.get("content-length")
    if cl and int(cl) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    return content


def _asset_type_from_mime(mime: str) -> str:
    if "pdf" in mime:
        return "pdf"
    elif "image" in mime:
        return "image"
    elif "markdown" in mime:
        return "markdown"
    elif "json" in mime:
        return "json"
    return "text"


@router.post("/official/pdf", response_model=JobResponse)
async def ingest_official_pdf(
    file: UploadFile = File(...),
    source_exam_code: str = Form(""),
    source_section_code: str = Form(""),
    source_module_code: str = Form(""),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    content = await _safe_read(file, MAX_FILE_SIZE)

    storage_path = await save_asset(file.filename or "upload.pdf", content, subfolder="official")
    checksum = compute_checksum(content)

    now = datetime.now(timezone.utc)
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        pdf_result = parse_pdf(tmp.name)

    raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])

    asset = QuestionAsset(
        id=asset_id,
        content_origin="official",
        asset_type="pdf",
        storage_path=storage_path,
        mime_type=file.content_type,
        page_start=0,
        page_end=len(pdf_result["pages"]) - 1,
        source_name=file.filename,
        source_exam_code=source_exam_code or None,
        source_section_code=source_section_code or None,
        source_module_code=source_module_code or None,
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    settings = get_settings()
    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin="official",
        input_format="pdf",
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v3.0",
        rules_version=settings.rules_version,
        raw_asset_id=asset_id,
        pass1_json={"raw_text": raw_text[:50000], "pages": len(pdf_result["pages"]), "source_metadata": {
            "source_exam_code": source_exam_code,
            "source_section_code": source_section_code,
            "source_module_code": source_module_code,
        }},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(_run_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


@router.post("/unofficial/file", response_model=JobResponse)
async def ingest_unofficial_file(
    file: UploadFile = File(...),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    content = await _safe_read(file, MAX_FILE_SIZE)

    if (file.content_type or "") in IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail="Image ingestion requires OCR which is not yet implemented. "
                   "Convert the image to PDF or extract the question text manually.",
        )

    storage_path = await save_asset(file.filename or "upload", content, subfolder="unofficial")
    checksum = compute_checksum(content)
    now = datetime.now(timezone.utc)
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()

    asset_type = _asset_type_from_mime(file.content_type or "")

    asset = QuestionAsset(
        id=asset_id,
        content_origin="unofficial",
        asset_type=asset_type,
        storage_path=storage_path,
        mime_type=file.content_type,
        source_name=file.filename,
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    raw_text = ""
    if asset_type == "pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            pdf_result = parse_pdf(tmp.name)
            raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])
    elif asset_type in ("text", "markdown"):
        raw_text = content.decode("utf-8", errors="replace")
    elif asset_type == "json":
        import json
        try:
            data = json.loads(content)
            raw_text = json.dumps(data, indent=2)
        except json.JSONDecodeError:
            raw_text = content.decode("utf-8", errors="replace")

    settings = get_settings()
    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin="unofficial",
        input_format=asset_type,
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v3.0",
        rules_version=settings.rules_version,
        raw_asset_id=asset_id,
        pass1_json={"raw_text": raw_text[:50000]},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(_run_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


@router.post("/text", response_model=JobResponse)
async def ingest_text(
    text: str = Form(...),
    content_origin: str = Form("unofficial"),
    source_exam_code: str = Form(""),
    source_section_code: str = Form(""),
    source_module_code: str = Form(""),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    if content_origin not in ("official", "unofficial"):
        raise HTTPException(status_code=422, detail="content_origin must be 'official' or 'unofficial'")

    settings = get_settings()
    now = datetime.now(timezone.utc)
    job_id = uuid.uuid4()

    source_metadata = {
        k: v for k, v in {
            "source_exam_code": source_exam_code or None,
            "source_section_code": source_section_code or None,
            "source_module_code": source_module_code or None,
        }.items() if v
    }

    job = QuestionJob(
        id=job_id,
        job_type="ingest",
        content_origin=content_origin,
        input_format="text",
        status="parsing",
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v3.0",
        rules_version=settings.rules_version,
        pass1_json={"raw_text": text[:50000], "source_metadata": source_metadata},
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(_run_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="ingest", status="parsing", created_at=now)


async def _run_reannotate_pipeline(job: QuestionJob, db: AsyncSession):
    """Reannotation pipeline — skips extraction and goes straight to annotation."""
    from app.llm.factory import get_provider
    from app.prompts.annotate_prompt import build_annotate_prompt
    from app.parsers.json_parser import extract_json_from_text, normalize_annotation

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
        base_url=settings.ollama_base_url,
        default_model=job.model_name,
    )
    extract_json = {}
    if job.pass1_json:
        extract_json = {k: v for k, v in job.pass1_json.items() if not k.startswith("_")}

    # Skip extraction, go straight to annotation
    job.status = "annotating"
    await db.commit()

    system, user = build_annotate_prompt(extract_json)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192)
        annotate_json = normalize_annotation(extract_json_from_text(result.raw_text))
        job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": str(e)}]
        await db.commit()
        return

    # Validate
    merged = {**extract_json, **annotate_json}
    errors = validate_question(merged, content_origin=job.content_origin)
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "needs_review"
        await db.commit()
        return

    job.status = "approved"

    # Create new annotation and version, update question
    now = datetime.now(timezone.utc)
    question = await db.get(Question, job.question_id)
    if not question:
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": "Question not found"}]
        await db.commit()
        return

    latest_version = max(question.versions, key=lambda v: v.version_number) if question.versions else None
    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()

    db.add(QuestionVersion(
        id=version_id,
        question_id=question.id,
        version_number=(latest_version.version_number + 1) if latest_version else 1,
        change_source="reprocess",
        question_text=extract_json.get("question_text", question.current_question_text),
        passage_text=extract_json.get("passage_text", question.current_passage_text),
        choices_jsonb=extract_json.get("options", []),
        correct_option_label=extract_json.get("correct_option_label", question.current_correct_option_label),
        explanation_text=annotate_json.get("explanation_short", question.current_explanation_text),
        created_at=now,
    ))

    db.add(QuestionAnnotation(
        id=annotation_id,
        question_id=question.id,
        question_version_id=version_id,
        provider_name=job.provider_name,
        model_name=job.model_name,
        prompt_version=job.prompt_version,
        rules_version=job.rules_version,
        annotation_jsonb=annotate_json,
        explanation_jsonb={"explanation_full": annotate_json.get("explanation_full", "")},
        confidence_jsonb={"annotation_confidence": annotate_json.get("annotation_confidence", 0.0), "needs_human_review": annotate_json.get("needs_human_review", False)},
        created_at=now,
    ))
    await db.flush()  # ensure new version/annotation IDs are visible before setting circular FKs

    question.current_explanation_text = annotate_json.get(
        "explanation_short", question.current_explanation_text
    )
    question.latest_annotation_id = annotation_id
    question.latest_version_id = version_id
    question.updated_at = now
    await db.commit()


async def _run_reannotate_pipeline_with_session(job_id: uuid.UUID):
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if job:
            await _run_reannotate_pipeline(job, db)


@router.post("/unofficial/batch", response_model=list[JobResponse])
async def ingest_unofficial_batch(
    files: list[UploadFile] = File(...),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    results = []
    for file in files:
        resp = await ingest_unofficial_file(
            file=file, provider_name=provider_name, model_name=model_name, db=db, _auth=_auth
        )
        results.append(resp)
    return results


@router.post("/reannotate/{question_id}", response_model=JobResponse)
async def reannotate_question(
    question_id: str,
    body: ReannotateRequest = Body(default_factory=ReannotateRequest),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    try:
        qid = uuid.UUID(question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    result = await db.execute(
        select(QuestionJob)
        .where(QuestionJob.question_id == qid)
        .order_by(QuestionJob.created_at.desc())
        .limit(1)
    )
    existing_job = result.scalars().first()
    if not existing_job or not existing_job.pass1_json:
        raise HTTPException(status_code=400, detail="No existing extract data for this question")

    settings = get_settings()
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    job = QuestionJob(
        id=job_id,
        job_type="reannotate",
        content_origin=q.content_origin,
        input_format="reannotate",
        status="annotating",
        provider_name=body.provider_name,
        model_name=body.model_name,
        prompt_version="v3.0",
        rules_version=settings.rules_version,
        pass1_json=existing_job.pass1_json,
        question_id=qid,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(_run_reannotate_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="reannotate", status="annotating", question_id=question_id, created_at=now)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Poll the status of an ingest/reannotate job."""
    try:
        jid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    job = await db.get(QuestionJob, jid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    validation_errors = []
    if job.validation_errors_jsonb:
        validation_errors = [
            {"step": e.get("step"), "severity": e.get("severity"), "message": e.get("message")}
            for e in job.validation_errors_jsonb
        ]

    return JobResponse(
        id=str(job.id),
        job_type=job.job_type,
        status=job.status,
        question_id=str(job.question_id) if job.question_id else None,
        created_at=job.created_at,
    )
