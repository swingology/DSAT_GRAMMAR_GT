"""Phase 9: Generation Quality Analytics endpoint tests."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

AUTH = {"X-API-Key": "admin-test-key"}


# ---------------------------------------------------------------------------
# GET /admin/analytics/generation
# ---------------------------------------------------------------------------

def test_generation_analytics_returns_shape(client):
    resp = client.get("/admin/analytics/generation", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "days" in data
    assert "generated_count" in data
    assert "reviewed_count" in data
    assert "approved_count" in data
    assert "rejected_count" in data
    assert "failed_count" in data
    assert "acceptance_rate" in data
    assert "copy_risk_failures" in data
    assert "avg_reviewer_disagreement" in data
    assert "by_generator_model" in data
    assert "rejection_reasons" in data
    assert isinstance(data["by_generator_model"], list)
    assert isinstance(data["rejection_reasons"], list)


def test_generation_analytics_defaults_to_30_days(client):
    resp = client.get("/admin/analytics/generation", headers=AUTH)
    assert resp.json()["days"] == 30


def test_generation_analytics_custom_days(client):
    resp = client.get("/admin/analytics/generation?days=7", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["days"] == 7


def test_generation_analytics_empty_db_zeros(client):
    resp = client.get("/admin/analytics/generation", headers=AUTH)
    data = resp.json()
    assert data["generated_count"] == 0
    assert data["approved_count"] == 0
    assert data["rejected_count"] == 0
    assert data["acceptance_rate"] == 0.0
    assert data["copy_risk_failures"] == 0


def test_generation_analytics_requires_auth(client):
    resp = client.get("/admin/analytics/generation")
    assert resp.status_code == 403


def test_generation_analytics_invalid_days(client):
    resp = client.get("/admin/analytics/generation?days=0", headers=AUTH)
    assert resp.status_code == 422


def test_generation_analytics_days_upper_bound(client):
    resp = client.get("/admin/analytics/generation?days=365", headers=AUTH)
    assert resp.status_code == 200


def test_generation_analytics_days_over_limit(client):
    resp = client.get("/admin/analytics/generation?days=366", headers=AUTH)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /admin/analytics/review
# ---------------------------------------------------------------------------

def test_review_analytics_returns_shape(client):
    resp = client.get("/admin/analytics/review", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "days" in data
    assert "by_reviewer_model" in data
    assert "token_usage" in data
    assert isinstance(data["by_reviewer_model"], list)
    assert isinstance(data["token_usage"], list)


def test_review_analytics_requires_auth(client):
    resp = client.get("/admin/analytics/review")
    assert resp.status_code == 403


def test_review_analytics_empty_db(client):
    resp = client.get("/admin/analytics/review", headers=AUTH)
    data = resp.json()
    assert data["by_reviewer_model"] == []
    assert data["token_usage"] == []


def test_review_analytics_reviewer_model_fields(client):
    """Even with empty data the shape must be valid."""
    resp = client.get("/admin/analytics/review", headers=AUTH)
    assert resp.status_code == 200
    for item in resp.json()["by_reviewer_model"]:
        assert "provider_name" in item
        assert "model_name" in item
        assert "review_count" in item
        assert "override_rate" in item
        assert "total_overrides" in item


# ---------------------------------------------------------------------------
# GET /admin/analytics/batches
# ---------------------------------------------------------------------------

def test_batch_analytics_returns_shape(client):
    resp = client.get("/admin/analytics/batches", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "days" in data
    assert "aggregates" in data
    assert "token_usage" in data
    agg = data["aggregates"]
    assert "batch_count" in agg
    assert "total_requested" in agg
    assert "total_created" in agg
    assert "total_accepted" in agg
    assert "total_rejected" in agg
    assert "total_failed" in agg
    assert "avg_review_latency_ms" in agg


def test_batch_analytics_requires_auth(client):
    resp = client.get("/admin/analytics/batches")
    assert resp.status_code == 403


def test_batch_analytics_empty_db_zeros(client):
    resp = client.get("/admin/analytics/batches", headers=AUTH)
    agg = resp.json()["aggregates"]
    assert agg["batch_count"] == 0
    assert agg["total_requested"] == 0
    assert agg["avg_review_latency_ms"] is None


# ---------------------------------------------------------------------------
# GET /admin/analytics/trends
# ---------------------------------------------------------------------------

def test_trend_analytics_returns_shape(client):
    resp = client.get("/admin/analytics/trends", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "days" in data
    assert "granularity" in data
    assert "points" in data
    assert isinstance(data["points"], list)


def test_trend_analytics_default_granularity(client):
    resp = client.get("/admin/analytics/trends", headers=AUTH)
    assert resp.json()["granularity"] == "week"


def test_trend_analytics_day_granularity(client):
    resp = client.get("/admin/analytics/trends?granularity=day", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["granularity"] == "day"


def test_trend_analytics_invalid_granularity(client):
    resp = client.get("/admin/analytics/trends?granularity=month", headers=AUTH)
    assert resp.status_code == 422


def test_trend_analytics_requires_auth(client):
    resp = client.get("/admin/analytics/trends")
    assert resp.status_code == 403


def test_trend_analytics_empty_db_empty_points(client):
    resp = client.get("/admin/analytics/trends", headers=AUTH)
    assert resp.json()["points"] == []


def test_trend_analytics_point_fields(client):
    resp = client.get("/admin/analytics/trends", headers=AUTH)
    for pt in resp.json()["points"]:
        assert "period" in pt
        assert "generated" in pt
        assert "approved" in pt
        assert "rejected" in pt
        assert "acceptance_rate" in pt


def test_trend_analytics_days_below_minimum(client):
    resp = client.get("/admin/analytics/trends?days=6", headers=AUTH)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /admin/analytics/export
# ---------------------------------------------------------------------------

def test_export_analytics_returns_shape(client):
    resp = client.get("/admin/analytics/export", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "days" in data
    assert "exported_at" in data
    assert "question_count" in data
    assert "questions" in data
    assert isinstance(data["questions"], list)


def test_export_analytics_requires_auth(client):
    resp = client.get("/admin/analytics/export")
    assert resp.status_code == 403


def test_export_analytics_empty_db(client):
    resp = client.get("/admin/analytics/export", headers=AUTH)
    data = resp.json()
    assert data["question_count"] == 0
    assert data["questions"] == []


def test_export_analytics_custom_days(client):
    resp = client.get("/admin/analytics/export?days=90", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["days"] == 90


def test_export_analytics_question_fields(client):
    resp = client.get("/admin/analytics/export", headers=AUTH)
    for q in resp.json()["questions"]:
        assert "question_id" in q
        assert "practice_status" in q
        assert "overlap_status" in q
        assert "generator_provider" in q
        assert "consensus_verdict" in q
