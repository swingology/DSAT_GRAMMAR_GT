import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './auth/AuthContext'
import { RequireAdmin } from './auth/RequireAdmin'
import { LoginPage } from './pages/LoginPage'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { UserManagement } from './pages/UserManagement'
import { DataManagement } from './pages/DataManagement'
import { StudentPerformance } from './pages/StudentPerformance'
import { PipelinePerformance } from './pages/PipelinePerformance'
import { VocabularyGovernance } from './pages/VocabularyGovernance'
import { Generate } from './pages/Generate'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastProvider } from './components/Toast'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
})

function AppRoutes() {
  const location = useLocation()

  return (
    <ErrorBoundary resetKey={location.pathname}>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <RequireAdmin>
                  <Layout />
                </RequireAdmin>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/users" element={<UserManagement />} />
              <Route path="/data" element={<DataManagement />} />
              <Route path="/students" element={<StudentPerformance />} />
              <Route path="/pipeline" element={<PipelinePerformance />} />
              <Route path="/vocabulary" element={<VocabularyGovernance />} />
              <Route path="/generate" element={<Generate />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
