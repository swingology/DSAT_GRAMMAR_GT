# Stimulus-Type Picker — Design

## Problem

`ConceptSelectorPage` (`APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx`) lets
students pick a practice session by weak concept (grammar/reading focus key), ranked by
weakness score. There is no way for a student to instead pick a practice session by
*stimulus type* — e.g. specifically practicing questions that include a chart/graph
(`prose_plus_graph`), a table (`prose_plus_table`), a poem, etc.

The active question bank's `stimulus_mode_key` column already has 9 canonical values:
`sentence_only`, `passage_excerpt`, `notes_bullets`, `prose_plus_table`,
`prose_plus_graph`, `prose_single`, `prose_paired`, `notes_summary`, `poem`. The backend
`GET /questions` endpoint already accepts `stimulus_mode_key` as a filter
(`backend/app/routers/student.py`); there is currently no UI that sets it.

## Design

### Backend: stimulus-type counts endpoint

New `GET /questions/stimulus-counts` in `backend/app/routers/student.py`. Runs a single
`GROUP BY stimulus_mode_key` count query over active/approved questions and returns one
entry per canonical `stimulus_mode_key`, including types with zero matching questions
(no filtering out empty types — seeing "0 available" is useful signal to the student).

Response shape: `[{ "stimulus_mode_key": string, "count": number }, ...]`, one row per
canonical value, 9 rows total.

### Frontend: ConceptSelectorPage tabs

- Add two tabs at the top of `ConceptSelectorPage`: **"By Weakness"** (existing list,
  unchanged behavior) and **"By Type"** (new).
- "By Type" tab fetches `/questions/stimulus-counts` via a new `useStimulusCounts()` hook
  (React Query, same pattern as the existing `useRecommendations()` hook), and renders one
  row per stimulus type: friendly label + count. Reuses the existing row visual style
  (rounded card, hover state, index number) but omits the weakness progress bar (not
  applicable to this list).
- Friendly label map (small const, colocated in the page):
  - `sentence_only` → "Sentence Only"
  - `passage_excerpt` → "Passage Excerpt"
  - `notes_bullets` → "Notes & Bullets"
  - `prose_plus_table` → "Prose + Table"
  - `prose_plus_graph` → "Prose + Graph"
  - `prose_single` → "Single Passage"
  - `prose_paired` → "Paired Passages"
  - `notes_summary` → "Notes Summary"
  - `poem` → "Poem"
- Rows sorted by count descending (most-available first), consistent with the existing
  weakness list being ranked.
- Tapping a row navigates to `/practice/mixed?stimulus_mode_key=<key>&limit=<limit>`.

### Practice flow: MixedPracticePage filter passthrough

`MixedPracticePage` reads `stimulus_mode_key` from `useSearchParams()` (same pattern
already used for `limit`) and, when present, forwards it into
`api.getQuestions({ limit: 1, mode: 'practice', randomize: true, stimulus_mode_key })`.
No UI change to `MixedPracticePage` itself — this is purely a filter passthrough. The
existing "n / limit" progress header, `StimulusAssets` rendering, and answer submission
flow are unchanged. A session with fewer results than `limit` (e.g. a rare stimulus type)
is an existing case already handled by the current empty/shortfall UI — no new handling
needed.

### Non-goals

- No change to `ConceptSelectorPage`'s "By Weakness" tab or the underlying weakness
  scoring.
- No new question-selection algorithm — the stratified/backfill logic from the
  concept-quick-pick feature is unrelated and out of scope here; this is a simple
  single-filter session.
- No changes to `DiagnosticTestRunner`, `PracticeTestRunner`, or `TestModeTab` — this
  feature is scoped to the Mixed Practice flow only.

## Testing

- Backend: unit test for `GET /questions/stimulus-counts` — confirms all 9 canonical
  types are present in the response (including zero-count types) and counts match a
  known fixture.
- Frontend: unit test for `useStimulusCounts` hook (fetch + shape).
- Frontend: component test confirming a "By Type" row navigates to `/practice/mixed`
  with the correct `stimulus_mode_key` query param.
- Frontend: test confirming `MixedPracticePage` forwards `stimulus_mode_key` into
  `api.getQuestions` when present in the URL, and omits it when absent.
