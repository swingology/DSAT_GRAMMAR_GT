#!/usr/bin/env bash
# Appends a POST-tool entry to .wolf/agent.log after Write/Edit completes.
# Tracks cumulative bytes written; fires a CHANGELOG snapshot at 50KB.
set -euo pipefail

BYTES_THRESHOLD=51200
PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG="$PROJ/.wolf/agent.log"
STATE_FILE="/tmp/claude_session_bytes_${CLAUDE_SESSION_ID:-default}"

INPUT=$(cat)
TOOL=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
FILE=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
inp=d.get('tool_input',{})
print(inp.get('file_path', inp.get('path','')))" 2>/dev/null || echo "")
RAM=$(free -h | awk '/^Mem:/ {printf "%s/%s", $3, $2}')
TS=$(date '+%Y-%m-%d %H:%M:%S')

printf '%s | POST | %-12s | ram=%-12s | %s\n' "$TS" "$TOOL" "$RAM" "$FILE" >> "$LOG"

# Accumulate bytes written; snapshot CHANGELOG at 50KB
if [[ -n "$FILE" && -f "$FILE" ]]; then
  FILE_BYTES=$(stat -c%s "$FILE" 2>/dev/null || echo 0)
  PREV=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
  NEW=$(( PREV + FILE_BYTES ))
  printf '%d' "$NEW" > "$STATE_FILE"

  if (( NEW >= BYTES_THRESHOLD )); then
    printf '0' > "$STATE_FILE"
    source "$(dirname "$0")/journal-changelog.sh"
    write_changelog_snapshot "$PROJ" "50kb-written"
  fi
fi
