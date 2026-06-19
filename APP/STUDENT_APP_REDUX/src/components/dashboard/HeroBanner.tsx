import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useRecommendations, useStats } from '../../hooks/useDashboardData'

function StatChip({
  label,
  value,
  loading,
}: {
  label: string
  value: string | number | undefined
  loading?: boolean
}) {
  return (
    <div className="flex flex-col items-center bg-white/60 backdrop-blur-sm rounded-xl px-4 py-3 min-w-[80px]">
      {loading ? (
        <div className="h-6 w-12 bg-white/40 rounded animate-pulse mb-1" />
      ) : (
        <span className="text-xl font-bold text-white drop-shadow-sm">
          {value ?? '—'}
        </span>
      )}
      <span className="text-xs text-blue-100 font-medium text-center leading-tight mt-0.5">
        {label}
      </span>
    </div>
  )
}

export function HeroBanner() {
  const navigate = useNavigate()
  const { data: recs, isLoading: recsLoading } = useRecommendations()
  const userId = recs?.user_id
  const { data: stats, isLoading: statsLoading } = useStats(userId)

  const isLoading = recsLoading
  const isFirstTime =
    !recsLoading && (!recs?.top_targets || recs.top_targets.length === 0)
  const topConcept = recs?.top_targets?.[0]?.focus_key?.replace(/_/g, ' ') ?? null
  const accuracy = stats?.accuracy != null ? `${Math.round(stats.accuracy * 100)}%` : undefined
  const weeklyAttempts = stats?.weekly_attempts
  const streak = stats?.streak_days

  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0, 0, 1] }}
      className="rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 px-5 pt-5 pb-6 mb-6 shadow-md"
    >
      {isLoading ? (
        <div className="py-2">
          <div className="h-5 w-32 bg-white/20 rounded-lg animate-pulse mb-3" />
          <div className="flex gap-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex-1 h-16 bg-white/20 rounded-xl animate-pulse" />
            ))}
          </div>
        </div>
      ) : isFirstTime ? (
        <div className="text-center py-2">
          <h2 className="text-xl font-bold text-white mb-1">Welcome to DSAT Prep</h2>
          <p className="text-blue-100 text-sm mb-4">
            Start with a diagnostic to build your personalized study plan.
          </p>
          <button
            onClick={() => navigate('/diagnostic')}
            className="px-6 py-2 bg-white text-blue-700 rounded-lg font-semibold text-sm hover:bg-blue-50 transition shadow-sm"
          >
            Start Diagnostic →
          </button>
        </div>
      ) : (
        <>
          <h2 className="text-white font-bold text-lg mb-1">Your Progress</h2>
          {topConcept && (
            <p className="text-blue-100 text-sm mb-4">
              Focus area: <span className="text-white font-medium">{topConcept}</span>
            </p>
          )}
          <div className="flex gap-2 flex-wrap">
            <StatChip label="Day streak" value={streak} loading={statsLoading} />
            <StatChip label="This week" value={weeklyAttempts} loading={statsLoading} />
            <StatChip label="Accuracy" value={accuracy} loading={statsLoading} />
            <StatChip
              label="Top weak area"
              value={topConcept ?? undefined}
              loading={recsLoading}
            />
          </div>
        </>
      )}
    </motion.div>
  )
}
