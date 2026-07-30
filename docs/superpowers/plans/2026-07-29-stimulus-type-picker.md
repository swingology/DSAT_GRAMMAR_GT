# Stimulus-Type Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let students pick a Mixed Practice session filtered to a specific stimulus type (e.g. `prose_plus_graph` for chart questions) from a new "By Type" tab on the concept selector page.

**Architecture:** A new backend endpoint returns per-type question counts from the existing `stimulus_mode_key` column. The concept selector page gains a second tab that lists those counts and navigates into the existing Mixed Practice page with a `stimulus_mode_key` query param, which the practice page forwards into its existing question-fetch call. Task 0 fixes an unrelated pre-existing bug in that fetch call, discovered while building this feature, that must be fixed first or the whole feature is unusable.

**Tech Stack:** FastAPI + SQLAlchemy (async) + Pydantic on the backend (`backend/`), React + TypeScript + React Query + React Router + Vitest/Testing Library on the frontend (`APP/STUDENT_APP_REDUX/`).

## Global Constraints

- Backend tests run with `.venv-jb/bin/python -m pytest` from `backend/` — do not use `uv run pytest` (segfaults on pymupdf in this environment).
- Frontend tests run with `npx vitest run <path>` from `APP/STUDENT_APP_REDUX/` (or `npm test -- run <path>`).
- Follow existing patterns exactly: response-list typing uses lowercase `list[...]` (PEP 585) in this backend, not `List[...]`.
- The student router (`backend/app/routers/student.py`) is mounted with `prefix="/api"` baked into its own `APIRouter(...)` declaration — new routes on `router` are automatically served under `/api/...`. Do not add another `/api` prefix.
- No changes to `DiagnosticTestRunner`, `PracticeTestRunner`, `TestModeTab`, or the weakness-scoring/recommendations logic — out of scope per the design spec (`docs/superpowers/specs/2026-07-29-stimulus-type-picker-design.md`).

---

### Task 0: Fix MixedPracticePage field-mismatch bug (bug-813)

**Files:**
- Modify: `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx:136`
- Test: `APP/STUDENT_APP_REDUX/src/pages/__tests__/MixedPracticePage.test.tsx` (new file — also used by Task 4)

**Interfaces:**
- Consumes: `api.getQuestions(params: Record<string, any>) => Promise<{ items: Question[]; inventory: {...} }>` (existing, `APP/STUDENT_APP_REDUX/src/api/client.ts:157`).
- Produces: nothing new — this task only fixes the existing `question` extraction so later tasks (and the page itself) work at all.

**Context:** `GET /api/questions` (`backend/app/routers/student.py::student_recall`) returns `StudentQuestionsListResponse` (`backend/app/models/payload.py:62`), which has fields `items` and `inventory` — there is no `questions` key. `MixedPracticePage.tsx` line 136 currently reads `data?.questions?.[0]`, which is always `undefined`, so `question` is always `null` and the page always renders the "No questions available right now." empty state. This is bug-813 in `.wolf/buglog.json`, logged 2026-07-29.

- [ ] **Step 1: Write the failing test**

Create `APP/STUDENT_APP_REDUX/src/pages/__tests__/MixedPracticePage.test.tsx`:

```tsx
import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MixedPracticePage } from '../MixedPracticePage'
import { api } from '../../api/client'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
  },
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useSubmitAnswer: () => ({ mutate: vi.fn() }),
}))

const mockedApi = vi.mocked(api)

function renderPage(initialEntry = '/practice/mixed') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <MixedPracticePage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('MixedPracticePage', () => {
  it('renders a question from the items array (not a questions array)', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-1',
          current_question_text: 'Which choice best completes the sentence?',
          current_passage_text: null,
          options: [
            { label: 'A', text: 'Option A' },
            { label: 'B', text: 'Option B' },
          ],
          domain: 'grammar',
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Which choice best completes the sentence?')).toBeInTheDocument()
    )
    expect(screen.queryByText('No questions available right now.')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run from `APP/STUDENT_APP_REDUX/`: `npx vitest run src/pages/__tests__/MixedPracticePage.test.tsx`
Expected: FAIL — `screen.getByText('Which choice best completes the sentence?')` not found (page shows the empty state instead).

- [ ] **Step 3: Fix the field name**

In `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx`, change line 136:

```tsx
  const question: Question | null = data?.items?.[0] ?? null
```

(was `data?.questions?.[0] ?? null`)

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/pages/__tests__/MixedPracticePage.test.tsx`
Expected: PASS

- [ ] **Step 5: Update bug-813 in the buglog and commit**

Edit `.wolf/buglog.json` bug-813's `"fix"` field to:
```
"FIXED: Changed data?.questions?.[0] to data?.items?.[0] in MixedPracticePage.tsx:136, matching the actual StudentQuestionsListResponse shape ({items, inventory}). Added a regression test (MixedPracticePage.test.tsx) asserting a question renders from a mocked {items: [...]} response."
```

Also update `DEBUG_LOG.md`'s "2026-07-29 - MixedPracticePage never renders a question" entry: wrap finding 1's text in `~~strikethrough~~` and add a `**Fixed:**` line matching the buglog fix text.

```bash
git add APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx APP/STUDENT_APP_REDUX/src/pages/__tests__/MixedPracticePage.test.tsx .wolf/buglog.json DEBUG_LOG.md
git commit -m "$(cat <<'EOF'
Fix MixedPracticePage reading data.questions instead of data.items

GET /api/questions returns {items, inventory}; the questions key
never existed, so Mixed Practice always showed the empty state.

Fixes bug-813.
EOF
)"
```

---

### Task 1: Backend stimulus-type counts endpoint

**Files:**
- Modify: `backend/app/models/payload.py` (add `StimulusModeCountResponse`, near `ActivityDayCount` at line 138)
- Modify: `backend/app/routers/student.py` (add import + new route after `student_recall`, which ends at line 589)
- Test: `backend/tests/test_stimulus_mode_counts.py` (new file)

**Interfaces:**
- Consumes: `STIMULUS_MODE_KEYS: tuple[str, ...]` (existing, `backend/app/models/ontology.py:52` — the 9 canonical values: `sentence_only`, `passage_excerpt`, `prose_single`, `prose_paired`, `prose_plus_table`, `prose_plus_graph`, `notes_bullets`, `notes_summary`, `poem`).
- Produces: `GET /api/questions/stimulus-counts` → `list[StimulusModeCountResponse]`, one entry per canonical key (9 total, in `STIMULUS_MODE_KEYS` order), each `{ "stimulus_mode_key": str, "count": int }`. Consumed by Task 2's `api.getStimulusCounts()`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_stimulus_mode_counts.py`:

```python
"""Tests for GET /api/questions/stimulus-counts."""

import pytest

from app.routers import student as student_router
from app.models.ontology import STIMULUS_MODE_KEYS


# ---------------------------------------------------------------------------
# HTTP-layer tests (use the TestClient via the `client` fixture from conftest)
# ---------------------------------------------------------------------------

def test_stimulus_counts_requires_auth(client):
    resp = client.get("/api/questions/stimulus-counts")
    assert resp.status_code == 403


def test_stimulus_counts_student_auth_accepted(client):
    resp = client.get("/api/questions/stimulus-counts", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200


def test_stimulus_counts_admin_auth_accepted(client):
    resp = client.get("/api/questions/stimulus-counts", headers={"X-API-Key": "admin-test-key"})
    assert resp.status_code == 200


def test_stimulus_counts_response_shape(client):
    resp = client.get("/api/questions/stimulus-counts", headers={"X-API-Key": "student-test-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == len(STIMULUS_MODE_KEYS)
    returned_keys = {row["stimulus_mode_key"] for row in data}
    assert returned_keys == set(STIMULUS_MODE_KEYS)
    for row in data:
        assert "count" in row
        assert isinstance(row["count"], int)


# ---------------------------------------------------------------------------
# Direct-call test with a fake DB returning known grouped counts
# ---------------------------------------------------------------------------

class _GroupByResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt):
        return _GroupByResult(self._rows)


@pytest.mark.asyncio
async def test_stimulus_counts_fills_zero_for_missing_keys():
    """Keys with no matching rows in the DB result must still appear, with count 0."""
    db = _FakeDB(rows=[("prose_plus_graph", 43), ("poem", 9)])
    result = await student_router.get_stimulus_mode_counts(db=db, auth=("student", "test"))

    by_key = {row.stimulus_mode_key: row.count for row in result}
    assert by_key["prose_plus_graph"] == 43
    assert by_key["poem"] == 9
    assert by_key["sentence_only"] == 0
    assert set(by_key.keys()) == set(STIMULUS_MODE_KEYS)


@pytest.mark.asyncio
async def test_stimulus_counts_preserves_ontology_order():
    db = _FakeDB(rows=[])
    result = await student_router.get_stimulus_mode_counts(db=db, auth=("student", "test"))
    assert [row.stimulus_mode_key for row in result] == list(STIMULUS_MODE_KEYS)
```

- [ ] **Step 2: Run tests to verify they fail**

Run from `backend/`: `.venv-jb/bin/python -m pytest tests/test_stimulus_mode_counts.py -v`
Expected: FAIL — `AttributeError: module 'app.routers.student' has no attribute 'get_stimulus_mode_counts'` (and 404s for the HTTP tests).

- [ ] **Step 3: Add the response model**

In `backend/app/models/payload.py`, add after `ActivityDayCount` (after line 140, before `class AdminEditRequest`):

```python
class StimulusModeCountResponse(BaseModel):
    """Count of active questions for one canonical stimulus_mode_key."""
    stimulus_mode_key: str
    count: int
```

- [ ] **Step 4: Add the route**

In `backend/app/routers/student.py`:

1. Add to the `from app.models.ontology import ...` line (line 85), append `STIMULUS_MODE_KEYS`:

```python
from app.models.ontology import CONTENT_ORIGINS, GRAMMAR_FOCUS_BY_ROLE, READING_FOCUS_BY_SKILL_FAMILY, STIMULUS_MODE_KEYS
```

2. Add `StimulusModeCountResponse` to the `from app.models.payload import (...)` block (anywhere in that import list, e.g. right after `ActivityDayCount,`).

3. Insert this route immediately after the `student_recall` function's closing `return StudentQuestionsListResponse(items=items, inventory=inventory)` (line 589), before `@router.post("/submit")`:

```python
@router.get("/questions/stimulus-counts", response_model=list[StimulusModeCountResponse])
async def get_stimulus_mode_counts(
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, str] = Depends(admin_or_student_required),
):
    """Count active questions per canonical stimulus_mode_key, for the practice-by-type picker."""
    dry_run_exists = (
        select(QuestionJob.id)
        .join(GenerationBatch, GenerationBatch.id == QuestionJob.generation_batch_id)
        .where(
            QuestionJob.question_id == Question.id,
            GenerationBatch.release_policy == _DRY_RUN_RELEASE_POLICY,
        )
        .exists()
    )
    result = await db.execute(
        select(Question.stimulus_mode_key, func.count())
        .where(Question.practice_status == "active")
        .where(~dry_run_exists)
        .group_by(Question.stimulus_mode_key)
    )
    counts_by_key = dict(result.all())
    return [
        StimulusModeCountResponse(
            stimulus_mode_key=key,
            count=counts_by_key.get(key, 0) or 0,
        )
        for key in STIMULUS_MODE_KEYS
    ]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv-jb/bin/python -m pytest tests/test_stimulus_mode_counts.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 6: Run the full backend suite to check for regressions**

Run: `.venv-jb/bin/python -m pytest -q`
Expected: same pass/fail counts as before this change, plus the 6 new passing tests (no new failures).

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/payload.py backend/app/routers/student.py backend/tests/test_stimulus_mode_counts.py
git commit -m "$(cat <<'EOF'
Add GET /api/questions/stimulus-counts endpoint

Returns active-question counts grouped by stimulus_mode_key, one
row per canonical type (zero-filled if none exist), for the new
practice-by-type picker on the student app.
EOF
)"
```

---

### Task 2: Frontend API client, types, and hook for stimulus counts

**Files:**
- Modify: `APP/STUDENT_APP_REDUX/src/types/index.ts` (add `StimulusModeCount` interface, near `StimulusAsset` at line 24)
- Modify: `APP/STUDENT_APP_REDUX/src/api/client.ts` (add `getStimulusCounts`, near `getStats` at line 174)
- Modify: `APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts` (add `useStimulusCounts` hook, near `useRecommendations` at line 44)
- Modify: `APP/STUDENT_APP_REDUX/src/hooks/__tests__/useDashboardData.test.ts` (add test suite)

**Interfaces:**
- Consumes: `GET /api/questions/stimulus-counts` (Task 1) → `[{ stimulus_mode_key, count }, ...]`.
- Produces: `api.getStimulusCounts(): Promise<StimulusModeCount[]>` and `useStimulusCounts(): UseQueryResult<StimulusModeCount[]>`. Consumed by Task 3's "By Type" tab.

- [ ] **Step 1: Write the failing test**

Append to `APP/STUDENT_APP_REDUX/src/hooks/__tests__/useDashboardData.test.ts`:

1. Add `getStimulusCounts: vi.fn(),` to the `vi.mock('../../api/client', ...)` block's `api` object (alongside the existing `getQuestions: vi.fn()`).
2. Add `useStimulusCounts` to the import on line 5: `import { useRecommendations, useMissedQuestions, useSubmitAnswer, useStimulusCounts } from '../useDashboardData'`.
3. Add this new `describe` block at the end of the file:

```ts
describe('useStimulusCounts', () => {
  it('returns counts on success', async () => {
    const mockData = [
      { stimulus_mode_key: 'sentence_only', count: 559 },
      { stimulus_mode_key: 'prose_plus_graph', count: 43 },
    ]
    mockedApi.getStimulusCounts.mockResolvedValue(mockData)

    const { result } = renderHook(() => useStimulusCounts(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.[1].stimulus_mode_key).toBe('prose_plus_graph')
  })

  it('enters error state when API fails', async () => {
    mockedApi.getStimulusCounts.mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useStimulusCounts(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run from `APP/STUDENT_APP_REDUX/`: `npx vitest run src/hooks/__tests__/useDashboardData.test.ts`
Expected: FAIL — `useStimulusCounts` is not exported from `../useDashboardData`.

- [ ] **Step 3: Add the type**

In `APP/STUDENT_APP_REDUX/src/types/index.ts`, add after the `StudyRecommendationsResponse` interface (after line 22, before `StimulusAsset`):

```ts
export interface StimulusModeCount {
  stimulus_mode_key: string
  count: number
}
```

- [ ] **Step 4: Add the API client method**

In `APP/STUDENT_APP_REDUX/src/api/client.ts`, add after `getStats` (after line 175):

```ts
  getStimulusCounts: (): Promise<import('../types').StimulusModeCount[]> =>
    apiCall('/questions/stimulus-counts'),
```

- [ ] **Step 5: Add the hook**

In `APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts`:

1. Add `StimulusModeCount` to the type-only import on line 3: `import type { StudyRecommendationsResponse, StimulusModeCount } from '../types'`.
2. Add after `useRecommendations` (after line 50):

```ts
export function useStimulusCounts() {
  return useQuery<StimulusModeCount[]>({
    queryKey: ['stimulus-counts'],
    queryFn: () => api.getStimulusCounts(),
    staleTime: 5 * 60 * 1000,
  })
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npx vitest run src/hooks/__tests__/useDashboardData.test.ts`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/types/index.ts APP/STUDENT_APP_REDUX/src/api/client.ts APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts APP/STUDENT_APP_REDUX/src/hooks/__tests__/useDashboardData.test.ts
git commit -m "$(cat <<'EOF'
Add useStimulusCounts hook and API client method

Fetches per-stimulus-type active question counts from the new
GET /api/questions/stimulus-counts endpoint.
EOF
)"
```

---

### Task 3: ConceptSelectorPage "By Type" tab

**Files:**
- Modify: `APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx`
- Test: `APP/STUDENT_APP_REDUX/src/pages/__tests__/ConceptSelectorPage.test.tsx` (new file)

**Interfaces:**
- Consumes: `useStimulusCounts()` (Task 2) → `{ data: StimulusModeCount[] | undefined, isLoading, isError }`; `useRecommendations()` (existing, unchanged) for the "By Weakness" tab.
- Produces: nothing consumed by later tasks — this is the picker UI itself. Navigates to `/practice/mixed?stimulus_mode_key=<key>&limit=<limit>`, consumed by Task 4.

- [ ] **Step 1: Write the failing tests**

Create `APP/STUDENT_APP_REDUX/src/pages/__tests__/ConceptSelectorPage.test.tsx`:

```tsx
import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ConceptSelectorPage } from '../ConceptSelectorPage'

const mockNavigate = vi.fn()

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../hooks/useDashboardData', () => ({
  useRecommendations: vi.fn().mockReturnValue({
    isLoading: false,
    isError: false,
    data: {
      user_id: 1,
      top_targets: [
        {
          domain: 'grammar', focus_key: 'comma_splice', skill_family_key: null,
          grammar_role_key: 'sentence_structure', difficulty: 'medium',
          weakness_score: 0.8, miss_count: 4, attempt_count: 5, miss_rate: 0.8,
          days_since_last_attempt: 2, inventory_unseen: 10, inventory_below_threshold: false,
        },
      ],
      threshold: 5,
    },
  }),
  useStimulusCounts: vi.fn().mockReturnValue({
    isLoading: false,
    isError: false,
    data: [
      { stimulus_mode_key: 'sentence_only', count: 559 },
      { stimulus_mode_key: 'prose_plus_graph', count: 43 },
      { stimulus_mode_key: 'poem', count: 9 },
    ],
  }),
}))

function wrap(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

beforeEach(() => { vi.clearAllMocks() })

describe('ConceptSelectorPage', () => {
  it('shows the By Weakness tab by default', () => {
    wrap(<ConceptSelectorPage />)
    expect(screen.getByText('comma splice')).toBeInTheDocument()
    expect(screen.queryByText('Prose + Graph')).not.toBeInTheDocument()
  })

  it('switches to the By Type tab and lists stimulus types by count descending', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByText('By Type'))

    expect(screen.getByText('Sentence Only')).toBeInTheDocument()
    expect(screen.getByText('Prose + Graph')).toBeInTheDocument()
    expect(screen.getByText('Poem')).toBeInTheDocument()
    expect(screen.queryByText('comma splice')).not.toBeInTheDocument()

    const labels = screen.getAllByText(/Sentence Only|Prose \+ Graph|Poem/).map((el) => el.textContent)
    expect(labels).toEqual(['Sentence Only', 'Prose + Graph', 'Poem'])
  })

  it('shows the count for each stimulus type', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByText('By Type'))
    expect(screen.getByText('43 questions')).toBeInTheDocument()
  })

  it('navigates to mixed practice with the stimulus_mode_key on tap', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByText('By Type'))
    fireEvent.click(screen.getByText('Prose + Graph'))
    expect(mockNavigate).toHaveBeenCalledWith('/practice/mixed?stimulus_mode_key=prose_plus_graph&limit=10')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run from `APP/STUDENT_APP_REDUX/`: `npx vitest run src/pages/__tests__/ConceptSelectorPage.test.tsx`
Expected: FAIL — `useStimulusCounts` not mocked/used yet, "By Type" text not found.

- [ ] **Step 3: Implement the tabs**

Replace the full contents of `APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useRecommendations, useStimulusCounts } from '../hooks/useDashboardData'

const STIMULUS_TYPE_LABELS: Record<string, string> = {
  sentence_only: 'Sentence Only',
  passage_excerpt: 'Passage Excerpt',
  notes_bullets: 'Notes & Bullets',
  prose_plus_table: 'Prose + Table',
  prose_plus_graph: 'Prose + Graph',
  prose_single: 'Single Passage',
  prose_paired: 'Paired Passages',
  notes_summary: 'Notes Summary',
  poem: 'Poem',
}

type Tab = 'weakness' | 'type'

export function ConceptSelectorPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const limit = searchParams.get('limit') ?? '10'
  const [tab, setTab] = useState<Tab>('weakness')

  const { data: recData, isLoading: recLoading, isError: recError } = useRecommendations()
  const targets = recData?.top_targets ?? []

  const { data: countsData, isLoading: countsLoading, isError: countsError } = useStimulusCounts()
  const sortedCounts = [...(countsData ?? [])].sort((a, b) => b.count - a.count)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← Back
        </button>
        <span className="text-gray-800 font-semibold">Pick a Concept</span>
      </header>

      <div className="max-w-lg mx-auto px-4 py-6">
        <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setTab('weakness')}
            className={`flex-1 text-sm font-medium py-1.5 rounded-md transition ${
              tab === 'weakness' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
            }`}
          >
            By Weakness
          </button>
          <button
            onClick={() => setTab('type')}
            className={`flex-1 text-sm font-medium py-1.5 rounded-md transition ${
              tab === 'type' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
            }`}
          >
            By Type
          </button>
        </div>

        {tab === 'weakness' && (
          <>
            <p className="text-sm text-gray-500 mb-4">
              Choose a concept to drill. Ranked by weakness score — hardest areas first.
            </p>

            {recLoading && (
              <div className="space-y-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            )}

            {recError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-center">
                <p className="text-red-700 font-medium">Failed to load concepts</p>
              </div>
            )}

            {!recLoading && targets.length === 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
                <p className="text-gray-500">No concepts found.</p>
                <p className="text-gray-400 text-sm mt-1">
                  Complete a diagnostic first to build your concept profile.
                </p>
                <button
                  onClick={() => navigate('/diagnostic')}
                  className="mt-4 px-5 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 transition"
                >
                  Run Diagnostic
                </button>
              </div>
            )}

            <div className="space-y-2">
              {targets.map((t, i) => {
                const pct = Math.round(t.weakness_score * 100)
                const barColor =
                  pct >= 70 ? 'bg-red-400' : pct >= 40 ? 'bg-amber-400' : 'bg-emerald-400'

                return (
                  <motion.button
                    key={`${t.domain}-${t.focus_key}`}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04, duration: 0.2, ease: 'easeOut' }}
                    onClick={() =>
                      navigate(
                        `/practice/grammar?focus_key=${encodeURIComponent(t.focus_key)}&domain=${encodeURIComponent(t.domain)}&limit=${limit}`
                      )
                    }
                    className="w-full text-left bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-blue-300 hover:shadow-sm transition-all group"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 w-5 flex-shrink-0 font-mono">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700">
                          {t.focus_key.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">{t.domain}</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${barColor} rounded-full`}
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono text-gray-400 w-8 text-right">{pct}%</span>
                      </div>
                    </div>
                  </motion.button>
                )
              })}
            </div>
          </>
        )}

        {tab === 'type' && (
          <>
            <p className="text-sm text-gray-500 mb-4">
              Choose a question type to practice — most available first.
            </p>

            {countsLoading && (
              <div className="space-y-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            )}

            {countsError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-center">
                <p className="text-red-700 font-medium">Failed to load question types</p>
              </div>
            )}

            <div className="space-y-2">
              {sortedCounts.map((c, i) => (
                <motion.button
                  key={c.stimulus_mode_key}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.2, ease: 'easeOut' }}
                  onClick={() =>
                    navigate(
                      `/practice/mixed?stimulus_mode_key=${encodeURIComponent(c.stimulus_mode_key)}&limit=${limit}`
                    )
                  }
                  className="w-full text-left bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-blue-300 hover:shadow-sm transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-5 flex-shrink-0 font-mono">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700">
                        {STIMULUS_TYPE_LABELS[c.stimulus_mode_key] ?? c.stimulus_mode_key}
                      </p>
                    </div>
                    <span className="text-xs text-gray-400 flex-shrink-0">{c.count} questions</span>
                  </div>
                </motion.button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx vitest run src/pages/__tests__/ConceptSelectorPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx APP/STUDENT_APP_REDUX/src/pages/__tests__/ConceptSelectorPage.test.tsx
git commit -m "$(cat <<'EOF'
Add By Type tab to ConceptSelectorPage

Lists the 9 canonical stimulus types with live question counts,
sorted by availability. Tapping a row launches Mixed Practice
filtered to that type (e.g. Prose + Graph for chart questions).
EOF
)"
```

---

### Task 4: MixedPracticePage stimulus_mode_key filter passthrough

**Files:**
- Modify: `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx`
- Modify: `APP/STUDENT_APP_REDUX/src/pages/__tests__/MixedPracticePage.test.tsx` (created in Task 0 — add to it)

**Interfaces:**
- Consumes: `stimulus_mode_key` URL query param (set by Task 3's navigation); `api.getQuestions(params)` (existing).
- Produces: nothing new for later tasks — this is the last task in the plan.

- [ ] **Step 1: Write the failing test**

Add to `APP/STUDENT_APP_REDUX/src/pages/__tests__/MixedPracticePage.test.tsx` (created in Task 0), inside the existing `describe('MixedPracticePage', ...)` block:

```tsx
  it('forwards stimulus_mode_key from the URL to getQuestions', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-2',
          current_question_text: 'What does the graph show?',
          current_passage_text: null,
          options: [{ label: 'A', text: 'Option A' }],
          domain: 'reading',
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage('/practice/mixed?stimulus_mode_key=prose_plus_graph')

    await waitFor(() => expect(mockedApi.getQuestions).toHaveBeenCalled())
    expect(mockedApi.getQuestions).toHaveBeenCalledWith(
      expect.objectContaining({ stimulus_mode_key: 'prose_plus_graph' })
    )
  })

  it('omits stimulus_mode_key from getQuestions when absent from the URL', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-3',
          current_question_text: 'Any question.',
          current_passage_text: null,
          options: [{ label: 'A', text: 'Option A' }],
          domain: 'grammar',
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage('/practice/mixed')

    await waitFor(() => expect(mockedApi.getQuestions).toHaveBeenCalled())
    const callArgs = mockedApi.getQuestions.mock.calls[0][0]
    expect(callArgs).not.toHaveProperty('stimulus_mode_key')
  })
```

- [ ] **Step 2: Run tests to verify they fail**

Run from `APP/STUDENT_APP_REDUX/`: `npx vitest run src/pages/__tests__/MixedPracticePage.test.tsx`
Expected: FAIL — `getQuestions` called without `stimulus_mode_key` in the first test.

- [ ] **Step 3: Add the filter passthrough**

In `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx`, in the `MixedPracticePage` function, modify the `limit` line and the `useQuery` block (originally lines 121–133):

```tsx
  const limit = Math.min(50, Math.max(1, parseInt(searchParams.get('limit') ?? '10', 10) || 10))
  const stimulusModeKey = searchParams.get('stimulus_mode_key') ?? undefined
  const [qIndex, setQIndex] = useState(0)
  const [answered, setAnswered] = useState(0)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['mixed-practice', qIndex, stimulusModeKey],
    queryFn: () =>
      api.getQuestions({
        limit: 1,
        mode: 'practice',
        randomize: true,
        ...(stimulusModeKey ? { stimulus_mode_key: stimulusModeKey } : {}),
      }),
  })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx vitest run src/pages/__tests__/MixedPracticePage.test.tsx`
Expected: PASS (all 3 tests: the Task 0 regression test plus these 2)

- [ ] **Step 5: Run the full frontend suite to check for regressions**

Run from `APP/STUDENT_APP_REDUX/`: `npx vitest run`
Expected: same pass/fail counts as before this change, plus the new passing tests (no new failures).

- [ ] **Step 6: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx APP/STUDENT_APP_REDUX/src/pages/__tests__/MixedPracticePage.test.tsx
git commit -m "$(cat <<'EOF'
Forward stimulus_mode_key filter into Mixed Practice question fetch

Completes the stimulus-type picker: ConceptSelectorPage's By Type
tab navigates here with ?stimulus_mode_key=..., which is now read
from the URL and passed to GET /api/questions.
EOF
)"
```

---

### Manual verification (after all tasks complete)

The dev stack should already be running (`bash .claude/skills/dev-stack/run.sh status` from the repo root to check; `start` if not). In a browser:

1. Go to the student app, navigate to Practice → Pick a Concept.
2. Click the "By Type" tab — confirm all 9 types appear with counts, sorted descending.
3. Click "Prose + Graph" — confirm it navigates to Mixed Practice and a question with a chart renders (not the empty state).
4. Confirm the chart image is fully visible and properly scaled within its container (this was the original ask that led to this feature).
