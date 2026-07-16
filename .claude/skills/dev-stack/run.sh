#!/bin/bash

# dev-stack — Full development stack runner (Podman Compose, Docker-compatible)
# Runs: PostgreSQL 16 + FastAPI Backend (uv) + React Frontend (Node.js 20 bookworm-slim)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"
DB_VOLUME="dsat_redux_md_dsat_pgdata_linux"

# Prefer podman explicitly — a shell alias (docker=podman) may be set
# interactively, but scripts/subagents run non-interactively and won't see it.
ENGINE="podman"
COMPOSE="podman compose"

if ! command -v podman &> /dev/null; then
  echo "podman not found." >&2
  exit 1
fi

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

ensure_podman_socket() {
  command -v systemctl >/dev/null 2>&1 || return 0
  systemctl --user start podman.socket >/dev/null 2>&1 || true
}

check_prerequisites() {
  local missing=0

  ensure_podman_socket

  if ! $COMPOSE version &> /dev/null; then
    log_error "$COMPOSE not found or not working."
    missing=1
  fi

  if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "docker-compose.yml not found at $REPO_ROOT"
    missing=1
  fi

  if [ $missing -eq 1 ]; then
    log_error "Missing prerequisites."
    exit 1
  fi

  log_success "All prerequisites found (engine: $ENGINE)"
}

ensure_volume() {
  if ! $ENGINE volume inspect "$DB_VOLUME" &> /dev/null; then
    log_info "Creating database volume: $DB_VOLUME"
    $ENGINE volume create "$DB_VOLUME"
    log_success "Volume created"
  fi
}

# Reads the actual host-mapped port for a service/container-port pair from
# compose, rather than hardcoding — host ports here have drifted from the
# defaults documented elsewhere before.
host_port() {
  $COMPOSE port "$1" "$2" 2>/dev/null | cut -d: -f2
}

start_all() {
  log_info "Starting DSAT development stack via $ENGINE compose..."
  echo

  check_prerequisites
  ensure_volume

  echo
  log_info "Building and starting services..."
  cd "$REPO_ROOT"

  # Start all services. --build is cheap here: dependency layers
  # (uv sync / npm ci) are cache-mounted and only rerun when lockfiles change.
  $COMPOSE up -d --build

  echo
  log_info "Waiting for services to be healthy..."
  sleep 3

  # Check service health
  local db_ready=0
  local backend_ready=0
  local frontend_ready=0
  local max_attempts=30

  for i in $(seq 1 $max_attempts); do
    if $COMPOSE exec -T db pg_isready -U dsat -d dsat_dev &>/dev/null; then
      db_ready=1
    fi
    if [ $db_ready -eq 1 ]; then
      break
    fi
    sleep 1
  done

  for i in $(seq 1 $max_attempts); do
    if $COMPOSE ps backend | grep -q "healthy"; then
      backend_ready=1
    fi
    if [ $backend_ready -eq 1 ]; then
      break
    fi
    sleep 1
  done

  for i in $(seq 1 $max_attempts); do
    if $COMPOSE ps frontend | grep -q "healthy"; then
      frontend_ready=1
    fi
    if [ $frontend_ready -eq 1 ]; then
      break
    fi
    sleep 1
  done

  local db_port backend_port frontend_port
  db_port="$(host_port db 5432)"
  backend_port="$(host_port backend 8000)"
  frontend_port="$(host_port frontend 5173)"

  echo
  log_success "All services started!"
  echo
  echo -e "${GREEN}=== DSAT Development Stack ===${NC}"
  echo -e "Frontend:    ${BLUE}http://localhost:${frontend_port}${NC}"
  echo -e "Backend API: ${BLUE}http://localhost:${backend_port}${NC}"
  echo -e "API Docs:    ${BLUE}http://localhost:${backend_port}/docs${NC}"
  echo -e "Database:    ${BLUE}localhost:${db_port}${NC} (dsat / dsat_dev)"
  echo
  echo "Node.js version: $($COMPOSE exec -T frontend node --version 2>/dev/null || echo 'unknown (frontend not up)')"
  echo
  echo "Commands:"
  echo "  /dev-stack stop              # Stop all services"
  echo "  /dev-stack status            # Check service status"
  echo "  /dev-stack logs              # Stream logs"
  echo "  /dev-stack logs backend      # Backend logs only"
  echo "  $COMPOSE down                # Full cleanup"
  echo
}

stop_all() {
  log_info "Stopping development stack..."

  cd "$REPO_ROOT"
  $COMPOSE down

  log_success "All services stopped"
}

show_status() {
  cd "$REPO_ROOT"

  echo -e "${GREEN}=== DSAT Stack Status ===${NC}"
  echo

  # Show compose ps output
  $COMPOSE ps

  echo
  echo "Service Health:"
  echo

  local db_port backend_port frontend_port
  db_port="$(host_port db 5432)"
  backend_port="$(host_port backend 8000)"
  frontend_port="$(host_port frontend 5173)"

  # Check database
  if $COMPOSE exec -T db pg_isready -U dsat -d dsat_dev &>/dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL (${db_port:-?}): ${GREEN}Ready${NC}"
  else
    echo -e "${RED}✗${NC} PostgreSQL (${db_port:-?}): ${RED}Not responding${NC}"
  fi

  # Check backend
  if [ -n "$backend_port" ] && curl -s "http://localhost:${backend_port}/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend (${backend_port:-?}): ${GREEN}Healthy${NC}"
  else
    echo -e "${RED}✗${NC} Backend (${backend_port:-?}): ${RED}Not responding${NC}"
  fi

  # Check frontend
  if [ -n "$frontend_port" ] && curl -s "http://localhost:${frontend_port}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend (${frontend_port:-?}): ${GREEN}Healthy${NC}"
  else
    echo -e "${RED}✗${NC} Frontend (${frontend_port:-?}): ${RED}Not responding${NC}"
  fi

  echo
}

stream_logs() {
  cd "$REPO_ROOT"

  if [ -n "$2" ]; then
    # Specific service logs
    log_info "Streaming logs for: $2"
    $COMPOSE logs -f "$2"
  else
    # All service logs
    log_info "Streaming logs (Ctrl+C to exit)..."
    $COMPOSE logs -f
  fi
}

main() {
  ensure_podman_socket

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
