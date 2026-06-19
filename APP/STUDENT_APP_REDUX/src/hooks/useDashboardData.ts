import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { StudyRecommendationsResponse } from '../types'

const USER_TOKEN = (import.meta as any).env.VITE_TEST_USER_TOKEN || ''

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
    queryFn: () => api.getStudyRecommendations(USER_TOKEN),
    staleTime: 5 * 60 * 1000,
    retry: 2,
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
    mutationFn: (data: any) => api.submitAnswer(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recommendations'] })
    },
  })
}

export function useMissedQuestions(params: { domain?: string; sort_by?: string } = {}) {
  return useQuery<MissedQuestionsResponse>({
    queryKey: ['missed', params],
    queryFn: () => api.getMissedQuestions({ user_token: USER_TOKEN, ...params }),
    enabled: !!USER_TOKEN,
    staleTime: 2 * 60 * 1000,
    retry: 1,
  })
}
