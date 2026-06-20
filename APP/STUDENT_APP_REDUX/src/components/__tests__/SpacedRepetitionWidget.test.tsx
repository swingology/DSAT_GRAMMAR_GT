import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SpacedRepetitionWidget } from '../dashboard/SpacedRepetitionWidget'

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

const mockNavigate = vi.fn()

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_t, tag: string) => ({ children, ...p }: any) =>
      React.createElement(tag as string, p, children),
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../hooks/useDashboardData', () => ({
  useSRProgress: vi.fn(),
  useSRDue: vi.fn(),
}))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

import * as hooks from '../../hooks/useDashboardData'

const mockedUseSRProgress = vi.mocked(hooks.useSRProgress)
const mockedUseSRDue = vi.mocked(hooks.useSRDue)

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

// ---------------------------------------------------------------------------
// Standard mock data
// ---------------------------------------------------------------------------

const mockProgress = {
  total_tracked: 10,
  mastered_count: 2,
  proficient_count: 3,
  developing_count: 4,
  novice_count: 1,
  due_for_review: 3,
  average_easiness_factor: 2.4,
  retention_rate: 0.75,
}

const mockDue = {
  due_questions: [
    {
      question_id: 'uuid-1',
      days_overdue: 2,
      confidence_level: 'developing',
      focus_area: 'comma_splice',
      domain: 'grammar',
      last_reviewed_at: null,
      next_review_at: null,
    },
    {
      question_id: 'uuid-2',
      days_overdue: 0.5,
      confidence_level: 'novice',
      focus_area: 'verb_tense_consistency',
      domain: 'grammar',
      last_reviewed_at: null,
      next_review_at: null,
    },
  ],
  total_due: 3,
  suggested_session_length_minutes: 9,
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SpacedRepetitionWidget', () => {
  it('shows loading skeleton while fetching', () => {
    mockedUseSRProgress.mockReturnValue({ isLoading: true, data: undefined } as any)
    mockedUseSRDue.mockReturnValue({ isLoading: true, data: undefined } as any)

    wrap(<SpacedRepetitionWidget />)

    const skeleton = document.querySelector('.animate-pulse')
    expect(skeleton).not.toBeNull()
  })

  it('shows empty state when total_tracked is 0', async () => {
    mockedUseSRProgress.mockReturnValue({
      isLoading: false,
      data: { ...mockProgress, total_tracked: 0 },
    } as any)
    mockedUseSRDue.mockReturnValue({
      isLoading: false,
      data: mockDue,
    } as any)

    wrap(<SpacedRepetitionWidget />)

    await waitFor(() => {
      expect(
        screen.getByText(/Complete diagnostics/i)
      ).toBeTruthy()
    })
  })

  it('shows due count badge when questions due', async () => {
    mockedUseSRProgress.mockReturnValue({
      isLoading: false,
      data: { ...mockProgress, due_for_review: 3 },
    } as any)
    mockedUseSRDue.mockReturnValue({
      isLoading: false,
      data: mockDue,
    } as any)

    wrap(<SpacedRepetitionWidget />)

    await waitFor(() => {
      expect(screen.getByText('3 due')).toBeTruthy()
    })
  })

  it('shows all caught up when nothing due', async () => {
    mockedUseSRProgress.mockReturnValue({
      isLoading: false,
      data: { ...mockProgress, due_for_review: 0 },
    } as any)
    mockedUseSRDue.mockReturnValue({
      isLoading: false,
      data: { ...mockDue, due_questions: [], total_due: 0 },
    } as any)

    wrap(<SpacedRepetitionWidget />)

    await waitFor(() => {
      expect(screen.getByText(/All caught up/i)).toBeTruthy()
    })
  })

  it('shows mastery tier breakdown', async () => {
    mockedUseSRProgress.mockReturnValue({
      isLoading: false,
      data: {
        ...mockProgress,
        mastered_count: 2,
        proficient_count: 5,
        novice_count: 1,
        developing_count: 0,
      },
    } as any)
    mockedUseSRDue.mockReturnValue({
      isLoading: false,
      data: mockDue,
    } as any)

    wrap(<SpacedRepetitionWidget />)

    await waitFor(() => {
      expect(screen.getByText('2 Mastered')).toBeTruthy()
      expect(screen.getByText('5 Proficient')).toBeTruthy()
      expect(screen.getByText('1 Novice')).toBeTruthy()
    })
  })

  it('shows due question list with focus area text', async () => {
    mockedUseSRProgress.mockReturnValue({
      isLoading: false,
      data: mockProgress,
    } as any)
    mockedUseSRDue.mockReturnValue({
      isLoading: false,
      data: mockDue,
    } as any)

    wrap(<SpacedRepetitionWidget />)

    await waitFor(() => {
      // focus_area rendered with underscores replaced by spaces
      expect(screen.getByText('comma splice')).toBeTruthy()
      expect(screen.getByText('verb tense consistency')).toBeTruthy()
    })
  })

  it('shows review button when questions due', async () => {
    mockedUseSRProgress.mockReturnValue({
      isLoading: false,
      data: { ...mockProgress, due_for_review: 5 },
    } as any)
    mockedUseSRDue.mockReturnValue({
      isLoading: false,
      data: mockDue,
    } as any)

    wrap(<SpacedRepetitionWidget />)

    await waitFor(() => {
      expect(screen.getByText('Review 5 questions')).toBeTruthy()
    })
  })

  it('review button navigates to grammar practice', async () => {
    mockedUseSRProgress.mockReturnValue({
      isLoading: false,
      data: { ...mockProgress, due_for_review: 5 },
    } as any)
    mockedUseSRDue.mockReturnValue({
      isLoading: false,
      data: mockDue,
    } as any)

    wrap(<SpacedRepetitionWidget />)

    await waitFor(() => {
      const btn = screen.getByText('Review 5 questions')
      fireEvent.click(btn)
    })

    expect(mockNavigate).toHaveBeenCalledWith('/practice/grammar')
  })
})
