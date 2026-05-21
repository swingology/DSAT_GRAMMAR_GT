# Generation, Review, and Self-Study Factory Task List

## Goal

Build a saved-question generation system that can produce targeted DSAT
questions on admin or self-study-agent request, review those questions with a
multi-model LLM ensemble, and give admins a visual review dashboard for
approving or rejecting low-quality generated items before students see them.

The system should support both grammar and reading generation, variable
question quantities, adjustable difficulty targets, official-question source
examples, student retrieval filters, and adaptive generation requests from a
self-study monitor.

## Existing Foundation

- `backend/app/routers/generate.py` creates generated questions and saves them
  as `Question`, `QuestionVersion`, `QuestionAnnotation`, and `QuestionOption`
  rows.
- Generated questions are saved as `practice_status = "draft"`, which keeps
  them out of student retrieval until admin approval.
- Generated questions run official-overlap detection and are blocked from
  approval if overlap remains unresolved.
- `GenerationRequest` and `GenerationCompareRequest` support grammar and
  reading targets.
- Generation prompts load both:
  - `rules_agent_dsat_grammar_ingestion_generation_v7.md`
  - `rules_agent_dsat_reading_v2.md`
- `source_question_ids` can load stored official questions, annotations, and
  options into the generation prompt as foundational source examples.
- `backend/app/models/db.py::LlmEvaluation` already exists with basic scoring
  fields, but it is not yet a full review-swarm result model.
- Student retrieval exists at `GET /api/questions`, currently with simple
  active-question filtering.
- Admin review already has approve/reject controls for questions. Current
  rejection behavior retires a question and clears some metadata; this must be
  changed before review-swarm data is attached to generated candidates.

## Target Flow

```text
self-study agent or admin request
  -> generation batch created
  -> N single-question generation jobs queued
  -> each generated question is saved as draft
  -> official overlap detection runs
  -> OpenAI / Claude / DeepSeek review swarm scores realism and quality
  -> deterministic consensus gate produces review verdict
  -> admin dashboard filters and visually reviews candidates
  -> approved questions become active
  -> student retrieval API serves active approved questions
```

## Design Decisions

- Generation, review, and release are separate stages. A generated question is
  never automatically student-visible just because generation succeeded.
- Batch generation should create one saved question per job, not one large LLM
  response containing many questions. This preserves traceability, retries,
  overlap checks, review results, and admin rejection at the question level.
- Generated questions should be saved before review so every review result has
  a durable `question_id`.
- Official questions are the foundational source examples for generation.
  Generated output must calibrate against them without copying passages, stems,
  options, or explanations.
- Difficulty is a request target and a review criterion. It should not be
  trusted solely because the generator was asked for `easy`, `medium`, or
  `hard`.
- The self-study agent may request generation, but the first production-safe
  release policy should be `admin_review_required`.
- The LLM review swarm should be advisory plus gated by deterministic consensus;
  admin remains the final authority for initial rollout.
- Reviewer disagreement is itself a signal. Questions with high disagreement
  should be prioritized for human review rather than auto-approved.

## Core Concepts

### Generation Batch

A generation batch is one request for multiple targeted questions. It records
the original intent and aggregate status.

Recommended fields:

- `id`
- `requested_count`
- `created_count`
- `accepted_count`
- `rejected_count`
- `failed_count`
- `requested_by`: `admin`, `self_study_agent`, or `system`
- `student_id`, nullable
- `request_jsonb`
- `release_policy`: initially `admin_review_required`
- `status`: `pending`, `generating`, `reviewing`, `admin_review_ready`,
  `completed`, `failed`, `cancelled`
- `created_at`
- `updated_at`

### Generated Candidate

Each generated question remains a normal `Question` row with
`content_origin = "generated"` and `practice_status = "draft"`. It should also
link to its batch.

Recommended fields or relation:

- `generation_batch_id` on `QuestionJob`
- `generation_request_jsonb` on each `QuestionJob`; `Question.generation_source_set`
  remains the saved-candidate lineage snapshot after a question exists
- `source_question_ids`
- generator `provider_name` and `model_name`
- prompt and rules versions

### Review Swarm Result

Each reviewer model writes an independent row in the dedicated
`llm_review_results` table. Existing `LlmEvaluation` remains available for its
current annotation-quality/manual evaluation role, but generated-question review
swarm data should not be squeezed into that table.

Recommended fields:

- `id`
- `question_id`
- `job_id`
- `generation_batch_id`
- `review_run_id`
- `provider_name`: `openai`, `anthropic`, `ollama`
- `model_name`: for example `gpt-*`, Claude, `deepseek-v4-pro:cloud`
- `task_type`: `generation_realism_review`
- `rubric_version`
- `rules_versions_jsonb`
- `scores_jsonb`
- `verdict`: `accept`, `needs_human_review`, `reject`
- `review_notes`
- `raw_response_jsonb`
- `latency_ms`
- `token_usage_jsonb`
- `review_status`: `ok`, `transient_failed`, or `permanent_failed`
- `error_message`
- `created_at`

Recommended score keys:

```json
{
  "realism_score": 8.7,
  "sat_fidelity_score": 8.4,
  "difficulty_match_score": 7.9,
  "distractor_quality_score": 8.1,
  "taxonomy_match_score": 9.0,
  "explanation_quality_score": 8.2,
  "copy_risk_score": 1.1
}
```

### Consensus Verdict

The consensus gate converts review-swarm results into one deterministic
admin-facing decision.

Recommended fields:

- `question_id`
- `generation_batch_id`
- `review_run_id`
- `reviewer_count`
- `average_realism`
- `average_sat_fidelity`
- `average_difficulty_match`
- `average_distractor_quality`
- `average_taxonomy_match`
- `max_copy_risk`
- `accept_votes`
- `needs_review_votes`
- `reject_votes`
- `reviewer_disagreement`
- `consensus_verdict`: `admin_review_ready`, `reject_recommended`,
  `regenerate_recommended`, `blocked_overlap`, `insufficient_reviews`
- `reasons_jsonb`

## Phase 0: Current-State Alignment

**Goal:** Make sure the current generation path has a clear baseline before
adding batch and swarm behavior, and land the destructive-rejection fix that
later phases depend on.

- [x] Confirm generated questions are always saved before review.
  (`backend/app/routers/generate.py::_run_generate_pipeline` saves
  `Question`/`QuestionVersion`/`QuestionAnnotation`/`QuestionOption`
  rows before any review hooks fire.)
- [x] Confirm generated questions stay `draft` by default.
  (`generate.py:275`, `practice_status="draft"`.)
- [x] Confirm admin approval is required before generated questions appear
  in student retrieval. (`backend/app/routers/questions.py` filters by
  `practice_status='active'`; only `admin_required` flips drafts to
  active.)
- [x] Confirm `source_question_ids` only loads stored official questions.
  (`generate.py::_load_official_source_examples` filters
  `content_origin='official'`.)
- [x] Confirm generation prompts include both grammar and reading rule
  markdowns. (`backend/app/prompts/generate_prompt.py` loads
  `rules_agent_dsat_grammar_ingestion_generation_v7.md` and
  `rules_agent_dsat_reading_v2.md`.)
- [x] Add or update a short architecture note explaining:
  - official questions are the generation foundation
  - generated items are candidates until reviewed
  - review swarm output is not the same as admin approval
  (`GENERATION_ARCHITECTURE.md` at repo root)
- [x] **`practice_status_enum` migration:** add `"rejected"` as a fourth
  value alongside `draft`, `active`, `retired`. Updated
  `vocabulary/master.json` and regenerated
  `backend/app/models/ontology.py` via `scripts/gen_vocab.py --generate`.
  Migration `020_add_rejected_status_and_reason_columns.py` ships the
  enum extension with `autocommit_block()` so the new value is visible
  in-migration. Verified live: `{draft, active, retired, rejected}`.
- [x] **New columns on `questions`:** `rejection_reason` (Text, nullable),
  `rejected_at` (DateTime tz, nullable), `rejected_by_admin_token`
  (String 128, nullable). Single migration `020_*` alongside the enum
  bump.
- [x] **Rewrite `reject_question`** (`backend/app/routers/admin.py`) as
  metadata-only. Sets `practice_status='rejected'`, populates the three
  reason columns, preserves all annotations/options/relations/evaluations
  and `latest_annotation_id`. `RejectQuestionRequest` body accepts an
  optional `reason`. Regression test
  `test_admin_reject_is_non_destructive` asserts execute_calls is empty
  during rejection. Override-row writing deferred to Phase 6 when
  `reviewer_admin_overrides` exists.
- [x] **Expand `_SOURCE_SET_OPERATIONAL_KEYS`** in
  `backend/app/routers/generate.py` to the locked 10-key set; deduplicated
  the constant (no more private copy in `_generation_profile_payload`).
  Regression test
  `test_source_set_operational_keys_filter_strips_all_operational`
  snapshots the set and asserts the lineage-survives invariant.

**Exit criteria:** The baseline behavior is documented and covered by targeted
tests. Rejection is non-destructive. The `rejected` enum and reason columns
exist. `_SOURCE_SET_OPERATIONAL_KEYS` matches the locked filter.

## Phase 1: Batch Generation Contract

**Goal:** Let admins request variable quantities of generated questions while
laying the batch identity/audit fields that the Phase 8 self-study endpoint
will reuse.

- [x] Add a `GenerationBatchRequest` model with:
  - `requested_count`, bounded by config
  - grammar target fields
  - reading target fields
  - `difficulty_overall`
  - `source_question_ids`
  - `release_policy`
  - `provider_name`, optional
  - `model_name`, optional
  - Requester identity is derived by the endpoint and stored on the batch:
    `requested_by`, `student_id`, and `requested_by_user_token`
- [x] Add validation rules:
  - request must contain a complete grammar target or complete reading target
  - `requested_count` must be within admin-configured limits
  - `POST /generate/batches` is admin-only per the locked auth table; self-study
    request validation and `user_token` resolution are deferred to
    `POST /api/study/generation-requests` in Phase 8
  - admin-created batches store `requested_by='admin'`, `student_id=null`, and
    `requested_by_user_token=null` in both columns and frozen request payloads
  - `release_policy` defaults to `admin_review_required` and is limited to the
    locked values: `admin_review_required`, `auto_release_on_accept`, `dry_run`
- [x] Add a `GenerationBatch` persistence model and migration.
  (`backend/app/models/db.py::GenerationBatch`, migration `021_phase1_generation_batches.py`)
- [x] Add `generation_batch_id` linkage for generated jobs. Saved questions
  reach their batch through `QuestionJob.question_id -> Question`.
- [x] Add durable `QuestionJob.generation_request_jsonb` storage so failed
  jobs can be retried without depending on a saved `Question` row. The snapshot
  is populated at job creation with the per-job source IDs, provider/model,
  seed, temperature, retry attempt, and derived requester identity.
- [x] Add enum/schema migration work required by this feature before any code
  writes the new values:
  - `job_status_enum`: `failed_transient`, `failed_permanent`, `retrying`
  - `practice_status_enum`: `rejected` — **already landed in Phase 0**;
    listed here for cross-reference only
  - `overlap_status_enum`: no new value planned; `none` remains the only clean
    state, and admin-cleared overlaps return to `none`
  - generated ontology constants and migration enum values must stay in sync
- [x] Add `questions.is_canonical_source` for the canonical official-source
  fallback pool.
- [x] Add config:
  - `GENERATION_MAX_BATCH_SIZE`
  - `GENERATION_DEFAULT_BATCH_SIZE`
  - `GENERATION_MAX_PENDING_BATCHES`
- [x] Add endpoint:
  - `POST /generate/batches`
  - `GET /generate/batches/{batch_id}`
  - `GET /generate/batches/{batch_id}/questions`
- [x] **Idempotency support on `POST /generate/batches`:**
  - Add `generation_batch_idempotency_keys` table (`idempotency_key`,
    `requested_by`, `generation_batch_id`, `expires_at`, `created_at`)
    with unique constraint on `(idempotency_key, requested_by)`.
  - Read `Idempotency-Key` header; if present, delete expired rows for
    that key first, then look up live mapping. Hit returns the original
    batch response; miss creates a new batch and inserts a key row with
    `expires_at = now + 24h`. Empty/missing header opts out.
  - `Idempotency-Key` is NOT copied into `GenerationBatch.request_jsonb`.
- [x] Ensure existing `POST /generate/questions` remains backward-compatible for
  one-off admin generation.

**Exit criteria:** An admin caller can request N targeted questions and receive
a batch ID with N queued generation jobs. Repeated calls with the same
`Idempotency-Key` return the original batch.

## Phase 2: Quantity-Aware Generation Runner

**Goal:** Execute batches safely while preserving one-question traceability.

- [x] Create one `QuestionJob` per requested generated question.
  (`backend/app/routers/generate.py` — Phase 1 already queued; Phase 2 wires runner)
- [x] Copy the batch request into each job's durable request metadata before
  the runner starts. (`QuestionJob.generation_request_jsonb`)
- [x] Preserve one LLM generation call per question. (`_run_generate_pipeline`)
- [x] Save each generated candidate as:
  - `Question`
  - `QuestionVersion`
  - `QuestionAnnotation`
  - `QuestionOption`
  - YAML archive mirror
  - A model output becomes a saved candidate only after generation,
    annotation, and blocking validation pass. Malformed JSON, refusals,
    ontology mismatch, and blocking validation failures stay on
    `QuestionJob` as terminal `failed_permanent` audit records and do not
    create partial `Question` rows.
- [x] Run official overlap detection per saved question. (`detect_overlaps` →
  `persist_overlap_relations` in `_run_generate_pipeline`)
- [x] Track batch counters (atomic SQL UPDATE per terminal job status):
  - created (`created_count` incremented in `_run_generate_pipeline` after persist)
  - failed (`failed_count` — `failed_permanent` + `failed_transient`)
  - needs review (`needs_review_count`)
  - approved (`accepted_count`)
  (`_update_batch_counters`, `_finalize_batch_status`)
- [x] Add retry behavior for failed individual generation jobs without rerunning
  the entire batch. (`POST /generate/batches/{batch_id}/retry-failed`; respects
  `GENERATION_JOB_MAX_RETRIES=3`; only jobs without a saved `Question` row are
  requeued, preventing duplicate saved candidates after post-persist failures)
- [x] Failure classification: transient (network/provider) → `failed_transient`;
  permanent (JSON parse, validation) → `failed_permanent`. (`_is_transient_error`)
- [x] Ensure every runner failure path settles to a terminal status before
  counters/finalization run: setup/source loading, prompt build, generation,
  annotation, validation, persistence, overlap detection, and YAML export.
- [x] Keep job pipeline success separate from admin release:
  - job status means the generation/review pipeline state
  - `Question.practice_status` means student visibility and admin decision
  - a generated job must not imply student approval just because the candidate
    saved successfully
  - current/legacy `QuestionJob.status = "approved"` must be treated only as
    "pipeline accepted or candidate saved"; dashboard/API copy must not label it
    as admin approval
- [x] Idempotency key support already landed in Phase 1; this phase relies
  on it (cross-reference only).

**Exit criteria:** Batch generation can partially succeed. Every valid generated
candidate has an individual status, saved payload, and audit trail; every
invalid generation attempt has a terminal `QuestionJob` status with retained
payload/error evidence.

Files: `backend/app/routers/generate.py` (`_is_transient_error`, `_batch_counter_field`,
`_update_batch_counters`, `_run_batch_job`, `_finalize_batch_status`, `_run_batch_pipeline`,
`retry_failed_batch_jobs`), `backend/app/config.py` (`generation_job_max_retries`),
`backend/tests/test_generate_runner.py` (30 tests — all pass).

## Phase 3: Review Swarm Rubric

**Goal:** Define a stable multi-model review contract for generated-question
quality.

- [x] Create `rules_agent_dsat_review_v1.md` at repo root holding scoring
  dimensions, anchor bands per numeric score, and the strict JSON schema
  reviewers must return.
- [x] Rubric must score:
  - DSAT realism → `realism_score`
  - SAT style fidelity → `sat_fidelity_score`
  - target taxonomy match → `taxonomy_match_score`
  - difficulty match → `difficulty_match_score`
  - distractor quality + correct-answer defensibility → `distractor_quality_score`
  - explanation quality + student-facing ambiguity risk → `explanation_quality_score`
  - copy/near-duplicate risk → `copy_risk_score` (inverted)
  - grammar/reading rule compliance → folded into `taxonomy_match_score`
- [x] Rubric must return strict JSON.
- [x] Rubric must include `verdict`:
  - `accept`
  - `needs_human_review`
  - `reject`
- [x] Rubric must require short reasons for every score below threshold.
- [x] **Create `backend/app/prompts/review_prompt.py`** loader that composes:
  - `rules_agent_dsat_review_v1.md` (rubric).
  - `rules_agent_dsat_grammar_ingestion_generation_v7.md` **always**,
    regardless of question domain (prose-style canon for all DSAT
    writing).
  - `rules_agent_dsat_reading_v2.md` only when the candidate is a reading
    question (additive on top of grammar v7).
  - Question payload, options, annotation, source examples, overlap
    status, original request.
- [x] **Create `llm_review_results` table** (per Locked Decisions data
  model). Includes `rubric_version` (filename version string) and
  `rules_versions_jsonb` snapshot of `{grammar, reading}` versions in
  effect at review time, so each row stands alone for audit.
- [x] **Create `review_runs` table** (per Locked Decisions review run
  grouping): `id`, `question_id`, `generation_batch_id` (nullable),
  `triggered_by`, `triggered_by_admin_token` (nullable),
  `rubric_version`, `rules_versions_jsonb`, `status` (`running` |
  `complete` | `partial` | `failed`), `started_at`, `completed_at`.
- [x] Add tests for parsing valid review JSON and rejecting malformed review
  output. (`backend/tests/test_review_parser.py`: 25 tests; `backend/tests/test_review_prompt.py`: 16 tests)
- [x] Version the rubric with `rubric_version` (filename = version
  string). Write-once: new version = new file; never edit a published
  version after it has been used for real reviews.

**Files:** `rules_agent_dsat_review_v1.md`, `backend/app/prompts/review_prompt.py`,
`backend/app/review/parser.py`, `backend/app/models/db.py` (ReviewRun, LlmReviewResult),
`backend/app/models/ontology.py` (review enums), `backend/app/config.py` (thresholds),
`backend/migrations/versions/022_phase3_review_tables.py`,
`backend/tests/test_review_parser.py`, `backend/tests/test_review_prompt.py`

**Exit criteria:** One generated question can be reviewed by one model and
produce a durable, structured quality review with rubric + grammar canon
loaded and a `review_run_id` linking reviewer rows to their run.

## Phase 4: Multi-Model Review Runner

**Goal:** Run OpenAI, Claude, and DeepSeek-style reviewers against saved
generated candidates.

- [x] Add review provider config:
  - `GENERATION_REVIEW_PROVIDERS=openai,anthropic,ollama`
  - `GENERATION_REVIEW_OPENAI_MODEL`
  - `GENERATION_REVIEW_ANTHROPIC_MODEL`
  - `GENERATION_REVIEW_OLLAMA_MODEL=deepseek-v4-pro:cloud`
  - `GENERATION_REVIEW_MAX_CONCURRENT`
  - `GENERATION_REVIEW_MAX_RETRIES`
- [x] Add a review runner that loads:
  - saved generated question
  - options
  - annotation
  - generation request
  - source official examples
  - overlap status
- [x] Run reviewers concurrently with a semaphore.
- [x] Save one review result per provider/model.
- [x] Treat review failure as a review status, not as deletion of the generated
  question.
- [x] Add endpoint:
  - `POST /admin/questions/{question_id}/review-swarm`
  - `GET /admin/questions/{question_id}/review-runs`
  - `POST /generate/batches/{batch_id}/review-swarm`
- [x] Add tests for:
  - all reviewers succeed
  - one reviewer fails
  - malformed reviewer JSON
  - duplicate review prevention (rerun creates new review_run_id)
  - batch review swarm skips already-reviewed questions
  - empty batch returns empty results
  - nonexistent batch raises ValueError

**Files:** `backend/app/review/runner.py`, `backend/app/routers/admin.py` (review-swarm and review-runs endpoints), `backend/app/routers/generate.py` (batch review-swarm endpoint), `backend/tests/test_review_runner.py` (18 tests)

**Exit criteria:** A saved generated question can receive independent reviews
from OpenAI, Claude, and DeepSeek/DeepSeek-via-Ollama without blocking the
question's saved record.

## Phase 5: Consensus Gate

**Goal:** Turn review-swarm output into deterministic admin-facing status.

- [x] Add consensus calculation after review results are saved.
- [x] Default policy:
  - reject recommended if any model reports high copy risk
  - reject recommended if average realism is below threshold
  - needs human review if reviewer disagreement is high
  - admin review ready if all core averages clear threshold
  - blocked if official overlap status is unresolved
- [x] Store consensus output in the dedicated `consensus_verdicts` table.
- [x] Add config thresholds:
  - `GENERATION_MIN_REALISM_SCORE`
  - `GENERATION_MIN_SAT_FIDELITY_SCORE`
  - `GENERATION_MIN_DISTRACTOR_QUALITY_SCORE`
  - `GENERATION_MIN_TAXONOMY_MATCH_SCORE`
  - `GENERATION_MAX_COPY_RISK_SCORE`
  - `GENERATION_MAX_REVIEWER_DISAGREEMENT`
- [x] Add tests for each verdict path.
- [x] Do not activate generated questions from consensus alone in the initial
  build.

**Files:** `backend/app/review/consensus.py`, `backend/app/models/db.py` (ConsensusVerdict model), `backend/app/review/runner.py` (wired consensus after review), `backend/migrations/versions/023_phase5_consensus_verdicts.py`, `backend/tests/test_consensus.py` (17 tests)

**Exit criteria:** Every reviewed generated question has a consensus verdict
that the admin dashboard can filter and sort.

## Phase 6: Admin Dashboard Review Queue

**Goal:** Let admins visually inspect, filter, approve, reject, and regenerate
generated candidates efficiently.

- [x] Add dashboard filters:
  - generation batch
  - requested by admin vs self-study agent
  - student/profile origin
  - domain: grammar or reading
  - grammar role/focus
  - reading skill family/focus
  - difficulty
  - generator provider/model
  - reviewer provider/model
  - average realism score
  - consensus verdict
  - reviewer disagreement
  - overlap status
  - creation date
- [x] Candidate card must show:
  - passage or stimulus
  - question stem
  - answer options
  - correct answer
  - explanation
  - requested target
  - actual annotation
  - generation source official questions
  - overlap warning
  - review-swarm score table
  - reviewer notes and reject reasons
- [x] Actions:
  - approve
  - reject
  - edit
  - request re-review
  - regenerate from same spec
  - compare with official source examples
- [x] Ensure rejection does not delete candidate evidence. It should mark
  `practice_status = "rejected"` and preserve annotations, options, review
  results, consensus rows, overlap relations, and generation lineage for audit.
- [x] Capture reviewer/admin agreement or disagreement implicitly during
  approve/reject; do not add a separate "reviewer was wrong" action.
- [x] **`reviewer_admin_overrides` plumbing:** approve and reject handlers
  generate one `admin_decision_id` (uuid4) per click and reuse it across
  the N rows written — one per reviewer in the latest completed review
  run for that question. Each row records `reviewer_verdict`,
  `admin_verdict`, and `override_direction` (`reviewer_correct` |
  `reviewer_too_harsh` | `reviewer_too_lenient`).
- [x] Add list endpoints optimized for dashboard filtering and pagination.

**Status 2026-05-20:** Complete. Implemented `GET /admin/generated-questions`
and detail/action endpoints, `/dashboard/review` filtering and review cards,
append-only `reviewer_admin_overrides` capture on approve/reject, regenerate
from same spec, and pagination support. Verified with `uv run alembic upgrade
head` and the full backend suite (`622 passed, 2 skipped`).

**Exit criteria:** Admin can filter to the riskiest generated questions first,
visually inspect them, and reject or approve without leaving the dashboard.

## Phase 7: Student Retrieval API Expansion

**Goal:** Serve approved questions to students with richer targeting and
inventory awareness.

- [x] Extend `GET /api/questions` filters:
  - `domain`
  - `difficulty`
  - `grammar_role_key`
  - `grammar_focus_key`
  - `reading_skill_family_key`
  - `reading_focus_key`
  - `stimulus_mode_key`
  - `origin=official|generated|mixed` (default `mixed`)
  - `exclude_seen` (boolean; default `true` for student tokens, `false`
    for admin tokens — derived from the `admin_or_student_required`
    dependency, not from a request body field)
  - `limit`
- [x] Introduce the `admin_or_student_required` dependency in
  `backend/app/auth.py` returning `(scope, key)`; this endpoint and the
  Phase 8 endpoints use it.
- [x] Add result metadata:
  - active inventory count for the requested target
  - whether generated questions were included
  - whether inventory is below threshold
- [x] Ensure student-facing payload never exposes answer key.
- [x] Ensure only `practice_status = "active"` questions are served.
- [x] Add tests for grammar filters, reading filters, difficulty filters,
  exclude-seen behavior, and active-only enforcement.

**Status 2026-05-20:** Complete. Added `admin_or_student_required` auth dependency,
rewrote `GET /api/questions` with full filter set, added `StudentQuestionsListResponse`
with `inventory` metadata block (matching_target_total, matching_unseen, served,
includes_generated, below_threshold, threshold), implemented exclude_seen resurface
logic (correct=never, wrong=resurface after 30 days), added `inventory_sufficient_threshold`
and `self_study_resurface_days` config. 30 new tests in `test_student_retrieval.py`.
Full suite: 652 passed, 2 skipped.

**Exit criteria:** A student or study agent can retrieve targeted active
questions across grammar and reading without seeing draft candidates.

## Phase 8: Self-Study Agent Request Layer

**Goal:** Let a monitor identify weak skills and request generation only when
existing inventory is insufficient.

- [x] Define a student weakness profile:
  - recent accuracy
  - missed grammar focus keys
  - missed syntactic traps
  - missed reading focus keys
  - difficulty bands where performance drops
  - recency weighting
- [x] Add endpoint:
  - `POST /api/study/recommendations`
  - `POST /api/study/generation-requests`
  - `GET /api/study/generation-requests/{batch_id}` (batch status)
- [x] Self-study agent flow:
  - inspect student progress
  - identify target focus and difficulty
  - check active inventory first
  - retrieve existing questions if enough inventory exists
  - create generation batch only when inventory is low
  - return batch status and expected review path
- [x] Add caps:
  - max generated per student per day
  - max pending generated questions per target
  - max pending batches per student
  - cooldown after poor batch quality
- [x] Generated questions from self-study agent requests remain draft until
  approved by admin. Self-study requests are forced to
  `admin_review_required` even if the caller asks for a different policy.

**Exit criteria:** The self-study agent can request exactly the type of
questions a student needs without bypassing quality review.

## Phase 9: Generation Quality Analytics

**Goal:** Measure which generation and review models actually produce useful
student-ready questions.

- [x] Add dashboard metrics:
  - generated count
  - reviewed count
  - approved count
  - rejected count
  - acceptance rate by generator model
  - rejection reason distribution
  - average realism by generator model
  - average reviewer disagreement
  - copy-risk failures
  - admin override rate by reviewer model
- [x] Add batch analytics:
  - requested count vs created count
  - created count vs approved count
  - average review latency
  - cost and token usage by provider
- [x] Add quality trend views over time (day/week granularity).
- [x] Add export endpoint for offline analysis.

**Status 2026-05-20:** Complete. Added four endpoints under `GET /admin/analytics/*`:
`generation`, `review`, `batches`, `trends`, and `export`. All backed by efficient
aggregate SQL queries with a configurable `days` lookback window. 28 tests in
`test_analytics.py`. Full suite: 719 passed, 2 skipped.

**Exit criteria:** Admin can see which generator/reviewer combinations produce
the best accepted questions and where bad generations are coming from.

## Phase 10: Controlled Auto-Release Policy

**Goal:** Only after enough review data exists, optionally allow narrowly scoped
auto-release.

- [ ] Define policy flags:
  - `GENERATION_AUTO_RELEASE_ENABLED=false`
  - `GENERATION_AUTO_RELEASE_MIN_REVIEWS=3`
  - `GENERATION_AUTO_RELEASE_MIN_ACCEPT_RATE`
  - `GENERATION_AUTO_RELEASE_ALLOWED_TARGETS`
- [ ] Auto-release requires:
  - no unresolved overlap
  - all review thresholds cleared
  - low reviewer disagreement
  - no copy-risk warnings
  - generator model with proven acceptance history
- [ ] Keep an audit trail explaining every auto-release.
- [ ] Add admin kill switch to disable auto-release immediately.

**Exit criteria:** Auto-release is possible but opt-in, thresholded, auditable,
and easy to disable.

## API Surface Summary

Planned admin/generation endpoints:

- `POST /generate/batches`
- `GET /generate/batches/{batch_id}`
- `GET /generate/batches/{batch_id}/questions`
- `POST /generate/batches/{batch_id}/retry-failed`
- `POST /generate/batches/{batch_id}/review-swarm`
- `POST /admin/questions/{question_id}/review-swarm`
- `GET /admin/generated-questions`
- `GET /admin/generated-questions/{question_id}`
- `POST /admin/generated-questions/{question_id}/approve`
- `POST /admin/generated-questions/{question_id}/reject`
- `POST /admin/generated-questions/{question_id}/regenerate`

Planned student/study endpoints:

- `GET /api/questions`
- `POST /api/study/recommendations`
- `POST /api/study/generation-requests`
- `GET /api/study/generation-requests/{batch_id}`

## Testing Strategy

- Unit tests for request validation.
- Unit tests for review JSON parsing and rubric validation.
- Unit tests for consensus verdict logic.
- Router tests for new admin, generation, and student endpoints.
- Integration tests for:
  - admin batch generation
  - self-study-agent batch generation
  - partial generation failure
  - review swarm with one failed reviewer
  - admin approve/reject
  - student retrieval active-only behavior
- Regression tests that generated drafts never appear in student retrieval.
- Regression tests that official overlap blocks approval.
- Regression tests that rejected generated questions remain auditable.
- Regression test for the request payload identity invariant:
  `Question.generation_source_set == {k: v for k, v in
  QuestionJob.generation_request_jsonb.items() if k not in
  _SOURCE_SET_OPERATIONAL_KEYS}`. Failure indicates a leaked operational
  key or a missing strip step.
- Regression test that `reject_question` is non-destructive: rejecting a
  question with annotations, options, evaluations, relations, and review
  results preserves all of them and only flips `practice_status` plus
  populates the reason columns.

## Operational Safeguards

- Batch size limits.
- Global generation concurrency limit.
- Review-swarm concurrency limit.
- Provider-level retry and timeout settings.
- Daily generation caps for self-study requests.
- Duplicate request idempotency keys.
- Per-target pending queue limits.
- Admin kill switch for auto-release.
- Review cost and token usage logging.

## Open Decisions

Resolved by locked decisions below:

- Use a dedicated `llm_review_results` table for generation review; keep
  `LlmEvaluation` for its existing annotation-quality/manual evaluation role.
- Put `generation_batch_id` on `question_jobs`; questions reach their batch
  through the generating job.

Still open:

- Whether self-study agent requests should be allowed to use non-official
  generated questions as future source examples. Initial recommendation: no.
- Whether approved generated questions can ever become source examples.
  Initial recommendation: only after they have enough student performance data
  and admin endorsement.
- Whether auto-release is acceptable for any target in alpha. Initial
  recommendation: keep disabled until quality analytics prove reliability.

## Recommended Build Order

0. Phase 0 alignment: enum + reason-column migration, non-destructive
   `reject_question`, expanded `_SOURCE_SET_OPERATIONAL_KEYS`. Prerequisite
   for every subsequent phase.
1. Generation batch model and request validation, including idempotency
   support and `generation_batch_idempotency_keys` table.
2. Quantity-aware generation runner with saved candidates.
3. Review rubric, `review_runs` + `llm_review_results` tables, and
   one-model review runner.
4. Multi-model review swarm.
   - **Run the 50-question calibration batch with placeholder thresholds
     before Phase 5 storage lands**; lock final threshold values informed
     by results. Then build Phase 5.
5. Consensus verdict storage and `reviewer_admin_overrides` table.
6. Admin dashboard filtering and visual review cards (implicit override
   capture on approve/reject).
7. Student retrieval API expansion + `admin_or_student_required`
   dependency.
8. Self-study agent request layer.
9. Quality analytics.
10. Optional controlled auto-release.

## Locked Decisions

Resolved via grilling session 2026-05-19. These are load-bearing
architectural choices that supersede ambiguous prose elsewhere in this
document. Smaller mechanical items (Phase 9 dashboard metric catalog,
cost/token alert thresholds) and explicitly deferred items (Phase 10
auto-release gating until calibration data exists) remain open. Auth
scopes are locked below.

### Data model

- New table `generation_batches`: `id`, `request_jsonb`, `requested_by`,
  `student_id`, `requested_by_user_token`, `release_policy`,
  `regenerate_source_batch_id`, `status`, denormalized counters
  (`created_count`, `accepted_count`, `rejected_count`, `failed_count`,
  `needs_review_count`), `created_at`, `updated_at`. Indexes on
  `status`, `student_id`, `requested_by_user_token`,
  `(requested_by, created_at)`.
- New table `generation_batch_idempotency_keys`: `id`, `idempotency_key`,
  `requested_by`, `generation_batch_id`, `expires_at`, `created_at`.
  Unique constraint on `(idempotency_key, requested_by)` is acceptable only
  because expired rows are deleted before lookup/create; otherwise the 24h TTL
  cannot work. The idempotency key comes from the `Idempotency-Key` header and
  is not copied into `GenerationBatch.request_jsonb`.
- New table `llm_review_results` replaces `LlmEvaluation` for generation
  review (annotation-quality use of `LlmEvaluation` stays). Columns:
  `question_id`, `job_id`, `generation_batch_id`, `review_run_id`,
  `provider_name`, `model_name`, `task_type` default
  `generation_realism_review`, `rubric_version`, `rules_versions_jsonb`,
  `scores_jsonb`, `verdict`, `review_notes`, `raw_response_jsonb`,
  `latency_ms`, `token_usage_jsonb`, `review_status` (`ok` |
  `transient_failed` | `permanent_failed`), `error_message`, `created_at`.
- New table `consensus_verdicts`. Append-only rows keyed by review run;
  latest `(question_id, rubric_version)` row by `created_at` wins. Stores
  `review_run_id`, `reviewer_count`, averages per dimension,
  `max_copy_risk`, `reviewer_disagreement_stddev`, per-verdict vote counts,
  `consensus_verdict` enum, `high_disagreement_flag`, `reasons_jsonb`, plus
  snapshot of `rubric_version` and `rules_versions_jsonb` for standalone audit.
- New table `reviewer_admin_overrides`. Append-only rows written implicitly
  when admin approves or rejects. Columns: `id`, `admin_decision_id`,
  `question_id`, `llm_review_result_id`, `reviewer_verdict`,
  `admin_verdict`, `override_direction` (`reviewer_correct` |
  `reviewer_too_harsh` | `reviewer_too_lenient`), `admin_token`,
  `admin_notes`, `created_at`. All rows written by one approve/reject click
  share `admin_decision_id`. Unique constraint:
  `(admin_decision_id, llm_review_result_id)`.
- Add `generation_batch_id` FK on `question_jobs` (indexed, nullable for
  legacy/non-batch jobs), plus durable `generation_request_jsonb`,
  `retry_count`, and optional `last_retry_at`. Questions reach their batch
  through the job, not via a column on `questions`.
- Add `is_canonical_source` boolean on `questions` for the official-source
  fallback pool. Default false.
- `UserProgress` migration: add `missed_reading_focus_key`,
  `missed_reading_skill_family_key`, `question_domain`,
  `question_difficulty` so the weakness profile can compute without
  joining annotations historically.

### Generation flow

- One LLM call per generated question. Prompt caching on shared system
  prompt across calls. Separate concurrency caps for generation and
  review.
- Idempotency uses a client-supplied `Idempotency-Key` header.
  Server stores `(idempotency_key, requested_by) -> batch_id` in
  `generation_batch_idempotency_keys` with `expires_at = created_at + 24h`.
  Repeat before expiry returns the original batch. Empty/missing header opts
  out. Expired key rows are deleted before lookup/create so the same key can
  be reused after the TTL.
- Per-job retry policy:
  - Transient failures (HTTP 429, 5xx, network timeout, provider rate
    limit, Ollama "model loading") auto-retry inside the runner up to
    2 attempts with exponential backoff.
  - Permanent failures (malformed JSON after repair attempt, model
    refusal, ontology mismatch, validation failure) do not auto-retry
    and surface via `POST /generate/batches/{id}/retry-failed`.
  - Distinct job statuses `failed_transient` and `failed_permanent` so
    the dashboard can show meaningful failure breakdown. This requires the
    Phase 1 enum migration before runner code writes these values.
  - Row-level `retrying` status guards re-retry collisions; no
    idempotency key needed on the retry endpoint.
  - `GENERATION_JOB_MAX_RETRIES = 3` admin-initiated retries on top of
    auto-retries. After cap the job is locked at `failed_permanent` and
    admin must regenerate-from-spec instead.
- Source-example selection when caller omits `source_question_ids`:
  - Filter `content_origin='official'` AND `practice_status='active'`.
  - Hard filter by request annotation keys (`grammar_role_key`,
    `grammar_focus_key`, or `reading_skill_family_key`,
    `reading_focus_key`, plus `stimulus_mode_key`).
  - Soft filter by matching `difficulty_overall` band.
  - Diversify across `source_exam_code` (avoid two examples from the
    same test when possible).
  - Rotation: dedupe against the last 50 generations' source IDs by
    walking `Question.generation_source_set` jsonb. No new schema.
  - If empty after broadening: fall back to a curated
    `is_canonical_source=true` pool (boolean column added to
    `questions`, hand-flagged ~5 grammar + 5 reading canonical
    questions).
  - Within a batch: shuffle and assign different subsets per job so the
    N parallel calls do not all see identical examples.
- Source-example counts per call: **3 grammar, 2 reading**. Reading
  passages dominate tokens.
- Caller-passed `source_question_ids` use **exactly** those IDs, no
  auto-augment. Validate at request time: 400 on domain mismatch.

### Review swarm

- Auto-run on save. Skip if `official_overlap_status != 'none'`.
  Manual `POST .../review-swarm` endpoints exist for re-runs after
  rubric or canon bumps, not as the primary path. `skip_review` debug
  flag available on batch request.
- Reviewer composition rules:
  - Exclude the generator's **provider** from the swarm
    (self-grading bias). This is the conservative rule even when the
    same provider hosts unrelated model families (e.g., Ollama running
    `qwen3-vl` as generator and `deepseek-v4-pro` as reviewer is still
    blocked — relax to model-level exclusion only after calibration
    shows the conservative rule is unnecessary).
  - One model per provider; identical rubric makes additional
    same-provider models low value.
  - Configured reviewer providers: OpenAI, Anthropic, Ollama
    (`deepseek-v4-pro:cloud`).
  - Failover: retry each reviewer up to 2 times with backoff, then
    record `review_status='transient_failed'` for that reviewer.
    Consensus runs on whatever reviewers succeeded. If <2 succeed,
    consensus verdict = `insufficient_reviews` and the batch flips to
    `admin_review_ready` with a flag; admin may re-run later.
- Rubric prompt composition:
  - `rules_agent_dsat_review_v1.md` at repo root holds scoring
    dimensions, anchor bands per numeric score, and the strict JSON
    schema reviewers must return.
  - `rules_agent_dsat_grammar_ingestion_generation_v7.md` is loaded as
    canon **always**, regardless of question domain. It is the prose
    style canon for all DSAT-style writing.
  - `rules_agent_dsat_reading_v2.md` is loaded only when the candidate
    is a reading question (additive on top of grammar v7).
  - Python loader: `backend/app/prompts/review_prompt.py` composes the
    final message list and injects the question payload, options,
    annotation, source examples, overlap status, and the original
    request.
- Rubric versioning:
  - Filename version is `rubric_version` (e.g. `v1`, `v1.1`, `v2`).
  - `rules_versions_jsonb` on `llm_review_results` and
    `consensus_verdicts` snapshots `{grammar: vN, reading: vN}` so each
    row stands alone for audit.
  - Write-once. Never edit a version after it has been used for real
    reviews. New version = new file.
  - Patch bumps (typo, clarification, no semantic change) leave
    existing rows on the prior version and do not trigger
    re-calibration.
  - Major bumps (added/removed dimension, retuned anchors, JSON schema
    change) require re-calibration of consensus thresholds.
- Reviewer sees **fresh** source examples drawn from the same
  difficulty-matched official pool but with a different random seed
  than the generator. Reviewer judges against the space of officials,
  not the specific officials the generator used.
- Re-review writes new `llm_review_results` rows with the current
  `rubric_version` and a fresh `review_run_id`; old rows are preserved.
  Consensus uses the latest completed review run for the current
  `rubric_version`.

### Consensus algorithm

Ordered, first match wins:

1. `official_overlap_status != none` -> `blocked_overlap`
2. successful review count < 2 -> `insufficient_reviews`
3. `max(copy_risk_score)` across reviewers >= MAX -> `reject_recommended`
4. `avg(realism_score)` < MIN -> `reject_recommended`
5. `avg(sat_fidelity_score)` < MIN -> `reject_recommended`
6. reviewer disagreement > MAX -> `admin_review_ready` with
   `high_disagreement_flag=true`
7. `avg(distractor_quality_score)` OR `avg(taxonomy_match_score)` < MIN
   -> `regenerate_recommended`
8. otherwise -> `admin_review_ready`

- Verdicts are advisory. Admin remains final. No auto-reject, no
  auto-approve in the initial build.
- Disagreement metric: stddev of `realism_score` across reviewers
  combined with the count of distinct `verdict` enums returned.
  Either crossing threshold trips `high_disagreement_flag`.
- Copy-risk is the **maximum** across reviewers, not the average. One
  reviewer detecting near-duplicate is sufficient signal.
- `insufficient_reviews` short-circuits steps 3-7 (averages are not
  trusted on a single reviewer).
- Consensus is computed at write time when the swarm completes. Re-run
  writes a new row; latest row by `created_at` wins for
  `(question_id, rubric_version)`.

### Threshold defaults (all scores out of 10)

| Threshold | Default | Notes |
| --- | --- | --- |
| `GENERATION_MIN_REALISM_SCORE` | 7.0 | Below = "doesn't feel like DSAT" |
| `GENERATION_MIN_SAT_FIDELITY_SCORE` | 7.0 | Same bar as realism |
| `GENERATION_MIN_DISTRACTOR_QUALITY_SCORE` | 6.5 | Mechanically fixable |
| `GENERATION_MIN_TAXONOMY_MATCH_SCORE` | 7.5 | Hit the requested target |
| `GENERATION_MAX_COPY_RISK_SCORE` | 5.0 | Asymmetric; any-reviewer trips |
| `GENERATION_MAX_REVIEWER_DISAGREEMENT` | 1.5 | Stddev of realism |

Strict by design for initial alpha. Bias toward false positives (good
questions flagged) over false negatives (bad questions approved).

### Calibration plan

- 50-question calibration batch before Phase 5 locks:
  - 20 grammar with varied focus keys.
  - 20 reading with varied skill families.
  - 10 deliberately weak (low-quality prompt, no source examples) as
    negative controls.
- Run full review swarm on all 50.
- Admin manually labels each `would_approve` / `would_reject` /
  `borderline`.
- Pick thresholds at the inflection where admin rejection rate flips
  from <20% to >50%.
- Recalibrate every ~500 reviewed questions, on any major version bump
  in `review`, `grammar`, or `reading`, or when adding a new generator
  or reviewer model.

### Release policy

Three values only:

- `admin_review_required` (default): question stays `draft` until admin
  approves. Consensus is advisory.
- `auto_release_on_accept` (admin only): if consensus =
  `admin_review_ready` AND no `high_disagreement_flag` AND overlap
  clean, question flips to `practice_status='active'` automatically.
  Otherwise behaves as `admin_review_required`. Requires global
  `GENERATION_AUTO_RELEASE_ENABLED=true` AND target in
  `GENERATION_AUTO_RELEASE_ALLOWED_TARGETS`. Both gates must pass.
- `dry_run` (admin only): saved, reviewed, scored, but never offered
  for approval. Used for calibration runs, benchmarking, A/B
  comparison. Filterable on dashboard. Excluded from inventory counts
  for the self-study agent.

Self-study-agent requests are forced to `admin_review_required`
regardless of what the agent passes.

### Self-study agent

- Caller surface: student-initiated synchronous only for the initial
  build. No background cron. The endpoint returns immediately
  available pool questions plus a `batch_id` for any newly created
  batch.
- Weakness profile shape:
  ```
  miss_rate       = miss_count / attempt_count
  recency_weight  = exp(-days_since_last_attempt / 14)
  volume_floor    = sqrt(attempt_count)
  weakness_score  = miss_rate * recency_weight * volume_floor
  ```
- Target selection: top-K = 5 per agent call. At most 2 targets share
  the same `focus_key`. Minimum 3 attempts to qualify. Targets that
  triggered a batch in the last 24h are dropped (cooldown).
- Inventory check per target:
  - Match `(domain, focus_key, difficulty_band)`, intersect with
    `practice_status='active'`, exclude student's seen set.
  - If remaining >= 5 -> serve from pool, no generation.
  - Else if a batch for this exact target is already pending -> serve
    pool, do nothing.
  - Else -> create a batch with `requested_count = max(threshold -
    remaining, MIN_BATCH=3)`; return existing pool + new `batch_id`.
- Configurable knobs:

  | Knob | Default | Notes |
  | --- | --- | --- |
  | `SELF_STUDY_LOOKBACK_DAYS` | 30 | Window for miss/attempt counts |
  | `SELF_STUDY_RECENCY_HALF_LIFE_DAYS` | 14 | Decay denominator |
  | `SELF_STUDY_TOP_K` | 5 | Targets per agent call |
  | `SELF_STUDY_MIN_ATTEMPTS_PER_TARGET` | 3 | Floor before target qualifies |
  | `INVENTORY_SUFFICIENT_THRESHOLD` | 5 | Per-target unseen-active floor |
  | `SELF_STUDY_MIN_GEN_BATCH_SIZE` | 3 | Floor for auto-generation |
  | `SELF_STUDY_TARGET_COOLDOWN_HOURS` | 24 | Prevent re-batching same target |
  | `SELF_STUDY_GEN_PER_STUDENT_PER_DAY` | 20 | Per-student daily ceiling |
  | `SELF_STUDY_MAX_PENDING_PER_TARGET` | 10 | Pending inventory cap |
  | `SELF_STUDY_MAX_PENDING_BATCHES_PER_STUDENT` | 3 | Work-in-flight cap |
  | `SELF_STUDY_POOR_QUALITY_COOLDOWN_HOURS` | 24 | After >=2 of last 3 batches with reject_rate >=0.5 |

- "Seen" semantics for `exclude_seen`:
  - All-time `UserProgress` attempts (not viewed-but-skipped).
  - Wrong-answered questions resurface after
    `SELF_STUDY_RESURFACE_DAYS=30`.
  - Right-answered questions never resurface in self-study mode.
- Deliberate exclusions from the weakness profile:
  - No `syntactic_trap_key` as a top-level target dimension; implicit
    in `focus_key`.
  - No `exam_code` / `test_id` segmentation.
  - No global accuracy score per student.

### Difficulty calibration

- Rubric anchor descriptions in `rules_agent_dsat_review_v1.md` must
  spell out difficulty bands with concrete markers (vocab tier,
  sentence complexity, inference depth, distractor closeness), not
  vibes.
- Source examples loaded for the reviewer are filtered to match the
  request's `difficulty_overall` band.
- The original request is included in the reviewer payload so the
  reviewer can compare requested vs apparent difficulty.
- Post-hoc calibration via student performance (`observed_difficulty`
  derived from `UserProgress.is_correct` aggregates) is deferred to
  Phase 9 analytics.

### Regenerate-from-spec (Phase 6 admin action)

- Creates a **new single-question batch**, not a new job in the
  original batch. Original batch's counters stay sealed.
- New batch's `regenerate_source_batch_id` FK points to the original.
- Original `generation_source_set` request payload is copied verbatim,
  with `requested_count=1`. Same provider/model by default; admin can
  override per regenerate.
- Source examples are re-selected fresh; original examples are now in
  the last-50 rotation window and naturally deprioritized.
- New question's `derived_from_question_id` points to the rejected
  question. Original question remains in DB with
  `practice_status='rejected'` for audit.
- Cap: `REGENERATE_MAX_ATTEMPTS_PER_QUESTION = 3`. After three
  regenerations the question is locked from further regenerate; admin
  must edit spec or give up.

### Admin override capture

- Implicit on every approve/reject. No separate "reviewer was wrong"
  click.
- One append-only row per reviewer per admin decision in
  `reviewer_admin_overrides`; rows from the same approve/reject click share
  `admin_decision_id`. If admin's decision matches a reviewer's verdict,
  `override_direction='reviewer_correct'` is still recorded for that reviewer.
- Reviewer-quality flagging:
  - `REVIEWER_FLAG_OVERRIDE_RATE = 0.30` over the last
    `REVIEWER_FLAG_MIN_REVIEWS = 50` reviews triggers an attention
    flag.
  - Flag only. No auto-disable. Admin decides whether to swap or retire
    a reviewer model.

### Student retrieval (`GET /api/questions`)

- `exclude_seen` is a boolean. Server applies the Q13 rule
  (all-time attempts with 30-day wrong-answer resurface, never for
  correct). Default `true` for student tokens, `false` for admin
  tokens.
- Response includes an `inventory` block:
  ```json
  {
    "matching_target_total": 47,
    "matching_unseen": 12,
    "served": 5,
    "includes_generated": true,
    "below_threshold": false,
    "threshold": 5
  }
  ```
- `origin` defaults to `mixed`. `includes_generated` is always present
  in the response so the frontend can label questions if desired.
- Only `practice_status='active'` ever reaches this endpoint
  regardless of filter combination. Drafts, rejected, and dry_run
  never served.

### Rejection semantics and enum migrations (Phase 0 prerequisite)

Current `reject_question` (`backend/app/routers/admin.py:351`) sets
`practice_status='retired'` AND deletes `LlmEvaluation`,
`QuestionAnnotation`, `QuestionRelation` rows plus clears per-option
annotation fields. That destructive behavior is incompatible with the
audit-trail and `reviewer_admin_overrides` requirements locked above.
Must change before review-swarm data is attached to generated
candidates.

- `PRACTICE_STATUSES` migration: add `"rejected"` as a new value
  alongside existing `"draft"`, `"active"`, `"retired"`. Two distinct
  terminal states:
  - `rejected` = failed quality review (never reached `active`).
  - `retired` = was `active`, removed later for post-release reasons
    (admin found typo, content deprecated). Re-activatable in
    principle.
  - Dashboard counts these separately: rejection rate is a generation
    quality metric, retirement rate is a post-release metric.
- `OVERLAP_STATUSES` migration: no new values for this feature. Keep the
  existing `("none", "possible", "confirmed")` enum. `none` remains the only
  clean state; when an admin dismisses a false-positive overlap, the existing
  clear-overlap path returns the question to `none`. The review consensus value
  `blocked_overlap` is a derived verdict, not a stored `official_overlap_status`
  value.
- Rewrite `reject_question` as metadata-only:
  - Set `practice_status='rejected'`.
  - Set new columns `rejection_reason`, `rejected_at`,
    `rejected_by_admin_token` on `questions`.
  - Write `reviewer_admin_overrides` rows for each existing
    `llm_review_results` row tied to this question (Q17 implicit
    capture).
  - Do **NOT** delete `LlmEvaluation`, `llm_review_results`,
    `consensus_verdicts`, `QuestionAnnotation`, `QuestionRelation`, or
    options; do **NOT** clear option annotation fields.
- Keep `DELETE /admin/questions/{id}` for the rare case where admin
  wants the row physically gone.

### Review run grouping

A "review run" is one swarm pass against one question. All reviewer
rows from that pass plus the resulting consensus row share a single
`review_run_id`.

- New table `review_runs`:
  - `id`, `question_id`, `generation_batch_id` (nullable).
  - `triggered_by`: `auto_on_save` | `manual_question` | `manual_batch`
    | `recalibration` | `rubric_bump`.
  - `triggered_by_admin_token` (nullable).
  - `rubric_version` and `rules_versions_jsonb` snapshot at run start.
  - `status`: `running` | `complete` | `partial` | `failed`.
  - `started_at`, `completed_at`.
- Scope is per-question, not per-batch. Batch-level review-swarm
  triggers spawn N runs (one per question). Per-question latency,
  cost, and reviewer agreement remain the dashboard's atomic unit.
- Batch-level grouping uses `generation_batch_id` on
  `llm_review_results`; do not double-encode via the run.
- `llm_review_results.review_run_id` and
  `consensus_verdicts.review_run_id` both FK to `review_runs.id`.
- Re-review always mints a new `review_run_id`. Previous runs'
  reviewer rows and consensus rows are preserved untouched. Latest
  consensus row by `created_at` per `(question_id, rubric_version)`
  is the active verdict.
- Partial-run handling (interacts with the reviewer failover rule):
  when fewer than 2 reviewers succeed, the run completes with
  `status='partial'`, reviewer rows are written for both successes
  (`review_status='ok'`) and failures
  (`review_status='transient_failed'` or `'permanent_failed'`), and a
  `consensus_verdicts` row IS still written with
  `consensus_verdict='insufficient_reviews'`. No question is left
  with a null verdict.

### Auth scopes for new endpoints

Existing auth surface is dual-track:

- Service-level: `admin_required` and `student_required` (header-based
  API key membership check, `backend/app/auth.py`).
- User-level: `User.user_token` UUID passed in request body/query.
  Service knows "a student client is calling" but not which student
  until the request supplies `user_token`.

Per-endpoint scope:

| Endpoint | Scope |
| --- | --- |
| `POST /generate/batches` | admin |
| `GET /generate/batches/{id}` | admin |
| `GET /generate/batches/{id}/questions` | admin |
| `POST /generate/batches/{id}/retry-failed` | admin |
| `POST /generate/batches/{id}/review-swarm` | admin |
| `POST /admin/questions/{id}/review-swarm` | admin |
| `GET /admin/generated-questions` | admin |
| `POST /admin/generated-questions/{id}/approve\|reject\|regenerate` | admin |
| `GET /api/questions` | student OR admin |
| `POST /api/study/recommendations` | student |
| `POST /api/study/generation-requests` | student |
| `GET /api/study/generation-requests/{batch_id}` | student (own batch) |

- New dependency `admin_or_student_required` returns a `(scope, key)`
  tuple. `GET /api/questions` branches on `scope` to set the default
  for `exclude_seen` (true for student, false for admin) and to choose
  which side of `origin=mixed` defaults to apply.
- Per-user identity continues to come from `user_token` in the request
  body or query parameter. No per-user API keys yet; the student API
  key remains a shared service password.
- Audit: `requested_by_user_token` recorded on `generation_batches`
  when `requested_by='self_study_agent'`, separate from the existing
  `student_id` FK. `student_id` is the normalized `users.id` when the supplied
  token resolves; `requested_by_user_token` preserves the caller identity even
  if later user/profile lookup rules change.

### Request payload layering

Three layers, each frozen at its own creation point, with a strict
derivation rule between them.

| Layer | What it holds | Frozen at |
| --- | --- | --- |
| `GenerationBatch.request_jsonb` | Raw POST body received at `/generate/batches`. Includes `requested_count`, `requested_by`, `student_id`, `requested_by_user_token`, `release_policy`, the content spec, optional `source_question_ids`. Does not include the `Idempotency-Key` header; that lives in `generation_batch_idempotency_keys`. | Batch creation |
| `QuestionJob.generation_request_jsonb` | Per-question specialization of the batch request: content spec + operational keys (`provider_name`, `model_name`, `seed`, `temperature`, `retry_attempt`, `derived_from_question_id`) + the actual source examples picked from the rotation pool for this specific job (differs across siblings within a batch). | Job creation |
| `Question.generation_source_set` | Content lineage. Derived from `QuestionJob.generation_request_jsonb` by stripping operational keys. Source example IDs are retained (they are lineage, not operational). Regeneration parentage is stored in `Question.derived_from_question_id`, not duplicated in this JSONB. | Question save |

Identity invariant (asserted by test):

```
Question.generation_source_set == {
    k: v for k, v in QuestionJob.generation_request_jsonb.items()
    if k not in _SOURCE_SET_OPERATIONAL_KEYS
}
```

Expanded operational-keys filter (current set in
`generate.py:31` is too narrow):

```python
_SOURCE_SET_OPERATIONAL_KEYS = {
    "provider_name", "model_name", "seed", "temperature",
    "retry_attempt", "idempotency_key", "derived_from_question_id",
    "requested_count", "requested_by", "student_id", "requested_by_user_token",
    "release_policy", "skip_review",
}
```

`idempotency_key` is in the filter as **defense-in-depth** — the locked
design also keeps it out of `request_jsonb` by storing it in
`generation_batch_idempotency_keys`. The filter entry catches accidental
leaks if a future code path copies the header into the request payload.

`source_question_ids` and content spec keys (`grammar_role_key`,
`reading_focus_key`, etc.) are lineage and stay.

Mutation discipline:

- `request_jsonb` and `generation_request_jsonb` are append-only at
  the row level (never `UPDATE`d). New event = new row. Transient
  retries reuse the same job (same jsonb); parameter-changing retries
  create a new job.
- `generation_source_set` is frozen at question save. Admin edits to
  question content create a new `QuestionVersion` row; the lineage
  field is untouched.

### Still open (smaller, mechanical, or explicitly deferred)

- Phase 9 dashboard metric catalog (lots of charts; not
  architecturally tricky).
- Phase 10 auto-release flag wiring and audit-log shape (gated by
  calibration data we do not have yet).
- Cost / token budget alerting thresholds.
