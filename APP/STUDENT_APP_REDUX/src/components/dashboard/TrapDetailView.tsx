import { useTrapDetails } from '../../hooks/useDashboardData'

interface TrapDetailViewProps {
  trapType: string
  onBack: () => void
}

function trapLabel(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

const SEVERITY_COLORS: Record<string, { text: string; bg: string; border: string }> = {
  critical: { text: '#dc2626', bg: '#fef2f2', border: '#fca5a5' },
  high:     { text: '#ea580c', bg: '#fff7ed', border: '#fdba74' },
  moderate: { text: '#ca8a04', bg: '#fefce8', border: '#fde047' },
  low:      { text: '#16a34a', bg: '#f0fdf4', border: '#86efac' },
}

export function TrapDetailView({ trapType, onBack }: TrapDetailViewProps) {
  const { data, isLoading, isError, refetch } = useTrapDetails(trapType)

  if (isLoading) {
    return (
      <div style={{ padding: 24, color: '#6b7280', fontSize: 14 }}>
        Loading trap details…
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div style={{ padding: 24 }}>
        <button onClick={onBack} style={backBtnStyle}>← Back</button>
        <p style={{ color: '#dc2626', fontSize: 14, marginTop: 12 }}>
          No data found for this trap.
        </p>
        <button
          onClick={() => refetch()}
          style={{ fontSize: 13, color: '#2563eb', background: 'none', border: 'none', cursor: 'pointer', marginTop: 4 }}
        >
          Retry
        </button>
      </div>
    )
  }

  const colors = SEVERITY_COLORS[data.severity] || SEVERITY_COLORS.moderate
  const trendUp = data.trend > 0
  const trendDown = data.trend < 0

  return (
    <div style={{ padding: '0 0 24px' }}>
      <button onClick={onBack} style={backBtnStyle}>← Back</button>

      <div style={{ marginTop: 16, marginBottom: 20 }}>
        <h2 style={{ margin: '0 0 4px', fontSize: 18, fontWeight: 700 }}>
          {trapLabel(trapType)}
        </h2>
        <span
          style={{
            background: colors.bg,
            border: `1px solid ${colors.border}`,
            color: colors.text,
            borderRadius: 99,
            padding: '2px 10px',
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          {data.severity} severity
        </span>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
        <StatCard label="Miss rate" value={`${Math.round(data.user_fall_rate * 100)}%`} color={colors.text} />
        <StatCard label="Attempts" value={String(data.user_encounters)} />
        <StatCard
          label="Trend"
          value={trendUp ? `↑ +${Math.round(data.trend * 100)}%` : trendDown ? `↓ ${Math.round(data.trend * 100)}%` : '→ Flat'}
          color={trendUp ? '#16a34a' : trendDown ? '#dc2626' : '#6b7280'}
        />
      </div>

      {/* Improvement bar */}
      <div style={{ background: '#f9fafb', borderRadius: 10, padding: '12px 16px', marginBottom: 20 }}>
        <p style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 600, color: '#374151' }}>
          Your Progress
        </p>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>
          <span>First 5 attempts</span>
          <span>Recent 5 attempts</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#6b7280', minWidth: 36 }}>
            {Math.round(data.first_accuracy * 100)}%
          </span>
          <div style={{ flex: 1, height: 6, background: '#e5e7eb', borderRadius: 99, overflow: 'hidden' }}>
            <div style={{ width: `${data.recent_accuracy * 100}%`, height: '100%', background: trendUp ? '#16a34a' : '#ef4444', borderRadius: 99 }} />
          </div>
          <span style={{ fontSize: 13, fontWeight: 600, color: trendUp ? '#16a34a' : '#dc2626', minWidth: 36, textAlign: 'right' }}>
            {Math.round(data.recent_accuracy * 100)}%
          </span>
        </div>
      </div>

      {/* Example mistakes */}
      {data.example_mistakes.length > 0 && (
        <div>
          <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 600, color: '#374151' }}>
            Example Questions You Missed
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {data.example_mistakes.map((ex: any, i: number) => (
              <div
                key={i}
                style={{
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: 8,
                  padding: '12px 14px',
                  fontSize: 13,
                }}
              >
                {ex.grammar_focus && (
                  <span style={{ fontSize: 11, color: '#6b7280', display: 'block', marginBottom: 4 }}>
                    Focus: {trapLabel(ex.grammar_focus)}
                  </span>
                )}
                <p style={{ margin: '0 0 6px', color: '#1f2937', lineHeight: 1.5 }}>
                  {ex.question_text || '(Question text not available)'}
                </p>
                <span style={{ fontSize: 12, color: '#dc2626' }}>
                  You chose: {ex.selected_option}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.example_mistakes.length === 0 && (
        <p style={{ fontSize: 13, color: '#16a34a', marginTop: 12 }}>
          No mistakes recorded for this trap yet.
        </p>
      )}
    </div>
  )
}

const backBtnStyle: React.CSSProperties = {
  background: 'none',
  border: '1px solid #e5e7eb',
  borderRadius: 6,
  padding: '4px 12px',
  fontSize: 13,
  color: '#374151',
  cursor: 'pointer',
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ background: '#f9fafb', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || '#1f2937' }}>{value}</div>
      <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{label}</div>
    </div>
  )
}
