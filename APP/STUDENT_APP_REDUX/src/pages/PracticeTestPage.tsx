import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import { PracticeTestRunner, type PracticeQuestion } from '../components/practice/PracticeTestRunner'
import { getUserToken } from '../auth/authStore'

const PRACTICE_TEST_SECONDS = 32 * 60
const MAX_QUESTIONS = 27

type PageState = 'idle' | 'loading' | 'running' | 'done'

export function PracticeTestPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [state, setState] = useState<PageState>('idle')
  const [questions, setQuestions] = useState<PracticeQuestion[]>([])
  const [error, setError] = useState<string | null>(null)

  const requestedCount = parseInt(params.get('questions') ?? '27', 10)
  const questionCount = Math.min(
    MAX_QUESTIONS,
    Number.isFinite(requestedCount) && requestedCount > 0 ? requestedCount : MAX_QUESTIONS,
  )

  async function startTest() {
    setState('loading')
    setError(null)
    try {
      const data = await api.getQuestions({ limit: questionCount, mode: 'test', randomize: true })
      const qs: PracticeQuestion[] = (data.items ?? data.questions ?? []).map((q: any) => ({
        id: q.id,
        current_question_text: q.current_question_text,
        current_passage_text: q.current_passage_text ?? null,
        options: q.options ?? [],
        domain: q.domain ?? null,
        difficulty_overall: q.difficulty_overall ?? null,
        grammar_focus_key: q.grammar_focus_key ?? null,
        reading_focus_key: q.reading_focus_key ?? null,
      }))
      if (qs.length === 0) {
        setError('No questions available. Please try again.')
        setState('idle')
        return
      }
      setQuestions(qs)
      setState('running')
    } catch {
      setError('Failed to load questions. Please try again.')
      setState('idle')
    }
  }

  if (state === 'running') {
    return (
      <PracticeTestRunner
        questions={questions}
        timeLimitSeconds={PRACTICE_TEST_SECONDS}
        userToken={getUserToken()}
        onComplete={() => setState('done')}
      />
    )
  }

  if (state === 'done') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.28, ease: 'easeOut' }}
          className="bg-white border border-gray-200 rounded-2xl p-8 max-w-sm w-full text-center shadow-sm"
        >
          <div className="text-5xl mb-4">✓</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Test Complete</h2>
          <p className="text-gray-500 text-sm mb-6">Your answers have been submitted.</p>
          <button
            onClick={() => navigate('/')}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition"
          >
            Back to Dashboard
          </button>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← Back
        </button>
        <span className="text-gray-800 font-semibold">Practice Test</span>
        <span className="ml-auto text-xs text-gray-400">
          {questionCount} questions · 32 min
        </span>
      </header>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.25, 0, 0, 1] }}
        className="max-w-lg mx-auto px-4 py-6 space-y-4"
      >
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="font-semibold text-gray-800 mb-1">Practice Test</h3>
          <p className="text-gray-500 text-sm">
            {questionCount} verbal questions · 32 minutes · auto-submits when time is up
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3 text-center">
          {[
            { label: 'Questions', value: questionCount },
            { label: 'Time limit', value: '32m' },
            { label: 'Format', value: 'Verbal' },
          ].map(({ label, value }) => (
            <div key={label} className="bg-gray-50 rounded-xl p-3">
              <div className="text-xl font-bold text-gray-800">{value}</div>
              <div className="text-xs text-gray-400 mt-0.5">{label}</div>
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-red-600 text-center">{error}</p>}

        <button
          onClick={startTest}
          disabled={state === 'loading'}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition"
        >
          {state === 'loading' ? 'Loading questions…' : 'Start Test'}
        </button>
      </motion.div>
    </div>
  )
}
