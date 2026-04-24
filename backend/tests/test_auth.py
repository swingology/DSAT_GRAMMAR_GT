from fastapi import FastAPI, Depends
from app.auth import admin_required, student_required

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