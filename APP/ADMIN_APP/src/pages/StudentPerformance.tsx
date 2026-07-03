import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { adminApi } from '../api/client'
import type { User, StudentStats, ActivityDay } from '../types'

function AccuracyBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct >= 70 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-400' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-500 w-8 text-right">{pct}%</span>
    </div>
  )
}

function bucketColor(count: number): string {
  if (count === 0) return 'bg-gray-100'
  if (count <= 2) return 'bg-emerald-200'
  if (count <= 5) return 'bg-emerald-300'
  if (count <= 10) return 'bg-emerald-500'
  return 'bg-emerald-700'
}

function ActivityHeatmap({ userId }: { userId: number }) {
  const { data, isLoading } = useQuery<ActivityDay[]>({
    queryKey: ['student-activity', userId],
    queryFn: () => adminApi.getStudentActivity(userId),
    retry: 1,
  })

  if (isLoading) return <div className="h-24 bg-gray-100 rounded-xl animate-pulse" />

  const counts = new Map((data ?? []).map((d) => [d.date, d.count]))
  const today = new Date()
  const days: { date: string; count: number }[] = []

  for (let i = 364; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    days.push({ date: key, count: counts.get(key) ?? 0 })
  }

  const weeks: { date: string; count: number }[][] = []
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7))
  }

  return (
    <div>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Activity</p>
      <div className="flex gap-0.5 overflow-x-auto pb-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-0.5">
            {week.map((day) => (
              <div
                key={day.date}
                title={`${day.date}: ${day.count} question${day.count === 1 ? '' : 's'}`}
                className={`w-2.5 h-2.5 rounded-sm ${bucketColor(day.count)}`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function StudentDetailPanel({ user }: { user: User }) {
  const { data: stats, isLoading } = useQuery<StudentStats>({
    queryKey: ['student-stats', user.id],
    queryFn: () => adminApi.getStudentStats(user.id),
    retry: 1,
  })

  if (isLoading) return <div className="h-32 bg-gray-100 rounded-xl animate-pulse mt-4" />

  if (!stats) return <div className="text-sm text-gray-400 mt-4">No data available.</div>

  const chartData = stats.top_missed_focus_keys.map((key) => ({
    key: key.replace(/_/g, ' '),
    misses: 1,
  }))

  return (
    <div className="mt-4 space-y-4 border-t border-gray-100 pt-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-gray-800">{stats.total_answered}</p>
          <p className="text-xs text-gray-500 mt-0.5">Answered</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-gray-800">{stats.total_correct}</p>
          <p className="text-xs text-gray-500 mt-0.5">Correct</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-gray-800">{Math.round(stats.accuracy * 100)}%</p>
          <p className="text-xs text-gray-500 mt-0.5">Accuracy</p>
        </div>
      </div>

      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Accuracy</p>
        <AccuracyBar value={stats.accuracy} />
      </div>

      <ActivityHeatmap userId={user.id} />

      {stats.top_missed_focus_keys.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Top Missed Areas</p>
          <div className="flex flex-wrap gap-1">
            {stats.top_missed_focus_keys.map((k) => (
              <span key={k} className="text-xs px-2 py-0.5 bg-red-50 text-red-700 rounded-full">
                {k.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {stats.top_missed_trap_keys.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Top Trap Keys Missed</p>
          <div className="flex flex-wrap gap-1">
            {stats.top_missed_trap_keys.map((k) => (
              <span key={k} className="text-xs px-2 py-0.5 bg-amber-50 text-amber-700 rounded-full">
                {k.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {chartData.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Missed by Focus Key</p>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: -20 }}>
              <XAxis dataKey="key" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="misses" radius={[4, 4, 0, 0]}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill="#ef4444" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

export function StudentPerformance() {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  const { data: users, isLoading, isError } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => adminApi.listUsers(),
    retry: 1,
  })

  const filtered = (users ?? []).filter((u) =>
    (u.email ?? u.username).toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Student Performance</h2>
        <p className="text-sm text-gray-500 mt-0.5">Track accuracy, weak areas, and progress per student</p>
      </div>

      {/* Search */}
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search students by email…"
        className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      />

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : isError ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center text-red-600 text-sm">
          Failed to load students. Backend may be offline.
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center text-gray-400 text-sm">
          No students found.
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((u) => (
            <div key={u.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedId(expandedId === u.id ? null : u.id)}
                className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 text-sm font-bold flex items-center justify-center flex-shrink-0">
                    {(u.email ?? u.username)[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{u.email ?? u.username}</p>
                    <p className="text-xs text-gray-400">ID #{u.id}</p>
                  </div>
                </div>
                <span className="text-gray-400 text-sm">{expandedId === u.id ? '▲' : '▼'}</span>
              </button>

              {expandedId === u.id && (
                <div className="px-5 pb-5">
                  <StudentDetailPanel user={u} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
