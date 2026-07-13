import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from './AuthContext'

/**
 * Gate every admin route behind a session with role "admin".
 *
 * A signed-in non-admin Google account holds valid JWTs (the backend issues them to
 * any registered user), but every /admin endpoint would 403 — so instead of a broken
 * dashboard they get an explicit "not an admin" screen with sign-out as the only exit.
 */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const { status, profile, logout } = useAuth()
  const location = useLocation()

  // Resuming a stored session — showing the login page here would flash it on every
  // reload for an already-signed-in admin.
  if (status === 'bootstrapping') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
      </div>
    )
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (profile && profile.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 text-center">
          <h1 className="text-xl font-bold text-gray-900">Not an admin account</h1>
          <p className="mt-3 text-sm text-gray-600">
            <span className="font-medium">{profile.email}</span> is signed in, but it
            doesn't have admin access. Sign out and use an admin account.
          </p>
          <button
            onClick={() => logout()}
            className="mt-6 inline-flex items-center justify-center rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
