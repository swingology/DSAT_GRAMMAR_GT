// Grammar-specific type definitions (aligned with rules_agent_v8.md)

export interface BackendGrammarClassification {
  grammar_role_key: string           // D.1: sentence_boundary, agreement, verb_form, etc.
  grammar_focus_key: string          // D.2: subject_verb_agreement, verb_tense_consistency, etc.
  syntactic_trap_key: string | string[]  // D.5: nearest_noun_attraction, temporal_sequence_ambiguity, etc.
  syntactic_trap_intensity: "low" | "medium" | "high"
  student_failure_mode_key?: string  // D.7: why students pick wrong answers
  secondary_grammar_focus_keys?: string[]
}

export interface GrammarReasoning {
  primary_rule: string              // The grammar rule that selects correct answer
  trap_mechanism: string            // How the syntactic trap misleads test-takers
  correct_answer_reasoning: string  // Step-by-step justification
  distractor_analysis_summary: string
}

export interface GrammarOption {
  id: string              // "A", "B", "C", "D"
  text: string
  correct: boolean
  student_failure_mode_key?: string  // Why this distractor is tempting (D.7)
}

export interface GrammarQuestion {
  id: string
  text: string                        // Full question prompt
  options: GrammarOption[]

  // Backend classification (from rules_v8, Part D)
  classification: BackendGrammarClassification

  // Reasoning & explanation
  reasoning: GrammarReasoning

  // Optional: test metadata
  source_exam?: string                // "PT1", "PT4", "GENERATED"
  source_question_number?: number
  explanation_short?: string
}

export interface SyntaxAnatomyKey {
  id: string
  label: string           // e.g., "Primary Subject"
  group: string           // "Sentence Anatomy"
  color: string
  lightBg: string
  description: string
  rule: string
  priority: number
}

export interface GrammarSessionState {
  question: GrammarQuestion | null
  selectedAnswer: string | null
  activeKeys: Set<string>              // Syntax Anatomy keys, NOT backend keys
  feedbackVisible: boolean
  isLoading: boolean
  error: string | null
}
