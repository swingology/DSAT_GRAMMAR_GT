# DSAT Backend

FastAPI-based ingestion, annotation, generation, and practice API for the DSAT Grammar corpus.

## Overview

The backend handles:
- **Ingestion** — Upload official PDFs or unofficial assets (PDF, image, markdown, JSON, text), extract structured question data via LLM Pass 1, annotate with V3 taxonomy via LLM Pass 2, validate, and store.
- **Generation** — Generate new DSAT-style questions from specifications, with optional multi-provider comparison.
- **Practice (Segment B)** — Student question recall, answer submission, and accuracy stats.
- **Admin** — Question editing, approval/rejection, overlap management, and evaluation scoring.

## Quick Start

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Copy and edit environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
app/
  main.py              # FastAPI app, lifespan, CORS, router registration
  config.py            # Pydantic Settings (.env loader)
  database.py            # SQLAlchemy async engine, session, Base
  auth.py              # API key header dependencies (admin, student)
  routers/             # HTTP route handlers
    health.py
    questions.py
    student.py
    admin.py
    ingest.py
    generate.py
  models/              # SQLAlchemy ORM + Pydantic schemas
    db.py              # 10 ORM tables
    ontology.py        # V3 controlled vocabularies
    payload.py         # Request/response Pydantic models
    extract.py         # Pass 1 extraction schema
    annotation.py      # Pass 2 annotation schema
    options.py         # Per-option analysis schema
  llm/                 # Provider abstraction
    base.py            # LLMProvider Protocol + LLMResponse dataclass
    factory.py         # get_provider() dispatcher
    anthropic_provider.py
    openai_provider.py
    ollama_provider.py
  parsers/             # Raw asset parsers
    pdf_parser.py      # pymupdf text + image extraction
    image_parser.py
    markdown_parser.py
    json_parser.py     # JSON extraction from LLM text
  pipeline/            # Business logic orchestration
    orchestrator.py    # Job state machine + JobOrchestrator
    validator.py       # PRD §15 validation rules
  prompts/             # LLM prompt builders
    extract_prompt.py
    annotate_prompt.py
    generate_prompt.py
  storage/             # Asset persistence
    local_store.py     # Filesystem storage + SHA-256 checksums
```

## Authentication

All endpoints except `GET /` require an `X-API-Key` header.

| Scope | Env Var | Example Key |
|---|---|---|
| Admin | `ADMIN_API_KEYS` | `admin-key-change-me` |
| Student | `STUDENT_API_KEYS` | `student-key-change-me` |

Multiple keys are comma-separated in the env var.
