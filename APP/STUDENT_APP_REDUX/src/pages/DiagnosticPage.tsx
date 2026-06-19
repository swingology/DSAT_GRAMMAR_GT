import { useNavigate } from 'react-router-dom'
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

      <div className="max-w-lg mx-auto px-4 py-6">
        <DiagnosticTab />
      </div>
    </div>
  )
}
