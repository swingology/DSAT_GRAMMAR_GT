import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PracticeCard } from '../dashboard/PracticeCard'

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

describe('PracticeCard', () => {
  it('renders the card header', () => {
    wrap(<PracticeCard />)
    expect(screen.getByText('Practice')).toBeInTheDocument()
    expect(screen.getByText('Grammar, concept drill, or mixed')).toBeInTheDocument()
  })

  it('sub-options are hidden by default', () => {
    wrap(<PracticeCard />)
    expect(screen.queryByText('Grammar Practice')).not.toBeInTheDocument()
    expect(screen.queryByText('Pick a Concept')).not.toBeInTheDocument()
    expect(screen.queryByText('Mixed Practice')).not.toBeInTheDocument()
  })

  it('expands sub-options on click', () => {
    wrap(<PracticeCard />)
    fireEvent.click(screen.getByText('Grammar, concept drill, or mixed'))
    expect(screen.getByText('Grammar Practice')).toBeInTheDocument()
    expect(screen.getByText('Pick a Concept')).toBeInTheDocument()
    expect(screen.getByText('Mixed Practice')).toBeInTheDocument()
  })

  it('collapses sub-options on second click', () => {
    wrap(<PracticeCard />)
    fireEvent.click(screen.getByText('Grammar, concept drill, or mixed'))
    expect(screen.getByText('Grammar Practice')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Grammar, concept drill, or mixed'))
    expect(screen.queryByText('Grammar Practice')).not.toBeInTheDocument()
  })

  it('navigates to grammar practice route', () => {
    wrap(<PracticeCard />)
    fireEvent.click(screen.getByText('Grammar, concept drill, or mixed'))
    fireEvent.click(screen.getByText('Grammar Practice'))
    expect(mockNavigate).toHaveBeenCalledWith('/practice/grammar')
  })

  it('navigates to concept selector route', () => {
    wrap(<PracticeCard />)
    fireEvent.click(screen.getByText('Grammar, concept drill, or mixed'))
    fireEvent.click(screen.getByText('Pick a Concept'))
    expect(mockNavigate).toHaveBeenCalledWith('/practice/concepts')
  })

  it('navigates to mixed practice route', () => {
    wrap(<PracticeCard />)
    fireEvent.click(screen.getByText('Grammar, concept drill, or mixed'))
    fireEvent.click(screen.getByText('Mixed Practice'))
    expect(mockNavigate).toHaveBeenCalledWith('/practice/mixed')
  })

  it('shows descriptions for each sub-option', () => {
    wrap(<PracticeCard />)
    fireEvent.click(screen.getByText('Grammar, concept drill, or mixed'))
    expect(screen.getByText(/sentence-level grammar questions/i)).toBeInTheDocument()
    expect(screen.getByText(/specific grammar or reading concept/i)).toBeInTheDocument()
    expect(screen.getByText(/random questions across all concepts/i)).toBeInTheDocument()
  })
})
