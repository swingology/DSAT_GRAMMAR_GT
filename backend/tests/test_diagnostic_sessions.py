"""Phase 1 — Diagnostic Session Management endpoint tests.

Covers all 5 diagnostic endpoints:
  POST /api/diagnostic/start
  POST /api/diagnostic/{session_id}/submit
  POST /api/diagnostic/{session_id}/complete
  GET  /api/diagnostic/history
  GET  /api/diagnostic/{session_id}

Auth is tested at the boundary (403 on missing key, 404 on bad token).
DB behaviour is mocked via conftest._MockSession with per-test overrides.
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

AUTH = {"X-API-Key": "student-test-key"}
USER_TOKEN = "00000000-0000-0000-0000-000000000001"
SESSION_UUID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
VALID_SESSION_ID = str(SESSION_UUID)
INVALID_UUID = "not-a-uuid"


# ---------------------------------------------------------------------------
# Fake domain objects
# ---------------------------------------------------------------------------

class FakeUser:
    id = 1
    user_token = uuid.UUID(USER_TOKEN)


class FakeDiagnosticSession:
    id = SESSION_UUID
    user_id = 1
    started_at = datetime(2026, 6, 20, 10, 0, 0, tzinfo=timezone.utc)
    completed_at = None
    total_questions = 4
    correct_count = 3
    accuracy = None
    question_ids = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
    diagnostic_type = "standard"
    focus_areas = []
    is_archived = False
    created_at = datetime(2026, 6, 20, 9, 55, 0, tzinfo=timezone.utc)


class FakeCompletedSession(FakeDiagnosticSession):
    completed_at = datetime(2026, 6, 20, 10, 30, 0, tzinfo=timezone.utc)
    accuracy = 0.75


class FakeProgress:
    id = uuid.uuid4()
    user_id = 1
    question_id = uuid.uuid4()
    diagnostic_session_id = SESSION_UUID
    is_correct = True
    selected_option_label = "B"
    missed_grammar_focus_key = None
    missed_reading_focus_key = None
    timestamp = datetime(2026, 6, 20, 10, 1, 0, tzinfo=timezone.utc)


class FakeMissedProgress:
    id = uuid.uuid4()
    user_id = 1
    question_id = uuid.uuid4()
    diagnostic_session_id = SESSION_UUID
    is_correct = False
    selected_option_label = "A"
    missed_grammar_focus_key = "comma_splice"
    missed_reading_focus_key = None
    timestamp = datetime(2026, 6, 20, 10, 2, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# _ScalarResult helpers
# ---------------------------------------------------------------------------

class _UserResult:
    """Returns a FakeUser from .scalars().first()."""
    def scalars(self):
        return self

    def unique(self):
        return self

    def first(self):
        return FakeUser()

    def all(self):
        return []


class _EmptyResult:
    """Returns nothing — no user, no sessions."""
    def scalars(self):
        return self

    def unique(self):
        return self

    def first(self):
        return None

    def all(self):
        return []


class _CountResult:
    """Returns a scalar integer for count() queries."""
    def __init__(self, count=0):
        self._count = count

    def scalars(self):
        return self

    def unique(self):
        return self

    def first(self):
        return self._count

    def all(self):
        return [self._count]


class _ListResult:
    """Returns a list from .scalars().all()."""
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None


# ---------------------------------------------------------------------------
# POST /api/diagnostic/start
# ---------------------------------------------------------------------------

class TestDiagnosticStart:
    def test_diagnostic_start_requires_auth(self, client):
        resp = client.post(
            "/api/diagnostic/start",
            json={"user_token": USER_TOKEN},
        )
        assert resp.status_code == 403

    def test_diagnostic_start_invalid_token(self, client):
        """Non-UUID user_token → 400."""
        resp = client.post(
            "/api/diagnostic/start",
            json={"user_token": "not-a-uuid"},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_diagnostic_start_user_not_found(self, client):
        """Valid UUID token but no matching user → 404."""
        resp = client.post(
            "/api/diagnostic/start",
            json={"user_token": USER_TOKEN},
            headers=AUTH,
        )
        # Default mock_db.execute returns _ScalarResult which .first() → None
        assert resp.status_code == 404

    def test_diagnostic_start_creates_session(self, client):
        """When a user is found, endpoint returns 200 with session_id."""
        from app.main import app
        from app.database import get_db

        created_session_id = uuid.uuid4()

        class _CreatingDB:
            async def execute(self, _stmt):
                return _UserResult()

            def add(self, obj):
                # Assign an ID so db.refresh works
                obj.id = created_session_id

            async def commit(self):
                pass

            async def refresh(self, obj):
                obj.id = created_session_id

        async def _override():
            yield _CreatingDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.post(
                "/api/diagnostic/start",
                json={"user_token": USER_TOKEN, "diagnostic_type": "standard"},
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "session_id" in data
            assert data["session_id"] == str(created_session_id)
        finally:
            # Restore original override from conftest
            from tests.conftest import _MockSession

            mock_db = _MockSession()

            async def _orig():
                yield mock_db

            app.dependency_overrides[get_db] = _orig


# ---------------------------------------------------------------------------
# POST /api/diagnostic/{session_id}/submit
# ---------------------------------------------------------------------------

class TestDiagnosticSubmit:
    def test_diagnostic_submit_requires_auth(self, client):
        resp = client.post(
            f"/api/diagnostic/{VALID_SESSION_ID}/submit",
            json={
                "user_token": USER_TOKEN,
                "question_id": str(uuid.uuid4()),
                "selected_option_label": "A",
            },
        )
        assert resp.status_code == 403

    def test_diagnostic_submit_invalid_session_id(self, client):
        resp = client.post(
            f"/api/diagnostic/{INVALID_UUID}/submit",
            json={
                "user_token": USER_TOKEN,
                "question_id": str(uuid.uuid4()),
                "selected_option_label": "A",
            },
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_diagnostic_submit_session_not_found(self, client):
        """Valid UUID session but db.get returns None → 404."""
        # conftest mock_db.get already returns None by default
        resp = client.post(
            f"/api/diagnostic/{VALID_SESSION_ID}/submit",
            json={
                "user_token": USER_TOKEN,
                "question_id": str(uuid.uuid4()),
                "selected_option_label": "A",
            },
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_diagnostic_submit_session_already_completed(self, client):
        """Session with completed_at set → 400."""
        from app.main import app
        from app.database import get_db
        from app.models.db import DiagnosticSession

        fake_session = FakeCompletedSession()

        class _CompletedDB:
            async def get(self, model, pk):
                if model is DiagnosticSession:
                    return fake_session
                return None

            async def execute(self, _stmt):
                return _EmptyResult()

            def add(self, obj):
                pass

            async def commit(self):
                pass

            async def refresh(self, obj):
                pass

        async def _override():
            yield _CompletedDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.post(
                f"/api/diagnostic/{VALID_SESSION_ID}/submit",
                json={
                    "user_token": USER_TOKEN,
                    "question_id": str(uuid.uuid4()),
                    "selected_option_label": "A",
                },
                headers=AUTH,
            )
            assert resp.status_code == 400
            assert "completed" in resp.json()["detail"].lower()
        finally:
            from tests.conftest import _MockSession

            mock_db = _MockSession()

            async def _orig():
                yield mock_db

            app.dependency_overrides[get_db] = _orig


# ---------------------------------------------------------------------------
# POST /api/diagnostic/{session_id}/complete
# ---------------------------------------------------------------------------

class TestDiagnosticComplete:
    def test_diagnostic_complete_requires_auth(self, client):
        resp = client.post(
            f"/api/diagnostic/{VALID_SESSION_ID}/complete",
            json={"user_token": USER_TOKEN},
        )
        assert resp.status_code == 403

    def test_diagnostic_complete_invalid_session_id(self, client):
        resp = client.post(
            f"/api/diagnostic/{INVALID_UUID}/complete",
            json={"user_token": USER_TOKEN},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_diagnostic_complete_session_not_found(self, client):
        # Default mock returns None for db.get → 404
        resp = client.post(
            f"/api/diagnostic/{VALID_SESSION_ID}/complete",
            json={"user_token": USER_TOKEN},
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_diagnostic_complete_marks_session(self, client):
        """Complete endpoint returns accuracy and total_questions."""
        from app.main import app
        from app.database import get_db
        from app.models.db import DiagnosticSession

        fake_session = FakeDiagnosticSession()

        class _CompleteDB:
            async def get(self, model, pk):
                if model is DiagnosticSession:
                    return fake_session
                return None

            async def execute(self, _stmt):
                # First call: resolve user; second: fetch progress records
                return _UserResult()

            def add(self, obj):
                pass

            async def commit(self):
                pass

            async def refresh(self, obj):
                pass

        # We need execute to alternate: first call → user, second call → progress records
        call_count = [0]

        class _AltDB:
            async def get(self, model, pk):
                if model is DiagnosticSession:
                    return fake_session
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    return _UserResult()
                # Progress records query
                return _ListResult([])

            def add(self, obj):
                pass

            async def commit(self):
                pass

            async def refresh(self, obj):
                pass

        async def _override():
            yield _AltDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.post(
                f"/api/diagnostic/{VALID_SESSION_ID}/complete",
                json={"user_token": USER_TOKEN},
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "accuracy" in data
            assert "total_questions" in data
            assert data["total_questions"] == fake_session.total_questions
            # accuracy = 3/4 = 0.75
            assert data["accuracy"] == pytest.approx(0.75)
        finally:
            from tests.conftest import _MockSession

            mock_db = _MockSession()

            async def _orig():
                yield mock_db

            app.dependency_overrides[get_db] = _orig


# ---------------------------------------------------------------------------
# GET /api/diagnostic/history
# ---------------------------------------------------------------------------

class TestDiagnosticHistory:
    def test_diagnostic_history_requires_auth(self, client):
        resp = client.get(f"/api/diagnostic/history?user_token={USER_TOKEN}")
        assert resp.status_code == 403

    def test_diagnostic_history_user_not_found(self, client):
        """Default mock execute → None user → 404."""
        resp = client.get(
            f"/api/diagnostic/history?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_diagnostic_history_empty(self, client):
        """Valid user but no sessions → 200 with empty list."""
        from app.main import app
        from app.database import get_db

        call_count = [0]

        class _EmptyHistoryDB:
            async def get(self, model, pk):
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    return _UserResult()
                if call_count[0] == 2:
                    # sessions query
                    return _ListResult([])
                # count query
                return _CountResult(0)

            def add(self, obj):
                pass

            async def commit(self):
                pass

            async def refresh(self, obj):
                pass

        async def _override():
            yield _EmptyHistoryDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.get(
                f"/api/diagnostic/history?user_token={USER_TOKEN}",
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "sessions" in data
            assert data["sessions"] == []
            assert "total_sessions" in data
        finally:
            from tests.conftest import _MockSession

            mock_db = _MockSession()

            async def _orig():
                yield mock_db

            app.dependency_overrides[get_db] = _orig

    def test_diagnostic_history_with_sessions(self, client):
        """Returns list of session summaries."""
        from app.main import app
        from app.database import get_db

        s1 = FakeCompletedSession()
        s1.id = uuid.uuid4()
        s2 = FakeCompletedSession()
        s2.id = uuid.uuid4()

        call_count = [0]

        class _HistoryDB:
            async def get(self, model, pk):
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    return _UserResult()
                if call_count[0] == 2:
                    return _ListResult([s1, s2])
                return _CountResult(2)

            def add(self, obj):
                pass

            async def commit(self):
                pass

            async def refresh(self, obj):
                pass

        async def _override():
            yield _HistoryDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.get(
                f"/api/diagnostic/history?user_token={USER_TOKEN}",
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["sessions"]) == 2
            assert data["total_sessions"] == 2
            assert "average_accuracy" in data
            # Both sessions have accuracy=0.75
            assert data["average_accuracy"] == pytest.approx(0.75)
        finally:
            from tests.conftest import _MockSession

            mock_db = _MockSession()

            async def _orig():
                yield mock_db

            app.dependency_overrides[get_db] = _orig


# ---------------------------------------------------------------------------
# GET /api/diagnostic/{session_id}
# ---------------------------------------------------------------------------

class TestDiagnosticDetail:
    def test_diagnostic_detail_requires_auth(self, client):
        resp = client.get(
            f"/api/diagnostic/{VALID_SESSION_ID}?user_token={USER_TOKEN}"
        )
        assert resp.status_code == 403

    def test_diagnostic_detail_invalid_session_id(self, client):
        resp = client.get(
            f"/api/diagnostic/{INVALID_UUID}?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_diagnostic_detail_not_found(self, client):
        # Default mock returns None from db.get → 404
        resp = client.get(
            f"/api/diagnostic/{VALID_SESSION_ID}?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_diagnostic_detail_returns_data(self, client):
        """Returns session detail with question_results and focus_breakdown."""
        from app.main import app
        from app.database import get_db
        from app.models.db import DiagnosticSession

        fake_session = FakeCompletedSession()
        progress_records = [FakeProgress(), FakeMissedProgress()]

        call_count = [0]

        class _DetailDB:
            async def get(self, model, pk):
                if model is DiagnosticSession:
                    return fake_session
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    # user resolution
                    return _UserResult()
                # progress records
                return _ListResult(progress_records)

            def add(self, obj):
                pass

            async def commit(self):
                pass

            async def refresh(self, obj):
                pass

        async def _override():
            yield _DetailDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.get(
                f"/api/diagnostic/{VALID_SESSION_ID}?user_token={USER_TOKEN}",
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["session_id"] == VALID_SESSION_ID
            assert "question_results" in data
            assert "focus_breakdown" in data
            assert "accuracy" in data
            assert "total_questions" in data
            assert len(data["question_results"]) == 2
            # comma_splice should appear in focus_breakdown from FakeMissedProgress
            assert "comma_splice" in data["focus_breakdown"]
        finally:
            from tests.conftest import _MockSession

            mock_db = _MockSession()

            async def _orig():
                yield mock_db

            app.dependency_overrides[get_db] = _orig
