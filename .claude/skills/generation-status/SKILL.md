---
name: generation-status
description: |
  Query the DSAT PostgreSQL database and report the health of the question
  generation pipeline. Shows batch-level summaries (total generated,
  approved/rejected/pending counts, auto-release eligibility) and optionally
  per-batch question details with domain, difficulty, and consensus verdicts.
  Use when asked for "generation status", "generated questions", "how many
  questions are generated", "generation health", or "batch status".
  Optional args: "batch=<uuid>" to drill into a specific batch,
  "status=pending|approved|rejected" to filter by verdict.
---

# Generation Status

## Connection constants

```
DB:   postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev
psql: PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev
```

## When invoked

Parse the argument string for `batch=<uuid>` and/or `status=<value>` filters.

- No args → run Step 1 (batch overview) only
- `batch=<uuid>` → run Step 1 + Step 2 (per-question detail for that batch)
- `status=<value>` → filter Step 2 by that verdict

## Step 1 — Batch overview

```sql
SELECT
  gb.id                                                  AS batch_id,
  gb.created_at::date                                    AS created_date,
  gb.status                                              AS batch_status,
  COUNT(DISTINCT q.id)                                   AS total_generated,
  COUNT(DISTINCT CASE WHEN q.status = 'active'   THEN q.id END) AS approved,
  COUNT(DISTINCT CASE WHEN q.status = 'rejected' THEN q.id END) AS rejected,
  COUNT(DISTINCT CASE WHEN q.status = 'draft'    THEN q.id END) AS pending,
  COUNT(DISTINCT CASE WHEN q.status = 'active' AND
        (ann.annotation_jsonb->>'domain') IS NOT NULL
                                                   THEN q.id END) AS annotated
FROM generation_batches gb
LEFT JOIN question_job_questions jq ON jq.job_id IN (
    SELECT id FROM question_jobs WHERE generation_batch_id = gb.id
)
LEFT JOIN questions q ON q.id = jq.question_id
LEFT JOIN question_annotations ann ON ann.id = q.latest_annotation_id
GROUP BY gb.id, gb.created_at, gb.status
ORDER BY gb.created_at DESC
LIMIT 20;
```

## Step 2 — Per-question detail (batch drill-down)

```sql
SELECT
  q.id                                                              AS question_id,
  q.status                                                          AS q_status,
  ann.annotation_jsonb->>'domain'                                   AS domain,
  ann.annotation_jsonb->>'difficulty'                               AS difficulty,
  ann.annotation_jsonb->>'skill_category'                           AS skill,
  LEFT(ann.annotation_jsonb->>'question_text', 80)                  AS question_preview,
  (SELECT rc.verdict
   FROM review_consensus rc
   WHERE rc.question_id = q.id
   ORDER BY rc.created_at DESC LIMIT 1)                             AS consensus_verdict,
  (SELECT COUNT(*) FROM llm_review_results lr
   WHERE lr.question_id = q.id)                                     AS reviewer_count,
  q.created_at::date                                                AS created_date
FROM question_jobs qjob
JOIN question_job_questions jq ON jq.job_id = qjob.id
JOIN questions q               ON q.id = jq.question_id
LEFT JOIN question_annotations ann ON ann.id = q.latest_annotation_id
WHERE qjob.generation_batch_id = '<BATCH_ID>'
  -- inject: AND q.status = '<status>'   (if status= arg given)
ORDER BY q.created_at DESC;
```

## Output format

### No-arg (batch overview)

Markdown table:
`Batch ID (short) | Date | Batch Status | Total | Approved | Rejected | Pending | Annotated`

Follow with:
- Auto-release eligibility: check if any batch has `batch_status = 'released'` or all pending = 0
- Total across all batches: X approved, Y rejected, Z pending

### Batch drill-down

Header: `## Batch <short-id> — <date> — <batch_status>`

Table:
`Q ID (short) | Status | Domain | Difficulty | Skill | Question Preview | Consensus | Reviewers`

Footer summary: `X approved, Y rejected, Z pending in this batch.`
