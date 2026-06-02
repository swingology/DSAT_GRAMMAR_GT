export interface QuestionOption {
  label: string;
  text: string;
  distractor_type_key?: string | null;
  why_wrong?: string | null;
  why_plausible?: string | null;
}

export interface Question {
  id: string;
  content_origin: string;
  current_question_text: string;
  current_passage_text: string | null;
  passage_tokens: Record<string, unknown>[] | null;
  practice_status: string;
  options: QuestionOption[];
  grammar_role_key: string | null;
  grammar_focus_key: string | null;
  reading_skill_family_key: string | null;
  reading_focus_key: string | null;
  difficulty_overall: string | null;
  stimulus_mode_key: string | null;
  source_release_year: number | null;
  source_test_name: string | null;
  source_question_number: number | null;
  question_family_key: string | null;
  syntactic_trap_key: string | null;
  reasoning_trap_key: string | null;
  explanation_short: string | null;
  solver_pattern_key: string | null;
  source_exam_code: string | null;
  source_subject_code: string | null;
  source_section_code: string | null;
  source_module_code: string | null;
}

export interface InventoryMetadata {
  matching_target_total: number;
  matching_unseen: number;
  served: number;
  includes_generated: boolean;
  below_threshold: boolean;
  threshold: number;
}

export interface QuestionsResponse {
  items: Question[];
  inventory: InventoryMetadata;
}

export interface SubmitResult {
  id: number;
  is_correct: boolean;
}

export interface UserStats {
  total_answered: number;
  total_correct: number;
  accuracy: number;
  top_missed_focus_keys: string[];
  top_missed_trap_keys: string[];
}
