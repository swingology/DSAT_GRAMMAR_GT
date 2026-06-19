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
