import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Force test env before any app imports — use assignment, not setdefault
os.environ["DATABASE_URL"] = "postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test"
os.environ["ADMIN_API_KEYS"] = "admin-test-key"
os.environ["STUDENT_API_KEYS"] = "student-test-key"

from fastapi.testclient import TestClient


class _ScalarResult:
    def scalars(self):
        return self

    def all(self):
        return []

    def first(self):
        return None

    def unique(self):
        return self


class _MockSession(AsyncMock):
    async def get(self, model, pk):
        return None

    async def execute(self, stmt):
        return _ScalarResult()

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    def add(self, obj):
        pass


@pytest.fixture
def client():
    from app.main import app
    from app.database import get_db

    mock_db = _MockSession()

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()