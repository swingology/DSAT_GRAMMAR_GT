import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './client'

beforeEach(() => {
  vi.restoreAllMocks()
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  }))
})

describe('review API client', () => {
  it('serializes filters, pagination, and CSV arrays', async () => {
    await api.getReviewQuestions({
      user_token: 'student token',
      source_type: ['diagnostic', 'drill'],
      content_origin: ['official', 'generated'],
      source_test_name: 'Bluebook 1',
      page: 2,
      page_size: 10,
    })

    const url = String(vi.mocked(fetch).mock.calls[0][0])
    const parsed = new URL(url, 'http://localhost')
    expect(parsed.pathname).toBe('/api/study/review')
    expect(parsed.searchParams.get('user_token')).toBe('student token')
    expect(parsed.searchParams.get('source_type')).toBe('diagnostic,drill')
    expect(parsed.searchParams.get('content_origin')).toBe('official,generated')
    expect(parsed.searchParams.get('source_test_name')).toBe('Bluebook 1')
    expect(parsed.searchParams.get('page')).toBe('2')
    expect(parsed.searchParams.get('page_size')).toBe('10')
  })

  it('requests student-scoped filter facets', async () => {
    await api.getReviewFilters('student token')

    const url = String(vi.mocked(fetch).mock.calls[0][0])
    const parsed = new URL(url, 'http://localhost')
    expect(parsed.pathname).toBe('/api/study/review/filters')
    expect(parsed.searchParams.get('user_token')).toBe('student token')
  })
})
