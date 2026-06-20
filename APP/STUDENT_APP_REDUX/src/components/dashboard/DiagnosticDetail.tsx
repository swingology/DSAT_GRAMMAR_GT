import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'

const USER_TOKEN = (import.meta as any).env.VITE_TEST_USER_TOKEN || ''

export function DiagnosticDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['diagnostic-detail', sessionId],
    queryFn: () => api.diagnosticDetail(sessionId!, USER_TOKEN),
    enabled: !!sessionId,
  })

  if (isLoading) return <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
  if (isError || !data) return <p className="text-red-500 text-sm">Failed to load session details.</p>

  const pct = data.accuracy != null ? Math.round(data.accuracy * 100) : null
  const date = new Date(data.created_at).toLocaleDateString(undefined, {
    weekday: 'long', month: 'long', day: 'numeric',
  })

  const focusEntries = Object.entries(data.focus_breakdown ?? {}) as [string, { attempted: number; correct: number }][]

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/diagnostic/history')}
          className="text-sm text-blue-600 hover:underline"
        >
          ← History
        </button>
        <span className="text-gray-300">|</span>
        <span className="text-sm text-gray-500">{date}</span>
      </div>

      {/* Score card */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 text-center">
        <div className={`text-5xl font-bold mb-1 ${
          pct == null ? 'text-gray-300'
          : pct >= 70 ? 'text-emerald-600'
          : pct >= 50 ? 'text-amber-500'
          : 'text-red-500'
        }`}>
          {pct != null ? `${pct}%` : '–'}
        </div>
        <p className="text-gray-500 text-sm">{data.correct_count} / {data.total_questions} correct</p>
      </div>

      {/* Focus breakdown */}
      {focusEntries.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-medium mb-3">
            Focus Area Breakdown
          </p>
          <div className="space-y-2">
            {focusEntries.map(([key, stats]) => {
              const acc = stats.attempted > 0 ? Math.round((stats.correct / stats.attempted) * 100) : 0
              return (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{key.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-xs">{stats.correct}/{stats.attempted}</span>
                    <span className={`font-semibold ${
                      acc >= 70 ? 'text-emerald-600' : acc >= 50 ? 'text-amber-500' : 'text-red-500'
                    }`}>{acc}%</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Question results */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <p className="text-xs text-gray-500 uppercase tracking-wide font-medium mb-3">
          Question by Question
        </p>
        <div className="space-y-1.5">
          {(data.question_results ?? []).map((r: any) => (
            <div key={r.question_number} className="flex items-center gap-3 text-sm">
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                r.is_correct ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
              }`}>
                {r.is_correct ? '✓' : '✗'}
              </span>
              <span className="text-gray-500 text-xs">Q{r.question_number}</span>
              {r.focus_area && (
                <span className="text-gray-400 text-xs">{r.focus_area.replace(/_/g, ' ')}</span>
              )}
              <span className="ml-auto text-gray-400 text-xs font-mono">
                {r.selected_option}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => navigate('/')}
          className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition"
        >
          Take Another Diagnostic
        </button>
        <button
          onClick={() => navigate('/diagnostic/history')}
          className="flex-1 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold rounded-xl transition"
        >
          View All History
        </button>
      </div>
    </div>
  )
}
