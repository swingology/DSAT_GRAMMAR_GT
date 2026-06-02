#!/usr/bin/env bash
# On session stop: append STOP entry to agent.log, write CHANGELOG snapshot,
# then clear the byte counter.
set -euo pipefail

PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG="$PROJ/.wolf/agent.log"
STATE_FILE="/tmp/claude_session_bytes_${CLAUDE_SESSION_ID:-default}"

BRANCH=$(git -C "$PROJ" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-repo")
HASH=$(git -C "$PROJ" rev-parse --short HEAD 2>/dev/null || echo "-------")
RAM=$(free -h | awk '/^Mem:/ {printf "%s/%s", $3, $2}')
TS=$(date '+%Y-%m-%d %H:%M:%S')

printf '%s | STOP | session      | ram=%-12s | branch=%s@%s\n' \
  "$TS" "$RAM" "$BRANCH" "$HASH" >> "$LOG"
printf '%s | ---- | ------------ | ----------------------------------------\n' \
  "$TS" >> "$LOG"

source "$(dirname "$0")/journal-changelog.sh"
write_changelog_snapshot "$PROJ" "session-end"

rm -f "$STATE_FILE"
