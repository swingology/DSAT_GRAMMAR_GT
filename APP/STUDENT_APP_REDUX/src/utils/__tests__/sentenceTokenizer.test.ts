import { describe, expect, it } from 'vitest'
import { normalizePassageTokens } from '../sentenceTokenizer'

describe('normalizePassageTokens', () => {
  it('preserves backend spans, tags, and snake-case blank metadata', () => {
    expect(normalizePassageTokens([
      { word: 'Although', tags: ['subordinate_clause'] },
      { text: ' ________', tags: ['main_verb'], is_blank: true },
    ], 'ignored fallback')).toEqual([
      { text: 'Although', tags: ['subordinate_clause'], isBlank: false },
      { text: ' ________', tags: ['main_verb'], isBlank: true },
    ])
  })

  it('falls back to client tokenization when backend tokens are absent', () => {
    const tokens = normalizePassageTokens(null, 'Although it rained, we left.')
    expect(tokens.some((token) => token.tags.includes('subordinate_clause'))).toBe(true)
  })
})
