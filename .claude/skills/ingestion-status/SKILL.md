---
name: ingestion-status
description: |
  Query the DSAT PostgreSQL database and report the health of the official
  practice test ingestion pipeline. Returns a per-module status table (job
  status, question count vs. expected 33, annotation coverage, null q-nums,
  duplicate jobs, stimulus rate) plus a prioritised issues list. Use when
  asked for "ingestion status", "which tests are ingested", "ingestion health",
  or "what's wrong with the ingestion". Optional args: "test=N" and/or
  "module=M" to narrow to a single module.
---

# Ingestion Status

## Connection constants

```
DB:   postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev
psql: PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev
```

## When invoked

Parse the argument string for `test=N` and `module=M` filters (both optional).
Then run the queries below and render the results as a markdown report.

## Step 1 — Per-module summary

```sql
SELECT
  qa.source_name,
  qj.status,
  COUNT(DISTINCT q.id)                                              AS questions,
  COUNT(DISTINCT CASE WHEN qo.question_id IS NOT NULL
                      THEN q.id END)                               AS with_answer,
  COUNT(DISTINCT CASE WHEN ann.id IS NOT NULL THEN q.id END)       AS annotated,
  COUNT(DISTINCT qsa.question_id)                                  AS has_stimulus,
  qj.created_at::date                                              AS ingested_date,
  qj.id                                                            AS job_id
FROM question_jobs qj
JOIN question_assets qa ON qa.id = qj.raw_asset_id
LEFT JOIN question_job_questions jq ON jq.job_id = qj.id
LEFT JOIN questions q                ON q.id = jq.question_id
LEFT JOIN question_options qo        ON qo.question_id = q.id AND qo.is_correct = TRUE
LEFT JOIN question_annotations ann   ON ann.id = q.latest_annotation_id
LEFT JOIN question_stimulus_assets qsa ON qsa.question_id = q.id
WHERE qa.source_name ILIKE 'Test_%'
  -- inject: AND qa.source_name ILIKE 'Test_<N>_%'   (if test= arg given)
  -- inject: AND qa.source_name ILIKE '%_mod0<M>.pdf' (if module= arg given)
GROUP BY qa.source_name, qj.status, qj.created_at::date, qj.id
ORDER BY qa.source_name, qj.status;
```

## Step 2 — Null question-number count

```sql
SELECT
  qa.source_name,
  COUNT(*) AS null_qnum
FROM question_jobs qj
JOIN question_assets qa            ON qa.id = qj.raw_asset_id
JOIN question_job_questions jq     ON jq.job_id = qj.id
JOIN questions q                   ON q.id = jq.question_id
JOIN question_annotations ann      ON ann.id = q.latest_annotation_id
WHERE qa.source_name ILIKE 'Test_%'
  AND qj.status != 'failed'
  AND (ann.annotation_jsonb->>'source_question_number') IS NULL
GROUP BY qa.source_name;
```

## Step 3 — Duplicate job detection

```sql
SELECT qa.source_name, COUNT(*) AS job_count, array_agg(qj.status) AS statuses
FROM question_jobs qj
JOIN question_assets qa ON qa.id = qj.raw_asset_id
WHERE qa.source_name ILIKE 'Test_%'
  AND qj.status != 'failed'
GROUP BY qa.source_name
HAVING COUNT(*) > 1;
```

## Output format

Render three sections:

### 1. Status Table

Markdown table with columns:
`Test | Module | Status | Q count | Expected | Delta | Answers | Annotated | Stimulus | Null Q# | Ingested`

- Expected = 33 for all modules (SAT standard)
- Delta = Q count − 33 (highlight negative in bold)
- Flag duplicate jobs with ⚠️ DUP in the Status cell

### 2. Issues by Priority

```
**P0 — Broken:** failed jobs with 0 questions
**P1 — Significant gap:** delta ≤ −3
**P2 — Minor gap / needs sign-off:** delta −1 or −2, needs_review status, null q-nums > 2, duplicate jobs
**P3 — Pending approval:** needs_review with full question count
```

List each issue as a bullet: `Test N mod M — <reason>`

### 3. Summary line

`X/Y modules fully healthy (approved + 33 questions). Z issues require attention.`
