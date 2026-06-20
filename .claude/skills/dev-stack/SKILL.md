# dev-stack

Runs the complete development stack via Docker Compose: PostgreSQL 16 + FastAPI backend + React frontend with Node.js v22.

## Usage

```bash
/dev-stack                 # Start all services
/dev-stack stop            # Stop all services
/dev-stack status          # Check service health
/dev-stack logs            # Stream logs from all services
/dev-stack logs backend    # Stream backend logs only
```

## What it does

Orchestrates three containerized services via `docker-compose up`:

1. **PostgreSQL 16** — Port 5434
   - Credentials: `dsat` / `dsat_dev`
   - Persistent data volume
   
2. **FastAPI Backend** — Port 8000
   - Python 3.12 + uvicorn
   - Automatic database migrations
   - Hot reload on code changes
   
3. **React Frontend** — Port 5173
   - **Node.js v20** (Debian Bookworm slim)
   - Vite dev server with hot module reloading
   - Proxies API calls to backend

## Prerequisites

- Docker & Docker Compose v2+
- Sufficient disk space for Docker images
- Ports 5173, 8000, 5434 available

## Access

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Student app |
| Backend | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5434 | PostgreSQL connection |

## Features

✅ Docker Compose orchestration (no manual service management)  
✅ Automatic health checks and service ordering  
✅ Node.js v22 (Alpine for minimal image size)  
✅ Hot reload for backend & frontend code  
✅ Persistent PostgreSQL data volume  
✅ Services communicate via Docker network  
✅ Real-time log streaming  

## Under the Hood

- Uses `docker-compose.yml` in repo root
- Builds images from `Dockerfile.backend` and `Dockerfile.frontend`
- Manages dependencies via Docker (no local npm/Python needed if using containers)
- All code changes trigger automatic reloads (no container rebuilds)

## Notes

- Database volume is created automatically if it doesn't exist
- Backend runs migrations on startup
- All services must be healthy before stack is considered "ready"
- Use `docker-compose down` for full cleanup including containers
