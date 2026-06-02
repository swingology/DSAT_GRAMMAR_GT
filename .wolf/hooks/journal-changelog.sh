#!/usr/bin/env bash
# Shared helper: append a session recovery snapshot to CHANGELOG.md
# and log a SNAP entry to agent.log.
# Usage: source this file, then call: write_changelog_snapshot "$PROJ" "$TRIGGER"

write_changelog_snapshot() {
  local PROJ="${1:-${CLAUDE_PROJECT_DIR:-$(pwd)}}"
  local TRIGGER="${2:-manual}"
  local CHANGELOG="$PROJ/CHANGELOG.md"
  local LOG="$PROJ/.wolf/agent.log"
  [[ -f "$CHANGELOG" ]] || return 0

  local TS BRANCH HASH RAM DIFF_STAT CHANGED_FILES UNTRACKED
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  BRANCH=$(git -C "$PROJ" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-repo")
  HASH=$(git -C "$PROJ" rev-parse --short HEAD 2>/dev/null || echo "-------")
  RAM=$(free -h | awk '/^Mem:/ {printf "%s/%s", $3, $2}')
  DIFF_STAT=$(git -C "$PROJ" diff --stat HEAD 2>/dev/null | tail -1 || echo "no changes")
  CHANGED_FILES=$(git -C "$PROJ" diff --name-only HEAD 2>/dev/null | head -20 | tr '\n' ' ' || echo "")
  UNTRACKED=$(git -C "$PROJ" ls-files --others --exclude-standard 2>/dev/null | head -5 | tr '\n' ' ' || echo "")

  printf '%s | SNAP | changelog    | ram=%-12s | trigger=%s branch=%s@%s\n' \
    "$TS" "$RAM" "$TRIGGER" "$BRANCH" "$HASH" >> "$LOG"

  {
    printf '\n## Session snapshot — %s (%s)\n' "$TS" "$TRIGGER"
    printf '_branch:_ `%s` · _commit:_ `%s` · _ram:_ `%s`\n\n' "$BRANCH" "$HASH" "$RAM"
    if [[ -n "$CHANGED_FILES" ]]; then
      printf '**Uncommitted changes:** %s\n' "$CHANGED_FILES"
      printf '_(%s)_\n' "$DIFF_STAT"
    else
      printf '_No uncommitted changes._\n'
    fi
    [[ -n "$UNTRACKED" ]] && printf '\n**Untracked:** %s\n' "$UNTRACKED"
    printf '\n---\n'
  } >> "$CHANGELOG"
}
