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