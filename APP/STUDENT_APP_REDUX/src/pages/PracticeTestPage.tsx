import { useNavigate, useSearchParams } from 'react-router-dom'
import { TestModeTab } from '../components/dashboard/TestModeTab'

export function PracticeTestPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()

  const questions = parseInt(params.get('questions') ?? '20', 10)
  const seconds = parseInt(params.get('seconds') ?? '1200', 10)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
        >
          ← Back
        </button>
        <span className="text-gray-800 font-semibold">Practice Test</span>
        <span className="ml-auto text-xs text-gray-400">
          {questions} questions · {Math.round(seconds / 60)} min
        </span>
      </header>

      <div className="max-w-lg mx-auto px-4 py-6">
        <TestModeTab questionCount={questions} durationSeconds={seconds} />
      </div>
    </div>
  )
}
