import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from 'recharts'
import { adminApi } from '../api/client'
import type { GenerationAnalytics, BatchAnalytics } from '../types'

function StatCard({
  label, value, sub, color = 'text-gray-800',
}: {
  label: string
  value: string | number
  sub?: string
  color?: string
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-base font-semibold text-gray-800">{title}</h3>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  )
}

export function PipelinePerformance() {
  const qc = useQueryClient()

  const { data: gen, isLoading: genLoading } = useQuery<GenerationAnalytics>({
    queryKey: ['analytics-generation'],
    queryFn: () => adminApi.getGenerationAnalytics(),
    retry: 1,
  })

  const { data: batches, isLoading: batchLoading } = useQuery<BatchAnalytics>({
    queryKey: ['analytics-batches'],
    queryFn: () => adminApi.getBatchAnalytics(),
    retry: 1,
  })

  const { data: autoRelease } = useQuery({
    queryKey: ['auto-release-status'],
    queryFn: () => adminApi.getAutoReleaseStatus(),
    retry: 1,
  })

  const enableMutation = useMutation({
    mutationFn: () => adminApi.enableAutoRelease(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['auto-release-status'] }),
  })
  const disableMutation = useMutation({
    mutationFn: () => adminApi.disableAutoRelease(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['auto-release-status'] }),
  })

  const approveRate = gen ? Math.round((gen.approve_rate ?? 0) * 100) : null
  const modelChartData = gen?.by_model?.map((m) => ({
    name: m.model_name.split('/').pop()?.slice(0, 12) ?? m.model_name,
    generated: m.generated_count,
    approved: m.approved_count,
    rejected: m.rejected_count,
  })) ?? []

  const batchChartData = batches?.recent_batches?.slice(0, 10).reverse().map((b) => ({
    date: new Date(b.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    accepted: b.accepted_count,
    rejected: b.rejected_count,
  })) ?? []

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Pipeline & Backend Performance</h2>
        <p className="text-sm text-gray-500 mt-0.5">Generation quality, batch throughput, and system controls</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {genLoading ? (
          [...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          ))
        ) : (
          <>
            <StatCard
              label="Total Generated"
              value={gen?.total_generated?.toLocaleString() ?? '—'}
            />
            <StatCard
              label="Approve Rate"
              value={approveRate !== null ? `${approveRate}%` : '—'}
              color={approveRate !== null && approveRate >= 70 ? 'text-emerald-600' : 'text-amber-600'}
            />
            <StatCard
              label="Total Approved"
              value={gen?.total_approved?.toLocaleString() ?? '—'}
              color="text-emerald-600"
            />
            <StatCard
              label="Total Rejected"
              value={gen?.total_rejected?.toLocaleString() ?? '—'}
              color="text-red-500"
            />
          </>
        )}
      </div>

      {/* Auto-Release Control */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between">
          <div>
            <SectionHeader title="Auto-Release" sub="Automatically publish approved generated questions" />
            <p className="text-xs text-gray-500 -mt-2">
              Status:{' '}
              <span className={autoRelease?.enabled ? 'text-emerald-600 font-medium' : 'text-red-500 font-medium'}>
                {autoRelease?.enabled ? 'Enabled' : 'Disabled'}
              </span>
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => enableMutation.mutate()}
              disabled={autoRelease?.enabled || enableMutation.isPending}
              className="px-4 py-2 text-sm bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg disabled:opacity-40 transition"
            >
              Enable
            </button>
            <button
              onClick={() => disableMutation.mutate()}
              disabled={!autoRelease?.enabled || disableMutation.isPending}
              className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-40 transition"
            >
              Disable
            </button>
          </div>
        </div>
      </div>

      {/* Model Performance Chart */}
      {modelChartData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <SectionHeader title="Performance by Model" sub="Generated, approved, and rejected counts per LLM" />
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={modelChartData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="generated" fill="#93c5fd" radius={[3, 3, 0, 0]} />
              <Bar dataKey="approved" fill="#6ee7b7" radius={[3, 3, 0, 0]} />
              <Bar dataKey="rejected" fill="#fca5a5" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent Batch Trend */}
      {batchChartData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <SectionHeader title="Recent Batch Trend" sub="Accepted vs rejected per batch over time" />
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={batchChartData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="accepted" stroke="#10b981" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="rejected" stroke="#ef4444" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Domain breakdown */}
      {gen?.by_domain && gen.by_domain.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <SectionHeader title="Approve Rate by Domain" />
          <div className="space-y-3">
            {gen.by_domain.map((d) => {
              const pct = Math.round((d.approve_rate ?? 0) * 100)
              return (
                <div key={d.domain}>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span className="capitalize">{d.domain}</span>
                    <span>{d.generated_count} generated · {pct}% approved</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: pct >= 70 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#ef4444',
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Recent Batches Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-x-auto">
        <div className="px-5 py-4 border-b border-gray-100">
          <SectionHeader title="Recent Batches" sub="Latest generation batches and their outcomes" />
        </div>
        {batchLoading ? (
          <div className="space-y-2 p-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : !batches?.recent_batches?.length ? (
          <div className="p-8 text-center text-gray-400 text-sm">No batch data available.</div>
        ) : (
          <table className="w-full min-w-[860px] text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Batch ID</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Requested by</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Requested</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Accepted</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Rejected</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {batches.recent_batches.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{b.id.slice(0, 8)}…</td>
                  <td className="px-4 py-3 text-xs text-gray-500 capitalize">{b.requested_by?.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${
                      b.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                      b.status === 'failed' ? 'bg-red-100 text-red-600' :
                      'bg-amber-100 text-amber-700'
                    }`}>
                      {b.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">{b.requested_count}</td>
                  <td className="px-4 py-3 text-xs text-emerald-600 font-medium">{b.accepted_count}</td>
                  <td className="px-4 py-3 text-xs text-red-500 font-medium">{b.rejected_count}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {new Date(b.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
