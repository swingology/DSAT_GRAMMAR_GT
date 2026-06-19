import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from '../../pages/DashboardPage'

const motionEl = (tag: string) =>
  ({ children, ...props }: any) => {
    const { initial, animate, transition, ...rest } = props
    return React.createElement(tag, rest, children)
  }

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => motionEl(tag) }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
  type: undefined,
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useRecommendations: vi.fn().mockReturnValue({
    isLoading: false,
    isError: false,
    data: { user_id: 1, top_targets: [], threshold: 0.5 },
  }),
  useStats: vi.fn().mockReturnValue({
    isLoading: false,
    data: undefined,
  }),
  useMissedQuestions: vi.fn().mockReturnValue({ isLoading: false, data: undefined }),
}))

function renderDashboard() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('DashboardPage', () => {
  it('renders the app header', () => {
    renderDashboard()
    expect(screen.getByText('DSAT Prep')).toBeInTheDocument()
  })

  it('renders the three action cards', () => {
    renderDashboard()
    expect(screen.getByText('Practice')).toBeInTheDocument()
    expect(screen.getByText('Diagnostic Test')).toBeInTheDocument()
    expect(screen.getByText('Practice Test')).toBeInTheDocument()
  })

  it('renders the progress section headings', () => {
    renderDashboard()
    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    expect(screen.getByText('Concept Weakness')).toBeInTheDocument()
  })

  it('shows first-time welcome when no top_targets', () => {
    renderDashboard()
    // With empty top_targets, HeroBanner should show the first-time variant
    expect(screen.getByText('Welcome to DSAT Prep')).toBeInTheDocument()
    expect(screen.getByText('Start Diagnostic →')).toBeInTheDocument()
  })

  it('renders start session section', () => {
    renderDashboard()
    expect(screen.getByText('Start a session')).toBeInTheDocument()
  })
})
