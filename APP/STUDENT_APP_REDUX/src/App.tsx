import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GrammarPractice } from './components/GrammarPractice'
import { DashboardPage } from './pages/DashboardPage'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/practice/grammar" element={<GrammarPractice />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}
