"""TASK-027 — span_annotator.py integration tests for annotate_spans().

Covers the async annotation service end-to-end with the LLM and DB mocked:
  1. happy path — valid tokens → passage_spans written, commit called, status "ok"
  2. question not found → ValueError
  3. question has no annotation → ValueError
  4. parse error on both attempts → failure logged to span_review_queue, status "failed"
  5. validation failure (concat_mismatch) → failure logged, status "failed"
  6. retry path — first call invalid JSON, second call valid → status "ok"

DB is mocked with a per-test AsyncMock that routes db.get() to fake Question /
QuestionAnnotation stand-ins. LLM is mocked via an AsyncMock provider returning
LLMResponse objects (matching the real AnthropicProvider.complete contract).
"""
import os

# Force env before any app imports (see conftest.py)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test"
)
os.environ.setdefault("ADMIN_API_KEYS", "admin-test-key")
os.environ.setdefault("STUDENT_API_KEYS", "student-test-key")

import json
import sys
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, "/home/jb/DSAT_REDUX_MD/backend")

from app.llm.base import LLMResponse
from app.models.db import Question, QuestionAnnotation, SpanReviewQueue
from app.services.span_annotator import annotate_spans


# ---------------------------------------------------------------------------
# Constants / fixtures
# ---------------------------------------------------------------------------

QUESTION_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ANNOTATION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

# A tiny passage that the LLM tokens must reconstruct exactly for validation.
# The "sat" token carries the grammar_focus_key in concept_tags so the
# missing_primary_concept validator check passes.
PASSAGE = "The cat sat."
VALID_TOKENS_JSON = (
    '[{"text":"The ","anatomy":["determiner"],"concept_tags":[],"is_blank":false},'
    '{"text":"cat","anatomy":["subject"],"concept_tags":[],"is_blank":false},'
    '{"text":" ","anatomy":[],"concept_tags":[],"is_blank":false},'
    '{"text":"sat","anatomy":["main_verb"],"concept_tags":["subject_verb_agreement"],"is_blank":false},'
    '{"text":".","anatomy":["punctuation_mark"],"concept_tags":[],"is_blank":false}]'
)
VALID_TOKENS = json.loads(VALID_TOKENS_JSON)


class _FakeQuestion:
    """Plain stand-in for Question — avoids SQLAlchemy mapper construction
    issues (see _FakeSR in test_spaced_repetition.py). Only plain attributes
    are accessed by annotate_spans()."""

    def __init__(self, *, passage_text=None, question_text=None, annotation_id=None):
        self.id = QUESTION_ID
        self.current_passage_text = passage_text
        self.current_question_text = question_text
        self.latest_annotation_id = annotation_id


class _FakeAnnotation:
    """Plain stand-in for QuestionAnnotation."""

    def __init__(self, annotation_jsonb=None):
        self.id = ANNOTATION_ID
        self.annotation_jsonb = annotation_jsonb or {}
        self.passage_spans = None
        self.span_annotated_at = None
        self.span_model_name = None


class _FakeDB:
    """AsyncMock-flavoured DB session that routes get() by model class and
    records add() calls so tests can assert span_review_queue entries."""

    def __init__(self, question=None, annotation=None):
        self._question = question
        self._annotation = annotation
        self.added: list = []
        self.committed = 0

    async def get(self, model, pk):
        # Route by identity to the right fake object
        if model is Question:
            return self._question
        if model is QuestionAnnotation:
            return self._annotation
        return None

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed += 1


def _provider(raw_text: str, model: str = "test-span-model"):
    """Build a MagicMock provider whose .complete is an AsyncMock returning
    a single LLMResponse. Matches the real AnthropicProvider contract."""
    provider = MagicMock()
    provider.default_model = model
    provider.complete = AsyncMock(
        return_value=LLMResponse(
            raw_text=raw_text, model=model, provider="anthropic"
        )
    )
    return provider


def _provider_sequence(raw_texts, model: str = "test-span-model"):
    """Provider whose .complete returns a sequence of LLMResponses (for retry
    path testing)."""
    provider = MagicMock()
    provider.default_model = model
    provider.complete = AsyncMock(
        side_effect=[
            LLMResponse(raw_text=rt, model=model, provider="anthropic")
            for rt in raw_texts
        ]
    )
    return provider


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------

class TestAnnotateSpansOk:
    @pytest.mark.asyncio
    async def test_writes_passage_spans_and_returns_ok(self):
        q = _FakeQuestion(
            passage_text=PASSAGE,
            question_text="ignored when passage present",
            annotation_id=ANNOTATION_ID,
        )
        ann = _FakeAnnotation(
            annotation_jsonb={"grammar_focus_key": "subject_verb_agreement"}
        )
        db = _FakeDB(question=q, annotation=ann)
        provider = _provider(VALID_TOKENS_JSON)

        result = await annotate_spans(QUESTION_ID, db, provider=provider)

        assert result["status"] == "ok"
        assert result["token_count"] == 5
        assert "label" in result
        # passage_spans written to annotation with required keys
        assert ann.passage_spans is not None
        assert ann.passage_spans["label"] == result["label"]
        assert ann.passage_spans["tokens"] == VALID_TOKENS
        assert "anatomy_present" in ann.passage_spans
        assert "concepts_present" in ann.passage_spans
        assert ann.passage_spans["passage_text_source"] == "current_passage_text"
        # metadata stamped
        assert ann.span_annotated_at is not None
        assert ann.span_model_name == "test-span-model"
        # committed exactly once on success
        assert db.committed == 1
        # nothing queued for review on success
        assert db.added == []


# ---------------------------------------------------------------------------
# 2. & 3. Missing data raises ValueError
# ---------------------------------------------------------------------------

class TestAnnotateSpansMissingData:
    @pytest.mark.asyncio
    async def test_raises_when_question_not_found(self):
        db = _FakeDB(question=None, annotation=None)
        provider = _provider(VALID_TOKENS_JSON)

        with pytest.raises(ValueError, match="not found"):
            await annotate_spans(QUESTION_ID, db, provider=provider)
        # LLM never called when question is missing
        provider.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_no_annotation(self):
        q = _FakeQuestion(
            passage_text=PASSAGE, question_text="x", annotation_id=None
        )
        db = _FakeDB(question=q, annotation=None)
        provider = _provider(VALID_TOKENS_JSON)

        with pytest.raises(ValueError, match="no annotation"):
            await annotate_spans(QUESTION_ID, db, provider=provider)
        provider.complete.assert_not_called()


# ---------------------------------------------------------------------------
# 4. Parse error on both attempts
# ---------------------------------------------------------------------------

class TestAnnotateSpansParseError:
    @pytest.mark.asyncio
    async def test_logs_failure_and_returns_failed(self):
        q = _FakeQuestion(
            passage_text=PASSAGE, question_text="x", annotation_id=ANNOTATION_ID
        )
        ann = _FakeAnnotation(
            annotation_jsonb={"grammar_focus_key": "subject_verb_agreement"}
        )
        db = _FakeDB(question=q, annotation=ann)
        # Both attempts return non-JSON
        provider = _provider_sequence(["not json at all", "still not json"])

        result = await annotate_spans(QUESTION_ID, db, provider=provider)

        assert result["status"] == "failed"
        assert result["error_type"] == "parse_error"
        # LLM called twice (retry)
        assert provider.complete.call_count == 2
        # one span_review_queue entry logged
        assert len(db.added) == 1
        entry = db.added[0]
        assert isinstance(entry, SpanReviewQueue)
        assert entry.error_type == "parse_error"
        assert entry.question_id == QUESTION_ID
        # annotation not written
        assert ann.passage_spans is None


# ---------------------------------------------------------------------------
# 5. Validation failure
# ---------------------------------------------------------------------------

class TestAnnotateSpansValidationError:
    @pytest.mark.asyncio
    async def test_concat_mismatch_logged_and_returns_failed(self):
        q = _FakeQuestion(
            passage_text=PASSAGE, question_text="x", annotation_id=ANNOTATION_ID
        )
        ann = _FakeAnnotation(
            annotation_jsonb={"grammar_focus_key": "subject_verb_agreement"}
        )
        db = _FakeDB(question=q, annotation=ann)
        # Tokens that don't reconstruct the passage → concat_mismatch
        bad_tokens = '[{"text":"wrong text"}]'
        provider = _provider(bad_tokens)

        result = await annotate_spans(QUESTION_ID, db, provider=provider)

        assert result["status"] == "failed"
        assert "concat_mismatch" in result["error_types"]
        assert provider.complete.call_count == 1
        # The validator runs all 6 checks and collects every error (not
        # short-circuited): bad tokens here trigger concat_mismatch AND
        # missing_primary_concept, so two queue entries are logged.
        assert len(db.added) == 2
        assert all(isinstance(e, SpanReviewQueue) for e in db.added)
        assert any(e.error_type == "concat_mismatch" for e in db.added)
        assert any(e.error_type == "missing_primary_concept" for e in db.added)
        assert all(e.question_id == QUESTION_ID for e in db.added)
        assert ann.passage_spans is None


# ---------------------------------------------------------------------------
# 6. Retry path — first call invalid, second call valid
# ---------------------------------------------------------------------------

class TestAnnotateSpansRetry:
    @pytest.mark.asyncio
    async def test_retries_on_parse_failure_then_succeeds(self):
        q = _FakeQuestion(
            passage_text=PASSAGE, question_text="x", annotation_id=ANNOTATION_ID
        )
        ann = _FakeAnnotation(
            annotation_jsonb={"grammar_focus_key": "subject_verb_agreement"}
        )
        db = _FakeDB(question=q, annotation=ann)
        # attempt 1: invalid JSON; attempt 2: valid tokens
        provider = _provider_sequence(["<<garbage>>", VALID_TOKENS_JSON])

        result = await annotate_spans(QUESTION_ID, db, provider=provider)

        assert result["status"] == "ok"
        assert provider.complete.call_count == 2
        assert ann.passage_spans is not None
        assert ann.passage_spans["passage_text_source"] == "current_passage_text"
        assert db.committed == 1
        assert db.added == []