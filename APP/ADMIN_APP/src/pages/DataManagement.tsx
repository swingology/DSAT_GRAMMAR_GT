import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../api/client'
import type { Question } from '../types'

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

export function DataManagement() {
  const qc = useQueryClient()
  const [status, setStatus] = useState<StatusFilter>('all')
  const [origin, setOrigin] = useState<OriginFilter>('all')
  const [page, setPage] = useState(1)
  const [rejectTarget, setRejectTarget] = useState<Question | null>(null)
  const limit = 25

  const params: Record<string, any> = { limit, offset: (page - 1) * limit }
  if (status !== 'all') params.practice_status = status
  if (origin !== 'all') params.content_origin = origin

  const { data, isLoading, isError } = useQuery({
    queryKey: ['questions', params],
    queryFn: () => adminApi.listQuestions(params),
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

        <div className="ml-auto text-xs text-gray-400 self-center">
          {total} total
        </div>
      </div>

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
                  <td className="px-4 py-3 max-w-sm">
                    <p className="text-gray-800 line-clamp-2 text-xs leading-relaxed">{q.current_question_text}</p>
                    <p className="text-gray-400 font-mono text-xs mt-0.5">{q.id.slice(0, 8)}…</p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={q.practice_status} />
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 capitalize">
                    {q.content_origin?.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {(q.grammar_focus_key || q.reading_focus_key || '—').replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 capitalize">
                    {q.difficulty_overall ?? '—'}
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

      {/* Pagination */}
      {totalPages > 1 && (
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

      {rejectTarget && (
        <RejectModal
          question={rejectTarget}
          onReject={(reason) => rejectMutation.mutate({ id: rejectTarget.id, reason })}
          onClose={() => setRejectTarget(null)}
        />
      )}
    </div>
  )
}
