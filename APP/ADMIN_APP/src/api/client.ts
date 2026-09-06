import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  setTokens,
  type AuthProfile,
} from '../auth/authStore'
import type {
  ActivityDay,
  AutoReleaseStatus,
  BatchAnalytics,
  CohortWeakSpots,
  GeneratedQuestionDetail,
  GenerationAnalytics,
  GenerationBatchJobs,
  GenerationBatchRequest,
  GenerationBatchResponse,
  GenerationBatchStatus,
  QuestionListResponse,
  StimulusExtractResponse,
  StimulusAsset,
  StimulusExtractionJob,
  StudentStats,
  TestSummary,
  User,
  VocabMaster,
  VocabCandidatesFile,
} from '../types'

const API_BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')

// Legacy static key — the backend still accepts it, and scripts depend on it. Leave
// VITE_ADMIN_TOKEN unset for normal Google sign-in.
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || ''

interface ApiCallOptions extends RequestInit {
  /** Skip the 401 silent-refresh interceptor (used by the auth calls themselves). */
  skipAuthRetry?: boolean
  /** Return the raw body as text instead of parsing JSON (markdown/CSV endpoints). */
  asText?: boolean
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
  role?: 'student' | 'admin'
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

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
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
  const isFormData = options.body instanceof FormData
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  }
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  if (ADMIN_TOKEN) headers['X-API-Key'] = ADMIN_TOKEN

  // admin_required checks the Bearer JWT before falling back to the key, so both may
  // be sent safely.
  const accessToken = getAccessToken()
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

  return fetch(`${API_BASE}${endpoint}`, { ...options, headers })
}

export async function apiCall<T = unknown>(
  endpoint: string,
  options: ApiCallOptions = {},
): Promise<T> {
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
  if (res.status === 204) return null as T
  if (options.asText) return res.text() as Promise<T>
  return res.json() as Promise<T>
}

export const authApi = {
  /** Exchange a Google ID token (GIS popup credential) for our JWT pair. */
  googleLogin: (credential: string) =>
    apiCall<TokenResponse>('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ credential }),
      skipAuthRetry: true,
    }),

  // Deliberately NOT skipAuthRetry: on a return visit the stored access token is
  // usually expired (minutes) while the refresh token is still good (days), so this
  // call must be allowed to refresh — that is what "remember me" rests on.
  me: () => apiCall<AuthProfile>('/auth/me'),

  logout: () => apiCall<null>('/auth/logout', { method: 'POST', skipAuthRetry: true }),
}

export const adminApi = {
  // Users
  listUsers: () => apiCall<User[]>('/users'),
  createUser: (data: CreateUserPayload) => apiCall<User>('/users', { method: 'POST', body: JSON.stringify(data) }),
  updateUser: (id: number, data: { username?: string; email?: string | null; role?: 'student' | 'admin'; is_active?: boolean }) =>
    apiCall<User>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  resetUserPassword: (id: number, newPassword: string) =>
    apiCall<null>(`/users/${id}/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    }),
  deleteUser: (id: number) => apiCall<null>(`/users/${id}`, { method: 'DELETE' }),

  // Questions
  listQuestions: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall<QuestionListResponse>(`/admin/questions?${q}`)
  },
  getTests: () => apiCall<TestSummary[]>('/admin/tests'),
  approveQuestion: (id: string) => apiCall(`/admin/questions/${id}/approve`, { method: 'POST' }),
  rejectQuestion: (id: string, reason: string) =>
    apiCall(`/admin/questions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
  editQuestion: (id: string, data: QuestionEditPayload) =>
    apiCall(`/admin/questions/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteQuestion: (id: string) => apiCall(`/admin/questions/${id}`, { method: 'DELETE' }),
  setGraphTag: (id: string, hasGraph: boolean) =>
    apiCall(`/admin/questions/${id}/graph-tag`, { method: 'POST', body: JSON.stringify({ has_graph: hasGraph }) }),

  // Stimulus assets
  getStimulusAssets: (questionId: string) =>
    apiCall<StimulusAsset[]>(`/admin/questions/${questionId}/stimulus-assets`),
  uploadStimulusAsset: (questionId: string, formData: FormData) =>
    apiCall<StimulusAsset>(`/admin/questions/${questionId}/stimulus-assets`, {
      method: 'POST',
      body: formData,
    }),
  deleteStimulusAsset: (questionId: string, assetId: string) =>
    apiCall<{ deleted: boolean }>(`/admin/questions/${questionId}/stimulus-assets/${assetId}`, {
      method: 'DELETE',
    }),
  extractStimulusAsset: (questionId: string, data: { stimulus_type?: string; replace_existing?: boolean } = {}) =>
    apiCall<StimulusExtractResponse>(`/admin/questions/${questionId}/extract-stimulus`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getStimulusExtractionJob: (jobId: string) =>
    apiCall<StimulusExtractionJob>(`/admin/stimulus-extraction-jobs/${jobId}`),

  // Analytics
  getGenerationAnalytics: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall<GenerationAnalytics>(`/admin/analytics/generation?${q}`)
  },
  getBatchAnalytics: (params: QueryParams = {}) => {
    const q = toQuery(params)
    return apiCall<BatchAnalytics>(`/admin/analytics/batches?${q}`)
  },
  getWeakSpots: (limit = 20) => apiCall<CohortWeakSpots>(`/admin/analytics/weak-spots?limit=${limit}`),

  // Student stats
  getStudentStats: (userId: number) => apiCall<StudentStats>(`/stats/${userId}`),
  getStudentActivity: (userId: number, days = 365) =>
    apiCall<ActivityDay[]>(`/stats/${userId}/activity?days=${days}`),

  // Auto-release
  getAutoReleaseStatus: () => apiCall<AutoReleaseStatus>('/admin/generation/auto-release/status'),
  enableAutoRelease: () => apiCall('/admin/generation/auto-release/enable', { method: 'POST' }),
  disableAutoRelease: () => apiCall('/admin/generation/auto-release/disable', { method: 'POST' }),

  // Controlled-vocabulary governance — read-only surfacing of master.json
  // (canonical keys per family) and candidates.json (off-vocab review queue).
  getVocabMaster: () => apiCall<VocabMaster>('/admin/vocab/master'),
  getVocabCandidates: () => apiCall<VocabCandidatesFile>('/admin/vocab/candidates'),

  // Generated-question candidates (draft inbox) + Markdown audit report
  getGeneratedQuestion: (id: string) => apiCall<GeneratedQuestionDetail>(`/admin/generated-questions/${id}`),
  getGeneratedQuestionReport: (id: string) =>
    apiCall<string>(`/admin/generated-questions/${id}/report`, { asText: true }),
}

/** Question generation — the /generate router (batch create + polling). */
export const generateApi = {
  createBatch: (body: GenerationBatchRequest) =>
    apiCall<GenerationBatchResponse>('/generate/batches', { method: 'POST', body: JSON.stringify(body) }),
  getBatch: (id: string) => apiCall<GenerationBatchStatus>(`/generate/batches/${id}`),
  getBatchJobs: (id: string) => apiCall<GenerationBatchJobs>(`/generate/batches/${id}/questions`),
  retryFailed: (id: string) =>
    apiCall<{ batch_id: string; retried_count: number }>(`/generate/batches/${id}/retry-failed`, { method: 'POST' }),
}
