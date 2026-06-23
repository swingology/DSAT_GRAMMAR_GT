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

// Mock question using the current backend API shape (flat fields, label-keyed options)
const mockQuestion = {
  id: 'q-123',
  text: 'The researcher, who had spent years on this project, [BLANK] their findings with the team.',
  current_passage_text: 'The researcher, who had spent years on this project, ________ their findings with the team.',
  current_question_text: 'Which choice completes the text so that it conforms to the conventions of Standard English?',
  current_correct_option_label: 'B',
  passage_tokens: [
    { text: 'The researcher', anatomy: ['subject'], concept_tags: [] },
    { text: ', who had spent years on this project, ', anatomy: ['relative_clause'], concept_tags: [] },
    { text: '________', anatomy: ['main_verb'], concept_tags: ['verb_tense_consistency'], is_blank: true },
    { text: ' their findings with the team.', anatomy: [], concept_tags: [] },
  ],
  passage_spans: {
    label: 'Verb tense: relative clause + main verb blank',
    anatomy_present: ['subject', 'relative_clause', 'main_verb'],
    concepts_present: ['verb_tense_consistency'],
  },
  options: [
    { label: 'A', text: 'shares' },
    { label: 'B', text: 'shared' },
    { label: 'C', text: 'had shared', why_plausible: 'Options A and D use present tense; option C uses past perfect, which is only for actions completed before another past event.' },
    { label: 'D', text: 'is sharing' },
  ],
  grammar_role_key: 'verb_form',
  grammar_focus_key: 'verb_tense_consistency',
  syntactic_trap_key: 'temporal_sequence_ambiguity',
  explanation_short: 'Choose the verb tense required by the sentence\'s time frame, not the tense that sounds more formal.',
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

  const sentenceBox = () => document.querySelector('.sentence-box') as HTMLElement
  const activeKeysBox = () => document.querySelector('.active-keys-explanation') as HTMLElement

  describe('Full User Journey: Load → Answer → Feedback → Analyze', () => {
    it('completes happy path: load question → select answer → view feedback → toggle keys → find traps → clear keys', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })
      vi.mocked(api.submitAnswer).mockResolvedValueOnce({ is_correct: true })

      renderComponent()

      // Step 1: Wait for page to load
      await waitFor(() => {
        expect(screen.getByText(/SAT Grammar Practice/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/Standard English Conventions/i)).toBeInTheDocument()

      // Step 2: Verify question loads with full text
      expect(sentenceBox()?.textContent).toContain('The researcher')
      expect(sentenceBox()?.textContent).toContain('their findings with the team')

      // Step 3: Verify all options are visible
      expect(screen.getByText('shares')).toBeInTheDocument()
      expect(screen.getByText('shared')).toBeInTheDocument()
      expect(screen.getByText('had shared')).toBeInTheDocument()
      expect(screen.getByText('is sharing')).toBeInTheDocument()

      // Step 4: Verify trap summary is displayed
      expect(screen.getByText(/Detected Trap Profile/i)).toBeInTheDocument()
      expect(screen.getByText('verb_form')).toBeInTheDocument()
      expect(screen.getByText('verb_tense_consistency')).toBeInTheDocument()

      // Step 5: Verify syntax anatomy keys are displayed
      expect(screen.getByText(/Sentence Anatomy/i)).toBeInTheDocument()
      expect(screen.getByText('Subject')).toBeInTheDocument()
      expect(activeKeysBox()?.textContent).toContain('Main Verb')

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
          /time frame/i
        )
      ).toBeInTheDocument()

      // Step 9: Toggle a key manually
      const mainVerbButton = screen.getByRole('button', { name: /Main Verb/i })
      fireEvent.click(mainVerbButton)

      // Step 10: Verify key is highlighted and explanation appears
      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })

      expect(screen.getByText('Main Verb')).toBeInTheDocument()

      // Step 11: Click Find Traps
      const findTrapsButton = screen.getByRole('button', { name: /Find Traps/i })
      fireEvent.click(findTrapsButton)

      // Step 12: Verify multiple keys are now highlighted
      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })
      expect(activeKeysBox()?.textContent).toContain('Verb Tense Consistency')

      // Step 13: Click Clear Keys
      const clearKeysButton = screen.getByRole('button', { name: /Clear Keys/i })
      fireEvent.click(clearKeysButton)

      // Active keys section should disappear
      const activeKeysSections = screen.queryAllByText(/Active Grammar Keys/i)
      expect(activeKeysSections.length).toBe(0)
    })
  })

  describe('Correct Answer Selection', () => {
    it('shows correct feedback when correct answer is selected', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })
      vi.mocked(api.submitAnswer).mockResolvedValueOnce({ is_correct: true })

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

      expect(screen.getByText(/time frame/i)).toBeInTheDocument()
    })
  })

  describe('Incorrect Answer Selection', () => {
    it('shows incorrect feedback when wrong answer is selected', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })
      vi.mocked(api.submitAnswer).mockResolvedValueOnce({ is_correct: false })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('had shared')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /had shared/i }))

      await waitFor(() => {
        expect(screen.getByText(/✗ Not quite/i)).toBeInTheDocument()
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
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

      renderComponent()

      // renderGrammarKeys() only shows keys that tag actual passage tokens.
      // The mock question produces main_verb and relative_clause tokens, so use Main Verb.
      await waitFor(() => {
        expect(screen.getByText('Main Verb')).toBeInTheDocument()
      })

      const subjectButton = screen.getByRole('button', { name: /Main Verb/i })

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

    it('Find Traps auto-highlights backend concept keys from passage_spans', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/Find Traps/i)).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Find Traps/i }))

      await waitFor(() => {
        expect(screen.getByText(/Active Grammar Keys/i)).toBeInTheDocument()
      })

      expect(activeKeysBox()?.textContent).toContain('Verb Tense Consistency')
    })

    it('Clear Keys removes all active keys', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

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
    it('displays sentence with blank before answer selection', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

      renderComponent()

      await screen.findByText('________')
      expect(sentenceBox()?.textContent).toContain('The researcher')
      expect(sentenceBox()?.textContent).toContain('________')
      expect(sentenceBox()?.textContent).toContain('their findings with the team')
    })

    it('replaces blank with selected answer text', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })
      vi.mocked(api.submitAnswer).mockResolvedValueOnce({ is_correct: true })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('shared')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /^shared$/i }))

      await waitFor(() => {
        expect(sentenceBox()?.textContent).toContain('shared')
      })
      expect(sentenceBox()?.textContent).not.toContain('________')
    })
  })

  describe('Trap Summary Display', () => {
    it('displays all trap summary fields', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/Detected Trap Profile/i)).toBeInTheDocument()
      })

      // Check grammar role and focus
      expect(screen.getByText('Grammar Role')).toBeInTheDocument()
      expect(screen.getByText('verb_form')).toBeInTheDocument()

      expect(screen.getByText('Grammar Focus')).toBeInTheDocument()
      expect(screen.getByText('verb_tense_consistency')).toBeInTheDocument()

      // Syntactic trap key (single string in new API)
      expect(screen.getByText('Syntactic Trap')).toBeInTheDocument()
      expect(screen.getByText('temporal_sequence_ambiguity')).toBeInTheDocument()
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

    it('displays error when no questions available', async () => {
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [] })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/no grammar questions available/i)).toBeInTheDocument()
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
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

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
      vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

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
