#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

DB_VOLUME="dsat_redux_md_dsat_pgdata_linux"
ADMIN_PORT="${ADMIN_PORT:-5175}"

usage() {
  cat <<'EOF'
Usage: ./stop.sh [--backup] [--status]

Safely stops the DSAT app without removing containers or volumes.

  --backup   Create a timestamped pg_dump in backups/ before stopping.
  --status   Print current compose/container status only.

This script intentionally uses:
  docker compose stop

It does not run:
  docker compose down
  docker compose down -v
  podman volume rm
EOF
}

want_backup=0
want_status=0

for arg in "$@"; do
  case "$arg" in
    --backup)
      want_backup=1
      ;;
    --status)
      want_status=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

compose_status() {
  docker compose ps || true
  echo
  docker volume inspect "$DB_VOLUME" >/dev/null
  echo "DB volume present: $DB_VOLUME"
}

if [ "$want_status" -eq 1 ]; then
  compose_status
  exit 0
fi

if ! docker volume inspect "$DB_VOLUME" >/dev/null; then
  echo "ERROR: expected DB volume not found: $DB_VOLUME" >&2
  echo "Refusing to stop because the persistent DB volume cannot be verified." >&2
  exit 1
fi

if [ "$want_backup" -eq 1 ] && docker ps --format '{{.Names}}' | grep -qx dsat-db; then
  mkdir -p backups
  stamp="$(date +%Y%m%d_%H%M%S)"
  container_dump="/tmp/dsat_dev_safe_stop_${stamp}.dump"
  host_dump="backups/dsat_dev_safe_stop_${stamp}.dump"
  echo "Creating DB backup: $host_dump"
  docker exec dsat-db pg_dump -U dsat -d dsat_dev -Fc -f "$container_dump"
  docker cp "dsat-db:${container_dump}" "$host_dump"
fi

if command -v fuser >/dev/null 2>&1; then
  if fuser "${ADMIN_PORT}/tcp" >/dev/null 2>&1; then
    echo "Stopping admin dev server on :${ADMIN_PORT}..."
    fuser -k "${ADMIN_PORT}/tcp" >/dev/null 2>&1 || true
  fi
fi

echo "Stopping DSAT compose services without removing containers or volumes..."
docker compose stop

echo
echo "Stopped safely. Persistent DB volume remains:"
docker volume inspect "$DB_VOLUME" --format '{{.Name}} {{.Mountpoint}}'
