def test_student_recall_requires_auth(client):
    resp = client.get("/api/questions")
    assert resp.status_code == 403


def test_student_recall_with_auth(client):
    resp = client.get("/api/questions", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_student_submit_invalid_uuid(client):
    resp = client.post("/api/submit", json={
        "user_id": 1,
        "question_id": "not-a-uuid",
        "is_correct": True,
        "selected_option_label": "A",
    }, headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 400


def test_student_submit_not_found(client):
    resp = client.post("/api/submit", json={
        "user_id": 1,
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