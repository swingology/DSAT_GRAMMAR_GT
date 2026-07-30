import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QuickPickPage } from '../QuickPickPage'
import * as quickPickHook from '../../hooks/useQuickPickQuestions'
import { useSubmitAnswer } from '../../hooks/useDashboardData'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
}))

vi.mock('../../hooks/useQuickPickQuestions', () => ({
  useQuickPickQuestions: vi.fn(),
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useSubmitAnswer: vi.fn(),
}))

const useQuickPickQuestions = vi.mocked(quickPickHook.useQuickPickQuestions)

function question(id: string) {
  return { id, current_question_text: `Question ${id}`, options: [{ label: 'A', text: 'Option A' }] }
}

function renderPage(search = '?domain=grammar&focus_key=verb_tense_consistency') {
  return render(
    <MemoryRouter initialEntries={[`/practice/quick${search}`]}>
      <QuickPickPage />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(useSubmitAnswer).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof useSubmitAnswer>)
})

describe('QuickPickPage', () => {
  it('shows a loading state', () => {
    useQuickPickQuestions.mockReturnValue({ questions: [], isLoading: true, isError: false, shortfallNote: null })
    renderPage()
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  it('shows an error state', () => {
    useQuickPickQuestions.mockReturnValue({ questions: [], isLoading: false, isError: true, shortfallNote: null })
    renderPage()
    expect(screen.getByText('Failed to load questions')).toBeInTheDocument()
  })

  it('reads domain and focus_key from the URL and passes them to the hook', () => {
    useQuickPickQuestions.mockReturnValue({ questions: [question('q1')], isLoading: false, isError: false, shortfallNote: null })
    renderPage('?domain=reading&focus_key=inference')
    expect(useQuickPickQuestions).toHaveBeenCalledWith('reading', 'inference')
  })

  it('shows the shortfall note when present', () => {
    useQuickPickQuestions.mockReturnValue({
      questions: [question('q1')],
      isLoading: false,
      isError: false,
      shortfallNote: 'Only 1 question available for this concept.',
    })
    renderPage()
    expect(screen.getByText('Only 1 question available for this concept.')).toBeInTheDocument()
  })

  it('advances through questions and shows a completion state at the end', () => {
    useQuickPickQuestions.mockReturnValue({
      questions: [question('q1'), question('q2')],
      isLoading: false,
      isError: false,
      shortfallNote: null,
    })
    renderPage()

    expect(screen.getByText('Question q1')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Option A'))
    fireEvent.click(screen.getByText('Next Question →'))
    expect(screen.getByText('Question q2')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Option A'))
    fireEvent.click(screen.getByText('Next Question →'))
    expect(screen.getByText('Session Complete')).toBeInTheDocument()
  })
})
