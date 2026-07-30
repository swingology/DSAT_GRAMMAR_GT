// Type definitions for Student App

export interface WeaknessTarget {
  domain: string
  focus_key: string
  skill_family_key?: string
  grammar_role_key?: string
  difficulty: string
  weakness_score: number
  miss_count: number
  attempt_count: number
  miss_rate: number
  days_since_last_attempt: number
  inventory_unseen: number
  inventory_below_threshold: boolean
}

export interface StudyRecommendationsResponse {
  user_id: number
  top_targets: WeaknessTarget[]
  threshold: number
}

export interface StimulusModeCount {
  stimulus_mode_key: string
  count: number
}

export interface Question {
  id: string
  text: string
  domain: string
  focus_key: string
  difficulty: string
  explanation?: string
  content_origin?: string
}

export interface StudentQuestion extends Question {
  options?: any[]
}

// ── Diagnostic v1 Blueprint Types ─────────────────────────────────────────────

export interface DiagnosticOptionPayload {
  label: string
  text: string
  distractor_type_key?: string | null
}

/** Question served during a blueprint diagnostic — no answer key. */
export interface DiagnosticQuestion {
  id: string
  seq: number
  current_question_text: string
  current_passage_text?: string | null
  passage_spans?: Record<string, unknown> | null
  options: DiagnosticOptionPayload[]
  domain?: string | null
  grammar_role_key?: string | null
  grammar_focus_key?: string | null
  reading_skill_family_key?: string | null
  reading_focus_key?: string | null
  difficulty_overall?: string | null
  question_family_key?: string | null
  stimulus_mode_key?: string | null
  // NOTE: current_correct_option_label intentionally absent
}

export interface DiagnosticStartV1Response {
  session_id: string
  total_questions: number
  time_limit_seconds: number
  questions: DiagnosticQuestion[]
  coverage_report: Record<string, unknown>
}

export interface CorrectTotal {
  correct: number
  total: number
}

export interface WeakestArea {
  area_key: string
  domain: string
  miss_count: number
  correct?: number
  total?: number
  accuracy?: number
}

export interface DiagnosticBreakdown {
  by_family: Record<string, CorrectTotal>
  by_difficulty: Record<string, CorrectTotal>
  by_trap: Record<string, CorrectTotal>
  weakest_areas: WeakestArea[]
}

export interface DiagnosticResult {
  session_id: string
  total_questions: number
  correct_count: number
  accuracy: number
  duration_seconds?: number | null
  weakest_focus_areas: Array<{ focus_key: string; miss_count: number }>
  breakdown?: DiagnosticBreakdown | null
}

export type ReviewSourceType =
  | 'diagnostic'
  | 'practice_test'
  | 'drill'
  | 'practice'
  | 'unknown'

export interface ReviewQuestionOption {
  label: string
  text: string
  is_correct: boolean
}

export interface ReviewQuestionItem {
  question_id: string
  passage_text: string | null
  paired_passage_text: string | null
  underlined_text: string | null
  question_text: string
  options: ReviewQuestionOption[]
  correct_option_label: string
  explanation: string | null
  user_answer: string
  domain: string | null
  focus_key: string | null
  focus_key_source: string | null
  stem_type_key: string | null
  difficulty: string | null
  content_origin: string
  source_test_name: string | null
  source_section_code: string | null
  source_module_code: string | null
  source_question_number: number | null
  source_type: string
  source_types: string[]
  miss_count: number
  last_missed_at: string | null
}

export interface ReviewQuestionsResponse {
  items: ReviewQuestionItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface ReviewFiltersResponse {
  source_types: string[]
  source_test_names: string[]
  source_section_codes: string[]
  source_module_codes: string[]
  domains: string[]
  focus_keys: string[]
  stem_type_keys: string[]
  difficulties: string[]
  content_origins: string[]
}

export interface ReviewQuestionFilters {
  source_type?: ReviewSourceType | ReviewSourceType[]
  source_test_name?: string
  source_section_code?: string
  source_module_code?: string
  domain?: string
  focus_key?: string
  stem_type_key?: string
  difficulty?: string
  content_origin?: string | string[]
}

export interface ReviewQuestionsParams extends ReviewQuestionFilters {
  user_token: string
  page?: number
  page_size?: number
}
