# Debug Log

## 2026-05-09 - Backend Review

Report created by: GPT-5 Codex

### Findings

1. ~~Critical: student APIs expose and trust the answer key.~~
   - ~~`/api/questions` returns `current_correct_option_label`.~~
   - ~~`/api/submit` persists client-supplied `is_correct` instead of deriving correctness server-side.~~
   - ~~Relevant files: `backend/app/routers/student.py`, `backend/app/models/payload.py`.~~
   - **Fixed:** Added `StudentQuestionResponse` (no answer key). Server now computes `is_correct` from `q.current_correct_option_label` vs submitted label.

2. ~~High: admin answer-key edits can leave option rows stale.~~
   - ~~`edit_question` creates a new `QuestionVersion` and updates `current_correct_option_label`, but does not create or update matching `QuestionOption` rows for the new version.~~
   - ~~Detail reads options by `question_id`, so API output can disagree with the current answer key.~~
   - ~~Relevant files: `backend/app/routers/admin.py`, `backend/app/routers/questions.py`.~~
   - **Fixed:** `edit_question` now clones `QuestionOption` rows for each new version with corrected `is_correct`/`option_role`. All option queries in admin and detail endpoints scoped to `latest_version_id`.

3. ~~High: `/users/{user_id}` delete can fail when the user has progress.~~
   - ~~The `/users` router deletes only the user row.~~
   - ~~`user_progress.user_id` has a normal foreign key with no cascade.~~
   - ~~Relevant files: `backend/app/routers/users.py`, `backend/app/models/db.py`.~~
   - **Already fixed in codebase:** `delete_user` deletes `UserProgress` rows before the user row.

4. ~~High: generated questions bypass official-overlap detection.~~
   - ~~Generation sets `official_overlap_status` to `none` unconditionally.~~
   - ~~Approval only blocks generated questions when overlap status is not `none`.~~
   - ~~Relevant files: `backend/app/routers/generate.py`, `backend/app/routers/admin.py`.~~
   - **Fixed:** Generation pipeline now runs `detect_overlaps` + `persist_overlap_relations` post-commit. Questions with similarity to official passages/questions are flagged `possible`, blocking approval until admin reviews.

5. Medium: hard-delete can fail on incoming self-references.
   - Question delete clears only the deleted question's own self-reference fields.
   - Other questions may still point to the deleted question through `canonical_official_question_id` or `derived_from_question_id`.
   - Relevant files: `backend/app/routers/admin.py`, `backend/app/models/db.py`.

6. Medium: default API keys are live credentials.
   - `admin-key-change-me` and `student-key-change-me` are accepted if environment variables are missing.
   - Relevant file: `backend/app/config.py`.

### Verification

- Ran `uv run pytest` in `backend/`.
- Result: 176 passed, 2 skipped.

### Coverage Gap

Many router tests use mocked database sessions, so real foreign-key behavior, delete cascades, and stale versioned option rows are not covered by integration tests.

---

## 2026-05-09 - Full Backend Audit

Report created by: Claude Sonnet 4.6
Git checkpoint: `07454e1` — Fix backend prompt rule loading and refresh docs

### Findings

1. ~~Critical: `users.py` `delete_user` missing UserProgress cascade.~~
   - ~~`DELETE /users/{user_id}` calls `db.delete(user)` with no prior `UserProgress` purge.~~
   - ~~Any user with progress records will cause a FK violation on delete.~~
   - ~~The `/api/users/{user_id}` in `student.py` was already fixed; this separate router at `/users` was not.~~
   - ~~Relevant file: `backend/app/routers/users.py:56–65`.~~
   - **Fixed:** Added `delete(UserProgress)` before `db.delete(user)` in `users.py`. Added `UserProgress` import and `delete` from sqlalchemy.

2. ~~Critical: `/api/users` POST (student router) has no authentication.~~
   - ~~`create_user` in `student.py` has no `Depends(admin_required)` or `Depends(student_required)`.~~
   - ~~Anyone can register arbitrary usernames with no API key.~~
   - ~~Relevant file: `backend/app/routers/student.py:157–171`.~~
   - **Fixed:** Added `Depends(admin_required)` to `create_user` in `student.py`.

3. ~~High: Reannotation pipeline creates a new `QuestionVersion` but no `QuestionOption` rows for it.~~
   - ~~`_run_reannotate_pipeline` sets `latest_version_id` to a version that has zero associated option rows.~~
   - ~~After the earlier version-scoped option query fix, reannotated questions return empty options from all read endpoints.~~
   - ~~Relevant file: `backend/app/routers/ingest.py:791–826`.~~
   - **Fixed (combined with #6):** Reannotation pipeline now loads existing option rows scoped to `latest_version_id` before advancing the version, then clones them with fresh annotation fields for the new version.

4. ~~High: `synthesized_pass1` in `reannotate_question` drops `paired_passage_text` and `underlined_text`.~~
   - ~~The dict that drives reannotation is missing both fields.~~
   - ~~Cross-text connection questions and complete-the-text questions get reannotated without their paired passage or underlined portion, producing wrong annotations.~~
   - ~~Relevant file: `backend/app/routers/ingest.py:898–910`.~~
   - **Fixed:** Added `paired_passage_text` and `underlined_text` to `synthesized_pass1`.

5. ~~High: Dashboard review queue options query is not version-scoped.~~
   - ~~`select(QuestionOption).where(QuestionOption.question_id.in_([...]))` returns options from all versions.~~
   - ~~After any admin edit, the review UI shows duplicate or stale option rows.~~
   - ~~Relevant file: `backend/app/routers/dashboard.py:154–160`.~~
   - **Fixed:** SQL query now selects `q.latest_version_id`. Options query filters by `question_version_id.in_(version_ids)` instead of by question_id.

6. ~~High: Reannotation option annotation update applies to old-version rows.~~
   - ~~`select(QuestionOption).where(QuestionOption.question_id == question.id)` fetches all versions' options and writes new annotation fields to them.~~
   - ~~No new option rows are created for the new version (see #3), so annotations land on rows that are no longer current.~~
   - ~~Relevant file: `backend/app/routers/ingest.py:830–837`.~~
   - **Fixed (combined with #3):** See #3 fix above.

7. Medium: `get_settings()` is not cached.
   - Every call constructs a new `Settings` object and re-reads environment variables.
   - Called on every auth check and every pipeline step.
   - Fix: `@functools.lru_cache()` on `get_settings`.
   - Relevant file: `backend/app/config.py:55–56`.

8. Medium: Raw text is silently truncated at 50,000 characters.
   - `raw_text[:50000]` in ingest routes drops content past the limit with no warning in job status or validation errors.
   - Multi-question PDFs longer than 50K chars silently lose tail questions.
   - Relevant files: `backend/app/routers/ingest.py:571, 653, 710`.

9. Medium: `_generation_profile_payload` in `generate.py` pollutes stored profiles.
   - Final `merged.update(sources[-1])` unconditionally merges the full `request_data` dict (including `target_grammar_role_key`, `difficulty_overall`, `provider_name`, etc.) into the profile.
   - The `ingest.py` version of the same function does not do this.
   - Stored `generation_profile_jsonb` in annotations contains non-profile fields.
   - Relevant file: `backend/app/routers/generate.py:21–33`.

10. Medium: No admin API path to activate official questions.
    - `POST /admin/questions/{id}/approve` hard-blocks `content_origin == "official"`.
    - Official questions are created as `draft` and can only become `active` via the `official_auto_activate_for_testing` config flag.
    - No API mechanism exists for an admin to review and activate official questions.
    - Relevant file: `backend/app/routers/admin.py:209–214`.

11. Medium: Duplicate user management systems at two route prefixes.
    - `/api/users` in `student.py` (mixed auth, unauthenticated POST) and `/users` in `users.py` (properly admin-only).
    - Creates ambiguity about which router is authoritative.
    - Relevant files: `backend/app/routers/student.py:157–210`, `backend/app/routers/users.py`.

12. Low: CORS wildcard in `main.py`.
    - `allow_origins=["*"]` should be restricted before any non-local deployment.
    - Relevant file: `backend/app/main.py:24–28`.

13. Low: Batch asset linking only covers the first question persisted per job.
    - `if job.raw_asset_id and not job.question_id` links the PDF asset to only the first successful question.
    - Remaining questions from the same PDF are orphaned from their source asset.
    - Relevant file: `backend/app/routers/ingest.py:266–271`.

14. Low: `_safe_read` Content-Length pre-check is advisory-only.
    - Clients that omit or lie about `Content-Length` bypass the early-exit path.
    - The post-read byte check is correct and enforced, but the comment is misleading.
    - Relevant file: `backend/app/routers/ingest.py:460–467`.

### Verification

- Ran `uv run pytest` in `backend/`.
- Result: 176 passed, 2 skipped (unchanged from prior session).

### Coverage Gap

Reannotation pipeline, version-scoped option queries, and multi-question batch asset linking have no integration test coverage. The user management auth gap (#2) is untested at the auth level (existing test `test_create_user_no_auth` confirms the endpoint accepts unauthenticated requests, but doesn't flag it as wrong).
