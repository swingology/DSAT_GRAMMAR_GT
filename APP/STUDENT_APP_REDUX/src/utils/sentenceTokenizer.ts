// Rule-based sentence tokenizer for grammar practice highlighting.
// Tags tokens with syntax anatomy key IDs so active grammar keys can
// highlight the relevant words in the passage.
//
// Pass 1 — clause and blank detection (state-machine, single pass)
// Pass 2 — structural annotation (prepositional phrases, subject, appositives)
//
// Pass 2 is heuristic and approximate. Exact word-level anatomy annotation
// is tracked as a future backend improvement (see future_features.md §Grammar).

export interface SentenceToken {
  text: string
  tags: string[]
  isBlank: boolean
}

interface BackendPassageToken {
  text?: unknown
  word?: unknown
  tags?: unknown
  anatomy?: unknown
  concept_tags?: unknown
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

// Prepositions that reliably start noun-phrase PPs.
// Excludes words that double as subordinating conjunctions (after/before/since/until/as).
const PREPOSITIONS = new Set([
  'of', 'in', 'at', 'by', 'with', 'from', 'into', 'between', 'among',
  'under', 'over', 'through', 'during', 'across', 'around', 'behind',
  'below', 'beyond', 'beside', 'near', 'via', 'upon', 'within', 'without',
  'against', 'along', 'despite', 'except', 'for', 'on', 'about', 'toward',
  'towards', 'regarding', 'unlike', 'per', 'throughout', 'to',
])

const ARTICLES = new Set(['a', 'an', 'the'])
const COORD_CONJ = new Set(['and', 'but', 'or', 'nor', 'yet', 'so'])

// Blank placeholder patterns
const BLANK_RE = /^_{3,}$|^\[blank\]$/i

// Split text into word tokens, preserving whitespace and punctuation as
// separate elements so the caller can render them inline without gaps.
function splitIntoRawParts(text: string): string[] {
  return text.split(/(\s+|,|;|:|\.|\(|\)|\[blank\]|_+)/).filter((t) => t !== '')
}

function hasClauseTag(tags: string[]): boolean {
  return tags.some(
    (t) =>
      t === 'subordinate_clause' ||
      t === 'subordinating_conj' ||
      t === 'relative_clause' ||
      t === 'main_verb'
  )
}

// Map grammar_focus_key → anatomy + concept tags for the blank slot.
// The blank is not always a verb — transition questions use conjunctive adverbs,
// pronoun questions use pronouns, etc.
function blankTags(grammarFocusKey?: string): string[] {
  switch (grammarFocusKey) {
    case 'transition_logic':
    case 'conjunctive_adverb_usage':
    case 'logical_relationships':
      return ['transition_word', 'conjunctive_adverb', 'transition_logic']

    case 'pronoun_antecedent_agreement':
    case 'pronoun_case':
    case 'pronoun_clarity':
      return ['pronoun', grammarFocusKey]

    case 'determiners_articles':
    case 'noun_countability':
      return ['determiner', grammarFocusKey]

    case 'punctuation_comma':
    case 'semicolon_use':
    case 'colon_dash_use':
    case 'apostrophe_use':
    case 'appositive_punctuation':
    case 'conjunctive_adverb_usage':
      return ['punctuation_mark', grammarFocusKey]

    case 'verb_tense_consistency':
    case 'verb_form':
    case 'subject_verb_agreement':
    case 'voice_active_passive':
    default:
      // Default: treat blank as a verb slot
      return ['main_verb', 'verb_form', 'verb_tense_consistency']
  }
}

export function tokenizeSentence(text: string, grammarFocusKey?: string): SentenceToken[] {
  const parts = splitIntoRawParts(text)

  // ── Pass 1: clause and blank tagging ──────────────────────────────────────
  const tokens: SentenceToken[] = []
  let inSubordinateClause = false
  let inRelativeClause = false
  let relativeClauseCommaCount = 0

  for (const part of parts) {
    if (/^\s+$/.test(part)) {
      tokens.push({ text: part, tags: [], isBlank: false })
      continue
    }

    const word = part.trim().toLowerCase()
    const isBlank = BLANK_RE.test(part.trim())
    const tags: string[] = []

    if (isBlank) {
      tags.push(...blankTags(grammarFocusKey))
      if (inSubordinateClause) tags.push('subordinate_clause')
      if (inRelativeClause) tags.push('relative_clause')
    } else if (part === ',') {
      if (inSubordinateClause) {
        tags.push('subordinate_clause')
        inSubordinateClause = false
      }
      if (inRelativeClause) {
        relativeClauseCommaCount++
        tags.push('relative_clause')
        if (relativeClauseCommaCount >= 2) {
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
      inSubordinateClause = false
    } else if (SUBORDINATING_CONJUNCTIONS.has(word)) {
      inSubordinateClause = true
      tags.push('subordinating_conj', 'subordinate_clause')
    } else if (RELATIVE_PRONOUNS.has(word)) {
      inRelativeClause = true
      relativeClauseCommaCount = 0
      tags.push('relative_clause')
    } else {
      if (inSubordinateClause) tags.push('subordinate_clause')
      if (inRelativeClause) tags.push('relative_clause')
    }

    tokens.push({ text: part, tags, isBlank })
  }

  // ── Pass 2a: prepositional phrase detection ────────────────────────────────
  // A PP starts at a preposition and ends at: another preposition, a clause
  // marker, a blank, or a sentence-level punctuation mark.
  let inPP = false
  for (const token of tokens) {
    const word = token.text.trim().toLowerCase()
    if (/^\s+$/.test(token.text)) continue

    if (hasClauseTag(token.tags) || token.isBlank) {
      inPP = false
      continue
    }
    if (word === ',' || word === ';' || word === '.') {
      inPP = false
      continue
    }
    if (PREPOSITIONS.has(word)) {
      inPP = true
      token.tags.push('prepositional_phrase')
    } else if (inPP) {
      token.tags.push('prepositional_phrase')
    }
  }

  // ── Pass 2b: subject detection ─────────────────────────────────────────────
  // The subject is the initial noun phrase of the sentence. If the sentence
  // opens with a prepositional phrase (introductory PP), skip it and look for
  // the subject after the following comma.
  // Approximate: stops at the first PP, clause, blank, or comma.
  let subjectDone = false
  let skippingIntroductoryPP = false
  let waitingForPostPPComma = false

  for (const token of tokens) {
    if (subjectDone) break
    const word = token.text.trim().toLowerCase()
    if (/^\s+$/.test(token.text)) continue

    const isInPP = token.tags.includes('prepositional_phrase')

    // Detect sentence-opening PP (introductory phrase: "In 2013, ...")
    if (!skippingIntroductoryPP && !waitingForPostPPComma && isInPP) {
      skippingIntroductoryPP = true
      continue
    }
    if (skippingIntroductoryPP) {
      if (isInPP) continue // still in the introductory PP
      if (word === ',') { waitingForPostPPComma = false; skippingIntroductoryPP = false; continue }
      // PP ended without a comma — fall through to subject logic below
      skippingIntroductoryPP = false
    }

    // Now look for the subject: untagged words until any boundary
    const blocksSub =
      token.isBlank ||
      token.tags.length > 0 || // already tagged (PP, clause marker)
      word === ',' ||
      word === ';' ||
      word === '.' ||
      word === '(' ||
      word === ')'

    if (blocksSub) {
      subjectDone = true
    } else {
      token.tags.push('subject')
    }
  }

  // ── Pass 2c: appositive detection ──────────────────────────────────────────
  // An appositive is a noun phrase between two commas that (a) doesn't open a
  // clause and (b) starts with an article (a/an/the). This catches the most
  // common SAT pattern: "Maria Martinez, a Tewa potter, made..."
  let commasSeen = 0
  let inAppositive = false
  let appStart = -1

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i]
    const word = token.text.trim().toLowerCase()

    if (word === '.') { commasSeen = 0; inAppositive = false; appStart = -1; continue }

    if (word === ',') {
      if (!inAppositive) {
        // Peek at next real word to decide if an appositive follows
        let j = i + 1
        while (j < tokens.length && /^\s+$/.test(tokens[j].text)) j++
        const peek = tokens[j]?.text.trim().toLowerCase() ?? ''
        const startsAppositive =
          ARTICLES.has(peek) &&
          !SUBORDINATING_CONJUNCTIONS.has(peek) &&
          !RELATIVE_PRONOUNS.has(peek) &&
          !COORD_CONJ.has(peek)
        if (startsAppositive && commasSeen > 0) {
          inAppositive = true
          appStart = j
        }
        commasSeen++
      } else {
        // Closing comma — tag the collected phrase as appositive
        for (let k = appStart; k < i; k++) {
          const t = tokens[k]
          if (!/^\s+$/.test(t.text) && t.tags.length === 0 && !t.isBlank) {
            t.tags.push('appositive')
          }
        }
        inAppositive = false
        appStart = -1
      }
    }
  }

  return tokens
}

/** Prefer exact backend spans and tags; tokenize locally only for legacy rows. */
export function normalizePassageTokens(
  passageTokens: BackendPassageToken[] | null | undefined,
  fallbackText: string,
  grammarFocusKey?: string | null
): SentenceToken[] {
  if (!Array.isArray(passageTokens) || passageTokens.length === 0) {
    return tokenizeSentence(fallbackText, grammarFocusKey ?? undefined)
  }

  // A single backend token means the backend couldn't identify a specific span
  // and tagged the whole passage as one block. Fall back to the local structural
  // tokenizer so we don't highlight the entire passage when a key is activated.
  // Multiple tokens mean the backend carved out real spans — use those.
  if (passageTokens.length === 1) {
    return tokenizeSentence(fallbackText, grammarFocusKey ?? undefined)
  }

  return passageTokens
    .map((token): SentenceToken | null => {
      const text =
        typeof token.text === 'string'
          ? token.text
          : typeof token.word === 'string'
            ? token.word
            : ''
      if (!text) return null

      const anatomy = Array.isArray(token.anatomy)
        ? (token.anatomy as unknown[]).filter((t): t is string => typeof t === 'string')
        : []
      const conceptTags = Array.isArray(token.concept_tags)
        ? (token.concept_tags as unknown[]).filter((t): t is string => typeof t === 'string')
        : []
      const legacyTags = Array.isArray(token.tags)
        ? (token.tags as unknown[]).filter(
            (t): t is string => typeof t === 'string' && t.length > 0
          )
        : []

      const tags = [...new Set([...anatomy, ...conceptTags, ...legacyTags])]

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
