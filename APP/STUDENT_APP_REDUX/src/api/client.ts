// API client for communication with backend

const API_BASE = '/api'

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  headers?: Record<string, string>
  body?: any
}

export async function apiCall(endpoint: string, options: ApiOptions = {}) {
  const { method = 'GET', headers = {}, body } = options

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  }

  const apiKey = (import.meta as any).env.VITE_STUDENT_API_KEY || 'student-test-key'
  requestHeaders['X-API-Key'] = apiKey

  const token = (import.meta as any).env.VITE_TEST_USER_TOKEN || localStorage.getItem('user_token')
  if (token) {
    requestHeaders['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers: requestHeaders,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export const api = {
  getStudyRecommendations: (userToken: string) =>
    apiCall('/study/recommendations', {
      method: 'POST',
      body: { user_token: userToken },
    }),

  getQuestions: (params: Record<string, any>) =>
    apiCall(`/questions?${new URLSearchParams(params).toString()}`),

  submitAnswer: (data: {
    question_id: string
    selected_option_label: string
    user_token: string
    missed_grammar_focus_key?: string
    missed_reading_focus_key?: string
  }) =>
    apiCall('/submit', {
      method: 'POST',
      body: data,
    }),

  getStats: (userId: number) =>
    apiCall(`/stats/${userId}`),

  getMissedQuestions: (params: { user_token: string; domain?: string; sort_by?: string; limit?: number }) => {
    const query = new URLSearchParams({ user_token: params.user_token })
    if (params.domain) query.set('domain', params.domain)
    if (params.sort_by) query.set('sort_by', params.sort_by)
    if (params.limit) query.set('limit', String(params.limit))
    return apiCall(`/study/missed?${query.toString()}`)
  },

  getGenerationRequests: () =>
    apiCall('/study/generation-requests'),

  diagnosticStart: (data: { user_token: string; diagnostic_type?: string }) =>
    apiCall('/diagnostic/start', { method: 'POST', body: data }),

  diagnosticSubmit: (sessionId: string, data: {
    user_token: string
    question_id: string
    selected_option_label: string
    missed_grammar_focus_key?: string
    missed_reading_focus_key?: string
  }) =>
    apiCall(`/diagnostic/${sessionId}/submit`, { method: 'POST', body: data }),

  diagnosticComplete: (sessionId: string, data: { user_token: string }) =>
    apiCall(`/diagnostic/${sessionId}/complete`, { method: 'POST', body: data }),

  diagnosticHistory: (userToken: string, limit = 20) =>
    apiCall(`/diagnostic/history?user_token=${encodeURIComponent(userToken)}&limit=${limit}`),

  diagnosticDetail: (sessionId: string, userToken: string) =>
    apiCall(`/diagnostic/${sessionId}?user_token=${encodeURIComponent(userToken)}`),

  srReview: (questionId: string, data: { user_token: string; quality: number }) =>
    apiCall(`/spaced-repetition/${questionId}/review`, { method: 'POST', body: data }),

  srDueQuestions: (userToken: string, limit = 20, domain?: string) => {
    const q = new URLSearchParams({ user_token: userToken, limit: String(limit) })
    if (domain) q.set('domain', domain)
    return apiCall(`/spaced-repetition/due?${q.toString()}`)
  },

  srProgress: (userToken: string) =>
    apiCall(`/spaced-repetition/progress?user_token=${encodeURIComponent(userToken)}`),
}
