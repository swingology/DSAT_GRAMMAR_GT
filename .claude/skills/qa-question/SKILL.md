---
name: qa-question
description: |
  Deep QA lookup for a single DSAT question stored in the database. Returns
  full question text, all answer options (with correct answer marked), stimulus
  and chart data if present, annotation JSONB, version history, admin audit log
  entries, and review swarm verdicts. Use when asked to "check question",
  "QA question", "pull question", "review question", or "is this question
  correct". Accepts a UUID, or a locator like "test=4 mod=1 q=13".
---

# QA Question

## Connection constants

```
DB:   postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev
psql: PGPASSWORD=dsat_dev psql -h localhost -p 5434 -U dsat -d dsat_dev
```

## When invoked

Parse the argument:
- UUID (e.g. `3f4a...`) → use directly as `q.id`
- `test=N mod=M q=K` → resolve via Step 0 first

## Step 0 — Resolve locator to UUID (skip if UUID given)

```sql
SELECT q.id
FROM questions q
JOIN question_job_questions jq  ON jq.question_id = q.id
JOIN question_jobs qjob         ON qjob.id = jq.job_id
JOIN question_assets qa         ON qa.id = qjob.raw_asset_id
JOIN question_annotations ann   ON ann.id = q.latest_annotation_id
WHERE qa.source_name ILIKE 'Test_<N>_digital_sec01_mod0<M>.pdf'
  AND (ann.annotation_jsonb->>'source_question_number')::int = <K>
  AND qjob.status != 'failed'
LIMIT 1;
```

## Step 1 — Core question + options

```sql
SELECT
  q.id,
  q.status,
  q.created_at,
  ann.annotation_jsonb->>'domain'                   AS domain,
  ann.annotation_jsonb->>'difficulty'               AS difficulty,
  ann.annotation_jsonb->>'skill_category'           AS skill,
  ann.annotation_jsonb->>'source_question_number'   AS q_num,
  ann.annotation_jsonb->>'question_text'            AS question_text,
  ann.annotation_jsonb->>'correct_option_label'     AS correct_label,
  ann.annotation_jsonb->>'correct_answer_rationale' AS rationale,
  ann.annotation_jsonb->>'passage_text'             AS passage,
  qv.version_number,
  qv.change_source
FROM questions q
JOIN question_annotations ann ON ann.id = q.latest_annotation_id
JOIN question_versions     qv ON qv.id  = q.latest_version_id
WHERE q.id = '<UUID>';
```

```sql
SELECT option_label, option_text, is_correct
FROM question_options
WHERE question_id = '<UUID>'
ORDER BY option_label;
```

## Step 2 — Stimulus assets (charts, passages, images)

```sql
SELECT
  qsa.stimulus_type,
  qsa.asset_uri,
  sa.structured_data,
  sa.raw_text,
  sa.ocr_text
FROM question_stimulus_assets qsa
JOIN stimulus_assets sa ON sa.id = qsa.stimulus_asset_id
WHERE qsa.question_id = '<UUID>';
```

If `asset_uri` starts with `local-s3://`, the file is at:
`/home/jb/DSAT_REDUX_MD/local_object_store/<path-after-local-s3://>`.
Read and display `structured_data` JSON for chart questions.

## Step 3 — Admin audit log

```sql
SELECT
  action,
  fields_changed,
  before_jsonb,
  after_jsonb,
  change_notes,
  created_at
FROM admin_question_audit_logs
WHERE question_id = '<UUID>'
ORDER BY created_at DESC;
```

## Step 4 — Review swarm verdicts

```sql
SELECT
  lr.reviewer_model,
  lr.verdict,
  lr.score,
  lr.reasoning
FROM llm_review_results lr
WHERE lr.question_id = '<UUID>'
ORDER BY lr.created_at DESC
LIMIT 10;
```

```sql
SELECT verdict, confidence, reasoning, created_at
FROM review_consensus
WHERE question_id = '<UUID>'
ORDER BY created_at DESC
LIMIT 1;
```

## Output format

### Header
`## Test N Mod M — Q<num> | <domain> | <difficulty> | Status: <status>`

### Question
Full passage (if present), then question text.

### Options table
```
| Label | Text | Correct? |
|-------|------|----------|
| A     | ...  |          |
| B     | ...  | ✅       |
```
Flag mismatch if `is_correct` label ≠ `correct_option_label` in annotation.

### Stimulus
If chart: print `structured_data` table (state/value pairs).
If passage: print text.

### Audit history
List any admin edits with before/after diff of changed fields. If none: "No admin edits."

### Review verdicts
List reviewer model + verdict + score. Print consensus verdict in bold.

### QA flags (auto-detect)
- ⚠️ `is_correct` label in options doesn't match `correct_option_label` in annotation
- ⚠️ Null question number
- ⚠️ Missing options (< 4)
- ⚠️ Admin edits exist (highlight what changed)
- ⚠️ Consensus verdict is `reject` or `needs_revision`
