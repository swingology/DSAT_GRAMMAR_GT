import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProgressTrend, useDomainTrend, useFocusSummary } from '../hooks/useDashboardData'

// ── Inline SVG line chart ──────────────────────────────────────────────────

interface Point { date: string; accuracy: number; attempts: number }

function LineChart({ points, color = '#2563eb', label }: { points: Point[]; color?: string; label: string }) {
  if (points.length === 0) {
    return (
      <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', fontSize: 13 }}>
        No data yet
      </div>
    )
  }

  const W = 300, H = 80, PAD = 8
  const values = points.map(p => p.accuracy)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 0.1

  const x = (i: number) => PAD + (i / Math.max(points.length - 1, 1)) * (W - PAD * 2)
  const y = (v: number) => H - PAD - ((v - min) / range) * (H - PAD * 2)

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(p.accuracy).toFixed(1)}`).join(' ')
  const areaD = `${pathD} L ${x(points.length - 1).toFixed(1)} ${H} L ${x(0).toFixed(1)} ${H} Z`

  return (
    <div>
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: H }}>
        <defs>
          <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.15" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaD} fill={`url(#grad-${color.replace('#', '')})`} />
        <path d={pathD} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {points.map((p, i) => (
          <circle key={i} cx={x(i)} cy={y(p.accuracy)} r="2.5" fill={color} />
        ))}
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
        <span>{points[0]?.date?.slice(5)}</span>
        <span>{points[points.length - 1]?.date?.slice(5)}</span>
      </div>
    </div>
  )
}

// ── Inline bar chart ───────────────────────────────────────────────────────

interface BarItem { label: string; value: number; domain: string }

function BarChart({ items }: { items: BarItem[] }) {
  if (items.length === 0) {
    return <p style={{ fontSize: 13, color: '#9ca3af' }}>No data yet</p>
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map((item) => {
        const pct = Math.round(item.value * 100)
        const color = item.domain === 'grammar' ? '#2563eb' : '#7c3aed'
        const barColor = pct < 50 ? '#ef4444' : pct < 70 ? '#f59e0b' : '#22c55e'
        return (
          <div key={item.label}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
              <span style={{ color: '#374151' }}>
                <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: color, marginRight: 5 }} />
                {item.label.replace(/_/g, ' ')}
              </span>
              <span style={{ fontWeight: 600, color: barColor }}>{pct}%</span>
            </div>
            <div style={{ height: 6, background: '#f3f4f6', borderRadius: 99, overflow: 'hidden' }}>
              <div style={{ width: `${pct}%`, height: '100%', background: barColor, borderRadius: 99 }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Stat pill ──────────────────────────────────────────────────────────────

function StatPill({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{ background: '#f9fafb', borderRadius: 10, padding: '12px 16px', textAlign: 'center', flex: 1 }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: '#111827' }}>{value}</div>
      <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 1 }}>{sub}</div>}
    </div>
  )
}

// ── Day selector ───────────────────────────────────────────────────────────

function DayPicker({ value, onChange }: { value: number; onChange: (d: number) => void }) {
  return (
    <div style={{ display: 'flex', gap: 6 }}>
      {[7, 14, 30, 60].map(d => (
        <button
          key={d}
          onClick={() => onChange(d)}
          style={{
            padding: '4px 10px',
            borderRadius: 99,
            border: '1px solid',
            borderColor: value === d ? '#2563eb' : '#e5e7eb',
            background: value === d ? '#2563eb' : '#fff',
            color: value === d ? '#fff' : '#374151',
            fontSize: 12,
            cursor: 'pointer',
            fontWeight: value === d ? 600 : 400,
          }}
        >
          {d}d
        </button>
      ))}
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

export function ProgressPage() {
  const navigate = useNavigate()
  const [days, setDays] = useState(30)

  const trend = useProgressTrend(days)
  const domain = useDomainTrend(days)
  const focus = useFocusSummary()

  const trendData = trend.data
  const domainData = domain.data
  const focusData = focus.data

  const overallPct = trendData ? Math.round(trendData.overall_accuracy * 100) : null

  return (
    <div style={{ maxWidth: 480, margin: '0 auto', padding: '20px 16px 40px', fontFamily: 'system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button
          onClick={() => navigate('/')}
          style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: 6, padding: '4px 12px', fontSize: 13, color: '#374151', cursor: 'pointer' }}
        >
          ← Dashboard
        </button>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Your Progress</h1>
      </div>

      {/* Day picker */}
      <div style={{ marginBottom: 20 }}>
        <DayPicker value={days} onChange={setDays} />
      </div>

      {/* Summary pills */}
      {trendData && (
        <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
          <StatPill label="Overall accuracy" value={`${overallPct}%`} />
          <StatPill label="Questions answered" value={String(trendData.total_attempts)} />
          <StatPill label="Day streak" value={String(trendData.streak_days)} sub="days in a row" />
        </div>
      )}

      {trend.isLoading && <LoadingCard label="Loading trend…" />}
      {trend.isError && <ErrorCard label="Couldn't load trend" onRetry={() => trend.refetch()} />}

      {/* Overall accuracy chart */}
      {trendData && trendData.points.length > 0 && (
        <Card title="Accuracy over time">
          <LineChart
            points={trendData.points}
            label={`Last ${days} days · ${trendData.points.length} active days`}
            color="#2563eb"
          />
        </Card>
      )}

      {/* Domain split */}
      {domainData && (domainData.grammar.length > 0 || domainData.reading.length > 0) && (
        <Card title="By domain">
          {domainData.grammar.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <LineChart points={domainData.grammar} label="Grammar" color="#2563eb" />
            </div>
          )}
          {domainData.reading.length > 0 && (
            <LineChart points={domainData.reading} label="Reading" color="#7c3aed" />
          )}
        </Card>
      )}

      {/* Focus areas */}
      {focus.isLoading && <LoadingCard label="Loading focus areas…" />}
      {focusData && focusData.top_focus_areas.length > 0 && (
        <Card title="Focus area accuracy">
          <BarChart
            items={focusData.top_focus_areas.map((f: { focus_key: string; accuracy: number; domain: string }) => ({
              label: f.focus_key,
              value: f.accuracy,
              domain: f.domain,
            }))}
          />
        </Card>
      )}

      {/* Weakest areas */}
      {focusData && focusData.weakest_focus_areas.length > 0 && (
        <Card title="Needs work">
          <BarChart
            items={focusData.weakest_focus_areas.map((f: { focus_key: string; accuracy: number; domain: string }) => ({
              label: f.focus_key,
              value: f.accuracy,
              domain: f.domain,
            }))}
          />
        </Card>
      )}

      {/* Empty state */}
      {!trend.isLoading && trendData && trendData.total_attempts === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#6b7280' }}>
          <p style={{ fontSize: 16, marginBottom: 8 }}>No data yet</p>
          <p style={{ fontSize: 13 }}>Answer some questions to see your progress here.</p>
          <button
            onClick={() => navigate('/practice/grammar')}
            style={{ marginTop: 16, padding: '8px 20px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, cursor: 'pointer' }}
          >
            Start practicing
          </button>
        </div>
      )}
    </div>
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: '16px', marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 14px', fontSize: 14, fontWeight: 600, color: '#374151' }}>{title}</h3>
      {children}
    </div>
  )
}

function LoadingCard({ label }: { label: string }) {
  return (
    <div style={{ background: '#f9fafb', borderRadius: 12, padding: 20, marginBottom: 16, color: '#6b7280', fontSize: 13 }}>
      {label}
    </div>
  )
}

function ErrorCard({ label, onRetry }: { label: string; onRetry: () => void }) {
  return (
    <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 12, padding: '12px 16px', marginBottom: 16 }}>
      <p style={{ margin: 0, fontSize: 13, color: '#dc2626' }}>{label}</p>
      <button onClick={onRetry} style={{ marginTop: 6, fontSize: 12, color: '#2563eb', background: 'none', border: 'none', cursor: 'pointer' }}>
        Retry
      </button>
    </div>
  )
}
