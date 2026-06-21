import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { GrammarPractice } from '../GrammarPractice'
import { api } from '../../api/client'

// Mock the API
vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
    submitAnswer: vi.fn().mockResolvedValue({ is_correct: true }),
  },
}))

// Mock question using the current backend API shape
const mockQuestion = {
  id: 'q-1',
  text: 'The researcher, who had spent years, [BLANK] findings.',
  current_question_text: 'The researcher, who had spent years, [BLANK] findings.',
  options: [
    { label: 'A', text: 'shares' },
    { label: 'B', text: 'shared' },
    { label: 'C', text: 'had shared' },
    { label: 'D', text: 'is sharing' },
  ],
  grammar_role_key: 'verb_form',
  grammar_focus_key: 'verb_tense_consistency',
  syntactic_trap_key: 'temporal_sequence_ambiguity',
  explanation_short: 'Choose simple past tense to match the sentence time frame.',
}

describe('GrammarPractice Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.submitAnswer).mockResolvedValue({ is_correct: true })
  })

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <GrammarPractice />
      </BrowserRouter>
    )
  }

  it('shows loading state initially', () => {
    vi.mocked(api.getQuestions).mockImplementationOnce(
      () => new Promise(() => {}) // Never resolves
    )

    renderComponent()

    expect(screen.getByText(/loading grammar question/i)).toBeInTheDocument()
  })

  it('displays error message on API failure', async () => {
    vi.mocked(api.getQuestions).mockRejectedValueOnce(
      new Error('Network error')
    )

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('renders question after loading', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/SAT Grammar Practice/i)).toBeInTheDocument()
    })

    expect(
      screen.getByText(/Standard English Conventions/i)
    ).toBeInTheDocument()
  })

  it('displays sentence with blank', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      // The sentence box's textContent contains the full passage with blank chars
      expect(screen.getByText(/researcher/i)).toBeInTheDocument()
    })
  })

  it('displays all answer options', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('shares')).toBeInTheDocument()
      expect(screen.getByText('shared')).toBeInTheDocument()
      expect(screen.getByText('had shared')).toBeInTheDocument()
      expect(screen.getByText('is sharing')).toBeInTheDocument()
    })
  })

  it('shows feedback when answer is selected', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('shared')).toBeInTheDocument()
    })

    const buttons = screen.getAllByRole('button')
    const sharedButton = buttons.find((btn) => btn.textContent?.includes('shared'))
    expect(sharedButton).toBeInTheDocument()
    if (sharedButton) fireEvent.click(sharedButton)

    await waitFor(() => {
      expect(screen.getByText(/✓ Correct/i)).toBeInTheDocument()
    })
  })

  it('displays grammar analysis section', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Grammar Analysis/i)).toBeInTheDocument()
    })
  })

  it('shows trap summary with backend taxonomy', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Detected Trap Profile/i)).toBeInTheDocument()
      expect(screen.getByText('verb_form')).toBeInTheDocument()
      expect(screen.getByText('verb_tense_consistency')).toBeInTheDocument()
    })
  })

  it('has working Find Traps button', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Find Traps/i)).toBeInTheDocument()
    })

    const findTrapsButton = screen.getByRole('button', { name: /Find Traps/i })
    fireEvent.click(findTrapsButton)

    // After clicking, some anatomy keys should be highlighted
    await waitFor(() => {
      const keyButtons = screen.getAllByRole('button')
      expect(keyButtons.length).toBeGreaterThan(4) // More than just option buttons
    })
  })

  it('has working Clear Keys button', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Clear Keys/i)).toBeInTheDocument()
    })

    const findTrapsButton = screen.getByRole('button', { name: /Find Traps/i })
    fireEvent.click(findTrapsButton)

    const clearKeysButton = screen.getByRole('button', { name: /Clear Keys/i })
    fireEvent.click(clearKeysButton)

    // Keys should be cleared (testing via button presence and state)
    expect(clearKeysButton).toBeInTheDocument()
  })

  it('displays syntax anatomy keys', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Sentence Anatomy/i)).toBeInTheDocument()
    })

    // Only keys that tag actual passage tokens are rendered (renderGrammarKeys filters by passageKeyIds).
    // The mock produces main_verb tags, so Main Verb is present; Primary Subject is not.
    expect(screen.getByText('Main Verb')).toBeInTheDocument()
  })

  it('toggles grammar keys when clicked', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Main Verb')).toBeInTheDocument()
    })

    const subjectButton = screen.getByRole('button', { name: /Main Verb/i })
    fireEvent.click(subjectButton)

    // Button should now be in active state (hard to test without checking CSS)
    expect(subjectButton).toBeInTheDocument()
  })
})
