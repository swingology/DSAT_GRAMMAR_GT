import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DiagnosticCard } from '../dashboard/DiagnosticCard'
import * as hooks from '../../hooks/useDashboardData'

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
  useRecommendations: vi.fn(),
}))

const mockedUseRecommendations = vi.mocked(hooks.useRecommendations)

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => { vi.clearAllMocks() })

describe('DiagnosticCard', () => {
  it('shows loading text while fetching', () => {
    mockedUseRecommendations.mockReturnValue({ isLoading: true, data: undefined } as any)
    wrap(<DiagnosticCard />)
    expect(screen.getByText(/loading your profile/i)).toBeInTheDocument()
  })

  it('shows baseline mode for first-time student', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: { user_id: 1, top_targets: [], threshold: 0.5 },
    } as any)
    wrap(<DiagnosticCard />)
    expect(screen.getByText('First-time baseline')).toBeInTheDocument()
    expect(screen.getByText(/baseline mode/i)).toBeInTheDocument()
    expect(screen.getByText(/20.30 questions/i)).toBeInTheDocument()
  })

  it('shows adaptive mode for returning student', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: {
        user_id: 1,
        top_targets: [{ focus_key: 'comma_splice', domain: 'grammar', weakness_score: 0.8 }],
        threshold: 0.5,
      },
    } as any)
    wrap(<DiagnosticCard />)
    expect(screen.getByText('Adaptive · weak areas')).toBeInTheDocument()
    expect(screen.getByText(/adaptive mode/i)).toBeInTheDocument()
    expect(screen.getByText('comma splice')).toBeInTheDocument()
  })

  it('always shows the Start Diagnostic button', () => {
    mockedUseRecommendations.mockReturnValue({ isLoading: true, data: undefined } as any)
    wrap(<DiagnosticCard />)
    expect(screen.getByRole('button', { name: /start diagnostic/i })).toBeInTheDocument()
  })

  it('navigates to /diagnostic on button click', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: { user_id: 1, top_targets: [], threshold: 0.5 },
    } as any)
    wrap(<DiagnosticCard />)
    fireEvent.click(screen.getByRole('button', { name: /start diagnostic/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/diagnostic')
  })
})
