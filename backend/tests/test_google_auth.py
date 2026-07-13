"""Tests for Google OAuth sign-in and the JWT-aware admin_required guard.

The Google verifier is faked at its seam (app.routers.student_auth.verify_google_id_token)
so no network or real credential is needed.
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import admin_required, create_access_token, create_refresh_token
from app.database import get_db
from app.google_oauth import GoogleTokenError


class _FakeUser:
    def __init__(self, id=1, email="student@example.com", role="student", is_active=True):
        self.id = id
        self.username = f"user{id}"
        self.email = email
        self.role = role
        self.is_active = is_active
        self.password_hash = None
        self.user_token = uuid.uuid4()
        self.refresh_token = None
        self.refresh_token_expires = None
        self.created_at = datetime.now(timezone.utc)


class _Result:
    def __init__(self, user):
        self._user = user

    def scalars(self):
        return self

    def first(self):
        return self._user


class _FakeDB:
    """Minimal async session that always resolves a lookup to `user`."""

    def __init__(self, user):
        self.user = user
        self.committed = False

    async def execute(self, stmt):
        return _Result(self.user)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass

    def add(self, obj):
        pass


def _client(user):
    from app.main import app

    db = _FakeDB(user)

    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    client = TestClient(app)
    client._fake_db = db
    return client


@pytest.fixture(autouse=True)
def _clear_overrides():
    from app.main import app

    yield
    app.dependency_overrides.clear()


def _fake_verifier(monkeypatch, claims=None, error=None):
    def _verify(credential):
        if error is not None:
            raise error
        return claims

    monkeypatch.setattr("app.routers.student_auth.verify_google_id_token", _verify)


# --- POST /api/auth/google ---------------------------------------------------


def test_google_login_succeeds_for_registered_active_user(monkeypatch):
    user = _FakeUser(email="student@example.com", role="student")
    _fake_verifier(monkeypatch, claims={"email": "student@example.com", "email_verified": True})

    client = _client(user)
    r = client.post("/api/auth/google", json={"credential": "fake-credential"})

    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    # Refresh token is rotated and persisted on the user.
    assert user.refresh_token == body["refresh_token"]
    assert user.refresh_token_expires is not None
    assert client._fake_db.committed


def test_google_login_rejects_unknown_email(monkeypatch):
    _fake_verifier(monkeypatch, claims={"email": "stranger@example.com", "email_verified": True})

    client = _client(None)  # no matching user row
    r = client.post("/api/auth/google", json={"credential": "fake-credential"})

    assert r.status_code == 401
    # No account enumeration: response must not confirm the address is unregistered
    # in a way that distinguishes it from other failures beyond the generic notice.
    assert "password" not in r.json()["detail"].lower()


def test_google_login_rejects_inactive_user(monkeypatch):
    user = _FakeUser(email="student@example.com", is_active=False)
    _fake_verifier(monkeypatch, claims={"email": "student@example.com", "email_verified": True})

    client = _client(user)
    r = client.post("/api/auth/google", json={"credential": "fake-credential"})

    assert r.status_code == 403


def test_google_login_rejects_invalid_credential(monkeypatch):
    user = _FakeUser()
    _fake_verifier(monkeypatch, error=GoogleTokenError("Token expired"))

    client = _client(user)
    r = client.post("/api/auth/google", json={"credential": "expired-or-wrong-audience"})

    assert r.status_code == 401
    # A bad credential must never mint tokens.
    assert "access_token" not in r.json()


# NOTE: the endpoint matches the email case-insensitively (func.lower on both sides).
# That is deliberately NOT asserted here — _FakeDB resolves any lookup to its user
# regardless of the WHERE clause, so such a test would pass even if the query were
# case-sensitive. Proving it needs a real DB; covered in Phase 4 live QA.


# --- verifier hardening ------------------------------------------------------


def test_verifier_rejects_unverified_email(monkeypatch):
    """An unverified Google email must not be accepted as an identity."""
    from app import google_oauth

    monkeypatch.setattr(
        google_oauth.id_token,
        "verify_oauth2_token",
        lambda *a, **kw: {
            "iss": "https://accounts.google.com",
            "email": "victim@example.com",
            "email_verified": False,
        },
    )

    with pytest.raises(GoogleTokenError, match="not verified"):
        google_oauth.verify_google_id_token("credential")


def test_verifier_rejects_untrusted_issuer(monkeypatch):
    from app import google_oauth

    monkeypatch.setattr(
        google_oauth.id_token,
        "verify_oauth2_token",
        lambda *a, **kw: {
            "iss": "https://evil.example.com",
            "email": "victim@example.com",
            "email_verified": True,
        },
    )

    with pytest.raises(GoogleTokenError, match="issuer"):
        google_oauth.verify_google_id_token("credential")


def test_verifier_wraps_google_value_error(monkeypatch):
    from app import google_oauth

    def _boom(*a, **kw):
        raise ValueError("Wrong audience")

    monkeypatch.setattr(google_oauth.id_token, "verify_oauth2_token", _boom)

    with pytest.raises(GoogleTokenError, match="Wrong audience"):
        google_oauth.verify_google_id_token("credential")


# --- GET /api/auth/me --------------------------------------------------------


def test_me_returns_user_token(monkeypatch):
    user = _FakeUser(id=7, role="student")
    client = _client(user)
    token = create_access_token(user.id, user.role)

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 200
    assert r.json()["user_token"] == str(user.user_token)


# --- upgraded admin_required -------------------------------------------------

guard_app = FastAPI()


@guard_app.get("/guarded")
async def guarded(actor: str = Depends(admin_required)):
    return {"actor": actor}


def _guard_client(user):
    db = _FakeDB(user)

    async def _override_get_db():
        yield db

    guard_app.dependency_overrides[get_db] = _override_get_db
    return TestClient(guard_app)


@pytest.fixture(autouse=True)
def _clear_guard_overrides():
    yield
    guard_app.dependency_overrides.clear()


def test_admin_required_accepts_legacy_api_key():
    client = _guard_client(None)
    r = client.get("/guarded", headers={"X-API-Key": "admin-test-key"})

    assert r.status_code == 200
    # Legacy callers still get the raw key back, which the audit trail persists.
    assert r.json()["actor"] == "admin-test-key"


def test_admin_required_accepts_admin_jwt():
    user = _FakeUser(id=3, email="boss@example.com", role="admin")
    client = _guard_client(user)
    token = create_access_token(user.id, "admin")

    r = client.get("/guarded", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 200
    # Audit trail records who acted, not an opaque key.
    assert r.json()["actor"] == "jwt:boss@example.com"


def test_admin_required_403s_student_jwt():
    user = _FakeUser(id=4, email="kid@example.com", role="student")
    client = _guard_client(user)
    token = create_access_token(user.id, "student")

    r = client.get("/guarded", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 403


def test_admin_required_403s_inactive_admin_jwt():
    user = _FakeUser(id=5, email="ex@example.com", role="admin", is_active=False)
    client = _guard_client(user)
    token = create_access_token(user.id, "admin")

    r = client.get("/guarded", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 403


def test_admin_required_rejects_refresh_token_as_access():
    user = _FakeUser(id=6, email="boss@example.com", role="admin")
    client = _guard_client(user)
    refresh = create_refresh_token(user.id)

    r = client.get("/guarded", headers={"Authorization": f"Bearer {refresh}"})

    assert r.status_code == 401


def test_admin_required_still_403s_bad_key():
    client = _guard_client(None)
    r = client.get("/guarded", headers={"X-API-Key": "wrong-key"})

    assert r.status_code == 403


# --- admin seed (O-07) -------------------------------------------------------
#
# The seed swallows exceptions so a DB outage can't take the API down, which also
# means a logic bug would fail silently. These cover it directly.


class _SeedDB(_FakeDB):
    def __init__(self, user):
        super().__init__(user)
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def _patch_session(monkeypatch, db):
    class _Ctx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr("app.database.async_session", lambda: _Ctx())


class _SeedSettings:
    admin_seed_email = "boss@example.com"
    admin_seed_username = "boss"


@pytest.mark.asyncio
async def test_seed_creates_admin_when_absent(monkeypatch):
    from app.main import _seed_admin_user

    db = _SeedDB(None)  # no existing user, and no username collision
    _patch_session(monkeypatch, db)

    await _seed_admin_user(_SeedSettings())

    assert len(db.added) == 1
    created = db.added[0]
    assert created.email == "boss@example.com"
    assert created.role == "admin"
    assert created.is_active is True
    assert created.password_hash is None  # Google-only account
    assert db.committed


@pytest.mark.asyncio
async def test_seed_promotes_existing_inactive_non_admin(monkeypatch):
    from app.main import _seed_admin_user

    existing = _FakeUser(email="boss@example.com", role="student", is_active=False)
    db = _SeedDB(existing)
    _patch_session(monkeypatch, db)

    await _seed_admin_user(_SeedSettings())

    assert existing.role == "admin"
    assert existing.is_active is True
    assert db.added == []  # promoted in place, not duplicated
    assert db.committed


@pytest.mark.asyncio
async def test_seed_is_idempotent_for_existing_admin(monkeypatch):
    from app.main import _seed_admin_user

    existing = _FakeUser(email="boss@example.com", role="admin", is_active=True)
    db = _SeedDB(existing)
    _patch_session(monkeypatch, db)

    await _seed_admin_user(_SeedSettings())

    assert db.added == []
    assert db.committed is False  # nothing to change → no write
