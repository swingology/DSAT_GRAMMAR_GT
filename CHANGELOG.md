# CHANGELOG

All significant changes to this project. Timestamps are commit time (PDT, UTC-7).
Agent/model varies by entry; see each entry's `Model` line.

---

## 2026-05-23 — Write in user highlight feature

**Model:** Antigravity (Agent)

### Added
- **`passage_tokens` generation requirement** (`rules_agent_dsat_grammar_ingestion_generation_v7.md`) — Added instruction to mandate `passage_tokens` tokenized array generation in the `classification` output schema, allowing the UI to highlight word-level grammar elements dynamically.
- **`passage_tokens` payload** (`backend/app/models/payload.py`) — Added `passage_tokens` list field to `StudentQuestionResponse`.
- **UI Highlight Support** (`htmx-grammar-app/templates/app_container.html` & `app.py`) — Updated the Flask testbed `get_context()` to flatten `latest_annotation` from the API so tokenized text and grammar metadata map to the Jinja templates. Added Jinja logic in `app_container.html` to parse and highlight specific `passage_tokens` tags visually when grammar keys are clicked. Added a demo token array to the hardcoded testbed fallback question.

---

## 2026-05-23 — Prompt Caching (Anthropic + Ollama) and Rules Version Upgrade

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

### Added

- **`build_annotate_prompt_parts()`** (`backend/app/prompts/annotate_prompt.py`) — new
  function that returns `(system_static, system_dynamic, user)` separating the large
  static rules block from the per-call dynamic instructions. `system_static` is the
  grammar v7 (~37K chars) or reading v2 (~40K chars) rules context. `system_dynamic`
  is the routing rules, allowed-key constraints, and `content_origin` marker (~6K chars).

- **`build_generate_prompt_parts()`** (`backend/app/prompts/generate_prompt.py`) — same
  split for the generation pipeline. `system_static` is the domain-filtered generation
  sections from grammar v7 + reading v2 (~80K chars). `system_dynamic` is the concise
  `GENERATE_SYSTEM_PROMPT` base (~1.3K chars).

- **`_SYSTEM_INSTRUCTIONS_TEMPLATE`** (`annotate_prompt.py`) — instructions-only system
  prompt template (identical routing rules, nullability enforcement, difficulty calibration,
  amendment proposal spec) that references rules "provided above" rather than embedding
  them inline. Used by `build_annotate_prompt_parts()`.

- **`AnthropicProvider.complete_cached()`** — sends system as a list of two content
  blocks: `[{text: system_static, cache_control: {type: ephemeral}}, {text: system_dynamic}]`.
  Anthropic caches everything up to and including the first block across calls within a
  5-minute window. `LLMResponse.cache_token_usage` now captures `cache_creation` and
  `cache_read` token counts from `response.usage`.

  **Token savings per 33-question module at Claude Sonnet pricing ($3/MTok input, $0.30/MTok cache read):**
  | Domain | Without caching | With caching | Saved |
  |---|---|---|---|
  | Grammar (16 Q) | 164,800 tokens | ~25,750 tokens | ~139,050 (84%) |
  | Reading (17 Q) | 297,500 tokens | ~45,500 tokens | ~252,000 (85%) |
  | **Total** | **462,300** | **~71,250** | **~391,000 (85%)** |

- **`OllamaProvider.complete_cached()`** — concatenates `system_static + system_dynamic`
  (same string as before for deterministic KV prefix matching) and adds
  `options.num_keep = max(len(system_static) // 3, 512)` to protect the static rules
  prefix from eviction if the context window overflows. Ollama automatically reuses KV
  cache when the same prefix appears in consecutive requests to the same loaded model.

- **`OpenAIProvider.complete_cached()`** — concatenates static + dynamic and delegates to
  `complete()`. OpenAI automatically caches stable prefixes ≥ 1024 tokens; no API change
  required.

- **`LLMResponse.cache_token_usage`** (`backend/app/llm/base.py`) — new `dict` field
  (default `{}`) on `LLMResponse` for provider-reported cache hit/creation counts.
  `cache_token_usage: {cache_creation: int, cache_read: int}` on Anthropic; empty on others.

- **`scripts/reannotate_official_v7.py`** — bulk re-annotation script that calls
  `POST /ingest/reannotate/{question_id}` for every `content_origin='official'` question
  (currently 569), polling each job to completion and writing a summary to
  `analysis/calibration/reannotation_report.json`. Accepts `--dry-run`, `--limit N`,
  `--provider`, `--model`, `--base-url`, `--api-key` flags.

### Changed

- **`config.py` `rules_version`** — corrected from `"rules_agent_dsat_grammar_ingestion_generation_v3"`
  to `"rules_agent_dsat_grammar_ingestion_generation_v7"`. This field is the metadata label
  stamped on every `question_annotations.rules_version` row. The annotation *prompt*
  (`annotate_prompt.py`) was already loading v7 grammar and v2 reading rules; only the
  label was stale, but the original 569 official question ingestion runs were also done
  before `annotate_prompt.py` pointed at v7, causing the taxonomy inconsistencies
  catalogued in `INCONSISTENT_KEYS_LIST.md`.

- **`prompt_version`** — all hardcoded `"v3.0"` values updated to `"v7.0"` across
  `ingest.py` (4 sites), `generate.py` (3 sites), and `student.py` (1 site). Jobs
  created from this point forward are correctly stamped.

- **All annotation call sites** in `ingest.py` (`_annotate_one` in `_run_pipeline` and
  `_run_reannotate_pipeline`) and `generate.py` (`_run_generate_pipeline`, both the
  generation pass and the post-generation annotation pass) now call
  `provider.complete_cached()` instead of `provider.complete()`.

- **`_run_reannotate_pipeline`** import updated from `build_annotate_prompt` to
  `build_annotate_prompt_parts`; `_run_pipeline` main import similarly updated.

### Verification

- `uv run pytest tests/ -q` → **751 passed, 2 skipped** (0 failures).
- All provider mocks in `test_backend_regressions.py`, `test_pipeline.py`, and
  `test_generate_runner.py` updated to mock `complete_cached` for annotation/generation
  calls and keep `complete` only for Pass 1 extraction calls.

---

## 2026-05-23 — Admin Question Audit Log

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

### Added

- New `admin_question_audit_logs` table (migration `027`) providing an append-only
  audit trail for every admin mutation of a question or its answer key.
- New `_write_admin_audit()` helper in `admin.py` called before every `db.commit()`
  in mutation endpoints.
- Audit wired into five endpoints: `PATCH /admin/questions/{id}` (edit),
  `POST .../approve`, `POST .../reject`, `POST .../confirm-overlap`,
  `POST .../clear-overlap`.
- Each row stores: `admin_token`, `action`, `fields_changed` (JSONB array),
  `before_jsonb`, `after_jsonb`, `change_notes`, and a FK to the new
  `QuestionVersion` for edit actions.

### Verification

- `uv run pytest tests/test_admin_router.py tests/test_backend_regressions.py -q`
  → `85 passed`.

---

## 2026-05-23 — Chart Data Correction via GLM OCR Crop (Test 4 Mod01 Q13)

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

### Fixed

- `question_stimulus_assets.structured_data_jsonb` and `question_annotations.annotation_jsonb.graph_data`
  for Test 4 · Sec 01 · Mod 01 · Q13 contained incorrect bar values. The original
  ingestion LLM misidentified which bar belonged to which state at full page-render
  resolution (1224×1584).
- Corrected by cropping and 3× upscaling the chart region, then submitting the crop
  to `glm-ocr:latest` via Ollama for a fresh read. GLM output cross-checked against
  user visual inspection of the original PDF.
- Corrected values: California 2800, Wisconsin 1300, New York 1000, Pennsylvania 800,
  Iowa 700, Washington 600 (previously Pennsylvania/Wisconsin/Iowa were all 1300,
  New York was 700).
- JSON file on disk (`local_object_store/stimulus-assets/charts/.../8d234175....json`)
  also patched to match.

---

## 2026-05-23 — Ingestion Test run.sh API Key Fix

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

### Fixed

- `.claude/skills/ingestion-test/run.sh` hardcoded `KEY="admin-test-key"` which never
  matched the backend default (`admin-key-change-me`), causing all ingestion test
  submissions to return HTTP 401.
- Changed to `KEY="${ADMIN_API_KEY:-admin-key-change-me}"` — falls back to the real
  default and can be overridden via environment variable.

---

## 2026-05-21 — Generation Phases 0-10 Code Gap Remediation

**Model:** GPT-5 Codex
**Branch:** `generation_build`

Fixed the code gaps recorded in `DEBUG_LOG.md` under "Generation Phases 0-10
Code Gap Review."

### Fixed

- Auto-release allowed-target matching now reads `QuestionAnnotation.annotation_jsonb`
  and infers grammar/reading domain from stored annotation keys.
- Auto-release now writes `AutoReleaseAuditLog` rows for blocked gate outcomes
  after a question is known, not only for successful releases.
- Self-study generation now builds a strict `GenerationBatchRequest`, fills the
  mandatory grammar/reading fields, selects official source examples, strips
  batch-only `requested_count` from job requests, and keeps
  `release_policy='admin_review_required'`.
- Dry-run generated questions are blocked from manual admin approval and are
  excluded from student recall even if a question is later marked active.
- Batch analytics and self-study quality cooldown now derive accepted/rejected
  counts from generated `Question.practice_status` via `QuestionJob`, avoiding
  stale batch decision counters.
- Review analytics and batch analytics now read provider token usage from the
  current `{"input": ..., "output": ...}` keys, with legacy key fallback.
- `copy_risk_failures` now counts only reject recommendations whose
  `max_copy_risk` meets the configured copy-risk threshold.
- Review swarm source examples are selected fresh from same-target official
  questions instead of reusing the generator's original examples.
- Auto-selected generation sources now hard-filter known stimulus-mode
  mismatches, avoid recently used source IDs when enough alternatives exist,
  and diversify across exam codes.

### Verification

- `uv run pytest tests/test_auto_release.py tests/test_self_study.py tests/test_generate_batches.py tests/test_analytics.py tests/test_backend_regressions.py -q`
  → `188 passed, 1 warning`.

---

## 2026-05-21 — Phase 10: Controlled Auto-Release Policy

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

Implemented the Phase 10 controlled auto-release layer — opt-in, thresholded,
auditable auto-activation of generated questions when all quality gates pass.

### Added

- `backend/app/review/auto_release.py` — `maybe_auto_release()` function
  implementing 8 ordered gates: (1) global config flag, (2) runtime kill switch,
  (3) batch `release_policy == 'auto_release_on_accept'`, (4) consensus verdict
  `admin_review_ready`, (5) `high_disagreement_flag` false, (6) overlap status
  `none`, (7) question annotation matches an entry in `GENERATION_AUTO_RELEASE_ALLOWED_TARGETS`,
  (8) generator model has ≥ `GENERATION_AUTO_RELEASE_MIN_REVIEWS` admin-decided
  questions with acceptance rate ≥ `GENERATION_AUTO_RELEASE_MIN_ACCEPT_RATE`. All
  gate outcomes recorded in the audit row regardless of result.
- `AutoReleaseAuditLog` ORM model in `backend/app/models/db.py` — immutable
  append-only row per release attempt, capturing question, batch, review run,
  consensus verdict, generator stats, release policy, and full `reasons_jsonb`.
- Migration `backend/migrations/versions/026_phase10_auto_release_audit.py` —
  creates `auto_release_audit_logs` table with indexes on `question_id` and
  `released_at`.
- `maybe_auto_release` wired into `backend/app/review/consensus.py` — called
  automatically after each consensus verdict is written.
- Config flags (all in `backend/app/config.py`):
  - `GENERATION_AUTO_RELEASE_ENABLED=false` — master opt-in switch, off by default
  - `GENERATION_AUTO_RELEASE_MIN_REVIEWS=3` — minimum admin-decided questions for generator
  - `GENERATION_AUTO_RELEASE_MIN_ACCEPT_RATE=0.80` — minimum historical acceptance rate
  - `GENERATION_AUTO_RELEASE_ALLOWED_TARGETS=""` — JSON array of annotation-key dicts,
    empty = auto-release disabled for all targets
- Admin endpoints in `backend/app/routers/admin.py`:
  - `GET /admin/generation/auto-release/status` — reports `config_enabled`,
    `runtime_disabled`, `effective_enabled`, threshold values, and parsed allowed targets
  - `POST /admin/generation/auto-release/disable` — flips runtime kill switch without restart
  - `POST /admin/generation/auto-release/enable` — re-enables after kill switch
  - `GET /admin/generation/auto-release/audit` — paginated audit log with `days` filter
- `backend/tests/test_auto_release.py` — 28 tests covering `_allowed_targets_list`
  parsing, `_target_matches` matching logic, all gate failure paths in
  `maybe_auto_release`, kill switch endpoints, and audit log endpoint shape/auth.

### Verification

- `uv run pytest tests/test_auto_release.py -v` → `28 passed`.
- Full backend suite: `uv run pytest tests/ -q` → `747 passed, 2 skipped`.

---

## 2026-05-20 — Phase 9: Generation Quality Analytics

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

Implemented the Phase 9 generation quality analytics layer — five read-only admin
endpoints that measure which generator/reviewer model combinations produce the best
student-ready questions.

### Added

- `GET /admin/analytics/generation` — Overall quality metrics for the lookback window:
  `generated_count`, `reviewed_count`, `approved_count`, `rejected_count`,
  `failed_count`, `acceptance_rate`, `copy_risk_failures`,
  `avg_reviewer_disagreement`, acceptance rate broken down by generator
  provider/model, and rejection reason distribution.
- `GET /admin/analytics/review` — Per-reviewer-model metrics: average scores per
  rubric dimension (`realism`, `sat_fidelity`, `difficulty_match`,
  `distractor_quality`, `taxonomy_match`), admin override rate, and token usage
  by provider.
- `GET /admin/analytics/batches` — Batch-level aggregates: requested vs created vs
  approved vs rejected vs failed counts, average review latency (ms), and token
  usage per provider.
- `GET /admin/analytics/trends` — Time-series acceptance rate bucketed by `day` or
  `week`; configurable via `granularity` query param.
- `GET /admin/analytics/export` — Full generated-question export as JSON for offline
  analysis; includes per-question practice status, overlap status, generator
  provider/model, consensus verdict, realism avg, copy risk, and disagreement flag.
- All endpoints accept a `days` query parameter (default 30, max 365) as the lookback
  window. `trends` minimum is 7 days.
- Added analytics payload models to `backend/app/models/payload.py`:
  `GeneratorModelStats`, `ReviewerModelStats`, `BatchAggregates`,
  `TokenUsageByProvider`, `GenerationTrendPoint`, `RejectionReasonCount`,
  `GenerationAnalyticsResponse`, `ReviewAnalyticsResponse`,
  `BatchAnalyticsResponse`, `TrendAnalyticsResponse`.
- Added `backend/tests/test_analytics.py` with 28 tests covering response shape,
  auth enforcement, empty-DB zero values, query parameter validation (bounds,
  invalid granularity), and per-field presence.

### Verification

- `uv run pytest tests/test_analytics.py -v` → `28 passed`.
- Full backend suite: `uv run pytest tests/ -q` → `719 passed, 2 skipped`.

---

## 2026-05-20 — Phase 8: Self-Study Agent Request Layer

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

Implemented the Phase 8 self-study agent layer: weakness profiling, inventory-gated generation requests, and batch status tracking.

### Added

- Added `POST /api/study/recommendations` (`backend/app/routers/student.py`) — read-only
  weakness profile probe returning top-K target recommendations with live inventory counts.
- Added `POST /api/study/generation-requests` — self-study agent main entry point.
  Computes weakness profile, serves existing pool questions per target, and creates
  `GenerationBatch` + `QuestionJob` rows only when inventory is below threshold and all
  rate caps allow. `release_policy` is forced to `admin_review_required` regardless of
  caller input.
- Added `GET /api/study/generation-requests/{batch_id}` — batch status endpoint;
  students can only view their own batches (403 on mismatch).
- Added `_weakness_score` helper implementing the locked formula:
  `miss_rate × exp(-days_since_last / 14) × sqrt(attempt_count)`.
- Added `_compute_weakness_targets` — builds bucketed weakness scores from recent
  `UserProgress` rows, applies top-K=5 cap, and enforces at-most-2-targets-per-focus-key.
  Requires minimum 3 attempts per bucket to qualify.
- Added `_inventory_for_target`, `_pending_batch_exists_for_target`,
  `_target_on_cooldown`, `_daily_gen_count`, `_pending_batch_count`,
  `_on_quality_cooldown` helpers enforcing all seven rate and quality caps.
- Added `_create_self_study_batch` — creates a `GenerationBatch` + `QuestionJob` rows
  and kicks off `_run_batch_pipeline` in a background asyncio task.
- Added `_fetch_pool_questions` — returns active unseen questions for a target
  (student-facing, no answer key).
- Added payload models to `backend/app/models/payload.py`:
  `WeaknessTarget`, `StudyRecommendationsRequest`, `StudyRecommendationsResponse`,
  `StudyGenerationRequest`, `StudyGenerationResponse`, `StudyBatchStatusResponse`.
- Added 11 self-study config knobs to `backend/app/config.py`:
  `self_study_lookback_days` (30), `self_study_recency_half_life_days` (14),
  `self_study_top_k` (5), `self_study_min_attempts_per_target` (3),
  `self_study_min_gen_batch_size` (3), `self_study_target_cooldown_hours` (24),
  `self_study_gen_per_student_per_day` (20), `self_study_max_pending_per_target` (10),
  `self_study_max_pending_batches_per_student` (3),
  `self_study_poor_quality_cooldown_hours` (24), plus `self_study_resurface_days` (30)
  carried over from Phase 7.
- Added migration `025_phase8_self_study.py` (`revision = "025"`, `down_revision = "024"`):
  adds `missed_reading_focus_key`, `missed_reading_skill_family_key`,
  `question_domain`, `question_difficulty` columns to `user_progress` with indexes.
- Auto-populated denormalized `UserProgress` target fields at answer-submit time
  (`POST /api/submit`) from the question's latest annotation JSONB.
- Added `backend/tests/test_self_study.py` with 39 tests covering: weakness score
  formula, bucket computation edge cases, inventory helpers, cooldown/cap helpers,
  all three endpoint shapes, auth enforcement, ownership check (403), and the
  `admin_review_required` force invariant.

### Fixed

- Renamed `024_phase8_self_study.py` → `025_phase8_self_study.py` and updated
  `revision = "025"` / `down_revision = "024"` to resolve a duplicate Alembic head
  collision with `024_phase6_reviewer_admin_overrides.py`. The old file must be deleted.

### Verification

- `uv run pytest tests/test_self_study.py -v` → `39 passed`.
- `uv run alembic heads` → single head `025` (after deleting `024_phase8_self_study.py`).

---

## 2026-05-20 — Phase 7: Student Retrieval API Expansion

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

Implemented the Phase 7 student-facing question retrieval API with full filter coverage and inventory metadata.

### Added

- Added `admin_or_student_required` dependency to `backend/app/auth.py` returning
  `(scope, key)` tuple; used by this endpoint and reserved for Phase 8.
- Rewrote `GET /api/questions` (`backend/app/routers/student.py`) with full filter set:
  `domain`, `difficulty`, `grammar_role_key`, `grammar_focus_key`,
  `reading_skill_family_key`, `reading_focus_key`, `stimulus_mode_key`,
  `origin` (official/generated/mixed), `exclude_seen`, `user_token`, `limit`, `offset`.
- Added `StudentQuestionsListResponse` wrapping `items` and `inventory` metadata block.
- Added `InventoryMetadata` with `matching_target_total`, `matching_unseen`, `served`,
  `includes_generated`, `below_threshold`, `threshold`.
- Extended `StudentQuestionResponse` with `grammar_role_key`, `reading_skill_family_key`,
  `reading_focus_key`. Answer key never exposed.
- Implemented `exclude_seen` resurface logic: correct answers never resurface;
  wrong answers resurface after `self_study_resurface_days` (default 30 days).
- Added `inventory_sufficient_threshold` (default 5) and `self_study_resurface_days`
  (default 30) to `backend/app/config.py`.
- Added `backend/tests/test_student_retrieval.py` with 30 tests covering grammar filters,
  reading filters, difficulty, origin, exclude_seen defaults per scope, resurface logic,
  active-only enforcement, inventory metadata shape, and answer-key exclusion.

### Verification

- Full backend suite: `uv run pytest tests/ -q` → `652 passed, 2 skipped`.

---

## 2026-05-20 — Phase 6: Admin Dashboard Review Queue

**Model:** GPT-5 Codex
**Branch:** `generation_build`

Implemented the Phase 6 generated-question review queue.

### Added

- Added `reviewer_admin_overrides` as an append-only audit table and migration
  (`024_phase6_reviewer_admin_overrides.py`).
- Added generated-question admin list/detail/action endpoints:
  `GET /admin/generated-questions`,
  `GET /admin/generated-questions/{question_id}`,
  approve/reject aliases, and regenerate-from-spec.
- Added reviewer/admin agreement capture on approve/reject. Each click writes
  one `admin_decision_id` shared across override rows for the latest review run.
- Expanded `/dashboard/review` with Phase 6 filters, candidate cards, review
  swarm score tables, source-example comparison, edit controls, approve/reject,
  re-review, regenerate, and pagination.
- Regenerate-from-spec now carries `derived_from_question_id`, reselection of
  source examples, and a per-question attempt cap.
- Added regression coverage for non-destructive rejection and reviewer/admin
  override row creation.

### Verification

- `uv run alembic upgrade head` applied `023 -> 024`.
- Affected suite: `171 passed`.
- Full backend suite: `uv run pytest tests/ -q` → `622 passed, 2 skipped`.

---

## 2026-05-20 — Phase 0–5 generation implementation gap remediation

**Model:** GPT-5 Codex
**Branch:** `generation_build`

Resolved the Phase 0–5 gaps found by comparing `TASKS_GENERATION.md`,
`GENERATION_ARCHITECTURE.md`, `CHANGELOG.md`, and the live implementation.

### Fixes

- Fixed `022_phase3_review_tables.py` so review enum types are created once
  and reused with `create_type=False`; clean migration now reaches Phase 3.
- Fixed `023_phase5_consensus_verdicts.py` so `consensus_verdicts.id` is a
  PostgreSQL UUID, matching the ORM model.
- Aligned consensus with the locked Phase 5 algorithm: unresolved
  `possible`/`confirmed` overlap blocks, fewer than two successful reviewers
  yields `insufficient_reviews`, copy risk rejects at the configured maximum,
  low SAT fidelity rejects, and disagreement combines realism variance with
  verdict diversity.
- Review runs now always write a consensus row, including all-failed review
  swarms.
- Auto-review now runs after clean generated-question save, skips when overlap
  is unresolved, and can be suppressed with `skip_review` for debug/calibration
  batches.
- The review swarm now excludes the generator provider before dispatching
  reviewer calls.
- Added the missing Phase 3 changelog entry for the review rubric, parser,
  prompt loader, review tables, and tests.

### Verification

- `uv run alembic upgrade head` applied `021 -> 022 -> 023` cleanly.
- Full backend suite: `uv run pytest tests/ -q` → `613 passed, 2 skipped`.
- Current Phase 0–5 implementation review has no remaining critical, high, or
  medium severity gaps.

---

## 2026-05-20 — Phase 5: Consensus Gate

**Model:** Claude Opus 4.6
**Branch:** `generation_build`

Implemented the deterministic consensus gate that converts review-swarm
output into admin-facing verdicts.

### New modules

- `backend/app/review/consensus.py` — Consensus computation:
  - `compute_consensus()` — ordered first-match-wins algorithm producing one
    of five verdicts: `blocked_overlap`, `insufficient_reviews`,
    `reject_recommended`, `regenerate_recommended`, `admin_review_ready`
  - `_compute_disagreement()` — realism-score standard deviation combined
    with reviewer verdict diversity
  - `save_consensus()` — async persistence of `ConsensusVerdict` row after
    review swarm completion
- `backend/migrations/versions/023_phase5_consensus_verdicts.py` — migration
  creating `consensus_verdicts` table with `consensus_verdict_enum` PG type

### Verdict algorithm (ordered, first-match-wins)

1. **blocked_overlap** — question has unresolved official overlap (`possible`
   or `confirmed`)
2. **insufficient_reviews** — fewer than two successful reviewer results
3. **reject_recommended** — max copy risk meets/exceeds threshold (>=5.0)
4. **reject_recommended** — average realism below threshold (<7.0)
5. **reject_recommended** — average SAT fidelity below threshold (<7.0)
6. **admin_review_ready** with `high_disagreement_flag=True` — reviewer
   disagreement exceeds threshold (>1.5)
7. **regenerate_recommended** — distractor quality or taxonomy match average
   below threshold
8. **admin_review_ready** — all thresholds cleared

Config thresholds (landed in Phase 3, now consumed by consensus):
`generation_min_realism_score=7.0`, `generation_min_sat_fidelity_score=7.0`,
`generation_min_distractor_quality_score=6.5`,
`generation_min_taxonomy_match_score=7.5`, `generation_max_copy_risk_score=5.0`,
`generation_max_reviewer_disagreement=1.5`.

### Model changes

- `ConsensusVerdict` model added to `db.py` with: `question_id`,
  `review_run_id`, `generation_batch_id`, `reviewer_count`, per-dimension
  averages, `max_copy_risk`, vote counts, `reviewer_disagreement`,
  `high_disagreement_flag`, `consensus_verdict` enum, `reasons_jsonb`.

### Runner integration

- `run_review_swarm()` in `runner.py` now calls `save_consensus()` after
  finalizing the review run status, using the question's `official_overlap_status`
  for the overlap check.

### Tests

- `backend/tests/test_consensus.py` — 20 tests: blocked_overlap,
  insufficient_reviews, reject for high copy risk, reject for low realism,
  reject for low SAT fidelity, disagreement flag, regenerate for below-threshold dimensions,
  admin_review_ready for all-clear, edge cases (failed reviewer exclusion,
  priority of copy risk over realism, blocked overlap overriding perfect
  scores). 613 total tests pass.

---

## 2026-05-20 — Phase 4: Multi-model review runner

**Model:** Claude Opus 4.6
**Branch:** `generation_build`

Implemented the review swarm runner that orchestrates concurrent multi-model
review of generated questions using OpenAI, Claude, and DeepSeek providers.

### New modules

- `backend/app/review/runner.py` — Review swarm orchestrator:
  - `_provider_config()` / `_review_providers()` — maps config to (provider, model) tuples
  - `_load_question_for_review()` — loads question, annotation, options, source examples,
    overlap status, and generation request for the review prompt
  - `_call_review_provider()` — LLM call with `@with_retry` (2 attempts)
  - `_run_single_reviewer()` — runs one provider, parses response via `review/parser.py`,
    persists `LlmReviewResult` with `transient_failed`/`permanent_failed` classification
  - `run_review_swarm()` — creates `ReviewRun`, builds prompt, runs all reviewers
    concurrently with a semaphore (`generation_review_max_concurrent`), finalizes run
    status as `complete`/`partial`/`failed`
  - `run_batch_review_swarm()` — reviews all generated questions in a batch that haven't
    been reviewed yet

### New endpoints

- `POST /admin/questions/{question_id}/review-swarm` — trigger single-question review
- `GET /admin/questions/{question_id}/review-runs` — list all review runs for a question
- `POST /generate/batches/{batch_id}/review-swarm` — trigger batch review

### Tests

- `backend/tests/test_review_runner.py` — 19 tests: provider config, generator
  provider exclusion, swarm success/partial/failure, malformed JSON handling,
  re-review creating new run IDs, batch review, question loading, version
  constants. 613 total tests pass.

---

## 2026-05-20 — Phase 3: Review Swarm Rubric

**Model:** Claude Opus 4.6
**Branch:** `generation_build`

Implemented the stable review-swarm rubric contract for generated-question
quality review.

### Rubric and prompt

- Added `rules_agent_dsat_review_v1.md` with the seven scoring dimensions:
  realism, SAT fidelity, difficulty match, distractor quality, taxonomy match,
  explanation quality, and inverted copy risk.
- Added `backend/app/prompts/review_prompt.py`, which loads the review rubric,
  always includes grammar v7 as the DSAT prose canon, conditionally includes
  reading v2 for reading candidates, and injects question payload, options,
  annotation, source examples, overlap status, and original request metadata.

### Persistence and parsing

- Added `backend/app/review/parser.py` for strict review JSON parsing and score
  validation.
- Added `review_runs` and `llm_review_results` storage through
  `backend/migrations/versions/022_phase3_review_tables.py`.
- Added `ReviewRun` and `LlmReviewResult` ORM models plus review enums in
  `backend/app/models/ontology.py`.

### Tests

- `backend/tests/test_review_parser.py` and
  `backend/tests/test_review_prompt.py` cover valid review JSON, malformed
  output rejection, prompt composition, and rubric/rules version constants.

---

## 2026-05-20 — Phase 2 gap remediation: terminal failures, retry finalization, and candidate boundary

**Model:** GPT-5 Codex
**Branch:** `generation_build`

Closed the Phase 2 gaps found against `TASKS_GENERATION.md` and
`GENERATION_ARCHITECTURE.md`.

### Runner fixes

- `_is_transient_error` now treats provider retry errors, HTTP 429/5xx, network
  timeouts, rate limits, and model-loading messages as transient while keeping
  generic `RuntimeError`, JSON parse failures, and validation failures
  permanent.
- `_run_generate_pipeline` now settles setup/source loading, prompt build,
  generation, annotation, validation, persistence, overlap detection, and YAML
  export failures to terminal job statuses with `validation_errors_jsonb`
  evidence.
- Blocking validation failures now become `failed_permanent` and do not create
  partial `Question` rows. A saved generated item is the candidate boundary for
  later overlap/review/admin release.
- Post-persist failures are locked as `failed_permanent`, and the retry endpoint
  refuses to requeue any failed job that already has a saved `Question` row, so
  retries cannot duplicate saved candidates.
- `_run_batch_job` catches unexpected runner exceptions and still increments the
  right terminal batch counter.
- Retry jobs now run through `_run_retry_batch_job`, which finalizes the batch
  after each retried job settles.
- `retry_failed_batch_jobs` no longer consumes the same SQLAlchemy scalar result
  twice; jobs at or above `GENERATION_JOB_MAX_RETRIES` are locked as
  `failed_permanent`.

### Docs alignment

- Clarified `TASKS_GENERATION.md` and `GENERATION_ARCHITECTURE.md`: valid
  generated outputs become saved candidates; malformed/refused/invalid outputs
  remain terminal `QuestionJob` audit records.

### Tests

- `backend/tests/test_generate_runner.py` expanded from 21 to 30 tests covering
  the new terminal-status, retry-cap, retry-finalization, and coroutine cleanup
  paths.
- Full backend suite: `uv run pytest tests/ -q` -> 531 passed, 2 skipped.

---

## 2026-05-20 — Phase 2 (generation factory): runner, failure classification, batch counters, and retry endpoint

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

Wired the batch runner so batches actually execute. Phase 1 queued `pending` jobs;
Phase 2 dispatches them concurrently, classifies failures, tracks counters atomically,
and exposes a retry endpoint for transient failures.

### Config

- `generation_job_max_retries: int = 3` added to `backend/app/config.py` — caps
  how many times a `failed_transient` job may be retried via the retry endpoint.

### Runner pipeline (`backend/app/routers/generate.py`)

- `_is_transient_error(exc)` — returns `True` for network/provider errors, `False`
  for `ValueError` (JSON parse failure). Drives `failed_transient` vs
  `failed_permanent` status assignment on every failure path in
  `_run_generate_pipeline`.
- `_batch_counter_field(job_status)` — maps terminal job status to the
  `GenerationBatch` column name (`accepted_count`, `needs_review_count`,
  `failed_count`, or `None` for non-terminal).
- `_run_generate_pipeline` return type changed from `None` → `str` (terminal job
  status). Every failure path now returns the status string so orchestrators can
  route to the right counter.
- `created_count` incremented atomically via `sa_update` immediately after a
  question is successfully persisted to the DB (inside `_run_generate_pipeline`,
  guarded by `getattr(job, "generation_batch_id", None)`).
- YAML export moved to execute before the overlap-check branch so it always runs
  when a question is saved, regardless of overlap result.
- Persist failure status changed from `"failed"` → `"failed_permanent"` (DB
  errors after a partial write should not be retried automatically).
- `_update_batch_counters(batch_id, job_status, db)` — atomic `sa_update` to the
  appropriate batch counter column; called by `_run_batch_job` after each job
  terminates.
- `_run_batch_job(job_id, batch_id, request_data, *, is_retry=False)` — opens its
  own `async_session`, optionally marks the job `retrying`, runs the full pipeline,
  and increments the batch counter.
- `_finalize_batch_status(batch_id, db)` — called after all jobs in a batch
  complete; sets `batch.status = "completed"` (any success) or `"failed"` (all
  jobs failed).
- `_run_batch_pipeline(batch_id)` — marks batch `generating`, fetches all `pending`
  jobs, dispatches each as an `asyncio.create_task` wrapped in `run_with_job_limit`,
  gathers all tasks, then calls `_finalize_batch_status`.
- `create_generation_batch` fires `_run_batch_pipeline(batch.id)` via
  `asyncio.create_task` immediately after the endpoint commits so jobs begin
  executing in the background.

### Retry endpoint

- `POST /generate/batches/{batch_id}/retry-failed` — finds all `failed_transient`
  jobs for the batch whose `retry_count < generation_job_max_retries`, decrements
  `batch.failed_count` for each, and re-queues them via `_run_batch_job` with
  `is_retry=True`. Returns `{batch_id, retried_count}`.

### Tests

- `backend/tests/test_generate_runner.py` — 21 new tests covering:
  - `_is_transient_error` and `_batch_counter_field` unit tests
  - `_run_generate_pipeline` classifies `ValueError` as `failed_permanent` and
    `ConnectionError` as `failed_transient`
  - `_finalize_batch_status` sets `completed`/`failed` correctly and is a no-op
    when jobs are still pending or the batch is missing
  - Retry endpoint: 404 for unknown batch, zero-count when no retriable jobs,
    correct count with two jobs queued, max-retries respected, `failed_count`
    decremented
- All 522 non-live tests pass (regression suite clean).

---

## 2026-05-20 — Phase 1 (generation factory): batch contract, idempotency, and architecture note

**Model:** Claude Sonnet 4.6
**Branch:** `generation_build`

Completed all Phase 1 deliverables from `TASKS_GENERATION.md`. The batch
endpoint, persistence layer, idempotency table, config knobs, and validation
model are now fully wired. Phase 2 (runner execution) can attach directly to
the `pending` jobs this endpoint queues.

### Schema

- New table `generation_batches`: stores one row per batch request with
  denormalized counters (`created_count`, `accepted_count`, `rejected_count`,
  `failed_count`, `needs_review_count`), `requested_by`, `student_id`,
  `requested_by_user_token`, `release_policy`, `regenerate_source_batch_id`,
  `status`, and standard timestamps. Indexes on `status`, `student_id`,
  `requested_by_user_token`, `(requested_by, created_at)`.
- New table `generation_batch_idempotency_keys`: maps
  `(idempotency_key, requested_by)` → `generation_batch_id` with a 24h TTL.
  Unique constraint on `(idempotency_key, requested_by)`. Expired rows are
  deleted before each lookup/create so the same key is reusable after TTL.
- `question_jobs` gains three columns: `generation_batch_id` (FK, nullable,
  indexed), `generation_request_jsonb` (durable per-job request snapshot),
  `retry_count` + `last_retry_at` for Phase 2 retry plumbing.
- `questions` gains `is_canonical_source` boolean (default false) for the
  official-source fallback pool.
- `job_status_enum` extended with `failed_transient`, `failed_permanent`,
  `retrying` — needed by Phase 2 runner before it writes those values.
- Migration: `021_phase1_generation_batches.py` (`020 → 021`).

### ORM models

- `backend/app/models/db.py`: `GenerationBatch`, `GenerationBatchIdempotencyKey`
  added; `QuestionJob` updated with new columns; `Question` updated with
  `is_canonical_source`.

### Config (`backend/app/config.py`)

- `generation_max_batch_size` (default 25)
- `generation_default_batch_size` (default 5)
- `generation_max_pending_batches` (default 20)
- `generation_batch_idempotency_ttl_hours` (default 24)

### Request/response models (`backend/app/models/payload.py`)

- `GenerationBatchRequest`: stricter than the legacy `GenerationRequest`.
  Enforces full mandatory-field lists per grammar v7 §B.1.1 and reading v2
  §16.1 including domain-exclusive validation (grammar and reading fields
  cannot be mixed), `very_low` frequency rejection, and conditional fields
  for `transition_logic`, `choose_best_notes_synthesis`, `polarity_fit`,
  `sentence_function`, `command_of_evidence_quantitative`,
  `craft_and_structure`, and `evidence_illustrates_claim`. `release_policy`
  is limited to the locked values: `admin_review_required`,
  `auto_release_on_accept`, and `dry_run`.
- `GenerationBatchResponse`: returns `id`, `status`, `requested_count`,
  `created_at`, `job_ids`, `idempotent_replay`.

### Endpoints (`backend/app/routers/generate.py`)

- `POST /generate/batches`: validates request, checks pending-batch cap,
  validates caller-supplied `source_question_ids` (existence + official-only
  + annotation-backed domain match when annotation exists), persists batch + N
  jobs in `pending` status, writes idempotency key row when `Idempotency-Key`
  header is present.
- `GET /generate/batches/{batch_id}`: returns batch counters and metadata.
- `GET /generate/batches/{batch_id}/questions`: returns job list with
  per-job `question_id` (null until Phase 2 runner populates it).
- `POST /generate/questions` (legacy) remains backward-compatible.

### Contract alignment

- `POST /generate/batches` is admin-only per the locked auth table in
  `TASKS_GENERATION.md`; student-triggered generation remains a Phase 8
  `/api/study/generation-requests` concern.
- Frozen `GenerationBatch.request_jsonb` now includes the derived identity
  fields `requested_by`, `student_id`, and `requested_by_user_token`.
- Each queued `QuestionJob.generation_request_jsonb` now freezes per-job
  `source_question_ids`, provider/model, seed, temperature, retry attempt, and
  derived requester identity at job creation. Caller-supplied source IDs are
  used exactly; omitted source IDs are selected from matched active official
  questions, with canonical official sources as fallback.

### Idempotency

- `Idempotency-Key` header (optional). On hit: deletes expired rows for the
  key first, then returns the original batch with `idempotent_replay=true`.
  On miss: creates batch + key row. Empty/missing header opts out entirely.
  Key is stored only in `generation_batch_idempotency_keys`, never in
  `GenerationBatch.request_jsonb`.

### Architecture documentation

- `GENERATION_ARCHITECTURE.md` (repo root): explains the three-layer design —
  official questions as generation foundation, generated items as candidates,
  review-swarm output as advisory (not admin approval). Also covers rejection
  semantics (`rejected` vs `retired`) and key file references.

### Tests

- `backend/tests/test_generate_batches.py`: 26 tests covering grammar/reading
  complete requests, mandatory-field rejection, `very_low` frequency guard,
  conditional-field guards (`transition_logic`, `polarity_fit`), mixed-domain
  rejection, count cap, idempotency replay, idempotency opt-out, pending-batch
  cap (429), release-policy validation, source-ID validation (invalid UUID,
  unknown ID, non-official ID, annotation-domain mismatch), per-job frozen
  source IDs, GET 404/400 paths, and legacy endpoint backward-compatibility.

### Verification

- `uv run pytest tests/test_generate_batches.py -q` → **26 passed**.
- `uv run pytest tests/test_generate_batches.py tests/test_generate_router.py
  tests/test_backend_regressions.py -q` → **94 passed**.
- `uv run pytest tests/ -q` → **501 passed, 2 skipped**.

---

## 2026-05-19 — Phase 0 (generation factory): non-destructive rejection + payload filter

**Model:** Claude Opus 4.7
**Branch:** `generation_build`

Landed the Phase 0 prerequisites from `TASKS_GENERATION.md` so the
review-swarm and audit-trail features in later phases have a stable
foundation to attach to. No behavior depends on a swarm yet; this is
pure groundwork.

### Schema

- Added `"rejected"` value to the `practice_status_enum` PostgreSQL type
  alongside existing `draft`, `active`, `retired`. `rejected` is the new
  terminal state for failed quality review; `retired` keeps its meaning
  of post-activation removal.
- Added three nullable columns on `questions`: `rejection_reason` (Text),
  `rejected_at` (DateTime tz), `rejected_by_admin_token` (String 128).
- Migration `020_add_rejected_status_and_reason_columns.py` ships both
  changes; uses `autocommit_block()` for the enum extension so the new
  value is visible in the same migration.
- Regenerated `backend/app/models/ontology.py` and the rules-doc VOCAB
  appendices from `vocabulary/master.json` via `scripts/gen_vocab.py
  --generate`.

### Behavior

- `POST /admin/questions/{id}/reject` (`backend/app/routers/admin.py`)
  is now metadata-only. The previous implementation deleted
  `LlmEvaluation`, `QuestionAnnotation`, and `QuestionRelation` rows
  and cleared per-option annotation fields, which would have wiped
  review-swarm data once that data starts accumulating. The new
  endpoint flips `practice_status` to `rejected`, records reason
  (from optional `RejectQuestionRequest.reason`), timestamp, and the
  admin API key. Annotations, options, relations, evaluations, and
  the `latest_annotation_id` pointer are all preserved.
- Hard-delete remains available via `DELETE /admin/questions/{id}`
  for the rare case where physical removal is genuinely needed.

### Generation payload filter

- Expanded `_SOURCE_SET_OPERATIONAL_KEYS` in
  `backend/app/routers/generate.py` from `{provider_name, model_name}`
  to the locked 10-key set (provider/model/seed/temperature,
  retry_attempt/idempotency_key, requested_count/requested_by/
  student_id/requested_by_user_token/release_policy).
- Deduplicated the constant: `_generation_profile_payload` no longer
  carries its own private copy.
- `idempotency_key` is included as defense-in-depth even though the
  locked design also keeps it out of the request payload by storing it
  in a separate table.

### Tests

- `test_admin_reject_is_non_destructive`: asserts no SQL DELETE/SELECT
  is issued against linked tables during rejection, and that
  `latest_annotation_id` is preserved.
- `test_admin_reject_accepts_empty_body`: dashboard's existing
  no-body POST still works.
- `test_source_set_operational_keys_filter_strips_all_operational`:
  snapshot test of the exact 10-key set plus the lineage-survives
  identity invariant.
- Updated `test_generate_pipeline_flushes_before_wiring_latest_pointers`
  to use a lineage key instead of `seed` (which is now correctly
  classified as operational and stripped from
  `generation_profile_jsonb`).

### Verification

- Migration applies cleanly: `alembic upgrade head` → `019 -> 020`.
- Live DB enum: `{draft, active, retired, rejected}`.
- Live DB columns on `questions`: `rejection_reason`, `rejected_at`,
  `rejected_by_admin_token` present.
- Full backend suite: `uv run pytest tests/ -q` → `475 passed,
  2 skipped`.

---

## 2026-05-20 — Generation overlap status completion fix

**Model:** GPT-5 Codex
**Branch:** `generation_build`

Fixed a generation run-status bug where saved generated questions could leave
their job stuck in `overlap_checking` after official-overlap detection finished.

### Fix

- Generation jobs now return to `approved` when no official overlap is found.
- Generation jobs now move to `needs_review` when possible official overlap is
  found, with a review-severity validation entry explaining the overlap risk.
- Added regression tests for both clear-overlap and possible-overlap generation
  paths.

### Verification

- Focused status tests: `3 passed`.
- Generation/regression suite: `90 passed`.
- Full backend suite: `uv run pytest tests/ -q` → `472 passed, 2 skipped`.

---

## 2026-05-20 — Generation nested payload flattening fix

**Model:** GPT-5 Codex
**Branch:** `generation_build`

Fixed a generation pipeline schema mismatch where strong model output could
nest the generated question under `pass1_json.question`, leaving
`question_text`, `correct_option_label`, and options unavailable at the top
level for validation and persistence.

### Fix

- Added Pass 1 generation normalization so nested fields such as
  `question.prompt_text`, `question.correct_option_label`, and
  `question.options` are flattened before validation, annotation, persistence,
  overlap detection, and YAML export.
- Preserved the original nested `question` object in `pass1_json` for
  traceability.
- Added a regression test covering the nested `question.prompt_text` payload
  shape from source-backed generation.

### Verification

- Targeted regression: `1 passed`.
- Generation/regression suite: `89 passed`.
- Full backend suite: `uv run pytest tests/ -q` → `471 passed, 2 skipped`.

---

## 2026-05-20 — Important: generation request contract supports reading and grammar

**Model:** GPT-5 Codex
**Branch:** `generation_build`

Expanded the generation request path so generated DSAT questions can be
targeted by either grammar or reading taxonomy while continuing to use the two
rule markdown sources that produced the strongest independent generation
results.

### Important

- `GenerationRequest` and `GenerationCompareRequest` now accept complete grammar
  targets or complete reading targets.
- Generation prompts now always include both `rules_agent_dsat_grammar_ingestion_generation_v7.md`
  and `rules_agent_dsat_reading_v2.md`.
- When `source_question_ids` are supplied, stored official questions,
  annotations, and options are loaded into the generation prompt as foundational
  source examples for style, taxonomy, passage architecture, distractor
  construction, and difficulty calibration.
- The dashboard generation form now supports reading-target fields instead of
  forcing grammar-only inputs.

### Verification

- Full backend suite: `uv run pytest tests/ -q` → `470 passed, 2 skipped`.

---

## 2026-05-18 — Phase 8 end-to-end hardening bug remediation

**Model:** Claude Opus 4.7
**Branch:** `main`

Validated the 12 findings in the `DEBUG_LOG.md` Phase 8 end-to-end hardening
review against the current working tree and resolved each.

### Fixes

- Added real-filesystem integration tests for the admin amendment promote
  endpoints — the genuine `amendment_review` implementation now runs against
  tmp dirs instead of canned mocks.
- Promotion tests now verify regenerated master.json/doc content and the
  amendment file's failure-state routing to `needs_manual_patch/`.
- `_FakeDb` in the capture tests now honors query filtering; added a test that
  jobs failing the query predicate are skipped.
- Added a 12-thread concurrent-write test for `_link_candidate` file locking.
- `scripts/amendments.py` now validates and resolves `--repo-root` rather than
  trusting the script's `__file__` location.
- Added a full capture → approve → promote → re-appraisal end-to-end test.
- `test_amendments_cli.py` now monkeypatches `amendment_review.REPO_ROOT`.

### Verdicts (no change)

- Finding 1 was already resolved by the Phase 7 fix (re-appraisal runs outside
  the promotion try/except).
- Findings 3, 9, 10 judged by-design: error codes are already split correctly
  (422 validation vs 409 conflict), and the `issubset`/SQL-substring test
  assertions are intentional forward-compat smoke checks.

### Verification

- Target suite: `65 passed` (+5 new tests).
- Related suites (`test_ingestion_analysis.py`, `test_rule_doc_patcher.py`,
  `test_pipeline.py`, `test_backend_regressions.py`): `110 passed`.

---

## 2026-05-18 — Phase 8 end-to-end hardening audit

**Model:** Claude Opus 4.7
**Branch:** `main`

Closed out Phase 8 of the rules-update workflow. Phase 8 is a verification
exercise — every line item was already built incrementally during Phases 2–7
and their bug-remediation passes — so this audit mapped each item to its
existing test(s), confirmed no gaps, and ran the full gate.

### Audit result

- All 10 Phase 8 test items and all 7 Acceptance Criteria are covered by
  existing tests; each checkbox in `TASKS_RULES_UPDATE_FEATURE.md` now cites
  the specific test(s) that satisfy it.
- `python scripts/gen_vocab.py --check` → `vocabulary in sync`.
- `uv run pytest` → `441 passed, 2 skipped`. The 4 collection errors are
  pre-existing in `backend/test_ocr_live.py` (a standalone live-OCR script with
  a missing `image` fixture), unrelated to the rules-update feature.

All eight phases (0–8) of the approval-gated rules-update workflow are complete.

---

## 2026-05-18 — Phase 7 ingestion analysis bug remediation

**Model:** Claude Opus 4.7
**Branch:** `main`

Validated the 10 findings in the `DEBUG_LOG.md` Phase 7 ingestion-analysis
review against current code and fixed the genuine defects.

### Fixes

- Moved `write_reappraisals_for_master_growth` outside `promote_amendment`'s
  rollback try/except so a re-appraisal IO failure can no longer roll back an
  already-committed promotion. Re-appraisal now runs best-effort after commit
  and logs a warning on failure (added `logging` + module logger to
  `amendment_review.py`).
- `write_ingestion_analysis` now skips question markdown files for records with
  no taxonomy fields and no question text, so pass1-fallback rows no longer
  emit empty `# Question` stubs (`_has_question_content` helper).
- `_amendment_candidates` now falls back to the shared `extract_amendment_proposal`,
  capturing the legacy top-level `amendment_proposal` key it previously missed.
- `write_reappraisals_for_master_growth` now uses `rglob` instead of a
  fixed-depth `glob("*/*/...")` pattern.
- `_exam_code` reads `source_metadata` once instead of twice.

### Verdicts (not defects)

- Hashes-in-DB: the spec requires hashes in every ingestion *analysis report*,
  which is satisfied; a `QuestionJob` column is scope expansion.
- Richer `summary.md` per-question detail: usability enhancement, deferred.
- Best-effort `except Exception` around analysis writing in `ingest.py`: by
  design — analysis writing must not fail an ingestion; it is logged.

### Verification

- Added `test_reappraisal_markdown_records_exam_and_hash_comparison`,
  `test_question_records_falls_back_to_pass1_questions`,
  `test_question_records_handles_single_question_pass2_without_annotations`,
  `test_question_records_handles_empty_annotations_list`,
  `test_empty_question_records_do_not_emit_stub_files`, and
  `test_amendment_candidates_captures_legacy_top_level_proposal`.
- Verified with:
  `uv run pytest tests/test_ingestion_analysis.py tests/test_amendment_review.py
  tests/test_amendments_cli.py tests/test_amendments.py tests/test_amendment_capture.py
  tests/test_pipeline.py tests/test_backend_regressions.py tests/test_rule_doc_patcher.py -q`
  (`146 passed`).

---

## 2026-05-18 — Rules update workflow Phase 7 ingestion analysis reports

**Model:** GPT-5 Codex
**Branch:** `main`

Implemented reproducible official ingestion analysis reports and vocabulary
growth re-appraisal records.

### Reports

- Added `app.pipeline.ingestion_analysis` to write immutable report folders under
  `analysis/ingestion/<exam>/run_<date>_<job-id>/`.
- Reports include `summary.md`, `taxonomy_coverage.json`,
  `validation_failures.json`, `amendment_candidates.json`, and per-question
  markdown files.
- Each report stores `master_json_hash`, `reading_rules_hash`,
  `grammar_rules_hash`, and `ontology_hash`.
- Official ingest completion now attempts to write an analysis report; generated
  and unofficial jobs are skipped.
- Amendment promotion now creates `reappraisal_<master_hash>.md` files for prior
  official analyses whose stored master hash is older than the current
  `master.json`.
- Marked Phase 7 complete in `TASKS_RULES_UPDATE_FEATURE.md`.

### Verification

- Added tests for report layout, official-only behavior, hash recording,
  re-appraisal creation after `master_json_hash` changes, and the promotion hook.
- Verified with:
  `uv run pytest tests/test_ingestion_analysis.py tests/test_amendment_review.py tests/test_amendments_cli.py tests/test_vocab_consistency.py tests/test_pipeline.py tests/test_backend_regressions.py -q`
  (`119 passed`).

---

## 2026-05-18 — Phase 6 consistency scanner bug remediation

**Model:** GPT-5 Codex
**Branch:** `main`

Fixed the Phase 6 consistency scanner issues recorded in `DEBUG_LOG.md`.

### Fixes

- Updated reading-shape checks to honor both `skill_family_key` and
  `reading_skill_family_key`.
- Consolidated shared field-to-vocabulary mappings in `app.models.vocab_fields`
  and wired amendment capture, candidate capture, and the scanner through it.
- Changed DB collection to async streaming with `yield_per` instead of loading
  all rows at once.
- Added reverse domain checks for grammar-domain records that carry reading
  skill/focus keys.
- Made `--no-fail` severity-aware: non-blocking findings can exit 0, but
  blocking findings still fail.
- Derived hierarchical parent mismatch checks from `master.json` parent-set
  metadata, with alias support for known parent fields.

### Verification

- Added regression coverage for alias-based shape checks, shared mapping reuse,
  dynamic parent mappings, reverse domain mismatch, severity-aware exit codes,
  and async DB collection.
- Verified scanner execution with:
  `uv run python ../scripts/check_vocab_consistency.py --exports ../analysis --json --no-fail`
  (`ok: true`).
- Verified with:
  `uv run pytest tests/test_vocab_consistency.py tests/test_vocab_sync.py tests/test_pipeline.py tests/test_amendments_cli.py tests/test_amendment_capture.py tests/test_amendment_review.py -q`
  (`82 passed`).

---

## 2026-05-18 — Rules update workflow Phase 6 vocabulary consistency scanner

**Model:** GPT-5 Codex
**Branch:** `main`

Implemented the Phase 6 scanner for checking persisted DB/JSONB data and
generated exports against the active compiled vocabulary in `master.json`.

### Scanner

- Added `scripts/check_vocab_consistency.py` with `--all`, `--db`, `--exports`,
  `--json`, and `--no-fail` options.
- Scanner inspects `question_jobs.pass1_json`, `question_jobs.pass2_json`,
  `question_jobs.validation_errors_jsonb`, `question_annotations` JSONB fields,
  `question_options`, and JSON/YAML export files.
- Reports unknown keys, deprecated keys, wrong hierarchical parents,
  reading-domain items with grammar keys, Cross-Text items missing
  `prose_paired`/paired passage data, and quantitative evidence items missing
  table/graph stimulus data.
- Marked Phase 6 complete in `TASKS_RULES_UPDATE_FEATURE.md`.

### Verification

- Added fixture tests for every required scanner error type, option-row scanning,
  machine-readable JSON reports, and JSON/YAML export loading.
- Verified scanner execution with:
  `uv run python ../scripts/check_vocab_consistency.py --exports ../analysis --json --no-fail`
  (`ok: true`).
- Verified with:
  `uv run pytest tests/test_vocab_consistency.py tests/test_vocab_sync.py tests/test_pipeline.py tests/test_amendments_cli.py -q`
  (`57 passed`).

---

## 2026-05-18 — Phase 5 dev CLI bug remediation

**Model:** GPT-5 Codex
**Branch:** `main`

Fixed the Phase 5 dev CLI issues recorded in `DEBUG_LOG.md`.

### Fixes

- Added `--repo-root` to `scripts/gen_vocab.py` so
  `--promote-from-amendment` can operate against non-default repo roots without
  monkeypatching globals.
- Split the CLI transition tests so request-more-evidence, approve, and reject
  each run from an appropriate starting amendment state.
- Added explicit successful-promotion output confirming ontology.py and VOCAB
  appendices were regenerated from `master.json`.

### Verification

- Verified with:
  `uv run pytest tests/test_amendments_cli.py tests/test_vocab_sync.py tests/test_amendment_review.py tests/test_rule_doc_patcher.py -q`
  (`36 passed`).

---

## 2026-05-18 — Rules update workflow Phase 5 dev CLI

**Model:** GPT-5 Codex
**Branch:** `main`

Implemented the local development CLI for the approval-gated amendment workflow.

### CLI

- Added `scripts/amendments.py` with `list`, `show`, `approve`, `reject`,
  `request-more-evidence`, and `promote` commands.
- Wired all CLI commands to the shared `app.pipeline.amendment_review` service
  used by the admin API, so local development cannot bypass approval gates.
- Added `scripts/gen_vocab.py --promote-from-amendment AMENDMENT_ID` as the
  approved promotion path while keeping legacy `--promote` fenced behind
  `--unsafe-direct-promote`.
- Marked Phase 5 complete in `TASKS_RULES_UPDATE_FEATURE.md`.

### Verification

- Added CLI tests for list/show/approval/rejection/request-more-evidence,
  promotion, blocked unapproved promotion, and `gen_vocab.py`
  `--promote-from-amendment`.
- Verified with:
  `uv run pytest tests/test_amendments_cli.py tests/test_amendment_review.py tests/test_admin_router.py tests/test_rule_doc_patcher.py tests/test_amendments.py tests/test_vocab_sync.py -q`
  (`56 passed`).

---

## 2026-05-18 — Phase 4 admin review API bug remediation

**Model:** GPT-5 Codex
**Branch:** `main`

Fixed the Phase 4 admin review API issues recorded in `DEBUG_LOG.md`.

### Fixes

- Added explicit amendment status-transition guards for approve, reject, request
  more evidence, and promote operations.
- Blocked promotion of approved-status files found outside the pending review
  directory.
- Added `error_code` classification to amendment operation results and mapped
  API failures to clearer HTTP statuses: 404 for missing amendments, 422 for
  validation failures, and 409 for conflicts.
- Added `apply_loaded_rule_doc_patch` so promotion uses the already-loaded
  amendment object instead of re-reading the file mid-operation.

### Verification

- Added service-level tests for reject and request-more-evidence behavior,
  invalid status transitions, promotion directory validation, and rollback after
  regeneration failure.
- Added API coverage for amendment validation failures returning 422.
- Verified with:
  `uv run pytest tests/test_amendment_review.py tests/test_admin_router.py tests/test_rule_doc_patcher.py tests/test_amendments.py -q`
  (`44 passed`).

---

## 2026-05-18 — Rules update workflow Phase 4 admin review API

**Model:** GPT-5 Codex
**Branch:** `main`

Implemented the admin-facing amendment review and promotion workflow.

### Admin API

- Added `GET /admin/amendments` and `GET /admin/amendments/{id}` for review
  queue listing and amendment detail.
- Added `POST /admin/amendments/{id}/approve`, `/reject`,
  `/request-more-evidence`, and `/promote`.
- Added shared `app.pipeline.amendment_review` service code so Phase 5 CLI work
  can reuse the same approval and promotion gates.

### Promotion Gates

- Approval validates official-source schema, clean rule-doc dry-run, candidate
  linkage or candidate creation, inactive proposed key, and hierarchical parent
  validity.
- Promotion requires an approved amendment, adds the active key to
  `vocabulary/master.json`, applies the rule-doc body patch, regenerates
  ontology/VOCAB appendices through the existing generator path, moves the file
  into `vocabulary/amendments/approved/`, and records promotion metadata.
- Marked Phase 4 complete in `TASKS_RULES_UPDATE_FEATURE.md`.

### Verification

- Added service tests for approval validation, candidate creation, blocked
  duplicate active keys, guarded promotion, master/doc mutation, regeneration,
  and approved-file movement.
- Added API tests for list/show/approve/reject/request-more-evidence/promote.
- Verified with:
  `uv run pytest tests/test_amendment_review.py tests/test_admin_router.py tests/test_rule_doc_patcher.py tests/test_amendments.py -q`
  (`36 passed`).

---

## 2026-05-18 — Phase 3 rule-doc patcher bug remediation

**Model:** GPT-5 Codex
**Branch:** `main`

Fixed the Phase 3 rule-doc patch engine issues recorded in `DEBUG_LOG.md`.

### Fixes

- Made generated VOCAB block detection parse matching START/END markers so
  editable body text immediately after an END marker is no longer treated as
  generated appendix content.
- Replaced the bare `assert result.doc_path is not None` with an explicit
  failure path that marks the amendment `needs_manual_patch` and preserves
  conflict details.
- Made appendix regeneration opt-in for `apply_rule_doc_patch`; guarded the
  opt-in path so regeneration cannot run until the amendment value is active in
  `vocabulary/master.json`.

### Verification

- Added regression tests for ambiguous body anchors, generated-block boundary
  handling, missing document-path results, default no-regeneration behavior, and
  guarded appendix regeneration.
- Verified with `uv run pytest tests/test_rule_doc_patcher.py -q`
  (`10 passed`).

---

## 2026-05-18 — Rules update workflow Phase 3 rule-doc patch engine

**Model:** GPT-5 Codex
**Branch:** `main`

Implemented the shared rule-document body patch engine needed before admin API
or CLI promotion can safely update `master.json`.

### Patch Engine

- Added `backend/app/pipeline/rule_doc_patcher.py` with dry-run and apply
  support for amendment `rule_doc_patch` payloads targeting:
  - `rules_agent_dsat_reading_v2.md`
  - `rules_agent_dsat_grammar_ingestion_generation_v7.md`
- Patch dry-runs return unified diffs for reviewer/admin display without writing
  files.
- Patch application performs exact body-anchor replacement. Generated appendix
  regeneration is handled by the guarded promotion flow after `master.json`
  contains the approved amendment value.
- Generated VOCAB appendix blocks are protected: patches targeting or anchoring
  inside `<!-- VOCAB:... -->` blocks are rejected.
- Patch failures move amendment files to
  `vocabulary/amendments/needs_manual_patch/`, set status to
  `needs_manual_patch`, and write conflict details into `review_notes`.

### Verification

- Added tests for dry-run diffs, successful body patching, generated VOCAB block
  rejection, missing-section rejection, and `needs_manual_patch` failure
  handling.
- Verified with `uv run python scripts/gen_vocab.py --check`
  (`vocabulary in sync`).
- Verified with:
  `uv run pytest tests/test_pipeline.py tests/test_backend_regressions.py tests/test_amendments.py tests/test_amendment_capture.py tests/test_rule_doc_patcher.py tests/test_prompts.py tests/test_vocab_sync.py tests/test_ontology.py`
  (`136 passed`).

---

## 2026-05-18 — Rules update workflow Phase 0 governance baseline

**Model:** GPT-5 Codex
**Branch:** `main`

Closed the direct vocabulary-promotion governance gap before implementing the
rule-doc patch engine. `master.json` is now documented as the compiled
enforcement manifest after approved rule amendments, not the casual authoring
surface for new taxonomy rules.

### Governance

- Updated `scripts/gen_vocab.py` docs and CLI help to distinguish regeneration,
  candidate review, and approved-amendment promotion.
- Blocked legacy `scripts/gen_vocab.py --promote VOCAB VALUE` by default.
  Direct promotion now requires the explicit development-only
  `--unsafe-direct-promote` flag.
- Added `docs/backend/VOCABULARY_GOVERNANCE.md` documenting the invariant:
  rule-doc body approval comes before active vocabulary growth.
- Marked Phase 0 complete in `TASKS_RULES_UPDATE_FEATURE.md`.

### Verification

- Added regression coverage proving unapproved direct promotion cannot mutate
  `master.json`; the explicit unsafe escape hatch remains available for isolated
  development.

---

## 2026-05-18 — Rename plausibility-source vocabulary constant

**Model:** GPT-5 Codex
**Branch:** `main`

Renamed the misspelled internal vocabulary constant
`PLANSIBILITY_SOURCE_KEYS` to `PLAUSIBILITY_SOURCE_KEYS` across the active
vocabulary source, generated artifacts, validation code, amendment/candidate
maps, and tests. The external field name remains unchanged:
`plausibility_source_key`.

### Fixes

- Updated `vocabulary/master.json` and `scripts/gen_vocab.py` to use
  `PLAUSIBILITY_SOURCE_KEYS`.
- Regenerated `backend/app/models/ontology.py` and both rules-doc VOCAB
  appendices from the corrected vocabulary name.
- Updated option validation, vocabulary candidate capture, amendment proposal
  capture, and ontology tests to import/map the corrected constant.
- Removed stale generated `PLANSIBILITY_SOURCE_KEYS` appendix blocks left behind
  by the marker rename.

### Verification

- Verified vocabulary artifacts with `uv run python scripts/gen_vocab.py --check`
  (`vocabulary in sync`).

---

## 2026-05-18 — Phase 2 amendment capture medium-bug remediation

**Model:** GPT-5 Codex
**Branch:** `main`

Resolved the medium-severity issues from the `DEBUG_LOG.md` Phase 2 amendment
capture review and followed the affected code paths through ingest finalization,
candidate linking, amendment deduplication, vocabulary field mapping, and tests.

### Fixes

- Preserved job-level Pass 2 annotation data during normal ingest finalization.
  Single-question jobs now keep the flat annotation payload in `job.pass2_json`
  alongside `_pass2_meta` and `_amendment_proposals`; multi-question jobs retain
  per-question annotations under `_annotations`.
- Added locked read-modify-write behavior when linking amendment IDs back into
  `vocabulary/candidates.json`, matching the concurrency guard used by the
  candidate recorder.
- Kept conflicting duplicate amendment proposal body fields visible to reviewers.
  Duplicate proposals still merge supporting examples by stable amendment ID, but
  conflicting definitions, rationale, rule-doc patches, and master-json patches
  are now captured in `review_notes`.
- Completed the directly affected field map chain by adding
  `syntactic_trap_key -> SYNTACTIC_TRAP_KEYS` and
  `transition_subtype_key -> TRANSITION_SUBTYPE_KEYS` to both amendment capture
  and vocabulary candidate mapping.

### Verification

- Added regressions for preserved single-question `pass2_json`, duplicate proposal
  conflict notes, and the new ontology field mappings.
- Verified with:
  `uv run pytest tests/test_pipeline.py tests/test_backend_regressions.py tests/test_amendments.py tests/test_amendment_capture.py tests/test_prompts.py tests/test_vocab_sync.py`
  (`117 passed`).

---

## 2026-05-18 — Rules update workflow Phase 2 completion

**Model:** GPT-5 Codex
**Branch:** `main`

Completed the missing Phase 2 pieces for approval-gated rule amendment capture.
Official Pass 2 annotations can now emit reviewable amendment proposals without
allowing proposed keys into production annotation fields, and completed jobs can
be replayed for pending amendment-file creation.

### Amendment capture

- Added completed-job backfill helpers in `backend/app/pipeline/amendments.py`
  to scan completed official ingest jobs and capture pending amendment files
  from `pass2_json.reasoning.amendment_proposal`.
- Added multi-question replay support through `pass2_json["_amendment_proposals"]`
  so normal ingest runs preserve enough proposal metadata for later review.
- Non-official and generated amendment proposals are now dropped with durable
  warning records on `validation_errors_jsonb`, not only logger output.
- Normal ingest now stores amendment proposal metadata alongside Pass 2 LLM
  metadata while preserving existing warning records during final job status
  cleanup.

### Verification

- Added tests for official proposal capture, non-official warning persistence,
  multi-question replay, completed-job scanning, deduplication, and candidate
  linkage.
- Verified with:
  `uv run pytest tests/test_pipeline.py tests/test_backend_regressions.py tests/test_amendments.py tests/test_amendment_capture.py tests/test_prompts.py tests/test_vocab_sync.py`
  (`115 passed`).

---

## 2026-05-18 — Master vocabulary file: single source of truth + review queue

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

The controlled vocabulary was hand-maintained in three places — `ontology.py`,
`rules_agent_dsat_reading_v2.md`, and the grammar v7 doc — which kept drifting
out of sync (the bug class behind Test 4 q6/q7). This change makes one file the
source of truth and adds a non-blocking growth path for keys the LLM invents.

### Source of truth

- **New `vocabulary/master.json`** — canonical home of all 41 controlled
  vocabularies (599 entries), each tagged with domain, status
  (`active`/`candidate`/`deprecated`), and `added` date. Hierarchical
  vocabularies (`GRAMMAR_FOCUS_BY_ROLE`, `READING_FOCUS_BY_SKILL_FAMILY`) carry
  a `parent`.
- **New `scripts/gen_vocab.py`** — regenerates `ontology.py` and the rules-doc
  `<!-- VOCAB:... -->` appendix blocks from master.json. `--bootstrap` seeded
  master.json from the existing ontology.py (verified: every constant
  round-trips identically). `--generate` is the edit workflow; `--check` is the
  drift gate.
- **`ontology.py` is now a generated artefact** — header says so; edits go to
  master.json.

### Review queue (non-blocking vocabulary growth)

- **New `backend/app/models/vocab_candidates.py`** — when the pipeline meets a
  key not yet in the vocabulary it records it in `vocabulary/candidates.json`
  (job id, occurrences, context) instead of dropping or hard-failing it. Writes
  are `fcntl`-locked because Pass-2 annotation runs concurrently.
- **`validator.py`** records unknown question-level keys; signature gained an
  optional `job_id`.
- **`options.py`** — the `distractor_type_key`, `plausibility_source_key`, and
  `student_failure_mode_key` validators no longer `raise ValueError` on an
  unknown key; they record a candidate and keep the value so the question still
  ingests. `distractor_distance` (a fixed micro-enum) still hard-rejects.
- **`gen_vocab.py --list-candidates / --promote / --reject`** — review the
  queue and promote real keys into master.json (promotion auto-regenerates).

### Propagation & CI

- Both rules docs gained an `Appendix V — Controlled Vocabulary (generated)`
  section with one fenced VOCAB block per vocabulary, regenerated in lockstep.
- `backend/tests/test_vocab_sync.py` runs `gen_vocab.py --check` as the drift
  gate (the repo has no separate CI runner) and covers candidate recording,
  dedup, and the non-blocking option behaviour.

---

## 2026-05-18 — Controlled-vocabulary reconciliation (ontology ↔ rules docs)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

A full cross-reference audit of `backend/app/models/ontology.py` against
`rules_agent_dsat_reading_v2.md` and
`rules_agent_dsat_grammar_ingestion_generation_v7.md` found two controlled
vocabularies still desynced — the same class of bug that blocked Test 4 q6/q7.
LLM-emittable keys were missing from the validator enums, so any question
carrying them failed at the `validating` step.

### Ontology

- **`STUDENT_FAILURE_MODE_KEYS` extended 46 → 63 keys.** Added the 16
  grammar-specific `student_failure_mode_key` values from grammar_v7 §D.7 (e.g.
  `transition_wrong_direction`, `nonfinite_for_finite`,
  `notes_synthesis_wrong_goal`), plus `tense_proximity_pull` and reading_v2 §19's
  approved synonym `polarity_blindness`. `student_failure_mode_key` is mandatory
  on every distractor and hard-validated at `options.py:42-46`.
- **New `REASONING_TRAP_KEYS` set (49 keys).** A dedicated controlled vocabulary
  for the question-level `reasoning_trap_key` field, distinct from
  `DISTRACTOR_TYPE_KEYS` (the option-level §12.1 list).

### Validation

- Added a `reasoning_trap_key` `@field_validator` to `QuestionAnnotation`
  (`annotation.py`) — previously an unvalidated free-text field.
- `annotate_prompt.py` ALLOWED KEY VALUES block now lists `reasoning_trap_key`'s
  vocabulary, with an explicit note not to use the §12.1 `distractor_type_key`
  list for it.

### Rules docs

- **reading_v2 §10 deduplicated:** `wrong_row_or_column`,
  `individual_from_aggregate`, and `all_measures_not_checked` merged into
  `wrong_table_row_or_column`, `individual_inference_from_aggregate_bins`, and
  `single_measure_focus`.
- reading_v2 §10 intro rewritten to state §10 governs `reasoning_trap_key`
  (question-level) and §12.1 governs `distractor_type_key` (option-level) — the
  two vocabularies overlap but are not interchangeable.

### Deferred

- Generate-side `target_reasoning_trap_key` lives in untyped `generation_profile`
  JSONB (`payload.py:42`) and cannot be validated until the profile is typed;
  `REASONING_TRAP_KEYS` is ready for that change.

---

## 2026-05-16 — Apply pending DB migrations (017, 018)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

The `dsat_dev` database was stranded at migration `016` while the codebase
expected `018`. The pipeline's per-question persist (`ingest.py`) inserts a
`QuestionJobQuestion` row into the `question_job_questions` table created by
migration `017`; with that table absent, every persist raised inside its
`begin_nested()` savepoint and rolled back — so no question could ever land in
the DB. Ran `alembic upgrade head`.

### Database

- **Migration 017 applied:** `question_job_questions` junction table created
  (job↔question link with `ix_qjq_job_id` / `ix_qjq_question_id` indexes).
- **Migration 018 applied:** `user_token` UUID column added to `users` (unique,
  indexed, backfilled).
- DB revision advanced `016` → `018 (head)`.

---

## 2026-05-16 — Full gap remediation (15 fixes across all audit findings)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Resolves 15 open audit findings across ingestion, generation, admin, and cross-cutting
areas. Two items (OCR integration tests and stub-DB migration) are deferred as they
require significant new test infrastructure.

### Ingestion Pipeline

- **OCR fallback logging:** Added explicit `logger.info` calls at OCR chain entry,
  each fallback transition, and paradigm-specific success messages (two-step vs
  VLM-fused). Previously only failure warnings were logged.
  **Files:** `backend/app/routers/ingest.py`

- **Per-page render size limit:** Added `MAX_PAGE_RENDER_BYTES = 10 MB` in ingest.py;
  `_store_page_render` now returns `None` for oversized pages (with warning log).
  `_store_pdf_page_renders` filters out `None`. Added `MAX_RENDER_DIMENSION = 3000px`
  in `pdf_parser.py` to cap rendered page dimensions.
  **Files:** `backend/app/routers/ingest.py`, `backend/app/parsers/pdf_parser.py`

- **Mixed PDF page-level OCR:** The OCR gate now checks per-page text availability.
  When a PDF has some text-layer pages and some blank/scanned pages, only the blank
  pages' images are sent through OCR. The OCR text is appended to the existing raw text.
  `_page_texts` is stored in `pass1_json` for per-page text inspection.
  **Files:** `backend/app/routers/ingest.py`

- **Job endpoint exposes OCR/LLM metadata:** `GET /ingest/jobs/{job_id}` now returns
  `ocr_meta` and `llm_meta` extracted from `pass1_json`.
  **Files:** `backend/app/models/payload.py`, `backend/app/routers/ingest.py`

### Generate Pipeline

- **`generate_compare` shared reference fix:** Each provider closure in
  `generate_compare` now receives `job_data = dict(request_data)` — a shallow copy — so
  mutations inside `_run_generate_pipeline` don't leak across jobs. The default-arg
  pattern is documented inline.
  **Files:** `backend/app/routers/generate.py`

- **Overlap race condition:** `persist_overlap_relations` now wraps each
  check-then-insert in `async with db.begin_nested()` (SAVEPOINT) and catches
  `IntegrityError` on concurrent duplicate inserts.
  **Files:** `backend/app/pipeline/overlap.py`

- **`overlap_checking` status in generate pipeline:** Added `job.status =
  "overlap_checking"` before running overlap detection in
  `_run_generate_pipeline`, matching the ingest pipeline behavior.
  **Files:** `backend/app/routers/generate.py`

- **Generation run diagnostics:** `GET /generate/runs/{run_id}` now returns
  `validation_errors`, `pass1_json`, and `pass2_json` for single-job responses,
  and `validation_errors` per job in comparison-group responses.
  **Files:** `backend/app/routers/generate.py`

- **`generation_source_set` pollution fix:** `generation_source_set` on the `Question`
  model now filters out `_SOURCE_SET_OPERATIONAL_KEYS` (`provider_name`, `model_name`)
  from the stored dict, matching the behavior of `_generation_profile_payload`.
  **Files:** `backend/app/routers/generate.py`

### Admin / Cross-Cutting

- **`LlmEvaluation.job_id` nullable fix:** Changed `EvaluationCreateRequest.job_id`
  from `str` to `Optional[str] = None` so an empty string no longer causes a 500
  on the `nullable=False` column.
  **Files:** `backend/app/routers/admin.py`

- **Official question activation:** Removed the blanket block on approving
  `content_origin == "official"` questions. Official questions can now be approved
  unless they have unresolved overlap (`official_overlap_status != "none"`).
  **Files:** `backend/app/routers/admin.py`

- **Student submit option verification:** Added a check that the submitted
  `selected_option_label` exists in `question_options` for the question's
  `latest_version_id` before recording the answer.
  **Files:** `backend/app/routers/student.py`

- **Consolidated user routes:** Removed duplicate user-management endpoints from
  `student.py` (`POST/GET/DELETE /api/users`). The canonical endpoints in `users.py`
  (`/users`) now serve all user CRUD with proper pagination, status codes (201/204),
  and explicit timestamps. Unused imports (`delete`, `admin_required`, `UserCreate`,
  `UserResponse`) removed from `student.py`.
  **Files:** `backend/app/routers/student.py`

- **Stuck-job sweeper:** Added a background `asyncio.Task` in the app lifespan that
  periodically marks jobs stuck in in-progress statuses (older than
  `pipeline_timeout_s`) as `failed`. Configurable via `job_sweeper_interval_s`
  (default 300s; set to 0 to disable). Complements the existing startup recovery.
  **Files:** `backend/app/main.py`, `backend/app/config.py`

- **CORS production guard:** In `env == "production"`, the app now raises `RuntimeError`
  at startup if `CORS_ALLOWED_ORIGINS` is `*`. Development mode still allows the
  wildcard with a warning.
  **Files:** `backend/app/main.py`

### Deferred

- **OCR integration tests:** No DB-backed pipeline tests for provider fallback,
  malformed vision JSON, mixed text/scanned PDFs, or batch `ocr_strategy`.
  Requires test-infrastructure setup (async DB fixtures).
- **Test suite stub-DB migration:** `_MockSession` returns `None` for `.get()` and
  empty results for `.execute()`. Real async DB fixtures would catch more regressions.

---

## 2026-05-16 — Pipeline gap remediation (audit follow-up)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Second pass on open audit findings from the DB-backed ingestion pipeline trace.
Fixes four bugs spanning error handling, data model correctness, and query efficiency.

### Fix 1 — Pass 1 extraction retry (Critical)
**Change:** The text-extraction step in `_run_pipeline` had no retry on malformed JSON,
while Pass 2 annotation already retried 3×. Added a matching 3-attempt loop with
exponential backoff (0.5s, 1s) around the `complete()` + `extract_json_from_text()`
call. A final failure marks the job `failed` with the last exception in
`validation_errors_jsonb`.
**File:** `backend/app/routers/ingest.py`

### Fix 2 — Empty question_text filter (Low)
**Change:** `_normalize_extracted_questions` previously passed questions with
empty/whitespace `question_text` through to Pass 2 annotation (wasting an LLM call)
before they failed the `question_text required` validator. Added an explicit early
filter with a `logger.warning` per dropped entry.
**File:** `backend/app/routers/ingest.py`

### Fix 3 — Per-passage `passage_group_id` grouping (Medium)
**Change:** Replaced `uuid.uuid4() if len(questions_data) > 1 else None` with a
content-aware mapping. A `_passage_to_group` counter assigns a shared UUID only to
passage texts that appear on 2+ questions; standalone-passage questions and
passage-less questions receive `None`. This correctly groups reading-comprehension
questions sharing a passage without conflating unrelated questions in the same batch.
**File:** `backend/app/routers/ingest.py`

### Fix 4 — `question_job_questions` junction table (Medium)
**Change:** `QuestionJob.question_id` previously linked only the first question
produced by a multi-question ingest batch. Added a `question_job_questions` junction
table (composite PK: `job_id + question_id`) so every question produced by a job has
a durable FK link. `_run_pipeline` inserts a `QuestionJobQuestion` row for each
successfully persisted question. Migration `017` creates the table.
**Files:** `backend/app/models/db.py`, `backend/app/routers/ingest.py`,
`backend/migrations/versions/017_add_question_job_questions.py`

---

## 2026-05-16 — Unified OCR fallback gate (two-step preferred over VLM)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Restructures the OCR gate into a single ordered fallback loop so any branch
can fall back to any other available strategy, with two-step OCR preferred
over VLM-fused providers.

### Change
- Replaced `_fallback_ocr_strategy` with `_build_ocr_chain(resolved, settings)`.
  The chain runs the resolved strategy first, then walks `["glm", "deepseek",
  "anthropic", "ollama", "openai"]` — **two-step (glm, deepseek) is preferred
  over VLM-fused (anthropic, ollama, openai)**. `ocr_fallback=False` reduces
  the chain to `[resolved]`.
- Rewrote the OCR gate (the three sequential `if`-blocks) as a `for _strategy
  in _ocr_chain` loop. Each branch sets `_ocr_done = True` on success or
  records `_ocr_last_err` on failure; the loop advances to the next strategy.
  This resolves the earlier limitation where VLM-fused failures could only
  fall back to other VLM-fused providers — a VLM failure can now fall back
  to glm/deepseek and vice versa.
- VLM body retains its 3-attempt JSON-parse retry (exponential backoff).
- Updated `tests/test_ocr.py` — replaced the two `_fallback_ocr_strategy`
  tests with three `_build_ocr_chain` tests covering ordering preference,
  two-step → two-step fallback, and `ocr_fallback=False` behavior.

**Files:** `backend/app/routers/ingest.py`, `backend/tests/test_ocr.py`

---

## 2026-05-16 — VLM fused OCR path: retry + provider fallback

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Closes the last ingestion-path resilience gap. The VLM fused OCR branch (Ollama/Anthropic/OpenAI
vision providers) previously had a single `try/except` — one malformed JSON response or transient
provider error failed the whole job, while the GLM and DeepSeek branches already had `ocr_fallback`
logic.

### Change
**VLM fused branch retry + fallback:** Each VLM strategy now runs through a 3-attempt JSON-parse
retry loop with exponential backoff (0.5s, 1s). When a strategy is exhausted and `ocr_fallback` is
enabled, the job falls back to another VLM-fused provider (`ollama`/`anthropic`/`openai`) chosen by
`_fallback_ocr_strategy`, with a tried-strategy set preventing loops. Resolves DEBUG_LOG findings
2026-05-15 #6 and 2026-05-10 OCR-review #3.

**Note:** Fallback from a fused VLM path to a two-step GLM/DeepSeek path is still not wired —
fallback stays within the VLM-fused family.

**File:** `backend/app/routers/ingest.py`

---

## 2026-05-16 — Fix six live-ingestion-run gaps (timeouts, diagnostics, label backfill)

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Remediation of the six findings from a live ingestion run of `Test_1_digital_sec01_mod01.pdf`
against `qwen3-vl:235b-instruct-cloud`.

### Fix 1 — Non-empty error messages for timeout exceptions (Critical)
**Change:** `httpx.TimeoutException` has an empty `str()`, so a timed-out extraction recorded
`{"step": "extracting", "error": ""}`. Added `_exception_message()` to `errors.py` — falls back to
`"{ExceptionType} (no message)"` when `str(exc)` is empty. `error_payload` now also always emits an
`error_type` field.
**File:** `backend/app/llm/errors.py`

### Fix 2 — Wider text-completion timeout (High)
**Change:** Ollama's text `client` used a hardcoded 120s timeout, insufficient for 30K+ char
extraction payloads against cloud models. Added `TEXT_TIMEOUT = 300.0` class constant (parallel to
`VISION_TIMEOUT`); the text client now uses it.
**File:** `backend/app/llm/ollama_provider.py`

### Fix 3 — Positional option-label backfill (High)
**Change:** Extraction sometimes emitted 4 options with empty `label` fields, failing the validator
with `Option labels must be exactly {A, B, C, D}, got ['']`. `_normalize_extracted_questions` now
backfills A/B/C/D positionally when a question has exactly 4 options and all labels are blank.
**File:** `backend/app/routers/ingest.py`

### Fix 4 — Structural retry on empty extraction (Medium)
**Change:** The Pass 1 retry loop only retried on JSON parse errors. Added a structural check — if
no extracted question has non-empty `question_text`, a `ValueError` is raised so the existing retry
branch re-attempts instead of proceeding to annotation with an empty payload.
**File:** `backend/app/routers/ingest.py`

### Fix 5 — Pipeline-level timeout (Medium)
**Change:** A hung model could occupy a job-semaphore slot indefinitely. `_run_pipeline_with_session`
now wraps `_run_pipeline` in `asyncio.wait_for(timeout=settings.pipeline_timeout_s)` (default 1800s);
on timeout the job is marked `failed` on a fresh session with a `pipeline_timeout` error. Added
`pipeline_timeout_s: int = 1800` to `Settings`.
**Files:** `backend/app/routers/ingest.py`, `backend/app/config.py`

### Fix 6 — `page_count` in PDF source metadata (Low)
**Change:** The official PDF ingest route now stores `page_count` in the `source_metadata` dict
within `pass1_json`.
**File:** `backend/app/routers/ingest.py`

---

## 2026-05-16 — Fix seven high-severity audit findings (generate pipeline, N+1, security, VLM fallback)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Fourth remediation pass addressing all remaining Critical and High severity items from the May audits.

### Fix 1 — Generate pipeline savepoint (High — data integrity)
**Change:** `_run_generate_pipeline` persist block (Question + Version + Annotation + Options) had
no savepoint. A DB error left the job stuck in `"annotating"` status. Wrapped the entire block in
`async with db.begin_nested()`. Failure rolls back only that attempt; job is marked `failed` with
the exception in `validation_errors_jsonb`.
**File:** `backend/app/routers/generate.py`

### Fix 2 — Generate pipeline JSON retry (High — reliability)
**Change:** Both the generate and annotate LLM calls in `_run_generate_pipeline` had no retry.
Added 3-attempt loops with exponential backoff (0.5s, 1s) matching the ingest pipeline.
`ValueError` (malformed JSON) retries; other exceptions fail immediately.
**File:** `backend/app/routers/generate.py`

### Fix 3 — `_generation_profile_payload` operational key leak (High — data correctness)
**Change:** The last `merged.update(sources[-1])` call unconditionally merged `provider_name`,
`model_name`, and all request fields into `generation_profile_jsonb`. Added
`_operational_keys = {"provider_name", "model_name"}` exclusion filter so only non-operational
fields from `request_data` are stored in the profile.
**File:** `backend/app/routers/generate.py`

### Fix 4 — Insecure default keys block startup in production (High — security)
**Change:** `_warn_if_insecure_keys` only logged a warning and allowed startup to proceed.
Renamed to `_check_insecure_keys`; now raises `RuntimeError` when `settings.env == "production"`
and default keys are active. Development mode retains the warning. Added `env: str = "development"`
to `Settings`.
**Files:** `backend/app/main.py`, `backend/app/config.py`

### Fix 5 — N+1 queries in all list endpoints (High — performance)
**Change:** `admin.py`, `student.py`, and `questions.py` list endpoints each issued one DB call
per question for annotations and options. Replaced with batch queries using
`SELECT ... WHERE id IN (...)` and in-memory dict lookup. All three endpoints now issue 2–3 queries
regardless of result set size.
**Files:** `backend/app/routers/admin.py`, `backend/app/routers/student.py`,
`backend/app/routers/questions.py`

### Fix 6 — Ollama reasoning fallback for thinking models (High — correctness)
**Change:** Thinking-capable Ollama models (qwen3-vl, qwen3) route all output to
`message.reasoning` instead of `message.content` via the OpenAI-compat API. Added
`_extract_content(message)` helper that falls back to `message.reasoning` when `message.content`
is empty and strips `<think>…</think>` wrappers via regex. Applied to both `complete()` and
`complete_vision()`.
**File:** `backend/app/llm/ollama_provider.py`

### Fix 7 — `detect_overlaps` safety cap (Medium → fix)
**Change:** Overlap scan loaded all official questions with no limit, risking OOM at scale.
Added `.limit(2000)` to the JOIN query.
**File:** `backend/app/pipeline/overlap.py`

---

## 2026-05-16 — Fix three critical security/reliability gaps (audit follow-up)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Third pass fixing the three Critical-severity items identified in the backend security review.

### Fix 1 — Persist loop savepoint (Critical — data integrity)
**Change:** The per-question persist loop previously called `await db.rollback()` on failure,
which rolled back all already-committed questions in the same batch. Replaced the bare
`try/except` block with `async with db.begin_nested()` (SQLAlchemy SAVEPOINT). A flush
failure inside the savepoint now rolls back only the failed question; the session remains
valid and the loop continues. Removed the explicit `db.rollback()` call. Added `begin_nested`
context manager support to `_FakeDB` in both regression and pipeline test suites.
**Files:** `backend/app/routers/ingest.py`, `backend/tests/test_backend_regressions.py`,
`backend/tests/test_pipeline.py`

### Fix 2 — Profile endpoint restricted to admin (Critical — auth)
**Change:** `GET /api/users/{user_id}` was protected by `student_required`, allowing any student
with the shared API key to enumerate sequential user IDs and read all profiles. Changed to
`admin_required`.
**File:** `backend/app/routers/student.py`

### Fix 3 — Per-user token for answer submission (Critical — auth)
**Change:** `POST /api/submit` previously accepted `user_id: int` in the request body, with no
binding to the caller's identity. Any student could attribute answers to any user ID. Replaced
`user_id` with `user_token: str` (UUID). The endpoint now resolves the user by token, ensuring
a student can only submit on behalf of the user whose token they hold. Added `user_token` UUID
column to the `User` model with server-default `gen_random_uuid()` and migration `018`.
`UserResponse` now exposes `user_token` so admins can retrieve it after user creation.
**Files:** `backend/app/models/db.py`, `backend/app/models/payload.py`,
`backend/app/routers/student.py`,
`backend/migrations/versions/018_add_user_token.py`,
`backend/tests/test_student_router.py`, `backend/tests/test_backend_regressions.py`

---

## 2026-05-15 — Wire stimulus asset pipeline end-to-end

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Connects the seven gaps identified in a program review: the stimulus data model and
storage were scaffolded but the runtime pipeline never activated any of those paths.
Questions with charts, tables, graphs, or figures are now extracted, annotated,
cropped, linked to source spans, served via API, and exported to YAML.

### Gap 1 — Extraction prompt (`extract_prompt.py`)
**Change:** Added `stimulus_assets` array to the per-question JSON schema. Each entry
carries `type`, `title`, `structured_data`, and `render_hints`. Rules instruct the
LLM to populate one entry per distinct visual element and to separate table/chart data
into the appropriate structured shape.
**File:** `backend/app/prompts/extract_prompt.py`

### Gap 2 — Layout region matching (`crop_detector.py`)
**Change:** Added `match_stimulus_regions_for_question()` — returns every `table`,
`chart`, and `figure` region on the same page as the matched question block. Updated
`crop_and_store()` to accept a `kind` parameter so stimulus crops use the correct
storage kind (`table_crop`, `chart_crop`, `figure_crop`) instead of `question_crop`.
**File:** `backend/app/storage/crop_detector.py`

### Gap 3 — Stimulus annotation pass (`stimulus_prompt.py`, `ingest.py`)
**Change:** New `stimulus_prompt.py` module with a vision prompt that instructs the
LLM to extract structured data and render hints from a cropped stimulus image. New
`_annotate_layout_stimulus()` helper in `ingest.py` loads the cropped bytes, calls
`complete_vision`, and returns the parsed annotation. Called per stimulus region inside
`_persist_single_question()` when a vision-capable provider is present; degrades
gracefully to empty annotation on failure.
**Files:** `backend/app/prompts/stimulus_prompt.py` (new),
`backend/app/routers/ingest.py`

### Gap 4 — Frontend API (`admin.py`)
**Change:** Added `GET /admin/questions/{question_id}/stimulus-assets` endpoint.
Returns all `QuestionStimulusAsset` rows for a question ordered by page then type,
with `id`, `stimulus_type`, `storage_path`, `source_page_number`, `title`,
`structured_data`, and `render_hints`.
**File:** `backend/app/routers/admin.py`

### Gap 5 — Storage kinds (`storage_layout.yaml`, `ingest.py`)
**Change:** Added `table_crop`, `chart_crop`, `figure_crop`, and `figure_asset` as
`object_kinds` in the storage layout YAML (all were referenced in code but not
defined). Added `_crop_kind_for_stimulus()` helper that maps region type → crop kind.
**Files:** `backend/config/storage_layout.yaml`, `backend/app/routers/ingest.py`

### Gap 6 — Source span provenance (`ingest.py`)
**Change:** `_persist_single_question()` now creates a `QuestionSourceSpan` row for
each layout-detected stimulus region with `source_region_role` set to the region type
(`table`, `chart`, or `figure`) rather than always `question_block`. The crop path
and layout JSON path are recorded on these spans.
**File:** `backend/app/routers/ingest.py`

### Gap 7 — YAML export (`yaml_export.py`)
**Change:** `_build_question_record()` now includes `stimulus_assets` (filtering out
internal `_`-prefixed keys added by the pipeline), `table_data`, and `graph_data`
when present in the extract JSON.
**File:** `backend/app/storage/yaml_export.py`

---

## 2026-05-15 — Layout detection, region cropping, and OCR diagnostics

**Model:** Claude Opus 4.7 (`claude-opus-4-7`)
**Branch:** `main`

Adds layout-detection enrichment after OCR extraction. Each page render is sent
to GLM-OCR with a layout prompt that identifies question blocks, tables, charts,
and figures with normalized bounding boxes. Detected regions are matched to
extracted questions by number, cropped from the page render with Pillow, and stored
via the object-store adapter. A per-job OCR diagnostics file is also persisted.
All steps degrade gracefully — any failure leaves questions with NULL crop/layout
paths rather than blocking the pipeline.

### Layout prompt (`layout_prompt.py`)
**Change:** New module with `LAYOUT_SYSTEM_PROMPT` and `build_layout_prompt()` that
instructs GLM-OCR to return a JSON array of regions (question_block, table, chart,
figure) with normalized bounding boxes per page.
**File:** `backend/app/prompts/layout_prompt.py` (new)

### Crop detector (`crop_detector.py`)
**Change:** New module with three functions:
- `detect_layout(page_images_data, settings)` — async, one GLM-OCR call per page,
  returns `{page_index: [RegionDetection]}`. Never raises; returns `{}` on failure.
- `match_region_for_question(layout_data, q_data, question_index)` — sync, matches
  a question to its region by number then positional fallback.
- `crop_and_store(region, page_images_data, question_id)` — sync, loads page bytes
  (path → storage_path → b64 fallback), crops with Pillow, writes PNG via
  `put_object('question_crop', ...)`.
Also includes `_parse_question_number`, `_clamp_bbox`, `_is_valid_bbox`, and
`_parse_region_list` helpers.
**File:** `backend/app/storage/crop_detector.py` (new)

### Config and storage layout
**Change:** Added `layout_detection_enabled: bool = True` to `Settings` as an admin
kill switch. Added `ocr_diagnostics` object kind to `storage_layout.yaml` (bucket
`ocr_artifacts`, template `diagnostics/{job_id}/page_{page_number:03d}.json`).
**Files:** `backend/app/config.py`, `backend/config/storage_layout.yaml`

### Ingestion pipeline wiring
**Change:**
- `_run_pipeline()` now calls `detect_layout()` after OCR and before the per-question
  loop, gated on `layout_detection_enabled` + `glm_ocr_model` + page renders. Layout
  JSON is stored via `put_object('ocr_layout', ...)`. On failure, layout_data and
  layout_paths reset to `{}` — pipeline continues with NULL crop/layout paths.
- After the layout block, a per-job OCR diagnostics file is written via
  `put_object('ocr_diagnostics', ...)` and the path is embedded in `_ocr_meta`.
- `_persist_single_question()` gained `layout_data` and `layout_paths` params.
  Inside, after `question_id` is determined, it calls `match_region_for_question()`
  then `crop_and_store()` to produce the crop, and passes `crop_path` and
  `layout_json_path` to `_build_question_source_span()`.
- `_build_question_source_span()` signature expanded with explicit `crop_path` and
  `layout_json_path` params (previously read from `q_data.get()` which was always NULL).
- `_persist_single_question` now performs 3 `db.flush()` calls (question+version,
  annotation+options, source_span), up from 2.
**File:** `backend/app/routers/ingest.py`

### Tests
**Change:**
- `test_crop_detector.py` (new): 27 unit tests covering `_parse_question_number`,
  `_clamp_bbox`, `_is_valid_bbox`, `_parse_region_list`, `match_region_for_question`,
  `crop_and_store` (temp file, b64 fallback, missing page, unloadable image,
  degenerate bbox), and `detect_layout` (success, model unset, exception).
- `test_ingest_router.py` (extended): 4 degradation tests —
  `_build_question_source_span` without crop/layout, with crop/layout paths,
  `match_region_for_question` on empty layout, `detect_layout` returning `{}`.
- `test_pipeline.py` and `test_backend_regressions.py`: updated all `SimpleNamespace`
  settings mocks with `layout_detection_enabled=False` and corrected `flush_count`
  assertions from 2 to 3.
**Files:** `backend/tests/test_crop_detector.py` (new),
`backend/tests/test_ingest_router.py`, `backend/tests/test_pipeline.py`,
`backend/tests/test_backend_regressions.py`

### All 274 tests pass

---

## 2026-05-15 — Local object storage provenance for ingestion

**Model:** OpenAI Codex (`gpt-5`)
**Branch:** `main`

Added the first executable slice for local Postgres plus S3/Supabase-style
storage testing.

### Local storage adapter
**Change:** Added a config-driven object-store adapter that reads
`backend/config/storage_layout.yaml`, writes local `local-s3://...` objects under
`local_object_store/`, and keeps bucket/key naming isolated for the later
Supabase Storage swap.
**Files:** `backend/app/storage/object_store.py`, `backend/app/config.py`,
`backend/config/storage_layout.yaml`

### Provenance schema
**Change:** Added `question_source_spans` and `question_stimulus_assets` models
and migration so questions can link back to rendered pages, OCR text, crops,
layout JSON, and structured table/chart/figure assets.
**Files:** `backend/app/models/db.py`, `backend/app/models/__init__.py`,
`backend/migrations/versions/016_add_question_source_provenance.py`

### Ingestion wiring
**Change:** Official/unofficial ingestion now stores raw uploads, OCR page
renders, and OCR text artifacts through the object-store adapter. Persisted
questions now receive a source-span row, and structured stimulus asset rows are
created when extractor output includes table/chart/figure asset data.
**File:** `backend/app/routers/ingest.py`

### Resume plan and tests
**Change:** Added `tasks_s3.md` as the pause/resume checklist and focused tests
for object storage plus source-span provenance helpers.
**Files:** `tasks_s3.md`, `backend/tests/test_object_store.py`,
`backend/tests/test_ingest_router.py`

---

## 2026-05-15 — Ollama OCR and extraction defaults

**Model:** OpenAI Codex (`gpt-5`)
**Branch:** `main`

Updated ingestion defaults so scanned assets OCR with `glm-ocr:latest` through
Ollama and text extraction defaults to `deepseek-v4-pro:cloud` through the
Ollama endpoint.

### Backend defaults
**Change:** Switched default annotation/extraction provider to `ollama` and
default Ollama/text model to `deepseek-v4-pro:cloud`. Kept GLM OCR as the
default OCR strategy/model.
**Files:** `backend/app/config.py`, `backend/.env`, `backend/.env.example`

### Provider routing
**Change:** Updated Ollama provider/factory defaults and guarded explicit
Anthropic/OpenAI requests from inheriting the Ollama DeepSeek model.
**Files:** `backend/app/llm/ollama_provider.py`, `backend/app/llm/factory.py`,
`backend/app/routers/ingest.py`

### Ingestion extraction reliability
**Change:** Added an Ollama `thinking=false` request option and enabled it only
for ingestion Pass 1 text extraction when `deepseek-v4-pro:cloud` is the Ollama
extractor.
**Files:** `backend/app/llm/ollama_provider.py`, `backend/app/routers/ingest.py`

### UI, docs, and tests
**Change:** Updated dashboard model presets, removed stale OCR-not-implemented
copy, refreshed API/config docs, and adjusted unit expectations for the new
defaults.
**Files:** `backend/app/routers/dashboard.py`, `backend/docs/*`,
`docs/PRD/INGESTION_PRD.md`, `backend/tests/*`

---

## 2026-05-15 — Prompt loader and DSAT rules completeness pass

**Model:** OpenAI Codex (`gpt-5`)
**Branch:** `main`
**Base commit:** `dd18673 Expand DSAT trap and construct rules`

Post-commit audit and implementation pass to make the active DSAT rule files usable
for both real-question classification and realistic generation from ground-truth
patterns. Normal backend test suite passes: `237 passed, 2 skipped`.

### Fix 1 — Generation prompt loader truncated active rule files
**Change:** Replaced the first-6,000-character rule loader with targeted section
extraction for generation-critical Grammar v7 and Reading v2 sections. Added
domain inference so grammar generation loads grammar rules, reading generation
loads reading rules, and ambiguous requests load both.
**File:** `backend/app/prompts/generate_prompt.py`
**Why:** The old loader cut Grammar v7 around the schema section and Reading v2
around construct-key definitions, excluding the late generation, distractor, and
validator sections needed for realistic item generation.

### Fix 2 — Reading annotation prompt omitted §17 disambiguation rules
**Change:** `_extract_between()` now searches for the end marker after the start
marker instead of matching the current heading as its own end.
**File:** `backend/app/prompts/annotate_prompt.py`
**Why:** Reading §17 was present in the file but not reliably loaded into the
annotation prompt, weakening classification for ambiguous reading/evidence cases.

### Fix 3 — Prompt tests now guard late-section loading
**Change:** Added tests that assert annotation includes Reading §17 and generation
includes Grammar B.4, Reading §16.9, and Reading §21.
**File:** `backend/tests/test_prompts.py`
**Why:** Prevents regression to truncated or incomplete rule context.

### Rules update 1 — Grammar v7 per-key generation/distractor completeness
**Change:** Expanded Grammar v7 B.3 passage-construction rules and B.4 distractor
heuristics so every production `grammar_focus_key` mapped in D.8 has a generation
recipe and distractor table.
**File:** `rules_agent_dsat_grammar_ingestion_generation_v7.md`
**Includes:**
- Added B.3 generation guidance for umbrella or previously under-specified keys:
  `verb_form`, `sentence_boundary`, `redundancy_concision`,
  `precision_word_choice`, `register_style_consistency`, `logical_relationships`,
  `emphasis_meaning_shifts`, `data_interpretation_claims`, `conjunction_usage`,
  and `elliptical_constructions`.
- Added B.4 distractor tables for missing production keys, including sentence
  boundary subtypes, verb form, voice, negation, countability, determiners,
  affirmative agreement, conjunctions, ellipsis, expression-of-ideas word choice,
  data claims, and transitions.
- Added secondary generation trap patterns for subject-verb agreement, tense,
  comma, and semicolon items.
- Normalized `syntactic_trap_key` examples to approved D.5/backend-compatible
  keys and moved narrower labels into subpattern notes.
- Kept B.4 plausibility sources inside the approved grammar plausibility source
  vocabulary.

### Rules update 2 — Reading v2 per-focus generation coverage
**Change:** Added Reading §16.9, a per-focus generation and distractor recipe
matrix for every approved `reading_focus_key`, plus construct-binding rules.
**File:** `rules_agent_dsat_reading_v2.md`
**Includes:**
- Generation recipes for textual evidence, quantitative evidence, central ideas,
  inferences, WIC, text structure/purpose, and cross-text focus keys.
- Required distractor behavior for each focus key, including wrong-claim evidence,
  wrong-group data, local maximum, absolute/proportional confusion, true-detail
  traps, rhetorical-scope errors, attribution swaps, and relationship-degree errors.
- Construct binding for `contextual_semantic_precision`,
  `rhetorical_function_precision`, `cross_text_relationship_precision`,
  `evidence_relation_precision`, `inference_boundary_control`,
  `quantitative_constraint_tracking`, and `figurative_interpretation_precision`.

### Rules update 3 — Additional Reading v2 realism refinements
**Change:** Added missing reading refinements discovered during the completeness
audit.
**File:** `rules_agent_dsat_reading_v2.md`
**Includes:**
- Added `figurative_language_meaning`, `figurative_interpretation_precision`,
  `figurative_literal_confusion`, and `figurative_meaning_blindness`.
- Added `causal_specification` for cross-text cases where Text 2 explains the
  mechanism behind Text 1's phenomenon.
- Added `false_concession_trap` for cross-text distractors that invent
  qualification or partial concession.
- Added `polarity_resolution` and `apply_negation_logic` support for WIC polarity.
- Expanded rhetorical verbs with `to examine`, `to question`, `to introduce`,
  `to summarize`, and `to distinguish`.
- Added passage architecture patterns: `analogy_driven_argument`,
  `multi_perspective_presentation`, and `qualification_restatement`.
- Added disambiguation for `command_of_evidence_textual` vs.
  `central_ideas_and_details` / `supporting_detail`.

### Verification
- `uv run pytest tests/test_prompts.py` → `4 passed`
- `uv run pytest tests` → `237 passed, 2 skipped`
- Structural scans confirmed:
  - no missing Grammar B.3 sections for D.8 production focus keys
  - no missing Grammar B.4 sections for D.8 production focus keys
  - no unapproved `syntactic_trap_key` examples in Grammar v7
  - no missing Reading §16 generation coverage for §7 reading focus keys
  - no missing Reading §16 construct coverage for §2.3 test construct keys
- `git diff --check` passed.

### Known test caveat
Full `uv run pytest` still collects preexisting live OCR helpers in
`backend/test_ocr_live.py`; those functions require an `image` fixture that is
not part of the normal test environment. The normal backend suite under
`backend/tests` passes.

### Wolf metadata
Updated OpenWolf audit files for this work:
`.wolf/anatomy.md`, `.wolf/buglog.json`, `.wolf/cerebrum.md`,
`.wolf/hooks/_session.json`, `.wolf/memory.md`, and `.wolf/token-ledger.json`.

---

## 2026-05-11 — Ingestion pipeline gap fixes (round 4)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Fourth audit pass, focused on VLM extraction quality: label normalization and duplicate suppression. 29 tests passing.

### Fix 1 — VLM answer-label format breaks validator ("A)" rejected as invalid)
**Change:** Added `_clean_option_label()` helper; applied in `_normalize_extracted_questions` to both `correct_option_label` and each option's `label` field. Strips trailing `)` and `.`, uppercases.
**File:** `backend/app/routers/ingest.py`
**Why:** VLMs (granite3.2-vision, qwen-vl family) frequently emit answer labels with trailing parens (`"A)"`, `"B."`) or lowercase (`"a"`). The validator requires `correct_option_label in ("A","B","C","D")` — these labels caused every such question to fail with a blocking error, silently discarding the entire ingestion batch.

### Fix 2 — VLM duplicate question rows persisted
**Change:** Added `seen_texts` deduplication set in `_normalize_extracted_questions`; questions whose `question_text` matches a prior entry (case-insensitive, stripped) are skipped.
**File:** `backend/app/routers/ingest.py`
**Why:** Small VLMs (confirmed with `granite3.2-vision:latest`) hallucinate repeated question objects in the `questions` array — e.g., Q2-Q4 all identical to Q2. Without deduplication these were persisted as separate `Question` rows, polluting the database.

### Fix 3 — OllamaProvider vision timeout too short for large VLMs (120s → 600s)
**Change:** Added `vision_client = httpx.AsyncClient(timeout=600.0)` on `OllamaProvider`; `complete_vision` now uses `vision_client`; `complete` still uses the original 120s client. `close()` closes both.
**File:** `backend/app/llm/ollama_provider.py`
**Why:** VLM OCR inference for models like `qwen3-vl:8b` takes 200-600s on local hardware. The shared 120s timeout caused all 3 retry attempts to time out (363s total). Text-only LLM calls are fast enough for 120s; only vision calls need the longer budget.

### Fix 4 — Benchmark GET missing `questions_extracted` (pre-validation count)
**Change:** `_run_pipeline` stores `_extracted_count` in `pass1_json` after `_normalize_extracted_questions`; benchmark GET maps it to `OCRJobResult.questions_extracted`.
**Files:** `backend/app/routers/ingest.py`, `backend/app/models/payload.py`
**Why:** The benchmark `OCRJobResult` only had `questions_created` (count of persisted questions after validation). When a VLM extracts 4 questions but 2 fail validation, you couldn't distinguish "model failed" from "validator blocked". `questions_extracted` gives the count after dedup but before validation.

### Live-test finding: deepseek-ocr:latest works on properly-sized images
**Context:** Earlier test showed only 107 output tokens from `deepseek-ocr:latest`. Re-test with small image (612×792 PNG) produced 763 tokens and extracted all 4 questions correctly including passage text, answer choices, and answer keys. Root cause of prior failure was image too large (1224×1584, 6MB) → model timeout/truncation.

### Tests added (6)
`test_normalize_questions_strips_trailing_paren_from_correct_label`, `test_normalize_questions_strips_trailing_period_from_correct_label`, `test_normalize_questions_lowercased_correct_label_upcased`, `test_normalize_questions_strips_option_label_parens`, `test_normalize_questions_deduplicates_identical_question_text`, `test_normalize_questions_dedup_is_case_insensitive`

---

## 2026-05-11 — Ingestion pipeline gap fixes (round 3)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Third audit pass, focused on benchmark quality-measurement correctness. 211 tests passing.

### Fix 1 — DeepSeek OCR metadata never persisted (SQLAlchemy in-place JSONB mutation)
**Change:** Replace `job.pass1_json["raw_text"] = …` + `job.pass1_json["_ocr_meta"] = …` with a single `job.pass1_json = {**(job.pass1_json or {}), "raw_text": …, "_ocr_meta": …}` assignment.
**File:** `backend/app/routers/ingest.py` (DeepSeek OCR gate block)
**Why:** SQLAlchemy only tracks attribute-level assignments, not in-place dict mutations. After the job's `pass1_json` was initially committed, the DeepSeek OCR gate mutated the dict in-place and then called `await db.commit()`. SQLAlchemy saw no attribute change and silently skipped the UPDATE — leaving `_ocr_meta.strategy` missing in benchmark poll results (returned as "unknown").

### Fix 2 — `_created_question_ids` never persisted (same root cause)
**Change:** Replace `job.pass1_json["_created_question_ids"] = [...]` with `job.pass1_json = {**(job.pass1_json or {}), "_created_question_ids": [...]}`.
**File:** `backend/app/routers/ingest.py:647`
**Why:** Same SQLAlchemy JSONB mutation tracking issue. `questions_created` in `GET /ingest/benchmark/ocr/{id}` was always 0 because the list was never written to the database.

### Fix 3 — Ollama VLM models outside Kimi skip JSON repair path
**Change:** `if "kimi" in model_key or ("ollama" == provider_key and "kimi" in model_key)` → `if provider_key == "ollama" or "kimi" in model_key`.
**File:** `backend/app/parsers/json_parser.py:150`
**Why:** Non-Kimi Ollama VLM models (llava, moondream, llama3.2-vision) can emit reasoning preambles or JSON-adjacent text with bare keys / curly quotes. Only Kimi-named models were routed through the `_extract_with_kimi_strategy` repair path; all other Ollama VLM models failed with "No valid JSON found" when their output needed repair.

### Tests added (3)
- `test_extract_json_routes_all_ollama_through_repair_path` — fenced JSON from `llava:13b` parsed correctly
- `test_extract_json_repair_path_handles_bare_keys_for_ollama` — bare-key JSON from `moondream:latest` normalized
- `test_run_pipeline_reassigns_pass1_json_with_created_ids` — `_created_question_ids` present in `pass1_json` after pipeline for unofficial ingest
**File:** `backend/tests/test_backend_regressions.py`

---

## 2026-05-10 — Ingestion pipeline gap fixes (round 2)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main`

Second pass implementing remaining gaps found in the ingestion multi-provider benchmarking audit. All 197 tests green.

### Fix 1 — Pass 2 `token_usage` bare attribute access in annotation loop
**Change:** `result.token_usage or {}` → `getattr(result, "token_usage", None) or {}`
**File:** `backend/app/routers/ingest.py:585`
**Why:** `SimpleNamespace` mocks in tests don't have `token_usage`; the `AttributeError` was silently caught and dropped the question, causing `StopIteration` in the test assertion.

### Fix 2 — `_resolve_ocr_strategy` auto priority: ollama before deepseek
**Change:** In "auto" mode, check `ocr_vision_provider == "ollama"` before `deepseek_ocr_base_url`.
**File:** `backend/app/routers/ingest.py:353-362`
**Why:** Tests expected `ocr_vision_provider` to signal explicit intent — deepseek is a fallback, not the default.

### Fix 3 — `_resolve_ocr_strategy` safe attribute access in auto mode
**Change:** `settings.anthropic_api_key` → `getattr(settings, "anthropic_api_key", None)` in "auto" path.
**File:** `backend/app/routers/ingest.py:358-361`
**Why:** FakeSettings in tests don't always carry all attributes; `AttributeError` masked the expected `ValueError`.

### Fix 4 — `_provider_registry` list alongside `_provider_cache` dict
**Change:** Added `_provider_registry: list = []`; `get_provider` and `get_ocr_client` append to it; `close_all_providers` iterates and clears it.
**File:** `backend/app/llm/factory.py`
**Why:** Test `test_close_all_providers_calls_close` expected a list-shaped `_provider_registry`. My prior refactor renamed it to a dict-only `_provider_cache`.

### Fix 5 — validator `graphic_data` severity restored to blocking
**Change:** `"severity": "review"` → `"severity": "blocking"` for Quantitative CoE missing graphic data.
**File:** `backend/app/pipeline/validator.py:157`
**Why:** Changed during audit session; test expects blocking to gate pipeline on this field.

### Fix 6 — Reannotate `_llm_meta` missing `token_usage`
**Change:** Added `"token_usage": getattr(result, "token_usage", None) or {}` to `_llm_meta` in `_run_reannotate_pipeline`.
**File:** `backend/app/routers/ingest.py:1007`
**Why:** All other pipeline `_llm_meta` dicts track token usage; reannotate was the only path that didn't.

### Fix 7 — Dead `if False` in `_vlm_model_for_strategy`
**Change:** `return settings.default_ollama_model if False else "gpt-4o"` → `return "gpt-4o"`.
**File:** `backend/app/routers/ingest.py:372`
**Why:** Dead branch from a placeholder; always evaluated the else side.

### Fix 8 — `get_job_status` dead `validation_errors` computation
**Change:** Remove local `validation_errors` variable; pass `job.validation_errors_jsonb` directly into `JobResponse`.
**File:** `backend/app/routers/ingest.py`, `backend/app/models/payload.py`
**Why:** `validation_errors` was computed but never included in the response — wasted work and missing diagnostic data.

### Fix 9 — Add `comparison_group_id` index for benchmark poll performance
**Change:** New migration `014_add_comparison_group_index.py`; index added to `QuestionJob.__table_args__`.
**Files:** `backend/migrations/versions/014_add_comparison_group_index.py`, `backend/app/models/db.py`
**Why:** `GET /benchmark/ocr/{id}` queries on `comparison_group_id`; without an index this is a full table scan.

---

## 2026-05-10 18:45 PDT — Ingestion pipeline gap audit (multi-provider benchmarking)

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
**Branch:** `main` · **Commit:** `fe3f436` — feat(ocr): Add OCR pipeline with DeepSeek and Ollama VLM support

Audit of all four ingestion providers (DeepSeek OCR-2, Ollama VLM, Claude, OpenAI) against the goal of measuring accuracy, token usage, and extraction quality per strategy. No code changed this session — findings only.

**Current status review (2026-05-10):** Mixed. Some findings have since been fixed in the working tree, some are partial, one was inaccurate against `fe3f436`, and tests are not currently green.

---

### Audit finding 1 — `_ocr_meta` overwritten by Pass 1 (Blocking)

**Status:** FIXED in working tree. `_run_pipeline()` now captures `_ocr_meta` before Pass 1 overwrites `pass1_json` and restores it after extraction.

On the DeepSeek path, `_run_pipeline()` writes `job.pass1_json["_ocr_meta"]` after OCR completes, then immediately replaces the entire `pass1_json` dict during Pass 1 extraction, erasing `_ocr_meta`. DeepSeek timing, model name, and page count are lost before they can be queried.

**Fix:** Capture `ocr_meta = job.pass1_json.get("_ocr_meta")` before Pass 1 overwrites the dict, then merge it back after. 2-line change — documented in plan `wiggly-shimmying-leaf.md` Part 1.

**Files:** `backend/app/routers/ingest.py` — `_run_pipeline()` around line 470

---

### Audit finding 2 — Token usage computed but never persisted (Critical)

**Status:** MOSTLY FIXED in working tree. `_ocr_meta`, Pass 1 `_llm_meta`, VLM fused metadata, and Pass 2 `_pass2_meta` now include `token_usage`. Remaining risk: no focused regression test currently verifies the full persistence path.

All four providers return `token_usage: {"input": N, "output": N}` in `LLMResponse`. None of these values reach the database:
- `_llm_meta` in `pass1_json` stores only `latency_ms`, not `token_usage`
- `_ocr_meta` stores only `latency_ms`, even though `ocr_result.token_usage` is available at the point of write
- Pass 2 (annotation) stores **no metadata at all** — no latency, no token count, no model record

Cost and throughput cannot be measured for any provider.

**Fix:** Add `token_usage` field to `_ocr_meta`, `_llm_meta`, and introduce `_pass2_meta` for annotation step.

**Files:** `backend/app/routers/ingest.py` — `_run_pipeline()` OCR gate (~line 394), Pass 1 block (~line 470), Pass 2 block (~line 507)

---

### Audit finding 3 — Claude and OpenAI have no vision / OCR implementation (Critical)

**Status:** FIXED in working tree. `AnthropicProvider.complete_vision()` and `OpenAIProvider.complete_vision()` are implemented.

`AnthropicProvider` and `OpenAIProvider` implement only `complete()`. Neither implements `complete_vision()`. Both Claude (Haiku 4.5, Sonnet 4.6) and GPT-4o support image input natively in their APIs, but scanned PDFs routed to these providers hit the base `raise NotImplementedError` and crash the job.

**Fix:** Implement `complete_vision()` in both providers using their respective multimodal message formats.

**Files:**
- `backend/app/llm/anthropic_provider.py` — add `complete_vision()` using `content: [{"type": "image", ...}]` blocks
- `backend/app/llm/openai_provider.py` — add `complete_vision()` using `content: [{"type": "image_url", ...}]` blocks

---

### Audit finding 4 — No benchmark endpoint (High)

**Status:** IMPLEMENTED BUT NOT VERIFIED. `POST /ingest/benchmark/ocr` and `GET /ingest/benchmark/ocr/{comparison_group_id}` exist in the working tree. No focused tests were found for the benchmark endpoints.

`POST /ingest/benchmark/ocr` and `GET /ingest/benchmark/ocr/{comparison_group_id}` are not implemented. There is no way to submit one file, run all strategies in parallel, and compare results. Plan `wiggly-shimmying-leaf.md` (Parts 1–4) specifies the full implementation.

**Files:** `backend/app/routers/ingest.py` — new endpoints; `backend/app/models/payload.py` — `OCRJobResult`, `OCRBenchmarkResponse`

---

### Audit finding 5 — `comparison_group_id` column missing from `QuestionJob` (High)

**Status:** AUDIT FINDING INACCURATE. `comparison_group_id` already exists in `QuestionJob` and in `backend/migrations/versions/001_initial_schema.py` at commit `fe3f436`. No separate migration is needed only if deployments are built from the initial schema; an already-migrated database still needs confirmation.

Benchmark grouping requires a shared `comparison_group_id` UUID on parallel jobs. No such column exists in the `QuestionJob` model and no migration has been written.

**Files:** `backend/app/models/db.py` — add column; new Alembic migration required

---

### Audit finding 6 — `ocr_fallback` config is dead code (Medium)

**Status:** PARTIALLY FIXED. `ocr_fallback` is now read when DeepSeek OCR fails, but the fallback always switches to Ollama without first checking that Ollama is configured/available.

`Settings.ocr_fallback: bool = True` is declared in `config.py` but `_resolve_ocr_strategy()` never reads it. If DeepSeek's endpoint is unavailable and `ocr_strategy="deepseek"` is requested, the job fails with no retry against Ollama.

**Files:** `backend/app/config.py` line 38; `backend/app/routers/ingest.py` — `_resolve_ocr_strategy()`

---

### Audit finding 7 — "vision" alias accepted internally but rejected by API (Medium)

**Status:** FIXED in working tree. Both upload endpoints now accept `"vision"` in the public `ocr_strategy` whitelist.

`_resolve_ocr_strategy()` accepts `"vision"` as an alias for `"ollama"`. Both upload endpoints validate `ocr_strategy not in {"deepseek", "ollama", "auto"}` and return 422 if a caller passes `"vision"`. The alias is unreachable via the public API.

**Fix:** Either add `"vision"` to the API whitelist or remove the alias from the resolver.

**Files:** `backend/app/routers/ingest.py` — `ingest_official_pdf()` line 650, `ingest_unofficial_file()` line 749

---

### Audit finding 8 — Pass 1 and Pass 2 locked to the same provider (Medium)

**Status:** STILL OPEN. OCR/VLM strategy can vary, but Pass 2 annotation still uses the job provider created at `_run_pipeline()` start. There is no general separate provider/model selection for extraction and annotation.

`_run_pipeline()` resolves one provider at job start and uses it for both extraction (Pass 1) and annotation (Pass 2). There is no mechanism to use different models for each stage (e.g. DeepSeek OCR → Claude extract → OpenAI annotate).

**Files:** `backend/app/routers/ingest.py` — `_run_pipeline()` top-level provider resolution

---

### Audit finding 9 — Raw text truncated silently at 50,000 chars (Low)

**Status:** PARTIALLY FIXED. Upload endpoints now set `"_truncated": true` when slicing `raw_text[:50000]`, but the data is still truncated and no warning log was found. Text-form ingest separately rejects inputs over 50,000 chars with HTTP 413.

Both upload endpoints store `raw_text[:50000]` in `pass1_json` with no flag indicating truncation. Long official PDFs silently lose questions from the tail; there is no `truncated: true` field and no warning logged.

**Fix:** Add `"_truncated": True` to `pass1_json` when truncation occurs; log a warning.

**Files:** `backend/app/routers/ingest.py` — `ingest_official_pdf()` line 718, `ingest_unofficial_file()` line 828

---

## 2026-05-10 — Ingestion bug fixes (audit batch 2)

### Fix: `OllamaProvider.complete_vision()` missing retry protection (Bug #20)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` to `complete_vision()`, matching the protection already on `complete()`. Transient Ollama timeouts and 503s during VLM-based scanned-PDF ingest will now retry with exponential backoff instead of immediately failing the job.

**Files amended**
- `backend/app/llm/ollama_provider.py` — `@with_retry` decorator added to `complete_vision()`.

---

### Fix: `DeepSeekOCRClient.extract()` missing retry protection (Bug #21)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added `from app.llm.retry import with_retry` import and `@with_retry(max_attempts=3, base_delay=1.0, max_delay=30.0)` decorator to `extract()`. Transient failures against the local vLLM/LMDeploy inference server will now retry instead of immediately failing the OCR ingest pass.

**Files amended**
- `backend/app/parsers/ocr.py` — `with_retry` import added; `@with_retry` decorator added to `extract()`.

---

### Fix: `_provider_registry` unbounded memory growth (Bug #23)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Replaced the module-level `_provider_registry: list` with `_provider_cache: dict` keyed by `(provider_name, api_key, base_url, default_model)`. Identical configurations now return the same provider instance rather than creating a new `httpx.AsyncClient` per pipeline call. `close_all_providers()` updated to iterate `.values()` on the dict.

**Files amended**
- `backend/app/llm/factory.py` — list replaced with keyed dict; `get_provider()` and `get_ocr_client()` check cache before creating; `close_all_providers()` iterates dict values.

---

### Fix: `command_of_evidence_quantitative` permanently blocked by phantom fields (Bug #24)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

`table_data` and `graph_data` are referenced in a blocking validation rule but no extraction prompt emits these fields. Permanently blocking these questions is incorrect. Changed severity from `"blocking"` to `"review"` with a message indicating the gap, routing them to the human review queue instead of auto-failing them.

**Files amended**
- `backend/app/pipeline/validator.py` — `graphic_data` check severity changed from `"blocking"` to `"review"`; message updated to explain the gap.

---

## 2026-05-10 — Ingestion bug fixes (audit batch 1)

### Fix: Duplicate-file detection on ingest (Bug #2)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added a checksum uniqueness check before creating `QuestionAsset` + `QuestionJob` rows in both official and unofficial upload endpoints. Re-uploading a file that has already been ingested now returns HTTP 409 instead of silently creating duplicate questions.

**Files amended**
- `backend/app/routers/ingest.py` — checksum check added in `ingest_official_pdf` and `ingest_unofficial_file` before asset creation.

---

### Fix: Background pipeline tasks swallow exceptions silently (Bug #10)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Added `_log_task_exception` done-callback to every `asyncio.create_task()` call in the ingest and generate routers. Uncaught exceptions from background pipeline tasks are now logged at ERROR level with full traceback instead of being silently discarded.

**Files amended**
- `backend/app/routers/ingest.py` — added `logger`, `_log_task_exception`, wired callback onto all four `create_task` calls.
- `backend/app/routers/generate.py` — added `logger`, `_log_task_exception`, wired callback onto both `create_task` calls.

---

### Fix: Wrong UUID passed to overlap self-skip guard (Bug #15)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

`detect_overlaps` was called with `question_id=job.id` (a job UUID) at the point in the pipeline before the question has been persisted. The self-skip guard `if oq.id == question_id` was therefore always false. Fixed by passing `None` at the call site and making the parameter `Optional` in the function signature.

**Files amended**
- `backend/app/pipeline/overlap.py` — `question_id` parameter changed to `Optional[uuid.UUID]`; guard updated to `if question_id and oq.id == question_id`.
- `backend/app/routers/ingest.py` — overlap call site updated to `question_id=None`.

---

### Fix: Text ingest silently truncated input at 50,000 chars (Bug #16)
**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Replaced silent `text[:50000]` truncation with an explicit HTTP 413 that tells the caller the actual length and the limit. Inputs within the limit are now stored verbatim (slice removed).

**Files amended**
- `backend/app/routers/ingest.py` — length check added in `ingest_text`; `text[:50000]` slice removed from `pass1_json` construction.

---

## 2026-05-10

### Backend — OCR integration (Phases 1–8)
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Implemented the OCR pipeline described in `docs/PRD/INGESTION_PRD.md` §8.
Scanned PDFs and image uploads now route through an OCR gate before Pass 1
extraction. Admin selects strategy per-job; both providers are configured
simultaneously. Text-layer PDFs are completely unaffected.

**New files**

- `backend/app/parsers/ocr.py` — `DeepSeekOCRClient`: thin HTTP client for
  DeepSeek-OCR-2 running locally via vLLM Docker or LMDeploy.
- `backend/tests/test_ocr.py` — 15 unit tests covering both OCR providers,
  helper functions, and the vision extraction prompt.

**Backend changes**

- `config.py` — Added `deepseek_ocr_base_url` and `deepseek_ocr_model`
  settings (Option A config alongside the existing Ollama VLM settings).
- `llm/base.py` — Added `ImageContent` dataclass and optional
  `complete_vision()` method to `LLMProvider` protocol.
- `llm/ollama_provider.py` — Implemented `complete_vision()` using Ollama's
  existing `/v1/chat/completions` endpoint with `image_url` content blocks.
- `llm/factory.py` — Added `get_ocr_client()` factory; `DeepSeekOCRClient`
  is registered in the provider registry so `close_all_providers()` cleans up.
- `prompts/extract_prompt.py` — Added `build_vision_extract_prompt()` for the
  Ollama VLM fused path (no raw text in user message; model reads from images).
- `parsers/pdf_parser.py` — Added `page.get_pixmap()` fallback: scanned pages
  with no extractable text and no embedded images are now rasterized at 144 DPI
  and returned as page images for the OCR gate.
- `routers/ingest.py` — Core pipeline changes:
  - `_collect_page_images()` helper reads `pass1_json._page_images`.
  - `_resolve_ocr_strategy()` helper resolves `deepseek | ollama | auto`.
  - OCR gate inserted in `_run_pipeline()` at the `no_raw_text` branch:
    - **DeepSeek path (Option A):** calls `DeepSeekOCRClient.extract()` →
      populates `raw_text` → existing Pass 1 runs unchanged.
    - **Ollama VLM path (Option B):** calls `provider.complete_vision()` →
      fused OCR+extraction → `pass1_json` populated → Pass 1 skipped via
      `"_vision_fused_"` sentinel.
  - Both `ingest_official_pdf()` and `ingest_unofficial_file()` now accept
    optional `ocr_strategy` form param (`deepseek | ollama | auto`).
  - `_page_images` pre-stored in `pass1_json` at route time for scanned PDFs.
  - Image uploads (`.png`, `.jpg`, `.webp`, `.gif`) accepted via
    `ingest_unofficial_file()`; the previous 422 "not yet implemented" block
    is removed.

**Tests added / modified**

- `tests/test_ocr.py` (new) — `test_deepseek_ocr_returns_text`,
  `test_deepseek_ocr_sends_image_url_block`, `test_ollama_complete_vision_*`,
  `test_collect_page_images_*`, `test_resolve_ocr_strategy_*`,
  `test_build_vision_extract_prompt_*`
- `tests/test_ingest_router.py` — `test_ingest_official_pdf_rejects_invalid_ocr_strategy`,
  `test_ingest_unofficial_file_rejects_invalid_ocr_strategy`

**Verification**

- Ran `pytest` from `backend/`.
- Final suite result: `197 passed, 2 skipped`.

---

## 2026-05-09

### Backend — bug fixes and gap closures
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Found and fixed four confirmed bugs via code audit and new regression tests.
Suite went from 178 to 184 collected tests; all pass.

**Fixes**

- `POST /api/submit` — added `practice_status == "active"` guard before
  recording a student answer; previously draft/retired questions were accepted.
- `POST /api/users` (student router) — removed inline `UserCreate` model that
  had no field constraints; now imports `UserCreate`/`UserResponse` from
  `app.models.payload`, which enforces `min_length=1, max_length=100`. Empty
  and oversized usernames were previously accepted at this endpoint while
  the canonical `/users` router rejected them.
- `POST /admin/relations` — added self-reference guard; a question can no
  longer be related to itself (returns 400).
- `GET /admin/relations` — added `limit` (default 100, max 500) and `offset`
  query params; the endpoint previously returned all rows without a cap.

**Tests added**

- `test_submit_answer_rejects_non_active_question`
- `test_admin_create_relation_rejects_self_reference`
- `test_api_users_empty_username_rejected`
- `test_api_users_username_too_long_rejected`
- `test_admin_relations_list_accepts_pagination`
- `test_admin_relations_list_rejects_zero_limit`

**Verification**

- Ran `pytest` from `backend/`.
- Final suite result: `182 passed, 2 skipped`.

---

## 2026-05-06

### Backend — prompt rule-file fix and green test suite
**LLM:** Codex GPT-5

Fixed the backend regressions found during the backend task audit and restored
the full backend test suite to green.

**Prompt-layer changes**

- Corrected the Grammar v7 rule-file reference used by annotation and
  generation prompts:
  - from `rules_agent_dsat_grammar_ingestion_generetion_v7.md`
  - to `rules_agent_dsat_grammar_ingestion_generation_v7.md`
- Added explicit Grammar v7 and Reading v2 rules-reference headers to prompt
  context output so tests can verify that the current rule files are actually
  loaded.
- Kept `build_annotate_prompt` compatible with the older `extract_json=...`
  keyword argument while supporting the current `q_data` call shape.

**Test and compatibility changes**

- Updated ingest pipeline prompt invocation to remain compatible with existing
  test doubles while still passing source metadata to extraction prompts.
- Updated stale backend tests/mocks for the current parser and admin-edit query
  behavior.
- Aligned the config default test with the actual default annotation provider:
  `anthropic`.

**Verification**

- Ran `uv run pytest` from `backend/`.
- Final suite result: `176 passed, 2 skipped`.

### Docs — backend audit cleanup
**LLM:** Codex GPT-5

- Replaced stale backend gap reports with historical-audit notices, resolved
  item summaries, and a current remaining-work list.
- Updated active backend API docs to clarify that direct image OCR ingestion is
  not implemented and image uploads are rejected with 422.
- Updated ingestion-flow docs to reflect current Grammar v7 / Reading v2 prompt
  loading behavior.
- Refreshed the backend review report to remove resolved risks around provider
  API-key selection, source metadata, MIME validation, asset overwrite behavior,
  async relationship access, and missing endpoint/overlap/logging work.

## 2026-04-30

### Backend — metadata persistence, guide-file runtime wiring, and validator alignment
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Aligned the backend more closely with the newer grammar and reading rule
documents while keeping the existing DB schema and migration chain intact.

**Persistence and API changes**

- Preserved structured annotation sections during normalization instead of
  flattening them away, so `annotation_jsonb` can retain richer model output
  while still exposing flat keys needed by the app
- Started persisting `generation_profile_jsonb` on `question_annotations`
  instead of writing `NULL` in generate/ingest flows
- Merged generation request metadata into stored generation profile payloads
  for generated questions
- Exposed stored `generation_profile` through:
  - admin recall API (`/questions/recall`)
  - student recall API (`/api/questions`)
  - admin detail API (`/questions/{question_id}`)
- Added backend documentation file:
  - `docs/backend/INGESTION_AND_STORAGE_FLOW.md`
  - explains ingest/generate flow, persisted data, prompt usage, required
    runtime process, and includes a Mermaid diagram

**Prompt-layer changes**

- Updated annotation prompt loading to use the newer guide markdown files at
  runtime instead of only the old v3 grammar file:
  - `rules_agent_dsat_grammar_ingestion_generetion_v7.md`
  - `rules_agent_dsat_reading_v2.md`
- Updated generation prompts to also inline trimmed excerpts of the newer
  grammar and reading rule files into the system prompt

**Ontology and validation changes**

- Expanded `STEM_TYPE_KEYS` to include newer reading/cross-text stems such as:
  - `choose_words_in_context`
  - `choose_cross_text_connection`
  - `choose_best_inference`
  - `choose_command_of_evidence_textual`
  - `choose_command_of_evidence_quantitative`
- Expanded grammar focus coverage for v7 additions:
  - `adjective_adverb_distinction`
  - `illogical_comparison`
  - `commonly_confused_words`
  - `preposition_idiom`
  - `unnecessary_internal_punctuation`
  - `end_punctuation_question_statement`
- Added reading taxonomy constants:
  - `READING_SKILL_FAMILY_KEYS`
  - `READING_FOCUS_BY_SKILL_FAMILY`
  - `READING_FOCUS_KEYS`
- Added `partial_match` to supported distractor types
- Relaxed the annotation schema so reading-domain items do not require
  `grammar_focus_key`
- Added reading-domain annotation fields including:
  - `skill_family_key`
  - `reading_focus_key`
  - `secondary_reading_focus_keys`
  - `reasoning_trap_key`
  - `transition_subtype_key`
- Validator now enforces:
  - reading-domain questions must not set grammar keys
  - reading-domain questions require `skill_family_key`
  - reading-domain questions require `reading_focus_key`
  - `reading_focus_key` must match the chosen reading skill family
  - Cross-Text items require `stimulus_mode_key="prose_paired"`
  - Cross-Text items require `paired_passage_text`
  - Quantitative CoE items require `prose_plus_table` or `prose_plus_graph`
  - Quantitative CoE items require `table_data` or `graph_data`
  - grammar role/focus pairing is checked against the updated v7 role map

**Test coverage**

- Added and updated tests for:
  - prompt runtime rule loading
  - generation-profile persistence
  - response model exposure of generation metadata
  - v7 grammar key acceptance
  - reading taxonomy key acceptance
  - reading-domain validator enforcement
- Verification runs completed:
  - `uv run pytest tests/test_parsers.py tests/test_backend_regressions.py -q`
  - `uv run pytest tests/test_schemas.py tests/test_questions_router.py tests/test_student_router.py tests/test_backend_regressions.py -q`
  - `uv run pytest tests/test_prompts.py tests/test_parsers.py tests/test_backend_regressions.py tests/test_generate_router.py tests/test_ingest_router.py -q`
  - `uv run pytest tests/test_ontology.py tests/test_schemas.py tests/test_pipeline.py tests/test_prompts.py -q`
  - `uv run pytest tests -q`
- Final suite result: `165 passed, 2 skipped`

**Known warning**

- Confirmed that the remaining SWIG-related deprecation warnings during tests
  come from `PyMuPDF` / `fitz` import initialization, not from project code.
  Reproduced with:
  - `uv run python -Wdefault -c "import warnings; warnings.simplefilter('default'); import fitz"`
  - warnings observed: `SwigPyPacked`, `SwigPyObject`, `swigvarlink`

## 2026-04-29

### Rules — Grammar v7 taxonomy audit and corrections
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Created `rules_agent_dsat_grammar_ingestion_generetion_v7.md` — taxonomy
corrections and additions derived from a cross-referenced audit of the v6
taxonomy against official College Board documentation (Assessment Framework,
Sample Questions PDF, score report skill labels), Khan Academy, The Critical
Reader, PrepScholar, Test Innovators, Albert.io, and released PT1–PT11.

#### Amendment Table

| Amendment | Type | Section | Detail |
|---|---|---|---|
| `skill_family` corrected to official CB names | **Fix** | C.1.3, A.3, B.12 | Replaced non-official values (`Sentence Boundaries`, `Agreement`, `Punctuation`, `Craft and Structure`) with the two official SEC skill names: `Boundaries` and `Form, Structure, and Sense`. All 10 official R&W skill families now enumerated, grouped by domain. |
| `skill_family` example in A.3 schema | **Fix** | A.3 | Example value corrected from `"Agreement"` → `"Form, Structure, and Sense"` |
| `skill_family` in Example A (B.12) | **Fix** | B.12 | Corrected from `"Agreement"` → `"Form, Structure, and Sense"` |
| `stem_type_key` expanded | **Addition** | C.1.2 | Added 5 missing official question types: `choose_words_in_context` (Words in Context — most frequent type, ~28% of section), `choose_cross_text_connection` (Cross-Text Connections), `choose_best_inference` (Inferences), `choose_command_of_evidence_textual` (Command of Evidence textual), `choose_command_of_evidence_quantitative` (Command of Evidence quantitative). Total: 12 → 17 values. Legacy aliases noted for `choose_best_support`, `choose_best_quote`, `choose_best_completion_from_data`. |
| `topic_broad` expanded | **Addition** | C.1.3 | Added `humanities` — official College Board fourth content area alongside Literature, History/Social Studies, and Science. Clarified that `arts`, `economics`, `technology`, `environment` are project-internal sub-tags, not official CB labels. |
| `stimulus_mode_key` descriptions | **Clarification** | C.1.1 | Added inline descriptions for all 8 values. `prose_plus_graph` now lists all confirmed graphic subtypes: bar chart, line graph, scatterplot (with or without line of best fit), pie chart, map. |
| `restatement_clarification` transition | **Addition** | B.5.2 | Added 24th `transition_subtype_key`: `restatement_clarification` — covers "in other words / that is / i.e." transitions that rephrase rather than add or contrast. |
| `adjective_adverb_distinction` promoted | **Promotion** | D.2.5 | Moved from pending (D.2.9) to production under `modifier`. Covers adjective vs. adverb selection after linking verbs ("feel bad" not "feel badly"). Added to D.8.1 role→focus mapping and D.8.3 frequency table at `medium`. |
| `illogical_comparison` promoted | **Promotion** | D.2.5 | Moved from pending (D.2.9) to production under `modifier`. Covers comparing nouns to dissimilar categories ("results of Study 1 were better than Study 2"). Distinct from `comparative_structures` (formal parallelism) — this error is logical. Added to D.8.1 and D.8.3 at `medium`. |
| `commonly_confused_words` promoted | **Promotion** | D.2.8 | Moved from pending (D.2.9) to production under `expression_of_ideas`. Covers non-homophone semantic confusion pairs (affect/effect, allusion/illusion, elicit/illicit, principle/principal). Homophone possession confusion remains under `possessive_contraction`. Added to D.8.3 at `low`. |
| `preposition_idiom` added | **Addition** | D.2.8 | New production focus key under `expression_of_ideas`. Covers verb-preposition and adjective-preposition collocations where the correct preposition is idiomatic (responsible *for*, different *from*, composed *of*, interested *in*). Added to D.8.1 mapping and D.8.3 at `low`. |
| `affirmative_agreement` flagged | **Confidence flag** | D.2.2, D.8.3 | Marked `dsat_confidence: low`. so/neither inversion and tag questions appear primarily in ACT conventions. Retained in taxonomy for completeness but excluded from generation weighting. |
| `negation` flagged | **Confidence flag** | D.2.4, D.8.3 | Marked `dsat_confidence: low`. Double negatives and hardly/scarcely inversions are ACT patterns. Key retained only for scope-of-negation coverage ("not all" vs "all not"); excluded from generation profiles. |
| D.2.9 pending keys updated | **Housekeeping** | D.2.9 | Removed three promoted keys. Only `subjunctive_mood` remains pending (too rare for standalone key; documented as `verb_form` sub-pattern). |
| D.8.1 role→focus mapping updated | **Update** | D.8.1 | `modifier` row extended with `illogical_comparison` and `adjective_adverb_distinction`. `expression_of_ideas` row extended with `commonly_confused_words` and `preposition_idiom`. |
| D.8.2 domain separation table updated | **Update** | D.8.2 | Added official skill family column showing the 10 CB skill names by domain. |
| D.8.3 frequency table updated | **Update** | D.8.3 | New keys placed: `adjective_adverb_distinction` and `illogical_comparison` at `medium`; `commonly_confused_words` and `preposition_idiom` at `low`; `affirmative_agreement` and `negation` marked ⚠️ at `very_low`. |
| `model_version` bumped | **Housekeeping** | A.3, B.12 | All `model_version` fields updated from `rules_agent_v6.0` → `rules_agent_v7.0`. |

**Sources consulted:** College Board Assessment Framework PDF, Digital SAT Sample Questions PDF, Khan Academy DSAT R&W course, The Critical Reader grammar analysis, PrepScholar SAT grammar guide, Test Innovators skill breakdown, Albert.io quantitative evidence review, dsat16.com transitions guide.

---

### Rules — Grammar v6 reorganization and gap fixes
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Created `rules_agent_dsat_grammar_ingestion_generetion_v6.md` — a structural
reorganization of v5 for generation-first LLM navigation.

**Structural changes:**

- Reorganized into five explicit parts: A (Mode Routing) → B (Generation) →
  C (Annotation) → D (Taxonomy Reference) → E (Quality Protocols)
- Generation workflow (Part B) now precedes annotation workflow (Part C)
- §20 megasection decomposed into 15 focused B.x subsections
- §30 (Transition Subtypes) and §31 (Notes Synthesis) integrated inline into
  Part B rather than appended as addenda

**Gaps fixed:**

- Broken `§20.5` reference replaced with two complete inline JSON generation
  examples (B.12): `subject_verb_agreement` medium-difficulty and
  `transition_logic` medium-difficulty
- Missing `classification` schema added to formal schemas (A.3)
- `synthesis_distractor_failure` field name standardized: per-option
  annotation uses `synthesis_distractor_failure` (singular string);
  generation input uses `distractor_synthesis_failures` (plural array)
- Mode-routing section added (A.2) with explicit generation vs annotation
  trigger conditions
- Four proposed focus keys documented with pending status in D.2.9:
  `adjective_adverb_distinction`, `illogical_comparison`,
  `commonly_confused_words`, `subjunctive_mood`
- `transition_subtype_key` vs `target_transition_subtype_key` naming
  clarified in B.5.1: stored annotation field vs generation request field

---

### Rules — CB PT4–PT11 gap analysis and v3.1 / v1.1 rule addenda
**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)

Cross-referenced official College Board answer explanations for Practice Tests 4–11
(sourced from `CB_ANSWERS_QUESTIONS_ANALYSIS.md`) against both production rule files.
Created two new addendum files covering every identified gap.

**Files created:**

- `rules_agent_dsat_grammar_ingestion_generation_v3_1.md`
- `rules_agent_dsat_reading_v1_1.md`

---

**`rules_agent_dsat_grammar_ingestion_generation_v3_1.md`**

*Addendum to `rules_agent_dsat_grammar_ingestion_generation_v3.md`*

- Added punctuation focus key `unnecessary_internal_punctuation` — covers
  absence-of-punctuation cases inside subject–verb, verb–object,
  preposition–complement, and integrated relative clause units (PT4, PT5,
  PT6, PT7, PT9, PT11)
- Added punctuation focus key `end_punctuation_question_statement` — period
  on indirect questions vs question mark on direct questions (PT6, PT11)
- Extended `appositive_punctuation` with three sub-patterns: restrictive
  appositive (no punctuation), title/role before proper name (no punctuation),
  coordinated restrictive appositive (no punctuation) (PT5, PT8, PT9)
- Added three named verb form generation patterns with passage templates and
  distractor constraints: `finite_verb_in_relative_clause`,
  `finite_verb_in_main_clause`, `modal_plus_plain_form` (PT5, PT8, PT9)
- Added `singular_event_reference` pronoun generation pattern — singular
  pronoun referring to a whole preceding clause or event, not a noun (PT5)
- Added `literary_present` to `passage_tense_register_key` — simple present
  when discussing events inside literary works (PT10)
- Added `transition_subtype_key` field with 23 named subtypes covering every
  transition word pattern observed in PT4–PT11; required on generation profiles
  and wrong-option annotations
- Added three metadata fields for notes synthesis generation:
  `synthesis_goal_key` (41 values), `audience_knowledge_key` (3 values),
  `required_content_key` (30 values); added `synthesis_distractor_failure`
  for wrong-option annotation
- Added `test_format_key` field distinguishing `digital_app_adaptive` (27 Qs)
  from `nondigital_linear_accommodation` (33 Qs) with validated
  domain-boundary position bands
- Added 11 grammar-specific `student_failure_mode_key` values
- Added 8 new validator checklist items (checks 18–25)

---

**`rules_agent_dsat_reading_v1_1.md`**

*Addendum to `rules_agent_dsat_reading_v1.md`*

- Added `polarity_fit` Words in Context focus key — for items where a negator
  or concessive ("by no means," "not atypical") reverses required word polarity
  (PT4, PT5, PT6); includes generation rule requiring all four options to
  remain viable after applying the negator
- Added `polarity_mismatch` reasoning trap key
- Added phrase-level WIC generation note — when the correct answer is a
  multi-word phrase, all options must match in length and structure
- Added 12 named functional roles for `sentence_function` items (concession,
  elaboration, contrast_motivation, parenthetical_definition, example,
  consequence, hypothesis, counter_evidence, scope_qualification,
  conventional_approach, obstacle, background_setup); `target_sentence_function_role`
  now required in generation profiles
- Added parenthetical-definition generation constraint — correct answer must
  identify term clarification, not broader passage purpose (PT7, PT11)
- Added 8 named quantitative sub-patterns with primary distractor traps:
  `exact_value_lookup`, `timing_constrained`, `all_measures`, `repeated_highest`,
  `two_variable_opposite`, `composition_change`, `binned_distribution`, `standard`
- Added 5 new quantitative reasoning trap keys: `wrong_row_or_column`,
  `wrong_time_window`, `all_measures_not_checked`, `individual_from_aggregate`,
  `direction_reversal`
- Added all 5 experimental passage architectures:
  `experiment_hypothesis_control_result`, `indirect_effect_mediation`,
  `alternative_explanation_ruled_out`, `mechanism_manipulation_test`,
  `studied_subgroup_generalization_limit`
- Added `study_design_isolation_limit` inference pattern — when passage design
  prevents isolating a causal variable (PT6, PT10)
- Added `subgroup_overgeneralization` inference pattern with generation
  template (PT11)
- Added two-part claim annotation rule for quote-illustration items — at least
  one distractor must satisfy exactly one of two required elements
- Added control-group distractor pattern for experimental architecture items
- Added `confirmation_with_qualification` generation note for cross-text items
- Added 10 new student failure mode keys
- Added 9 new validator checklist items

---

## 2026-04-27

### 14:35 — Added missing indexes to SQLAlchemy models
**Commits:** *(pending)*

- Added `Index()` declarations to `models/db.py` `__table_args__` to match migration 005:
  - `Question`: `ix_questions_practice_status`, `ix_questions_content_origin`, `ix_questions_latest_annotation_id`
  - `QuestionJob`: `ix_question_jobs_status`, `ix_question_jobs_created_at`
  - `UserProgress`: `ix_user_progress_user_id`, `ix_user_progress_question_id`
  - `QuestionRelation`: `ix_question_relations_from_question_id`, `ix_question_relations_to_question_id`
- Added `Index` import to `models/db.py`

### Rules — Grammar module expansion and realism rules upgrade

Files changed: `rules/mcq_realism_rules.md`, `rules/rules_grammar_module_outline.md`, `rules/rules_core_generation_outline.md`, `rules/rules_reading_module_outline.md`

**`mcq_realism_rules.md`**

- Added **All-Four-Plausible Rule** section: every answer choice — including all three distractors — must produce plausible English on first read; nothing eliminable by ear-test alone; includes difficulty gradient table (low/medium/high)
- Added **Student Failure Mode Requirement** section: 16 named psychological failure modes (`nearest_noun_reflex`, `comma_fix_illusion`, `formal_word_bias`, `possessive_contraction_confusion`, `tense_proximity_pull`, `parallel_shape_bias`, `pronoun_anchor_error`, `ear_test_pass`, etc.) now mandatory on every distractor via `student_failure_mode_key`
- Added **SEC Distractor Architecture by Grammar Type** section: specific 4-option construction rules for all grammar categories including subject-verb agreement, verb tense, semicolons, apostrophes, modifiers, parallel structure, pronouns, adjective/adverb, illogical comparisons, sentence boundary, subjunctive mood, and transitions
- Added **Step 2 (Syntactic Trap)** to Generator Workflow: trap must be named before distractors are written
- Added **Step 6 (All-Four-Plausible Verification)**: explicit read-aloud check inserted before competitive ranking check
- Added **Hard-Item Validator Checklist**: additional validation layer for `difficulty_overall: high` — no shared failure modes across distractors, correct answer not the only formal-sounding option, ear-test cannot resolve the item

**`rules_grammar_module_outline.md`**

- Converted from planning outline to full operational document
- Full taxonomy tables for all grammar role keys and focus keys
- Added 4 grammar types from research that were absent from the taxonomy:
  - `adjective_adverb_distinction` (proposed key, parent: `modifier`)
  - `illogical_comparison` (proposed key, parent: `modifier`)
  - `commonly_confused_words` (proposed key, parent: `expression_of_ideas`)
  - `subjunctive_mood` (added to `verb_form` family)
- Added correlative conjunction rules under `parallel_structure` (both/and, either/or, neither/nor, not only/but also)
- Added syntactic trap taxonomy table with grammar focus mappings
- Added passage construction templates for every grammar focus key
- Added distractor heuristic tables with `student_failure_mode_key` for every focus key
- Added frequency band table for all focus keys
- Added full grammar validation checklist

**`rules_core_generation_outline.md`**

- Converted from planning outline to full shared infrastructure document
- Added SAT Realism Layer (Section 8): distractor distance, plausible wrong count, answer separation strength, all-four-plausible requirement, realism scoring thresholds
- Added shared distractor engineering rules with `student_failure_mode_key` requirement
- Added anti-clone and diversity controls
- Added provenance and audit trail schema
- Added shared validation lifecycle with core checklist

**`rules_reading_module_outline.md`**

- Added Section 14 with reading-specific `student_failure_mode_key` values: `local_detail_fixation`, `overreach`, `underreach`, `text_label_swap`, `topic_association`, `inverse_logic`, `false_agreement`
- Added realism requirements aligned to core (all-four-plausible requirement for reading items)

---

## 2026-04-25

### 18:10 — Option annotation hydration & metadata lifecycle management
**Commits:** `26ba7e9`

- Added `backend/app/pipeline/option_hydration.py` — shared helpers to extract, apply, and clear the 12 per-option annotation fields (`distractor_type_key`, `semantic_relation_key`, `plausibility_source_key`, `option_error_focus_key`, `why_plausible`, `why_wrong`, `grammar_fit`, `tone_match`, `precision_score`, `student_failure_mode_key`, `distractor_distance`, `distractor_competition_score`) from `annotate_json` to `QuestionOption` rows
- Ingest pipeline (`_run_pipeline`): all `QuestionOption` annotation columns now populated on creation
- Ingest reannotation (`_run_reannotate_pipeline`): existing option rows refreshed with new annotation; `annotation_stale` cleared to `False` on success
- Generate pipeline: identical option annotation hydration on first creation
- `models/db.py` — added `annotation_stale` boolean to `Question`
- Migration `009_add_annotation_stale`: adds `annotation_stale` column with `server_default=false`
- Admin `PATCH /questions/{id}`: sets `annotation_stale=True` on any edit — flags question for reannotation queue
- Admin `POST /questions/{id}/reject`: cascade-deletes `question_annotations`, `llm_evaluations`, `question_relations`; nulls per-option annotation fields; retires question
- Admin `DELETE /questions/{id}` (new endpoint): hard-deletes question and all linked rows in safe FK order; detaches jobs and assets (preserves audit trail and files on disk)

---

### 17:47 — PDF filename typo fix
**Commits:** `7b3f5dd`

- Renamed `Test_10_digitial_sec01_mod02.pdf` → `Test_10_digital_sec01_mod02.pdf` in `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/`

---

### 17:07 — Verbal practice test PDFs added
**Commits:** `bbd5c12` *(pulled from remote)*

- Added 14 verbal section PDFs for Practice Tests 1, 6–11 (both `sec01_mod01` and `sec01_mod02`) to `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/`
- Validated all 18 PDFs: readable, unencrypted, 13–16 pages, 28k–35k chars each
- Note: Test 11 mod01/mod02 have zero embedded images (vector-rendered); all other tests have 14–17 embedded images per file
- Documented canonical test source path in `CLAUDE.md`

---

### 15:45 — DB integrity gap remediation (6 gaps)
**Commits:** `ba88685`

- Migration `004_add_unique_constraints`: `UniqueConstraint` on `question_versions(question_id, version_number)`, `question_options(question_version_id, option_label)`, `question_relations(from_question_id, to_question_id, relation_type)`
- Migration `005_add_performance_indexes`: 9 indexes on hot query columns across `questions`, `question_jobs`, `user_progress`, `question_relations`
- Migration `006_add_check_constraints`: DB-level `CHECK` constraints mirroring Pydantic validation — option labels A–D, LLM scores 0–10, relation strength 0–1
- Migration `007_add_source_section_code_to_assets`: adds `source_section_code` to `question_assets`
- Migration `008_add_server_defaults`: `server_default=now()` on all 12 timestamp columns across all tables
- `models/db.py`: added `UniqueConstraint` `__table_args__` to `QuestionVersion`, `QuestionOption`, `QuestionRelation`; added `source_section_code` to `QuestionAsset`
- `routers/ingest.py`: write `source_section_code` to asset at upload time; backfill from `extract_json` during pipeline link-back
- `migrations/env.py`: fixed `else` branch that silently discarded `-x sqlalchemy.url` override; `run_migrations_online()` now reads URL from config instead of hardcoding `settings.database_url`

---

## 2026-04-24

### 20:09 — User CRUD endpoints
**Commits:** `8e45fa5`

- Added `POST /users`, `GET /users/{id}`, `DELETE /users/{id}` with admin auth

### 20:08 — N+1 query fix in overlap detection
**Commits:** `ff11b72`

- Replaced N+1 annotation queries in `detect_overlaps` with a single JOIN

### 20:07 — V3 ontology key validation
**Commits:** `1586ffc`

- Validator now checks `grammar_role_key`, `grammar_focus_key`, `stimulus_mode_key`, `stem_type_key` against approved V3 keys; `explanation_short` capped at 300 chars

### 20:04 — LLM provider cleanup on shutdown
**Commits:** `e7ca0bb`

- Closed `httpx` clients for all LLM providers on app shutdown via FastAPI lifespan

### 20:01 — Generation provider selection
**Commits:** `bfce92f`

- Caller can now specify `provider_name` and `model_name` in generate requests

### 20:00 — Reannotation request body fix
**Commits:** `09cfb6b`

- Moved `provider_name`/`model_name` from query params to JSON body in reannotate endpoint

### 19:59 — Upload size guard
**Commits:** `55ca86c`

- Check `Content-Length` before reading upload body to avoid loading 50 MB into RAM

### 15:05 — API routers and integration tests
**Commits:** `3d19244`

- Added 5 API routers with 19 endpoints; integration test suite

### 14:18 — Request/response schemas and API docs
**Commits:** `33e8d88`

- Added generation/ingest request schemas, job response model, OpenAPI docs

### 13:11 — Migration order, Docker Postgres, manual test CLI
**Commits:** `ce423ba`

- Fixed migration ordering; added Docker Postgres config; manual test CLI

### 12:35 — Prompts, pipeline orchestrator, validator
**Commits:** `198b7da`

- Extract and annotate prompts; `JobOrchestrator`; question validator

### 12:34 — Parsers
**Commits:** `f845a4c`

- JSON, PDF (pymupdf), image, and markdown extraction parsers

### 12:34 — LLM provider layer
**Commits:** `08b9133`

- Protocol, factory, Anthropic, OpenAI, and Ollama providers

### 12:13 — Initial migration
**Commits:** `b621316`

- Alembic config; 10-table initial schema migration
