import { useEffect, useRef, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { GOOGLE_CLIENT_ID, useGoogleScript } from '../auth/useGoogleScript'

export function LoginPage() {
  const { status, loginWithGoogle } = useAuth()
  const scriptStatus = useGoogleScript()
  const buttonRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [signingIn, setSigningIn] = useState(false)

  useEffect(() => {
    if (scriptStatus !== 'ready' || !GOOGLE_CLIENT_ID || !buttonRef.current) return

    const google = (window as any).google
    google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: async (response: { credential: string }) => {
        setError(null)
        setSigningIn(true)
        try {
          await loginWithGoogle(response.credential)
        } catch (err) {
          // The backend returns a deliberately generic message for unregistered
          // emails; surface it as-is rather than inventing our own.
          setError((err as any)?.detail || 'Sign-in failed. Please try again.')
          setSigningIn(false)
        }
      },
    })

    google.accounts.id.renderButton(buttonRef.current, {
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      shape: 'pill',
      width: 280,
    })
  }, [scriptStatus, loginWithGoogle])

  if (status === 'authenticated') return <Navigate to="/" replace />

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900">DSAT Practice</h1>
        <p className="mt-2 text-sm text-gray-600">
          Sign in with the Google account your tutor registered for you.
        </p>

        <div className="mt-8 flex justify-center min-h-[44px]">
          {!GOOGLE_CLIENT_ID ? (
            <p className="text-sm text-red-600">
              VITE_GOOGLE_CLIENT_ID is not set — the sign-in button cannot load.
            </p>
          ) : scriptStatus === 'error' ? (
            <p className="text-sm text-red-600">
              Couldn't reach Google sign-in. Check your connection and reload.
            </p>
          ) : (
            <>
              {/* The button div stays mounted across a failed sign-in. Swapping it out
                  would leave GIS holding a detached node, and it would never re-render
                  the button — leaving a rejected user unable to retry without a reload. */}
              <div ref={buttonRef} hidden={signingIn} />
              {signingIn && <p className="text-sm text-gray-500">Signing you in…</p>}
            </>
          )}
        </div>

        {error && (
          <p className="mt-6 text-sm text-red-600 bg-red-50 rounded-lg px-4 py-3">{error}</p>
        )}
      </div>
    </div>
  )
}
