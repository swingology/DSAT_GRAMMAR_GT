import React from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { PracticeTestPage } from '../PracticeTestPage'

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
}))

vi.mock('../../components/dashboard/TestModeTab', () => ({
  TestModeTab: ({ questionCount, durationSeconds }: { questionCount: number; durationSeconds: number }) => (
    <div data-testid="test-mode-props">
      {questionCount} questions / {durationSeconds} seconds
    </div>
  ),
}))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/test" element={<PracticeTestPage />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('PracticeTestPage', () => {
  it('caps requested question count at 27 and fixes duration at 32 minutes', () => {
    renderAt('/test?questions=33&seconds=600')

    expect(screen.getByText('27 questions · 32 min')).toBeInTheDocument()
    expect(screen.getByTestId('test-mode-props')).toHaveTextContent('27 questions / 1920 seconds')
  })
})
