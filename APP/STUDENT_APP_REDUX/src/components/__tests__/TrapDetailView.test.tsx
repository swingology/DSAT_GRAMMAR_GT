import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TrapDetailView } from '../dashboard/TrapDetailView'
import * as dashboardHooks from '../../hooks/useDashboardData'

vi.mock('../../hooks/useDashboardData', () => ({
  useTrapDetails: vi.fn(),
}))

const SAMPLE_DETAIL = {
  trap_type: 'subject_number_mismatch',
  user_encounters: 10,
  user_fall_rate: 0.7,
  first_accuracy: 0.2,
  recent_accuracy: 0.6,
  trend: 0.4,
  severity: 'high',
  example_mistakes: [
    {
      question_text: 'The group of students were studying for the exam.',
      selected_option: 'B',
      is_correct: false,
      grammar_focus: 'subject_verb_agreement',
    },
  ],
}

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('TrapDetailView', () => {
  const mockOnBack = vi.fn()

  beforeEach(() => { vi.clearAllMocks() })

  it('shows loading state', () => {
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: true, isError: false, data: undefined, refetch: vi.fn(),
    } as any)
    wrap(<TrapDetailView trapType="subject_number_mismatch" onBack={mockOnBack} />)
    expect(screen.getByText(/loading trap details/i)).toBeInTheDocument()
  })

  it('shows error state with back button', () => {
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: false, isError: true, data: undefined, refetch: vi.fn(),
    } as any)
    wrap(<TrapDetailView trapType="subject_number_mismatch" onBack={mockOnBack} />)
    expect(screen.getByText(/← Back/)).toBeInTheDocument()
    expect(screen.getByText(/no data found/i)).toBeInTheDocument()
  })

  it('renders trap name as heading', () => {
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DETAIL, refetch: vi.fn(),
    } as any)
    wrap(<TrapDetailView trapType="subject_number_mismatch" onBack={mockOnBack} />)
    expect(screen.getByText('Subject Number Mismatch')).toBeInTheDocument()
  })

  it('shows miss rate, attempts, and trend stats', () => {
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DETAIL, refetch: vi.fn(),
    } as any)
    wrap(<TrapDetailView trapType="subject_number_mismatch" onBack={mockOnBack} />)
    expect(screen.getByText('70%')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText(/↑/)).toBeInTheDocument()
  })

  it('shows example mistakes', () => {
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DETAIL, refetch: vi.fn(),
    } as any)
    wrap(<TrapDetailView trapType="subject_number_mismatch" onBack={mockOnBack} />)
    expect(screen.getByText(/group of students/i)).toBeInTheDocument()
    expect(screen.getByText(/you chose: B/i)).toBeInTheDocument()
  })

  it('calls onBack when back button is clicked', () => {
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DETAIL, refetch: vi.fn(),
    } as any)
    wrap(<TrapDetailView trapType="subject_number_mismatch" onBack={mockOnBack} />)
    fireEvent.click(screen.getByText('← Back'))
    expect(mockOnBack).toHaveBeenCalledOnce()
  })

  it('shows severity badge', () => {
    vi.mocked(dashboardHooks.useTrapDetails).mockReturnValue({
      isLoading: false, isError: false, data: SAMPLE_DETAIL, refetch: vi.fn(),
    } as any)
    wrap(<TrapDetailView trapType="subject_number_mismatch" onBack={mockOnBack} />)
    expect(screen.getByText(/high severity/i)).toBeInTheDocument()
  })
})
