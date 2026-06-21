import { describe, expect, it, vi } from 'vitest'
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
    expect(screen.getByText('Backend Grammar Keys')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Verb Tense Consistency' }))

    await waitFor(() => {
      expect(taggedSpan).toHaveStyle({ borderBottomWidth: '2.5px' })
    })
  })
})
