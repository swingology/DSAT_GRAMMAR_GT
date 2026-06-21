// Rule-based sentence tokenizer for grammar practice highlighting.
// Tags tokens with syntax anatomy key IDs so active grammar keys can
// highlight the relevant words in the passage.

export interface SentenceToken {
  text: string
  tags: string[]
  isBlank: boolean
}

interface BackendPassageToken {
  text?: unknown
  word?: unknown
  tags?: unknown
  is_blank?: unknown
  isBlank?: unknown
}

// Words that open a subordinate (dependent) clause
const SUBORDINATING_CONJUNCTIONS = new Set([
  'although', 'because', 'since', 'while', 'when', 'unless', 'if', 'though',
  'after', 'before', 'until', 'as', 'once', 'whereas', 'whether', 'wherever',
  'even', // "even though" — partial; "though" handles the full conjunction
])

// Words that open a relative clause
const RELATIVE_PRONOUNS = new Set(['which', 'who', 'whom', 'whose'])

// Blank placeholder patterns
const BLANK_RE = /^_{3,}$|^\[blank\]$/i

// Split text into word tokens, preserving whitespace and punctuation as
// separate elements so the caller can render them inline without gaps.
function splitIntoRawParts(text: string): string[] {
  // Split on punctuation boundaries while keeping the delimiter tokens
  return text.split(/(\s+|,|;|:|\.|\(|\)|\[blank\]|_+)/).filter((t) => t !== '')
}

export function tokenizeSentence(text: string): SentenceToken[] {
  const parts = splitIntoRawParts(text)
  const tokens: SentenceToken[] = []

  let inSubordinateClause = false
  let inRelativeClause = false
  // Track comma count inside relative clause so we close on the closing comma
  let relativeClauseCommaCount = 0

  for (const part of parts) {
    // Pure whitespace — pass through untagged
    if (/^\s+$/.test(part)) {
      tokens.push({ text: part, tags: [], isBlank: false })
      continue
    }

    const word = part.trim().toLowerCase()
    const isBlank = BLANK_RE.test(part.trim())
    const tags: string[] = []

    if (isBlank) {
      // The blank always represents the tested verb slot
      tags.push('main_verb', 'verb_form', 'verb_tense_consistency')
      if (inSubordinateClause) tags.push('subordinate_clause')
      if (inRelativeClause) tags.push('relative_clause')
    } else if (part === ',') {
      if (inSubordinateClause) {
        // First comma closes the subordinate clause
        tags.push('subordinate_clause')
        inSubordinateClause = false
      }
      if (inRelativeClause) {
        relativeClauseCommaCount++
        tags.push('relative_clause')
        if (relativeClauseCommaCount >= 2) {
          // Closing comma of a non-restrictive relative clause
          inRelativeClause = false
          relativeClauseCommaCount = 0
        }
      }
    } else if (part === '.' || part === ';') {
      if (inRelativeClause) {
        tags.push('relative_clause')
        inRelativeClause = false
        relativeClauseCommaCount = 0
      }
    } else if (SUBORDINATING_CONJUNCTIONS.has(word)) {
      inSubordinateClause = true
      tags.push('subordinating_conj', 'subordinate_clause')
    } else if (RELATIVE_PRONOUNS.has(word)) {
      inRelativeClause = true
      relativeClauseCommaCount = 0
      tags.push('relative_clause')
    } else {
      // Regular word — inherit active clause context
      if (inSubordinateClause) tags.push('subordinate_clause')
      if (inRelativeClause) tags.push('relative_clause')
    }

    tokens.push({ text: part, tags, isBlank })
  }

  return tokens
}

/** Prefer exact backend spans and tags; tokenize locally only for legacy rows. */
export function normalizePassageTokens(
  passageTokens: BackendPassageToken[] | null | undefined,
  fallbackText: string
): SentenceToken[] {
  if (!Array.isArray(passageTokens) || passageTokens.length === 0) {
    return tokenizeSentence(fallbackText)
  }

  return passageTokens
    .map((token): SentenceToken | null => {
      const text = typeof token.text === 'string'
        ? token.text
        : typeof token.word === 'string'
          ? token.word
          : ''
      if (!text) return null

      const tags = Array.isArray(token.tags)
        ? token.tags.filter((tag): tag is string => typeof tag === 'string' && tag.length > 0)
        : []

      return {
        text,
        tags,
        isBlank: token.is_blank === true || token.isBlank === true,
      }
    })
    .filter((token): token is SentenceToken => token !== null)
}

export interface KeyColorInfo {
  id: string
  priority: number
  color: string
  lightBg: string
}

// Return the highest-priority key among a token's tags that is currently active.
export function findActiveKeyForToken(
  tags: string[],
  activeKeys: Set<string>,
  allKeys: KeyColorInfo[]
): KeyColorInfo | null {
  return (
    allKeys
      .filter((k) => tags.includes(k.id) && activeKeys.has(k.id))
      .sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0))[0] ?? null
  )
}
