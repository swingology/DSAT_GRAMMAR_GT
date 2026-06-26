import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../api/client'
import { useDiagnosticTimer } from '../../hooks/useDiagnosticTimer'
import type { DiagnosticQuestion } from '../../types'

interface Props {
  sessionId: string
  questions: DiagnosticQuestion[]
  timeLimitSeconds: number
  userToken: string
  onComplete: () => void
}

type QuestionState = 'unanswered' | 'answered' | 'flagged'

export function DiagnosticTestRunner({
  sessionId,
  questions,
  timeLimitSeconds,
  userToken,
  onComplete,
}: Props) {
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [flags, setFlags] = useState<Set<string>>(new Set())
  const [showConfirm, setShowConfirm] = useState(false)

  const timer = useDiagnosticTimer(timeLimitSeconds)

  const q = questions[current]
  const answered = Object.keys(answers).length
  const unanswered = questions.length - answered

  function questionState(qid: string): QuestionState {
    if (answers[qid]) return 'answered'
    if (flags.has(qid)) return 'flagged'
    return 'unanswered'
  }

  function selectOption(label: string) {
    if (!q) return
    const newAnswers = { ...answers, [q.id]: label }
    setAnswers(newAnswers)

    // Fire-and-forget submit — do NOT use response to reveal correctness
    api.diagnosticSubmit(sessionId, {
      user_token: userToken,
      question_id: q.id,
      selected_option_label: label,
      missed_grammar_focus_key: q.grammar_focus_key ?? undefined,
      missed_reading_focus_key: q.reading_focus_key ?? undefined,
    }).catch(() => {
      // Silent — answer is recorded locally; backend sync is best-effort
    })
  }

  function toggleFlag() {
    if (!q) return
    setFlags((f) => {
      const next = new Set(f)
      if (next.has(q.id)) next.delete(q.id)
      else next.add(q.id)
      return next
    })
  }

  function handleSubmitClick() {
    if (unanswered > 0) {
      setShowConfirm(true)
    } else {
      onComplete()
    }
  }

  if (!q) return null

  const urgent = timer.remaining < 5 * 60
  const timerLabel = timer.isOvertime
    ? `Overtime: ${timer.formatted.slice(1)}`
    : `Time remaining: ${timer.formatted}`

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ── Header ── */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-4 sticky top-0 z-10">
        <span className="text-sm text-gray-500 font-medium">
          {current + 1} / {questions.length}
        </span>
        <div className="flex-1" />
        <span
          className={`font-mono text-sm font-bold tabular-nums ${
            timer.isOvertime
              ? 'text-red-600 animate-pulse'
              : urgent
                ? 'text-red-600'
                : 'text-gray-700'
          }`}
          style={timer.isOvertime ? { animationDuration: '2.4s' } : undefined}
          aria-label={timerLabel}
          title={timerLabel}
        >
          {timer.formatted}
        </span>
        <button
          onClick={handleSubmitClick}
          className="ml-2 text-xs px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
        >
          Submit Test
        </button>
      </header>

      <div className="flex flex-1 gap-4 p-4 max-w-6xl mx-auto w-full">
        {/* ── Question panel ── */}
        <div className="flex-1 min-w-0">
          <motion.div
            key={q.id}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.18 }}
            className="bg-white border border-gray-200 rounded-xl p-6 mb-4"
          >
            {/* Domain badge */}
            {q.domain && (
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3 block">
                {q.domain} {q.difficulty_overall ? `· ${q.difficulty_overall}` : ''}
              </span>
            )}

            {/* Passage */}
            {q.current_passage_text && (
              <div className="text-sm text-gray-600 leading-relaxed bg-gray-50 rounded-lg p-4 mb-4 border border-gray-100">
                {q.current_passage_text}
              </div>
            )}

            {/* Stem */}
            <p className="text-gray-800 leading-relaxed mb-5 text-base">
              {q.current_question_text}
            </p>

            {/* Options — no correctness styling */}
            <div className="space-y-2">
              {q.options.map((opt) => {
                const isSelected = answers[q.id] === opt.label
                return (
                  <button
                    key={opt.label}
                    onClick={() => selectOption(opt.label)}
                    className={[
                      'w-full text-left p-3 rounded-lg border text-sm transition-all flex gap-3 items-start',
                      isSelected
                        ? 'bg-blue-50 border-blue-400 text-blue-800 font-medium'
                        : 'border-gray-200 hover:bg-blue-50 hover:border-blue-300 text-gray-700',
                    ].join(' ')}
                  >
                    <span className="font-semibold shrink-0 w-4">{opt.label}.</span>
                    <span>{opt.text}</span>
                  </button>
                )
              })}
            </div>
          </motion.div>

          {/* ── Nav + Flag ── */}
          <div className="flex gap-2">
            <button
              onClick={() => setCurrent(Math.max(0, current - 1))}
              disabled={current === 0}
              className="flex-1 py-2 bg-white border border-gray-200 hover:bg-gray-50 disabled:opacity-40 rounded-lg text-sm font-medium transition"
            >
              ← Back
            </button>
            <button
              onClick={toggleFlag}
              className={[
                'px-4 py-2 rounded-lg text-sm font-medium border transition',
                flags.has(q.id)
                  ? 'bg-amber-50 border-amber-300 text-amber-700'
                  : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50',
              ].join(' ')}
            >
              {flags.has(q.id) ? '⚑ Flagged' : '⚑ Flag'}
            </button>
            <button
              onClick={() => setCurrent(Math.min(questions.length - 1, current + 1))}
              disabled={current === questions.length - 1}
              className="flex-1 py-2 bg-white border border-gray-200 hover:bg-gray-50 disabled:opacity-40 rounded-lg text-sm font-medium transition"
            >
              Next →
            </button>
          </div>
        </div>

        {/* ── Question palette ── */}
        <aside className="w-48 shrink-0 hidden md:block">
          <div className="bg-white border border-gray-200 rounded-xl p-4 sticky top-20">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Questions
            </p>
            <div className="flex flex-wrap gap-1.5">
              {questions.map((sq, i) => {
                const state = questionState(sq.id)
                const isCurrent = i === current
                return (
                  <button
                    key={sq.id}
                    onClick={() => setCurrent(i)}
                    aria-label={`Question ${i + 1}`}
                    className={[
                      'w-8 h-8 rounded text-xs font-semibold transition',
                      isCurrent ? 'ring-2 ring-blue-500' : '',
                      state === 'answered' && !isCurrent ? 'bg-blue-100 text-blue-700' : '',
                      state === 'flagged' && !isCurrent ? 'bg-amber-100 text-amber-700' : '',
                      state === 'unanswered' && !isCurrent ? 'bg-gray-100 text-gray-500 hover:bg-gray-200' : '',
                      isCurrent ? 'bg-blue-600 text-white' : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                  >
                    {i + 1}
                  </button>
                )
              })}
            </div>

            <div className="mt-4 space-y-1 text-xs text-gray-500">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-blue-100 rounded inline-block" />
                Answered ({answered})
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-amber-100 rounded inline-block" />
                Flagged ({flags.size})
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-gray-100 rounded inline-block" />
                Unanswered ({unanswered})
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* ── Confirm dialog ── */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl p-6 max-w-sm mx-4 shadow-xl"
          >
            <h3 className="font-semibold text-gray-800 mb-2">Submit test?</h3>
            <p className="text-sm text-gray-500 mb-5">
              You have <strong>{unanswered}</strong> unanswered{' '}
              {unanswered === 1 ? 'question' : 'questions'}. You cannot return after submitting.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 transition"
              >
                Keep going
              </button>
              <button
                onClick={() => { setShowConfirm(false); onComplete() }}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition"
              >
                Submit anyway
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
