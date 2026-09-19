#!/usr/bin/env python3
"""Read one DSAT question and its latest annotation from the dev database."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fetch_question.py QUESTION_UUID", file=sys.stderr)
        return 2
    try:
        question_id = str(uuid.UUID(sys.argv[1]))
    except ValueError:
        print("question_id must be a UUID", file=sys.stderr)
        return 2

    dsn = os.environ.get("DSAT_DATABASE_URL")
    query = f"""
        SELECT jsonb_build_object(
            'retrieved_at', CURRENT_TIMESTAMP,
            'database', current_database(),
            'question', to_jsonb(q),
            'version', to_jsonb(v),
            'annotation', to_jsonb(a),
            'stimulus_assets', COALESCE((
                SELECT jsonb_agg(to_jsonb(s) ORDER BY s.id)
                FROM question_stimulus_assets s WHERE s.question_id = q.id
            ), '[]'::jsonb),
            'options', COALESCE((
                SELECT jsonb_agg(to_jsonb(o) ORDER BY o.option_label)
                FROM question_options o
                WHERE o.question_version_id = q.latest_version_id
            ), '[]'::jsonb)
        )
        FROM questions q
        LEFT JOIN question_versions v ON v.id = q.latest_version_id
        LEFT JOIN question_annotations a ON a.id = q.latest_annotation_id
        WHERE q.id = '{question_id}'::uuid
    """
    try:
        readonly = "-c default_transaction_read_only=on -c statement_timeout=8000"
        command = ["psql"] if dsn else [
            "podman", "exec", "-e", f"PGOPTIONS={readonly}",
            "dsat-db", "psql", "-U", "dsat", "-d", "dsat_dev",
        ]
        result = subprocess.run(
            command + ["-X", "-At", "-v", "ON_ERROR_STOP=1", "-c", query],
            env={**os.environ, **({"PGDATABASE": dsn} if dsn else {}),
                 "PGOPTIONS": readonly,
                 "PGCONNECT_TIMEOUT": "5"},
            check=False, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("Could not run psql or the database request timed out.", file=sys.stderr)
        return 1
    if result.returncode:
        print("Database query failed; check DSAT_DATABASE_URL and database availability.", file=sys.stderr)
        return 1
    raw = result.stdout.strip()
    if not raw:
        print(f"question not found: {question_id}", file=sys.stderr)
        return 1
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print("Database returned invalid JSON.", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
