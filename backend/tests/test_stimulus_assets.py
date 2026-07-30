"""Tests for GET /api/stimulus-assets/{asset_id} — the visual-stimulus serving route.

Covers auth gating, not-found cases, the active-vs-non-active parent guard,
and the happy path (returns the cropped image bytes with a content type).
"""

import uuid

import pytest

from app.routers import student as student_router


# ---------------------------------------------------------------------------
# HTTP-layer gating (conftest mock DB returns None for .get -> 404)
# ---------------------------------------------------------------------------

def test_stimulus_asset_requires_auth(client):
    resp = client.get(f"/api/stimulus-assets/{uuid.uuid4()}")
    assert resp.status_code == 403


def test_stimulus_asset_bad_uuid_returns_404(client):
    resp = client.get("/api/stimulus-assets/not-a-uuid", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 404


def test_stimulus_asset_missing_returns_404(client):
    # Mock DB's .get() returns None, so the asset lookup misses.
    resp = client.get(f"/api/stimulus-assets/{uuid.uuid4()}", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Direct-call tests with a fake DB that returns controlled rows
# ---------------------------------------------------------------------------

class _FakeAsset:
    def __init__(self, id, question_id, stimulus_type="graph", storage_path="local-s3://crops/a.png", source_span_id=None):
        self.id = id
        self.question_id = question_id
        self.stimulus_type = stimulus_type
        self.storage_path = storage_path
        self.source_span_id = source_span_id
        self.title = "Annual Output"
        self.source_page_number = 3
        self.structured_data_jsonb = None
        self.render_hints_jsonb = None


class _FakeQuestion:
    def __init__(self, practice_status="active"):
        self.practice_status = practice_status


class _FakeSpan:
    def __init__(self, crop_path=None):
        self.crop_path = crop_path


class _FakeDB:
    """Returns predetermined objects keyed by (model, pk)."""

    def __init__(self, mapping):
        self._mapping = mapping

    async def get(self, model, pk):
        return self._mapping.get((model, pk))


@pytest.mark.asyncio
async def test_serve_stimulus_asset_non_active_parent_404(monkeypatch):
    aid = uuid.uuid4()
    asset = _FakeAsset(id=aid, question_id=uuid.uuid4())
    db = _FakeDB({
        (student_router.QuestionStimulusAsset, aid): asset,
        (student_router.Question, asset.question_id): _FakeQuestion(practice_status="draft"),
    })
    # Should never reach read_object; assert it isn't called.
    monkeypatch.setattr(student_router, "read_object", lambda p: pytest.fail("must not read for non-active"))

    with pytest.raises(Exception) as exc:
        await student_router.serve_stimulus_asset(str(aid), db=db, auth=("student", "test"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_serve_stimulus_asset_active_returns_image_bytes(monkeypatch):
    aid = uuid.uuid4()
    asset = _FakeAsset(id=aid, question_id=uuid.uuid4(), storage_path="local-s3://crops/chart.png")
    db = _FakeDB({
        (student_router.QuestionStimulusAsset, aid): asset,
        (student_router.Question, asset.question_id): _FakeQuestion(practice_status="active"),
    })
    monkeypatch.setattr(student_router, "read_object", lambda p: b"\x89PNG\r\n\x1a\n" if p.endswith("chart.png") else b"")

    resp = await student_router.serve_stimulus_asset(str(aid), db=db, auth=("student", "test"))

    assert resp.status_code == 200
    assert resp.media_type == "image/png"
    assert resp.body == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_serve_stimulus_asset_prefers_span_crop_path(monkeypatch):
    """When a source span with a crop_path exists, the span crop is served, not the asset's storage_path."""
    span_id = uuid.uuid4()
    aid = uuid.uuid4()
    asset = _FakeAsset(id=aid, question_id=uuid.uuid4(), storage_path="local-s3://crops/full.png", source_span_id=span_id)
    db = _FakeDB({
        (student_router.QuestionStimulusAsset, aid): asset,
        (student_router.Question, asset.question_id): _FakeQuestion(practice_status="active"),
        (student_router.QuestionSourceSpan, span_id): _FakeSpan(crop_path="local-s3://crops/cropped.png"),
    })

    served = {}

    def fake_read(p):
        served["path"] = p
        return b"\x89PNG\r\n\x1a\n"

    monkeypatch.setattr(student_router, "read_object", fake_read)

    resp = await student_router.serve_stimulus_asset(str(aid), db=db, auth=("student", "test"))
    assert resp.status_code == 200
    assert served["path"].endswith("cropped.png")


@pytest.mark.asyncio
async def test_serve_stimulus_asset_missing_artifact_404(monkeypatch):
    aid = uuid.uuid4()
    asset = _FakeAsset(id=aid, question_id=uuid.uuid4())
    db = _FakeDB({
        (student_router.QuestionStimulusAsset, aid): asset,
        (student_router.Question, asset.question_id): _FakeQuestion(practice_status="active"),
    })
    monkeypatch.setattr(student_router, "read_object", lambda p: (_ for _ in ()).throw(FileNotFoundError()))

    with pytest.raises(Exception) as exc:
        await student_router.serve_stimulus_asset(str(aid), db=db, auth=("student", "test"))
    assert exc.value.status_code == 404