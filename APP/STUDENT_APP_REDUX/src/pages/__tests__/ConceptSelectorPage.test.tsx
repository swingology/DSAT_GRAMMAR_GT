import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ConceptSelectorPage } from '../ConceptSelectorPage'

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
  useRecommendations: vi.fn().mockReturnValue({
    isLoading: false,
    isError: false,
    data: {
      user_id: 1,
      top_targets: [
        {
          domain: 'grammar', focus_key: 'comma_splice', skill_family_key: null,
          grammar_role_key: 'sentence_structure', difficulty: 'medium',
          weakness_score: 0.8, miss_count: 4, attempt_count: 5, miss_rate: 0.8,
          days_since_last_attempt: 2, inventory_unseen: 10, inventory_below_threshold: false,
        },
      ],
      threshold: 5,
    },
  }),
  useStimulusCounts: vi.fn().mockReturnValue({
    isLoading: false,
    isError: false,
    data: [
      { stimulus_mode_key: 'sentence_only', count: 559 },
      { stimulus_mode_key: 'prose_plus_graph', count: 43 },
      { stimulus_mode_key: 'poem', count: 9 },
    ],
  }),
}))

function wrap(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

beforeEach(() => { vi.clearAllMocks() })

describe('ConceptSelectorPage', () => {
  it('shows the By Weakness tab by default', () => {
    wrap(<ConceptSelectorPage />)
    expect(screen.getByText('comma splice')).toBeInTheDocument()
    expect(screen.queryByText('Prose + Graph')).not.toBeInTheDocument()
  })

  it('switches to the By Type tab and lists stimulus types by count descending', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByText('By Type'))

    expect(screen.getByText('Sentence Only')).toBeInTheDocument()
    expect(screen.getByText('Prose + Graph')).toBeInTheDocument()
    expect(screen.getByText('Poem')).toBeInTheDocument()
    expect(screen.queryByText('comma splice')).not.toBeInTheDocument()

    const labels = screen.getAllByText(/Sentence Only|Prose \+ Graph|Poem/).map((el) => el.textContent)
    expect(labels).toEqual(['Sentence Only', 'Prose + Graph', 'Poem'])
  })

  it('shows the count for each stimulus type', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByText('By Type'))
    expect(screen.getByText('43 questions')).toBeInTheDocument()
  })

  it('navigates to mixed practice with the stimulus_mode_key on tap', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByText('By Type'))
    fireEvent.click(screen.getByText('Prose + Graph'))
    expect(mockNavigate).toHaveBeenCalledWith('/practice/mixed?stimulus_mode_key=prose_plus_graph&limit=10')
  })

  it('navigates to the drill route when the row body is tapped', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByText('comma splice'))
    expect(mockNavigate).toHaveBeenCalledWith(
      '/practice/grammar?focus_key=comma_splice&domain=grammar&limit=10'
    )
  })

  it('navigates to the quick pick route when the quick pick action is tapped', () => {
    wrap(<ConceptSelectorPage />)
    fireEvent.click(screen.getByRole('button', { name: /Quick Pick/i }))
    expect(mockNavigate).toHaveBeenCalledWith(
      '/practice/quick?domain=grammar&focus_key=comma_splice'
    )
  })
})
