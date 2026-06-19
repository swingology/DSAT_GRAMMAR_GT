import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useRecommendations } from '../../hooks/useDashboardData'

export function DiagnosticCard() {
  const navigate = useNavigate()
  const { data: recs, isLoading } = useRecommendations()

  const hasHistory = (recs?.top_targets?.length ?? 0) > 0
  const topTarget = recs?.top_targets?.[0]
  const mode = hasHistory ? 'adaptive' : 'baseline'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08, duration: 0.25, ease: 'easeOut' }}
      className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden"
    >
      <div className="p-5">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-xl bg-violet-100 flex items-center justify-center text-2xl flex-shrink-0">
            🎯
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-gray-900 text-base">Diagnostic Test</h3>
            {isLoading ? (
              <div className="h-3 w-32 bg-gray-100 rounded animate-pulse mt-1" />
            ) : (
              <p className="text-gray-500 text-sm">
                {mode === 'baseline' ? 'First-time baseline' : 'Adaptive · weak areas'}
              </p>
            )}
          </div>
        </div>

        {!isLoading && (
          <div className="bg-gray-50 rounded-xl p-3 mb-4 text-sm">
            {mode === 'baseline' ? (
              <p className="text-gray-600">
                <span className="font-medium text-violet-700">Baseline mode</span> — 20–30 questions
                across all concept areas to build your initial profile.
              </p>
            ) : (
              <p className="text-gray-600">
                <span className="font-medium text-violet-700">Adaptive mode</span> — targets your top
                weak areas, starting with{' '}
                <span className="font-medium text-gray-800">
                  {topTarget?.focus_key?.replace(/_/g, ' ')}
                </span>
                .
              </p>
            )}
          </div>
        )}

        <button
          onClick={() => navigate('/diagnostic')}
          disabled={isLoading}
          className="w-full py-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-gray-200 text-white font-semibold rounded-xl text-sm transition"
        >
          Start Diagnostic
        </button>
      </div>
    </motion.div>
  )
}
