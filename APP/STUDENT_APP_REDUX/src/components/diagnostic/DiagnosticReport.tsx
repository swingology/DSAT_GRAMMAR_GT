import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../../api/client'
import type { DiagnosticResult } from '../../types'

interface Props {
  result: DiagnosticResult | null
  sessionId: string
  userToken: string
  onRetake: () => void
}

function BarRow({ label, correct, total }: { label: string; correct: number; total: number }) {
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-40 shrink-0 text-gray-600 capitalize truncate">{label.replace(/_/g, ' ')}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${pct >= 70 ? 'bg-emerald-400' : pct >= 50 ? 'bg-amber-400' : 'bg-red-400'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-16 text-right text-gray-500 shrink-0">
        {correct}/{total} ({pct}%)
      </span>
    </div>
  )
}

export function DiagnosticReport({ result, sessionId, userToken, onRetake }: Props) {
  const navigate = useNavigate()
  const [section, setSection] = useState<'summary' | 'breakdown' | 'review'>('summary')

  const pct = result ? Math.round(result.accuracy * 100) : 0
  const scoreColor = pct >= 70 ? 'text-emerald-600' : pct >= 50 ? 'text-amber-500' : 'text-red-500'

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
      {/* Score card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-white border border-gray-200 rounded-2xl p-6 text-center"
      >
        <div className={`text-6xl font-black mb-1 ${scoreColor}`}>{pct}%</div>
        <p className="text-gray-500 text-lg">
          {result ? `${result.correct_count} / ${result.total_questions} correct` : '—'}
        </p>
        {result?.duration_seconds && (
          <p className="text-xs text-gray-400 mt-1">
            Time used: {Math.floor(result.duration_seconds / 60)}m {result.duration_seconds % 60}s
          </p>
        )}
        <div className="flex gap-3 justify-center mt-5">
          <button
            onClick={onRetake}
            className="px-5 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition"
          >
            Retake
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition"
          >
            Practice weak areas
          </button>
        </div>
      </motion.div>

      {/* Tab strip */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {(['summary', 'breakdown', 'review'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSection(tab)}
            className={[
              'flex-1 py-1.5 text-sm font-medium rounded-lg transition capitalize',
              section === tab ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700',
            ].join(' ')}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Summary — weakest areas */}
      {section === 'summary' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-3"
        >
          <h2 className="text-sm font-semibold text-gray-700">Top Weakest Areas</h2>
          {result && result.weakest_focus_areas.length > 0 ? (
            result.weakest_focus_areas.slice(0, 5).map((area, i) => (
              <div
                key={area.focus_key}
                className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-4"
              >
                <span className="text-2xl font-black text-red-200">#{i + 1}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-800 capitalize">
                    {area.focus_key.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xs text-gray-400">{area.miss_count} miss{area.miss_count !== 1 ? 'es' : ''}</p>
                </div>
                <button
                  onClick={() => navigate(`/practice/grammar?focus_key=${area.focus_key}`)}
                  className="text-xs px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg font-medium transition"
                >
                  Practice →
                </button>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-400 text-center py-4">No areas to show yet.</p>
          )}
        </motion.div>
      )}

      {/* Breakdown — bars by difficulty + domain */}
      {section === 'breakdown' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-5"
        >
          {result?.breakdown ? (
            <>
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">By Domain</h3>
                <div className="space-y-2">
                  {Object.entries(result.breakdown.by_family).map(([key, ct]) => (
                    <BarRow key={key} label={key} correct={ct.correct} total={ct.total} />
                  ))}
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">By Difficulty</h3>
                <div className="space-y-2">
                  {Object.entries(result.breakdown.by_difficulty).map(([key, ct]) => (
                    <BarRow key={key} label={key} correct={ct.correct} total={ct.total} />
                  ))}
                </div>
              </div>
              {Object.keys(result.breakdown.by_trap).length > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl p-4">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">By Trap Type</h3>
                  <div className="space-y-2">
                    {Object.entries(result.breakdown.by_trap).map(([key, ct]) => (
                      <BarRow key={key} label={key} correct={ct.correct} total={ct.total} />
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-400 text-center py-4">Breakdown not available.</p>
          )}
        </motion.div>
      )}

      {/* Review — fetch session detail */}
      {section === 'review' && (
        <ReviewSection sessionId={sessionId} userToken={userToken} />
      )}
    </div>
  )
}

function ReviewSection({ sessionId, userToken }: { sessionId: string; userToken: string }) {
  const [detail, setDetail] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)

  async function load() {
    if (loaded) return
    setLoading(true)
    try {
      const data = await api.diagnosticDetail(sessionId, userToken)
      setDetail(data)
    } catch {
      // ignore
    }
    setLoaded(true)
    setLoading(false)
  }

  if (!loaded && !loading) {
    return (
      <div className="text-center py-6">
        <button
          onClick={load}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition"
        >
          Load question review
        </button>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (!detail?.question_results?.length) {
    return <p className="text-sm text-gray-400 text-center py-4">No review data available.</p>
  }

  return (
    <div className="space-y-3">
      {detail.question_results.map((qr: any) => (
        <motion.div
          key={qr.question_id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className={`bg-white border rounded-xl p-4 ${qr.is_correct ? 'border-emerald-200' : 'border-red-200'}`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-base ${qr.is_correct ? 'text-emerald-500' : 'text-red-500'}`}>
              {qr.is_correct ? '✓' : '✗'}
            </span>
            <span className="text-xs text-gray-400">Q{qr.question_number}</span>
            {qr.focus_area && (
              <span className="text-xs text-gray-400 capitalize">{qr.focus_area.replace(/_/g, ' ')}</span>
            )}
          </div>
          <p className="text-xs text-gray-500">
            Your answer: <strong>{qr.selected_option}</strong>
          </p>
        </motion.div>
      ))}
    </div>
  )
}
