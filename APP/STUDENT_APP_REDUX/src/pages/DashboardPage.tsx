import { useState } from 'react'
import { Link } from 'react-router-dom'
import { WeakConceptsTab } from '../components/dashboard/WeakConceptsTab'
import { DiagnosticTab } from '../components/dashboard/DiagnosticTab'
import { TestModeTab } from '../components/dashboard/TestModeTab'
import { MissedQuestionsTab } from '../components/dashboard/MissedQuestionsTab'

type Tab = 'weak' | 'diagnostic' | 'test' | 'missed'

const TABS: Array<{ id: Tab; label: string; icon: string }> = [
  { id: 'weak', label: 'Weak Concepts', icon: '📊' },
  { id: 'diagnostic', label: 'Diagnostic', icon: '🎯' },
  { id: 'test', label: 'Test Mode', icon: '⏱' },
  { id: 'missed', label: 'Missed', icon: '📋' },
]

export function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>('weak')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-blue-600 font-bold text-lg">DSAT Prep</span>
        </div>
        <Link
          to="/practice/grammar"
          className="text-sm px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
        >
          Grammar Practice
        </Link>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6">
        {/* Tab bar */}
        <div className="flex bg-white border border-gray-200 rounded-xl p-1 mb-6 gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={[
                'flex-1 flex flex-col items-center gap-0.5 py-2 px-1 rounded-lg text-xs font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50',
              ].join(' ')}
            >
              <span className="text-base">{tab.icon}</span>
              <span className="leading-tight text-center">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div>
          {activeTab === 'weak' && <WeakConceptsTab />}
          {activeTab === 'diagnostic' && <DiagnosticTab />}
          {activeTab === 'test' && <TestModeTab />}
          {activeTab === 'missed' && <MissedQuestionsTab />}
        </div>
      </div>
    </div>
  )
}
