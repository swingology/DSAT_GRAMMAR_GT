// No shared base path: users.router mounts at /users, admin.router at /admin,
// but student.router (stats/study endpoints) mounts at /api — each adminApi
// call below spells out its own real backend prefix instead of assuming one.
const API_BASE = ''

const ADMIN_TOKEN = (import.meta as any).env.VITE_ADMIN_TOKEN || ''

export async function apiCall(endpoint: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': ADMIN_TOKEN,
      ...(options.headers || {}),
    },
  })
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`)
  if (res.status === 204) return null
  return res.json()
}

export const adminApi = {
  // Users
  listUsers: () => apiCall('/users'),
  getUser: (id: number) => apiCall(`/users/${id}`),
  createUser: (data: any) => apiCall('/users', { method: 'POST', body: JSON.stringify(data) }),
  deleteUser: (id: number) => apiCall(`/users/${id}`, { method: 'DELETE' }),

  // Questions
  listQuestions: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiCall(`/admin/questions?${q}`)
  },
  getQuestion: (id: string) => apiCall(`/admin/questions/${id}`),
  approveQuestion: (id: string) => apiCall(`/admin/questions/${id}/approve`, { method: 'POST' }),
  rejectQuestion: (id: string, reason: string) =>
    apiCall(`/admin/questions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
  editQuestion: (id: string, data: any) =>
    apiCall(`/admin/questions/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteQuestion: (id: string) => apiCall(`/admin/questions/${id}`, { method: 'DELETE' }),

  // Jobs / generated questions
  listJobs: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiCall(`/admin/jobs?${q}`)
  },
  listGeneratedQuestions: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiCall(`/admin/generated-questions?${q}`)
  },
  approveGenerated: (id: string) => apiCall(`/admin/generated-questions/${id}/approve`, { method: 'POST' }),
  rejectGenerated: (id: string, reason: string) =>
    apiCall(`/admin/generated-questions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),

  // Analytics
  getGenerationAnalytics: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiCall(`/admin/analytics/generation?${q}`)
  },
  getReviewAnalytics: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiCall(`/admin/analytics/review?${q}`)
  },
  getBatchAnalytics: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiCall(`/admin/analytics/batches?${q}`)
  },
  getTrendAnalytics: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiCall(`/admin/analytics/trends?${q}`)
  },

  // Student stats (student.router mounts at /api, unlike users/admin routers)
  getStudentStats: (userId: number) => apiCall(`/api/stats/${userId}`),
  getStudentRecommendations: (userToken: string) =>
    apiCall('/api/study/recommendations', { method: 'POST', body: JSON.stringify({ user_token: userToken }) }),
  getStudentMissed: (userToken: string) =>
    apiCall(`/api/study/missed?user_token=${userToken}`),

  // Auto-release
  getAutoReleaseStatus: () => apiCall('/admin/generation/auto-release/status'),
  enableAutoRelease: () => apiCall('/admin/generation/auto-release/enable', { method: 'POST' }),
  disableAutoRelease: () => apiCall('/admin/generation/auto-release/disable', { method: 'POST' }),
  getAutoReleaseAudit: () => apiCall('/admin/generation/auto-release/audit'),
}
