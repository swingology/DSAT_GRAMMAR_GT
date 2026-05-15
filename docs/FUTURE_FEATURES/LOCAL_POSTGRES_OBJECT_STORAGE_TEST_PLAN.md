# Local Postgres Object-Storage Test Plan

## Goal

Create a local testing setup that behaves like Supabase Postgres plus Supabase Storage/S3, without requiring a hosted Supabase project. The backend should persist structured ingestion state in Postgres and write PDFs, page renders, crops, OCR artifacts, and table/chart JSON into a local object-store directory whose layout can later map directly to Supabase Storage buckets.

## Current Scope

This plan defines the local storage scaffold and the database work needed to test provenance locally. The first backend slice is now wired: raw uploads, OCR page renders, OCR text artifacts, and per-question source-span rows use the config-driven local object store. Automatic crop detection and rich chart/table extraction are still future work.

Configured local object-store root:

```text
local_object_store/
```

Editable storage layout config:

```text
backend/config/storage_layout.yaml
```

## Local Object-Store Layout

The local directory mimics S3/Supabase buckets:

```text
local_object_store/
  raw-sources/
    official/
    unofficial/
  page-renders/
    official/
    unofficial/
  page-crops/
    questions/
    tables/
    charts/
    figures/
  stimulus-assets/
    tables/
    charts/
    figures/
  ocr-artifacts/
    text/
    layout/
    diagnostics/
  benchmark-artifacts/
    reports/
    json/
```

The config file maps these local prefixes to future Supabase bucket names:

- `dsat-raw-sources`
- `dsat-page-renders`
- `dsat-page-crops`
- `dsat-stimulus-assets`
- `dsat-ocr-artifacts`
- `dsat-benchmark-artifacts`

## Proposed Postgres Tables

Keep the existing core tables:

- `question_assets`
- `question_jobs`
- `questions`
- `question_versions`
- `question_options`
- `question_annotations`

These local-test tables are implemented by migration `016_add_question_source_provenance.py`.

### `question_source_spans`

Purpose: link a persisted question to the exact source page, crop, OCR text, layout JSON, and diagnostic reason.

Suggested columns:

```sql
create table question_source_spans (
  id uuid primary key,
  question_id uuid not null references questions(id),
  question_job_id uuid references question_jobs(id),
  raw_asset_id uuid references question_assets(id),
  source_page_number int not null,
  source_region_role text not null,
  extraction_method text not null,
  rendered_page_path text,
  crop_path text,
  ocr_text_path text,
  layout_json_path text,
  pymupdf_text text,
  ocr_text text,
  diagnostics_jsonb jsonb,
  confidence_jsonb jsonb,
  created_at timestamptz default now()
);
```

Recommended `source_region_role` values:

- `full_page`
- `question_block`
- `answer_options`
- `table`
- `chart`
- `figure`
- `header_footer`

Recommended `extraction_method` values:

- `pymupdf`
- `glm_ocr`
- `deepseek_v4_extract`
- `vlm_layout`
- `manual_review`

### `question_stimulus_assets`

Purpose: store UI-renderable table/chart/figure metadata linked to a question.

Suggested columns:

```sql
create table question_stimulus_assets (
  id uuid primary key,
  question_id uuid not null references questions(id),
  question_job_id uuid references question_jobs(id),
  raw_asset_id uuid references question_assets(id),
  stimulus_type text not null,
  storage_path text not null,
  source_page_number int,
  source_span_id uuid references question_source_spans(id),
  title text,
  structured_data_jsonb jsonb,
  render_hints_jsonb jsonb,
  created_at timestamptz default now()
);
```

Recommended `stimulus_type` values:

- `table`
- `chart`
- `graph`
- `figure`
- `diagram`

## Local Execution Plan

1. Start local Postgres:

```bash
docker compose up -d db
```

1. Apply current migrations:

```bash
cd backend
UV_CACHE_DIR=/tmp/uv-cache uv run alembic upgrade head
```

1. Confirm migration `016_add_question_source_provenance.py` is present for `question_source_spans` and `question_stimulus_assets`.

1. Add storage settings to `backend/app/config.py`:

```python
object_storage_layout_config: str = "../backend/config/storage_layout.yaml"
object_storage_backend: str = "local_fs"
object_storage_local_root: str = "../local_object_store"
```

1. Confirm the storage adapter layer:

```text
backend/app/storage/object_store.py
```

Required functions:

- `put_object(kind, context, content, filename=None, mime_type=None) -> StoredObject`
- `read_object(storage_path) -> bytes`
- `object_uri(bucket, key) -> str`
- `local_path(bucket, key) -> Path`

1. Ingestion now writes:

- raw PDFs to `raw-sources`
- rendered pages to `page-renders`
- OCR text to `ocr-artifacts`
- structured table/chart/figure JSON to `stimulus-assets` when those assets are present in extractor output

Still to build:

- automatic question/table/chart/figure crop detection and persistence to `page-crops`
- OCR layout JSON persistence to `ocr-artifacts/layout`
- diagnostics persistence to `ocr-artifacts/diagnostics`

1. During persistence, ingestion now inserts:

- one `question_source_spans` row per persisted question
- one `question_stimulus_assets` row per extracted table/chart/figure when structured asset data is present

1. Verify correlation with SQL:

```sql
select
  q.id,
  q.source_exam_code,
  q.source_section_code,
  q.source_module_code,
  q.source_question_number,
  s.source_page_number,
  s.source_region_role,
  s.extraction_method,
  s.rendered_page_path,
  s.crop_path,
  a.stimulus_type,
  a.storage_path
from questions q
left join question_source_spans s on s.question_id = q.id
left join question_stimulus_assets a on a.question_id = q.id
where q.source_exam_code = 'PT01'
  and q.source_subject_code = 'verbal'
  and q.source_section_code = '01'
  and q.source_module_code = '01'
order by q.source_question_number, s.source_page_number;
```

## Supabase Migration Path

When moving to Supabase:

1. Keep the Postgres tables and migrations unchanged.
2. Change `active_backend` from `local_fs` to `supabase` in `backend/config/storage_layout.yaml`.
3. Create matching Supabase Storage buckets from the `supabase_bucket` names.
4. Replace local file writes in `object_store.py` with Supabase Storage uploads.
5. Keep the same object keys and database `storage_path` values.

This keeps UI and database correlation stable while only swapping the storage backend.
