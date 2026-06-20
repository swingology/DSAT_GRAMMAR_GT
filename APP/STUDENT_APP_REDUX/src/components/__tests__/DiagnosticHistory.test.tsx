import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DiagnosticHistory } from '../dashboard/DiagnosticHistory'

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
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../api/client', () => ({
  api: {
    diagnosticHistory: vi.fn(),
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

const SESSION_1 = {
  session_id: 'session-aaa-111',
  created_at: '2026-06-18T09:00:00Z',
  completed_at: '2026-06-18T09:20:00Z',
  accuracy: 0.75,
  total_questions: 8,
  correct_count: 6,
  diagnostic_type: 'standard',
  duration_seconds: 1200,
}

const SESSION_2 = {
  session_id: 'session-bbb-222',
  created_at: '2026-06-15T14:00:00Z',
  completed_at: '2026-06-15T14:22:00Z',
  accuracy: 0.5,
  total_questions: 8,
  correct_count: 4,
  diagnostic_type: 'adaptive',
  duration_seconds: 1320,
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DiagnosticHistory', () => {
  it('shows loading skeleton while query is fetching', async () => {
    const { api } = await import('../../api/client')
    // Never resolve — keeps loading state
    vi.mocked(api.diagnosticHistory).mockReturnValue(new Promise(() => {}))

    wrap(<DiagnosticHistory />)

    // The loading skeleton has the animate-pulse class
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows empty state when no sessions', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticHistory).mockResolvedValue({
      sessions: [],
      total_sessions: 0,
      average_accuracy: null,
      improvement_trend: null,
    })

    wrap(<DiagnosticHistory />)

    await waitFor(() => {
      expect(screen.getByText(/no diagnostics completed yet/i)).toBeInTheDocument()
    })
  })

  it('renders session list with dates and accuracy', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticHistory).mockResolvedValue({
      sessions: [SESSION_1, SESSION_2],
      total_sessions: 2,
      average_accuracy: 0.625,
      improvement_trend: null,
    })

    wrap(<DiagnosticHistory />)

    await waitFor(() => {
      // 75% accuracy shown for SESSION_1
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    // 50% accuracy for SESSION_2
    expect(screen.getByText('50%')).toBeInTheDocument()

    // Both correct/total counts shown
    expect(screen.getByText(/6\/8 correct/i)).toBeInTheDocument()
    expect(screen.getByText(/4\/8 correct/i)).toBeInTheDocument()
  })

  it('shows improvement trend badge when trend is positive', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticHistory).mockResolvedValue({
      sessions: [SESSION_1, SESSION_2],
      total_sessions: 2,
      average_accuracy: 0.625,
      improvement_trend: 0.1,
    })

    wrap(<DiagnosticHistory />)

    await waitFor(() => {
      expect(screen.getByText(/improving/i)).toBeInTheDocument()
    })
  })

  it('navigates to session detail on row click', async () => {
    const { api } = await import('../../api/client')
    vi.mocked(api.diagnosticHistory).mockResolvedValue({
      sessions: [SESSION_1],
      total_sessions: 1,
      average_accuracy: 0.75,
      improvement_trend: null,
    })

    wrap(<DiagnosticHistory />)

    // Wait for session to render, then click it
    await waitFor(() => {
      // Multiple "75%" elements may exist (avg accuracy stat + session row)
      expect(screen.getAllByText('75%').length).toBeGreaterThan(0)
    })

    // Find the session row button — it contains the percentage as a div inside it
    const buttons = screen.getAllByRole('button')
    // The session row button is the one that's not "Take a Diagnostic"
    const sessionButton = buttons.find(b => b.textContent?.includes('6/8'))
    expect(sessionButton).not.toBeUndefined()
    fireEvent.click(sessionButton!)

    expect(mockNavigate).toHaveBeenCalledWith(`/diagnostic/${SESSION_1.session_id}`)
  })
})
