import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useDiagnosticTimer } from '../useDiagnosticTimer'

describe('useDiagnosticTimer', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('counts down while time remains', () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useDiagnosticTimer(3))

    expect(result.current.formatted).toBe('0:03')
    expect(result.current.isOvertime).toBe(false)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.formatted).toBe('0:02')
    expect(result.current.isOvertime).toBe(false)
  })

  it('keeps running as an overtime stopwatch after zero', () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useDiagnosticTimer(1))

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.formatted).toBe('+0:00')
    expect(result.current.isOvertime).toBe(true)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.formatted).toBe('+0:01')

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.formatted).toBe('+0:02')
    expect(result.current.overtimeSeconds).toBe(2)
  })
})
