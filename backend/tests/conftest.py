import os
import pytest

# Force test env before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test")
os.environ.setdefault("ADMIN_API_KEYS", "admin-test-key")
os.environ.setdefault("STUDENT_API_KEYS", "student-test-key")

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)