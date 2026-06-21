import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useRecommendations, useSubmitAnswer } from '../../hooks/useDashboardData'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { WeaknessTarget } from '../../types'

const USER_TOKEN = (import.meta as any).env.VITE_TEST_USER_TOKEN || ''

type DiagnosticState = 'idle' | 'running' | 'done'

interface DiagnosticQuestion {
  id: string
  current_question_text: string
  options: Array<{ label: string; text: string; distractor_type_key?: string }>
  grammar_focus_key?: string
  reading_focus_key?: string
  domain: string
  explanation_short?: string
  // correct_answer revealed after submit via is_correct response
  _selectedLabel?: string
  _isCorrect?: boolean
}

function DiagnosticQuestionCard({
  question,
  onAnswer,
  sessionId,
}: {
  question: DiagnosticQuestion
  onAnswer: (label: string, isCorrect: boolean) => void
  sessionId: string | null
}) {
  const [selected, setSelected] = useState<string | null>(null)
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null)
  const submitAnswer = useSubmitAnswer()

  function choose(label: string) {
    if (selected) return
    setSelected(label)
    const selectedOpt = question.options.find((o) => o.label === label)
    const trapType = selectedOpt?.distractor_type_key ?? undefined
    if (sessionId) {
      api.diagnosticSubmit(sessionId, {
        user_token: USER_TOKEN,
        question_id: question.id,
        selected_option_label: label,
        missed_grammar_focus_key: question.grammar_focus_key,
        missed_reading_focus_key: question.reading_focus_key,
        missed_syntactic_trap_key: trapType,
      }).then((res) => {
        setIsCorrect(res.is_correct)
        onAnswer(label, res.is_correct)
      }).catch(() => onAnswer(label, false))
    } else {
      submitAnswer.mutate(
        {
          question_id: question.id,
          selected_option_label: label,
          missed_grammar_focus_key: question.grammar_focus_key,
          missed_reading_focus_key: question.reading_focus_key,
          missed_syntactic_trap_key: trapType,
        },
        {
          onSuccess: (res) => {
            setIsCorrect(res.is_correct)
            onAnswer(label, res.is_correct)
          },
          onError: () => {
            // Optimistic: treat as answered, correctness unknown
            onAnswer(label, false)
          },
        }
      )
    }
  }

  const focusKey = (question.grammar_focus_key || question.reading_focus_key || '').replace(/_/g, ' ')

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <p className="text-sm text-gray-500 mb-3 uppercase tracking-wide font-medium">
        {question.domain}{focusKey ? ` · ${focusKey}` : ''}
      </p>
      <p className="text-gray-800 mb-5 leading-relaxed">{question.current_question_text}</p>
      <div className="space-y-2">
        {question.options.map((opt) => {
          const isSelected = selected === opt.label
          const showCorrect = isCorrect === true && isSelected
          const showWrong = isCorrect === false && isSelected
          return (
            <button
              key={opt.label}
              onClick={() => choose(opt.label)}
              disabled={!!selected}
              className={[
                'w-full text-left p-3 rounded-lg border text-sm transition-all',
                !selected ? 'hover:bg-blue-50 hover:border-blue-300 border-gray-200' : '',
                showCorrect ? 'bg-emerald-50 border-emerald-400 text-emerald-800' : '',
                showWrong ? 'bg-red-50 border-red-400 text-red-800' : '',
                isSelected && isCorrect === null ? 'bg-blue-50 border-blue-400' : '',
                !isSelected && !!selected ? 'opacity-50 border-gray-200' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <span className="font-mono text-gray-400 mr-2">{opt.label}.</span>
              {opt.text}
            </button>
          )
        })}
      </div>
      {selected && question.explanation_short && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-500 font-medium mb-1">Explanation</p>
          <p className="text-sm text-gray-700">{question.explanation_short}</p>
        </div>
      )}
    </div>
  )
}

function DiagnosticRunner({
  targets,
  onDone,
  sessionId,
}: {
  targets: WeaknessTarget[]
  onDone: (results: { correct: number; total: number }) => void
  sessionId: string | null
}) {
  const [qIndex, setQIndex] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)

  const currentTarget = targets[Math.min(qIndex, targets.length - 1)]
  const totalQuestions = Math.min(targets.length, 8)

  const { data: qData, isLoading } = useQuery({
    queryKey: ['diagnostic-q', currentTarget?.focus_key, qIndex],
    queryFn: () =>
      api.getQuestions({
        grammar_focus_key: currentTarget.domain === 'grammar' ? currentTarget.focus_key : undefined,
        reading_focus_key: currentTarget.domain === 'reading' ? currentTarget.focus_key : undefined,
        limit: 1,
      }),
    enabled: !!currentTarget,
  })

  const question: DiagnosticQuestion | null = qData?.questions?.[0] ?? null

  function handleAnswer(_label: string, isCorrect: boolean) {
    const newCorrect = correctCount + (isCorrect ? 1 : 0)
    setCorrectCount(newCorrect)

    setTimeout(() => {
      if (qIndex + 1 >= totalQuestions) {
        onDone({ correct: newCorrect, total: totalQuestions })
      } else {
        setQIndex(qIndex + 1)
      }
    }, 1500)
  }

  if (isLoading || !question) {
    return (
      <div className="space-y-3">
        <div className="h-8 bg-gray-100 rounded animate-pulse w-1/3" />
        <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-gray-500">
          Question {qIndex + 1} of {totalQuestions}
        </span>
        <div className="flex gap-1">
          {Array.from({ length: totalQuestions }).map((_, i) => (
            <div
              key={i}
              className={`h-1.5 w-6 rounded-full ${
                i < qIndex ? 'bg-blue-500' : i === qIndex ? 'bg-blue-300' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>
      <DiagnosticQuestionCard question={question} onAnswer={handleAnswer} sessionId={sessionId} />
    </div>
  )
}

export function DiagnosticTab() {
  const [state, setState] = useState<DiagnosticState>('idle')
  const [results, setResults] = useState<{ correct: number; total: number } | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const { data: recs, isLoading } = useRecommendations()
  const navigate = useNavigate()

  const targets = recs?.top_targets ?? []

  if (isLoading) {
    return <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
  }

  if (state === 'done' && results) {
    const pct = Math.round((results.correct / results.total) * 100)
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="bg-white border border-gray-200 rounded-xl p-8 text-center"
      >
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.35, type: 'spring', bounce: 0.4 }}
          className="text-5xl font-bold text-blue-600 mb-2"
        >
          {pct}%
        </motion.div>
        <p className="text-gray-600 text-lg mb-1">
          {results.correct} / {results.total} correct
        </p>
        <p className="text-gray-400 text-sm mb-6">Diagnostic complete — weak concept profile updated</p>
        <div className="flex gap-3 justify-center flex-wrap">
          <button
            onClick={() => setState('idle')}
            className="px-5 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition"
          >
            Try again
          </button>
          <button
            onClick={() => navigate('/practice/grammar')}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition"
          >
            Practice grammar
          </button>
          <button
            onClick={() => navigate('/diagnostic/history')}
            className="px-5 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition"
          >
            View History
          </button>
        </div>
      </motion.div>
    )
  }

  if (state === 'running') {
    return (
      <DiagnosticRunner
        targets={targets}
        sessionId={sessionId}
        onDone={async (r) => {
          if (sessionId) {
            await api.diagnosticComplete(sessionId, { user_token: USER_TOKEN }).catch(() => {})
          }
          setResults(r)
          setState('done')
        }}
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <h3 className="font-semibold text-blue-900 mb-1">Adaptive Diagnostic</h3>
        <p className="text-blue-700 text-sm">
          {targets.length > 0
            ? `${Math.min(targets.length, 8)} questions targeting your top ${targets.length} weak areas`
            : 'Answer questions to build your weakness profile'}
        </p>
      </div>
      {targets.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-medium mb-3">
            Top targets for this diagnostic
          </p>
          <ul className="space-y-1">
            {targets.slice(0, 5).map((t) => (
              <li key={`${t.domain}-${t.focus_key}`} className="flex items-center gap-2 text-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                <span className="text-gray-700">{t.focus_key.replace(/_/g, ' ')}</span>
                <span className="text-gray-400 text-xs">({t.domain})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <button
        onClick={async () => {
          const res = await api.diagnosticStart({ user_token: USER_TOKEN, diagnostic_type: 'adaptive' }).catch(() => null)
          setSessionId(res?.session_id ?? null)
          setState('running')
        }}
        disabled={targets.length === 0}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition"
      >
        Start Diagnostic
      </button>
    </div>
  )
}
