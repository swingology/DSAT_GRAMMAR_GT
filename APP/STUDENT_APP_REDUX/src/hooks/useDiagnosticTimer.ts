import { useState, useEffect, useRef } from 'react'

export interface DiagnosticTimerState {
  remaining: number
  isExpired: boolean
  formatted: string
}

export function useDiagnosticTimer(
  timeLimitSeconds: number,
  onExpire: () => void,
): DiagnosticTimerState {
  const [remaining, setRemaining] = useState(timeLimitSeconds)
  const expiredRef = useRef(false)
  const onExpireRef = useRef(onExpire)
  onExpireRef.current = onExpire

  useEffect(() => {
    expiredRef.current = false
    setRemaining(timeLimitSeconds)
  }, [timeLimitSeconds])

  useEffect(() => {
    if (remaining <= 0) {
      if (!expiredRef.current) {
        expiredRef.current = true
        onExpireRef.current()
      }
      return
    }
    const timer = setTimeout(() => setRemaining((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [remaining])

  const m = Math.floor(remaining / 60)
  const s = remaining % 60
  const formatted = `${m}:${String(s).padStart(2, '0')}`

  return { remaining, isExpired: remaining <= 0, formatted }
}
