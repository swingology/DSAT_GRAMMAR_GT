import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useRecommendations } from '../hooks/useDashboardData'

export function ConceptSelectorPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useRecommendations()
  const targets = data?.top_targets ?? []

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← Back
        </button>
        <span className="text-gray-800 font-semibold">Pick a Concept</span>
      </header>

      <div className="max-w-lg mx-auto px-4 py-6">
        <p className="text-sm text-gray-500 mb-4">
          Choose a concept to drill. Ranked by weakness score — hardest areas first.
        </p>

        {isLoading && (
          <div className="space-y-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        )}

        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-center">
            <p className="text-red-700 font-medium">Failed to load concepts</p>
          </div>
        )}

        {!isLoading && targets.length === 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
            <p className="text-gray-500">No concepts found.</p>
            <p className="text-gray-400 text-sm mt-1">
              Complete a diagnostic first to build your concept profile.
            </p>
            <button
              onClick={() => navigate('/diagnostic')}
              className="mt-4 px-5 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 transition"
            >
              Run Diagnostic
            </button>
          </div>
        )}

        <div className="space-y-2">
          {targets.map((t, i) => {
            const pct = Math.round(t.weakness_score * 100)
            const barColor =
              pct >= 70 ? 'bg-red-400' : pct >= 40 ? 'bg-amber-400' : 'bg-emerald-400'

            return (
              <motion.button
                key={`${t.domain}-${t.focus_key}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, duration: 0.2, ease: 'easeOut' }}
                onClick={() =>
                  navigate(
                    `/practice/grammar?focus_key=${encodeURIComponent(t.focus_key)}&domain=${encodeURIComponent(t.domain)}`
                  )
                }
                className="w-full text-left bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-blue-300 hover:shadow-sm transition-all group"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-5 flex-shrink-0 font-mono">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700">
                      {t.focus_key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">{t.domain}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${barColor} rounded-full`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono text-gray-400 w-8 text-right">{pct}%</span>
                  </div>
                </div>
              </motion.button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
