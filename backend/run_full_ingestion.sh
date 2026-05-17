#!/usr/bin/env bash
# Full ingestion test — submits all official verbal test PDFs and tracks outcomes.
set -euo pipefail

API_BASE="http://localhost:8000"
API_KEY="admin-test-key"
PDF_DIR="../TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL"
RESULTS_DIR="/tmp/ingestion_results"
mkdir -p "$RESULTS_DIR"

# Map PDF filenames to their metadata codes
# Format: Test_N_digital_sec01_mod01.pdf → exam=N, subject=verbal, section=01, module=01
declare -A JOBS

echo "=== FULL INGESTION TEST $(date -Iseconds) ==="
echo ""

submit_and_track() {
    local pdf="$1"
    local exam_code="$2"
    local section="$3"
    local module="$4"
    local pdf_path="$PDF_DIR/$pdf"
    local outfile="$RESULTS_DIR/${pdf%.pdf}.json"

    if [[ ! -f "$pdf_path" ]]; then
        echo "SKIP: $pdf — file not found"
        return
    fi

    echo "SUBMIT: $pdf (exam=$exam_code, section=$section, module=$module)"

    # Submit the PDF
    local response
    response=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_BASE/ingest/official/pdf" \
        -H "X-API-Key: $API_KEY" \
        -F "file=@$pdf_path" \
        -F "source_exam_code=$exam_code" \
        -F "source_subject_code=verbal" \
        -F "source_section_code=$section" \
        -F "source_module_code=$module" \
        2>&1)

    local http_code=$(echo "$response" | tail -1)
    local body=$(echo "$response" | sed '$d')

    echo "  HTTP $http_code"

    if [[ "$http_code" != "200" ]]; then
        echo "  ERROR: Submission failed — $body"
        echo "{\"pdf\":\"$pdf\",\"status\":\"submit_failed\",\"http_code\":$http_code,\"error\":$(echo "$body" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '"unknown"')}" > "$outfile"
        return
    fi

    # Extract job_id
    local job_id=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job_id','') or d.get('id',''))" 2>/dev/null || echo "")
    if [[ -z "$job_id" ]]; then
        echo "  ERROR: No job_id in response — $body"
        echo "{\"pdf\":\"$pdf\",\"status\":\"no_job_id\",\"response\":$(echo "$body" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '"unknown"')}" > "$outfile"
        return
    fi

    echo "  JOB_ID: $job_id"
    local status="pending"
    local max_wait=600  # 10 minutes max per job
    local elapsed=0

    # Poll until terminal state
    while [[ "$status" == "pending" || "$status" == "parsing" || "$status" == "extracting" || "$status" == "annotating" || "$status" == "validating" || "$status" == "overlap_checking" ]]; do
        sleep 10
        elapsed=$((elapsed + 10))

        if [[ $elapsed -ge $max_wait ]]; then
            echo "  TIMEOUT: Job still $status after ${max_wait}s"
            status="timeout"
            break
        fi

        local poll_body
        poll_body=$(curl -s -H "X-API-Key: $API_KEY" "$API_BASE/ingest/jobs/$job_id" 2>&1)
        status=$(echo "$poll_body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null || echo "unknown")

        echo "  [$((elapsed))s] status=$status"

        # Save intermediate result
        if [[ "$status" == "approved" || "$status" == "needs_review" || "$status" == "failed" || "$status" == "timeout" ]]; then
            break
        fi
    done

    # Save final result
    local final_body
    final_body=$(curl -s -H "X-API-Key: $API_KEY" "$API_BASE/ingest/jobs/$job_id" 2>&1)
    echo "$final_body" > "$outfile"

    local num_questions
    num_questions=$(echo "$final_body" | python3 -c "
import sys, json
d = json.load(sys.stdin)
qs = d.get('questions', [])
print(len(qs))
" 2>/dev/null || echo "0")

    local error_msg
    error_msg=$(echo "$final_body" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('error', '') or '')
" 2>/dev/null || echo "parse_error")

    echo "  RESULT: status=$status, questions=$num_questions, error='$error_msg'"
    echo ""
}

# Process all 18 PDFs
for pdf in "$PDF_DIR"/Test_*_digital_sec*.pdf; do
    filename=$(basename "$pdf")

    # Parse: Test_N_digital_secMM_modMM.pdf
    # Extract exam number
    exam=$(echo "$filename" | sed -E 's/Test_([0-9]+)_digital.*/\1/')
    section=$(echo "$filename" | sed -E 's/.*_sec([0-9]+)_.*/\1/')
    module=$(echo "$filename" | sed -E 's/.*_mod([0-9]+)\.pdf/\1/')

    submit_and_track "$filename" "$exam" "$section" "$module"
done

echo ""
echo "=== INGESTION TEST COMPLETE ==="
echo "Results saved to $RESULTS_DIR/"
echo ""

# Summary
echo "=== SUMMARY ==="
python3 -c "
import json, os, sys
results_dir = '$RESULTS_DIR'
total = 0
approved = 0
needs_review = 0
failed = 0
timeout = 0
submit_failed = 0
errors = []

for f in sorted(os.listdir(results_dir)):
    if not f.endswith('.json'):
        continue
    total += 1
    try:
        with open(os.path.join(results_dir, f)) as fh:
            d = json.load(fh)
        status = d.get('status', 'unknown')
        error = d.get('error', '') or ''
        questions = len(d.get('questions', []))

        if status == 'approved':
            approved += 1
        elif status == 'needs_review':
            needs_review += 1
        elif status == 'failed':
            failed += 1
            if error:
                errors.append((f, error))
        elif status == 'submit_failed':
            submit_failed += 1
        elif status == 'timeout':
            timeout += 1

        print(f'  {f}: status={status}, questions={questions}, error={repr(error)[:100]}')
    except Exception as e:
        print(f'  {f}: PARSE ERROR — {e}')

print()
print(f'Total: {total}')
print(f'Approved: {approved}')
print(f'Needs Review: {needs_review}')
print(f'Failed: {failed}')
print(f'Submit Failed: {submit_failed}')
print(f'Timeout: {timeout}')
print()
if errors:
    print('ERROR DETAILS:')
    for f, err in errors:
        print(f'  {f}: {err[:200]}')
"