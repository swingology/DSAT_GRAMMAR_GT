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


def test_create_user_with_email_stores_email_and_returns_is_active():
    """POST /users with an optional email persists it on the row and the
    response includes is_active (defaults to True for a freshly created user).
    """
    import uuid as _uuid
    from fastapi.testclient import TestClient

    from app.main import app
    from app.database import get_db

    created = {}

    class _EmptyResult:
        def scalars(self):
            return self

        def first(self):
            return None

        def all(self):
            return []

    class FakeSession:
        async def execute(self, stmt):
            return _EmptyResult()

        def add(self, obj):
            created["user"] = obj

        async def commit(self):
            pass

        async def refresh(self, obj):
            # Mimic the column defaults a real DB insert would populate.
            obj.id = 1
            obj.role = "student"
            obj.is_active = True
            obj.user_token = _uuid.uuid4()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.post(
                "/users",
                headers=AUTH,
                json={"username": "bob", "email": "bob@example.com"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "bob@example.com"
    assert body["is_active"] is True
    assert created["user"].email == "bob@example.com"


def test_create_user_duplicate_email_rejected():
    """A second user created with an email already on file gets a 409,
    even when the username differs from the existing row.
    """
    from fastapi.testclient import TestClient

    from app.main import app
    from app.database import get_db

    class _ExistingUser:
        id = 5
        username = "carol"
        email = "dup@example.com"

    call_count = {"n": 0}

    class _Result:
        def __init__(self, found):
            self._found = found

        def scalars(self):
            return self

        def first(self):
            return self._found

        def all(self):
            return [self._found] if self._found else []

    class FakeSession:
        async def execute(self, stmt):
            call_count["n"] += 1
            # 1st execute = username duplicate check (none), 2nd = email
            # duplicate check (existing row).
            if call_count["n"] == 2:
                return _Result(_ExistingUser())
            return _Result(None)

        def add(self, obj):
            pass

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.post(
                "/users",
                headers=AUTH,
                json={"username": "newname", "email": "dup@example.com"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Email already exists"


def test_create_user_empty_email_stored_as_none():
    """Posting an empty-string email must persist NULL, not "".

    User.email is unique+nullable: a stored "" would make the second
    empty-email user fail with an IntegrityError (500) instead of a clean
    response, and "" also defeats the frontend's `email ?? username` fallback.
    """
    import uuid as _uuid
    from fastapi.testclient import TestClient

    from app.main import app
    from app.database import get_db

    created = {}

    class _EmptyResult:
        def scalars(self):
            return self

        def first(self):
            return None

        def all(self):
            return []

    class FakeSession:
        async def execute(self, stmt):
            return _EmptyResult()

        def add(self, obj):
            created["user"] = obj

        async def commit(self):
            pass

        async def refresh(self, obj):
            # Mimic the column defaults a real DB insert would populate.
            obj.id = 1
            obj.role = "student"
            obj.is_active = True
            obj.user_token = _uuid.uuid4()

    async def _override_get_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            resp = c.post(
                "/users",
                headers=AUTH,
                json={"username": "x", "email": ""},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 201
    assert created["user"].email is None
    assert resp.json()["email"] is None
