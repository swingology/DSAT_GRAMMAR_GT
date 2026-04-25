# Docker Image Build Plan — DSAT Grammar Backend

Package the FastAPI backend into a single Docker image that connects to Supabase (Postgres) and supports all LLM providers (Anthropic, OpenAI, Ollama).

---

## 1. Image Structure

```
dsat-backend:latest
├── /app                    # Python application
│   ├── app/                # FastAPI app package
│   ├── migrations/         # Alembic migrations
│   ├── pyproject.toml      # Project metadata + deps
│   ├── alembic.ini         # Alembic config
│   └── archive/            # Uploaded asset storage (VOLUME)
├── /rules_agent_dsat_grammar_ingestion_generation_v3.md  # Rules file (from project root)
├── docker-entrypoint.sh    # Startup script
└── .env                    # Mounted at runtime (not baked in)
```

## 2. Dockerfile

### Base image
- `python:3.12-slim` — minimal, well-maintained
- Install `libpq5` (for asyncpg) and `pymupdf` system deps

### Build stage
- Install `uv` for fast dependency resolution
- Create virtualenv, install `.[dev]`
- Copy application code
- Copy the rules file from the repo root into `/`

### Runtime
- `WORKDIR /app`
- `EXPOSE 8000`
- Entrypoint runs: alembic upgrade → uvicorn

## 3. Dependencies (system packages)

| Package | Reason |
|---------|--------|
| `libpq5` | asyncpg Postgres driver |
| `libgl1-mesa-glx` | pymupdf PDF rendering |
| `libglib2.0-0` | pymupdf GLib dependency |

## 4. Entrypoint Script (`docker-entrypoint.sh`)

```bash
#!/bin/sh
set -e

# Wait for Postgres to be ready
until pg_isready -h "$(echo $DATABASE_URL | sed 's/.*@//' | sed 's/:.*//')" -U postgres; do
  echo "Waiting for Postgres..."
  sleep 2
done

# Run migrations
alembic upgrade head

# Start server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## 5. Environment Variables (runtime, via `.env` or `-e` flags)

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | Supabase connection string (required) |
| `ADMIN_API_KEYS` | Comma-separated admin keys |
| `STUDENT_API_KEYS` | Comma-separated student keys |
| `ANTHROPIC_API_KEY` | For Claude provider |
| `OPENAI_API_KEY` | For GPT provider |
| `OLLAMA_BASE_URL` | For Ollama provider (e.g. `http://host.docker.internal:11434`) |
| `DEFAULT_ANNOTATION_PROVIDER` | `anthropic`, `openai`, or `ollama` |
| `DEFAULT_ANNOTATION_MODEL` | Model name string |
| `RULES_VERSION` | Rules file identifier |
| `LOCAL_ARCHIVE_MIRROR` | Default `./archive` |

## 6. Volumes

| Mount | Purpose |
|-------|---------|
| `/app/archive` | Persist uploaded PDFs/images across restarts |

## 7. Build & Run Commands

```bash
# Build
docker build -t dsat-backend -f backend/Dockerfile .

# Run (Ollama — local model)
docker run -d --name dsat-api \
  -p 8000:8000 \
  --env-file backend/.env \
  --add-host host.docker.internal:host-gateway \
  -v dsat-archive:/app/archive \
  dsat-backend

# Run (Anthropic — cloud)
docker run -d --name dsat-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -e DEFAULT_ANNOTATION_PROVIDER=anthropic \
  -e DEFAULT_ANNOTATION_MODEL=claude-sonnet-4-6 \
  -v dsat-archive:/app/archive \
  dsat-backend
```

## 8. File Locations — Pre vs Post Docker

| Resource | Current (local) | Docker image path |
|----------|----------------|-------------------|
| App code | `backend/app/` | `/app/app/` |
| Migrations | `backend/migrations/` | `/app/migrations/` |
| Alembic config | `backend/alembic.ini` | `/app/alembic.ini` |
| `pyproject.toml` | `backend/pyproject.toml` | `/app/pyproject.toml` |
| Rules file | `rules_agent_dsat_grammar_ingestion_generation_v3.md` | `/rules_agent_dsat_grammar_ingestion_generation_v3.md` |
| Archive | `backend/archive/` | `/app/archive/` (volume) |

The rules file path resolution in `app/prompts/annotate_prompt.py` goes up 3 levels from `app/prompts/` → project root. In Docker the project root is `/app`, so it resolves to `/rules_agent_dsat_grammar_ingestion_generation_v3.md`. The Dockerfile must copy the rules file to `/` for this to work.

## 9. Build Context

```
Context: /Users/jb/Downloads/DSAT_GRAMMAR_GT/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── Dockerfile          (NEW)
│   └── docker-entrypoint.sh (NEW)
└── rules_agent_dsat_grammar_ingestion_generation_v3.md
```

The build context must be the repo root (not `backend/`) so the Dockerfile can access the rules file.

## 10. Dockerfile Contents

```dockerfile
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY rules_agent_dsat_grammar_ingestion_generation_v3.md /

WORKDIR /app
COPY backend/pyproject.toml backend/alembic.ini ./
COPY backend/migrations/ migrations/
COPY backend/app/ app/

RUN pip install --no-cache-dir uv \
    && uv venv \
    && . .venv/bin/activate \
    && uv pip install .[dev]

EXPOSE 8000
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
```

## 11. Multi-Arch Support

Add `--platform linux/amd64` flag when building for deployment on `linux/amd64` hosts (most cloud VPS, Lambda, ECS). Apple Silicon users build natively with `--platform linux/arm64`.

```bash
# For AMD64 deployment (e.g., AWS, DigitalOcean)
docker build --platform linux/amd64 -t dsat-backend .

# For local ARM64 (Apple Silicon)
docker build -t dsat-backend .
```

## 12. Testing the Image

```bash
# Build
docker build -t dsat-backend -f backend/Dockerfile .

# Run with local .env
docker run -d --name dsat-api-test \
  -p 8000:8000 \
  --env-file backend/.env \
  --add-host host.docker.internal:host-gateway \
  -v dsat-archive:/app/archive \
  dsat-backend

# Health check
curl http://localhost:8000/

# Check logs
docker logs dsat-api-test
```

## 13. CI / Deployment Notes

- **Secrets**: Never bake `.env` into the image. Use `--env-file` at `docker run` or Docker Swarm/Kubernetes secrets.
- **Migrations**: Run `alembic upgrade head` as part of the entrypoint (idempotent).
- **Workers**: `--workers 2` is a starting point; tune based on CPU/memory. Each worker holds its own async event loop.
- **Ollama**: Pass `OLLAMA_BASE_URL=http://host.docker.internal:11434` so the container reaches the host's Ollama. On Linux, use `--network host` instead of `host.docker.internal`.

## 14. Implementation Order

1. Create `backend/Dockerfile`
2. Create `backend/docker-entrypoint.sh`
3. Add `backend/.dockerignore` (exclude `.venv`, `__pycache__`, `.git`)
4. Build and test locally
5. Push to registry (Docker Hub / ECR / GHCR)
6. Deploy target (VPS / ECS / Railway / Fly.io)
