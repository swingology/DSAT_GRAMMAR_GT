import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { GrammarPractice } from '../GrammarPractice'
import { api } from '../../api/client'

vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
    submitAnswer: vi.fn(),
  },
}))

describe('GrammarPractice backend passage tokens', () => {
  it('uses backend spans and tags for passage highlighting', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({
      items: [{
        id: 'q-tokenized',
        current_passage_text: 'The researcher had spent years on the project.',
        current_question_text: 'Which choice completes the text?',
        passage_tokens: [
          { text: 'The researcher ', tags: [] },
          { text: 'had spent years', tags: ['verb_form', 'verb_tense_consistency'] },
          { text: ' on the project.', tags: [] },
        ],
        grammar_role_key: 'verb_form',
        grammar_focus_key: 'verb_tense_consistency',
        syntactic_trap_key: null,
        options: [
          { label: 'A', text: 'shares' },
          { label: 'B', text: 'shared' },
        ],
      }],
    })

    render(
      <BrowserRouter>
        <GrammarPractice />
      </BrowserRouter>
    )

    const taggedSpan = await screen.findByText('had spent years')
    expect(screen.getByText('Which choice completes the text?')).toBeInTheDocument()
    expect(screen.getByText('Grammar Concepts')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Verb Tense Consistency' }))

    await waitFor(() => {
      expect(taggedSpan).toHaveStyle({ borderBottomWidth: '2.5px' })
    }, { timeout: 5000 })
  })
})


// ---------------------------------------------------------------------------
// TASK-032 — Frontend integration tests: highlighting with the new span format
//
// Exercises the full GrammarPractice -> useGrammarSession -> QuestionSection /
// GrammarAnalysisSection pipeline against mocked /api/questions responses
// using the Pass 3 data shape (passage_spans summaries + passage_tokens with
// anatomy / concept_tags). No network calls — the API client is mocked.
// ---------------------------------------------------------------------------

// Build a question with the new Pass 3 span shape. `overrides` merges last so
// each test can tailor passage_spans / passage_tokens.
function makeSpanQuestion(overrides: Record<string, any> = {}) {
  return {
    id: 'q-span',
    current_passage_text: 'The cat sat.',
    current_question_text: 'Which choice completes the text?',
    current_correct_option_label: 'B',
    grammar_role_key: 'verb_form',
    grammar_focus_key: 'subject_verb_agreement',
    syntactic_trap_key: null,
    options: [
      { label: 'A', text: 'runs' },
      { label: 'B', text: 'jumps' },
    ],
    ...overrides,
  }
}

async function renderPractice() {
  render(
    <BrowserRouter>
      <GrammarPractice />
    </BrowserRouter>
  )
  // wait for the first question to load before interacting with it
  await screen.findByText('Select the best answer')
}

describe('GrammarPractice passage_spans highlighting (TASK-032)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // 1. concept pill appears only when concepts_present is non-empty
  it('test_concept_key_pill_shown_when_concepts_present', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({
      items: [makeSpanQuestion({
        passage_spans: {
          label: 'SVA: subject + main_verb',
          anatomy_present: [],
          concepts_present: ['subject_verb_agreement'],
        },
        passage_tokens: [
          { text: 'The ', anatomy: [], concept_tags: [] },
          { text: 'cat', anatomy: ['subject'], concept_tags: [] },
          { text: 'sat', anatomy: ['main_verb'], concept_tags: ['subject_verb_agreement'] },
          { text: '.', anatomy: [], concept_tags: [] },
        ],
      })],
    })

    await renderPractice()

    // "Grammar Concepts" group is rendered because concepts_present is non-empty
    expect(screen.getByText('Grammar Concepts')).toBeInTheDocument()
    // The concept pill labelled "Subject Verb Agreement" is present
    expect(
      screen.getByRole('button', { name: 'Subject Verb Agreement' })
    ).toBeInTheDocument()
  })

  // 2. anatomy pills are filtered to only those represented in the passage.
  //    With passage_spans omitted, the local tokenizer fallback tags "The cat
  //    sat." with only `subject` (no prepositional phrase), so only the Subject
  //    pill renders — never the full SYNTAX_ANATOMY_KEYS catalog.
  it('test_anatomy_pills_filtered_to_passage', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({
      // passage_spans omitted -> null; passage_tokens omitted -> local
      // tokenizer. No concept tags -> no Grammar Concepts group.
      items: [makeSpanQuestion({ passage_spans: null, passage_tokens: undefined })],
    })

    await renderPractice()

    // Sentence Anatomy group renders because `subject` is present
    expect(screen.getByText('Sentence Anatomy')).toBeInTheDocument()
    // The Subject pill (present in the passage) is rendered
    expect(
      screen.getByRole('button', { name: 'Subject' })
    ).toBeInTheDocument()
    // Prepositional Phrase is NOT in this passage -> pill is omitted
    expect(
      screen.queryByRole('button', { name: 'Prepositional Phrase' })
    ).not.toBeInTheDocument()
    // No concept keys derived -> Grammar Concepts group is absent
    expect(screen.queryByText('Grammar Concepts')).not.toBeInTheDocument()
  })

  // 3. clicking a concept pill highlights the matching span
  it('test_clicking_concept_key_highlights_span', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({
      items: [makeSpanQuestion({
        passage_spans: {
          label: 'SVA: subject + main_verb',
          anatomy_present: [],
          concepts_present: ['subject_verb_agreement'],
        },
        passage_tokens: [
          { text: 'The ', anatomy: [], concept_tags: [] },
          { text: 'cat', anatomy: ['subject'], concept_tags: [] },
          { text: 'sat', anatomy: ['main_verb'], concept_tags: ['subject_verb_agreement'] },
          { text: '.', anatomy: [], concept_tags: [] },
        ],
      })],
    })

    await renderPractice()

    const taggedSpan = screen.getByText('sat')
    // before click: no highlight border
    expect(taggedSpan).not.toHaveStyle({ borderBottomWidth: '2.5px' })

    fireEvent.click(screen.getByRole('button', { name: 'Subject Verb Agreement' }))

    await waitFor(() => {
      expect(taggedSpan).toHaveStyle({ borderBottomWidth: '2.5px' })
    }, { timeout: 5000 })
  })

  // 4. clicking an anatomy pill highlights the matching span
  it('test_clicking_anatomy_key_highlights_span', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({
      items: [makeSpanQuestion({
        current_passage_text: 'In the morning, she ran.',
        passage_spans: {
          label: 'Modifier: prepositional_phrase',
          anatomy_present: ['prepositional_phrase'],
          concepts_present: [],
        },
        passage_tokens: [
          { text: 'In the morning', anatomy: ['prepositional_phrase'], concept_tags: [] },
          { text: ', she ran.', anatomy: [], concept_tags: [] },
        ],
      })],
    })

    await renderPractice()

    const taggedSpan = screen.getByText('In the morning')
    expect(taggedSpan).not.toHaveStyle({ borderBottomWidth: '2.5px' })

    fireEvent.click(screen.getByRole('button', { name: 'Prepositional Phrase' }))

    await waitFor(() => {
      expect(taggedSpan).toHaveStyle({ borderBottomWidth: '2.5px' })
    }, { timeout: 5000 })
  })

  // 5. active pill has inverted colors — background becomes the key color,
  //    text becomes white
  it('test_active_pill_has_inverted_colors', async () => {
    vi.mocked(api.getQuestions).mockResolvedValueOnce({
      items: [makeSpanQuestion({
        current_passage_text: 'In the morning, she ran.',
        passage_spans: {
          label: 'Modifier: prepositional_phrase',
          anatomy_present: ['prepositional_phrase'],
          concepts_present: [],
        },
        passage_tokens: [
          { text: 'In the morning', anatomy: ['prepositional_phrase'], concept_tags: [] },
          { text: ', she ran.', anatomy: [], concept_tags: [] },
        ],
      })],
    })

    await renderPractice()

    const pill = screen.getByRole('button', { name: 'Prepositional Phrase' })
    // inactive: not active class
    expect(pill).not.toHaveClass('active')

    fireEvent.click(pill)

    // active: background == border color (both are key.color — the invert),
    // and text inverts to white
    await waitFor(() => {
      expect(pill).toHaveClass('active')
      expect(pill.style.backgroundColor).toBe(pill.style.borderColor)
      expect(pill.style.color).toBe('white')
    }, { timeout: 5000 })
  })
})