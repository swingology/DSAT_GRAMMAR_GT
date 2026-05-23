# Debug Log

## 2026-05-23 - Test 5 Ingestion Gap Pattern — Consistent Extraction Failure
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `6254837` — docs: add future topic taxonomy plan

### Context

Test 5 (both mod01 and mod02) has been ingested twice with the default model (`qwen3-vl:235b-instruct-cloud` via Ollama) and both times produced only ~19/18 questions instead of the expected 33. The PDF raw text is normal (32–34K chars, no truncation), ruling out extraction failure. The problem is that the LLM parser consistently skips the same question ranges.

### Findings

1. **High — Systematic question gap in both modules across two independent runs:**
   - **mod01 extracted:** Q3, Q4, Q5, Q7, Q18–Q22, Q24–Q30, Q32, Q33 (19 questions)
   - **mod01 missing:** Q1, Q2, Q6, Q8–Q17, Q23, Q31 (14 questions)
   - **mod02 extracted:** Q3, Q4, Q5, Q7, Q8, Q19–Q25, Q27–Q29, Q31–Q33 (18 questions)
   - **mod02 missing:** Q1, Q2, Q6, Q9–Q18, Q26, Q30 (15 questions)
   - Both modules miss Q1–Q2 and Q6–Q17 consistently — a gap of roughly 14 questions in the early-to-middle range.
   - The gap is **identical across both ingestion runs** for each module, confirming it is deterministic, not random LLM noise.

2. **Medium — Suspected root cause — PDF structure in Q1–Q17 range:**
   - Q1–Q2 and Q6–Q17 likely share a common layout feature (long reading passage, multi-question passage group, dense table, or non-standard question numbering) that `qwen3-vl` fails to parse into individual question objects.
   - The raw text for those questions is present in `pass1_json.raw_text` (text length is normal) but the LLM extraction step does not output them as discrete question entries.
   - To investigate: read `pass1_json.raw_text` directly and look at the Q1–Q17 region to confirm the text is present and identify the structural feature being skipped.

### Models Used

| Run | Pass 1 (extraction) | Pass 2 (annotation) |
|---|---|---|
| Run 1 (2026-05-20) | `qwen3-vl:235b-instruct-cloud` via Ollama | `qwen3-vl:235b-instruct-cloud` via Ollama |
| Run 2 (2026-05-23) | `qwen3-vl:235b-instruct-cloud` via Ollama | `qwen3-vl:235b-instruct-cloud` via Ollama |

Next step: retry Pass 1 extraction with `deepseek-v4-pro:cloud` to determine if the gap is model-specific or structural in the PDF.

## 2026-05-23 - Admin Question Audit Log — Implementation
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Gap

No unified audit trail existed for admin mutations of questions and answers. `QuestionVersion` captured edit content but not the actor or a diff. `reviewer_admin_overrides` captured approve/reject verdicts but not field-level before/after state. Answer key changes, status transitions, and overlap decisions were untracked.

### Implementation

**New table:** `admin_question_audit_logs` (migration `027`)

| Column | Purpose |
|--------|---------|
| `question_id` | Question affected |
| `admin_token` | Admin actor |
| `action` | `edit`, `approve`, `reject`, `confirm_overlap`, `clear_overlap` |
| `fields_changed` | JSONB array of field names touched |
| `before_jsonb` | Snapshot of relevant fields before the change |
| `after_jsonb` | Snapshot of relevant fields after the change |
| `change_notes` | Optional human note or rejection reason |
| `question_version_id` | FK to new `QuestionVersion` created by edit actions |

**New helper:** `_write_admin_audit()` in `admin.py` — called before every `db.commit()` in mutation endpoints.

**Endpoints wired:**
- `PATCH /admin/questions/{id}` — captures all edited fields + before/after + linked version
- `POST /admin/questions/{id}/approve` — captures status transition `draft/rejected → active`
- `POST /admin/questions/{id}/reject` — captures status transition + rejection reason
- `POST /admin/questions/{id}/confirm-overlap` — captures overlap status + canonical question ID
- `POST /admin/questions/{id}/clear-overlap` — captures overlap status cleared

**Verification:** 85 tests pass (`test_admin_router.py`, `test_backend_regressions.py`).

---

## 2026-05-23 - Chart Data Correction via OCR Process with Crop — Test 4 Mod01 Q13
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Issue

Chart `structured_data_jsonb` for Test 4 · Sec 01 · Mod 01 · Q13 ("US States with the Greatest Number of Organic Farms in 2016") contained incorrect bar values. The original ingestion LLM read the y-axis gridlines correctly but misidentified which bar belonged to which state — likely due to low page-render resolution causing bar/label misalignment.

- **Stimulus asset ID:** `8d234175-93f6-4dc2-8ffe-091a2ea931ff`
- **Question ID:** `e22a6533-19c8-5b62-b511-b254be102401`
- **Storage path:** `local_object_store/stimulus-assets/charts/e22a6533.../8d234175....json`

### Values Before / After

| State | Original (wrong) | Corrected |
|-------|-----------------|-----------|
| California | 2,700 | 2,800 |
| Wisconsin | 1,300 | 1,300 ✅ |
| New York | 700 | 1,000 |
| Pennsylvania | 1,300 | 800 |
| Iowa | 1,300 | 700 |
| Washington | 700 | 600 |

### Method

1. Extracted page render `page_006.png` from `local_object_store/page-renders/official/4/...`
2. Cropped and 3× upscaled the chart region using Pillow
3. Submitted crop to `glm-ocr:latest` via Ollama with explicit chart-reading prompt
4. Cross-checked GLM output against user visual inspection of the original PDF
5. Patched `structured_data_jsonb` in DB and JSON file on disk

### Root Cause

Original ingestion OCR ran on the full page render at native resolution (1224×1584). Chart bars are narrow at that scale; the LLM assigned the same approximate gridline value (1,300) to three distinct states. Cropping + upscaling before GLM submission produced an accurate read.

- **Fixed:** `structured_data_jsonb` in `question_stimulus_assets` and `local_object_store/stimulus-assets/charts/.../8d234175....json`

---

## 2026-05-23 - Ingestion Test Run (Test_9_digital_sec01_mod01) — Re-run / API Key Blocker
Report created by: Claude (ingestion-test skill subagent)
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Summary

Run aborted — `run.sh` returned `RESULT_JSON:{"error":"no job_id","response":"{\"detail\":\"Invalid admin API key\"}"}`.
No job was submitted; no extraction or creation counts available.

### Findings

1. **High:** API key mismatch blocked job submission. The bundled `run.sh` hardcodes `X-API-Key: admin-test-key`, which matches `backend/.env` (`ADMIN_API_KEYS=admin-test-key`). However, the server on `:8000` (uvicorn pid 175680, started as `backend.app.main:app` from the project root rather than from `backend/`) loaded config without picking up `backend/.env`, so it fell back to the pydantic-settings default `admin-key-change-me`. Manual probing confirmed `admin-key-change-me` is accepted and `admin-test-key` is rejected, proving the server ran without the `.env`.

   - **Root cause:** Server was launched from the project root directory (`uvicorn backend.app.main:app`), not from `backend/` (`uvicorn app.main:app`). pydantic-settings `.env` discovery is CWD-relative; starting from the wrong directory means `backend/.env` is not found.
   - **Fix required (operational, not code):** Kill pid 175680 and restart the server from `backend/` with `uv run uvicorn app.main:app` so `backend/.env` is picked up, then re-run `run.sh`.

---

## 2026-05-23 - Ingestion Test Run (Test_9_digital_sec01_mod02)
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Summary

Job `9231d84b-596d-4715-85aa-c9e43bad6e44` — status: `needs_review`
Extracted: 33 | Created: 33 | Option-label cascade (`got ['']`): **absent**

### Findings

Clean run. No blocking validation errors, no missing `options` or `correct_option_label` fields, no empty option labels. All 33 questions created successfully.

---

## 2026-05-23 - Ingestion Test Run (Test_9_digital_sec01_mod01)
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Summary

Job `b5e06c5f-9df0-4a44-894b-56cca2274897` — status: `needs_review`
Extracted: 33 | Created: 33 | Option-label cascade (`got ['']`): **absent**

### Findings

1. **Medium:** Q33 (`expression_of_ideas`) is missing its `options` field in the annotation JSONB, though `correct_option_label` (`C`) is present and 4 option rows exist in `question_options`. Annotation JSONB did not capture the options snapshot — options are stored correctly in DB rows but the annotation key is absent.
   - **To investigate:** Query `annotation_jsonb` for the Q33 question in job `b5e06c5f`. Check which annotation pass writes the `options` key and why it was skipped for the last question. Likely a pass2 truncation or off-by-one on the question list.

2. **Medium:** 2 questions have `source_question_number = NULL` and are missing `correct_option_label`. These appear to be sub-items (possibly cross-text passage components) that were extracted without a top-level question number. `question_family_key` and `skill_family_key` are also absent, suggesting the annotation pass did not fully resolve them.
   - **To investigate:** Pull `pass1_json` from job `b5e06c5f` and find the raw extracted entries with no question number. Check whether they were paired-passage cross-text sub-items that should have been merged with a parent question or skipped entirely.

No blocking failures — all 33 questions were created and the job reached `needs_review`.

---

## 2026-05-23 - Generation Factory Status Review
Report created by: Claude Sonnet 4.6
Git branch: `generation_build`
Git checkpoint: `89d3526` — feat(generation): Phase 8 — self-study agent request layer

### Scope

Full status review of the generation factory (Phases 0–10) and ingestion pipeline.

### Generation Factory: Phases 0–10 — All Complete

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Current-state alignment, non-destructive reject, rejected enum | Complete |
| 1 | Batch generation contract, `GenerationBatch` model | Complete |
| 2 | Quantity-aware runner, retry, batch counters | Complete |
| 3 | Review swarm rubric, `llm_review_results` / `review_runs` tables | Complete |
| 4 | Multi-model review runner (OpenAI/Claude/DeepSeek concurrent) | Complete |
| 5 | Consensus gate, `consensus_verdicts` table | Complete |
| 6 | Admin dashboard review queue endpoints | Complete |
| 7 | Student retrieval API expansion | Complete |
| 8 | Self-study agent request layer | Complete |
| 9 | Generation quality analytics endpoints | Complete |
| 10 | Controlled auto-release policy + audit log | Complete |

All 9 bugs found in the May 21 Codex audit were remediated. 188 tests passing.

### Open Items (process/documentation, not code)

1. **Medium — Calibration gap:** The 50-question calibration batch required before Phase 5 threshold lock-in was never run or recorded. Auto-release is still disabled by config so this is not blocking production, but the decision to waive or actually run it has not been made.

2. **Low — `TASKS_GENERATION.md` doc drift:** API Surface Summary omits several implemented analytics and auto-release endpoints. Phase 10 still has stale "Still open" text. Phase 8 is missing a completion summary paragraph.

### Ingestion Side

Ingestion pipeline is running. Test 5 (both modules) reached `needs_review` with OCR cross-check warnings (18 `qnum_ocr_crosscheck` mismatches on mod01 — non-blocking). The full 18-PDF batch has not been run yet.

---

## 2026-05-21 - Generation Phases 0-10 Code Gap Review
Report created by: GPT-5 Codex
Git branch: `generation_build`
Git checkpoint: `89d3526`

### Scope

Reviewed the live generation Phase 0-10 implementation paths after the
document-drift review: batch generation, source-example selection, self-study
generation requests, review-swarm source loading, consensus/auto-release, admin
approve/reject/regenerate, student retrieval, and Phase 9 analytics.

### Findings

1. **High:** Auto-release allowed-target matching is broken.
   - `backend/app/review/auto_release.py::_annotation_dict` reads attributes
     such as `grammar_focus_key` directly from `QuestionAnnotation`, but those
     values live in `QuestionAnnotation.annotation_jsonb`. Configured allowed
     targets therefore usually never match.

2. **High:** Auto-release audit rows are only written for successful releases.
   - `maybe_auto_release` returns early on failed gates and creates
     `AutoReleaseAuditLog` only after every gate passes. This contradicts the
     Phase 10 changelog claim that all gate outcomes are recorded.

3. **High:** Self-study generation bypasses the batch request contract and
   source-example selection.
   - `_create_self_study_batch` creates minimal request JSON with only
     focus/difficulty, skips `GenerationBatchRequest` validation, and does not
     call source-example selection. Resulting jobs can enter the generation
     prompt without required grammar/reading fields or official examples.

4. **Medium:** `dry_run` release policy is not enforced at release/retrieval.
   - Admin approval can activate generated questions from `dry_run` batches,
     and student retrieval only filters `practice_status='active'`; no path
     excludes active dry-run generated questions.

5. **Medium:** Phase 9 batch analytics and self-study quality cooldown can use
   stale denormalized counters for admin decisions.
   - Generation increments `GenerationBatch.accepted_count` for clean pipeline
     saves, while admin approve/reject changes `Question.practice_status`
     without changing batch decision counters. Any analytics or quality gate
     that treats those counters as admin decisions can misreport quality.

6. **Medium:** Auto-selected official source examples do not implement the full
   locked selection contract.
   - `_select_source_question_ids_for_batch` lacks last-50 source dedupe,
     request `stimulus_mode_key` hard filtering, and exam-code diversification.

7. **Medium:** Review swarm reuses generator source examples.
   - `_load_question_for_review` pulls `source_question_ids` from the original
     generation request instead of selecting fresh same-target official examples
     for review calibration.

8. **Low:** Analytics token totals read the wrong JSON keys.
   - LLM providers store token usage as `{"input": ..., "output": ...}`, while
     analytics sums `input_tokens` / `output_tokens`, so totals can report zero.

9. **Low:** `copy_risk_failures` overcounts all reject recommendations.
   - Phase 9 analytics counts every `reject_recommended` consensus as a copy
     risk failure, including low-realism or low-SAT-fidelity rejects.

### Verification Before Fix

Focused suite still passed despite the findings:
`uv run pytest tests/test_auto_release.py tests/test_self_study.py tests/test_generate_batches.py tests/test_analytics.py -q`
returned `121 passed, 1 warning`. The warning was an existing async mock warning
in `tests/test_generate_batches.py::test_batch_reading_complete_request_creates_batch`.

### Resolution

All nine code findings in this section were remediated on 2026-05-21 and logged
to `CHANGELOG.md` under "Generation Phases 0-10 Code Gap Remediation."

Verification after fix:
`uv run pytest tests/test_auto_release.py tests/test_self_study.py tests/test_generate_batches.py tests/test_analytics.py tests/test_backend_regressions.py -q`
returned `188 passed, 1 warning`. The warning is the same pre-existing async mock
warning in `tests/test_generate_batches.py::test_batch_reading_complete_request_creates_batch`.

## 2026-05-21 - Generation Phases 0-10 Changelog/Task Drift Review
Report created by: GPT-5 Codex
Git branch: `generation_build`
Git checkpoint: `89d3526`

### Scope

Compared `TASKS_GENERATION.md` against the latest generation-related entries in
`CHANGELOG.md` for Phases 0-10. Follow-up code scan covered the implementation
surfaces for the suspected gaps: admin analytics endpoints, review-run endpoint,
auto-release logic/endpoints/config/tests, dashboard routes, and calibration
references.

### Findings

1. **High:** 50-question calibration remains undocumented while thresholds and
   Phase 10 auto-release are implemented.
   - `TASKS_GENERATION.md` requires a 50-question calibration batch before Phase
     5 threshold lock-in. The changelog records fixed Phase 5 thresholds and
     Phase 10 auto-release plumbing, but no calibration result, calibration
     batch ID, admin labels, threshold-selection evidence, or recalibration
     decision record.
   - Code check: `backend/app/config.py` still describes auto-release as
     disabled by default until calibration data exists, and `rg` found only
     prompt/test/config references to calibration, not a durable calibration
     artifact. This is primarily a process/documentation gap unless a separate
     calibration artifact exists outside the searched tree.

2. **Medium:** `TASKS_GENERATION.md` has stale "Still open" text for Phase 10.
   - The locked-decisions tail still says Phase 10 auto-release flag wiring and
     audit-log shape remain open. The Phase 10 task body and changelog both say
     they are complete.
   - Code check: `backend/app/review/auto_release.py`,
     `backend/app/review/consensus.py`, `backend/app/routers/admin.py`,
     `backend/app/models/db.py`, migration
     `backend/migrations/versions/026_phase10_auto_release_audit.py`, and
     `backend/tests/test_auto_release.py` confirm the Phase 10 wiring exists.
     This is doc drift unless code review later finds behavioral defects.

3. **Medium:** `TASKS_GENERATION.md` API Surface Summary is stale.
   - The summary omits implemented endpoints that appear in phase bodies and
     changelog entries, including `GET /admin/questions/{question_id}/review-runs`,
     `GET /admin/analytics/generation`, `GET /admin/analytics/review`,
     `GET /admin/analytics/batches`, `GET /admin/analytics/trends`,
     `GET /admin/analytics/export`, and the Phase 10 auto-release status,
     enable/disable, and audit endpoints.
   - Code check: those route decorators exist in `backend/app/routers/admin.py`;
     tests exist in `backend/tests/test_analytics.py` and
     `backend/tests/test_auto_release.py`. This is doc drift.

4. **Low:** Phase 8 lacks the same task-doc completion summary style used by
   nearby phases.
   - Phase 8 checklist items are checked, and `CHANGELOG.md` has the
     implementation and verification detail, but `TASKS_GENERATION.md` does not
     include a `Status 2026-05-20` completion paragraph like Phases 6, 7, 9,
     and 10.
   - Code check: `backend/app/routers/student.py` contains the self-study
     recommendation/generation-request/status path, and changelog verification
     records `backend/tests/test_self_study.py`. This is consistency cleanup in
     the task doc.

5. **Low:** Phase 9 wording may overstate dashboard/UI completion.
   - `TASKS_GENERATION.md` says "dashboard metrics" and "trend views"; the
     changelog records five read-only admin analytics endpoints. If endpoint
     delivery is the intended Phase 9 surface, the task doc should say so. If a
     rendered dashboard page was intended, the changelog is missing that detail
     and the implementation appears endpoint-only.
   - Code check: `backend/app/routers/admin.py` contains the analytics
     endpoints, and `backend/tests/test_analytics.py` covers them. A targeted
     scan of `backend/app/routers/dashboard.py` did not show a dedicated
     analytics dashboard page comparable to `/dashboard/review`.

### Recommended Step-Through Order

1. Decide whether the calibration gap requires a real 50-question run now, a
   recorded waiver, or a task-doc downgrade because auto-release is still gated
   off by config and allowed targets.
2. Clean stale Phase 10 "Still open" text in `TASKS_GENERATION.md`.
3. Refresh the API Surface Summary.
4. Add a Phase 8 status paragraph to match neighboring completed phases.
5. Clarify Phase 9 endpoint-only vs dashboard-UI language.

## 2026-05-20 - TASKS_INGESTION_REFACTOR Pre-Coding Review
Report created by: GPT-5 Codex
Git branch: `generation_build`
Git checkpoint: `21227c7` - feat(generation): support reading generation sources

### Findings

1. **Medium:** Task 3 is stale/already implemented.
   - `backend/app/prompts/annotate_prompt.py` already gates annotation rule context by `_detect_domain()` inside `build_annotate_prompt()`: grammar questions get grammar rules, reading questions get reading rules, and unknown questions get a limited combined context. Before coding starts, re-scope Task 3 to regression tests/metrics instead of reimplementing prompt routing.

2. **Medium:** Task 2 is stale/already implemented.
   - `backend/app/prompts/extract_prompt.py` already keeps raw OCR text out of `build_vision_extract_prompt()`; the VLM prompt relies on page images plus metadata. Treat this as a regression-test task, not an implementation task.

3. **Medium:** Task 6 is unsafe as written.
   - `backend/app/llm/ollama_provider.py` documents that `TEXT_TIMEOUT` was raised from 120s to 300s because large extraction payloads exceeded the prior ceiling. Reducing it globally after Anthropic prompt caching would also affect Ollama/non-Anthropic text paths, including extraction. Make timeout reduction measurement-gated, provider/path-specific, or configurable.

4. **Medium:** Task 4 needs a narrower skip condition.
   - Current qnum crosscheck issues in `backend/app/routers/ingest.py` are warnings/deferred-activation signals, not necessarily terminal blockers. Skipping Pass 2 for those would remove useful taxonomy/review data from draft questions. Only skip annotation for structural blockers that make persistence invalid or intentionally impossible.

5. **Medium:** Task 5 should reuse existing visual-stimulus detection.
   - The proposed table/chart gate is directionally correct, but checking only `table_data` / `graph_data` is too narrow. Use `_stimulus_candidates()` plus visual `stimulus_mode_key` values so the gate covers `stimulus_assets`, `visual_assets`, shorthand `tables/charts/graphs/figures`, and extracted visual modes.

6. **Low:** Task 1 needs a provider-contract note.
   - Anthropic cache-control system blocks should not silently change the shared `LLMProvider.complete(system: str, ...)` contract used by OpenAI and Ollama providers. Either keep provider-neutral string prompts with an Anthropic-specific cache adapter or intentionally update the protocol and provider tests. Verification should also record Anthropic cache token usage in `LLMResponse.token_usage`.

7. **Low:** Tasks 7 and 8 appear to be no-ops.
   - Page renders are already stored once and reused through `_collect_page_images()`. OCR fallback providers also appear lazily instantiated inside selected strategy branches rather than eagerly created by `_build_ocr_chain()`. Keep these as confirmation checks unless new evidence shows otherwise.

8. **Low:** Task 9 is stale/inverted.
   - `.claude/skills/ingestion-test/run.sh` already sleeps 15 seconds between polls. Changing that to 10 seconds would poll more often, not less. Leave it alone or update the task wording.

### Recommendation

Update `TASKS_INGESTION_REFACTOR.md` before implementation: move Tasks 2, 3, 7, 8, and 9 into confirmed/no-op or regression-test-only status; tighten Tasks 4 and 5; and make Task 6 config/measurement-driven instead of a hard-coded timeout reduction.

## 2026-05-20 - Ingestion Test Run (Test_7_digital_sec01_mod01) [verification re-run]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `765bea0` — Widen vocab key columns and reconcile model with migration 012

### Findings

1. **Resolved (verification PASS):** Job `01e44c3f-be54-4d14-8c17-b01eb9877156`. Status: `approved`. Extracted 33, created 33 (full parity). `validation_errors_jsonb` is empty across every step (0 rows) — no `extracting`, `normalizing`, `validating`, `persisting`, or `qnum_ocr_crosscheck` errors. This is the clean run targeted by the three-fix sequence (657570b strict +1 contiguity, e3be02b composite-key dedupe, 765bea0 VARCHAR(100) widening).

2. **bug-121 (stem_type_key VARCHAR(40) overflow) did NOT recur.** Migration 019 widening to VARCHAR(100) verified — the same Test_7_mod01 input that previously truncated `identify_evidence_that_supports_conclusion` now persists cleanly. Marking bug-121 as fixed (fixed_by commit 765bea0) in buglog.json.

3. **The `[2, 3, 4, 5]` early-question gap pattern did NOT recur.** Source question numbers persisted contiguously 1–33.

4. **The option-labels `got ['']` cascade did NOT appear.** Zero validating-step errors.

## 2026-05-20 - Ingestion Test Run (Test_7_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `657570b` — Filter passage line numbers from qnum OCR crosscheck

### Findings

1. **High:** Persisting step — `StringDataRightTruncationError` on `stem_type_key` (persisting step).
   - Job `310142c4-fb50-479a-818b-66753722435b` (Test_7_digital_sec01_mod01). Status: `needs_review`. Extracted 33, created 32. Question at index 13 (source Q14) failed to INSERT because `stem_type_key` value `'identify_evidence_that_supports_conclusion'` (44 chars) exceeds the `VARCHAR(40)` column limit. SQLAlchemy/asyncpg raised `value too long for type character varying(40)`. Only the persisting step had any error (1 total); single question dropped (33→32).

2. **Resolved (normalization fix verified):** The systematic `[2, 3, 4, 5]` (and similar early-number) gap pattern reported on Test_5, Test_6_mod01, and Test_6_mod02 is GONE on Test_7_mod01. Persisted `source_question_number`s are contiguous 1–13, 15–33 — the only missing value (14) is the question dropped by the persisting-step truncation in finding 1, not by normalization. No `normalize`-step errors appeared in `validation_errors_jsonb` (zero `dropped_empty_stem` / `dropped_duplicate_stem` diagnostics).

3. **No "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.** That regression remains absent.

4. **No `qnum_ocr_crosscheck` mismatches and no `question_number_validation` errors recorded** — the only entry in `validation_errors_jsonb` is the single `persisting` truncation above.

## 2026-05-19 - Ingestion Test Run (Test_6_digital_sec01_mod02)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `657570b` — Filter passage line numbers from qnum OCR crosscheck

### Findings

1. **High:** Blocking validation errors on Cross-Text Connections question (validating step).
   - Job `dc235908-e4a0-48e0-b152-99f61cc3d09f` (Test_6_digital_sec01_mod02). Status: `needs_review`. Extracted 16, created 15. Question at index 7 (source Q12) tagged as Cross-Text Connections is missing required `stimulus_mode_key='prose_paired'` and `paired_passage_text`. Both errors flagged as `blocking`, which prevented this question from being created (15 created vs 16 extracted).

2. ~~**High:** Non-contiguous question numbers with gaps at [2, 3, 4, 5] (question_number_validation step).~~
   - ~~Same job. Found question numbers [1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 27, 30] — gaps at 2, 3, 4, 5. LLM skips early questions (2-5) and extracts non-sequential tail numbers (19, 27, 30), matching the same systematic extraction pattern seen on Test_5 and Test_6 mod01.~~
   - **Fixed (e3be02b):** Root cause was `_normalize_extracted_questions` deduping by `question_text` alone after `_split_passage_from_question` collapsed near-duplicate SAT stems ("Which choice…") to identical strings. LLM was always emitting 33 questions; the normalize layer was silently dropping ~half. Dedupe key is now `(question_text, source_question_number)`. Verified on Test_7 mod01 (job 01e44c3f): 33/33 with contiguous numbering 1–33.

3. ~~**Medium:** 16 question-number / OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Same job. Representative: question_index 15 LLM=30 but OCR=17. The crosscheck flags the non-contiguous LLM numbering vs sequential OCR-detected numbers — a symptom of the same underlying extraction issue as finding 2.~~
   - **Fixed (e3be02b, downstream symptom):** All mismatches were caused by finding 2 — restoring the missing questions also restored sequential numbering, eliminating the crosscheck mismatches.

4. **No "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.** That regression remains absent.

## 2026-05-19 - Ingestion Test Run (Test_6_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `657570b` — Filter passage line numbers from qnum OCR crosscheck

### Findings

1. ~~**High:** Non-contiguous question numbers with gaps at [2, 3, 5] (question_number_validation step).~~
   - ~~Job `21993eaf-0cc6-43c4-94b1-789d66dd267f` (Test_6_digital_sec01_mod01). Status: `needs_review`. Extracted 17, created 17. Found question numbers [1, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 26, 31] — gaps at 2, 3, 5. LLM is skipping early questions (2, 3, 5) and extracting non-sequential tail numbers (19, 26, 31), matching the same systematic extraction pattern seen on Test_5.~~
   - **Fixed (e3be02b):** Same `_normalize_extracted_questions` silent-dedupe bug. See Test_6 mod02 finding 2 above. Confirmed via DB inspection that `pass1_json.questions` always contained 33 raw entries; the normalize layer was dropping ~half.

2. ~~**Medium:** 16 question-number / OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Same job. Representative: question_index 16 LLM=31 but OCR=17. The crosscheck flags the non-contiguous LLM numbering vs the sequential OCR-detected numbers, a symptom of the same underlying extraction issue as finding 1.~~
   - **Fixed (e3be02b, downstream symptom):** Resolved by fixing finding 1.

3. **No "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.** No blocking `validating`-step errors; job reached `needs_review` with all 17 extracted questions persisted.

## 2026-05-19 - Ingestion Test Run (Test_5)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `66fbf69` — Update OpenWolf session state and debug log

### Findings

1. ~~**High:** Mod01 — non-contiguous question numbers with gaps at [3, 4, 5, 7] (question_number_validation step).~~
   - ~~Job `245d37e6-3e5a-41fc-b5aa-1289c41804ca` (Test_5_digital_sec01_mod01). Status: `needs_review`. Extracted 16, created 16. Found question numbers [1, 2, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 23, 31] — gaps at 3, 4, 5, 7. The LLM appears to be extracting questions with non-sequential numbers (jumping from 2→6, 7→8, and oddities like 20, 23, 31 in the tail), suggesting OCR or extraction confusion on this test form.~~
   - **Fixed (e3be02b):** Misdiagnosis at the time — the LLM was NOT confused, it was emitting 33 questions cleanly. `_normalize_extracted_questions` deduped by stem alone and silently dropped near-duplicate SAT stems. Composite-key dedupe restored.

2. ~~**High:** Mod01 — 14 question-number / OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Same job. Representative: question_index 15 LLM extracted 31 but OCR shows 16. The crosscheck correctly flags the non-contiguous numbering as mismatches between LLM-extracted and OCR-detected question numbers. This is a symptom of the same underlying extraction issue (item 1 above).~~
   - **Fixed (e3be02b, downstream symptom):** Resolved by fixing finding 1.

3. **High:** Mod02 — blocking validation error: missing paired_passage_text for Cross-Text Connections question (validating step).
   - Job `72048cf4-303f-4eb4-a098-49b7f9539956` (Test_5_digital_sec01_mod02). Status: `needs_review`. Extracted 16, created 15. Question at index 3 (source Q8) is tagged as Cross-Text Connections but has no `paired_passage_text` field. This is a blocking validation error that prevents auto-approval.

4. ~~**High:** Mod02 — non-contiguous question numbers with gaps at [3, 4, 5, 7] (question_number_validation step).~~
   - ~~Same job. Found question numbers [1, 2, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 26, 30] — gaps at 3, 4, 5, 7. Same pattern as mod01: the LLM skips question numbers 3-5 and 7.~~
   - **Fixed (e3be02b):** Same dedupe-loss root cause. See finding 1.

5. ~~**High:** Mod02 — 16 question-number / OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Same job. Representative: question_index 15 LLM=30 but OCR=50. Confirms systematic question-number extraction problems on Test 5.~~
   - **Fixed (e3be02b, downstream symptom):** Resolved by fixing finding 4.

6. **Medium:** Duplicate checksum prevented mod02 re-ingestion via run.sh.
   - The mod02 PDF was already ingested from a prior session. The runner exited with `{"error":"no job_id","response":"{\"detail\":\"This file has already been ingested (duplicate checksum).\"}"}`. Data for mod02 was collected from the existing job via direct DB queries.

7. **No "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared** in either module.

## 2026-05-19 - Ingestion Test Run (Test_5) — Docker prerequisite failure
Report created by: Claude
Git branch: `main`
Git checkpoint: `66fbf69` — Update OpenWolf session state and debug log

### Findings

1. **High:** Docker daemon not running — Postgres unavailable, ingestion test could not execute.
   - The test runner (`run.sh Test_5`) exited immediately with `RESULT_JSON:{"error":"postgres unavailable"}`. The Docker daemon was not running (`Cannot connect to the Docker daemon at unix:///home/jb/.docker/desktop/docker.sock`), so the Postgres container could not be started. No ingestion job was submitted or processed.
   - This is an environment prerequisite failure, not a pipeline bug. Start Docker before running ingestion tests.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01) [attempt 4]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `3a3eb72` — test 5 sec01 mod 01 successful - only chart bug left

### Findings

1. ~~**Medium:** 18 question-number/OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Job `edb9c0a8-3cc1-43d5-b08a-b96ede1b2c22` reached `needs_review` with 33/33 questions extracted and 33/33 created. All 18 validation errors are `qnum_ocr_crosscheck` mismatches where the LLM-extracted question number differs from the OCR-detected number. Representative examples: question_index 15 (LLM=16, OCR=40), question_index 16 (LLM=17, OCR=30), question_index 17 (LLM=18, OCR=20), question_index 18 (LLM=19, OCR=16), question_index 19 (LLM=20, OCR=17). The mismatches suggest OCR misreads of question numbers on Test 5 sec01 mod01 — the pattern (40, 30, 20, 16, 17) looks like OCR confusing stylized digits on this particular test form. No blocking validation errors; no "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.~~
   - **Fixed (657570b):** Root cause was OCR-side false positives, not the LLM. `_scan_qnums_from_ocr` was accepting passage line numbers (poetry/SAT "5, 10, 15, 20" margins) as question numbers and aligning them positionally against the LLM's question list. Changed to strict `+1` contiguity: the first bare integer is accepted, subsequent integers only accepted if they equal previous+1. Passage line numbers and OCR misreads no longer slot into the comparison list.

2. **Low:** Duplicate checksum prevented re-ingestion — test runner does not handle already-ingested PDFs gracefully.
   - The run.sh script exited with `RESULT_JSON:{"error":"no job_id","response":"{\"detail\":\"This file has already been ingested (duplicate checksum).\"}"}` because the PDF was already ingested in a prior session. The script does not have a code path for retrieving the existing job_id when a duplicate is detected. The existing job data was collected via direct DB queries instead.

## 2026-05-18 - VLM-Fused Extraction Drops All Passage Text
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. **Critical:** ~~qwen3-vl VLM-fused extraction drops ALL passage text — 0/33 questions have `current_passage_text`.~~
   - Job `edb9c0a8-3cc1-43d5-b08a-b96ede1b2c22` (Test 5 sec01 mod01). The OCR strategy was `ollama` (qwen3-vl:235b-instruct-cloud), which uses the VLM-fused path: the vision model processes page images directly and its output IS the extraction result (Pass 1 is skipped entirely via `raw_text = "_vision_fused_"` sentinel at `ingest.py:1498`). The model successfully extracted question stems, options, and answer keys, but **returned `passage_text: null` at the top level and omitted `passage_text` from every question dict**. For most questions, the VLM also dumped passage content directly into `question_text` (e.g., Q6's `question_text` starts with "The following text is adapted from Jean Webster's 1912 novel Daddy-Long-Legs..."). For Q1, the passage was dropped entirely (only the 65-char stem survived).
   - The pymupdf raw_text (32866 chars) in `pass1_json.raw_text` **does contain all passage content** — e.g., Q1's passage about "The King's Coin" starts at char offset 539.
   - Root cause: `build_vision_extract_prompt()` sends only page images to the VLM with no raw_text context. The prompt instructs the model to output `passage_text` per the JSON schema, but qwen3-vl ignores this field systematically and embeds passage content in `question_text` instead.
   - **Fixed:** Added two post-extraction helpers in `ingest.py`: (1) `_split_passage_from_question()` detects passage content in `question_text` using stem-opener patterns (e.g., "Which choice", "As used in the text", "Which quotation") at sentence boundaries (period, blank `_______`, or newline) and splits it into `passage_text` / `question_text`. (2) `_recover_passage_from_raw_text()` uses pymupdf `raw_text` to recover passages the VLM completely dropped (like Q1) — it finds the question stem in the raw text, looks backwards for the question number marker, and extracts the passage between them. Both helpers run inside `_normalize_extracted_questions()` after the shared_passage propagation step. Result: 33/33 questions now have properly separated passage_text and question_text.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01) [attempt 3]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Medium:** 18 question-number/OCR crosscheck mismatches (qnum_ocr_crosscheck step).~~
   - ~~Job `edb9c0a8-3cc1-43d5-b08a-b96ede1b2c22` reached `needs_review` with 33/33 questions extracted and created. All 18 validation errors are `qnum_ocr_crosscheck` mismatches where the LLM-extracted question number differs from the OCR-detected number. Representative examples: question_index 15 (LLM=16, OCR=40), question_index 16 (LLM=17, OCR=30), question_index 17 (LLM=18, OCR=20). The mismatches suggest OCR misreads of question numbers on this particular test form (Test 5 sec01 mod01) — the pattern (40, 30, 20, 16, 17) looks like OCR confusing stylized digits. No blocking validation errors; no "Option labels must be exactly {A, B, C, D}, got ['']" cascade appeared.~~
   - **Fixed (657570b):** Same OCR-side false-positive root cause as the attempt-4 entry above. Strict `+1` contiguity in `_scan_qnums_from_ocr` filters passage line numbers.

2. **High (prerequisite resolved this attempt):** Database had no tables — Alembic migrations needed.
   - The Postgres container was healthy on port 5434 but the `dsat_dev` database was completely empty (0 tables). The `run.sh` script only checks Postgres connectivity, not schema readiness. First two attempts today failed before reaching this point (Docker context issue), so the missing schema went unnoticed. Running `uv run alembic upgrade head` (migrations 001-018) resolved the issue and the ingestion job then submitted and completed successfully.
   - **Fixed:** Ran `alembic upgrade head` to create all 18 migration steps.

3. **High:** Graph/chart image crops not generated — layout detection produced no stimulus regions.
   - Job `edb9c0a8-3cc1-43d5-b08a-b96ede1b2c22`. Q14 (`stimulus_mode_key: table_and_passage`) and Q16 (`stimulus_mode_key: graph_and_passage`) both have structured data in `question_stimulus_assets` (JSON with series/headers), but no image crops were stored in `local_object_store/page-crops/charts/` or `page-crops/tables/` — those directories only contain `.gitkeep` files. The `ocr-artifacts/layout/` directory is also empty, meaning `detect_layout()` either failed silently or the vision model (`glm-ocr`) did not return valid region data with `chart`/`table` typed regions for the pages containing Q14 and Q16. Page renders do exist on disk (13 PNGs under `local_object_store/page-renders/official/5/verbal/section_01/module_01/`). The `crop_and_store()` code path is wired correctly and would have fired if `match_stimulus_regions_for_question()` returned chart/table regions — but it received none from layout detection. Result: no visual crop of the Q16 graph (line chart: "Ratio of Manganese to Calcium") or Q14 table ("Candidate Species for De-extinction") was saved; only the LLM-extracted structured JSON survived.
   - **Status:** Unresolved — layout detection needs debugging to determine why `glm-ocr` is not detecting chart/table regions on Test 5 page renders.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01) [attempt 2]
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. **High:** Docker daemon not running — ingestion test cannot execute.
   - The test runner (`run.sh`) requires Postgres on localhost:5434, started via `docker compose up -d db`. Docker client v29.2.1 is installed but the daemon is unreachable: Docker context is `desktop-linux` pointing to `/home/jb/.docker/desktop/docker.sock` which does not exist, and the system socket `/var/run/docker.sock` also has no responding daemon. The runner emitted `RESULT_JSON:{"error":"postgres unavailable"}` and exited before any job was submitted.
   - **Status:** Blocked — Docker daemon must be started manually (e.g., `sudo service docker start` or launch Docker Desktop). Same root cause as attempt 1 earlier today.

## 2026-05-18 - Ingestion Test Run (Test_5_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. **High:** Docker daemon unavailable — ingestion test could not run.
   - The test runner (`run.sh`) requires Postgres on localhost:5434, provided by a Docker container (`postgres:16` in `docker-compose.yml`). Docker socket at `/home/jb/.docker/desktop/docker.sock` does not exist; system socket `/var/run/docker.sock` exists but Docker daemon is not running. `sudo service docker start` failed (no sudo access). The runner emitted `RESULT_JSON:{"error":"postgres unavailable"}` and exited before submitting any job.
   - **Status:** Blocked — requires Docker daemon to be started manually by the user.

## 2026-05-18 - Phase 8 End-to-End Hardening Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

**Validation pass (2026-05-18, Claude Opus 4.7):** All 12 findings re-checked
against the current working tree (Phase 7 fixes already applied). Findings 2,
4, 5, 6, 7, 8, 11, 12 confirmed as gaps and fixed. Finding 1 confirmed already
fixed by Phase 7. Findings 3, 9, 10 judged by-design (verdicts inline). Verified
with `uv run pytest tests/test_admin_router.py tests/test_amendment_review.py
tests/test_amendment_capture.py tests/test_amendments.py tests/test_amendments_cli.py
tests/test_vocab_consistency.py` (`65 passed`) plus
`tests/test_ingestion_analysis.py tests/test_rule_doc_patcher.py tests/test_pipeline.py
tests/test_backend_regressions.py` (`110 passed`).

### Findings

1. ~~**Medium:** `promote_amendment` re-appraisal call inside try/except creates rollback hazard.~~
   - ~~`amendment_review.py:232-233` — `write_reappraisals_for_master_growth` is called inside the promotion try/except block. If re-appraisal raises an exception (e.g., permission error, disk full), the broad `except Exception` at line 234 calls `_restore_files(backups)`, undoing the already-committed master.json update and rule doc patch.~~
   - **Fixed:** Already resolved by the Phase 7 fix. Confirmed in current code:
     `write_reappraisals_for_master_growth` runs at `amendment_review.py:238-249`,
     outside the promotion try/except, in its own best-effort try/except that
     logs a warning and never rolls back. No further change needed.

2. ~~**Medium:** Admin router tests are all mocked — no integration test for the actual file-system promotion flow.~~
   - ~~`test_admin_router.py` tests for amendment endpoints all monkeypatch `amendment_review` functions to return canned results. None exercise the real code paths that touch the filesystem.~~
   - **Fixed:** Added `test_admin_amendment_promote_flow_against_real_filesystem`
     and `test_admin_amendment_promote_unapproved_returns_422_real_filesystem`
     to `test_admin_router.py`. They build a real on-disk repo in `tmp_path`,
     re-bind every `amendment_review` function via `functools.partial(repo_root=repo)`
     so the genuine implementation runs against tmp dirs (no canned results),
     and drive the approve → promote flow through the actual router endpoints,
     asserting master.json/doc updates, file moves, and the 422 status guard.
     Only the external `regenerate_vocab_appendices` subprocess is stubbed.

3. **Medium (verdict: by-design):** `_amendment_or_404` maps `error_code="conflict"` to HTTP 409.
   - Re-checked current code: `amendment_review.py` uses `error_code="validation"`
     (→422) for "Proposed key is already active" (line 301) and for all status-guard
     errors (`_require_status`, line 422; `promote_amendment` lines 177/184). Only
     genuinely ambiguous rule-doc patch anchors (`dry_run_rule_doc_patch` /
     `apply_loaded_rule_doc_patch` failures) surface `error_code="conflict"` (→409).
     The two-code split is therefore already correct and meaningful: 422 for
     client-side validation failures, 409 for an actionable repository-state
     conflict needing a manual patch. No behavior change made. The new
     `test_admin_amendment_promote_unapproved_returns_422_real_filesystem`
     additionally pins the validation → 422 mapping through the real code path.

4. ~~**Low:** `test_promote_patches_doc_updates_master_regenerates_and_moves_file` doesn't verify the regenerated content.~~
   - **Fixed:** The fake `regenerate_vocab_appendices` now asserts, at call time,
     that master.json already carries the new `evidence_scope_shift` entry and
     that the reading rule doc body was patched. The test also verifies the new
     master entry's `status`/`parent`/`description`, the promoted amendment
     file's `status` and `promotion` review note, and that the candidate row was
     dropped after promotion.

5. ~~**Low:** `test_promote_restores_master_and_doc_when_regeneration_fails` doesn't verify the amendment file state on failure.~~
   - **Fixed:** The test now asserts the amendment file state after a
     regeneration failure: it is no longer in `pending/`, was not promoted to
     `approved/`, and was routed to `needs_manual_patch/` with
     `status="needs_manual_patch"` and a `rule_doc_patch_failure` review note.

6. ~~**Low:** `test_capture_amendments_from_completed_official_jobs_scans_db` uses a fake DB that ignores query filtering.~~
   - **Fixed:** `_FakeDb` now applies the same predicate as the real query
     (`job_type == "ingest"`, `content_origin == "official"`, completed status,
     non-null `pass2_json`) and records the executed statement. Added
     `test_capture_amendments_skips_jobs_that_fail_query_filter`, which feeds in
     non-official, wrong-type, and null-`pass2_json` jobs and asserts only the
     official ingest job is captured.

7. ~~**Low:** No test for concurrent file access in `_link_candidate` (fcntl.flock).~~
   - **Fixed:** Added `test_link_candidate_concurrent_writes_do_not_lose_amendment_ids`
     to `test_amendments.py`. It launches 12 threads (synchronized on a barrier
     for maximum contention) that each link a distinct amendment id to the same
     candidate row, then asserts every id survived — proving the `fcntl.flock`
     exclusive lock serializes the read-modify-write.

8. ~~**Low:** CLI `scripts/amendments.py` hardcodes `REPO_ROOT` from `__file__`.~~
   - **Fixed:** `--repo-root` now uses a `_resolve_repo_root` type converter
     that `expanduser().resolve()`s the path and rejects any directory missing a
     `vocabulary/` subdirectory with a clear `argparse` error. The default
     remains the script-relative `REPO_ROOT` (correct because the script lives
     inside the repo), but an explicit `--repo-root` is now validated.

9. **Low (verdict: by-design):** `issubset` rather than exact-match in the vocab-consistency scanner test.
   - Confirmed intentional: the scanner is expected to grow new diagnostic
     codes, and `issubset` keeps the test stable across additive changes. Exact
     matching would make every new error code a breaking test change. Left as-is;
     recorded here as a deliberate forward-compatibility decision.

10. **Low (verdict: by-design):** `test_collect_db_records_streams_rows_from_async_session` uses a hardcoded SQL text check.
    - Confirmed intentional: the substring check on `str(stmt)` is a lightweight
      smoke assertion that the query targets the expected tables without standing
      up a real database. A query refactor that changes table names *should*
      prompt a deliberate test update. Left as-is as an accepted trade-off.

11. ~~**Low:** No end-to-end test for the full `capture → approve → promote → re-appraisal` flow.~~
    - **Fixed:** Added `test_capture_approve_promote_reappraisal_end_to_end` to
      `test_amendment_review.py`. It captures a proposal via
      `capture_amendment_proposal`, approves and promotes it through the real
      `amendment_review` functions, and seeds a prior `taxonomy_coverage.json`
      with a stale master hash so the test verifies promotion triggers
      `write_reappraisals_for_master_growth` and writes a `reappraisal_*.md`
      report. Only the `regenerate_vocab_appendices` subprocess is stubbed.

12. ~~**Low:** `test_gen_vocab_promote_from_amendment_uses_gated_workflow` does not monkeypatch `amendment_review.REPO_ROOT`.~~
    - **Fixed:** The test now also `monkeypatch.setattr(amendment_review,
      "REPO_ROOT", repo)`, so if `cmd_promote_from_amendment` ever stops
      forwarding `repo_root` the promotion would no longer silently fall back to
      the real repository root.

## 2026-05-18 - Phase 7 Ingestion Analysis & Re-Appraisal Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

**Validation pass (2026-05-18, Claude Opus 4.7):** All 10 findings re-checked
against current code. Findings 1, 3, 4, 5, 6, 7, 10 confirmed and fixed.
Findings 2, 8, 9 judged not defects (verdicts below). Verified with
`uv run pytest tests/test_ingestion_analysis.py tests/test_amendment_review.py
tests/test_amendments_cli.py tests/test_amendments.py tests/test_amendment_capture.py
tests/test_pipeline.py tests/test_backend_regressions.py tests/test_rule_doc_patcher.py`
(`146 passed`).

1. ~~**Medium:** `write_reappraisals_for_master_growth` is called inside `promote_amendment`'s try/except block after `_drop_candidate` succeeds.~~
   - `amendment_review.py:232-233` — if the re-appraisal write raises an exception, it triggers `_restore_files(backups)` which undoes the master.json update and rule doc patch that already succeeded. A re-appraisal IO failure would roll back a successful promotion.
   - **Fixed:** Moved the `write_reappraisals_for_master_growth` call outside the
     promotion try/except. Re-appraisal now runs only after the promotion is
     fully committed, inside its own best-effort try/except that logs a warning
     (`logger`) and never rolls back. Added `logging` + module logger to
     `amendment_review.py`.

2. **Medium (verdict: not a defect):** Hashes are not stored back into the DB job record.
   - The task spec says "Store hashes in every ingestion analysis" but hashes are only written to JSON files on disk (`taxonomy_coverage.json`). There is no `master_json_hash` / `reading_rules_hash` / `grammar_rules_hash` / `ontology_hash` column on `QuestionJob`.
   - **Verdict:** The spec text is "Store hashes in every ingestion *analysis*",
     and the analysis report is the unit being produced. All four hashes are
     written into every report (`taxonomy_coverage.json`, `validation_failures.json`,
     `amendment_candidates.json`, and `summary.md`). The Phase 7 exit criteria
     are met. Adding `QuestionJob` columns is a schema change / scope expansion,
     not a fix — left as a potential future enhancement, not actioned.

3. ~~**Low:** `_question_records` falls back to `pass1_json` which lacks annotation fields.~~
   - When `pass2_json` is None it returns `pass1_json` records that produce empty `# Question` markdown files.
   - **Fixed:** Added `_has_question_content`; `write_ingestion_analysis` now
     skips writing a question file for any record with no taxonomy fields and
     no question text, so pass1-fallback rows no longer emit empty stubs.

4. ~~**Low:** `_exam_code` evaluates `pass1.get("source_metadata")` twice.~~
   - The original finding text is largely self-refuting (concludes the behavior "is actually fine"); the only real nit is the double `.get()` call.
   - **Fixed:** `_exam_code` now reads `source_metadata` once into `raw_meta`
     and reuses it.

5. ~~**Low:** `_amendment_candidates` does not use `extract_amendment_proposal` from `amendments.py`.~~
   - It manually walked `_amendment_proposals` / `reasoning.amendment_proposal` and missed the legacy top-level `amendment_proposal` key.
   - **Fixed:** `_amendment_candidates` now falls back to the shared
     `extract_amendment_proposal`, which handles both `reasoning.amendment_proposal`
     and the legacy top-level `amendment_proposal` key.

6. ~~**Low:** `glob("*/*/taxonomy_coverage.json")` assumes exactly 2-level depth.~~
   - **Fixed:** `write_reappraisals_for_master_growth` now uses
     `rglob("taxonomy_coverage.json")`, which is layout-independent.

7. ~~**Low:** No test for re-appraisal content correctness.~~
   - **Fixed:** Added `test_reappraisal_markdown_records_exam_and_hash_comparison`
     verifying the re-appraisal markdown carries both hashes, the source exam
     code, and the question count.

8. **Low (verdict: enhancement, not a defect):** `_summary_markdown` doesn't include per-question details or hash comparison guidance.
   - **Verdict:** The Phase 7 spec only requires a `summary.md` to exist, and it
     does, with counts and all four hashes. Richer per-question diffing is a
     usability enhancement, not a correctness defect — deferred, not actioned.

9. **Low (verdict: by design):** `write_ingestion_analysis` is called in `ingest.py:1956-1959` with a bare `except Exception` that logs a warning.
   - **Verdict:** This is intentional. Analysis report writing is best-effort
     and must never fail an otherwise successful ingestion. The failure is
     logged (`logger.warning`), not silently swallowed. Keeping the non-fatal
     behavior is correct; no change made.

10. ~~**Low:** No test for `_question_records` fallback paths.~~
    - **Fixed:** Added `test_question_records_falls_back_to_pass1_questions`,
      `test_question_records_handles_single_question_pass2_without_annotations`,
      `test_question_records_handles_empty_annotations_list`,
      `test_empty_question_records_do_not_emit_stub_files`, and
      `test_amendment_candidates_captures_legacy_top_level_proposal`.

## 2026-05-18 - Phase 6 Consistency Scanner Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Medium:** `_check_reading_shape_rules` only checks `skill_family_key`, not `reading_skill_family_key`.~~
   - `check_vocab_consistency.py:231-232` — reads `payload.get("skill_family_key")` for
     Cross-Text and quantitative shape rules, but `FIELD_TO_VOCAB` also maps
     `reading_skill_family_key` to the same vocabulary. Records using
     `reading_skill_family_key` instead of `skill_family_key` will skip both
     `cross_text_missing_prose_paired` and `quantitative_missing_graphic_data` checks.
   - **Fixed:** Shape checks now accept `skill_family_key` and
     `reading_skill_family_key`; fixture coverage verifies both Cross-Text and
     quantitative issues are reported through the alias.

2. ~~**Low:** `FIELD_TO_VOCAB` is duplicated in 3 places (scanner, amendments, vocab_candidates).~~
   - Scanner has 19 entries, amendments has 13, vocab_candidates has 13. The scanner
     legitimately has more (target-prefixed variants, `distractor_distance`), but the
     shared 13 entries must be kept in sync manually. A new field added to one but not
     the others will silently be missed.
   - **Fixed:** Added shared `app.models.vocab_fields` mappings. Amendment
     capture and candidate capture now use `BASE_FIELD_TO_VOCAB`; the scanner
     uses `SCANNER_FIELD_TO_VOCAB` for base plus scanner-only fields.

3. ~~**Low:** `collect_db_records` loads all rows with no limit or chunking.~~
   - `select(QuestionJob)`, `select(QuestionAnnotation)`, `select(QuestionOption)` with
     no `limit()` or batching. Acceptable for a CLI tool on small datasets but will OOM
     on large production databases.
   - **Fixed:** DB collection now uses async streaming with `yield_per`
     execution options for jobs, annotations, and options.

4. ~~**Low:** `_check_domain_rules` only flags grammar keys on reading questions, not the reverse.~~
   - Doesn't check for `skill_family_key` or `reading_focus_key` on grammar-domain questions.
   - **Fixed:** Domain checks now also flag grammar-domain records that carry
     reading skill/focus keys.

5. ~~**Low:** `--no-fail` exits 0 on all issues regardless of severity.~~
   - `check_vocab_consistency.py:402` — treats blocking errors and review warnings
     equally. A CI pipeline using `--no-fail` will never catch any issue.
   - **Fixed:** `--no-fail` now exits 0 only for non-blocking findings; blocking
     issues still return non-zero. Added `exit_code_for_report` coverage.

6. ~~**Low:** `PARENT_FIELD_BY_CHILD_FIELD` is hardcoded; new hierarchical vocabularies
     added to `master.json` won't be scanned for parent mismatches.
   - `scripts/check_vocab_consistency.py:46-51`~~
   - **Fixed:** Parent-child checks now derive hierarchical vocabulary
     relationships from `master.json` parent-set metadata, with alias fields for
     known parent vocabularies. Added dynamic hierarchical fixture coverage.

7. ~~**Low:** No DB integration test for `collect_db_records` or `run_scan --all/--db`.~~
   - All 4 tests use in-memory fixtures via `scan_records`/`scan_option_rows`. The async
     DB path and `run_scan` flow are untested.
   - **Fixed:** Added async-session fixture coverage for `collect_db_records`
     using streamed fake rows for jobs, annotations, and options.

## 2026-05-18 - Phase 5 Dev CLI Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Low:** `gen_vocab.py --promote-from-amendment` hardcodes `repo_root=REPO_ROOT`.~~
   - `gen_vocab.py:484` — unlike `amendments.py` which has `--repo-root`, the
     promote-from-amendment path has no CLI flag for custom repo root. Tests
     monkeypatch `gen_vocab.REPO_ROOT` instead. Both default to the same root,
     so this only affects non-standard layouts.
   - **Fixed:** Added `--repo-root` to `scripts/gen_vocab.py` and routed
     `--promote-from-amendment` through the supplied repository root.

2. ~~**Low:** CLI test exercises 4 transitions on the same amendment sequentially,
   masking the Phase 4 status-guard gap.
   - `test_amendments_cli.py:119-138` — does `request-more-evidence` → `approve` →
     `reject` on the same amendment. Each succeeds because there's no status
     transition validation, reinforcing that the gap exists but hiding it behind
     a passing test.
   - `tests/test_amendments_cli.py`~~
   - **Fixed:** Split the CLI transition coverage into independent tests for
     list/show, request-more-evidence, approve, and reject so each command runs
     from an appropriate starting state.

3. ~~**Low:** `gen_vocab.py --promote-from-amendment` gives no explicit regeneration
     confirmation output.
   - `gen_vocab.py:492-495` — prints `"promoted amendment ..."` but doesn't confirm
     that `ontology.py` and VOCAB blocks were regenerated. `amendment_review.promote_amendment`
     handles regeneration internally; the user just sees the amendment status.
   - `scripts/gen_vocab.py`~~
   - **Fixed:** Successful `--promote-from-amendment` now prints an explicit
     regeneration confirmation naming the `master.json` source.

4. **Info:** All Phase 5 checklist items are complete. CLI (`scripts/amendments.py`)
     implements all 6 subcommands, shares logic with the admin API through
     `amendment_review`, `gen_vocab.py --promote-from-amendment` is gated behind
     the approval workflow, and `--promote` is blocked without
     `--unsafe-direct-promote`. 5 CLI tests pass.

## 2026-05-18 - Phase 4 Admin Review API Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Medium:** `approve_amendment` has no status transition guard.~~
   - `amendment_review.py:67-87` — does not check `amendment.status` before approving. Allows double-approve, approve-after-reject, and approve-after-promote, silently overwriting the status and `admin_decision`. Only `promote_amendment` has a status guard (`amendment.status != APPROVED`).
   - **Fixed:** `approve_amendment` now only accepts `pending` and
     `more_evidence_requested` amendments. Invalid transitions return a
     validation failure instead of overwriting status/admin metadata.

2. ~~**Medium:** `reject_amendment` has no status transition guard.~~
   - `amendment_review.py:90-108` — allows rejecting an already-promoted amendment. The file moves to `rejected/` but the key remains active in `master.json`, creating inconsistency between file state and vocabulary state.
   - **Fixed:** `reject_amendment` now blocks `promoted` amendments and only
     allows rejection from pre-promotion review states.

3. ~~**Medium:** `_restore_files` rollback on promotion failure is untested.~~
   - `amendment_review.py:190-192` — the try/except with `_restore_files(backups)` is the critical safety mechanism if patching fails after `master.json` has been mutated. No test exercises this path; the only promotion test mocks regeneration so it never fails mid-operation.
   - **Fixed:** Added a promotion regression that forces regeneration failure
     after `master.json` mutation and verifies both `master.json` and the rule
     doc body are restored.

4. ~~**Low:** `request_more_evidence` has no status transition guard.~~
   - `amendment_review.py:111-126` — can be called on already-approved or already-promoted amendments with no semantic validation.
   - **Fixed:** `request_more_evidence` now only accepts `pending`
     amendments.

5. ~~**Low:** No business-logic test for `reject_amendment`.~~
   - Only a mocked router test exists (`test_admin_router.py:121`). No test in `test_amendment_review.py` verifies that the file actually moves to `rejected/` and the status updates.
   - **Fixed:** Added service-level tests proving rejection moves the file,
     updates status, and blocks promoted amendments.

6. ~~**Low:** No business-logic test for `request_more_evidence`.~~
   - Same as finding 5 — only a mocked router test.
   - **Fixed:** Added service-level tests proving pending amendments can request
     more evidence and approved amendments cannot.

7. ~~**Low:** `_amendment_or_404` returns HTTP 409 for all non-not-found errors.~~
   - `admin.py:61` — schema validation failures, already-active-key, and patch failures all return 409 (Conflict). Some are more naturally 422 or 400.
   - **Fixed:** `AmendmentOperationResult` now carries an `error_code`, and the
     router maps `not_found` to 404, `validation` to 422, and true conflicts to
     409.

8. ~~**Low:** `promote_amendment` doesn't verify amendment file directory.~~
   - Uses `_find_amendment_path` which searches all directories. A manually placed `approved`-status file in `rejected/` would pass the status check. Unlikely edge case.
   - **Fixed:** Promotion now requires the approved amendment file to still be
     in the pending review directory before promotion.

9. ~~**Low:** Dual-read pattern in `promote_amendment` is fragile.~~
   - `amendment_review.py:162` calls `apply_rule_doc_patch(loaded.path, ...)` which re-reads the amendment file. The file still has `status=approved` at that point. Works correctly now but the implicit ordering dependency could confuse future maintainers.
   - **Fixed:** Added `apply_loaded_rule_doc_patch` and changed promotion to pass
     the already-loaded amendment object into the patcher, removing the implicit
     re-read dependency.

## 2026-05-18 - Phase 3 Rule-Doc Patch Engine Review
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Low:** `_inside_generated_vocab_block` off-by-one edge case.~~
   - `rule_doc_patcher.py:174-182` — `rfind("<!-- VOCAB:", 0, index + 1)` and the `block_end + len(" END -->")` comparison can include text after the `END -->` marker on the same line. In practice `END -->` is line-terminal so this rarely triggers, but the bounds check is imprecise.
   - **Fixed:** Generated VOCAB block detection now parses matching
     `<!-- VOCAB:... START -->` / `<!-- VOCAB:... END -->` markers and treats
     only the exact generated block bounds as protected. Added a regression
     proving an editable anchor immediately after an END marker is accepted.

2. ~~**Low:** `apply_rule_doc_patch` uses bare `assert` for `result.doc_path is not None`.~~
   - `rule_doc_patcher.py:62` — assertions are stripped with `-O`, so if an unreachable code path produced `ok=True` with `doc_path=None`, it would crash in production with no useful message. Should be an explicit `if result.doc_path is None: raise ValueError(...)`.
   - **Fixed:** Replaced the bare assert with an explicit guard that returns a
     failed `RuleDocPatchResult`, marks the amendment `needs_manual_patch`, and
     records conflict details.

3. ~~**Low:** No test for ambiguous `before` anchor (count > 1).~~
   - `_validate_body_patch_target` returns an "ambiguous" error when `text.count(patch.before) > 1`, but no test covers this case. The code is correct but untested.
   - **Fixed:** Added `test_rule_doc_patch_rejects_ambiguous_before_anchor`.

4. ~~**Medium:** `apply_rule_doc_patch` regenerates appendix blocks from `master.json` *without* first adding the new key to it.~~
   - `rule_doc_patcher.py:63-67` — `regenerate_vocab_appendices()` runs `gen_vocab.py --generate`, which emits only active keys from master.json. If the approved key hasn't been promoted into master.json yet (that's Phase 4's job), the regenerated appendix blocks will omit the new key, making the patch incomplete until a separate promotion step adds it. The ordering constraint (master.json update before body patch + regeneration) isn't documented or enforced.
   - **Fixed:** Appendix regeneration is now opt-in and guarded. Calling
     `apply_rule_doc_patch(..., regenerate_appendix=True)` before the amendment
     value is active in `vocabulary/master.json` fails before writing the rule
     document, moves the amendment to `needs_manual_patch`, and skips
     regeneration. Phase 4 can safely opt in after master promotion.

## 2026-05-18 - Phase 2 Amendment Capture Review
Report created by: Claude Sonnet 4.6
Git branch: `main`
Git checkpoint: `00a9307` — Add master vocabulary file as single source of truth + review queue

### Findings

1. ~~**Medium:** `pass2_json` overwrite loses annotation data for single-question jobs.~~
   - **Fixed:** Single-question jobs now merge the annotation into `pass2_payload`
     via `pass2_payload.update(pass2_annotation_records[0]["annotation"])` at
     `ingest.py:1926`. Multi-question jobs store annotations under `_annotations`.
     The original bug (metadata-only payload) is resolved.

2. ~~**Medium:** `_link_candidate` writes to `candidates.json` without file locking.~~
   - **Fixed:** `_link_candidate` now uses `fcntl.flock(fh.fileno(), fcntl.LOCK_EX)`
     with a `fcntl = None` graceful fallback (non-Linux platforms). Matches the
     locking pattern in `vocab_candidates.py`.

3. ~~**Medium:** Dedup key too aggressive — `_merge_supporting_example` discards
   second proposal's body fields.~~
   - **Fixed:** `_merge_supporting_example` now calls
     `_conflicting_proposal_note(existing, amendment)` which compares `definition`,
     `current_best_fit`, `why_current_rules_are_insufficient`, `official_evidence`,
     `rule_doc_patch`, and `master_json_patch`. Conflicts are appended to
     `review_notes` as structured JSON. Test
     `test_duplicate_proposals_preserve_conflicting_body_fields_in_review_notes`
     verifies the conflict detection.

4. ~~**Medium:** `_affected_vocab` fails for several real vocabularies.~~
   - **Fixed:** `FIELD_TO_VOCAB` now maps all 14 annotation-relevant fields including
     `syntactic_trap_key` → `SYNTACTIC_TRAP_KEYS` and `transition_subtype_key` →
     `TRANSITION_SUBTYPE_KEYS`. Test
     `test_capture_amendment_proposal_maps_additional_ontology_fields` verifies both
     new entries.

5. **Low:** `PLANSIBILITY_SOURCE_KEYS` typo propagated to `FIELD_TO_VOCAB`.
   - `amendments.py:38` maps `plausibility_source_key` → `PLANSIBILITY_SOURCE_KEYS`,
     matching the typo in `ontology.py:188` and `master.json:1629`. Consistent
     so no runtime mismatch, but the misspelling is now permanent in amendment
     files and generated artifacts.

6. **Low:** No test for `ValidationError` path in `capture_amendment_proposal`.
   - The `except (TypeError, ValueError, ValidationError)` block at
     `amendments.py:86` is never exercised by tests. A malformed proposal
     (missing required fields) should be tested to verify the warning is
     recorded and `None` returned.

7. **Low:** No test for warning survival through final job cleanup.
   - `_record_job_warning` adds warnings to `job.validation_errors_jsonb`, but
     the ingest pipeline's final cleanup (ingest.py:1926-1931) rebuilds
     `validation_errors_jsonb` from `existing_job_warnings + all_errors`. No
     integration test proves amendment-capture warnings survive this pass.

8. **Low:** `_merge_supporting_example` re-validates entire `RuleAmendment`.
   - `amendments.py:341-354` calls `RuleAmendment.model_validate(data)` on the
     whole merged dict. If the file's metadata is stale or the schema has
     evolved, this could fail on a previously valid amendment.

9. **Low:** `_record_job_warning` doesn't deduplicate.
   - If the same job triggers `capture_amendment_proposal` twice (normal flow
     + backfill), identical warnings are appended without dedup.

10. **Low:** Prompt-to-schema alignment is weak — now observed via logging.
    - The annotation prompt says "A proposal must include affected_doc,
      affected_vocab, proposed_value…" but `_proposal_to_amendment` has many
      fallback paths (`proposal.get("proposed_key")`, `proposal.get("evidence_text")`,
      `proposal.get("reason")`) suggesting the LLM regularly uses different field
      names. Rather than adding a JSON schema to the prompt (which would make
      LLM output formula-based), observational logging was added: `_first()`
      helper tracks which fallback fields the LLM used, and `logger.info`
      logs heuristic inference in `_affected_doc`, `_affected_vocab`,
      `_proposed_value`. After construction, amendment logs all fallback
      mappings: `"amendment %s used fallback field mappings: %s"`.

## 2026-05-18 - Controlled-Vocabulary Audit (ontology vs rules docs)
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `8ffc83f` — router - needs review flag fixed

**Context:** Full cross-reference of every controlled-vocabulary set in
`backend/app/models/ontology.py` against `rules_agent_dsat_reading_v2.md` and
`rules_agent_dsat_grammar_ingestion_generation_v7.md`. The 2026-05-18 reading-focus
fix resolved one instance of the desync class; this audit found the same class
(see 2026-05-16 18-PDF run finding 4) still live in two larger vocabularies.
Validator behavior confirmed in `backend/app/models/options.py` and `annotation.py`.

### Findings

1. **High:** `STUDENT_FAILURE_MODE_KEYS` missing the entire grammar v7 §D.7
   grammar-specific failure-mode block. `student_failure_mode_key` is mandatory
   on every distractor (worked example §B.12 emits these verbatim) and is
   validated at `options.py:42-46` (`ValueError` on miss). 17 absent keys.
   - **Fixed:** Added `tense_proximity_pull`, `polarity_blindness` (reading v2
     §19 approved synonym) and the 16 §D.7 grammar keys to
     `STUDENT_FAILURE_MODE_KEYS` in `ontology.py` (now 63 keys, all unique).

2. ~~**High:** Reading v2 §10.1/§10.2 `reasoning_trap_key` trap vocabulary — 21
   keys absent from `DISTRACTOR_TYPE_KEYS`. The question-level `reasoning_trap_key`
   field (`annotation.py:24`) has no validator so is not blocking, but §10 states
   the same vocabulary applies per-option, and per-option `distractor_type_key`
   IS validated (`options.py:31`). reading_v2 is internally inconsistent: §12.1's
   `distractor_type_key` list omits these §10 keys.~~
   - Re-traced: `distractor_type_key` is NOT blocking — every §12.1 key is already
     in `DISTRACTOR_TYPE_KEYS`; the risk was only LLM cross-contamination between
     §10 and §12.1. `reasoning_trap_key` was confirmed a consumed signal (generation
     reads `target_reasoning_trap_key`), so it warrants a controlled vocabulary.
   - **Fixed (2026-05-18):** Added `REASONING_TRAP_KEYS` (49 keys) to `ontology.py`
     as a dedicated set distinct from `DISTRACTOR_TYPE_KEYS`. reading_v2 §10 was
     deduplicated first — `wrong_row_or_column`, `individual_from_aggregate`,
     `all_measures_not_checked` merged into `wrong_table_row_or_column`,
     `individual_inference_from_aggregate_bins`, `single_measure_focus`. Added a
     `reasoning_trap_key` `@field_validator` to `annotation.py`; added the set to
     the `annotate_prompt.py` ALLOWED KEY VALUES block; tightened reading_v2 §10
     intro to state §10 governs `reasoning_trap_key` and §12.1 governs
     `distractor_type_key` (not interchangeable).
   - **Follow-up (deferred):** generate-side `target_reasoning_trap_key` is stored
     in untyped `generation_profile` JSONB (`payload.py:42`) — no schema, so it
     cannot be validated yet. Typing `generation_profile` is a separate change;
     `REASONING_TRAP_KEYS` is ready for it.

3. **Low:** Ontology extras absent from both rules docs (cosmetic, never surfaced
   to the LLM, unverifiable): `STIMULUS_MODE_KEYS` `notes_summary`;
   `STEM_TYPE_KEYS` `conform_to_standard_english`, `compare_contributions`,
   `synthesize_information`. Not fixed — left pending doc reconciliation.

## 2026-05-18 - Ingestion Test Run (Test_4_digital_sec01_mod01)
Report created by: Claude (ingestion-test skill subagent)
Git branch: `main`
Git checkpoint: `8ffc83f` — router - needs review flag fixed

**Context:** Attempted the official-verbal ingestion pipeline test for
Test_4_digital_sec01_mod01. The API rejected the submission before any job was
created: `{"detail":"This file has already been ingested (duplicate
checksum)."}`. The PDF was already ingested as job
`c9aeeb9d-cc84-4012-bc8f-5af8366f16c8` on 2026-05-17. The bundled runner has no
re-ingestion / force flag, so no fresh job ran. Findings below reflect the
state of the existing job `c9aeeb9d` (status `approved`, 33 extracted /
31 created, 8 validation errors). No new pipeline behavior could be verified;
the prior q6/q7 `reading_focus_key` block (see 2026-05-17 entry below) remains
present and unfixed in this job's stored validation errors.

### Findings

1. **Prereq failure:** Duplicate-checksum rejection — Test_4_digital_sec01_mod01
   could not be re-ingested. RESULT_JSON: `{"error":"no job_id","response":"..
   This file has already been ingested (duplicate checksum)."}`. Run aborted at
   submission. To force a fresh run, the existing asset/job for this checksum
   must be removed or a re-ingestion flag added to the runner.

2. ~~**High:** q6/q7 still blocked at `validating` step in existing job
   `c9aeeb9d` — `reading_focus_key 'structural_pattern' is not allowed for
   skill_family_key 'text_structure_and_purpose'` (severity `blocking`),
   question_index 5 (source_question_number 6) and question_index 6
   (source_question_number 7). Both questions remain absent from the 31 created
   (33 extracted). The ontology/rules-doc desync described in the 2026-05-17
   "Reading Ontology vs Rules-Doc Desync" entry is NOT yet resolved in the data
   for this job. A fresh re-ingest is required to confirm any code-side fix.~~
   - **Diagnosed (2026-05-18, Claude Opus 4.7):** Not a live code bug. `git blame`
     of `ontology.py:330` shows `READING_FOCUS_BY_SKILL_FAMILY['text_structure_and_purpose']`
     listed `overall_purpose, text_structure, sentence_function, rhetorical_shift,
     author_stance` (no `structural_pattern`) until commit `bbb6c51`
     (2026-05-18 05:01, "Reconcile controlled vocabularies"). Job `c9aeeb9d` was
     ingested 2026-05-17 — under the old map — so `validator.py:185` blocked the
     LLM-emitted `structural_pattern` focus key and dropped q6/q7. Those errors
     are a frozen snapshot in `validation_errors_jsonb`.
   - **Fixed:** Current code already accepts `structural_pattern` for
     `text_structure_and_purpose` (verified by invoking `validate_question`
     directly — no `reading_focus_key` error). Added regression tests
     `test_validate_text_structure_accepts_structural_pattern` and
     `test_validate_rejects_focus_key_from_wrong_family` in `test_pipeline.py`
     to lock the mapping and prove the family/focus gate still rejects
     cross-family keys. The stale stored errors in job `c9aeeb9d` remain until a
     fresh re-ingest, which is itself blocked by the duplicate-checksum
     rejection (finding 1 / separate re-ingest-flag gap).

3. **Medium:** 6 `question_number_validation` `out_of_range` warnings in job
   `c9aeeb9d` — question_index 27–32 carry numbers 28–33, flagged "outside
   expected range 1–27 for verbal/mod01". Non-blocking; these reflect the
   pre-`bb1c597` (1,27) cap and predate the (1,33) range correction.

Note: The "Option labels must be exactly {A, B, C, D}, got ['']" cascade did
NOT appear in job `c9aeeb9d`. No new run executed today.

## 2026-05-17 - Ingestion Test Run (Test_4_digital_sec01_mod02)
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `4ec08a4` — test: add concurrent annotation tests and fix mock settings

**Context:** Ran the official-verbal ingestion pipeline test for
Test_4_digital_sec01_mod02 (job 31ab501e-6b29-4d0f-87f9-021c1d539a2b). Job
reached `approved` with 33/33 extracted and 33/33 created — no blocking
validation errors, no per-question validating-step failures. The "Option
labels must be exactly {A, B, C, D}, got ['']" cascade did NOT appear.

### Findings

1. **Medium:** 33 qnum_ocr_crosscheck warnings — every question (indices 0–32)
   flagged a question-number mismatch between the LLM-extracted value and the
   OCR text. Job 31ab501e-6b29-4d0f-87f9-021c1d539a2b, all 33 questions.
   Representative: "question_index 0: LLM extracted 1 but OCR text shows 2".
   Consistent off-by-one offset module-wide; non-blocking — job reached
   approved and persisted all 33 questions.

## 2026-05-17 - Stale Test After Verbal Cap Correction
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `4ec08a4` — test: add concurrent annotation tests and fix mock settings

### Findings

1. **Low:** `test_validate_qnums_out_of_range` failed — not an ingestion regression.
   - Commit `bb1c597` changed the verbal range in `_DSAT_QUESTION_RANGES`
     (ingest.py:197-198) from `(1, 27)` to `(1, 33)` but did not update the test.
   - Test data `[25, 26, 28]` (comment `# 28 > 27 for verbal`) is now fully in
     range, so `_validate_question_numbers` emits no `out_of_range` warning.
   - **Fixed:** updated test data to `[32, 33, 35]` (`35 > 33 cap`) in
     test_backend_regressions.py:1104; still triggers `non_contiguous` too.

## 2026-05-17 - Reading Ontology vs Rules-Doc Desync (Test 4 ingest)
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `bb1c597` — feat(ingest): correct verbal question cap and add ingestion test tooling

**Context:** Test 4 sec01/mod01 ingest (job `c9aeeb9d`) reached `approved` with 31/33
questions persisted. Two questions (q6, q7) were blocked at the `validating` step:
`reading_focus_key 'structural_pattern' is not allowed for skill_family_key
'text_structure_and_purpose'`. Investigation traced this to a controlled-vocabulary
desync between the LLM-facing rules doc and the code ontology.

### Findings

1. ~~**High: `reading_focus_key` controlled vocabulary has diverged between
   `rules_agent_dsat_reading_v2.md` and `backend/app/models/ontology.py`.**
   - The Pass 2 annotate prompt injects the full reading rules doc *and* a
     code-derived allowed-keys block — these now contradict each other.
   - The validator checks the code ontology (`READING_FOCUS_BY_SKILL_FAMILY`);
     the LLM trusts the richer, repeated rules-doc descriptions. Any question
     whose focus the model names per the rules doc fails validation.
   - Full audit of all 7 reading skill families — 4 match, 3 drift:
     - `text_structure_and_purpose`: rules says `structural_pattern`, code says
       `text_structure`; code also has `rhetorical_shift`, rules §7.6 does not.
       → directly blocked Test 4 q6, q7.
     - `words_in_context`: rules §7.5 adds `figurative_language_meaning`; code
       ontology lacks it.
     - `cross_text_connections`: near-total divergence — only `text2_response_to_text1`
       is shared. Rules §7.7 has 6 keys absent from code; code has 3 keys absent
       from rules. Every cross-text question is a latent validation failure.
   - Likely the same root cause behind the earlier "unknown enum key" symptoms
     (bug-106), not generic model sloppiness.~~
   - **Fixed (2026-05-18):** Reconciled `ontology.py` to the rules doc as the
     canonical source — the rules doc is internally self-consistent and is
     referenced by both the annotate and generate prompts (tables, checklists),
     so it is cheaper and safer to make the ontology follow it than vice versa.
     `READING_FOCUS_BY_SKILL_FAMILY` updated: `text_structure_and_purpose` →
     `(overall_purpose, sentence_function, structural_pattern, author_stance)`;
     `words_in_context` gains `figurative_language_meaning`;
     `cross_text_connections` → the full rules §7.7 set (`text2_response_to_text1,
     both_texts_agree, texts_disagree, text2_qualifies_text1,
     text2_contradicts_text1, methodological_critique, expectation_violation`).
     All 38 reading focus keys now appear verbatim in the rules doc. Verified the
     5 dropped keys (`text_structure`, `rhetorical_shift`, `agreement_across_texts`,
     `difference_across_texts`, `shared_topic_different_conclusion`) have no DB
     rows in `question_annotations` and no code references, so no migration is
     needed. The allowed-keys block in `annotate_prompt.py` is built from this
     same ontology, so prompt and validator are now consistent. Unblocks Test 4
     q6/q7.

## 2026-05-16 - Full Ingestion Run Error Tracking (18 PDFs)
Report created by: Claude Opus 4.7
Git branch: `main`
Git checkpoint: `cde9480` — fix(pipeline): remediate in-flight gaps and log 17 open gap inventory entries

**Context:** Ran all 18 official verbal test PDFs (Tests 1, 4–11, sec01/mod01 + sec01/mod02) through `/ingest/official/pdf` with `ocr_strategy=auto`. DB crashed mid-run before completion. 4 jobs reached terminal states before crash.

### Findings

1. ~~**High: Empty option labels on all questions after annotation merge.**
   - Extraction (Pass 1) produces correct option labels (`label: 'A'`, `label: 'B'`, etc.)
   - After annotation (Pass 2), the merged dict `{**q_data, **annotate_json}` replaces the `options` key with the annotation output, which has empty labels
   - Validation then fails: `Option labels must be exactly {A, B, C, D}, got ['']`
   - Affects ALL questions in every job that reaches the validation step
   - **Not yet fixed** — annotation prompt or merge logic needs to preserve option labels~~
   - **Fixed:** Added `_merge_for_validation()` + `_EXTRACTION_OWNED_KEYS` to `ingest.py`. Extraction owns the structural keys (`options`, `question_text`, `passage_text`, `correct_option_label`, etc.); on any merge collision extraction wins, so the annotation's per-option *analysis* block (keyed `option_label`, blank `label`) can no longer blank the A/B/C/D labels. Applied at both merge sites (ingest pipeline + generate pipeline).

2. ~~**High: Question number out-of-range after extraction.**
   - LLM assigns question numbers 28–33 for modules that only have 27 questions (verbal/mod01)
   - The `_validate_question_numbers` check correctly flags these as `out_of_range`
   - OCR crosscheck also shows mismatches (LLM says Q1, OCR says Q10; LLM says Q18, OCR says Q50)
   - The LLM is hallucinating question numbers that don't exist in the PDF
   - **Not yet fixed** — extraction prompt may need stronger constraints on question numbering~~
   - **Fixed:** Added an explicit QUESTION NUMBERING rule block to `EXTRACT_SYSTEM_PROMPT` — `source_question_number` must be the literal printed number (copy, never compute/guess), capped at the module maximum (27 verbal / 22 math), unique and contiguous, `null` when no number is printed, and never derived from output array position.

3. ~~**High: JSON parse failure on large inputs (39K chars).**
   - `Test_10_digital_sec01_mod02.pdf` (39836 input chars) produced valid-looking JSON that `extract_json_from_text` couldn't parse
   - Error: `No valid JSON found in text (provider='ollama', model='qwen3-vl:235b-instruct-cloud', input_len=39836)`
   - Preview shows correct JSON structure (`{ "passage_text": null, "questions": [...]`) suggesting truncated output or formatting issue
   - **Not yet fixed** — need to check if max_tokens limit is causing truncation or if the JSON has nested issues~~
   - **Fixed:** Confirmed truncation — the 16000-token extraction `max_tokens` cap couldn't fit a full large module's JSON. Added `extraction_max_tokens` setting (default 32000); both Pass 1 `complete()` calls now read `getattr(settings, "extraction_max_tokens", 32000)`.

4. ~~**Medium: Unknown annotation keys from LLM.**
   - `stem_type_key` values: `'analyze_structure'`, `'most_logically_completes'`, `'synthesize_information'`, `'emphasize_duration_purpose'`, `'highlight_difference'`
   - `stimulus_mode_key` values: `'notes_to_summary'`
   - `reading_focus_key` mismatch: `'structural_pattern'` not allowed for `skill_family_key 'text_structure_and_purpose'`
   - These are valid semantic descriptions but not in the validator's allowed enum sets
   - **Not yet fixed** — validator enums need updating or the annotation prompt needs to restrict output~~
   - **Fixed:** These were hallucinated synonyms, not new concepts — kept the controlled vocabulary intact and restricted the prompt instead. `annotate_prompt.py` now builds an `ALLOWED KEY VALUES` block from the ontology (`STIMULUS_MODE_KEYS`, `STEM_TYPE_KEYS`, `READING_FOCUS_BY_SKILL_FAMILY`) and injects it into `_SYSTEM_BASE` as rule 6, instructing the LLM to choose verbatim from the list.

5. ~~**Medium: `.env` file has stale `OCR_VISION_MODEL`.**
   - `.env` sets `OCR_VISION_MODEL=qwen2.5vl:7b` but `config.py` default is `qwen3.0-vl`
   - The `.env` value overrides the default, so fused VLM fallback uses the old model
   - **Not yet fixed** — `.env` needs updating to `qwen3.0-vl`~~
   - **Fixed:** `backend/.env` and `backend/.env.example` updated to `OCR_VISION_MODEL=qwen3.0-vl`; `tests/test_config.py` default-value assertion updated to match.

6. ~~**Low: DB connection saturation during concurrent ingestion.**
   - With 18 concurrent jobs and `max_concurrent_jobs=4`, the connection pool was exhausted
   - Direct Python/psql queries failed with `ConnectionRefusedError`
   - Eventually Docker/PostgreSQL container died entirely
   - **Not yet fixed** — connection pool sizing or job concurrency needs tuning~~
   - **Fixed:** `max_concurrent_jobs` raised 4→8; DB pool made configurable via `db_pool_size` (15) and `db_max_overflow` (10) — 25 connections total, comfortably covering 8 concurrent jobs plus request handlers and staying well under PG's default `max_connections=100`. `database.py` engine now reads these settings instead of hardcoded `pool_size=5`.

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

## Single Test Ingestion — 2026-05-17T04:37:15-07:00

ERROR: FastAPI server failed to start within 30s

---

## Single Test Ingestion — 2026-05-17T04:53:06-07:00

**Ingestion result**: annotating

- **PDF**: `Test_1_digital_sec01_mod01.pdf`
- **Job ID**: `3bd8c445-f12a-442f-a6d2-3ef482487402`
- **Status**: annotating
- **Errors/Warnings**: 0


#### LLM
- Extract latency: ?ms
- Annotate latency: ?ms

---

## 2026-05-17 — Single Test Ingestion (Test 1 / verbal / sec01 / mod01)

**PDF**: `Test_1_digital_sec01_mod01.pdf`  
**Job ID**: `b3c81e18-bfd6-4772-a845-325faffa98c3`  
**Final Status**: `failed` (0 of 33 questions persisted)

---

### Pipeline Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| PDF parse | ~0s | Text layer present, 14 pages extracted |
| Pass 1 (extraction) | ~183s (3 min) | LLM: `qwen3-vl:235b-instruct-cloud` via Ollama |
| Layout detection | ~10s | `glm-ocr:latest` — 3 of 14 pages failed (no valid JSON) |
| Pass 2 (annotation) | ~22 min total | 33 questions × ~40s avg per annotation call |
| Validation | immediate | **All 33 questions blocked** |

### Root Cause: Every Question Failed Validation

The entire batch was rejected because **all 33 questions** had blocking validation errors. No questions were persisted to the `questions` table.

#### Primary Blocking Error — `options` field empty

Every single question (33/33) had:
```
field: options
message: "Option labels must be exactly {A, B, C, D}, got ['']"
severity: blocking
```

This means the annotation LLM (`qwen3-vl:235b-instruct-cloud`) returned an `options` field that was either:
- An empty list `[]`
- A list of empty-string labels `['']`
- Missing the A/B/C/D option structure entirely

Since `options` was empty/invalid, every question also failed the `correct_option_label` check:
```
"correct_option_label 'X' is not present in the option labels ['']"
```

#### Secondary Errors

| Type | Count | Detail |
|------|-------|--------|
| `stem_type_key` unknown | 12 | Values like `conform_to_standard_english`, `complete_the_argument`, `synthesize_information` not in validator whitelist |
| `stimulus_mode_key` unknown | 1 | `notes_summary` not recognized |
| Question numbers out of range (28–33) | 6 | LLM extracted 33 questions but the PDF only has 27 for verbal/mod01 |
| OCR cross-check mismatches | 8 | LLM extracted question numbers 16–23 don't match OCR text numbers 22,23,16–21 |

### Why Pass 2 Was Slow (~22 minutes)

- **Annotation prompt size**: ~88K chars (~20K prompt tokens) per question due to the full grammar rules reference being included
- **33 questions** × **~40s average** per LLM call = **~22 minutes** total
- The model is a cloud-hosted Ollama model (`qwen3-vl:235b-instruct-cloud`), which adds network latency
- Each annotation call uses ~10K input tokens + ~2K output tokens

### Why the Options Were Empty

The most likely cause is that the **annotation prompt output format** doesn't match what the validator expects. The LLM likely returned options in a format like:

```json
{
  "options": [{"A": "text"}, {"B": "text"}, {"C": "text"}, {"D": "text"}],
  "correct_option_label": "B"
}
```

But the validator expects:

```json
{
  "options": [
    {"label": "A", "text": "text"},
    {"label": "B", "text": "text"},
    ...
  ],
  "correct_option_label": "B"
}
```

The `normalize_annotation()` function in `app/parsers/json_parser.py` should handle this transformation, but either:
1. The LLM is returning options in a format `normalize_annotation()` doesn't handle, or
2. The LLM is not returning options at all (returning `[]` or `[{"label": "", "text": "..."}]`)

### Recommendations

1. **Check `normalize_annotation()`**: Verify how it handles the `options` field from `qwen3-vl:235b-instruct-cloud` output
2. **Consider a smaller/faster model for annotation**: The 88K-char system prompt is very large; a model with better instruction-following on structured output would reduce errors
3. **Add options format validation before persistence**: Fail fast with a clear error message if options come back empty
4. **Fix question number range**: The LLM extracted 33 questions (Q1–Q33) from a 27-question module; the OCR cross-check detected mismatches but didn't correct them
5. **Add `stem_type_key` and `stimulus_mode_key` values** to the validator's allowed enums: `conform_to_standard_english`, `complete_the_argument`, `synthesize_information`, `compare_contributions`, `notes_summary`

---

## 2026-05-17 — Root Cause Analysis: Pass 2 Annotation "Stuck" & All Questions Failing Validation

### Executive Summary

The ingestion pipeline for Test 1 (verbal/sec01/mod01) completes both Pass 1 (extraction) and Pass 2 (annotation) successfully, but **every single question fails validation** because the annotation LLM returns options in `option_label`/`option_text` format, which overwrites the extraction's `label`/`text` format during the dict merge. The `_EXTRACTION_OWNED_KEYS` protection in `_merge_for_validation()` should restore the extraction options, and isolated testing confirms it works — but **all 33 questions still fail with empty option labels** in production.

### Investigation Results

1. **Extraction (Pass 1)**: Works correctly. All 33 questions have 4 options with proper `{label: "A"|"B"|"C"|"D", text: "..."}` format. The `_normalize_extracted_questions()` function even backfills empty labels with A/B/C/D.

2. **Annotation (Pass 2)**: The `qwen3-vl:235b-instruct-cloud` model returns annotations with:
   - `stem_type_key`: values like `conform_to_standard_english` (not in ontology's `STEM_TYPE_KEYS`) — **review** severity
   - `stimulus_mode_key`: `notes_summary` (not in `STIMULUS_MODE_KEYS`) — **review** severity
   - `options`: list of dicts with `option_label`/`option_text` format instead of `label`/`text` — **this is the root cause of the blocking errors**

3. **Merge Protection**: The `_merge_for_validation()` function correctly preserves extraction-owned keys (`options`, `question_text`, etc.) by restoring them from `q_data` after the merge. Isolated testing confirms this works:
   ```
   q_data labels: ['A', 'B', 'C', 'D']    ← extraction format
   annotate labels: ['A', 'A', ...]          ← option_label format (from annotate_json)
   merged labels: ['A', 'B', 'C', 'D']      ← correctly restored from q_data
   ```

4. **Yet ALL 33 questions fail** with `"Option labels must be exactly {A, B, C, D}, got ['']"`. This means `merged["options"]` somehow has `label=""` for all options in the actual pipeline run.

### The Mystery

The isolated test passes validation with 0 blocking errors. But the full pipeline fails for all 33 questions. This suggests either:
- A mutation of `q_data` somewhere in the per-question loop that strips option labels
- A race condition or shared-reference issue in the dict merge
- The annotation LLM returning a format that bypasses the protection in a way not caught by isolated testing

### Additional Issues

- **Question count**: LLM extracts 33 questions but the PDF only has 27 for verbal/mod01. Questions 28-33 are out of range.
- **OCR cross-check mismatches**: Questions 16-22 have LLM-extracted numbers that don't match the OCR text.
- **`stem_type_key` not in ontology**: `conform_to_standard_english` (12 occurrences), `complete_the_argument`, `synthesize_information`, `compare_contributions` are not in `STEM_TYPE_KEYS` in `ontology.py`.
- **`stimulus_mode_key` not in ontology**: `notes_summary` is not in `STIMULUS_MODE_KEYS` (should be `notes_bullets`).
- **Layout detection**: `glm-ocr:latest` fails to return valid JSON for 3 of 14 pages.
- **Pass 2 is slow**: ~40s per question × 33 questions ≈ 22 minutes, due to the ~88K-char annotation system prompt (~20K input tokens per call).

### Recommended Fixes

1. **Add debug logging** to `_merge_for_validation()` and the per-question loop to capture the exact state of `q_data["options"]` and `annotate_json["options"]` before and after merge, then re-run the pipeline to identify where labels are lost.

2. **Map `option_label` → `label`** in `normalize_annotation()` or `_merge_for_validation()` so that annotation-style options are normalized to the extraction format, regardless of which dict "wins" the merge.

3. **Add missing stem_type_key values** to `ontology.py`: `conform_to_standard_english`, `complete_the_argument`, `synthesize_information`, `compare_contributions`.

4. **Add missing stimulus_mode_key**: `notes_summary` → map to `notes_bullets` (or add as alias).

5. **Reduce annotation prompt size**: The 88K-char system prompt is the main bottleneck. Consider trimming the rules reference or using a two-pass approach where the domain is detected first, then only the relevant rules section is included.

6. **Fix question count over-extraction**: Investigate why the LLM extracts 33 questions from a 27-question module.

---

## 2026-05-17 — Bug: option_label/option_text vs label/text Format Mismatch

### Bug Description

The annotation rules markdown (`rules_agent_dsat_grammar_ingestion_generation_v7.md`) defines the output schema for options using `option_label` and `option_text` keys (see Section B.12 examples). However, the extraction pipeline and internal code use `label` and `text` keys. The validator (`validator.py`) checks for `label` and `text`, causing ALL questions to fail with:

```
Option labels must be exactly {A, B, C, D}, got ['']
```

### Root Cause

The `_merge_for_validation()` function protects extraction-owned keys (including `options`) by restoring `q_data["options"]` after the `{**q_data, **annotate_json}` merge. In isolated testing, this works correctly. However, in production runs, all 33 questions failed with empty option labels, suggesting a subtle mutation or edge case that bypasses the protection.

### Fix Applied

1. **`backend/app/pipeline/validator.py`** — Added option key normalization before validation:
   ```python
   for opt in options:
       if isinstance(opt, dict):
           if "label" not in opt or not opt["label"]:
               opt["label"] = opt.get("option_label", "")
           if "text" not in opt or not opt["text"]:
               opt["text"] = opt.get("option_text", "")
   ```

2. **`backend/app/routers/ingest.py`** (`_merge_for_validation`) — Added the same normalization after the merge:
   ```python
   for opt in merged.get("options", []):
       if isinstance(opt, dict):
           if "label" not in opt or not opt["label"]:
               opt["label"] = opt.get("option_label", "")
           if "text" not in opt or not opt["text"]:
               opt["text"] = opt.get("option_text", "")
   ```

3. **`backend/app/models/ontology.py`** — Added missing values:
   - `STEM_TYPE_KEYS`: `conform_to_standard_english`, `most_logically_completes`, `synthesize_information`, `compare_contributions`
   - `STIMULUS_MODE_KEYS`: `notes_summary`

### Why Both Locations

- **Validator** is the last line of defense — it must handle whatever format arrives
- **`_merge_for_validation`** normalizes early so downstream code (persistence, etc.) also sees consistent keys
- The `option_hydration.py` module already handles both formats at persist time, so this is a belt-and-suspenders approach

### Dual-Key Reference

| Internal Key | Rules v7 Key | Used In | Normalized By |
|---|---|---|---|
| `label` | `option_label` | Extraction, Validator, DB | validator.py, ingest.py merge |
| `text` | `option_text` | Extraction, Validator, DB | validator.py, ingest.py merge |
| `correct_option_label` | `correct_option_label` | Both stages | Already consistent |
| `source_question_number` | `source_question_number` | Both stages | Already consistent |

---

## 2026-05-17 — Full Codebase Schema Inconsistency Audit

### Summary

Found **3 blocking issues** (1 fixed, 2 latent) and **6 latent issues** across the backend codebase. The root cause of the production failure (all 33 questions failing validation) was the `option_label`/`option_text` vs `label`/`text` format mismatch between the annotation LLM output and the validator.

### Issues Found

| # | Severity | Issue | Files | Status |
|---|----------|-------|-------|--------|
| 1 | **BLOCKING** | `option_label`/`option_text` vs `label`/`text` format mismatch | validator.py, ingest.py | **FIXED** |
| 2 | REVIEW | Missing `stem_type_key` values in ontology | ontology.py | **FIXED** |
| 3 | REVIEW | Missing `stimulus_mode_key` value (`notes_summary`) | ontology.py | **FIXED** |
| 4 | LATENT | Domain string vs `question_family_key` mapping | annotate_prompt.py | Needs monitoring |
| 5 | LATENT | `skill_family` display name vs `skill_family_key` enum | annotate_prompt.py | Needs monitoring |
| 6 | LATENT | `subskill` vs `grammar_focus_key` | annotate_prompt.py | Needs monitoring |
| 7 | OK | DB column names (`option_label`/`option_text`) vs extraction (`label`/`text`) | db.py, ingest.py | Handled by persist code |
| 8 | OK | `correct_option_label` consistent across pipeline | All files | Consistent |
| 9 | OK | API response format (`label`/`text`) | student.py, admin.py | Consistent |

### Detailed Findings

**Issue 1 (FIXED): option format mismatch**
- Annotation LLM returns `{option_label: "A", option_text: "...", is_correct: false, ...}`
- Validator expects `{label: "A", text: "..."}`
- `_merge_for_validation` restores extraction's options but the annotation's options overwrite first
- **Fix**: Added `option_label → label` and `option_text → text` normalization in both `validator.py` and `_merge_for_validation()`
- Also in `option_hydration.py`: `option_analyses_by_label()` already handles both formats via `opt.get("option_label") or opt.get("label")`

**Issue 2 (FIXED): Missing stem_type_key values**
- `conform_to_standard_english` — returned by LLM for SEC complete_the_text questions
- `most_logically_completes` — defined in reading v2 Section 3.2
- `synthesize_information` — in `_READING_STEMS` but not in `STEM_TYPE_KEYS`
- `compare_contributions` — in `_READING_STEMS` but not in `STEM_TYPE_KEYS`
- **Fix**: Added all 4 to `STEM_TYPE_KEYS` in `ontology.py`

**Issue 3 (FIXED): Missing stimulus_mode_key**
- `notes_summary` — LLM returns this instead of `notes_bullets` for Rhetorical Synthesis questions
- **Fix**: Added `notes_summary` to `STIMULUS_MODE_KEYS` in `ontology.py`

**Issue 4 (LATENT): Domain string vs question_family_key**
- Annotation returns `"domain": "Standard English Conventions"` (display name)
- Ontology uses `"question_family_key": "conventions_grammar"` (enum key)
- `normalize_annotation()` bubbles up `question_family_key` from nested `classification` dict
- `_detect_domain()` and `_infer_domain_from_annotation()` handle the domain string
- **Risk**: If LLM returns `domain` without `question_family_key`, the latter may be `None`

**Issue 5 (LATENT): skill_family display name vs enum**
- Rules v7 examples use `skill_family: "Form, Structure, and Sense"` (display name)
- Ontology uses `skill_family_key: "form_and_structure"` (snake_case enum)
- The `allowed_keys` block in the annotation prompt lists the enum values
- **Risk**: LLM may return display names instead of enum values

**Issue 6 (LATENT): subskill vs grammar_focus_key**
- Rules v7 examples use `subskill: "subject-verb agreement with plural prepositional object"` (free text)
- Ontology uses `grammar_focus_key: "subject_verb_agreement"` (snake_case enum)
- **Risk**: `grammar_focus_key` validation may flag LLM-returned values not in `GRAMMAR_FOCUS_KEYS`

**Issue 7 (OK): DB column name mapping**
- `QuestionOption` uses `option_label` and `option_text` columns
- `_persist_single_question()` correctly maps `opt.get("label")` → `option_label` and `opt.get("text")` → `option_text`
- `option_analyses_by_label()` correctly handles both `option_label` and `label`

### Key Name Reference Table

| Extraction (Pass 1) | Annotation (Pass 2) | DB (Persist) | Validator | Normalized? |
|---------------------|--------------------|---------------|-----------|-------------|
| `label` | `option_label` | `option_label` | `label` | ✅ Now yes |
| `text` | `option_text` | `option_text` | `text` | ✅ Now yes |
| `correct_option_label` | `correct_option_label` | `current_correct_option_label` | `correct_option_label` | ✅ Yes |
| `question_text` | `question.question_text` | `current_question_text` | `question_text` | ✅ Yes |
| `passage_text` | `question.passage_text` | `current_passage_text` | `passage_text` | ✅ Yes |
| `stem_type_key` | `stem_type_key` or `classification.stem_type_key` | `stem_type_key` | `stem_type_key` | ✅ Normalized |
| `stimulus_mode_key` | `stimulus_mode_key` or `question.stimulus_mode_key` | `stimulus_mode_key` | `stimulus_mode_key` | ✅ Normalized |
| `domain` (N/A) | `classification.domain` | N/A | Not checked | ⚠️ Not validated |
| `question_family_key` | `classification.question_family_key` | N/A | `question_family_key` | ✅ Normalized |
| `grammar_role_key` | `classification.grammar_role_key` or top-level | N/A | `grammar_role_key` | ✅ Normalized |
| `grammar_focus_key` | `classification.grammar_focus_key` or top-level | N/A | `grammar_focus_key` | ✅ Normalized |

---
