import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { getUserToken } from '../auth/authStore'
import type {
  ReviewFiltersResponse,
  ReviewQuestionFilters,
  ReviewQuestionsResponse,
} from '../types'

export function useReviewQuestions(
  filters: ReviewQuestionFilters = {},
  page = 1,
  pageSize = 20,
) {
  return useQuery<ReviewQuestionsResponse>({
    queryKey: ['review-questions', filters, page, pageSize],
    queryFn: () => api.getReviewQuestions({
      user_token: getUserToken(),
      ...filters,
      page,
      page_size: pageSize,
    }),
    staleTime: 60_000,
    retry: 1,
  })
}

export function useReviewFilters() {
  return useQuery<ReviewFiltersResponse>({
    queryKey: ['review-filters', getUserToken()],
    queryFn: () => api.getReviewFilters(getUserToken()),
    staleTime: 5 * 60_000,
    retry: 1,
  })
}
