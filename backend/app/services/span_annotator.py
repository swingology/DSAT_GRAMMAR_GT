"""Pass 3 span annotation service.

annotate_spans() is the main entrypoint:
  1. Fetch question + its latest QuestionAnnotation from DB
  2. Call the LLM (Anthropic, always — reliable JSON output required)
  3. Validate tokens against passage text + vocabulary
  4. Derive summaries + generate human-readable label
  5. Write passage_spans to QuestionAnnotation and commit

Failures (parse error, validation error) are logged to span_review_queue
instead of raising, so the caller gets a structured result either way.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.llm.anthropic_provider import AnthropicProvider
from app.models.db import Question, QuestionAnnotation, SpanReviewQueue
from app.prompts.span_prompt import (
    build_span_system_prompt,
    build_span_user_message,
    parse_llm_span_response,
)
from app.services.span_label import generate_span_label
from app.services.span_validator import derive_summaries, is_valid, validate_tokens


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _log_failure(
    db: AsyncSession,
    question_id: UUID,
    annotation_id: UUID | None,
    error_type: str,
    error_detail: str,
    raw: object,
) -> None:
    """Insert a span_review_queue row. Never raises."""
    try:
        entry = SpanReviewQueue(
            question_id=question_id,
            annotation_id=annotation_id,
            error_type=error_type,
            error_detail=error_detail,
            raw_llm_output=raw if isinstance(raw, dict) else {"raw": str(raw)[:4000]},
        )
        db.add(entry)
        await db.commit()
    except Exception:
        pass


async def annotate_spans(
    question_id: UUID,
    db: AsyncSession,
    provider: AnthropicProvider | None = None,
) -> dict:
    """Annotate a single question's passage with word-level span data.

    Returns a dict with "status": "ok" | "failed".
    """
    # 1. Fetch question
    q: Question | None = await db.get(Question, question_id)
    if not q:
        raise ValueError(f"Question {question_id} not found")
    if not q.latest_annotation_id:
        raise ValueError(
            f"Question {question_id} has no annotation — run Pass 2 first"
        )

    ann: QuestionAnnotation | None = await db.get(
        QuestionAnnotation, q.latest_annotation_id
    )
    if not ann:
        raise ValueError(
            f"QuestionAnnotation {q.latest_annotation_id} not found in DB"
        )

    ann_data: dict = ann.annotation_jsonb or {}

    if q.current_passage_text:
        passage_text = q.current_passage_text
        passage_text_source = "current_passage_text"
    elif q.current_question_text:
        passage_text = q.current_question_text
        passage_text_source = "current_question_text"
    else:
        raise ValueError(f"Question {question_id} has no passage text")

    grammar_focus_key = ann_data.get("grammar_focus_key")
    grammar_role_key = ann_data.get("grammar_role_key")
    syntactic_trap_key = ann_data.get("syntactic_trap_key")
    secondary_keys = ann_data.get("secondary_grammar_focus_keys") or []

    # 2. Build provider if not supplied
    if provider is None:
        settings = get_settings()
        provider = AnthropicProvider(
            api_key=settings.anthropic_api_key,
            default_model=settings.span_annotator_model,
        )

    system = build_span_system_prompt()
    user = build_span_user_message(
        passage_text, grammar_focus_key, grammar_role_key,
        syntactic_trap_key, secondary_keys,
    )

    # 3. Call LLM (with one retry on parse failure)
    raw: str | None = None
    tokens: list[dict] | None = None
    for attempt in range(2):
        user_msg = user
        if attempt == 1:
            user_msg = (
                user + "\n\nYour previous response was not valid JSON. "
                "Return ONLY a JSON array, nothing else. No prose, no markdown."
            )
        try:
            resp = await provider.complete(system=system, user=user_msg, max_tokens=4096)
            # AnthropicProvider.complete returns a LLMResponse dataclass; older/test
            # mocks may return a plain str. Accept both.
            raw = resp.raw_text if hasattr(resp, "raw_text") else resp
            tokens = parse_llm_span_response(raw)
            break
        except ValueError:
            if attempt == 1:
                # Both attempts failed — log and return
                await _log_failure(
                    db, q.id, ann.id, "parse_error",
                    f"Failed to parse LLM response after 2 attempts",
                    {"raw": (raw or "")[:4000]},
                )
                return {"status": "failed", "error_type": "parse_error"}

    if tokens is None:
        return {"status": "failed", "error_type": "parse_error"}

    # 4. Validate
    errors = validate_tokens(tokens, passage_text, grammar_focus_key)
    if errors:
        for err in errors:
            await _log_failure(
                db, q.id, ann.id,
                err.error_type, err.error_detail,
                {"tokens": tokens, "raw": (raw or "")[:2000]},
            )
        return {
            "status": "failed",
            "error_types": [e.error_type for e in errors],
        }

    # 5. Derive summaries + label
    anatomy_present, concepts_present = derive_summaries(tokens)
    label = generate_span_label(grammar_focus_key, anatomy_present, concepts_present)

    # 6. Write to DB
    ann.passage_spans = {
        "label": label,
        "anatomy_present": anatomy_present,
        "concepts_present": concepts_present,
        "tokens": tokens,
        "passage_text_source": passage_text_source,
    }
    ann.span_annotated_at = _utcnow()
    ann.span_model_name = provider.default_model
    await db.commit()

    return {
        "status": "ok",
        "label": label,
        "anatomy_present": anatomy_present,
        "concepts_present": concepts_present,
        "token_count": len(tokens),
    }
