#!/usr/bin/env bash
# Appends a PRE-tool entry to .wolf/agent.log before Bash/Write/Edit executes.
set -euo pipefail

PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG="$PROJ/.wolf/agent.log"

INPUT=$(cat)
TOOL=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
TARGET=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
inp=d.get('tool_input',{})
v=inp.get('file_path', inp.get('path', inp.get('command','')))
print(str(v).replace('\n',' ').replace('\r','')[:80])" 2>/dev/null || echo "")
RAM=$(free -h | awk '/^Mem:/ {printf "%s/%s", $3, $2}')
TS=$(date '+%Y-%m-%d %H:%M:%S')

printf '%s | PRE  | %-12s | ram=%-12s | %s\n' "$TS" "$TOOL" "$RAM" "$TARGET" >> "$LOG"
