# DSAT Grammar Backend — Historical Gap Audit

Generated: 2026-04-24  
Status reviewed: 2026-05-06

This report is preserved for provenance only. It was accurate when written, but
the critical runtime gaps it described have been addressed in the current
backend.

Current verification:

- `uv run pytest` from `backend/`
- Result: `176 passed, 2 skipped`

## Resolved Critical Items

- ORM enum names now align with migration enum types.
- Ingest jobs now persist question, version, annotation, and option rows.
- Generate jobs now persist full question metadata instead of orphaned question
  rows.
- Admin and student recall filters run in SQL before pagination.
- Alembic downgrade no longer depends on an upgrade-local enum list.
- Ingest uses the stored job provider/model.
- Admin edit snapshots options and updates latest-version pointers.
- Reannotation skips extraction and updates current annotation/version state.
- Asset and latest annotation/version links are populated by current pipelines.
- DB health, overlap detection, relation/evaluation/user APIs, retry wrappers,
  request IDs, structured logging, and provider shutdown exist in current code.

## Still Current

- Official question approval is blocked until answer verification is
  implemented.
- Direct image OCR ingest is not implemented.
- Background LLM jobs are in-process and not durable.
- The unit suite is green, but release confidence still needs real DB migration
  and happy-path API smoke coverage.
- Student auth is API-key based and does not establish per-user identity.
- Runtime retry settings are not wired into provider decorators.
