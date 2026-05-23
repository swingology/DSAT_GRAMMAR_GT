"""Phase 10: Controlled auto-release tests."""
import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

AUTH = {"X-API-Key": "admin-test-key"}


class _Result:
    def __init__(self, items=None, first_item=None):
        self._items = list(items or [])
        self._first_item = first_item

    def scalars(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._first_item


# ---------------------------------------------------------------------------
# Unit tests for _allowed_targets_list
# ---------------------------------------------------------------------------

def test_allowed_targets_empty_string():
    from app.review.auto_release import _allowed_targets_list
    settings = MagicMock()
    settings.generation_auto_release_allowed_targets = ""
    assert _allowed_targets_list(settings) == []


def test_allowed_targets_none_value():
    from app.review.auto_release import _allowed_targets_list
    settings = MagicMock()
    settings.generation_auto_release_allowed_targets = None
    assert _allowed_targets_list(settings) == []


def test_allowed_targets_valid_json():
    from app.review.auto_release import _allowed_targets_list
    targets = [{"domain": "grammar", "grammar_focus_key": "comma_splice"}]
    settings = MagicMock()
    settings.generation_auto_release_allowed_targets = json.dumps(targets)
    assert _allowed_targets_list(settings) == targets


def test_allowed_targets_invalid_json():
    from app.review.auto_release import _allowed_targets_list
    settings = MagicMock()
    settings.generation_auto_release_allowed_targets = "not json"
    assert _allowed_targets_list(settings) == []


# ---------------------------------------------------------------------------
# Unit tests for _target_matches
# ---------------------------------------------------------------------------

def test_target_matches_exact():
    from app.review.auto_release import _target_matches
    ann = {"domain": "grammar", "grammar_focus_key": "comma_splice", "difficulty_overall": "medium"}
    allowed = {"domain": "grammar", "grammar_focus_key": "comma_splice"}
    assert _target_matches(ann, allowed) is True


def test_target_matches_wildcard_key():
    from app.review.auto_release import _target_matches
    ann = {"domain": "grammar", "grammar_focus_key": "any_key"}
    # allowed only restricts domain
    assert _target_matches(ann, {"domain": "grammar"}) is True


def test_target_matches_wrong_value():
    from app.review.auto_release import _target_matches
    ann = {"domain": "grammar", "grammar_focus_key": "comma_splice"}
    allowed = {"domain": "reading"}
    assert _target_matches(ann, allowed) is False


def test_target_matches_empty_allowed():
    from app.review.auto_release import _target_matches
    assert _target_matches({"domain": "grammar"}, {}) is False


def test_target_matches_none_annotation():
    from app.review.auto_release import _target_matches
    allowed = {"domain": "grammar"}
    assert _target_matches(None, allowed) is False


@pytest.mark.asyncio
async def test_annotation_dict_reads_annotation_jsonb():
    from app.review.auto_release import _annotation_dict
    ann = SimpleNamespace(
        annotation_jsonb={
            "grammar_role_key": "sentence_boundary",
            "grammar_focus_key": "comma_splice",
            "difficulty_overall": "medium",
        }
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_Result(first_item=ann))

    result = await _annotation_dict(uuid.uuid4(), db)

    assert result["domain"] == "grammar"
    assert result["grammar_role_key"] == "sentence_boundary"
    assert result["grammar_focus_key"] == "comma_splice"
    assert result["difficulty_overall"] == "medium"


# ---------------------------------------------------------------------------
# Auto-release eligibility: gate failures via maybe_auto_release
# ---------------------------------------------------------------------------

def _make_settings(**overrides):
    s = MagicMock()
    s.generation_auto_release_enabled = True
    s.generation_auto_release_min_reviews = 3
    s.generation_auto_release_min_accept_rate = 0.80
    s.generation_auto_release_allowed_targets = json.dumps(
        [{"domain": "grammar"}]
    )
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


def _make_verdict(**overrides):
    v = MagicMock()
    v.id = uuid.uuid4()
    v.consensus_verdict = "admin_review_ready"
    v.high_disagreement_flag = False
    v.generation_batch_id = uuid.uuid4()
    v.review_run_id = uuid.uuid4()
    for k, val in overrides.items():
        setattr(v, k, val)
    return v


@pytest.mark.asyncio
async def test_auto_release_blocked_when_config_disabled():
    from app.review.auto_release import maybe_auto_release
    settings = _make_settings(generation_auto_release_enabled=False)
    verdict = _make_verdict()
    db = AsyncMock()
    result = await maybe_auto_release(uuid.uuid4(), verdict, db, settings)
    assert result is False


@pytest.mark.asyncio
async def test_auto_release_blocked_by_runtime_kill_switch():
    import app.review.auto_release as ar
    original = ar._auto_release_disabled
    ar._auto_release_disabled = True
    try:
        settings = _make_settings()
        verdict = _make_verdict()
        db = AsyncMock()
        result = await ar.maybe_auto_release(uuid.uuid4(), verdict, db, settings)
        assert result is False
    finally:
        ar._auto_release_disabled = original


@pytest.mark.asyncio
async def test_auto_release_blocked_wrong_verdict():
    from app.review.auto_release import maybe_auto_release
    from app.models.db import Question
    settings = _make_settings()
    verdict = _make_verdict(consensus_verdict="reject_recommended")
    db = AsyncMock()
    mock_q = MagicMock(spec=Question)
    mock_q.official_overlap_status = "none"
    mock_q.practice_status = "draft"
    db.get = AsyncMock(return_value=mock_q)
    result = await maybe_auto_release(uuid.uuid4(), verdict, db, settings)
    assert result is False


@pytest.mark.asyncio
async def test_auto_release_blocked_gate_writes_audit():
    from app.review.auto_release import maybe_auto_release
    from app.models.db import AutoReleaseAuditLog, Question

    settings = _make_settings()
    verdict = _make_verdict(consensus_verdict="reject_recommended")
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    mock_q = MagicMock(spec=Question)
    mock_q.official_overlap_status = "none"
    mock_q.practice_status = "draft"
    db.get = AsyncMock(return_value=mock_q)

    result = await maybe_auto_release(uuid.uuid4(), verdict, db, settings)

    assert result is False
    audit = db.add.call_args.args[0]
    assert isinstance(audit, AutoReleaseAuditLog)
    assert audit.reasons_jsonb["result"] == "blocked"
    assert audit.reasons_jsonb["blocked_by"] == "consensus_verdict"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_release_blocked_high_disagreement():
    from app.review.auto_release import maybe_auto_release
    from app.models.db import Question
    settings = _make_settings()
    verdict = _make_verdict(high_disagreement_flag=True)
    db = AsyncMock()
    mock_q = MagicMock(spec=Question)
    mock_q.official_overlap_status = "none"
    mock_q.practice_status = "draft"
    db.get = AsyncMock(return_value=mock_q)
    result = await maybe_auto_release(uuid.uuid4(), verdict, db, settings)
    assert result is False


@pytest.mark.asyncio
async def test_auto_release_blocked_overlap_not_clean():
    from app.review.auto_release import maybe_auto_release
    from app.models.db import Question
    settings = _make_settings()
    verdict = _make_verdict()
    db = AsyncMock()
    mock_q = MagicMock(spec=Question)
    mock_q.official_overlap_status = "confirmed"
    mock_q.practice_status = "draft"
    db.get = AsyncMock(return_value=mock_q)
    result = await maybe_auto_release(uuid.uuid4(), verdict, db, settings)
    assert result is False


@pytest.mark.asyncio
async def test_auto_release_blocked_no_allowed_targets():
    from app.review.auto_release import maybe_auto_release
    from app.models.db import Question, GenerationBatch

    settings = _make_settings(generation_auto_release_allowed_targets="")
    verdict = _make_verdict()
    db = AsyncMock()
    mock_q = MagicMock(spec=Question)
    mock_q.official_overlap_status = "none"
    mock_q.practice_status = "draft"
    mock_batch = MagicMock(spec=GenerationBatch)
    mock_batch.release_policy = "auto_release_on_accept"

    async def _get(model_class, pk):
        if model_class == Question:
            return mock_q
        if model_class == GenerationBatch:
            return mock_batch
        return None

    db.get = _get

    # Wire db.execute to return a scalars mock compatible with .first()
    scalars_mock = MagicMock()
    scalars_mock.first.return_value = None
    scalars_mock.all.return_value = []
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=execute_result)

    result = await maybe_auto_release(uuid.uuid4(), verdict, db, settings)
    assert result is False


@pytest.mark.asyncio
async def test_auto_release_success_activates_and_writes_audit():
    from app.review.auto_release import maybe_auto_release
    from app.models.db import AutoReleaseAuditLog, GenerationBatch, Question

    settings = _make_settings()
    question_id = uuid.uuid4()
    verdict = _make_verdict()
    mock_q = MagicMock(spec=Question)
    mock_q.official_overlap_status = "none"
    mock_q.practice_status = "draft"
    mock_batch = MagicMock(spec=GenerationBatch)
    mock_batch.release_policy = "auto_release_on_accept"
    mock_job = SimpleNamespace(
        generation_batch_id=verdict.generation_batch_id,
        provider_name="openai",
        model_name="gpt-test",
    )

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def _get(model_class, pk):
        if model_class == Question:
            return mock_q
        if model_class == GenerationBatch:
            return mock_batch
        return None

    db.get = _get
    db.execute = AsyncMock(return_value=_Result(first_item=mock_job))

    with patch(
        "app.review.auto_release._annotation_dict",
        new_callable=AsyncMock,
        return_value={"domain": "grammar", "grammar_focus_key": "comma_splice"},
    ), patch(
        "app.review.auto_release._generator_acceptance_stats",
        new_callable=AsyncMock,
        return_value=(3, 3, 1.0),
    ):
        result = await maybe_auto_release(question_id, verdict, db, settings)

    assert result is True
    assert mock_q.practice_status == "active"
    audit = db.add.call_args.args[0]
    assert isinstance(audit, AutoReleaseAuditLog)
    assert audit.generator_provider_name == "openai"
    assert audit.generator_model_name == "gpt-test"
    assert audit.reasons_jsonb["result"] == "auto_released"
    db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Admin kill switch endpoints
# ---------------------------------------------------------------------------

def test_auto_release_status_endpoint(client):
    resp = client.get("/admin/generation/auto-release/status", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "config_enabled" in data
    assert "runtime_disabled" in data
    assert "effective_enabled" in data
    assert "min_reviews_required" in data
    assert "min_accept_rate" in data


def test_auto_release_status_requires_auth(client):
    resp = client.get("/admin/generation/auto-release/status")
    assert resp.status_code == 403


def test_disable_endpoint(client):
    import app.review.auto_release as ar
    original = ar._auto_release_disabled
    try:
        resp = client.post("/admin/generation/auto-release/disable", headers=AUTH)
        assert resp.status_code == 200
        assert resp.json()["status"] == "disabled"
        assert ar._auto_release_disabled is True
    finally:
        ar._auto_release_disabled = original


def test_enable_endpoint(client):
    import app.review.auto_release as ar
    ar._auto_release_disabled = True
    try:
        resp = client.post("/admin/generation/auto-release/enable", headers=AUTH)
        assert resp.status_code == 200
        assert resp.json()["status"] == "enabled"
        assert ar._auto_release_disabled is False
    finally:
        ar._auto_release_disabled = False


def test_disable_requires_auth(client):
    resp = client.post("/admin/generation/auto-release/disable")
    assert resp.status_code == 403


def test_enable_requires_auth(client):
    resp = client.post("/admin/generation/auto-release/enable")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Audit log endpoint
# ---------------------------------------------------------------------------

def test_audit_log_returns_shape(client):
    resp = client.get("/admin/generation/auto-release/audit", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "days" in data
    assert "count" in data
    assert "events" in data
    assert isinstance(data["events"], list)


def test_audit_log_empty_db(client):
    resp = client.get("/admin/generation/auto-release/audit", headers=AUTH)
    assert resp.json()["count"] == 0
    assert resp.json()["events"] == []


def test_audit_log_custom_days(client):
    resp = client.get("/admin/generation/auto-release/audit?days=7", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["days"] == 7


def test_audit_log_invalid_days(client):
    resp = client.get("/admin/generation/auto-release/audit?days=0", headers=AUTH)
    assert resp.status_code == 422


def test_audit_log_requires_auth(client):
    resp = client.get("/admin/generation/auto-release/audit")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Disable -> status reflects change
# ---------------------------------------------------------------------------

def test_disable_then_status_shows_disabled(client):
    import app.review.auto_release as ar
    original = ar._auto_release_disabled
    try:
        client.post("/admin/generation/auto-release/disable", headers=AUTH)
        resp = client.get("/admin/generation/auto-release/status", headers=AUTH)
        assert resp.json()["runtime_disabled"] is True
        assert resp.json()["effective_enabled"] is False
    finally:
        ar._auto_release_disabled = original


def test_enable_after_disable(client):
    import app.review.auto_release as ar
    original = ar._auto_release_disabled
    try:
        ar._auto_release_disabled = True
        client.post("/admin/generation/auto-release/enable", headers=AUTH)
        assert ar._auto_release_disabled is False
    finally:
        ar._auto_release_disabled = original
