# Second Pass: TASKS_GEN_PIPELINE Implementation Review

This is a second-pass review of [TASKS_GEN_PIPELINE.md](../TASKS_GEN_PIPELINE.md) against the current backend implementation in this directory.

## Executive Summary

The generation pipeline is partially implemented. The main scaffolding exists:

- generation router exists
- generation run creation exists
- background generation loop exists
- seed selection via embeddings exists
- drift detection exists
- coaching generation exists
- router registration exists
- payload models and tests exist

The biggest mismatch is that the current backend still uses a second LLM realism-scoring call as the quality gate. The task doc explicitly replaces that with corpus-grounded conformance using `v_corpus_fingerprint`, `generation_result_jsonb`, and preserved failed attempts. That replacement is not implemented.

In practice, the current pipeline behaves more like an alpha-v4-style system with some v1 improvements, not the full task-doc design.

## Status Key

- `Complete`: implemented in a way that broadly matches the task doc
- `Partial`: implemented, but with material behavior differences
- `Missing`: not implemented or not present in this backend

## Task-by-Task Status

### Task 1 — Migration 038 context

Status: `Assumed complete`

The review did not re-audit migration `038`, but the codebase is clearly written against generation fields such as:

- `content_origin`
- `generation_run_id`
- `seed_question_id`
- seeded generation templates

This aligns with the task doc’s assumption that the foundational generation schema already exists.

### Task 2 — Migration 041: corpus fingerprint + status constraint + generation_result_jsonb

Status: `Missing`

What the task doc expects:

- new statuses: `drift_failed`, `conformance_failed`
- `question_ingestion_jobs.generation_result_jsonb`
- materialized view `v_corpus_fingerprint`
- function `fn_refresh_corpus_fingerprint()`

What exists now:

- no `041_corpus_fingerprint.sql` migration found under [migrations](./migrations)
- no references to `v_corpus_fingerprint` in the app code
- no references to `fn_refresh_corpus_fingerprint()`
- no visible handling of `conformance_failed`

Impact:

The corpus-grounded gate described in the task doc cannot run in the current implementation.

### Task 3 — `app/prompts/generation.py`

Status: `Partial`

Implemented in [app/prompts/generation.py](./app/prompts/generation.py):

- `PASS1_OUTPUT_SCHEMA`
- grouped `_CONSTRAINT_GROUPS`
- `build_generation_system_prompt()`
- `build_generation_user_prompt()`
- IRT anchor support

Mismatch:

- the file still includes `build_realism_scoring_prompt()`
- the task doc explicitly says there should be no second realism LLM call

So the prompt file is structurally close, but it still carries the old quality-gate approach.

### Task 4 — `app/pipeline/drift.py`

Status: `Partial`

Implemented in [app/pipeline/drift.py](./app/pipeline/drift.py):

- `compute_expected_fingerprint()`
- `detect_drift()`
- `DriftReport`
- `should_rerun()`

Missing relative to the task doc:

- no `ConformanceReport`
- no `corpus_conformance_score()`
- no family-aware SEC critical dimensions
- no `evidence_distribution_key`, `inference_distance_key`, or `blank_position_key` in critical drift
- no grammar-specific critical handling for `conventions_grammar`

Current behavior:

- drift only checks a smaller set of dimensions
- rerun logic depends only on critical drift, not corpus conformance

### Task 5 — `app/pipeline/generate.py`

Status: `Partial`

Implemented in [app/pipeline/generate.py](./app/pipeline/generate.py):

- `create_generation_run()`
- `select_seed_question()` using embeddings with round-robin fallback
- `process_generation_run()` background loop
- merging run constraints over seed profile
- staging generated content through `question_ingestion_jobs`
- Pass 2 reuse via `process_job()`
- drift check after Pass 2

Major mismatches:

- still performs a second LLM realism-scoring call
- does not run corpus conformance against `v_corpus_fingerprint`
- inserts generated jobs with status `'extracting'`, while the task doc says generated jobs should skip extraction and begin at `'annotating'`
- preserves no per-attempt audit JSON in `generation_result_jsonb`
- deletes drift-failed jobs instead of preserving them
- does not mark terminal failures as `drift_failed` or `conformance_failed`
- writes `generation_params_snapshot_jsonb` to `generated_questions`, not to the staged job as described
- always marks the run `complete` at the end unless a fatal exception occurs; it does not compute `failed` vs `partial_complete` vs `complete`
- LLM error retries are not separated from drift-attempt retries the way the task doc specifies

Important implementation note:

The code claims unspecified seed dimensions are not inherited, but the actual merge is:

```python
merged = {**seed_profile, **run_constraints}
```

That means unspecified dimensions from the seed profile are inherited. This contradicts the task doc.

### Task 6 — `app/prompts/coaching.py`

Status: `Complete`

The prompt module exists and is wired into coaching generation. This part appears aligned with the task doc at a high level.

### Task 7 — `app/pipeline/coaching.py`

Status: `Partial`

Implemented in [app/pipeline/coaching.py](./app/pipeline/coaching.py):

- loads question content and choices
- calls coaching prompt
- writes `question_coaching_annotations`
- writes `question_reasoning.coaching_summary`

Mismatch:

- `_find_span()` uses exact substring matching
- the task doc requires whitespace normalization before matching
- the task doc also calls for explicit null-result logging for unmatched spans; current logging is minimal

So the pipeline exists, but the span-resolution logic is lighter than planned.

### Task 8 — `app/routers/generate.py`

Status: `Partial`

Implemented in [app/routers/generate.py](./app/routers/generate.py):

- `POST /generate`
- `GET /generate/runs`
- `GET /generate/runs/{run_id}`
- `GET /generate/runs/{run_id}/questions`
- `GET /generate/templates`
- `PATCH /generate/questions/{id}/status`
- `GET /generate/runs/{run_id}/drift`

Missing relative to the task doc:

- no `GET /generate/runs/{run_id}/jobs`
- no corpus-too-small warning in `POST /generate`
- `GET /drift` only queries `v_generation_traceability`; it does not merge staging attempts from `question_ingestion_jobs`

This means pre-approval visibility and failed-attempt analysis are both incomplete.

### Task 9 — `app/models/payload.py` additions

Status: `Partial`

Implemented in [app/models/payload.py](./app/models/payload.py):

- `GenerationRequest`
- `GenerationRunRead`
- `GeneratedQuestionRead`
- `GeneratedQuestionStatusUpdate`

Mismatch:

- no `GenerationRunCreated` model
- `GenerationRequest.item_count` has no `ge=1, le=20` guard from the task doc
- no warning fields for corpus bootstrap state

### Task 10 — Hook into approval path in `app/routers/jobs.py`

Status: `Partial`

Implemented in [app/routers/jobs.py](./app/routers/jobs.py):

- approval path exists
- IRT refresh is triggered as a background task
- coaching generation is triggered for generated jobs

Missing relative to the task doc:

- no corpus fingerprint refresh
- no synchronous rewrite from staging `content_origin='generated'` to production `content_origin='ai_human_revised'`

Related mismatch in [app/pipeline/upsert.py](./app/pipeline/upsert.py):

- generated questions are still upserted with `content_origin='generated'`
- the task doc explicitly says production rows must be rewritten to `ai_human_revised`

### Task 11 — `app/main.py`

Status: `Complete`

The generate router is registered in `app/main.py`.

### Task 12 — `app/pipeline/validator.py`

Status: `Partial`

The validator accepts `content_origin` as a parameter, which is the right shape for the planned guard.

But the task-doc-specific behavior is not clearly implemented:

- there is no visible skip for generated-job source checks in [app/pipeline/validator.py](./app/pipeline/validator.py)

This may be handled elsewhere in the ingestion flow, but based on the validator module alone, the task is incomplete.

### Task 13 — Tests

Status: `Partial`

Implemented:

- [tests/test_generation.py](./tests/test_generation.py)
- [tests/test_drift.py](./tests/test_drift.py)

What is covered well:

- prompt grouping
- seed selection
- basic drift behavior
- some coaching helpers
- run creation validation

What is missing relative to the task doc:

- corpus conformance tests
- `generation_result_jsonb` audit-path tests
- preserved `drift_failed` row behavior
- `conformance_failed` behavior
- pre-approval `/generate/runs/{run_id}/jobs` read path
- dual-source drift endpoint behavior
- corpus bootstrap warning behavior
- approval hook test for corpus fingerprint refresh

The test suite matches the current implementation, not the fuller task-doc design.

### Task 14 — End-to-end smoke test

Status: `Not packaged as described`

There is no obvious repo-local smoke-test script or checklist implementing the exact task-doc flow. The current codebase has enough pieces for manual testing, but not the full task-doc workflow because the corpus conformance layer is still absent.

## Current Architecture vs Planned Architecture

### What is already strong

- The backend has a real generation router and background run loop.
- It reuses the ingestion pipeline rather than inventing a separate annotation path.
- Seed selection by embedding similarity is implemented.
- Prompt grouping is implemented.
- Drift detection exists and is tested.
- Coaching generation after approval exists.

### What still blocks parity with the task doc

- No corpus fingerprint migration or refresh path
- No corpus-grounded conformance gate
- Failed drift attempts are deleted instead of preserved
- No attempt-level `generation_result_jsonb` audit trail
- No pre-approval run-jobs endpoint
- No production rewrite to `ai_human_revised`
- Still using an LLM realism judge instead of empirical corpus gating

## Bottom Line

If the question is “does this backend contain the generation pipeline?”, the answer is yes.

If the question is “does it match the design in `TASKS_GEN_PIPELINE.md`?”, the answer is not yet. The current implementation is best described as:

- `complete` on router and core scaffolding
- `partial` on prompting, drift, coaching, models, approval hooks, and tests
- `missing` on the corpus-conformance architecture that the task doc treats as the defining quality-control mechanism

## Recommended Next Delta

The highest-value next step is to implement the corpus-based quality gate before adding more surface area. In order:

1. add migration `041_corpus_fingerprint.sql`
2. add `generation_result_jsonb` and preserved failed-attempt semantics
3. implement `ConformanceReport` and `corpus_conformance_score()` in `app/pipeline/drift.py`
4. remove the realism-scoring LLM gate from `app/pipeline/generate.py`
5. add `GET /generate/runs/{run_id}/jobs`
6. rewrite approved generated content to `ai_human_revised` in the approval/upsert path

