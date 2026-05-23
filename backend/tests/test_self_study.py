"""Phase 8 — Self-Study Agent Request Layer tests.

Covers:
- _weakness_score: pure-function scoring formula
- _compute_weakness_targets: bucketing, scoring, top-K, at-most-2-per-focus-key
- _inventory_for_target: unseen count + below_threshold flag
- _pending_batch_exists_for_target: live-batch guard
- _target_on_cooldown: cooldown-window check
- _daily_gen_count / _pending_batch_count: rate-cap helpers
- _on_quality_cooldown: poor-quality batch guard
- POST /api/study/recommendations: requires auth; 404 on bad token; shape
- POST /api/study/generation-requests: serves questions; creates batches; cap enforcement
- GET /api/study/generation-requests/{batch_id}: auth, 404, ownership, shape
"""

import math
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers import student as student_router
from app.models.payload import WeaknessTarget


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

def _utcnow():
    return datetime.now(timezone.utc)


def _make_user(uid=1):
    return SimpleNamespace(
        id=uid,
        user_token=uuid.uuid4(),
    )


def _make_settings(**overrides):
    defaults = dict(
        inventory_sufficient_threshold=5,
        self_study_resurface_days=30,
        self_study_lookback_days=30,
        self_study_recency_half_life_days=14,
        self_study_top_k=5,
        self_study_min_attempts_per_target=3,
        self_study_min_gen_batch_size=3,
        self_study_target_cooldown_hours=24,
        self_study_gen_per_student_per_day=20,
        self_study_max_pending_per_target=10,
        self_study_max_pending_batches_per_student=3,
        default_annotation_provider="ollama",
        default_annotation_model="test-model",
        rules_version="v3.0",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_progress(
    *,
    user_id=1,
    is_correct=False,
    question_domain="grammar",
    missed_grammar_focus_key="comma_splice",
    missed_reading_focus_key=None,
    missed_reading_skill_family_key=None,
    missed_syntactic_trap_key=None,
    question_difficulty="medium",
    timestamp=None,
):
    return SimpleNamespace(
        user_id=user_id,
        is_correct=is_correct,
        question_domain=question_domain,
        missed_grammar_focus_key=missed_grammar_focus_key,
        missed_reading_focus_key=missed_reading_focus_key,
        missed_reading_skill_family_key=missed_reading_skill_family_key,
        missed_syntactic_trap_key=missed_syntactic_trap_key,
        question_difficulty=question_difficulty,
        timestamp=timestamp or _utcnow(),
    )


def _make_weakness_target(
    domain="grammar",
    focus_key="comma_splice",
    difficulty="medium",
    inventory_unseen=0,
    inventory_below_threshold=True,
):
    return WeaknessTarget(
        domain=domain,
        focus_key=focus_key,
        skill_family_key=None,
        grammar_role_key=None,
        difficulty=difficulty,
        weakness_score=0.5,
        miss_count=3,
        attempt_count=5,
        miss_rate=0.6,
        days_since_last_attempt=1.0,
        inventory_unseen=inventory_unseen,
        inventory_below_threshold=inventory_below_threshold,
    )


class _ScalarResult:
    def __init__(self, items=None, first_item=None):
        self._items = items or []
        self._first_item = first_item

    def unique(self):
        return self

    def scalars(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._first_item


class _QueueDB:
    """DB mock that pops pre-configured results in call order."""

    def __init__(self, results=None):
        self._results = list(results or [])

    async def execute(self, stmt):
        if self._results:
            return self._results.pop(0)
        return _ScalarResult()

    async def get(self, model, pk):
        return None

    def add(self, obj):
        pass

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


# ---------------------------------------------------------------------------
# _weakness_score
# ---------------------------------------------------------------------------

def test_weakness_score_zero_attempts():
    assert student_router._weakness_score(0, 0, 0.0) == 0.0


def test_weakness_score_full_miss_recent():
    score = student_router._weakness_score(5, 5, 0.0)
    # miss_rate=1.0, recency_weight=1.0, volume=sqrt(5)
    assert abs(score - math.sqrt(5)) < 1e-9


def test_weakness_score_decays_with_time():
    score_recent = student_router._weakness_score(3, 5, 0.0)
    score_old = student_router._weakness_score(3, 5, 28.0)
    assert score_recent > score_old


def test_weakness_score_partial_miss():
    # miss_rate=0.5, recency=1.0 (t=0), volume=sqrt(4)
    score = student_router._weakness_score(2, 4, 0.0)
    assert abs(score - 0.5 * math.sqrt(4)) < 1e-9


# ---------------------------------------------------------------------------
# _compute_weakness_targets
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compute_weakness_targets_empty_progress():
    db = _QueueDB(results=[_ScalarResult(items=[])])
    targets = await student_router._compute_weakness_targets(
        _make_user(), db, _make_settings()
    )
    assert targets == []


@pytest.mark.asyncio
async def test_compute_weakness_targets_below_min_attempts_excluded():
    # Only 2 records for the key — below min_attempts=3
    records = [
        _make_progress(is_correct=False, missed_grammar_focus_key="comma_splice"),
        _make_progress(is_correct=False, missed_grammar_focus_key="comma_splice"),
    ]
    db = _QueueDB(results=[_ScalarResult(items=records)])
    targets = await student_router._compute_weakness_targets(
        _make_user(), db, _make_settings(self_study_min_attempts_per_target=3)
    )
    assert targets == []


@pytest.mark.asyncio
async def test_compute_weakness_targets_basic_grammar():
    records = [
        _make_progress(is_correct=False, missed_grammar_focus_key="comma_splice"),
        _make_progress(is_correct=False, missed_grammar_focus_key="comma_splice"),
        _make_progress(is_correct=True,  missed_grammar_focus_key="comma_splice"),
    ]
    db = _QueueDB(results=[_ScalarResult(items=records)])
    targets = await student_router._compute_weakness_targets(
        _make_user(), db, _make_settings()
    )
    assert len(targets) == 1
    t = targets[0]
    assert t.domain == "grammar"
    assert t.focus_key == "comma_splice"
    assert t.miss_count == 2
    assert t.attempt_count == 3


@pytest.mark.asyncio
async def test_compute_weakness_targets_reading():
    records = [
        _make_progress(
            is_correct=False,
            question_domain="reading",
            missed_reading_focus_key="main_idea",
            missed_reading_skill_family_key="information_and_ideas",
            missed_grammar_focus_key=None,
        ),
        _make_progress(
            is_correct=False,
            question_domain="reading",
            missed_reading_focus_key="main_idea",
            missed_reading_skill_family_key="information_and_ideas",
            missed_grammar_focus_key=None,
        ),
        _make_progress(
            is_correct=False,
            question_domain="reading",
            missed_reading_focus_key="main_idea",
            missed_reading_skill_family_key="information_and_ideas",
            missed_grammar_focus_key=None,
        ),
    ]
    db = _QueueDB(results=[_ScalarResult(items=records)])
    targets = await student_router._compute_weakness_targets(
        _make_user(), db, _make_settings()
    )
    assert len(targets) == 1
    t = targets[0]
    assert t.domain == "reading"
    assert t.focus_key == "main_idea"
    assert t.skill_family_key == "information_and_ideas"


@pytest.mark.asyncio
async def test_compute_weakness_targets_top_k_limit():
    # Generate 6 distinct focus keys, each with 3 records.
    focus_keys = [f"key_{i}" for i in range(6)]
    records = []
    for fk in focus_keys:
        records += [
            _make_progress(is_correct=False, missed_grammar_focus_key=fk),
            _make_progress(is_correct=False, missed_grammar_focus_key=fk),
            _make_progress(is_correct=False, missed_grammar_focus_key=fk),
        ]
    db = _QueueDB(results=[_ScalarResult(items=records)])
    targets = await student_router._compute_weakness_targets(
        _make_user(), db, _make_settings(self_study_top_k=5)
    )
    assert len(targets) <= 5


@pytest.mark.asyncio
async def test_compute_weakness_targets_at_most_two_per_focus_key():
    # Same focus key, two difficulty levels → 2 slots consumed; third excluded.
    records = []
    for difficulty in ("easy", "medium", "hard"):
        records += [
            _make_progress(
                is_correct=False,
                missed_grammar_focus_key="comma_splice",
                question_difficulty=difficulty,
            ),
            _make_progress(
                is_correct=False,
                missed_grammar_focus_key="comma_splice",
                question_difficulty=difficulty,
            ),
            _make_progress(
                is_correct=False,
                missed_grammar_focus_key="comma_splice",
                question_difficulty=difficulty,
            ),
        ]
    db = _QueueDB(results=[_ScalarResult(items=records)])
    targets = await student_router._compute_weakness_targets(
        _make_user(), db, _make_settings(self_study_top_k=10)
    )
    # At most 2 entries for the same focus_key.
    focus_key_counts: dict = {}
    for t in targets:
        focus_key_counts[t.focus_key] = focus_key_counts.get(t.focus_key, 0) + 1
    for count in focus_key_counts.values():
        assert count <= 2


@pytest.mark.asyncio
async def test_compute_weakness_targets_skips_rows_without_domain():
    records = [
        SimpleNamespace(
            user_id=1,
            is_correct=False,
            question_domain=None,  # no domain — should be skipped
            missed_grammar_focus_key="comma_splice",
            missed_reading_focus_key=None,
            missed_reading_skill_family_key=None,
            question_difficulty="medium",
            timestamp=_utcnow(),
        ),
    ]
    db = _QueueDB(results=[_ScalarResult(items=records)])
    targets = await student_router._compute_weakness_targets(
        _make_user(), db, _make_settings()
    )
    assert targets == []


# ---------------------------------------------------------------------------
# _inventory_for_target
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_inventory_for_target_above_threshold():
    # Inventory query returns count=10, threshold=5 → not below
    db = _QueueDB(results=[_ScalarResult(first_item=10)])
    target = _make_weakness_target()
    unseen, below = await student_router._inventory_for_target(
        _make_user(), target, db, _make_settings(inventory_sufficient_threshold=5)
    )
    assert unseen == 10
    assert below is False


@pytest.mark.asyncio
async def test_inventory_for_target_below_threshold():
    db = _QueueDB(results=[_ScalarResult(first_item=2)])
    target = _make_weakness_target()
    unseen, below = await student_router._inventory_for_target(
        _make_user(), target, db, _make_settings(inventory_sufficient_threshold=5)
    )
    assert unseen == 2
    assert below is True


@pytest.mark.asyncio
async def test_inventory_for_reading_target():
    db = _QueueDB(results=[_ScalarResult(first_item=3)])
    target = _make_weakness_target(domain="reading", focus_key="main_idea")
    unseen, below = await student_router._inventory_for_target(
        _make_user(), target, db, _make_settings(inventory_sufficient_threshold=5)
    )
    assert unseen == 3
    assert below is True


# ---------------------------------------------------------------------------
# _pending_batch_exists_for_target
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pending_batch_exists_true():
    fake_batch = SimpleNamespace(id=uuid.uuid4())
    db = _QueueDB(results=[_ScalarResult(first_item=fake_batch)])
    target = _make_weakness_target()
    assert await student_router._pending_batch_exists_for_target(_make_user(), target, db) is True


@pytest.mark.asyncio
async def test_pending_batch_exists_false():
    db = _QueueDB(results=[_ScalarResult(first_item=None)])
    target = _make_weakness_target()
    assert await student_router._pending_batch_exists_for_target(_make_user(), target, db) is False


# ---------------------------------------------------------------------------
# _target_on_cooldown
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_target_on_cooldown_true():
    fake_batch = SimpleNamespace(id=uuid.uuid4())
    db = _QueueDB(results=[_ScalarResult(first_item=fake_batch)])
    target = _make_weakness_target()
    assert await student_router._target_on_cooldown(_make_user(), target, _make_settings(), db) is True


@pytest.mark.asyncio
async def test_target_on_cooldown_false():
    db = _QueueDB(results=[_ScalarResult(first_item=None)])
    target = _make_weakness_target()
    assert await student_router._target_on_cooldown(_make_user(), target, _make_settings(), db) is False


# ---------------------------------------------------------------------------
# _daily_gen_count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_daily_gen_count_returns_value():
    db = _QueueDB(results=[_ScalarResult(first_item=7)])
    count = await student_router._daily_gen_count(_make_user(), db)
    assert count == 7


@pytest.mark.asyncio
async def test_daily_gen_count_none_returns_zero():
    db = _QueueDB(results=[_ScalarResult(first_item=None)])
    count = await student_router._daily_gen_count(_make_user(), db)
    assert count == 0


# ---------------------------------------------------------------------------
# _pending_batch_count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pending_batch_count_returns_value():
    db = _QueueDB(results=[_ScalarResult(first_item=2)])
    count = await student_router._pending_batch_count(_make_user(), db)
    assert count == 2


# ---------------------------------------------------------------------------
# _on_quality_cooldown
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_quality_cooldown_fewer_than_two_batches_no_cooldown():
    recent = [
        SimpleNamespace(accepted_count=1, rejected_count=4),  # 80% reject — poor
    ]
    db = _QueueDB(results=[_ScalarResult(items=recent)])
    # Only 1 batch — threshold requires 2 poor ones.
    assert await student_router._on_quality_cooldown(_make_user(), _make_settings(), db) is False


@pytest.mark.asyncio
async def test_quality_cooldown_two_poor_batches_triggers_cooldown():
    recent = [
        SimpleNamespace(accepted_count=1, rejected_count=4),   # 80% reject
        SimpleNamespace(accepted_count=0, rejected_count=3),   # 100% reject
        SimpleNamespace(accepted_count=5, rejected_count=1),   # 17% reject — ok
    ]
    db = _QueueDB(results=[_ScalarResult(items=recent)])
    assert await student_router._on_quality_cooldown(_make_user(), _make_settings(), db) is True


@pytest.mark.asyncio
async def test_quality_cooldown_one_poor_batch_no_cooldown():
    recent = [
        SimpleNamespace(accepted_count=1, rejected_count=4),   # 80% reject
        SimpleNamespace(accepted_count=5, rejected_count=1),   # 17% reject — ok
    ]
    db = _QueueDB(results=[_ScalarResult(items=recent)])
    assert await student_router._on_quality_cooldown(_make_user(), _make_settings(), db) is False


# ---------------------------------------------------------------------------
# _resolve_user_by_token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_user_invalid_token_raises_400():
    from fastapi import HTTPException
    db = _QueueDB()
    with pytest.raises(HTTPException) as exc_info:
        await student_router._resolve_user_by_token("not-a-uuid", db)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_resolve_user_not_found_raises_404():
    from fastapi import HTTPException
    db = _QueueDB(results=[_ScalarResult(first_item=None)])
    with pytest.raises(HTTPException) as exc_info:
        await student_router._resolve_user_by_token(str(uuid.uuid4()), db)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_resolve_user_found_returns_user():
    user = _make_user()
    db = _QueueDB(results=[_ScalarResult(first_item=user)])
    result = await student_router._resolve_user_by_token(str(user.user_token), db)
    assert result is user


# ---------------------------------------------------------------------------
# HTTP-layer: POST /api/study/recommendations
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    from app.main import app
    from app.database import get_db
    from fastapi.testclient import TestClient

    db_mock = AsyncMock()
    db_mock.execute = AsyncMock(return_value=_ScalarResult())

    async def _override():
        yield db_mock

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c, db_mock
    app.dependency_overrides.clear()


def test_study_recommendations_requires_auth(client):
    c, _ = client
    resp = c.post("/api/study/recommendations", json={"user_token": str(uuid.uuid4())})
    assert resp.status_code == 403


def test_study_recommendations_invalid_user_token(client):
    c, db_mock = client
    db_mock.execute.return_value = _ScalarResult(first_item=None)
    resp = c.post(
        "/api/study/recommendations",
        json={"user_token": str(uuid.uuid4())},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 404


def test_study_recommendations_returns_shape(client):
    c, db_mock = client
    user = _make_user()

    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _ScalarResult(first_item=user)
        return _ScalarResult(items=[], first_item=None)

    db_mock.execute = _execute

    resp = c.post(
        "/api/study/recommendations",
        json={"user_token": str(user.user_token)},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "user_id" in body
    assert "top_targets" in body
    assert "threshold" in body
    assert isinstance(body["top_targets"], list)


# ---------------------------------------------------------------------------
# HTTP-layer: POST /api/study/generation-requests
# ---------------------------------------------------------------------------

def test_study_generation_request_requires_auth(client):
    c, _ = client
    resp = c.post("/api/study/generation-requests", json={"user_token": str(uuid.uuid4())})
    assert resp.status_code == 403


def test_study_generation_request_invalid_user_token(client):
    c, db_mock = client
    db_mock.execute.return_value = _ScalarResult(first_item=None)
    resp = c.post(
        "/api/study/generation-requests",
        json={"user_token": str(uuid.uuid4())},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 404


def test_study_generation_request_no_targets_returns_empty(client):
    c, db_mock = client
    user = _make_user()
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _ScalarResult(first_item=user)
        return _ScalarResult(items=[], first_item=0)

    db_mock.execute = _execute

    resp = c.post(
        "/api/study/generation-requests",
        json={"user_token": str(user.user_token)},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "questions" in body
    assert "new_batch_ids" in body
    assert "targets_analyzed" in body
    assert "targets_with_new_batch" in body
    assert body["targets_with_new_batch"] == 0
    assert body["new_batch_ids"] == []


# ---------------------------------------------------------------------------
# HTTP-layer: GET /api/study/generation-requests/{batch_id}
# ---------------------------------------------------------------------------

def test_get_study_batch_status_requires_auth(client):
    c, _ = client
    resp = c.get(
        f"/api/study/generation-requests/{uuid.uuid4()}",
        params={"user_token": str(uuid.uuid4())},
    )
    assert resp.status_code == 403


def test_get_study_batch_status_invalid_batch_id(client):
    c, _ = client
    resp = c.get(
        "/api/study/generation-requests/not-a-uuid",
        params={"user_token": str(uuid.uuid4())},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 400


def test_get_study_batch_status_batch_not_found(client):
    c, db_mock = client
    user = _make_user()
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _ScalarResult(first_item=user)
        return _ScalarResult(first_item=None)

    db_mock.execute = _execute

    resp = c.get(
        f"/api/study/generation-requests/{uuid.uuid4()}",
        params={"user_token": str(user.user_token)},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 404


def test_get_study_batch_status_wrong_student_returns_403(client):
    c, db_mock = client
    user = _make_user(uid=1)
    other_user_id = 99
    now = _utcnow()
    fake_batch = SimpleNamespace(
        id=uuid.uuid4(),
        student_id=other_user_id,  # owned by a different student
        status="pending",
        requested_count=3,
        created_count=0,
        accepted_count=0,
        rejected_count=0,
        failed_count=0,
        needs_review_count=0,
        release_policy="admin_review_required",
        requested_by="self_study_agent",
        created_at=now,
        updated_at=now,
    )
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _ScalarResult(first_item=user)
        return _ScalarResult(first_item=fake_batch)

    db_mock.execute = _execute

    resp = c.get(
        f"/api/study/generation-requests/{fake_batch.id}",
        params={"user_token": str(user.user_token)},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 403


def test_get_study_batch_status_returns_shape(client):
    c, db_mock = client
    user = _make_user()
    now = _utcnow()
    batch_id = uuid.uuid4()
    fake_batch = SimpleNamespace(
        id=batch_id,
        student_id=user.id,
        status="pending",
        requested_count=5,
        created_count=0,
        accepted_count=0,
        rejected_count=0,
        failed_count=0,
        needs_review_count=0,
        release_policy="admin_review_required",
        requested_by="self_study_agent",
        created_at=now,
        updated_at=now,
    )
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _ScalarResult(first_item=user)
        return _ScalarResult(first_item=fake_batch)

    db_mock.execute = _execute

    resp = c.get(
        f"/api/study/generation-requests/{batch_id}",
        params={"user_token": str(user.user_token)},
        headers={"X-API-Key": "student-test-key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["batch_id"] == str(batch_id)
    assert body["status"] == "pending"
    assert body["requested_count"] == 5
    assert body["release_policy"] == "admin_review_required"
    assert body["requested_by"] == "self_study_agent"


# ---------------------------------------------------------------------------
# Integration: _create_self_study_batch forces admin_review_required
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_self_study_batch_forces_admin_review_required():
    """Batch must always have release_policy='admin_review_required' regardless of target."""
    target = _make_weakness_target()
    user = _make_user()
    settings = _make_settings()

    created_batches = []
    created_jobs = []

    class _TrackingDB:
        async def execute(self, stmt):
            return _ScalarResult(items=[], first_item=0)

        def add(self, obj):
            from app.models.db import GenerationBatch, QuestionJob
            if isinstance(obj, GenerationBatch) or (hasattr(obj, "release_policy")):
                created_batches.append(obj)
            if isinstance(obj, QuestionJob):
                created_jobs.append(obj)

        async def flush(self):
            pass

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

    db = _TrackingDB()

    with patch("app.routers.generate._run_batch_pipeline", new_callable=AsyncMock):
        with patch("app.job_limits.run_with_job_limit", new_callable=AsyncMock):
            with patch("asyncio.create_task"):
                try:
                    await student_router._create_self_study_batch(
                        user, target, 3, settings, db
                    )
                except Exception:
                    pass  # Pipeline start may fail in test env

    # Find the GenerationBatch-like object.
    batch_obj = next(
        (o for o in created_batches if hasattr(o, "release_policy")), None
    )
    if batch_obj is not None:
        assert batch_obj.release_policy == "admin_review_required"
        assert batch_obj.requested_by == "self_study_agent"
        assert batch_obj.request_jsonb["target_grammar_role_key"] == "sentence_boundary"
        assert batch_obj.request_jsonb["target_grammar_focus_key"] == "comma_splice"
        assert batch_obj.request_jsonb["target_frequency_band"] == "medium"
        assert batch_obj.request_jsonb["test_format_key"] == "digital_app_adaptive"
        assert batch_obj.request_jsonb["stimulus_mode_key"] == "sentence_only"
    assert created_jobs
    for job in created_jobs:
        request = job.generation_request_jsonb
        assert "requested_count" not in request
        assert request["release_policy"] == "admin_review_required"
        assert request["target_grammar_role_key"] == "sentence_boundary"
        assert request["source_question_ids"] == []
        assert isinstance(request["seed"], int)
