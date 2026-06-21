import { useState } from 'react'
import { useTrapSusceptibility } from '../../hooks/useDashboardData'
import { TrapDetailView } from './TrapDetailView'

interface TrapMetric {
  trap_type: string
  fall_rate: number
  occurrences: number
  correct_count: number
  severity: 'critical' | 'high' | 'moderate' | 'low'
}

const SEVERITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: '#fef2f2', text: '#dc2626', border: '#fca5a5' },
  high:     { bg: '#fff7ed', text: '#ea580c', border: '#fdba74' },
  moderate: { bg: '#fefce8', text: '#ca8a04', border: '#fde047' },
  low:      { bg: '#f0fdf4', text: '#16a34a', border: '#86efac' },
}

function trapLabel(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function TrapCard({ metric, onClick }: { metric: TrapMetric; onClick: () => void }) {
  const colors = SEVERITY_COLORS[metric.severity]
  const pct = Math.round(metric.fall_rate * 100)
  return (
    <button
      onClick={onClick}
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: 10,
        padding: '14px 18px',
        textAlign: 'left',
        cursor: 'pointer',
        width: '100%',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontWeight: 600, color: colors.text, fontSize: 14 }}>
          {trapLabel(metric.trap_type)}
        </span>
        <span
          style={{
            background: colors.border,
            color: colors.text,
            borderRadius: 99,
            padding: '2px 8px',
            fontSize: 12,
            fontWeight: 700,
            whiteSpace: 'nowrap',
          }}
        >
          {pct}% miss rate
        </span>
      </div>
      <div style={{ marginTop: 4, fontSize: 12, color: '#6b7280' }}>
        {metric.occurrences} attempt{metric.occurrences !== 1 ? 's' : ''} · {metric.correct_count} correct
      </div>
    </button>
  )
}

export function TrapSusceptibilityDashboard() {
  const [selectedTrap, setSelectedTrap] = useState<string | null>(null)
  const { data, isLoading, isError, refetch } = useTrapSusceptibility()

  if (selectedTrap) {
    return <TrapDetailView trapType={selectedTrap} onBack={() => setSelectedTrap(null)} />
  }

  if (isLoading) {
    return (
      <div style={{ padding: 24, color: '#6b7280', fontSize: 14 }}>
        Loading trap analysis…
      </div>
    )
  }

  if (isError) {
    return (
      <div style={{ padding: 24 }}>
        <p style={{ color: '#dc2626', fontSize: 14 }}>Failed to load trap data.</p>
        <button
          onClick={() => refetch()}
          style={{ marginTop: 8, fontSize: 13, color: '#2563eb', background: 'none', border: 'none', cursor: 'pointer' }}
        >
          Retry
        </button>
      </div>
    )
  }

  if (!data || data.total_questions_attempted === 0) {
    return (
      <div style={{ padding: 24, color: '#6b7280', fontSize: 14, textAlign: 'center' }}>
        No trap data yet. Answer some questions to see your patterns.
      </div>
    )
  }

  const hasSusceptible = data.most_susceptible_traps.length > 0

  return (
    <div style={{ padding: '0 0 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Your Grammar Traps</h3>
        <span style={{ fontSize: 12, color: '#6b7280' }}>
          {data.total_questions_attempted} questions answered
        </span>
      </div>

      {!hasSusceptible && (
        <p style={{ fontSize: 13, color: '#16a34a', margin: '0 0 12px' }}>
          No trap patterns found yet — keep practicing!
        </p>
      )}

      {hasSusceptible && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
          {data.most_susceptible_traps.map((metric: TrapMetric) => (
            <TrapCard
              key={metric.trap_type}
              metric={metric}
              onClick={() => setSelectedTrap(metric.trap_type)}
            />
          ))}
        </div>
      )}

      {data.overcoming_traps.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: '#16a34a', margin: '0 0 6px' }}>
            ✓ Improving on
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {data.overcoming_traps.map((m: TrapMetric) => (
              <span
                key={m.trap_type}
                style={{
                  background: '#f0fdf4',
                  border: '1px solid #86efac',
                  color: '#16a34a',
                  borderRadius: 99,
                  padding: '3px 10px',
                  fontSize: 12,
                }}
              >
                {trapLabel(m.trap_type)}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.persistent_traps.length > 0 && (
        <div>
          <p style={{ fontSize: 12, fontWeight: 600, color: '#dc2626', margin: '0 0 6px' }}>
            ⚠ Still struggling with
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {data.persistent_traps.map((m: TrapMetric) => (
              <span
                key={m.trap_type}
                style={{
                  background: '#fef2f2',
                  border: '1px solid #fca5a5',
                  color: '#dc2626',
                  borderRadius: 99,
                  padding: '3px 10px',
                  fontSize: 12,
                }}
              >
                {trapLabel(m.trap_type)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
