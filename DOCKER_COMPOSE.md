# Docker Compose Setup

Complete development environment with PostgreSQL, FastAPI backend, and React frontend (Node.js v22).

## Quick Start

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild images
docker-compose up --build
```

## Services

| Service | Port | URL | Notes |
|---------|------|-----|-------|
| **Database** | 5434 | postgres://dsat:dsat_dev@localhost:5434/dsat_dev | PostgreSQL 16 |
| **Backend** | 8000 | http://localhost:8000 | FastAPI + uvicorn |
| **Frontend** | 5173 | http://localhost:5173 | Vite dev server (Node.js v22) |

## Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Database**: localhost:5434

## Features

- ✅ All services with health checks
- ✅ Automatic service dependency ordering
- ✅ Volume mounting for hot reload (backend & frontend code)
- ✅ Node.js v22 (Alpine Linux for small image size)
- ✅ Python 3.12 with uv package manager
- ✅ PostgreSQL 16 with persistent data volume

## Environment Variables

Backend service uses:
- `DATABASE_URL`: Points to PostgreSQL in docker network
- `PYTHONUNBUFFERED`: For real-time log output

Frontend service uses:
- `VITE_API_BASE`: Backend URL for API calls (defaults to http://backend:8000)

## Docker Network

All services communicate via Docker's internal network:
- Backend can reach database at `db:5432`
- Frontend can reach backend at `backend:8000`
- All services accessible from host on their mapped ports

## Database Persistence

The PostgreSQL data volume is created externally:

```bash
# Create the volume first (if not already created)
docker volume create dsat_redux_md_dsat_pgdata_linux

# View volume info
docker volume inspect dsat_redux_md_dsat_pgdata_linux
```

## Running Migrations

When backend starts, it automatically runs Alembic migrations against the database.

To manually run migrations:

```bash
docker-compose exec backend uv run alembic upgrade head
```

## Development Workflow

1. **Code changes are hot-reloaded**:
   - Backend: FastAPI with `--reload` flag
   - Frontend: Vite dev server with HMR

2. **View logs in real-time**:
   ```bash
   docker-compose logs -f backend frontend
   ```

3. **Access a service shell**:
   ```bash
   docker-compose exec backend /bin/bash
   docker-compose exec frontend sh
   ```

4. **Rebuild after dependency changes**:
   ```bash
   docker-compose up --build
   ```

## Troubleshooting

### Database connection refused
```bash
# Wait for database to be ready
docker-compose exec db pg_isready -U dsat

# Check database logs
docker-compose logs db
```

### Frontend can't reach backend
```bash
# Check if backend is healthy
docker-compose ps

# Check backend logs
docker-compose logs backend

# Verify connectivity from frontend
docker-compose exec frontend wget http://backend:8000/docs
```

### Port conflicts
```bash
# Check what's using the ports
lsof -i :5173
lsof -i :8000
lsof -i :5434

# Modify ports in docker-compose.yml
```

### Node.js version issues
The frontend Dockerfile uses `node:22-alpine`, which provides Node.js v22. To verify:

```bash
docker-compose exec frontend node --version
```

### Force rebuild
```bash
docker-compose down -v
docker-compose up --build
```

## Performance Notes

- Alpine Linux images are smaller and faster to pull
- Volume mounts allow code hot-reload without rebuilds
- Health checks ensure services are ready before dependents start
- Node.js v22 Alpine provides latest LTS with minimal overhead

## Production Considerations

This setup is optimized for **development**. For production:
- Use multi-stage builds
- Build frontend once, serve static files
- Use environment-specific configs
- Add proper secret management
- Enable HTTPS/TLS
- Optimize resource limits
- Use proper logging infrastructure
