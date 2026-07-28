# Concept Quick Pick — Design

## Problem

`ConceptSelectorPage` (`APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx`) lists a
student's weak concepts (grammar + reading), ranked by weakness score. Tapping a concept
row navigates to `/practice/grammar?focus_key=...&domain=...&limit=...`, intended as a
focused drill on that concept.

There is currently no way to get a single batch of questions spanning a *range* of
difficulty for one concept — every fetch uses a single exact-match difficulty filter (or
none). This design adds a "Quick Pick" mode: tapping a new per-row action fetches 10
questions for that concept spread across low/medium/high difficulty in one batch.

## Pre-existing bug (fixed as part of this work)

`GrammarPractice.tsx` / `useGrammarSession.ts` never reads `focus_key`/`domain` from the
URL — `useGrammarSession` calls `api.getQuestions({ domain: 'grammar', limit })` only. So
today, tapping a concept row does **not** actually filter to that concept; the existing
"drill" flow silently ignores the selection. This is fixed here for the grammar drill path
(`useGrammarSession` now forwards `grammar_focus_key` from the URL param).

**Out of scope**: there is no reading-domain drill page today (`ConceptSelectorPage`
always routes taps to `/practice/grammar`, which mis-renders reading concepts). Building a
proper reading drill page is a separate, larger project and is not addressed here. Quick
Pick (below) works for both domains independently of the drill path, since it uses its own
new, domain-agnostic route.

## Design

### Fetching (client-side, no backend changes)

`GET /questions` already supports exact-match `difficulty` (`low`/`medium`/`high`),
`grammar_focus_key`, `reading_focus_key`, and `limit` (see `backend/app/routers/student.py`).
Quick Pick issues three parallel calls per concept:

- `difficulty=low, limit=3`
- `difficulty=medium, limit=4`
- `difficulty=high, limit=3`

passing `grammar_focus_key` or `reading_focus_key` depending on `domain`. Results are
concatenated in that block order (low → medium → high) and deduped by `id`.

**Shortfall handling**: if any bucket returns fewer than requested, issue one backfill
call (same focus key, no difficulty filter, limit = shortfall + a margin) and append
results (deduped) to reach 10 total where possible. If the concept has fewer than 10
questions in total, render what's available and show a small note, e.g. "Only 7 questions
available for this concept" — this is not an error state.

This logic lives in a new hook, e.g. `useQuickPickQuestions(domain, focusKey)`, colocated
with the new page.

### UI

- **`ConceptSelectorPage`**: each concept row gains a small secondary action (e.g. a ⚡
  icon button) alongside the existing tappable row body. Tapping the row body still
  launches the existing single-difficulty drill (now correctly filtered, per the bug fix
  above); tapping the icon launches Quick Pick.
- **New route**: `/practice/quick?domain=...&focus_key=...`, backed by a new
  `QuickPickPage` component.
- **Rendering**: reuse the existing domain-agnostic `QuestionCard` component currently
  defined inline in `MixedPracticePage.tsx` — it already handles passage text, options,
  stimulus assets, explanation, and displays whichever of `grammar_focus_key` /
  `reading_focus_key` is present. Lift it into a shared component file
  (e.g. `components/QuestionCard.tsx`) so both `MixedPracticePage` and the new
  `QuickPickPage` import it, rather than duplicating rendering logic.
- Progress header shows `n / 10` consistent with other practice pages.
- Answer submission uses `source_type: 'drill'` (consistent with concept-targeted
  practice, as opposed to `'practice'` used by unfiltered mixed practice).

### Non-goals

- No backend endpoint changes — the stratified sample is assembled client-side from
  existing filters.
- No reading-domain drill page (existing gap, separate scope).
- No change to how weakness targets are computed or ranked.

## Testing

- Unit test for the bucket-merge/backfill logic (`useQuickPickQuestions`): even split,
  shortfall backfill, total-shortfall note.
- Unit test confirming `useGrammarSession` now forwards `grammar_focus_key` from the URL.
- Component test for `ConceptSelectorPage` confirming the new quick-pick action navigates
  to `/practice/quick` with the right query params, independent of the row-body tap.
