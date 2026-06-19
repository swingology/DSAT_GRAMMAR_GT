import { useGrammarSession } from '../../hooks/useGrammarSession'

type GrammarSessionReturn = ReturnType<typeof useGrammarSession>

interface QuestionSectionProps {
  grammar: GrammarSessionReturn
}

export function QuestionSection({ grammar }: QuestionSectionProps) {
  if (!grammar.question) return null

  const options = grammar.renderOptions()
  const feedback = grammar.renderFeedback()
  const sentenceText = grammar.renderSentence()

  return (
    <div className="question-section">
      <div className="question-header">
        <h2>Select the best answer</h2>
      </div>

      <div className="sentence-box">{sentenceText}</div>

      <div className="options">
        {options.map((option) => (
          <button
            key={option.id}
            className={`option-btn ${
              option.isSelected ? 'selected' : ''
            } ${
              option.isCorrect ? 'correct' : ''
            } ${
              option.isIncorrect ? 'incorrect' : ''
            }`}
            onClick={() => grammar.selectAnswer(option.id)}
            disabled={grammar.feedbackVisible && !option.correct}
          >
            <span className="option-label">{option.id}</span>
            <span className="option-text">{option.text}</span>
          </button>
        ))}
      </div>

      {grammar.feedbackVisible && feedback && (
        <div className={`feedback ${feedback.isCorrect ? 'correct' : 'incorrect'}`}>
          <div className="feedback-title">{feedback.title}</div>
          <div className="feedback-text">{feedback.explanation}</div>
          <div className="feedback-rule">
            <strong>Rule:</strong> {feedback.primaryRule}
          </div>
          {feedback.failureMode && (
            <div className="failure-mode">
              <strong>Why this is tempting:</strong> {feedback.failureMode}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
