import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useRecommendations, useSubmitAnswer } from '../../hooks/useDashboardData'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { WeaknessTarget } from '../../types'

type DiagnosticState = 'idle' | 'running' | 'done'

interface DiagnosticQuestion {
  id: string
  text: string
  options: Array<{ id: string; text: string }>
  focus_key: string
  domain: string
  correct_answer_id?: string
  explanation?: string
}

function DiagnosticQuestion({
  question,
  onAnswer,
}: {
  question: DiagnosticQuestion
  onAnswer: (optionId: string) => void
}) {
  const [selected, setSelected] = useState<string | null>(null)

  function choose(id: string) {
    if (selected) return
    setSelected(id)
    onAnswer(id)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <p className="text-sm text-gray-500 mb-3 uppercase tracking-wide font-medium">
        {question.domain} · {question.focus_key.replace(/_/g, ' ')}
      </p>
      <p className="text-gray-800 mb-5 leading-relaxed">{question.text}</p>
      <div className="space-y-2">
        {question.options.map((opt) => {
          const isSelected = selected === opt.id
          const isCorrect = selected && opt.id === question.correct_answer_id
          const isWrong = isSelected && opt.id !== question.correct_answer_id
          return (
            <button
              key={opt.id}
              onClick={() => choose(opt.id)}
              disabled={!!selected}
              className={[
                'w-full text-left p-3 rounded-lg border text-sm transition-all',
                !selected ? 'hover:bg-blue-50 hover:border-blue-300 border-gray-200' : '',
                isCorrect ? 'bg-emerald-50 border-emerald-400 text-emerald-800' : '',
                isWrong ? 'bg-red-50 border-red-400 text-red-800' : '',
                isSelected && !isWrong && !isCorrect ? 'bg-blue-50 border-blue-400' : '',
                !isSelected && selected ? 'opacity-50 border-gray-200' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              {opt.text}
            </button>
          )
        })}
      </div>
      {selected && question.explanation && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-500 font-medium mb-1">Explanation</p>
          <p className="text-sm text-gray-700">{question.explanation}</p>
        </div>
      )}
    </div>
  )
}

function DiagnosticRunner({
  targets,
  onDone,
}: {
  targets: WeaknessTarget[]
  onDone: (results: { correct: number; total: number }) => void
}) {
  const [qIndex, setQIndex] = useState(0)
  const [answers, setAnswers] = useState<string[]>([])
  const submitAnswer = useSubmitAnswer()

  const currentTarget = targets[Math.min(qIndex, targets.length - 1)]

  const { data: qData, isLoading } = useQuery({
    queryKey: ['diagnostic-q', currentTarget?.focus_key, qIndex],
    queryFn: () =>
      api.getQuestions({
        focus_key: currentTarget.focus_key,
        domain: currentTarget.domain,
        limit: 1,
        mode: 'diagnostic',
      }),
    enabled: !!currentTarget,
  })

  const question: DiagnosticQuestion | null = qData?.questions?.[0] ?? null
  const totalQuestions = Math.min(targets.length, 8)

  function handleAnswer(optionId: string) {
    if (!question) return

    submitAnswer.mutate({
      question_id: question.id,
      answer_id: optionId,
      mode: 'diagnostic',
    })

    const newAnswers = [...answers, optionId]
    setAnswers(newAnswers)

    setTimeout(() => {
      if (qIndex + 1 >= totalQuestions) {
        const correct = newAnswers.filter(
          (a, i) => a === (qData?.questions?.[i]?.correct_answer_id ?? '__none__')
        ).length
        onDone({ correct, total: totalQuestions })
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
      <DiagnosticQuestion question={question} onAnswer={handleAnswer} />
    </div>
  )
}

export function DiagnosticTab() {
  const [state, setState] = useState<DiagnosticState>('idle')
  const [results, setResults] = useState<{ correct: number; total: number } | null>(null)
  const { data: recs, isLoading } = useRecommendations()
  const navigate = useNavigate()

  const targets = recs?.top_targets ?? []

  if (isLoading) {
    return <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
  }

  if (state === 'done' && results) {
    const pct = Math.round((results.correct / results.total) * 100)
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
        <div className="text-5xl font-bold text-blue-600 mb-2">{pct}%</div>
        <p className="text-gray-600 text-lg mb-1">
          {results.correct} / {results.total} correct
        </p>
        <p className="text-gray-400 text-sm mb-6">Diagnostic complete — weak concept profile updated</p>
        <div className="flex gap-3 justify-center">
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
        </div>
      </div>
    )
  }

  if (state === 'running') {
    return (
      <DiagnosticRunner
        targets={targets}
        onDone={(r) => {
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
        onClick={() => setState('running')}
        disabled={targets.length === 0}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition"
      >
        Start Diagnostic
      </button>
    </div>
  )
}
