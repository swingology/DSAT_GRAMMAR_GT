import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MissedQuestionsTab } from '../dashboard/MissedQuestionsTab'
import * as hooks from '../../hooks/useDashboardData'

vi.mock('../../hooks/useDashboardData', () => ({
  useMissedQuestions: vi.fn(),
}))

const mockedUseMissedQuestions = vi.mocked(hooks.useMissedQuestions)

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const mockItem = {
  question_id: 'q-1',
  question_text: 'Which option corrects the comma splice?',
  domain: 'grammar',
  focus_key: 'comma_splice',
  difficulty: 'medium',
  user_answer: 'A',
  correct_answer: 'B',
  explanation: 'Two independent clauses cannot be joined with only a comma.',
  miss_count: 3,
  last_missed_at: '2026-06-15T10:00:00Z',
}

beforeEach(() => { vi.clearAllMocks() })

describe('MissedQuestionsTab', () => {
  it('shows loading skeletons while fetching', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: true, isError: false, data: undefined,
    } as any)
    wrap(<MissedQuestionsTab />)
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows error state when fetch fails', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: true, data: undefined,
    } as any)
    wrap(<MissedQuestionsTab />)
    expect(screen.getByText(/failed to load missed questions/i)).toBeInTheDocument()
  })

  it('shows empty success state when no misses', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [], total: 0 },
    } as any)
    wrap(<MissedQuestionsTab />)
    expect(screen.getByText(/no missed questions/i)).toBeInTheDocument()
  })

  it('renders a card for each missed question', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [mockItem], total: 1 },
    } as any)
    wrap(<MissedQuestionsTab />)
    expect(screen.getByText('Which option corrects the comma splice?')).toBeInTheDocument()
  })

  it('shows miss count badge', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [mockItem], total: 1 },
    } as any)
    wrap(<MissedQuestionsTab />)
    expect(screen.getByText('✗ 3×')).toBeInTheDocument()
  })

  it('shows user answer and correct answer', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [mockItem], total: 1 },
    } as any)
    wrap(<MissedQuestionsTab />)
    // Use getAllByText since "Correct:" appears in both the answer row and possibly parent elements
    expect(screen.getAllByText(/you chose/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/correct:/i).length).toBeGreaterThanOrEqual(1)
  })

  it('hides explanation by default and reveals on click', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [mockItem], total: 1 },
    } as any)
    wrap(<MissedQuestionsTab />)
    expect(screen.queryByText('Two independent clauses cannot be joined with only a comma.')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText(/show explanation/i))
    expect(screen.getByText('Two independent clauses cannot be joined with only a comma.')).toBeInTheDocument()
  })

  it('collapses explanation after second click', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [mockItem], total: 1 },
    } as any)
    wrap(<MissedQuestionsTab />)
    fireEvent.click(screen.getByText(/show explanation/i))
    fireEvent.click(screen.getByText(/hide explanation/i))
    expect(screen.queryByText('Two independent clauses cannot be joined with only a comma.')).not.toBeInTheDocument()
  })

  it('shows domain and focus key badges', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [mockItem], total: 1 },
    } as any)
    wrap(<MissedQuestionsTab />)
    // 'grammar' appears in both the card badge and the filter button — verify at least 2
    expect(screen.getAllByText('grammar').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('comma splice')).toBeInTheDocument()
  })

  it('shows total count summary', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [mockItem], total: 1 },
    } as any)
    wrap(<MissedQuestionsTab />)
    expect(screen.getByText(/1 question missed/i)).toBeInTheDocument()
  })

  it('domain filter buttons are rendered', () => {
    mockedUseMissedQuestions.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, items: [], total: 0 },
    } as any)
    wrap(<MissedQuestionsTab />)
    expect(screen.getByRole('button', { name: /^all$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^grammar$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^reading$/i })).toBeInTheDocument()
  })
})
