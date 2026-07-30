import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { QuestionCard } from '../components/QuestionCard'
import { useQuickPickQuestions } from '../hooks/useQuickPickQuestions'

export function QuickPickPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const domain = searchParams.get('domain') ?? 'grammar'
  const focusKey = searchParams.get('focus_key') ?? ''
  const { questions, isLoading, isError, shortfallNote } = useQuickPickQuestions(domain, focusKey)

  const [index, setIndex] = useState(0)
  const isDone = questions.length > 0 && index >= questions.length

  function handleNext() {
    setIndex((i) => i + 1)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/practice/concepts')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← Back
        </button>
        <span className="text-gray-800 font-semibold">Quick Pick: {focusKey.replace(/_/g, ' ')}</span>
        {!isLoading && !isError && questions.length > 0 && (
          <span className="ml-auto text-xs text-gray-400">
            {Math.min(index + 1, questions.length)} / {questions.length}
          </span>
        )}
      </header>

      <div className="max-w-lg mx-auto px-4 py-6">
        {shortfallNote && (
          <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
            {shortfallNote}
          </p>
        )}

        {isLoading && (
          <div className="space-y-3">
            <div className="h-8 bg-gray-100 rounded animate-pulse w-1/3">Loading quick pick questions...</div>
            <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
          </div>
        )}

        {!isLoading && isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-700 font-medium">Failed to load questions</p>
          </div>
        )}

        {!isLoading && !isError && questions.length === 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
            <p className="text-gray-500">No questions available for this concept.</p>
          </div>
        )}

        {!isLoading && !isError && isDone && (
          <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center">
            <div className="text-5xl mb-4">✓</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Session Complete</h2>
            <p className="text-gray-500 text-sm mb-6">You answered all {questions.length} questions.</p>
            <button
              onClick={() => navigate('/practice/concepts')}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition"
            >
              Back to Concepts
            </button>
          </div>
        )}

        {!isLoading && !isError && !isDone && questions[index] && (
          <QuestionCard question={questions[index]} onNext={handleNext} sourceType="drill" />
        )}
      </div>
    </div>
  )
}
