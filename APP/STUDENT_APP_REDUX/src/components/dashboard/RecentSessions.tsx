import { useRecommendations, useStats } from '../../hooks/useDashboardData'

export function RecentSessions() {
  const { data: recs } = useRecommendations()
  const { data: stats, isLoading } = useStats(recs?.user_id)

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  // Backend does not yet expose a session-history endpoint.
  // Show summary stats as a placeholder until that endpoint ships.
  if (!stats) {
    return (
      <p className="text-sm text-gray-400 text-center py-4">
        No session history available yet.
      </p>
    )
  }

  const accuracy = stats.accuracy != null ? `${Math.round(stats.accuracy * 100)}%` : '—'

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between bg-gray-50 rounded-xl px-4 py-3">
        <div>
          <p className="text-sm font-medium text-gray-800">All-time</p>
          <p className="text-xs text-gray-400 mt-0.5">
            {stats.total_attempts} attempts · {stats.correct_count} correct
          </p>
        </div>
        <span className="text-lg font-bold text-blue-600">{accuracy}</span>
      </div>
      {stats.weekly_attempts != null && (
        <div className="flex items-center justify-between bg-gray-50 rounded-xl px-4 py-3">
          <div>
            <p className="text-sm font-medium text-gray-800">This week</p>
            <p className="text-xs text-gray-400 mt-0.5">{stats.weekly_attempts} questions answered</p>
          </div>
          <span className="text-lg font-bold text-emerald-600">+{stats.weekly_attempts}</span>
        </div>
      )}
    </div>
  )
}
