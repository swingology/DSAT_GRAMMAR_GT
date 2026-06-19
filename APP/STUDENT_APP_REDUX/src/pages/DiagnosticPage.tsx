import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { DiagnosticTab } from '../components/dashboard/DiagnosticTab'

export function DiagnosticPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← Back
        </button>
        <span className="text-gray-800 font-semibold">Diagnostic Test</span>
      </header>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.25, 0, 0, 1] }}
        className="max-w-lg mx-auto px-4 py-6"
      >
        <DiagnosticTab />
      </motion.div>
    </div>
  )
}
