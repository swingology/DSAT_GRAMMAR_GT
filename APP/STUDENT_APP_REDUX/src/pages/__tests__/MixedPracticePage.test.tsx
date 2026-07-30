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

vi.mock('../../auth/authStore', () => ({
  // Non-empty so the seen-exclusion user_token is forwarded; the real getUserToken
  // reads profile/env/localStorage and can be '' for an anonymous session.
  getUserToken: vi.fn(() => 'tok-test-uuid'),
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

  it('forwards stimulus_mode_key from the URL to getQuestions', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-2',
          current_question_text: 'What does the graph show?',
          current_passage_text: null,
          options: [{ label: 'A', text: 'Option A' }],
          domain: 'reading',
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage('/practice/mixed?stimulus_mode_key=prose_plus_graph')

    await waitFor(() => expect(mockedApi.getQuestions).toHaveBeenCalled())
    expect(mockedApi.getQuestions).toHaveBeenCalledWith(
      expect.objectContaining({ stimulus_mode_key: 'prose_plus_graph' })
    )
  })

  it('omits stimulus_mode_key from getQuestions when absent from the URL', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-3',
          current_question_text: 'Any question.',
          current_passage_text: null,
          options: [{ label: 'A', text: 'Option A' }],
          domain: 'grammar',
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage('/practice/mixed')

    await waitFor(() => expect(mockedApi.getQuestions).toHaveBeenCalled())
    const callArgs = mockedApi.getQuestions.mock.calls[0][0]
    expect(callArgs).not.toHaveProperty('stimulus_mode_key')
  })

  it('passes randomize and user_token so the backend shuffles and excludes seen questions', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-4',
          current_question_text: 'Shuffled question.',
          current_passage_text: null,
          options: [{ label: 'A', text: 'Option A' }],
          domain: 'grammar',
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage('/practice/mixed')

    await waitFor(() => expect(mockedApi.getQuestions).toHaveBeenCalled())
    expect(mockedApi.getQuestions).toHaveBeenCalledWith(
      expect.objectContaining({ randomize: true, user_token: 'tok-test-uuid' })
    )
  })

  it('renders passage text and stimulus asset images when present', async () => {
    mockedApi.getQuestions.mockResolvedValue({
      items: [
        {
          id: 'q-5',
          current_question_text: 'According to the graph, which year peaked?',
          current_passage_text: 'The chart below tracks annual output from 2010 to 2024.',
          options: [{ label: 'A', text: 'Option A' }],
          domain: 'reading',
          stimulus_assets: [
            {
              id: 'asset-1',
              stimulus_type: 'graph',
              url: '/api/stimulus-assets/asset-1',
              title: 'Annual Output',
              source_page_number: 3,
            },
          ],
        },
      ],
      inventory: { matching_target_total: 1, matching_unseen: 1, served: 1, includes_generated: false, below_threshold: false, threshold: 5 },
    })

    renderPage('/practice/mixed')

    await waitFor(() =>
      expect(screen.getByText('According to the graph, which year peaked?')).toBeInTheDocument()
    )
    expect(screen.getByText('The chart below tracks annual output from 2010 to 2024.')).toBeInTheDocument()
    const img = screen.getByRole('img') as HTMLImageElement
    expect(img.src).toContain('/api/stimulus-assets/asset-1')
    expect(img.alt).toContain('Annual Output')
    expect(screen.getByText(/Annual Output.*p\. 3/)).toBeInTheDocument()
  })
})
