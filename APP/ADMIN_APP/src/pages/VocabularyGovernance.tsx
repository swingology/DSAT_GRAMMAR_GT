import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../api/client'
import type { VocabCandidate, Vocabulary, VocabMaster, VocabCandidatesFile } from '../types'

function errorMessage(err: unknown) {
  return err instanceof Error ? err.message : 'Request failed.'
}

function fmtDate(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

function StatCard({
  label, value, sub, color = 'text-gray-800',
}: {
  label: string
  value: string | number
  sub?: string
  color?: string
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-base font-semibold text-gray-800">{title}</h3>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  )
}

const DOMAIN_COLORS: Record<string, string> = {
  system: 'bg-gray-100 text-gray-700',
  grammar: 'bg-purple-100 text-purple-700',
  reading: 'bg-blue-100 text-blue-700',
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  retired: 'bg-gray-200 text-gray-500',
}

function CandidateRow({ c }: { c: VocabCandidate }) {
  const [open, setOpen] = useState(false)
  const hasContext = c.contexts.length > 0 || c.job_ids.length > 0
  return (
    <>
      <tr
        className={hasContext ? 'hover:bg-gray-50 cursor-pointer' : 'hover:bg-gray-50'}
        onClick={() => hasContext && setOpen((v) => !v)}
      >
        <td className="px-4 py-2 font-mono text-xs text-gray-800">{c.value}</td>
        <td className="px-4 py-2 font-mono text-xs text-gray-500">{c.field}</td>
        <td className="px-4 py-2 font-mono text-xs text-gray-500">{c.vocab}</td>
        <td className="px-4 py-2 text-right text-sm font-semibold text-gray-800">{c.occurrences}</td>
        <td className="px-4 py-2 text-xs text-gray-500">{fmtDate(c.first_seen)}</td>
        <td className="px-4 py-2 text-xs text-gray-500">{fmtDate(c.last_seen)}</td>
        <td className="px-4 py-2 text-xs text-gray-400">
          {hasContext ? (open ? '▾' : '▸') : ''}
        </td>
      </tr>
      {open && hasContext && (
        <tr className="bg-gray-50">
          <td colSpan={7} className="px-4 py-3">
            {c.contexts.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-semibold text-gray-500 mb-1">Contexts</p>
                <ul className="space-y-1">
                  {c.contexts.map((ctx, i) => (
                    <li key={i} className="text-xs text-gray-700 font-mono bg-white border border-gray-200 rounded px-2 py-1 break-all">
                      {ctx}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {c.job_ids.length > 0 && (
              <p className="text-xs text-gray-500">
                <span className="font-semibold">Jobs:</span> {c.job_ids.join(', ')}
              </p>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

function VocabCard({ v }: { v: Vocabulary }) {
  const [open, setOpen] = useState(false)
  const activeCount = v.entries.filter((e) => e.status === 'active').length
  const retiredCount = v.entries.length - activeCount
  const domainColor = DOMAIN_COLORS[v.domain] ?? 'bg-gray-100 text-gray-700'
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((val) => !val)}
        className="w-full flex items-start justify-between gap-3 px-4 py-3 text-left hover:bg-gray-50 transition"
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs font-semibold text-gray-800">{v.name}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${domainColor}`}>{v.domain}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{v.kind}</span>
          </div>
          {v.comment && <p className="text-xs text-gray-500 mt-1">{v.comment}</p>}
        </div>
        <div className="flex-shrink-0 text-right">
          <p className="text-sm font-semibold text-gray-800">{v.entries.length}</p>
          <p className="text-[10px] text-gray-400">{activeCount} active · {retiredCount} retired</p>
        </div>
      </button>
      {open && (
        <div className="border-t border-gray-200 px-4 py-3 bg-gray-50/50">
          <ul className="space-y-1">
            {v.entries.map((e) => (
              <li key={e.value} className="flex items-center gap-2 text-xs">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${STATUS_COLORS[e.status] ?? 'bg-gray-100 text-gray-600'}`}>
                  {e.status}
                </span>
                <span className="font-mono text-gray-800">{e.value}</span>
                {e.description && <span className="text-gray-400">— {e.description}</span>}
                <span className="text-gray-300 ml-auto">added {e.added}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

type Tab = 'candidates' | 'master'

export function VocabularyGovernance() {
  const [tab, setTab] = useState<Tab>('candidates')
  const [candSearch, setCandSearch] = useState('')
  const [masterSearch, setMasterSearch] = useState('')
  const [domainFilter, setDomainFilter] = useState<string>('all')

  const { data: master, isLoading: masterLoading, isError: masterError, error: masterErr } =
    useQuery<VocabMaster>({
      queryKey: ['vocab-master'],
      queryFn: () => adminApi.getVocabMaster(),
      retry: 1,
    })

  const { data: candFile, isLoading: candLoading, isError: candError, error: candErr } =
    useQuery<VocabCandidatesFile>({
      queryKey: ['vocab-candidates'],
      queryFn: () => adminApi.getVocabCandidates(),
      retry: 1,
    })

  const candidates = candFile?.candidates ?? []
  const candidatesByVocab = useMemo(() => {
    const filtered = candSearch.trim()
      ? candidates.filter((c) =>
          [c.value, c.field, c.vocab].some((s) => s.toLowerCase().includes(candSearch.toLowerCase())))
      : candidates
    const sorted = [...filtered].sort((a, b) => b.occurrences - a.occurrences)
    const groups: Record<string, VocabCandidate[]> = {}
    for (const c of sorted) {
      ;(groups[c.vocab] ??= []).push(c)
    }
    return groups
  }, [candidates, candSearch])

  const totalOccurrences = candidates.reduce((s, c) => s + c.occurrences, 0)

  const filteredVocabs = useMemo(() => {
    if (!master) return []
    const bySearch = masterSearch.trim()
      ? master.vocabularies.filter((v) =>
          [v.name, v.comment, ...v.entries.map((e) => e.value)].some((s) =>
            s.toLowerCase().includes(masterSearch.toLowerCase())))
      : master.vocabularies
    return domainFilter === 'all'
      ? bySearch
      : bySearch.filter((v) => v.domain === domainFilter)
  }, [master, masterSearch, domainFilter])

  const domains = useMemo(() => {
    if (!master) return []
    return Array.from(new Set(master.vocabularies.map((v) => v.domain)))
  }, [master])

  const isLoading = tab === 'candidates' ? candLoading : masterLoading
  const isError = tab === 'candidates' ? candError : masterError
  const error = tab === 'candidates' ? candErr : masterErr

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Vocabulary Governance</h2>
        <p className="text-sm text-gray-500 mt-1">
          Controlled-vocabulary manifest and the off-vocabulary candidate review queue.
          Candidates are non-blocking — never promoted directly. Approve a canonical
          replacement in the rule doc, then run <code className="text-xs bg-gray-100 px-1 rounded">gen_vocab --generate</code>.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        <button
          onClick={() => setTab('candidates')}
          className={`px-4 py-2 text-sm font-medium transition ${
            tab === 'candidates'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          Candidate Queue {candidates.length > 0 && `(${candidates.length})`}
        </button>
        <button
          onClick={() => setTab('master')}
          className={`px-4 py-2 text-sm font-medium transition ${
            tab === 'master'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          Canonical Vocabularies {master && `(${master.vocabularies.length})`}
        </button>
      </div>

      {tab === 'candidates' && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard label="Unique candidates" value={candidates.length} sub="off-vocab keys seen at ingest" />
            <StatCard label="Total occurrences" value={totalOccurrences} sub="across all candidates" />
            <StatCard
              label="Queue status"
              value={candidates.length > 10 ? 'Over threshold' : 'Within threshold'}
              sub={candidates.length > 10 ? 'gen_vocab --check would fail CI' : '≤10 unreviewed'}
              color={candidates.length > 10 ? 'text-amber-600' : 'text-green-600'}
            />
          </div>

          <div className="flex items-center justify-between gap-3">
            <input
              type="text"
              placeholder="Filter by value, field, or vocab…"
              value={candSearch}
              onChange={(e) => setCandSearch(e.target.value)}
              className="flex-1 max-w-sm text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400">
              {Object.keys(candidatesByVocab).length} vocab families ·{' '}
              {Object.values(candidatesByVocab).reduce((s, g) => s + g.length, 0)} shown
            </p>
          </div>

          {isLoading && <p className="text-sm text-gray-500">Loading candidates…</p>}
          {isError && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              {errorMessage(error)}
            </div>
          )}
          {!isLoading && !isError && candidates.length === 0 && (
            <div className="text-sm text-gray-500 bg-white border border-gray-200 rounded-lg p-6 text-center">
              No off-vocabulary candidates queued — every extracted key matched an active entry.
            </div>
          )}

          {!isLoading && !isError && Object.keys(candidatesByVocab).length > 0 && (
            <div className="space-y-5">
              {Object.entries(candidatesByVocab)
                .sort((a, b) => b[1].reduce((s, c) => s + c.occurrences, 0) - a[1].reduce((s, c) => s + c.occurrences, 0))
                .map(([vocab, items]) => (
                  <div key={vocab}>
                    <SectionHeader
                      title={vocab}
                      sub={`${items.length} candidate${items.length === 1 ? '' : 's'} · ${items.reduce((s, c) => s + c.occurrences, 0)} occurrences`}
                    />
                    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                          <tr>
                            <th className="px-4 py-2 text-left">Value</th>
                            <th className="px-4 py-2 text-left">Field</th>
                            <th className="px-4 py-2 text-left">Vocab</th>
                            <th className="px-4 py-2 text-right">Occ.</th>
                            <th className="px-4 py-2 text-left">First seen</th>
                            <th className="px-4 py-2 text-left">Last seen</th>
                            <th className="px-4 py-2"></th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {items.map((c, i) => (
                            <CandidateRow key={`${c.value}-${i}`} c={c} />
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </>
      )}

      {tab === 'master' && (
        <>
          {master && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatCard label="Vocabularies" value={master.vocabularies.length} />
              <StatCard
                label="Total entries"
                value={master.vocabularies.reduce((s, v) => s + v.entries.length, 0)}
              />
              <StatCard
                label="Active entries"
                value={master.vocabularies.reduce(
                  (s, v) => s + v.entries.filter((e) => e.status === 'active').length,
                  0,
                )}
              />
              <StatCard
                label="Retired entries"
                value={master.vocabularies.reduce(
                  (s, v) => s + v.entries.filter((e) => e.status !== 'active').length,
                  0,
                )}
              />
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <input
              type="text"
              placeholder="Filter by vocab name or key…"
              value={masterSearch}
              onChange={(e) => setMasterSearch(e.target.value)}
              className="flex-1 min-w-[200px] max-w-sm text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All domains</option>
              {domains.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400">{filteredVocabs.length} shown</p>
          </div>

          {isLoading && <p className="text-sm text-gray-500">Loading vocabularies…</p>}
          {isError && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              {errorMessage(error)}
            </div>
          )}
          {!isLoading && !isError && filteredVocabs.length === 0 && (
            <p className="text-sm text-gray-500">No vocabularies match the filter.</p>
          )}

          {!isLoading && !isError && filteredVocabs.length > 0 && (
            <div className="space-y-3">
              {filteredVocabs.map((v) => (
                <VocabCard key={v.name} v={v} />
              ))}
            </div>
          )}

          {master && (
            <p className="text-xs text-gray-400 italic">
              {master.note}
            </p>
          )}
        </>
      )}
    </div>
  )
}