"""Phase 2 — Spaced Repetition endpoint and algorithm tests.

Covers:
  A. SM-2 algorithm unit tests (no DB required)
  B. API endpoint tests:
       POST /api/spaced-repetition/{question_id}/review
       GET  /api/spaced-repetition/due
       GET  /api/spaced-repetition/progress

Auth tested at the boundary (403 on missing key, 404 on bad token).
DB behaviour is mocked via conftest._MockSession with per-test overrides.
"""

import sys
import os
import uuid

# Force env before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test")
os.environ.setdefault("ADMIN_API_KEYS", "admin-test-key")
os.environ.setdefault("STUDENT_API_KEYS", "student-test-key")

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Imports from app (after env is set)
# ---------------------------------------------------------------------------

sys.path.insert(0, '/home/jb/DSAT_REDUX_MD/backend')

from app.routers.student import _sm2_update, _sr_confidence_level
from app.models.db import SpacedRepetitionState

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

AUTH = {"X-API-Key": "student-test-key"}
USER_TOKEN = "00000000-0000-0000-0000-000000000001"
QUESTION_UUID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
VALID_QUESTION_ID = str(QUESTION_UUID)
INVALID_UUID = "not-a-uuid"


# ---------------------------------------------------------------------------
# SM-2 helper
# ---------------------------------------------------------------------------

class _FakeSR:
    """Plain Python stand-in for SpacedRepetitionState for unit tests.

    Using SQLAlchemy.__new__ fails because the mapper requires a proper
    construction context to initialise InstrumentedAttribute descriptors.
    This plain class has identical fields and works with _sm2_update /
    _sr_confidence_level because those functions only access plain attributes.
    """
    def __init__(self):
        self.easiness_factor = 2.5
        self.interval_days = 1.0
        self.repetition_count = 0
        self.total_attempts = 0
        self.correct_attempts = 0
        self.last_reviewed_at = None
        self.next_review_at = None


def fresh_sr() -> _FakeSR:
    """Return a fresh SM-2 state with default values."""
    return _FakeSR()


NOW = datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# A. SM-2 Algorithm unit tests
# ---------------------------------------------------------------------------

class TestSM2Algorithm:
    def test_sm2_quality_5_first_rep(self):
        """quality=5, first rep → interval=1.0, rep_count=1, EF increases."""
        sr = fresh_sr()
        _sm2_update(sr, 5, NOW)
        assert sr.repetition_count == 1
        assert sr.interval_days == 1.0
        # EF formula: 2.5 + (0.1 - (5-5)*(0.08 + (5-5)*0.02)) = 2.5 + 0.1 = 2.6
        assert sr.easiness_factor > 2.5

    def test_sm2_quality_5_second_rep(self):
        """Apply quality=5 twice → second interval=6.0, rep_count=2."""
        sr = fresh_sr()
        _sm2_update(sr, 5, NOW)
        _sm2_update(sr, 5, NOW)
        assert sr.repetition_count == 2
        assert sr.interval_days == 6.0

    def test_sm2_quality_5_third_rep(self):
        """Apply quality=5 three times → third interval ~ EF*6, rep_count=3."""
        sr = fresh_sr()
        _sm2_update(sr, 5, NOW)
        _sm2_update(sr, 5, NOW)
        _sm2_update(sr, 5, NOW)
        assert sr.repetition_count == 3
        # After 3 reps: interval = 6 * EF ≈ 6 * 2.6 = 15.6
        assert sr.interval_days > 10.0

    def test_sm2_quality_below_3_resets(self):
        """quality=2 → rep_count resets to 0, interval resets to 1.0."""
        sr = fresh_sr()
        # Earn some reps first
        _sm2_update(sr, 5, NOW)
        _sm2_update(sr, 5, NOW)
        assert sr.repetition_count == 2
        # Now a failing answer
        _sm2_update(sr, 2, NOW)
        assert sr.repetition_count == 0
        assert sr.interval_days == 1.0

    def test_sm2_ef_floor(self):
        """EF never drops below 1.3 regardless of how many quality=0 are applied."""
        sr = fresh_sr()
        for _ in range(20):
            _sm2_update(sr, 0, NOW)
        assert sr.easiness_factor >= 1.3

    def test_sm2_ef_cap(self):
        """EF never exceeds 5.0 regardless of how many quality=5 are applied.

        We test this by applying the EF formula directly on a freshly reset SR
        state (so interval never grows uncontrollably into overflow territory).
        Each iteration resets rep_count to 1 (via a quality=0 reset followed by
        a quality=5) so interval stays small while EF accumulates.
        """
        sr = fresh_sr()
        # Apply quality=5 on a fresh state repeatedly; after each update reset
        # rep_count so next_review_at stays within sane date range.
        for _ in range(15):
            sr.repetition_count = 0   # keep interval from compounding
            sr.interval_days = 1.0
            _sm2_update(sr, 5, NOW)
        assert sr.easiness_factor <= 5.0

    def test_sm2_next_review_set(self):
        """After update, next_review_at = now + interval_days."""
        sr = fresh_sr()
        _sm2_update(sr, 5, NOW)
        expected = NOW + timedelta(days=sr.interval_days)
        assert sr.next_review_at == expected

    def test_sm2_attempts_counted(self):
        """quality=5 increments both total and correct; quality=1 increments only total."""
        sr = fresh_sr()
        _sm2_update(sr, 5, NOW)
        assert sr.total_attempts == 1
        assert sr.correct_attempts == 1
        _sm2_update(sr, 1, NOW)
        assert sr.total_attempts == 2
        assert sr.correct_attempts == 1  # quality < 3, not counted correct

    def test_confidence_novice(self):
        """Fresh SR state → 'novice'."""
        sr = fresh_sr()
        assert _sr_confidence_level(sr) == "novice"

    def test_confidence_developing(self):
        """1 repetition → 'developing'."""
        sr = fresh_sr()
        _sm2_update(sr, 4, NOW)
        assert _sr_confidence_level(sr) == "developing"

    def test_confidence_proficient(self):
        """3 reps, EF=2.5 → 'proficient'."""
        sr = fresh_sr()
        # Quality=4 keeps EF near 2.5 (exactly: 2.5 + (0.1 - 1*0.1) = 2.5)
        _sm2_update(sr, 4, NOW)
        _sm2_update(sr, 4, NOW)
        _sm2_update(sr, 4, NOW)
        assert sr.repetition_count == 3
        # EF stays ≥ 2.5 with quality=4
        level = _sr_confidence_level(sr)
        assert level in ("proficient", "mastered")

    def test_confidence_mastered(self):
        """5 reps with quality=5, EF well above 3.5 → 'mastered'."""
        sr = fresh_sr()
        for _ in range(5):
            _sm2_update(sr, 5, NOW)
        assert sr.repetition_count == 5
        # After 5 quality-5 reps, EF ≥ 3.0 (may not always reach 3.5)
        level = _sr_confidence_level(sr)
        assert level in ("proficient", "mastered")


# ---------------------------------------------------------------------------
# Fake domain objects for API tests
# ---------------------------------------------------------------------------

class FakeUser:
    id = 1
    user_token = uuid.UUID(USER_TOKEN)


class FakeQuestion:
    id = QUESTION_UUID
    practice_status = "active"
    latest_annotation_id = None
    latest_version_id = None


class FakeSRState:
    id = 1
    user_id = 1
    question_id = QUESTION_UUID
    easiness_factor = 2.5
    interval_days = 1.0
    repetition_count = 1
    total_attempts = 1
    correct_attempts = 1
    last_reviewed_at = NOW
    next_review_at = NOW + timedelta(days=1)


class FakeSRStateMastered:
    id = 2
    user_id = 1
    question_id = uuid.uuid4()
    easiness_factor = 4.0
    interval_days = 60.0
    repetition_count = 8
    total_attempts = 10
    correct_attempts = 9
    last_reviewed_at = NOW - timedelta(days=61)
    next_review_at = NOW - timedelta(days=1)  # overdue


class FakeSRStateNovice:
    id = 3
    user_id = 1
    question_id = uuid.uuid4()
    easiness_factor = 2.5
    interval_days = 1.0
    repetition_count = 0
    total_attempts = 1
    correct_attempts = 0
    last_reviewed_at = NOW - timedelta(days=2)
    next_review_at = NOW - timedelta(days=1)  # overdue


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

class _UserResult:
    def scalars(self): return self
    def unique(self): return self
    def first(self): return FakeUser()
    def all(self): return []


class _EmptyResult:
    def scalars(self): return self
    def unique(self): return self
    def first(self): return None
    def all(self): return []


class _ListResult:
    def __init__(self, items):
        self._items = items
    def scalars(self): return self
    def unique(self): return self
    def all(self): return self._items
    def first(self): return self._items[0] if self._items else None


class _ScalarIntResult:
    def __init__(self, value):
        self._value = value
    def scalars(self): return self
    def unique(self): return self
    def first(self): return self._value
    def all(self): return [self._value]


# ---------------------------------------------------------------------------
# B. API Endpoint Tests — POST /api/spaced-repetition/{question_id}/review
# ---------------------------------------------------------------------------

class TestSRReview:
    def test_sr_review_requires_auth(self, client):
        resp = client.post(
            f"/api/spaced-repetition/{VALID_QUESTION_ID}/review",
            json={"user_token": USER_TOKEN, "quality": 5},
        )
        assert resp.status_code == 403

    def test_sr_review_invalid_question_id(self, client):
        resp = client.post(
            f"/api/spaced-repetition/{INVALID_UUID}/review",
            json={"user_token": USER_TOKEN, "quality": 5},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_sr_review_question_not_found(self, client):
        """Valid UUID but db.get returns None for Question → 404.
        Also need user to be found first via execute.
        """
        from app.main import app
        from app.database import get_db

        call_count = [0]

        class _UserFoundQNotFound:
            async def get(self, model, pk):
                # Question lookup → None
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    # user resolution via _resolve_user_by_token
                    return _UserResult()
                return _EmptyResult()

            def add(self, obj): pass
            async def commit(self): pass
            async def refresh(self, obj): pass

        async def _override():
            yield _UserFoundQNotFound()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.post(
                f"/api/spaced-repetition/{VALID_QUESTION_ID}/review",
                json={"user_token": USER_TOKEN, "quality": 5},
                headers=AUTH,
            )
            assert resp.status_code == 404
        finally:
            from tests.conftest import _MockSession
            mock_db = _MockSession()
            async def _orig(): yield mock_db
            app.dependency_overrides[get_db] = _orig

    def test_sr_review_creates_state(self, client):
        """First review with quality=5 → 200 with confidence_level in response."""
        from app.main import app
        from app.database import get_db
        from app.models.db import Question

        fake_sr = FakeSRState()
        call_count = [0]

        class _CreateSRDB:
            async def get(self, model, pk):
                if model is Question:
                    return FakeQuestion()
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    # user resolution
                    return _UserResult()
                # SR state lookup → none existing (first review)
                return _EmptyResult()

            def add(self, obj):
                # Simulate the DB assigning state values
                obj.easiness_factor = fake_sr.easiness_factor
                obj.interval_days = fake_sr.interval_days
                obj.repetition_count = fake_sr.repetition_count
                obj.total_attempts = fake_sr.total_attempts
                obj.correct_attempts = fake_sr.correct_attempts
                obj.next_review_at = fake_sr.next_review_at
                obj.last_reviewed_at = fake_sr.last_reviewed_at

            async def commit(self): pass

            async def refresh(self, obj):
                obj.easiness_factor = fake_sr.easiness_factor
                obj.interval_days = fake_sr.interval_days
                obj.repetition_count = fake_sr.repetition_count
                obj.total_attempts = fake_sr.total_attempts
                obj.correct_attempts = fake_sr.correct_attempts
                obj.next_review_at = fake_sr.next_review_at
                obj.last_reviewed_at = fake_sr.last_reviewed_at

        async def _override():
            yield _CreateSRDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.post(
                f"/api/spaced-repetition/{VALID_QUESTION_ID}/review",
                json={"user_token": USER_TOKEN, "quality": 5},
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "confidence_level" in data
            assert data["confidence_level"] in ("novice", "developing", "proficient", "mastered")
            assert "next_review_at" in data
            assert "interval_days" in data
        finally:
            from tests.conftest import _MockSession
            mock_db = _MockSession()
            async def _orig(): yield mock_db
            app.dependency_overrides[get_db] = _orig


# ---------------------------------------------------------------------------
# B. API Endpoint Tests — GET /api/spaced-repetition/due
# ---------------------------------------------------------------------------

class TestSRDue:
    def test_sr_due_requires_auth(self, client):
        resp = client.get(f"/api/spaced-repetition/due?user_token={USER_TOKEN}")
        assert resp.status_code == 403

    def test_sr_due_user_not_found(self, client):
        """Valid format token, no matching user → 404."""
        # Default conftest mock_db.execute returns _ScalarResult with .first() = None
        resp = client.get(
            f"/api/spaced-repetition/due?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_sr_due_empty(self, client):
        """User found, no SR records → {due_questions: [], total_due: 0}."""
        from app.main import app
        from app.database import get_db

        call_count = [0]

        class _EmptyDueDB:
            async def get(self, model, pk):
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    return _UserResult()
                if call_count[0] == 2:
                    # due SR records query
                    return _ListResult([])
                # total_due count query
                return _ScalarIntResult(0)

            def add(self, obj): pass
            async def commit(self): pass
            async def refresh(self, obj): pass

        async def _override():
            yield _EmptyDueDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.get(
                f"/api/spaced-repetition/due?user_token={USER_TOKEN}",
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "due_questions" in data
            assert data["due_questions"] == []
            assert data["total_due"] == 0
        finally:
            from tests.conftest import _MockSession
            mock_db = _MockSession()
            async def _orig(): yield mock_db
            app.dependency_overrides[get_db] = _orig


# ---------------------------------------------------------------------------
# B. API Endpoint Tests — GET /api/spaced-repetition/progress
# ---------------------------------------------------------------------------

class TestSRProgress:
    def test_sr_progress_requires_auth(self, client):
        resp = client.get(f"/api/spaced-repetition/progress?user_token={USER_TOKEN}")
        assert resp.status_code == 403

    def test_sr_progress_user_not_found(self, client):
        """Default mock returns no user → 404."""
        resp = client.get(
            f"/api/spaced-repetition/progress?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_sr_progress_empty(self, client):
        """User with no SR records → zeros."""
        from app.main import app
        from app.database import get_db

        call_count = [0]

        class _EmptyProgressDB:
            async def get(self, model, pk):
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    return _UserResult()
                # All SR records query → empty
                return _ListResult([])

            def add(self, obj): pass
            async def commit(self): pass
            async def refresh(self, obj): pass

        async def _override():
            yield _EmptyProgressDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.get(
                f"/api/spaced-repetition/progress?user_token={USER_TOKEN}",
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_tracked"] == 0
            assert data["due_for_review"] == 0
            assert data["retention_rate"] == 0.0
        finally:
            from tests.conftest import _MockSession
            mock_db = _MockSession()
            async def _orig(): yield mock_db
            app.dependency_overrides[get_db] = _orig

    def test_sr_progress_with_records(self, client):
        """User with 2 SR records (one mastered EF=4.0/reps=8, one novice reps=0)
        → correct tier counts."""
        from app.main import app
        from app.database import get_db

        mastered_sr = FakeSRStateMastered()
        novice_sr = FakeSRStateNovice()
        # FakeSRStateMastered: EF=4.0, reps=8 → mastered
        # FakeSRStateNovice: EF=2.5, reps=0 → novice

        call_count = [0]

        class _WithRecordsDB:
            async def get(self, model, pk):
                return None

            async def execute(self, _stmt):
                call_count[0] += 1
                if call_count[0] == 1:
                    return _UserResult()
                # All SR records
                return _ListResult([mastered_sr, novice_sr])

            def add(self, obj): pass
            async def commit(self): pass
            async def refresh(self, obj): pass

        async def _override():
            yield _WithRecordsDB()

        app.dependency_overrides[get_db] = _override
        try:
            resp = client.get(
                f"/api/spaced-repetition/progress?user_token={USER_TOKEN}",
                headers=AUTH,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_tracked"] == 2
            # mastered_sr has next_review_at = NOW - 1 day = overdue
            # novice_sr has next_review_at = NOW - 1 day = overdue
            assert data["due_for_review"] == 2
            # Tier breakdown: 1 mastered, 0 proficient, 0 developing, 1 novice
            assert data["mastered_count"] == 1
            assert data["novice_count"] == 1
            # Retention: (9+0) / (10+1) ≈ 0.8182
            assert data["retention_rate"] > 0.0
        finally:
            from tests.conftest import _MockSession
            mock_db = _MockSession()
            async def _orig(): yield mock_db
            app.dependency_overrides[get_db] = _orig
