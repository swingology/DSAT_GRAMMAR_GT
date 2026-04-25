# Configuration

All settings are loaded from `.env` via `pydantic-settings`.

## Required Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev` | Async Postgres connection string |

## Auth

| Variable | Default | Description |
|---|---|---|
| `ADMIN_API_KEYS` | `admin-key-change-me` | Comma-separated list of admin API keys |
| `STUDENT_API_KEYS` | `student-key-change-me` | Comma-separated list of student API keys |

## LLM

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | `""` | Anthropic API key |
| `OPENAI_API_KEY` | `""` | OpenAI API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `DEFAULT_ANNOTATION_PROVIDER` | `anthropic` | Default LLM provider for annotation |
| `DEFAULT_ANNOTATION_MODEL` | `claude-sonnet-4-6` | Default model name |
| `RULES_VERSION` | `rules_agent_dsat_grammar_ingestion_generation_v3` | V3 rules file identifier |

## Storage

| Variable | Default | Description |
|---|---|---|
| `RAW_ASSET_STORAGE_BACKEND` | `local` | Storage backend (only `local` implemented) |
| `LOCAL_ARCHIVE_MIRROR` | `./archive` | Local filesystem archive root |

## Dev Server

```bash
uvicorn app.main:app --reload --port 8000
```

With reload, code changes restart the server automatically. The `--port` flag binds to `8000`.

## Testing

```bash
pytest tests/ -v
```

Test environment defaults are set in `tests/conftest.py`. Override via env vars:

```bash
export DATABASE_URL="postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test"
export ADMIN_API_KEYS="admin-test-key"
export STUDENT_API_KEYS="student-test-key"
```

## Migrations

Using Alembic with async support:

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

Migration files live in `migrations/versions/`.
