#!/usr/bin/env bash
# One-shot launcher for the DSAT apps:
#   - dev stack (PostgreSQL + FastAPI backend + grammar-practice/student app) via podman compose
#   - admin dashboard (APP/ADMIN_APP) as a host Vite dev server
#
# Student/admin are reachable through Tailscale Serve. Port 443 is left untouched
# because BOOKMARKS_LINKS owns it on this node.
#
# Usage:
#   ./start.sh          start everything (reuses whatever is already running)
#   ./start.sh stop     stop the admin dev server and the compose stack
#   ./start.sh status   show what's up and the URLs
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_DIR="$ROOT/APP/ADMIN_APP"
RUN_SH="$ROOT/.claude/skills/dev-stack/run.sh"

BACKEND_PORT="${DSAT_BACKEND_PORT:-8002}"
STUDENT_PORT="${DSAT_STUDENT_PORT:-5174}"
ADMIN_PORT="${DSAT_ADMIN_PORT:-${ADMIN_PORT:-5175}}"
STUDENT_TLS_PORT="${DSAT_STUDENT_TLS_PORT:-8443}"
ADMIN_TLS_PORT="${DSAT_ADMIN_TLS_PORT:-8444}"
ADMIN_TOKEN="${VITE_ADMIN_TOKEN:-admin-test-key}"
BACKEND_ORIGIN="http://127.0.0.1:${BACKEND_PORT}"
ADMIN_PID_FILE="$ROOT/.admin-dashboard.pid"
ADMIN_LOG_FILE="$ROOT/.admin-dashboard.log"

up() { curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:$1$2"; }
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
  tailscale serve --bg --https="${STUDENT_TLS_PORT}" "http://127.0.0.1:${STUDENT_PORT}" >/dev/null 2>&1 || \
    echo "WARN: tailscale serve :${STUDENT_TLS_PORT} failed (Tailscale not up?) — student TLS skipped." >&2
}

# Same idea for the admin dashboard, on https://<node>:8444. Kept on a separate
# port so it doesn't collide with the student (:8443) or bookmarks (:443) configs.
ensure_admin_tls() {
  command -v tailscale >/dev/null 2>&1 || return 0
  tailscale status >/dev/null 2>&1 || return 0
  tailscale serve --bg --https="${ADMIN_TLS_PORT}" "http://127.0.0.1:${ADMIN_PORT}" >/dev/null 2>&1 || \
    echo "WARN: tailscale serve :${ADMIN_TLS_PORT} failed (Tailscale not up?) — admin TLS skipped." >&2
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
  printf '%-26s %-30s %s\n' "Student app (grammar):" "http://127.0.0.1:${STUDENT_PORT}" "$(student_up && echo UP || echo DOWN)"
  printf '%-26s %-30s %s\n' "Admin dashboard:"       "http://127.0.0.1:${ADMIN_PORT}"   "$(admin_up && echo UP || echo DOWN)"
  printf '%-26s %-30s %s\n' "Backend API:"           "${BACKEND_ORIGIN}"                "$(backend_up && echo UP || echo DOWN)"
  if [ -n "$ts" ]; then
    echo "Tailscale (MagicDNS):"
    echo "  student:  http://${ts}:${STUDENT_PORT}"
    echo "  student (TLS):  https://${ts}:${STUDENT_TLS_PORT}"
    echo "  admin:    http://${ts}:${ADMIN_PORT}"
    echo "  admin (TLS):    https://${ts}:${ADMIN_TLS_PORT}"
  fi
}

case "${1:-start}" in
  status)
    summary
    ;;

  stop)
    if [ -f "$ADMIN_PID_FILE" ]; then
      pid="$(cat "$ADMIN_PID_FILE" 2>/dev/null || true)"
      if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "Stopping admin dev server (pid $pid)..."
        kill "$pid" 2>/dev/null || true
      fi
      rm -f "$ADMIN_PID_FILE"
    fi
    if admin_up; then
      echo "Admin dev server still on :${ADMIN_PORT}, force-killing..."
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

    # 2. Admin dashboard on the host, auto-started detached (survives this shell
    #    exiting — a prior foreground `exec` here meant admin died with the
    #    invoking terminal, which is why it kept turning up DOWN).
    if admin_up; then
      echo "Admin dashboard already running on :${ADMIN_PORT}."
      # Re-affirm the Tailscale TLS proxy in case it was dropped.
      ensure_admin_tls
      summary
      exit 0
    fi

    # Clear a stale pidfile/orphaned process from a previous crashed run before
    # launching a fresh one, so we don't leak zombie vite processes.
    if [ -f "$ADMIN_PID_FILE" ]; then
      old_pid="$(cat "$ADMIN_PID_FILE" 2>/dev/null || true)"
      [ -n "$old_pid" ] && kill "$old_pid" 2>/dev/null || true
      rm -f "$ADMIN_PID_FILE"
    fi
    fuser -k "${ADMIN_PORT}/tcp" 2>/dev/null || true

    # Node 20 via NVM (host default), per project convention.
    source "$HOME/.nvm/nvm.sh"
    cd "$ADMIN_DIR"
    [ -d node_modules ] || npm install

    # Wire the admin TLS endpoint before launching — `tailscale serve` just sets
    # the proxy config, so the port doesn't need to be up yet.
    ensure_admin_tls

    echo "Starting admin dashboard on :${ADMIN_PORT} (detached, log: ${ADMIN_LOG_FILE})..."
    nohup env VITE_BACKEND_ORIGIN="$BACKEND_ORIGIN" VITE_ADMIN_TOKEN="$ADMIN_TOKEN" \
      npm run dev -- --host 127.0.0.1 --port "$ADMIN_PORT" --strictPort \
      >"$ADMIN_LOG_FILE" 2>&1 &
    disown
    echo $! >"$ADMIN_PID_FILE"

    for _ in $(seq 1 30); do
      admin_up && break
      sleep 1
    done
    admin_up || echo "WARN: admin dashboard did not come up at :${ADMIN_PORT} within 30s — check ${ADMIN_LOG_FILE}" >&2

    summary
    ;;

  *)
    echo "Usage: $0 [start|stop|status]" >&2
    exit 1
    ;;
esac
