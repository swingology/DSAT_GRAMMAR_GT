import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { useSubmitAnswer } from '../hooks/useDashboardData'

interface Question {
  id: string
  current_question_text: string
  options: Array<{ label: string; text: string }>
  explanation_short?: string
  grammar_focus_key?: string
  reading_focus_key?: string
  domain?: string
}

function QuestionCard({
  question,
  onNext,
}: {
  question: Question
  onNext: () => void
}) {
  const [selected, setSelected] = useState<string | null>(null)
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null)
  const submitAnswer = useSubmitAnswer()

  function choose(label: string) {
    if (selected) return
    setSelected(label)
    submitAnswer.mutate(
      {
        question_id: question.id,
        selected_option_label: label,
        source_type: 'practice',
        missed_grammar_focus_key: question.grammar_focus_key,
        missed_reading_focus_key: question.reading_focus_key,
      },
      { onSuccess: (res) => setIsCorrect(res.is_correct) }
    )
  }

  return (
    <motion.div
      key={question.id}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="bg-white border border-gray-200 rounded-xl p-6"
    >
      {question.domain && (
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{question.domain}</p>
      )}
      {(question.grammar_focus_key || question.reading_focus_key) && (
        <p className="text-xs text-blue-500 font-medium mb-3">
          {(question.grammar_focus_key || question.reading_focus_key || '').replace(/_/g, ' ')}
        </p>
      )}
      <p className="text-gray-800 leading-relaxed mb-5">{question.current_question_text}</p>

      <div className="space-y-2">
        {question.options.map((opt) => {
          const isSelected = selected === opt.label
          const showCorrect = isCorrect === true && isSelected
          const showWrong = isCorrect === false && isSelected
          return (
            <button
              key={opt.label}
              onClick={() => choose(opt.label)}
              disabled={!!selected}
              className={[
                'w-full text-left p-3 rounded-lg border text-sm transition-all',
                !selected ? 'hover:bg-blue-50 hover:border-blue-300 border-gray-200' : '',
                showCorrect ? 'bg-emerald-50 border-emerald-400 text-emerald-800' : '',
                showWrong ? 'bg-red-50 border-red-400 text-red-800' : '',
                isSelected && isCorrect === null ? 'bg-blue-50 border-blue-400' : '',
                !isSelected && !!selected ? 'opacity-50 border-gray-200' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <span className="font-mono text-gray-400 mr-2">{opt.label}.</span>
              {opt.text}
            </button>
          )
        })}
      </div>

      {selected && question.explanation_short && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-500 font-medium mb-1">Explanation</p>
          <p className="text-sm text-gray-700">{question.explanation_short}</p>
        </div>
      )}

      {selected && (
        <button
          onClick={onNext}
          className="mt-4 w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl text-sm transition"
        >
          Next Question →
        </button>
      )}
    </motion.div>
  )
}

export function MixedPracticePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const limit = Math.min(50, Math.max(1, parseInt(searchParams.get('limit') ?? '10', 10) || 10))
  const [qIndex, setQIndex] = useState(0)
  const [answered, setAnswered] = useState(0)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['mixed-practice', qIndex],
    queryFn: () =>
      api.getQuestions({
        limit: 1,
        mode: 'practice',
        randomize: true,
      }),
  })

  const question: Question | null = data?.items?.[0] ?? null

  function handleNext() {
    const newAnswered = answered + 1
    setAnswered(newAnswered)
    if (newAnswered >= limit) return
    setQIndex((n) => n + 1)
    refetch()
  }

  if (answered >= limit) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
        <div className="bg-white border border-gray-200 rounded-2xl p-8 max-w-sm w-full text-center shadow-sm">
          <div className="text-5xl mb-4">✓</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Session Complete</h2>
          <p className="text-gray-500 text-sm mb-6">You answered all {limit} questions.</p>
          <button
            onClick={() => navigate('/')}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition"
          >
            Back to Dashboard
          </button>
        </div>
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
        <span className="text-gray-800 font-semibold">Mixed Practice</span>
        <span className="ml-auto text-xs text-gray-400">{answered} / {limit}</span>
      </header>

      <div className="max-w-lg mx-auto px-4 py-6">
        {isLoading && (
          <div className="space-y-3">
            <div className="h-8 bg-gray-100 rounded animate-pulse w-1/3" />
            <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
          </div>
        )}

        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700 font-medium">Failed to load question</p>
            <button
              onClick={() => refetch()}
              className="mt-3 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm transition"
            >
              Try again
            </button>
          </div>
        )}

        {!isLoading && !isError && !question && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
            <p className="text-gray-500">No questions available right now.</p>
          </div>
        )}

        {question && <QuestionCard question={question} onNext={handleNext} />}
      </div>
    </div>
  )
}
