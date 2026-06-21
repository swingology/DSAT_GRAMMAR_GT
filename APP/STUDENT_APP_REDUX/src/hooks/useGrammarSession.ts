import { useState, useEffect, useCallback, useMemo } from 'react'
import { SYNTAX_ANATOMY_KEYS } from '../data/syntaxAnatomyKeys'
import { normalizePassageTokens } from '../utils/sentenceTokenizer'
import type {
  GrammarSessionState,
  SyntaxAnatomyKey,
} from '../types/grammar'
import { api } from '../api/client'

export function useGrammarSession() {
  const [state, setState] = useState<GrammarSessionState>({
    question: null,
    selectedAnswer: null,
    isCorrect: null,
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
        const resp = await api.getQuestions({
          domain: 'grammar',
          limit: 1,
        })
        const questions = resp?.items ?? []
        if (questions.length > 0) {
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

  // Reset interactive state whenever a new question loads
  useEffect(() => {
    setState((prev) => ({
      ...prev,
      activeKeys: new Set(),
      selectedAnswer: null,
      isCorrect: null,
      feedbackVisible: false,
    }))
  }, [state.question?.id])

  const passageText = useMemo(() => {
    const q = state.question as any
    return q?.current_passage_text ?? q?.current_question_text ?? q?.text ?? ''
  }, [state.question])

  // Exact Pass 2 spans win. The local tokenizer keeps older rows interactive.
  const passageTokens = useMemo(() => {
    const q = state.question as any
    return normalizePassageTokens(q?.passage_tokens, passageText)
  }, [state.question, passageText])

  const passageKeyIds = useMemo((): Set<string> => {
    const ids = new Set<string>()
    passageTokens.forEach((token) => token.tags.forEach((tag) => ids.add(tag)))
    return ids
  }, [passageTokens])

  const allKeys = useMemo((): SyntaxAnatomyKey[] => {
    const knownIds = new Set(SYNTAX_ANATOMY_KEYS.map((key) => key.id))
    const backendKeys = [...passageKeyIds]
      .filter((id) => !knownIds.has(id))
      .map((id, index) => {
        const hue = (index * 67 + 215) % 360
        return {
          id,
          label: id.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()),
          group: 'Backend Grammar Keys',
          color: `hsl(${hue} 65% 38%)`,
          lightBg: `hsl(${hue} 75% 94%)`,
          description: `Backend annotation for ${id.replace(/_/g, ' ')}.`,
          rule: 'Highlighted spans come from the stored passage-token annotation.',
          priority: 30,
        }
      })

    return [...SYNTAX_ANATOMY_KEYS, ...backendKeys]
  }, [passageKeyIds])

  // ─────────────────────────────────────────────────────────────────
  // 11 Core Functions (from component breakdown)
  // ─────────────────────────────────────────────────────────────────

  /**
   * 1. renderSentence()
   * Returns the question text (API field: current_question_text)
   */
  const renderSentence = useCallback(() => {
    return passageText
  }, [passageText])

  const renderQuestionPrompt = useCallback(() => {
    const q = state.question as any
    if (!q?.current_passage_text) return null
    return q.current_question_text ?? q.text ?? null
  }, [state.question])

  /**
   * 2. renderOptions()
   * Returns array of options with selected state.
   * API options use { label, text } — no correct field exposed.
   */
  const renderOptions = useCallback(() => {
    if (!state.question) return []

    return (state.question as any).options.map((option: any) => {
      const isSelected = option.label === state.selectedAnswer
      return {
        id: option.label,
        text: option.text,
        isSelected,
        isCorrect: isSelected && state.isCorrect === true,
        isIncorrect: isSelected && state.isCorrect === false,
      }
    })
  }, [state.question, state.selectedAnswer, state.feedbackVisible, state.isCorrect])

  /**
   * 3. renderGrammarKeys()
   * Returns grouped syntax anatomy keys — only those that tag at least one
   * token in the current passage, so no irrelevant pills are shown.
   */
  const renderGrammarKeys = useCallback(() => {
    const presentKeys = allKeys.filter((key) => passageKeyIds.has(key.id))
    const groups = [...new Set(presentKeys.map((key) => key.group))]

    return groups.map((group) => ({
      group,
      keys: presentKeys.filter((key) => key.group === group).sort(
        (a, b) => b.priority - a.priority
      ),
      activeKeys: presentKeys.filter(
        (key) => key.group === group && state.activeKeys.has(key.id)
      ),
    }))
  }, [state.activeKeys, passageKeyIds, allKeys])

  /**
   * 4. renderTrapSummary()
   * Returns trap analysis — fields are flat on the API question object.
   */
  const renderTrapSummary = useCallback(() => {
    if (!state.question) return null
    const q = state.question as any
    return {
      grammarRole: q.grammar_role_key,
      grammarFocus: q.grammar_focus_key,
      trapKeys: q.syntactic_trap_key ? [q.syntactic_trap_key] : [],
      trapIntensity: null,
      trapMechanism: null,
    }
  }, [state.question])

  /**
   * 5. renderExplanations()
   * Returns explanation text. API exposes explanation_short; correct answer not revealed.
   */
  const renderExplanations = useCallback(() => {
    if (!state.question || !state.selectedAnswer) return null
    const q = state.question as any
    const selectedOption = q.options.find((o: any) => o.label === state.selectedAnswer)

    const isCorrect = state.isCorrect
    return {
      isCorrect: isCorrect === true,
      title: isCorrect === true ? '✓ Correct!' : isCorrect === false ? '✗ Not quite' : 'Answer submitted',
      explanation: q.explanation_short ?? '',
      primaryRule: q.grammar_focus_key ?? '',
      failureMode: selectedOption?.why_plausible ?? null,
    }
  }, [state.question, state.selectedAnswer, state.isCorrect])

  /**
   * 6. selectAnswer()
   * Submits the answer to the backend, stores correctness, shows feedback.
   */
  const selectAnswer = useCallback(async (optionId: string) => {
    if (!state.question) return

    // Optimistically show the selection immediately
    setState((prev) => ({ ...prev, selectedAnswer: optionId }))

    const USER_TOKEN = (import.meta as any).env.VITE_TEST_USER_TOKEN || localStorage.getItem('user_token') || ''
    let isCorrect: boolean | null = null

    try {
      const selectedOption = ((state.question as any).options as any[])?.find(
        (o: any) => o.label === optionId
      )
      const result = await api.submitAnswer({
        question_id: (state.question as any).id,
        selected_option_label: optionId,
        user_token: USER_TOKEN,
        missed_grammar_focus_key: (state.question as any).grammar_focus_key,
        missed_syntactic_trap_key: selectedOption?.distractor_type_key ?? undefined,
      })
      isCorrect = result?.is_correct ?? null
    } catch {
      // Submit failed (e.g. backend down) — degrade gracefully, no correctness shown
    }

    setState((prev) => ({
      ...prev,
      selectedAnswer: optionId,
      isCorrect,
      feedbackVisible: true,
    }))
  }, [state.question])

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

    const question = state.question as any
    const grammar_focus_key = question.grammar_focus_key

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

    const backendKeys = [
      question.grammar_role_key,
      question.grammar_focus_key,
      question.syntactic_trap_key,
    ].filter((id): id is string => typeof id === 'string')
    const relevantKeys = [
      ...backendKeys,
      ...(focusKeyToAnatomyKeys[grammar_focus_key] || []),
    ].filter((id) => passageKeyIds.has(id))
    const newKeys = new Set(relevantKeys)

    setState((prev) => ({
      ...prev,
      activeKeys: newKeys,
    }))
  }, [state.question, passageKeyIds])

  /**
   * 11. getKey()
   * Looks up a syntax anatomy key by ID
   */
  const getKey = useCallback((keyId: string): SyntaxAnatomyKey | null => {
    return allKeys.find((key) => key.id === keyId) || null
  }, [allKeys])

  /**
   * Helper: findActiveKey()
   * Returns all active keys as objects
   */
  const findActiveKey = useCallback(() => {
    return allKeys.filter((key) => state.activeKeys.has(key.id))
  }, [state.activeKeys, allKeys])

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
    renderQuestionPrompt,
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
    allKeys,
    passageKeyIds,
    passageTokens,
  }
}
