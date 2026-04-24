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
    client = TestClient(app)
    response = client.get("/admin-test", headers={"X-API-Key": "admin-test-key"})
    assert response.status_code == 200


def test_admin_with_invalid_key():
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/admin-test", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403


def test_admin_with_no_key():
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/admin-test")
    assert response.status_code == 403


def test_student_with_valid_key():
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/student-test", headers={"X-API-Key": "student-test-key"})
    assert response.status_code == 200


def test_student_with_admin_key():
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/student-test", headers={"X-API-Key": "admin-test-key"})
    assert response.status_code == 403