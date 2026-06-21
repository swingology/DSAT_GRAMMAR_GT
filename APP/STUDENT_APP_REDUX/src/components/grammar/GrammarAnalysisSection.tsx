import { useGrammarSession } from '../../hooks/useGrammarSession'

type GrammarSessionReturn = ReturnType<typeof useGrammarSession>

interface GrammarAnalysisSectionProps {
  grammar: GrammarSessionReturn
}

const GROUP_META: Record<string, { badge?: string; badgeColor?: string }> = {
  'Sentence Anatomy': {},
  'Grammar Concepts': {
    badge: '✓ annotated in this passage',
    badgeColor: '#16a34a',
  },
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
        {groupedKeys.map((group) => {
          const meta = GROUP_META[group.group] ?? {}
          const isConcepts = group.group === 'Grammar Concepts'
          return (
            <div
              key={group.group}
              className={`key-group${isConcepts ? ' key-group--concepts' : ''}`}
            >
              <div className="key-group-title">
                {group.group}
                {meta.badge && (
                  <span
                    className="key-group-badge"
                    style={{ color: meta.badgeColor }}
                  >
                    {meta.badge}
                  </span>
                )}
              </div>
              <div className="key-group-buttons">
                {group.keys.map((key) => (
                  <button
                    key={key.id}
                    className={`key-btn ${
                      grammar.activeKeys.has(key.id) ? 'active' : ''
                    }${isConcepts ? ' key-btn--concept' : ''}`}
                    onClick={() => grammar.toggleKey(key.id)}
                    title={key.rule}
                    style={{
                      backgroundColor: grammar.activeKeys.has(key.id)
                        ? key.color
                        : key.lightBg,
                      color: grammar.activeKeys.has(key.id) ? 'white' : key.color,
                      borderColor: key.color,
                    }}
                  >
                    {key.label}
                  </button>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {grammar.activeKeys.size > 0 && (
        <div className="active-keys-explanation">
          <h3>Active Grammar Keys</h3>
          {grammar.findActiveKey()
            .filter((key) => grammar.passageKeyIds.has(key.id))
            .map((key) => (
              <div
                key={key.id}
                className="key-explanation"
                style={{ borderLeftColor: key.color, backgroundColor: key.lightBg }}
              >
                <h4 style={{ color: key.color }}>{key.label}</h4>
                <p>{key.description}</p>
                <p className="key-rule"><strong style={{ color: key.color }}>SAT Rule: </strong>{key.rule}</p>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
