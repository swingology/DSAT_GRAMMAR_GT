import { useSearchParams, useNavigate } from 'react-router-dom'
import { useGrammarSession } from '../hooks/useGrammarSession'
import { Header } from './grammar/Header'
import { QuestionSection } from './grammar/QuestionSection'
import { GrammarAnalysisSection } from './grammar/GrammarAnalysisSection'
import './GrammarPractice.css'

interface GrammarPracticeProps {
  onQuestionComplete?: (result: any) => void
}

export function GrammarPractice({}: GrammarPracticeProps) {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const limit = Math.min(50, Math.max(1, parseInt(params.get('limit') ?? '10', 10) || 10))
  const grammar = useGrammarSession({ limit })

  if (grammar.isLoading) {
    return (
      <div className="grammar-practice">
        <div className="loading">Loading grammar question...</div>
      </div>
    )
  }

  if (grammar.error) {
    return (
      <div className="grammar-practice">
        <div className="error">Error: {grammar.error}</div>
      </div>
    )
  }

  if (!grammar.question) {
    return (
      <div className="grammar-practice">
        <div className="error">No question available</div>
      </div>
    )
  }

  const isDone = !grammar.hasNext && grammar.feedbackVisible

  if (isDone) {
    return (
      <div className="grammar-practice">
        <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✓</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>Session Complete</h2>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
            You answered all {limit} questions.
          </p>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '0.625rem 1.5rem',
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: '0.75rem',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="grammar-practice">
      <Header
        question={grammar.question}
        currentIndex={grammar.currentIndex}
        totalQuestions={grammar.totalQuestions}
        totalAvailable={grammar.totalAvailable}
      />

      <QuestionSection
        grammar={grammar}
      />

      <GrammarAnalysisSection
        grammar={grammar}
      />
    </div>
  )
}
