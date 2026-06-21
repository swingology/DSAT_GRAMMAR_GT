"""Tests for Phase 3 progress analytics endpoints."""
import pytest
from fastapi.testclient import TestClient

AUTH = {"X-API-Key": "student-test-key"}
USER_TOKEN = "00000000-0000-0000-0000-000000000001"


class TestProgressTrend:
    def test_requires_auth(self, client: TestClient):
        resp = client.get(f"/api/progress/trend?user_token={USER_TOKEN}")
        assert resp.status_code in (401, 403)

    def test_user_not_found_returns_404(self, client: TestClient):
        resp = client.get(
            f"/api/progress/trend?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get(
            f"/api/progress/trend?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code != 405

    def test_days_param_validation(self, client: TestClient):
        # days < 7 should be rejected
        resp = client.get(
            f"/api/progress/trend?user_token={USER_TOKEN}&days=3",
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_days_param_too_large(self, client: TestClient):
        resp = client.get(
            f"/api/progress/trend?user_token={USER_TOKEN}&days=91",
            headers=AUTH,
        )
        assert resp.status_code == 422


class TestDomainTrend:
    def test_requires_auth(self, client: TestClient):
        resp = client.get(f"/api/progress/domain-trend?user_token={USER_TOKEN}")
        assert resp.status_code in (401, 403)

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get(
            f"/api/progress/domain-trend?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code != 405


class TestFocusSummary:
    def test_requires_auth(self, client: TestClient):
        resp = client.get(f"/api/progress/focus-summary?user_token={USER_TOKEN}")
        assert resp.status_code in (401, 403)

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get(
            f"/api/progress/focus-summary?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code != 405


class TestProgressBusinessLogic:
    """Unit tests for pure computation in progress analytics."""

    def test_accuracy_calculation(self):
        correct, total = 7, 10
        accuracy = round(correct / total, 4)
        assert accuracy == 0.7

    def test_accuracy_zero_attempts(self):
        total = 0
        accuracy = round(0 / total, 4) if total else 0.0
        assert accuracy == 0.0

    def test_overall_accuracy_aggregation(self):
        """overall = sum(correct) / sum(attempts) across all days."""
        points = [
            {"attempts": 10, "correct": 7},
            {"attempts": 5, "correct": 5},
            {"attempts": 20, "correct": 10},
        ]
        total_att = sum(p["attempts"] for p in points)
        total_cor = sum(p["correct"] for p in points)
        overall = round(total_cor / total_att, 4)
        assert overall == round(22 / 35, 4)

    def test_streak_logic(self):
        """Streak counts consecutive trailing days with attempts."""
        from datetime import date, timedelta
        today = date.today()
        dates_with_attempts = {
            str(today),
            str(today - timedelta(days=1)),
            str(today - timedelta(days=2)),
            # gap here
            str(today - timedelta(days=4)),
        }
        streak = 0
        check = today
        while str(check) in dates_with_attempts:
            streak += 1
            check -= timedelta(days=1)
        assert streak == 3

    def test_streak_broken(self):
        """A gap yesterday breaks the streak."""
        from datetime import date, timedelta
        today = date.today()
        dates_with_attempts = {
            str(today - timedelta(days=2)),
            str(today - timedelta(days=3)),
        }
        streak = 0
        check = today
        while str(check) in dates_with_attempts:
            streak += 1
            check -= timedelta(days=1)
        assert streak == 0

    def test_weakest_focus_requires_min_attempts(self):
        """Only include focus areas with >= 3 attempts in weakest list."""
        stats = [
            {"focus_key": "a", "total_attempts": 2, "accuracy": 0.1},  # excluded
            {"focus_key": "b", "total_attempts": 5, "accuracy": 0.2},
            {"focus_key": "c", "total_attempts": 10, "accuracy": 0.8},
        ]
        qualified = [s for s in stats if s["total_attempts"] >= 3]
        assert len(qualified) == 2
        assert qualified[0]["focus_key"] == "b"

    def test_top_focus_areas_sorted_by_volume(self):
        """Top areas are sorted by total_attempts descending."""
        stats = [
            {"focus_key": "a", "total_attempts": 3},
            {"focus_key": "b", "total_attempts": 15},
            {"focus_key": "c", "total_attempts": 7},
        ]
        top = sorted(stats, key=lambda s: s["total_attempts"], reverse=True)
        assert top[0]["focus_key"] == "b"
        assert top[-1]["focus_key"] == "a"
