#!/usr/bin/env bash
# One-shot launcher for the DSAT apps:
#   - dev stack (PostgreSQL + FastAPI backend + grammar-practice/student app) via podman compose
#   - admin dashboard (APP/ADMIN_APP) as a host Vite dev server
#
# Both apps are reachable over Tailscale via MagicDNS host + port (they bind 0.0.0.0
# and allowlist .ts.net hosts in their Vite configs). The student grammar app is also
# exposed over TLS at https://<node>:8443 via `tailscale serve` (wired in ensure_student_tls
# below). Port 443 is left untouched — it's already claimed by another app on this node.
#
# Usage:
#   ./start.sh          start everything (reuses whatever is already running)
#   ./start.sh stop     stop the admin dev server and the compose stack
#   ./start.sh status   show what's up and the URLs
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_DIR="$ROOT/APP/ADMIN_APP"
RUN_SH="$ROOT/.claude/skills/dev-stack/run.sh"

# Host ports = host side of the container mappings in docker-compose.yml.
BACKEND_PORT="$(grep -oE '"[0-9]+:8000"' "$ROOT/docker-compose.yml" | head -1 | tr -d '"' | cut -d: -f1)"
BACKEND_PORT="${BACKEND_PORT:-8002}"
STUDENT_PORT="$(grep -oE '"[0-9]+:5173"' "$ROOT/docker-compose.yml" | head -1 | tr -d '"' | cut -d: -f1)"
STUDENT_PORT="${STUDENT_PORT:-5174}"
ADMIN_PORT="${ADMIN_PORT:-5175}"
ADMIN_TOKEN="${VITE_ADMIN_TOKEN:-admin-test-key}"
BACKEND_ORIGIN="http://localhost:${BACKEND_PORT}"

up() { curl -sf -o /dev/null --max-time 2 "http://localhost:$1$2"; }
backend_up() { up "$BACKEND_PORT" /docs; }
student_up() { up "$STUDENT_PORT" /; }
admin_up()   { up "$ADMIN_PORT" /; }

# Ensure the student grammar app is reachable over Tailscale at https://<node>:8443
# (TLS terminated by tailscale serve). Idempotent: re-running on an already-set
# port is a no-op. Deliberately does NOT use `tailscale serve reset` — that would
# also wipe the :443 config that proxies to the bookmarks app on :8765.
ensure_student_tls() {
  command -v tailscale >/dev/null 2>&1 || return 0
  tailscale status >/dev/null 2>&1 || return 0
  tailscale serve --bg --https=8443 "http://localhost:${STUDENT_PORT}" >/dev/null 2>&1 || \
    echo "WARN: tailscale serve :8443 failed (Tailscale not up?) — student TLS skipped." >&2
}

magicdns_name() {
  tailscale status --json 2>/dev/null \
    | grep -oE '"DNSName": *"[^"]*"' | head -1 \
    | sed -E 's/.*"([^"]+)\.".*/\1/'
}

summary() {
  local ts; ts="$(magicdns_name || true)"
  echo
  echo "=== DSAT apps ==="
  printf '%-26s %-30s %s\n' "Student app (grammar):" "http://localhost:${STUDENT_PORT}" "$(student_up && echo UP || echo DOWN)"
  printf '%-26s %-30s %s\n' "Admin dashboard:"       "http://localhost:${ADMIN_PORT}"   "$(admin_up && echo UP || echo DOWN)"
  printf '%-26s %-30s %s\n' "Backend API:"           "${BACKEND_ORIGIN}"                "$(backend_up && echo UP || echo DOWN)"
  if [ -n "$ts" ]; then
    echo "Tailscale (MagicDNS):"
    echo "  student:  http://${ts}:${STUDENT_PORT}"
    echo "  student (TLS):  https://${ts}:8443"
    echo "  admin:    http://${ts}:${ADMIN_PORT}"
  fi
}

case "${1:-start}" in
  status)
    summary
    ;;

  stop)
    if admin_up; then
      echo "Stopping admin dev server on :${ADMIN_PORT}..."
      fuser -k "${ADMIN_PORT}/tcp" 2>/dev/null || true
    fi
    bash "$RUN_SH" stop
    ;;

  start)
    # 1. Compose stack: DB + backend + student app. run.sh is idempotent and
    #    handles podman-first engine detection + DB volume creation.
    if backend_up && student_up; then
      echo "Dev stack already running (backend :${BACKEND_PORT}, student app :${STUDENT_PORT})."
    else
      echo "Starting dev stack (first build can take a few minutes)..."
      bash "$RUN_SH" start
      for _ in $(seq 1 60); do
        backend_up && break
        sleep 2
      done
      backend_up || { echo "ERROR: backend did not become healthy at ${BACKEND_ORIGIN}" >&2; exit 1; }
    fi

    # Ensure the student grammar app is served over Tailscale at https://<node>:8443.
    student_up && ensure_student_tls

    # 2. Admin dashboard on the host.
    if admin_up; then
      echo "Admin dashboard already running on :${ADMIN_PORT}."
      summary
      exit 0
    fi

    # Node 20 via NVM (host default), per project convention.
    source "$HOME/.nvm/nvm.sh"
    cd "$ADMIN_DIR"
    [ -d node_modules ] || npm install

    summary
    echo
    echo "Starting admin dashboard on :${ADMIN_PORT}..."
    echo "(Ctrl-C stops only the admin app; the stack keeps running. Use './start.sh stop' to stop everything.)"
    exec env VITE_BACKEND_ORIGIN="$BACKEND_ORIGIN" VITE_ADMIN_TOKEN="$ADMIN_TOKEN" \
      npm run dev -- --port "$ADMIN_PORT" --strictPort
    ;;

  *)
    echo "Usage: $0 [start|stop|status]" >&2
    exit 1
    ;;
esac
