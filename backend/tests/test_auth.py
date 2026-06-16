import bcrypt
from fastapi import Depends, FastAPI

from app.auth import (
    admin_required,
    hash_password,
    student_required,
    verify_and_update_password,
    verify_password,
)

app = FastAPI()


@app.get("/admin-test", dependencies=[Depends(admin_required)])
def admin_endpoint():
    return {"ok": True}


@app.get("/student-test", dependencies=[Depends(student_required)])
def student_endpoint():
    return {"ok": True}


def test_admin_with_valid_key():
    from fastapi.testclient import TestClient
    # Use admin-test-key which matches the conftest env var
    import os
    admin_key = os.environ.get("ADMIN_API_KEYS", "admin-test-key").split(",")[0].strip()
    c = TestClient(app)
    response = c.get("/admin-test", headers={"X-API-Key": admin_key})
    assert response.status_code == 200


def test_admin_with_invalid_key():
    from fastapi.testclient import TestClient
    c = TestClient(app)
    response = c.get("/admin-test", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403


def test_admin_with_no_key():
    from fastapi.testclient import TestClient
    c = TestClient(app)
    response = c.get("/admin-test")
    assert response.status_code == 403


def test_student_with_valid_key():
    from fastapi.testclient import TestClient
    import os
    student_key = os.environ.get("STUDENT_API_KEYS", "student-test-key").split(",")[0].strip()
    c = TestClient(app)
    response = c.get("/student-test", headers={"X-API-Key": student_key})
    assert response.status_code == 200


def test_student_with_admin_key():
    from fastapi.testclient import TestClient
    import os
    admin_key = os.environ.get("ADMIN_API_KEYS", "admin-test-key").split(",")[0].strip()
    c = TestClient(app)
    response = c.get("/student-test", headers={"X-API-Key": admin_key})
    assert response.status_code == 403


def test_hash_password_uses_argon2_and_verifies():
    hashed = hash_password("correct horse battery staple")

    assert hashed.startswith("$argon2")
    assert verify_password("correct horse battery staple", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct horse battery staple")

    assert not verify_password("wrong password", hashed)


def test_verify_password_accepts_legacy_bcrypt_hash():
    legacy_hash = bcrypt.hashpw(b"legacy-password", bcrypt.gensalt()).decode("utf-8")

    for prefix in ("$2a$", "$2b$", "$2y$"):
        prefixed_hash = prefix + legacy_hash[4:]
        assert verify_password("legacy-password", prefixed_hash)


def test_verify_and_update_password_returns_argon2_for_legacy_bcrypt():
    legacy_hash = bcrypt.hashpw(b"legacy-password", bcrypt.gensalt()).decode("utf-8")

    verified, updated_hash = verify_and_update_password("legacy-password", legacy_hash)

    assert verified is True
    assert updated_hash is not None
    assert updated_hash.startswith("$argon2")
    assert verify_password("legacy-password", updated_hash)
