# Debug Log

## 2026-05-16 - Open Gap Inventory (All Audits)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `f37850e` — chore: add settings.local.json to .gitignore

Summary of all unresolved findings across prior audits. Four items previously in flight are now resolved:
- ~~OCR fallback transition logging (2026-05-15 #7)~~ → **Fixed:** fallback loop now logs chain entry, transitions, and paradigm info.
- ~~Per-page render size limit (2026-05-15 #9)~~ → **Fixed:** `MAX_PAGE_RENDER_BYTES` cap in `_store_page_render`; `MAX_RENDER_DIMENSION` cap in `_render_page_b64`.
- ~~`generate_compare` shared `request_data` reference (2026-05-15 #5)~~ → **Fixed:** each closure gets `dict(request_data)` copy.
- ~~`generate_compare` closure default-arg comment (2026-05-15 #22)~~ → **Fixed:** documented inline with the `job_data=job_data` default arg.

Additional items resolved in this session (2026-05-16):
- ~~Mixed text+scanned PDFs skip OCR on scanned pages (Inventory #2)~~ → **Fixed:** per-page text check detects mixed PDFs and sends only blank pages through OCR.
- ~~`GET /ingest/jobs/{job_id}` doesn't expose OCR/LLM meta (Inventory #3)~~ → **Fixed:** `JobResponse` now includes `ocr_meta` and `llm_meta` from `pass1_json`.
- ~~`persist_overlap_relations` race condition (Inventory #5)~~ → **Fixed:** wrapped in `begin_nested()` savepoint with `IntegrityError` catch.
- ~~`generate_compare` no error aggregation (Inventory #6)~~ → **Fixed:** `get_generation_run` now returns `validation_errors` per job and `pass1_json`/`pass2_json` for single jobs.
- ~~`overlap_checking` status never set in generate pipeline (Inventory #7)~~ → **Fixed:** added `job.status = "overlap_checking"` before overlap detection in `_run_generate_pipeline`.
- ~~`generation_source_set` stores full `request_data` (Inventory #9)~~ → **Fixed:** filters out `_SOURCE_SET_OPERATIONAL_KEYS` (`provider_name`, `model_name`).
- ~~`LlmEvaluation.job_id` nullable=False receiving None (Inventory #11)~~ → **Fixed:** `EvaluationCreateRequest.job_id` changed to `Optional[str] = None`.
- ~~No admin API to activate official questions (Inventory #13)~~ → **Fixed:** `/admin/questions/{id}/approve` now allows official questions unless they have unresolved overlap.
- ~~Duplicate user-management routes (Inventory #14)~~ → **Fixed:** removed CRUD endpoints from `student.py`; canonical `/users` endpoints in `users.py` now serve all user management.
- ~~Student submit doesn't verify option label (Inventory #15)~~ → **Fixed:** added `QuestionOption` existence check in `submit_answer`.
- ~~No live heartbeat for stuck jobs (Inventory #12)~~ → **Fixed:** background sweeper task marks stuck jobs as failed every `job_sweeper_interval_s` (default 300s).
- ~~CORS wildcard default (Inventory #17)~~ → **Fixed:** production mode raises `RuntimeError` on `allow_origins=["*"]`.

### Remaining (deferred)

4. **Low: OCR pipeline test coverage gaps.**
   No DB-backed pipeline tests for: provider failure fallback, malformed vision JSON, mixed text/scanned PDFs, and batch `ocr_strategy` forwarding edge cases.
   - `backend/tests/test_ocr.py`, `backend/tests/test_ingest_router.py`, `backend/tests/test_backend_regressions.py`
   - Cross-reference: 2026-05-10 OCR Gap Review #9

16. **Low: Test suite uses stub DB session — real DB query regressions are invisible.**
    `_MockSession` returns `None` for all `.get()` and empty results for all `.execute()`. Wrong JOINs, missing WHERE clauses, and bad column references all pass silently.
    - `backend/tests/conftest.py`
    - Cross-reference: 2026-05-10 Backend Gap Audit #25

---

## 2026-05-16 - Live Ingestion Run Gaps
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `4c43353` — fix(pipeline): remediate four open audit findings — retry, empty filter, passage grouping, junction table

### Findings

1. ~~**Critical: `httpx.TimeoutException` produces empty error message in `validation_errors_jsonb`.**
   Live run of `Test_1_digital_sec01_mod01.pdf` (30,257 chars raw text) against `qwen3-vl:235b-instruct-cloud` via Ollama timed out after 120s on the extraction call. The `@with_retry` decorator retried 3 times, all timed out. After the final retry, the `TimeoutException` propagates to the `except Exception as _exc` block at line 1477, which calls `error_payload("extracting", _last_p1_err)`. But `str(httpx.TimeoutException)` is empty or near-empty, resulting in `{"step": "extracting", "error": ""}` — no useful diagnostic info (no timeout duration, no model name, no input length).
   - `backend/app/routers/ingest.py:1477-1483`, `backend/app/llm/errors.py:72`, `backend/app/llm/ollama_provider.py:28`~~
   - **Fixed:** Added `_exception_message()` helper to `errors.py`. When `str(exc)` is empty it falls back to `"{ExceptionType} (no message)"`. `error_payload` now also always emits an `error_type` field for diagnostics.

2. ~~**High: Ollama `complete()` timeout is 120s — insufficient for large extraction payloads.**
   The `OllamaProvider.__init__` sets `self.client = httpx.AsyncClient(timeout=120.0)`. With 30K+ chars of raw text, the extraction prompt sends ~30K input tokens to the cloud model. The `qwen3-vl:235b-instruct-cloud` model took >120s for this payload, causing all 3 retry attempts to time out. Vision calls get 600s but text extraction only gets 120s. For large PDFs this is inadequate.
   - `backend/app/llm/ollama_provider.py:28`~~
   - **Fixed:** Added `TEXT_TIMEOUT = 300.0` class constant (parallel to `VISION_TIMEOUT`); the text `client` now uses it instead of the hardcoded 120s.

3. ~~**High: Text ingest validation failure — LLM returns empty option labels.**
   A short 2-question text ingest succeeded through extraction and annotation but failed at validation with `"Option labels must be exactly {A, B, C, D}, got ['']"`. The LLM parsed the questions but produced options with empty string labels. This reveals that the extraction prompt does not reliably force the LLM to output `"label": "A"` format for options, and the retry loop only retries on `ValueError` (JSON parse failure), not on structurally valid JSON that produces invalid question data.
   - `backend/app/routers/ingest.py:1469-1476`, `backend/app/pipeline/validator.py`~~
   - **Fixed:** `_normalize_extracted_questions` now backfills positional labels (A/B/C/D) when a question has exactly 4 options and all option labels are blank — the exact failure mode observed.

4. ~~**Medium: `extract_json_from_text` retries don't cover the case where JSON parses but produces bad structure.**
   The 3-attempt retry loop at lines 1430-1479 retries on `ValueError` (JSON parse failure) but breaks immediately on `Exception` (line 1477-1479). If the LLM returns valid JSON that parses successfully but produces an empty `questions` array or questions with empty option labels, the retry loop exits with `extract_root` set to a valid but useless dict. No structural validation occurs between JSON parsing and proceeding to annotation.
   - `backend/app/routers/ingest.py:1430-1479`~~
   - **Fixed:** Added a structural check inside the Pass 1 retry loop — if no extracted question has a non-empty `question_text`, a `ValueError` is raised, which the existing `except ValueError` branch retries.

5. ~~**Medium: No pipeline-level timeout or heartbeat.**
   Even with `@with_retry(max_attempts=3)`, a slow model can occupy the job semaphore for 3×120s = 6 minutes per extraction attempt. Four concurrent stuck jobs block all new ingestion for up to 24 minutes. There's no pipeline-level timeout that aborts a job after N total minutes.
   - `backend/app/routers/ingest.py`, `backend/app/job_limits.py`~~
   - **Fixed:** `_run_pipeline_with_session` now wraps `_run_pipeline` in `asyncio.wait_for(timeout=settings.pipeline_timeout_s)` (default 1800s). On timeout the job is marked `failed` on a fresh session with a `pipeline_timeout` error.

6. ~~**Low: Source metadata `page_count` is `null` for PDF ingests.**
   The `source_metadata` in `pass1_json` includes `source_exam_code` but not `page_count` — the field is missing from the stored JSON. The PDF parser computes page count but it's not preserved in the metadata dict passed through to `pass1_json`.
   - `backend/app/routers/ingest.py`~~
   - **Fixed:** The official PDF ingest route now includes `"page_count": len(pdf_result["pages"])` in the `source_metadata` dict stored in `pass1_json`.

---

## 2026-05-16 - Pipeline Gap Remediation Session
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `a15ec07` — fix(pipeline): correct source_name truncation, diagnostics bloat, raw_text slice, and ocr provenance

### Findings

All items below were identified from the pipeline code trace and existing open audit findings.

1. ~~**Critical / Partially open → now fixed for text path:** Pass 1 extraction had zero JSON parse retries.~~
   `_run_pipeline` text-extraction path (line 1424): the single `try/except` terminated the job on the first malformed JSON response. Pass 2 annotation already had 3-attempt retry (line 1577). Parity gap.
   - **Fixed:** Wrapped the Pass 1 `complete()` + `extract_json_from_text()` call in a 3-attempt retry loop with exponential backoff (`0.5s`, `1s`). On final failure the job is marked `failed` with the last exception. VLM fused path (finding #6 below) still has no retry — that remains open.
   - `backend/app/routers/ingest.py` (Pass 1 block)

2. ~~**Low:** `_normalize_extracted_questions` passed empty-text questions through to Pass 2, wasting an LLM call before failing validation.~~
   - **Fixed:** Added `if not q_text_key: continue` guard with `logger.warning`. Cross-reference: finding #14 in the DB-Backed Run Trace section.

3. ~~**Low/Feature:** `passage_group_id` was assigned as one UUID per batch regardless of actual passage content — all 33 questions in a module would share the same group even when spanning multiple distinct passages.~~
   - **Fixed:** Replaced flat UUID with per-passage-text grouping using a `_passage_to_group` count map. Only passages appearing on 2+ questions get a group UUID; standalone-passage questions and passage-less questions get `None`. Cross-reference: finding #15.

4. ~~**Medium:** `job.question_id` only linked the first question produced by a multi-question job. N-1 question links lived only in `pass1_json["_created_question_ids"]` with no FK.~~
   - **Fixed:** Added `question_job_questions` junction table (migration `017`) and inserted a `QuestionJobQuestion` row per question in the pipeline loop. Cross-reference: finding #6 in the 2026-05-09 Current Backend Gap Review.

---

## 2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `606f1e3` — fix(audit): harden json_parser, CORS, filename sanitization, mark findings resolved

### Findings

#### Crash Paths & Unhandled Exceptions

1. ~~**Critical: `_persist_single_question` — no rollback on flush failure leaves session dirty.**~~
   ~~Lines 524, 541, 610 perform `await db.flush()` with no savepoint. If the second or third flush fails (e.g., IntegrityError from a duplicate UUID), the SQLAlchemy session is in a failed state and every subsequent DB operation on that session will also fail — including the `job.status = "failed"` commit at line 1694. The per-question `try/except` at line 1660-1672 calls `await db.rollback()` which clears the session, but this also rolls back ALL previously-flushed question rows from the same loop iteration, not just the failed one. For official questions, the idempotency check at line 469-473 mitigates this partially, but only if the UUID5 matches an existing row.~~
   - ~~`backend/app/routers/ingest.py:524, 541, 610, 1660-1672`~~
   - **Fixed:** The persist loop now wraps each question in `async with db.begin_nested()` (SQLAlchemy SAVEPOINT). A flush failure inside the savepoint rolls back only that question, leaving the session valid. The explicit `db.rollback()` was removed. The `QuestionJobQuestion` insert is inside the same savepoint so the junction row is only committed if the question persists successfully.

2. ~~**High: Generate pipeline — single `db.flush()` covers Question + Version + Annotation + Options with no savepoint.**
   `_run_generate_pipeline` at lines 131-183 does one `await db.flush()` after adding Question, QuestionVersion, and QuestionAnnotation. If this flush fails, the exception propagates and the job is left stuck in "annotating" status (set at line 73). The `except` blocks at lines 75-79 and 89-93 only cover the LLM call phases; there is no `try/except` around the entire persistence block (lines 107-186). A DB error here leaves the job unrecoverable.
   - `backend/app/routers/generate.py:131-186`~~
   - **Fixed:** Wrapped entire Question/Version/Annotation/Option persist block in `async with db.begin_nested()`. Failure only rolls back that question; job status update proceeds on a clean session.

3. ~~**High: Generate pipeline — `extract_json_from_text` failures are fatal with no retry.**
   Lines 71 and 86 call `extract_json_from_text` with no retry loop. If the LLM returns malformed JSON, the entire generate job fails immediately. Compare with the ingest pipeline which retries annotation 3 times (lines 1577-1603). The generate pipeline has zero retries.
   - `backend/app/routers/generate.py:71, 86`~~
   - **Fixed:** Both generate and annotate steps now use 3-attempt retry loops with exponential backoff (0.5s, 1s). `ValueError` (malformed JSON) retries; other exceptions fail immediately.

4. ~~**High: Generate pipeline — `_generation_profile_payload` merges entire `request_data` into stored profile.**
   Line 41-42: `merged.update(sources[-1])` unconditionally dumps the full `request_data` dict into the stored `generation_profile_jsonb`. This includes `provider_name`, `model_name`, and any other request fields that aren't part of the generation profile. The ingest pipeline's version of this function (line 180-189) only merges the `generation_profile` sub-key.
   - `backend/app/routers/generate.py:41-42`~~
   - **Fixed:** Added `_operational_keys = {"provider_name", "model_name"}` exclusion filter when merging the last source (`request_data`) into the profile.

5. ~~**Low: `generate_compare` — all provider jobs share the same `request_data` reference.**
   Line 293: `request_data = body.model_dump()` is computed once. Each `_run_generate_pipeline` closure captures the same dict reference. If any pipeline mutates `request_data` (unlikely but possible via `merged.update`), it affects subsequent jobs. Should be a deep copy per provider.
   - `backend/app/routers/generate.py:293`~~
   - **Fixed:** Each closure now receives `job_data = dict(request_data)` — a shallow copy per provider. The closure default-arg pattern (`jid=jid, job_data=job_data`) also documents why the default arg is needed.

6. ~~**Medium: `_run_pipeline` — VLM fused path `extract_json_from_text` failure kills job with no fallback.**
   Lines 1371-1402: The VLM extraction try/except catches any exception and sets `job.status = "failed"`. Unlike the GLM and DeepSeek branches (which have `ocr_fallback` logic), the VLM path has no fallback — a single malformed JSON response from the vision model terminates the entire job.
   - `backend/app/routers/ingest.py:1397-1402`~~
   - **Fixed:** The whole OCR gate is now a single ordered fallback loop driven by `_build_ocr_chain`, which preferentially orders **two-step strategies (glm, deepseek) before VLM-fused providers (anthropic, ollama, openai)**. The VLM body retains its 3-attempt JSON-parse retry (exponential backoff). Failure in any branch records the error and the loop advances to the next strategy; the job is only marked `failed` when the whole chain is exhausted. `_fallback_ocr_strategy` was replaced by `_build_ocr_chain`.

7. ~~**Low / Observability: `_run_pipeline` — GLM/DeepSeek OCR fallback switches extraction paradigm without explicit diagnostics.**
   When OCR fails and fallback succeeds (lines 1276-1292), the code changes `resolved_strategy` and continues. But the fallback strategy runs the VLM fused path (lines 1346-1402), which does BOTH OCR and extraction in one call. If the original strategy was `glm` or `deepseek` (two-step: OCR then separate LLM extraction), the fallback switches to a completely different extraction paradigm without logging the paradigm shift or adjusting the pipeline accordingly. The `text_extraction_provider` is already set (line 1268-1274) for the two-step path but is never used when fallback activates the VLM fused path.
   - `backend/app/routers/ingest.py:1276-1292, 1346-1402`~~
   - **Fixed:** OCR fallback loop now logs the full chain at entry and logs each fallback transition. Two-step successes log paradigm info. VLM-fused successes log that Pass 1 is skipped.

#### Timeout & Resource Exhaustion

8. ~~**Medium: No application-level timeout around whole LLM pipeline calls.**
   Provider clients do have HTTP timeouts (for example 600s for vision), but there is no shorter pipeline-level timeout/heartbeat around `provider.complete()` or `provider.complete_vision()`. Four long-hanging jobs can still occupy the global job semaphore.
   - `backend/app/routers/ingest.py:1363, 1579`, `backend/app/job_limits.py:29`~~
   - **Fixed:** `_run_pipeline_with_session` wraps `_run_pipeline` in `asyncio.wait_for(timeout=settings.pipeline_timeout_s)` (default 1800s). On timeout the job is marked `failed` on a fresh session. See also 2026-05-16 Live Ingestion Run Gaps #5. (Heartbeat-style progress monitoring remains unimplemented but the semaphore-starvation risk is closed.)

9. ~~**Medium: `_store_page_render` decodes base64 and stores raw bytes — no size limit per page.**
   Line 957: `base64.b64decode(b64)` decodes the entire page image. For a high-DPI scan, a single page can be 20+ MB decoded. `max_images` (default 10) caps page count but not per-page size. A 10-page PDF with 20 MB pages writes 200 MB to object storage in the request path.
   - `backend/app/routers/ingest.py:957`~~
   - **Fixed:** Added `MAX_PAGE_RENDER_BYTES = 10 MB` constant. `_store_page_render` now decodes first, checks size, and returns `None` (skipping the page) if over the limit. `_store_pdf_page_renders` filters out `None` returns. `_render_page_b64` in `pdf_parser.py` now caps rendered dimensions to `MAX_RENDER_DIMENSION = 3000px` per side.

10. ~~**Medium: `detect_overlaps` loads all official questions with no limit.**
    Line 46-56: A single JOIN query loads every `Question` with `content_origin == "official"` and `practice_status in ("active", "draft")`, plus their annotations. At 10,000+ official questions, this becomes a multi-hundred-megabyte result set per overlap check. No pagination, no limit clause.
    - `backend/app/pipeline/overlap.py:46-56`~~
    - **Fixed:** Added `.limit(2000)` safety cap to the overlap scan query. Full-text index pre-filtering remains a future optimization.

#### Data Integrity & Edge Cases

11. ~~**High: Validator option labels check only fires when `len(options) == 4`.**~~
    ~~Line 34: `if len(options) == 4:` gates the label validation. If the LLM returns 3 or 5 options, the label set check (`label_set != {"A", "B", "C", "D"}`) is skipped entirely, and duplicate or wrong labels pass silently. The blocking error at line 30 catches the count mismatch, but for `len(options) > 4` with correct labels A-D plus extras, neither check catches the extras.~~
    - **Fixed/stale finding:** `len(options) != 4` is itself a blocking validation error, and the exact-label check runs for the only count that can pass. Extra/missing option rows do not pass validation.
    - `backend/app/pipeline/validator.py:34-48`

12. ~~**High: `correct_option_label` validated against option labels only when 4 options exist.**~~
    ~~Line 56-63: The check `if correct in ("A", "B", "C", "D")` then verifies `correct not in actual_labels`. But this is inside the `if len(options) == 4:` block. With 3 options (labels A, B, C), `correct="D"` passes the A-D check but `D` is never found in `actual_labels`. However, the earlier blocking error for `len(options) != 4` should catch this — unless `len(options) == 4` but with duplicate labels like `["A", "A", "B", "C"]` where `label_set` is `{"A", "B", "C"}` (3 elements, not 4), which IS caught by the `label_set != {"A", "B", "C", "D"}` check. So this is actually safe for 4 options but not for != 4.~~
    - **Fixed/stale finding:** Current validator checks `correct_option_label` against `actual_labels` whenever the correct label is in A-D, independent of option count. Count mismatch remains blocking.
    - `backend/app/pipeline/validator.py:56-63`

13. **Medium / Design review: Generate pipeline — `generation_source_set` stored as the full `request_data` dict.**
    Line 125 in `db.py`: `generation_source_set` column stores the entire `GenerationRequest.model_dump()`. Line 96 in `generate.py`: `merged = {**generated, **annotate_json, "generation_source_set": request_data}`. The `request_data` dict includes `provider_name`, `model_name`, and all generation parameters. This is stored as-is into the `Question` row. Compare with the ingest pipeline which stores only metadata-relevant fields.
    - `backend/app/routers/generate.py:96`, `backend/app/models/db.py:125`

14. ~~**Medium: `_normalize_extracted_questions` drops questions with empty/whitespace `question_text` silently.**
    Lines 415-419: Questions with `question_text` that is empty or whitespace-only pass the dedup check (because `q_text_key` is falsy and won't be added to `seen_texts`), but they also don't get deduplicated. They proceed through Pass 2 annotation, which wastes an LLM call, and then fail the validator's `question_text is required` blocking check. The fix should filter out empty-text questions early, before the annotation loop.
    - `backend/app/routers/ingest.py:415-419`~~
    - **Fixed:** Added explicit `if not q_text_key: continue` guard with a warning log in `_normalize_extracted_questions`. Empty-text entries are now rejected before the per-question annotation loop.

15. ~~**Medium: `passage_group_id` is `None` for single-question batches.**
    Line 1478: `passage_group_id = uuid.uuid4() if len(questions_data) > 1 else None`. A single question with a passage_text gets no passage group. If the same passage appears in a later batch, the two groups won't be linked. This is a known gap but worth noting as it affects reading comprehension question grouping.
    - `backend/app/routers/ingest.py:1478`~~
    - **Fixed:** Replaced flat batch UUID with per-passage-text grouping. A `_passage_to_group` map assigns a shared UUID to all questions that share the same passage. Passages appearing in only one question get `None`. The old `len > 1` heuristic incorrectly grouped all questions in a batch regardless of passage content.

16. **Medium: Overlap detection race condition — `persist_overlap_relations` checks existence then inserts non-atomically.**
    Lines 116-123: The duplicate check `existing.scalars().first()` and the subsequent `db.add()` are not atomic. Two concurrent overlap checks for the same question pair could both pass the existence check and both insert, causing a unique constraint violation (if one exists) or duplicate rows (if no unique constraint on `(from_question_id, to_question_id, relation_type)`).
    - `backend/app/pipeline/overlap.py:116-123`

#### Generation & Analysis Reporting Gaps

17. **Medium: `generate_compare` — no error aggregation across providers.**
    Each provider job runs independently in a background task. If one provider fails, the other succeeds, the comparison endpoint `GET /generate/runs/{run_id}` returns status per job but doesn't indicate which provider failed or why. There's no per-job `validation_errors_jsonb` exposure in the response (lines 332-349).
    - `backend/app/routers/generate.py:307-349`

18. **Medium: Generate pipeline — `overlap_checking` status never set.**
    The ingest pipeline sets `job.status = "overlap_checking"` (line 1616). The generate pipeline at lines 189-201 runs overlap detection but never updates the job status from "approved". If overlap detection is slow, the job appears "approved" before overlap checks complete. If overlap is found, the status is changed to "possible" after commit, creating a brief window where the question appears approved but may be flagged.
    - `backend/app/routers/generate.py:189-201`

19. ~~**Medium: `_run_generate_pipeline` — `Question.practice_status` hardcoded to `"draft"`.**~~
    ~~Line 123: `practice_status="draft"`. Unlike the ingest pipeline which sets `practice_status` based on `content_origin` and `official_auto_activate_for_testing`, generated questions are always "draft" with no path to "active" via the API. The admin approval endpoint at `/admin/questions/{id}/approve` could be used, but there's no specific documentation or test for this workflow.~~
    - **Fixed/stale finding:** Generated questions intentionally start as `draft`, and `/admin/questions/{id}/approve` supports generated questions when overlap status is clear.
    - `backend/app/routers/generate.py:123`

20. **Medium: `get_generation_run` endpoint doesn't expose errors or pass1/pass2 data.**
    Lines 307-349: The response only includes `id`, `status`, `provider_name`, `question_id`, and `comparison_group_id`. There's no `validation_errors_jsonb`, no `pass1_json` or `pass2_json`, and no annotation details. Admins cannot diagnose failed generation jobs through the API.
    - `backend/app/routers/generate.py:307-349`

21. **Low: `_run_generate_pipeline` — `raw_asset_id` is `None` for generated questions.**
    The `QuestionJob` at line 225 has no `raw_asset_id`. This means the `QuestionAsset` link is absent, and the `QuestionSourceSpan` and `QuestionStimulusAsset` foreign keys to `raw_asset_id` will be `None`. No provenance tracking for generated content.
    - `backend/app/routers/generate.py:225`

22. ~~**Low: `generate_compare` uses `async_session()` inside a closure that captures `jid` via default arg.**
    Line 297: `async def _run(jid=jid):` — this is the Python closure-default-arg pattern to avoid late binding. It works correctly but is fragile; if someone refactors to `async def _run():` the `jid` would be captured by reference and all tasks would use the last `jid` value. Worth a comment.
    - `backend/app/routers/generate.py:297`~~
    - **Fixed:** Documented inline with the `job_data=job_data` default arg, matching the `jid=jid` pattern.

### Cross-References To Existing Entries

- **Canonical for ingestion/generation DB transaction gaps:** findings #1 and #2 above. Older related notes about missing savepoints or failed flush handling should be read as duplicates of these two items unless they identify a distinct call site.
- **Canonical for malformed LLM JSON retry gaps:** finding #3 above for generation and finding #6 above for VLM fused ingestion fallback behavior. Older malformed-JSON notes remain valid only where they name a separate parser path.
- **Canonical for overlap scan scalability:** finding #10 above. This supersedes the older backend audit item "Full-table scan for every overlap check".
- **Canonical for generated profile/request-data leakage:** findings #4 and #13 above. These cross-reference the older `_generation_profile_payload` and `generation_profile_jsonb` pollution entries.
- **Still separate from this organized ingestion entry:** student-facing security findings in the 2026-05-10 backend audit (#1, #4, #5), insecure deployment defaults, and list-endpoint N+1 query behavior. They are not ingestion workflow defects and should stay tracked independently.

---


## 2026-05-11 - VLM Provider Quality Audit (OCR Loop)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `fe3f436` — feat(ocr): Add OCR pipeline with DeepSeek and Ollama VLM support

### Findings

1. ~~**High:** `qwen3-vl:8b` returns empty `content` via OpenAI-compatible API — all output goes to `reasoning` field.
   - Ollama's OpenAI-compatible endpoint (`/v1/chat/completions`) for thinking-capable models (qwen3-vl, qwen3) routes all model output to `message.reasoning` instead of `message.content`. `OllamaProvider.complete_vision()` reads only `message.content`, so the extracted text is always empty string.
   - Root cause: Ollama's OpenAI-compat layer does not honour `options.thinking=false` or `think=false` at request level. The native `/api/chat` endpoint with `"think": false` works correctly.
   - Affected models: any Ollama model with `thinking` in its capabilities list.~~
   - **Fixed:** Added `_extract_content(message)` helper to `ollama_provider.py` that falls back to `message.reasoning` when `message.content` is empty and strips `<think>…</think>` wrappers via regex. Applied to both `complete()` and `complete_vision()`.

2. **High:** `qwen3-vl:8b` inference exceeds 600s vision timeout on local hardware — all 3 retry attempts timed out (total ~1803s).
   - Model is 6.1 GB and significantly slower than `granite3.2-vision:latest` (2.4 GB, ~105s).
   - **Not yet fixed:** Increase `VISION_TIMEOUT` or add per-model timeout config; or document that only models ≤3 GB are practical for local VLM OCR.

3. **Medium:** `granite3.2-vision:latest` still misses Q4 from a 4-question page — 3 of 4 extracted.
   - Model quality issue; not a code bug. Smaller VLMs (2.4 GB) have lower recall on dense test pages.
   - **Not a code fix:** Accept limitation; note in provider selection docs that this model is best-effort for multi-question pages.

4. ~~**High:** VLM answer labels `"A)"` / `"a"` fail validator — blocking all extracted questions.~~
   - ~~`correct_option_label` emitted by VLMs (granite3.2-vision, qwen-vl) with trailing `)` or `.` was rejected by `validate_question` which requires exact `"A"–"D"` match.~~
   - **Fixed:** Added `_clean_option_label()` in `_normalize_extracted_questions`; strips trailing `).` and uppercases. Applied to both `correct_option_label` and each option's `label`. 6 regression tests added.

5. ~~**High:** VLM duplicate question rows persisted (granite3.2-vision hallucinated Q2–Q4 as copies of Q2).~~
   - ~~No deduplication in `_normalize_extracted_questions` — all rows passed to persistence loop.~~
   - **Fixed:** `seen_texts` set added; case-insensitive `question_text` deduplication skips repeat rows. 2 regression tests added.

6. ~~**High:** `OllamaProvider.complete_vision()` shared 120s timeout with text calls — timed out on any model >3 GB.~~
   - **Fixed:** `vision_client = httpx.AsyncClient(timeout=600s)` added; `complete_vision` uses `vision_client`. `close()` updated to close both clients. Unit tests updated to patch `vision_client`.

7. ~~**Medium:** `deepseek-ocr:latest` appeared to return only 107 tokens on first test.~~
   - ~~Suspected model quality issue.~~
   - **Confirmed not a bug:** Root cause was oversized test image (1224×1584, 6 MB → model timeout/truncation). Re-test with 1× zoom image (612×792, 64 KB) produced 763 tokens and correct full-page extraction of all 4 questions.

---

## 2026-05-10 - Backend Gap Audit (Codex-Generated Code)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `fe3f436` — feat(ocr): Add OCR pipeline with DeepSeek and Ollama VLM support

### Findings

1. ~~**Critical:** Student API returns questions without answer options.
   - `StudentQuestionResponse` has no `options` field. `GET /api/questions` returns question text and passage but no A/B/C/D choices. Students cannot display a answerable question.
   - Relevant files: `backend/app/models/payload.py`, `backend/app/routers/student.py`.~~
   - **Fixed:** Added `options: List[dict]` to `StudentQuestionResponse`. `student_recall` batch-loads options by `latest_version_id` and populates per-question lists.

2. ~~**Critical:** No duplicate-detection on ingest — same PDF uploaded twice creates duplicate questions.~~
   - ~~`checksum` is computed and stored on `QuestionAsset` but never checked before creating a new asset/job. Re-uploading the same file runs the full pipeline again.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed:** Checksum uniqueness check added before asset creation in both upload endpoints. Returns HTTP 409 on duplicate.

3. ~~**Critical:** CORS is wide open (`allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`).~~
   - ~~Any website can make requests to the API from a user's browser.~~
   - ~~Relevant file: `backend/app/main.py`.~~
   - **Fixed/overstated:** CORS is now config-driven, methods and headers are restricted. Deployment still defaults to `CORS_ALLOWED_ORIGINS="*"`, tracked separately as a Low deployment hardening item.

4. ~~**Critical:** Students can read any user's profile — no ownership check on `GET /api/users/{user_id}`.~~
   - ~~Route uses `student_required` but accepts any integer `user_id`. User IDs are sequential integers, trivially enumerable.~~
   - ~~Relevant file: `backend/app/routers/student.py`.~~
   - **Fixed:** `GET /api/users/{user_id}` changed to `admin_required`. Students no longer have access to the profile endpoint.

5. ~~**Critical:** Students can submit answers attributed to any `user_id` — no auth/user binding.~~
   - ~~`POST /api/submit` accepts `user_id: int` in body. No check that the student key corresponds to the given user.~~
   - ~~Relevant file: `backend/app/routers/student.py`.~~
   - **Fixed:** Replaced `user_id: int` with `user_token: str` (UUID) in `UserProgressCreate`. Submit endpoint now looks up the user by token. Added `user_token` UUID column to `User` model with migration `018`. `UserResponse` exposes the token so admins can retrieve it when creating users.

6. ~~**High / Deployment:** Insecure default keys only log a warning; server does not refuse to start.
   - `_warn_if_insecure_keys` logs when `admin-key-change-me` / `student-key-change-me` are active but does not block startup. This is acceptable only for isolated local development.
   - Relevant files: `backend/app/main.py`, `backend/app/config.py`.~~
   - **Fixed:** Renamed to `_check_insecure_keys`. Now raises `RuntimeError` on startup when `settings.env == "production"` and default keys are active. Development mode still logs a warning. Added `env: str = "development"` to `Settings`.

7. ~~**High:** N+1 query pattern in all list endpoints.
   - `admin.py`, `questions.py`, `student.py` each fetch a question list then issue one DB call per question for annotations and another for options. 50 questions = 101 queries instead of 3.
   - Relevant files: `backend/app/routers/admin.py`, `backend/app/routers/questions.py`, `backend/app/routers/student.py`.~~
   - **Fixed:** All three list endpoints now batch-load annotations (and options where applicable) via `SELECT ... WHERE id IN (...)` with in-memory dict lookup. `admin.py` and `student.py` also batch-load `QuestionOption` rows.

8. ~~**High:** Full-table scan for every overlap check — O(N×M) as official questions grow.
   - `detect_overlaps` loads all official questions and annotations into memory and compares in Python via Jaccard similarity. No text index, no candidate pre-filtering.
   - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` finding #10.
   - Relevant file: `backend/app/pipeline/overlap.py`.~~
   - **Partially fixed:** Added `.limit(2000)` cap. Full pre-filtering with a text index remains open.

9. ~~**High:** Scanned-PDF page images stored as base64 in JSONB — can be megabytes per DB row.~~
   - ~~`max_images` limits pages but not images-per-page. A 10-page PDF with 5 images per page stores 50 base64 blobs in one `pass1_json` JSONB column.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed/stale finding:** PDF/image page renders are stored as object-store files and `pass1_json._page_images` stores references (`path`, `storage_path`, `mime_type`, `page_number`), not inline base64 for new ingests.

10. ~~**High:** Background pipeline tasks swallow exceptions silently.~~
    - ~~`asyncio.create_task(_run_pipeline_with_session(...))` has no `add_done_callback`. An uncaught exception leaves the job stuck in its last committed status with no error recorded.~~
    - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`.~~
    - **Fixed:** `_log_task_exception` done-callback added to all `create_task` calls in both routers; exceptions now logged at ERROR level with full traceback.

11. ~~**High:** No recovery for stuck jobs after server restart.~~
    - ~~Jobs interrupted mid-pipeline stay in `"extracting"` / `"annotating"` forever. No startup sweep, no timeout, no admin endpoint to force-fail or retry.~~
    - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`.~~
    - **Fixed:** Startup lifespan recovery marks non-terminal jobs as `failed` with a `startup_recovery` validation error.

12. **Medium / Partially fixed:** Job status is still committed before long LLM work, so a crash can leave a job in an in-progress state until recovery runs. Startup recovery prevents the stuck state from being permanent, but there is still no timeout/heartbeat retry while the server stays up.
    - Relevant files: `backend/app/routers/ingest.py`, `backend/app/main.py`.

13. **Medium:** Duplicate user management routes — `student.py` (`/api/users`) and `users.py` (`/users`) already diverged.
    - `/api/users` list has no pagination; `/users` list has `limit`/`offset`. `/api/users/{id}` GET uses `student_required`; `/users/{id}` GET uses `admin_required`. DELETE returns different status codes.
    - Relevant files: `backend/app/routers/student.py`, `backend/app/routers/users.py`.

14. **Medium:** `_generation_profile_payload` in `generate.py` overwrites merged profile with all of `request_data`.
    - Final `merged.update(sources[-1])` dumps provider, model, source_question_ids, etc. into the stored generation profile. The `ingest.py` version of the same helper does not have this line.
    - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` findings #4 and #13.
    - Relevant file: `backend/app/routers/generate.py`.

15. ~~**Medium:** `detect_overlaps` receives `job.id` (a job UUID) as `question_id`, not the new question's UUID.~~
    - ~~The self-skip guard `if oq.id == question_id: continue` is always false because job IDs and question IDs never collide. Intent is not achieved.~~
    - ~~Relevant file: `backend/app/routers/ingest.py` (call site at overlap check).~~
    - **Fixed:** Call site passes `None`; `detect_overlaps` signature updated to `Optional[uuid.UUID]`; guard is now a no-op when `None` (correct — question not yet persisted at check time).

16. ~~**Medium:** Text ingest silently truncates input at 50,000 chars with no warning in the response.~~
    - ~~Relevant file: `backend/app/routers/ingest.py`.~~
    - **Fixed:** Returns HTTP 413 with the actual char count when input exceeds 50,000. The `text[:50000]` slice in `pass1_json` construction was removed.

17. **Medium:** `LlmEvaluation.job_id` is `nullable=False` in the model but `create_evaluation` can pass `None` if `body.job_id` is an empty string, causing an unhandled 500.
    - Relevant files: `backend/app/models/db.py`, `backend/app/routers/admin.py`.

18. ~~**Low:** No rate limiting or concurrent-job cap — unlimited LLM pipeline calls per key.~~
    - **Partially fixed:** Active background jobs are capped at 4 via `backend/app/job_limits.py`. Per-user/API-key rate limiting for paid external providers remains open and is tracked in the 2026-05-15 ingestion audit.

19. ~~**Low:** Dashboard HTML served at `GET /dashboard` without authentication — exposes route structure and feature set to unauthenticated callers.~~
    - ~~Relevant file: `backend/app/routers/dashboard.py`.~~
    - **Fixed:** Dashboard routes now require `admin_required`.

20. ~~**High:** `OllamaProvider.complete_vision()` has no `@with_retry` decorator.~~
    - ~~`complete()` is wrapped with retry/backoff but `complete_vision()` is a single bare `await self.client.post(...)` call. Any transient Ollama timeout or 503 during VLM-based scanned-PDF ingest permanently fails the job.~~
    - ~~Relevant file: `backend/app/llm/ollama_provider.py`.~~
    - **Fixed:** Added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `complete_vision()`.

21. ~~**High:** `DeepSeekOCRClient.extract()` has no `@with_retry` decorator.~~
    - ~~Single-attempt HTTP call to a local vLLM/LMDeploy process. Any flaky network or overloaded inference server fails the OCR pass with no retry.~~
    - ~~Relevant file: `backend/app/parsers/ocr.py`.~~
    - **Fixed:** Imported `with_retry` and added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `extract()`.

22. ~~**Medium:** `AnthropicProvider` has no `complete_vision()` implementation.~~
    - ~~Anthropic Claude 3+ supports image inputs, but the provider only exposes `complete()`. Selecting `anthropic` as an OCR strategy will raise an `AttributeError` at runtime because the `complete_vision` call site expects the method to exist.~~
    - ~~Relevant file: `backend/app/llm/anthropic_provider.py`.~~
    - **Fixed:** `AnthropicProvider.complete_vision()` now exists and is covered by the vision fallback path.

23. ~~**Medium:** `_provider_registry` in `factory.py` grows unbounded — new `httpx.AsyncClient` per pipeline call.~~
    - ~~`get_provider()` creates a new provider instance on every invocation and appends it to a module-level list with no eviction. Each instance owns its own `httpx.AsyncClient` connection pool. Under sustained load or a multi-job burst, these accumulate in memory indefinitely.~~
    - ~~Relevant file: `backend/app/llm/factory.py`.~~
    - **Fixed:** Replaced `_provider_registry: list` with `_provider_cache: dict` keyed by `(provider_name, api_key, base_url, default_model)`. Identical configs return the same provider instance. `close_all_providers()` iterates `.values()` and clears the dict.

24. ~~**Medium:** `validator.py` blocks `command_of_evidence_quantitative` questions for missing `table_data` / `graph_data` — fields that are never extracted or stored.~~
    - ~~The blocking rules reference `table_data` and `graph_data` keys, but no extraction prompt emits these fields, no `normalize_annotation()` path sets them, and no DB column stores them. Every quantitative evidence question is permanently blocked at validation.~~
    - ~~Relevant files: `backend/app/pipeline/validator.py`, `backend/app/prompts/`.~~
    - **Fixed:** Downgraded from `"blocking"` to `"review"` severity with an explanatory message. Questions now route to human review queue instead of being permanently failed.

25. **Low:** Test suite uses a stub DB session (`_MockSession`) that returns `None` for all `.get()` and empty result sets for all `.execute()`.
    - Router tests cover auth and HTTP routing but cannot catch any DB query regression. A wrong JOIN, a missing `.where()` clause, or a bad column reference passes all tests silently.
    - Relevant file: `backend/tests/conftest.py`.

---

## 2026-05-10 - Current OCR Gap Review
Report created by: GPT-5 Codex
Git branch: `main`

### Findings

1. ~~**High:** DeepSeek OCR provenance is lost after Pass 1.~~
   - ~~The DeepSeek branch writes `job.pass1_json["_ocr_meta"]`, then the normal text Pass 1 replaces `job.pass1_json` with the extracted JSON and `_llm_meta`.~~
   - ~~Result: `pass1_json._ocr_meta.strategy == "deepseek"` is not preserved for audit or smoke-test verification.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed:** Pass 1 now preserves `_ocr_meta`, `_ocr_artifacts`, and `_page_images` when replacing `pass1_json`.

2. ~~**High:** `/ingest/unofficial/batch` does not accept or forward `ocr_strategy`.~~
   - ~~Single official/unofficial ingest routes accept `ocr_strategy`.~~
   - ~~The batch route has no `ocr_strategy` form param and calls `ingest_unofficial_file()` without forwarding any OCR selection.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed:** Batch ingest accepts, validates, and forwards `ocr_strategy`.

3. ~~**Medium / Partially fixed:** `auto` strategy fallback exists for GLM and DeepSeek failures, and auto now prefers GLM before DeepSeek/Ollama/Claude/OpenAI. Remaining gap: if the resolved strategy is a fused VLM provider (`ollama`, `anthropic`, or `openai`) and that provider fails, the VLM branch still fails the job rather than trying the next fallback provider.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/config.py`.~~
   - **Fixed:** The OCR gate now uses a unified `_build_ocr_chain` fallback loop that runs the resolved strategy first, then **prefers two-step (glm, deepseek) before VLM-fused (anthropic, ollama, openai)**. A failed VLM-fused branch now correctly falls back to a two-step path (and vice versa). See 2026-05-15 finding #6.

4. **Medium / Design gap:** OCR routing is job-level, not per-question or visual-stimulus aware.
   - Current behavior applies one OCR strategy to the whole ingest job.
   - There is no routing that uses DeepSeek OCR for text recovery while reserving VLMs for chart/table/graph/image questions.
   - Needed for the desired workflow: text-only scanned page → DeepSeek OCR; visual-reasoning item → VLM.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/pipeline/validator.py`.

5. **Medium:** Mixed text-layer and scanned PDFs are not handled well.
   - Route-time image collection only runs when the joined `raw_text` for the whole PDF is empty.
   - A PDF with some text pages and some scanned/image pages skips OCR for the scanned pages.
   - Relevant file: `backend/app/routers/ingest.py`.

6. ~~**Medium:** Base64 page images are stored directly in `question_jobs.pass1_json`.~~
   - ~~This can bloat JSONB rows for scanned PDFs and image uploads, especially failed jobs.~~
   - ~~Prefer storing asset/page references and loading or rendering images inside the background worker, keeping only OCR/vision metadata and extracted text/JSON in `pass1_json`.~~
   - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/db.py`.~~
   - **Fixed/stale finding:** New PDF/image ingests store page images as object references, not inline base64. Legacy records may still contain inline `b64` and `_collect_page_images` still supports them.

7. **Low / Partially fixed:** Job polling now returns `validation_errors`, and OCR benchmark polling exposes `ocr_meta`. Remaining gap: generic `GET /ingest/jobs/{job_id}` still returns `JobResponse` only and does not expose `_ocr_meta` or `_llm_meta`.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/payload.py`.

8. ~~**Medium:** OCR/VLM provider calls are not retried.~~
   - ~~`OllamaProvider.complete_vision()` is not wrapped by the retry decorator used by text completion.~~
   - ~~`DeepSeekOCRClient.extract()` is also single-attempt.~~
   - ~~This does not match the PRD fallback/retry expectations.~~
   - ~~Relevant files: `backend/app/llm/ollama_provider.py`, `backend/app/parsers/ocr.py`.~~
   - **Fixed:** `OllamaProvider.complete_vision()` and `DeepSeekOCRClient.extract()` are now wrapped with retry.

9. **Low / Partially fixed:** OCR pipeline tests are broader than this original audit reported, including fallback strategy and batch `ocr_strategy` coverage. Remaining test gaps: full DB-backed OCR pipeline cases for provider failure fallback, malformed vision JSON, and mixed text/scanned PDFs.
   - Relevant files: `backend/tests/test_ocr.py`, `backend/tests/test_ingest_router.py`, `backend/tests/test_backend_regressions.py`.

### Verification

- Ran `uv run pytest -q` in `backend/`.
- Result: 197 passed, 2 skipped.

### Coverage Gap

- Add pipeline-level OCR tests for DeepSeek and Ollama paths.
- Add batch route tests for `ocr_strategy`.
- Add failure/fallback tests for `auto`, unreachable Ollama, DeepSeek failure, malformed vision JSON, and mixed text/scanned PDFs.

---

## 2026-05-10 - OCR Integration Implementation (Phases 1–8)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `ba101fd` — Fix seven backend bugs across routers, config, and persistence layer

### Findings

1. **Implemented:** OCR gate wired into `_run_pipeline()` at the `no_raw_text` failure point.
   - `_collect_page_images()` reads `pass1_json._page_images` (pre-stored at route time).
   - `_resolve_ocr_strategy()` resolves `deepseek` | `ollama` | `auto` per-job or from config.
   - DeepSeek path: `DeepSeekOCRClient.extract()` → `raw_text` → existing Pass 1 unchanged.
   - Ollama VLM path: `provider.complete_vision()` → fused extraction → sentinel skips Pass 1.
   - **Files:** `backend/app/routers/ingest.py`, `backend/app/parsers/ocr.py`, `backend/app/llm/base.py`, `backend/app/llm/ollama_provider.py`, `backend/app/llm/factory.py`, `backend/app/parsers/pdf_parser.py`, `backend/app/prompts/extract_prompt.py`, `backend/app/config.py`

2. **Implemented:** Image uploads now accepted (previously raised 422).
   - `ingest_unofficial_file()` now parses image content via `parse_image()` and stores as `_page_images` for the OCR gate.
   - Both ingest routes accept optional `ocr_strategy` form param with 422 validation on invalid values.

3. **Implemented:** `parse_pdf()` now renders scanned pages via `page.get_pixmap()` when no text or embedded images are found.

4. **Test result:** 197 passed, 2 skipped — all prior tests green; 15 new OCR tests added.

## 2026-05-09 - Current Backend Gap Review
Report created by: GPT-5 Codex
Git branch: `main`

### Findings

1. ~~**High:** Cross-text, underlined, and graphic stimulus data is not fully persisted.~~
   - ~~The schema, prompts, validator, and admin UI reference `paired_passage_text`, `underlined_text`, `table_data`, and `graph_data`.~~
   - ~~Normal ingest/generate persistence primarily writes `question_text`, `passage_text`, options, and answer fields, so cross-text and quantitative reading items can lose required stimulus data after extraction/generation.~~
   - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`, `backend/app/pipeline/validator.py`, `backend/app/models/db.py`.~~
   - **Fixed (partial):** `ingest.py` and `generate.py` now write `paired_passage_text` and `underlined_text` to both the `Question` and `QuestionVersion` rows. `table_data`/`graph_data` have no DB columns — validator-only, remains unimplemented.

2. ~~**High:** Hard-delete can still fail on incoming self-references.~~
   - ~~`delete_question` clears `canonical_official_question_id` and `derived_from_question_id` only on the question being deleted.~~
   - ~~Other questions can still point to the deleted question through those self-referential FKs.~~
   - ~~Relevant files: `backend/app/routers/admin.py`, `backend/app/models/db.py`.~~
   - **Fixed:** `delete_question` now bulk-nulls `canonical_official_question_id` and `derived_from_question_id` on all other questions pointing to the target before flushing the delete.

3. ~~**High:** Default API keys are live credentials.~~
   - ~~`admin-key-change-me` and `student-key-change-me` are accepted if the corresponding environment variables are missing.~~
   - ~~Auth checks use the configured/default key lists directly.~~
   - ~~Relevant files: `backend/app/config.py`, `backend/app/auth.py`.~~
   - **Fixed:** `get_settings()` is now cached with `@lru_cache` (also closes Low #8). A startup warning fires if either default key is detected in the active key lists. `conftest.py` clears the cache before each test so `monkeypatch.setenv` continues to work.

4. **Medium:** Official questions have no normal admin activation path.
   - Official ingest creates `draft` questions unless `official_auto_activate_for_testing` is enabled.
   - `POST /admin/questions/{id}/approve` rejects `content_origin == "official"`, so a reviewed official question cannot be activated through the admin API.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/admin.py`, `backend/app/config.py`.

5. **Low / Partially fixed:** Raw PDF/file ingest text is no longer truncated at 50,000 characters; stored/extracted raw text now uses a 100,000-character threshold. Remaining gap: PDF/file ingestion can still truncate beyond 100,000 chars with only `_truncated` metadata, while direct text ingest returns HTTP 413 over 50,000 chars.
   - Relevant file: `backend/app/routers/ingest.py`.

6. ~~**Medium:** Batch asset provenance links only the first created question.
   - Multi-question ingest can create several `Question` rows from one uploaded asset.
   - `question_assets.question_id` is a single FK, and `_persist_single_question` links the asset only when the job has no primary question yet.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/db.py`.~~
   - **Fixed:** Added `question_job_questions` junction table (migration 017) linking each job to every question it produced. `_run_pipeline` now inserts a `QuestionJobQuestion` row for each successfully persisted question. The `job.question_id` single FK is kept for backward compatibility but the junction table is the authoritative many-to-many record.

7. **Medium / Design Review:** Generated `generation_profile_jsonb` stores the full request dict.
   - `_generation_profile_payload` in `generate.py` merges `request_data` into the stored profile, including fields such as `target_grammar_role_key`, `difficulty_overall`, `provider_name`, and `model_name`.
   - Existing tests currently expect this behavior, so this should be resolved as either intentional contract or data-shape cleanup.
   - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` findings #4 and #13.
   - Relevant files: `backend/app/routers/generate.py`, `backend/tests/test_backend_regressions.py`.

8. ~~**Low:** `get_settings()` is not cached.~~
   - ~~Each call creates a new `Settings` object and re-reads environment configuration.~~
   - ~~Called from auth checks and pipeline paths.~~
   - ~~Relevant file: `backend/app/config.py`.~~
   - **Fixed:** `get_settings()` is cached with `@lru_cache(maxsize=1)`.

9. **Low / Deployment:** CORS wildcard remains enabled.
   - `allow_origins=["*"]` is still configured globally.
   - This is acceptable for local development but should be restricted before non-local deployment.
   - Relevant file: `backend/app/main.py`.

10. **Low:** Student answer submission does not verify the selected option exists on the latest option set.
    - The request schema limits labels to `A`-`D`, and correctness is now computed server-side.
    - The submit path does not check that the submitted label is present in `question_options` for `latest_version_id`.
    - Relevant files: `backend/app/routers/student.py`, `backend/app/models/payload.py`.

### Verification

- Ran `uv run pytest` in `backend/`.
- Result: 182 passed, 2 skipped.

### Coverage Gap

- The suite is still mostly unit/mock based around router behavior.
- Real database FK behavior for incoming self-references, complete stimulus persistence for reading/graphic items, multi-question asset provenance, and long-source truncation behavior need integration coverage.

---

## 2026-05-09 - Backend Bug Audit
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `36583f3` — Fix backend audit findings

### Findings

1. ~~**High:** `POST /api/submit` accepted draft/retired questions — students could record answers against non-active questions. Affected: `backend/app/routers/student.py`.~~
   - **Fixed:** Added `practice_status != "active"` → 400 guard before user lookup in `submit_answer`.

2. ~~**High:** `POST /api/users` (student router) had no username validation — empty strings and oversized usernames were accepted. Affected: `backend/app/routers/student.py` (inline `UserCreate` model).~~
   - **Fixed:** Removed inline `UserCreate`/`UserResponse` models; now imports from `app.models.payload` which enforces `min_length=1, max_length=100`. Consistent with the canonical `/users` router.

3. ~~**Medium:** `POST /admin/relations` allowed self-referential relations (`from_question_id == to_question_id`). Affected: `backend/app/routers/admin.py`.~~
   - **Fixed:** Added `from_id == to_id` → 400 guard before relation creation.

4. ~~**Medium:** `GET /admin/relations` returned all rows without pagination — unbounded query at scale. Affected: `backend/app/routers/admin.py`.~~
   - **Fixed:** Added `limit` (default 100, max 500) and `offset` Query params.

---

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

5. ~~Medium: hard-delete can fail on incoming self-references.~~
   - ~~Question delete clears only the deleted question's own self-reference fields.~~
   - ~~Other questions may still point to the deleted question through `canonical_official_question_id` or `derived_from_question_id`.~~
   - ~~Relevant files: `backend/app/routers/admin.py`, `backend/app/models/db.py`.~~
   - **Fixed:** `delete_question` now bulk-nulls incoming `canonical_official_question_id` and `derived_from_question_id` references before deleting.

6. ~~**High / Deployment:** default API keys are live credentials.
   - `admin-key-change-me` and `student-key-change-me` are accepted if environment variables are missing. Startup warning exists, but startup does not fail.
   - Relevant files: `backend/app/config.py`, `backend/app/main.py`.~~
   - **Fixed:** See 2026-05-10 Backend Gap Audit #6. Startup now raises `RuntimeError` when `env=production` and default keys are active.

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

7. ~~Medium: `get_settings()` is not cached.~~
   - ~~Every call constructs a new `Settings` object and re-reads environment variables.~~
   - ~~Called on every auth check and every pipeline step.~~
   - ~~Fix: `@functools.lru_cache()` on `get_settings`.~~
   - ~~Relevant file: `backend/app/config.py:55–56`.~~
   - **Fixed:** `get_settings()` is cached.

8. Low / Partially fixed: Raw text is no longer silently truncated at 50,000 characters in PDF/file routes.
   - Stored PDF/file raw text now uses 100,000 chars and `_truncated`; direct text ingest rejects over 50,000 chars with HTTP 413. Remaining issue is provenance completeness for PDF/file sources above 100,000 chars.
   - Relevant file: `backend/app/routers/ingest.py`.

9. Medium: `_generation_profile_payload` in `generate.py` pollutes stored profiles.
   - Final `merged.update(sources[-1])` unconditionally merges the full `request_data` dict (including `target_grammar_role_key`, `difficulty_overall`, `provider_name`, etc.) into the profile.
   - The `ingest.py` version of the same function does not do this.
   - Stored `generation_profile_jsonb` in annotations contains non-profile fields.
   - **Cross-reference:** Canonical current tracking is `2026-05-15 - Ingest Pipeline DB-Backed Run Trace & Generation/Reporting Fragility` findings #4 and #13.
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
