# Incorrect Questions Review — Plan

**Status:** Design approved 2026-07-16. Gap-review fixes added 2026-07-16. Second-pass
review fixes (versioned-options join, `current_*` field mapping, `domain`/`difficulty`/`focus_key`
column sources, dedup+pagination semantics, `diagnostic`-on-generic-endpoint 422) added
2026-07-16. Phases 1 and 2 (data model, submit tagging, review APIs, and filter facets) implemented
and verified on branch `missed_question`; frontend review hooks/page remain.

**Implementation plan:** the phase-by-phase task breakdown (exact file paths, code, tests,
commit steps) will live in `incorrect_questions_tasks.md`, following the same design/execution
split used by `admin_dashboard_plan.md` / `admin_dashboard_tasks.md`. This file is the
design/spec layer.

---

## 1. Goal

Let a student review every question they've gotten wrong — across diagnostic sessions,
practice tests, drills, general practice, and historical uncategorized attempts — from a single
page reachable from the main dashboard. Each missed question shows the full passage, question,
and answer choices; the correct answer and explanation stay hidden until the student explicitly
reveals them. Filterable by attempt source, source test/section metadata, domain,
concept/focus key, question type, difficulty, and content origin (official/generated/unofficial).
Sorted reverse-chronologically by when it was answered.

## 2. Current state — what already exists

- `MissedQuestionsTab.tsx` (`APP/STUDENT_APP_REDUX/src/components/dashboard/`) — a dashboard
  tab backed by `GET /study/missed` (`backend/app/routers/student.py:1513`). It groups misses
  by question (dedup, shows a miss-count), truncates question text to 3 lines, has no passage
  or full choice list, filters only by `domain` (grammar/reading), and already has a working
  explanation-toggle button per card.
- **This is left as-is.** The new feature is a separate, purpose-built page — not a rewrite of
  this tab — so nothing here regresses the existing dashboard.

## 3. Data model gap and fix

`user_progress` (`backend/app/models/db.py:500`) can tell "diagnostic" apart from everything
else via `diagnostic_session_id`, but has no field distinguishing a practice-test attempt from
a drill or general-practice attempt — all three flow through the same generic `POST /submit`
endpoint (`student.py:538`) with no session/source tag.

**Fix:** add `user_progress.source_type` (`String(20)`, nullable, indexed).

Values: `diagnostic` | `practice_test` | `drill` | `practice` | `unknown`

- **Migration backfill:** rows with `diagnostic_session_id IS NOT NULL` -> `'diagnostic'`;
  every other existing row -> `'unknown'` (attempts before this change cannot be reclassified
  retroactively — accepted trade-off). Include an index named
  `ix_user_progress_source_type`.
- **Diagnostic submit** (`POST /diagnostic/{session_id}/submit`, `student.py:1767`): already a
  dedicated endpoint — hardcode `source_type='diagnostic'` when constructing the `UserProgress`
  row. No client change needed.
- **Generic submit** (`POST /submit`, `student.py:538`): add
  `source_type: Literal['practice_test', 'drill', 'practice', 'unknown'] = 'unknown'` to
  `UserProgressCreate` (`backend/app/models/payload.py:106`) and persist it on the
  `UserProgress` row. The field is intentionally optional at the backend boundary for
  compatibility while all callers are upgraded. New/updated student-app calls must pass a
  specific source type; missing values are accepted but stored as `'unknown'`.
  `source_type='diagnostic'` is **not** in the generic-endpoint `Literal` and must 422 if sent
  here — diagnostic attempts only enter through `POST /diagnostic/{session_id}/submit`, which
  hardcodes `'diagnostic'`. (This keeps the two submit paths from being able to lie about each
  other's source.)
- **Client API and mutation wrapper:** add `source_type` to
  `APP/STUDENT_APP_REDUX/src/api/client.ts::submitAnswer()` and to
  `APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts::useSubmitAnswer()`. The shared mutation
  wrapper is the critical propagation point; updating only leaf components will not work.
- **Known generic-submit call sites to update:**
  - `APP/STUDENT_APP_REDUX/src/components/practice/PracticeTestRunner.tsx` -> `'practice_test'`
  - `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts` -> `'drill'`
  - `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx` -> `'practice'`
  - `APP/STUDENT_APP_REDUX/src/components/dashboard/TestModeTab.tsx` -> `'practice_test'`
  - `APP/STUDENT_APP_REDUX/src/components/dashboard/DiagnosticTab.tsx` fallback generic-submit
    path -> `'practice'` unless a live `sessionId` exists, in which case it already uses
    `/diagnostic/{session_id}/submit`.
- **Drill routing note:** `ConceptSelectorPage.tsx` does not submit answers directly. It routes
  into `GrammarPractice`, whose underlying `useGrammarSession` submit is the actual drill
  source-type site.

## 4. Backend API

### `GET /study/review`

Query params:

| Param | Notes |
|---|---|
| `user_token` | required |
| `source_type` | comma-separated (`diagnostic,practice_test,...`); omitted/`all` = combined |
| `source_test_name` | question source metadata, exact value from `Question.source_test_name` |
| `source_section_code` | question source metadata, exact value from `Question.source_section_code` |
| `source_module_code` | question source metadata, exact value from `Question.source_module_code` |
| `domain` | `grammar` \| `reading` |
| `focus_key` | concept filter |
| `stem_type_key` | question-type filter |
| `difficulty` | exact attempt-time facet value returned by `/study/review/filters` (the current data includes values such as `low` and `medium`; do not hardcode a three-value enum) |
| `content_origin` | comma-separated `official,unofficial,generated` |
| `page`, `page_size` | pagination, default `page_size=20` |

Sort is fixed to reverse-chronological by `last_missed_at` — no sort selector (per requirement:
"for now keep it reverse ordered by date").

Dedup is per question within the currently filtered result set:

- `last_missed_at` is the latest missed `UserProgress.timestamp` for that question after all
  filters are applied.
- `user_answer`, `source_type`, `domain`, `difficulty`, `focus_key`, and `focus_key_source`
  describe that same latest matching miss row. These values must be selected as one row, not with
  independent `MAX()` aggregates that can combine metadata from different attempts.
- `source_types` is the sorted distinct list of source types for all matching misses for that
  question after filters are applied.
- `miss_count` is the number of matching misses for that question after filters are applied.
- A defensive SQL `NULL` source value behaves as `unknown` in output, facets, and filtering even
  though the migration and all upgraded submit paths should write non-null values.
- If a student missed the same question in both diagnostic and drill, the All view shows one
  card with both source types in `source_types`; filtering to Drill shows the drill miss only.

Reuses the two-step query pattern already proven in `/study/missed` (`student.py:1513–1604`):
a grouped `UserProgress` query (filter → `GROUP BY question_id` → `MAX(timestamp)` → order →
`LIMIT/OFFSET`), then a bulk fetch of `Question` + `QuestionAnnotation` for the page's
`question_id`s. `/study/missed` does **not** fetch `QuestionOption`; this endpoint adds a
current-version `QuestionOption` bulk fetch (see versioned-options caveat below). Extended with
`content_origin` (from `Question.content_origin`), question source metadata, and `source_type`.

**Versioned-options caveat (must be handled by the implementation):** `QuestionOption`
(`db.py:171`) is keyed by `question_version_id` (`UniqueConstraint("question_version_id",
"option_label")`) — options belong to a `QuestionVersion`, not directly to `Question`. The
`question_id` FK on `QuestionOption` is denormalized, so joining `Question → QuestionOption`
on `question_id` alone returns options for *every* version of the question (duplicates / stale
choices). The implementation MUST scope `QuestionOption` to the question's current version via
`Question.latest_version_id` (`db.py:104`) before reading `option_label` / `option_text` /
`is_correct`. Note: `/study/missed` does **not** fetch `QuestionOption` at all, so this is new
code, not a reuse. Use the proven pattern already in `student.py`: bulk via
`student.py:455–459` (`{q.latest_version_id: q.id}` then
`QuestionOption.question_version_id.in_(...)`), or the single-question shape at
`student.py:1627–1630` (`where(question_id == q.id).where(question_version_id == q.latest_version_id).order_by(option_label)`).

**Source-of-truth for "correct":** `Question.current_correct_option_label` and
`QuestionOption.is_correct` both express correctness. Cross-check them without a bare runtime
assertion. If exactly one current-version option is marked correct, its label is the effective
`correct_option_label`; log a warning if the `Question` field differs. If zero or multiple options
are marked correct but `Question.current_correct_option_label` names a fetched option, use that
label and normalize the response flags to it. If neither source resolves one correct option, log
the question ID and return a deliberate API error rather than exposing a misleading answer.

Focus-key semantics:

- For grammar rows, `focus_key = UserProgress.missed_grammar_focus_key`.
- For reading rows, `focus_key = UserProgress.missed_reading_focus_key` when present.
- If a reading miss has no `missed_reading_focus_key`, fall back to
  `UserProgress.missed_reading_skill_family_key`. This matches the existing backend reality
  where some reading-bank rows classify via `skill_family_key`/reading skill family instead of
  the narrower focus key.
- `focus_key_source` in the response says which field supplied the rendered filter value:
  `grammar_focus_key`, `reading_focus_key`, or `reading_skill_family_key`.
- **`focus_key` filter resolution:** the `focus_key` query param must match against the
  column that *produced* the facet value, not always `missed_reading_focus_key`. Concretely,
  filter with `(missed_grammar_focus_key = :v) OR (missed_reading_focus_key = :v) OR
  (missed_reading_skill_family_key = :v)` so a reading-skill-family facet value still filters
  its rows. Without this, reading-skill-family misses are unfilterable. Because the filter ORs
  across all three columns, `/review/filters` returns a flat distinct union of their values; it
  does not need per-value column attribution for the UI to round-trip a selected value.

`domain` and `difficulty` sources (denormalized at attempt time on `UserProgress`, not on
`Question` — `Question` has no `difficulty`/`domain` column):

- `domain` = `UserProgress.question_domain` (`db.py:514`, indexed).
- `difficulty` = `UserProgress.question_difficulty` (`db.py:518`). This is intentional: the
  review shows the difficulty the student faced at attempt time, not a post-hoc re-level on
  `Question`. Both the `domain`/`difficulty` filters and the response fields read from these
  `UserProgress` columns.

Response item — everything needed to render without a follow-up call:

```
question_id, passage_text, paired_passage_text, underlined_text, question_text,
options: [{ label, text, is_correct }], correct_option_label, explanation,
user_answer, domain, focus_key, focus_key_source, stem_type_key, difficulty,
content_origin, source_test_name, source_section_code, source_module_code,
source_question_number, source_type, source_types, miss_count, last_missed_at
```

**Response field → column mapping** (the wire names above are stable; the implementation reads
from these columns — note the `current_*` prefix on `Question`):

| Response field | Source column |
|---|---|
| `passage_text` | `Question.current_passage_text` |
| `paired_passage_text` | `Question.current_paired_passage_text` |
| `underlined_text` | `Question.current_underlined_text` |
| `question_text` | `Question.current_question_text` |
| `explanation` | `QuestionAnnotation.explanation_jsonb` fallback chain (`explanation_short` → `short` → `explanation` → `annotation_jsonb.explanation_short`), matching `/study/missed` at `student.py:1574–1582`. Do **not** read `Question.current_explanation_text` — the annotation-based chain is the proven pattern and handles missing keys. |
| `correct_option_label` | effective current-version correct label after the integrity check above |
| `options[].label` / `options[].text` / `options[].is_correct` | `QuestionOption.option_label` / `option_text` / `is_correct` (current version only — see versioned-options caveat) |
| `stem_type_key` | `Question.stem_type_key` |
| `content_origin` | `Question.content_origin` (Enum — see note below) |
| `source_test_name` / `source_section_code` / `source_module_code` / `source_question_number` | `Question.*` |
| `domain` | `UserProgress.question_domain` |
| `difficulty` | `UserProgress.question_difficulty` |
| `focus_key` / `focus_key_source` | `UserProgress.missed_*` per focus-key semantics above |
| `user_answer` | `UserProgress.selected_option_label` (latest matching miss row) |
| `source_type` / `source_types` / `miss_count` / `last_missed_at` | derived from filtered `UserProgress` rows |

The unprefixed `passage_text` / `paired_passage_text` / `underlined_text` / `explanation_text`
columns live on `QuestionVersion` (`db.py:136–141`), which this endpoint does **not** join — do
not query them. `content_origin` is a Postgres `Enum` (`CONTENT_ORIGINS = official, unofficial,
generated`, `ontology.py:9`), not a `String`; the `content_origin` comma-separated filter must
validate values against that allowlist and use an Enum-aware `IN` comparison without casting the
database column to `String`.

Top-level envelope: `{ items, total, page, page_size, has_more }`.

- `total` is the **deduped question count** (number of distinct question cards in the full
  filtered result set), not the raw miss-row count — it must match the pagination of cards.
- Dedup happens across the **full filtered set before page slicing**, not within a page. Rank the
  filtered misses per question by `timestamp DESC NULLS LAST, id DESC`; the `row_number = 1` row
  supplies all latest-attempt fields. Join it to per-question aggregates, then order cards by
  `last_missed_at DESC NULLS LAST, question_id ASC` before `LIMIT/OFFSET`. The ID and question-ID
  tie-breakers make latest-row selection and page boundaries deterministic. Slicing raw rows first
  would shift page boundaries and drop cards.

`is_correct` and `explanation` are always included in the payload (one request, no round trip
on reveal) — the frontend withholds rendering them until the student clicks "Show answer" per
card.

### `GET /study/review/filters`

Returns the distinct facet values actually present in the student's own missed-question set
(which `focus_key`s, `stem_type_key`s, `difficulty`s, `content_origin`s, `source_type`s,
`source_test_name`s, `source_section_code`s, and `source_module_code`s they have), so filter
dropdowns never show empty/irrelevant options. Fetched once per page load, cached client-side
(independent of currently-applied filters, so the dropdown options don't shrink as you filter).
Include `unknown` if historical rows exist for the student.
`focus_keys` is a flat distinct union of grammar, reading-focus, and reading-skill-family values;
the review endpoint's OR filter makes every returned value round-trip without source attribution.

## 5. Frontend

- **Route:** new `/review` page, `ReviewMissedPage.tsx`, added to `App.tsx` alongside the
  existing `/diagnostic`, `/test`, `/progress` routes.
- **Entry points:** a dashboard summary card on `DashboardPage`
  ("You have missed N questions — Review them"). `N` is the review endpoint's unfiltered,
  per-question-deduped `total` (`page=1&page_size=1` is sufficient); reuse an existing count only
  if a test proves identical semantics. If a reusable main navigation component exists at
  implementation time, add a `/review` link there too; do not invent a new global nav just for
  this feature.
- **Filter bar:**
  - Segmented control for source: `All` plus the source types returned by the filters endpoint,
    displayed in canonical order `Diagnostic / Practice Test / Drill / Practice / Unknown`.
    `All` is always present and is the default; absent source types are not shown.
  - Dropdown: source test
  - Separate dropdowns: source section and source module
  - Dropdown: domain
  - Dropdown: concept/focus key
  - Dropdown: question type (`stem_type_key`)
  - Toggle: difficulty
  - Toggle: content origin (official / generated / unofficial)
  - All options populated from `GET /study/review/filters`, never hardcoded
  - Any filter change resets pagination to page 1 before the next request
- **List:** reverse-chron, paginated (20/page), cards visually consistent with the existing
  `MissedCard` (badges for domain/focus/difficulty) but expanded:
  - Full question text, no truncation
  - Full passage — collapsed behind a "Show passage" toggle by default when present (reading
    passages can be long; keeps the list scannable), expands inline on click
  - All answer choices (A–D) listed, neutral/unstyled until revealed
  - Single **"Show answer"** toggle per card: reveals the correct-choice highlight among the
    options and the explanation block together
- **Hooks:** `useReviewQuestions(filters, page)` and `useReviewFilters()`, following the
  existing `useMissedQuestions` react-query pattern in `useDashboardData.ts` (or a new
  `useReviewData.ts` if that file is getting crowded)
- Loading/empty/error states mirror `MissedQuestionsTab`'s existing skeleton/empty-state
  patterns for visual consistency

## 6. Required acceptance coverage

The implementation is not complete unless these checks are represented in
`incorrect_questions_tasks.md` and pass before handoff:

- Backend migration/model coverage: `source_type` column exists, index exists, diagnostic rows
  backfill to `diagnostic`, non-diagnostic rows backfill to `unknown`.
- `POST /api/submit` coverage: omitted `source_type` stores `unknown`; explicit
  `practice_test`, `drill`, and `practice` are accepted; invalid values 422; `source_type=
  'diagnostic'` sent to the generic endpoint 422s.
- Diagnostic submit coverage: `/api/diagnostic/{session_id}/submit` stores `diagnostic`.
- `GET /api/study/review` coverage: auth, missing token, empty state, pagination,
  reverse-chron ordering, source/domain/focus/stem/difficulty/content/source-section filters,
  per-question dedup after filters, `source_types`, and latest-miss `user_answer` semantics.
  Must also cover: `options` come from the **current version only** (no duplicate/stale options
  from other versions); `focus_key` filter resolves against the producing column (a
  reading-skill-family facet value filters its rows); `total` equals deduped question count
  and pagination is stable across page boundaries (dedup precedes `LIMIT/OFFSET`); `domain`
  and `difficulty` read from `UserProgress.question_domain` / `question_difficulty`. Equal-
  timestamp misses must prove the `id DESC` latest-row tie-breaker, and all row-level metadata
  must come from that selected row rather than independent aggregate maxima.
  Invalid `source_type` / `content_origin` values return 422, and null source values behave as
  `unknown` for output, filtering, and facets.
- `GET /api/study/review/filters` coverage: facets come from the student's own misses,
  include `unknown` when present, and do not include values from other students.
- Frontend coverage: API client query strings, hooks query keys, review page loading/error/empty
  states, filter changes with page reset, pagination, passage reveal, and answer/explanation reveal.
- Manual QA: run the app, create or reuse a student with missed rows from at least two source
  types, verify All view and source filters behave as specified.

## 7. Cross-session agent handoff rules

Use `incorrect_questions_tasks.md` as the execution source of truth. Agents working across
sessions should:

- Claim one task ID at a time and complete it fully before starting the next dependency.
- Update the checkbox status in `incorrect_questions_tasks.md` as work lands.
- Leave a short "Handoff note" under the current task if stopping mid-task, including files
  touched, commands run, failing tests, and the next exact command to run.
- Keep commits task-scoped when the user asks for commits; otherwise leave the working tree
  with clear status and no unrelated rewrites.
- Do not modify `MissedQuestionsTab.tsx` or `GET /study/missed` except if a task explicitly says
  to add shared types/tests without changing behavior.

## 8. Non-goals / explicitly out of scope for this pass

- Not touching or rewriting `MissedQuestionsTab.tsx` / `GET /study/missed`
- No retroactive reclassification of pre-migration `user_progress` rows (`'unknown'` bucket is
  permanent for historical data)
- No sort-order selector beyond reverse-chron by date
- No spaced-repetition or re-practice action wired into this page (review-only, for now)
