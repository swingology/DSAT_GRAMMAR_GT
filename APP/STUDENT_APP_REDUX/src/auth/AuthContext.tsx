import { createContext, useContext, useCallback, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import {
  clearSession,
  getProfile,
  hasSession,
  setProfile as storeProfile,
  setTokens,
  subscribe,
  type AuthProfile,
} from './authStore'

type AuthStatus = 'bootstrapping' | 'authenticated' | 'anonymous'

interface AuthContextValue {
  status: AuthStatus
  profile: AuthProfile | null
  /** Exchange a GIS popup credential for a session. Throws on rejection. */
  loginWithGoogle: (credential: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

/** Sign the user out of Google too, so the next login re-prompts for an account. */
function disableGoogleAutoSelect() {
  try {
    ;(window as any).google?.accounts?.id?.disableAutoSelect?.()
  } catch {
    // GIS script may not have loaded; nothing to reset.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>(hasSession() ? 'bootstrapping' : 'anonymous')
  const [profile, setProfileState] = useState<AuthProfile | null>(getProfile())
  const queryClient = useQueryClient()

  // Resume an existing session on load. apiCall silently refreshes an expired access
  // token, so this only fails when the refresh token is dead too.
  useEffect(() => {
    if (!hasSession()) return

    let cancelled = false
    ;(async () => {
      try {
        const me = await api.me()
        if (cancelled) return
        storeProfile(me)
        setProfileState(me)
        setStatus('authenticated')
      } catch {
        if (cancelled) return
        clearSession()
        setStatus('anonymous')
      }
    })()

    return () => {
      cancelled = true
    }
  }, [])

  // client.ts clears the store when a refresh fails mid-session; reflect that here so
  // the route guard bounces to the login page.
  useEffect(
    () =>
      subscribe(() => {
        if (!hasSession()) {
          setProfileState(null)
          setStatus('anonymous')
        }
      }),
    [],
  )

  const loginWithGoogle = useCallback(async (credential: string) => {
    const tokens = await api.googleLogin(credential)
    setTokens(tokens)

    // The token response carries no user_token — only /me does, and every legacy
    // endpoint needs it.
    const me = await api.me()
    storeProfile(me)
    setProfileState(me)
    setStatus('authenticated')
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // Best effort: a dead token server-side still means we drop the local session.
    }
    disableGoogleAutoSelect()
    clearSession()
    setProfileState(null)
    setStatus('anonymous')

    // Query keys don't include the user token, so cached answers/progress would
    // otherwise be served to whoever signs in next on this browser.
    queryClient.clear()
  }, [queryClient])

  return (
    <AuthContext.Provider value={{ status, profile, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used within an AuthProvider')
  return value
}
