import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QuestionCard, type Question } from '../QuestionCard'
import { useSubmitAnswer } from '../../hooks/useDashboardData'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useSubmitAnswer: vi.fn(),
}))

const question: Question = {
  id: 'q-1',
  current_question_text: 'Which choice completes the text?',
  current_passage_text: 'A passage.',
  options: [
    { label: 'A', text: 'First option' },
    { label: 'B', text: 'Second option' },
  ],
  explanation_short: 'B is correct because...',
  grammar_focus_key: 'verb_tense_consistency',
  domain: 'grammar',
}

describe('QuestionCard', () => {
  const mutate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useSubmitAnswer).mockReturnValue({ mutate } as unknown as ReturnType<typeof useSubmitAnswer>)
  })

  it('renders domain, focus key, passage, and options', () => {
    render(<QuestionCard question={question} onNext={vi.fn()} sourceType="drill" />)
    expect(screen.getByText('grammar')).toBeInTheDocument()
    expect(screen.getByText('verb tense consistency')).toBeInTheDocument()
    expect(screen.getByText('A passage.')).toBeInTheDocument()
    expect(screen.getByText('First option')).toBeInTheDocument()
  })

  it('submits with the given sourceType when an option is chosen', async () => {
    mutate.mockImplementation((_data, { onSuccess }: any) => onSuccess({ is_correct: true }))
    render(<QuestionCard question={question} onNext={vi.fn()} sourceType="drill" />)

    fireEvent.click(screen.getByText('First option'))

    await waitFor(() => {
      expect(mutate).toHaveBeenCalledWith(
        expect.objectContaining({ question_id: 'q-1', selected_option_label: 'A', source_type: 'drill' }),
        expect.anything(),
      )
    })
  })

  it('shows Next Question button only after answering', () => {
    render(<QuestionCard question={question} onNext={vi.fn()} sourceType="drill" />)
    expect(screen.queryByText('Next Question →')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('First option'))
    expect(screen.getByText('Next Question →')).toBeInTheDocument()
  })
})
