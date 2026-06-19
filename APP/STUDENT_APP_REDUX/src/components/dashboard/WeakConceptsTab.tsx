import { useRecommendations } from '../../hooks/useDashboardData'
import type { WeaknessTarget } from '../../types'

function scoreBar(score: number) {
  const pct = Math.round(Math.min(score * 100, 100))
  const color =
    pct >= 70 ? 'bg-red-500' : pct >= 40 ? 'bg-amber-400' : 'bg-emerald-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-500 w-8 text-right">{pct}%</span>
    </div>
  )
}

function ConceptCard({ target, rank }: { target: WeaknessTarget; rank: number }) {
  const daysSince = Math.round(target.days_since_last_attempt)
  const lastSeen =
    daysSince === 0 ? 'today' : daysSince === 1 ? 'yesterday' : `${daysSince}d ago`

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-sm transition-all">
      <div className="flex items-start gap-3">
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-100 text-gray-500 text-xs font-bold flex items-center justify-center">
          {rank}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-blue-600 uppercase tracking-wide">
              {target.domain}
            </span>
            <span className="text-xs text-gray-400">·</span>
            <span className="text-xs text-gray-400">{target.difficulty}</span>
          </div>
          <p className="text-sm font-semibold text-gray-800 mb-2 truncate">
            {target.focus_key.replace(/_/g, ' ')}
          </p>
          {scoreBar(target.weakness_score)}
          <div className="flex gap-4 mt-2 text-xs text-gray-500">
            <span>{target.miss_count}/{target.attempt_count} missed</span>
            <span>{Math.round(target.miss_rate * 100)}% miss rate</span>
            <span>last seen {lastSeen}</span>
            {target.inventory_unseen > 0 && (
              <span className="text-emerald-600">{target.inventory_unseen} new Qs</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function WeakConceptsTab() {
  const { data, isLoading, isError, error } = useRecommendations()

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-700 font-medium">Failed to load recommendations</p>
        <p className="text-red-500 text-sm mt-1">{String(error)}</p>
      </div>
    )
  }

  const targets = data?.top_targets ?? []

  if (targets.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
        <p className="text-gray-500 text-lg">No weak concepts found yet.</p>
        <p className="text-gray-400 text-sm mt-1">Complete some practice questions to see your profile.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
          Top {targets.length} weak areas · ranked by weakness score
        </h3>
      </div>
      {targets.map((t, i) => (
        <ConceptCard key={`${t.domain}-${t.focus_key}`} target={t} rank={i + 1} />
      ))}
    </div>
  )
}
