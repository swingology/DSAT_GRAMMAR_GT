import { findActiveKeyForToken } from '../../utils/sentenceTokenizer'
import { useGrammarSession } from '../../hooks/useGrammarSession'

type GrammarSessionReturn = ReturnType<typeof useGrammarSession>

interface QuestionSectionProps {
  grammar: GrammarSessionReturn
}

export function QuestionSection({ grammar }: QuestionSectionProps) {
  if (!grammar.question) return null

  const options = grammar.renderOptions()
  const feedback = grammar.renderFeedback()
  const questionPrompt = grammar.renderQuestionPrompt()
  const tokens = grammar.passageTokens
  type RenderedOption = ReturnType<typeof grammar.renderOptions>[number]
  const selectedOption = options.find((o: RenderedOption) => o.isSelected)

  return (
    <div className="question-section">
      <div className="question-header">
        <h2>Select the best answer</h2>
      </div>

      {/* Tokenized sentence with color-coordinated grammar highlighting */}
      <div className="sentence-box">
        {tokens.map((token, i) => {
          const matchingKey = findActiveKeyForToken(
            token.tags,
            grammar.activeKeys,
            grammar.allKeys
          )

          if (token.isBlank) {
            // Determine fill state after answering
            let blankClass = 'blank'
            let blankText = '________'
            if (grammar.feedbackVisible && selectedOption) {
              blankText = selectedOption.text
              blankClass += selectedOption.isCorrect ? ' filled-correct' : ' filled-wrong'
            }

            const blankStyle: React.CSSProperties = matchingKey
              ? {
                  boxShadow: `0 0 0 3px ${matchingKey.lightBg}`,
                  borderColor: matchingKey.color,
                }
              : {}

            return (
              <span key={i} className={blankClass} style={blankStyle}>
                {blankText}
              </span>
            )
          }

          // Whitespace — render as-is
          if (/^\s+$/.test(token.text)) {
            return <span key={i}>{token.text}</span>
          }

          // Regular token with optional highlighting
          const tokenStyle: React.CSSProperties =
            matchingKey && token.tags.length > 0
              ? {
                  backgroundColor: matchingKey.lightBg,
                  borderBottom: `2.5px solid ${matchingKey.color}`,
                  padding: '1px 3px',
                  borderRadius: '2px',
                }
              : {}

          return (
            <span key={i} className="token" style={tokenStyle}>
              {token.text}
            </span>
          )
        })}
      </div>

      {questionPrompt && <div className="question-prompt">{questionPrompt}</div>}

      {/* Answer Options */}
      <div className="options">
        {options.map((option: RenderedOption) => (
          <button
            key={option.id}
            className={`option-btn ${option.isSelected ? 'selected' : ''} ${
              option.isCorrect ? 'correct' : ''
            } ${option.isIncorrect ? 'incorrect' : ''}`}
            onClick={() => grammar.selectAnswer(option.id)}
            disabled={grammar.feedbackVisible}
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
