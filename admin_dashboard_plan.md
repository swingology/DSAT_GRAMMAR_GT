# Admin Dashboard — Living Plan

**Status:** Active development. This file is the up-to-date source of truth for the admin
dashboard's current state and near-term backlog. It supersedes the day-to-day accuracy of
`ADMIN_DASHBOARD_DESIGN.md` / `_WIREFRAMES.md` / `_TASKS.md` / `_README.md`, which described
an initial MVP plan (2026-06-18) that the actual build diverged from — see "Reality check"
below. Those docs are kept for historical rationale (auth model, testing strategy, DB audit
table) but their file structure and phase checklists are stale.

**Implementation plan:** the code-level, phase-by-phase task breakdown for §5-§9 below lives in
`admin_dashboard_tasks.md` (exact file paths, complete code, tests, and commit steps per task).
This file (`admin_dashboard_plan.md`) is the design/spec layer; that file is the execution layer.

---

## 1. Reality check — plan vs. what was actually built

The original 4-doc package planned admin pages inside `FRONTEND/src/pages/admin/`
(QuestionListPage, ReviewQueuePage, AnalyticsPage as a deferred Phase 4) with routers named
`admin_questions.py` / `admin_jobs.py` / `admin_analytics.py`.

What actually exists is a **separate standalone Vite app**, `APP/ADMIN_APP/`, backed by the
single existing `backend/app/routers/admin.py` (2578 lines, prefix `/admin`). The "Phase 4
Future" analytics the old plan deferred are already implemented. Treat the sections below as
current ground truth.

---

## 2. Current state — frontend (`APP/ADMIN_APP/`)

Routes (`src/App.tsx`), all under a shared `Layout`:

| Route | Page | Purpose |
|---|---|---|
| `/users` (default) | `UserManagement.tsx` | List/create/delete students, stat cards |
| `/data` | `DataManagement.tsx` | Question list, filter by status/origin, approve/reject/edit questions |
| `/students` | `StudentPerformance.tsx` | Per-student accuracy, top missed focus/trap keys, expandable detail panel |
| `/pipeline` | `PipelinePerformance.tsx` | Generation/batch/review analytics, auto-release controls |

Shared infra: `src/api/client.ts` (`adminApi` fetch wrapper, bearer token via
`VITE_ADMIN_TOKEN`), `src/types/index.ts` (TS interfaces mirroring backend payloads).

## 3. Current state — backend API surface

`backend/app/routers/admin.py` (prefix `/admin`), grouped by area:

- **Amendments:** `GET /amendments`, `GET /amendments/{id}`, `POST /amendments/{id}/approve|reject|request-more-evidence|promote`
- **Questions:** `GET /questions`, `PATCH /questions/{id}`, `POST /questions/{id}/approve|reject|confirm-overlap|clear-overlap|annotate-spans`, `DELETE /questions/{id}`, `GET /questions/{id}/stimulus-assets`
- **Generated questions:** `GET /generated-questions`, `GET /generated-questions/{id}`, `POST /generated-questions/{id}/approve|reject|regenerate`
- **Jobs / evaluations:** `POST /jobs/{id}/fail`, `POST /evaluations`, `POST /evaluations/{id}/score`
- **Relations:** `GET /relations`, `POST /relations`, `DELETE /relations/{id}`
- **Review swarm:** `POST /questions/{id}/review-swarm`, `GET /questions/{id}/review-runs`
- **Analytics:** `GET /analytics/generation|review|batches|trends|export|weak-spots|student-cohort-summary|trap-analytics`
- **Auto-release:** `GET /generation/auto-release/status|audit`, `POST /generation/auto-release/enable|disable`

Student-facing stats consumed by the admin app come from `backend/app/routers/student.py`
(prefix `/api`): `GET /stats/{user_id}` (`UserStats`: total answered/correct, accuracy, top
missed focus/trap keys). User CRUD comes from `backend/app/routers/users.py` (prefix `/users`).

## 4. Backlog (not yet built)

- Bulk approve/reject across a job (currently per-question only)
- Question text/passage search (list only supports field filters)
- Real-time updates across concurrent admins (manual refresh only)
- **Student activity heatmap** — see full spec below (§5).
- **Admin password reset** — see full spec below (§6).
- **Question browser, detail view, edit UI, and test explorer** — see full spec below (§7).
- **User edit endpoint** (username/email/role) — see full spec below (§8).
- **Interactive dashboard redesign, desktop + iPad** — see full spec below (§9). Blocked on reference screenshot.

---

## 5. NEW FEATURE — Student Activity Heatmap

**Requested by:** user, 2026-07-01. Adds a GitHub-style contribution graph to each student's
expanded detail panel on `/students` — dark green for high-activity days, grey for none.

### 5.1 Placement

Inside `StudentDetailPanel` (`APP/ADMIN_APP/src/pages/StudentPerformance.tsx`), as a new
section below the existing Answered/Correct/Accuracy stat tiles and above "Top Missed Areas".

### 5.2 Data source

No schema change needed. `UserProgress.timestamp` (`backend/app/models/db.py`) already records
one row per attempt. Aggregate with `GROUP BY date_trunc('day', timestamp)` per user.

**Activity metric:** count of all `UserProgress` rows per calendar day — practice + diagnostic
pooled, regardless of correctness. Consistent with this project's existing "pool diagnostic +
practice" decision for the weakness profile (do not filter to correct-only or split by session
type).

### 5.3 Backend

New endpoint in `student.py`, alongside the existing `/stats/{user_id}`:

```
GET /api/stats/{user_id}/activity?days=365
```

Response: `[{ "date": "2026-06-30", "count": 7 }, ...]` — one entry per day with count > 0
(sparse; the frontend fills gaps as zero/grey). `days` defaults to 365, capped reasonably
(e.g. 400) to bound the query range.

Add `getStudentActivity` to `adminApi` in `client.ts`:
```
getStudentActivity: (userId: number, days = 365) =>
  apiCall(`/stats/${userId}/activity?days=${days}`)
```

### 5.4 Frontend component

New `ActivityHeatmap` component (co-located in `StudentPerformance.tsx` or split out if it grows
past ~80 lines), rendered as 53 week-columns × 7 day-rows ending today — the standard GitHub
layout, rolling last 12 months.

**Color buckets** (reusing the emerald palette already established by `AccuracyBar` in the same
file, for visual consistency):

| Count | Class |
|---|---|
| 0 | `bg-gray-100` |
| 1–2 | `bg-emerald-200` |
| 3–5 | `bg-emerald-300` |
| 6–10 | `bg-emerald-500` |
| 11+ | `bg-emerald-700` |

Thresholds are a starting point — revisit once real usage data shows the actual daily-question
distribution.

Each day cell shows a hover tooltip with the exact date and count (native `title` attribute is
sufficient; no need for a custom tooltip library given `recharts` is already a dependency for
other charts on this page but not needed here).

### 5.5 Tasks

- [ ] Backend: add `GET /api/stats/{user_id}/activity` endpoint + Pydantic response model in `student.py`
- [ ] Backend: unit test — days with zero activity are omitted from the sparse response; date bucketing uses UTC day boundaries consistent with existing `timestamp` usage elsewhere in the router
- [ ] Frontend: add `getStudentActivity` to `adminApi`
- [ ] Frontend: `ActivityHeatmap` component (grid layout, color bucketing, tooltip)
- [ ] Frontend: wire into `StudentDetailPanel`, loading skeleton matching existing pattern
- [ ] Manual QA: verify a student with no activity renders all-grey, not an error state

---

## 6. NEW FEATURE — Admin Password Reset

**Requested by:** user, 2026-07-01. Lets an admin set/reset a student's password from the
`/users` (`UserManagement.tsx`) page.

### 6.1 Rationale

Confirmed in code, not assumed: `create_user` (`backend/app/routers/users.py`) creates a
`User` row with no `password_hash` at all — students added via the admin panel currently
have no way to log in through the email+password flow (`POST /api/auth/login` in
`student_auth.py`, which 401s whenever `user.password_hash is None`). An admin
set/reset-password action is the fix for that gap, and also covers the ordinary "student
forgot their password" case going forward. Password hashing utilities already exist and
need no new dependency: `hash_password()` in `backend/app/auth.py` (argon2 via `pwdlib`).

### 6.2 Backend

New endpoint in `users.py`, alongside the existing `admin_required`-gated CRUD:

```
POST /users/{user_id}/reset-password
```

Request body (new payload model in `payload.py`, mirroring `StudentSignup`'s constraint):
```python
class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
```

Handler: 404 if user not found, `user.password_hash = hash_password(body.new_password)`,
and — since this forces a credential change — also clear `user.refresh_token` /
`user.refresh_token_expires` so any existing session is invalidated and the student must
log in again with the new password. Return 204 (no body; never echo the password or hash
back in a response).

### 6.3 Frontend

Add `resetUserPassword` to `adminApi` in `client.ts`:
```
resetUserPassword: (id: number, newPassword: string) =>
  apiCall(`/users/${id}/reset-password`, { method: 'POST', body: JSON.stringify({ new_password: newPassword }) })
```

In `UserManagement.tsx`, add a "Reset Password" action next to the existing "Delete" button
in the table's action column. Opens a `ResetPasswordModal` (mirrors the existing
`CreateUserModal` pattern: local `newPassword` state, a `useMutation`, Cancel/Confirm
buttons). Since there's no email-sending infrastructure in this project, the modal shows
the new password back to the admin on success (in the modal itself, not a toast that
auto-dismisses) so they can relay it to the student out-of-band.

### 6.4 Tasks

- [ ] Backend: `AdminPasswordReset` payload model in `payload.py`
- [ ] Backend: `POST /users/{user_id}/reset-password` endpoint in `users.py` (404 on missing user, clears refresh token on success)
- [ ] Backend: unit test — resetting a password invalidates any existing refresh token (old refresh token 401s on `/api/auth/refresh` afterward)
- [ ] Frontend: `resetUserPassword` in `adminApi`
- [ ] Frontend: `ResetPasswordModal` + row action wiring in `UserManagement.tsx`
- [ ] Manual QA: reset a password, confirm old session is logged out and new password logs in via `/api/auth/login`

---

## 7. NEW FEATURE — Question Browser, Detail View, Edit UI & Test Explorer

**Requested by:** user, 2026-07-01: "admin should be able to pick any question, figure out
planned tests, look at questions and answers of every question in the db" — plus "make sure
all entries and fields can be easily changed and the database will propagate the changes."
This section supersedes the narrower "question edit UI" backlog line by folding in the
detail-view and test-browsing asks, since all three live in the same page
(`DataManagement.tsx`) and share the same underlying data. Full audit in `DEBUG_LOG.md`
2026-07-01.

### 7.1 What's already correct (verified, not assumed)

- The **version-propagation architecture is sound.** Every read of `QuestionOption` across
  `student.py` and `admin.py` filters by `latest_version_id` (checked all 6 call sites), so
  once a question is edited, students and every admin view see the new content immediately
  — no stale-cache class of bug here.
- `PATCH /admin/questions/{question_id}` (`admin.py:1001`) already does the right thing on
  edit: creates a new `QuestionVersion`, clones options with updated correctness flags,
  updates `Question.current_*`/`latest_version_id`, sets `annotation_stale=True`, and writes
  an audit log entry (`_write_admin_audit`). **No backend changes needed for editing itself.**
- `GET /admin/questions` (`admin.py:150-248`) already returns, per question: full
  `current_passage_text`, `current_question_text`, `current_correct_option_label`,
  `current_explanation_text`, complete `options` array (with `is_correct` per option), and a
  merged `annotation` object (grammar/reading focus keys, difficulty, trap keys, etc.). It
  also already supports `source_test_name` / `source_release_year` / `source_exam_code` /
  `sort_by_source=true` filters for ordered, per-test browsing. **No new backend work needed
  to fetch full Q&A data — it's already in the response.**

### 7.2 What's actually broken or missing

- `DataManagement.tsx` never renders any of the above except a truncated `question_text` —
  no detail view exists, so admins can't currently look at a question's passage, options,
  correct answer, or explanation from the UI at all.
- `adminApi.editQuestion()` is defined in `client.ts` but called from nowhere — dead code.
  There is no edit form, so fields cannot be changed from the UI despite the backend fully
  supporting it.
- The frontend `Question` type mismatches the real API shape: `grammar_focus_key` /
  `reading_focus_key` / `difficulty_overall` are declared top-level but actually arrive
  nested under `annotation.*`, so the existing Focus/Difficulty table columns silently
  render `—` for every row (see `DEBUG_LOG.md` finding #4).
- `annotation_stale` (set by every edit) isn't in the frontend type and isn't surfaced
  anywhere — an admin has no way to see which edited questions still carry pre-edit AI
  annotation metadata.
- There's no "browse by test" view — questions can only be paged through 25-at-a-time with
  status/origin filters, with no sense of which test/section/module a question belongs to
  or how many questions that test/module has.

### 7.3 Backend changes

1. Add `annotation_stale` to the per-item dict in `list_questions` (`admin.py:226-246`) —
   one line, the column already exists on `Question`.
2. New lightweight aggregation endpoint for the test explorer's landing view:
   ```
   GET /admin/tests
   ```
   Groups `Question` by `(source_release_year, source_test_name, source_exam_code,
   source_subject_code, source_section_code, source_module_code)` with `COUNT(*)` and
   `COUNT(*) FILTER (WHERE practice_status IN ('active','approved'))`, so the UI can render
   "Test 4 · sec01 · mod01 — 33 questions (33 approved)" cards without paging through the
   full question list. Mirrors the grouping the `ingestion-status` skill already does via
   raw SQL over `question_jobs`/`question_assets` — this endpoint groups the canonical
   `Question` columns instead, which is what the admin app should browse by (ingestion job
   status is a separate, already-covered concern via the `ingestion-status` skill).

No other backend changes needed — §7.1 already covers detail/edit/browse data needs.

### 7.4 Frontend changes

- Fix the `Question` TS type in `types/index.ts` to match reality: move
  `grammar_focus_key`/`reading_focus_key`/`difficulty_overall` into a nested `annotation?:
  Record<string, any>` field (or a typed `QuestionAnnotation` interface), add
  `current_explanation_text`, `annotation_stale`, `is_admin_edited`, `official_overlap_status`,
  and the `source_*` columns already returned but not typed.
- Fix `DataManagement.tsx`'s Focus/Difficulty columns to read `q.annotation?.grammar_focus_key
  ?? q.annotation?.reading_focus_key` and `q.annotation?.difficulty_overall`.
- New `QuestionDetailModal`, opened on row click: read-only view of passage, question text,
  all options (correct one highlighted), explanation, and annotation metadata, with an
  "annotation stale — needs reannotation" badge when `annotation_stale === true`. An "Edit"
  button switches the modal into a form (question/passage/paired-passage/underlined text,
  correct-option-label select, explanation) that calls the now-wired `adminApi.editQuestion`.
- New "Tests" tab/mode in `DataManagement.tsx`: fetches `GET /admin/tests`, renders one card
  per test/section/module; clicking a card filters the question list via the already-existing
  `source_test_name` + `sort_by_source=true` params so questions display in correct Q# order.

### 7.5 Tasks

- [ ] Backend: add `annotation_stale` to `list_questions` response
- [ ] Backend: `GET /admin/tests` aggregation endpoint
- [ ] Backend: unit test for `/admin/tests` grouping + counts
- [ ] Frontend: fix `Question` type to match actual API shape (nested `annotation`)
- [ ] Frontend: fix Focus/Difficulty column rendering in `DataManagement.tsx`
- [ ] Frontend: `QuestionDetailModal` (view mode) wired to row click
- [ ] Frontend: edit mode in the same modal, wired to `adminApi.editQuestion`
- [ ] Frontend: `annotation_stale` badge in the modal and/or as a table indicator
- [ ] Frontend: "Tests" browse tab using `GET /admin/tests` + `sort_by_source`
- [ ] Manual QA: edit a question, confirm the new version's text/options appear immediately in both the admin detail view and a student-facing question fetch
- [ ] Manual QA: browse a test end-to-end (pick test → module → question → view → edit)

---

## 8. NEW FEATURE — User Edit Endpoint

**Requested by:** user, 2026-07-01 (part of the "entries and fields easily changed" ask).

### 8.1 Rationale

Confirmed by reading `backend/app/routers/users.py` in full: it has `POST ""`, `GET ""`,
`GET "/{user_id}"`, `DELETE "/{user_id}"` — no update route. An admin cannot currently fix a
typo'd email/username or change a user's `role` without a direct DB edit.

### 8.2 Backend

```
PATCH /users/{user_id}
```
Body: partial `{ username?, email?, role? }` (reuse the `exclude_unset` pattern from
`AdminEditRequest`/`edit_question`). Enforce the same uniqueness checks `create_user` already
does for `username` (and add one for `email` if set). `is_active` toggling can reuse this
endpoint too (`{ is_active: false }`) rather than adding a separate route.

### 8.3 Frontend

Add `updateUser` to `adminApi`; add an "Edit" action next to "Delete" and the §6 "Reset
Password" action in `UserManagement.tsx`'s row actions, opening a small inline edit form
(mirrors `CreateUserModal`).

### 8.4 Tasks

- [ ] Backend: `PATCH /users/{user_id}` endpoint + uniqueness checks
- [ ] Backend: unit test — duplicate email/username on edit returns 409, not 500
- [ ] Frontend: `updateUser` in `adminApi`
- [ ] Frontend: edit action + form in `UserManagement.tsx`

---

## 9. NEW FEATURE — Modular Widget Dashboard (Desktop + iPad)

**Requested by:** user, 2026-07-01. Originally framed around a reference screenshot (not
reachable from this Linux session — see history), but the user clarified they were describing
the idea in broad strokes and want an AI-led design rather than a pixel match, with one hard
requirement: **panels must be easy to rearrange after the first design ships.** Design approved
2026-07-01.

### 9.1 Approved design

**Structure:** the 4 existing pages (`/users`, `/data`, `/students`, `/pipeline`) stay as-is —
full-featured destinations for editing/filtering/deep-dive work. Add a new `/dashboard` route,
made the default landing page (replaces the current `Navigate to="/users"` redirect in
`App.tsx`), built as a **grid of independent, rearrangeable panels** surfacing "at a glance"
summaries pulled from each domain.

**Rejected alternatives:**
- *Make each existing page internally modular* (drag-reorder cards within e.g.
  `PipelinePerformance`) — less effort, but doesn't give the cross-cutting "everything at a
  glance" dashboard feel that was the actual ask.
- *Full dashboard-builder* (multiple saved layouts, arbitrary widget catalog) — over-engineered
  for an internal tool with a single admin persona.

**Mechanism — how "movable after the first design" gets built:**
- Library: **`react-grid-layout`** — drag-to-reorder, resize, and responsive breakpoints out of
  the box. One widget set is defined once; the library reflows it differently at desktop width
  vs. iPad width, which is the literal mechanism for "same admin functions on both platforms,
  different layout."
- Each widget is a **self-contained component**: its own data hook (reusing existing
  `adminApi` calls — no new endpoints required for v1), its own "panel shell" (title bar + drag
  handle), no cross-widget coupling. Reordering is free; adding a new widget later (e.g. the
  §5 heatmap or §7 question browser, once built) is just registering another panel.
- Layout (panel positions/order per breakpoint) persists to `localStorage` for v1 — no backend
  schema needed. A backend-synced layout (per-admin, cross-device) is a possible future add,
  not in scope now.

**Candidate v1 widgets** (all backed by data/endpoints that already exist — no new backend
work required to populate the dashboard itself):
- Total users / active users (from `listUsers`)
- Questions pending review + approve rate (from `getGenerationAnalytics`)
- Auto-release status + enable/disable control (from `getAutoReleaseStatus`/`enable`/`disable`)
- Recent batches table (from `getBatchAnalytics`)
- Cohort weak-spots summary (from the currently-unused `/analytics/weak-spots` — this dashboard
  is also the natural first UI consumer of that dead endpoint noted in the Tier-A suggestions)
- Student activity heatmap panel — slots in once §5 is built
- Question browser quick-access panel — slots in once §7 is built

**Phased delivery:**
1. **Desktop:** grid shell, panel component contract, the widget list above, drag/resize on
   desktop viewport, `localStorage` persistence.
2. **iPad interactivity/animation layer** (after desktop ships): touch drag already works via
   `react-grid-layout`'s pointer-event handling; this phase adds **`framer-motion`** spring
   transitions so panels visibly glide into place on reorder/resize rather than snapping, plus
   touch-sized drag handles and breakpoint tuning for iPad's viewport width.

### 9.2 Tasks

- [ ] Add `react-grid-layout` (+ `framer-motion` for phase 2) as frontend dependencies
- [ ] Build the panel shell component (title bar, drag handle, remove/collapse affordance)
- [ ] Build each v1 widget as an isolated component against existing `adminApi` calls
- [ ] `/dashboard` route + grid shell wiring, `localStorage` layout persistence
- [ ] Make `/dashboard` the default landing route in `App.tsx`
- [ ] Desktop QA: drag, resize, reload-persists-layout, all widgets load real data
- [ ] iPad phase: `framer-motion` reflow animation, touch drag handle sizing, responsive breakpoint tuning
- [ ] iPad QA: every admin action reachable on desktop is also reachable on iPad (no dropped functionality)
