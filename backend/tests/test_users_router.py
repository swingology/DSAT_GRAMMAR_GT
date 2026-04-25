AUTH = {"X-API-Key": "admin-test-key"}
STUDENT_AUTH = {"X-API-Key": "student-test-key"}


def test_create_user_no_auth(client):
    resp = client.post("/users", json={"username": "alice"})
    assert resp.status_code == 403


def test_create_user_missing_username(client):
    resp = client.post("/users", headers=AUTH, json={})
    assert resp.status_code == 422


def test_create_user_empty_username(client):
    resp = client.post("/users", headers=AUTH, json={"username": ""})
    assert resp.status_code == 422


def test_create_user_username_too_long(client):
    resp = client.post("/users", headers=AUTH, json={"username": "x" * 101})
    assert resp.status_code == 422


def test_list_users_requires_admin(client):
    resp = client.get("/users", headers=STUDENT_AUTH)
    assert resp.status_code == 403


def test_list_users_admin(client):
    resp = client.get("/users", headers=AUTH)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_user_not_found(client):
    resp = client.get("/users/999", headers=AUTH)
    assert resp.status_code == 404


def test_get_user_no_auth(client):
    resp = client.get("/users/1")
    assert resp.status_code == 403


def test_delete_user_not_found(client):
    resp = client.delete("/users/999", headers=AUTH)
    assert resp.status_code == 404


def test_delete_user_no_auth(client):
    resp = client.delete("/users/1")
    assert resp.status_code == 403
