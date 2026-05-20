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
- Admin review already has approve/reject controls for questions.

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

- `generation_batch_id` on `QuestionJob`, `Question`, or a join table
- `generation_request_jsonb` or reuse `generation_source_set`
- `source_question_ids`
- generator `provider_name` and `model_name`
- prompt and rules versions

### Review Swarm Result

Each reviewer model writes an independent review result. This can extend
`LlmEvaluation` or use a new `llm_review_results` table if richer JSON and
verdicts are cleaner than widening the existing table.

Recommended fields:

- `id`
- `question_id`
- `job_id`
- `generation_batch_id`
- `provider_name`: `openai`, `anthropic`, `ollama`
- `model_name`: for example `gpt-*`, Claude, `deepseek-v4-pro:cloud`
- `task_type`: `generation_realism_review`
- `rubric_version`
- `scores_jsonb`
- `verdict`: `accept`, `needs_human_review`, `reject`
- `review_notes`
- `raw_response_jsonb`
- `latency_ms`
- `token_usage_jsonb`
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
adding batch and swarm behavior.

- [ ] Confirm generated questions are always saved before review.
- [ ] Confirm generated questions stay `draft` by default.
- [ ] Confirm admin approval is required before generated questions appear in
  student retrieval.
- [ ] Confirm `source_question_ids` only loads stored official questions.
- [ ] Confirm generation prompts include both grammar and reading rule
  markdowns.
- [ ] Add or update a short architecture note explaining:
  - official questions are the generation foundation
  - generated items are candidates until reviewed
  - review swarm output is not the same as admin approval

**Exit criteria:** The baseline behavior is documented and covered by targeted
tests.

## Phase 1: Batch Generation Contract

**Goal:** Let admins and self-study agents request variable quantities of
generated questions.

- [ ] Add a `GenerationBatchRequest` model with:
  - `requested_count`, bounded by config
  - grammar target fields
  - reading target fields
  - `difficulty_overall`
  - `source_question_ids`
  - `requested_by`
  - `student_id`, optional
  - `release_policy`
  - `provider_name`, optional
  - `model_name`, optional
- [ ] Add validation rules:
  - request must contain a complete grammar target or complete reading target
  - `requested_count` must be within admin-configured limits
  - self-study-agent requests must include a student identifier or profile
    reference
  - `release_policy` defaults to `admin_review_required`
- [ ] Add a `GenerationBatch` persistence model and migration.
- [ ] Add `generation_batch_id` linkage for generated jobs and saved questions.
- [ ] Add config:
  - `GENERATION_MAX_BATCH_SIZE`
  - `GENERATION_DEFAULT_BATCH_SIZE`
  - `GENERATION_MAX_PENDING_BATCHES`
- [ ] Add endpoint:
  - `POST /generate/batches`
  - `GET /generate/batches/{batch_id}`
  - `GET /generate/batches/{batch_id}/questions`
- [ ] Ensure existing `POST /generate/questions` remains backward-compatible for
  one-off admin generation.

**Exit criteria:** A caller can request N targeted questions and receive a
batch ID with N queued generation jobs.

## Phase 2: Quantity-Aware Generation Runner

**Goal:** Execute batches safely while preserving one-question traceability.

- [ ] Create one `QuestionJob` per requested generated question.
- [ ] Copy the batch request into each job's generation source metadata.
- [ ] Preserve one LLM generation call per question.
- [ ] Save each generated candidate as:
  - `Question`
  - `QuestionVersion`
  - `QuestionAnnotation`
  - `QuestionOption`
  - YAML archive mirror
- [ ] Run official overlap detection per saved question.
- [ ] Track batch counters:
  - created
  - failed
  - needs review
  - rejected
  - approved
- [ ] Add retry behavior for failed individual generation jobs without rerunning
  the entire batch.
- [ ] Add idempotency key support so repeated admin clicks do not create
  duplicate batches.

**Exit criteria:** Batch generation can partially succeed, and every generated
candidate has an individual status, saved payload, and audit trail.

## Phase 3: Review Swarm Rubric

**Goal:** Define a stable multi-model review contract for generated-question
quality.

- [ ] Create a rubric prompt for generated-question realism review.
- [ ] Rubric must score:
  - DSAT realism
  - SAT style fidelity
  - target taxonomy match
  - difficulty match
  - distractor quality
  - correct-answer defensibility
  - explanation quality
  - grammar/reading rule compliance
  - copy or near-duplicate risk
  - student-facing ambiguity risk
- [ ] Rubric must return strict JSON.
- [ ] Rubric must include `verdict`:
  - `accept`
  - `needs_human_review`
  - `reject`
- [ ] Rubric must require short reasons for every score below threshold.
- [ ] Add tests for parsing valid review JSON and rejecting malformed review
  output.
- [ ] Version the rubric with `rubric_version`.

**Exit criteria:** One generated question can be reviewed by one model and
produce a durable, structured quality review.

## Phase 4: Multi-Model Review Runner

**Goal:** Run OpenAI, Claude, and DeepSeek-style reviewers against saved
generated candidates.

- [ ] Add review provider config:
  - `GENERATION_REVIEW_PROVIDERS=openai,anthropic,ollama`
  - `GENERATION_REVIEW_OPENAI_MODEL`
  - `GENERATION_REVIEW_ANTHROPIC_MODEL`
  - `GENERATION_REVIEW_OLLAMA_MODEL=deepseek-v4-pro:cloud`
  - `GENERATION_REVIEW_MAX_CONCURRENT`
- [ ] Add a review runner that loads:
  - saved generated question
  - options
  - annotation
  - generation request
  - source official examples
  - overlap status
- [ ] Run reviewers concurrently with a semaphore.
- [ ] Save one review result per provider/model.
- [ ] Treat review failure as a review status, not as deletion of the generated
  question.
- [ ] Add endpoint:
  - `POST /admin/questions/{question_id}/review-swarm`
  - `POST /generate/batches/{batch_id}/review-swarm`
- [ ] Add tests for:
  - all reviewers succeed
  - one reviewer fails
  - malformed reviewer JSON
  - duplicate review prevention
  - review rerun creates a new rubric/versioned attempt or supersedes old
    attempts predictably

**Exit criteria:** A saved generated question can receive independent reviews
from OpenAI, Claude, and DeepSeek/DeepSeek-via-Ollama without blocking the
question's saved record.

## Phase 5: Consensus Gate

**Goal:** Turn review-swarm output into deterministic admin-facing status.

- [ ] Add consensus calculation after review results are saved.
- [ ] Default policy:
  - reject recommended if any model reports high copy risk
  - reject recommended if average realism is below threshold
  - needs human review if reviewer disagreement is high
  - admin review ready if all core averages clear threshold
  - blocked if official overlap status is unresolved
- [ ] Store consensus output on a new table or in batch/question review JSON.
- [ ] Add config thresholds:
  - `GENERATION_MIN_REALISM_SCORE`
  - `GENERATION_MIN_SAT_FIDELITY_SCORE`
  - `GENERATION_MIN_DISTRACTOR_QUALITY_SCORE`
  - `GENERATION_MIN_TAXONOMY_MATCH_SCORE`
  - `GENERATION_MAX_COPY_RISK_SCORE`
  - `GENERATION_MAX_REVIEWER_DISAGREEMENT`
- [ ] Add tests for each verdict path.
- [ ] Do not activate generated questions from consensus alone in the initial
  build.

**Exit criteria:** Every reviewed generated question has a consensus verdict
that the admin dashboard can filter and sort.

## Phase 6: Admin Dashboard Review Queue

**Goal:** Let admins visually inspect, filter, approve, reject, and regenerate
generated candidates efficiently.

- [ ] Add dashboard filters:
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
- [ ] Candidate card must show:
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
- [ ] Actions:
  - approve
  - reject
  - edit
  - request re-review
  - regenerate from same spec
  - mark reviewer assessment as wrong
  - compare with official source examples
- [ ] Ensure rejection does not delete the record. It should retire or mark the
  question rejected for audit.
- [ ] Add list endpoints optimized for dashboard filtering and pagination.

**Exit criteria:** Admin can filter to the riskiest generated questions first,
visually inspect them, and reject or approve without leaving the dashboard.

## Phase 7: Student Retrieval API Expansion

**Goal:** Serve approved questions to students with richer targeting and
inventory awareness.

- [ ] Extend `GET /api/questions` filters:
  - `domain`
  - `difficulty`
  - `grammar_role_key`
  - `grammar_focus_key`
  - `reading_skill_family_key`
  - `reading_focus_key`
  - `stimulus_mode_key`
  - `origin=official|generated|mixed`
  - `exclude_seen`
  - `limit`
- [ ] Add result metadata:
  - active inventory count for the requested target
  - whether generated questions were included
  - whether inventory is below threshold
- [ ] Ensure student-facing payload never exposes answer key.
- [ ] Ensure only `practice_status = "active"` questions are served.
- [ ] Add tests for grammar filters, reading filters, difficulty filters,
  exclude-seen behavior, and active-only enforcement.

**Exit criteria:** A student or study agent can retrieve targeted active
questions across grammar and reading without seeing draft candidates.

## Phase 8: Self-Study Agent Request Layer

**Goal:** Let a monitor identify weak skills and request generation only when
existing inventory is insufficient.

- [ ] Define a student weakness profile:
  - recent accuracy
  - missed grammar focus keys
  - missed syntactic traps
  - missed reading focus keys
  - difficulty bands where performance drops
  - recency weighting
- [ ] Add endpoint:
  - `POST /api/study/recommendations`
  - `POST /api/study/generation-requests`
- [ ] Self-study agent flow:
  - inspect student progress
  - identify target focus and difficulty
  - check active inventory first
  - retrieve existing questions if enough inventory exists
  - create generation batch only when inventory is low
  - return batch status and expected review path
- [ ] Add caps:
  - max generated per student per day
  - max pending generated questions per target
  - max pending batches per student
  - cooldown after poor batch quality
- [ ] Generated questions from self-study agent requests remain draft until
  approved by admin or an explicitly configured later release policy.

**Exit criteria:** The self-study agent can request exactly the type of
questions a student needs without bypassing quality review.

## Phase 9: Generation Quality Analytics

**Goal:** Measure which generation and review models actually produce useful
student-ready questions.

- [ ] Add dashboard metrics:
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
  - generated vs official student performance
- [ ] Add batch analytics:
  - requested count vs created count
  - created count vs approved count
  - average review latency
  - cost and token usage by provider
- [ ] Add quality trend views over time.
- [ ] Add export endpoint for offline analysis.

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

- Whether to widen `LlmEvaluation` or add a dedicated `llm_review_results`
  table.
- Whether batch linkage should live directly on `questions`, on
  `question_jobs`, or in a join table.
- Whether self-study agent requests should be allowed to use non-official
  generated questions as future source examples. Initial recommendation: no.
- Whether approved generated questions can ever become source examples.
  Initial recommendation: only after they have enough student performance data
  and admin endorsement.
- Whether auto-release is acceptable for any target in alpha. Initial
  recommendation: keep disabled until quality analytics prove reliability.

## Recommended Build Order

1. Generation batch model and request validation.
2. Quantity-aware generation runner with saved candidates.
3. Review rubric and one-model review runner.
4. Multi-model review swarm.
5. Consensus verdict storage.
6. Admin dashboard filtering and visual review cards.
7. Student retrieval API expansion.
8. Self-study agent request layer.
9. Quality analytics.
10. Optional controlled auto-release.
