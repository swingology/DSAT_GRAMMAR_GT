#!/usr/bin/env python3
"""View and resolve entries in the span_review_queue table.

Usage:
  cd backend
  uv run python ../scripts/review_span_queue.py [options]

Options:
  --error-type TEXT   Filter by error_type column
  --show-raw          Include raw_llm_output JSON in output
  --resolve UUID      Mark a queue entry as resolved
  --note TEXT         Resolution note (used with --resolve)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

DB_DSN = "postgresql://dsat:dsat_dev@localhost:5434/dsat_dev"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_unresolved(
    conn,
    error_type: str | None = None,
) -> list[dict]:
    """Return all unresolved span_review_queue rows, with question text snippet."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        query = """
            SELECT
                srq.id,
                srq.question_id,
                srq.annotation_id,
                srq.error_type,
                srq.error_detail,
                srq.raw_llm_output,
                srq.created_at,
                LEFT(q.current_question_text, 50) AS question_snippet
            FROM span_review_queue srq
            LEFT JOIN questions q ON q.id = srq.question_id
            WHERE srq.resolved_at IS NULL
        """
        params: list = []
        if error_type:
            query += " AND srq.error_type = %s"
            params.append(error_type)
        query += " ORDER BY srq.error_type, srq.created_at"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def display_queue(rows: list[dict], show_raw: bool) -> None:
    """Print grouped table of unresolved entries."""
    if not rows:
        print("span_review_queue — no unresolved entries")
        return

    print(f"span_review_queue — {len(rows)} unresolved entries")
    print()

    # Group by error_type
    groups: dict[str, list[dict]] = {}
    for row in rows:
        et = row["error_type"] or "unknown"
        groups.setdefault(et, []).append(row)

    for error_type, group_rows in sorted(groups.items()):
        print(f"{error_type} ({len(group_rows)}):")
        for row in group_rows:
            entry_id = str(row["id"])
            snippet = (row["question_snippet"] or "").replace("\n", " ").strip()
            created = ""
            if row["created_at"]:
                # Format as YYYY-MM-DD HH:MM
                created = row["created_at"].strftime("%Y-%m-%d %H:%M")

            detail = row.get("error_detail") or ""

            print(f"  [{entry_id}] Q: \"{snippet}\" | {detail} | {created}")

            if show_raw and row.get("raw_llm_output"):
                raw_str = json.dumps(row["raw_llm_output"], indent=4)
                # Indent each line for readability
                for line in raw_str.splitlines():
                    print(f"      {line}")

        print()


def resolve_entry(conn, entry_id: str, note: str | None) -> None:
    """Mark a span_review_queue entry as resolved."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE span_review_queue
            SET
                resolved_at    = %s,
                resolved_by    = 'manual',
                resolution_note = %s
            WHERE id = %s
              AND resolved_at IS NULL
            RETURNING id
            """,
            (_now_iso(), note or "", entry_id),
        )
        updated = cur.fetchone()
        conn.commit()

    if updated:
        print(f"Resolved entry {entry_id}.")
    else:
        print(
            f"No unresolved entry found with id={entry_id}. "
            "It may already be resolved or the UUID is wrong."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="View and resolve entries in the span_review_queue table."
    )
    parser.add_argument(
        "--error-type",
        default=None,
        metavar="TEXT",
        help="Filter displayed entries by error_type",
    )
    parser.add_argument(
        "--show-raw",
        action="store_true",
        help="Include raw_llm_output JSON in output",
    )
    parser.add_argument(
        "--resolve",
        default=None,
        metavar="UUID",
        help="Mark the queue entry with this UUID as resolved",
    )
    parser.add_argument(
        "--note",
        default=None,
        metavar="TEXT",
        help="Resolution note to attach when using --resolve",
    )
    args = parser.parse_args()

    try:
        conn = psycopg2.connect(DB_DSN)
    except psycopg2.OperationalError as exc:
        print(f"ERROR: Could not connect to database: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.resolve:
            resolve_entry(conn, args.resolve, args.note)
        else:
            rows = fetch_unresolved(conn, error_type=args.error_type)
            display_queue(rows, show_raw=args.show_raw)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
