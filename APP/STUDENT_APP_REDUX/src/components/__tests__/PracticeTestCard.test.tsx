import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PracticeTestCard } from '../dashboard/PracticeTestCard'

const mockNavigate = vi.fn()

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...p }: any) => React.createElement(tag as string, p, children) }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function wrap(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

beforeEach(() => { vi.clearAllMocks() })

describe('PracticeTestCard', () => {
  it('renders the card header with defaults', () => {
    wrap(<PracticeTestCard />)
    expect(screen.getByText('Practice Test')).toBeInTheDocument()
    expect(screen.getByText('27 questions · 32 min')).toBeInTheDocument()
  })

  it('config options are hidden by default', () => {
    wrap(<PracticeTestCard />)
    expect(screen.queryByText('Questions')).not.toBeInTheDocument()
    expect(screen.queryByText('Time limit')).not.toBeInTheDocument()
    expect(screen.queryByText('32 min · auto-submit')).not.toBeInTheDocument()
  })

  it('expands config on click', () => {
    wrap(<PracticeTestCard />)
    fireEvent.click(screen.getByText('Practice Test'))
    expect(screen.getByText('Questions')).toBeInTheDocument()
    expect(screen.getByText('Time limit')).toBeInTheDocument()
    expect(screen.getByText('32 min · auto-submit')).toBeInTheDocument()
  })

  it('shows all question count options', () => {
    wrap(<PracticeTestCard />)
    fireEvent.click(screen.getByText('Practice Test'))
    expect(screen.getByRole('button', { name: '10' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '20' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '27' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '33' })).not.toBeInTheDocument()
  })

  it('shows fixed auto-submit time', () => {
    wrap(<PracticeTestCard />)
    fireEvent.click(screen.getByText('Practice Test'))
    expect(screen.getByText('32 min · auto-submit')).toBeInTheDocument()
  })

  it('updates subtitle when question count changes', () => {
    wrap(<PracticeTestCard />)
    fireEvent.click(screen.getByText('Practice Test'))
    fireEvent.click(screen.getByRole('button', { name: '10' }))
    expect(screen.getByText('10 questions · 32 min')).toBeInTheDocument()
  })

  it('navigates to /test with correct query params on start', () => {
    wrap(<PracticeTestCard />)
    fireEvent.click(screen.getByText('Practice Test'))
    fireEvent.click(screen.getByRole('button', { name: /start test/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/test?questions=27&seconds=1920')
  })

  it('navigates with updated params after changing config', () => {
    wrap(<PracticeTestCard />)
    fireEvent.click(screen.getByText('Practice Test'))
    fireEvent.click(screen.getByRole('button', { name: '20' }))
    fireEvent.click(screen.getByRole('button', { name: /start test/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/test?questions=20&seconds=1920')
  })
})
