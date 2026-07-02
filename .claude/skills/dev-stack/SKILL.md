# dev-stack

Runs the complete development stack via Podman Compose (Docker-compatible): PostgreSQL 16 + FastAPI backend (uv) + React frontend with Node.js 20 (bookworm-slim).

## Usage

```bash
/dev-stack                 # Start all services
/dev-stack stop            # Stop all services
/dev-stack status          # Check service health
/dev-stack logs            # Stream logs from all services
/dev-stack logs backend    # Stream backend logs only
```

## What it does

Orchestrates three containerized services via `podman compose up` (falls back to `docker compose` if podman isn't installed):

1. **PostgreSQL 16** — host port 5437 (container 5432)
   - Credentials: `dsat` / `dsat_dev`
   - Persistent external volume: `dsat_redux_md_dsat_pgdata_linux` (auto-created if missing)

2. **FastAPI Backend** — host port 8002 (container 8000)
   - Python 3.12 + uv + uvicorn
   - Hot reload on code changes

3. **React Frontend** — host port 5174 (container 5173)
   - **Node.js 20** (Debian Bookworm slim — not Alpine; avoids a WASM/vite compilation crash on WSL2 Linux)
   - Vite dev server with hot module reloading
   - Proxies API calls to backend

Host ports are defined in `docker-compose.yml` and can drift — `run.sh` reads them dynamically via `compose port <service> <container-port>` rather than hardcoding, and this doc's numbers may go stale before that does.

## Prerequisites

- Podman (preferred) or Docker, with Compose v2+
- Sufficient disk space for images
- Ports 5174, 8002, 5437 available (or whatever `docker-compose.yml` currently maps)

## Access

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5174 | Student app |
| Backend | http://localhost:8002 | FastAPI server |
| API Docs | http://localhost:8002/docs | Swagger UI |
| Database | localhost:5437 | PostgreSQL connection |

## Features

✅ Podman/Docker Compose orchestration (no manual service management)
✅ Automatic health checks and service ordering
✅ Node.js 20 bookworm-slim (avoids Alpine WASM issues)
✅ uv-based backend build with dependency-layer caching (fast rebuilds)
✅ Hot reload for backend & frontend code
✅ Persistent PostgreSQL data volume
✅ Services communicate via a container network
✅ Real-time log streaming

## Under the Hood

- Uses `docker-compose.yml` in repo root
- Builds images from `Dockerfile.backend` and `Dockerfile.frontend`
- Backend: `uv sync --frozen` with a `--mount=type=cache` uv cache — dependency
  layer only rebuilds when `pyproject.toml`/`uv.lock` change
- Frontend: `npm cache clean --force` before `npm ci` (a corrupted local cache
  once got silently reused across builds here; forcing a clean cache prevents
  a repeat)
- Manages dependencies via containers (no local npm/Python needed)
- All code changes trigger automatic reloads (no container rebuilds needed)

## Notes

- Database volume is external and created automatically by `run.sh` if missing
- All services must be healthy before stack is considered "ready"
- Use `<engine> compose down` for full cleanup including containers
