import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from '../auth/authStore'

const API_BASE = '/api'

// Legacy static key — the backend still accepts it, and scripts depend on it. Leave
// VITE_ADMIN_TOKEN unset for normal Google sign-in.
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || ''

interface ApiCallOptions extends RequestInit {
  /** Skip the 401 silent-refresh interceptor (used by the auth calls themselves). */
  skipAuthRetry?: boolean
}

/** Query-string params: values are stringified; undefined entries are skipped. */
export type QueryParams = Record<string, string | number | boolean | undefined>

function toQuery(params: QueryParams): string {
  const sp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) sp.set(key, String(value))
  }
  return sp.toString()
}

/** Payload for creating a user — mirrors updateUser's optional fields, username required. */
export interface CreateUserPayload {
  username: string
  email?: string | null
  password?: string
  role?: string
  is_active?: boolean
}

/** Payload for editing a question's content. */
export interface QuestionEditPayload {
  question_text: string
  passage_text?: string
  correct_option_label: string
  explanation_text?: string
  change_notes?: string
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

function rawApiCall(endpoint: string, options: ApiCallOptions): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  }

  if (ADMIN_TOKEN) headers['X-API-Key'] = ADMIN_TOKEN

  // admin_required checks the Bearer JWT before falling back to the key, so both may
  // be sent safely.
  const accessToken = getAccessToken()
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

  return fetch(`${API_BASE}${endpoint}`, { ...options, headers })
}

export async function apiCall(endpoint: string, options: ApiCallOptions = {}) {
  let res = await rawApiCall(endpoint, options)

  if (res.status === 401 && !options.skipAuthRetry && getRefreshToken()) {
    if (await refreshTokens()) {
      res = await rawApiCall(endpoint, options)
    } else {
      // Refresh is dead — drop the session. AuthContext subscribes to the store and
      // sends the user to the login page.
      clearSession()
    }
  }

  if (!res.ok) {
    let detail = ''
    try {
      const payload = await res.clone().json()
      detail = typeof payload?.detail === 'string' ? payload.detail : ''
    } catch {
      // payload wasn't JSON; detail stays '' from init
    }
    const error = new Error(
      `API error: ${res.status} ${res.statusText}${detail ? `: ${detail}` : ''}`,
    ) as Error & { detail: string; status: number }
    // Callers that want to show the backend's message read this rather than
    // re-parsing the string above.
    error.detail = detail
    error.status = res.status
    throw error
  }
  if (res.status === 204) return null
  return res.json()
}

export const authApi = {
  /** Exchange a Google ID token (GIS popup credential) for our JWT pair. */
  googleLogin: (credential: string) =>
    apiCall('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ credential }),
      skipAuthRetry: true,
    }),

  // Deliberately NOT skipAuthRetry: on a return visit the stored access token is
  // usually expired (minutes) while the refresh token is still good (days), so this
  // call must be allowed to refresh — that is what "remember me" rests on.
  me: () => apiCall('/auth/me'),

  logout: () => apiCall('/auth/logout', { method: 'POST', skipAuthRetry: true }),
}

export const adminApi = {
  // Users
  listUsers: () => apiCall('/users'),
  getUser: (id: number) => apiCall(`/users/${id}`),
  createUser: (data: CreateUserPayload) => apiCall('/users', { method: 'POST', body: JSON.stringify(data) }),
  updateUser: (id: number, data: { username?: string; email?: string | null; role?: string; is_active?: boolean }) =>
    apiCall(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  resetUserPassword: (id: number, newPassword: string) =>
    apiCall(`/users/${id}/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    }),
  deleteUser: (id: number) => apiCall(`/users/${id}`, { method: 'DELETE' }),

  // Questions
  listQuestions: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall(`/admin/questions?${q}`)
  },
  getQuestion: (id: string) => apiCall(`/admin/questions/${id}`),
  getTests: () => apiCall('/admin/tests'),
  approveQuestion: (id: string) => apiCall(`/admin/questions/${id}/approve`, { method: 'POST' }),
  rejectQuestion: (id: string, reason: string) =>
    apiCall(`/admin/questions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
  editQuestion: (id: string, data: QuestionEditPayload) =>
    apiCall(`/admin/questions/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteQuestion: (id: string) => apiCall(`/admin/questions/${id}`, { method: 'DELETE' }),

  // Jobs / generated questions
  listJobs: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall(`/admin/jobs?${q}`)
  },
  listGeneratedQuestions: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall(`/admin/generated-questions?${q}`)
  },
  approveGenerated: (id: string) => apiCall(`/admin/generated-questions/${id}/approve`, { method: 'POST' }),
  rejectGenerated: (id: string, reason: string) =>
    apiCall(`/admin/generated-questions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),

  // Analytics
  getGenerationAnalytics: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall(`/admin/analytics/generation?${q}`)
  },
  getReviewAnalytics: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall(`/admin/analytics/review?${q}`)
  },
  getBatchAnalytics: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall(`/admin/analytics/batches?${q}`)
  },
  getTrendAnalytics: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall(`/admin/analytics/trends?${q}`)
  },
  getWeakSpots: (limit = 20) => apiCall(`/admin/analytics/weak-spots?limit=${limit}`),

  // Student stats
  getStudentStats: (userId: number) => apiCall(`/stats/${userId}`),
  getStudentActivity: (userId: number, days = 365) =>
    apiCall(`/stats/${userId}/activity?days=${days}`),
  getStudentRecommendations: (userToken: string) =>
    apiCall('/study/recommendations', { method: 'POST', body: JSON.stringify({ user_token: userToken }) }),
  getStudentMissed: (userToken: string) =>
    apiCall(`/study/missed?user_token=${userToken}`),

  // Auto-release
  getAutoReleaseStatus: () => apiCall('/admin/generation/auto-release/status'),
  enableAutoRelease: () => apiCall('/admin/generation/auto-release/enable', { method: 'POST' }),
  disableAutoRelease: () => apiCall('/admin/generation/auto-release/disable', { method: 'POST' }),
  getAutoReleaseAudit: () => apiCall('/admin/generation/auto-release/audit'),
}
