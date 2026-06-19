import type { GrammarQuestion } from '../../types/grammar'

interface HeaderProps {
  question: GrammarQuestion
}

export function Header({ question }: HeaderProps) {
  return (
    <div className="grammar-header">
      <div className="header-left">
        <div className="header-icon">✦</div>
        <div className="header-text">
          <h1>SAT Grammar Practice</h1>
          <p>Standard English Conventions</p>
        </div>
      </div>

      <div className="progress-container">
        {question.source_exam && (
          <div className="progress-info">
            <span className="label">Source:</span>
            <span className="value">{question.source_exam}</span>
          </div>
        )}
        {question.source_question_number && (
          <div className="progress-info">
            <span className="label">Question:</span>
            <span className="value">{question.source_question_number}</span>
          </div>
        )}
      </div>
    </div>
  )
}
