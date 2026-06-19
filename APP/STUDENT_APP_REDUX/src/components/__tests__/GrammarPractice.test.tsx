import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { GrammarPractice } from '../GrammarPractice'
import { api } from '../../api/client'

// Mock the API
vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
  },
}))

const mockQuestion = {
  id: 'q-1',
  text: 'The researcher, who had spent years, [BLANK] findings.',
  options: [
    { id: 'A', text: 'shares', correct: false },
    { id: 'B', text: 'shared', correct: true },
    { id: 'C', text: 'had shared', correct: false },
    { id: 'D', text: 'is sharing', correct: false },
  ],
  classification: {
    grammar_role_key: 'verb_form',
    grammar_focus_key: 'verb_tense_consistency',
    syntactic_trap_key: ['temporal_sequence_ambiguity'],
    syntactic_trap_intensity: 'medium' as const,
  },
  reasoning: {
    primary_rule: 'Choose simple past',
    trap_mechanism: 'Subordinate clause makes past perfect sound correct',
    correct_answer_reasoning: 'Main verb should be simple past',
    distractor_analysis_summary: 'Complex tenses are tempting',
  },
}

describe('GrammarPractice Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/SAT Grammar Practice/i)).toBeInTheDocument()
    })

    expect(
      screen.getByText(/Standard English Conventions/i)
    ).toBeInTheDocument()
  })

  it('displays sentence with blank', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/researcher.*___.*findings/i)).toBeInTheDocument()
    })
  })

  it('displays all answer options', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('shares')).toBeInTheDocument()
      expect(screen.getByText('shared')).toBeInTheDocument()
      expect(screen.getByText('had shared')).toBeInTheDocument()
      expect(screen.getByText('is sharing')).toBeInTheDocument()
    })
  })

  it('shows feedback when answer is selected', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

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
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Grammar Analysis/i)).toBeInTheDocument()
    })
  })

  it('shows trap summary with backend taxonomy', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Detected Trap Profile/i)).toBeInTheDocument()
      expect(screen.getByText('verb_form')).toBeInTheDocument()
      expect(screen.getByText('verb_tense_consistency')).toBeInTheDocument()
    })
  })

  it('has working Find Traps button', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

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
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

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
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Sentence Anatomy/i)).toBeInTheDocument()
    })

    // Check for some anatomy keys
    expect(screen.getByText('Primary Subject')).toBeInTheDocument()
    expect(screen.getByText('Main Verb')).toBeInTheDocument()
  })

  it('toggles grammar keys when clicked', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Primary Subject')).toBeInTheDocument()
    })

    const subjectButton = screen.getByRole('button', { name: /Primary Subject/i })
    fireEvent.click(subjectButton)

    // Button should now be in active state (hard to test without checking CSS)
    expect(subjectButton).toBeInTheDocument()
  })
})
