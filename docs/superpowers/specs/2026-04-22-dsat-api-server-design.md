# DSAT API Server Design

**Date:** 2026-04-22
**Status:** Approved

## Overview

Containerized FastAPI server for the DSAT grammar question generation pipeline. Supports question generation, PDF ingestion, validation, and custom scripts. Grows incrementally by adding router modules.

## Architecture

**Monolithic FastAPI with router modules** — single Docker image, each feature is a separate router. Add a feature = add a router file + service file.

### Why This Approach

- Local-first, cloud-ready — one `docker build` runs anywhere
- File-based storage consistent with existing project (rules are MD files, output is MD)
- LLM-bound workload (not I/O-bound) — file storage is fast enough
- Router modules keep features decoupled while staying simple
- v3 rules only — single source of truth

## Project Structure

```
dsat-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, mounts routers
│   ├── config.py               # Pydantic Settings (env + defaults)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py           # GET /health
│   │   ├── generation.py       # POST /generate/*
│   │   ├── ingestion.py        # POST /ingest/*
│   │   └── validation.py       # POST /validate/* (future)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_client.py       # Unified Claude/OpenAI/Ollama client
│   │   ├── rules_loader.py     # Load v3 rules from file
│   │   └── prompt_builder.py   # Build prompts from rules + params
│   └── models/
│       ├── __init__.py
│       ├── generation.py       # Request/response schemas
│       └── ingestion.py
├── rules/                      # v3 rules only (bundled or mounted)
│   └── v3/
│       └── rules_agent_dsat_grammar_ingestion_generation_v3.md
├── scripts/                   # Custom scripts (mounted volume)
├── output/                    # Generated results (mounted volume)
├── tests/
│   ├── test_generation.py
│   └── test_ingestion.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

## LLM Client

**`services/llm_client.py`** — single `generate()` method routing by `LLM_PROVIDER`:

| Provider | Env Var | Backend |
|----------|---------|---------|
| `claude` | `ANTHROPIC_API_KEY` | Anthropic API |
| `openai` | `OPENAI_API_KEY` | OpenAI API |
| `ollama` | `OLLAMA_BASE_URL` | Local Ollama (default `http://localhost:11434`) |

All providers return the same `GenerationResult` for consistent handling.

## Rules Loader

**`services/rules_loader.py`**:
- Loads `rules_agent_dsat_grammar_ingestion_generation_v3.md` from `RULES_PATH`
- Caches in memory after first load (~90KB, negligible)
- `POST /admin/reload-rules` for hot-reload without restart
- Configurable path supports both bundled-in-image and mounted-volume modes

## Endpoints

```
GET  /health                    # Service status + rules loaded info

POST /generate/questions        # Generate SAT grammar questions
  Body: { topic, difficulty, count, question_type, ... }
  Response: { questions: [...] }

POST /generate/module           # Generate a full test module
  Body: { module_type, difficulty, question_count, ... }
  Response: { module_id, questions: [...] }

POST /ingest/pdf                # Ingest a practice test PDF
  Body: multipart/form-data (PDF file + config)
  Response: { extracted_questions: [...] }

GET  /rules/info                # Current rules version, path, size, last loaded

POST /admin/reload-rules        # Hot-reload rules from disk

GET  /scripts/list              # List available custom scripts

POST /scripts/run/{name}        # Execute a custom script
  Body: { args: {...} }
  Response: { output: ... }
```

## Custom Scripts

- Drop a Python script into `scripts/` directory
- Each script must expose `run(**kwargs) -> dict`
- `/scripts/run/{name}` discovers and executes them
- Scripts can import `app.services` for LLM client, rules loader reuse
- Mounted volume — add scripts without rebuilding

## Docker Configuration

### Dockerfile (multi-stage)

Stage 1: Install dependencies from `pyproject.toml`
Stage 2: Copy app code, rules, entrypoint
Expose 8000, run with `uvicorn`

### docker-compose.yml

```yaml
services:
  dsat-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=claude
      - RULES_PATH=/app/rules/v3
    volumes:
      - ./output:/app/output         # generated results
      - ./scripts:/app/scripts       # custom scripts
      # Uncomment to override bundled rules:
      # - ./rules:/app/rules
    env_file:
      - .env
```

## Environment Variables

| Env Var | Default | Description |
|---------|---------|-------------|
| `LLM_PROVIDER` | `claude` | Which LLM backend to use |
| `ANTHROPIC_API_KEY` | required | Claude API key |
| `OPENAI_API_KEY` | optional | OpenAI API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `RULES_PATH` | `/app/rules/v3` | Path to v3 rules file |
| `OUTPUT_PATH` | `/app/output` | Where generated results go |
| `SCRIPTS_PATH` | `/app/scripts` | Custom scripts directory |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## Error Handling

All endpoints return structured JSON errors:
- LLM failures → 502 with retry info
- Missing rules file → 500 with "rules not found at PATH" message
- Invalid script → 404 with available scripts listed
- Malformed request → 422 with Pydantic validation details

Response format: `{ "error": "category", "detail": "specific message" }`

## Testing

- Unit tests for services (rules loader, prompt builder, LLM client with mocked responses)
- Integration tests for endpoints using FastAPI `TestClient`
- Docker smoke test: build, run, hit `/health`, confirm rules loaded
- Fixtures: sample v3 rules excerpt, mock LLM responses, sample PDF

## Storage

File-based storage consistent with existing project:
- Rules: MD files in `rules/v3/`
- Generated output: MD files in `output/`
- Custom scripts: Python files in `scripts/`
- All output paths configurable via env vars
- No database — LLM-bound workload means file I/O is negligible

## Design Decisions

1. **v3 only** — single rules version, no v2/v4 branching
2. **File-based storage** — consistent with existing project, fast enough for LLM-bound workload
3. **Configurable mount points** — rules can be bundled in image or mounted as volume
4. **Custom scripts via run() convention** — drop-in extensibility without code changes
5. **Pydantic Settings for config** — env vars with defaults, type validation, `.env` support