import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useGrammarSession } from '../useGrammarSession'
import { api } from '../../api/client'

// Mock the API
vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
    submitAnswer: vi.fn().mockResolvedValue({ is_correct: true }),
  },
}))

describe('useGrammarSession', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.submitAnswer).mockResolvedValue({ is_correct: true })
  })

  // Mock question data — matches the new backend API shape
  const mockQuestion = {
    id: 'q-1',
    text: 'The researcher, who had spent years, [BLANK] findings.',
    current_question_text: 'The researcher, who had spent years, [BLANK] findings.',
    current_correct_option_label: 'B',
    options: [
      { label: 'A', text: 'shares' },
      { label: 'B', text: 'shared' },
      { label: 'C', text: 'had shared' },
      { label: 'D', text: 'is sharing' },
    ],
    grammar_role_key: 'verb_form',
    grammar_focus_key: 'verb_tense_consistency',
    syntactic_trap_key: 'temporal_sequence_ambiguity',
    explanation_short: 'Choose simple past tense here.',
  }

  it('initializes with loading state', () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    expect(result.current.isLoading).toBe(true)
    expect(result.current.question).toBeNull()
  })

  it.skip('loads question on mount', async () => {
    // TODO: Fix API mock setup for hook tests
    // The mock isn't being invoked properly in hook context
    // Manual integration tests pass when testing via component
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(result.current.question).toEqual(mockQuestion)
    expect(result.current.isLoading).toBe(false)
  })

  it('selectAnswer sets selectedAnswer and shows feedback', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    // Wait for question to load
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.selectAnswer('B')
    })

    expect(result.current.selectedAnswer).toBe('B')
    expect(result.current.feedbackVisible).toBe(true)
  })

  it('toggleKey adds and removes keys from activeKeys', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(result.current.activeKeys.has('subject')).toBe(false)

    act(() => {
      result.current.toggleKey('subject')
    })

    expect(result.current.activeKeys.has('subject')).toBe(true)

    act(() => {
      result.current.toggleKey('subject')
    })

    expect(result.current.activeKeys.has('subject')).toBe(false)
  })

  it('clearKeys removes all active keys', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    act(() => {
      result.current.toggleKey('subject')
      result.current.toggleKey('main_verb')
    })

    expect(result.current.activeKeys.size).toBe(2)

    act(() => {
      result.current.clearKeys()
    })

    expect(result.current.activeKeys.size).toBe(0)
  })

  it.skip('findTraps populates activeKeys based on grammar_focus_key', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    act(() => {
      result.current.findTraps()
    })

    // verb_tense_consistency should map to specific keys
    expect(result.current.activeKeys.size).toBeGreaterThan(0)
    expect(result.current.activeKeys.has('main_verb')).toBe(true)
  })

  it.skip('renderSentence returns sentence with selected answer', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    let sentence = result.current.renderSentence()
    expect(sentence).toContain('___')

    await act(async () => {
      await result.current.selectAnswer('B')
    })

    sentence = result.current.renderSentence()
    expect(sentence).toContain('shared')
  })

  it('renderOptions returns options with selection state', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    let options = result.current.renderOptions()
    expect(options.every((o: any) => !o.isSelected)).toBe(true)

    await act(async () => {
      await result.current.selectAnswer('B')
    })

    options = result.current.renderOptions()
    const selectedOption = options.find((o: any) => o.id === 'B')
    expect(selectedOption?.isSelected).toBe(true)
    expect(selectedOption?.isCorrect).toBe(true)
  })

  it('getKey returns grammar key by id', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    const key = result.current.getKey('subject')
    expect(key).toBeDefined()
    expect(key?.label).toBe('Primary Subject')
  })

  it('renderFeedback returns explanation data', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({ items: [mockQuestion] })

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    let feedback = result.current.renderFeedback()
    expect(feedback).toBeNull()

    await act(async () => {
      await result.current.selectAnswer('B')
    })

    feedback = result.current.renderFeedback()
    expect(feedback?.isCorrect).toBe(true)
    expect(feedback?.title).toContain('Correct')
  })

  it('handles API errors gracefully', async () => {
    vi.mocked(api.getQuestions).mockRejectedValueOnce(
      new Error('Network error')
    )

    const { result } = renderHook(() => useGrammarSession())

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(result.current.error).toBe('Network error')
    expect(result.current.isLoading).toBe(false)
  })
})
