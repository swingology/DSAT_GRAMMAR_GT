import { useState, useEffect } from 'react'

export interface DiagnosticTimerState {
  remaining: number
  isOvertime: boolean
  overtimeSeconds: number
  formatted: string
}

function formatDuration(seconds: number): string {
  const safeSeconds = Math.max(0, seconds)
  const m = Math.floor(safeSeconds / 60)
  const s = safeSeconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

export function useDiagnosticTimer(timeLimitSeconds: number): DiagnosticTimerState {
  const [remaining, setRemaining] = useState(timeLimitSeconds)

  useEffect(() => {
    setRemaining(timeLimitSeconds)
  }, [timeLimitSeconds])

  useEffect(() => {
    const timer = setTimeout(() => setRemaining((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [remaining])

  const isOvertime = remaining <= 0
  const overtimeSeconds = isOvertime ? Math.abs(remaining) : 0
  const formatted = isOvertime
    ? `+${formatDuration(overtimeSeconds)}`
    : formatDuration(remaining)

  return { remaining, isOvertime, overtimeSeconds, formatted }
}
