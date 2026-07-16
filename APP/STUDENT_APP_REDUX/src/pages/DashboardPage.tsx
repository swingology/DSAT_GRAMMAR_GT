import { motion, type Easing } from 'framer-motion'
import { Link } from 'react-router-dom'
import { HeroBanner } from '../components/dashboard/HeroBanner'
import { PracticeCard } from '../components/dashboard/PracticeCard'
import { DiagnosticCard } from '../components/dashboard/DiagnosticCard'
import { PracticeTestCard } from '../components/dashboard/PracticeTestCard'
import { RecentSessions } from '../components/dashboard/RecentSessions'
import { ConceptWeaknessChart } from '../components/dashboard/ConceptWeaknessChart'
import { SpacedRepetitionWidget } from '../components/dashboard/SpacedRepetitionWidget'
import { TrapSusceptibilityDashboard } from '../components/dashboard/TrapSusceptibilityDashboard'
import { UserMenu } from '../components/UserMenu'
import { BookOpen, ChevronRight } from 'lucide-react'
import { useReviewQuestions } from '../hooks/useReviewData'

const EASE: Easing = 'easeOut'

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.28, ease: EASE },
})

export function DashboardPage() {
  const reviewSummary = useReviewQuestions({}, 1, 1)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="text-blue-600 font-bold text-lg">DSAT Prep</span>
        <UserMenu />
      </header>

      <div className="max-w-lg mx-auto px-4 py-6 space-y-4">
        {/* Hero */}
        <HeroBanner />

        {/* Quick-start action cards */}
        <motion.section {...fadeUp(0.05)}>
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">
            Start a session
          </h2>
          <div className="space-y-3">
            <motion.div {...fadeUp(0.10)}>
              <PracticeCard />
            </motion.div>
            <motion.div {...fadeUp(0.16)}>
              <DiagnosticCard />
            </motion.div>
            <motion.div {...fadeUp(0.22)}>
              <PracticeTestCard />
            </motion.div>
          </div>
        </motion.section>

        {/* Spaced Review */}
        <motion.section {...fadeUp(0.30)}>
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">
            Spaced review
          </h2>
          <SpacedRepetitionWidget />
          <Link
            to="/review"
            className="mt-3 flex min-h-16 items-center gap-3 rounded-lg border border-gray-200 bg-white px-4 shadow-sm transition-colors hover:bg-gray-50"
          >
            <span className="grid size-10 shrink-0 place-items-center rounded-md bg-blue-50 text-blue-600">
              <BookOpen size={20} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-semibold text-gray-800">Review missed questions</span>
              <span className="block text-xs text-gray-500">
                {reviewSummary.isLoading
                  ? 'Loading review count'
                  : reviewSummary.isError
                    ? 'Open your review set'
                    : `${reviewSummary.data?.total ?? 0} questions to revisit`}
              </span>
            </span>
            <ChevronRight size={18} className="shrink-0 text-gray-400" />
          </Link>
        </motion.section>

        {/* Progress section */}
        <motion.section className="pt-2" {...fadeUp(0.38)}>
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">
            Progress
          </h2>

          <motion.div {...fadeUp(0.44)} className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 mb-3">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Activity</h3>
            <RecentSessions />
          </motion.div>

          <motion.div {...fadeUp(0.50)} className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Concept Weakness</h3>
            <ConceptWeaknessChart />
          </motion.div>

          <motion.div {...fadeUp(0.56)} className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
            <TrapSusceptibilityDashboard />
          </motion.div>

          <motion.div {...fadeUp(0.62)} className="mt-3">
            <Link
              to="/progress"
              className="block w-full text-center py-3 rounded-2xl border border-gray-200 bg-white text-sm font-medium text-blue-600 hover:bg-blue-50 transition-colors"
            >
              View full progress →
            </Link>
          </motion.div>
        </motion.section>
      </div>
    </div>
  )
}
