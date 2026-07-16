import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ReviewMissedPage } from '../ReviewMissedPage'
import * as reviewHooks from '../../hooks/useReviewData'
import type { ReviewQuestionItem } from '../../types'

vi.mock('../../hooks/useReviewData', () => ({
  useReviewQuestions: vi.fn(),
  useReviewFilters: vi.fn(),
}))

const useReviewQuestions = vi.mocked(reviewHooks.useReviewQuestions)
const useReviewFilters = vi.mocked(reviewHooks.useReviewFilters)

const question: ReviewQuestionItem = {
  question_id: 'q-1',
  passage_text: 'Passage one.',
  paired_passage_text: 'Passage two.',
  underlined_text: null,
  question_text: 'Which option is correct?',
  options: [
    { label: 'A', text: 'First option', is_correct: false },
    { label: 'B', text: 'Second option', is_correct: true },
  ],
  correct_option_label: 'B',
  explanation: 'B follows from the passage.',
  user_answer: 'A',
  domain: 'reading',
  focus_key: 'inference',
  focus_key_source: 'reading_focus_key',
  stem_type_key: 'inference',
  difficulty: 'low',
  content_origin: 'official',
  source_test_name: 'Bluebook 1',
  source_section_code: 'RW',
  source_module_code: 'M1',
  source_question_number: 1,
  source_type: 'practice_test',
  source_types: ['practice_test'],
  miss_count: 2,
  last_missed_at: '2026-07-16T00:00:00Z',
}

const facets = {
  source_types: ['practice_test', 'drill'],
  source_test_names: ['Bluebook 1'],
  source_section_codes: ['RW'],
  source_module_codes: ['M1'],
  domains: ['reading', 'grammar'],
  focus_keys: ['inference'],
  stem_type_keys: ['inference'],
  difficulties: ['low', 'medium'],
  content_origins: ['official', 'generated'],
}

function queryResult(overrides: Record<string, unknown> = {}) {
  return {
    data: { items: [question], total: 11, page: 1, page_size: 10, has_more: true },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof reviewHooks.useReviewQuestions>
}

function renderPage() {
  return render(<MemoryRouter><ReviewMissedPage /></MemoryRouter>)
}

beforeEach(() => {
  vi.clearAllMocks()
  useReviewFilters.mockReturnValue({ data: facets } as ReturnType<typeof reviewHooks.useReviewFilters>)
  useReviewQuestions.mockReturnValue(queryResult())
})

describe('ReviewMissedPage', () => {
  it('shows loading, error, and empty states', () => {
    useReviewQuestions.mockReturnValue(queryResult({ data: undefined, isLoading: true }))
    const view = renderPage()
    expect(screen.getByLabelText('Loading missed questions')).toBeInTheDocument()

    useReviewQuestions.mockReturnValue(queryResult({ data: undefined, isError: true }))
    view.rerender(<MemoryRouter><ReviewMissedPage /></MemoryRouter>)
    expect(screen.getByText('Could not load missed questions')).toBeInTheDocument()

    useReviewQuestions.mockReturnValue(queryResult({
      data: { items: [], total: 0, page: 1, page_size: 10, has_more: false },
    }))
    view.rerender(<MemoryRouter><ReviewMissedPage /></MemoryRouter>)
    expect(screen.getByText('No missed questions found')).toBeInTheDocument()
  })

  it('resets pagination when a filter changes', () => {
    renderPage()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(useReviewQuestions).toHaveBeenLastCalledWith({}, 2, 10)

    fireEvent.change(screen.getByLabelText('Domain'), { target: { value: 'grammar' } })
    expect(useReviewQuestions).toHaveBeenLastCalledWith({ domain: 'grammar' }, 1, 10)
  })

  it('reveals passage and answer details only on demand', () => {
    renderPage()
    expect(screen.queryByText('Passage one.')).not.toBeInTheDocument()
    expect(screen.queryByText('Correct answer: B')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Passage/ }))
    expect(screen.getByText('Passage one.')).toBeInTheDocument()
    expect(screen.getByText('Passage two.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Show answer' }))
    expect(screen.getByText('Correct answer: B')).toBeInTheDocument()
    expect(screen.getByText('B follows from the passage.')).toBeInTheDocument()
  })

  it('offers only backend source facets in canonical order', () => {
    renderPage()
    const sourceButtons = screen.getByRole('group', { name: 'Source' }).querySelectorAll('button')
    expect(Array.from(sourceButtons).map(button => button.textContent)).toEqual([
      'All', 'Practice Test', 'Drill',
    ])
  })
})
