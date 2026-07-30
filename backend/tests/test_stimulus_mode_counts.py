"""Tests for GET /api/questions/stimulus-counts."""

import pytest

from app.routers import student as student_router
from app.models.ontology import STIMULUS_MODE_KEYS


# ---------------------------------------------------------------------------
# HTTP-layer tests (use the TestClient via the `client` fixture from conftest)
# ---------------------------------------------------------------------------

def test_stimulus_counts_requires_auth(client):
    resp = client.get("/api/questions/stimulus-counts")
    assert resp.status_code == 403


def test_stimulus_counts_student_auth_accepted(client):
    resp = client.get("/api/questions/stimulus-counts", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200


def test_stimulus_counts_admin_auth_accepted(client):
    resp = client.get("/api/questions/stimulus-counts", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 200


def test_stimulus_counts_response_shape(client):
    resp = client.get("/api/questions/stimulus-counts", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == len(STIMULUS_MODE_KEYS)
    returned_keys = {row["stimulus_mode_key"] for row in data}
    assert returned_keys == set(STIMULUS_MODE_KEYS)
    for row in data:
        assert "count" in row
        assert isinstance(row["count"], int)


# ---------------------------------------------------------------------------
# Direct-call test with a fake DB returning known grouped counts
# ---------------------------------------------------------------------------

class _GroupByResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt):
        return _GroupByResult(self._rows)


@pytest.mark.asyncio
async def test_stimulus_counts_fills_zero_for_missing_keys():
    """Keys with no matching rows in the DB result must still appear, with count 0."""
    db = _FakeDB(rows=[("prose_plus_graph", 43), ("poem", 9)])
    result = await student_router.get_stimulus_mode_counts(db=db, auth=("student", "test"))

    by_key = {row.stimulus_mode_key: row.count for row in result}
    assert by_key["prose_plus_graph"] == 43
    assert by_key["poem"] == 9
    assert by_key["sentence_only"] == 0
    assert set(by_key.keys()) == set(STIMULUS_MODE_KEYS)


@pytest.mark.asyncio
async def test_stimulus_counts_preserves_ontology_order():
    db = _FakeDB(rows=[])
    result = await student_router.get_stimulus_mode_counts(db=db, auth=("student", "test"))
    assert [row.stimulus_mode_key for row in result] == list(STIMULUS_MODE_KEYS)
