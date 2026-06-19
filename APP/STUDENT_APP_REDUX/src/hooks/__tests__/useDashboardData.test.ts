import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useRecommendations, useMissedQuestions, useSubmitAnswer } from '../useDashboardData'
import * as clientModule from '../../api/client'

vi.mock('../../api/client', () => ({
  api: {
    getStudyRecommendations: vi.fn(),
    getMissedQuestions: vi.fn(),
    submitAnswer: vi.fn(),
    getQuestions: vi.fn(),
  },
}))

const mockedApi = vi.mocked(clientModule.api)

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: any }) =>
    createElement(QueryClientProvider, { client: qc }, children)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useRecommendations', () => {
  it('returns top_targets on success', async () => {
    const mockData = {
      user_id: 1,
      top_targets: [
        {
          domain: 'grammar',
          focus_key: 'comma_splice',
          skill_family_key: null,
          grammar_role_key: 'sentence_structure',
          difficulty: 'medium',
          weakness_score: 0.8,
          miss_count: 4,
          attempt_count: 5,
          miss_rate: 0.8,
          days_since_last_attempt: 2,
          inventory_unseen: 10,
          inventory_below_threshold: false,
        },
      ],
      threshold: 5,
    }
    mockedApi.getStudyRecommendations.mockResolvedValue(mockData)

    const { result } = renderHook(() => useRecommendations(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.top_targets).toHaveLength(1)
    expect(result.current.data?.top_targets[0].focus_key).toBe('comma_splice')
  })

  it('enters error state when API fails', async () => {
    mockedApi.getStudyRecommendations.mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useRecommendations(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })

  it('starts in loading state', () => {
    mockedApi.getStudyRecommendations.mockReturnValue(new Promise(() => {}))

    const { result } = renderHook(() => useRecommendations(), { wrapper: makeWrapper() })

    expect(result.current.isLoading).toBe(true)
  })
})

describe('useMissedQuestions', () => {
  it('returns items on success', async () => {
    const mockData = {
      user_id: 1,
      items: [
        {
          question_id: 'q-1',
          question_text: 'Which option corrects the sentence?',
          domain: 'grammar',
          focus_key: 'comma_splice',
          difficulty: 'medium',
          user_answer: 'A',
          correct_answer: 'B',
          explanation: 'A comma splice joins two independent clauses incorrectly.',
          miss_count: 3,
          last_missed_at: '2026-06-18T10:00:00Z',
        },
      ],
      total: 1,
    }
    mockedApi.getMissedQuestions.mockResolvedValue(mockData)

    const { result } = renderHook(() => useMissedQuestions(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0].focus_key).toBe('comma_splice')
    expect(result.current.data?.total).toBe(1)
  })

  it('passes domain filter to API', async () => {
    mockedApi.getMissedQuestions.mockResolvedValue({ user_id: 1, items: [], total: 0 })

    const { result } = renderHook(() => useMissedQuestions({ domain: 'grammar' }), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.getMissedQuestions).toHaveBeenCalledWith(
      expect.objectContaining({ domain: 'grammar' })
    )
  })

  it('passes sort_by filter to API', async () => {
    mockedApi.getMissedQuestions.mockResolvedValue({ user_id: 1, items: [], total: 0 })

    const { result } = renderHook(() => useMissedQuestions({ sort_by: 'miss_count' }), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.getMissedQuestions).toHaveBeenCalledWith(
      expect.objectContaining({ sort_by: 'miss_count' })
    )
  })

  it('returns empty items array when no misses', async () => {
    mockedApi.getMissedQuestions.mockResolvedValue({ user_id: 1, items: [], total: 0 })

    const { result } = renderHook(() => useMissedQuestions(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toHaveLength(0)
  })
})

describe('useSubmitAnswer', () => {
  it('calls submitAnswer API with correct payload', async () => {
    mockedApi.submitAnswer.mockResolvedValue({ id: 1, is_correct: true })
    mockedApi.getStudyRecommendations.mockResolvedValue({ user_id: 1, top_targets: [], threshold: 5 })

    const { result } = renderHook(() => useSubmitAnswer(), { wrapper: makeWrapper() })

    result.current.mutate({
      question_id: 'q-1',
      answer_id: 'opt-a',
      mode: 'practice',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.submitAnswer).toHaveBeenCalledWith({
      question_id: 'q-1',
      answer_id: 'opt-a',
      mode: 'practice',
    })
  })

  it('enters error state when submission fails', async () => {
    mockedApi.submitAnswer.mockRejectedValue(new Error('submit failed'))

    const { result } = renderHook(() => useSubmitAnswer(), { wrapper: makeWrapper() })

    result.current.mutate({ question_id: 'q-1', answer_id: 'opt-a', mode: 'test' })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
