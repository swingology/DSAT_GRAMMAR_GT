import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useRecommendations, useStimulusCounts } from '../hooks/useDashboardData'

const STIMULUS_TYPE_LABELS: Record<string, string> = {
  sentence_only: 'Sentence Only',
  passage_excerpt: 'Passage Excerpt',
  notes_bullets: 'Notes & Bullets',
  prose_plus_table: 'Prose + Table',
  prose_plus_graph: 'Prose + Graph',
  prose_single: 'Single Passage',
  prose_paired: 'Paired Passages',
  notes_summary: 'Notes Summary',
  poem: 'Poem',
}

type Tab = 'weakness' | 'type'

export function ConceptSelectorPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const limit = searchParams.get('limit') ?? '10'
  const [tab, setTab] = useState<Tab>('weakness')

  const { data: recData, isLoading: recLoading, isError: recError } = useRecommendations()
  const targets = recData?.top_targets ?? []

  const { data: countsData, isLoading: countsLoading, isError: countsError } = useStimulusCounts()
  const sortedCounts = [...(countsData ?? [])].sort((a, b) => b.count - a.count)

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
        <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setTab('weakness')}
            className={`flex-1 text-sm font-medium py-1.5 rounded-md transition ${
              tab === 'weakness' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
            }`}
          >
            By Weakness
          </button>
          <button
            onClick={() => setTab('type')}
            className={`flex-1 text-sm font-medium py-1.5 rounded-md transition ${
              tab === 'type' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
            }`}
          >
            By Type
          </button>
        </div>

        {tab === 'weakness' && (
          <>
            <p className="text-sm text-gray-500 mb-4">
              Choose a concept to drill. Ranked by weakness score — hardest areas first.
            </p>

            {recLoading && (
              <div className="space-y-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            )}

            {recError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-center">
                <p className="text-red-700 font-medium">Failed to load concepts</p>
              </div>
            )}

            {!recLoading && targets.length === 0 && (
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
                        `/practice/grammar?focus_key=${encodeURIComponent(t.focus_key)}&domain=${encodeURIComponent(t.domain)}&limit=${limit}`
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
          </>
        )}

        {tab === 'type' && (
          <>
            <p className="text-sm text-gray-500 mb-4">
              Choose a question type to practice — most available first.
            </p>

            {countsLoading && (
              <div className="space-y-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            )}

            {countsError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-center">
                <p className="text-red-700 font-medium">Failed to load question types</p>
              </div>
            )}

            <div className="space-y-2">
              {sortedCounts.map((c, i) => (
                <motion.button
                  key={c.stimulus_mode_key}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.2, ease: 'easeOut' }}
                  onClick={() =>
                    navigate(
                      `/practice/mixed?stimulus_mode_key=${encodeURIComponent(c.stimulus_mode_key)}&limit=${limit}`
                    )
                  }
                  className="w-full text-left bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-blue-300 hover:shadow-sm transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-5 flex-shrink-0 font-mono">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700">
                        {STIMULUS_TYPE_LABELS[c.stimulus_mode_key] ?? c.stimulus_mode_key}
                      </p>
                    </div>
                    <span className="text-xs text-gray-400 flex-shrink-0">{c.count} questions</span>
                  </div>
                </motion.button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
