import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { getUserToken } from '../auth/authStore'
import { QuestionCard, type Question } from '../components/QuestionCard'

export function MixedPracticePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const limit = Math.min(50, Math.max(1, parseInt(searchParams.get('limit') ?? '10', 10) || 10))
  const stimulusModeKey = searchParams.get('stimulus_mode_key') ?? undefined
  // Identity for seen-exclusion: without user_token the backend skips the
  // "already answered" filter, so the same question would repeat every fetch.
  const userToken = getUserToken()
  const [qIndex, setQIndex] = useState(0)
  const [answered, setAnswered] = useState(0)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['mixed-practice', qIndex, stimulusModeKey, userToken],
    queryFn: () =>
      api.getQuestions({
        limit: 1,
        mode: 'practice',
        randomize: true,
        ...(stimulusModeKey ? { stimulus_mode_key: stimulusModeKey } : {}),
        ...(userToken ? { user_token: userToken } : {}),
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

        {question && <QuestionCard question={question} onNext={handleNext} sourceType="practice" />}
      </div>
    </div>
  )
}
