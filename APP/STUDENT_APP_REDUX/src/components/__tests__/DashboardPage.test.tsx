import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from '../../pages/DashboardPage'

// Mock framer-motion to avoid animation complexity in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

// Mock all dashboard tab components
vi.mock('../../components/dashboard/WeakConceptsTab', () => ({
  WeakConceptsTab: () => <div data-testid="weak-concepts-tab">Weak Concepts</div>,
}))
vi.mock('../../components/dashboard/DiagnosticTab', () => ({
  DiagnosticTab: () => <div data-testid="diagnostic-tab">Diagnostic</div>,
}))
vi.mock('../../components/dashboard/TestModeTab', () => ({
  TestModeTab: () => <div data-testid="test-mode-tab">Test Mode</div>,
}))
vi.mock('../../components/dashboard/MissedQuestionsTab', () => ({
  MissedQuestionsTab: () => <div data-testid="missed-questions-tab">Missed Questions</div>,
}))

function renderDashboard() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('DashboardPage', () => {
  it('renders the header and all four tab buttons', () => {
    renderDashboard()
    expect(screen.getByText('DSAT Prep')).toBeInTheDocument()
    // Use getAllByText since tab label text also appears in mock tab content
    expect(screen.getAllByText('Weak Concepts').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Diagnostic').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Test Mode').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Missed').length).toBeGreaterThanOrEqual(1)
  })

  it('shows Weak Concepts tab by default', () => {
    renderDashboard()
    expect(screen.getByTestId('weak-concepts-tab')).toBeInTheDocument()
    expect(screen.queryByTestId('diagnostic-tab')).not.toBeInTheDocument()
    expect(screen.queryByTestId('test-mode-tab')).not.toBeInTheDocument()
    expect(screen.queryByTestId('missed-questions-tab')).not.toBeInTheDocument()
  })

  it('switches to Diagnostic tab on click', () => {
    renderDashboard()
    fireEvent.click(screen.getByRole('button', { name: /diagnostic/i }))
    expect(screen.getByTestId('diagnostic-tab')).toBeInTheDocument()
    expect(screen.queryByTestId('weak-concepts-tab')).not.toBeInTheDocument()
  })

  it('switches to Test Mode tab on click', () => {
    renderDashboard()
    fireEvent.click(screen.getByRole('button', { name: /test mode/i }))
    expect(screen.getByTestId('test-mode-tab')).toBeInTheDocument()
    expect(screen.queryByTestId('weak-concepts-tab')).not.toBeInTheDocument()
  })

  it('switches to Missed tab on click', () => {
    renderDashboard()
    fireEvent.click(screen.getByRole('button', { name: /missed/i }))
    expect(screen.getByTestId('missed-questions-tab')).toBeInTheDocument()
    expect(screen.queryByTestId('weak-concepts-tab')).not.toBeInTheDocument()
  })

  it('can navigate back to Weak Concepts after switching', () => {
    renderDashboard()
    fireEvent.click(screen.getByRole('button', { name: /diagnostic/i }))
    fireEvent.click(screen.getByRole('button', { name: /weak concepts/i }))
    expect(screen.getByTestId('weak-concepts-tab')).toBeInTheDocument()
    expect(screen.queryByTestId('diagnostic-tab')).not.toBeInTheDocument()
  })

  it('renders Grammar Practice nav link', () => {
    renderDashboard()
    const link = screen.getByRole('link', { name: /grammar practice/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/practice/grammar')
  })

  it('applies active styling to the selected tab button', () => {
    renderDashboard()
    const weakBtn = screen.getAllByRole('button').find((b) => b.textContent?.includes('Weak Concepts'))
    expect(weakBtn?.className).toContain('bg-blue-600')
  })

  it('active class moves to newly selected tab', () => {
    renderDashboard()
    fireEvent.click(screen.getByText('Diagnostic'))
    const diagBtn = screen.getAllByRole('button').find((b) => b.textContent?.includes('Diagnostic'))
    const weakBtn = screen.getAllByRole('button').find((b) => b.textContent?.includes('Weak Concepts'))
    expect(diagBtn?.className).toContain('bg-blue-600')
    expect(weakBtn?.className).not.toContain('bg-blue-600')
  })
})
