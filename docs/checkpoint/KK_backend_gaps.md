# DSAT Grammar Backend — Historical Gap Audit

Generated: 2026-04-24  
Status reviewed: 2026-05-06

This file is retained as a historical audit. The original report listed many
critical backend gaps that have since been resolved. Do not use the old issue
list as the current backend task list.

Current verification:

- `uv run pytest` from `backend/`
- Result: `176 passed, 2 skipped`

## Resolved Since This Audit

- Ingest pipeline now creates `Question`, `QuestionVersion`,
  `QuestionAnnotation`, and `QuestionOption` rows.
- Generate pipeline now creates version, annotation, and option rows instead of
  orphaned `Question` rows.
- Admin edit now snapshots current options and updates
  `Question.latest_version_id`.
- Recall filters for admin and student routes are SQL-side, avoiding
  Python-side pagination bugs.
- `stimulus_mode_key` response mapping uses the correct `Question` field.
- Reannotation has a dedicated pipeline path that skips Pass 1 extraction.
- `QuestionAsset.question_id`, `Question.latest_annotation_id`, and
  `Question.latest_version_id` are updated by current persistence paths.
- Relation CRUD, LLM evaluation creation, and user CRUD endpoints exist.
- Overlap detection and overlap relation persistence are implemented.
- `pool_pre_ping=True` is enabled on the async SQLAlchemy engine.
- Alembic enum definitions are module-level for upgrade/downgrade access.
- LLM provider API keys are selected by provider name in ingest and generate
  routes.
- Upload MIME validation and Content-Length fast rejection are implemented.
- Local asset paths are UUID-prefixed to avoid same-filename overwrites.
- Structured logging, request IDs, and provider shutdown are wired through app
  startup/shutdown.

## Current Remaining Backend Work

1. **Official answer verification**
   Official questions cannot be approved until answer-key verification is
   implemented.

2. **Image/OCR ingestion**
   Image uploads are intentionally rejected with 422. OCR/vision settings exist,
   but the ingestion route does not perform OCR.

3. **Durable background jobs**
   Ingest, generate, and reannotation jobs run with in-process
   `asyncio.create_task`. A restart can lose active work.

4. **Integration-level DB coverage**
   The unit suite is green, but route tests mostly use mocked DB sessions.
   Fresh Postgres migration and happy-path ingest/generate smoke tests should be
   part of release verification.

5. **Auth hardening**
   Auth is shared API-key based. Student endpoints trust submitted `user_id`;
   public multi-user deployment needs real user identity and ownership checks.

6. **Retry configuration wiring**
   `Settings` exposes `llm_retry_*`, while providers currently use decorator
   constants.

7. **Optional storage/backend polish**
   `raw_asset_storage_backend` is configurable, but only local filesystem
   storage is implemented.
