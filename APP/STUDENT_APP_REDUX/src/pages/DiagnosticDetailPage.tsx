import { motion } from 'framer-motion'
import { DiagnosticDetail } from '../components/dashboard/DiagnosticDetail'

export function DiagnosticDetailPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.25, 0, 0, 1] }}
        className="max-w-lg mx-auto px-4 py-6"
      >
        <DiagnosticDetail />
      </motion.div>
    </div>
  )
}
