#!/usr/bin/env bash
set -euo pipefail

FRONTEND_URL="http://localhost:5174/"

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

tailscale serve --bg 5174
tailscale serve status
