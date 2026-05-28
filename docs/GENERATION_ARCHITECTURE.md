# Generation Architecture

This document explains the three-layer design for question generation, review,
and release. It is a Phase 0 deliverable for the Generation, Review, and
Self-Study Factory (see `TASKS_GENERATION.md`).

## Layer 1 — Official Questions as the Generation Foundation

Official College Board questions (ingested from the canonical PDF source in
`TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/`) are the authoritative source
of style, difficulty, and taxonomy for all generated content.

- Stored with `content_origin = "official"` and `practice_status = "active"`.
- Loaded by `_load_official_source_examples()` in `generate.py` as in-context
  examples for every generation prompt.
- Generated questions must calibrate against them without copying passages,
  stems, options, or explanations.
- `is_canonical_source` (Phase 1) will mark a curated fallback pool of ~5
  grammar + 5 reading exemplars for targets where no closely matched officials
  exist in the active pool.

## Layer 2 — Generated Items as Candidates

A generated question is a candidate, not a student-ready item, until it clears
both the review swarm and explicit admin approval.

- Saved with `content_origin = "generated"` and `practice_status = "draft"`.
- Outputs that fail blocking validation are failed generation attempts, not
  saved candidates. They retain pass payloads and validation/error details on
  `QuestionJob` and do not create partial `Question` rows.
- Never served by `GET /api/questions` while in `draft` state.
- Linked to its originating `GenerationBatch` (Phase 1) through
  `QuestionJob.generation_batch_id`.
- Every candidate carries its full lineage in `Question.generation_source_set`:
  the content spec and source official example IDs. Operational workflow and
  model-run keys such as provider, model, seed, temperature, retry attempt,
  requester identity, and release policy are stripped by
  `_SOURCE_SET_OPERATIONAL_KEYS`.
- Official overlap detection runs immediately after save. A question with an
  unresolved overlap is blocked from approval and blocked from the review swarm.

## Layer 3 — Review Swarm Output Is Not Admin Approval

The multi-model LLM review swarm (Phase 3–4) produces a quality signal, not a
release decision.

- Each reviewer model (OpenAI, Anthropic, Ollama/DeepSeek) writes an
  independent row to `llm_review_results` with numeric scores and a verdict
  (`accept` | `needs_human_review` | `reject`).
- A deterministic consensus gate (Phase 5) converts those rows into a single
  advisory verdict stored in `consensus_verdicts`: `admin_review_ready`,
  `reject_recommended`, `regenerate_recommended`, `blocked_overlap`, or
  `insufficient_reviews`.
- **Advisory means advisory.** No consensus verdict automatically flips a
  question to `practice_status = "active"`. Only an explicit admin approve
  action does that (Phase 6 dashboard or `POST
  /admin/generated-questions/{id}/approve`).
- The only mechanism that makes a generated question student-visible is:
  `draft` → admin approval → `practice_status = "active"`.
- Auto-release (`auto_release_on_accept` policy) is an opt-in Phase 10 feature
  gated behind `GENERATION_AUTO_RELEASE_ENABLED=false` and not active in the
  initial build.

## Rejection Semantics

`rejected` and `retired` are distinct terminal states:

- `rejected`: failed quality review before ever reaching `active`. All
  annotations, options, review results, consensus rows, and generation lineage
  are preserved for audit. Only `practice_status`, `rejection_reason`,
  `rejected_at`, and `rejected_by_admin_token` change.
- `retired`: was `active`, removed post-release (typo found, content
  deprecated). Re-activatable in principle.

The generation quality metric uses the `rejected` count. Post-release health
uses the `retired` count. They must not be conflated.

## Key Files

| File | Role |
|------|------|
| `backend/app/routers/generate.py` | Generation pipeline, source-example loading, `_SOURCE_SET_OPERATIONAL_KEYS` |
| `backend/app/routers/admin.py` | Non-destructive `reject_question`, approve |
| `backend/app/models/db.py` | `Question`, `QuestionJob`, `LlmEvaluation` ORM models |
| `backend/app/models/ontology.py` | Generated enums including `practice_status` (`draft`, `active`, `retired`, `rejected`) |
| `backend/migrations/versions/020_*.py` | `rejected` enum value + reason columns |
| `backend/migrations/versions/021_*.py` | `generation_batches` + idempotency key tables (Phase 1) |
| `TASKS_GENERATION.md` | Full 10-phase roadmap with locked architectural decisions |
