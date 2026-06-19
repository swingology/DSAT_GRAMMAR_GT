import { useGrammarSession } from '../../hooks/useGrammarSession'

type GrammarSessionReturn = ReturnType<typeof useGrammarSession>

interface GrammarAnalysisSectionProps {
  grammar: GrammarSessionReturn
}

export function GrammarAnalysisSection({ grammar }: GrammarAnalysisSectionProps) {
  if (!grammar.question) return null

  const trapSummary = grammar.renderTrapSummary()
  const groupedKeys = grammar.renderGrammarKeys()

  return (
    <div className="grammar-analysis-section">
      <div className="section-header">
        <div>
          <h2>Grammar Analysis</h2>
          <p>Identify the grammar concepts at play</p>
        </div>
        <div className="section-actions">
          <button
            className="btn-action find-btn"
            onClick={() => grammar.findTraps()}
          >
            Find Traps
          </button>
          <button
            className="btn-action clear-btn"
            onClick={() => grammar.clearKeys()}
          >
            Clear Keys
          </button>
        </div>
      </div>

      {trapSummary && (
        <div className="trap-summary">
          <div className="trap-summary-title">Detected Trap Profile</div>
          <div className="trap-summary-grid">
            <div className="trap-summary-item">
              <div className="trap-summary-label">Grammar Role</div>
              <div className="trap-summary-value">{trapSummary.grammarRole}</div>
            </div>
            <div className="trap-summary-item">
              <div className="trap-summary-label">Grammar Focus</div>
              <div className="trap-summary-value">{trapSummary.grammarFocus}</div>
            </div>
            <div className="trap-summary-item">
              <div className="trap-summary-label">Syntactic Trap</div>
              <div className="trap-summary-value">
                {trapSummary.trapKeys.join(', ')}
              </div>
            </div>
            <div className="trap-summary-item">
              <div className="trap-summary-label">Trap Intensity</div>
              <div className="trap-summary-value">{trapSummary.trapIntensity}</div>
            </div>
          </div>
          <div className="trap-mechanism">
            <strong>Why the trap works:</strong> {trapSummary.trapMechanism}
          </div>
        </div>
      )}

      <div className="grammar-keys">
        {groupedKeys.map((group) => (
          <div key={group.group} className="key-group">
            <div className="key-group-title">{group.group}</div>
            <div className="key-group-buttons">
              {group.keys.map((key) => (
                <button
                  key={key.id}
                  className={`key-btn ${
                    grammar.activeKeys.has(key.id) ? 'active' : ''
                  }`}
                  onClick={() => grammar.toggleKey(key.id)}
                  title={key.rule}
                  style={{
                    backgroundColor: grammar.activeKeys.has(key.id)
                      ? key.color
                      : key.lightBg,
                    color: grammar.activeKeys.has(key.id) ? 'white' : key.color,
                  }}
                >
                  {key.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {grammar.activeKeys.size > 0 && (
        <div className="active-keys-explanation">
          <h3>Active Grammar Keys</h3>
          {grammar.findActiveKey().map((key) => (
            <div key={key.id} className="key-explanation">
              <h4>{key.label}</h4>
              <p>{key.rule}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
