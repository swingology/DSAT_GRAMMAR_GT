import { HeroBanner } from '../components/dashboard/HeroBanner'
import { PracticeCard } from '../components/dashboard/PracticeCard'
import { DiagnosticCard } from '../components/dashboard/DiagnosticCard'
import { PracticeTestCard } from '../components/dashboard/PracticeTestCard'
import { RecentSessions } from '../components/dashboard/RecentSessions'
import { ConceptWeaknessChart } from '../components/dashboard/ConceptWeaknessChart'

export function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="text-blue-600 font-bold text-lg">DSAT Prep</span>
        <span className="text-xs text-gray-400">Student Portal</span>
      </header>

      <div className="max-w-lg mx-auto px-4 py-6 space-y-4">
        {/* Hero */}
        <HeroBanner />

        {/* Quick-start action cards */}
        <section>
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">
            Start a session
          </h2>
          <div className="space-y-3">
            <PracticeCard />
            <DiagnosticCard />
            <PracticeTestCard />
          </div>
        </section>

        {/* Progress section */}
        <section className="pt-2">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">
            Progress
          </h2>

          <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 mb-3">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Activity</h3>
            <RecentSessions />
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Concept Weakness</h3>
            <ConceptWeaknessChart />
          </div>
        </section>
      </div>
    </div>
  )
}
