import { useState } from 'react'
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Eye,
  RefreshCw,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useReviewFilters, useReviewQuestions } from '../hooks/useReviewData'
import type {
  ReviewQuestionFilters,
  ReviewQuestionItem,
  ReviewSourceType,
} from '../types'

const PAGE_SIZE = 10
const SOURCE_ORDER: ReviewSourceType[] = [
  'diagnostic',
  'practice_test',
  'drill',
  'practice',
  'unknown',
]

const labelFor = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())

function ReviewCard({ item }: { item: ReviewQuestionItem }) {
  const [showPassage, setShowPassage] = useState(false)
  const [showAnswer, setShowAnswer] = useState(false)
  const hasPassage = Boolean(item.passage_text || item.paired_passage_text)

  return (
    <article className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
      <div className="mb-4 flex flex-wrap gap-2">
        {[item.domain, item.focus_key, item.difficulty, item.content_origin, ...item.source_types]
          .filter((value): value is string => Boolean(value))
          .map((value, index) => (
            <span
              key={`${value}-${index}`}
              className="rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600"
            >
              {labelFor(value)}
            </span>
          ))}
      </div>

      {hasPassage && (
        <div className="mb-4 border-y border-gray-100 py-3">
          <button
            type="button"
            onClick={() => setShowPassage(value => !value)}
            className="flex min-h-10 w-full items-center justify-between gap-3 text-left text-sm font-semibold text-gray-700"
            aria-expanded={showPassage}
          >
            <span className="flex items-center gap-2"><BookOpen size={17} /> Passage</span>
            {showPassage ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
          {showPassage && (
            <div className="space-y-3 pt-3 text-sm leading-7 text-gray-700">
              {item.passage_text && <p className="whitespace-pre-wrap">{item.passage_text}</p>}
              {item.paired_passage_text && <p className="whitespace-pre-wrap border-t border-gray-100 pt-3">{item.paired_passage_text}</p>}
            </div>
          )}
        </div>
      )}

      <p className="mb-4 text-base font-semibold leading-7 text-gray-900">{item.question_text}</p>
      <div className="space-y-2">
        {item.options.map(option => {
          const isCorrect = showAnswer && option.is_correct
          const isIncorrectSelection = showAnswer && option.label === item.user_answer && !option.is_correct
          return (
            <div
              key={option.label}
              className={`grid min-h-12 grid-cols-[2rem_1fr] items-start gap-3 rounded-md border px-3 py-3 text-sm ${
                isCorrect
                  ? 'border-emerald-400 bg-emerald-50 text-emerald-950'
                  : isIncorrectSelection
                    ? 'border-red-300 bg-red-50 text-red-900'
                    : 'border-gray-200 bg-white text-gray-700'
              }`}
            >
              <span className="font-bold">{option.label}</span>
              <span>{option.text}</span>
            </div>
          )
        })}
      </div>

      <button
        type="button"
        onClick={() => setShowAnswer(value => !value)}
        className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-md bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-700"
        aria-expanded={showAnswer}
      >
        <Eye size={17} /> {showAnswer ? 'Hide answer' : 'Show answer'}
      </button>

      {showAnswer && (
        <div className="mt-4 border-l-4 border-emerald-500 bg-emerald-50 p-4 text-sm text-emerald-950">
          <p className="font-semibold">Correct answer: {item.correct_option_label}</p>
          {item.explanation && <p className="mt-2 leading-6">{item.explanation}</p>}
        </div>
      )}
    </article>
  )
}

interface FilterSelectProps {
  label: string
  value?: string
  values: string[]
  onChange: (value: string | undefined) => void
}

function FilterSelect({ label, value, values, onChange }: FilterSelectProps) {
  if (values.length === 0) return null
  return (
    <label className="block text-xs font-semibold text-gray-600">
      {label}
      <select
        value={value ?? ''}
        onChange={event => onChange(event.target.value || undefined)}
        className="mt-1 min-h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm font-normal text-gray-800"
      >
        <option value="">All</option>
        {values.map(option => <option key={option} value={option}>{labelFor(option)}</option>)}
      </select>
    </label>
  )
}

export function ReviewMissedPage() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<ReviewQuestionFilters>({})
  const [page, setPage] = useState(1)
  const facets = useReviewFilters()
  const review = useReviewQuestions(filters, page, PAGE_SIZE)

  const updateFilter = <K extends keyof ReviewQuestionFilters>(
    key: K,
    value: ReviewQuestionFilters[K],
  ) => {
    setFilters(current => {
      const next = { ...current, [key]: value }
      if (value === undefined || (Array.isArray(value) && value.length === 0)) delete next[key]
      return next
    })
    setPage(1)
  }

  const availableSources = SOURCE_ORDER.filter(source => facets.data?.source_types.includes(source))
  const selectedOrigins = Array.isArray(filters.content_origin)
    ? filters.content_origin
    : filters.content_origin ? [filters.content_origin] : []

  const toggleOrigin = (origin: string) => {
    const next = selectedOrigins.includes(origin)
      ? selectedOrigins.filter(value => value !== origin)
      : [...selectedOrigins, origin]
    updateFilter('content_origin', next)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex min-h-16 max-w-6xl items-center gap-3 px-4 sm:px-6">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="grid size-10 shrink-0 place-items-center rounded-md text-gray-600 hover:bg-gray-100"
            aria-label="Back to dashboard"
            title="Back to dashboard"
          >
            <ArrowLeft size={20} />
          </button>
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-gray-900">Missed questions</h1>
            <p className="text-sm text-gray-500">
              {review.isLoading ? 'Loading review set' : `${review.data?.total ?? 0} questions to revisit`}
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <div className="grid gap-6 lg:grid-cols-[17rem_minmax(0,1fr)]">
          <aside className="space-y-5 lg:sticky lg:top-6 lg:self-start" aria-label="Review filters">
            <div>
              <p className="mb-2 text-xs font-semibold text-gray-600">Source</p>
              <div className="flex flex-wrap gap-1" role="group" aria-label="Source">
                {[undefined, ...availableSources].map(source => {
                  const active = filters.source_type === source || (!source && !filters.source_type)
                  return (
                    <button
                      key={source ?? 'all'}
                      type="button"
                      onClick={() => updateFilter('source_type', source)}
                      className={`min-h-9 rounded-md px-3 text-xs font-semibold ${active ? 'bg-gray-900 text-white' : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-100'}`}
                    >
                      {source ? labelFor(source) : 'All'}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
              <FilterSelect label="Test" value={filters.source_test_name} values={facets.data?.source_test_names ?? []} onChange={value => updateFilter('source_test_name', value)} />
              <FilterSelect label="Section" value={filters.source_section_code} values={facets.data?.source_section_codes ?? []} onChange={value => updateFilter('source_section_code', value)} />
              <FilterSelect label="Module" value={filters.source_module_code} values={facets.data?.source_module_codes ?? []} onChange={value => updateFilter('source_module_code', value)} />
              <FilterSelect label="Domain" value={filters.domain} values={facets.data?.domains ?? []} onChange={value => updateFilter('domain', value)} />
              <FilterSelect label="Focus" value={filters.focus_key} values={facets.data?.focus_keys ?? []} onChange={value => updateFilter('focus_key', value)} />
              <FilterSelect label="Stem type" value={filters.stem_type_key} values={facets.data?.stem_type_keys ?? []} onChange={value => updateFilter('stem_type_key', value)} />
            </div>

            {(facets.data?.difficulties.length ?? 0) > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold text-gray-600">Difficulty</p>
                <div className="flex flex-wrap gap-1">
                  {facets.data?.difficulties.map(value => (
                    <button
                      key={value}
                      type="button"
                      aria-pressed={filters.difficulty === value}
                      onClick={() => updateFilter('difficulty', filters.difficulty === value ? undefined : value)}
                      className={`min-h-9 rounded-md px-3 text-xs font-semibold ${filters.difficulty === value ? 'bg-blue-600 text-white' : 'border border-gray-300 bg-white text-gray-700'}`}
                    >
                      {labelFor(value)}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {(facets.data?.content_origins.length ?? 0) > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold text-gray-600">Content origin</p>
                <div className="flex flex-wrap gap-1">
                  {facets.data?.content_origins.map(value => (
                    <button
                      key={value}
                      type="button"
                      aria-pressed={selectedOrigins.includes(value)}
                      onClick={() => toggleOrigin(value)}
                      className={`min-h-9 rounded-md px-3 text-xs font-semibold ${selectedOrigins.includes(value) ? 'bg-blue-600 text-white' : 'border border-gray-300 bg-white text-gray-700'}`}
                    >
                      {labelFor(value)}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </aside>

          <section className="min-w-0" aria-live="polite">
            {review.isLoading && (
              <div className="space-y-4" aria-label="Loading missed questions">
                {[1, 2].map(value => <div key={value} className="h-72 animate-pulse rounded-lg border border-gray-200 bg-white" />)}
              </div>
            )}

            {review.isError && (
              <div className="rounded-lg border border-red-200 bg-white p-8 text-center">
                <AlertCircle className="mx-auto text-red-500" size={28} />
                <h2 className="mt-3 font-semibold text-gray-900">Could not load missed questions</h2>
                <button type="button" onClick={() => review.refetch()} className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-md bg-gray-900 px-4 text-sm font-semibold text-white">
                  <RefreshCw size={16} /> Try again
                </button>
              </div>
            )}

            {!review.isLoading && !review.isError && review.data?.items.length === 0 && (
              <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
                <BookOpen className="mx-auto text-gray-400" size={30} />
                <h2 className="mt-3 font-semibold text-gray-900">No missed questions found</h2>
                <p className="mt-1 text-sm text-gray-500">Adjust the filters or continue practicing.</p>
              </div>
            )}

            <div className="space-y-4">
              {review.data?.items.map(item => <ReviewCard key={item.question_id} item={item} />)}
            </div>

            {review.data && review.data.total > 0 && (
              <nav className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4" aria-label="Review pages">
                <button
                  type="button"
                  onClick={() => setPage(value => Math.max(1, value - 1))}
                  disabled={page === 1}
                  className="inline-flex min-h-10 items-center gap-1 rounded-md border border-gray-300 bg-white px-3 text-sm font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft size={17} /> Previous
                </button>
                <span className="text-sm text-gray-500">Page {page}</span>
                <button
                  type="button"
                  onClick={() => setPage(value => value + 1)}
                  disabled={!review.data.has_more}
                  className="inline-flex min-h-10 items-center gap-1 rounded-md border border-gray-300 bg-white px-3 text-sm font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next <ChevronRight size={17} />
                </button>
              </nav>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}
