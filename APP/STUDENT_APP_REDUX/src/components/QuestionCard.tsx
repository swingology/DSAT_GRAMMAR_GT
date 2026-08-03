import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSubmitAnswer } from '../hooks/useDashboardData'
import type { SubmitSourceType } from '../api/client'
import { StimulusAssets } from './StimulusAssets'
import { QuestionIdBadge } from './QuestionIdBadge'
import type { StimulusAsset } from '../types'

export interface Question {
  id: string
  current_question_text: string
  current_passage_text?: string | null
  options: Array<{ label: string; text: string }>
  explanation_short?: string
  grammar_focus_key?: string
  reading_focus_key?: string
  domain?: string
  stimulus_assets?: StimulusAsset[]
}

export function QuestionCard({
  question,
  onNext,
  sourceType,
}: {
  question: Question
  onNext: () => void
  sourceType: SubmitSourceType
}) {
  const [selected, setSelected] = useState<string | null>(null)
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null)
  const submitAnswer = useSubmitAnswer()

  function choose(label: string) {
    if (selected) return
    setSelected(label)
    submitAnswer.mutate(
      {
        question_id: question.id,
        selected_option_label: label,
        source_type: sourceType,
        missed_grammar_focus_key: question.grammar_focus_key,
        missed_reading_focus_key: question.reading_focus_key,
      },
      { onSuccess: (res) => setIsCorrect(res.is_correct) }
    )
  }

  return (
    <motion.div
      key={question.id}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="bg-white border border-gray-200 rounded-xl p-6"
    >
      <QuestionIdBadge id={question.id} className="mb-3" />
      {question.domain && (
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{question.domain}</p>
      )}
      {(question.grammar_focus_key || question.reading_focus_key) && (
        <p className="text-xs text-blue-500 font-medium mb-3">
          {(question.grammar_focus_key || question.reading_focus_key || '').replace(/_/g, ' ')}
        </p>
      )}
      {question.current_passage_text && (
        <div className="text-sm text-gray-600 leading-relaxed bg-gray-50 rounded-lg p-4 mb-4 border border-gray-100 whitespace-pre-wrap">
          {question.current_passage_text}
        </div>
      )}
      <StimulusAssets assets={question.stimulus_assets} />
      <p className="text-gray-800 leading-relaxed mb-5">{question.current_question_text}</p>

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

      {selected && (
        <button
          onClick={onNext}
          className="mt-4 w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl text-sm transition"
        >
          Next Question →
        </button>
      )}
    </motion.div>
  )
}
