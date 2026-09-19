# Admin Dashboard — Developer Documentation

> **Status:** Active. This document describes the implemented system as of 2026-09.
> Open issues are tracked in `admin_dashboard_issues.md`.

---

## 1. Overview

The admin dashboard is a standalone React/Vite single-page application (`APP/ADMIN_APP/`) that provides a web UI for managing DSAT questions, users, generation pipelines, review workflows, and analytics. It communicates with a FastAPI backend (`backend/app/`) via JSON over HTTP.

**Stack:** React 19 · TypeScript · Vite 8 · TanStack Query v5 · react-router-dom v7 · Tailwind v4 · react-grid-layout · framer-motion · recharts

**Auth:** Google OAuth (JWT) or legacy static API key. Both accepted on all admin endpoints.

---

## 2. Architecture

```
┌─────────────────────┐     Vite dev proxy      ┌──────────────────┐
│  APP/ADMIN_APP      │  /api/admin → /admin     │  FastAPI backend  │
│  (Vite SPA)         │  /api/users → /users     │  (port 8000)      │
│  port 5175 (dev)    │  /api/generate → /gen    │                   │
│  port 8444 (TLS)    │  /api/* → forwarded      │  Postgres (db)    │
└─────────────────────┘                         └──────────────────┘
```

### 2.1 Frontend (`APP/ADMIN_APP/`)

| Path | Role |
|---|---|
| `src/main.tsx` | Entry point — mounts `QueryClientProvider` → `BrowserRouter` → `App` |
| `src/App.tsx` | Route table, auth gate, error boundary, toast provider |
| `src/api/client.ts` | All HTTP calls — `adminApi`, `authApi`, `generateApi` objects + `apiCall()` fetch wrapper with 401 auto-refresh |
| `src/types/index.ts` | TypeScript interfaces mirroring backend payloads |
| `src/auth/AuthContext.tsx` | Auth state machine — Google login, token bootstrap, session management |
| `src/auth/RequireAdmin.tsx` | Route guard — redirects unauthenticated users to `/login` |
| `src/auth/authStore.ts` | Token persistence in `localStorage` (`auth.access_token`, `auth.refresh_token`, `auth.profile`) |
| `src/auth/useGoogleScript.ts` | Loads Google Identity Services script |
| `src/components/Layout.tsx` | Sidebar nav + collapsible layout shell |
| `src/components/ErrorBoundary.tsx` | Catches render errors, resets on route change |
| `src/components/Toast.tsx` | Toast notification provider |
| `src/components/PanelShell.tsx` | Drag-handle panel wrapper for the widget dashboard |
| `src/components/dashboard/widgets.tsx` | Five dashboard widgets (Users, Generation, AutoRelease, RecentBatches, WeakSpots) |
| `src/pages/Dashboard.tsx` | `/dashboard` — modular widget grid (react-grid-layout, localStorage persistence) |
| `src/pages/UserManagement.tsx` | `/users` — CRUD users, edit role/email, reset password, activate/deactivate |
| `src/pages/DataManagement.tsx` | `/data` — question browser with test explorer, detail/edit modal, approve/reject, stimulus assets, graph tagging |
| `src/pages/StudentPerformance.tsx` | `/students` — per-student stats, missed focus/trap keys, activity heatmap |
| `src/pages/PipelinePerformance.tsx` | `/pipeline` — generation/review analytics, batch table, auto-release controls |
| `src/pages/VocabularyGovernance.tsx` | `/vocabulary` — controlled-vocabulary master browser + off-vocab candidate queue |
| `src/pages/Generate.tsx` | `/generate` — batch question generation form with presets, live polling, retry-failed |
| `src/pages/LoginPage.tsx` | `/login` — Google sign-in button |

### 2.2 Backend routers

Routers are mounted in `backend/app/main.py` without extra prefixes unless noted:

| Router file | Prefix | Used by admin app | Purpose |
|---|---|---|---|
| `admin.py` | `/admin` | Yes (via Vite proxy strip) | Questions, generated questions, analytics, auto-release, vocab, amendments, review swarm, stimulus, relations |
| `users.py` | `/users` | Yes (via Vite proxy strip) | User CRUD, password reset |
| `student.py` | `/api` | Yes (direct) | Student stats, activity heatmap, study features (also used by student app) |
| `generate.py` | `/generate` | Yes (via Vite proxy strip) | Batch generation, batch polling, retry, batch review swarm |
| `student_auth.py` | `/api/auth` | Yes (direct) | Google login, token refresh, logout, `/me` |
| `dashboard.py` | `/dashboard` | No | Server-rendered HTML dashboard (separate, not consumed by React app) |
| `ingest.py` | `/ingest` | No | PDF ingestion pipeline |
| `questions.py` | `/questions` | No | Public question read API |
| `health.py` | `""` | No | Docker healthcheck |

### 2.3 Dev proxy and the `/api` prefix problem

The frontend sets `API_BASE = '/api'` for all calls. The Vite dev proxy (`vite.config.ts`) strips `/api` for three router prefixes:

| Proxy rule | Rewrite | Target router |
|---|---|---|
| `/api/admin` → | `/admin` | `admin.py` |
| `/api/users` → | `/users` | `users.py` |
| `/api/generate` → | `/generate` | `generate.py` |
| `/api/*` (everything else) | forwarded unchanged | `student.py`, `student_auth.py` (already at `/api`) |

> **Known issue (H5):** In production there is no Vite proxy. `admin.py` and `users.py` are mounted without `/api`, so `/api/admin/*` and `/api/users/*` 404 unless a reverse proxy performs the same rewrite. Fix: mount with `prefix="/api"` in `main.py` or configure the production reverse proxy. See `admin_dashboard_issues.md`.

### 2.4 Running the admin app

**Dev (host Vite server):**
```bash
./start.sh          # starts admin Vite dev server on :5175 + compose stack (backend on :8002)
```

The admin app runs as a host-level Vite dev server (not in Docker). `start.sh` also sets up Tailscale Serve for TLS on port 8444.

**Environment variables (`APP/ADMIN_APP/.env`):**

| Variable | Default | Purpose |
|---|---|---|
| `VITE_ADMIN_TOKEN` | `admin-test-key` | Legacy static API key. Set empty for Google-only auth. |
| `VITE_GOOGLE_CLIENT_ID` | `721127096332-...` | Google OAuth client ID. Must match `google_oauth_client_id` in backend `config.py`. |
| `VITE_BACKEND_ORIGIN` | `http://localhost:8002` | Backend URL for the Vite dev proxy. |
| `VITE_API_BASE` | `/api` | Base path for all API calls. |

---

## 3. Authentication

### 3.1 Two auth paths

| Method | Header(s) sent | Backend check | Use case |
|---|---|---|---|
| **Google OAuth (JWT)** | `Authorization: Bearer <access_token>` | `admin_required` decodes JWT, looks up `User`, checks `role == "admin"` | Normal admin login via Google sign-in |
| **Legacy API key** | `X-API-Key: <key>` | `admin_required` checks against `ADMIN_API_KEYS` config | Scripts, automated tools, dev shortcuts |

Both headers may be sent simultaneously — the backend checks Bearer JWT first, then falls back to the API key.

### 3.2 Token lifecycle

1. User clicks Google sign-in → Google Identity Services returns an ID credential.
2. Frontend sends `POST /api/auth/google` with the credential.
3. Backend exchanges it for a JWT pair: `{ access_token, refresh_token }`.
4. Frontend stores both in `localStorage` (`authStore.ts`).
5. Every subsequent request includes `Authorization: Bearer <access_token>`.
6. On 401, `apiCall()` transparently calls `POST /api/auth/refresh` with the refresh token, retries the original request once. If refresh fails, session is cleared and the user is redirected to login.

### 3.3 Auth dependencies (`backend/app/auth.py`)

| Dependency | Accepts | Used by |
|---|---|---|
| `admin_required` | JWT (Bearer) **or** API key (`X-API-Key`) | All `admin.py`, `users.py` endpoints |
| `student_required` | API key only | 20+ `student.py` routes |
| `student_jwt_required` | JWT **or** API key | Imported but **not yet used** in `student.py` (see issue H3) |
| `admin_or_student_required` | API key only | `student.py` routes that serve both roles |
| `admin_or_student_jwt_required` | JWT **or** API key | Imported but **not yet used** |

> **Known issue (H3):** `student.py` routes that the admin app calls (`/api/stats/{user_id}`, `/api/stats/{user_id}/activity`) use `student_required` (API-key-only), so JWT-authenticated admins get 403. The JWT-aware variants exist but are not wired in. See `admin_dashboard_issues.md`.

---

## 4. Features

### 4.1 Dashboard (`/dashboard`)

Modular widget grid built with `react-grid-layout`. Panels are draggable, resizable, and the layout persists to `localStorage`.

**Widgets:**

| Widget | Data source | Displays |
|---|---|---|
| UsersWidget | `GET /users` | Total users, active users count |
| GenerationWidget | `GET /admin/analytics/generation` | Generated/approved/rejected counts, acceptance rate |
| AutoReleaseWidget | `GET /admin/generation/auto-release/status` | Config enabled, runtime disabled, effective enabled, enable/disable buttons |
| RecentBatchesWidget | `GET /admin/analytics/batches` | Recent generation batches with status counts |
| WeakSpotsWidget | `GET /admin/analytics/weak-spots` | Cohort focus-area miss rates |

The dashboard is the default landing route (`/` redirects to `/dashboard`).

### 4.2 User Management (`/users`)

| Action | Endpoint | Method |
|---|---|---|
| List all users | `GET /users` | — |
| Create user | `POST /users` | Body: `{ username, email?, role?, is_active? }` |
| Edit user | `PATCH /users/{id}` | Body: `{ username?, email?, role?, is_active? }` |
| Reset password | `POST /users/{id}/reset-password` | Body: `{ new_password }` — clears refresh token, returns 204 |
| Delete user | `DELETE /users/{id}` | Returns 204 |

**Password hashing:** `hash_password()` from `backend/app/auth.py` (argon2 via `pwdlib`). Reset clears `refresh_token` / `refresh_token_expires` to invalidate existing sessions.

### 4.3 Data Management (`/data`)

Two browsing modes:

**Questions mode** — paginated table with filters:
- `practice_status`: `all` | `active` | `draft` | `rejected` (and `needs_review` mapped to `job_status` param)
- `content_origin`: `all` | `official` | `generated`
- `source_release_year`, `source_test_name`, `source_exam_code`, `source_subject_code`, `source_section_code`, `source_module_code`
- `sort_by_source=true` for Q# ordering

**Tests mode** — card grid from `GET /admin/tests`, grouped by `(year, test_name, exam_code, subject, section, module)`. Clicking a card filters questions to that test/section/module.

**Question detail/edit modal** (on row click):
- View: passage, question text, all 4 options (correct highlighted), explanation, annotation metadata (focus keys, difficulty, trap keys), `annotation_stale` badge
- Edit: question text, passage text, correct option label, explanation, change notes → `PATCH /admin/questions/{id}`
- Edit creates a new `QuestionVersion`, updates `Question.current_*` fields, sets `annotation_stale = True`, writes `AdminAuditLog`

**Row actions:**
- Approve → `POST /admin/questions/{id}/approve` (sets `practice_status = "active"`)
- Reject → `POST /admin/questions/{id}/reject` (sets `practice_status = "rejected"`, records reason)
- Delete → `DELETE /admin/questions/{id}`
- Graph tag → `POST /admin/questions/{id}/graph-tag` (toggles `source_has_graph`)

**Stimulus assets (sub-feature):**
- List assets → `GET /admin/questions/{id}/stimulus-assets`
- Upload → `POST /admin/questions/{id}/stimulus-assets` (multipart form)
- Delete → `DELETE /admin/questions/{id}/stimulus-assets/{asset_id}`
- Extract → `POST /admin/questions/{id}/extract-stimulus` (queues a `StimulusExtractionJob`)
- Poll job → `GET /admin/stimulus-extraction-jobs/{job_id}`

### 4.4 Student Performance (`/students`)

- Lists all users (does not currently filter to `role === 'student'` — see issue F3)
- Per-student expandable detail panel:
  - Stat tiles: total answered, total correct, accuracy
  - Activity heatmap: 53-week × 7-day GitHub-style grid from `GET /api/stats/{user_id}/activity?days=365`
  - Top missed focus keys and trap keys from `GET /api/stats/{user_id}`

### 4.5 Pipeline & Backend (`/pipeline`)

- Generation analytics: counts, acceptance rate, copy-risk failures, per-model breakdown, rejection reasons
- Batch analytics: aggregates (total requested/created/accepted/rejected/failed), recent batches table, token usage by provider
- Auto-release controls: status display + enable/disable buttons + audit log

### 4.6 Vocabulary Governance (`/vocabulary`)

- Master vocabulary browser: `GET /admin/vocab/master` — displays all controlled vocabularies (families, entries, statuses, descriptions)
- Off-vocab candidate queue: `GET /admin/vocab/candidates` — shows non-standard keys found during ingestion with occurrence counts, job IDs, and context snippets

### 4.7 Generate (`/generate`)

Batch question generation form with:
- Domain selection (grammar/reading) — toggles domain-specific fields
- All generation target parameters (focus keys, trap keys, difficulty, stimulus mode, stem type, etc.)
- Provider/model selection
- Preset save/load (localStorage)
- Draft persistence (localStorage)
- Batch creation → `POST /generate/batches`
- Live polling of batch status → `GET /generate/batches/{id}`
- Per-job status → `GET /generate/batches/{id}/questions`
- Retry failed jobs → `POST /generate/batches/{id}/retry-failed`

---

## 5. Generation & Review Pipeline

### 5.1 Generation flow

```
Admin (UI or API)
  │
  ├─ POST /generate/batches { requested_count, target_params, release_policy }
  │    → creates GenerationBatch + N QuestionJob rows
  │    → each job runs: LLM generate → parse → validate → persist → overlap check
  │    → on save: auto-triggers review swarm (_run_auto_review_swarm)
  │
  ├─ Poll GET /generate/batches/{id} until status is terminal
  │
  └─ POST /generate/batches/{id}/retry-failed (if any jobs failed)
```

**Key constraints:**
- Max batch size: 25 (`generation_max_batch_size`)
- Default batch size: 5 (`generation_default_batch_size`)
- Max pending batches: 20 (`generation_max_pending_batches`)
- Max retries per job: 3 (`generation_job_max_retries`)
- Idempotency: duplicate batch submissions within 24h are replayed, not re-run

**Release policies:**

| Policy | Behavior |
|---|---|
| `admin_review_required` (default) | Generated questions stay `draft` until admin approves |
| `auto_release_on_accept` | Eligible for auto-release (8-gate check, see below) |
| `dry_run` | Generate + review but do not persist questions |

### 5.2 Review swarm

Triggered automatically after each generated question is saved (`triggered_by = "auto_on_save"`), or manually via `POST /admin/questions/{id}/review-swarm`.

**Flow:**
```
run_review_swarm(question_id)
  │
  ├─ Create ReviewRun (status = "running")
  │
  ├─ For each configured provider (parallel, max 6 concurrent):
  │    ├─ Compose prompt: review rubric + grammar v8 rules + reading v3 rules (if reading question)
  │    ├─ Call LLM → parse JSON response
  │    ├─ Extract 7 scores + verdict + reasons
  │    └─ Write LlmReviewResult row
  │
  ├─ Exclude the generating provider from review (no self-review)
  │
  ├─ Compute consensus verdict (deterministic, first-match-wins)
  │    └─ Write ConsensusVerdict row
  │
  └─ Update ReviewRun (status = "completed")
```

**Review providers (configurable):**

| Config | Default | Options |
|---|---|---|
| `generation_review_providers` | `"ollama"` | Comma-separated: `openai`, `anthropic`, `ollama` |
| `generation_review_openai_model` | `"gpt-4o"` | Any OpenAI model |
| `generation_review_anthropic_model` | `"claude-sonnet-5"` | Any Anthropic model |
| `generation_review_ollama_model` | `"kimi-k3:cloud"` | Any Ollama-routed model |
| `generation_review_max_concurrent` | `6` | Parallel reviewer calls |
| `generation_review_max_retries` | `2` | Per-reviewer retry count |

### 5.3 Scoring dimensions (rubric v1)

Each reviewer returns 7 numeric scores (0–10, one decimal) and a verdict:

| Score | Threshold | Gate |
|---|---|---|
| `realism_score` | ≥ 7.0 | Below → `reject_recommended` |
| `sat_fidelity_score` | ≥ 7.0 | Below → `reject_recommended` |
| `difficulty_match_score` | — | Informational |
| `distractor_quality_score` | ≥ 6.5 | Below → `regenerate_recommended` |
| `taxonomy_match_score` | ≥ 7.5 | Below → `regenerate_recommended` |
| `explanation_quality_score` | — | Informational |
| `copy_risk_score` | ≤ 5.0 | Above → `reject_recommended` |

**Verdicts per reviewer:** `accept` | `needs_human_review` | `reject`

### 5.4 Consensus gate (deterministic, first-match-wins)

Algorithm (`review/consensus.py`):

| Priority | Condition | Consensus verdict |
|---|---|---|
| 1 | Unresolved official overlap | `blocked_overlap` |
| 2 | < 2 successful reviewer results | `insufficient_reviews` |
| 3 | Any reviewer's `copy_risk_score` ≥ threshold | `reject_recommended` |
| 4 | Average `realism_score` < threshold | `reject_recommended` |
| 5 | Average `sat_fidelity_score` < threshold | `reject_recommended` |
| 6 | Reviewer disagreement > threshold | `admin_review_ready` (with `high_disagreement_flag`) |
| 7 | Average `distractor_quality_score` < threshold | `regenerate_recommended` |
| 8 | Average `taxonomy_match_score` < threshold | `regenerate_recommended` |
| 9 | All thresholds cleared | `admin_review_ready` |

**Consensus is advisory.** No consensus verdict automatically changes `practice_status`. Only an explicit admin approve action flips `draft` → `active`.

### 5.5 Auto-release (Phase 10, disabled by default)

When `generation_auto_release_enabled = true` and `release_policy = "auto_release_on_accept"`, the system can auto-approve questions that pass all 8 gates:

1. `generation_auto_release_enabled` is `true`
2. Runtime kill switch (`_auto_release_disabled`) is `false`
3. Batch `release_policy == "auto_release_on_accept"`
4. Consensus verdict is `admin_review_ready`
5. `high_disagreement_flag` is `false`
6. `official_overlap_status == "none"`
7. Question's target matches at least one entry in `generation_auto_release_allowed_targets` (JSON)
8. The generator model has ≥ `generation_auto_release_min_reviews` (3) admin-reviewed questions with acceptance rate ≥ `generation_auto_release_min_accept_rate` (0.80)

Every auto-release writes an immutable `AutoReleaseAuditLog` row. The runtime kill switch can be toggled via `POST /admin/generation/auto-release/disable` without a restart.

**Config defaults:**

| Setting | Default |
|---|---|
| `generation_auto_release_enabled` | `false` |
| `generation_auto_release_min_reviews` | `3` |
| `generation_auto_release_min_accept_rate` | `0.80` |
| `generation_auto_release_allowed_targets` | `""` (empty = no targets match) |

---

## 6. Data Model (admin-relevant tables)

### 6.1 Core question tables

| Table | Purpose | Key columns |
|---|---|---|
| `questions` | Canonical question identity | `id`, `content_origin` (official/unofficial/generated), `practice_status` (draft/active/retired/rejected), `current_question_text`, `current_passage_text`, `current_correct_option_label`, `current_explanation_text`, `annotation_stale`, `is_admin_edited`, `official_overlap_status`, `generation_source_set` (JSONB), `is_canonical_source`, `rejection_reason`, `rejected_at`, `rejected_by_admin_token` |
| `question_versions` | Immutable content snapshots per edit/generation | `version_number`, FK → `questions` |
| `question_annotations` | LLM-managed taxonomy metadata | `annotation_jsonb` (focus keys, trap keys, difficulty, distractor types, etc.) |
| `question_options` | Per-option analysis (4 rows per question) | `option_label`, `option_text`, `is_correct`, `distractor_type_key`, `plausibility_source_key` |
| `question_assets` | Raw source files and extracted artifacts | FK → `questions` |
| `question_stimulus_assets` | Stimulus images/tables/graphs | `stimulus_type`, `url`, `structured_data` (JSONB) |
| `question_source_spans` | Character-level source evidence | FK → `questions` |
| `question_relations` | Cross-question linking and overlap detection | `from_question_id`, `to_question_id`, `relation_type` |

### 6.2 Generation & review tables

| Table | Purpose | Key columns |
|---|---|---|
| `generation_batches` | Batch generation orchestration | `id`, `requested_count`, `request_jsonb`, `release_policy`, `status`, `created_count`, `accepted_count`, `rejected_count`, `failed_count`, `needs_review_count` |
| `generation_batch_idempotency_keys` | Prevents duplicate batch submissions | `idempotency_key`, `requested_by`, `expires_at` |
| `question_jobs` | Per-question generation/ingestion job | `job_type`, `status`, `question_id`, `generation_batch_id`, `validation_errors_jsonb` |
| `review_runs` | Groups a set of reviewer results per review invocation | `question_id`, `triggered_by` (auto_on_save/manual/manual_batch), `status` (running/completed/failed), `rubric_version` |
| `llm_review_results` | Per-reviewer scores and verdicts | `review_run_id`, `provider_name`, `model_name`, `scores_jsonb`, `verdict` (accept/needs_human_review/reject), `review_status`, `latency_ms`, `token_usage_jsonb` |
| `consensus_verdicts` | Deterministic consensus from review swarm | `review_run_id`, `reviewer_count`, averages, vote counts, `consensus_verdict`, `high_disagreement_flag`, `reasons_jsonb` |
| `reviewer_admin_overrides` | Records when admin disagrees with a reviewer | `reviewer_verdict`, `admin_verdict`, `override_direction` |
| `llm_evaluations` | Beta model comparison scores (older, separate from review swarm) | `score_overall`, `score_metadata`, `score_explanation`, `score_generation` |

### 6.3 User & analytics tables

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Student and admin accounts | `id`, `username`, `email`, `password_hash`, `role` (student/admin), `is_active`, `user_token`, `refresh_token` |
| `user_progress` | Answer attempts and accuracy tracking | `user_id`, `question_id`, `is_correct`, `timestamp` |
| `diagnostic_sessions` | Diagnostic test sessions | `user_id`, `status`, `module1_results` (JSONB) |
| `admin_audit_log` | Immutable audit trail for admin actions | `question_id`, `admin_token`, `action`, `before_jsonb`, `after_jsonb`, `fields_changed` |

---

## 7. Complete Endpoint Reference

### 7.1 Admin router (`/admin` prefix, auth: `admin_required`)

#### Questions

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/questions` | List questions with filters (status, origin, source_*, pagination) |
| PATCH | `/admin/questions/{id}` | Edit question content (creates new version, sets annotation_stale) |
| DELETE | `/admin/questions/{id}` | Delete question |
| POST | `/admin/questions/{id}/approve` | Set practice_status → active |
| POST | `/admin/questions/{id}/reject` | Set practice_status → rejected (non-destructive, preserves audit trail) |
| POST | `/admin/questions/{id}/confirm-overlap` | Mark official overlap as confirmed |
| POST | `/admin/questions/{id}/clear-overlap` | Clear official overlap status |
| POST | `/admin/questions/{id}/graph-tag` | Toggle source_has_graph flag |
| POST | `/admin/questions/{id}/annotate-spans` | Trigger span annotation |
| GET | `/admin/tests` | Aggregated question counts grouped by test/section/module |

#### Generated questions

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/generated-questions` | List generated question candidates (defaults to draft status) |
| GET | `/admin/generated-questions/{id}` | Get single generated question with review results + consensus |
| GET | `/admin/generated-questions/{id}/report` | Markdown audit report for a generated question |
| POST | `/admin/generated-questions/{id}/approve` | Approve generated question → active |
| POST | `/admin/generated-questions/{id}/reject` | Reject generated question |
| POST | `/admin/generated-questions/{id}/regenerate` | Re-queue generation from a rejected item |

#### Review swarm

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/questions/{id}/review-swarm` | Manually trigger review swarm for a question |
| GET | `/admin/questions/{id}/review-runs` | List review runs for a question |

#### Stimulus assets

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/questions/{id}/stimulus-assets` | List stimulus assets for a question |
| POST | `/admin/questions/{id}/stimulus-assets` | Upload stimulus asset (multipart) |
| DELETE | `/admin/questions/{id}/stimulus-assets/{asset_id}` | Delete stimulus asset |
| POST | `/admin/questions/{id}/extract-stimulus` | Queue stimulus extraction job |
| GET | `/admin/stimulus-extraction-jobs/{job_id}` | Poll stimulus extraction job status |

#### Jobs & evaluations

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/jobs/{job_id}/fail` | Force-fail a stuck job |
| POST | `/admin/evaluations` | Create an LLM evaluation |
| POST | `/admin/evaluations/{id}/score` | Score an LLM evaluation |

> **Known issue (H2):** `GET /admin/jobs` (list endpoint) does not exist. The Jobs UI in the frontend calls it but gets 404. See `admin_dashboard_issues.md`.

#### Relations

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/relations` | List question relations |
| POST | `/admin/relations` | Create a question relation |
| DELETE | `/admin/relations/{id}` | Delete a question relation |

#### Analytics

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/analytics/generation` | Generation counts, acceptance rate, per-model stats, rejection reasons |
| GET | `/admin/analytics/review` | Review analytics (token usage, latency, reviewer agreement) |
| GET | `/admin/analytics/batches` | Batch aggregates, recent batches, token usage by provider |
| GET | `/admin/analytics/trends` | Time-series generation/review trends |
| GET | `/admin/analytics/export` | Export analytics as CSV/JSON |
| GET | `/admin/analytics/weak-spots` | Cohort focus-area miss rates |
| GET | `/admin/analytics/student-cohort-summary` | Per-student cohort summary |
| GET | `/admin/analytics/trap-analytics` | Trap key analytics across cohort |

#### Auto-release

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/generation/auto-release/status` | Current config + runtime kill switch state |
| POST | `/admin/generation/auto-release/enable` | Enable auto-release |
| POST | `/admin/generation/auto-release/disable` | Disable auto-release (runtime kill switch, no restart) |
| GET | `/admin/generation/auto-release/audit` | Audit log of auto-release decisions |

#### Vocabulary governance

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/vocab/master` | Controlled-vocabulary master file (all canonical keys) |
| GET | `/admin/vocab/candidates` | Off-vocabulary candidate review queue |

#### Amendments

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/amendments` | List grammar rule amendment proposals |
| GET | `/admin/amendments/{id}` | Get single amendment |
| POST | `/admin/amendments/{id}/approve` | Approve amendment |
| POST | `/admin/amendments/{id}/reject` | Reject amendment |
| POST | `/admin/amendments/{id}/request-more-evidence` | Request more evidence for amendment |
| POST | `/admin/amendments/{id}/promote` | Promote amendment to canonical rules |

### 7.2 Users router (`/users` prefix, auth: `admin_required`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/users` | Create user (`{ username, email?, role?, is_active? }`) |
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get single user |
| PATCH | `/users/{id}` | Update user (`{ username?, email?, role?, is_active? }`) |
| POST | `/users/{id}/reset-password` | Reset password (clears refresh token, returns 204) |
| DELETE | `/users/{id}` | Delete user (returns 204) |

### 7.3 Generate router (`/generate` prefix, auth: `admin_required`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/generate/questions` | Single question generation (legacy, pre-batch) |
| POST | `/generate/questions/compare` | Multi-model comparison generation |
| GET | `/generate/runs/{run_id}` | Get generation run status |
| POST | `/generate/batches` | Create generation batch |
| GET | `/generate/batches/{id}` | Poll batch status |
| GET | `/generate/batches/{id}/questions` | List per-job status for a batch |
| POST | `/generate/batches/{id}/retry-failed` | Retry all failed jobs in a batch |
| POST | `/generate/batches/{id}/review-swarm` | Trigger review swarm for all questions in a batch |

### 7.4 Student router (`/api` prefix — admin-consumed endpoints)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/stats/{user_id}` | `student_required` | User stats: total answered, correct, accuracy, top missed keys |
| GET | `/api/stats/{user_id}/activity` | `student_required` | Daily activity counts for heatmap |

### 7.5 Auth router (`/api/auth` prefix, no admin auth required)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/google` | Exchange Google credential for JWT pair |
| POST | `/api/auth/refresh` | Refresh access token using refresh token |
| POST | `/api/auth/logout` | Logout (server-side token invalidation) |
| GET | `/api/auth/me` | Get current user profile |

---

## 8. Rejection Semantics

`rejected` and `retired` are distinct terminal states:

| State | Meaning | Data preserved? | Reversible? |
|---|---|---|---|
| `rejected` | Failed quality review before ever reaching `active` | Yes — all annotations, options, review results, consensus rows, generation lineage preserved for audit | In principle |
| `retired` | Was `active`, removed post-release (typo found, content deprecated) | Yes | In principle |

On rejection, only `practice_status`, `rejection_reason`, `rejected_at`, `rejected_by_admin_token` change. The question's history remains fully auditable.

The generation quality metric uses the `rejected` count. Post-release health uses the `retired` count.

---

## 9. Version Propagation Architecture

Every edit creates a new immutable `QuestionVersion` row:

1. `PATCH /admin/questions/{id}` creates a new `QuestionVersion` with the updated content.
2. `QuestionOption` rows are cloned with updated correctness flags, linked to the new version.
3. `Question.current_*` fields and `latest_version_id` are updated to point at the new version.
4. `annotation_stale` is set to `True` (signals that the LLM annotation predates the edit).
5. An `AdminAuditLog` row records the action, before/after state, and admin identity.

All reads across `student.py` and `admin.py` filter `QuestionOption` by `latest_version_id`, so students and admin views see the new content immediately — no stale-cache class of bug.

---

## 10. Key Configuration (`backend/app/config.py`)

| Setting | Default | Purpose |
|---|---|---|
| `admin_api_keys` | — | Comma-separated list of valid admin API keys |
| `google_oauth_client_id` | — | Google OAuth client ID (must match frontend `VITE_GOOGLE_CLIENT_ID`) |
| `generation_max_batch_size` | `25` | Maximum questions per batch |
| `generation_default_batch_size` | `5` | Default batch size |
| `generation_job_max_retries` | `3` | Max retries per generation job |
| `generation_review_providers` | `"ollama"` | Comma-separated review providers |
| `generation_review_openai_model` | `"gpt-4o"` | OpenAI reviewer model |
| `generation_review_anthropic_model` | `"claude-sonnet-5"` | Anthropic reviewer model |
| `generation_review_ollama_model` | `"kimi-k3:cloud"` | Ollama reviewer model |
| `generation_review_max_concurrent` | `6` | Parallel reviewer calls |
| `generation_min_realism_score` | `7.0` | Consensus reject threshold |
| `generation_min_sat_fidelity_score` | `7.0` | Consensus reject threshold |
| `generation_min_distractor_quality_score` | `6.5` | Consensus regenerate threshold |
| `generation_min_taxonomy_match_score` | `7.5` | Consensus regenerate threshold |
| `generation_max_copy_risk_score` | `5.0` | Consensus reject threshold |
| `generation_max_reviewer_disagreement` | `1.5` | High-disagreement flag threshold |
| `generation_auto_release_enabled` | `false` | Global auto-release toggle |
| `generation_auto_release_min_reviews` | `3` | Min admin-reviewed questions for model trust |
| `generation_auto_release_min_accept_rate` | `0.80` | Min acceptance rate for model trust |
| `generation_auto_release_allowed_targets` | `""` | JSON array of allowed generation targets |

---

## 11. Known Issues

Tracked in `admin_dashboard_issues.md`. Summary of open critical issues:

| ID | Issue | Impact |
|---|---|---|
| H1 | `GET /admin/questions/{id}` missing | Question-detail view 404s (only `GET /admin/generated-questions/{id}` exists, which 404s on official questions) |
| H2 | `GET /admin/jobs` missing | Jobs tab non-functional |
| H3 | `student.py` rejects JWT admins | Student Performance page 403s for Google-authenticated admins |
| H5 | Production `/api` prefix mismatch | Admin/users requests 404 in production without Vite proxy |
| B1 | Refresh tokens stored raw | DB leak exposes all valid refresh tokens |