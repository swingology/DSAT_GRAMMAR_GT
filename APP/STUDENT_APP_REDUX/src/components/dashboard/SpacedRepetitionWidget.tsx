import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useSRProgress, useSRDue } from '../../hooks/useDashboardData'

const CONFIDENCE_COLORS: Record<string, string> = {
  mastered: 'bg-emerald-100 text-emerald-700',
  proficient: 'bg-blue-100 text-blue-700',
  developing: 'bg-amber-100 text-amber-700',
  novice: 'bg-red-100 text-red-700',
}

interface DueQuestion {
  question_id: string
  days_overdue: number
  confidence_level: string
  last_reviewed_at: string | null
  next_review_at: string | null
  focus_area: string | null
  domain: string | null
}

export function SpacedRepetitionWidget() {
  const { data: progress, isLoading: loadingProgress } = useSRProgress()
  const { data: due, isLoading: loadingDue } = useSRDue(5)
  const navigate = useNavigate()

  if (loadingProgress || loadingDue) {
    return <div className="h-32 bg-gray-100 rounded-2xl animate-pulse" />
  }

  const dueCount = progress?.due_for_review ?? 0
  const totalTracked = progress?.total_tracked ?? 0

  // Show nothing meaningful if no questions tracked yet
  if (totalTracked === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-2xl p-5 text-center">
        <p className="text-sm text-gray-400">
          Complete diagnostics to start tracking review intervals.
        </p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1, duration: 0.25, ease: 'easeOut' }}
      className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden"
    >
      {/* Header */}
      <div className="px-5 pt-5 pb-3 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900 text-sm">Spaced Review</h3>
          <p className="text-xs text-gray-400 mt-0.5">{totalTracked} questions tracked</p>
        </div>
        {dueCount > 0 && (
          <span className="text-xs font-bold bg-blue-600 text-white px-2.5 py-1 rounded-full">
            {dueCount} due
          </span>
        )}
        {dueCount === 0 && (
          <span className="text-xs text-emerald-600 font-medium">All caught up ✓</span>
        )}
      </div>

      {/* Mastery breakdown */}
      <div className="px-5 pb-3 flex gap-2 flex-wrap">
        {[
          { key: 'mastered', label: 'Mastered', count: progress?.mastered_count ?? 0 },
          { key: 'proficient', label: 'Proficient', count: progress?.proficient_count ?? 0 },
          { key: 'developing', label: 'Developing', count: progress?.developing_count ?? 0 },
          { key: 'novice', label: 'Novice', count: progress?.novice_count ?? 0 },
        ]
          .filter((t) => t.count > 0)
          .map((tier) => (
            <span
              key={tier.key}
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${CONFIDENCE_COLORS[tier.key]}`}
            >
              {tier.count} {tier.label}
            </span>
          ))}
      </div>

      {/* Due questions list */}
      {(due?.due_questions?.length ?? 0) > 0 && (
        <div className="border-t border-gray-100 px-5 py-3 space-y-1.5">
          <p className="text-xs text-gray-400 uppercase tracking-wide font-medium mb-2">
            Due for review
          </p>
          {due!.due_questions.slice(0, 5).map((q: DueQuestion) => (
            <div key={q.question_id} className="flex items-center justify-between text-sm">
              <span className="text-gray-600 text-xs truncate">
                {q.focus_area?.replace(/_/g, ' ') ?? 'Question'}
              </span>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span
                  className={`text-xs px-1.5 py-0.5 rounded font-medium ${CONFIDENCE_COLORS[q.confidence_level] ?? 'bg-gray-100 text-gray-500'}`}
                >
                  {q.confidence_level}
                </span>
                {q.days_overdue > 0 && (
                  <span className="text-xs text-red-400">
                    +{q.days_overdue.toFixed(0)}d
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CTA */}
      {dueCount > 0 && (
        <div className="px-5 pb-5 pt-2">
          <button
            onClick={() => navigate('/practice/grammar')}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition"
          >
            Review {dueCount} question{dueCount !== 1 ? 's' : ''}
          </button>
        </div>
      )}
    </motion.div>
  )
}
