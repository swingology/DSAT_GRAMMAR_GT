#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VOLUME_NAME="dsat_redux_md_dsat_pgdata_linux"
DSAT_DB_PORT="${DSAT_DB_PORT:-5437}"
DSAT_BACKEND_PORT="${DSAT_BACKEND_PORT:-8002}"
DSAT_STUDENT_PORT="${DSAT_STUDENT_PORT:-5174}"
FRONTEND_URL="http://127.0.0.1:${DSAT_STUDENT_PORT}/"
BACKEND_URL="http://127.0.0.1:${DSAT_BACKEND_PORT}/docs"

cd "$ROOT_DIR"

docker context use default >/dev/null
docker volume create "$VOLUME_NAME" >/dev/null
docker compose up -d
docker compose ps

echo "Waiting for frontend..."
curl -fsS --retry 20 --retry-delay 1 --retry-connrefused "$FRONTEND_URL" >/dev/null

echo "Waiting for backend..."
curl -fsS --retry 20 --retry-delay 1 --retry-connrefused "$BACKEND_URL" >/dev/null

cat <<EOF

DSAT app is running.
Frontend: $FRONTEND_URL
Backend:  $BACKEND_URL
Database: 127.0.0.1:${DSAT_DB_PORT}
EOF
