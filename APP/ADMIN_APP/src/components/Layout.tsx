import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '⌂' },
  { to: '/users', label: 'User Management', icon: '👥' },
  { to: '/data', label: 'Data Management', icon: '📋' },
  { to: '/students', label: 'Student Performance', icon: '📈' },
  { to: '/pipeline', label: 'Pipeline & Backend', icon: '⚙️' },
  { to: '/vocabulary', label: 'Vocabulary', icon: '🔑' },
  { to: '/generate', label: 'Generate', icon: '✨' },
]

const APP_VERSION = import.meta.env.VITE_APP_VERSION || 'dev'

export function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const { profile, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`flex-shrink-0 bg-gray-900 text-white flex flex-col transition-all duration-200 ${
          collapsed ? 'w-16' : 'w-56'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-800">
          {!collapsed && (
            <span className="text-sm font-bold tracking-wide text-white">DSAT Admin</span>
          )}
          <button
            onClick={() => setCollapsed((v) => !v)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="text-gray-400 hover:text-white transition p-1 rounded"
          >
            {collapsed ? '→' : '←'}
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800',
                ].join(' ')
              }
            >
              <span className="text-base flex-shrink-0" aria-hidden="true">{item.icon}</span>
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-800 text-xs text-gray-500">
          {!collapsed && `DSAT Admin ${APP_VERSION}`}
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <h1 className="text-base font-semibold text-gray-800">Admin Dashboard</h1>
          <div className="flex items-center gap-3">
            {profile ? (
              <span className="text-xs text-gray-500 hidden sm:inline" title={profile.username}>
                {profile.email}
              </span>
            ) : (
              <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">Admin</span>
            )}
            <button
              onClick={handleLogout}
              className="text-xs font-medium text-gray-600 hover:text-gray-900 rounded-lg px-3 py-1.5 hover:bg-gray-100 transition-colors"
            >
              Sign out
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
