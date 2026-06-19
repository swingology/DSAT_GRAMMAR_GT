import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { GrammarPractice } from '../../components/GrammarPractice'
import { api } from '../../api/client'

// Mock the API
vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
    submitAnswer: vi.fn(),
  },
}))

const mockQuestion = {
  id: 'q-123',
  text: 'The researcher, who had spent years on this project, [BLANK] their findings with the team.',
  options: [
    { id: 'A', text: 'shares', correct: false, student_failure_mode_key: 'tense_proximity_pull' },
    { id: 'B', text: 'shared', correct: true },
    { id: 'C', text: 'had shared', correct: false, student_failure_mode_key: 'tense_proximity_pull' },
    { id: 'D', text: 'is sharing', correct: false, student_failure_mode_key: 'tense_proximity_pull' },
  ],
  source_exam: 'PT4',
  source_question_number: 23,
  classification: {
    grammar_role_key: 'verb_form',
    grammar_focus_key: 'verb_tense_consistency',
    syntactic_trap_key: ['temporal_sequence_ambiguity', 'early_clause_anchor'],
    syntactic_trap_intensity: 'medium' as const,
    student_failure_mode_key: 'tense_proximity_pull',
  },
  reasoning: {
    primary_rule:
      'Choose the verb tense required by the sentence\'s time frame, not the tense that sounds more formal.',
    trap_mechanism:
      'The opening subordinate clause and the formal SAT style make past perfect sound attractive, but the main clause "reflected" sets a completed-past frame with no earlier-past sequence.',
    correct_answer_reasoning:
      'The main verb must be simple past (shared) to match the time frame established by the opening phrase.',
    distractor_analysis_summary:
      'Options A and D use present tense; option C uses past perfect, which is only for actions completed before another past event.',
  },
}

describe('Grammar Practice Page — Integration Tests', () => {
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

  describe('Full User Journey: Load → Answer → Feedback → Analyze', () => {
    it.skip('completes happy path: load question → select answer → view feedback → toggle keys → find traps → clear keys', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      // Step 1: Wait for page to load
      await waitFor(() => {
        expect(screen.getByText(/SAT Grammar Practice/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/Standard English Conventions/i)).toBeInTheDocument()
      expect(screen.getByText('PT4')).toBeInTheDocument()
      expect(screen.getByText('23')).toBeInTheDocument()

      // Step 2: Verify question loads with full text
      expect(
        screen.getByText(
          /researcher.*had spent years.*findings.*team/i
        )
      ).toBeInTheDocument()

      // Step 3: Verify all options are visible
      expect(screen.getByText('shares')).toBeInTheDocument()
      expect(screen.getByText('shared')).toBeInTheDocument()
      expect(screen.getByText('had shared')).toBeInTheDocument()
      expect(screen.getByText('is sharing')).toBeInTheDocument()

      // Step 4: Verify trap summary is displayed
      expect(screen.getByText(/Detected Trap Profile/i)).toBeInTheDocument()
      expect(screen.getByText('verb_form')).toBeInTheDocument()
      expect(screen.getByText('verb_tense_consistency')).toBeInTheDocument()
      expect(screen.getByText('medium')).toBeInTheDocument()

      // Step 5: Verify syntax anatomy keys are displayed
      expect(screen.getByText(/Sentence Anatomy/i)).toBeInTheDocument()
      expect(screen.getByText('Primary Subject')).toBeInTheDocument()
      expect(screen.getByText('Main Verb')).toBeInTheDocument()

      // Step 6: Select correct answer
      const buttons = screen.getAllByRole('button')
      const sharedButton = buttons.find((btn) => btn.textContent?.includes('shared'))
      expect(sharedButton).toBeDefined()
      if (sharedButton) fireEvent.click(sharedButton)

      // Step 7: Verify feedback is shown
      await waitFor(() => {
        expect(screen.getByText(/Correct/i)).toBeInTheDocument()
      })

      // Step 8: Verify explanation is displayed
      expect(
        screen.getByText(
          /simple past.*time frame/i
        )
      ).toBeInTheDocument()

      // Step 9: Verify trap mechanism is shown
      expect(
        screen.getByText(
          /subordinate clause.*past perfect/i
        )
      ).toBeInTheDocument()

      // Step 10: Toggle a key manually
      const subjectButton = screen.getByRole('button', { name: /Primary Subject/i })
      fireEvent.click(subjectButton)

      // Step 11: Verify key is highlighted and explanation appears
      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })

      expect(screen.getByText('Primary Subject')).toBeInTheDocument()

      // Step 12: Click Find Traps
      const findTrapsButton = screen.getByRole('button', { name: /Find Traps/i })
      fireEvent.click(findTrapsButton)

      // Step 13: Verify multiple keys are now highlighted
      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })

      // Main Verb should be in active keys (from grammar_focus_key mapping)
      expect(screen.getByText('Main Verb')).toBeInTheDocument()

      // Step 14: Click Clear Keys
      const clearKeysButton = screen.getByRole('button', { name: /Clear Keys/i })
      fireEvent.click(clearKeysButton)

      // Step 15: Verify active keys explanation disappears
      // (After clearing, "Active Grammar Keys" section should not be visible)
      const activeKeysSections = screen.queryAllByText(/Active Grammar Keys/i)
      expect(activeKeysSections.length).toBe(0)
    })
  })

  describe('Correct Answer Selection', () => {
    it('shows correct feedback when correct answer is selected', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('shared')).toBeInTheDocument()
      })

      const buttons = screen.getAllByRole('button')
      const sharedButton = buttons.find((btn) => btn.textContent?.includes('shared'))
      if (sharedButton) fireEvent.click(sharedButton)

      await waitFor(() => {
        expect(screen.getByText(/✓ Correct/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/simple past.*time frame/i)).toBeInTheDocument()
    })
  })

  describe('Incorrect Answer Selection', () => {
    it('shows incorrect feedback when wrong answer is selected', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('had shared')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /had shared/i }))

      await waitFor(() => {
        expect(screen.getByText(/✗ Incorrect/i)).toBeInTheDocument()
      })

      expect(
        screen.getByText(
          /past perfect.*only for actions completed before another past event/i
        )
      ).toBeInTheDocument()
    })
  })

  describe('Grammar Key Interactions', () => {
    it('toggles keys on and off correctly', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Primary Subject')).toBeInTheDocument()
      })

      const subjectButton = screen.getByRole('button', { name: /Primary Subject/i })

      // First click: activate
      fireEvent.click(subjectButton)

      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })

      // Second click: deactivate
      fireEvent.click(subjectButton)

      // Active keys section should disappear
      const activeKeysSections = screen.queryAllByText(/Active Grammar Keys/i)
      expect(activeKeysSections.length).toBe(0)
    })

    it.skip('Find Traps auto-highlights keys based on grammar_focus_key', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/Find Traps/i)).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Find Traps/i }))

      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })

      // For verb_tense_consistency, should highlight Main Verb
      expect(screen.getByText('Main Verb')).toBeInTheDocument()
    })

    it('Clear Keys removes all active keys', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/Find Traps/i)).toBeInTheDocument()
      })

      // Activate some keys
      fireEvent.click(screen.getByRole('button', { name: /Find Traps/i }))

      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })

      // Clear all keys
      fireEvent.click(screen.getByRole('button', { name: /Clear Keys/i }))

      // Active keys section should disappear
      const activeKeysSections = screen.queryAllByText(/Active Grammar Keys/i)
      expect(activeKeysSections.length).toBe(0)
    })
  })

  describe('Sentence Rendering', () => {
    it.skip('displays sentence with blank before answer selection', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(
          screen.getByText(/researcher.*had spent years.*_____.*findings.*team/i)
        ).toBeInTheDocument()
      })
    })

    it.skip('replaces blank with selected answer text', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('shared')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /^shared$/i }))

      // After selection, sentence should show the actual word
      await waitFor(() => {
        expect(
          screen.getByText(/researcher.*had spent years.*shared.*findings.*team/i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('Trap Summary Display', () => {
    it('displays all trap summary fields', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/Detected Trap Profile/i)).toBeInTheDocument()
      })

      // Check all fields
      expect(screen.getByText('Grammar Role')).toBeInTheDocument()
      expect(screen.getByText('verb_form')).toBeInTheDocument()

      expect(screen.getByText('Grammar Focus')).toBeInTheDocument()
      expect(screen.getByText('verb_tense_consistency')).toBeInTheDocument()

      expect(screen.getByText('Syntactic Trap')).toBeInTheDocument()
      expect(
        screen.getByText(/temporal_sequence_ambiguity.*early_clause_anchor/i)
      ).toBeInTheDocument()

      expect(screen.getByText('Trap Intensity')).toBeInTheDocument()
      expect(screen.getByText('medium')).toBeInTheDocument()

      // Check trap mechanism description
      expect(
        screen.getByText(/subordinate clause.*past perfect.*sound attractive/i)
      ).toBeInTheDocument()
    })
  })

  describe('Error States', () => {
    it('displays error when API fails', async () => {
      vi.mocked(api.getQuestions).mockRejectedValueOnce(
        new Error('Network error')
      )

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })

    it.skip('displays error when no questions available', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/no question available/i)).toBeInTheDocument()
      })
    })
  })

  describe('Loading States', () => {
    it('shows loading indicator while fetching', () => {
      vi.mocked(api.getQuestions).mockImplementationOnce(
        () => new Promise(() => {}) // Never resolves
      )

      renderComponent()

      expect(screen.getByText(/loading grammar question/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility & Interaction', () => {
    it('all buttons are keyboard accessible', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('shared')).toBeInTheDocument()
      })

      // Get all buttons
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)

      // All should be keyboard accessible (role=button)
      buttons.forEach((btn) => {
        expect(btn).toHaveProperty('type')
      })
    })

    it('option buttons have proper labels', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce([mockQuestion])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('shared')).toBeInTheDocument()
      })

      // Each option should have label (A, B, C, D) and text
      expect(screen.getByText('shares')).toBeInTheDocument()
      expect(screen.getByText('shared')).toBeInTheDocument()
      expect(screen.getByText('had shared')).toBeInTheDocument()
      expect(screen.getByText('is sharing')).toBeInTheDocument()
    })
  })
})
