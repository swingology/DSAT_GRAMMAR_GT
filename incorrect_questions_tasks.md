# Incorrect Questions Review — Implementation Tasks

> **For agentic workers:** Implement task-by-task. Claim one task ID at a time, update its
> checkbox state, and leave a handoff note before stopping mid-task. This file is the execution
> layer for `incorrect_questions_plan.md`; the plan is the product/API source of truth.

**Goal:** Build the student missed-question review page and backend APIs described in
`incorrect_questions_plan.md`, including the gap-review fixes for source typing, dedup
semantics, source metadata filters, historical `unknown` rows, and cross-session handoff.

**Stack:** FastAPI + SQLAlchemy async + Alembic + pytest in `backend/`; React + TypeScript +
Vite + TanStack Query in `APP/STUDENT_APP_REDUX/`.

## Agent Operating Protocol

- Start every session by reading `incorrect_questions_plan.md`, this file, and `git status`.
- Use `rtk` for shell commands in this repo.
- Do not batch unrelated tasks. Each task below is designed to be independently reviewable.
- Claim a task by replacing its `Handoff note: Not started.` with `Handoff note: Status=in_progress;
  owner=<agent/session>; base=<commit>; files=<expected files>.` The task file is the durable
  ownership ledger; chat-only claims do not survive sessions.
- If using subagents, assign by phase boundary: migration/backend model, backend API, frontend
  data layer, frontend UI, QA. Subagents must report changed files, tests run, and open risks.
- Agents sharing one worktree must not edit the same file concurrently. Use separate worktrees or
  serialize overlapping edits, then have the main agent re-read and integrate the final file.
- If stopping mid-task, add a `Handoff note:` under that task with:
  - current status,
  - files touched,
  - tests run and exact results,
  - next command or edit,
  - blockers or assumptions.
- Mark a task complete only after all of its checkboxes and required verification pass. Record
  `Status=complete`, the commit (if any), and exact test results in its handoff note.
- Do not rewrite `MissedQuestionsTab.tsx` or alter `GET /study/missed` behavior. This feature is
  additive.

## Dependency Map

**Execution order:** complete IQ-B01 first. After IQ-B01 lands, separate agents may work on
IQ-B02 and IQ-B03 in parallel. The phase headings below group related work; they are not a rule
that all of Phase 1 must finish before any Phase 2 task starts.

1. IQ-B01 blocks IQ-B02 and IQ-B03 because both require the `source_type` schema/model contract.
2. IQ-B02 and IQ-B03 may run in parallel after IQ-B01 only in separate worktrees/branches because
   both touch `payload.py` and `student.py`; merge IQ-B02 first, then rebase/integrate IQ-B03. In a
   shared worktree, run IQ-B02 before IQ-B03.
3. IQ-B04 depends on IQ-B03 so it can reuse the review query/filter semantics.
4. IQ-F01 depends on the final IQ-B03 and IQ-B04 endpoint/response contracts.
5. IQ-F02 depends on IQ-F01. It does not need to wait for IQ-B02 to compile, but source badges
   cannot be integration-tested until IQ-B02 writes tagged attempts.
6. IQ-QA01 depends on every implementation task. Do not start final QA with any earlier task
   unchecked or with an unresolved handoff note.

---

## Phase 1 — Backend data model & submit tagging

### IQ-B01: Add `user_progress.source_type` with migration and model support

**Files:**
- Modify: `backend/app/models/db.py`
- Add: `backend/migrations/versions/034_user_progress_source_type.py` (use next revision ID if
  the repo has advanced)
- Test: migration/model coverage in the closest existing backend migration/model test location;
  if no migration-test harness exists, document manual Alembic verification in the handoff.

**Requirements:**
- Add `source_type = Column(String(20), nullable=True, index=True)` to `UserProgress`.
- Create index `ix_user_progress_source_type`.
- Migration backfill:
  - `diagnostic_session_id IS NOT NULL` -> `diagnostic`
  - all other existing rows -> `unknown`
- Keep column nullable in DB for safe deploy/backfill compatibility, but application code should
  write a non-null value after IQ-B02.

- [x] Add model column and migration.
- [x] Run Alembic upgrade against the local dev DB or a disposable test DB.
- [x] Verify schema has `source_type` and index.
- [x] Verify backfill SQL handles existing rows correctly.

**Handoff note:** Status=complete; owner=Codex/missed_question; base=4586709; no commit yet.
Changed `backend/app/models/db.py`, `backend/migrations/versions/034_user_progress_source_type.py`,
`backend/tests/test_models.py`, and this ledger. `tests/test_models.py`: 7 passed. Dev DB upgraded
033 -> 034; verified nullable `varchar(20)`, `ix_user_progress_source_type`, 19 diagnostic rows,
2 unknown rows, and 0 backfill mismatches.

---

### IQ-B02: Persist source type from all submit paths

**Files:**
- Modify: `backend/app/models/payload.py`
- Modify: `backend/app/routers/student.py`
- Modify: `APP/STUDENT_APP_REDUX/src/api/client.ts`
- Modify: `APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts`
- Modify call sites:
  - `APP/STUDENT_APP_REDUX/src/components/practice/PracticeTestRunner.tsx`
  - `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`
  - `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx`
  - `APP/STUDENT_APP_REDUX/src/components/dashboard/TestModeTab.tsx`
  - `APP/STUDENT_APP_REDUX/src/components/dashboard/DiagnosticTab.tsx`
- Tests:
  - `backend/tests/test_student_api_contracts.py`
  - `backend/tests/test_diagnostic_sessions.py`
  - relevant student frontend hook/component tests under `APP/STUDENT_APP_REDUX/src/**/__tests__/`

**Backend contract:**
- `UserProgressCreate.source_type` accepts only `practice_test`, `drill`, `practice`, `unknown`.
- Default is `unknown` so older clients do not fail immediately.
- `/api/submit` stores `body.source_type or "unknown"`.
- `/api/diagnostic/{session_id}/submit` stores `diagnostic`.
- Invalid source types return 422. `source_type='diagnostic'` sent to the **generic** `/api/submit`
  must 422 — `diagnostic` is intentionally excluded from the generic `Literal` so the two submit
  paths cannot lie about each other's source. Diagnostic attempts only enter via
  `/api/diagnostic/{session_id}/submit`, which hardcodes `diagnostic`.

**Frontend mapping:**
- `PracticeTestRunner.tsx` -> `practice_test`
- `TestModeTab.tsx` -> `practice_test`
- `useGrammarSession.ts` -> `drill`
- `MixedPracticePage.tsx` -> `practice`
- `DiagnosticTab.tsx` fallback generic-submit path -> `practice`; live diagnostic sessions
  continue using `api.diagnosticSubmit()`.

- [x] Add backend payload field and persistence.
- [x] Add backend tests for: omitted (stores `unknown`), explicit `practice_test`/`drill`/`practice`
      (accepted), invalid value (422), `source_type='diagnostic'` on generic `/submit` (422), and
      `/diagnostic/{session_id}/submit` stores `diagnostic`.
- [x] Add source type to `api.submitAnswer()` TS type.
- [x] Add source type to `useSubmitAnswer()` mutation input.
- [x] Update every known call site above.
- [x] Update frontend tests/mocks that assert submit payloads.

**Suggested verification:**

```bash
rtk pytest backend/tests/test_student_api_contracts.py -q
rtk pytest backend/tests/test_diagnostic_sessions.py -q
rtk npm --prefix APP/STUDENT_APP_REDUX test -- --run
```

**Handoff note:** Status=complete; owner=Codex/missed_question; base=4586709; no commit yet.
Backend payload/persistence and all five generic frontend call sites are tagged; diagnostic submit
hardcodes `diagnostic`. Focused backend source-tag/model coverage: 17 passed. Frontend hook/session/
test-mode coverage: 27 passed. TypeScript project check and production build pass. FastAPI's request
model rejects `diagnostic`/invalid generic values (mapped to HTTP 422); direct async tests verify
stored `unknown`, `drill`, and `diagnostic`. The full backend TestClient files were not run as a
whole because their shared lifespan waits on the unavailable `localhost:5432/dsat_test`; focused
tests bypassing that unrelated startup dependency pass. Dev DB remains verified at revision 034.

---

## Phase 2 — Review APIs

### IQ-B03: Add review response models and `GET /api/study/review`

**Files:**
- Modify: `backend/app/models/payload.py`
- Modify: `backend/app/routers/student.py`
- Test: `backend/tests/test_student_api_contracts.py` or a new focused
  `backend/tests/test_study_review.py`

**Endpoint:** `GET /api/study/review`

**Query params:**
- `user_token` required
- `source_type` comma-separated; omitted or `all` means all source types
- `source_test_name`
- `source_section_code`
- `source_module_code`
- `domain`
- `focus_key`
- `stem_type_key`
- `difficulty`
- `content_origin` comma-separated
- `page` default `1`, minimum `1`
- `page_size` default `20`, minimum `1`, maximum `100`

`difficulty` is an exact attempt-time facet string returned by `/study/review/filters`; do not
hardcode `easy|medium|hard`, because existing data also contains values such as `low`.

**Response envelope:**

```python
{
    "items": [...],
    "total": 42,
    "page": 1,
    "page_size": 20,
    "has_more": True,
}
```

**Response item fields** (wire names) and their **source columns** — note the `current_*`
prefix on `Question`; do NOT query the unprefixed `passage_text`/`explanation_text` columns
(those live on `QuestionVersion`, which this endpoint does not join):

| Response field | Source column |
|---|---|
| `question_id` | `UserProgress.question_id` |
| `passage_text` | `Question.current_passage_text` |
| `paired_passage_text` | `Question.current_paired_passage_text` |
| `underlined_text` | `Question.current_underlined_text` |
| `question_text` | `Question.current_question_text` |
| `options[].label` / `options[].text` / `options[].is_correct` | `QuestionOption.option_label` / `option_text` / `is_correct` — **current version only** (see Versioned-options fetch below) |
| `correct_option_label` | effective current-version correct label after the integrity check below |
| `explanation` | `QuestionAnnotation.explanation_jsonb` fallback chain (see Explanation source below) |
| `user_answer` | `UserProgress.selected_option_label` of the latest matching miss row |
| `domain` | `UserProgress.question_domain` |
| `focus_key` / `focus_key_source` | `UserProgress.missed_*` per Focus-key semantics below |
| `stem_type_key` | `Question.stem_type_key` |
| `difficulty` | `UserProgress.question_difficulty` |
| `content_origin` | `Question.content_origin` (Postgres `Enum` — see note) |
| `source_test_name` / `source_section_code` / `source_module_code` / `source_question_number` | `Question.*` |
| `source_type` / `source_types` / `miss_count` / `last_missed_at` | derived from filtered `UserProgress` rows |

**Versioned-options fetch (NEW code — not a reuse of `/study/missed`):** `/study/missed` does not
fetch `QuestionOption` at all, so there is no existing template inside that endpoint. `QuestionOption`
is keyed by `question_version_id` (`UniqueConstraint("question_version_id", "option_label")`), so
joining on `question_id` alone returns options from every version. Scope to the current version via
`Question.latest_version_id` (`db.py:104`). Use the proven pattern already in this router:
- Bulk: `student.py:455–459` — build `{q.latest_version_id: q.id}` then
  `select(QuestionOption).where(QuestionOption.question_version_id.in_(...))`.
- Single (reference shape): `student.py:1627–1630` —
  `select(QuestionOption).where(question_id == q.id).where(question_version_id == q.latest_version_id).order_by(option_label)`.

**Explanation source:** follow the existing `/study/missed` extraction at `student.py:1574–1582` —
pull from `QuestionAnnotation.explanation_jsonb` with the fallback chain
`explanation_short` → `short` → `explanation` → `annotation_jsonb.explanation_short`. Do **not**
read `Question.current_explanation_text` instead; the annotation-based chain is the proven pattern
and handles missing keys. (The plan's §4 mapping table now points here too — plan and tasks agree.)

**Correct-answer source of truth:** `options[].is_correct` comes from `QuestionOption.is_correct`
(current version only); `correct_option_label` normally agrees with
`Question.current_correct_option_label`. Cross-check the fields, but do not use a runtime `assert`
that can turn one bad question into a 500 for the whole page. When exactly one current-version
option is marked correct, use that option's label as the effective `correct_option_label` and log
a warning if `Question.current_correct_option_label` differs. When zero or multiple options are
marked correct, log a data-integrity error; if `Question.current_correct_option_label` names a
fetched option, use it and normalize the response's `is_correct` flags to that one label. If no
single correct option can be resolved, log the question ID and raise a deliberate API error rather
than silently returning a misleading answer. Do not use a bare Python assertion for this branch.

**`content_origin` is a Postgres `Enum`** (`CONTENT_ORIGINS = official, unofficial, generated`,
`ontology.py:9`), not a `String`. Parse the comma-separated values, reject values outside that
allowlist with 422, and apply an enum-aware `Question.content_origin.in_(validated_values)`
comparison. Do not cast the database column to `String`.

**CSV filter validation:** trim and deduplicate `source_type` and `content_origin` values before
querying. Omitted, blank, or exactly `all` means no filter. Reject `all` mixed with concrete values
and reject values outside the documented allowlists with 422. The review `source_type` allowlist
includes all five persisted values, including `diagnostic` and `unknown`.

**Dedup semantics:**
- Filter rows first, then group by question.
- `miss_count` counts matching missed rows for that question.
- `last_missed_at`, `user_answer`, singular `source_type`, `domain`, `difficulty`, `focus_key`,
  and `focus_key_source` come from the same latest matching miss row. Do not use independent
  `MAX()` calls for these row-level fields; that can combine values from different attempts.
- `source_types` is the sorted distinct source-type list from matching misses.
- Sort cards by `last_missed_at DESC`.
- Treat a null persisted `source_type` defensively as `unknown` in singular and aggregate output,
  even though the migration and new submit paths should prevent it. The `source_type=unknown`
  filter and the filters facet must likewise treat SQL `NULL` as `unknown`.
- **Latest-row selection:** build the filtered missed-row relation first, including joins needed
  for `Question`-owned filters. Rank it with `row_number() over (partition by question_id order by
  timestamp desc nulls last, id desc)`. The `rn = 1` row supplies all latest-attempt fields above.
  An equivalent deterministic latest-row subquery is acceptable, but `MAX(timestamp)` by itself
  is not: it cannot supply `selected_option_label` or resolve equal timestamps.
- **Dedup precedes pagination:** aggregate the filtered relation by `question_id`, join its stats
  to the `rn = 1` rows, then paginate the deduped cards. Use the stable order
  `last_missed_at DESC NULLS LAST, question_id ASC` so ties have stable page boundaries. Do not
  slice raw miss rows first and dedup inside the page.
- **`total` is the deduped question count** (distinct question cards in the full filtered set), not
  the raw miss-row count — it must match the pagination of cards. `has_more = (offset + len(items))
  < total` (or equivalent).

**Focus-key semantics:**
- Grammar: `focus_key = UserProgress.missed_grammar_focus_key`; `focus_key_source = grammar_focus_key`.
- Reading: `focus_key = missed_reading_focus_key` when present (`focus_key_source = reading_focus_key`),
  else fall back to `missed_reading_skill_family_key` (`focus_key_source = reading_skill_family_key`).
- Resolve that fallback from the latest matching miss row selected above. Do not use `func.max()`
  across the group: lexical maximum is not necessarily the latest attempt's classification.
- **`focus_key` filter resolution:** the `focus_key` query param must match against the column that
  *produced* the value, not always `missed_reading_focus_key`. Filter with
  `(missed_grammar_focus_key = :v) OR (missed_reading_focus_key = :v) OR (missed_reading_skill_family_key = :v)`
  so a reading-skill-family facet value still filters its rows. Because the filter ORs across all
  three, the frontend can round-trip a `focus_key` value without the backend having to attribute it
  to a specific column on the `/review/filters` side.

- [x] Add Pydantic response models with the fields above.
- [x] Implement endpoint with auth via `student_required` + `user_token` query param (matches
      `/study/missed` at `student.py:1515`).
- [x] Build the filtered missed-row relation, deterministic `row_number()` latest-row relation,
      grouped stats (`miss_count`, sorted distinct `source_types`, `last_missed_at`), deduped total,
      and stable card pagination in that order. Pull latest `user_answer`/`source_type`/domain/
      difficulty/focus fields only from `rn = 1`.
- [x] Bulk-fetch `Question` + current-version `QuestionOption` (via `latest_version_id`) +
      `QuestionAnnotation` for the page's question_ids; assemble options/explanation per the
      source tables above.
- [x] Implement the `focus_key` OR-filter resolution and `content_origin` enum-aware filter.
- [x] Add tests for: auth, missing token, empty result, pagination + stable page boundaries,
      reverse-chron ordering, source/domain/focus/stem/difficulty/content/source-section filters,
      per-question dedup after filters, `source_types`, latest-miss `user_answer`, current-version
      options only (no stale/duplicate options from other versions), `total` = deduped count, and
      `focus_key` filter matching a reading-skill-family facet value. Seed equal-timestamp misses
      with different IDs and attempt metadata to prove the tie-breaker and ensure latest-row fields
      are not assembled from independent aggregate maxima. Cover invalid `source_type` and
      `content_origin` query values (422), null-source rows behaving as `unknown`, correctness-field
      mismatch recovery, and an unresolvable correct answer returning a logged API error.

**Handoff note:** Status=complete; owner=Codex/missed_question; base=2400c67; no commit yet.
Implemented the filtered/ranked/grouped review query, deterministic pagination, current-version
options, latest annotation explanations, correctness integrity handling, all documented filters,
and response models. Focused Phase 2/model tests: 24 passed. Live PostgreSQL checks returned 200
for unfiltered, diagnostic, unknown, page 2, and `difficulty=low` requests; invalid content origin
and mixed `all` CSV requests returned 422. Implementation discovery: attempt data contains `low`,
so difficulty now round-trips exact facet strings instead of a hardcoded three-value enum.

---

### IQ-B04: Add `GET /api/study/review/filters`

**Files:**
- Modify: `backend/app/models/payload.py`
- Modify: `backend/app/routers/student.py`
- Test: same backend review test file as IQ-B03

**Endpoint:** `GET /api/study/review/filters`

**Query params:**
- `user_token` required

**Response fields:**
- `source_types`
- `source_test_names`
- `source_section_codes`
- `source_module_codes`
- `domains`
- `focus_keys`
- `stem_type_keys`
- `difficulties`
- `content_origins`

**Rules:**
- Only include facets present in this student's missed rows.
- Do not include facets from correct rows or other students.
- Include `unknown` in `source_types` when the student has historical unknown or null-source misses.
- Do not apply currently selected page filters to this endpoint; frontend caches it once per
  page load.
- `focus_keys` is a flat list of distinct values drawn from `missed_grammar_focus_key`,
  `missed_reading_focus_key`, and `missed_reading_skill_family_key` (union of all three). Because
  the `/study/review` `focus_key` filter ORs across all three columns, the frontend can round-trip
  any facet value without per-value column attribution — so `focus_keys` can stay flat (no need to
  return which column each value came from).

- [x] Add response model.
- [x] Implement endpoint.
- [x] Add tests for student scoping, missed-only facets, `unknown`, and empty state.

**Handoff note:** Status=complete; owner=Codex/missed_question; base=2400c67; no commit yet.
Implemented student-scoped missed-only aggregate facets with null-source `unknown` handling and a
flat union of all focus-key columns. Covered scoping SQL, focus union, unknown, and empty facets in
`backend/tests/test_study_review.py`; live responses verified source/content/domain/focus facets.

---

## Phase 3 — Frontend

### IQ-F01: Add student review API client and hooks

**Files:**
- Modify: `APP/STUDENT_APP_REDUX/src/api/client.ts`
- Modify or add: `APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts` or
  `APP/STUDENT_APP_REDUX/src/hooks/useReviewData.ts`
- Tests: hook/client tests under `APP/STUDENT_APP_REDUX/src/hooks/__tests__/`

**Requirements:**
- Add `api.getReviewQuestions(params)` for `/study/review`.
- Add `api.getReviewFilters(userToken)` for `/study/review/filters`.
- Add `useReviewQuestions(filters, page)` and `useReviewFilters()`.
- Query keys must include all filters and page values so filter changes refetch correctly.
- Types must match backend response fields from IQ-B03/IQ-B04.
- UI filter changes must reset `page` to 1 before requesting data; otherwise a valid filtered
  result can appear empty because the previous page offset is out of range.

- [x] Add API methods and TS types.
- [x] Add hooks.
- [x] Add tests for query params, query keys, CSV encoding, and page reset on filter changes.

**Handoff note:** Status=complete; owner=Codex/missed_question; base=9e80a9d; no commit yet.
Added exact backend response types, deterministic URL/CSV serialization, and independently cached review
and facet hooks. Query keys contain the full filter object, page, and page size. Focused client/hook tests
cover all query parameters, array filters, token encoding, and refetches on filter/page changes. Page-reset
coverage lives with IQ-F02 because pagination state is owned by the page.

---

### IQ-F02: Build `/review` page and dashboard entry point

**Files:**
- Add: `APP/STUDENT_APP_REDUX/src/pages/ReviewMissedPage.tsx`
- Modify: `APP/STUDENT_APP_REDUX/src/App.tsx`
- Modify: `APP/STUDENT_APP_REDUX/src/pages/DashboardPage.tsx`
- Tests:
  - `APP/STUDENT_APP_REDUX/src/pages/__tests__/ReviewMissedPage.test.tsx`
  - update `APP/STUDENT_APP_REDUX/src/components/__tests__/DashboardPage.test.tsx`

**UI requirements:**
- Route `/review`.
- Dashboard summary card links to `/review` and shows the deduped, unfiltered `total` from the
  review contract (a `page=1&page_size=1` request is sufficient). Reuse an existing count only if
  a test proves it has exactly the same student scope and per-question dedup semantics.
- Filters:
  - source segmented control: All plus only the `source_types` returned by `/review/filters`, in
    canonical order Diagnostic, Practice Test, Drill, Practice, Unknown
  - source test dropdown
  - separate source section and source module dropdowns
  - domain dropdown
  - focus key dropdown
  - stem type dropdown
  - difficulty toggle
  - content origin toggle
- Cards:
  - full question text
  - collapsible passage when present
  - all options A-D neutral before reveal
  - one Show answer toggle revealing correct highlight and explanation together
  - badges for domain, focus, difficulty, content origin, and source type(s)
- Loading, error, and empty states should visually match the existing dashboard style without
  changing `MissedQuestionsTab.tsx`.

- [x] Build route and page.
- [x] Add dashboard entry card.
- [x] Add tests for loading/error/empty, filter changes, pagination, passage reveal, answer
  reveal, and dashboard link.

**Handoff note:** Status=complete; owner=Codex/missed_question; base=9e80a9d; no commit yet.
Added the protected `/review` route, canonical source segments, all endpoint-backed facets, page reset on
every filter change, responsive question cards, passage/answer disclosure, states, and pagination. The
dashboard requests `page=1&page_size=1` with no filters and links the returned deduplicated total to
`/review`. `MissedQuestionsTab.tsx` was not changed. Verification: TypeScript passes; production build
passes; 15 focused Phase 3 tests pass; live Vite source returns 200; direct and Vite-proxied review calls
return a populated response for a current DB user. Repository-wide tests still have 17 unrelated existing
grammar/card/color failures. Lint is blocked before file analysis by the existing ESLint config omitting
the `react-hooks` plugin registration. Playwright is not installed, so no browser screenshots were taken.

---

## Phase 4 — QA & release handoff

### IQ-QA01: End-to-end verification and release handoff

**Files:**
- Update this task's handoff note with final verification.
- Update `incorrect_questions_plan.md` only if implementation discovers a real design change.

**Required commands:**

```bash
rtk pytest backend/tests/test_student_api_contracts.py -q
rtk pytest backend/tests/test_diagnostic_sessions.py -q
rtk npm --prefix APP/STUDENT_APP_REDUX test -- --run
rtk npm --prefix APP/STUDENT_APP_REDUX run build
```

**Manual QA:**
- Start the dev stack using the repo's current startup path.
- Use a student account with misses from at least two source types, or seed rows manually in the
  dev DB.
- Verify All view dedups a repeated missed question and shows multiple `source_types`.
- Verify filtering to one source changes `miss_count`, latest answer, and source badges to the
  filtered subset.
- Verify historical `unknown` rows appear under All and Unknown.
- Verify answer/explanation remain hidden until Show answer is clicked.
- Verify passage reveal does not shift the page into an unusable layout on mobile width.

- [ ] Run backend tests.
- [ ] Run frontend tests and build.
- [ ] Complete manual QA.
- [ ] Record final status, commands, and residual risks below.

**Handoff note:** Not started.
