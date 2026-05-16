# Debug Log

## 2026-05-15 - extract_json_from_text Fragility Audit
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `bd82cb4` — Switch default extraction model to qwen3-vl:235b and add OCR benchmarks

### Findings

1. **High:** No validation that parsed dict matches expected shape — function returns *any* `dict`. If the LLM outputs `{"error": "rate limited", "retry_after": 30}`, that passes as valid extraction output. Downstream code (`_normalize_extracted_questions`, etc.) checks for expected keys, but by then the pipeline has committed to a bad parse and produces zero questions with no clear error explaining why.
   - `backend/app/parsers/json_parser.py:155-158`

2. **High:** Trailing comma repair only activates for Ollama/Kimi — `_repair_json_like_object` strips trailing commas (line 69), but this path only runs when `provider_name=="ollama"` or `"kimi" in model_key` (line 150). If Anthropic or OpenAI returns trailing commas (rare but possible), the default strategy fails with `ValueError` instead of attempting repair.
   - `backend/app/parsers/json_parser.py:69, 150`

3. **High:** `ValueError` on failure has no recovery path in any caller — line 159 raises `ValueError("No valid JSON found in text")` with no context about what strategies were tried or what the input looked like. The `@with_retry` decorator only covers network errors; `ValueError` is not retryable. Callers either kill the entire job (Pass 1) or permanently skip the question (Pass 2).
   - `backend/app/parsers/json_parser.py:159`, `backend/app/llm/retry.py:37-50`, `backend/app/routers/ingest.py:1206-1227, 1381-1395`

4. **Medium:** `_extract_first_braced_candidate` returns only the first JSON object — if the LLM outputs multiple separate JSON objects (e.g., two extraction results), only the first is extracted and the rest are silently lost. No check that the extracted object contains expected keys like `"questions"`.
   - `backend/app/parsers/json_parser.py:21-49`

5. **Medium:** Reasoning wrapper stripper is regex-based and fragile — `_strip_reasoning_wrappers` uses a non-greedy `re.sub` pattern that matches the shortest span between think tags. If an LLM emits nested thinking blocks or multiple separate blocks, only the first is stripped. Also, `<thinking>` tags are not caught — the pattern only matches the exact `<think>...</think>` form (despite the case-insensitive flag on the regex, the tag name itself must be `think`).
   - `backend/app/parsers/json_parser.py:52-57`

6. **Medium:** `_quote_bare_keys` regex can produce false positives — the pattern `([{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)` quotes any word before a colon after `{` or `,`. Already-quoted keys produce `""key"":` (harmless — `json.loads` accepts it), but edge cases like `{, key: val}` produce broken JSON.
   - `backend/app/parsers/json_parser.py:74`

7. **Low:** `extract_json_array_from_text` has zero test coverage — the function exists (lines 162-206) and is exported but has no direct tests. It reuses the same bracket-counting approach and has the same nested-brace fragility.
   - `backend/app/parsers/json_parser.py:162-206`, `backend/tests/test_parsers.py`

8. **Low:** Only 6 direct tests for `extract_json_from_text` — coverage misses: trailing commas with non-Ollama provider, `_quote_bare_keys` false positives, multiple JSON objects in output, nested think blocks or `<thinking>` tags, partially valid JSON (missing closing brace), very large outputs, and the false-positive dict case (`{"error": "rate limited"}`).
   - `backend/tests/test_parsers.py:12-80`

---

## 2026-05-15 - Ingestion Workflow Gap Audit (Error Handling, Data Integrity, Security)
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `bd82cb4` — Switch default extraction model to qwen3-vl:235b and add OCR benchmarks

### Findings

#### Error Handling & Recovery

1. **Critical:** Malformed LLM JSON is never retried — `ValueError` from `extract_json_from_text` kills the job or skips the question permanently. The `@with_retry` decorator only covers network errors (TimeoutException, ConnectionError, HTTP 429/5xx). A model that returns syntactically invalid JSON never gets a second chance.
   - `backend/app/parsers/json_parser.py:159`, `backend/app/llm/retry.py:37-50`, `backend/app/routers/ingest.py:1206-1227`

2. **Critical:** No stuck-job recovery — if the process crashes or an unhandled exception kills the `asyncio.create_task`, the `QuestionJob` stays in a non-terminal state ("annotating", "extracting") forever. No reaper, no startup scan, no timeout. `_log_task_exception` only logs; it cannot update the job's DB row.
   - `backend/app/routers/ingest.py:37-39, 1603`

3. **High:** No savepoints or rollback — `db.flush()` calls in `_persist_single_question` (3 flushes at lines 495, 512, 576) have no savepoint wrapping. If the second flush fails (e.g., constraint violation), the session is dirty and the entire pipeline dies. No `db.rollback()` exists anywhere in the codebase.
   - `backend/app/routers/ingest.py:495, 512, 576`

4. **Medium:** Object storage I/O errors unhandled — `path.write_bytes(data)` has no try/except. Disk-full or permission errors crash the pipeline with the job stuck in a non-terminal state. `read_object` at line 203 similarly has no try/except for missing files.
   - `backend/app/storage/object_store.py:183, 203`

5. **Low:** DeepSeek OCR fallback always goes to Ollama — even if the user originally requested Anthropic as the OCR strategy. No configurable fallback chain.
   - `backend/app/routers/ingest.py:1115-1124`

6. **Low:** VLM `extract_json_from_text` call at line 1266 is outside its own try/except — if it raises `ValueError`, the exception falls through to the broader per-question handler which marks the entire job as failed rather than retrying just the extraction parse.
   - `backend/app/routers/ingest.py:1266`

7. **Low:** Option hydration silently skips non-ABCD labels — if the LLM returns labels like `"E"` or `"1"`, those options get empty annotation fields with no warning or error logged.
   - `backend/app/pipeline/option_hydration.py:35-36`

8. **Low:** Overlap detection loads all official questions into memory unbounded — no pagination or limit. As the question bank grows, this becomes a multi-hundred-megabyte result set per overlap check.
   - `backend/app/pipeline/overlap.py:45-56`

#### Data Integrity

9. **Critical:** UUID5 collision crashes on re-ingestion — no `ON CONFLICT` / upsert. Re-uploading the same official exam hits a primary key violation with no `IntegrityError` handling. Two concurrent ingestions of the same question will both compute the same UUID5 and the second `db.flush()` raises an unhandled `IntegrityError`.
   - `backend/app/routers/ingest.py:437-440, 453`

10. **Critical:** Bad question number passes validation but crashes persist — `_validate_question_numbers` logs warnings for non-integer `source_question_number` values (e.g., `"3a"`, `"?"`) but does not prevent them from reaching `_persist_single_question` where `int(q_num)` throws `ValueError`/`TypeError`.
    - `backend/app/routers/ingest.py:438, 185-277`

11. **High:** Option labels not validated as exactly {A,B,C,D} — duplicates (`A,A,C,D`) or wrong labels (`A,B,C,E`) pass the `len==4` check. The `QuestionExtract` Pydantic model enforces `pattern=r"^[A-D]$"` but is never applied at ingestion time — raw LLM dicts bypass it.
    - `backend/app/pipeline/validator.py:30-36`, `backend/app/models/extract.py:8`

12. **High:** `correct_option_label` not validated against actual option labels — if the LLM says `"C"` but options only have labels `["A", "B", "D", "E"]`, no option gets `is_correct=True`. The question ends up with zero correct answers in the database.
    - `backend/app/pipeline/validator.py:33-36`, `backend/app/routers/ingest.py:516-530`

13. **High:** No cross-batch question deduplication — re-uploading the same PDF with a different filename (different checksum) creates duplicate Question rows. Overlap detection only runs for `content_origin in ("unofficial", "generated")`; official questions are excluded from overlap checking.
    - `backend/app/routers/ingest.py:379-407, 1507-1510`

14. **Medium:** Passage dedup is batch-only — same passage across separate ingestion jobs gets different `passage_group_id` values. No passage content hashing. Single-question passages get no group at all (`passage_group_id` is `None` when `len(questions_data) == 1`).
    - `backend/app/routers/ingest.py:1239`, `backend/app/models/db.py:80`

15. **Medium:** JSONB schema drift — `choices_jsonb`, `annotation_jsonb`, `pass1_json` store arbitrary JSON with no schema validation. Key renames in LLM output create inconsistent records over time. No migration strategy to reconcile old vs. new key names.
    - `backend/app/models/db.py:39-41`, `backend/app/routers/ingest.py:488, 504-507`

16. **Medium:** No application-level FK checks before `_persist_single_question` — if a Question insert fails silently (e.g., UUID5 PK collision), subsequent QuestionOption/QuestionAnnotation inserts fail with FK violations rather than being skipped. Partial flushes can create orphaned rows.
    - `backend/app/routers/ingest.py:494-575`

17. **Medium:** Wrong question number = wrong UUID5 = silent data corruption — if an LLM misidentifies question number 3 as question 5, `_official_question_uuid` produces the UUID for question 5, potentially overwriting the real question 5. The OCR cross-check logs warnings but does not gate persistence.
    - `backend/app/routers/ingest.py:438, 1260`

#### Security & API

18. **Critical:** Zero rate limiting on any endpoint — no middleware anywhere. Each ingest endpoint triggers expensive LLM calls. An attacker with a valid admin API key can drain API budgets by flooding endpoints. The batch endpoint `/ingest/unofficial/batch` has no limit on the number of files.
    - Entire app — no rate limiting middleware

19. **High:** No magic-number file validation — only the `Content-Type` header is checked. A malicious binary with `Content-Type: application/pdf` gets written to disk via `_store_raw_upload` before `fitz.open()` rejects it. The file is already persisted to object storage before parsing runs.
    - `backend/app/routers/ingest.py:1433-1441`

20. **High:** Prompt injection via raw user text — the extraction prompt interpolates raw text with only `---` delimiters. `source_exam_code` is also unsanitized. No XML-tag-based isolation of user content.
    - `backend/app/prompts/extract_prompt.py:87-92, 70-71`

21. **High:** CORS wide open — `allow_origins=["*"]` + `allow_headers=["*"]`. Any origin can make authenticated cross-origin requests using a leaked API key. The custom `X-API-Key` header is sent regardless of `allow_credentials` setting.
    - `backend/app/main.py:38-43`

22. **High:** Unsanitized filename stored in DB — `file.filename` from uploads goes directly into `QuestionAsset.source_name`. XSS payload possible if the filename is ever rendered in a web UI.
    - `backend/app/routers/ingest.py:1564, 1649, 2138`

23. **Medium:** No PDF page count limit — a 50 MB PDF with 50,000 pages passes size validation but exhausts memory during rasterization. Each page is rendered at 2x scale as a PNG.
    - `backend/app/parsers/pdf_parser.py:13-34`

24. **Low:** Default API keys in source code — `"admin-key-change-me"` / `"student-key-change-me"` are active if env vars aren't set. Startup warning exists but doesn't prevent access.
    - `backend/app/config.py:10-11`

25. **Low:** Unauthenticated health and dashboard endpoints — `/health` exposes DB connectivity and app version; `/dashboard` HTML exposes API route structure and provider/model defaults.
    - `backend/app/routers/health.py:11`, `backend/app/routers/dashboard.py:31`

26. **Low:** Local filesystem paths persisted in `pass1_json` — `_store_page_render` includes absolute local path in stored data. Not directly exposed via API but could leak infrastructure details if a future endpoint returns `pass1_json`.
    - `backend/app/routers/ingest.py:894`

---

## 2026-05-11 - VLM Provider Quality Audit (OCR Loop)
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `fe3f436` — feat(ocr): Add OCR pipeline with DeepSeek and Ollama VLM support

### Findings

1. **High:** `qwen3-vl:8b` returns empty `content` via OpenAI-compatible API — all output goes to `reasoning` field.
   - Ollama's OpenAI-compatible endpoint (`/v1/chat/completions`) for thinking-capable models (qwen3-vl, qwen3) routes all model output to `message.reasoning` instead of `message.content`. `OllamaProvider.complete_vision()` reads only `message.content`, so the extracted text is always empty string.
   - Root cause: Ollama's OpenAI-compat layer does not honour `options.thinking=false` or `think=false` at request level. The native `/api/chat` endpoint with `"think": false` works correctly.
   - Affected models: any Ollama model with `thinking` in its capabilities list.
   - **Not yet fixed:** Requires either (a) switching `complete_vision` to native Ollama `/api/chat` endpoint with `think: false`, or (b) adding a fallback that reads `message.reasoning` when `message.content` is empty and strips `<think>…</think>` wrappers.

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

1. **Critical:** Student API returns questions without answer options.
   - `StudentQuestionResponse` has no `options` field. `GET /api/questions` returns question text and passage but no A/B/C/D choices. Students cannot display a answerable question.
   - Relevant files: `backend/app/models/payload.py`, `backend/app/routers/student.py`.

2. ~~**Critical:** No duplicate-detection on ingest — same PDF uploaded twice creates duplicate questions.~~
   - ~~`checksum` is computed and stored on `QuestionAsset` but never checked before creating a new asset/job. Re-uploading the same file runs the full pipeline again.~~
   - ~~Relevant file: `backend/app/routers/ingest.py`.~~
   - **Fixed:** Checksum uniqueness check added before asset creation in both upload endpoints. Returns HTTP 409 on duplicate.

3. **Critical:** CORS is wide open (`allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`).
   - Any website can make requests to the API from a user's browser.
   - Relevant file: `backend/app/main.py`.

4. **Critical:** Students can read any user's profile — no ownership check on `GET /api/users/{user_id}`.
   - Route uses `student_required` but accepts any integer `user_id`. User IDs are sequential integers, trivially enumerable.
   - Relevant file: `backend/app/routers/student.py`.

5. **Critical:** Students can submit answers attributed to any `user_id` — no auth/user binding.
   - `POST /api/submit` accepts `user_id: int` in body. No check that the student key corresponds to the given user.
   - Relevant file: `backend/app/routers/student.py`.

6. **Critical:** Insecure default keys only log a warning; server does not refuse to start.
   - `_warn_if_insecure_keys` logs when `admin-key-change-me` / `student-key-change-me` are active but does not block startup.
   - Relevant file: `backend/app/main.py`.

7. **High:** N+1 query pattern in all list endpoints.
   - `admin.py`, `questions.py`, `student.py` each fetch a question list then issue one DB call per question for annotations and another for options. 50 questions = 101 queries instead of 3.
   - Relevant files: `backend/app/routers/admin.py`, `backend/app/routers/questions.py`, `backend/app/routers/student.py`.

8. **High:** Full-table scan for every overlap check — O(N×M) as official questions grow.
   - `detect_overlaps` loads all official questions and annotations into memory and compares in Python via Jaccard similarity. No text index, no candidate pre-filtering.
   - Relevant file: `backend/app/pipeline/overlap.py`.

9. **High:** Scanned-PDF page images stored as base64 in JSONB — can be megabytes per DB row.
   - `max_images` limits pages but not images-per-page. A 10-page PDF with 5 images per page stores 50 base64 blobs in one `pass1_json` JSONB column.
   - Relevant file: `backend/app/routers/ingest.py`.

10. ~~**High:** Background pipeline tasks swallow exceptions silently.~~
    - ~~`asyncio.create_task(_run_pipeline_with_session(...))` has no `add_done_callback`. An uncaught exception leaves the job stuck in its last committed status with no error recorded.~~
    - ~~Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`.~~
    - **Fixed:** `_log_task_exception` done-callback added to all `create_task` calls in both routers; exceptions now logged at ERROR level with full traceback.

11. **High:** No recovery for stuck jobs after server restart.
    - Jobs interrupted mid-pipeline stay in `"extracting"` / `"annotating"` forever. No startup sweep, no timeout, no admin endpoint to force-fail or retry.
    - Relevant files: `backend/app/routers/ingest.py`, `backend/app/routers/generate.py`.

12. **High:** Job status committed before work completes — crash window leaves permanent stuck state.
    - Pattern throughout `_run_pipeline`: `job.status = "extracting"; await db.commit()` then LLM call. A crash between commit and LLM call leaves the job stuck.
    - Relevant file: `backend/app/routers/ingest.py`.

13. **Medium:** Duplicate user management routes — `student.py` (`/api/users`) and `users.py` (`/users`) already diverged.
    - `/api/users` list has no pagination; `/users` list has `limit`/`offset`. `/api/users/{id}` GET uses `student_required`; `/users/{id}` GET uses `admin_required`. DELETE returns different status codes.
    - Relevant files: `backend/app/routers/student.py`, `backend/app/routers/users.py`.

14. **Medium:** `_generation_profile_payload` in `generate.py` overwrites merged profile with all of `request_data`.
    - Final `merged.update(sources[-1])` dumps provider, model, source_question_ids, etc. into the stored generation profile. The `ingest.py` version of the same helper does not have this line.
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

18. **Low:** No rate limiting or concurrent-job cap — unlimited LLM pipeline calls per key.

19. **Low:** Dashboard HTML served at `GET /dashboard` without authentication — exposes route structure and feature set to unauthenticated callers.
    - Relevant file: `backend/app/routers/dashboard.py`.

20. ~~**High:** `OllamaProvider.complete_vision()` has no `@with_retry` decorator.~~
    - ~~`complete()` is wrapped with retry/backoff but `complete_vision()` is a single bare `await self.client.post(...)` call. Any transient Ollama timeout or 503 during VLM-based scanned-PDF ingest permanently fails the job.~~
    - ~~Relevant file: `backend/app/llm/ollama_provider.py`.~~
    - **Fixed:** Added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `complete_vision()`.

21. ~~**High:** `DeepSeekOCRClient.extract()` has no `@with_retry` decorator.~~
    - ~~Single-attempt HTTP call to a local vLLM/LMDeploy process. Any flaky network or overloaded inference server fails the OCR pass with no retry.~~
    - ~~Relevant file: `backend/app/parsers/ocr.py`.~~
    - **Fixed:** Imported `with_retry` and added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `extract()`.

22. **Medium:** `AnthropicProvider` has no `complete_vision()` implementation.
    - Anthropic Claude 3+ supports image inputs, but the provider only exposes `complete()`. Selecting `anthropic` as an OCR strategy will raise an `AttributeError` at runtime because the `complete_vision` call site expects the method to exist.
    - Relevant file: `backend/app/llm/anthropic_provider.py`.

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

1. **High:** DeepSeek OCR provenance is lost after Pass 1.
   - The DeepSeek branch writes `job.pass1_json["_ocr_meta"]`, then the normal text Pass 1 replaces `job.pass1_json` with the extracted JSON and `_llm_meta`.
   - Result: `pass1_json._ocr_meta.strategy == "deepseek"` is not preserved for audit or smoke-test verification.
   - Relevant file: `backend/app/routers/ingest.py`.

2. **High:** `/ingest/unofficial/batch` does not accept or forward `ocr_strategy`.
   - Single official/unofficial ingest routes accept `ocr_strategy`.
   - The batch route has no `ocr_strategy` form param and calls `ingest_unofficial_file()` without forwarding any OCR selection.
   - Relevant file: `backend/app/routers/ingest.py`.

3. **High:** `auto` strategy does not perform real fallback.
   - `_resolve_ocr_strategy()` chooses Ollama whenever `ocr_vision_provider == "ollama"` without checking model reachability.
   - If the Ollama VLM call fails, the job fails immediately instead of trying DeepSeek.
   - `ocr_fallback` exists in settings but is not used by the OCR gate.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/config.py`.

4. **High:** OCR routing is job-level, not per-question or visual-stimulus aware.
   - Current behavior applies one OCR strategy to the whole ingest job.
   - There is no routing that uses DeepSeek OCR for text recovery while reserving VLMs for chart/table/graph/image questions.
   - Needed for the desired workflow: text-only scanned page → DeepSeek OCR; visual-reasoning item → VLM.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/pipeline/validator.py`.

5. **Medium:** Mixed text-layer and scanned PDFs are not handled well.
   - Route-time image collection only runs when the joined `raw_text` for the whole PDF is empty.
   - A PDF with some text pages and some scanned/image pages skips OCR for the scanned pages.
   - Relevant file: `backend/app/routers/ingest.py`.

6. **Medium:** Base64 page images are stored directly in `question_jobs.pass1_json`.
   - This can bloat JSONB rows for scanned PDFs and image uploads, especially failed jobs.
   - Prefer storing asset/page references and loading or rendering images inside the background worker, keeping only OCR/vision metadata and extracted text/JSON in `pass1_json`.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/db.py`.

7. **Medium:** OCR metadata and validation details are not observable via job polling.
   - `GET /ingest/jobs/{job_id}` returns only `JobResponse`.
   - The endpoint computes `validation_errors` but does not return them, and does not expose `pass1_json._ocr_meta`.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/payload.py`.

8. **Medium:** OCR/VLM provider calls are not retried.
   - `OllamaProvider.complete_vision()` is not wrapped by the retry decorator used by text completion.
   - `DeepSeekOCRClient.extract()` is also single-attempt.
   - This does not match the PRD fallback/retry expectations.
   - Relevant files: `backend/app/llm/ollama_provider.py`, `backend/app/parsers/ocr.py`.

9. **Medium:** Full OCR pipeline tests are missing.
   - Current OCR tests cover provider request shape, helpers, and prompt construction.
   - There are no integration-style tests proving `_run_pipeline()` preserves DeepSeek `_ocr_meta`, skips Pass 1 for Ollama VLM, handles OCR failures/fallback, or forwards batch `ocr_strategy`.
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

5. **Medium:** Raw ingest text is silently truncated at 50,000 characters.
   - PDF, file, and text ingestion store only `raw_text[:50000]` in `pass1_json`.
   - Long multi-question sources can lose later content without a blocking error or user-visible warning.
   - Relevant file: `backend/app/routers/ingest.py`.

6. **Medium:** Batch asset provenance links only the first created question.
   - Multi-question ingest can create several `Question` rows from one uploaded asset.
   - `question_assets.question_id` is a single FK, and `_persist_single_question` links the asset only when the job has no primary question yet.
   - Relevant files: `backend/app/routers/ingest.py`, `backend/app/models/db.py`.

7. **Medium / Design Review:** Generated `generation_profile_jsonb` stores the full request dict.
   - `_generation_profile_payload` in `generate.py` merges `request_data` into the stored profile, including fields such as `target_grammar_role_key`, `difficulty_overall`, `provider_name`, and `model_name`.
   - Existing tests currently expect this behavior, so this should be resolved as either intentional contract or data-shape cleanup.
   - Relevant files: `backend/app/routers/generate.py`, `backend/tests/test_backend_regressions.py`.

8. **Low:** `get_settings()` is not cached.
   - Each call creates a new `Settings` object and re-reads environment configuration.
   - Called from auth checks and pipeline paths.
   - Relevant file: `backend/app/config.py`.

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
