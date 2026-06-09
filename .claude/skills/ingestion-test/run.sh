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
PDF_DIR="$ROOT/TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL"
API="http://localhost:8000"
KEY="${ADMIN_API_KEY:-admin-test-key}"
TARGET="${1:-Test_1_digital_sec01_mod01}"
STARTED_SERVER=0
SERVER_PID=""

log() { echo "[$(date +%H:%M:%S)] $*"; }

cleanup() {
    if [[ "$STARTED_SERVER" == "1" && -n "$SERVER_PID" ]]; then
        log "stopping server (pid $SERVER_PID)"
        kill "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# --- 1. Prerequisites -------------------------------------------------------
cd "$BACKEND" || { echo "RESULT_JSON:{\"error\":\"backend dir missing\"}"; exit 1; }

if ! PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -c '\q' 2>/dev/null; then
    log "Postgres down — starting db container"
    (cd "$ROOT" && docker compose up -d db) || true
    for _ in $(seq 1 20); do
        PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -c '\q' 2>/dev/null && break
        sleep 3
    done
fi
if ! PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -c '\q' 2>/dev/null; then
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
PDF="$PDF_DIR/${TARGET}.pdf"
[[ -f "$PDF" ]] || { echo "RESULT_JSON:{\"error\":\"pdf not found: $PDF\"}"; exit 1; }

EXAM=$(echo "$TARGET"    | sed -E 's/[Tt]est_?([0-9]+).*/\1/')
SECTION=$(echo "$TARGET" | sed -E 's/.*[Ss]ec([0-9]+).*/\1/')
MODULE=$(echo "$TARGET"  | sed -E 's/.*[Mm]od([0-9]+).*/\1/')

log "submitting $TARGET (exam=$EXAM section=$SECTION module=$MODULE)"
SUBMIT=$(curl -s -X POST "$API/ingest/official/pdf" -H "X-API-Key: $KEY" \
    -F "file=@$PDF" -F "source_exam_code=$EXAM" -F "source_subject_code=verbal" \
    -F "source_section_code=$SECTION" -F "source_module_code=$MODULE" \
    -F "source_release_year=2025")
JOB=$(echo "$SUBMIT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id') or d.get('job_id') or '')" 2>/dev/null)
[[ -n "$JOB" ]] || { echo "RESULT_JSON:{\"error\":\"no job_id\",\"response\":$(echo "$SUBMIT" | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read()))')}"; exit 1; }
log "job_id=$JOB"

# --- 4. Poll ----------------------------------------------------------------
STATUS="pending"
for _ in $(seq 1 120); do   # 120 × 15s = 30 min cap
    sleep 15
    STATUS=$(curl -s -H "X-API-Key: $KEY" "$API/ingest/jobs/$JOB" \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
    log "status=$STATUS"
    case "$STATUS" in approved|needs_review|failed) break;; esac
done

# --- 5. Collect validation errors ------------------------------------------
ERR_COUNTS=$(PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -tA -F'|' -c \
  "SELECT e->>'step', count(*) FROM question_jobs, jsonb_array_elements(validation_errors_jsonb) e WHERE id='$JOB' GROUP BY 1;" 2>/dev/null)
CREATED=$(PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -tA -c \
  "SELECT count(*) FROM question_job_questions WHERE job_id='$JOB';" 2>/dev/null)
EXTRACTED=$(PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -tA -c \
  "SELECT pass1_json->>'_extracted_count' FROM question_jobs WHERE id='$JOB';" 2>/dev/null)

echo "=== validation error counts by step ==="
echo "${ERR_COUNTS:-（none）}"
echo "=== representative errors ==="
PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev -c \
  "SELECT DISTINCT ON (e->>'step') jsonb_pretty(e) FROM question_jobs, jsonb_array_elements(validation_errors_jsonb) e WHERE id='$JOB';" 2>/dev/null

echo "RESULT_JSON:{\"mode\":\"single\",\"target\":\"$TARGET\",\"job_id\":\"$JOB\",\"status\":\"$STATUS\",\"extracted\":\"${EXTRACTED:-?}\",\"created\":\"${CREATED:-0}\"}"
