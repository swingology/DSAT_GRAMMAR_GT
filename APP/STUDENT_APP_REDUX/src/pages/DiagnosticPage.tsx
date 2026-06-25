import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DiagnosticIntro } from '../components/diagnostic/DiagnosticIntro'
import { DiagnosticTestRunner } from '../components/diagnostic/DiagnosticTestRunner'
import { DiagnosticReport } from '../components/diagnostic/DiagnosticReport'
import { api } from '../api/client'
import type { DiagnosticStartV1Response, DiagnosticResult } from '../types'

type Phase = 'intro' | 'running' | 'complete'

const USER_TOKEN =
  (import.meta as any).env.VITE_TEST_USER_TOKEN ||
  localStorage.getItem('user_token') ||
  ''

export function DiagnosticPage() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>('intro')
  const [sessionData, setSessionData] = useState<DiagnosticStartV1Response | null>(null)
  const [result, setResult] = useState<DiagnosticResult | null>(null)

  async function handleStarted(data: DiagnosticStartV1Response) {
    setSessionData(data)
    setPhase('running')
  }

  async function handleComplete() {
    if (!sessionData) return
    try {
      const res = await api.diagnosticComplete(sessionData.session_id, {
        user_token: USER_TOKEN,
      })
      setResult(res as DiagnosticResult)
    } catch {
      // Still move to complete phase — report will show what we have
    }
    setPhase('complete')
  }

  if (phase === 'running' && sessionData) {
    return (
      <DiagnosticTestRunner
        sessionId={sessionData.session_id}
        questions={sessionData.questions}
        timeLimitSeconds={sessionData.time_limit_seconds}
        userToken={USER_TOKEN}
        onComplete={handleComplete}
      />
    )
  }

  if (phase === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="text-gray-400 hover:text-gray-700 text-sm font-medium transition"
          >
            ← Dashboard
          </button>
          <span className="text-gray-800 font-semibold">Results</span>
        </header>
        <DiagnosticReport
          result={result}
          sessionId={sessionData?.session_id ?? ''}
          userToken={USER_TOKEN}
          onRetake={() => { setPhase('intro'); setSessionData(null); setResult(null) }}
        />
      </div>
    )
  }

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
      <DiagnosticIntro userToken={USER_TOKEN} onStarted={handleStarted} />
    </div>
  )
}
