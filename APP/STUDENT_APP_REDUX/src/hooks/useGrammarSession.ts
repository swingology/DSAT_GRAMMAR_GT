import { useState, useEffect, useCallback, useMemo } from 'react'
import { SYNTAX_ANATOMY_KEYS } from '../data/syntaxAnatomyKeys'
import { normalizePassageTokens } from '../utils/sentenceTokenizer'
import { assignKeyColor } from '../utils/keyColors'
import type {
  GrammarSessionState,
  SyntaxAnatomyKey,
} from '../types/grammar'
import { api } from '../api/client'


export function useGrammarSession() {
  const [questions, setQuestions] = useState<any[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [totalAvailable, setTotalAvailable] = useState(0)

  const [state, setState] = useState<GrammarSessionState>({
    question: null,
    selectedAnswer: null,
    isCorrect: null,
    activeKeys: new Set(),
    feedbackVisible: false,
    isLoading: true,
    error: null,
  })

  // Fetch a batch of questions on mount
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setState((prev) => ({ ...prev, isLoading: true, error: null }))
        const resp = await api.getQuestions({
          domain: 'grammar',
          limit: 50,
        })
        const items = resp?.items ?? []
        const total = resp?.matching_target_total ?? items.length
        if (items.length > 0) {
          setQuestions(items)
          setTotalAvailable(total)
          setState((prev) => ({
            ...prev,
            question: items[0],
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

    fetchQuestions()
  }, [])

  // Sync current question to state when index changes
  useEffect(() => {
    if (questions.length > 0 && questions[currentIndex]) {
      setState((prev) => ({ ...prev, question: questions[currentIndex] }))
    }
  }, [currentIndex, questions])

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

  // Passage and stem are now stored in separate DB fields.
  // Fall back to current_question_text as passage for the one question type
  // that has no passage body (e.g. "As used in the text...").
  const [passageText, stemText] = useMemo(() => {
    const q = state.question as any
    const passage = q?.current_passage_text || ''
    const stem = q?.current_question_text ?? q?.text ?? ''
    if (passage) {
      return [passage as string, stem as string]
    }
    // No separate passage — use full question text for tokenization, no stem shown
    return [stem, null]
  }, [state.question])

  // Exact Pass 2 spans win. The local tokenizer keeps older rows interactive.
  // grammar_focus_key tells the tokenizer what the blank slot actually is
  // (verb, transition word, pronoun, etc.) so it tags it correctly.
  const passageTokens = useMemo(() => {
    const q = state.question as any
    return normalizePassageTokens(q?.passage_tokens, passageText, q?.grammar_focus_key)
  }, [state.question, passageText])

  const passageKeyIds = useMemo((): Set<string> => {
    const q = state.question as any
    const spans = q?.passage_spans
    if (spans) {
      return new Set<string>([
        ...(spans.anatomy_present  as string[] ?? []),
        ...(spans.concepts_present as string[] ?? []),
      ])
    }
    // Fallback: derive from flat passage_tokens tags
    const ids = new Set<string>()
    passageTokens.forEach((token) => token.tags.forEach((tag) => ids.add(tag)))
    return ids
  }, [state.question, passageTokens])

  const allKeys = useMemo((): SyntaxAnatomyKey[] => {
    const knownIds = new Set(SYNTAX_ANATOMY_KEYS.map((key) => key.id))
    const backendKeys = [...passageKeyIds]
      .filter((id) => !knownIds.has(id))
      .map((id) => {
        const { color, lightBg } = assignKeyColor(id, 'concept')
        return {
          id,
          label: id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
          group: 'Grammar Concepts',
          color,
          lightBg,
          description: `Grammar concept: ${id.replace(/_/g, ' ')}.`,
          rule: 'Highlighted spans come from the stored span annotation.',
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
    return stemText ?? null
  }, [stemText])

  /**
   * 2. renderOptions()
   * Returns array of options with selected state.
   * API options use { label, text } — no correct field exposed.
   */
  const renderOptions = useCallback(() => {
    if (!state.question) return []

    const q = state.question as any
    const correctLabel = q.current_correct_option_label

    return q.options.map((option: any) => {
      const isSelected = option.label === state.selectedAnswer
      const isTheCorrectAnswer = state.feedbackVisible && option.label === correctLabel
      return {
        id: option.label,
        text: option.text,
        isSelected,
        // Green: selected and correct, OR the correct answer revealed after a wrong pick
        isCorrect: (isSelected && state.isCorrect === true) || (state.isCorrect === false && isTheCorrectAnswer),
        isIncorrect: isSelected && state.isCorrect === false,
      }
    })
  }, [state.question, state.selectedAnswer, state.feedbackVisible, state.isCorrect])

  /**
   * 3. renderGrammarKeys()
   * Returns two explicit groups:
   *   Group 1 "Sentence Anatomy" — all anatomy keys, always shown
   *   Group 2 "Grammar Concepts" — only concept keys with actual passage spans
   */
  const renderGrammarKeys = useCallback(() => {
    const knownIds = new Set(SYNTAX_ANATOMY_KEYS.map((k) => k.id))

    const sortedAnatomy = [...SYNTAX_ANATOMY_KEYS].sort((a, b) => b.priority - a.priority)
    const anatomyGroup = {
      group: 'Sentence Anatomy',
      keys: sortedAnatomy,
      activeKeys: sortedAnatomy.filter((k) => state.activeKeys.has(k.id)),
    }

    const conceptKeys = [...passageKeyIds]
      .filter((id) => !knownIds.has(id))
      .map((id) => allKeys.find((k) => k.id === id))
      .filter((k): k is SyntaxAnatomyKey => k !== undefined)
      .sort((a, b) => b.priority - a.priority)

    const conceptGroup = {
      group: 'Grammar Concepts',
      keys: conceptKeys,
      activeKeys: conceptKeys.filter((k) => state.activeKeys.has(k.id)),
    }

    return conceptKeys.length > 0 ? [anatomyGroup, conceptGroup] : [anatomyGroup]
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

    const q = state.question as any

    // Evaluate correctness immediately from the question payload — no network wait
    const isCorrect: boolean = optionId === q.current_correct_option_label

    setState((prev) => ({
      ...prev,
      selectedAnswer: optionId,
      isCorrect,
      feedbackVisible: true,
    }))

    // Submit to backend in the background for progress tracking
    const USER_TOKEN = (import.meta as any).env.VITE_TEST_USER_TOKEN || localStorage.getItem('user_token') || ''
    const selectedOption = (q.options as any[])?.find((o: any) => o.label === optionId)
    api.submitAnswer({
      question_id: q.id,
      selected_option_label: optionId,
      user_token: USER_TOKEN,
      missed_grammar_focus_key: q.grammar_focus_key,
      missed_syntactic_trap_key: selectedOption?.distractor_type_key ?? undefined,
    }).catch(() => {
      // Backend submission failed — feedback already shown, nothing to undo
    })
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
   * Auto-highlights keys from passage_spans.concepts_present when available;
   * falls back to focus/role/trap keys + anatomy heuristics.
   */
  const findTraps = useCallback(() => {
    if (!state.question) return

    const question = state.question as any

    // Prefer span annotation concepts — these are accurate and pre-computed
    const spans = question?.passage_spans
    if (spans?.concepts_present?.length) {
      setState((prev) => ({ ...prev, activeKeys: new Set<string>(spans.concepts_present) }))
      return
    }

    // Fallback: derive from classification keys + anatomy heuristics
    const grammar_focus_key = question.grammar_focus_key
    const focusKeyToAnatomyKeys: Record<string, string[]> = {
      subject_verb_agreement:      ['subject', 'main_verb', 'prepositional_phrase'],
      verb_tense_consistency:      ['main_verb', 'subordinate_clause'],
      pronoun_antecedent_agreement: ['subject', 'relative_clause'],
      modifier_placement:          ['modifier', 'subject'],
      parallel_structure:          ['subject', 'main_verb'],
      punctuation_comma:           ['appositive', 'relative_clause', 'prepositional_phrase'],
      sentence_fragment:           ['subordinate_clause'],
      comma_splice:                ['subordinate_clause', 'main_verb'],
      run_on_sentence:             ['subordinate_clause', 'main_verb'],
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

    setState((prev) => ({ ...prev, activeKeys: new Set(relevantKeys) }))
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

  const nextQuestion = useCallback(() => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((i) => i + 1)
    }
  }, [currentIndex, questions.length])

  const prevQuestion = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1)
    }
  }, [currentIndex])

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

    // Navigation
    currentIndex,
    totalQuestions: questions.length,
    totalAvailable,
    nextQuestion,
    prevQuestion,
    hasNext: currentIndex < questions.length - 1,
    hasPrev: currentIndex > 0,

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
