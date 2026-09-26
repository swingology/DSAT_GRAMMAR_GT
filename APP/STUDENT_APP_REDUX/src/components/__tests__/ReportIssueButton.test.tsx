import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ReportIssueButton } from '../ReportIssueButton'
import { api } from '../../api/client'

vi.mock('../../api/client', () => ({ api: { reportQuestionIssue: vi.fn() } }))
vi.mock('../../auth/authStore', () => ({ getUserToken: () => 'user-token-1' }))

describe('ReportIssueButton', () => {
  it('sends the chosen problem and thanks the student', async () => {
    vi.mocked(api.reportQuestionIssue).mockResolvedValue({ id: 'i-1', status: 'open' })
    render(<ReportIssueButton questionId="q-1" />)

    fireEvent.click(screen.getByText('Report a problem'))
    const send = screen.getByText('Send report')
    expect(send).toBeDisabled()

    fireEvent.click(screen.getByLabelText('The correct answer is wrong'))
    fireEvent.change(screen.getByLabelText('Details (optional)'), { target: { value: ' B is right ' } })
    fireEvent.click(send)

    await waitFor(() => expect(screen.getByText(/we'll review this question/)).toBeInTheDocument())
    expect(api.reportQuestionIssue).toHaveBeenCalledWith('q-1', {
      user_token: 'user-token-1',
      issue_type: 'wrong_answer_key',
      note: 'B is right',
    })
  })

  it('shows the server message and closes on Escape', async () => {
    vi.mocked(api.reportQuestionIssue).mockRejectedValue(
      Object.assign(new Error('409'), { detail: 'You already reported this problem' }),
    )
    render(<ReportIssueButton questionId="q-1" />)
    fireEvent.click(screen.getByText('Report a problem'))
    fireEvent.click(screen.getByLabelText('Something else'))
    fireEvent.click(screen.getByText('Send report'))

    await waitFor(() => expect(screen.getByText('You already reported this problem')).toBeInTheDocument())
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
