import { describe, it, expect } from 'vitest'
import { assignKeyColor, activeKeyStyle, inactiveKeyStyle } from '../keyColors'

describe('assignKeyColor', () => {
  it('returns a color and lightBg for anatomy keys', () => {
    const { color, lightBg } = assignKeyColor('subject', 'anatomy')
    expect(color).toMatch(/^hsl\(\d+, 50%, 32%\)$/)
    expect(lightBg).toMatch(/^hsl\(\d+, 40%, 93%\)$/)
  })

  it('returns a color and lightBg for concept keys', () => {
    const { color, lightBg } = assignKeyColor('subject_verb_agreement', 'concept')
    expect(color).toMatch(/^hsl\(\d+, 70%, 26%\)$/)
    expect(lightBg).toMatch(/^hsl\(\d+, 65%, 89%\)$/)
  })

  it('is deterministic — same id + category always returns same value', () => {
    const a = assignKeyColor('main_verb', 'anatomy')
    const b = assignKeyColor('main_verb', 'anatomy')
    expect(a.color).toBe(b.color)
    expect(a.lightBg).toBe(b.lightBg)
  })

  it('anatomy hue is in the 10–178° range', () => {
    const ids = ['subject', 'main_verb', 'subordinate_clause', 'relative_clause', 'appositive']
    for (const id of ids) {
      const { color } = assignKeyColor(id, 'anatomy')
      const hue = parseInt(color.match(/hsl\((\d+)/)![1])
      expect(hue).toBeGreaterThanOrEqual(10)
      expect(hue).toBeLessThanOrEqual(178)
    }
  })

  it('concept hue is in the 182–355° range', () => {
    const ids = ['subject_verb_agreement', 'transition_logic', 'pronoun_antecedent_agreement']
    for (const id of ids) {
      const { color } = assignKeyColor(id, 'concept')
      const hue = parseInt(color.match(/hsl\((\d+)/)![1])
      expect(hue).toBeGreaterThanOrEqual(182)
      expect(hue).toBeLessThanOrEqual(355)
    }
  })

  it('different ids produce different colors (low collision)', () => {
    const ids = ['subject', 'main_verb', 'subordinate_clause', 'relative_clause', 'appositive']
    const colors = ids.map((id) => assignKeyColor(id, 'anatomy').color)
    const unique = new Set(colors)
    expect(unique.size).toBe(ids.length)
  })

  it('anatomy and concept produce different hue ranges', () => {
    const id = 'subject_verb_agreement'
    const anatomy = assignKeyColor(id, 'anatomy')
    const concept = assignKeyColor(id, 'concept')
    expect(anatomy.color).not.toBe(concept.color)
  })
})

describe('activeKeyStyle', () => {
  it('returns white text on the key color', () => {
    const style = activeKeyStyle('#1d4ed8')
    expect(style.backgroundColor).toBe('#1d4ed8')
    expect(style.color).toBe('#ffffff')
    expect(style.borderColor).toBe('#1d4ed8')
  })
})

describe('inactiveKeyStyle', () => {
  it('returns light background with colored text', () => {
    const style = inactiveKeyStyle('#1d4ed8', '#eff6ff')
    expect(style.backgroundColor).toBe('#eff6ff')
    expect(style.color).toBe('#1d4ed8')
    expect(style.borderColor).toBe('#1d4ed8')
  })
})
