# Concept Quick Pick Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a student tap a "Quick Pick" action on any concept in `ConceptSelectorPage` and get a batch of 10 questions for that concept spanning low/medium/high difficulty, and fix the pre-existing bug where the grammar drill silently ignores the selected concept.

**Architecture:** Two independent additions on top of the existing student app. (1) A small bug fix threads `focus_key` from the URL into `useGrammarSession`'s existing fetch call. (2) A new `useQuickPickQuestions` hook issues three parallel `GET /questions` calls (low/medium/high, 3/4/3) filtered by concept, merges them with backfill for shortfalls, and a new `QuickPickPage` renders the result using a `QuestionCard` component lifted out of `MixedPracticePage.tsx` into its own file so both pages share it. No backend changes.

**Tech Stack:** React + TypeScript, react-router-dom v6, @tanstack/react-query, vitest + @testing-library/react.

## Global Constraints

- No backend/API changes — all filtering uses existing `GET /questions` query params (`domain`, `difficulty`, `grammar_focus_key`, `reading_focus_key`, `limit`).
- Difficulty values are exactly `"low"`, `"medium"`, `"high"` (see `backend/app/models/ontology.py` `DIFFICULTY_KEYS`).
- Quick Pick question order is grouped low → medium → high (not shuffled).
- Split is 3 low / 4 medium / 3 high = 10 total, with backfill from an unfiltered-difficulty call when a bucket comes up short, and a visible note (not an error) if fewer than 10 total exist for the concept.
- Reading-domain drill page is explicitly out of scope — do not build one.
- Answer submissions from Quick Pick use `source_type: 'drill'`.
- Follow existing test conventions: vitest + `@testing-library/react`, mock `react-router-dom`'s `useNavigate` while keeping `vi.importActual` for the rest, mock `framer-motion` when a component under test uses `motion.*`, mock hook modules directly with `vi.mock(...)` rather than mocking `api` inside page-level tests.

---

### Task 1: Fix `useGrammarSession` to forward `grammar_focus_key`

**Files:**
- Modify: `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts:13,30-37`
- Modify: `APP/STUDENT_APP_REDUX/src/components/GrammarPractice.tsx:12-16`
- Test: `APP/STUDENT_APP_REDUX/src/hooks/__tests__/useGrammarSession.test.ts`

**Interfaces:**
- Consumes: existing `api.getQuestions(params: Record<string, any>)` from `APP/STUDENT_APP_REDUX/src/api/client.ts`.
- Produces: `useGrammarSession({ limit, focusKey }: { limit?: number; focusKey?: string })` — the new `focusKey` param is optional so all other current call sites (none currently pass it) keep working unchanged.

- [ ] **Step 1: Write the failing test**

Add this test to `APP/STUDENT_APP_REDUX/src/hooks/__tests__/useGrammarSession.test.ts` (in the existing `describe('useGrammarSession')` block, reusing the file's existing `mockQuestion` fixture and `api` mock):

```ts
  it('forwards focusKey as grammar_focus_key to the questions API', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({
      items: [mockQuestion],
      matching_target_total: 1,
    })

    renderHook(() => useGrammarSession({ limit: 10, focusKey: 'verb_tense_consistency' }))

    await waitFor(() => {
      expect(api.getQuestions).toHaveBeenCalledWith({
        domain: 'grammar',
        limit: 10,
        grammar_focus_key: 'verb_tense_consistency',
      })
    })
  })

  it('omits grammar_focus_key when no focusKey is given', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({
      items: [mockQuestion],
      matching_target_total: 1,
    })

    renderHook(() => useGrammarSession({ limit: 10 }))

    await waitFor(() => {
      expect(api.getQuestions).toHaveBeenCalledWith({
        domain: 'grammar',
        limit: 10,
      })
    })
  })
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/hooks/__tests__/useGrammarSession.test.ts`
Expected: FAIL — first test fails because `api.getQuestions` is called without `grammar_focus_key`; second test currently passes already (that's fine, it should stay passing after the change too).

- [ ] **Step 3: Implement the fix**

In `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`, change the function signature and the fetch call:

```ts
export function useGrammarSession({ limit = 10, focusKey }: { limit?: number; focusKey?: string } = {}) {
```

and inside `fetchQuestions`, replace:

```ts
        const resp = await api.getQuestions({
          domain: 'grammar',
          limit,
        })
```

with:

```ts
        const resp = await api.getQuestions({
          domain: 'grammar',
          limit,
          ...(focusKey ? { grammar_focus_key: focusKey } : {}),
        })
```

Also add `focusKey` to the effect's dependency array (currently `[]`) so a change in `focusKey` triggers a refetch:

```ts
  useEffect(() => {
    const fetchQuestions = async () => {
      // ...unchanged body...
    }

    fetchQuestions()
  }, [focusKey])
```

In `APP/STUDENT_APP_REDUX/src/components/GrammarPractice.tsx`, change:

```tsx
  const limit = Math.min(50, Math.max(1, parseInt(params.get('limit') ?? '10', 10) || 10))
  const grammar = useGrammarSession({ limit })
```

to:

```tsx
  const limit = Math.min(50, Math.max(1, parseInt(params.get('limit') ?? '10', 10) || 10))
  const focusKey = params.get('focus_key') ?? undefined
  const grammar = useGrammarSession({ limit, focusKey })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/hooks/__tests__/useGrammarSession.test.ts`
Expected: PASS (all tests in the file, including the two new ones)

- [ ] **Step 5: Run the full existing GrammarPractice test suite to check for regressions**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/components/__tests__/GrammarPractice.test.tsx src/components/__tests__/GrammarPractice.backendTokens.test.tsx src/__tests__/integration/grammar-page.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts APP/STUDENT_APP_REDUX/src/components/GrammarPractice.tsx APP/STUDENT_APP_REDUX/src/hooks/__tests__/useGrammarSession.test.ts
git commit -m "Forward grammar_focus_key from URL to grammar drill question fetch"
```

---

### Task 2: Extract `QuestionCard` into its own shared component

**Files:**
- Create: `APP/STUDENT_APP_REDUX/src/components/QuestionCard.tsx`
- Modify: `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx:1-117`
- Test: `APP/STUDENT_APP_REDUX/src/components/__tests__/QuestionCard.test.tsx`

**Interfaces:**
- Consumes: `StimulusAssets` component from `APP/STUDENT_APP_REDUX/src/components/StimulusAssets.tsx`; `StimulusAsset` type and `useSubmitAnswer` hook from `APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts`.
- Produces: `export interface Question { id: string; current_question_text: string; current_passage_text?: string | null; options: Array<{ label: string; text: string }>; explanation_short?: string; grammar_focus_key?: string; reading_focus_key?: string; domain?: string; stimulus_assets?: StimulusAsset[] }` and `export function QuestionCard({ question, onNext, sourceType }: { question: Question; onNext: () => void; sourceType: SubmitSourceType })` — both from `components/QuestionCard.tsx`. Task 4 imports this component and type directly.

Note the added `sourceType` prop: today `MixedPracticePage`'s inline `QuestionCard` hardcodes `source_type: 'practice'` in its submit call. Quick Pick needs `'drill'` instead, so this becomes a required prop rather than a hardcoded string, with `MixedPracticePage` passing `'practice'` explicitly to keep its current behavior unchanged.

- [ ] **Step 1: Write the failing test**

Create `APP/STUDENT_APP_REDUX/src/components/__tests__/QuestionCard.test.tsx`:

```tsx
import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QuestionCard, type Question } from '../QuestionCard'
import { useSubmitAnswer } from '../../hooks/useDashboardData'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useSubmitAnswer: vi.fn(),
}))

const question: Question = {
  id: 'q-1',
  current_question_text: 'Which choice completes the text?',
  current_passage_text: 'A passage.',
  options: [
    { label: 'A', text: 'First option' },
    { label: 'B', text: 'Second option' },
  ],
  explanation_short: 'B is correct because...',
  grammar_focus_key: 'verb_tense_consistency',
  domain: 'grammar',
}

describe('QuestionCard', () => {
  const mutate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useSubmitAnswer).mockReturnValue({ mutate } as unknown as ReturnType<typeof useSubmitAnswer>)
  })

  it('renders domain, focus key, passage, and options', () => {
    render(<QuestionCard question={question} onNext={vi.fn()} sourceType="drill" />)
    expect(screen.getByText('grammar')).toBeInTheDocument()
    expect(screen.getByText('verb tense consistency')).toBeInTheDocument()
    expect(screen.getByText('A passage.')).toBeInTheDocument()
    expect(screen.getByText('First option')).toBeInTheDocument()
  })

  it('submits with the given sourceType when an option is chosen', async () => {
    mutate.mockImplementation((_data, { onSuccess }: any) => onSuccess({ is_correct: true }))
    render(<QuestionCard question={question} onNext={vi.fn()} sourceType="drill" />)

    fireEvent.click(screen.getByText('First option'))

    await waitFor(() => {
      expect(mutate).toHaveBeenCalledWith(
        expect.objectContaining({ question_id: 'q-1', selected_option_label: 'A', source_type: 'drill' }),
        expect.anything(),
      )
    })
  })

  it('shows Next Question button only after answering', () => {
    render(<QuestionCard question={question} onNext={vi.fn()} sourceType="drill" />)
    expect(screen.queryByText('Next Question →')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('First option'))
    expect(screen.getByText('Next Question →')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/components/__tests__/QuestionCard.test.tsx`
Expected: FAIL with "Cannot find module '../QuestionCard'"

- [ ] **Step 3: Create the shared component**

Create `APP/STUDENT_APP_REDUX/src/components/QuestionCard.tsx` — this is the exact body currently inline in `MixedPracticePage.tsx`, moved verbatim, with the `source_type` hardcode replaced by a prop:

```tsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSubmitAnswer } from '../hooks/useDashboardData'
import type { SubmitSourceType } from '../api/client'
import { StimulusAssets } from './StimulusAssets'
import type { StimulusAsset } from '../types'

export interface Question {
  id: string
  current_question_text: string
  current_passage_text?: string | null
  options: Array<{ label: string; text: string }>
  explanation_short?: string
  grammar_focus_key?: string
  reading_focus_key?: string
  domain?: string
  stimulus_assets?: StimulusAsset[]
}

export function QuestionCard({
  question,
  onNext,
  sourceType,
}: {
  question: Question
  onNext: () => void
  sourceType: SubmitSourceType
}) {
  const [selected, setSelected] = useState<string | null>(null)
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null)
  const submitAnswer = useSubmitAnswer()

  function choose(label: string) {
    if (selected) return
    setSelected(label)
    submitAnswer.mutate(
      {
        question_id: question.id,
        selected_option_label: label,
        source_type: sourceType,
        missed_grammar_focus_key: question.grammar_focus_key,
        missed_reading_focus_key: question.reading_focus_key,
      },
      { onSuccess: (res) => setIsCorrect(res.is_correct) }
    )
  }

  return (
    <motion.div
      key={question.id}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="bg-white border border-gray-200 rounded-xl p-6"
    >
      {question.domain && (
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{question.domain}</p>
      )}
      {(question.grammar_focus_key || question.reading_focus_key) && (
        <p className="text-xs text-blue-500 font-medium mb-3">
          {(question.grammar_focus_key || question.reading_focus_key || '').replace(/_/g, ' ')}
        </p>
      )}
      {question.current_passage_text && (
        <div className="text-sm text-gray-600 leading-relaxed bg-gray-50 rounded-lg p-4 mb-4 border border-gray-100">
          {question.current_passage_text}
        </div>
      )}
      <StimulusAssets assets={question.stimulus_assets} />
      <p className="text-gray-800 leading-relaxed mb-5">{question.current_question_text}</p>

      <div className="space-y-2">
        {question.options.map((opt) => {
          const isSelected = selected === opt.label
          const showCorrect = isCorrect === true && isSelected
          const showWrong = isCorrect === false && isSelected
          return (
            <button
              key={opt.label}
              onClick={() => choose(opt.label)}
              disabled={!!selected}
              className={[
                'w-full text-left p-3 rounded-lg border text-sm transition-all',
                !selected ? 'hover:bg-blue-50 hover:border-blue-300 border-gray-200' : '',
                showCorrect ? 'bg-emerald-50 border-emerald-400 text-emerald-800' : '',
                showWrong ? 'bg-red-50 border-red-400 text-red-800' : '',
                isSelected && isCorrect === null ? 'bg-blue-50 border-blue-400' : '',
                !isSelected && !!selected ? 'opacity-50 border-gray-200' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <span className="font-mono text-gray-400 mr-2">{opt.label}.</span>
              {opt.text}
            </button>
          )
        })}
      </div>

      {selected && question.explanation_short && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-500 font-medium mb-1">Explanation</p>
          <p className="text-sm text-gray-700">{question.explanation_short}</p>
        </div>
      )}

      {selected && (
        <button
          onClick={onNext}
          className="mt-4 w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl text-sm transition"
        >
          Next Question →
        </button>
      )}
    </motion.div>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/components/__tests__/QuestionCard.test.tsx`
Expected: PASS

- [ ] **Step 5: Update `MixedPracticePage.tsx` to import the shared component**

Replace the top of `APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx` (the `interface Question` block and the whole local `function QuestionCard(...)` definition, i.e. everything from the current line 1 through the closing brace of `QuestionCard`, right before `export function MixedPracticePage()`) with:

```tsx
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { QuestionCard, type Question } from '../components/QuestionCard'
```

And where `MixedPracticePage` renders the card, change:

```tsx
        {question && <QuestionCard question={question} onNext={handleNext} />}
```

to:

```tsx
        {question && <QuestionCard question={question} onNext={handleNext} sourceType="practice" />}
```

Everything else in `MixedPracticePage.tsx` (the `MixedPracticePage` function body, its `useQuery`, `handleNext`, loading/error/empty states) stays unchanged.

- [ ] **Step 6: Run the existing MixedPracticePage-related tests (if any) plus a manual smoke check**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run` (full suite — this file has no dedicated test today, so the main risk is a broken import elsewhere)
Expected: PASS, no new failures

- [ ] **Step 7: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/components/QuestionCard.tsx APP/STUDENT_APP_REDUX/src/components/__tests__/QuestionCard.test.tsx APP/STUDENT_APP_REDUX/src/pages/MixedPracticePage.tsx
git commit -m "Extract QuestionCard into a shared component"
```

---

### Task 3: `useQuickPickQuestions` hook (fetch, merge, backfill)

**Files:**
- Create: `APP/STUDENT_APP_REDUX/src/hooks/useQuickPickQuestions.ts`
- Test: `APP/STUDENT_APP_REDUX/src/hooks/__tests__/useQuickPickQuestions.test.ts`

**Interfaces:**
- Consumes: `api.getQuestions(params: Record<string, any>)` from `APP/STUDENT_APP_REDUX/src/api/client.ts`, returning `{ items: any[]; matching_target_total?: number }`; `Question` type from `APP/STUDENT_APP_REDUX/src/components/QuestionCard.tsx`.
- Produces: `export function useQuickPickQuestions(domain: string, focusKey: string): { questions: Question[]; isLoading: boolean; isError: boolean; shortfallNote: string | null }`. Task 4 consumes this directly.

- [ ] **Step 1: Write the failing tests**

Create `APP/STUDENT_APP_REDUX/src/hooks/__tests__/useQuickPickQuestions.test.ts`:

```ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useQuickPickQuestions } from '../useQuickPickQuestions'
import { api } from '../../api/client'

vi.mock('../../api/client', () => ({
  api: { getQuestions: vi.fn() },
}))

function q(id: string) {
  return { id, current_question_text: `Q ${id}`, options: [{ label: 'A', text: 'x' }] }
}

describe('useQuickPickQuestions', () => {
  beforeEach(() => vi.clearAllMocks())

  it('fetches low/medium/high in a 3/4/3 split for the given concept', async () => {
    vi.mocked(api.getQuestions).mockImplementation(async (params: any) => {
      if (params.difficulty === 'low') return { items: [q('l1'), q('l2'), q('l3')] }
      if (params.difficulty === 'medium') return { items: [q('m1'), q('m2'), q('m3'), q('m4')] }
      if (params.difficulty === 'high') return { items: [q('h1'), q('h2'), q('h3')] }
      return { items: [] }
    })

    const { result } = renderHook(() => useQuickPickQuestions('grammar', 'verb_tense_consistency'))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(api.getQuestions).toHaveBeenCalledWith({
      domain: 'grammar', grammar_focus_key: 'verb_tense_consistency', difficulty: 'low', limit: 3,
    })
    expect(api.getQuestions).toHaveBeenCalledWith({
      domain: 'grammar', grammar_focus_key: 'verb_tense_consistency', difficulty: 'medium', limit: 4,
    })
    expect(api.getQuestions).toHaveBeenCalledWith({
      domain: 'grammar', grammar_focus_key: 'verb_tense_consistency', difficulty: 'high', limit: 3,
    })
    expect(result.current.questions.map((x) => x.id)).toEqual([
      'l1', 'l2', 'l3', 'm1', 'm2', 'm3', 'm4', 'h1', 'h2', 'h3',
    ])
    expect(result.current.shortfallNote).toBeNull()
  })

  it('uses reading_focus_key when domain is reading', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ items: [] })
    renderHook(() => useQuickPickQuestions('reading', 'inference'))

    await waitFor(() => {
      expect(api.getQuestions).toHaveBeenCalledWith(
        expect.objectContaining({ domain: 'reading', reading_focus_key: 'inference' }),
      )
    })
  })

  it('backfills a shortfall from an unfiltered-difficulty call', async () => {
    vi.mocked(api.getQuestions).mockImplementation(async (params: any) => {
      if (params.difficulty === 'low') return { items: [q('l1')] } // only 1 of 3
      if (params.difficulty === 'medium') return { items: [q('m1'), q('m2'), q('m3'), q('m4')] }
      if (params.difficulty === 'high') return { items: [q('h1'), q('h2'), q('h3')] }
      // backfill call: no difficulty param
      return { items: [q('l1'), q('b1'), q('b2')] } // l1 is a dup and must be excluded
    })

    const { result } = renderHook(() => useQuickPickQuestions('grammar', 'verb_tense_consistency'))
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.questions.map((x) => x.id)).toEqual([
      'l1', 'b1', 'b2', 'm1', 'm2', 'm3', 'm4', 'h1', 'h2', 'h3',
    ])
    expect(result.current.shortfallNote).toBeNull()
  })

  it('sets a shortfallNote when fewer than 10 questions exist in total', async () => {
    vi.mocked(api.getQuestions).mockImplementation(async (params: any) => {
      if (params.difficulty === 'low') return { items: [q('l1')] }
      if (params.difficulty === 'medium') return { items: [q('m1'), q('m2')] }
      if (params.difficulty === 'high') return { items: [] }
      return { items: [] } // backfill has nothing more either
    })

    const { result } = renderHook(() => useQuickPickQuestions('grammar', 'rare_focus'))
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.questions).toHaveLength(3)
    expect(result.current.shortfallNote).toBe('Only 3 questions available for this concept.')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/hooks/__tests__/useQuickPickQuestions.test.ts`
Expected: FAIL with "Cannot find module '../useQuickPickQuestions'"

- [ ] **Step 3: Implement the hook**

Create `APP/STUDENT_APP_REDUX/src/hooks/useQuickPickQuestions.ts`:

```ts
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Question } from '../components/QuestionCard'

const BUCKETS: Array<{ difficulty: 'low' | 'medium' | 'high'; limit: number }> = [
  { difficulty: 'low', limit: 3 },
  { difficulty: 'medium', limit: 4 },
  { difficulty: 'high', limit: 3 },
]
const TARGET_TOTAL = 10

function focusKeyParam(domain: string, focusKey: string): Record<string, string> {
  return domain === 'reading' ? { reading_focus_key: focusKey } : { grammar_focus_key: focusKey }
}

export function useQuickPickQuestions(domain: string, focusKey: string) {
  const [questions, setQuestions] = useState<Question[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [shortfallNote, setShortfallNote] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function run() {
      setIsLoading(true)
      setIsError(false)
      setShortfallNote(null)

      try {
        const focusParam = focusKeyParam(domain, focusKey)
        const results = await Promise.all(
          BUCKETS.map((bucket) =>
            api.getQuestions({ domain, ...focusParam, difficulty: bucket.difficulty, limit: bucket.limit })
          )
        )

        const seenIds = new Set<string>()
        // One slot array per bucket, in bucket order (low, medium, high). Backfill items
        // for a given bucket's shortfall are appended into that same slot, so the final
        // list stays grouped low -> medium -> high with backfill landing next to the
        // block it's compensating for, rather than all dumped at the very end.
        const slots: Question[][] = BUCKETS.map(() => [])
        const shortfallByBucket: number[] = []

        results.forEach((resp, i) => {
          const items: Question[] = resp?.items ?? []
          const taken = items.slice(0, BUCKETS[i].limit)
          taken.forEach((item) => {
            if (!seenIds.has(item.id)) {
              seenIds.add(item.id)
              slots[i].push(item)
            }
          })
          shortfallByBucket[i] = BUCKETS[i].limit - taken.length
        })

        const totalShortfall = shortfallByBucket.reduce((a, b) => a + b, 0)

        if (totalShortfall > 0 && !cancelled) {
          const alreadyHave = slots.reduce((n, slot) => n + slot.length, 0)
          const backfillResp = await api.getQuestions({ domain, ...focusParam, limit: totalShortfall + alreadyHave })
          const backfillItems: Question[] = backfillResp?.items ?? []
          let backfillIndex = 0

          for (let i = 0; i < BUCKETS.length; i++) {
            let need = shortfallByBucket[i]
            while (need > 0 && backfillIndex < backfillItems.length) {
              const candidate = backfillItems[backfillIndex]
              backfillIndex++
              if (seenIds.has(candidate.id)) continue
              seenIds.add(candidate.id)
              slots[i].push(candidate)
              need--
            }
          }
        }

        if (cancelled) return

        const merged = slots.flat()
        setQuestions(merged)
        setShortfallNote(
          merged.length < TARGET_TOTAL
            ? `Only ${merged.length} question${merged.length === 1 ? '' : 's'} available for this concept.`
            : null
        )
      } catch {
        if (!cancelled) setIsError(true)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [domain, focusKey])

  return { questions, isLoading, isError, shortfallNote }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/hooks/__tests__/useQuickPickQuestions.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/hooks/useQuickPickQuestions.ts APP/STUDENT_APP_REDUX/src/hooks/__tests__/useQuickPickQuestions.test.ts
git commit -m "Add useQuickPickQuestions hook for stratified-difficulty concept fetch"
```

---

### Task 4: `QuickPickPage` and route

**Files:**
- Create: `APP/STUDENT_APP_REDUX/src/pages/QuickPickPage.tsx`
- Test: `APP/STUDENT_APP_REDUX/src/pages/__tests__/QuickPickPage.test.tsx`
- Modify: `APP/STUDENT_APP_REDUX/src/App.tsx:11,34`

**Interfaces:**
- Consumes: `useQuickPickQuestions(domain, focusKey)` from Task 3; `QuestionCard`/`Question` from Task 2.
- Produces: `export function QuickPickPage()`, mounted at route `/practice/quick`. Task 5 navigates here with `?domain=...&focus_key=...`.

- [ ] **Step 1: Write the failing test**

Create `APP/STUDENT_APP_REDUX/src/pages/__tests__/QuickPickPage.test.tsx`:

```tsx
import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QuickPickPage } from '../QuickPickPage'
import * as quickPickHook from '../../hooks/useQuickPickQuestions'
import { useSubmitAnswer } from '../../hooks/useDashboardData'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
}))

vi.mock('../../hooks/useQuickPickQuestions', () => ({
  useQuickPickQuestions: vi.fn(),
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useSubmitAnswer: vi.fn(),
}))

const useQuickPickQuestions = vi.mocked(quickPickHook.useQuickPickQuestions)

function question(id: string) {
  return { id, current_question_text: `Question ${id}`, options: [{ label: 'A', text: 'Option A' }] }
}

function renderPage(search = '?domain=grammar&focus_key=verb_tense_consistency') {
  return render(
    <MemoryRouter initialEntries={[`/practice/quick${search}`]}>
      <QuickPickPage />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(useSubmitAnswer).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof useSubmitAnswer>)
})

describe('QuickPickPage', () => {
  it('shows a loading state', () => {
    useQuickPickQuestions.mockReturnValue({ questions: [], isLoading: true, isError: false, shortfallNote: null })
    renderPage()
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  it('shows an error state', () => {
    useQuickPickQuestions.mockReturnValue({ questions: [], isLoading: false, isError: true, shortfallNote: null })
    renderPage()
    expect(screen.getByText('Failed to load questions')).toBeInTheDocument()
  })

  it('reads domain and focus_key from the URL and passes them to the hook', () => {
    useQuickPickQuestions.mockReturnValue({ questions: [question('q1')], isLoading: false, isError: false, shortfallNote: null })
    renderPage('?domain=reading&focus_key=inference')
    expect(useQuickPickQuestions).toHaveBeenCalledWith('reading', 'inference')
  })

  it('shows the shortfall note when present', () => {
    useQuickPickQuestions.mockReturnValue({
      questions: [question('q1')],
      isLoading: false,
      isError: false,
      shortfallNote: 'Only 1 question available for this concept.',
    })
    renderPage()
    expect(screen.getByText('Only 1 question available for this concept.')).toBeInTheDocument()
  })

  it('advances through questions and shows a completion state at the end', () => {
    useQuickPickQuestions.mockReturnValue({
      questions: [question('q1'), question('q2')],
      isLoading: false,
      isError: false,
      shortfallNote: null,
    })
    renderPage()

    expect(screen.getByText('Question q1')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Option A'))
    fireEvent.click(screen.getByText('Next Question →'))
    expect(screen.getByText('Question q2')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Option A'))
    fireEvent.click(screen.getByText('Next Question →'))
    expect(screen.getByText('Session Complete')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/pages/__tests__/QuickPickPage.test.tsx`
Expected: FAIL with "Cannot find module '../QuickPickPage'"

- [ ] **Step 3: Implement the page**

Create `APP/STUDENT_APP_REDUX/src/pages/QuickPickPage.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { QuestionCard } from '../components/QuestionCard'
import { useQuickPickQuestions } from '../hooks/useQuickPickQuestions'

export function QuickPickPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const domain = searchParams.get('domain') ?? 'grammar'
  const focusKey = searchParams.get('focus_key') ?? ''
  const { questions, isLoading, isError, shortfallNote } = useQuickPickQuestions(domain, focusKey)

  const [index, setIndex] = useState(0)
  const isDone = questions.length > 0 && index >= questions.length

  function handleNext() {
    setIndex((i) => i + 1)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/practice/concepts')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← Back
        </button>
        <span className="text-gray-800 font-semibold">Quick Pick: {focusKey.replace(/_/g, ' ')}</span>
        {!isLoading && !isError && questions.length > 0 && (
          <span className="ml-auto text-xs text-gray-400">
            {Math.min(index + 1, questions.length)} / {questions.length}
          </span>
        )}
      </header>

      <div className="max-w-lg mx-auto px-4 py-6">
        {shortfallNote && (
          <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
            {shortfallNote}
          </p>
        )}

        {isLoading && (
          <div className="space-y-3">
            <div className="h-8 bg-gray-100 rounded animate-pulse w-1/3">Loading quick pick questions...</div>
            <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
          </div>
        )}

        {!isLoading && isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700 font-medium">Failed to load questions</p>
          </div>
        )}

        {!isLoading && !isError && questions.length === 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
            <p className="text-gray-500">No questions available for this concept.</p>
          </div>
        )}

        {!isLoading && !isError && isDone && (
          <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center">
            <div className="text-5xl mb-4">✓</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Session Complete</h2>
            <p className="text-gray-500 text-sm mb-6">You answered all {questions.length} questions.</p>
            <button
              onClick={() => navigate('/practice/concepts')}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition"
            >
              Back to Concepts
            </button>
          </div>
        )}

        {!isLoading && !isError && !isDone && questions[index] && (
          <QuestionCard question={questions[index]} onNext={handleNext} sourceType="drill" />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/pages/__tests__/QuickPickPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Wire the route**

In `APP/STUDENT_APP_REDUX/src/App.tsx`, add the import next to the other page imports:

```tsx
import { QuickPickPage } from './pages/QuickPickPage'
```

and add the route next to `/practice/concepts`:

```tsx
                    <Route path="/practice/concepts" element={<ConceptSelectorPage />} />
                    <Route path="/practice/quick" element={<QuickPickPage />} />
```

- [ ] **Step 6: Run the full test suite**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run`
Expected: PASS, no new failures

- [ ] **Step 7: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/pages/QuickPickPage.tsx APP/STUDENT_APP_REDUX/src/pages/__tests__/QuickPickPage.test.tsx APP/STUDENT_APP_REDUX/src/App.tsx
git commit -m "Add QuickPickPage and /practice/quick route"
```

---

### Task 5: Quick Pick action on `ConceptSelectorPage`

**Files:**
- Modify: `APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx:58-97`
- Test: `APP/STUDENT_APP_REDUX/src/pages/__tests__/ConceptSelectorPage.test.tsx`

**Interfaces:**
- Consumes: `useRecommendations` from `APP/STUDENT_APP_REDUX/src/hooks/useDashboardData.ts` (existing, unchanged).
- Produces: no new exports — this is a UI-only change to an existing page.

- [ ] **Step 1: Write the failing test**

Create `APP/STUDENT_APP_REDUX/src/pages/__tests__/ConceptSelectorPage.test.tsx`:

```tsx
import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ConceptSelectorPage } from '../ConceptSelectorPage'
import * as dashboardHooks from '../../hooks/useDashboardData'

const mockNavigate = vi.fn()

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../hooks/useDashboardData', () => ({
  useRecommendations: vi.fn(),
}))

const useRecommendations = vi.mocked(dashboardHooks.useRecommendations)

const target = {
  domain: 'grammar',
  focus_key: 'verb_tense_consistency',
  difficulty: 'medium',
  weakness_score: 0.8,
  miss_count: 5,
  attempt_count: 6,
  miss_rate: 0.83,
  days_since_last_attempt: 1,
  inventory_unseen: 10,
  inventory_below_threshold: false,
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ConceptSelectorPage />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  useRecommendations.mockReturnValue({
    data: { user_id: 1, top_targets: [target], threshold: 0.5 },
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof dashboardHooks.useRecommendations>)
})

describe('ConceptSelectorPage', () => {
  it('navigates to the drill route when the row body is tapped', () => {
    renderPage()
    fireEvent.click(screen.getByText('verb tense consistency'))
    expect(mockNavigate).toHaveBeenCalledWith(
      '/practice/grammar?focus_key=verb_tense_consistency&domain=grammar&limit=10'
    )
  })

  it('navigates to the quick pick route when the quick pick action is tapped', () => {
    renderPage()
    fireEvent.click(screen.getByRole('button', { name: /Quick Pick/i }))
    expect(mockNavigate).toHaveBeenCalledWith(
      '/practice/quick?domain=grammar&focus_key=verb_tense_consistency'
    )
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/pages/__tests__/ConceptSelectorPage.test.tsx`
Expected: FAIL — no element with accessible name matching `/Quick Pick/i` exists yet, and the row-body click currently fires the whole `motion.button` (including nested content), so it should already pass for the first test; confirm that only the second test fails.

- [ ] **Step 3: Add the quick-pick action**

In `APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx`, the current row is a single `motion.button` whose `onClick` handles the drill navigation. Split it so the row is a container `motion.div` with two independent actions: the existing content becomes a `<button>` for drill navigation, and a new sibling `<button>` handles quick pick. Replace the `targets.map` block:

```tsx
        <div className="space-y-2">
          {targets.map((t, i) => {
            const pct = Math.round(t.weakness_score * 100)
            const barColor =
              pct >= 70 ? 'bg-red-400' : pct >= 40 ? 'bg-amber-400' : 'bg-emerald-400'

            return (
              <motion.div
                key={`${t.domain}-${t.focus_key}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, duration: 0.2, ease: 'easeOut' }}
                className="flex items-stretch gap-2"
              >
                <button
                  onClick={() =>
                    navigate(
                      `/practice/grammar?focus_key=${encodeURIComponent(t.focus_key)}&domain=${encodeURIComponent(t.domain)}&limit=${limit}`
                    )
                  }
                  className="flex-1 text-left bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-blue-300 hover:shadow-sm transition-all group"
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
                </button>
                <button
                  onClick={() =>
                    navigate(
                      `/practice/quick?domain=${encodeURIComponent(t.domain)}&focus_key=${encodeURIComponent(t.focus_key)}`
                    )
                  }
                  aria-label={`Quick Pick 10 for ${t.focus_key.replace(/_/g, ' ')}`}
                  title="Quick Pick: 10 questions, mixed difficulty"
                  className="flex-shrink-0 w-11 flex items-center justify-center bg-white border border-gray-200 rounded-xl hover:border-violet-300 hover:bg-violet-50 transition-all text-lg"
                >
                  ⚡
                </button>
              </motion.div>
            )
          })}
        </div>
```

(`limit` here is the same `searchParams.get('limit') ?? '10'` value already defined earlier in the component — unchanged.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run src/pages/__tests__/ConceptSelectorPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the full test suite**

Run: `cd APP/STUDENT_APP_REDUX && npx vitest run`
Expected: PASS, no new failures

- [ ] **Step 6: Commit**

```bash
git add APP/STUDENT_APP_REDUX/src/pages/ConceptSelectorPage.tsx APP/STUDENT_APP_REDUX/src/pages/__tests__/ConceptSelectorPage.test.tsx
git commit -m "Add Quick Pick action to concept selector rows"
```

---

## Final Verification

- [ ] Run `cd APP/STUDENT_APP_REDUX && npx vitest run` once more — full suite green.
- [ ] Run `cd APP/STUDENT_APP_REDUX && npx tsc --noEmit` (or the project's existing typecheck script) — no new type errors.
- [ ] Manually smoke-test in the dev stack (`/dev-stack`): log in, go to Pick a Concept, confirm the ⚡ button navigates to a 10-question (or fewer, with note) mixed-difficulty set, and confirm the row-body tap still launches the correctly-filtered drill.
