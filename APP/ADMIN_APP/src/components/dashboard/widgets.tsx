import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../../api/client'
import { PanelShell } from '../PanelShell'
import type { CohortWeakSpots, User } from '../../types'

function percent(value: unknown): number | null {
  return typeof value === 'number' ? Math.round(value * 100) : null
}

export function UsersWidget() {
  const { data: users, isLoading } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => adminApi.listUsers(),
    retry: 1,
  })

  return (
    <PanelShell title="Users">
      {isLoading ? (
        <div className="h-12 bg-gray-100 rounded animate-pulse" />
      ) : (
        <p className="text-3xl font-bold text-gray-800">{users?.length ?? '-'}</p>
      )}
      <p className="text-xs text-gray-400 mt-1">Total registered students</p>
    </PanelShell>
  )
}

export function GenerationWidget() {
  const { data, isLoading } = useQuery<any>({
    queryKey: ['analytics-generation'],
    queryFn: () => adminApi.getGenerationAnalytics(),
    retry: 1,
  })
  const rate = percent(data?.approve_rate ?? data?.acceptance_rate)
  const total = data?.total_generated ?? data?.generated_count ?? 0

  return (
    <PanelShell title="Generation Approve Rate">
      {isLoading ? (
        <div className="h-12 bg-gray-100 rounded animate-pulse" />
      ) : (
        <p className={`text-3xl font-bold ${rate !== null && rate >= 70 ? 'text-emerald-600' : 'text-amber-600'}`}>
          {rate !== null ? `${rate}%` : '-'}
        </p>
      )}
      <p className="text-xs text-gray-400 mt-1">{total} generated total</p>
    </PanelShell>
  )
}

export function AutoReleaseWidget() {
  const { data } = useQuery<any>({
    queryKey: ['auto-release-status'],
    queryFn: () => adminApi.getAutoReleaseStatus(),
    retry: 1,
  })
  const enabled = data?.enabled ?? data?.effective_enabled

  return (
    <PanelShell title="Auto-Release">
      <p className={`text-lg font-semibold ${enabled ? 'text-emerald-600' : 'text-red-500'}`}>
        {enabled ? 'Enabled' : 'Disabled'}
      </p>
      <p className="text-xs text-gray-400 mt-1">Manage from Pipeline & Backend</p>
    </PanelShell>
  )
}

export function RecentBatchesWidget() {
  const { data, isLoading } = useQuery<any>({
    queryKey: ['analytics-batches'],
    queryFn: () => adminApi.getBatchAnalytics(),
    retry: 1,
  })
  const rows = Array.isArray(data?.recent_batches) ? data.recent_batches.slice(0, 5) : []

  return (
    <PanelShell title="Recent Batches">
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-6 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-400">No recent batch list available.</p>
      ) : (
        <ul className="space-y-1.5">
          {rows.map((b: any) => (
            <li key={b.id} className="grid grid-cols-[1fr_auto_auto] gap-2 text-xs">
              <span className="text-gray-500 font-mono truncate">{String(b.id).slice(0, 8)}</span>
              <span className="text-emerald-600">{b.accepted_count ?? 0} ok</span>
              <span className="text-red-500">{b.rejected_count ?? 0} rej</span>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  )
}

export function WeakSpotsWidget() {
  const { data, isLoading } = useQuery<CohortWeakSpots>({
    queryKey: ['analytics-weak-spots'],
    queryFn: () => adminApi.getWeakSpots(),
    retry: 1,
  })
  const top = data?.focus_area_misses?.slice(0, 5) ?? []

  return (
    <PanelShell title="Cohort Weak Spots">
      {isLoading ? (
        <div className="h-16 bg-gray-100 rounded animate-pulse" />
      ) : top.length === 0 ? (
        <p className="text-sm text-gray-400">Not enough data yet.</p>
      ) : (
        <ul className="space-y-1.5">
          {top.map((f) => (
            <li key={`${f.domain}-${f.focus_key}`} className="grid grid-cols-[1fr_auto] gap-2 text-xs">
              <span className="text-gray-600 truncate">{f.focus_key.replace(/_/g, ' ')}</span>
              <span className="text-red-500 font-medium">{Math.round(f.miss_rate * 100)}% miss</span>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  )
}
