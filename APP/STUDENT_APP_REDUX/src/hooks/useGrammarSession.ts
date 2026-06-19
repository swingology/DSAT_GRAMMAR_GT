import { useState, useEffect, useCallback } from 'react'
import { SYNTAX_ANATOMY_KEYS } from '../data/syntaxAnatomyKeys'
import type {
  GrammarSessionState,
  SyntaxAnatomyKey,
} from '../types/grammar'
import { api } from '../api/client'

export function useGrammarSession() {
  const [state, setState] = useState<GrammarSessionState>({
    question: null,
    selectedAnswer: null,
    activeKeys: new Set(),
    feedbackVisible: false,
    isLoading: true,
    error: null,
  })

  // Fetch initial question on mount
  useEffect(() => {
    const fetchQuestion = async () => {
      try {
        setState((prev) => ({ ...prev, isLoading: true, error: null }))
        const questions = await api.getQuestions({
          domain: 'verbal',
          focus: 'grammar',
          limit: 1,
        })
        if (questions && questions.length > 0) {
          setState((prev) => ({
            ...prev,
            question: questions[0],
            isLoading: false,
          }))
        } else {
          setState((prev) => ({
            ...prev,
            error: 'No grammar questions available',
            isLoading: false,
          }))
        }
      } catch (err) {
        setState((prev) => ({
          ...prev,
          error: err instanceof Error ? err.message : 'Failed to fetch question',
          isLoading: false,
        }))
      }
    }

    fetchQuestion()
  }, [])

  // ─────────────────────────────────────────────────────────────────
  // 11 Core Functions (from component breakdown)
  // ─────────────────────────────────────────────────────────────────

  /**
   * 1. renderSentence()
   * Returns the sentence text with selected answer highlighted
   */
  const renderSentence = useCallback(() => {
    if (!state.question) return ''

    // Simple implementation: replace [BLANK] with selected answer or "___"
    const answerText = state.selectedAnswer
      ? state.question.options.find((o) => o.id === state.selectedAnswer)?.text
      : '___'

    return state.question.text.replace('[BLANK]', answerText || '___')
  }, [state.question, state.selectedAnswer])

  /**
   * 2. renderOptions()
   * Returns array of options with selected state
   */
  const renderOptions = useCallback(() => {
    if (!state.question) return []

    return state.question.options.map((option) => ({
      ...option,
      isSelected: option.id === state.selectedAnswer,
      isCorrect: option.correct && state.feedbackVisible,
      isIncorrect:
        !option.correct &&
        state.selectedAnswer === option.id &&
        state.feedbackVisible,
    }))
  }, [state.question, state.selectedAnswer, state.feedbackVisible])

  /**
   * 3. renderGrammarKeys()
   * Returns grouped syntax anatomy keys
   */
  const renderGrammarKeys = useCallback(() => {
    const groups = [...new Set(SYNTAX_ANATOMY_KEYS.map((key) => key.group))]

    return groups.map((group) => ({
      group,
      keys: SYNTAX_ANATOMY_KEYS.filter((key) => key.group === group).sort(
        (a, b) => b.priority - a.priority
      ),
      activeKeys: SYNTAX_ANATOMY_KEYS.filter(
        (key) => key.group === group && state.activeKeys.has(key.id)
      ),
    }))
  }, [state.activeKeys])

  /**
   * 4. renderTrapSummary()
   * Returns trap analysis from backend classification
   */
  const renderTrapSummary = useCallback(() => {
    if (!state.question) return null

    const { classification, reasoning } = state.question
    const trapKeys = Array.isArray(classification.syntactic_trap_key)
      ? classification.syntactic_trap_key
      : [classification.syntactic_trap_key]

    return {
      grammarRole: classification.grammar_role_key,
      grammarFocus: classification.grammar_focus_key,
      trapKeys,
      trapIntensity: classification.syntactic_trap_intensity,
      trapMechanism: reasoning.trap_mechanism,
    }
  }, [state.question])

  /**
   * 5. renderExplanations()
   * Returns explanation text based on correctness
   */
  const renderExplanations = useCallback(() => {
    if (!state.question || !state.selectedAnswer) return null

    const selectedOption = state.question.options.find(
      (o) => o.id === state.selectedAnswer
    )
    const isCorrect = selectedOption?.correct ?? false
    const { reasoning } = state.question

    return {
      isCorrect,
      title: isCorrect ? '✓ Correct!' : '✗ Incorrect',
      explanation: isCorrect
        ? reasoning.correct_answer_reasoning
        : reasoning.distractor_analysis_summary,
      primaryRule: reasoning.primary_rule,
      failureMode: selectedOption?.student_failure_mode_key,
    }
  }, [state.question, state.selectedAnswer])

  /**
   * 6. selectAnswer()
   * Sets selected answer and shows feedback
   */
  const selectAnswer = useCallback((optionId: string) => {
    setState((prev) => ({
      ...prev,
      selectedAnswer: optionId,
      feedbackVisible: true,
    }))
  }, [])

  /**
   * 7. renderFeedback()
   * Returns feedback data (already computed in renderExplanations)
   */
  const renderFeedback = useCallback(() => {
    return renderExplanations()
  }, [renderExplanations])

  /**
   * 8. toggleKey()
   * Toggles a syntax anatomy key in activeKeys
   */
  const toggleKey = useCallback((keyId: string) => {
    setState((prev) => {
      const newKeys = new Set(prev.activeKeys)
      if (newKeys.has(keyId)) {
        newKeys.delete(keyId)
      } else {
        newKeys.add(keyId)
      }
      return { ...prev, activeKeys: newKeys }
    })
  }, [])

  /**
   * 9. clearKeys()
   * Clears all active keys
   */
  const clearKeys = useCallback(() => {
    setState((prev) => ({
      ...prev,
      activeKeys: new Set(),
    }))
  }, [])

  /**
   * 10. findTraps()
   * Auto-highlights relevant syntax anatomy keys based on backend classification
   */
  const findTraps = useCallback(() => {
    if (!state.question) return

    const { grammar_focus_key } = state.question.classification

    // Mapping from backend grammar_focus_key to relevant syntax anatomy keys
    const focusKeyToAnatomyKeys: Record<string, string[]> = {
      subject_verb_agreement: ['subject', 'main_verb', 'prepositional_phrase'],
      verb_tense_consistency: ['main_verb', 'subordinate_clause'],
      pronoun_antecedent_agreement: ['subject', 'relative_clause'],
      modifier_placement: ['modifier', 'subject'],
      parallel_structure: ['subject', 'main_verb'],
      punctuation_comma: ['appositive', 'relative_clause', 'prepositional_phrase'],
      sentence_fragment: ['subordinate_clause'],
      comma_splice: ['subordinate_clause', 'main_verb'],
      run_on_sentence: ['subordinate_clause', 'main_verb'],
    }

    const relevantKeys = focusKeyToAnatomyKeys[grammar_focus_key] || []
    const newKeys = new Set(relevantKeys)

    setState((prev) => ({
      ...prev,
      activeKeys: newKeys,
    }))
  }, [state.question])

  /**
   * 11. getKey()
   * Looks up a syntax anatomy key by ID
   */
  const getKey = useCallback((keyId: string): SyntaxAnatomyKey | null => {
    return SYNTAX_ANATOMY_KEYS.find((key) => key.id === keyId) || null
  }, [])

  /**
   * Helper: findActiveKey()
   * Returns all active keys as objects
   */
  const findActiveKey = useCallback(() => {
    return SYNTAX_ANATOMY_KEYS.filter((key) => state.activeKeys.has(key.id))
  }, [state.activeKeys])

  return {
    // State
    state,
    question: state.question,
    selectedAnswer: state.selectedAnswer,
    activeKeys: state.activeKeys,
    feedbackVisible: state.feedbackVisible,
    isLoading: state.isLoading,
    error: state.error,

    // Render functions
    renderSentence,
    renderOptions,
    renderGrammarKeys,
    renderTrapSummary,
    renderExplanations,
    renderFeedback,

    // Event handlers
    selectAnswer,
    toggleKey,
    clearKeys,
    findTraps,

    // Helpers
    getKey,
    findActiveKey,
    allKeys: SYNTAX_ANATOMY_KEYS,
  }
}
