import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

const QUESTION_COUNTS = [10, 20, 33]
const TIME_PRESETS: Array<{ label: string; seconds: number }> = [
  { label: '10 min', seconds: 600 },
  { label: '20 min', seconds: 1200 },
  { label: '32 min (SAT)', seconds: 1920 },
]

export function PracticeTestCard() {
  const [configOpen, setConfigOpen] = useState(false)
  const [qCount, setQCount] = useState(20)
  const [timeSeconds, setTimeSeconds] = useState(1200)
  const navigate = useNavigate()

  function startTest() {
    navigate(`/test?questions=${qCount}&seconds=${timeSeconds}`)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.14, duration: 0.25, ease: 'easeOut' }}
      className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden"
    >
      <button
        onClick={() => setConfigOpen((v) => !v)}
        className="w-full flex items-center gap-4 p-5 hover:bg-gray-50 transition text-left"
      >
        <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center text-2xl flex-shrink-0">
          ⏱️
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 text-base">Practice Test</h3>
          <p className="text-gray-500 text-sm">
            {qCount} questions · {Math.round(timeSeconds / 60)} min
          </p>
        </div>
        <span
          className={`text-gray-400 transition-transform duration-200 ${configOpen ? 'rotate-180' : ''}`}
        >
          ▾
        </span>
      </button>

      <AnimatePresence>
        {configOpen && (
          <motion.div
            key="config"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="border-t border-gray-100 px-4 pb-4 pt-3 space-y-4">
              {/* Question count */}
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Questions
                </p>
                <div className="flex gap-2">
                  {QUESTION_COUNTS.map((n) => (
                    <button
                      key={n}
                      onClick={() => setQCount(n)}
                      className={[
                        'flex-1 py-2 rounded-lg text-sm font-medium border transition',
                        qCount === n
                          ? 'bg-amber-500 border-amber-500 text-white'
                          : 'border-gray-200 text-gray-600 hover:bg-amber-50 hover:border-amber-200',
                      ].join(' ')}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>

              {/* Time limit */}
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Time limit
                </p>
                <div className="flex gap-2">
                  {TIME_PRESETS.map((p) => (
                    <button
                      key={p.seconds}
                      onClick={() => setTimeSeconds(p.seconds)}
                      className={[
                        'flex-1 py-2 rounded-lg text-xs font-medium border transition',
                        timeSeconds === p.seconds
                          ? 'bg-amber-500 border-amber-500 text-white'
                          : 'border-gray-200 text-gray-600 hover:bg-amber-50 hover:border-amber-200',
                      ].join(' ')}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={startTest}
                className="w-full py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-xl text-sm transition"
              >
                Start Test →
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
