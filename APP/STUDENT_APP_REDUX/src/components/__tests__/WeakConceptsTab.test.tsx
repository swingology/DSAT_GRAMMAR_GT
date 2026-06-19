import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WeakConceptsTab } from '../dashboard/WeakConceptsTab'
import * as hooks from '../../hooks/useDashboardData'

vi.mock('framer-motion', () => ({
  motion: { div: ({ children, ...p }: any) => <div {...p}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useRecommendations: vi.fn(),
}))

const mockedUseRecommendations = vi.mocked(hooks.useRecommendations)

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const mockTarget = {
  domain: 'grammar',
  focus_key: 'comma_splice',
  skill_family_key: null,
  grammar_role_key: 'sentence_structure',
  difficulty: 'medium',
  weakness_score: 0.75,
  miss_count: 3,
  attempt_count: 4,
  miss_rate: 0.75,
  days_since_last_attempt: 1,
  inventory_unseen: 5,
  inventory_below_threshold: false,
}

beforeEach(() => { vi.clearAllMocks() })

describe('WeakConceptsTab', () => {
  it('shows loading skeletons while fetching', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: true, isError: false, data: undefined, error: null,
    } as any)
    wrap(<WeakConceptsTab />)
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows error message on failure', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false, isError: true, data: undefined, error: new Error('fail'),
    } as any)
    wrap(<WeakConceptsTab />)
    expect(screen.getByText(/failed to load recommendations/i)).toBeInTheDocument()
  })

  it('shows empty state when no targets', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, top_targets: [], threshold: 5 },
    } as any)
    wrap(<WeakConceptsTab />)
    expect(screen.getByText(/no weak concepts found/i)).toBeInTheDocument()
  })

  it('renders a card for each target', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, top_targets: [mockTarget, { ...mockTarget, focus_key: 'run_on' }], threshold: 5 },
    } as any)
    wrap(<WeakConceptsTab />)
    expect(screen.getByText('comma splice')).toBeInTheDocument()
    expect(screen.getByText('run on')).toBeInTheDocument()
  })

  it('displays rank numbers starting at 1', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, top_targets: [mockTarget], threshold: 5 },
    } as any)
    wrap(<WeakConceptsTab />)
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('shows miss count and attempt count', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, top_targets: [mockTarget], threshold: 5 },
    } as any)
    wrap(<WeakConceptsTab />)
    expect(screen.getByText('3/4 missed')).toBeInTheDocument()
  })

  it('shows "yesterday" for 1 day since last attempt', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, top_targets: [mockTarget], threshold: 5 },
    } as any)
    wrap(<WeakConceptsTab />)
    expect(screen.getByText(/yesterday/)).toBeInTheDocument()
  })

  it('shows new question count when inventory_unseen > 0', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false, isError: false,
      data: { user_id: 1, top_targets: [mockTarget], threshold: 5 },
    } as any)
    wrap(<WeakConceptsTab />)
    expect(screen.getByText('5 new Qs')).toBeInTheDocument()
  })
})
