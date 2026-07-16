#!/usr/bin/env bash
set -euo pipefail

DSAT_STUDENT_PORT="${DSAT_STUDENT_PORT:-5174}"
DSAT_ADMIN_PORT="${DSAT_ADMIN_PORT:-5175}"
DSAT_STUDENT_TLS_PORT="${DSAT_STUDENT_TLS_PORT:-8443}"
DSAT_ADMIN_TLS_PORT="${DSAT_ADMIN_TLS_PORT:-8444}"
FRONTEND_URL="http://127.0.0.1:${DSAT_STUDENT_PORT}/"
ADMIN_URL="http://127.0.0.1:${DSAT_ADMIN_PORT}/"

if ! command -v tailscale >/dev/null 2>&1; then
  echo "tailscale CLI is not installed or is not on PATH." >&2
  exit 1
fi

if ! tailscale status >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Tailscale is not connected.

Start and authenticate Tailscale first:
  sudo systemctl start tailscaled
  sudo systemctl enable tailscaled
  tailscale up
EOF
  exit 1
fi

curl -fsS --retry 10 --retry-delay 1 --retry-connrefused "$FRONTEND_URL" >/dev/null

tailscale serve --bg --https="${DSAT_STUDENT_TLS_PORT}" "$FRONTEND_URL"
if curl -fsS --max-time 2 "$ADMIN_URL" >/dev/null 2>&1; then
  tailscale serve --bg --https="${DSAT_ADMIN_TLS_PORT}" "$ADMIN_URL"
fi
tailscale serve status
