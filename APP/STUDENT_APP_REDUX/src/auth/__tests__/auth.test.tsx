import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// authStore reads localStorage at import time, so each test re-imports it fresh.
async function freshModules() {
  vi.resetModules()
  const store = await import('../authStore')
  const client = await import('../../api/client')
  return { store, client }
}

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: String(status),
    json: async () => body,
    clone() {
      return this
    },
  } as unknown as Response
}

beforeEach(() => {
  localStorage.clear()
  vi.unstubAllEnvs()
})

afterEach(() => {
  vi.restoreAllMocks()
})

// The VITE_TEST_USER_TOKEN layer of getUserToken() has no test: Vite inlines
// import.meta.env.VITE_* at transform time, so it reads as undefined under vitest and
// vi.stubEnv can't reach it. The two layers below are the ones that actually vary.
describe('getUserToken', () => {
  it('prefers the signed-in profile over the legacy fallback', async () => {
    localStorage.setItem('user_token', 'legacy-uuid')
    const { store } = await freshModules()
    store.setProfile({
      id: 1,
      username: 'ada',
      email: 'ada@example.com',
      role: 'student',
      created_at: '2026-01-01T00:00:00Z',
      user_token: 'profile-uuid',
    })
    expect(store.getUserToken()).toBe('profile-uuid')
  })

  it('falls back to the legacy localStorage token when nobody is signed in', async () => {
    localStorage.setItem('user_token', 'legacy-uuid')
    const { store } = await freshModules()
    expect(store.getUserToken()).toBe('legacy-uuid')
  })

  it('clearing the session drops back to the legacy token', async () => {
    localStorage.setItem('user_token', 'legacy-uuid')
    const { store } = await freshModules()
    store.setProfile({
      id: 1,
      username: 'ada',
      email: 'ada@example.com',
      role: 'student',
      created_at: '2026-01-01T00:00:00Z',
      user_token: 'profile-uuid',
    })
    store.clearSession()
    expect(store.getUserToken()).toBe('legacy-uuid')
  })
})

describe('apiCall auth', () => {
  it('sends the JWT access token as a Bearer header', async () => {
    const { store, client } = await freshModules()
    store.setTokens({ access_token: 'jwt-access', refresh_token: 'jwt-refresh' })

    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await client.apiCall('/stats/1')

    const headers = fetchMock.mock.calls[0][1].headers
    expect(headers.Authorization).toBe('Bearer jwt-access')
    // Legacy key still goes out — both auth paths run in parallel.
    expect(headers['X-API-Key']).toBeTruthy()
  })

  it('refreshes once on 401 and retries the original request', async () => {
    const { store, client } = await freshModules()
    store.setTokens({ access_token: 'stale', refresh_token: 'good-refresh' })

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(
        jsonResponse({ access_token: 'fresh', refresh_token: 'rotated', expires_in: 900 }),
      )
      .mockResolvedValueOnce(jsonResponse({ data: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await client.apiCall('/stats/1')

    expect(result).toEqual({ data: 'ok' })
    expect(fetchMock.mock.calls[1][0]).toContain('/auth/refresh')
    // Retry carries the refreshed token, and the rotated refresh token is stored.
    expect(fetchMock.mock.calls[2][1].headers.Authorization).toBe('Bearer fresh')
    expect(store.getAccessToken()).toBe('fresh')
    expect(store.getRefreshToken()).toBe('rotated')
  })

  it('clears the session when the refresh token is dead, without looping', async () => {
    const { store, client } = await freshModules()
    store.setTokens({ access_token: 'stale', refresh_token: 'dead-refresh' })

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(jsonResponse({ detail: 'invalid' }, 401)) // refresh rejected
    vi.stubGlobal('fetch', fetchMock)

    await expect(client.apiCall('/stats/1')).rejects.toThrow(/401/)

    // One original + one refresh attempt: no retry storm.
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(store.hasSession()).toBe(false)
    expect(store.getAccessToken()).toBeNull()
  })
})

describe('RequireAuth', () => {
  it('redirects an anonymous visitor to the login page', async () => {
    const { AuthProvider } = await import('../AuthContext')
    const { RequireAuth } = await import('../RequireAuth')

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<div>Login page</div>} />
              <Route
                path="/"
                element={
                  <RequireAuth>
                    <div>Secret dashboard</div>
                  </RequireAuth>
                }
              />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument())
    expect(screen.queryByText('Secret dashboard')).not.toBeInTheDocument()
  })

  it('restores a stored session on load and renders the guarded route', async () => {
    localStorage.setItem('auth.access_token', 'jwt-access')
    localStorage.setItem('auth.refresh_token', 'jwt-refresh')

    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: 1,
        username: 'ada',
        email: 'ada@example.com',
        role: 'student',
        created_at: '2026-01-01T00:00:00Z',
        user_token: 'profile-uuid',
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    vi.resetModules()
    const { AuthProvider } = await import('../AuthContext')
    const { RequireAuth } = await import('../RequireAuth')

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<div>Login page</div>} />
              <Route
                path="/"
                element={
                  <RequireAuth>
                    <div>Secret dashboard</div>
                  </RequireAuth>
                }
              />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => expect(screen.getByText('Secret dashboard')).toBeInTheDocument())
    expect(fetchMock.mock.calls[0][0]).toContain('/auth/me')
  })

  // The real "remember me" path: on a return visit the access token has expired but the
  // refresh token hasn't, so bootstrap must refresh rather than bounce to /login.
  it('refreshes an expired access token on load instead of logging the student out', async () => {
    localStorage.setItem('auth.access_token', 'expired-access')
    localStorage.setItem('auth.refresh_token', 'good-refresh')

    const profile = {
      id: 1,
      username: 'ada',
      email: 'ada@example.com',
      role: 'student',
      created_at: '2026-01-01T00:00:00Z',
      user_token: 'profile-uuid',
    }

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'expired' }, 401)) // /auth/me
      .mockResolvedValueOnce(
        jsonResponse({ access_token: 'fresh', refresh_token: 'rotated', expires_in: 900 }),
      )
      .mockResolvedValueOnce(jsonResponse(profile)) // /auth/me retried
    vi.stubGlobal('fetch', fetchMock)

    vi.resetModules()
    const { AuthProvider } = await import('../AuthContext')
    const { RequireAuth } = await import('../RequireAuth')
    const store = await import('../authStore')

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<div>Login page</div>} />
              <Route
                path="/"
                element={
                  <RequireAuth>
                    <div>Secret dashboard</div>
                  </RequireAuth>
                }
              />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => expect(screen.getByText('Secret dashboard')).toBeInTheDocument())
    expect(screen.queryByText('Login page')).not.toBeInTheDocument()
    expect(fetchMock.mock.calls[1][0]).toContain('/auth/refresh')
    expect(store.getUserToken()).toBe('profile-uuid')
  })
})
