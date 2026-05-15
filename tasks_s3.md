# Local S3/Postgres Ingestion Tasks

## Goal

Make local Postgres ingestion store asset/provenance references as if it were writing to S3/Supabase Storage, while keeping bucket names and object key formats editable in `backend/config/storage_layout.yaml`.

## Current Status

- [x] Local object-store directory scaffold exists at `local_object_store/`.
- [x] Storage layout config exists at `backend/config/storage_layout.yaml`.
- [x] Local execution plan exists at `docs/FUTURE_FEATURES/LOCAL_POSTGRES_OBJECT_STORAGE_TEST_PLAN.md`.
- [x] Add Postgres provenance tables.
- [x] Add SQLAlchemy models for provenance tables.
- [x] Add object storage adapter that reads `storage_layout.yaml`.
- [x] Wire ingestion uploads/page renders/OCR text to the object storage adapter.
- [x] Add focused tests for adapter and provenance helpers.
- [x] Run backend tests/migration checks.
- [x] Apply migration `016` to the running local Postgres container.

## Remaining Follow-Up

- [ ] Add automatic page crop detection for question blocks, charts, tables, and figures.
- [ ] Persist OCR layout JSON to `ocr-artifacts/layout`.
- [ ] Persist OCR diagnostics JSON to `ocr-artifacts/diagnostics`.
- [ ] Implement Supabase Storage writes behind the existing object-store adapter.
- [ ] Add integration coverage against a running local Postgres database after migration `016`.

## Implementation Notes

- Local backend should use `active_backend: local_fs`.
- Object paths stored in Postgres should be stable URIs, not machine-specific absolute paths.
- Supabase migration should keep the same bucket/key concepts and only replace the storage implementation.
- Existing YAML archive export can remain separate from object storage for now.

## Resume Steps

1. Read this file first.
2. Check `git diff -- backend/app backend/migrations backend/config tasks_s3.md`.
3. Continue from the first unchecked task in `Remaining Follow-Up`.
4. Verify with focused tests before broad test runs.
