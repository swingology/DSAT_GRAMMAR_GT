import { useGrammarSession } from '../hooks/useGrammarSession'
import { Header } from './grammar/Header'
import { QuestionSection } from './grammar/QuestionSection'
import { GrammarAnalysisSection } from './grammar/GrammarAnalysisSection'
import './GrammarPractice.css'

interface GrammarPracticeProps {
  onQuestionComplete?: (result: any) => void
}

export function GrammarPractice({}: GrammarPracticeProps) {
  const grammar = useGrammarSession()

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

  return (
    <div className="grammar-practice">
      <Header question={grammar.question} />

      <QuestionSection
        grammar={grammar}
      />

      <GrammarAnalysisSection
        grammar={grammar}
      />
    </div>
  )
}
