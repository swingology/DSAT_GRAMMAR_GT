import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GrammarPractice } from './components/GrammarPractice'
import { DashboardPage } from './pages/DashboardPage'
import { DiagnosticPage } from './pages/DiagnosticPage'
import { PracticeTestPage } from './pages/PracticeTestPage'
import { ConceptSelectorPage } from './pages/ConceptSelectorPage'
import { MixedPracticePage } from './pages/MixedPracticePage'
import { DiagnosticHistoryPage } from './pages/DiagnosticHistoryPage'
import { DiagnosticDetailPage } from './pages/DiagnosticDetailPage'
import { ProgressPage } from './pages/ProgressPage'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/practice/grammar" element={<GrammarPractice />} />
          <Route path="/practice/concepts" element={<ConceptSelectorPage />} />
          <Route path="/practice/mixed" element={<MixedPracticePage />} />
          <Route path="/diagnostic" element={<DiagnosticPage />} />
          <Route path="/diagnostic/history" element={<DiagnosticHistoryPage />} />
          <Route path="/diagnostic/:sessionId" element={<DiagnosticDetailPage />} />
          <Route path="/test" element={<PracticeTestPage />} />
          <Route path="/progress" element={<ProgressPage />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}
