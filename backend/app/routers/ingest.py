import uuid
import asyncio
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.auth import admin_required
from app.config import get_settings
from app.models.db import QuestionJob, QuestionAsset, Question
from app.storage.local_store import save_asset, compute_checksum
from app.parsers.pdf_parser import parse_pdf
from app.parsers.json_parser import extract_json_from_text
from app.pipeline.orchestrator import JobOrchestrator
from app.pipeline.validator import validate_question
from app.models.payload import JobResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_MIME = {
    "application/pdf", "image/png", "image/jpeg", "image/webp",
    "text/markdown", "text/plain", "application/json",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def _run_pipeline(job: QuestionJob, db: AsyncSession):
    from app.llm.factory import get_provider
    from app.prompts.extract_prompt import build_extract_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt

    settings = get_settings()
    provider = get_provider(
        settings.default_annotation_provider,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
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
        annotate_json = extract_json_from_text(result.raw_text)
        job.pass2_json = {**annotate_json, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        orch.fail("annotating", "llm_error", str(e))
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "annotating", "error": str(e)}]
        await db.commit()
        return

    # Validate
    orch.advance()
    job.status = "validating"
    merged = {**extract_json, **annotate_json}
    errors = validate_question(merged, content_origin=job.content_origin)
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "needs_review"
    else:
        job.status = "approved"
    await db.commit()


async def _run_pipeline_with_session(job_id: uuid.UUID):
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if job:
            await _run_pipeline(job, db)


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
    source_module_code: str = Form(""),
    provider_name: str = Form("anthropic"),
    model_name: str = Form("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

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
        prompt_version="v1",
        rules_version=settings.rules_version,
        raw_asset_id=asset_id,
        pass1_json={"raw_text": raw_text[:50000], "pages": len(pdf_result["pages"]), "source_metadata": {
            "source_exam_code": source_exam_code,
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
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

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
        prompt_version="v1",
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
    provider_name: str = "anthropic",
    model_name: str = "claude-sonnet-4-6",
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
        provider_name=provider_name,
        model_name=model_name,
        prompt_version="v1",
        rules_version=settings.rules_version,
        pass1_json=existing_job.pass1_json,
        question_id=qid,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(_run_pipeline_with_session(job_id))

    return JobResponse(id=str(job_id), job_type="reannotate", status="annotating", question_id=question_id, created_at=now)