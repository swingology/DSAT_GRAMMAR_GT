import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { TestModeTab } from '../dashboard/TestModeTab'
import { api } from '../../api/client'

vi.mock('../../api/client', () => ({
  api: {
    getQuestions: vi.fn(),
    submitAnswer: vi.fn(),
    module1Complete: vi.fn(),
    module2Blueprint: vi.fn(),
  },
}))

vi.mock('../../hooks/useDashboardData', () => ({
  useSubmitAnswer: () => ({ mutate: vi.fn() }),
}))

const MOCK_QUESTION = {
  id: 'q-1',
  current_question_text: 'The researcher [BLANK] findings.',
  options: [
    { label: 'A', text: 'share' },
    { label: 'B', text: 'shares' },
    { label: 'C', text: 'shared' },
    { label: 'D', text: 'is sharing' },
  ],
}

const ROUTING_HIGHER = {
  test_session_id: 'sess-123',
  module_2_difficulty: 'higher',
  routing_rationale: 'Accuracy 75% ≥ 70% threshold — routing to higher difficulty',
  module_1_accuracy: 0.75,
}

const ROUTING_LOWER = {
  test_session_id: 'sess-456',
  module_2_difficulty: 'lower',
  routing_rationale: 'Accuracy 50% < 70% threshold — routing to lower difficulty',
  module_1_accuracy: 0.50,
}

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('TestModeTab — Adaptive routing', () => {
  beforeEach(() => { vi.clearAllMocks() })
  afterEach(() => { vi.useRealTimers() })

  it('shows adaptive test label when adaptive=true', () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ questions: [], items: [] })
    wrap(<TestModeTab adaptive={true} userToken="test-token" />)
    expect(screen.getByText(/adaptive practice test/i)).toBeInTheDocument()
  })

  it('shows standard label when adaptive=false', () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ questions: [], items: [] })
    wrap(<TestModeTab adaptive={false} />)
    expect(screen.getByText(/timed practice module/i)).toBeInTheDocument()
  })

  it('shows routing screen with higher difficulty after module 1', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ questions: [MOCK_QUESTION], items: [MOCK_QUESTION] })
    vi.mocked(api.module1Complete).mockResolvedValue(ROUTING_HIGHER)

    wrap(<TestModeTab adaptive={true} questionCount={1} userToken="test-token" />)

    fireEvent.click(screen.getByText(/start adaptive test/i))

    await waitFor(() => {
      expect(screen.getByText(/the researcher/i)).toBeInTheDocument()
    })

    // Submit the test
    fireEvent.click(screen.getByText('Submit'))

    await waitFor(() => {
      expect(screen.getByText(/module 1 complete/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/↑ Advanced Module 2/i)).toBeInTheDocument()
  })

  it('shows routing screen with lower difficulty after poor performance', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ questions: [MOCK_QUESTION], items: [MOCK_QUESTION] })
    vi.mocked(api.module1Complete).mockResolvedValue(ROUTING_LOWER)

    wrap(<TestModeTab adaptive={true} questionCount={1} userToken="test-token" />)
    fireEvent.click(screen.getByText(/start adaptive test/i))

    await waitFor(() => {
      expect(screen.getByText(/the researcher/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Submit'))

    await waitFor(() => {
      expect(screen.getByText(/↓ Foundation Module 2/i)).toBeInTheDocument()
    })
  })

  it('shows review module 1 and start module 2 buttons on routing screen', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ questions: [MOCK_QUESTION], items: [MOCK_QUESTION] })
    vi.mocked(api.module1Complete).mockResolvedValue(ROUTING_HIGHER)

    wrap(<TestModeTab adaptive={true} questionCount={1} userToken="test-token" />)
    fireEvent.click(screen.getByText(/start adaptive test/i))

    await waitFor(() => screen.getByText(/the researcher/i))
    fireEvent.click(screen.getByText('Submit'))

    await waitFor(() => screen.getByText(/module 1 complete/i))

    expect(screen.getByText(/review module 1/i)).toBeInTheDocument()
    expect(screen.getByText(/start module 2/i)).toBeInTheDocument()
  })

  it('falls through to done when adaptive=false', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ questions: [MOCK_QUESTION], items: [MOCK_QUESTION] })

    wrap(<TestModeTab adaptive={false} questionCount={1} userToken="test-token" />)
    fireEvent.click(screen.getByText(/start test/i))

    await waitFor(() => screen.getByText(/the researcher/i))
    fireEvent.click(screen.getByText('Submit'))

    await waitFor(() => {
      // Should go to done (TestResults) not routing
      expect(screen.queryByText(/module 1 complete/i)).not.toBeInTheDocument()
    })
    // module1Complete should not have been called
    expect(vi.mocked(api.module1Complete)).not.toHaveBeenCalled()
  })

  it('auto-submits when the practice test timer expires', async () => {
    vi.mocked(api.getQuestions).mockResolvedValue({ questions: [MOCK_QUESTION], items: [MOCK_QUESTION] })
    vi.mocked(api.module1Complete).mockResolvedValue(ROUTING_LOWER)

    wrap(<TestModeTab adaptive={true} questionCount={1} durationSeconds={1} userToken="test-token" />)
    fireEvent.click(screen.getByText(/start adaptive test/i))

    await waitFor(() => screen.getByText(/the researcher/i))

    await waitFor(() => {
      expect(vi.mocked(api.module1Complete)).toHaveBeenCalledWith(
        expect.objectContaining({
          user_token: 'test-token',
          module_1_duration_seconds: expect.any(Number),
        })
      )
    }, { timeout: 2500 })
  }, 4000)
})
