export interface User {
  id: number
  username: string
  email?: string | null
  role: string
  is_active: boolean
  user_token: string
  created_at: string
}

export interface QuestionAnnotation {
  grammar_focus_key?: string
  grammar_role_key?: string
  reading_focus_key?: string
  difficulty_overall?: string
  [key: string]: unknown
}

export interface Question {
  id: string
  content_origin: 'official' | 'generated' | 'admin_created'
  practice_status: 'draft' | 'active' | 'approved' | 'rejected' | 'needs_review'
  official_overlap_status?: string
  current_question_text: string
  current_passage_text?: string
  current_correct_option_label: string
  current_explanation_text?: string
  is_admin_edited?: boolean
  annotation_stale?: boolean
  annotation?: QuestionAnnotation | null
  source_release_year?: number
  source_test_name?: string
  source_exam_code?: string
  source_subject_code?: string
  source_section_code?: string
  source_module_code?: string
  source_question_number?: number
  options?: QuestionOption[]
  updated_at?: string
  created_at?: string
}

export interface QuestionOption {
  id: string
  option_label: string
  option_text: string
  is_correct?: boolean
}

export interface GenerationAnalytics {
  total_generated: number
  total_approved: number
  total_rejected: number
  approve_rate: number
  by_model: ModelStats[]
  by_domain: DomainStats[]
}

export interface ModelStats {
  model_name: string
  provider_name: string
  generated_count: number
  approved_count: number
  rejected_count: number
  approve_rate: number
}

export interface DomainStats {
  domain: string
  generated_count: number
  approved_count: number
  approve_rate: number
}

export interface ReviewAnalytics {
  total_reviews: number
  avg_score: number
  by_model: ModelStats[]
}

export interface BatchAnalytics {
  total_batches: number
  completed_batches: number
  failed_batches: number
  avg_batch_size: number
  recent_batches: BatchSummary[]
}

export interface BatchSummary {
  id: string
  status: string
  requested_count: number
  created_count: number
  accepted_count: number
  rejected_count: number
  created_at: string
  requested_by: string
}

export interface StudentStats {
  total_answered: number
  total_correct: number
  accuracy: number
  top_missed_focus_keys: string[]
  top_missed_trap_keys: string[]
}
