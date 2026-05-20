"""Phase 2 (generation factory) — runner, failure classification, batch
counter updates, finalize-status logic, and retry endpoint tests.

All tests use mocked sessions or minimal HTTP overrides; no live DB required.
"""

import asyncio
import uuid as _uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


AUTH = {"X-API-Key": "admin-test-key"}

# ---------------------------------------------------------------------------
# Helper unit tests — no DB needed
# ---------------------------------------------------------------------------

def test_is_transient_error_false_for_none():
    from app.routers.generate import _is_transient_error
    assert _is_transient_error(None) is False


def test_is_transient_error_false_for_value_error():
    from app.routers.generate import _is_transient_error
    assert _is_transient_error(ValueError("bad json")) is False


def test_is_transient_error_true_for_runtime_error():
    from app.routers.generate import _is_transient_error
    assert _is_transient_error(RuntimeError("network timeout")) is True


def test_is_transient_error_false_for_generic_runtime_error():
    from app.routers.generate import _is_transient_error
    assert _is_transient_error(RuntimeError("bad generated shape")) is False


def test_is_transient_error_true_for_connection_error():
    from app.routers.generate import _is_transient_error
    assert _is_transient_error(ConnectionError("refused")) is True


def test_is_transient_error_uses_retryable_status_code():
    from app.llm.errors import LLMAPIError
    from app.routers.generate import _is_transient_error

    assert _is_transient_error(
        LLMAPIError("rate limited", provider="openai", model="m", status_code=429)
    ) is True
    assert _is_transient_error(
        LLMAPIError("bad request", provider="openai", model="m", status_code=400)
    ) is False


def test_batch_counter_field_approved():
    from app.routers.generate import _batch_counter_field
    assert _batch_counter_field("approved") == "accepted_count"


def test_batch_counter_field_needs_review():
    from app.routers.generate import _batch_counter_field
    assert _batch_counter_field("needs_review") == "needs_review_count"


def test_batch_counter_field_failed_permanent():
    from app.routers.generate import _batch_counter_field
    assert _batch_counter_field("failed_permanent") == "failed_count"


def test_batch_counter_field_failed_transient():
    from app.routers.generate import _batch_counter_field
    assert _batch_counter_field("failed_transient") == "failed_count"


def test_batch_counter_field_unknown_status():
    from app.routers.generate import _batch_counter_field
    assert _batch_counter_field("pending") is None
    assert _batch_counter_field("retrying") is None


# ---------------------------------------------------------------------------
# _run_generate_pipeline — failure status classification
# ---------------------------------------------------------------------------

def _make_job(**kwargs):
    """Return a minimal QuestionJob-like object for pipeline tests."""
    defaults = dict(
        id=_uuid.uuid4(),
        provider_name="ollama",
        model_name="test-model",
        prompt_version="v3.0",
        rules_version="v7",
        status="pending",
        pass1_json=None,
        pass2_json=None,
        validation_errors_jsonb=None,
        question_id=None,
        generation_batch_id=None,
        retry_count=0,
        last_retry_at=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class _FakePipelineSession(AsyncMock):
    """Minimal async session that just records status changes."""

    def __init__(self):
        super().__init__()
        self.committed = []

    async def commit(self):
        pass

    async def get(self, model, pk):
        return None

    async def execute(self, stmt):
        return MagicMock(unique=MagicMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))))

    def add(self, obj):
        pass

    def begin_nested(self):
        return _FakeSavepoint()


class _FakeSavepoint:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def commit(self):
        pass


def _mock_provider(*, raise_exc):
    provider = AsyncMock()
    if isinstance(raise_exc, Exception):
        provider.complete.side_effect = raise_exc
    return provider


@pytest.mark.asyncio
async def test_pipeline_returns_failed_permanent_for_json_parse_failure():
    from app.routers.generate import _run_generate_pipeline

    job = _make_job()
    db = _FakePipelineSession()

    with patch("app.llm.factory.get_provider") as mock_get:
        provider = AsyncMock()
        provider.complete.side_effect = ValueError("invalid json")
        mock_get.return_value = provider

        result = await _run_generate_pipeline(
            job, db, {"source_question_ids": [], "provider_name": "ollama", "model_name": "x"}
        )

    assert result == "failed_permanent"
    assert job.status == "failed_permanent"


@pytest.mark.asyncio
async def test_pipeline_returns_failed_transient_for_network_error():
    from app.routers.generate import _run_generate_pipeline

    job = _make_job()
    db = _FakePipelineSession()

    with patch("app.llm.factory.get_provider") as mock_get:
        provider = AsyncMock()
        provider.complete.side_effect = ConnectionError("network down")
        mock_get.return_value = provider

        result = await _run_generate_pipeline(
            job, db, {"source_question_ids": [], "provider_name": "ollama", "model_name": "x"}
        )

    assert result == "failed_transient"
    assert job.status == "failed_transient"


@pytest.mark.asyncio
async def test_pipeline_returns_failed_permanent_for_blocking_validation(monkeypatch):
    from app.routers import generate as generate_router

    job = _make_job()
    db = _FakePipelineSession()
    generated = {
        "question_text": "Broken generated question",
        "correct_option_label": "A",
        "options": [{"label": "A", "text": "Only option"}],
    }
    annotated = {
        "explanation_short": "Bad",
        "explanation_full": "Bad",
        "annotation_confidence": 0.5,
        "needs_human_review": True,
    }
    responses = iter([generated, annotated])
    provider = AsyncMock()
    provider.complete.side_effect = [
        SimpleNamespace(raw_text="generate", provider="ollama", model="m", latency_ms=1),
        SimpleNamespace(raw_text="annotate", provider="ollama", model="m", latency_ms=1),
    ]

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.generate_prompt.build_generate_prompt", lambda *_args, **_kwargs: ("system", "user"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_args, **_kwargs: ("system", "user"))
    monkeypatch.setattr(generate_router, "extract_json_from_text", lambda *_args, **_kwargs: next(responses))
    monkeypatch.setattr(
        generate_router,
        "validate_question",
        lambda *_args, **_kwargs: [
            {"severity": "blocking", "field": "options", "message": "Need four options"}
        ],
    )

    result = await generate_router._run_generate_pipeline(
        job, db, {"source_question_ids": [], "provider_name": "ollama", "model_name": "x"}
    )

    assert result == "failed_permanent"
    assert job.status == "failed_permanent"
    assert job.question_id is None
    assert job.validation_errors_jsonb[0]["field"] == "options"


@pytest.mark.asyncio
async def test_pipeline_settles_setup_exception(monkeypatch):
    from app.routers import generate as generate_router

    job = _make_job()
    db = _FakePipelineSession()

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: AsyncMock())
    monkeypatch.setattr(
        generate_router,
        "_load_official_source_examples",
        AsyncMock(side_effect=ConnectionError("network down")),
    )

    result = await generate_router._run_generate_pipeline(
        job, db, {"source_question_ids": ["not-loaded"], "provider_name": "ollama"}
    )

    assert result == "failed_transient"
    assert job.status == "failed_transient"
    assert job.validation_errors_jsonb[0]["step"] == "generating_setup"


@pytest.mark.asyncio
async def test_pipeline_settles_overlap_exception(monkeypatch):
    from app.routers import generate as generate_router

    job = _make_job()
    db = _FakePipelineSession()
    generated = {
        "question_text": "Generated question",
        "correct_option_label": "A",
        "options": [
            {"label": "A", "text": "Correct"},
            {"label": "B", "text": "Wrong"},
        ],
    }
    annotated = {
        "explanation_short": "Ok",
        "explanation_full": "Ok",
        "annotation_confidence": 0.9,
        "needs_human_review": False,
    }
    responses = iter([generated, annotated])
    provider = AsyncMock()
    provider.complete.side_effect = [
        SimpleNamespace(raw_text="generate", provider="ollama", model="m", latency_ms=1),
        SimpleNamespace(raw_text="annotate", provider="ollama", model="m", latency_ms=1),
    ]

    monkeypatch.setattr("app.llm.factory.get_provider", lambda *args, **kwargs: provider)
    monkeypatch.setattr("app.prompts.generate_prompt.build_generate_prompt", lambda *_args, **_kwargs: ("system", "user"))
    monkeypatch.setattr("app.prompts.annotate_prompt.build_annotate_prompt", lambda *_args, **_kwargs: ("system", "user"))
    monkeypatch.setattr(generate_router, "extract_json_from_text", lambda *_args, **_kwargs: next(responses))
    monkeypatch.setattr(generate_router, "validate_question", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(generate_router, "detect_overlaps", AsyncMock(side_effect=ConnectionError("network down")))

    result = await generate_router._run_generate_pipeline(
        job, db, {"source_question_ids": [], "provider_name": "ollama", "model_name": "x"}
    )

    assert result == "failed_permanent"
    assert job.status == "failed_permanent"
    assert job.question_id is not None
    assert job.validation_errors_jsonb[0]["step"] == "overlap_checking"


# ---------------------------------------------------------------------------
# _finalize_batch_status
# ---------------------------------------------------------------------------

def _fake_batch(*, requested=3, accepted=0, needs_review=0, failed=0, status="generating"):
    b = SimpleNamespace(
        id=_uuid.uuid4(),
        requested_count=requested,
        accepted_count=accepted,
        needs_review_count=needs_review,
        failed_count=failed,
        status=status,
        updated_at=datetime.now(timezone.utc),
    )
    return b


class _BatchSession(AsyncMock):
    def __init__(self, batch):
        super().__init__()
        self._batch = batch

    async def get(self, model, pk):
        return self._batch

    async def commit(self):
        pass


@pytest.mark.asyncio
async def test_finalize_sets_completed_when_all_approved():
    from app.routers.generate import _finalize_batch_status

    batch = _fake_batch(requested=3, accepted=3)
    await _finalize_batch_status(batch.id, _BatchSession(batch))
    assert batch.status == "completed"


@pytest.mark.asyncio
async def test_finalize_sets_failed_when_all_failed():
    from app.routers.generate import _finalize_batch_status

    batch = _fake_batch(requested=3, failed=3)
    await _finalize_batch_status(batch.id, _BatchSession(batch))
    assert batch.status == "failed"


@pytest.mark.asyncio
async def test_finalize_sets_completed_for_partial_success():
    from app.routers.generate import _finalize_batch_status

    batch = _fake_batch(requested=3, accepted=2, failed=1)
    await _finalize_batch_status(batch.id, _BatchSession(batch))
    assert batch.status == "completed"


@pytest.mark.asyncio
async def test_finalize_noop_when_jobs_still_pending():
    from app.routers.generate import _finalize_batch_status

    batch = _fake_batch(requested=3, accepted=1)  # only 1 of 3 done
    await _finalize_batch_status(batch.id, _BatchSession(batch))
    assert batch.status == "generating"  # unchanged


@pytest.mark.asyncio
async def test_finalize_noop_for_missing_batch():
    from app.routers.generate import _finalize_batch_status

    class NoBatch(AsyncMock):
        async def get(self, model, pk):
            return None
        async def commit(self):
            pass

    await _finalize_batch_status(_uuid.uuid4(), NoBatch())  # should not raise


class _AsyncSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_run_batch_job_settles_unexpected_pipeline_exception(monkeypatch):
    from app.routers import generate as generate_router

    bid = _uuid.uuid4()
    job = _fake_job(status="pending", retry_count=0, batch_id=bid)

    class JobSession(_FakeRetrySession):
        async def get(self, model, pk):
            if model.__name__ == "QuestionJob" and pk == job.id:
                return job
            return await super().get(model, pk)

    sess = JobSession(jobs=[job])
    counter = AsyncMock()
    monkeypatch.setattr(generate_router, "async_session", lambda: _AsyncSessionContext(sess))
    monkeypatch.setattr(generate_router, "_run_generate_pipeline", AsyncMock(side_effect=ConnectionError("network down")))
    monkeypatch.setattr(generate_router, "_update_batch_counters", counter)

    await generate_router._run_batch_job(job.id, bid, {"source_question_ids": []})

    assert job.status == "failed_transient"
    assert job.validation_errors_jsonb[0]["step"] == "running_batch_job"
    counter.assert_awaited_once_with(bid, "failed_transient", sess)


@pytest.mark.asyncio
async def test_run_retry_batch_job_finalizes_after_retry(monkeypatch):
    from app.routers import generate as generate_router

    bid = _uuid.uuid4()
    jid = _uuid.uuid4()
    sess = _FakeRetrySession(batch=_fake_batch(requested=1, accepted=1))
    run_batch_job = AsyncMock()
    finalize = AsyncMock()
    monkeypatch.setattr(generate_router, "_run_batch_job", run_batch_job)
    monkeypatch.setattr(generate_router, "_finalize_batch_status", finalize)
    monkeypatch.setattr(generate_router, "async_session", lambda: _AsyncSessionContext(sess))

    await generate_router._run_retry_batch_job(jid, bid, {"source_question_ids": []})

    run_batch_job.assert_awaited_once_with(jid, bid, {"source_question_ids": []}, is_retry=True)
    finalize.assert_awaited_once_with(bid, sess)


# ---------------------------------------------------------------------------
# POST /batches/{batch_id}/retry-failed — HTTP endpoint tests
# ---------------------------------------------------------------------------

class _FakeRetrySession:
    """In-memory session for retry-failed endpoint tests."""

    def __init__(self, *, batch=None, jobs=None):
        self._batch = batch
        self._jobs = list(jobs or [])
        self.committed = False

    def add(self, obj):
        pass

    async def flush(self):
        pass

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass

    async def get(self, model, pk):
        name = model.__name__
        if name == "GenerationBatch" and self._batch is not None:
            if self._batch.id == pk:
                return self._batch
        return None

    async def execute(self, stmt):
        text = str(stmt).lower()
        if "from question_jobs" in text:
            return _Result(self._jobs)
        return _Result([])


class _Result:
    def __init__(self, rows):
        self._rows = list(rows)

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


def _make_client_with_session(session):
    from app.main import app
    from app.database import get_db

    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


def _release():
    from app.main import app
    from app.database import get_db
    app.dependency_overrides.pop(get_db, None)


def _fake_job(*, status="failed_transient", retry_count=0, batch_id=None, question_id=None):
    return SimpleNamespace(
        id=_uuid.uuid4(),
        status=status,
        retry_count=retry_count,
        generation_batch_id=batch_id,
        question_id=question_id,
        generation_request_jsonb={"provider_name": "ollama"},
        last_retry_at=None,
    )


def _capturing_create_task(launched):
    def _fake_create_task(coro, **kwargs):
        launched.append(coro)
        coro.close()
        t = MagicMock()
        t.add_done_callback = MagicMock(return_value=None)
        return t
    return _fake_create_task


def test_retry_failed_404_for_unknown_batch():
    sess = _FakeRetrySession()
    client = _make_client_with_session(sess)
    try:
        resp = client.post(f"/generate/batches/{_uuid.uuid4()}/retry-failed", headers=AUTH)
        assert resp.status_code == 404
    finally:
        _release()


def test_retry_failed_returns_zero_when_no_failed_transient_jobs():
    bid = _uuid.uuid4()
    batch = _fake_batch(requested=2, failed=0, status="completed")
    batch.id = bid
    sess = _FakeRetrySession(batch=batch, jobs=[])
    client = _make_client_with_session(sess)
    try:
        resp = client.post(f"/generate/batches/{bid}/retry-failed", headers=AUTH)
        assert resp.status_code == 200
        assert resp.json()["retried_count"] == 0
    finally:
        _release()


def test_retry_failed_queues_two_retriable_jobs(monkeypatch):
    bid = _uuid.uuid4()
    batch = _fake_batch(requested=3, failed=2, status="generating")
    batch.id = bid
    jobs = [
        _fake_job(status="failed_transient", retry_count=0, batch_id=bid),
        _fake_job(status="failed_transient", retry_count=0, batch_id=bid),
    ]
    sess = _FakeRetrySession(batch=batch, jobs=jobs)

    launched = []
    import asyncio as _asyncio
    monkeypatch.setattr(_asyncio, "create_task", _capturing_create_task(launched))

    client = _make_client_with_session(sess)
    try:
        resp = client.post(f"/generate/batches/{bid}/retry-failed", headers=AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert data["retried_count"] == 2
        assert len(launched) == 2
    finally:
        _release()


def test_retry_failed_skips_jobs_at_max_retries(monkeypatch):
    bid = _uuid.uuid4()
    batch = _fake_batch(requested=2, failed=2, status="generating")
    batch.id = bid
    max_retries = 3
    jobs = [
        _fake_job(status="failed_transient", retry_count=max_retries, batch_id=bid),
        _fake_job(status="failed_transient", retry_count=max_retries - 1, batch_id=bid),
    ]
    sess = _FakeRetrySession(batch=batch, jobs=jobs)

    launched = []
    import asyncio as _asyncio
    monkeypatch.setattr(_asyncio, "create_task", _capturing_create_task(launched))

    client = _make_client_with_session(sess)
    try:
        resp = client.post(f"/generate/batches/{bid}/retry-failed", headers=AUTH)
        assert resp.status_code == 200
        data = resp.json()
        # Only the job at retry_count = max_retries-1 is eligible
        assert data["retried_count"] == 1
        assert len(launched) == 1
    finally:
        _release()


def test_retry_failed_decrements_failed_count(monkeypatch):
    bid = _uuid.uuid4()
    batch = _fake_batch(requested=2, failed=2, status="generating")
    batch.id = bid
    jobs = [
        _fake_job(status="failed_transient", retry_count=0, batch_id=bid),
        _fake_job(status="failed_transient", retry_count=0, batch_id=bid),
    ]
    sess = _FakeRetrySession(batch=batch, jobs=jobs)

    launched = []
    import asyncio as _asyncio
    monkeypatch.setattr(_asyncio, "create_task", _capturing_create_task(launched))

    client = _make_client_with_session(sess)
    try:
        client.post(f"/generate/batches/{bid}/retry-failed", headers=AUTH)
        assert batch.failed_count == 0  # decremented by 2
    finally:
        _release()


def test_retry_failed_marks_jobs_at_retry_cap_permanent(monkeypatch):
    bid = _uuid.uuid4()
    batch = _fake_batch(requested=1, failed=1, status="failed")
    batch.id = bid
    job = _fake_job(status="failed_transient", retry_count=3, batch_id=bid)
    sess = _FakeRetrySession(batch=batch, jobs=[job])

    client = _make_client_with_session(sess)
    try:
        resp = client.post(f"/generate/batches/{bid}/retry-failed", headers=AUTH)
        assert resp.status_code == 200
        assert resp.json()["retried_count"] == 0
        assert job.status == "failed_permanent"
    finally:
        _release()


def test_retry_failed_does_not_requeue_saved_question_job(monkeypatch):
    bid = _uuid.uuid4()
    batch = _fake_batch(requested=1, failed=1, status="failed")
    batch.id = bid
    job = _fake_job(
        status="failed_transient",
        retry_count=0,
        batch_id=bid,
        question_id=_uuid.uuid4(),
    )
    sess = _FakeRetrySession(batch=batch, jobs=[job])

    launched = []
    import asyncio as _asyncio
    monkeypatch.setattr(_asyncio, "create_task", _capturing_create_task(launched))

    client = _make_client_with_session(sess)
    try:
        resp = client.post(f"/generate/batches/{bid}/retry-failed", headers=AUTH)
        assert resp.status_code == 200
        assert resp.json()["retried_count"] == 0
        assert launched == []
        assert job.status == "failed_permanent"
    finally:
        _release()
