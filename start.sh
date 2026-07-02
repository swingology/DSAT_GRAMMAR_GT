#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$ROOT_DIR/scripts/start_app.sh"

if ! "$ROOT_DIR/scripts/expose_tailscale.sh"; then
  cat <<'EOF'

Local app startup succeeded, but Tailscale exposure did not start.
Run scripts/expose_tailscale.sh again after Tailscale is connected.
EOF
fi
