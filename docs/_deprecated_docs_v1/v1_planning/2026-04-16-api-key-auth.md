# API Key Authentication Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add API key authentication to all FastAPI routes so no unauthenticated caller can read questions, approve jobs, trigger generation, or run searches.

**Architecture:** A single FastAPI dependency (`require_api_key`) reads the `X-API-Key` header and compares it against a secret loaded from `settings.api_key`. The dependency is applied at the router level in `main.py` via `dependencies=[]`. `/health` remains public for uptime monitoring. The API key is configured via `.env` — no migration or DB change needed.

**Tech Stack:** FastAPI `Depends`, `HTTPException`, `pydantic-settings`, pytest `TestClient`.

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `FULL_PLAN/backend/app/auth.py` | `require_api_key` dependency + `APIKeyMissing`/`APIKeyInvalid` exceptions |
| Modify | `FULL_PLAN/backend/app/config.py` | Add `api_key: str` field |
| Modify | `FULL_PLAN/backend/app/main.py` | Apply `require_api_key` to all routers except `/health` |
| Create | `FULL_PLAN/backend/.env.example` | Document `API_KEY` alongside other vars (file does not exist yet) |
| Create | `FULL_PLAN/backend/tests/test_auth.py` | Auth tests for each protected router |

---

## Chunk 1: Dependency + Config

### Task 1: Add `api_key` to Settings

**Files:**
- Modify: `FULL_PLAN/backend/app/config.py`

- [ ] **Step 1: Write the failing test**

In a new file `FULL_PLAN/backend/tests/test_auth.py`:

```python
"""
Tests for API key authentication.
All routes except /health require X-API-Key header.
"""
import pytest
from contextlib import asynccontextmanager
from unittest.mock import patch, MagicMock

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import require_api_key

VALID_KEY = "test-secret-key"


def test_settings_has_api_key_field():
    """Settings must expose api_key."""
    from app.config import Settings
    # Construct with explicit value (avoids reading .env)
    s = Settings(
        supabase_db_url="postgresql://x",
        api_key="my-secret",
    )
    assert s.api_key == "my-secret"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd FULL_PLAN/backend
uv run pytest tests/test_auth.py::test_settings_has_api_key_field -v
```

Expected: FAIL — `Settings` has no `api_key` field.

- [ ] **Step 3: Add `api_key = ""` to `conftest.py` mock_settings** ⚠️ MANDATORY — do not skip

The autouse `mock_settings` fixture in `FULL_PLAN/backend/tests/conftest.py` sets up a `MagicMock` for settings. Without an explicit `api_key` attribute, `get_settings().api_key` returns a truthy `MagicMock` object and auth would be "enabled" in every test — causing 401s across the entire test suite once `require_api_key` is wired in. Add `fake.api_key = ""` after `fake.pass2_max_tokens = 4096` to disable auth by default in tests:

```python
    fake.pass2_max_tokens = 4096
    fake.api_key = ""          # disable auth by default in all tests
```

- [ ] **Step 4: Add `api_key` to Settings**

In `FULL_PLAN/backend/app/config.py`, add after `pass2_max_tokens`:

```python
    # Auth
    api_key: str = ""
```

- [ ] **Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_auth.py::test_settings_has_api_key_field -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add FULL_PLAN/backend/app/config.py FULL_PLAN/backend/tests/conftest.py FULL_PLAN/backend/tests/test_auth.py
git commit -m "feat: add api_key field to Settings"
```

---

### Task 2: Create `app/auth.py` — the dependency

**Files:**
- Create: `FULL_PLAN/backend/app/auth.py`
- Modify: `FULL_PLAN/backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests for the dependency**

Add to `FULL_PLAN/backend/tests/test_auth.py`:

```python
def _make_protected_app(configured_key: str = VALID_KEY):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/protected", dependencies=[Depends(require_api_key)])
    async def protected():
        return {"ok": True}

    return app


def test_valid_key_allows_request():
    app = _make_protected_app()
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.api_key = VALID_KEY
        with TestClient(app) as c:
            resp = c.get("/protected", headers={"X-API-Key": VALID_KEY})
    assert resp.status_code == 200


def test_missing_key_returns_401():
    app = _make_protected_app()
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.api_key = VALID_KEY
        with TestClient(app) as c:
            resp = c.get("/protected")
    assert resp.status_code == 401
    assert "X-API-Key" in resp.json()["detail"]


def test_wrong_key_returns_403():
    app = _make_protected_app()
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.api_key = VALID_KEY
        with TestClient(app) as c:
            resp = c.get("/protected", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 403


def test_empty_configured_key_disables_auth():
    """If api_key is empty string in settings, auth is disabled (dev mode)."""
    app = _make_protected_app()
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.api_key = ""
        with TestClient(app) as c:
            resp = c.get("/protected")
    assert resp.status_code == 200


def test_no_auth_on_wrong_header_name_returns_401():
    app = _make_protected_app()
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.api_key = VALID_KEY
        with TestClient(app) as c:
            resp = c.get("/protected", headers={"Authorization": f"Bearer {VALID_KEY}"})
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_auth.py -k "not test_settings" -v
```

Expected: FAIL — `require_api_key` not defined.

- [ ] **Step 3: Implement `app/auth.py`**

Create `FULL_PLAN/backend/app/auth.py`:

```python
"""
API key authentication dependency.

All protected routes use: dependencies=[Depends(require_api_key)]

If settings.api_key is empty (default), auth is disabled — safe for local dev
without setting up a key. In production, set API_KEY in .env.
"""
from fastapi import Header, HTTPException

from app.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    configured = settings.api_key

    # Dev mode: api_key not set → skip auth entirely
    if not configured:
        return

    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
        )
    if x_api_key != configured:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_auth.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add FULL_PLAN/backend/app/auth.py FULL_PLAN/backend/tests/test_auth.py
git commit -m "feat: add require_api_key FastAPI dependency"
```

---

## Chunk 2: Apply to All Routers + Integration Tests

### Task 3: Wire `require_api_key` into `main.py`

**Files:**
- Modify: `FULL_PLAN/backend/app/main.py`
- Modify: `FULL_PLAN/backend/tests/test_auth.py`

- [ ] **Step 1: Write integration tests for each router**

Add to `FULL_PLAN/backend/tests/test_auth.py`:

```python
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers import ingest, jobs, questions, search
from app.routers import ontology as ontology_router
from app.routers import generate


def _make_full_app(api_key: str = VALID_KEY):
    """Spin up the real app with all routers, mocked DB/settings."""
    @asynccontextmanager
    async def lifespan(app):
        app.state.ontology = {}
        yield

    app = FastAPI(lifespan=lifespan)
    deps = [Depends(require_api_key)]
    app.include_router(ingest.router,          prefix="/ingest",    dependencies=deps)
    app.include_router(jobs.router,            prefix="/jobs",      dependencies=deps)
    app.include_router(questions.router,       prefix="/questions", dependencies=deps)
    app.include_router(ontology_router.router, prefix="/ontology",  dependencies=deps)
    app.include_router(search.router,          prefix="/search",    dependencies=deps)
    app.include_router(generate.router,        prefix="/generate",  dependencies=deps)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


PROTECTED_ROUTES = [
    ("GET",  "/questions",         {}),
    ("GET",  "/ontology/domains",  {}),
    ("GET",  "/jobs",              {}),
]


@pytest.mark.parametrize("method,path,body", PROTECTED_ROUTES)
def test_protected_routes_require_key(method, path, body):
    app = _make_full_app(api_key=VALID_KEY)
    with patch("app.auth.get_settings") as mock_s:
        mock_s.return_value.api_key = VALID_KEY
        with patch("app.routers.questions.get_pool"), \
             patch("app.routers.ontology.get_pool"), \
             patch("app.routers.jobs.get_pool"):
            with TestClient(app) as c:
                resp = getattr(c, method.lower())(path)
    assert resp.status_code == 401, f"{method} {path} should require auth"


def test_health_is_public():
    app = _make_full_app(api_key=VALID_KEY)
    with patch("app.auth.get_settings") as mock_s:
        mock_s.return_value.api_key = VALID_KEY
        with TestClient(app) as c:
            resp = c.get("/health")
    assert resp.status_code == 200


def test_valid_key_reaches_questions_router():
    """With a valid key, requests reach the router (may return 500 from missing DB — that's OK)."""
    app = _make_full_app(api_key=VALID_KEY)
    with patch("app.auth.get_settings") as mock_s:
        mock_s.return_value.api_key = VALID_KEY
        pool = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            fetch=AsyncMock(return_value=[])
        ))
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("app.routers.questions.get_pool", return_value=pool):
            with TestClient(app) as c:
                resp = c.get("/questions", headers={"X-API-Key": VALID_KEY})
    # 200 or any non-401/403 means auth passed
    assert resp.status_code not in (401, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_auth.py -k "protected_routes or health_is_public or valid_key_reaches" -v
```

Expected: FAIL — `/health` may return 200 but protected routes won't return 401 (no auth yet).

- [ ] **Step 3: Apply dependency to all routers in `main.py`**

Three targeted edits to `FULL_PLAN/backend/app/main.py`:

**Edit A** — add `Depends` and `require_api_key` imports (change the existing import block):

```python
# Before:
from fastapi import FastAPI

# After:
from fastapi import Depends, FastAPI

from app.auth import require_api_key
```

**Edit B** — inside `create_app()`, add `_auth` and apply to every `include_router` call (replace the six `app.include_router(...)` lines):

```python
    _auth = [Depends(require_api_key)]

    app.include_router(ingest.router,          prefix="/ingest",    tags=["ingest"],      dependencies=_auth)
    app.include_router(jobs.router,            prefix="/jobs",      tags=["jobs"],        dependencies=_auth)
    app.include_router(questions.router,       prefix="/questions", tags=["questions"],   dependencies=_auth)
    app.include_router(ontology_router.router, prefix="/ontology",  tags=["ontology"],    dependencies=_auth)
    app.include_router(search.router,          prefix="/search",    tags=["search"],      dependencies=_auth)
    app.include_router(generate.router,        prefix="/generate",  tags=["generation"],  dependencies=_auth)
```

`/health` is defined inline after the routers with no `dependencies=` — leave it untouched.

- [ ] **Step 4: Run integration tests**

```bash
uv run pytest tests/test_auth.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run full suite to check regressions**

```bash
uv run pytest tests/ -q
```

Expected: all previously passing tests still pass.

> **Note on existing router tests:** Tests in `test_routers.py` build their own `FastAPI` app without auth — they will still pass because they don't go through `create_app()`. Only the new integration tests use the real wired app.

- [ ] **Step 6: Commit**

```bash
git add FULL_PLAN/backend/app/main.py FULL_PLAN/backend/tests/test_auth.py
git commit -m "feat: apply require_api_key to all routes; /health remains public"
```

---

## Chunk 3: Config + Docs

### Task 4: Document API key in `.env.example` and update `.env`

**Files:**
- Create: `FULL_PLAN/backend/.env.example`

- [ ] **Step 1: Create `.env.example`**

Create `FULL_PLAN/backend/.env.example`:

```bash
# Database
SUPABASE_DB_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres

# Auth — set a strong random key for production; leave empty to disable auth in dev
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
API_KEY=

# LLM provider (anthropic | openai | openrouter | ollama)
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6

# Provider API keys (only the selected provider key is required)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=

# Ollama (local, no key needed)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Ingestion tunables
MAX_FILE_UPLOAD_MB=20
PASS1_MAX_TOKENS=2048
PASS2_MAX_TOKENS=4096
```

- [ ] **Step 2: Add `API_KEY` to the live `.env`**

Generate a key and add it to `FULL_PLAN/backend/.env`:

```bash
python -c "import secrets; print('API_KEY=' + secrets.token_hex(32))"
# Copy the output and add to FULL_PLAN/backend/.env
```

- [ ] **Step 3: Verify auth works against the live server**

```bash
cd FULL_PLAN/backend
uv run uvicorn app.main:app --reload &
sleep 2

# Should return 401
curl -s http://localhost:8000/questions | python -m json.tool

# Should return questions list
API_KEY=$(grep API_KEY .env | cut -d= -f2-)
curl -s -H "X-API-Key: $API_KEY" http://localhost:8000/questions | python -m json.tool

# Health should be public
curl -s http://localhost:8000/health | python -m json.tool

kill %1
```

- [ ] **Step 4: Commit**

```bash
git add FULL_PLAN/backend/.env.example
# Do NOT add .env — it contains secrets
git commit -m "docs: add .env.example with API_KEY documentation"
```

---

## Verify `.gitignore` covers `.env`

- [ ] Check `.gitignore` has `.env` entry

```bash
grep "^\.env" FULL_PLAN/backend/.gitignore 2>/dev/null || grep "\.env" .gitignore 2>/dev/null || echo "WARNING: .env not in .gitignore"
```

If not present, add it before committing.
