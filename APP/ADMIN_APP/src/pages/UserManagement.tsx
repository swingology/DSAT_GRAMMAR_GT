import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../api/client'
import type { User } from '../types'

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
    </div>
  )
}

function CreateUserModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const mutation = useMutation({
    mutationFn: (data: any) => adminApi.createUser(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Create User</h2>
        <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="student_username"
        />
        <label className="block text-sm font-medium text-gray-700 mb-1">Email (optional)</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="student@example.com"
        />
        {mutation.isError && (
          <p className="text-red-600 text-sm mb-3">Failed to create user.</p>
        )}
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate({ username, email: email || undefined })}
            disabled={!username || mutation.isPending}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition"
          >
            {mutation.isPending ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

function EditUserModal({ user, onClose }: { user: User; onClose: () => void }) {
  const qc = useQueryClient()
  const [username, setUsername] = useState(user.username)
  const [email, setEmail] = useState(user.email ?? '')
  const [role, setRole] = useState(user.role)
  const [isActive, setIsActive] = useState(user.is_active)
  const mutation = useMutation({
    mutationFn: () =>
      adminApi.updateUser(user.id, {
        username,
        email: email.trim() || null,
        role,
        is_active: isActive,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Edit User</h2>
        <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="student">student</option>
          <option value="admin">admin</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-700 mb-4">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Active account
        </label>
        {mutation.isError && <p className="text-red-600 text-sm mb-3">Failed to update user.</p>}
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!username || mutation.isPending}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition"
          >
            {mutation.isPending ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ResetPasswordModal({ user, onClose }: { user: User; onClose: () => void }) {
  const [newPassword, setNewPassword] = useState('')
  const [done, setDone] = useState(false)
  const mutation = useMutation({
    mutationFn: () => adminApi.resetUserPassword(user.id, newPassword),
    onSuccess: () => setDone(true),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold text-gray-800 mb-2">Reset Password</h2>
        <p className="text-sm text-gray-500 mb-4">for {user.email ?? user.username}</p>

        {done ? (
          <>
            <p className="text-sm text-gray-700 mb-2">Password reset. Share this with the student:</p>
            <p className="font-mono text-sm bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 mb-4 break-all">
              {newPassword}
            </p>
            <div className="flex justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Done
              </button>
            </div>
          </>
        ) : (
          <>
            <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
            <input
              type="text"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {mutation.isError && <p className="text-red-600 text-sm mb-3">Failed to reset password.</p>}
            <div className="flex gap-2 justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => mutation.mutate()}
                disabled={newPassword.length < 8 || mutation.isPending}
                className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50 transition"
              >
                {mutation.isPending ? 'Resetting...' : 'Reset Password'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export function UserManagement() {
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<User | null>(null)
  const [resetTarget, setResetTarget] = useState<User | null>(null)
  const [search, setSearch] = useState('')
  const qc = useQueryClient()

  const { data: users, isLoading, isError } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => adminApi.listUsers(),
    retry: 1,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminApi.deleteUser(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  const filtered = (users ?? []).filter((u) =>
    (u.email ?? u.username).toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-800">User Management</h2>
          <p className="text-sm text-gray-500 mt-0.5">Manage student accounts</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
        >
          + New User
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Total Users" value={users?.length ?? '—'} />
        <StatCard label="Active" value={users?.length ?? '—'} />
        <StatCard label="New This Week" value="—" />
      </div>

      {/* Search */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by email or username…"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-8 text-center text-red-600 text-sm">Failed to load users. Backend may be offline.</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No users found.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">ID</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Email</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Token</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">{u.id}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{u.email ?? u.username}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-400 truncate max-w-xs">
                    {u.user_token?.slice(0, 16)}…
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setEditTarget(u)}
                      className="text-xs text-blue-500 hover:text-blue-700 transition mr-3"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setResetTarget(u)}
                      className="text-xs text-amber-600 hover:text-amber-700 transition mr-3"
                    >
                      Reset Password
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete user ${u.email ?? u.username}?`)) deleteMutation.mutate(u.id)
                      }}
                      className="text-xs text-red-500 hover:text-red-700 transition"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} />}
      {editTarget && <EditUserModal user={editTarget} onClose={() => setEditTarget(null)} />}
      {resetTarget && (
        <ResetPasswordModal user={resetTarget} onClose={() => setResetTarget(null)} />
      )}
    </div>
  )
}
