# PDF Ingest and DB Verification

This document explains:

- whether the backend can ingest a PDF
- how to tell it whether content is `official`, `unofficial`, or `generated`
- how to provide test metadata such as exam and module
- how to check whether the DB stored the question correctly

## Short Answer

Yes, the backend can ingest a PDF today.

Supported flows:

- `official` PDF ingest
- `unofficial` PDF ingest
- `generated` question creation from a generation request

Not supported:

- direct image ingestion with OCR is still not implemented

## Content Origin Mapping

Use these endpoints to control origin:

| Origin | Endpoint | How origin is set |
|---|---|---|
| `official` | `POST /ingest/official/pdf` | fixed by endpoint |
| `unofficial` | `POST /ingest/unofficial/file` | fixed by endpoint |
| `official` or `unofficial` text | `POST /ingest/text` | use `content_origin` form field |
| `generated` | `POST /generate/questions` | fixed by endpoint |

## Can I Pass a PDF?

Yes.

### Official PDF

Endpoint:

```text
POST /ingest/official/pdf
```

This route:

- accepts a PDF upload
- saves the raw asset
- parses PDF text
- runs extraction
- runs annotation
- validates the result
- persists the question and metadata

### Unofficial PDF

Endpoint:

```text
POST /ingest/unofficial/file
```

This route follows the same general process, but stores the item as
`content_origin = unofficial`.

## How To Tell It the Test / Module

For official ingest, provide these form fields:

- `source_exam_code`
- `source_section_code`
- `source_module_code`

These are used to tag the question and are persisted on the question row and
related asset/job metadata.

## Official PDF Example

```bash
curl -X POST http://localhost:8000/ingest/official/pdf \
  -H "X-API-Key: admin-key-change-me" \
  -F "file=@/absolute/path/to/test.pdf" \
  -F "source_exam_code=PT11" \
  -F "source_section_code=RW" \
  -F "source_module_code=M1" \
  -F "provider_name=openai" \
  -F "model_name=gpt-4o"
```

Expected response shape:

```json
{
  "id": "job-uuid",
  "job_type": "ingest",
  "status": "parsing",
  "created_at": "..."
}
```

## Unofficial PDF Example

```bash
curl -X POST http://localhost:8000/ingest/unofficial/file \
  -H "X-API-Key: admin-key-change-me" \
  -F "file=@/absolute/path/to/question-set.pdf" \
  -F "provider_name=openai" \
  -F "model_name=gpt-4o"
```

## Official Text Example

If you want to bypass PDF parsing and ingest raw text directly:

```bash
curl -X POST http://localhost:8000/ingest/text \
  -H "X-API-Key: admin-key-change-me" \
  -F "text=...raw question text..." \
  -F "content_origin=official" \
  -F "source_exam_code=PT11" \
  -F "source_section_code=RW" \
  -F "source_module_code=M1"
```

## Generated Question Example

For generated items, use:

```bash
curl -X POST http://localhost:8000/generate/questions \
  -H "X-API-Key: admin-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "target_grammar_role_key": "agreement",
    "target_grammar_focus_key": "subject_verb_agreement",
    "target_syntactic_trap_key": "nearest_noun_attraction",
    "difficulty_overall": "medium",
    "provider_name": "openai",
    "model_name": "gpt-4o"
  }'
```

## What Process Runs After the Request

The request does not do all work inline.

Instead:

1. a `question_jobs` row is created
2. the API returns immediately
3. a background task runs the pipeline
4. the pipeline performs parse → extract/generate → annotate → validate → persist

That means the initial `JobResponse` only tells you the job was accepted.

You still need to poll the job status to know whether the question was actually stored.

## How To Check Whether the DB Stored It Correctly

## Step 1: Poll the job

Use the job ID returned by the ingest/generate request.

```bash
curl -H "X-API-Key: admin-key-change-me" \
  http://localhost:8000/ingest/jobs/<job_id>
```

If the job completed successfully, the response should contain a `question_id`.

Example:

```json
{
  "id": "job-uuid",
  "job_type": "ingest",
  "status": "approved",
  "question_id": "question-uuid",
  "created_at": "..."
}
```

## Step 2: Fetch the stored question

Once you have `question_id`:

```bash
curl -H "X-API-Key: admin-key-change-me" \
  http://localhost:8000/questions/<question_id>
```

This returns:

- question content
- explanation
- latest annotation
- generation profile if present
- options
- lineage metadata

## Step 3: Recall active questions

To pull stored active questions:

```bash
curl -H "X-API-Key: admin-key-change-me" \
  "http://localhost:8000/questions/recall?origin=generated"
```

For the student-facing recall surface:

```bash
curl -H "X-API-Key: student-key-change-me" \
  "http://localhost:8000/api/questions?origin=generated"
```

## What Tables Store the Data

The main persisted tables are:

- `question_jobs`
- `question_assets`
- `questions`
- `question_versions`
- `question_annotations`
- `question_options`
- `question_relations`

## What to Inspect in the DB

### 1. Job audit trail

```sql
select
  id,
  job_type,
  content_origin,
  status,
  provider_name,
  model_name,
  question_id,
  created_at
from question_jobs
order by created_at desc
limit 20;
```

### 2. Stored question rows

```sql
select
  id,
  content_origin,
  source_exam_code,
  source_section_code,
  source_module_code,
  source_question_number,
  current_question_text,
  current_passage_text,
  current_correct_option_label,
  current_explanation_text,
  practice_status,
  generation_source_set
from questions
order by created_at desc
limit 20;
```

### 3. Stored annotation metadata

```sql
select
  question_id,
  provider_name,
  model_name,
  rules_version,
  annotation_jsonb,
  explanation_jsonb,
  generation_profile_jsonb,
  confidence_jsonb
from question_annotations
order by created_at desc
limit 20;
```

### 4. Stored option metadata

```sql
select
  question_id,
  option_label,
  option_text,
  is_correct,
  option_role,
  distractor_type_key,
  why_plausible,
  why_wrong,
  precision_score
from question_options
order by created_at desc
limit 40;
```

## What “Stored Correctly” Usually Means

For a successful ingest/generate, you should expect:

- `question_jobs.question_id` is not null
- one row exists in `questions`
- one row exists in `question_versions`
- one row exists in `question_annotations`
- four rows exist in `question_options`
- metadata fields are populated in `annotation_jsonb` and possibly `generation_profile_jsonb`

## Limitations

- official questions are persisted as `draft`, not automatically recallable as active practice items
- generated questions are also stored as `draft` until approved
- unofficial ingests may be `active` depending on validation path
- image OCR ingest is not implemented
- background tasks are in-process, so a restart can interrupt an in-flight job

## Recommended End-to-End Manual Check

Use this order:

1. submit ingest or generate request
2. copy `job_id`
3. poll `/ingest/jobs/<job_id>` or `/generate/runs/<job_id>`
4. wait until `question_id` is present
5. fetch `/questions/<question_id>`
6. run the SQL queries above if you want direct DB confirmation

## Note About Remote DB Access

If your backend can reach the configured database, the API and SQL checks above
are the right way to verify storage.

If a remote DB host is unreachable from your environment, the API may accept the
request but persistence will fail when the pipeline tries to use the DB session.
