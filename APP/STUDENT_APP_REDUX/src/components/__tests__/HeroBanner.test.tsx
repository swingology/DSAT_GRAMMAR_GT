import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HeroBanner } from '../dashboard/HeroBanner'
import * as hooks from '../../hooks/useDashboardData'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => vi.fn() }
})

vi.mock('../../hooks/useDashboardData', () => ({
  useRecommendations: vi.fn(),
  useStats: vi.fn(),
}))

const mockedUseRecommendations = vi.mocked(hooks.useRecommendations)
const mockedUseStats = vi.mocked(hooks.useStats)

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => { vi.clearAllMocks() })

describe('HeroBanner', () => {
  it('shows loading skeleton while recommendations are fetching', () => {
    mockedUseRecommendations.mockReturnValue({ isLoading: true, data: undefined } as any)
    mockedUseStats.mockReturnValue({ isLoading: false, data: undefined } as any)
    wrap(<HeroBanner />)
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows first-time welcome when top_targets is empty', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: { user_id: 1, top_targets: [], threshold: 0.5 },
    } as any)
    mockedUseStats.mockReturnValue({ isLoading: false, data: undefined } as any)
    wrap(<HeroBanner />)
    expect(screen.getByText('Welcome to DSAT Prep')).toBeInTheDocument()
    expect(screen.getByText(/start with a diagnostic/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start diagnostic/i })).toBeInTheDocument()
  })

  it('shows first-time welcome when data is undefined (API error)', () => {
    mockedUseRecommendations.mockReturnValue({ isLoading: false, data: undefined } as any)
    mockedUseStats.mockReturnValue({ isLoading: false, data: undefined } as any)
    wrap(<HeroBanner />)
    expect(screen.getByText('Welcome to DSAT Prep')).toBeInTheDocument()
  })

  it('shows returning student stats when top_targets exist', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: {
        user_id: 1,
        top_targets: [{ focus_key: 'comma_splice', domain: 'grammar', weakness_score: 0.8 }],
        threshold: 0.5,
      },
    } as any)
    mockedUseStats.mockReturnValue({ isLoading: false, data: undefined } as any)
    wrap(<HeroBanner />)
    expect(screen.getByText('Your Progress')).toBeInTheDocument()
    expect(screen.getByText('Day streak')).toBeInTheDocument()
    expect(screen.getByText('This week')).toBeInTheDocument()
    expect(screen.getByText('Accuracy')).toBeInTheDocument()
    expect(screen.getByText('Top weak area')).toBeInTheDocument()
  })

  it('shows top concept name in the focus area line', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: {
        user_id: 1,
        top_targets: [{ focus_key: 'transition_logic', domain: 'grammar', weakness_score: 0.9 }],
        threshold: 0.5,
      },
    } as any)
    mockedUseStats.mockReturnValue({ isLoading: false, data: undefined } as any)
    wrap(<HeroBanner />)
    expect(screen.getAllByText('transition logic').length).toBeGreaterThanOrEqual(1)
  })

  it('shows accuracy from stats when available', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: {
        user_id: 1,
        top_targets: [{ focus_key: 'comma_splice', domain: 'grammar', weakness_score: 0.7 }],
        threshold: 0.5,
      },
    } as any)
    mockedUseStats.mockReturnValue({
      isLoading: false,
      data: { user_id: 1, total_attempts: 50, correct_count: 38, accuracy: 0.76 },
    } as any)
    wrap(<HeroBanner />)
    expect(screen.getByText('76%')).toBeInTheDocument()
  })
})
