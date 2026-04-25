# Backend Architecture

## Request Lifecycle

```
Client Request
    → FastAPI Router (app/routers/)
    → API Key Auth (app/auth.py)
    → Async SQLAlchemy Session (app/database.py)
    → Business Logic / Pipeline (app/pipeline/)
    → LLM Provider (app/llm/)
    → ORM Model (app/models/db.py)
    → PostgreSQL
```

## Module Responsibilities

### `app.main`
- Creates the `FastAPI` app with lifespan context manager
- Registers CORS middleware (allows all origins in dev)
- Includes all routers: health, questions, student, admin, ingest, generate
- Disposes the SQLAlchemy engine on shutdown

### `app.config`
- `Settings` class loads from `.env` via `pydantic-settings`
- Exposes `admin_api_key_list` and `student_api_key_list` as computed properties
- Defines LLM defaults (provider, model, rules version)

### `app.database`
- `create_async_engine` with `pool_size=5`, `max_overflow=10`
- `async_sessionmaker` with `expire_on_commit=False`
- `DeclarativeBase` subclass for ORM models
- `get_db()` dependency yields `AsyncSession`

### `app.auth`
- `APIKeyHeader` with `auto_error=False`
- `admin_required()` — rejects with 403 if key not in admin list
- `student_required()` — rejects with 403 if key not in student list

## Data Flow: Ingestion

```
Upload PDF/Image/MD/JSON/Text
    → save_asset() → local filesystem
    → compute_checksum() → SHA-256
    → QuestionAsset row created
    → QuestionJob created (status=parsing)
    → background task spawned

Background Pipeline:
    parsing → extracting (LLM Pass 1: extract_prompt)
          → annotating (LLM Pass 2: annotate_prompt)
          → validating (validator.validate_question)
          → approved | needs_review | failed
```

## Data Flow: Generation

```
POST /generate/questions
    → QuestionJob created (status=extracting)
    → background task spawned

Background Pipeline:
    extracting → generating (LLM: generate_prompt)
             → annotating (LLM: annotate_prompt)
             → validating
             → Question row created
             → approved | needs_review | failed
```

## State Machine

Defined in `app/pipeline/orchestrator.py`:

| Status | Next | Terminal |
|---|---|---|
| `pending` | `parsing` / `extracting` | No |
| `parsing` | `extracting` | No |
| `extracting` | `generating` / `annotating` | No |
| `generating` | `annotating` | No |
| `annotating` | `overlap_checking` / `validating` | No |
| `overlap_checking` | `validating` | No |
| `validating` | `approved` / `needs_review` | No |
| `approved` | — | Yes |
| `needs_review` | — | Yes |
| `failed` | — | Yes |

## Segment Model

- **Segment A (Corpus)** — owns `question_jobs`, `questions`, `question_versions`, `question_annotations`, `question_options`, `question_assets`, `question_relations`, `llm_evaluations`
- **Segment B (Student)** — owns `users`, `user_progress`
- Segment B may **read** (never write) `questions`, `question_annotations`, `question_versions`, `question_options`
