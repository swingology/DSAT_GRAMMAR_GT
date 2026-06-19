import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { useSubmitAnswer } from '../../hooks/useDashboardData'

const DEFAULT_DURATION_SECONDS = 32 * 60
const DEFAULT_QUESTIONS = 27

type TestState = 'idle' | 'running' | 'review' | 'done'

interface TestQuestion {
  id: string
  current_question_text: string
  options: Array<{ label: string; text: string }>
  explanation_short?: string
  grammar_focus_key?: string
  reading_focus_key?: string
  domain?: string
  // is_correct populated after submit
  _isCorrect?: boolean
}

function Timer({ seconds, onExpire }: { seconds: number; onExpire: () => void }) {
  const [remaining, setRemaining] = useState(seconds)
  const ref = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    ref.current = setInterval(() => {
      setRemaining((s) => {
        if (s <= 1) {
          clearInterval(ref.current!)
          onExpire()
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(ref.current!)
  }, [])

  const m = Math.floor(remaining / 60)
  const s = remaining % 60
  const urgent = remaining < 5 * 60
  return (
    <span className={`font-mono text-sm font-bold ${urgent ? 'text-red-600' : 'text-gray-700'}`}>
      {m}:{String(s).padStart(2, '0')}
    </span>
  )
}

function TestRunner({
  questions,
  durationSeconds,
  onSubmit,
}: {
  questions: TestQuestion[]
  durationSeconds: number
  onSubmit: (answers: Record<string, string>) => void
}) {
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const submitAnswer = useSubmitAnswer()
  const q = questions[current]

  function selectOption(label: string) {
    if (answers[q.id]) return
    const newAnswers = { ...answers, [q.id]: label }
    setAnswers(newAnswers)
    submitAnswer.mutate({
      question_id: q.id,
      selected_option_label: label,
      missed_grammar_focus_key: q.grammar_focus_key,
      missed_reading_focus_key: q.reading_focus_key,
    })
  }

  const answered = Object.keys(answers).length
  const progress = Math.round((answered / questions.length) * 100)

  return (
    <div>
      {/* Header bar */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-gray-500">
          {current + 1} / {questions.length}
        </span>
        <Timer seconds={durationSeconds} onExpire={() => onSubmit(answers)} />
        <button
          onClick={() => onSubmit(answers)}
          className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 font-medium transition"
        >
          Submit
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-100 rounded-full mb-5 overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Question */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-4">
        {q.domain && (
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">{q.domain}</p>
        )}
        <p className="text-gray-800 leading-relaxed mb-5">{q.current_question_text}</p>
        <div className="space-y-2">
          {q.options.map((opt) => {
            const isSelected = answers[q.id] === opt.label
            return (
              <button
                key={opt.label}
                onClick={() => selectOption(opt.label)}
                className={[
                  'w-full text-left p-3 rounded-lg border text-sm transition-all',
                  isSelected
                    ? 'bg-blue-50 border-blue-400 text-blue-800'
                    : 'border-gray-200 hover:bg-blue-50 hover:border-blue-300',
                ].join(' ')}
              >
                {opt.text}
              </button>
            )
          })}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex gap-2">
        <button
          onClick={() => setCurrent(Math.max(0, current - 1))}
          disabled={current === 0}
          className="flex-1 py-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-40 rounded-lg text-sm font-medium transition"
        >
          ← Back
        </button>
        <button
          onClick={() => setCurrent(Math.min(questions.length - 1, current + 1))}
          disabled={current === questions.length - 1}
          className="flex-1 py-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-40 rounded-lg text-sm font-medium transition"
        >
          Next →
        </button>
      </div>

      {/* Question nav dots */}
      <div className="flex flex-wrap gap-1 mt-4">
        {questions.map((q2, i) => (
          <button
            key={q2.id}
            onClick={() => setCurrent(i)}
            className={[
              'w-7 h-7 rounded text-xs font-medium transition',
              i === current ? 'bg-blue-600 text-white' : '',
              answers[q2.id] && i !== current ? 'bg-blue-100 text-blue-700' : '',
              !answers[q2.id] && i !== current ? 'bg-gray-100 text-gray-500 hover:bg-gray-200' : '',
            ]
              .filter(Boolean)
              .join(' ')}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  )
}

function TestResults({
  questions,
  answers,
  onRetry,
}: {
  questions: TestQuestion[]
  answers: Record<string, string>
  onRetry: () => void
}) {
  const [showAll, setShowAll] = useState(false)

  const scored = questions.map((q) => ({
    q,
    userAnswer: answers[q.id] ?? null,
    // is_correct is stored on the question after submit; fall back to false if missing
    correct: q._isCorrect ?? false,
  }))
  const numCorrect = scored.filter((s) => s.correct).length
  const pct = Math.round((numCorrect / questions.length) * 100)
  const display = showAll ? scored : scored.filter((s) => !s.correct)

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.28, ease: 'easeOut' }}
        className="bg-white border border-gray-200 rounded-xl p-6 text-center"
      >
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.12, duration: 0.35, type: 'spring', bounce: 0.4 }}
          className="text-5xl font-bold text-blue-600 mb-2"
        >
          {pct}%
        </motion.div>
        <p className="text-gray-600 text-lg">
          {numCorrect} / {questions.length} correct
        </p>
        <div className="flex gap-3 justify-center mt-4">
          <button
            onClick={onRetry}
            className="px-5 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition"
          >
            New test
          </button>
          <button
            onClick={() => setShowAll((v) => !v)}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition"
          >
            {showAll ? 'Show wrong only' : 'Review all'}
          </button>
        </div>
      </motion.div>

      {display.map(({ q, userAnswer, correct }, i) => (
        <motion.div
          key={q.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + i * 0.04, duration: 0.2, ease: 'easeOut' }}
          className={`bg-white border rounded-xl p-4 ${correct ? 'border-emerald-200' : 'border-red-200'}`}
        >
          <div className="flex items-start gap-2 mb-2">
            <span className={`text-lg ${correct ? 'text-emerald-500' : 'text-red-500'}`}>
              {correct ? '✓' : '✗'}
            </span>
            <p className="text-sm text-gray-700 leading-relaxed">{q.current_question_text}</p>
          </div>
          {!correct && q.options.map((opt) => {
            const isUser = opt.label === userAnswer
            if (!isUser) return null
            return (
              <p
                key={opt.label}
                className="text-xs mt-1 pl-6 text-red-600 line-through"
              >
                ✗ {opt.label}. {opt.text}
              </p>
            )
          })}
          {q.explanation_short && (
            <p className="text-xs text-gray-500 mt-2 pl-6 italic">{q.explanation_short}</p>
          )}
        </motion.div>
      ))}
    </div>
  )
}

export function TestModeTab({
  questionCount = DEFAULT_QUESTIONS,
  durationSeconds = DEFAULT_DURATION_SECONDS,
}: {
  questionCount?: number
  durationSeconds?: number
}) {
  const [state, setState] = useState<TestState>('idle')
  const [answers, setAnswers] = useState<Record<string, string>>({})

  const { data: qData, isLoading, refetch } = useQuery({
    queryKey: ['test-questions', questionCount],
    queryFn: () =>
      api.getQuestions({
        limit: questionCount,
        mode: 'test',
        randomize: true,
      }),
    enabled: false,
  })

  const questions: TestQuestion[] = qData?.questions ?? []

  async function startTest() {
    setAnswers({})
    await refetch()
    setState('running')
  }

  function handleSubmit(finalAnswers: Record<string, string>) {
    setAnswers(finalAnswers)
    setState('done')
  }

  if (state === 'running') {
    if (isLoading || questions.length === 0) {
      return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
    }
    return <TestRunner questions={questions} durationSeconds={durationSeconds} onSubmit={handleSubmit} />
  }

  if (state === 'done') {
    return (
      <TestResults
        questions={questions}
        answers={answers}
        onRetry={() => setState('idle')}
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="font-semibold text-gray-800 mb-1">Timed Practice Module</h3>
        <p className="text-gray-500 text-sm">
          {questionCount} verbal questions · {Math.round(durationSeconds / 60)} minutes · mirrors real DSAT
        </p>
      </div>
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: 'Questions', value: questionCount },
          { label: 'Time limit', value: `${Math.round(durationSeconds / 60)}m` },
          { label: 'Format', value: 'Verbal' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-50 rounded-xl p-3">
            <div className="text-xl font-bold text-gray-800">{value}</div>
            <div className="text-xs text-gray-400 mt-0.5">{label}</div>
          </div>
        ))}
      </div>
      <button
        onClick={startTest}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition"
      >
        Start Test
      </button>
    </div>
  )
}
