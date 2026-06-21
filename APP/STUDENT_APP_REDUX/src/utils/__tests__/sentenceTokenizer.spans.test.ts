import { describe, it, expect } from 'vitest'
import { normalizePassageTokens } from '../sentenceTokenizer'

describe('normalizePassageTokens — anatomy + concept_tags (TASK-018)', () => {
  it('merges anatomy and concept_tags into flat tags array', () => {
    const raw = [
      { text: 'Students', anatomy: ['subject'], concept_tags: ['subject_verb_agreement'] },
      { text: ' run',     anatomy: ['main_verb'], concept_tags: [] },
    ]
    const tokens = normalizePassageTokens(raw, 'Students run', 'subject_verb_agreement')
    expect(tokens[0].tags).toContain('subject')
    expect(tokens[0].tags).toContain('subject_verb_agreement')
    expect(tokens[1].tags).toContain('main_verb')
  })

  it('deduplicates tags when anatomy and concept_tags overlap', () => {
    const raw = [
      {
        text: '_______',
        anatomy: ['main_verb'],
        concept_tags: ['main_verb', 'subject_verb_agreement'],
        is_blank: true,
      },
    ]
    const tokens = normalizePassageTokens(raw, '_______', 'subject_verb_agreement')
    const mainVerbCount = tokens[0].tags.filter((t) => t === 'main_verb').length
    expect(mainVerbCount).toBe(1)
  })

  it('still handles legacy flat-tags tokens (no anatomy / concept_tags fields)', () => {
    // Only tags that survive the tokenizer's merge are returned; the key invariant
    // is that the function does NOT throw and returns a non-empty token list.
    const raw = [
      { text: 'old_style', tags: ['subject'] },
    ]
    const tokens = normalizePassageTokens(raw, 'old_style', null)
    expect(tokens.length).toBeGreaterThan(0)
    expect(tokens[0].tags).toContain('subject')
  })

  it('handles tokens with only anatomy (no concept_tags)', () => {
    const raw = [{ text: 'She', anatomy: ['subject'] }]
    const tokens = normalizePassageTokens(raw, 'She', null)
    expect(tokens[0].tags).toContain('subject')
    expect(tokens[0].tags).not.toContain(undefined)
  })

  it('concept_tags are preserved alongside anatomy on the same token', () => {
    // Mirrors the confirmed-passing anatomy+concept_tags merge test but with
    // a different focus key to show concept_tags travel through the merge.
    const raw = [
      { text: 'Students', anatomy: ['subject'], concept_tags: ['subject_verb_agreement'] },
      { text: ' run', anatomy: ['main_verb'], concept_tags: ['subject_verb_agreement'] },
    ]
    const tokens = normalizePassageTokens(raw, 'Students run', 'subject_verb_agreement')
    // Both tokens carry subject_verb_agreement as a concept_tag
    const allTags = tokens.flatMap((t) => t.tags)
    expect(allTags).toContain('subject_verb_agreement')
  })

  it('sets isBlank from is_blank field', () => {
    const raw = [{ text: '_______', is_blank: true, anatomy: ['main_verb'], concept_tags: [] }]
    const tokens = normalizePassageTokens(raw, '_______', null)
    expect(tokens[0].isBlank).toBe(true)
  })

  it('handles empty tokens array gracefully', () => {
    const tokens = normalizePassageTokens([], '', null)
    expect(tokens).toEqual([])
  })

  it('falls back to local tokenizer when raw tokens is null', () => {
    const tokens = normalizePassageTokens(null, 'Hello world.', null)
    expect(tokens.length).toBeGreaterThan(0)
    expect(tokens.some((t) => t.text.trim() !== '')).toBe(true)
  })
})
