// Session state for the logged-in student.
//
// This is a plain module rather than a React context because `api/client.ts` needs to
// read tokens outside of a component. AuthContext subscribes to this store and mirrors
// it into React state.

export interface AuthProfile {
  id: number
  username: string
  email: string
  role: string
  created_at: string
  /** UUID the legacy endpoints take as a `user_token` param — not the JWT. */
  user_token: string
}

const ACCESS_KEY = 'auth.access_token'
const REFRESH_KEY = 'auth.refresh_token'
const PROFILE_KEY = 'auth.profile'

type Listener = () => void
const listeners = new Set<Listener>()

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    // Private-mode / storage-disabled browsers still work for the current tab.
  }
}

let accessToken: string | null = read(ACCESS_KEY)
let refreshToken: string | null = read(REFRESH_KEY)
let profile: AuthProfile | null = (() => {
  const raw = read(PROFILE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthProfile
  } catch {
    return null
  }
})()

function notify() {
  listeners.forEach((listener) => listener())
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getAccessToken(): string | null {
  return accessToken
}

export function getRefreshToken(): string | null {
  return refreshToken
}

export function getProfile(): AuthProfile | null {
  return profile
}

/**
 * The `user_token` UUID the legacy endpoints expect in bodies and query params.
 *
 * Falls back to the pre-OAuth env var / localStorage sources so scripts, tests, and
 * existing sessions keep working while both auth paths run in parallel.
 */
export function getUserToken(): string {
  return (
    profile?.user_token ||
    (import.meta as any).env.VITE_TEST_USER_TOKEN ||
    read('user_token') ||
    ''
  )
}

export function hasSession(): boolean {
  return accessToken !== null
}

export function setTokens(next: { access_token: string; refresh_token: string }) {
  accessToken = next.access_token
  refreshToken = next.refresh_token
  write(ACCESS_KEY, accessToken)
  write(REFRESH_KEY, refreshToken)
  notify()
}

export function setProfile(next: AuthProfile) {
  profile = next
  write(PROFILE_KEY, JSON.stringify(next))
  notify()
}

export function clearSession() {
  accessToken = null
  refreshToken = null
  profile = null
  write(ACCESS_KEY, null)
  write(REFRESH_KEY, null)
  write(PROFILE_KEY, null)
  notify()
}
