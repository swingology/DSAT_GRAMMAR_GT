#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VOLUME_NAME="dsat_redux_md_dsat_pgdata_linux"
FRONTEND_URL="http://localhost:5174/"
BACKEND_URL="http://localhost:8002/docs"

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
Database: localhost:5437
EOF
