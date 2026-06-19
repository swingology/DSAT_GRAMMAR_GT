import { useRecommendations } from '../../hooks/useDashboardData'

export function ConceptWeaknessChart() {
  const { data, isLoading } = useRecommendations()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-8 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  const targets = (data?.top_targets ?? []).slice(0, 8)

  if (targets.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-4">
        No data yet — complete practice sessions to see your concept breakdown.
      </p>
    )
  }

  const maxScore = Math.max(...targets.map((t) => t.weakness_score), 0.01)

  return (
    <div className="space-y-2">
      {targets.map((t, i) => {
        const pct = Math.round((t.weakness_score / maxScore) * 100)
        const barColor =
          pct >= 75 ? 'bg-red-400' : pct >= 45 ? 'bg-amber-400' : 'bg-emerald-400'

        return (
          <div key={`${t.domain}-${t.focus_key}-${i}`} className="flex items-center gap-3">
            <span className="text-xs text-gray-500 w-36 truncate flex-shrink-0 text-right">
              {t.focus_key.replace(/_/g, ' ')}
            </span>
            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${barColor} rounded-full transition-all`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-xs font-mono text-gray-400 w-8 flex-shrink-0">
              {Math.round(t.weakness_score * 100)}%
            </span>
          </div>
        )
      })}
    </div>
  )
}
