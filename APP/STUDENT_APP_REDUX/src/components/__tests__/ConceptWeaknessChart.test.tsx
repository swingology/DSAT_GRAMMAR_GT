import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConceptWeaknessChart } from '../dashboard/ConceptWeaknessChart'
import * as hooks from '../../hooks/useDashboardData'

vi.mock('../../hooks/useDashboardData', () => ({
  useRecommendations: vi.fn(),
}))

const mockedUseRecommendations = vi.mocked(hooks.useRecommendations)

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const mockTarget = (focusKey: string, score: number) => ({
  domain: 'grammar',
  focus_key: focusKey,
  weakness_score: score,
  miss_count: 2,
  attempt_count: 4,
  miss_rate: 0.5,
  days_since_last_attempt: 3,
  inventory_unseen: 0,
  inventory_below_threshold: false,
  difficulty: 'medium',
})

beforeEach(() => { vi.clearAllMocks() })

describe('ConceptWeaknessChart', () => {
  it('shows loading skeletons while fetching', () => {
    mockedUseRecommendations.mockReturnValue({ isLoading: true, data: undefined } as any)
    wrap(<ConceptWeaknessChart />)
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('shows empty state when no targets', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: { user_id: 1, top_targets: [], threshold: 0.5 },
    } as any)
    wrap(<ConceptWeaknessChart />)
    expect(screen.getByText(/no data yet/i)).toBeInTheDocument()
  })

  it('renders a bar row for each target', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: {
        user_id: 1,
        top_targets: [
          mockTarget('comma_splice', 0.8),
          mockTarget('transition_logic', 0.5),
        ],
        threshold: 0.5,
      },
    } as any)
    wrap(<ConceptWeaknessChart />)
    expect(screen.getByText('comma splice')).toBeInTheDocument()
    expect(screen.getByText('transition logic')).toBeInTheDocument()
  })

  it('caps at 8 targets even if more are provided', () => {
    const targets = Array.from({ length: 10 }, (_, i) =>
      mockTarget(`focus_${i}`, 0.9 - i * 0.05)
    )
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: { user_id: 1, top_targets: targets, threshold: 0.5 },
    } as any)
    wrap(<ConceptWeaknessChart />)
    // Only first 8 should be rendered
    expect(screen.getByText('focus 0')).toBeInTheDocument()
    expect(screen.getByText('focus 7')).toBeInTheDocument()
    expect(screen.queryByText('focus 8')).not.toBeInTheDocument()
  })

  it('shows percentage score for each concept', () => {
    mockedUseRecommendations.mockReturnValue({
      isLoading: false,
      data: {
        user_id: 1,
        top_targets: [mockTarget('comma_splice', 0.75)],
        threshold: 0.5,
      },
    } as any)
    wrap(<ConceptWeaknessChart />)
    expect(screen.getByText('75%')).toBeInTheDocument()
  })
})
