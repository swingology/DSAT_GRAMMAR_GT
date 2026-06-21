import type { GrammarQuestion } from '../../types/grammar'

interface HeaderProps {
  question: GrammarQuestion
  currentIndex?: number
  totalQuestions?: number
  totalAvailable?: number
}

export function Header({ question, currentIndex, totalQuestions, totalAvailable }: HeaderProps) {
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
        {totalQuestions != null && totalQuestions > 0 && (
          <div className="progress-info">
            <span className="label">Progress:</span>
            <span className="value">
              {(currentIndex ?? 0) + 1} / {totalQuestions}
              {totalAvailable != null && totalAvailable > totalQuestions && (
                <span className="total-available"> ({totalAvailable} total)</span>
              )}
            </span>
          </div>
        )}
        {question.source_exam && (
          <div className="progress-info">
            <span className="label">Source:</span>
            <span className="value">{question.source_exam}</span>
          </div>
        )}
        {question.source_question_number && (
          <div className="progress-info">
            <span className="label">Q#:</span>
            <span className="value">{question.source_question_number}</span>
          </div>
        )}
      </div>
    </div>
  )
}
