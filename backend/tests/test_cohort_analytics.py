"""Tests for Phase 5 cohort analytics endpoints."""
import pytest
from fastapi.testclient import TestClient

AUTH = {"X-API-Key": "admin-test-key"}
STUDENT_AUTH = {"X-API-Key": "student-test-key"}


class TestWeakSpotsEndpoint:
    def test_requires_admin_auth(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots")
        assert resp.status_code in (401, 403)

    def test_student_auth_rejected(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots", headers=STUDENT_AUTH)
        assert resp.status_code in (401, 403)

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots", headers=AUTH)
        assert resp.status_code != 405

    def test_returns_200_with_admin_key(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots", headers=AUTH)
        assert resp.status_code == 200

    def test_response_has_required_keys(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots", headers=AUTH)
        data = resp.json()
        assert "generated_at" in data
        assert "question_wise_misses" in data
        assert "focus_area_misses" in data

    def test_question_misses_is_list(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots", headers=AUTH)
        assert isinstance(resp.json()["question_wise_misses"], list)

    def test_limit_param_accepted(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots?limit=5", headers=AUTH)
        assert resp.status_code == 200

    def test_limit_too_small_rejected(self, client: TestClient):
        resp = client.get("/admin/analytics/weak-spots?limit=1", headers=AUTH)
        assert resp.status_code == 422

    def test_focus_key_derived_from_annotation_jsonb(self):
        """Regression: the focus-map lookup must read
        QuestionAnnotation.annotation_jsonb (the real column) and derive the
        focus key in Python, not select a nonexistent
        QuestionAnnotation.grammar_focus_key ORM attribute.

        This only exercises the buggy code path when there is at least one
        question-miss row, since the annotation-join query is skipped
        entirely when `question_ids` is empty.
        """
        import uuid as _uuid
        from types import SimpleNamespace
        from fastapi.testclient import TestClient

        from app.main import app
        from app.database import get_db

        qid = _uuid.uuid4()

        class FakeResult:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        class FakeSession:
            def __init__(self):
                self.call_count = 0

            async def execute(self, stmt):
                self.call_count += 1
                if self.call_count == 1:
                    # Per-question miss rates (UserProgress aggregation)
                    return FakeResult([
                        SimpleNamespace(
                            question_id=qid,
                            question_domain="grammar",
                            total=10,
                            misses=6,
                        )
                    ])
                if self.call_count == 2:
                    # Focus-key lookup joined against QuestionAnnotation
                    return FakeResult([
                        (qid, {"grammar_focus_key": "subject_verb_agreement"}),
                    ])
                # Focus-area (grammar / reading) miss-rate queries: no rows
                return FakeResult([])

        fake = FakeSession()

        async def _override_get_db():
            yield fake

        app.dependency_overrides[get_db] = _override_get_db
        try:
            with TestClient(app) as c:
                resp = c.get("/admin/analytics/weak-spots", headers=AUTH)
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200
        misses = resp.json()["question_wise_misses"]
        assert len(misses) == 1
        assert misses[0]["question_id"] == str(qid)
        assert misses[0]["focus_key"] == "subject_verb_agreement"


class TestCohortSummaryEndpoint:
    def test_requires_admin_auth(self, client: TestClient):
        resp = client.get("/admin/analytics/student-cohort-summary")
        assert resp.status_code in (401, 403)

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get("/admin/analytics/student-cohort-summary", headers=AUTH)
        assert resp.status_code != 405

    def test_returns_200(self, client: TestClient):
        resp = client.get("/admin/analytics/student-cohort-summary", headers=AUTH)
        assert resp.status_code == 200

    def test_response_shape(self, client: TestClient):
        resp = client.get("/admin/analytics/student-cohort-summary", headers=AUTH)
        data = resp.json()
        assert "total_students" in data
        assert "active_this_week" in data
        assert "average_accuracy" in data
        assert "accuracy_distribution" in data
        assert "domain_performance" in data

    def test_accuracy_distribution_has_6_buckets(self, client: TestClient):
        resp = client.get("/admin/analytics/student-cohort-summary", headers=AUTH)
        buckets = resp.json()["accuracy_distribution"]
        assert len(buckets) == 6

    def test_zero_students_returns_valid_response(self, client: TestClient):
        resp = client.get("/admin/analytics/student-cohort-summary", headers=AUTH)
        data = resp.json()
        assert data["total_students"] >= 0
        assert data["average_accuracy"] >= 0.0


class TestTrapAnalyticsEndpoint:
    def test_requires_admin_auth(self, client: TestClient):
        resp = client.get("/admin/analytics/trap-analytics")
        assert resp.status_code in (401, 403)

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get("/admin/analytics/trap-analytics", headers=AUTH)
        assert resp.status_code != 405

    def test_returns_200(self, client: TestClient):
        resp = client.get("/admin/analytics/trap-analytics", headers=AUTH)
        assert resp.status_code == 200

    def test_response_shape(self, client: TestClient):
        resp = client.get("/admin/analytics/trap-analytics", headers=AUTH)
        data = resp.json()
        assert "generated_at" in data
        assert "total_trap_encounters" in data
        assert "most_common_traps" in data
        assert "most_effective_traps" in data

    def test_traps_are_lists(self, client: TestClient):
        resp = client.get("/admin/analytics/trap-analytics", headers=AUTH)
        data = resp.json()
        assert isinstance(data["most_common_traps"], list)
        assert isinstance(data["most_effective_traps"], list)

    def test_min_encounters_param_accepted(self, client: TestClient):
        resp = client.get(
            "/admin/analytics/trap-analytics?min_encounters=10", headers=AUTH
        )
        assert resp.status_code == 200


class TestCohortAnalyticsBusinessLogic:
    """Unit tests for analytics calculation logic."""

    def test_miss_rate_calculation(self):
        total, misses = 100, 42
        miss_rate = round(misses / total, 4)
        assert miss_rate == 0.42

    def test_miss_rate_zero_misses(self):
        total, misses = 50, 0
        miss_rate = round(misses / total, 4) if total else 0.0
        assert miss_rate == 0.0

    def test_accuracy_bucket_ranges(self):
        buckets = [
            ("0–50%", 0.0, 0.5),
            ("50–60%", 0.5, 0.6),
            ("60–70%", 0.6, 0.7),
            ("70–80%", 0.7, 0.8),
            ("80–90%", 0.8, 0.9),
            ("90–100%", 0.9, 1.01),
        ]
        accuracies = [0.45, 0.55, 0.65, 0.75, 0.85, 0.95]
        for (label, lo, hi), acc in zip(buckets, accuracies):
            count = sum(1 for a in accuracies if lo <= a < hi)
            assert count == 1, f"Bucket {label} should contain exactly 1 student"

    def test_average_accuracy_across_students(self):
        per_student = [(10, 7), (20, 12), (5, 5)]  # (total, correct)
        accuracies = [c / t for t, c in per_student]
        avg = round(sum(accuracies) / len(accuracies), 4)
        assert 0.0 <= avg <= 1.0

    def test_most_common_traps_sorted_by_volume(self):
        stats = [
            {"trap_type": "a", "total_encounters": 3},
            {"trap_type": "b", "total_encounters": 50},
            {"trap_type": "c", "total_encounters": 12},
        ]
        top = sorted(stats, key=lambda s: s["total_encounters"], reverse=True)[:10]
        assert top[0]["trap_type"] == "b"

    def test_most_effective_traps_sorted_by_fall_rate(self):
        stats = [
            {"trap_type": "a", "fall_rate": 0.3, "total_encounters": 10},
            {"trap_type": "b", "fall_rate": 0.9, "total_encounters": 15},
            {"trap_type": "c", "fall_rate": 0.6, "total_encounters": 8},
        ]
        effective = sorted(
            [s for s in stats if s["total_encounters"] >= 5],
            key=lambda s: s["fall_rate"],
            reverse=True,
        )[:10]
        assert effective[0]["trap_type"] == "b"

    def test_min_encounters_filter(self):
        stats = [
            {"trap_type": "rare", "total_encounters": 2, "fall_rate": 0.9},
            {"trap_type": "common", "total_encounters": 20, "fall_rate": 0.4},
        ]
        min_enc = 5
        filtered = [s for s in stats if s["total_encounters"] >= min_enc]
        assert len(filtered) == 1
        assert filtered[0]["trap_type"] == "common"
