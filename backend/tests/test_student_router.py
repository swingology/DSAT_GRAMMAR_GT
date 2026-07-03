def test_student_recall_requires_auth(client):
    resp = client.get("/api/questions")
    assert resp.status_code == 403


def test_student_recall_with_auth(client):
    resp = client.get("/api/questions", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "inventory" in data
    assert isinstance(data["items"], list)


def test_student_submit_invalid_uuid(client):
    resp = client.post("/api/submit", json={
        "user_token": "00000000-0000-0000-0000-000000000001",
        "question_id": "not-a-uuid",
        "is_correct": True,
        "selected_option_label": "A",
    }, headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 400


def test_student_submit_not_found(client):
    resp = client.post("/api/submit", json={
        "user_token": "00000000-0000-0000-0000-000000000001",
        "question_id": "00000000-0000-0000-0000-000000000000",
        "is_correct": True,
        "selected_option_label": "A",
    }, headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 404


def test_student_stats_empty(client):
    resp = client.get("/api/stats/99999", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_answered"] == 0


def test_api_users_empty_username_rejected(client):
    resp = client.post(
        "/users",
        json={"username": ""},
        headers={"X-API-Key": "admin-test-key"},
    )
    assert resp.status_code == 422


def test_api_users_username_too_long_rejected(client):
    resp = client.post(
        "/users",
        json={"username": "x" * 101},
        headers={"X-API-Key": "admin-test-key"},
    )
    assert resp.status_code == 422


def test_student_stats_accepts_admin_key(client):
    resp = client.get("/api/stats/99999", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 200


def test_student_stats_still_accepts_student_key(client):
    resp = client.get("/api/stats/99999", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200


def test_student_activity_empty(client):
    resp = client.get("/api/stats/1/activity", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_student_activity_accepts_admin_key(client):
    resp = client.get("/api/stats/1/activity", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 200


def test_student_activity_returns_daily_counts(monkeypatch):
    from datetime import date
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    class _Row:
        def __init__(self, day, count):
            self.day = day
            self.count = count

    rows = [_Row(date(2026, 6, 30), 7), _Row(date(2026, 7, 1), 3)]

    class _Result:
        def all(self):
            return rows

    class FakeSession:
        async def execute(self, stmt):
            return _Result()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.get("/api/stats/1/activity", headers={"X-API-Key": "student-test-key"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    assert resp.json() == [
        {"date": "2026-06-30", "count": 7},
        {"date": "2026-07-01", "count": 3},
    ]
