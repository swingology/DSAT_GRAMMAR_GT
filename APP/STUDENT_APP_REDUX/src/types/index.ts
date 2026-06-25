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
