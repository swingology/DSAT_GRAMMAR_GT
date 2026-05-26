import uuid
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("Background generate task failed", exc_info=task.exception(), extra={"task": task.get_name()})

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, and_, delete as sa_delete, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.auth import admin_required
from app.config import get_settings
from app.job_limits import run_with_job_limit
from app.llm.errors import error_payload
from app.llm.retry import _is_retryable as _is_llm_retryable
from app.models.db import (
    QuestionJob, Question, QuestionVersion, QuestionAnnotation, QuestionOption,
    GenerationBatch, GenerationBatchIdempotencyKey,
)
from app.parsers.json_parser import extract_json_from_text, normalize_annotation
from app.pipeline.validator import validate_question
from app.pipeline.option_hydration import option_analyses_by_label, option_annotation_fields
from app.pipeline.overlap import detect_overlaps, persist_overlap_relations
from app.models.payload import (
    GenerationRequest, GenerationCompareRequest, JobResponse,
    GenerationBatchRequest, GenerationBatchResponse,
)

router = APIRouter(prefix="/generate", tags=["generate"])

# Keys that describe HOW a question was generated (or workflow metadata around
# the request) but are not part of the question's content lineage. Stripped
# from `Question.generation_source_set` at save time.
#
# `idempotency_key` is included as defense-in-depth: the locked design also
# keeps it out of the batch request payload by storing it in
# `generation_batch_idempotency_keys`, but this filter catches accidental
# leaks if any future code path copies the header into the request dict.
_SOURCE_SET_OPERATIONAL_KEYS = {
    # how it was made
    "provider_name", "model_name", "seed", "temperature",
    # retry plumbing
    "retry_attempt", "idempotency_key",
    # regeneration parent, stored in the dedicated Question FK
    "derived_from_question_id",
    # batch-level workflow metadata that does not belong on a single
    # question's content lineage
    "requested_count", "requested_by", "student_id",
    "requested_by_user_token", "release_policy", "skip_review",
}

_GRAMMAR_SOURCE_EXAMPLE_COUNT = 3
_READING_SOURCE_EXAMPLE_COUNT = 2
_DEFAULT_GENERATION_TEMPERATURE = 0.7
_TRANSIENT_ERROR_MARKERS = (
    "429",
    "too many requests",
    "rate limit",
    "rate_limit",
    "timeout",
    "timed out",
    "connection",
    "connect",
    "network",
    "model loading",
    "temporarily unavailable",
    "server error",
    "service unavailable",
)


def _is_transient_error(exc: Exception | None) -> bool:
    """True for provider/network failures that may resolve on retry."""
    if exc is None:
        return False
    if isinstance(exc, ValueError):
        return False
    if _is_llm_retryable(exc):
        return True
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code == 429 or 500 <= status_code <= 599
    message = str(exc).lower()
    return any(marker in message for marker in _TRANSIENT_ERROR_MARKERS)


def _batch_counter_field(job_status: str) -> str | None:
    """Map a terminal job status to the GenerationBatch counter column name."""
    return {
        "approved": "accepted_count",
        "needs_review": "needs_review_count",
        "failed_permanent": "failed_count",
        "failed_transient": "failed_count",
        "failed": "failed_count",
    }.get(job_status)


async def _rollback_if_possible(db: AsyncSession) -> None:
    rollback = getattr(db, "rollback", None)
    if rollback is not None:
        await rollback()


async def _mark_job_failed(
    job: QuestionJob,
    db: AsyncSession,
    *,
    step: str,
    exc: Exception,
    status: str | None = None,
) -> str:
    final_status = status or (
        "failed_transient" if _is_transient_error(exc) else "failed_permanent"
    )
    job.status = final_status
    job.validation_errors_jsonb = [error_payload(step, exc)]
    await db.commit()
    return final_status


async def _run_auto_review_swarm(
    question_id: uuid.UUID,
    generation_batch_id: uuid.UUID | None,
) -> None:
    from app.review.runner import run_review_swarm

    await run_review_swarm(
        question_id,
        triggered_by="auto_on_save",
        generation_batch_id=generation_batch_id,
    )


def _generation_profile_payload(*sources: dict | None) -> dict | None:
    """Build the stored generation profile from model output and request metadata."""
    merged: dict = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        profile = source.get("generation_profile")
        if isinstance(profile, dict):
            merged.update(profile)
    # Merge the last source (request spec) but exclude operational keys so
    # they don't pollute generation_profile_jsonb.
    if isinstance(sources[-1], dict):
        merged.update({k: v for k, v in sources[-1].items() if k not in _SOURCE_SET_OPERATIONAL_KEYS})
    return merged or None


def _provider_api_key(settings, provider_name: str) -> str:
    if provider_name == "anthropic":
        return settings.anthropic_api_key
    if provider_name == "openai":
        return settings.openai_api_key
    return ""


def _without_none_values(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if value is not None}


def _clean_option_label(label: object | None) -> str:
    """Normalize model-emitted labels like 'A)', 'A.', or 'a' to 'A'."""
    if label is None:
        return ""
    return str(label).strip().rstrip(").").upper()


def _normalize_generated_options(options: object) -> object:
    if not isinstance(options, list):
        return options

    normalized: list[object] = []
    for opt in options:
        if not isinstance(opt, dict):
            normalized.append(opt)
            continue

        option = dict(opt)
        raw_label = (
            option.get("label")
            or option.get("option_label")
            or option.get("letter")
            or option.get("choice_label")
        )
        raw_text = (
            option.get("text")
            or option.get("option_text")
            or option.get("answer_text")
            or option.get("choice_text")
        )
        option["label"] = _clean_option_label(raw_label)
        option["text"] = raw_text or ""
        normalized.append(option)

    if len(normalized) == 4 and all(
        isinstance(opt, dict) and not opt.get("label")
        for opt in normalized
    ):
        for idx, opt in enumerate(normalized):
            opt["label"] = "ABCD"[idx]

    return normalized


def _normalize_generated_question(data: dict) -> dict:
    """Flatten generated-question payloads that wrap fields under question."""
    flat = dict(data)
    question = data.get("question")

    field_aliases = {
        "question_text": ("question_text", "prompt_text", "stem_text", "stem"),
        "passage_text": ("passage_text", "stimulus_text"),
        "paired_passage_text": ("paired_passage_text",),
        "underlined_text": ("underlined_text",),
        "options": ("options", "answer_options", "choices"),
        "correct_option_label": ("correct_option_label", "correct_answer_label"),
    }
    for target, aliases in field_aliases.items():
        if flat.get(target) is not None:
            continue
        for alias in aliases:
            value = flat.get(alias)
            if value is None and isinstance(question, dict):
                value = question.get(alias)
            if value is not None:
                flat[target] = value
                break

    if "correct_option_label" in flat:
        flat["correct_option_label"] = _clean_option_label(flat.get("correct_option_label"))
    if "options" in flat:
        flat["options"] = _normalize_generated_options(flat.get("options"))
    return flat


async def _load_official_source_examples(db: AsyncSession, source_question_ids: list[str] | None) -> list[dict]:
    """Load stored official questions to use as generation source examples."""
    if not source_question_ids:
        return []

    parsed_ids: list[uuid.UUID] = []
    for raw_id in source_question_ids:
        try:
            parsed_ids.append(uuid.UUID(str(raw_id)))
        except (TypeError, ValueError):
            logger.warning("Ignoring invalid source_question_id for generation: %r", raw_id)

    if not parsed_ids:
        return []

    q_result = await db.execute(
        select(Question).where(
            Question.id.in_(parsed_ids),
            Question.content_origin == "official",
        )
    )
    questions = q_result.unique().scalars().all()
    q_by_id = {q.id: q for q in questions}

    ann_ids = [
        getattr(q, "latest_annotation_id", None)
        for q in questions
        if getattr(q, "latest_annotation_id", None)
    ]
    if ann_ids:
        ann_result = await db.execute(select(QuestionAnnotation).where(QuestionAnnotation.id.in_(ann_ids)))
        ann_by_id = {ann.id: ann for ann in ann_result.scalars().all()}
    else:
        ann_by_id = {}

    version_to_qid = {q.latest_version_id: q.id for q in questions if q.latest_version_id}
    opts_by_qid: dict[uuid.UUID, list[QuestionOption]] = {}
    if version_to_qid:
        opts_result = await db.execute(
            select(QuestionOption)
            .where(QuestionOption.question_version_id.in_(list(version_to_qid.keys())))
            .order_by(QuestionOption.question_id, QuestionOption.option_label)
        )
        for opt in opts_result.scalars().all():
            qid = version_to_qid.get(opt.question_version_id)
            if qid:
                opts_by_qid.setdefault(qid, []).append(opt)

    examples: list[dict] = []
    for source_id in parsed_ids:
        q = q_by_id.get(source_id)
        if not q:
            logger.warning("Generation source_question_id was not a stored official question: %s", source_id)
            continue

        ann = ann_by_id.get(q.latest_annotation_id) if q.latest_annotation_id else None
        example = _without_none_values({
            "source_question_id": str(q.id),
            "source_exam_code": q.source_exam_code,
            "source_subject_code": q.source_subject_code,
            "source_section_code": q.source_section_code,
            "source_module_code": q.source_module_code,
            "source_question_number": q.source_question_number,
            "stimulus_mode_key": q.stimulus_mode_key,
            "stem_type_key": q.stem_type_key,
            "question_text": q.current_question_text,
            "passage_text": q.current_passage_text,
            "paired_passage_text": q.current_paired_passage_text,
            "underlined_text": q.current_underlined_text,
            "correct_option_label": q.current_correct_option_label,
            "annotation": ann.annotation_jsonb if ann else None,
        })
        options = [
            _without_none_values({
                "label": opt.option_label,
                "text": opt.option_text,
                "is_correct": opt.is_correct,
                "distractor_type_key": opt.distractor_type_key,
                "why_plausible": opt.why_plausible,
                "why_wrong": opt.why_wrong,
                "student_failure_mode_key": opt.student_failure_mode_key,
            })
            for opt in opts_by_qid.get(q.id, [])
        ]
        if options:
            example["options"] = options
        examples.append(example)

    return examples


def _annotation_payload(annotation: QuestionAnnotation | None) -> dict:
    if annotation and isinstance(annotation.annotation_jsonb, dict):
        return annotation.annotation_jsonb
    return {}


async def _latest_annotations_for_questions(
    db: AsyncSession,
    questions: list[Question],
) -> dict[uuid.UUID, QuestionAnnotation]:
    ann_ids = [
        getattr(q, "latest_annotation_id", None)
        for q in questions
        if getattr(q, "latest_annotation_id", None)
    ]
    if not ann_ids:
        return {}

    ann_result = await db.execute(
        select(QuestionAnnotation).where(QuestionAnnotation.id.in_(ann_ids))
    )
    annotations = ann_result.scalars().all()
    return {ann.question_id: ann for ann in annotations}


def _source_question_domain(
    question: Question,
    annotation: QuestionAnnotation | None,
) -> str | None:
    ann = _annotation_payload(annotation)
    if ann.get("grammar_role_key") or ann.get("grammar_focus_key"):
        return "grammar"
    if (
        ann.get("reading_skill_family_key")
        or ann.get("skill_family_key")
        or ann.get("reading_focus_key")
    ):
        return "reading"

    if not getattr(question, "current_passage_text", None):
        return "grammar"
    return None


def _matches_batch_target(
    question: Question,
    annotation: QuestionAnnotation | None,
    body: GenerationBatchRequest,
    domain: str,
    *,
    exact: bool,
) -> bool:
    inferred_domain = _source_question_domain(question, annotation)
    if inferred_domain is not None and inferred_domain != domain:
        return False
    if not exact:
        return True

    ann = _annotation_payload(annotation)
    requested_stimulus = body.stimulus_mode_key
    source_stimulus = ann.get("stimulus_mode_key") or getattr(question, "stimulus_mode_key", None)
    if requested_stimulus and source_stimulus and source_stimulus != requested_stimulus:
        return False

    if domain == "grammar":
        return (
            ann.get("grammar_role_key") == body.target_grammar_role_key
            and ann.get("grammar_focus_key") == body.target_grammar_focus_key
        )

    reading_skill = body.target_reading_skill_family_key or body.target_skill_family_key
    source_skill = ann.get("reading_skill_family_key") or ann.get("skill_family_key")
    return (
        source_skill == reading_skill
        and ann.get("reading_focus_key") == body.target_reading_focus_key
    )


def _difficulty_sort_key(
    question: Question,
    annotation: QuestionAnnotation | None,
    body: GenerationBatchRequest,
) -> tuple[int, str, int]:
    ann = _annotation_payload(annotation)
    difficulty_penalty = 0 if ann.get("difficulty_overall") == body.difficulty_overall else 1
    exam = getattr(question, "source_exam_code", None) or ""
    number = getattr(question, "source_question_number", None) or 0
    return (difficulty_penalty, exam, number)


async def _recent_generation_source_ids(
    db: AsyncSession,
    *,
    limit: int = 50,
) -> set[uuid.UUID]:
    """Return official source IDs used by recent generated questions."""
    result = await db.execute(
        select(Question.generation_source_set)
        .where(Question.content_origin == "generated")
        .order_by(Question.created_at.desc())
        .limit(limit)
    )
    recent_ids: set[uuid.UUID] = set()
    for row in result.all():
        payload = None
        try:
            payload = row[0]
        except (TypeError, KeyError, IndexError):
            payload = getattr(row, "generation_source_set", None)
        if not isinstance(payload, dict):
            continue
        for raw_id in payload.get("source_question_ids") or []:
            try:
                recent_ids.add(uuid.UUID(str(raw_id)))
            except (TypeError, ValueError):
                continue
    return recent_ids


def _rotate_source_ids(
    candidates: list[Question],
    *,
    requested_count: int,
    source_count: int,
) -> list[list[str]]:
    if not candidates:
        return [[] for _ in range(requested_count)]

    take_count = min(source_count, len(candidates))
    selections: list[list[str]] = []
    for job_index in range(requested_count):
        start = job_index % len(candidates)
        ordered = [
            candidates[(start + offset) % len(candidates)]
            for offset in range(len(candidates))
        ]
        selected: list[Question] = []
        seen_exams: set[str] = set()
        for candidate in ordered:
            exam = getattr(candidate, "source_exam_code", None) or ""
            if exam in seen_exams:
                continue
            selected.append(candidate)
            seen_exams.add(exam)
            if len(selected) == take_count:
                break
        if len(selected) < take_count:
            selected_ids = {q.id for q in selected}
            for candidate in ordered:
                if candidate.id in selected_ids:
                    continue
                selected.append(candidate)
                if len(selected) == take_count:
                    break
        selections.append([str(q.id) for q in selected])
    return selections


async def _select_source_question_ids_for_batch(
    db: AsyncSession,
    body: GenerationBatchRequest,
    domain: str,
    parsed_source_ids: list[uuid.UUID],
) -> list[list[str]]:
    if parsed_source_ids:
        exact_ids = [str(source_id) for source_id in parsed_source_ids]
        return [list(exact_ids) for _ in range(body.requested_count)]

    result = await db.execute(
        select(Question).where(
            Question.content_origin == "official",
            Question.practice_status == "active",
        )
    )
    questions = [
        q for q in result.unique().scalars().all()
        if (
            getattr(q, "content_origin", None) == "official"
            and getattr(q, "practice_status", None) == "active"
        )
    ]
    annotations = await _latest_annotations_for_questions(db, questions)

    exact_matches = [
        q for q in questions
        if _matches_batch_target(q, annotations.get(q.id), body, domain, exact=True)
    ]
    if exact_matches:
        candidates = exact_matches
    else:
        canonical = [
            q for q in questions
            if getattr(q, "is_canonical_source", False)
            and _matches_batch_target(q, annotations.get(q.id), body, domain, exact=False)
        ]
        candidates = canonical or [
            q for q in questions
            if _matches_batch_target(q, annotations.get(q.id), body, domain, exact=False)
        ]

    source_count = (
        _GRAMMAR_SOURCE_EXAMPLE_COUNT
        if domain == "grammar"
        else _READING_SOURCE_EXAMPLE_COUNT
    )
    recent_source_ids = await _recent_generation_source_ids(db)
    if recent_source_ids:
        non_recent = [q for q in candidates if q.id not in recent_source_ids]
        if len(non_recent) >= source_count:
            candidates = non_recent

    candidates = sorted(
        candidates,
        key=lambda q: _difficulty_sort_key(q, annotations.get(q.id), body),
    )
    return _rotate_source_ids(
        candidates,
        requested_count=body.requested_count,
        source_count=source_count,
    )


async def _run_generate_pipeline(job: QuestionJob, db: AsyncSession, request_data: dict) -> str:
    from app.llm.factory import get_provider
    from app.prompts.generate_prompt import build_generate_prompt_parts
    from app.prompts.annotate_prompt import build_annotate_prompt_parts

    settings = get_settings()
    try:
        provider = get_provider(
            job.provider_name,
            api_key=_provider_api_key(settings, job.provider_name),
            base_url=settings.ollama_base_url,
            default_model=job.model_name,
        )
        source_examples = await _load_official_source_examples(db, request_data.get("source_question_ids"))
        gen_static, gen_dynamic, gen_user = build_generate_prompt_parts(
            generation_request=request_data, source_examples=source_examples
        )
    except Exception as exc:
        logger.error("Generate setup failed (job %s): %s", job.id, exc)
        return await _mark_job_failed(job, db, step="generating_setup", exc=exc)

    # Generate — 3-attempt retry on malformed JSON
    generated = None
    _last_err: Exception | None = None
    for _attempt in range(3):
        try:
            result = await provider.complete_cached(
                system_static=gen_static, system_dynamic=gen_dynamic,
                user=gen_user, max_tokens=8192, temperature=0.7,
            )
            generated = _normalize_generated_question(
                extract_json_from_text(result.raw_text, job.provider_name, job.model_name)
            )
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
        return await _mark_job_failed(
            job,
            db,
            step="generating",
            exc=_last_err or Exception("unknown"),
        )

    # Annotate — 3-attempt retry on malformed JSON
    try:
        ann_static, ann_dynamic, ann_user = build_annotate_prompt_parts(generated)
    except Exception as exc:
        logger.error("Generate annotation prompt failed (job %s): %s", job.id, exc)
        return await _mark_job_failed(job, db, step="annotating_setup", exc=exc)
    annotate_json = None
    _last_err = None
    for _attempt in range(3):
        try:
            result = await provider.complete_cached(
                system_static=ann_static, system_dynamic=ann_dynamic,
                user=ann_user, max_tokens=8192,
            )
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
        return await _mark_job_failed(
            job,
            db,
            step="annotating",
            exc=_last_err or Exception("unknown"),
        )

    # Validate and create question
    merged = {**generated, **annotate_json, "generation_source_set": request_data}
    try:
        errors = validate_question(merged, content_origin="generated")
    except Exception as exc:
        logger.error("Generate validation failed unexpectedly (job %s): %s", job.id, exc)
        return await _mark_job_failed(
            job,
            db,
            step="validating",
            exc=exc,
            status="failed_permanent",
        )
    job.validation_errors_jsonb = errors

    if any(e["severity"] == "blocking" for e in errors):
        job.status = "failed_permanent"
        await db.commit()
        return "failed_permanent"

    job.status = "approved"

    question_id = uuid.uuid4()
    version_id = uuid.uuid4()
    annotation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    derived_from_question_id = None
    if request_data.get("derived_from_question_id"):
        try:
            derived_from_question_id = uuid.UUID(str(request_data["derived_from_question_id"]))
        except (TypeError, ValueError) as exc:
            return await _mark_job_failed(
                job,
                db,
                step="validating",
                exc=exc,
                status="failed_permanent",
            )

    # Persist inside a savepoint so a DB error only rolls back this question,
    # leaving the session valid for the status update that follows.
    job_id_for_log = job.id
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
                derived_from_question_id=derived_from_question_id,
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
            await db.flush()

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
        if getattr(job, "generation_batch_id", None):
            await db.execute(
                sa_update(GenerationBatch)
                .where(GenerationBatch.id == job.generation_batch_id)
                .values(
                    created_count=GenerationBatch.created_count + 1,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
    except Exception as _persist_err:
        logger.error("Generate persist failed (job %s): %s", job_id_for_log, _persist_err)
        await _rollback_if_possible(db)
        refreshed_job = await db.get(QuestionJob, job_id_for_log)
        return await _mark_job_failed(
            refreshed_job or job,
            db,
            step="persisting",
            exc=_persist_err,
            status="failed_permanent",
        )

    # Run overlap detection against official questions and update status if found
    job.status = "overlap_checking"
    await db.commit()
    try:
        overlaps = await detect_overlaps(
            question_id=question_id,
            annotation_jsonb=annotate_json,
            passage_text=generated.get("passage_text"),
            question_text=generated.get("question_text", ""),
            db=db,
        )
        from app.storage.yaml_export import export_generated_question
        export_generated_question(
            question_id=str(question_id),
            extract_json=generated,
            annotate_json=annotate_json,
            generation_source_set=request_data,
            base_dir=settings.local_archive_mirror,
        )

        if overlaps:
            await persist_overlap_relations(question_id=question_id, overlaps=overlaps, db=db)
            q_created = await db.get(Question, question_id)
            if q_created:
                q_created.official_overlap_status = "possible"
            job.status = "needs_review"
            job.validation_errors_jsonb = [
                *(job.validation_errors_jsonb or []),
                {
                    "severity": "review",
                    "field": "official_overlap_status",
                    "message": "Generated question has possible official overlap",
                },
            ]
            await db.commit()
            return "needs_review"
        job.status = "approved"
        await db.commit()
        if not request_data.get("skip_review"):
            asyncio.create_task(
                _run_auto_review_swarm(
                    question_id,
                    getattr(job, "generation_batch_id", None),
                )
            ).add_done_callback(_log_task_exception)
        return "approved"
    except Exception as exc:
        logger.error("Generate overlap/export failed (job %s): %s", job.id, exc)
        await _rollback_if_possible(db)
        return await _mark_job_failed(
            job,
            db,
            step="overlap_checking",
            exc=exc,
            status="failed_permanent",
        )


async def _update_batch_counters(
    batch_id: uuid.UUID,
    job_status: str,
    db: AsyncSession,
) -> None:
    counter = _batch_counter_field(job_status)
    if counter is None:
        return
    col = getattr(GenerationBatch, counter)
    await db.execute(
        sa_update(GenerationBatch)
        .where(GenerationBatch.id == batch_id)
        .values(**{counter: col + 1, "updated_at": datetime.now(timezone.utc)})
    )
    await db.commit()


async def _run_batch_job(
    job_id: uuid.UUID,
    batch_id: uuid.UUID,
    request_data: dict,
    *,
    is_retry: bool = False,
) -> None:
    async with async_session() as db:
        job = await db.get(QuestionJob, job_id)
        if job is None:
            return
        if is_retry:
            job.status = "retrying"
            job.retry_count = (job.retry_count or 0) + 1
            job.last_retry_at = datetime.now(timezone.utc)
            await db.commit()
        try:
            terminal_status = await _run_generate_pipeline(job, db, request_data)
        except Exception as exc:
            logger.error("Batch generate job failed unexpectedly (job %s): %s", job.id, exc)
            await _rollback_if_possible(db)
            terminal_status = await _mark_job_failed(
                job,
                db,
                step="running_batch_job",
                exc=exc,
            )
        await _update_batch_counters(batch_id, terminal_status, db)


async def _run_retry_batch_job(
    job_id: uuid.UUID,
    batch_id: uuid.UUID,
    request_data: dict,
) -> None:
    await _run_batch_job(job_id, batch_id, request_data, is_retry=True)
    async with async_session() as db:
        await _finalize_batch_status(batch_id, db)


async def _finalize_batch_status(batch_id: uuid.UUID, db: AsyncSession) -> None:
    batch = await db.get(GenerationBatch, batch_id)
    if batch is None:
        return
    terminal = (batch.accepted_count or 0) + (batch.needs_review_count or 0) + (batch.failed_count or 0)
    if terminal < batch.requested_count:
        return
    final_status = "failed" if (batch.failed_count or 0) == batch.requested_count else "completed"
    batch.status = final_status
    batch.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def _run_batch_pipeline(batch_id: uuid.UUID) -> None:
    async with async_session() as db:
        batch = await db.get(GenerationBatch, batch_id)
        if batch is None:
            return
        batch.status = "generating"
        batch.updated_at = datetime.now(timezone.utc)
        await db.commit()

        result = await db.execute(
            select(QuestionJob).where(
                QuestionJob.generation_batch_id == batch_id,
                QuestionJob.status == "pending",
            )
        )
        job_specs = [(j.id, j.generation_request_jsonb) for j in result.scalars().all()]

    tasks = [
        asyncio.create_task(
            run_with_job_limit(lambda jid=jid, req=req: _run_batch_job(jid, batch_id, req))
        )
        for jid, req in job_specs
    ]
    for t in tasks:
        t.add_done_callback(_log_task_exception)
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    async with async_session() as db:
        await _finalize_batch_status(batch_id, db)


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
        prompt_version="v8.0",
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
            prompt_version="v8.0",
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


# --- Phase 1: Generation batches ---------------------------------------------

async def _validate_source_question_ids(
    db: AsyncSession,
    source_ids: list[str] | None,
    domain: str,
) -> list[uuid.UUID]:
    """Confirm caller-supplied source IDs exist, are official, and match the
    target domain.

    Per the Phase 1 locked decision (Q9): caller-passed IDs are used
    exactly, with no auto-augment. Request-time validation returns 400
    on any failure so the caller can fix the request before any job is
    queued.

    `domain` is 'grammar' or 'reading' (derived from which target keys
    the validated request populated).
    """
    if not source_ids:
        return []

    parsed: list[uuid.UUID] = []
    for raw_id in source_ids:
        try:
            parsed.append(uuid.UUID(str(raw_id)))
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source_question_id: {raw_id!r}",
            )

    result = await db.execute(
        select(Question).where(Question.id.in_(parsed))
    )
    by_id = {q.id: q for q in result.unique().scalars().all()}

    missing = [str(qid) for qid in parsed if qid not in by_id]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "source_question_ids include unknown question id(s)",
                "missing": missing,
            },
        )

    non_official = [
        str(qid) for qid, q in by_id.items() if q.content_origin != "official"
    ]
    if non_official:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "source_question_ids must point to official questions",
                "non_official": non_official,
            },
        )

    annotations = await _latest_annotations_for_questions(db, list(by_id.values()))

    # Domain mismatch: a grammar request can't use reading source examples
    # (and vice versa). Prefer latest annotation keys because passage presence
    # alone is not authoritative for all grammar items.
    mismatched: list[str] = []
    for qid, q in by_id.items():
        source_domain = _source_question_domain(q, annotations.get(qid))
        if source_domain is not None and source_domain != domain:
            mismatched.append(str(qid))

    if mismatched:
        raise HTTPException(
            status_code=400,
            detail={
                "error": (
                    "source_question_ids include questions whose domain "
                    f"appears to mismatch the request domain ({domain!r})"
                ),
                "mismatched": mismatched,
            },
        )

    return parsed


def _domain_for_batch(body: GenerationBatchRequest) -> str:
    """Return 'grammar' or 'reading' based on which target keys the
    request populated. Assumes the request passed model validation,
    so exactly one domain is in use.
    """
    if body.target_grammar_role_key or body.target_grammar_focus_key:
        return "grammar"
    return "reading"


@router.post("/batches", response_model=GenerationBatchResponse)
async def create_generation_batch(
    body: GenerationBatchRequest,
    db: AsyncSession = Depends(get_db),
    auth_token: str = Depends(admin_required),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """Create a batch of N targeted generation jobs.

    `requested_by` is derived from the auth dependency (admin endpoint;
    always 'admin'). Phase 8 will introduce a student-token endpoint
    that sets it to 'self_study_agent'.

    `Idempotency-Key` (optional header): if supplied and a non-expired
    mapping exists for `(key, requested_by)`, returns the original
    batch's response with `idempotent_replay=true`. Empty/missing header
    opts out.

    Jobs are created in `pending` status. Phase 2 wires the runner;
    Phase 1 only queues.
    """
    settings = get_settings()
    requested_by = "admin"
    requested_by_user_token = None
    student_id = None
    now = datetime.now(timezone.utc)

    # Idempotency lookup runs BEFORE config caps so a replay returns the
    # original batch even if a different body would have failed validation.
    if idempotency_key:
        await db.execute(
            sa_delete(GenerationBatchIdempotencyKey).where(
                and_(
                    GenerationBatchIdempotencyKey.idempotency_key == idempotency_key,
                    GenerationBatchIdempotencyKey.requested_by == requested_by,
                    GenerationBatchIdempotencyKey.expires_at <= now,
                )
            )
        )
        result = await db.execute(
            select(GenerationBatchIdempotencyKey).where(
                and_(
                    GenerationBatchIdempotencyKey.idempotency_key == idempotency_key,
                    GenerationBatchIdempotencyKey.requested_by == requested_by,
                )
            )
        )
        existing = result.scalars().first()
        if existing is not None:
            batch_result = await db.execute(
                select(GenerationBatch).where(GenerationBatch.id == existing.generation_batch_id)
            )
            batch = batch_result.scalars().first()
            if batch is not None:
                job_result = await db.execute(
                    select(QuestionJob).where(QuestionJob.generation_batch_id == batch.id)
                )
                job_ids = [str(j.id) for j in job_result.scalars().all()]
                return GenerationBatchResponse(
                    id=str(batch.id),
                    status=batch.status,
                    requested_count=batch.requested_count,
                    created_at=batch.created_at,
                    job_ids=job_ids,
                    idempotent_replay=True,
                )

    # Caps only after idempotency miss.
    if body.requested_count > settings.generation_max_batch_size:
        raise HTTPException(
            status_code=422,
            detail=(
                f"requested_count {body.requested_count} exceeds "
                f"GENERATION_MAX_BATCH_SIZE={settings.generation_max_batch_size}"
            ),
        )

    # Pending-batch cap (admin can't queue runaway work).
    pending_count_result = await db.execute(
        select(GenerationBatch).where(
            GenerationBatch.status.in_(("pending", "generating", "reviewing"))
        )
    )
    pending_batches = pending_count_result.scalars().all()
    if len(pending_batches) >= settings.generation_max_pending_batches:
        raise HTTPException(
            status_code=429,
            detail=(
                f"pending batch count {len(pending_batches)} has reached "
                f"GENERATION_MAX_PENDING_BATCHES="
                f"{settings.generation_max_pending_batches}"
            ),
        )

    # Validate caller-supplied source IDs (request-time, exact match per Q9).
    domain = _domain_for_batch(body)
    parsed_source_ids = await _validate_source_question_ids(
        db, body.source_question_ids, domain
    )
    per_job_source_ids = await _select_source_question_ids_for_batch(
        db, body, domain, parsed_source_ids
    )

    # Persist the batch.
    request_jsonb = body.model_dump()
    request_jsonb.update({
        "requested_by": requested_by,
        "student_id": student_id,
        "requested_by_user_token": requested_by_user_token,
    })
    batch = GenerationBatch(
        requested_count=body.requested_count,
        request_jsonb=request_jsonb,
        requested_by=requested_by,
        student_id=student_id,
        requested_by_user_token=requested_by_user_token,
        release_policy=body.release_policy,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(batch)
    await db.flush()  # populate batch.id before linking jobs

    job_ids: list[str] = []
    provider_name = body.provider_name or settings.default_annotation_provider
    model_name = body.model_name or settings.default_annotation_model
    for job_index in range(body.requested_count):
        job_id = uuid.uuid4()
        per_job_request = dict(request_jsonb)
        per_job_request.pop("requested_count", None)
        per_job_request.update({
            "source_question_ids": per_job_source_ids[job_index],
            "provider_name": provider_name,
            "model_name": model_name,
            "seed": job_id.int % 2_147_483_647,
            "temperature": _DEFAULT_GENERATION_TEMPERATURE,
            "retry_attempt": 0,
        })
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
            generation_batch_id=batch.id,
            generation_request_jsonb=per_job_request,
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        job_ids.append(str(job_id))

    if idempotency_key:
        db.add(
            GenerationBatchIdempotencyKey(
                idempotency_key=idempotency_key,
                requested_by=requested_by,
                generation_batch_id=batch.id,
                expires_at=now + timedelta(
                    hours=settings.generation_batch_idempotency_ttl_hours
                ),
                created_at=now,
            )
        )

    await db.commit()

    asyncio.create_task(_run_batch_pipeline(batch.id)).add_done_callback(_log_task_exception)

    return GenerationBatchResponse(
        id=str(batch.id),
        status=batch.status,
        requested_count=batch.requested_count,
        created_at=batch.created_at,
        job_ids=job_ids,
        idempotent_replay=False,
    )


@router.get("/batches/{batch_id}")
async def get_generation_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    try:
        bid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    batch = await db.get(GenerationBatch, bid)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    return {
        "id": str(batch.id),
        "status": batch.status,
        "requested_count": batch.requested_count,
        "created_count": batch.created_count,
        "accepted_count": batch.accepted_count,
        "rejected_count": batch.rejected_count,
        "failed_count": batch.failed_count,
        "needs_review_count": batch.needs_review_count,
        "requested_by": batch.requested_by,
        "release_policy": batch.release_policy,
        "request_jsonb": batch.request_jsonb,
        "regenerate_source_batch_id":
            str(batch.regenerate_source_batch_id) if batch.regenerate_source_batch_id else None,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
    }


@router.get("/batches/{batch_id}/questions")
async def list_batch_questions(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """List jobs (and their resulting question ids when available) for a
    batch.

    Phase 1 returns jobs in `pending` state with `question_id=null`.
    Phase 2's runner populates `question_id` once a candidate is saved.
    """
    try:
        bid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    batch = await db.get(GenerationBatch, bid)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = await db.execute(
        select(QuestionJob).where(QuestionJob.generation_batch_id == bid)
        .order_by(QuestionJob.created_at)
    )
    jobs = result.scalars().all()

    return {
        "batch_id": str(batch.id),
        "status": batch.status,
        "jobs": [
            {
                "id": str(j.id),
                "status": j.status,
                "question_id": str(j.question_id) if j.question_id else None,
                "retry_count": j.retry_count,
                "validation_errors": j.validation_errors_jsonb,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
    }


@router.post("/batches/{batch_id}/retry-failed")
async def retry_failed_batch_jobs(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Retry failed_transient jobs whose retry_count has not yet reached
    GENERATION_JOB_MAX_RETRIES and that do not already have a saved question.
    Decrements failed_count for each job queued so the batch counters stay
    accurate.

    Returns {batch_id, retried_count}.
    """
    try:
        bid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    batch = await db.get(GenerationBatch, bid)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    settings = get_settings()
    result = await db.execute(
        select(QuestionJob).where(
            QuestionJob.generation_batch_id == bid,
            QuestionJob.status == "failed_transient",
        )
    )
    failed_transient_jobs = result.scalars().all()
    now = datetime.now(timezone.utc)
    locked = [
        j for j in failed_transient_jobs
        if (j.retry_count or 0) >= settings.generation_job_max_retries
        or getattr(j, "question_id", None) is not None
    ]
    for job in locked:
        job.status = "failed_permanent"
        job.last_retry_at = now

    retriable = [
        j for j in failed_transient_jobs
        if j not in locked
    ]

    if not retriable:
        if locked:
            batch.updated_at = now
            await db.commit()
        return {"batch_id": batch_id, "retried_count": 0}

    # Decrement failed_count before re-queuing so the counter stays accurate
    # (each job will increment it again if it fails again).
    for _j in retriable:
        batch.failed_count = max(0, (batch.failed_count or 0) - 1)
    batch.status = "generating"
    batch.updated_at = now
    await db.commit()

    for job in retriable:
        jid = job.id
        req = job.generation_request_jsonb or {}
        asyncio.create_task(
            run_with_job_limit(lambda jid=jid, req=req: _run_retry_batch_job(jid, bid, req))
        ).add_done_callback(_log_task_exception)

    return {"batch_id": batch_id, "retried_count": len(retriable)}


# --- Phase 4: Batch review swarm -------------------------------------------------


@router.post("/batches/{batch_id}/review-swarm")
async def trigger_batch_review_swarm(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    auth_token: str = Depends(admin_required),
):
    """Run the review swarm on all generated questions in a batch.

    For each question that has been generated but not yet reviewed, creates
    a new review run with all configured reviewers. Questions that already
    have a completed review run are skipped (re-review creates a new run).

    Returns the list of review results per question.
    """
    try:
        bid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    batch = await db.get(GenerationBatch, bid)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    from app.review.runner import run_batch_review_swarm
    try:
        review_results = await run_batch_review_swarm(
            bid,
            triggered_by="manual_batch",
            admin_token=auth_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {
        "batch_id": batch_id,
        "review_results": review_results,
        "reviewed_count": len(review_results),
    }
