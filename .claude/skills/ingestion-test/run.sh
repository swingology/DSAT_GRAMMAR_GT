#!/usr/bin/env bash
# Ingestion pipeline test runner — used by the /ingestion-test skill.
# Self-contained so the whole flow is a single allowlistable command.
#
# Usage:  run.sh <TARGET>
#   <TARGET> = a PDF stem (e.g. Test_4_digital_sec01_mod01)
#            | "full"  → runs backend/run_full_ingestion.sh
#            | empty   → defaults to Test_1_digital_sec01_mod01
#
# Emits a JSON summary on the last line prefixed with "RESULT_JSON:" and
# leaves the server running ONLY if it was already up; a server it starts
# itself is stopped on exit.

set -uo pipefail

ROOT="/home/jb/DSAT_REDUX_MD"
BACKEND="$ROOT/backend"
PDF_DIR_2025="$ROOT/TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL"
PDF_DIR_2024="$ROOT/TESTS/DATA_SRC/2024-2025 Tests Answers"
API="http://localhost:8000"
KEY="${ADMIN_API_KEY:-admin-test-key}"
# DB port: env override → backend/.env DATABASE_URL → default 5437.
# Avoids the 5434/5437 host-port drift between this runner and docker-compose (bug-765).
DB_PORT="${DB_PORT:-$(grep -oE 'localhost:[0-9]+' "$BACKEND/.env" 2>/dev/null | grep -oE '[0-9]+' | head -1)}"
DB_PORT="${DB_PORT:-5437}"
TARGET="${1:-Test_1_digital_sec01_mod01}"
STARTED_SERVER=0
SERVER_PID=""
KEEP_SERVER_ON_EXIT=0
POLL_TIMEOUT=false

log() { echo "[$(date +%H:%M:%S)] $*"; }

cleanup() {
    if [[ "$STARTED_SERVER" == "1" && -n "$SERVER_PID" ]]; then
        if [[ "$KEEP_SERVER_ON_EXIT" == "1" ]]; then
            log "leaving self-started server running (pid $SERVER_PID) because job is still active"
            return
        fi
        log "stopping server (pid $SERVER_PID)"
        kill "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# --- 1. Prerequisites -------------------------------------------------------
cd "$BACKEND" || { echo "RESULT_JSON:{\"error\":\"backend dir missing\"}"; exit 1; }

if ! PGPASSWORD=dsat_dev psql -h localhost -p "$DB_PORT" -U dsat -d dsat_dev -c '\q' 2>/dev/null; then
    log "Postgres down — starting db container"
    (cd "$ROOT" && docker compose up -d db) || true
    for _ in $(seq 1 20); do
        PGPASSWORD=dsat_dev psql -h localhost -p "$DB_PORT" -U dsat -d dsat_dev -c '\q' 2>/dev/null && break
        sleep 3
    done
fi
if ! PGPASSWORD=dsat_dev psql -h localhost -p "$DB_PORT" -U dsat -d dsat_dev -c '\q' 2>/dev/null; then
    echo "RESULT_JSON:{\"error\":\"postgres unavailable\"}"; exit 1
fi

if [[ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:11434/ 2>/dev/null)" != "200" ]]; then
    echo "RESULT_JSON:{\"error\":\"ollama not reachable on :11434\"}"; exit 1
fi

# --- 2. API server ----------------------------------------------------------
if [[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/" 2>/dev/null)" == "200" ]]; then
    log "reusing server already running on :8000"
else
    log "starting API server"
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/dsat_server.log 2>&1 &
    SERVER_PID=$!
    STARTED_SERVER=1
    for _ in $(seq 1 30); do
        [[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/" 2>/dev/null)" == "200" ]] && break
        sleep 2
    done
    if [[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/" 2>/dev/null)" != "200" ]]; then
        echo "RESULT_JSON:{\"error\":\"server failed to start\",\"log\":\"/tmp/dsat_server.log\"}"; exit 1
    fi
fi

# --- 3. Full-batch mode -----------------------------------------------------
if [[ "$TARGET" == "full" ]]; then
    log "running full batch"
    bash "$BACKEND/run_full_ingestion.sh"
    echo "RESULT_JSON:{\"mode\":\"full\",\"results_dir\":\"/tmp/ingestion_results\"}"
    exit 0
fi

# --- 3b. Single-PDF submit --------------------------------------------------
# Resolve PDF path: try 2025-2026 VERBAL dir first, then 2024-2025 dir.
if [[ -f "$PDF_DIR_2025/${TARGET}.pdf" ]]; then
    PDF="$PDF_DIR_2025/${TARGET}.pdf"
    RELEASE_YEAR=2025
elif [[ -f "$PDF_DIR_2024/${TARGET}.pdf" ]]; then
    PDF="$PDF_DIR_2024/${TARGET}.pdf"
    RELEASE_YEAR=2024
else
    echo "RESULT_JSON:{\"error\":\"pdf not found in 2025-2026 VERBAL or 2024-2025 dirs: ${TARGET}.pdf\"}"; exit 1
fi
log "resolved pdf: $PDF (year=$RELEASE_YEAR)"

EXAM=$(echo "$TARGET"    | sed -E 's/[Tt]est_?([0-9]+).*/\1/')
SECTION=$(echo "$TARGET" | sed -E 's/.*[Ss]ec([0-9]+).*/\1/')
MODULE=$(echo "$TARGET"  | sed -E 's/.*[Mm]od([0-9]+).*/\1/')

log "submitting $TARGET (exam=$EXAM section=$SECTION module=$MODULE)"
SUBMIT=$(curl -s -X POST "$API/ingest/official/pdf" -H "X-API-Key: $KEY" \
    -F "file=@$PDF" -F "source_exam_code=$EXAM" -F "source_subject_code=verbal" \
    -F "source_section_code=$SECTION" -F "source_module_code=$MODULE" \
    -F "source_release_year=$RELEASE_YEAR")
JOB=$(echo "$SUBMIT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id') or d.get('job_id') or '')" 2>/dev/null)
[[ -n "$JOB" ]] || { echo "RESULT_JSON:{\"error\":\"no job_id\",\"response\":$(echo "$SUBMIT" | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read()))')}"; exit 1; }
log "job_id=$JOB"

# --- 4. Poll ----------------------------------------------------------------
STATUS="pending"
PIPELINE_TIMEOUT_S="${PIPELINE_TIMEOUT_S:-}"
if [[ -z "$PIPELINE_TIMEOUT_S" ]]; then
    PIPELINE_TIMEOUT_S=$(uv run python -c 'from app.config import get_settings; print(get_settings().pipeline_timeout_s)' 2>/dev/null || true)
fi
[[ "$PIPELINE_TIMEOUT_S" =~ ^[0-9]+$ ]] || PIPELINE_TIMEOUT_S=10800
POLL_INTERVAL_S="${INGESTION_TEST_POLL_INTERVAL_S:-15}"
[[ "$POLL_INTERVAL_S" =~ ^[0-9]+$ && "$POLL_INTERVAL_S" -gt 0 ]] || POLL_INTERVAL_S=15
POLL_GRACE_S="${INGESTION_TEST_POLL_GRACE_S:-300}"
[[ "$POLL_GRACE_S" =~ ^[0-9]+$ ]] || POLL_GRACE_S=300
POLL_DEADLINE_S=$((PIPELINE_TIMEOUT_S + POLL_GRACE_S))
POLL_ATTEMPTS=$(((POLL_DEADLINE_S + POLL_INTERVAL_S - 1) / POLL_INTERVAL_S))
log "polling for up to ${POLL_DEADLINE_S}s (${POLL_ATTEMPTS} × ${POLL_INTERVAL_S}s; pipeline_timeout_s=${PIPELINE_TIMEOUT_S})"
for _ in $(seq 1 "$POLL_ATTEMPTS"); do
    sleep "$POLL_INTERVAL_S"
    STATUS=$(curl -s -H "X-API-Key: $KEY" "$API/ingest/jobs/$JOB" \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
    log "status=$STATUS"
    case "$STATUS" in approved|needs_review|failed) break;; esac
done
case "$STATUS" in
    approved|needs_review|failed) ;;
    *)
        POLL_TIMEOUT=true
        KEEP_SERVER_ON_EXIT="$STARTED_SERVER"
        log "poll deadline reached with non-terminal status=$STATUS"
        ;;
esac

# --- 5. Collect validation errors ------------------------------------------
ERR_COUNTS=$(PGPASSWORD=dsat_dev psql -h localhost -p "$DB_PORT" -U dsat -d dsat_dev -tA -F'|' -c \
  "SELECT e->>'step', count(*) FROM question_jobs, jsonb_array_elements(validation_errors_jsonb) e WHERE id='$JOB' GROUP BY 1;" 2>/dev/null)
CREATED=$(PGPASSWORD=dsat_dev psql -h localhost -p "$DB_PORT" -U dsat -d dsat_dev -tA -c \
  "SELECT count(*) FROM question_job_questions WHERE job_id='$JOB';" 2>/dev/null)
EXTRACTED=$(PGPASSWORD=dsat_dev psql -h localhost -p "$DB_PORT" -U dsat -d dsat_dev -tA -c \
  "SELECT pass1_json->>'_extracted_count' FROM question_jobs WHERE id='$JOB';" 2>/dev/null)

echo "=== validation error counts by step ==="
echo "${ERR_COUNTS:-（none）}"
echo "=== representative errors ==="
PGPASSWORD=dsat_dev psql -h localhost -p "$DB_PORT" -U dsat -d dsat_dev -c \
  "SELECT DISTINCT ON (e->>'step') jsonb_pretty(e) FROM question_jobs, jsonb_array_elements(validation_errors_jsonb) e WHERE id='$JOB';" 2>/dev/null

echo "RESULT_JSON:{\"mode\":\"single\",\"target\":\"$TARGET\",\"job_id\":\"$JOB\",\"status\":\"$STATUS\",\"poll_timeout\":$POLL_TIMEOUT,\"extracted\":\"${EXTRACTED:-?}\",\"created\":\"${CREATED:-0}\"}"
