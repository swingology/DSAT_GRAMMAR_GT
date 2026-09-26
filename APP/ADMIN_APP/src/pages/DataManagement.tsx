import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi, type QueryParams } from '../api/client'
import { IdChip, IdListPanel } from '../components/IdChip'
import { useToast } from '../components/Toast'
import { ptLabel, questionSourceLabel } from '../utils/sourceLabel'
import type { IssueType, Question, QuestionIssue, TestSummary } from '../types'

const ID_LIST_KEY = 'admin:idList'
const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/

// Mirrors _parse_question_search in backend/app/routers/admin.py so the pill can
// switch on every keystroke instead of waiting for the query round-trip.
type SearchKind = 'id' | 'id_prefix' | 'source' | 'text'
const SOURCE_TOKEN_RE = /(?<year>(?:19|20)\d{2})(?!\d)|(?:pt|(?:practice\s*)?test)\s*(?<pt>\d{1,2})(?!\d)|s(?:ec(?:tion)?)?\s*(?<sec>\d{1,2})(?!\d)|m(?:od(?:ule)?)?\s*(?<mod>\d{1,2}[ab]?)(?![\da-z])|q(?:uestion)?\s*(?<q>\d{1,3})(?!\d)/gi
const isSeparators = (s: string) => /^[ \t·.,;:/|\-_#]*$/.test(s)

function classifySearch(raw: string): SearchKind | null {
  const q = raw.trim()
  if (!q) return null
  if (UUID_RE.test(q)) return 'id'
  const seen = new Set<string>()
  let consumed = 0
  let isSource = true
  for (const m of q.matchAll(SOURCE_TOKEN_RE)) {
    const key = Object.entries(m.groups ?? {}).find(([, v]) => v !== undefined)?.[0]
    if (!key || seen.has(key) || !isSeparators(q.slice(consumed, m.index))) { isSource = false; break }
    seen.add(key)
    consumed = m.index + m[0].length
  }
  if (isSource && seen.size > 0 && isSeparators(q.slice(consumed))) return 'source'
  if (/^[0-9a-f-]{4,35}$/i.test(q) && /\d/.test(q)) return 'id_prefix'
  return 'text'
}

const SEARCH_PILL: Record<SearchKind, { label: string; className: string }> = {
  id: { label: 'Question ID', className: 'bg-emerald-50/70 text-emerald-700 ring-emerald-200/70' },
  id_prefix: { label: 'ID prefix', className: 'bg-sky-50/70 text-sky-700 ring-sky-200/70' },
  source: { label: 'Source ref', className: 'bg-violet-50/70 text-violet-700 ring-violet-200/70' },
  text: { label: 'Text', className: 'bg-gray-100/70 text-gray-600 ring-gray-200/70' },
}

type StatusFilter = 'all' | 'active' | 'draft' | 'needs_review' | 'rejected'
type OriginFilter = 'all' | 'official' | 'generated' | 'admin_created'

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: 'bg-emerald-100 text-emerald-700',
    approved: 'bg-emerald-100 text-emerald-700',
    draft: 'bg-gray-100 text-gray-600',
    needs_review: 'bg-amber-100 text-amber-700',
    rejected: 'bg-red-100 text-red-600',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

function RejectModal({ question, onReject, onClose }: {
  question: Question
  onReject: (reason: string) => void
  onClose: () => void
}) {
  const [reason, setReason] = useState('')
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold text-gray-800 mb-2">Reject Question</h2>
        <p className="text-sm text-gray-500 mb-4 line-clamp-2">{question.current_question_text}</p>
        <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-red-500"
          placeholder="Why is this question being rejected?"
        />
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
            Cancel
          </button>
          <button
            onClick={() => onReject(reason)}
            disabled={!reason}
            className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50 transition"
          >
            Reject
          </button>
        </div>
      </div>
    </div>
  )
}

const ISSUE_LABELS: Record<IssueType, string> = {
  missing_graph: 'Missing graph / image',
  wrong_answer_key: 'Wrong answer key',
  bad_options: 'Wrong or missing options',
  wrong_source_info: 'Wrong source info',
  passage_problem: 'Passage missing / garbled',
  typo_formatting: 'Typo / formatting',
  duplicate: 'Duplicate',
  bad_explanation: 'Bad explanation',
  other: 'Other',
}

const errorDetail = (e: unknown) => (e as { detail?: string } | null)?.detail || 'Request failed.'

function IssuesPanel({ question, onRejected }: { question: Question; onRejected: () => void }) {
  const qc = useQueryClient()
  const [issueType, setIssueType] = useState<IssueType>('missing_graph')
  const [note, setNote] = useState('')
  const [decisionNote, setDecisionNote] = useState('')
  const issuesKey = ['question-issues', question.id]
  const { data: issues = [], isLoading } = useQuery<QuestionIssue[]>({
    queryKey: issuesKey,
    queryFn: () => adminApi.listQuestionIssues(question.id),
  })
  const refresh = () => {
    qc.invalidateQueries({ queryKey: issuesKey })
    qc.invalidateQueries({ queryKey: ['questions'] })
  }
  const flag = useMutation({
    mutationFn: () => adminApi.flagQuestionIssue(question.id, issueType, note.trim() || undefined),
    onSuccess: () => { setNote(''); refresh() },
  })
  const resolve = useMutation({
    mutationFn: (resolution: 'approved' | 'edited' | 'rejected') =>
      adminApi.resolveQuestionIssues(question.id, resolution, decisionNote.trim() || undefined),
    onSuccess: (_data, resolution) => {
      setDecisionNote('')
      refresh()
      if (resolution === 'rejected') onRejected()
    },
  })
  const openIssues = issues.filter((i) => i.status === 'open')

  return (
    <div className="border-t border-gray-100 pt-4 space-y-3">
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Issues</p>
        {openIssues.length > 0 && (
          <span className="text-xs px-2 py-0.5 rounded-md bg-red-50 text-red-600 font-medium">
            {openIssues.length} open
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="h-8 bg-gray-100 rounded animate-pulse" />
      ) : issues.length === 0 ? (
        <p className="text-xs text-gray-400">No issues flagged.</p>
      ) : (
        <ul className="space-y-1.5">
          {issues.map((i) => (
            <li
              key={i.id}
              className={`text-xs rounded-lg border px-3 py-2 ${
                i.status === 'open' ? 'border-red-200 bg-red-50/40' : 'border-gray-200 text-gray-400'
              }`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className={`font-medium ${i.status === 'open' ? 'text-red-700' : ''}`}>
                  {ISSUE_LABELS[i.issue_type] ?? i.issue_type}
                </span>
                <span className="text-gray-400">
                  {i.reported_by_role === 'student' ? `Student #${i.reporter_user_id ?? '?'}` : 'Admin'}
                  {i.created_at ? ` · ${new Date(i.created_at).toLocaleDateString()}` : ''}
                </span>
                {i.status === 'resolved' && (
                  <span className="capitalize">· resolved: {i.resolution}</span>
                )}
              </div>
              {i.note && <p className="mt-1 text-gray-600 whitespace-pre-wrap">{i.note}</p>}
              {i.resolution_note && <p className="mt-1 italic">{i.resolution_note}</p>}
            </li>
          ))}
        </ul>
      )}

      {openIssues.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/60 p-3 space-y-2">
          <p className="text-xs text-amber-800">
            Review the open issues, then decide. To fix it, use <span className="font-medium">Edit</span> —
            saving resolves them as edited — or mark them fixed after an edit you already saved.
          </p>
          <input
            type="text"
            value={decisionNote}
            onChange={(e) => setDecisionNote(e.target.value)}
            placeholder="Decision note (optional; used as the rejection reason)"
            maxLength={2000}
            className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => resolve.mutate('approved')}
              disabled={resolve.isPending}
              className="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg disabled:opacity-50 transition"
            >
              Approve — no change needed
            </button>
            <button
              onClick={() => resolve.mutate('edited')}
              disabled={resolve.isPending}
              className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition"
            >
              Mark fixed (edited)
            </button>
            <button
              onClick={() => resolve.mutate('rejected')}
              disabled={resolve.isPending}
              className="px-3 py-1.5 text-xs bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50 transition"
            >
              Reject question
            </button>
          </div>
          {resolve.isError && <p className="text-xs text-red-600">{errorDetail(resolve.error)}</p>}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <select
          value={issueType}
          onChange={(e) => setIssueType(e.target.value as IssueType)}
          aria-label="Issue type"
          className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {(Object.keys(ISSUE_LABELS) as IssueType[]).map((t) => (
            <option key={t} value={t}>{ISSUE_LABELS[t]}</option>
          ))}
        </select>
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !flag.isPending) flag.mutate() }}
          placeholder="What's wrong? (optional)"
          maxLength={2000}
          className="flex-1 min-w-40 border border-gray-300 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => flag.mutate()}
          disabled={flag.isPending}
          className="px-3 py-1.5 text-xs border border-red-200 text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50 transition"
        >
          {flag.isPending ? 'Flagging…' : 'Flag issue'}
        </button>
      </div>
      {flag.isError && <p className="text-xs text-red-600">{errorDetail(flag.error)}</p>}
    </div>
  )
}

function QuestionDetailModal({ question, onClose }: { question: Question; onClose: () => void }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [questionText, setQuestionText] = useState(question.current_question_text)
  const [passageText, setPassageText] = useState(question.current_passage_text ?? '')
  const [correctLabel, setCorrectLabel] = useState(question.current_correct_option_label)
  const [explanationText, setExplanationText] = useState(question.current_explanation_text ?? '')
  const [changeNotes, setChangeNotes] = useState('')
  const toast = useToast()
  // Same query as IssuesPanel, so flags/decisions made while this modal is open count.
  const { data: issues = [] } = useQuery<QuestionIssue[]>({
    queryKey: ['question-issues', question.id],
    queryFn: () => adminApi.listQuestionIssues(question.id),
  })
  const openIssueCount = issues.filter((i) => i.status === 'open').length
  const [resolveOnSave, setResolveOnSave] = useState(true)

  // Esc closes the modal, but not mid-edit — that would silently drop unsaved changes.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !editing) onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [editing, onClose])

  const editMutation = useMutation({
    mutationFn: async () => {
      await adminApi.editQuestion(question.id, {
        question_text: questionText,
        passage_text: passageText || undefined,
        correct_option_label: correctLabel,
        explanation_text: explanationText || undefined,
        change_notes: changeNotes || undefined,
      })
      // Resolve only after the edit is saved; the backend also checks for it.
      // A failure here must not look like a failed save, or the admin re-saves a duplicate version.
      if (openIssueCount > 0 && resolveOnSave) {
        try {
          await adminApi.resolveQuestionIssues(question.id, 'edited', changeNotes || undefined)
        } catch (e) {
          return { resolveError: errorDetail(e) }
        }
      }
      return { resolveError: null }
    },
    onSuccess: ({ resolveError }) => {
      qc.invalidateQueries({ queryKey: ['questions'] })
      qc.invalidateQueries({ queryKey: ['question-issues', question.id] })
      if (resolveError) toast.showError(`Edit saved, but issues were not resolved: ${resolveError}`)
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              {questionSourceLabel(question) || 'Question'}
            </h2>
            <IdChip id={question.id} />
          </div>
          <div className="flex items-center gap-2">
            {question.annotation_stale && (
              <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full font-medium">
                Annotation stale
              </span>
            )}
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">
              ×
            </button>
          </div>
        </div>

        {!editing ? (
          <div className="space-y-4">
            {question.current_passage_text && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Passage</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{question.current_passage_text}</p>
              </div>
            )}
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Question</p>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{question.current_question_text}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Options</p>
              <div className="space-y-1">
                {(question.options ?? []).map((opt) => (
                  <div
                    key={opt.id ?? opt.option_label}
                    className={`text-sm px-3 py-1.5 rounded-lg border ${
                      opt.option_label === question.current_correct_option_label
                        ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                        : 'border-gray-200 text-gray-600'
                    }`}
                  >
                    <span className="font-medium">{opt.option_label}.</span> {opt.option_text}
                  </div>
                ))}
              </div>
            </div>
            {question.current_explanation_text && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Explanation</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{question.current_explanation_text}</p>
              </div>
            )}
            {question.annotation && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Annotation</p>
                <div className="flex flex-wrap gap-1">
                  {question.annotation.grammar_focus_key && (
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                      {String(question.annotation.grammar_focus_key).replace(/_/g, ' ')}
                    </span>
                  )}
                  {question.annotation.reading_focus_key && (
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                      {String(question.annotation.reading_focus_key).replace(/_/g, ' ')}
                    </span>
                  )}
                  {question.annotation.difficulty_overall && (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full capitalize">
                      {String(question.annotation.difficulty_overall)}
                    </span>
                  )}
                </div>
              </div>
            )}
            <IssuesPanel question={question} onRejected={onClose} />
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setEditing(true)}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Edit
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {question.current_passage_text !== undefined && (
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  Passage
                </label>
                <textarea
                  value={passageText}
                  onChange={(e) => setPassageText(e.target.value)}
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Question text
              </label>
              <textarea
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Correct option
              </label>
              <select
                value={correctLabel}
                onChange={(e) => setCorrectLabel(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {(question.options ?? []).map((opt) => (
                  <option key={opt.option_label} value={opt.option_label}>
                    {opt.option_label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Explanation
              </label>
              <textarea
                value={explanationText}
                onChange={(e) => setExplanationText(e.target.value)}
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Change notes
              </label>
              <input
                type="text"
                value={changeNotes}
                onChange={(e) => setChangeNotes(e.target.value)}
                placeholder="Why is this edit being made?"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            {openIssueCount > 0 && (
              <label className="flex items-center gap-2 text-xs text-gray-600">
                <input
                  type="checkbox"
                  checked={resolveOnSave}
                  onChange={(e) => setResolveOnSave(e.target.checked)}
                />
                Resolve {openIssueCount} open issue{openIssueCount === 1 ? '' : 's'} as edited when saving
              </label>
            )}
            {editMutation.isError && (
              <p className="text-red-600 text-sm">Failed to save changes. {errorDetail(editMutation.error)}</p>
            )}
            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={() => setEditing(false)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => editMutation.mutate()}
                disabled={editMutation.isPending}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition"
              >
                {editMutation.isPending ? 'Saving…' : 'Save'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function TestBrowser({ onSelectTest }: { onSelectTest: (t: TestSummary) => void }) {
  const { data: tests, isLoading } = useQuery<TestSummary[]>({
    queryKey: ['admin-tests'],
    queryFn: () => adminApi.getTests(),
    retry: 1,
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (!tests || tests.length === 0) {
    return <div className="p-8 text-center text-gray-400 text-sm">No source test data found.</div>
  }

  const originLabels: Record<string, string> = {
    official: 'Official',
    unofficial: 'Unofficial',
    generated: 'Generated',
  }
  const originOrder = ['official', 'unofficial', 'generated']

  // Backend sorts by content_origin, then year/PT for official rows and by
  // source_test_name for unofficial rows — so grouping here just buckets
  // consecutive same-key runs rather than re-sorting.
  const byOrigin = new Map<string, TestSummary[]>()
  for (const t of tests) {
    const origin = t.content_origin ?? 'official'
    const list = byOrigin.get(origin)
    if (list) list.push(t)
    else byOrigin.set(origin, [t])
  }

  const originKeys = [...byOrigin.keys()].sort(
    (a, b) => originOrder.indexOf(a) - originOrder.indexOf(b),
  )

  function groupBy<T extends TestSummary>(items: T[], keyFn: (t: T) => string): { key: string; items: T[] }[] {
    const groups: { key: string; items: T[] }[] = []
    for (const t of items) {
      const key = keyFn(t)
      const last = groups[groups.length - 1]
      if (last && last.key === key) last.items.push(t)
      else groups.push({ key, items: [t] })
    }
    return groups
  }

  function TestCard({ t }: { t: TestSummary }) {
    return (
      <button
        onClick={() => onSelectTest(t)}
        className="bg-white border border-gray-200 rounded-xl p-4 text-left hover:border-blue-300 hover:shadow-sm transition"
      >
        <p className="text-sm font-semibold text-gray-800">
          {t.source_release_year ? `${t.source_release_year} · ` : ''}
          {t.pt_number != null ? ptLabel(t.pt_number) : (t.source_test_name ?? 'Unknown')}
          {t.source_section_code ? ` Sec${t.source_section_code}` : ''}
          {t.source_module_code ? ` Mod${t.source_module_code}` : ''}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {t.question_count} questions · {t.approved_count} approved
        </p>
      </button>
    )
  }

  return (
    <div className="space-y-8">
      {originKeys.map((origin) => {
        const items = byOrigin.get(origin)!
        const isUnofficial = origin === 'unofficial'
        // Unofficial has no official PT#, so subcategorize by source name
        // (e.g. "CrackAP") instead of by year.
        const subGroups = isUnofficial
          ? groupBy(items, (t) => t.source_test_name ?? 'Unknown source')
          : groupBy(items, (t) => String(t.source_release_year ?? 'Unknown year'))

        return (
          <div key={origin}>
            <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 pb-1 border-b border-gray-200">
              {originLabels[origin] ?? origin}
            </h2>
            <div className="space-y-6">
              {subGroups.map((g, gi) => (
                <div key={gi}>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                    {g.key}
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {g.items.map((t, i) => (
                      <TestCard key={i} t={t} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function DataManagement() {
  const qc = useQueryClient()
  const [status, setStatus] = useState<StatusFilter>('all')
  const [origin, setOrigin] = useState<OriginFilter>('all')
  const [page, setPage] = useState(1)
  const [rejectTarget, setRejectTarget] = useState<Question | null>(null)
  const [detailTarget, setDetailTarget] = useState<Question | null>(null)
  const [mode, setMode] = useState<'list' | 'tests'>('list')
  const [testFilter, setTestFilter] = useState<TestSummary | null>(null)
  const limit = 25

  // Collected question ids — survives navigation so a list can be built across pages/tests.
  const [idList, setIdList] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem(ID_LIST_KEY) ?? '[]') } catch { return [] }
  })
  const updateIdList = (next: string[]) => {
    setIdList(next)
    try { localStorage.setItem(ID_LIST_KEY, JSON.stringify(next)) } catch { /* storage unavailable */ }
  }
  const toggleId = (id: string) =>
    updateIdList(idList.includes(id) ? idList.filter((x) => x !== id) : [...idList, id])

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 250)
    return () => clearTimeout(t)
  }, [search])
  const searchKind = classifySearch(search)
  // A search is bank-wide: it replaces the test/module scoping, and the backend
  // also drops status/origin filters for ID searches.
  const [issuesOnly, setIssuesOnly] = useState(false)
  const browsingTests = mode === 'tests' && !testFilter && !debouncedSearch && !issuesOnly

  const params: QueryParams = { limit, offset: (page - 1) * limit }
  if (debouncedSearch) params.q = debouncedSearch
  if (issuesOnly) params.has_open_issues = true
  if (status === 'needs_review') {
    // needs_review is a question_jobs.status value, not a practice_status
    // value (practice_status is publication state: draft/active/retired/rejected).
    params.job_status = status
  } else if (status !== 'all') {
    params.practice_status = status
  }
  if (origin !== 'all') params.content_origin = origin
  if (testFilter && !debouncedSearch) {
    if (testFilter.source_release_year != null) params.source_release_year = testFilter.source_release_year
    if (testFilter.source_test_name) params.source_test_name = testFilter.source_test_name
    if (testFilter.source_exam_code) params.source_exam_code = testFilter.source_exam_code
    if (testFilter.source_subject_code) params.source_subject_code = testFilter.source_subject_code
    if (testFilter.source_section_code) params.source_section_code = testFilter.source_section_code
    if (testFilter.source_module_code) params.source_module_code = testFilter.source_module_code
    params.sort_by_source = true
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['questions', params],
    queryFn: () => adminApi.listQuestions(params),
    enabled: !browsingTests,
    retry: 1,
  })

  const approveMutation = useMutation({
    mutationFn: (id: string) => adminApi.approveQuestion(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['questions'] }),
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      adminApi.rejectQuestion(id, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['questions'] })
      setRejectTarget(null)
    },
  })

  const questions: Question[] = data?.questions ?? data?.items ?? data ?? []
  const total: number = data?.total ?? questions.length
  const totalPages = Math.ceil(total / limit)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Data Management</h2>
        <p className="text-sm text-gray-500 mt-0.5">Review, approve, and manage questions</p>
      </div>

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap gap-3">
        {/* Status filter */}
        <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
          {(['all', 'active', 'draft', 'needs_review', 'rejected'] as StatusFilter[]).map((s) => (
            <button
              key={s}
              onClick={() => { setStatus(s); setPage(1) }}
              className={[
                'px-3 py-1.5 rounded-md text-xs font-medium transition capitalize',
                status === s ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700',
              ].join(' ')}
            >
              {s.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {/* Origin filter */}
        <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
          {(['all', 'official', 'generated', 'admin_created'] as OriginFilter[]).map((o) => (
            <button
              key={o}
              onClick={() => { setOrigin(o); setPage(1) }}
              className={[
                'px-3 py-1.5 rounded-md text-xs font-medium transition capitalize',
                origin === o ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700',
              ].join(' ')}
            >
              {o.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
          <button
            onClick={() => { setMode('list'); setTestFilter(null) }}
            className={[
              'px-3 py-1.5 rounded-md text-xs font-medium transition',
              mode === 'list' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700',
            ].join(' ')}
          >
            All Questions
          </button>
          <button
            onClick={() => setMode('tests')}
            className={[
              'px-3 py-1.5 rounded-md text-xs font-medium transition',
              mode === 'tests' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700',
            ].join(' ')}
          >
            Browse by Test
          </button>
        </div>

        <button
          onClick={() => { setIssuesOnly(!issuesOnly); setPage(1) }}
          aria-pressed={issuesOnly}
          className={[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition border',
            issuesOnly
              ? 'bg-red-50 text-red-600 border-red-200'
              : 'bg-white text-gray-500 border-gray-200 hover:text-gray-700',
          ].join(' ')}
        >
          Has open issues
        </button>

        <div className="relative w-96 max-w-full">
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            onKeyDown={(e) => { if (e.key === 'Escape') { setSearch(''); setPage(1) } }}
            placeholder="Search: ID, ID prefix, 2024 PT5 section 1 mod02b Q10, or text"
            aria-label="Search questions by ID, source reference, or text"
            spellCheck={false}
            className="w-full pl-3 pr-24 py-1.5 rounded-lg border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
          {searchKind && (
            <span
              aria-live="polite"
              className={`pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 px-2 py-0.5 rounded-md text-[11px] font-medium ring-1 backdrop-blur-sm transition-colors ${SEARCH_PILL[searchKind].className}`}
            >
              {SEARCH_PILL[searchKind].label}
            </span>
          )}
        </div>

        <div className="ml-auto text-xs text-gray-400 self-center">
          {total} total
        </div>
      </div>

      {browsingTests ? (
        <TestBrowser onSelectTest={setTestFilter} />
      ) : (
        <>
          {testFilter && (
            <button
              onClick={() => setTestFilter(null)}
              className="text-xs text-blue-600 hover:underline"
            >
              ← Back to tests
            </button>
          )}
          {/* Table */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            {isLoading ? (
              <div className="space-y-2 p-4">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
                ))}
              </div>
            ) : isError ? (
              <div className="p-8 text-center text-red-600 text-sm">Failed to load questions.</div>
            ) : questions.length === 0 ? (
              <div className="p-8 text-center text-gray-400 text-sm">No questions found.</div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Question</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Origin</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Focus</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Difficulty</th>
                    <th className="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {questions.map((q) => (
                    <tr key={q.id} className="hover:bg-gray-50 transition">
                      <td
                        className="px-4 py-3 max-w-sm cursor-pointer"
                        onClick={() => setDetailTarget(q)}
                      >
                        <p className="text-gray-800 line-clamp-2 text-xs leading-relaxed hover:underline">
                          {q.current_question_text}
                        </p>
                        <div className="mt-1 flex flex-wrap items-center gap-2">
                          <IdChip id={q.id} collected={idList.includes(q.id)} onToggleCollect={toggleId} />
                          {questionSourceLabel(q) && (
                            <span className="text-[11px] text-gray-400">{questionSourceLabel(q)}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap items-center gap-1">
                          <StatusBadge status={q.practice_status} />
                          {(q.open_issue_count ?? 0) > 0 && (
                            <span
                              className="text-xs px-2 py-0.5 rounded-md bg-red-50 text-red-600 font-medium"
                              title={`${q.open_issue_count} open issue(s)`}
                            >
                              {q.open_issue_count} issue{q.open_issue_count === 1 ? '' : 's'}
                            </span>
                          )}
                          {q.content_origin === 'official' && !q.cb_question_id && (
                            <span
                              className="text-xs px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 font-medium"
                              title="Official question with no College Board bank ID"
                            >
                              No CB ID
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500 capitalize">
                        {q.content_origin?.replace(/_/g, ' ')}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {(q.annotation?.grammar_focus_key ?? q.annotation?.reading_focus_key ?? '—')
                          .toString()
                          .replace(/_/g, ' ')}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500 capitalize">
                        {q.annotation?.difficulty_overall ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex gap-1 justify-end">
                          {q.practice_status !== 'active' && q.practice_status !== 'approved' && (
                            <button
                              onClick={() => approveMutation.mutate(q.id)}
                              disabled={approveMutation.isPending}
                              className="text-xs px-2 py-1 bg-emerald-100 hover:bg-emerald-200 text-emerald-700 rounded transition"
                            >
                              Approve
                            </button>
                          )}
                          {q.practice_status !== 'rejected' && (
                            <button
                              onClick={() => setRejectTarget(q)}
                              className="text-xs px-2 py-1 bg-red-100 hover:bg-red-200 text-red-600 rounded transition"
                            >
                              Reject
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* Pagination */}
      {!browsingTests && totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 text-xs">
            Page {page} of {totalPages} · {total} questions
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
            >
              ← Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
            >
              Next →
            </button>
          </div>
        </div>
      )}

      <IdListPanel ids={idList} onClear={() => updateIdList([])} onRemove={(id) => updateIdList(idList.filter((x) => x !== id))} />

      {rejectTarget && (
        <RejectModal
          question={rejectTarget}
          onReject={(reason) => rejectMutation.mutate({ id: rejectTarget.id, reason })}
          onClose={() => setRejectTarget(null)}
        />
      )}

      {detailTarget && (
        <QuestionDetailModal question={detailTarget} onClose={() => setDetailTarget(null)} />
      )}
    </div>
  )
}
