# Admin Dashboard — Issues Report

Thorough examination of the admin dashboard (`APP/ADMIN_APP`, React/TS + Vite) and its
FastAPI backend (`backend/app/routers/*`). Produced by cross-referencing every frontend
API call in `src/api/client.ts` against every backend route, plus a line-level read of
each page, component, auth module, and router.

**Scope:** `APP/ADMIN_APP/src/**` and `backend/app/routers/{admin,generate,users,dashboard,student,student_auth,questions,health}.py` + `backend/app/{main,auth,google_oauth}.py`.
**Not in scope:** the student app (`APP/STUDENT_APP_REDUX`), the standalone HTML dashboard in `dashboard.py`.
**Method:** three parallel read-only examiners (frontend, backend admin/generate/users, backend dashboard/student/auth) + architectural verification of router prefixes and the Vite proxy.

---

## Executive summary

The dashboard "has a lot of bugs and missing endpoints" for three concrete, compounding reasons:

1. **Two backend endpoints the frontend calls don't exist** — `GET /admin/questions/{id}` and `GET /admin/jobs`. The Question-detail view and the Jobs tab 404.
2. **Student-data routes reject JWT-authenticated admins** — every `/api/stats/*` and `/api/study/*` route uses the API-key-only auth dependency, so the default Google sign-in flow (Bearer JWT, no `VITE_ADMIN_TOKEN`) gets 403. The Student Performance page is effectively dead for normal admin login.
3. **A live 500 on the Questions filter** — the Data Management page exposes a `needs_review` status filter, but `practice_status_enum` has no such value; selecting it throws `asyncpg InvalidTextRepresentationError`.

On top of those, there is a **systemic frontend issue class** (no `isError` branches anywhere — every backend failure is silently rendered as "empty data"), a **production routing trap** (the `/api` prefix is stripped only by the Vite dev proxy, not in prod), and several **correctness bugs in KPIs/charts** (Active-users count shows total, Missed-by-Focus-Key chart is hardcoded to `1`, admins appear in the Student list).

**Counts:** 4 high-severity, ~13 medium, ~17 low. 2 missing endpoints. 10 dead client methods (defined, never called by any page).

---

## Architecture context (read this first)

Router prefixes (`main.py:170-178`, included with no extra prefix):

| Router | Prefix | Frontend reachability |
|---|---|---|
| `health.py` | `""` | `/` — docker healthcheck |
| `questions.py` | `/questions` | not used by admin app |
| `student.py` | `/api` | `/api/stats/*`, `/api/study/*` ✓ |
| `student_auth.py` | `/api/auth` | `/api/auth/*` ✓ |
| `admin.py` | `/admin` | needs `/api` stripped → `/admin/*` |
| `users.py` | `/users` | needs `/api` stripped → `/users/*` |
| `generate.py` | `/generate` | not used by admin app |
| `ingest.py` | `/ingest` | not used by admin app |
| `dashboard.py` | `/dashboard` | **not used by admin app** (see note) |

The frontend `API_BASE = '/api'` (`client.ts:8`), so every call begins with `/api`. The
Vite dev proxy (`vite.config.ts:24-34`) rewrites:

- `/api/admin` → `/admin` (strip `/api`)
- `/api/users` → `/users` (strip `/api`)
- `/api` (everything else) → forwarded unchanged

This makes dev work, but it is **dev-only**. In production there is no Vite proxy, so
`/api/admin/*` and `/api/users/*` hit FastAPI verbatim and 404 (admin/users routers are
mounted without `/api`). The vite config itself documents this as "bug-777/778".

> **Note on `/dashboard`:** `dashboard.py` (prefix `/dashboard`) is a standalone
> server-rendered HTML admin UI for ingestion/generation inspection, not a JSON API.
> The React admin app does **not** call `/api/dashboard/*` anywhere. The
> `/dashboard` vs `/api/dashboard` prefix difference is therefore **intentional, not a
> bug**. (Flagged here because it looks like one at first glance.)

---

## Critical issues (high severity)

### H1. `GET /admin/questions/{question_id}` — endpoint missing
- **Frontend:** `client.ts:171` `getQuestion: (id) => apiCall('/admin/questions/${id}')`
- **Backend:** `admin.py` has `PATCH`, `DELETE`, `POST .../approve`, `POST .../reject` for `/admin/questions/{question_id}` but **no `GET`**. The lookalike `GET /admin/generated-questions/{question_id}` (`admin.py:890`) requires `content_origin == "generated"` and 404s on official questions.
- **Impact:** Question-detail view 404s. After the Vite strip the request is `/admin/questions/{id}` — no handler.
- **Fix:** Add `@router.get("/questions/{question_id}")` returning the same shape as `list_questions` items, handling both official and generated origins (unlike `/generated-questions/{id}`).

### H2. `GET /admin/jobs` — endpoint missing
- **Frontend:** `client.ts:183` `listJobs: (params) => apiCall('/admin/jobs?${q}')`
- **Backend:** The only `/admin/jobs/*` route is `POST /admin/jobs/{job_id}/fail` (`admin.py:1474`). There is no list endpoint. `GET /generate/runs/{run_id}` (`generate.py:1052`) takes a single run id, not query params, and is under `/generate` not `/admin`.
- **Impact:** Jobs tab 404s. The entire jobs UI is non-functional (no list, no retry, no cancel — only force-fail).
- **Fix:** Add `@router.get("/jobs")` with filters (status, provider, batch_id, limit/offset) returning serialized `QuestionJob` rows. Optionally `POST /admin/jobs/{job_id}/retry`.

### H3. `student.py` routes reject JWT-authenticated admins (auth-dependency misuse)
- **Files:** `backend/app/routers/student.py` — 27 routes depend on `student_required` / `admin_or_student_required` (lines 374, 546, 636, 664, 1317, 1345, 1478, 1525, 1742, 1962, 2077, 2167, 2257, 2371, 2434, 2541, 2592, 2668, 2728, 2840, 2894, 2975, 3022, 3066, 3152, 3188, 3319).
- **Root cause:** Both helpers (`auth.py:172`, `:179`) inspect **only** the `X-API-Key` header and never read `Authorization: Bearer`. The JWT-aware equivalents `student_jwt_required` / `admin_or_student_jwt_required` (`auth.py:237`, `:295`) are imported at `student.py:19` but **never used**.
- **Frontend effect:** `client.ts:91-96` sends `X-API-Key` only when `VITE_ADMIN_TOKEN` is set. The default Google sign-in flow sends **only** the Bearer JWT. So the admin app's calls to `getStudentStats`, `getStudentActivity`, `getStudentRecommendations`, `getStudentMissed` (`client.ts:213-219`) all return `403 "Invalid admin API key"` / `"Invalid student API key"`.
- **Why the student app masks it:** `STUDENT_APP_REDUX` always sends `X-API-Key`. The admin app's Google flow does not.
- **Fix:** Swap `Depends(student_required)` → `Depends(student_jwt_required)` and `Depends(admin_or_student_required)` → `Depends(admin_or_student_jwt_required)`. The JWT-aware versions accept both JWT and legacy API key, so backward compat is preserved. At minimum, the four admin-called routes (`/api/stats/{user_id}`, `/api/stats/{user_id}/activity`, `/api/study/recommendations`, `/api/study/missed`) must switch.

### H4. `needs_review` filter causes HTTP 500 (frontend/backend schema mismatch)
- **Frontend:** `DataManagement.tsx:6` — `StatusFilter` type lists `'needs_review'` as a selectable filter.
- **Backend:** `admin.py:202` inside `list_questions`, `await db.execute(stmt)` runs `WHERE questions.practice_status = $1::practice_status_enum` with `'needs_review'`, which PostgreSQL rejects: `asyncpg.exceptions.InvalidTextRepresentationError: invalid input value for enum practice_status_enum: "needs_review"`.
- **Impact:** Clicking the "needs_review" filter tab returns 500. Other values (`active`, `draft`, `rejected`) need confirmation against the actual enum.
- **Fix:** Either (a) add `needs_review` to `practice_status_enum` via a migration, or (b) remove it from the frontend `StatusFilter` and filter UI. Confirm the valid enum set first.

### H5. Production `/api` prefix mismatch (bug-777/778)
- **Files:** `backend/app/main.py:170-177` + `APP/ADMIN_APP/vite.config.ts:24-30`.
- **Problem:** The Vite dev proxy strips `/api` for `/api/admin` and `/api/users`. In production there is no such proxy, so the frontend's `/api/admin/jobs` etc. hit FastAPI verbatim — admin/users routers are mounted at `/admin` and `/users` (no `/api`), so **every admin/users request 404s in production** unless a reverse proxy performs the same rewrite.
- **Fix (pick one):** (a) mount `admin.router` and `users.router` with `prefix="/api"` in `main.py`; (b) configure the production reverse proxy to strip `/api` for these routers; (c) make the frontend `API_BASE` environment-aware. Document the required production rewrite regardless.

---

## Frontend issues

### High

| # | file:line | category | description | fix |
|---|---|---|---|---|
| F1 | `UserManagement.tsx:249` | response-shape-mismatch | "Active" `StatCard` shows `users?.length` (total users), not `users?.filter(u => u.is_active).length`. Active KPI == Total Users KPI. | `value={users?.filter(u => u.is_active).length ?? '—'}` |
| F2 | `StudentPerformance.tsx:84-87` | type-mismatch | "Missed by Focus Key" bar chart maps `top_missed_focus_keys` to `{ key, misses: 1 }` — every bar is `1`; chart is meaningless. `StudentStats.top_missed_focus_keys` is `string[]` with no counts. | Remove the chart, or fetch per-focus-key miss counts (e.g. from weak-spots) and pass real counts. Extends `types/index.ts:111-117`. |

### Medium

| # | file:line | category | description | fix |
|---|---|---|---|---|
| F3 | `StudentPerformance.tsx:164-168` | response-shape-mismatch | `adminApi.listUsers()` returns all users (admins included); page is "Student Performance" with "Search students by email…". Admins appear in the list and get empty/404 stats panels. | Filter `users.filter(u => u.role === 'student')`, or pass a role query param if supported. |
| F4 | `DataManagement.tsx:318-326, 420` | routing/logic | Selecting a test calls `setTestFilter(t)` but does **not** reset `page` to 1. If the user was on page 3 (offset 50) then picks a test with 10 questions, the query runs at `offset=50`, returns empty, and pagination controls are hidden (`totalPages > 1` is false) — user is stuck on "No questions found." | `onSelectTest={(t) => { setTestFilter(t); setPage(1) }}`; also reset page in the "All Questions" button handler. |
| F5 | `DataManagement.tsx:349-350` | response-shape-mismatch | `data?.questions ?? data?.items ?? data ?? []` and `data?.total ?? questions.length`. If the backend returns a bare array (no `total`), `total` falls back to `questions.length` (current page only), so `totalPages` is always 1 and pagination silently hides everything past page 1. | Confirm backend shape; require `{ questions, total }`; else use a count endpoint or "showing N of unknown". |
| F6 | `AuthContext.tsx:79-87` + `authStore.ts:78` + `client.ts:72-73,132` | type-mismatch | `apiCall` returns `any`; token responses (`googleLogin`, `refresh`) are stored unvalidated. If the backend ever returns camelCase (`accessToken`) instead of `access_token`/`refresh_token`, `setTokens` stores `undefined` for both and every subsequent request 401s. Root cause of the response-shape-mismatch class. | Genericize `apiCall<T>()` or type each `adminApi`/`authApi` method; validate `{ access_token, refresh_token }` before storing. |
| F7 | `AuthContext.tsx:84-87` | auth-bug | In `loginWithGoogle`, if `setTokens(tokens)` succeeds but `authApi.me()` throws, tokens are stored but `status` stays `anonymous` and `profile` is null. `RequireAdmin` redirects to `/login` even though `hasSession()` is true; next reload succeeds via bootstrap. Confusing mid-session state. | In the catch path, `clearSession()` for consistency, or set `authenticated` optimistically and let `me` populate profile. |
| F8 | `PipelinePerformance.tsx:138-140` | response-shape-mismatch | Reads `autoRelease?.enabled` only, but `widgets.tsx` (same endpoint) uses `enabled ?? effective_enabled`. If the backend returns `effective_enabled` (globally disabled, per-tenant enabled), this page shows the wrong status and enables the wrong button. | Use the same `enabled ?? effective_enabled` normalization as the widget, via a shared type. |
| F9 | `widgets.tsx:38-196` (5 widgets) | missing-error-handling | None of the five dashboard widgets handle `isError`. On backend failure: Users → `-`, Generation → `-`, Auto-Release → "Disabled", Recent Batches → "No recent batch list available.", Weak Spots → "Not enough data yet." Every one conflates error with empty. | Branch on `isError`; render a per-widget "Failed to load" state. |
| F10 | `DataManagement.tsx:261-300` | missing-error-handling | `TestBrowser` handles `isLoading` only; on error `tests` is undefined and UI shows "No source test data found." — misleading an error for empty. | Branch on `isError`; show "Failed to load tests" with retry. |
| F11 | `PipelinePerformance.tsx:44-60` | missing-error-handling | Neither `gen` nor `batches` queries handle `isError`; on failure KPIs render `—` and charts render nothing, with no "backend unreachable" message. | Track `isError` for both; show a "Failed to load analytics" banner. |

### Low

| # | file:line | category | description | fix |
|---|---|---|---|---|
| F12 | `LoginPage.tsx:54` + `RequireAdmin.tsx:27` | auth-bug | `RequireAdmin` captures `state={{ from: location.pathname }}` but `LoginPage` navigates to `"/"` and ignores `from` — deep-link resume after login is lost. | `Navigate to={from ?? '/dashboard' replace}`. |
| F13 | `StudentPerformance.tsx:29-33, 73-82` | missing-error-handling | `ActivityHeatmap` and `StudentDetailPanel` have no `isError` branch; on error they render the empty-state ("No data available." / 365 grey cells) identical to genuine empty. | Add `isError` branches with retry hints. |
| F14 | `StudentPerformance.tsx:214` | undefined-ref | `(u.email ?? u.username)[0].toUpperCase()` throws if both are empty strings (`[0]` is `undefined`). | `(u.email ?? u.username)?.[0]?.toUpperCase() ?? '?'`. |
| F15 | `StudentPerformance.tsx:44` | response-shape-mismatch | Heatmap keys dates by `d.toISOString().slice(0,10)` (UTC), but `ActivityDay.date` is an opaque backend string; if backend emits local-time dates the heatmap is off by one day. | Use the backend `date` string directly as the map key. |
| F16 | `UserManagement.tsx:250` | hardcoded-value | "New This Week" KPI hardcoded to `"—"`. | Compute `users?.filter(u => Date.now() - new Date(u.created_at).getTime() < 7*864e5).length`, or remove. |
| F17 | `UserManagement.tsx:58` | type-mismatch | `createUser` called with only `{ username, email }`; no role/active fields exposed → admins can't create admin accounts from this UI. | Add role select + active checkbox to `CreateUserModal` if admin-creation is intended. |
| F18 | `UserManagement.tsx:313` | a11y | `confirm(...)` uses the blocking native dialog; inconsistent with the styled modal pattern elsewhere. | Replace with a `ConfirmModal`. |
| F19 | `App.tsx:24-39` | routing-bug | No catch-all `<Route path="*">`. Unknown URLs render Layout with an empty `<Outlet/>` (blank page). | Add `<Route path="*" element={<Navigate to="/dashboard" replace />} />`. |
| F20 | `ErrorBoundary.tsx:11-37` | other | No reset on navigation: once `state.error` is set the boundary never recovers even on a healthy route. | Reset on route change, or key the boundary by location. |
| F21 | `main.tsx:10-14` | other | `ToastProvider` sits outside `ErrorBoundary`; a provider render throw is uncaught. | Move `ErrorBoundary` above `ToastProvider`. |
| F22 | `Dashboard.tsx:84-95` | other | Widgets render via dynamic `Object.entries(WIDGETS).map`; a throw in one widget unmounts the whole grid via the top-level boundary. | Wrap each widget in its own error boundary. |
| F23 | `widgets.tsx:158` | undefined-ref | `<li key={b.id}>` where `BatchRow.id` is `string \| number \| undefined`; undefined key breaks reconciliation on reorder. | `key={String(b.id ?? index)}`. |
| F24 | `widgets.tsx:63` | type-mismatch | `percent(data?.approve_rate ?? data?.acceptance_rate)` accepts `unknown`; `acceptance_rate` is not in `GenerationAnalytics`. Defensive but masks shape drift. | Settle on one field name; document if both are valid. |
| F25 | `PipelinePerformance.tsx:146-156` | other | Enable/Disable buttons not disabled while `autoRelease` is still loading (status undefined); `enableMutation.mutate()` can race the status query. | `disabled={autoRelease === undefined \|\| autoRelease?.enabled \|\| enableMutation.isPending}`. |
| F26 | `PipelinePerformance.tsx:88` | other | `new Date(b.created_at).toLocaleDateString()` with no fallback; null `created_at` renders "Invalid Date". | `b.created_at ? new Date(b.created_at).toLocaleDateString() : '—'`. |
| F27 | `DataManagement.tsx:285` | a11y | `key={i}` (array index) for test cards; reordering collides React keys. | Composite key from `source_test_name + source_section_code + source_module_code`. |
| F28 | `Layout.tsx:5-11, 67` | a11y/hardcoded | Nav icons are emoji announced verbatim by screen readers; `'DSAT Admin v1'` hardcoded version string drifts. | `aria-hidden` on icons; read version from `package.json`/env. |
| F29 | `AuthContext.tsx:42-63` | auth-bug | Bootstrap effect has no `storage` event listener; cross-tab token changes aren't picked up. | Add a `storage` listener that re-runs bootstrap on `auth.access_token` change. |

---

## Backend issues

### Already listed under Critical
H1 (`GET /admin/questions/{id}` missing), H2 (`GET /admin/jobs` missing), H3 (student.py auth-dep misuse), H4 (`needs_review` 500), H5 (prod `/api` prefix).

### Medium

| # | file:line | category | description | fix |
|---|---|---|---|---|
| B1 | `student_auth.py:63, 108, 162, 228` | security | Comments say "Store refresh token hash + expiry" but code stores the raw refresh-token JWT on `user.refresh_token` and compares with exact equality (line 204). A DB leak exposes all valid refresh tokens for replay until expiry. | Store `hashlib.sha256(refresh_token)`; compare hashes. |
| B2 | `admin.py:2241-2247` | n+1-query | `analytics_export` runs a separate `select(ConsensusVerdict)...limit(1)` per exported question inside the row loop. | Batch-load latest consensus verdicts for all exported ids in one query (window function / `distinct on (question_id)`). |
| B3 | `admin.py:1764-1767` | n+1-query | `list_review_runs` issues `select(LlmReviewResult)` per review run inside the `for run in review_runs` loop. | Collect `run.id`s; one `LlmReviewResult.review_run_id.in_(...)` query; group in memory. |
| B4 | `admin.py:736` | logic/default-filter | `list_generated_questions` defaults `practice_status` to `"draft"` via `Query("draft")`. The frontend doesn't always pass `practice_status`, so the dashboard silently sees only drafts (approved/rejected generated questions hidden). | Default to `None` (no filter), or have the frontend pass the desired status explicitly. |
| B5 | `student.py:2619-2632` | n+1-query | `/api/spaced-repetition/due` issues `db.get(Question)` + `select(QuestionAnnotation)` per due row (up to `limit=100`) — up to 200 round-trips. | Bulk-fetch `Question` and `QuestionAnnotation` by `id IN (...)` in two queries; build lookup dicts. |
| B6 | `student.py:2788-2802` | n+1-query | `/api/student/trap-susceptibility` runs two queries (`early_rows` asc, `late_rows` desc) per distinct `missed_syntactic_trap_key` — 2×N. | Window function / single grouped query for first/last-5 accuracy. |
| B7 | `student.py:2586-2661` | logic | `/api/spaced-repetition/due`: the `domain` filter is applied by `continue`-ing inside the Python loop **after** the SQL `limit` (line 2606). `total_due` (line 2617) counts all due rows regardless of `domain`. Result: `due_questions` is shorter than `limit` while `total_due` reports the unfiltered count — inconsistent and under-returns. | Push `domain` into SQL (join `Question`+`QuestionAnnotation`) before `limit`; apply same filter to the count query. |

### Low

| # | file:line | category | description | fix |
|---|---|---|---|---|
| B8 | `student.py:2073` | response-model-mismatch | `/api/diagnostic/start` has no `response_model`; returns `DiagnosticStartV1Response` (line 2140) or `DiagnosticSessionStartResponse` (line 2159) — OpenAPI documents neither, FastAPI can't validate the union. | Declare `Union[...]` response_model, or split into two endpoints. |
| B9 | `student.py:2933-2941` | n+1-query | `/api/student/trap-details/{trap_type}` does `db.get(Question)` per example (bounded at 5, minor). | One `select(Question).where(id.in_(...))`. |
| B10 | `student_auth.py:258` | other | `/api/auth/me` returns `user_token=str(user.user_token)`; if `None`, the body contains the literal string `"None"`, which a client may mistake for a valid token. | `user_token=str(user.user_token) if user.user_token else None`; make `StudentMeResponse.user_token` `Optional`. |
| B11 | `student.py:3191-3192` | style | `from fastapi import HTTPException` and `import uuid as _uuid` re-imported inline though already at module top (lines 9, 4). | Remove inline imports; use module-level symbols. |
| B12 | `health.py:15` | swallowed-exception | `except Exception:` silently sets `db_ok=False` with no logging; root-cause visibility lost on DB misconfiguration. | `logger.warning("health DB probe failed: %s", exc)` before setting `db_ok=False`. |
| B13 | `admin.py:1474-1493` | incomplete | The only job-management endpoint is `POST /admin/jobs/{job_id}/fail`; no list/retry/cancel. Combined with H2 the entire Jobs UI is non-functional. | Implement `GET /admin/jobs` (H2) and `POST /admin/jobs/{job_id}/retry`. |
| B14 | `admin.py:2503` | code smell | `week_ago = now - __import__("datetime").timedelta(days=7)` re-imports `datetime` inline though `from datetime import datetime, timezone` is at top. | Add `timedelta` to the top-level import; use it directly. |
| B15 | `admin.py:2626-2649` | error shape | `/questions/{question_id}/annotate-spans` raises `HTTPException(422, detail=result)` where `result` is a dict — different from the `{"error", "details"}` shape used by `_amendment_or_404`. | Standardize on one error envelope for admin write endpoints. |
| B16 | `admin.py:904-910, 913-920` | indirect call | `approve_generated_question`/`reject_generated_question` call `approve_question`/`reject_question` directly, bypassing DI. Fine now (deps passed explicitly), but any future `Depends(...)` added to the inner function would be silently skipped. | If the inner functions grow deps, refactor to a shared helper. |

### Checked and found clean
- No bare `except:` / `except: pass` in any router. All `except Exception` blocks in `generate.py` (lines 581, 606, 620, 646, 662, 785, 843, 890) log and route through `_mark_job_failed`.
- No `TODO`/`FIXME`/`NotImplementedError`/`pass` stubs in any router.
- All `admin.py`/`users.py` routes use `Depends(admin_required)` — no auth bypass.
- All handlers use `db: AsyncSession = Depends(get_db)` — no missing DB dependency.
- No undefined function/variable references.
- Response models on admin analytics endpoints (`GenerationAnalyticsResponse`, `ReviewAnalyticsResponse`, `BatchAnalyticsResponse`, `TrendAnalyticsResponse`, `CohortWeakSpotsResponse`, `CohortSummaryResponse`, `CohortTrapAnalyticsResponse`, `list[TestSummary]`, `UserResponse`) match returned objects.

---

## Dead API surface (defined in `client.ts`, never called by any page)

These `adminApi` methods exist in the client but no page/component uses them — either
wire them into the UI or remove them so the API surface reflects actual capabilities.

| Method | Endpoint |
|---|---|
| `listJobs` | `GET /admin/jobs` *(also missing on backend — H2)* |
| `listGeneratedQuestions` | `GET /admin/generated-questions` |
| `approveGenerated` | `POST /admin/generated-questions/{id}/approve` |
| `rejectGenerated` | `POST /admin/generated-questions/{id}/reject` |
| `getReviewAnalytics` | `GET /admin/analytics/review` |
| `getTrendAnalytics` | `GET /admin/analytics/trends` |
| `getStudentRecommendations` | `POST /api/study/recommendations` *(also 403 via H3)* |
| `getStudentMissed` | `GET /api/study/missed` *(also 403 via H3)* |
| `getAutoReleaseAudit` | `GET /admin/generation/auto-release/audit` |
| `getUser` | `GET /users/{id}` (only `listUsers` is used) |

---

## Backend routes with no frontend caller (extra, not bugs)

Present in the backend but not consumed by `APP/ADMIN_APP`. Listed so the dashboard's
*intended* vs *actual* capability gap is visible — these are candidates for new UI, not
defects:

`/admin/amendments*` (6 routes), `/admin/generated-questions/{id}` (GET single),
`/admin/generated-questions/{id}/regenerate`, `/admin/questions/{id}/{confirm-overlap,clear-overlap,stimulus-assets,review-swarm,review-runs,annotate-spans}`,
`/admin/evaluations*` (2), `/admin/relations*` (3), `/admin/analytics/{export,student-cohort-summary,trap-analytics}`,
all of `/generate/*` (8 routes), all of `/questions/*` (3 routes), all of `/dashboard/*` (4 routes).

---

## Recommended fix order

1. **H3** — swap student.py auth deps to the JWT-aware variants. Unblocks the Student Performance page for normal admin login. Largest blast-radius fix; no schema change.
2. **H1 + H2** — add `GET /admin/questions/{id}` and `GET /admin/jobs`. Unblocks Question-detail and Jobs.
3. **H4** — resolve the `needs_review` enum mismatch (migration or remove the filter). Stops the 500.
4. **H5** — fix the production `/api` prefix so admin/users calls don't 404 in prod.
5. **F1, F2, F3** — the wrong-KPI / meaningless-chart / admins-in-student-list correctness bugs (trivial, high visibility).
6. **F4, F5** — Data Management pagination traps (stuck-on-empty, silent page-1-only).
7. **F6** — type `apiCall<T>()` and validate token responses; removes the root cause of the response-shape-mismatch class.
8. **F9–F11, F13** — add `isError` branches across widgets and pages so backend failures stop masquerading as empty data.
9. **B1** — hash refresh tokens before storing (security).
10. **B2–B7** — N+1 and post-limit-filter query fixes (performance/correctness).
11. **F12–F29, B8–B16** — low-severity polish.

---

*Examined 2026-07-27. Findings reflect the code at HEAD on that date; verify line numbers before patching, as files are large and actively edited.*