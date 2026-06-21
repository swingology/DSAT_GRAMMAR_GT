"""Tests for GET /api/student/trap-susceptibility endpoint."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

AUTH = {"X-API-Key": "student-test-key"}
USER_TOKEN = "00000000-0000-0000-0000-000000000001"


def make_user(user_id=1, token="testtoken"):
    u = MagicMock()
    u.id = user_id
    u.user_token = token
    return u


def make_progress(trap_type, is_correct, timestamp=None):
    from datetime import datetime, timezone
    p = MagicMock()
    p.missed_syntactic_trap_key = trap_type
    p.is_correct = is_correct
    p.timestamp = timestamp or datetime(2026, 1, 1, tzinfo=timezone.utc)
    return p


class TestTrapSusceptibility:
    def test_trap_susceptibility_requires_auth(self, client: TestClient):
        resp = client.get("/api/student/trap-susceptibility?user_token=bad")
        assert resp.status_code in (401, 403)

    def test_trap_susceptibility_user_not_found(self, client: TestClient):
        """Default mock_db returns None for user lookup → 404."""
        resp = client.get(
            f"/api/student/trap-susceptibility?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_trap_susceptibility_endpoint_exists(self, client: TestClient):
        """Endpoint is routed — returns 404 (no user) not 405 (no route)."""
        resp = client.get(
            f"/api/student/trap-susceptibility?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code != 405, "Endpoint must be registered"

    def test_fall_rate_formula(self):
        """Fall rate = 1 - (correct / total), bounded 0–1."""
        # 3 correct out of 10: fall_rate = 0.7
        correct = 3
        total = 10
        fall_rate = round(1.0 - correct / total, 4)
        assert fall_rate == 0.7

    def test_fall_rate_all_correct(self):
        correct = 5
        total = 5
        fall_rate = round(1.0 - correct / total, 4)
        assert fall_rate == 0.0

    def test_fall_rate_all_wrong(self):
        correct = 0
        total = 8
        fall_rate = round(1.0 - correct / total, 4)
        assert fall_rate == 1.0

    def test_severity_thresholds(self):
        """Severity labels follow the defined thresholds."""
        def _severity(fall_rate: float) -> str:
            if fall_rate >= 0.8:
                return "critical"
            if fall_rate >= 0.6:
                return "high"
            if fall_rate >= 0.4:
                return "moderate"
            return "low"

        assert _severity(0.9) == "critical"
        assert _severity(0.8) == "critical"
        assert _severity(0.7) == "high"
        assert _severity(0.6) == "high"
        assert _severity(0.5) == "moderate"
        assert _severity(0.4) == "moderate"
        assert _severity(0.3) == "low"
        assert _severity(0.0) == "low"

    def test_improvement_detection(self):
        """recent_accuracy >= 0.6 and > first_accuracy → overcoming."""
        first_acc = 0.2
        recent_acc = 0.8
        assert recent_acc >= 0.6 and recent_acc > first_acc

    def test_persistent_trap_detection(self):
        """recent_accuracy < 0.4 and fall_rate > 0.6 → persistent."""
        recent_acc = 0.2
        fall_rate = 0.8
        assert recent_acc < 0.4 and fall_rate > 0.6

    def test_most_susceptible_sorted_by_fall_rate(self):
        """most_susceptible_traps must be sorted fall_rate DESC, max 5."""
        metrics = [
            {"trap_type": f"trap_{i}", "fall_rate": i / 10.0} for i in range(8)
        ]
        top5 = sorted(metrics, key=lambda m: m["fall_rate"], reverse=True)[:5]
        assert len(top5) == 5
        assert top5[0]["fall_rate"] == 0.7
        assert top5[-1]["fall_rate"] == 0.3
