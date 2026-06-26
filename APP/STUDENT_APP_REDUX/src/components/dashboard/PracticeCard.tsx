import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

type PracticeMode = 'grammar' | 'concepts' | 'mixed'

const QUESTION_COUNTS = [10, 20, 27]

const OPTIONS: Array<{ id: PracticeMode; label: string; desc: string; route: string }> = [
  {
    id: 'grammar',
    label: 'Grammar Practice',
    desc: 'Sentence-level grammar questions with detailed analysis',
    route: '/practice/grammar',
  },
  {
    id: 'concepts',
    label: 'Pick a Concept',
    desc: 'Choose a specific grammar or reading concept to drill',
    route: '/practice/concepts',
  },
  {
    id: 'mixed',
    label: 'Mixed Practice',
    desc: 'Random questions across all concepts',
    route: '/practice/mixed',
  },
]

export function PracticeCard() {
  const [open, setOpen] = useState(false)
  const [counts, setCounts] = useState<Record<PracticeMode, number>>({
    grammar: 10,
    concepts: 10,
    mixed: 10,
  })
  const navigate = useNavigate()

  function setCount(mode: PracticeMode, n: number) {
    setCounts((c) => ({ ...c, [mode]: n }))
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-4 p-5 hover:bg-gray-50 transition text-left"
      >
        <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center text-2xl flex-shrink-0">
          ✏️
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 text-base">Practice</h3>
          <p className="text-gray-500 text-sm truncate">Grammar, concept drill, or mixed</p>
        </div>
        <span
          className={`text-gray-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        >
          ▾
        </span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            key="options"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="border-t border-gray-100 px-4 pb-4 pt-2 space-y-3">
              {OPTIONS.map((opt) => (
                <div
                  key={opt.id}
                  className="rounded-xl border border-gray-100 p-3 space-y-2"
                >
                  <div>
                    <p className="font-medium text-gray-800 text-sm">{opt.label}</p>
                    <p className="text-gray-400 text-xs mt-0.5 leading-snug">{opt.desc}</p>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 mr-1">Questions</span>
                    {QUESTION_COUNTS.map((n) => (
                      <button
                        key={n}
                        onClick={() => setCount(opt.id, n)}
                        className={[
                          'px-2.5 py-1 rounded-lg text-xs font-medium border transition',
                          counts[opt.id] === n
                            ? 'bg-emerald-500 border-emerald-500 text-white'
                            : 'border-gray-200 text-gray-600 hover:bg-emerald-50 hover:border-emerald-200',
                        ].join(' ')}
                      >
                        {n}
                      </button>
                    ))}
                    <button
                      onClick={() => navigate(`${opt.route}?limit=${counts[opt.id]}`)}
                      className="ml-auto flex items-center gap-1 px-3 py-1 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold rounded-lg transition"
                    >
                      Start
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
