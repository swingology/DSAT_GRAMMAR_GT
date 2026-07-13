import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { StudyRecommendationsResponse } from '../types'
import { getUserToken } from '../auth/authStore'


export interface StudentStats {
  user_id: number
  total_attempts: number
  correct_count: number
  accuracy: number
  weekly_attempts?: number
  streak_days?: number
}

export function useStats(userId: number | undefined) {
  return useQuery<StudentStats>({
    queryKey: ['stats', userId],
    queryFn: () => api.getStats(userId!),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000,
  })
}

export interface MissedQuestionItem {
  question_id: string
  question_text: string
  domain: string | null
  focus_key: string | null
  difficulty: string | null
  user_answer: string | null
  correct_answer: string | null
  explanation: string | null
  miss_count: number
  last_missed_at: string | null
}

export interface MissedQuestionsResponse {
  user_id: number
  items: MissedQuestionItem[]
  total: number
}

export function useRecommendations() {
  return useQuery<StudyRecommendationsResponse>({
    queryKey: ['recommendations'],
    queryFn: () => api.getStudyRecommendations(getUserToken()),
    staleTime: 5 * 60 * 1000,
  })
}

export function useQuestions(params: Record<string, any>, enabled = true) {
  return useQuery({
    queryKey: ['questions', params],
    queryFn: () => api.getQuestions(params),
    enabled,
    staleTime: 60 * 1000,
  })
}

export function useSubmitAnswer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      question_id: string
      selected_option_label: string
      missed_grammar_focus_key?: string
      missed_reading_focus_key?: string
      missed_syntactic_trap_key?: string
    }) =>
      api.submitAnswer({ ...data, user_token: getUserToken() }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recommendations'] })
    },
  })
}

export function useMissedQuestions(params: { domain?: string; sort_by?: string } = {}) {
  return useQuery<MissedQuestionsResponse>({
    queryKey: ['missed', params],
    queryFn: () => api.getMissedQuestions({ user_token: getUserToken(), ...params }),
    staleTime: 2 * 60 * 1000,
    retry: 1,
  })
}

export function useSRProgress() {
  return useQuery({
    queryKey: ['sr-progress'],
    queryFn: () => api.srProgress(getUserToken()),
    staleTime: 60_000,
  })
}

export function useSRDue(limit = 20) {
  return useQuery({
    queryKey: ['sr-due', limit],
    queryFn: () => api.srDueQuestions(getUserToken(), limit),
    staleTime: 60_000,
  })
}

export function useTrapSusceptibility() {
  return useQuery({
    queryKey: ['trap-susceptibility'],
    queryFn: () => api.getTrapSusceptibility(getUserToken()),
    staleTime: 5 * 60_000,
  })
}

export function useQuestionTypePerformance() {
  return useQuery({
    queryKey: ['question-type-performance'],
    queryFn: () => api.getQuestionTypePerformance(getUserToken()),
    staleTime: 5 * 60_000,
  })
}

export function useTrapDetails(trapType: string) {
  return useQuery({
    queryKey: ['trap-details', trapType],
    queryFn: () => api.getTrapDetails(trapType, getUserToken()),
    staleTime: 5 * 60_000,
    enabled: !!trapType,
  })
}

export function useProgressTrend(days = 30) {
  return useQuery({
    queryKey: ['progress-trend', days],
    queryFn: () => api.getProgressTrend(getUserToken(), days),
    staleTime: 5 * 60_000,
  })
}

export function useDomainTrend(days = 30) {
  return useQuery({
    queryKey: ['domain-trend', days],
    queryFn: () => api.getDomainTrend(getUserToken(), days),
    staleTime: 5 * 60_000,
  })
}

export function useFocusSummary() {
  return useQuery({
    queryKey: ['focus-summary'],
    queryFn: () => api.getFocusSummary(getUserToken()),
    staleTime: 5 * 60_000,
  })
}
