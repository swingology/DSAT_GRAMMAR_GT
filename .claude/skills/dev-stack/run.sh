#!/bin/bash

# dev-stack — Full development stack runner (Docker Compose)
# Runs: PostgreSQL 16 + FastAPI Backend + React Frontend (Node.js v22)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"
DB_VOLUME="dsat_redux_md_dsat_pgdata_linux"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

check_prerequisites() {
  local missing=0

  if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Install Docker Desktop or Docker Engine."
    missing=1
  fi

  if ! docker compose version &> /dev/null; then
    log_error "Docker Compose not found. Install Docker Compose v2+."
    missing=1
  fi

  if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "docker compose.yml not found at $REPO_ROOT"
    missing=1
  fi

  if [ $missing -eq 1 ]; then
    log_error "Missing prerequisites."
    exit 1
  fi

  log_success "All prerequisites found"
}

ensure_volume() {
  if ! docker volume inspect "$DB_VOLUME" &> /dev/null; then
    log_info "Creating database volume: $DB_VOLUME"
    docker volume create "$DB_VOLUME"
    log_success "Volume created"
  fi
}

start_all() {
  log_info "Starting DSAT development stack via Docker Compose..."
  echo

  check_prerequisites
  ensure_volume

  echo
  log_info "Building and starting services..."
  cd "$REPO_ROOT"

  # Start all services
  docker compose up -d

  echo
  log_info "Waiting for services to be healthy..."
  sleep 3

  # Check service health
  local db_ready=0
  local backend_ready=0
  local frontend_ready=0
  local max_attempts=30

  for i in $(seq 1 $max_attempts); do
    if docker compose exec -T db pg_isready -U dsat -d dsat_dev &>/dev/null; then
      db_ready=1
    fi
    if [ $db_ready -eq 1 ]; then
      break
    fi
    sleep 1
  done

  for i in $(seq 1 $max_attempts); do
    if docker compose ps backend | grep -q "healthy"; then
      backend_ready=1
    fi
    if [ $backend_ready -eq 1 ]; then
      break
    fi
    sleep 1
  done

  for i in $(seq 1 $max_attempts); do
    if docker compose ps frontend | grep -q "healthy"; then
      frontend_ready=1
    fi
    if [ $frontend_ready -eq 1 ]; then
      break
    fi
    sleep 1
  done

  echo
  log_success "All services started!"
  echo
  echo -e "${GREEN}=== DSAT Development Stack ===${NC}"
  echo "Frontend:    ${BLUE}http://localhost:5173${NC}"
  echo "Backend API: ${BLUE}http://localhost:8000${NC}"
  echo "API Docs:    ${BLUE}http://localhost:8000/docs${NC}"
  echo "Database:    ${BLUE}localhost:5434${NC} (dsat / dsat_dev)"
  echo
  echo "Node.js version: $(docker compose exec -T frontend node --version 2>/dev/null || echo 'v22 (Alpine)')"
  echo
  echo "Commands:"
  echo "  /dev-stack stop              # Stop all services"
  echo "  /dev-stack status            # Check service status"
  echo "  /dev-stack logs              # Stream logs"
  echo "  /dev-stack logs backend      # Backend logs only"
  echo "  docker compose down          # Full cleanup"
  echo
}

stop_all() {
  log_info "Stopping development stack..."

  cd "$REPO_ROOT"
  docker compose down

  log_success "All services stopped"
}

show_status() {
  cd "$REPO_ROOT"

  echo -e "${GREEN}=== DSAT Stack Status ===${NC}"
  echo

  # Show docker compose ps output
  docker compose ps

  echo
  echo "Service Health:"
  echo

  # Check database
  if docker compose exec -T db pg_isready -U dsat -d dsat_dev &>/dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL (5434): ${GREEN}Ready${NC}"
  else
    echo -e "${RED}✗${NC} PostgreSQL (5434): ${RED}Not responding${NC}"
  fi

  # Check backend
  if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend (8000): ${GREEN}Healthy${NC}"
  else
    echo -e "${RED}✗${NC} Backend (8000): ${RED}Not responding${NC}"
  fi

  # Check frontend
  if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend (5173): ${GREEN}Healthy${NC}"
  else
    echo -e "${RED}✗${NC} Frontend (5173): ${RED}Not responding${NC}"
  fi

  echo
}

stream_logs() {
  cd "$REPO_ROOT"

  if [ -n "$2" ]; then
    # Specific service logs
    log_info "Streaming logs for: $2"
    docker compose logs -f "$2"
  else
    # All service logs
    log_info "Streaming logs (Ctrl+C to exit)..."
    docker compose logs -f
  fi
}

main() {
  case "${1:-}" in
    start)
      start_all
      ;;
    stop)
      stop_all
      ;;
    status)
      show_status
      ;;
    logs)
      stream_logs "$@"
      ;;
    *)
      start_all
      ;;
  esac
}

main "$@"
