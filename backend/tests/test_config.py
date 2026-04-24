import os
import pytest


def test_settings_loads_from_env():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/testdb"
    os.environ["ADMIN_API_KEYS"] = "key1,key2"
    os.environ["STUDENT_API_KEYS"] = "skey1"
    from app.config import Settings
    s = Settings()
    assert "key1" in s.admin_api_key_list
    assert s.database_url == "postgresql+asyncpg://test:test@localhost:5432/testdb"


def test_settings_default_values():
    os.environ.pop("ADMIN_API_KEYS", None)
    os.environ.pop("STUDENT_API_KEYS", None)
    from app.config import Settings
    s = Settings()
    assert s.default_annotation_provider == "anthropic"
    assert s.rules_version.startswith("rules_agent")