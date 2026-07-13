import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { DiagnosticReport } from '../components/diagnostic/DiagnosticReport'
import type { DiagnosticResult } from '../types'
import { getUserToken } from '../auth/authStore'

export function DiagnosticDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<DiagnosticResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    api.diagnosticDetail(sessionId, getUserToken())
      .then((data: any) => {
        // Map detail response to DiagnosticResult shape
        setResult({
          session_id: data.session_id,
          total_questions: data.total_questions,
          correct_count: data.correct_count,
          accuracy: data.accuracy ?? 0,
          duration_seconds: data.duration_seconds ?? null,
          weakest_focus_areas: Object.entries(data.focus_breakdown ?? {}).map(
            ([k, v]: any) => ({ focus_key: k, miss_count: v })
          ),
          breakdown: null,
        })
      })
      .catch((e: any) => setError(e?.message ?? 'Could not load session'))
      .finally(() => setLoading(false))
  }, [sessionId])

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/diagnostic/history')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← History
        </button>
        <span className="text-gray-800 font-semibold">Session Detail</span>
      </header>

      {loading && (
        <div className="max-w-lg mx-auto px-4 py-10 space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      )}
      {error && (
        <p className="text-center text-sm text-red-500 mt-10">{error}</p>
      )}
      {!loading && !error && (
        <DiagnosticReport
          result={result}
          sessionId={sessionId ?? ''}
          userToken={getUserToken()}
          onRetake={() => navigate('/diagnostic')}
        />
      )}
    </div>
  )
}
