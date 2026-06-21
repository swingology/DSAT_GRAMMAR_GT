"""Tests for Phase 4: Adaptive Module 2 Routing."""
import pytest
from fastapi.testclient import TestClient

AUTH = {"X-API-Key": "student-test-key"}
USER_TOKEN = "00000000-0000-0000-0000-000000000001"
FAKE_SESSION_ID = "00000000-0000-0000-0000-000000000099"


class TestRoutingAlgorithm:
    """Unit tests for _route_module_2 routing logic."""

    def _route(self, accuracy: float, duration: int | None = None):
        from app.routers.student import _route_module_2
        return _route_module_2(accuracy, duration)

    def test_exactly_70_routes_higher(self):
        diff, rationale = self._route(0.70)
        assert diff == "higher"

    def test_above_70_routes_higher(self):
        diff, _ = self._route(0.85)
        assert diff == "higher"

    def test_perfect_score_routes_higher(self):
        diff, _ = self._route(1.0)
        assert diff == "higher"

    def test_below_70_routes_lower(self):
        diff, _ = self._route(0.69)
        assert diff == "lower"

    def test_zero_accuracy_routes_lower(self):
        diff, _ = self._route(0.0)
        assert diff == "lower"

    def test_rationale_included_for_higher(self):
        _, rationale = self._route(0.75)
        assert "higher" in rationale.lower()
        assert "70%" in rationale

    def test_rationale_included_for_lower(self):
        _, rationale = self._route(0.50)
        assert "lower" in rationale.lower()
        assert "70%" in rationale

    def test_duration_accepted_without_affecting_routing(self):
        diff1, _ = self._route(0.80, duration=600)
        diff2, _ = self._route(0.80, duration=None)
        assert diff1 == diff2 == "higher"

    def test_boundary_just_below_70(self):
        diff, _ = self._route(0.699)
        assert diff == "lower"

    def test_boundary_just_above_70(self):
        diff, _ = self._route(0.701)
        assert diff == "higher"


class TestModule1CompleteEndpoint:
    def test_requires_auth(self, client: TestClient):
        resp = client.post(
            "/api/test-session/module-1-complete",
            json={
                "user_token": USER_TOKEN,
                "module_1_accuracy": 0.75,
            },
        )
        assert resp.status_code in (401, 403)

    def test_user_not_found_returns_404(self, client: TestClient):
        resp = client.post(
            "/api/test-session/module-1-complete",
            json={"user_token": USER_TOKEN, "module_1_accuracy": 0.75},
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_endpoint_exists(self, client: TestClient):
        resp = client.post(
            "/api/test-session/module-1-complete",
            json={"user_token": USER_TOKEN, "module_1_accuracy": 0.75},
            headers=AUTH,
        )
        assert resp.status_code != 405

    def test_missing_accuracy_rejected(self, client: TestClient):
        resp = client.post(
            "/api/test-session/module-1-complete",
            json={"user_token": USER_TOKEN},
            headers=AUTH,
        )
        assert resp.status_code == 422


class TestModule2BlueprintEndpoint:
    def test_requires_auth(self, client: TestClient):
        resp = client.get(
            f"/api/test-session/{FAKE_SESSION_ID}/module-2-blueprint"
            f"?user_token={USER_TOKEN}"
        )
        assert resp.status_code in (401, 403)

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get(
            f"/api/test-session/{FAKE_SESSION_ID}/module-2-blueprint"
            f"?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code != 405

    def test_invalid_uuid_rejected(self, client: TestClient):
        resp = client.get(
            "/api/test-session/not-a-uuid/module-2-blueprint"
            f"?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code in (404, 422)

    def test_nonexistent_session_returns_404(self, client: TestClient):
        resp = client.get(
            f"/api/test-session/{FAKE_SESSION_ID}/module-2-blueprint"
            f"?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        # Either 404 (user not found) or 404 (session not found) — both acceptable
        assert resp.status_code == 404


class TestSessionHistoryEndpoint:
    def test_requires_auth(self, client: TestClient):
        resp = client.get(f"/api/test-session/history?user_token={USER_TOKEN}")
        assert resp.status_code in (401, 403)

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get(
            f"/api/test-session/history?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code != 405

    def test_user_not_found_returns_404(self, client: TestClient):
        resp = client.get(
            f"/api/test-session/history?user_token={USER_TOKEN}",
            headers=AUTH,
        )
        assert resp.status_code == 404
