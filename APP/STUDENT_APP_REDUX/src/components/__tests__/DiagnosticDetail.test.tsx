import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DiagnosticDetail } from '../dashboard/DiagnosticDetail'

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

const mockNavigate = vi.fn()

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children),
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ sessionId: 'test-session-123' }),
  }
})

vi.mock('../../api/client', () => ({
  api: {
    diagnosticDetail: vi.fn(),
  },
}))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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

const MOCK_SESSION_DETAIL = {
  session_id: 'test-session-123',
  user_id: 1,
  created_at: '2026-06-18T09:00:00Z',
  completed_at: '2026-06-18T09:20:00Z',
  total_questions: 3,
  correct_count: 2,
  accuracy: 0.75,
  question_results: [
    {
      question_number: 1,
      question_id: 'q-aaa-001',
      selected_option: 'B',
      is_correct: true,
      focus_area: 'comma_splice',
    },
    {
      question_number: 2,
      question_id: 'q-bbb-002',
      selected_option: 'A',
      is_correct: false,
      focus_area: 'subject_verb_agreement',
    },
    {
      question_number: 3,
      question_id: 'q-ccc-003',
      selected_option: 'C',
      is_correct: true,
      focus_area: 'comma_splice',
    },
  ],
  focus_breakdown: {
    comma_splice: { attempted: 2, correct: 2 },
    subject_verb_agreement: { attempted: 1, correct: 0 },
  },
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DiagnosticDetail', () => {
  it('shows loading skeleton while query fetches', async () => {
    const { api } = await import('../../api/client')
    // Never resolves — stays in loading state
    vi.mocked(api.diagnosticDetail).mockReturnValue(new Promise(() => {}))

    wrap(<DiagnosticDetail />)

    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows error state on fetch failure', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticDetail).mockRejectedValue(new Error('API error: 404 Not Found'))

    wrap(<DiagnosticDetail />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load session details/i)).toBeInTheDocument()
    })
  })

  it('renders score percentage when accuracy is 0.75', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticDetail).mockResolvedValue(MOCK_SESSION_DETAIL)

    wrap(<DiagnosticDetail />)

    await waitFor(() => {
      expect(screen.getByText('75%')).toBeInTheDocument()
    })
  })

  it('renders all question results', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticDetail).mockResolvedValue(MOCK_SESSION_DETAIL)

    wrap(<DiagnosticDetail />)

    await waitFor(() => {
      expect(screen.getByText('Q1')).toBeInTheDocument()
    })

    expect(screen.getByText('Q2')).toBeInTheDocument()
    expect(screen.getByText('Q3')).toBeInTheDocument()
  })

  it('renders focus breakdown entries', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticDetail).mockResolvedValue(MOCK_SESSION_DETAIL)

    wrap(<DiagnosticDetail />)

    await waitFor(() => {
      // "comma splice" appears in both focus breakdown section AND question results;
      // use getAllByText and assert at least 1 exists
      expect(screen.getAllByText('comma splice').length).toBeGreaterThan(0)
    })

    // "subject verb agreement" appears in focus breakdown (and possibly question results)
    expect(screen.getAllByText('subject verb agreement').length).toBeGreaterThan(0)
  })

  it('back link navigates to history', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticDetail).mockResolvedValue(MOCK_SESSION_DETAIL)

    wrap(<DiagnosticDetail />)

    await waitFor(() => {
      expect(screen.getByText('← History')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('← History'))
    expect(mockNavigate).toHaveBeenCalledWith('/diagnostic/history')
  })
})
