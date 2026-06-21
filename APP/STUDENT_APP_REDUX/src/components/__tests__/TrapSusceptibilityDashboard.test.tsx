import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TrapSusceptibilityDashboard } from '../dashboard/TrapSusceptibilityDashboard'
import * as dashboardHooks from '../../hooks/useDashboardData'

vi.mock('../../hooks/useDashboardData', () => ({
  useTrapSusceptibility: vi.fn(),
  useTrapDetails: vi.fn(),
}))

const EMPTY_DATA = {
  user_id: 1,
  total_questions_attempted: 0,
  trap_encounters: {},
  trap_fall_rates: {},
  trap_correct_counts: {},
  most_susceptible_traps: [],
  overcoming_traps: [],
  persistent_traps: [],
  trap_improvement: {},
}

const SAMPLE_DATA = {
  user_id: 1,
  total_questions_attempted: 42,
  trap_encounters: { subject_number_mismatch: 10, pronoun_case_ambiguity: 5 },
  trap_fall_rates: { subject_number_mismatch: 0.7, pronoun_case_ambiguity: 0.4 },
  trap_correct_counts: { subject_number_mismatch: 3, pronoun_case_ambiguity: 3 },
  most_susceptible_traps: [
    { trap_type: 'subject_number_mismatch', fall_rate: 0.7, occurrences: 10, correct_count: 3, severity: 'high' },
    { trap_type: 'pronoun_case_ambiguity', fall_rate: 0.4, occurrences: 5, correct_count: 3, severity: 'moderate' },
  ],
  overcoming_traps: [
    { trap_type: 'pronoun_case_ambiguity', fall_rate: 0.4, occurrences: 5, correct_count: 3, severity: 'moderate' },
  ],
  persistent_traps: [
    { trap_type: 'subject_number_mismatch', fall_rate: 0.7, occurrences: 10, correct_count: 3, severity: 'high' },
  ],
  trap_improvement: {},
}

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('TrapSusceptibilityDashboard', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('shows loading state', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: true, isError: false, data: undefined, refetch: vi.fn(),
    } as any)
    wrap(<TrapSusceptibilityDashboard />)
    expect(screen.getByText(/loading trap analysis/i)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: false, isError: true, data: undefined, refetch: vi.fn(),
    } as any)
    wrap(<TrapSusceptibilityDashboard />)
    expect(screen.getByText(/failed to load trap data/i)).toBeInTheDocument()
    expect(screen.getByText(/retry/i)).toBeInTheDocument()
  })

  it('shows empty state when no questions answered', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: false, isError: false, data: EMPTY_DATA, refetch: vi.fn(),
    } as any)
    wrap(<TrapSusceptibilityDashboard />)
    expect(screen.getByText(/no trap data yet/i)).toBeInTheDocument()
  })

  it('renders trap cards for susceptible traps', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DATA, refetch: vi.fn(),
    } as any)
    wrap(<TrapSusceptibilityDashboard />)
    // Trap names appear in both the card and the persistent/overcoming pill sections
    expect(screen.getAllByText('Subject Number Mismatch').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Pronoun Case Ambiguity').length).toBeGreaterThanOrEqual(1)
  })

  it('shows miss rate percentage', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DATA, refetch: vi.fn(),
    } as any)
    wrap(<TrapSusceptibilityDashboard />)
    expect(screen.getByText('70% miss rate')).toBeInTheDocument()
  })

  it('shows overcoming and persistent sections', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DATA, refetch: vi.fn(),
    } as any)
    wrap(<TrapSusceptibilityDashboard />)
    expect(screen.getByText(/improving on/i)).toBeInTheDocument()
    expect(screen.getByText(/still struggling/i)).toBeInTheDocument()
  })

  it('shows total questions answered', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DATA, refetch: vi.fn(),
    } as any)
    wrap(<TrapSusceptibilityDashboard />)
    expect(screen.getByText(/42 questions answered/i)).toBeInTheDocument()
  })

  it('navigates to trap detail view when card is clicked', () => {
    vi.mocked(dashboardHooks.useTrapSusceptibility).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DATA, refetch: vi.fn(),
    } as any)
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: true, isError: false, data: undefined, refetch: vi.fn(),
    } as any)

    wrap(<TrapSusceptibilityDashboard />)

    // Click the first trap card button
    const cardButtons = screen.getAllByRole('button')
    const trapCardBtn = cardButtons.find(b => b.textContent?.includes('Subject Number Mismatch'))
    expect(trapCardBtn).toBeTruthy()
    fireEvent.click(trapCardBtn!)

    // Should now show the detail view (loading state)
    expect(screen.getByText(/loading trap details/i)).toBeInTheDocument()
  })
})
