import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MixedPracticePage } from '../MixedPracticePage'
import { api } from '../../api/client'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
  },
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useSubmitAnswer: () => ({ mutate: vi.fn() }),
}))

const mockedApi = vi.mocked(api)

function renderPage(initialEntry = '/practice/mixed') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <MixedPracticePage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('MixedPracticePage', () => {
  it('renders a question from the items array (not a questions array)', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-1',
          current_question_text: 'Which choice best completes the sentence?',
          current_passage_text: null,
          options: [
            { label: 'A', text: 'Option A' },
            { label: 'B', text: 'Option B' },
          ],
          domain: 'grammar',
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Which choice best completes the sentence?')).toBeInTheDocument()
    )
    expect(screen.queryByText('No questions available right now.')).not.toBeInTheDocument()
  })
})
