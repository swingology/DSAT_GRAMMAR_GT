import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../api/client'
import type { DiagnosticStartV1Response } from '../../types'

interface Props {
  userToken: string
  onStarted: (data: DiagnosticStartV1Response) => void
}

export function DiagnosticIntro({ userToken, onStarted }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleStart() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.diagnosticStartV1(userToken)
      onStarted(data as DiagnosticStartV1Response)
    } catch (e: any) {
      setError(e?.message ?? 'Could not start diagnostic. Try again.')
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="max-w-lg mx-auto px-4 py-10 space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-800 mb-1">Diagnostic Test</h1>
        <p className="text-gray-500 text-sm">
          Find out exactly where your skills stand — before you start any practice.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: 'Questions', value: '16' },
          { label: 'Time limit', value: '~19 min' },
          { label: 'Format', value: 'Timed' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-50 rounded-xl p-4 border border-gray-100">
            <div className="text-xl font-bold text-gray-800">{value}</div>
            <div className="text-xs text-gray-400 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* What to expect */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
        <h2 className="font-semibold text-gray-700 text-sm">What to expect</h2>
        <ul className="space-y-2 text-sm text-gray-600">
          {[
            'Covers grammar and reading — every major skill area.',
            'Answers are hidden until the end (just like the real test).',
            'A timer counts down — the test auto-submits when time runs out.',
            'After submission you get a full breakdown of your weak spots.',
          ].map((item) => (
            <li key={item} className="flex gap-2">
              <span className="text-blue-500 mt-0.5 shrink-0">✓</span>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {error && (
        <p className="text-sm text-red-500 bg-red-50 rounded-lg px-4 py-2">{error}</p>
      )}

      <button
        onClick={handleStart}
        disabled={loading}
        className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold rounded-xl text-base transition"
      >
        {loading ? 'Loading questions…' : 'Start Diagnostic'}
      </button>

      <p className="text-center text-xs text-gray-400">
        Make sure you have ~20 minutes of uninterrupted time before starting.
      </p>
    </motion.div>
  )
}
