// API client for communication with backend

import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from '../auth/authStore'

const API_BASE = (import.meta as any).env.VITE_API_BASE || '/api'

export type SubmitSourceType = 'practice_test' | 'drill' | 'practice' | 'unknown'

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  headers?: Record<string, string>
  body?: any
  /** Skip the 401 silent-refresh interceptor (used by the auth calls themselves). */
  skipAuthRetry?: boolean
}

/**
 * Exchange the refresh token for a fresh pair.
 *
 * Deliberately a bare `fetch` rather than `apiCall`: routing it through the interceptor
 * would let an expired refresh token trigger its own 401 handler and recurse.
 * Concurrent 401s share one in-flight refresh.
 */
let refreshInFlight: Promise<boolean> | null = null

function refreshTokens(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) return false

    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!response.ok) return false

      const tokens = await response.json()
      setTokens(tokens)
      return true
    } catch {
      return false
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

async function rawApiCall(endpoint: string, options: ApiOptions): Promise<Response> {
  const { method = 'GET', headers = {}, body } = options

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  }

  // Legacy static key — the backend still accepts it, and scripts depend on it.
  const apiKey = (import.meta as any).env.VITE_STUDENT_API_KEY || 'student-test-key'
  requestHeaders['X-API-Key'] = apiKey

  const accessToken = getAccessToken()
  if (accessToken) {
    requestHeaders['Authorization'] = `Bearer ${accessToken}`
  }

  return fetch(`${API_BASE}${endpoint}`, {
    method,
    headers: requestHeaders,
    body: body ? JSON.stringify(body) : undefined,
  })
}

export async function apiCall(endpoint: string, options: ApiOptions = {}) {
  let response = await rawApiCall(endpoint, options)

  if (response.status === 401 && !options.skipAuthRetry && getRefreshToken()) {
    if (await refreshTokens()) {
      response = await rawApiCall(endpoint, options)
    } else {
      // Refresh is dead — drop the session. AuthContext subscribes to the store and
      // sends the user to the login page.
      clearSession()
    }
  }

  if (!response.ok) {
    let detail = ''
    try {
      const payload = await response.clone().json()
      detail = typeof payload?.detail === 'string' ? payload.detail : ''
    } catch {
      detail = ''
    }
    const error = new Error(
      `API error: ${response.status} ${response.statusText}${detail ? `: ${detail}` : ''}`,
    )
    // Callers that want to show the backend's message read this rather than
    // re-parsing the string above.
    ;(error as any).detail = detail
    ;(error as any).status = response.status
    throw error
  }

  if (response.status === 204) return null

  return response.json()
}

export const api = {
  /** Exchange a Google ID token (GIS popup credential) for our JWT pair. */
  googleLogin: (credential: string) =>
    apiCall('/auth/google', {
      method: 'POST',
      body: { credential },
      skipAuthRetry: true,
    }),

  // Deliberately NOT skipAuthRetry: on a return visit the stored access token is
  // usually expired (minutes) while the refresh token is still good (days), so this
  // call must be allowed to refresh — that is what "remember me" rests on.
  me: () => apiCall('/auth/me'),

  logout: () => apiCall('/auth/logout', { method: 'POST', skipAuthRetry: true }),

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
    source_type: SubmitSourceType
    missed_grammar_focus_key?: string
    missed_reading_focus_key?: string
    missed_syntactic_trap_key?: string
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

  /** Blueprint v1 diagnostic — returns full 16-question module with no answer key. */
  diagnosticStartV1: (userToken: string) =>
    apiCall('/diagnostic/start', {
      method: 'POST',
      body: { user_token: userToken, diagnostic_type: 'blueprint_v1' },
    }),

  diagnosticSubmit: (sessionId: string, data: {
    user_token: string
    question_id: string
    selected_option_label: string
    missed_grammar_focus_key?: string
    missed_reading_focus_key?: string
    missed_syntactic_trap_key?: string
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

  getTrapSusceptibility: (userToken: string) =>
    apiCall(`/student/trap-susceptibility?user_token=${encodeURIComponent(userToken)}`),

  getQuestionTypePerformance: (userToken: string) =>
    apiCall(`/student/question-type-performance?user_token=${encodeURIComponent(userToken)}`),

  getTrapDetails: (trapType: string, userToken: string) =>
    apiCall(`/student/trap-details/${encodeURIComponent(trapType)}?user_token=${encodeURIComponent(userToken)}`),

  module1Complete: (data: {
    user_token: string
    module_1_accuracy: number
    module_1_duration_seconds?: number
    focus_breakdown?: Record<string, unknown>
    test_mode?: string
  }) =>
    apiCall('/test-session/module-1-complete', { method: 'POST', body: data }),

  module2Blueprint: (testSessionId: string, userToken: string, limit = 27) =>
    apiCall(
      `/test-session/${encodeURIComponent(testSessionId)}/module-2-blueprint` +
      `?user_token=${encodeURIComponent(userToken)}&limit=${limit}`
    ),

  testSessionHistory: (userToken: string) =>
    apiCall(`/test-session/history?user_token=${encodeURIComponent(userToken)}`),

  getProgressTrend: (userToken: string, days = 30) =>
    apiCall(`/progress/trend?user_token=${encodeURIComponent(userToken)}&days=${days}`),

  getDomainTrend: (userToken: string, days = 30) =>
    apiCall(`/progress/domain-trend?user_token=${encodeURIComponent(userToken)}&days=${days}`),

  getFocusSummary: (userToken: string) =>
    apiCall(`/progress/focus-summary?user_token=${encodeURIComponent(userToken)}`),
}
