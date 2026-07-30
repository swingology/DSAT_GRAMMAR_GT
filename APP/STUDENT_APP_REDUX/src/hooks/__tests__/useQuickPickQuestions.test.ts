import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useQuickPickQuestions } from '../useQuickPickQuestions'
import { api } from '../../api/client'

vi.mock('../../api/client', () => ({
  api: { getQuestions: vi.fn() },
}))

function q(id: string) {
  return { id, current_question_text: `Q ${id}`, options: [{ label: 'A', text: 'x' }] }
}

describe('useQuickPickQuestions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches low/medium/high in a 3/4/3 split for the given concept', async () => {
    vi.mocked(api.getQuestions).mockImplementation(async (params: any) => {
      if (params.difficulty === 'low') return { items: [q('l1'), q('l2'), q('l3')] }
      if (params.difficulty === 'medium') return { items: [q('m1'), q('m2'), q('m3'), q('m4')] }
      if (params.difficulty === 'high') return { items: [q('h1'), q('h2'), q('h3')] }
      return { items: [] }
    })

    const { result } = renderHook(() => useQuickPickQuestions('grammar', 'verb_tense_consistency'))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(api.getQuestions).toHaveBeenCalledWith({
      domain: 'grammar', grammar_focus_key: 'verb_tense_consistency', difficulty: 'low', limit: 3,
    })
    expect(api.getQuestions).toHaveBeenCalledWith({
      domain: 'grammar', grammar_focus_key: 'verb_tense_consistency', difficulty: 'medium', limit: 4,
    })
    expect(api.getQuestions).toHaveBeenCalledWith({
      domain: 'grammar', grammar_focus_key: 'verb_tense_consistency', difficulty: 'high', limit: 3,
    })
    expect(result.current.questions.map((x) => x.id)).toEqual([
      'l1', 'l2', 'l3', 'm1', 'm2', 'm3', 'm4', 'h1', 'h2', 'h3',
    ])
    expect(result.current.shortfallNote).toBeNull()
  })

  it('uses reading_focus_key when domain is reading', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ items: [] })
    renderHook(() => useQuickPickQuestions('reading', 'inference'))

    await waitFor(() => {
      expect(api.getQuestions).toHaveBeenCalledWith(
        expect.objectContaining({ domain: 'reading', reading_focus_key: 'inference' }),
      )
    })
  })

  it('backfills a shortfall from an unfiltered-difficulty call', async () => {
    vi.mocked(api.getQuestions).mockImplementation(async (params: any) => {
      if (params.difficulty === 'low') return { items: [q('l1')] } // only 1 of 3
      if (params.difficulty === 'medium') return { items: [q('m1'), q('m2'), q('m3'), q('m4')] }
      if (params.difficulty === 'high') return { items: [q('h1'), q('h2'), q('h3')] }
      // backfill call: no difficulty param
      return { items: [q('l1'), q('b1'), q('b2')] } // l1 is a dup and must be excluded
    })

    const { result } = renderHook(() => useQuickPickQuestions('grammar', 'verb_tense_consistency'))
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.questions.map((x) => x.id)).toEqual([
      'l1', 'b1', 'b2', 'm1', 'm2', 'm3', 'm4', 'h1', 'h2', 'h3',
    ])
    expect(result.current.shortfallNote).toBeNull()
  })

  it('sets a shortfallNote when fewer than 10 questions exist in total', async () => {
    vi.mocked(api.getQuestions).mockImplementation(async (params: any) => {
      if (params.difficulty === 'low') return { items: [q('l1')] }
      if (params.difficulty === 'medium') return { items: [q('m1'), q('m2')] }
      if (params.difficulty === 'high') return { items: [] }
      return { items: [] } // backfill has nothing more either
    })

    const { result } = renderHook(() => useQuickPickQuestions('grammar', 'rare_focus'))
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.questions).toHaveLength(3)
    expect(result.current.shortfallNote).toBe('Only 3 questions available for this concept.')
  })
})
