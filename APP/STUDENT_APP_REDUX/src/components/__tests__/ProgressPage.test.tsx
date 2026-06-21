import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProgressPage } from '../../pages/ProgressPage'
import * as hooks from '../../hooks/useDashboardData'

vi.mock('../../hooks/useDashboardData', () => ({
  useProgressTrend: vi.fn(),
  useDomainTrend: vi.fn(),
  useFocusSummary: vi.fn(),
}))

const EMPTY_TREND = {
  user_id: 1,
  days: 30,
  points: [] as Array<{ date: string; attempts: number; correct: number; accuracy: number }>,
  overall_accuracy: 0,
  total_attempts: 0,
  streak_days: 0,
}
const SAMPLE_TREND = {
  user_id: 1,
  days: 30,
  points: [
    { date: '2026-06-01', attempts: 10, correct: 7, accuracy: 0.7 },
    { date: '2026-06-10', attempts: 15, correct: 12, accuracy: 0.8 },
    { date: '2026-06-20', attempts: 8, correct: 6, accuracy: 0.75 },
  ],
  overall_accuracy: 0.75,
  total_attempts: 33,
  streak_days: 3,
}
const SAMPLE_DOMAIN = {
  user_id: 1, days: 30,
  grammar: [{ date: '2026-06-10', attempts: 10, correct: 7, accuracy: 0.7 }],
  reading: [{ date: '2026-06-10', attempts: 5, correct: 4, accuracy: 0.8 }],
}
const SAMPLE_FOCUS = {
  user_id: 1,
  top_focus_areas: [
    { focus_key: 'verb_tense_consistency', domain: 'grammar', total_attempts: 20, correct_count: 14, accuracy: 0.7 },
    { focus_key: 'subject_verb_agreement', domain: 'grammar', total_attempts: 15, correct_count: 9, accuracy: 0.6 },
  ],
  weakest_focus_areas: [
    { focus_key: 'subject_verb_agreement', domain: 'grammar', total_attempts: 15, correct_count: 9, accuracy: 0.6 },
  ],
}

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ProgressPage', () => {
  beforeEach(() => { vi.clearAllMocks() })

  function mockAll({ trend = EMPTY_TREND, domain = SAMPLE_DOMAIN, focus = SAMPLE_FOCUS } = {}) {
    vi.mocked(hooks.useProgressTrend).mockReturnValue({ data: trend, isLoading: false, isError: false, refetch: vi.fn() } as any)
    vi.mocked(hooks.useDomainTrend).mockReturnValue({ data: domain, isLoading: false, isError: false, refetch: vi.fn() } as any)
    vi.mocked(hooks.useFocusSummary).mockReturnValue({ data: focus, isLoading: false, isError: false, refetch: vi.fn() } as any)
  }

  it('renders the page heading', () => {
    mockAll()
    wrap(<ProgressPage />)
    expect(screen.getByText('Your Progress')).toBeInTheDocument()
  })

  it('shows empty state when no attempts', () => {
    mockAll({ trend: EMPTY_TREND })
    wrap(<ProgressPage />)
    expect(screen.getByText(/no data yet/i)).toBeInTheDocument()
    expect(screen.getByText(/start practicing/i)).toBeInTheDocument()
  })

  it('shows summary pills with real data', () => {
    mockAll({ trend: SAMPLE_TREND })
    wrap(<ProgressPage />)
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText('33')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders day picker buttons', () => {
    mockAll()
    wrap(<ProgressPage />)
    expect(screen.getByText('7d')).toBeInTheDocument()
    expect(screen.getByText('30d')).toBeInTheDocument()
  })

  it('clicking day picker changes selection', () => {
    mockAll()
    wrap(<ProgressPage />)
    const btn14 = screen.getByText('14d')
    fireEvent.click(btn14)
    expect(btn14).toBeInTheDocument()
  })

  it('renders focus area bars', () => {
    mockAll({ trend: SAMPLE_TREND })
    wrap(<ProgressPage />)
    expect(screen.getAllByText(/verb tense consistency/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/subject verb agreement/i).length).toBeGreaterThanOrEqual(1)
  })

  it('renders dashboard back link', () => {
    mockAll()
    wrap(<ProgressPage />)
    expect(screen.getByText(/← Dashboard/i)).toBeInTheDocument()
  })

  it('shows loading states', () => {
    vi.mocked(hooks.useProgressTrend).mockReturnValue({ data: undefined, isLoading: true, isError: false, refetch: vi.fn() } as any)
    vi.mocked(hooks.useDomainTrend).mockReturnValue({ data: undefined, isLoading: true, isError: false, refetch: vi.fn() } as any)
    vi.mocked(hooks.useFocusSummary).mockReturnValue({ data: undefined, isLoading: true, isError: false, refetch: vi.fn() } as any)
    wrap(<ProgressPage />)
    expect(screen.getByText(/loading trend/i)).toBeInTheDocument()
  })
})
