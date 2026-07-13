import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

/** Signed-in identity + sign-out, shown on the dashboard. */
export function UserMenu() {
  const { profile, logout } = useAuth()
  const navigate = useNavigate()

  if (!profile) return null

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600 hidden sm:inline" title={profile.email}>
        {profile.username}
      </span>
      <button
        onClick={handleLogout}
        className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-lg px-3 py-1.5 hover:bg-gray-100 transition-colors"
      >
        <LogOut size={16} />
        Sign out
      </button>
    </div>
  )
}
