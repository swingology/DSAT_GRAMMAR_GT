#!/usr/bin/env bash
# dev_reset_ingestion.sh
# DEV-ONLY wrapper. Two parts, both behind one confirmation:
#   1. Runs dev_reset_ingestion.sql against the DB in backend/.env (DATABASE_URL).
#   2. Clears on-disk ingestion asset storage so re-ingest starts from scratch.
#
# Usage:
#   scripts/dev_reset_ingestion.sh             # DB + storage, interactive confirm
#   scripts/dev_reset_ingestion.sh --yes       # skip confirmation
#   scripts/dev_reset_ingestion.sh --db-only   # truncate DB, leave files
#   scripts/dev_reset_ingestion.sh --storage-only  # clear files, leave DB
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/backend/.env"
SQL_FILE="$SCRIPT_DIR/dev_reset_ingestion.sql"

# Ingestion asset directories whose CONTENTS are cleared. The directories
# themselves and any .gitkeep files are preserved.
# benchmark-artifacts/ is intentionally NOT listed — it belongs to /benchmark.
STORAGE_DIRS=(
    "$REPO_ROOT/backend/archive/official"
    "$REPO_ROOT/backend/archive/generated"
    "$REPO_ROOT/archive/official"
    "$REPO_ROOT/archive/generated"
    "$REPO_ROOT/local_object_store/raw-sources"
    "$REPO_ROOT/local_object_store/page-renders"
    "$REPO_ROOT/local_object_store/page-crops"
    "$REPO_ROOT/local_object_store/ocr-artifacts"
    "$REPO_ROOT/local_object_store/stimulus-assets"
)

DO_DB=1
DO_STORAGE=1
SKIP_CONFIRM=0
case "${1:-}" in
    --yes)          SKIP_CONFIRM=1 ;;
    --db-only)      DO_STORAGE=0 ;;
    --storage-only) DO_DB=0 ;;
    "")             ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
esac

clear_storage() {
    echo "Clearing on-disk ingestion storage:"
    for dir in "${STORAGE_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            local n
            n="$(find "$dir" -mindepth 1 -type f | wc -l | tr -d ' ')"
            # Depth-first delete of everything inside, then restore .gitkeep
            # so the empty directory survives in git.
            find "$dir" -mindepth 1 -delete
            touch "$dir/.gitkeep"
            echo "  cleared $dir ($n files)"
        else
            mkdir -p "$dir"
            touch "$dir/.gitkeep"
            echo "  recreated $dir (was absent)"
        fi
    done
}

if [[ "$DO_DB" -eq 1 ]]; then
    [[ -f "$ENV_FILE" ]] || { echo "ERROR: $ENV_FILE not found" >&2; exit 1; }
    [[ -f "$SQL_FILE" ]] || { echo "ERROR: $SQL_FILE not found" >&2; exit 1; }
    # Pull DATABASE_URL from backend/.env and strip the SQLAlchemy +asyncpg
    # driver suffix so psql accepts it.
    DB_URL="$(grep -E '^DATABASE_URL=' "$ENV_FILE" | tail -1 | cut -d= -f2-)"
    [[ -n "$DB_URL" ]] || { echo "ERROR: DATABASE_URL not set in $ENV_FILE" >&2; exit 1; }
    PSQL_URL="${DB_URL/+asyncpg/}"
    echo "Target database: $PSQL_URL"
fi

echo "This will:"
[[ "$DO_DB" -eq 1 ]]      && echo "  - TRUNCATE all ingested question data (users are kept)"
[[ "$DO_STORAGE" -eq 1 ]] && echo "  - DELETE on-disk asset files in archive/ and local_object_store/"

if [[ "$SKIP_CONFIRM" -ne 1 ]]; then
    read -r -p "Type 'reset' to proceed: " confirm
    [[ "$confirm" == "reset" ]] || { echo "Aborted."; exit 1; }
fi

if [[ "$DO_DB" -eq 1 ]]; then
    psql "$PSQL_URL" -v ON_ERROR_STOP=1 -f "$SQL_FILE"
fi

if [[ "$DO_STORAGE" -eq 1 ]]; then
    clear_storage
    echo 'On-disk ingestion storage cleared.'
fi
