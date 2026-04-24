# Testing Guide

This document describes how to run the DSAT backend test suite, what each test file covers, and how to perform local smoke tests.

---

## Running Tests

All tests are written with **pytest** and **pytest-asyncio**.

### Activate the virtual environment

```bash
cd /home/jb/DSAT_REDUX_MD/backend
source .venv/bin/activate
```

### Run the full test suite

```bash
pytest tests/ -v
```

### Run a specific test file

```bash
pytest tests/test_config.py -v
pytest tests/test_database.py -v
pytest tests/test_ontology.py -v
pytest tests/test_models.py -v
pytest tests/test_schemas.py -v
pytest tests/test_auth.py -v
pytest tests/test_health.py -v
```

### Run a specific test case

```bash
pytest tests/test_config.py::test_settings_loads_from_env -v
```

---

## Test File Inventory

| File | What It Tests |
|---|---|
| `tests/test_config.py` | `Settings` loads from environment variables; default values for LLM provider, model, and rules version are correct |
| `tests/test_database.py` | Database module imports (`engine`, `async_session`, `Base`) succeed; tables can be created and dropped via `Base.metadata` |
| `tests/test_ontology.py` | All V3 ontology constants are defined and contain expected values (content origins, job statuses, grammar roles, focus keys, syntactic traps, etc.) |
| `tests/test_models.py` | All 10 SQLAlchemy ORM tables are registered on `Base.metadata`; required columns exist on `QuestionJob`, `Question`, and `QuestionOption`; foreign keys are configured on `UserProgress` |
| `tests/test_schemas.py` | Pydantic schemas validate correctly: `QuestionExtract` accepts valid data and rejects bad option labels; `QuestionAnnotation` rejects invalid grammar focus keys; `OptionAnalysis` accepts valid distractor analysis; `QuestionRecallResponse` serializes correctly |
| `tests/test_auth.py` | Admin and student API key dependencies accept valid keys and reject invalid or missing keys; admin keys are rejected by student endpoints |
| `tests/test_health.py` | `GET /` returns `200 OK` with `status: ok` and a `version` field |

---

## Test Environment Setup

Before running tests, ensure the following environment variables are set. The `tests/conftest.py` file sets defaults, but you can override them.

### Required environment variables

```bash
# Database (used by conftest and database module)
export DATABASE_URL="postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test"

# Auth (used by auth tests)
export ADMIN_API_KEYS="admin-test-key"
export STUDENT_API_KEYS="student-test-key"
```

### Optional environment variables

```bash
# LLM (not required for unit tests)
export ANTHROPIC_API_KEY=""
export OPENAI_API_KEY=""
export OLLAMA_BASE_URL="http://localhost:11434"

# Storage
export RAW_ASSET_STORAGE_BACKEND="local"
export LOCAL_ARCHIVE_MIRROR="./archive"
```

The `.env.example` file in the backend root contains a full template.

---

## Dev Server and Smoke Tests

### Start the dev server

```bash
cd /home/jb/DSAT_REDUX_MD/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.

### Health check

```bash
curl http://localhost:8000/
```

Expected response:
```json
{"status":"ok","version":"0.1.0"}
```

### Auth rejection (no key)

```bash
curl -X GET http://localhost:8000/admin-test
```

Expected response: `403 Forbidden`

### Auth rejection (wrong key)

```bash
curl -X GET http://localhost:8000/admin-test \
  -H "X-API-Key: wrong-key"
```

Expected response: `403 Forbidden`

### Auth acceptance (admin endpoint)

```bash
curl -X GET http://localhost:8000/admin-test \
  -H "X-API-Key: admin-key-change-me"
```

Expected response: `200 OK` with `{"ok":true}` (once admin routers are registered)

---

## Notes

- The database test uses the real Postgres connection by default. For CI or local development without Postgres, override `DATABASE_URL` to point to an SQLite database or use the test override in `conftest.py`.
- Auth tests require the `ADMIN_API_KEYS` and `STUDENT_API_KEYS` environment variables to be set before importing the auth module.
- Schema tests validate against the V3 ontology constants; if the ontology module changes, these tests may need updating.
