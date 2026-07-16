import { createElement } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as clientModule from '../../api/client'
import { useReviewFilters, useReviewQuestions } from '../useReviewData'

vi.mock('../../api/client', () => ({
  api: {
    getReviewQuestions: vi.fn(),
    getReviewFilters: vi.fn(),
  },
}))

const mockedApi = vi.mocked(clientModule.api)

function makeWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedApi.getReviewQuestions.mockResolvedValue({
    items: [], total: 0, page: 1, page_size: 20, has_more: false,
  })
  mockedApi.getReviewFilters.mockResolvedValue({
    source_types: [], source_test_names: [], source_section_codes: [],
    source_module_codes: [], domains: [], focus_keys: [], stem_type_keys: [],
    difficulties: [], content_origins: [],
  })
})

describe('useReviewQuestions', () => {
  it('passes every filter and pagination value to the API', async () => {
    const filters = {
      source_type: ['diagnostic', 'drill'] as Array<'diagnostic' | 'drill'>,
      source_test_name: 'Bluebook 1',
      source_section_code: 'RW',
      source_module_code: 'M1',
      domain: 'reading',
      focus_key: 'inference',
      stem_type_key: 'transitions',
      difficulty: 'low',
      content_origin: ['official', 'generated'],
    }
    const { result } = renderHook(() => useReviewQuestions(filters, 3, 10), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.getReviewQuestions).toHaveBeenCalledWith({
      user_token: '', ...filters, page: 3, page_size: 10,
    })
  })

  it('refetches when filters or page change', async () => {
    const { rerender } = renderHook(
      ({ domain, page }) => useReviewQuestions({ domain }, page),
      { initialProps: { domain: 'reading', page: 1 }, wrapper: makeWrapper() },
    )
    await waitFor(() => expect(mockedApi.getReviewQuestions).toHaveBeenCalledTimes(1))

    rerender({ domain: 'grammar', page: 2 })
    await waitFor(() => expect(mockedApi.getReviewQuestions).toHaveBeenCalledTimes(2))
    expect(mockedApi.getReviewQuestions).toHaveBeenLastCalledWith(
      expect.objectContaining({ domain: 'grammar', page: 2 }),
    )
  })
})

describe('useReviewFilters', () => {
  it('loads filters for the current student token', async () => {
    const { result } = renderHook(() => useReviewFilters(), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.getReviewFilters).toHaveBeenCalledWith('')
  })
})
