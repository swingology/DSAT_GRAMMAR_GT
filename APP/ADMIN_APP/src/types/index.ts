export interface User {
  id: number
  username: string
  email?: string | null
  role: string
  is_active: boolean
  user_token: string
  created_at?: string | null
}

export interface QuestionAnnotation {
  grammar_focus_key?: string
  grammar_role_key?: string
  reading_focus_key?: string
  difficulty_overall?: string
  [key: string]: unknown
}

export interface StimulusAsset {
  id: string
  stimulus_type: string
  url: string
  title?: string | null
  source_page_number?: number | null
  storage_path?: string
  structured_data?: unknown
  render_hints?: unknown
  created_at?: string
}

export interface StimulusExtractionJob {
  id: string
  question_id: string
  stimulus_type: string
  replace_existing: boolean
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  attempt_count: number
  error_message?: string | null
  result_asset_id?: string | null
  asset?: StimulusAsset | null
  created_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  updated_at?: string | null
}

export interface StimulusExtractResponse {
  created: boolean
  queued: boolean
  asset: StimulusAsset | null
  job: StimulusExtractionJob | null
  message: string
}

export interface Question {
  id: string
  content_origin: 'official' | 'unofficial' | 'generated'
  practice_status: 'draft' | 'active' | 'retired' | 'rejected'
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
  source_has_graph?: boolean | null
  stimulus_mode_key?: string | null
  options?: QuestionOption[]
  stimulus_assets?: StimulusAsset[]
  updated_at?: string
  created_at?: string
}

export interface QuestionListResponse {
  questions: Question[]
  total: number
  limit: number
  offset: number
}

export interface QuestionOption {
  id: string
  option_label: string
  option_text: string
  is_correct?: boolean
}

export interface TestSummary {
  content_origin?: 'official' | 'unofficial' | 'generated'
  source_release_year?: number
  pt_number?: number
  source_test_name?: string
  source_exam_code?: string
  source_subject_code?: string
  source_section_code?: string
  source_module_code?: string
  question_count: number
  approved_count: number
}

export interface GenerationAnalytics {
  days: number
  generated_count: number
  reviewed_count: number
  approved_count: number
  rejected_count: number
  failed_count: number
  acceptance_rate: number
  copy_risk_failures: number
  avg_reviewer_disagreement?: number | null
  by_generator_model: GeneratorModelStats[]
  rejection_reasons: RejectionReasonCount[]
}

export interface GeneratorModelStats {
  model_name: string
  provider_name: string
  generated_count: number
  approved_count: number
  rejected_count: number
  acceptance_rate: number
}

export interface RejectionReasonCount {
  reason?: string | null
  count: number
}

export interface TokenUsageByProvider {
  provider_name: string
  review_count: number
  total_input_tokens: number
  total_output_tokens: number
}

export interface BatchAggregates {
  total_requested: number
  total_created: number
  total_accepted: number
  total_rejected: number
  total_failed: number
  batch_count: number
  avg_review_latency_ms?: number | null
}

export interface RecentBatchSummary {
  id: string
  status: string
  requested_count: number
  created_count: number
  accepted_count: number
  rejected_count: number
  failed_count: number
  needs_review_count: number
  created_at?: string | null
  requested_by: string
}

export interface BatchAnalytics {
  days: number
  aggregates: BatchAggregates
  recent_batches: RecentBatchSummary[]
  token_usage: TokenUsageByProvider[]
}

export interface AutoReleaseStatus {
  config_enabled: boolean
  runtime_disabled: boolean
  effective_enabled: boolean
  min_reviews_required: number
  min_accept_rate: number
  allowed_targets_raw: string
}

export interface StudentStats {
  total_answered: number
  total_correct: number
  accuracy: number
  top_missed_focus_keys: string[]
  top_missed_trap_keys: string[]
}

export interface ActivityDay {
  date: string
  count: number
}

export interface FocusAreaMissRate {
  focus_key: string
  domain: string
  total_attempts: number
  unique_students: number
  miss_count: number
  miss_rate: number
}

export interface CohortWeakSpots {
  generated_at: string
  question_wise_misses: unknown[]
  focus_area_misses: FocusAreaMissRate[]
}

// --- Controlled-vocabulary governance (vocabulary/master.json + candidates.json) ---

export interface VocabEntry {
  value: string
  status: 'active' | 'retired' | string
  added: string
  description: string
}

export interface Vocabulary {
  name: string
  kind: 'flat' | 'hierarchical' | string
  domain: 'system' | 'grammar' | 'reading' | string
  comment: string
  entries: VocabEntry[]
}

export interface VocabMaster {
  schema_version: number
  note: string
  samples_companion: string
  vocabularies: Vocabulary[]
}

export interface VocabCandidate {
  vocab: string
  value: string
  field: string
  first_seen: string
  last_seen: string
  occurrences: number
  job_ids: string[]
  contexts: string[]
}

export interface VocabCandidatesFile {
  schema_version: number
  candidates: VocabCandidate[]
}
