import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/Layout'
import { UserManagement } from './pages/UserManagement'
import { DataManagement } from './pages/DataManagement'
import { StudentPerformance } from './pages/StudentPerformance'
import { PipelinePerformance } from './pages/PipelinePerformance'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/users" replace />} />
            <Route path="/users" element={<UserManagement />} />
            <Route path="/data" element={<DataManagement />} />
            <Route path="/students" element={<StudentPerformance />} />
            <Route path="/pipeline" element={<PipelinePerformance />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
