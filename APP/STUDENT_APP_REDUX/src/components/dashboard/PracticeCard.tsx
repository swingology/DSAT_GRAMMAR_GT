import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

type PracticeMode = 'grammar' | 'concepts' | 'mixed'

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
  const navigate = useNavigate()

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
            <div className="border-t border-gray-100 px-4 pb-4 pt-2 space-y-2">
              {OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => navigate(opt.route)}
                  className="w-full text-left flex items-start gap-3 p-3 rounded-xl hover:bg-emerald-50 hover:border-emerald-200 border border-transparent transition group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 text-sm group-hover:text-emerald-800">
                      {opt.label}
                    </p>
                    <p className="text-gray-400 text-xs mt-0.5 leading-snug">{opt.desc}</p>
                  </div>
                  <span className="text-gray-300 group-hover:text-emerald-400 mt-0.5">→</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
