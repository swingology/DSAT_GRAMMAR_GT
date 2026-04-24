def test_recall_requires_auth(client):
    resp = client.get("/questions/recall")
    assert resp.status_code == 403


def test_recall_with_auth(client):
    resp = client.get("/questions/recall", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_question_detail_invalid_uuid(client):
    resp = client.get("/questions/not-a-uuid", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 400


def test_question_detail_not_found(client):
    resp = client.get("/questions/00000000-0000-0000-0000-000000000000", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 404


def test_question_versions_invalid_uuid(client):
    resp = client.get("/questions/not-a-uuid/versions", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 400


def test_question_versions_not_found(client):
    resp = client.get("/questions/00000000-0000-0000-0000-000000000000/versions", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 404