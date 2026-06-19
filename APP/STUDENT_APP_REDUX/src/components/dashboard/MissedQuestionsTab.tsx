import { useState } from 'react'
import { useMissedQuestions, type MissedQuestionItem } from '../../hooks/useDashboardData'

type SortBy = 'date' | 'miss_count' | 'domain'
type Domain = 'all' | 'grammar' | 'reading'

function MissedCard({ item }: { item: MissedQuestionItem }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          {item.domain && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 capitalize">
              {item.domain}
            </span>
          )}
          {item.focus_key && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
              {item.focus_key.replace(/_/g, ' ')}
            </span>
          )}
          {item.difficulty && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 capitalize">
              {item.difficulty}
            </span>
          )}
        </div>
        <span className="text-xs text-red-500 font-semibold whitespace-nowrap">
          ✗ {item.miss_count}×
        </span>
      </div>

      <p className="text-sm text-gray-800 leading-relaxed line-clamp-3">{item.question_text}</p>

      {(item.user_answer || item.correct_answer) && (
        <div className="mt-2 flex gap-3 text-xs">
          {item.user_answer && (
            <span className="text-red-600">
              You chose: <span className="font-medium">{item.user_answer}</span>
            </span>
          )}
          {item.correct_answer && (
            <span className="text-emerald-700">
              Correct: <span className="font-medium">{item.correct_answer}</span>
            </span>
          )}
        </div>
      )}

      {item.explanation && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="mt-2 text-xs text-blue-600 hover:text-blue-800 transition"
        >
          {expanded ? '▲ Hide explanation' : '▼ Show explanation'}
        </button>
      )}
      {expanded && item.explanation && (
        <p className="mt-2 text-xs text-gray-600 bg-gray-50 rounded-lg p-3 leading-relaxed">
          {item.explanation}
        </p>
      )}

      {item.last_missed_at && (
        <p className="mt-2 text-xs text-gray-400">
          Last missed {new Date(item.last_missed_at).toLocaleDateString()}
        </p>
      )}
    </div>
  )
}

export function MissedQuestionsTab() {
  const [sortBy, setSortBy] = useState<SortBy>('date')
  const [domain, setDomain] = useState<Domain>('all')

  const { data, isLoading, isError } = useMissedQuestions({
    sort_by: sortBy,
    domain: domain === 'all' ? undefined : domain,
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-700 text-sm">Failed to load missed questions. Backend may be offline.</p>
      </div>
    )
  }

  const items = data?.items ?? []

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex gap-2 flex-wrap">
        {/* Domain filter */}
        <div className="flex bg-white border border-gray-200 rounded-lg p-0.5 gap-0.5">
          {(['all', 'grammar', 'reading'] as Domain[]).map((d) => (
            <button
              key={d}
              onClick={() => setDomain(d)}
              className={[
                'px-3 py-1 rounded-md text-xs font-medium transition capitalize',
                domain === d ? 'bg-blue-600 text-white' : 'text-gray-500 hover:text-gray-700',
              ].join(' ')}
            >
              {d}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div className="flex bg-white border border-gray-200 rounded-lg p-0.5 gap-0.5">
          {([
            { id: 'date', label: 'Recent' },
            { id: 'miss_count', label: 'Most missed' },
            { id: 'domain', label: 'Domain' },
          ] as { id: SortBy; label: string }[]).map((s) => (
            <button
              key={s.id}
              onClick={() => setSortBy(s.id)}
              className={[
                'px-3 py-1 rounded-md text-xs font-medium transition',
                sortBy === s.id ? 'bg-blue-600 text-white' : 'text-gray-500 hover:text-gray-700',
              ].join(' ')}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary */}
      {data && (
        <p className="text-xs text-gray-400">
          {data.total} question{data.total !== 1 ? 's' : ''} missed
        </p>
      )}

      {/* List */}
      {items.length === 0 ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-8 text-center">
          <div className="text-3xl mb-3">🎉</div>
          <h3 className="font-semibold text-emerald-900 mb-1">No missed questions</h3>
          <p className="text-emerald-700 text-sm">
            {domain !== 'all' ? `No missed ${domain} questions` : 'Keep it up!'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <MissedCard key={item.question_id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
