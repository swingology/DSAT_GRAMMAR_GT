import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { getUserToken } from '../auth/authStore'

// Must stay a subset of StudentIssueType in backend/app/models/payload.py.
const STUDENT_ISSUE_TYPES = [
  ['missing_graph', 'A graph, table, or image is missing'],
  ['wrong_answer_key', 'The correct answer is wrong'],
  ['bad_options', 'Answer choices are wrong or missing'],
  ['passage_problem', 'The passage is missing or garbled'],
  ['typo_formatting', 'Typo or formatting problem'],
  ['bad_explanation', 'The explanation is wrong or unclear'],
  ['other', 'Something else'],
] as const

type Status = 'idle' | 'sending' | 'sent'

export function ReportIssueButton({ questionId }: { questionId: string }) {
  const [open, setOpen] = useState(false)
  const [issueType, setIssueType] = useState<string>('')
  const [note, setNote] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState('')

  const close = () => {
    setOpen(false)
    setIssueType('')
    setNote('')
    setStatus('idle')
    setError('')
  }

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  const submit = async () => {
    if (!issueType) return
    setStatus('sending')
    setError('')
    try {
      await api.reportQuestionIssue(questionId, {
        user_token: getUserToken(),
        issue_type: issueType,
        note: note.trim() || undefined,
      })
      setStatus('sent')
    } catch (e) {
      setError((e as { detail?: string }).detail || 'Could not send the report. Please try again.')
      setStatus('idle')
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded px-2 py-1 text-xs font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-700"
      >
        Report a problem
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={close}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={`report-title-${questionId}`}
            className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            {status === 'sent' ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-700">Thanks — we'll review this question.</p>
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={close}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <h2 id={`report-title-${questionId}`} className="text-base font-semibold text-gray-800">
                  What's wrong with this question?
                </h2>
                <fieldset className="space-y-1.5">
                  <legend className="sr-only">Problem type</legend>
                  {STUDENT_ISSUE_TYPES.map(([value, label]) => (
                    <label key={value} className="flex items-center gap-2 text-sm text-gray-700">
                      <input
                        type="radio"
                        name={`issue-type-${questionId}`}
                        value={value}
                        checked={issueType === value}
                        onChange={() => setIssueType(value)}
                      />
                      {label}
                    </label>
                  ))}
                </fieldset>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={3}
                  maxLength={1000}
                  aria-label="Details (optional)"
                  placeholder="Details (optional)"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {error && <p className="text-sm text-red-600">{error}</p>}
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={close}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={submit}
                    disabled={!issueType || status === 'sending'}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {status === 'sending' ? 'Sending…' : 'Send report'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
