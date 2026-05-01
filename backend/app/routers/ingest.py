import uuid
import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path

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
from app.pipeline.option_hydration import option_analyses_by_label, option_annotation_fields, apply_option_annotations
from app.models.payload import JobResponse, ReannotateRequest

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_MIME = {
    "application/pdf", "image/png", "image/jpeg", "image/webp",
    "image/gif", "text/markdown", "text/plain", "application/json",
}
IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _resolve_provider_and_model(
    settings,
    provider_name: str | None,
    model_name: str | None,
) -> tuple[str, str]:
    provider = (provider_name or settings.default_annotation_provider or "anthropic").strip()
    model = (model_name or "").strip()
    if model:
        return provider, model
    if provider == "ollama":
        return provider, settings.default_ollama_model
    return provider, settings.default_annotation_model


def _provider_api_key(settings, provider_name: str) -> str:
    if provider_name == "anthropic":
        return settings.anthropic_api_key
    if provider_name == "openai":
        return settings.openai_api_key
    return ""


def _should_auto_activate_official(settings) -> bool:
    return bool(getattr(settings, "official_auto_activate_for_testing", False))


def _normalize_source_subject_code(value: str | None) -> str | None:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    aliases = {
        "verbal": "verbal",
        "reading_writing": "verbal",
        "reading-writing": "verbal",
        "rw": "verbal",
        "english": "verbal",
        "math": "math",
        "mathematics": "math",
        "m": "math",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"verbal", "math"}:
        raise HTTPException(status_code=422, detail="source_subject_code must be 'verbal' or 'math'")
    return normalized


def _normalize_source_slot(value: str | None, field_name: str) -> str | None:
    normalized = (value or "").strip().upper()
    if not normalized:
        return None
    aliases = {
        "S1": "01",
        "S2": "02",
        "M1": "01",
        "M2": "02",
        "1": "01",
        "2": "02",
        "01": "01",
        "02": "02",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"01", "02"}:
        raise HTTPException(status_code=422, detail=f"{field_name} must be '01' or '02'")
    return normalized


def _normalize_source_metadata(
    source_subject_code: str | None,
    source_section_code: str | None,
    source_module_code: str | None,
) -> tuple[str | None, str | None, str | None]:
    return (
        _normalize_source_subject_code(source_subject_code),
        _normalize_source_slot(source_section_code, "source_section_code"),
        _normalize_source_slot(source_module_code, "source_module_code"),
    )


def _generation_profile_payload(*sources: dict | None) -> dict | None:
    """Extract a stored generation profile when annotation output includes one."""
    merged: dict = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        profile = source.get("generation_profile")
        if isinstance(profile, dict):
            merged.update(profile)
    return merged or None


def _normalize_extracted_questions(extract_root: dict) -> tuple[list[dict], str | None, dict]:
    """Normalize LLM extract output to a list of per-question dicts.

    Handles both the new format (``{passage_text, questions: [...]}``) and
    the legacy single-question format (flat top-level fields).

    Returns ``(questions, shared_passage, shared_source)`` where each question
    dict has its own ``question_text``, ``options``, ``correct_option_label``,
    ``source_question_number``, etc., with shared ``passage_text`` and source
    fields merged in.
    """
    shared_passage = extract_root.get("passage_text")
    shared_source = {
        "source_exam_code": extract_root.get("source_exam_code"),
        "source_subject_code": extract_root.get("source_subject_code"),
        "source_section_code": extract_root.get("source_section_code"),
        "source_module_code": extract_root.get("source_module_code"),
    }

    if "questions" in extract_root and isinstance(extract_root["questions"], list):
        raw_questions = extract_root["questions"]
    else:
        raw_questions = [extract_root]

    questions = []
    for q in raw_questions:
        enriched = dict(q)
        for k, v in shared_source.items():
            if v and not enriched.get(k):
                enriched[k] = v
        if shared_passage and not enriched.get("passage_text"):
            enriched["passage_text"] = shared_passage
        questions.append(enriched)

    return questions, shared_passage, shared_source


async def _persist_single_question(
    db: AsyncSession,
    job: QuestionJob,
    q_data: dict,
    annotate_json: dict,
    passage_text: str | None,
    passage_group_id: uuid.UUID | None,
    overlaps: list,
    section_code: str | None,
) -> uuid.UUID:
    """Create Question + QuestionVersion + QuestionAnnotation + QuestionOption rows.

    Returns the newly created ``question_id`` UUID.
    """
    now = datetime.now(timezone.utc)
    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()

    official_auto_activate = _should_auto_activate_official(get_settings())
    practice_status = (
        "active"
        if job.content_origin == "official" and official_auto_activate
        else "draft" if job.content_origin == "official" else "active"
    )
    overlap_status = "possible" if overlaps else "none"

    question = Question(
        id=question_id,
        content_origin=job.content_origin,
        source_exam_code=q_data.get("source_exam_code"),
        source_subject_code=q_data.get("source_subject_code"),
        source_section_code=q_data.get("source_section_code"),
        source_module_code=q_data.get("source_module_code"),
        source_question_number=q_data.get("source_question_number"),
        stimulus_mode_key=q_data.get("stimulus_mode_key"),
        stem_type_key=q_data.get("stem_type_key"),
        current_question_text=q_data.get("question_text", ""),
        current_passage_text=passage_text or q_data.get("passage_text"),
        current_correct_option_label=q_data.get("correct_option_label", ""),
        current_explanation_text=annotate_json.get("explanation_short", ""),
        practice_status=practice_status,
        official_overlap_status=overlap_status,
        passage_group_id=passage_group_id,
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
        change_source="ingest",
        question_text=q_data.get("question_text", ""),
        passage_text=passage_text or q_data.get("passage_text"),
        choices_jsonb=q_data.get("options", []),
        correct_option_label=q_data.get("correct_option_label", ""),
        explanation_text=annotate_json.get("explanation_short"),
        created_at=now,
    ))

    await db.flush()

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
        generation_profile_jsonb=_generation_profile_payload(q_data, annotate_json),
        confidence_jsonb={"annotation_confidence": annotate_json.get("annotation_confidence", 0.0), "needs_human_review": annotate_json.get("needs_human_review", False)},
        created_at=now,
    ))

    await db.flush()

    question.latest_annotation_id = annotation_id
    question.latest_version_id = version_id

    correct_label = q_data.get("correct_option_label", "")
    opt_analyses = option_analyses_by_label(annotate_json)
    for opt in q_data.get("options", []):
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

    # Link asset to the first created question
    if job.raw_asset_id and not job.question_id:
        asset = await db.get(QuestionAsset, job.raw_asset_id)
        if asset:
            asset.question_id = question_id
            if not asset.source_section_code and section_code:
                asset.source_section_code = section_code

    if overlaps:
        from app.pipeline.overlap import persist_overlap_relations
        await persist_overlap_relations(question_id=question_id, overlaps=overlaps, db=db)

    return question_id


def _export_question(job: QuestionJob, q_data: dict, annotate_json: dict, question_id: uuid.UUID) -> None:
    """Export a single question to YAML after successful persistence."""
    from app.storage.yaml_export import export_official_question, export_generated_question
    from app.config import get_settings

    settings = get_settings()
    source_meta = (job.pass1_json or {}).get("source_metadata", {})
    exam_code = q_data.get("source_exam_code") or source_meta.get("source_exam_code")
    section_code = q_data.get("source_section_code") or source_meta.get("source_section_code")
    module_code = q_data.get("source_module_code") or source_meta.get("source_module_code")

    if job.content_origin == "official" and exam_code and module_code:
        export_official_question(
            question_id=str(question_id),
            exam_code=exam_code,
            module_code=module_code,
            question_number=q_data.get("source_question_number"),
            extract_json=q_data,
            annotate_json=annotate_json,
            section_code=section_code,
            base_dir=settings.local_archive_mirror,
        )
    elif job.content_origin in ("unofficial", "generated"):
        export_generated_question(
            question_id=str(question_id),
            extract_json=q_data,
            annotate_json=annotate_json,
            base_dir=settings.local_archive_mirror,
        )


async def _run_pipeline(job: QuestionJob, db: AsyncSession):
    from app.llm.factory import get_provider
    from app.prompts.extract_prompt import build_extract_prompt
    from app.prompts.annotate_prompt import build_annotate_prompt, enforce_nullability, _detect_domain

    settings = get_settings()
    provider = get_provider(
        job.provider_name,
        api_key=_provider_api_key(settings, job.provider_name),
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

    # ---- Pass 1: Extract (single call, may return multiple questions) ----
    orch.advance()
    job.status = "extracting"
    await db.commit()

    # Save form-submitted metadata before pass1_json is overwritten by LLM extraction
    form_meta = (job.pass1_json or {}).get("source_metadata", {})
    system, user = build_extract_prompt(raw_text[:100000], source_metadata=form_meta)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=16000)
        extract_root = extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
        job.pass1_json = {**extract_root, "_llm_meta": {"provider": result.provider, "model": result.model, "latency_ms": result.latency_ms}}
    except Exception as e:
        orch.fail("extracting", "llm_error", str(e))
        job.status = "failed"
        job.validation_errors_jsonb = [{"step": "extracting", "error": str(e)}]
        await db.commit()
        return

    # Normalize to a list of per-question dicts (handles both new and legacy formats)
    questions_data, shared_passage, shared_source = _normalize_extracted_questions(extract_root)

    # Determine passage_group_id: set only for multi-question batches
    passage_group_id = uuid.uuid4() if len(questions_data) > 1 else None

    # Form-submitted metadata takes precedence; fall back to LLM-extracted values
    exam_code = form_meta.get("source_exam_code") or shared_source.get("source_exam_code")
    subject_code = form_meta.get("source_subject_code") or shared_source.get("source_subject_code")
    section_code = form_meta.get("source_section_code") or shared_source.get("source_section_code")
    module_code = form_meta.get("source_module_code") or shared_source.get("source_module_code")

    # ---- Per-question loop ----
    created_question_ids: list[uuid.UUID] = []
    all_errors: list[dict] = []

    for i, q_data in enumerate(questions_data):
        # Form-submitted metadata takes precedence over LLM-extracted values
        if exam_code:
            q_data["source_exam_code"] = exam_code
        q_data.setdefault("source_subject_code", subject_code)
        q_data.setdefault("source_section_code", section_code)
        q_data.setdefault("source_module_code", module_code)
        # ---- Pass 2: Annotate ----
        job.status = "annotating"
        await db.commit()

        system, user = build_annotate_prompt(q_data)
        try:
            result = await provider.complete(system=system, user=user, max_tokens=8192)
            annotate_json = normalize_annotation(
                extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
            )
            # Hard-enforce domain nullability rules after LLM output
            annotate_json = enforce_nullability(annotate_json, _detect_domain(q_data))
        except Exception as e:
            all_errors.append({"question_index": i, "step": "annotating", "error": str(e), "source_question_number": q_data.get("source_question_number")})
            continue

        # ---- Overlap check (unofficial/generated only) ----
        overlaps: list = []
        if job.content_origin in ("unofficial", "generated"):
            job.status = "overlap_checking"
            await db.commit()

            from app.pipeline.overlap import detect_overlaps

            question_text = q_data.get("question_text", "")
            passage_text = shared_passage or q_data.get("passage_text")

            overlaps = await detect_overlaps(
                question_id=job.id,
                annotation_jsonb=annotate_json,
                passage_text=passage_text,
                question_text=question_text,
                db=db,
            )

        # ---- Validate ----
        job.status = "validating"
        merged = {**q_data, **annotate_json}
        errors = validate_question(merged, content_origin=job.content_origin)

        if any(e["severity"] == "blocking" for e in errors):
            all_errors.append({"question_index": i, "step": "validating", "errors": errors, "source_question_number": q_data.get("source_question_number")})
            continue

        # ---- Persist ----
        question_id = await _persist_single_question(
            db=db,
            job=job,
            q_data=q_data,
            annotate_json=annotate_json,
            passage_text=shared_passage,
            passage_group_id=passage_group_id,
            overlaps=overlaps,
            section_code=section_code,
        )
        created_question_ids.append(question_id)

        # ---- YAML export ----
        _export_question(job, q_data, annotate_json, question_id)

    # ---- Final job status ----
    job.validation_errors_jsonb = all_errors if all_errors else None

    if created_question_ids:
        # At least one question succeeded
        job.question_id = created_question_ids[0]  # primary question for the job
        if job.content_origin == "official" and not _should_auto_activate_official(settings):
            job.status = "needs_review"
        else:
            job.status = "approved"
        job.pass1_json["_created_question_ids"] = [str(qid) for qid in created_question_ids]
    else:
        # All questions failed
        job.status = "failed"

    await db.commit()


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


def _normalize_mime(mime: str | None) -> str:
    return (mime or "").split(";", 1)[0].strip().lower()


def _validate_upload_mime(mime: str | None, allowed: set[str] = ALLOWED_MIME) -> str:
    normalized = _normalize_mime(mime)
    if normalized not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type. Allowed: {allowed_list}",
        )
    return normalized


def _parse_pdf_content(content: bytes) -> dict:
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            tmp_path = Path(tmp.name)
        return parse_pdf(str(tmp_path))
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


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
    source_subject_code: str = Form(""),
    source_section_code: str = Form(""),
    source_module_code: str = Form(""),
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    mime_type = _validate_upload_mime(file.content_type, {"application/pdf"})
    content = await _safe_read(file, MAX_FILE_SIZE)
    source_subject_code, source_section_code, source_module_code = _normalize_source_metadata(
        source_subject_code,
        source_section_code,
        source_module_code,
    )

    storage_path = await save_asset(file.filename or "upload.pdf", content, subfolder="official")
    checksum = compute_checksum(content)

    now = datetime.now(timezone.utc)
    asset_id = uuid.uuid4()
    job_id = uuid.uuid4()

    pdf_result = _parse_pdf_content(content)
    raw_text = "\n\n".join(p["text"] for p in pdf_result["pages"])

    asset = QuestionAsset(
        id=asset_id,
        content_origin="official",
        asset_type="pdf",
        storage_path=storage_path,
        mime_type=mime_type,
        page_start=0,
        page_end=len(pdf_result["pages"]) - 1,
        source_name=file.filename,
        source_exam_code=source_exam_code or None,
        source_subject_code=source_subject_code,
        source_section_code=source_section_code or None,
        source_module_code=source_module_code or None,
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    settings = get_settings()
    provider_name, model_name = _resolve_provider_and_model(settings, provider_name, model_name)
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
            "source_subject_code": source_subject_code,
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
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    mime_type = _validate_upload_mime(file.content_type)
    content = await _safe_read(file, MAX_FILE_SIZE)

    if mime_type in IMAGE_MIME_TYPES:
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

    asset_type = _asset_type_from_mime(mime_type)

    asset = QuestionAsset(
        id=asset_id,
        content_origin="unofficial",
        asset_type=asset_type,
        storage_path=storage_path,
        mime_type=mime_type,
        source_name=file.filename,
        checksum=checksum,
        created_at=now,
    )
    db.add(asset)

    raw_text = ""
    if asset_type == "pdf":
        pdf_result = _parse_pdf_content(content)
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
    provider_name, model_name = _resolve_provider_and_model(settings, provider_name, model_name)
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
    source_subject_code: str = Form(""),
    source_section_code: str = Form(""),
    source_module_code: str = Form(""),
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    if content_origin not in ("official", "unofficial"):
        raise HTTPException(status_code=422, detail="content_origin must be 'official' or 'unofficial'")
    source_subject_code, source_section_code, source_module_code = _normalize_source_metadata(
        source_subject_code,
        source_section_code,
        source_module_code,
    )

    settings = get_settings()
    now = datetime.now(timezone.utc)
    job_id = uuid.uuid4()

    source_metadata = {
        k: v for k, v in {
            "source_exam_code": source_exam_code or None,
            "source_subject_code": source_subject_code,
            "source_section_code": source_section_code or None,
            "source_module_code": source_module_code or None,
        }.items() if v
    }

    provider_name, model_name = _resolve_provider_and_model(settings, provider_name, model_name)
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
        api_key=_provider_api_key(settings, job.provider_name),
        base_url=settings.ollama_base_url,
        default_model=job.model_name,
    )
    extract_json = {}
    if job.pass1_json:
        extract_json = {k: v for k, v in job.pass1_json.items() if not k.startswith("_")}

    # Skip extraction, go straight to annotation
    job.status = "annotating"
    await db.commit()

    from app.prompts.annotate_prompt import enforce_nullability, _detect_domain
    system, user = build_annotate_prompt(extract_json)
    try:
        result = await provider.complete(system=system, user=user, max_tokens=8192)
        annotate_json = normalize_annotation(
            extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
        )
        # Hard-enforce domain nullability rules after LLM output
        domain = _detect_domain(extract_json)
        annotate_json = enforce_nullability(annotate_json, domain)
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

    latest_version_result = await db.execute(
        select(QuestionVersion)
        .where(QuestionVersion.question_id == question.id)
        .order_by(QuestionVersion.version_number.desc())
        .limit(1)
    )
    latest_version = latest_version_result.scalars().first()
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
    await db.flush()  # persist version before annotation FK references it

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
        generation_profile_jsonb=_generation_profile_payload(extract_json, annotate_json),
        confidence_jsonb={"annotation_confidence": annotate_json.get("annotation_confidence", 0.0), "needs_human_review": annotate_json.get("needs_human_review", False)},
        created_at=now,
    ))
    await db.flush()  # ensure annotation ID is visible before setting circular FKs

    question.current_explanation_text = annotate_json.get(
        "explanation_short", question.current_explanation_text
    )
    question.latest_annotation_id = annotation_id
    question.latest_version_id = version_id
    question.annotation_stale = False
    question.updated_at = now

    # Refresh per-option annotation fields from the new annotation
    opts_result = await db.execute(
        select(QuestionOption).where(QuestionOption.question_id == question.id)
    )
    opt_analyses = option_analyses_by_label(annotate_json)
    for option_row in opts_result.scalars().all():
        analysis = opt_analyses.get(option_row.option_label, {})
        if analysis:
            apply_option_annotations(option_row, analysis)

    await db.commit()


async def _run_reannotate_pipeline_with_session(job_id: uuid.UUID):
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if job:
            await _run_reannotate_pipeline(job, db)


@router.post("/unofficial/batch", response_model=list[JobResponse])
async def ingest_unofficial_batch(
    files: list[UploadFile] = File(...),
    provider_name: str | None = Form(None),
    model_name: str | None = Form(None),
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

    # Always synthesize pass1_json from current DB state so the single-question
    # format (question_text, options, etc. at top level) is guaranteed.
    # The old job's pass1_json may be a full-batch extraction (questions list),
    # which the reannotate pipeline cannot validate as a single question.
    ver_result = await db.execute(
        select(QuestionVersion).where(QuestionVersion.id == q.latest_version_id)
    )
    ver = ver_result.scalars().first()
    choices = ver.choices_jsonb if ver else []
    synthesized_pass1 = {
        "question_text": q.current_question_text,
        "passage_text": q.current_passage_text,
        "options": choices,
        "correct_option_label": q.current_correct_option_label,
        "stem_type_key": q.stem_type_key,
        "stimulus_mode_key": q.stimulus_mode_key,
        "source_exam_code": q.source_exam_code,
        "source_section_code": q.source_section_code,
        "source_module_code": q.source_module_code,
        "source_question_number": q.source_question_number,
    }

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
        pass1_json=synthesized_pass1,
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
