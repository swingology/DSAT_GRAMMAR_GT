import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminApi, generateApi, type QueryParams } from '../api/client'
import type {
  GenerationBatchJob,
  GenerationBatchRequest,
  Question,
  ReleasePolicy,
  TestSummary,
  VocabMaster,
} from '../types'

type Domain = 'grammar' | 'reading'
type Spec = Record<string, string>

const LAST_BATCH_KEY = 'generate:lastBatchId'
const PRESETS_KEY = 'generate:presets'
const DRAFT_KEY = 'generate:draft'

/** Everything the form holds, so a preset or the auto-saved draft restores it 1:1. */
interface FormState {
  domain: Domain
  spec: Spec
  distractors: string[]
  count: number
  releasePolicy: ReleasePolicy
  skipReview: boolean
  providerName: string
  modelName: string
  referenceId?: string
  referenceLabel?: string
}
interface Preset extends FormState {
  name: string
  builtin?: boolean
}

const EMPTY_FORM: FormState = {
  domain: 'reading',
  spec: { difficulty_overall: 'medium' },
  distractors: ['', '', ''],
  count: 3,
  releasePolicy: 'admin_review_required',
  skipReview: false,
  providerName: '',
  modelName: '',
}

/** Quick-fill templates using canonical keys from CANONICAL_VOCABULARIES.md / rules §10–§16. */
const BUILTIN_PRESETS: Preset[] = [
  {
    name: 'Grammar · sentence boundary, garden-path trap (high)',
    builtin: true,
    ...EMPTY_FORM,
    domain: 'grammar',
    spec: {
      target_grammar_role_key: 'sentence_boundary',
      target_grammar_focus_key: 'sentence_boundary',
      target_syntactic_trap_key: 'garden_path',
      target_frequency_band: 'high',
      test_format_key: 'digital_app_adaptive',
      stimulus_mode_key: 'sentence_only',
      stem_type_key: 'conform_to_standard_english',
      difficulty_overall: 'high',
    },
  },
  {
    name: 'Grammar · subject–verb agreement, interrupted subject (medium)',
    builtin: true,
    ...EMPTY_FORM,
    domain: 'grammar',
    spec: {
      target_grammar_role_key: 'agreement',
      target_grammar_focus_key: 'subject_verb_agreement',
      target_syntactic_trap_key: 'interruption_breaks_subject_verb',
      target_frequency_band: 'high',
      test_format_key: 'digital_app_adaptive',
      stimulus_mode_key: 'sentence_only',
      stem_type_key: 'conform_to_standard_english',
      difficulty_overall: 'medium',
    },
  },
  {
    name: 'Reading · inference, study-design isolation limit (high)',
    builtin: true,
    ...EMPTY_FORM,
    domain: 'reading',
    spec: {
      target_skill_family_key: 'inferences',
      target_reading_focus_key: 'implication_inference',
      question_family_key: 'information_and_ideas',
      target_test_construct_key: 'inference_boundary_control',
      target_reasoning_trap_key: 'overreach',
      passage_structure_pattern: 'research_summary',
      passage_architecture_key: 'experiment_hypothesis_control_result',
      inference_type_note: 'study_design_isolation_limit',
      stimulus_mode_key: 'prose_single',
      stem_type_key: 'most_logically_completes',
      difficulty_overall: 'high',
    },
    distractors: ['overreach', 'contradiction', 'topical_relevance_without_logical_connection'],
  },
  {
    name: 'Reading · inference, comparative count / inverted-logic trap (high)',
    builtin: true,
    ...EMPTY_FORM,
    domain: 'reading',
    spec: {
      target_skill_family_key: 'inferences',
      target_reading_focus_key: 'implication_inference',
      question_family_key: 'information_and_ideas',
      target_test_construct_key: 'inference_boundary_control',
      target_reasoning_trap_key: 'inverted_logic',
      passage_structure_pattern: 'compare_contrast',
      stimulus_mode_key: 'prose_single',
      stem_type_key: 'most_logically_completes',
      difficulty_overall: 'high',
    },
    distractors: ['overreach', 'inverted_logic', 'partial_match'],
  },
]

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? { ...fallback, ...(JSON.parse(raw) as T) } : fallback
  } catch {
    return fallback
  }
}
function writeJson(key: string, value: unknown) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* storage unavailable */ }
}
function loadPresets(): Preset[] {
  try {
    const raw = localStorage.getItem(PRESETS_KEY)
    return raw ? (JSON.parse(raw) as Preset[]) : []
  } catch {
    return []
  }
}
const LIVE_BATCH_STATUSES = new Set(['pending', 'generating', 'reviewing'])
const LIVE_JOB_STATUSES = new Set(['pending', 'extracting', 'annotating', 'overlap_checking', 'validating', 'retrying'])

/**
 * Form fields per domain. `required` mirrors GenerationBatchRequest's
 * per-domain mandatory list (payload.py) so the server's 422 is never a
 * surprise; `vocab` is a substring used to find a datalist in master.json.
 */
const FIELDS: Record<Domain, { key: string; required?: boolean; vocab?: string; hint?: string }[]> = {
  grammar: [
    { key: 'target_grammar_role_key', required: true, vocab: 'grammar_role' },
    { key: 'target_grammar_focus_key', required: true, vocab: 'grammar_focus' },
    { key: 'target_syntactic_trap_key', vocab: 'syntactic_trap', hint: '"none" if no trap' },
    { key: 'target_frequency_band', required: true, vocab: 'frequency_band' },
    { key: 'test_format_key', required: true, vocab: 'test_format' },
    { key: 'stimulus_mode_key', required: true, vocab: 'stimulus_mode' },
    { key: 'stem_type_key', required: true, vocab: 'stem_type' },
    { key: 'target_transition_subtype_key', vocab: 'transition_subtype', hint: 'transition_logic items only' },
  ],
  reading: [
    { key: 'target_skill_family_key', required: true, vocab: 'skill_family' },
    { key: 'target_reading_focus_key', required: true, vocab: 'reading_focus' },
    { key: 'question_family_key', vocab: 'question_family' },
    { key: 'target_test_construct_key', required: true, vocab: 'test_construct' },
    { key: 'target_reasoning_trap_key', required: true, vocab: 'reasoning_trap' },
    { key: 'passage_structure_pattern', required: true, vocab: 'passage_structure' },
    { key: 'passage_architecture_key', vocab: 'passage_architecture' },
    { key: 'stimulus_mode_key', required: true, vocab: 'stimulus_mode' },
    { key: 'stem_type_key', required: true, vocab: 'stem_type' },
    { key: 'target_craft_subconstruct_key', vocab: 'craft_subconstruct', hint: 'required for craft_and_structure' },
    { key: 'inference_type_note', hint: 'inferences only' },
    { key: 'polarity_context', hint: 'polarity_fit only' },
    { key: 'target_sentence_function_role', hint: 'sentence_function only' },
    { key: 'quantitative_sub_pattern', hint: 'command_of_evidence_quantitative only' },
  ],
}

function str(v: unknown): string {
  return typeof v === 'string' ? v : ''
}

function domainOf(q: Question | null): Domain | null {
  const a = q?.annotation
  if (!a) return null
  if (a.reading_focus_key || a.reading_skill_family_key || a.skill_family_key) return 'reading'
  if (a.grammar_role_key || a.grammar_focus_key) return 'grammar'
  return null
}

/** Pre-fill the target spec from the reference question's annotation. */
function specFromReference(q: Question, domain: Domain): { spec: Spec; distractors: string[] } {
  const a = (q.annotation ?? {}) as Record<string, unknown>
  const profile = (a.generation_profile ?? {}) as Record<string, unknown>
  const shared: Spec = {
    stimulus_mode_key: str(a.stimulus_mode_key) || str(q.stimulus_mode_key),
    stem_type_key: str(a.stem_type_key),
    difficulty_overall: str(a.difficulty_overall) || 'medium',
  }
  if (domain === 'grammar') {
    return {
      spec: {
        ...shared,
        target_grammar_role_key: str(a.grammar_role_key),
        target_grammar_focus_key: str(a.grammar_focus_key),
        target_syntactic_trap_key: str(a.syntactic_trap_key) || 'none',
        target_frequency_band: str(profile.target_frequency_band) || 'high',
        test_format_key: 'digital_app_adaptive',
      },
      distractors: [],
    }
  }
  const annOptions = Array.isArray(a.options) ? (a.options as Record<string, unknown>[]) : []
  const distractors = annOptions
    .filter((o) => !o.is_correct && str(o.distractor_type_key) && o.distractor_type_key !== 'correct')
    .map((o) => str(o.distractor_type_key))
    .slice(0, 3)
  while (distractors.length < 3) distractors.push('')
  return {
    spec: {
      ...shared,
      target_skill_family_key: str(a.reading_skill_family_key) || str(a.skill_family_key),
      target_reading_focus_key: str(a.reading_focus_key),
      question_family_key: str(a.question_family_key),
      target_test_construct_key: str(a.target_test_construct_key),
      target_reasoning_trap_key: str(a.reasoning_trap_key),
      passage_structure_pattern: str(a.passage_structure_pattern),
      passage_architecture_key: str(a.passage_architecture_key),
      target_craft_subconstruct_key: str(a.target_craft_subconstruct_key) || str(a.craft_subconstruct_key),
      inference_type_note: str(a.inference_type_note),
      polarity_context: str(a.polarity_context),
      target_sentence_function_role: str(a.target_sentence_function_role),
      quantitative_sub_pattern: str(a.quantitative_sub_pattern),
    },
    distractors,
  }
}

function testLabel(t: TestSummary): string {
  const parts = [
    t.source_release_year,
    t.pt_number != null ? `PT${t.pt_number}` : t.source_test_name ?? t.source_exam_code,
    t.source_section_code && `Sec ${t.source_section_code}`,
    t.source_module_code && `Mod ${t.source_module_code}`,
  ]
  return parts.filter(Boolean).join(' · ')
}

function testParams(t: TestSummary): QueryParams {
  const p: QueryParams = { content_origin: 'official', sort_by_source: true, limit: 200 }
  if (t.source_release_year != null) p.source_release_year = t.source_release_year
  if (t.source_test_name) p.source_test_name = t.source_test_name
  if (t.source_exam_code) p.source_exam_code = t.source_exam_code
  if (t.source_subject_code) p.source_subject_code = t.source_subject_code
  if (t.source_section_code) p.source_section_code = t.source_section_code
  if (t.source_module_code) p.source_module_code = t.source_module_code
  return p
}

function JobBadge({ status }: { status: string }) {
  const tone = status === 'approved'
    ? 'bg-emerald-100 text-emerald-700'
    : status === 'needs_review'
      ? 'bg-amber-100 text-amber-700'
      : status.startsWith('failed')
        ? 'bg-red-100 text-red-600'
        : 'bg-blue-50 text-blue-700'
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tone}`}>{status.replace(/_/g, ' ')}</span>
}

const inputCls = 'w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200'

export function Generate() {
  const qc = useQueryClient()

  // --- reference question -------------------------------------------------
  const [test, setTest] = useState<TestSummary | null>(null)
  const [filter, setFilter] = useState('')
  const [reference, setReference] = useState<Question | null>(null)

  const tests = useQuery({ queryKey: ['tests'], queryFn: adminApi.getTests })
  const officialTests = useMemo(
    () => (tests.data ?? []).filter((t) => !t.content_origin || t.content_origin === 'official'),
    [tests.data],
  )
  const moduleQuestions = useQuery({
    queryKey: ['questions', 'reference', test],
    queryFn: () => adminApi.listQuestions(testParams(test as TestSummary)),
    enabled: !!test,
  })
  const candidates = useMemo(() => {
    const rows: Question[] = moduleQuestions.data?.questions ?? []
    const f = filter.trim().toLowerCase()
    if (!f) return rows
    return rows.filter((q) =>
      String(q.source_question_number ?? '').includes(f) || q.current_question_text.toLowerCase().includes(f)
        || (q.current_passage_text ?? '').toLowerCase().includes(f),
    )
  }, [moduleQuestions.data, filter])

  // --- target spec ------------------------------------------------------
  // The form auto-restores from the last visit; presets are named snapshots.
  const [draft] = useState<FormState>(() => readJson(DRAFT_KEY, EMPTY_FORM))
  const [domain, setDomain] = useState<Domain>(draft.domain)
  const [spec, setSpec] = useState<Spec>(draft.spec)
  const [distractors, setDistractors] = useState<string[]>(draft.distractors)
  const [count, setCount] = useState(draft.count)
  const [releasePolicy, setReleasePolicy] = useState<ReleasePolicy>(draft.releasePolicy)
  const [skipReview, setSkipReview] = useState(draft.skipReview)
  const [providerName, setProviderName] = useState(draft.providerName)
  const [modelName, setModelName] = useState(draft.modelName)
  // Reference restored from a draft/preset by id only (no get-by-id endpoint for
  // official questions); re-picking it in section 1 replaces this.
  const [refFallback, setRefFallback] = useState<{ id: string; label: string } | null>(
    draft.referenceId ? { id: draft.referenceId, label: draft.referenceLabel ?? '' } : null,
  )

  const [presets, setPresets] = useState<Preset[]>(loadPresets)
  const [presetChoice, setPresetChoice] = useState('')
  const [presetName, setPresetName] = useState('')

  const referenceLabel = (q: Question) =>
    [q.source_test_name ?? q.source_exam_code, q.source_module_code && `Mod ${q.source_module_code}`, q.source_question_number != null && `Q${q.source_question_number}`]
      .filter(Boolean).join(' · ')

  const snapshot = (): FormState => ({
    domain, spec, distractors, count, releasePolicy, skipReview, providerName, modelName,
    referenceId: reference?.id ?? refFallback?.id,
    referenceLabel: reference ? referenceLabel(reference) : refFallback?.label,
  })
  useEffect(() => { writeJson(DRAFT_KEY, snapshot()) })  // no deps: persist after every render

  const applyForm = (f: FormState) => {
    setDomain(f.domain)
    setSpec({ difficulty_overall: 'medium', ...f.spec })
    setDistractors(f.distractors?.length === 3 ? f.distractors : ['', '', ''])
    setCount(f.count ?? 3)
    setReleasePolicy(f.releasePolicy ?? 'admin_review_required')
    setSkipReview(!!f.skipReview)
    setProviderName(f.providerName ?? '')
    setModelName(f.modelName ?? '')
    if (f.referenceId && f.referenceId !== reference?.id) {
      setReference(null)
      setRefFallback({ id: f.referenceId, label: f.referenceLabel ?? '' })
    }
  }
  const allPresets = [...BUILTIN_PRESETS, ...presets]
  const loadPreset = (name: string) => {
    setPresetChoice(name)
    const p = allPresets.find((x) => x.name === name)
    if (p) applyForm(p)
  }
  const savePreset = () => {
    const name = presetName.trim()
    if (!name) return
    const next = [...presets.filter((p) => p.name !== name), { ...snapshot(), name }]
    setPresets(next)
    writeJson(PRESETS_KEY, next)
    setPresetChoice(name)
    setPresetName('')
  }
  const deletePreset = () => {
    const next = presets.filter((p) => p.name !== presetChoice)
    setPresets(next)
    writeJson(PRESETS_KEY, next)
    setPresetChoice('')
  }
  const resetForm = () => { applyForm(EMPTY_FORM); setReference(null); setRefFallback(null); setPresetChoice('') }

  const vocab = useQuery({ queryKey: ['vocab-master'], queryFn: adminApi.getVocabMaster, staleTime: 5 * 60_000 })
  const datalist = (needle?: string): string[] => {
    if (!needle || !vocab.data) return []
    const v = (vocab.data as VocabMaster).vocabularies.find((x) => x.name.toLowerCase().includes(needle))
    return v ? v.entries.filter((e) => e.status === 'active').map((e) => e.value) : []
  }

  const pickReference = (q: Question) => {
    setReference(q)
    setRefFallback(null)
    const d = domainOf(q)
    if (d) {
      const filled = specFromReference(q, d)
      setDomain(d)
      setSpec(filled.spec)
      setDistractors(filled.distractors)
    }
  }
  const setField = (key: string, value: string) => setSpec((s) => ({ ...s, [key]: value }))

  const missing = FIELDS[domain].filter((f) => f.required && !spec[f.key]?.trim()).map((f) => f.key)
  if (domain === 'reading' && distractors.some((d) => !d.trim())) missing.push('target_distractor_pattern (3)')

  // --- batch --------------------------------------------------------------
  const [batchId, setBatchId] = useState<string>(() => {
    try { return localStorage.getItem(LAST_BATCH_KEY) ?? '' } catch { return '' }
  })
  const [trackInput, setTrackInput] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [reportId, setReportId] = useState<string | null>(null)

  useEffect(() => {
    try { if (batchId) localStorage.setItem(LAST_BATCH_KEY, batchId) } catch { /* storage unavailable */ }
  }, [batchId])

  const createBatch = useMutation({
    mutationFn: (body: GenerationBatchRequest) => generateApi.createBatch(body),
    onSuccess: (res) => { setBatchId(res.id); setReportId(null); setSubmitError('') },
    onError: (e: Error & { detail?: string }) => setSubmitError(e.detail || e.message),
  })

  const submit = () => {
    const body: GenerationBatchRequest = {
      requested_count: count,
      release_policy: releasePolicy,
      skip_review: skipReview,
      difficulty_overall: spec.difficulty_overall || 'medium',
    }
    const targets: Record<string, string> = {}
    for (const f of FIELDS[domain]) {
      const v = spec[f.key]?.trim()
      if (v) targets[f.key] = v
    }
    Object.assign(body, targets)
    if (domain === 'grammar' && !body.target_syntactic_trap_key) body.target_syntactic_trap_key = 'none'
    if (domain === 'reading') body.target_distractor_pattern = distractors.map((d) => d.trim())
    const refId = reference?.id ?? refFallback?.id
    if (refId) {
      body.derived_from_question_id = refId
      body.source_question_ids = [refId]
    }
    if (providerName.trim()) body.provider_name = providerName.trim()
    if (modelName.trim()) body.model_name = modelName.trim()
    createBatch.mutate(body)
  }

  const batch = useQuery({
    queryKey: ['gen-batch', batchId],
    queryFn: () => generateApi.getBatch(batchId),
    enabled: !!batchId,
    refetchInterval: (q) => (q.state.data && LIVE_BATCH_STATUSES.has(q.state.data.status) ? 3000 : false),
  })
  const jobs = useQuery({
    queryKey: ['gen-batch-jobs', batchId],
    queryFn: () => generateApi.getBatchJobs(batchId),
    enabled: !!batchId,
    refetchInterval: (q) => {
      const rows = q.state.data?.jobs ?? []
      return rows.some((j) => LIVE_JOB_STATUSES.has(j.status)) || LIVE_BATCH_STATUSES.has(q.state.data?.status ?? '')
        ? 3000
        : false
    },
  })

  const refreshBatch = () => {
    qc.invalidateQueries({ queryKey: ['gen-batch', batchId] })
    qc.invalidateQueries({ queryKey: ['gen-batch-jobs', batchId] })
  }
  const approve = useMutation({
    mutationFn: (id: string) => adminApi.approveQuestion(id),
    onSuccess: () => { refreshBatch(); qc.invalidateQueries({ queryKey: ['questions'] }) },
  })
  const reject = useMutation({
    mutationFn: (id: string) => adminApi.rejectQuestion(id, 'Rejected from Generate page'),
    onSuccess: () => { refreshBatch(); qc.invalidateQueries({ queryKey: ['questions'] }) },
  })
  const retryFailed = useMutation({ mutationFn: () => generateApi.retryFailed(batchId), onSuccess: refreshBatch })

  // --- report -------------------------------------------------------------
  const report = useQuery({
    queryKey: ['gen-report', reportId],
    queryFn: () => adminApi.getGeneratedQuestionReport(reportId as string),
    enabled: !!reportId,
    // The review swarm lands a little after the question is saved; keep the
    // open report fresh without the user re-clicking.
    refetchInterval: 15_000,
  })
  const [copied, setCopied] = useState(false)
  const copyReport = async () => {
    if (!report.data) return
    try {
      await navigator.clipboard.writeText(report.data)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch { /* clipboard blocked; user can select the text */ }
  }
  const downloadHref = useMemo(
    () => (report.data ? URL.createObjectURL(new Blob([report.data], { type: 'text/markdown' })) : ''),
    [report.data],
  )

  const jobRows: GenerationBatchJob[] = jobs.data?.jobs ?? []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Generate</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Pick an official reference question, adjust the target spec, and queue a batch. Results land in
          Data Management as <span className="font-medium">draft</span> until approved; the review swarm runs
          automatically.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* ---------------- reference ---------------- */}
        <section className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">1 · Reference question</h3>
          <div className="flex gap-2">
            <select
              className={inputCls}
              value={test ? officialTests.indexOf(test) : ''}
              onChange={(e) => { setTest(officialTests[Number(e.target.value)] ?? null); setFilter('') }}
            >
              <option value="">{tests.isLoading ? 'Loading tests…' : 'Select test / module'}</option>
              {officialTests.map((t, i) => (
                <option key={i} value={i}>{testLabel(t)} ({t.question_count ?? '?'})</option>
              ))}
            </select>
            <input
              className={inputCls}
              placeholder="Filter by Q# or text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              disabled={!test}
            />
          </div>

          {test && (
            <div className="max-h-64 overflow-y-auto border border-gray-100 rounded-md divide-y divide-gray-100">
              {moduleQuestions.isLoading && <div className="p-3 text-sm text-gray-400">Loading…</div>}
              {candidates.map((q) => {
                const d = domainOf(q)
                const a = q.annotation ?? {}
                const focus = d === 'grammar' ? `${a.grammar_role_key} · ${a.grammar_focus_key}` : str(a.reading_focus_key)
                return (
                  <button
                    key={q.id}
                    onClick={() => pickReference(q)}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 ${reference?.id === q.id ? 'bg-blue-50' : ''}`}
                  >
                    <span className="font-mono text-xs text-gray-500 mr-2">Q{q.source_question_number ?? '?'}</span>
                    <span className="text-xs text-gray-500 mr-2">{d ?? 'unannotated'} · {focus || '—'} · {str(a.difficulty_overall) || '?'}</span>
                    <span className="text-gray-700 line-clamp-1">{q.current_question_text}</span>
                  </button>
                )
              })}
              {!moduleQuestions.isLoading && candidates.length === 0 && (
                <div className="p-3 text-sm text-gray-400">No questions match.</div>
              )}
            </div>
          )}

          {!reference && refFallback && (
            <div className="rounded-md bg-gray-50 border border-gray-100 p-3 text-xs text-gray-600 flex items-center gap-2">
              <span>Reference from saved settings: <span className="font-medium">{refFallback.label || '(unlabeled)'}</span> <span className="font-mono">{refFallback.id}</span></span>
              <button className="ml-auto text-red-600 hover:underline" onClick={() => setRefFallback(null)}>clear</button>
            </div>
          )}
          {reference && (
            <div className="rounded-md bg-gray-50 border border-gray-100 p-3 text-sm space-y-2">
              <div className="text-xs text-gray-500 font-mono">{reference.id}</div>
              {reference.current_passage_text && (
                <p className="text-gray-700 whitespace-pre-wrap">{reference.current_passage_text}</p>
              )}
              <p className="font-medium text-gray-800">{reference.current_question_text}</p>
              <ul className="space-y-0.5">
                {(reference.options ?? []).map((o) => (
                  <li key={o.id} className={o.is_correct ? 'text-emerald-700 font-medium' : 'text-gray-600'}>
                    {o.option_label}. {o.option_text}{o.is_correct ? ' ✓' : ''}
                  </li>
                ))}
              </ul>
              {!domainOf(reference) && (
                <p className="text-xs text-amber-700">This question has no annotation; fill the spec by hand.</p>
              )}
            </div>
          )}
        </section>

        {/* ---------------- spec ---------------- */}
        <section className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">2 · Target spec</h3>
            <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
              {(['reading', 'grammar'] as Domain[]).map((d) => (
                <button
                  key={d}
                  onClick={() => setDomain(d)}
                  className={`px-3 py-1 rounded-md text-xs font-medium capitalize ${domain === d ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'}`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Presets: built-in quick-fills + named snapshots saved in this browser */}
          <div className="flex flex-wrap gap-2 items-center rounded-md bg-gray-50 border border-gray-100 p-2">
            <select className={`${inputCls} flex-1 min-w-48`} value={presetChoice} onChange={(e) => loadPreset(e.target.value)}>
              <option value="">Load a template / saved settings…</option>
              <optgroup label="Templates">
                {BUILTIN_PRESETS.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
              </optgroup>
              {presets.length > 0 && (
                <optgroup label="Saved">
                  {presets.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
                </optgroup>
              )}
            </select>
            {presets.some((p) => p.name === presetChoice) && (
              <button className="px-2.5 py-1.5 text-xs rounded-md border border-gray-200 text-red-600" onClick={deletePreset}>Delete</button>
            )}
            <input
              className={`${inputCls} w-44`}
              placeholder="Save current as…"
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') savePreset() }}
            />
            <button className="px-2.5 py-1.5 text-xs rounded-md border border-gray-200" onClick={savePreset} disabled={!presetName.trim()}>Save</button>
            <button className="px-2.5 py-1.5 text-xs rounded-md border border-gray-200 text-gray-500" onClick={resetForm}>Reset</button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {FIELDS[domain].map((f) => {
              const options = datalist(f.vocab)
              const listId = `dl-${f.key}`
              return (
                <label key={f.key} className="text-xs text-gray-600">
                  <span className={f.required ? 'font-medium text-gray-700' : ''}>
                    {f.key}{f.required ? ' *' : ''}
                  </span>
                  {f.hint && <span className="text-gray-400"> — {f.hint}</span>}
                  <input
                    className={`${inputCls} mt-0.5 ${f.required && !spec[f.key]?.trim() ? 'border-amber-300' : ''}`}
                    list={options.length ? listId : undefined}
                    value={spec[f.key] ?? ''}
                    onChange={(e) => setField(f.key, e.target.value)}
                  />
                  {options.length > 0 && (
                    <datalist id={listId}>{options.map((v) => <option key={v} value={v} />)}</datalist>
                  )}
                </label>
              )
            })}
            <label className="text-xs text-gray-600">
              <span className="font-medium text-gray-700">difficulty_overall *</span>
              <select className={`${inputCls} mt-0.5`} value={spec.difficulty_overall ?? 'medium'} onChange={(e) => setField('difficulty_overall', e.target.value)}>
                {['low', 'medium', 'high'].map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </label>
          </div>

          {domain === 'reading' && (
            <div>
              <div className="text-xs font-medium text-gray-700">target_distractor_pattern * — one failure type per wrong option</div>
              <div className="grid grid-cols-3 gap-2 mt-0.5">
                {distractors.map((d, i) => (
                  <input
                    key={i}
                    className={`${inputCls} ${!d.trim() ? 'border-amber-300' : ''}`}
                    list="dl-distractor"
                    placeholder={`distractor ${i + 1}`}
                    value={d}
                    onChange={(e) => setDistractors((arr) => arr.map((x, j) => (j === i ? e.target.value : x)))}
                  />
                ))}
              </div>
              <datalist id="dl-distractor">{datalist('distractor_type').map((v) => <option key={v} value={v} />)}</datalist>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100">
            <label className="text-xs text-gray-600">
              count (1–25)
              <input type="number" min={1} max={25} className={`${inputCls} mt-0.5`} value={count} onChange={(e) => setCount(Math.max(1, Math.min(25, Number(e.target.value) || 1)))} />
            </label>
            <label className="text-xs text-gray-600">
              release_policy
              <select className={`${inputCls} mt-0.5`} value={releasePolicy} onChange={(e) => setReleasePolicy(e.target.value as ReleasePolicy)}>
                <option value="admin_review_required">admin_review_required</option>
                <option value="dry_run">dry_run</option>
                <option value="auto_release_on_accept">auto_release_on_accept</option>
              </select>
            </label>
            <label className="text-xs text-gray-600">
              provider_name <span className="text-gray-400">— blank = backend default</span>
              <input className={`${inputCls} mt-0.5`} placeholder="anthropic / openai / ollama" value={providerName} onChange={(e) => setProviderName(e.target.value)} />
            </label>
            <label className="text-xs text-gray-600">
              model_name <span className="text-gray-400">— blank = backend default</span>
              <input className={`${inputCls} mt-0.5`} value={modelName} onChange={(e) => setModelName(e.target.value)} />
            </label>
            <label className="text-xs text-gray-600 flex items-center gap-2 col-span-2">
              <input type="checkbox" checked={skipReview} onChange={(e) => setSkipReview(e.target.checked)} />
              skip the review swarm for this batch
            </label>
          </div>

          {missing.length > 0 && (
            <p className="text-xs text-amber-700">Required: {missing.join(', ')}</p>
          )}
          {submitError && <p className="text-xs text-red-600">{submitError}</p>}
          <button
            onClick={submit}
            disabled={missing.length > 0 || createBatch.isPending}
            className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium disabled:opacity-40"
          >
            {createBatch.isPending ? 'Queuing…' : `Generate ${count} question${count === 1 ? '' : 's'}`}
          </button>
        </section>
      </div>

      {/* ---------------- batch tracker ---------------- */}
      <section className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">3 · Batch</h3>
          {batchId && <span className="font-mono text-xs text-gray-500">{batchId}</span>}
          {batch.data && (
            <span className="text-xs text-gray-600">
              <JobBadge status={batch.data.status} /> · created {batch.data.created_count}/{batch.data.requested_count}
              · approved {batch.data.accepted_count} · needs review {batch.data.needs_review_count} · failed {batch.data.failed_count}
            </span>
          )}
          <div className="ml-auto flex gap-2">
            <input className={`${inputCls} w-72`} placeholder="Track another batch id" value={trackInput} onChange={(e) => setTrackInput(e.target.value)} />
            <button className="px-3 py-1.5 text-xs rounded-md border border-gray-200" onClick={() => { if (trackInput.trim()) { setBatchId(trackInput.trim()); setReportId(null) } }}>Track</button>
            {batch.data && batch.data.failed_count > 0 && (
              <button className="px-3 py-1.5 text-xs rounded-md border border-gray-200" onClick={() => retryFailed.mutate()}>Retry failed</button>
            )}
          </div>
        </div>

        {batch.isError && <p className="text-xs text-red-600">Batch not found.</p>}
        {jobRows.length > 0 && (
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500 text-left">
              <tr><th className="py-1">#</th><th>status</th><th>question</th><th>retries</th><th className="text-right">actions</th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {jobRows.map((j, i) => (
                <tr key={j.id}>
                  <td className="py-1.5 text-gray-500">{i + 1}</td>
                  <td><JobBadge status={j.status} /></td>
                  <td className="font-mono text-xs text-gray-600">{j.question_id ?? '—'}</td>
                  <td className="text-gray-500">{j.retry_count}</td>
                  <td className="text-right space-x-2">
                    {j.question_id && (
                      <>
                        <button className="text-xs text-blue-700 hover:underline" onClick={() => setReportId(j.question_id)}>Report</button>
                        <button className="text-xs text-emerald-700 hover:underline" onClick={() => approve.mutate(j.question_id as string)}>Approve</button>
                        <button className="text-xs text-red-600 hover:underline" onClick={() => reject.mutate(j.question_id as string)}>Reject</button>
                      </>
                    )}
                    {!j.question_id && Array.isArray(j.validation_errors) && j.validation_errors.length > 0 && (
                      <span className="text-xs text-red-600" title={JSON.stringify(j.validation_errors)}>validation errors</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* ---------------- report ---------------- */}
      {reportId && (
        <section className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-3">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">4 · Report</h3>
            <span className="font-mono text-xs text-gray-500">{reportId}</span>
            <div className="ml-auto flex gap-2">
              <button className="px-3 py-1.5 text-xs rounded-md border border-gray-200" onClick={() => report.refetch()}>Refresh</button>
              <button className="px-3 py-1.5 text-xs rounded-md border border-gray-200" onClick={copyReport}>{copied ? 'Copied' : 'Copy markdown'}</button>
              {downloadHref && (
                <a className="px-3 py-1.5 text-xs rounded-md border border-gray-200" href={downloadHref} download={`generated_${reportId}.md`}>Download .md</a>
              )}
              <button className="px-3 py-1.5 text-xs rounded-md border border-gray-200" onClick={() => setReportId(null)}>Close</button>
            </div>
          </div>
          {report.isLoading && <p className="text-sm text-gray-400">Rendering…</p>}
          {report.isError && <p className="text-sm text-red-600">Could not load report.</p>}
          {report.data && (
            <pre className="whitespace-pre-wrap text-xs leading-relaxed text-gray-800 bg-gray-50 border border-gray-100 rounded-md p-4 max-h-[70vh] overflow-y-auto">{report.data}</pre>
          )}
        </section>
      )}
    </div>
  )
}
