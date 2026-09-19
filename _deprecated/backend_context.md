# Backend Context

## Current Focus

We are building local Postgres ingestion testing that mimics Supabase Postgres plus Supabase Storage/S3.

The goal is to make ingestion save raw PDFs, rendered page images, OCR artifacts, crops, charts, tables, and other visual assets into a predictable object-store layout, while Postgres stores stable references to those objects.

This should let us test locally now and move to Supabase later by swapping the storage backend rather than rewriting ingestion/database logic.

## Current Implementation State

The first executable slice is complete.

Implemented:

- Local object-store scaffold under `local_object_store/`.
- Editable storage layout config at `backend/config/storage_layout.yaml`.
- Pause/resume checklist at `tasks_s3.md`.
- Local/Supabase storage execution plan at `docs/FUTURE_FEATURES/LOCAL_POSTGRES_OBJECT_STORAGE_TEST_PLAN.md`.
- Object storage adapter at `backend/app/storage/object_store.py`.
- New Postgres migration:
  - `backend/migrations/versions/016_add_question_source_provenance.py`
- New ORM models:
  - `QuestionSourceSpan`
  - `QuestionStimulusAsset`
- Ingestion now writes these through the object-store adapter:
  - raw uploaded PDFs/files
  - rendered page images used by OCR
  - OCR text artifacts
- Persisted questions now get a `question_source_spans` row.
- Structured table/chart/figure assets are persisted when extractor output includes those asset structures.

## Local Postgres State

The local DSAT Postgres container was running on port `5434`.

Migration `016` was applied successfully.

Last verified Alembic state:

```bash
cd backend
uv run alembic current
```

Expected output:

```text
016 (head)
```

## Important Files

- `tasks_s3.md`
  - Resume checklist and remaining tasks.
- `backend/config/storage_layout.yaml`
  - Source of truth for local bucket prefixes, future Supabase buckets, and object key formats.
- `backend/app/storage/object_store.py`
  - Config-driven storage adapter. Currently supports `local_fs`; Supabase backend is intentionally not implemented yet.
- `backend/app/routers/ingest.py`
  - Ingestion wiring for raw uploads, page renders, OCR text, source spans, and stimulus asset rows.
- `backend/app/models/db.py`
  - SQLAlchemy models, including `QuestionSourceSpan` and `QuestionStimulusAsset`.
- `backend/migrations/versions/016_add_question_source_provenance.py`
  - DB schema migration for provenance tables.
- `docs/FUTURE_FEATURES/LOCAL_POSTGRES_OBJECT_STORAGE_TEST_PLAN.md`
  - Larger plan and Supabase migration path.
- `CHANGELOG.md`
  - Updated with this backend storage/provenance slice.

## OCR Impact

The OCR model behavior was not intentionally changed.

Still the same:

- GLM-OCR model calls.
- DeepSeek text extraction path.
- OCR fallback behavior.
- `thinking=false` behavior for `deepseek-v4-pro:cloud` ingestion extraction.

Changed:

- OCR page renders are now saved through object storage.
- OCR text is now saved to `local_object_store/ocr-artifacts/text/...`.
- Questions persisted from OCR-backed ingestion now have DB provenance rows linking them to page render/OCR artifact paths.

Compatibility note:

- Existing `_page_images` entries with local `path` are still supported.
- New `_page_images` entries use `storage_path` and can be read back through `object_store.read_object()`.

## Verified

Commands run successfully:

```bash
cd backend
uv run pytest tests/test_object_store.py tests/test_ingest_router.py
uv run pytest tests/test_config.py tests/test_yaml_export.py tests/test_object_store.py
uv run alembic heads
uv run alembic current
```

Also passed:

```bash
git diff --check ...
```

Note: `git status` and some `git diff` operations can hit a Git LFS clean-filter error because `.git/lfs/tmp` is read-only in this environment. This is unrelated to the backend implementation.

## Remaining Work

Continue from `tasks_s3.md`.

Current remaining follow-ups:

- Add automatic page crop detection for question blocks, charts, tables, and figures.
- Persist OCR layout JSON to `ocr-artifacts/layout`.
- Persist OCR diagnostics JSON to `ocr-artifacts/diagnostics`.
- Implement Supabase Storage writes behind the existing object-store adapter.
- Add integration coverage against a running local Postgres database after migration `016`.

## Recommended Next Step

Next implementation slice should be crop/layout provenance:

1. Extend PDF/page processing to create deterministic crops for:
   - full question block
   - chart/table/figure regions
2. Save crops through `object_store.put_object()` using:
   - `question_crop`
   - `table_crop`
   - `chart_crop`
   - `figure_crop`
3. Store crop paths in `question_source_spans.crop_path`.
4. Store chart/table structured JSON in `question_stimulus_assets`.
5. Add tests around object key generation and DB row creation.

## Resume Instructions

1. Read `backend_context.md`.
2. Read `tasks_s3.md`.
3. Check the current migration:

```bash
cd backend
uv run alembic current
```

4. Run focused tests before editing:

```bash
uv run pytest tests/test_object_store.py tests/test_ingest_router.py
```

5. Start with the first unchecked item in `tasks_s3.md`.
