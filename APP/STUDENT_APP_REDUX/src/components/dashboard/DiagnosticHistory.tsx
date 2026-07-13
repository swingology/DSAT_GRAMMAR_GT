import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { useNavigate } from 'react-router-dom'
import { getUserToken } from '../../auth/authStore'


export function DiagnosticHistory() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['diagnostic-history'],
    queryFn: () => api.diagnosticHistory(getUserToken()),
  })

  if (isLoading) return <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
  if (isError) return <p className="text-red-500 text-sm">Failed to load diagnostic history.</p>

  const sessions = data?.sessions ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Diagnostic History</h2>
        {data?.average_accuracy != null && (
          <span className="text-sm text-gray-500">
            Avg accuracy: <span className="font-semibold text-blue-600">{Math.round(data.average_accuracy * 100)}%</span>
          </span>
        )}
      </div>

      {data?.improvement_trend != null && (
        <div className={`text-xs px-3 py-1.5 rounded-full inline-block font-medium ${
          data.improvement_trend > 0
            ? 'bg-emerald-50 text-emerald-700'
            : data.improvement_trend < 0
            ? 'bg-red-50 text-red-700'
            : 'bg-gray-100 text-gray-500'
        }`}>
          {data.improvement_trend > 0 ? '↑' : data.improvement_trend < 0 ? '↓' : '→'}{' '}
          {data.improvement_trend > 0 ? 'Improving' : data.improvement_trend < 0 ? 'Declining' : 'Stable'}
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-gray-500 text-sm">No diagnostics completed yet.</p>
          <button
            onClick={() => navigate('/')}
            className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
          >
            Take a Diagnostic
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((s: any) => {
            const pct = s.accuracy != null ? Math.round(s.accuracy * 100) : null
            const date = new Date(s.created_at).toLocaleDateString(undefined, {
              month: 'short', day: 'numeric', year: 'numeric',
            })
            const duration = s.duration_seconds
              ? `${Math.round(s.duration_seconds / 60)}m`
              : null

            return (
              <button
                key={s.session_id}
                onClick={() => navigate(`/diagnostic/${s.session_id}`)}
                className="w-full text-left bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:bg-blue-50 transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{date}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {s.correct_count}/{s.total_questions} correct
                      {duration ? ` · ${duration}` : ''}
                      {s.diagnostic_type ? ` · ${s.diagnostic_type}` : ''}
                    </p>
                  </div>
                  <div className={`text-xl font-bold ${
                    pct == null ? 'text-gray-300'
                    : pct >= 70 ? 'text-emerald-600'
                    : pct >= 50 ? 'text-amber-500'
                    : 'text-red-500'
                  }`}>
                    {pct != null ? `${pct}%` : '–'}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
