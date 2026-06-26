#!/usr/bin/env python3
"""
Bulk re-annotate all official questions using v7 grammar + v2 reading rules.

This script calls the backend's /reannotate/{question_id} endpoint for every
question with content_origin='official', replacing their v3 annotations with
fresh v7-stamped annotations.

Usage:
  cd backend
  uv run python ../scripts/reannotate_official_v7.py [--dry-run] [--limit N]
                                                      [--provider ollama]
                                                      [--model deepseek-v4-pro:cloud]
                                                      [--base-url http://localhost:8000]
                                                      [--api-key admin-key-change-me]

The script polls each job until it reaches a terminal state (approved /
needs_review / failed), then moves to the next. A summary is written to
analysis/calibration/reannotation_report.json at the end.
"""

import argparse
import json
import os
import sys
import time
import psycopg2
import psycopg2.extras
import urllib.request
import urllib.error

DB_DSN = "postgresql://dsat:dsat_dev@localhost:5437/dsat_dev"
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_KEY = "admin-key-change-me"
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "deepseek-v4-pro:cloud"

TERMINAL_STATUSES = {"approved", "needs_review", "failed"}
POLL_INTERVAL_S = 3
JOB_TIMEOUT_S = 120


def _api(method: str, path: str, base_url: str, api_key: str, body: dict | None = None):
    url = base_url.rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {url}: {body_text}") from e


V7_RULES = "rules_agent_dsat_grammar_ingestion_generation_v7"


def fetch_official_question_ids(conn, skip_v7: bool = False) -> list[tuple[str, str]]:
    """Return list of (question_id, source_exam_code) for official questions.

    If skip_v7=True, excludes questions that already have a v7 annotation as
    their latest_annotation_id — allows resumable batched runs.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        if skip_v7:
            cur.execute("""
                SELECT q.id, q.source_exam_code
                FROM questions q
                LEFT JOIN question_annotations a ON a.id = q.latest_annotation_id
                WHERE q.content_origin = 'official'
                  AND (a.rules_version IS NULL OR a.rules_version != %s)
                ORDER BY q.source_exam_code, q.source_question_number
            """, (V7_RULES,))
        else:
            cur.execute("""
                SELECT q.id, q.source_exam_code
                FROM questions q
                WHERE q.content_origin = 'official'
                ORDER BY q.source_exam_code, q.source_question_number
            """)
        return [(str(r["id"]), r["source_exam_code"]) for r in cur.fetchall()]


def submit_reannotate(question_id: str, base_url: str, api_key: str, provider: str, model: str) -> str:
    resp = _api(
        "POST",
        f"/ingest/reannotate/{question_id}",
        base_url,
        api_key,
        body={"provider_name": provider, "model_name": model},
    )
    return resp["id"]  # job_id


def poll_job(job_id: str, base_url: str, api_key: str) -> str:
    """Poll until terminal status; return final status string."""
    deadline = time.monotonic() + JOB_TIMEOUT_S
    while time.monotonic() < deadline:
        resp = _api("GET", f"/ingest/jobs/{job_id}", base_url, api_key)
        status = resp.get("status", "unknown")
        if status in TERMINAL_STATUSES:
            return status
        time.sleep(POLL_INTERVAL_S)
    return "timeout"


def main():
    parser = argparse.ArgumentParser(description="Bulk re-annotate official questions with v7 rules")
    parser.add_argument("--dry-run", action="store_true", help="List questions; do not submit jobs")
    parser.add_argument("--limit", type=int, default=0, help="Max questions to process (0 = all)")
    parser.add_argument("--skip-v7", action="store_true", help="Skip questions already annotated with v7 rules (enables resumable batches)")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--concurrent", type=int, default=1,
                        help="Number of concurrent reannotation jobs (default 1 = sequential)")
    args = parser.parse_args()

    conn = psycopg2.connect(DB_DSN)
    question_ids = fetch_official_question_ids(conn, skip_v7=args.skip_v7)
    conn.close()

    total = len(question_ids)
    if args.limit:
        question_ids = question_ids[: args.limit]

    print(f"Found {total} official questions. Processing {len(question_ids)}.")

    if args.dry_run:
        for qid, exam in question_ids[:20]:
            print(f"  {exam}  {qid}")
        if len(question_ids) > 20:
            print(f"  ... and {len(question_ids) - 20} more")
        return

    results = []
    approved = failed = needs_review = timeout_count = 0

    for i, (qid, exam) in enumerate(question_ids, 1):
        print(f"[{i}/{len(question_ids)}] {exam} {qid} ... ", end="", flush=True)
        try:
            job_id = submit_reannotate(qid, args.base_url, args.api_key, args.provider, args.model)
            status = poll_job(job_id, args.base_url, args.api_key)
        except Exception as exc:
            status = f"error: {exc}"

        print(status)
        results.append({"question_id": qid, "exam": exam, "job_status": status})

        if status == "approved":
            approved += 1
        elif status == "needs_review":
            needs_review += 1
        elif status == "timeout":
            timeout_count += 1
        else:
            failed += 1

    print()
    print(f"Done. approved={approved}, needs_review={needs_review}, failed={failed}, timeout={timeout_count}")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "analysis", "calibration")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "reannotation_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "total_processed": len(question_ids),
            "approved": approved,
            "needs_review": needs_review,
            "failed": failed,
            "timeout": timeout_count,
            "provider": args.provider,
            "model": args.model,
            "rules_version": "rules_agent_dsat_grammar_ingestion_generation_v7",
            "prompt_version": "v7.0",
            "results": results,
        }, f, indent=2)
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
