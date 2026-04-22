# TASKS_GEN_PIPELINE.md — Generation Pipeline (Full Implementation)

Fresh implementation on `alpha-v3-codex`. Not a port — build it right using
the deeper schema this branch has that alpha-v4 lacks.

**Design principle:** The LLM produces text. The DB controls everything else.
Constraints are typed schema data, not free-form strings. Quality is enforced
by structure, not by hoping the model behaves.

---

## What alpha-v4 Did (and Why We Can Do Better)

| alpha-v4 | This implementation |
|----------|-------------------|
| Flat list of `target_*` constraints in prompt | Grouped prompt sections by linguistic category |
| Round-robin seed selection | Vector similarity seed selection via `question_embeddings` |
| No drift detection | Post-generation Pass 2 diff; auto-rerun on critical drift |
| Subjective LLM realism gate | Corpus conformance check against approved CB questions |
| No coaching annotations | Third LLM call generates span-level coaching after approval |
| No IRT update after approval | `fn_refresh_irt_b()` called automatically on approval |
| No snapshot at generation time | `generation_params_snapshot_jsonb` written at item creation |
| 2 pipeline functions | Separated into focused modules (generate, drift, coaching) |

---

## Lifecycle Clarification

**`generated_questions` is post-approval only.** During generation, the only
pre-approval object is `question_ingestion_jobs` (with `content_origin='generated'`).
The review workflow lives entirely on `PATCH /jobs/{id}/status`. The
`PATCH /generate/questions/{id}/status` endpoint operates on already-approved
records. This eliminates the dual-state-machine problem.

**Drift-failed attempts are never hard-deleted.** On critical drift, the job row
is marked `status='drift_failed'` and kept. A new job is created for the retry.
This preserves Pass 1 output, Pass 2 annotations, validation failures, and
per-attempt traceability for prompt calibration.

---

## File Structure

```
backend/app/
  pipeline/
    generate.py       — core pipeline (create run, background loop)
    drift.py          — NEW: post-generation drift detection
    coaching.py       — NEW: coaching annotation generation after approval
  prompts/
    generation.py     — prompt builders (grouped constraints)
    coaching.py       — NEW: coaching annotation prompt
  routers/
    generate.py       — HTTP endpoints
  models/
    payload.py        — add generation models
backend/migrations/
  042_corpus_fingerprint.sql   — materialized view + status constraint + grammar fields
```

---

## Task 1 — Migration 038 (ALREADY COMPLETE)

**Migration 038 (`038_fresh_build_context_reconciliation.sql`) already implements
everything originally planned for "Migration 037":**

- `content_origin`, `generation_run_id`, `seed_question_id` on `question_ingestion_jobs` ✅
- `qij_input_format_check` constraint updated to include `'generated'` ✅
- `idx_qij_generation_run` index ✅
- All 9 generation templates seeded ✅
- `annotation_confidence` on `question_generation_profiles` ✅

**No new migration needed for these columns. Migrations 039 and 040 are already
taken (grammar keys and tokenization status). The next generation migration is
042 (corpus fingerprint view + status constraint + grammar fields).**

---

## Task 2 — Migration 042: Corpus Fingerprint + Status Constraint + Grammar Fields

File: `backend/migrations/042_corpus_fingerprint.sql`

Four parts bundled: (1) status constraint extended for `drift_failed`/`conformance_failed`,
(2) `generation_result_jsonb` added to `question_ingestion_jobs` so conformance
reports and attempt metadata are stored on staging rows, (3) the materialized
corpus fingerprint view including grammar dimensions for SEC gating, and (4) the
refresh function (app-layer only — no trigger).

**No DB trigger for refresh.** The trigger fires on `questions.review_status`
which does not exist on that table in this schema (it lives on
`generated_questions`). Refresh is handled exclusively by the app-layer call in
Task 10. Do not add a trigger here.

```sql
-- ── Part 1a: Extend question_ingestion_jobs status constraint ────────────────
-- Migration 014 created question_ingestion_jobs with a hard status check.
-- Add drift_failed and conformance_failed so pipeline writes don't crash.

ALTER TABLE public.question_ingestion_jobs
    DROP CONSTRAINT IF EXISTS qij_status_check;

ALTER TABLE public.question_ingestion_jobs
    ADD CONSTRAINT qij_status_check CHECK (
        status IN (
            'pending', 'extracting', 'annotating',
            'draft', 'reviewed', 'approved', 'rejected', 'failed',
            'drift_failed', 'conformance_failed'
        )
    );

-- ── Part 1b: Extend generation_runs status constraint ────────────────────────
-- Migration 021 created generation_runs with status CHECK ('running','complete',
-- 'failed','cancelled'). Add partial_complete for runs where some items fail.

ALTER TABLE public.generation_runs
    DROP CONSTRAINT IF EXISTS generation_runs_status_check;

ALTER TABLE public.generation_runs
    ADD CONSTRAINT generation_runs_status_check CHECK (
        status IN ('running', 'complete', 'partial_complete', 'failed', 'cancelled')
    );


-- ── Part 2: generation_result_jsonb on question_ingestion_jobs ───────────────
-- Migration 035 added generation_params_snapshot_jsonb to generated_questions
-- (post-approval only). Staging rows need their own column for conformance
-- reports, drift reports, and attempt metadata — including drift_failed rows
-- that are never promoted to generated_questions.

ALTER TABLE public.question_ingestion_jobs
    ADD COLUMN IF NOT EXISTS generation_result_jsonb jsonb;

-- NOTE: generation_params_snapshot_jsonb is NOT added here. That column lives on
-- generated_questions (migration 035, post-approval only). On staging rows,
-- generation_result_jsonb is the single column that holds ALL per-attempt data
-- (conformance_report, drift_report, attempt_number, constraint snapshot, model).
-- At approval time, the full record is copied from generation_result_jsonb into
-- generated_questions.generation_params_snapshot_jsonb. Do not reference
-- generation_params_snapshot_jsonb on question_ingestion_jobs in any pipeline code.

-- ── Part 2b: Composite index for drift endpoint filtering ─────────────────────

CREATE INDEX IF NOT EXISTS idx_qij_run_status
    ON public.question_ingestion_jobs(generation_run_id, status)
    WHERE generation_run_id IS NOT NULL;


-- ── Part 3: Materialized corpus fingerprint ───────────────────────────────────
-- Includes grammar_focus_key and grammar_role_key so SEC family questions
-- are gated against real CB grammar dimensions, not just prose/syntax ones.

CREATE MATERIALIZED VIEW IF NOT EXISTS public.v_corpus_fingerprint AS
SELECT
    qgp.question_family_key,
    qc.syntactic_complexity_key,
    qc.prose_register_key,
    qc.lexical_tier_key,
    qc.rhetorical_structure_key,
    qc.epistemic_stance_key,
    qc.difficulty_overall,
    qc.evidence_distribution_key,
    qc.inference_distance_key,
    qc.blank_position_key,
    qc.grammar_focus_key,
    qc.grammar_role_key,
    COUNT(*)                        AS n,
    AVG(qc.irt_b_estimate)          AS mean_irt_b,
    STDDEV(qc.irt_b_estimate)       AS stddev_irt_b
FROM public.question_classifications qc
JOIN public.questions q             ON q.id = qc.question_id
JOIN public.question_generation_profiles qgp ON qgp.question_id = q.id
WHERE q.is_active = TRUE
  AND (q.content_origin IS NULL OR q.content_origin = 'official')
-- NOTE: questions table has NO review_status column (it lives on generated_questions).
-- is_active=TRUE + official content_origin is the correct filter for CB ground truth.
GROUP BY
    qgp.question_family_key,
    qc.syntactic_complexity_key,
    qc.prose_register_key,
    qc.lexical_tier_key,
    qc.rhetorical_structure_key,
    qc.epistemic_stance_key,
    qc.difficulty_overall,
    qc.evidence_distribution_key,
    qc.inference_distance_key,
    qc.blank_position_key,
    qc.grammar_focus_key,
    qc.grammar_role_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_v_corpus_fingerprint
    ON public.v_corpus_fingerprint (
        question_family_key,
        syntactic_complexity_key,
        prose_register_key,
        lexical_tier_key,
        rhetorical_structure_key,
        epistemic_stance_key,
        difficulty_overall,
        evidence_distribution_key,
        inference_distance_key,
        blank_position_key,
        grammar_focus_key,
        grammar_role_key
    );


-- ── Part 4: Refresh function (called from app layer only) ─────────────────────
-- No trigger — refresh is called explicitly from routers/jobs.py on approval.
-- If two approvals occur concurrently, REFRESH MATERIALIZED VIEW CONCURRENTLY
-- may raise LockNotAvailableError. The app layer must catch this and either retry
-- once after 200ms or log-and-skip (the next approval will trigger another refresh).

CREATE OR REPLACE FUNCTION public.fn_refresh_corpus_fingerprint()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.v_corpus_fingerprint;
END $$;
```

---

## Task 3 — `app/prompts/generation.py`

### 3a. `PASS1_OUTPUT_SCHEMA`

The output contract injected via `<<pass1_schema>>`. Same shape as alpha-v4
but with stricter rules:
- `source_exam_code`, `source_module_code`, `source_question_number` must be null
- `table_data` / `graph_data` fields added for `prose_plus_table` /
  `prose_plus_graph` questions (shape per migration 020 COMMENT ON COLUMN)

### 3b. `_CONSTRAINT_GROUPS` — grouped constraint labels

**Do not use a flat list.** Group constraints by linguistic category.
The LLM processes grouped information more reliably than an undifferentiated list.

```python
_CONSTRAINT_GROUPS = [
    ("PASSAGE STYLE", [
        ("target_passage_source_type_key",   "Source type"),      # most powerful
        ("target_prose_register_key",        "Register"),
        ("target_prose_tone_key",            "Tone"),
        ("target_passage_era_key",           "Era"),
        ("target_narrator_perspective_key",  "Narrator"),
        ("target_passage_topic_domain_key",  "Topic domain"),
    ]),
    ("SYNTACTIC STRUCTURE", [
        ("target_syntactic_complexity_key",  "Sentence complexity"),
        ("target_syntactic_interruption_key","Interruption pattern"),
        ("target_noun_phrase_complexity_key","Noun phrase complexity"),
        ("target_clause_depth_min",          "Clause depth min"),
        ("target_clause_depth_max",          "Clause depth max"),
        ("target_sentence_length_profile",   "Sentence length"),
        ("target_nominalization_density",    "Nominalization density"),
        ("target_syntactic_trap_key",        "Syntactic trap to embed"),
    ]),
    ("LEXICAL PROFILE", [
        ("target_lexical_tier_key",          "Vocabulary tier"),
        ("target_vocabulary_profile_key",    "Vocabulary profile"),
        ("target_lexical_density",           "Lexical density"),
        ("target_lexile_min",                "Lexile min"),
        ("target_lexile_max",                "Lexile max"),
        ("target_word_count_min",            "Word count min"),
        ("target_word_count_max",            "Word count max"),
    ]),
    ("DISCOURSE & RHETORIC", [
        ("target_rhetorical_structure_key",  "Rhetorical structure"),
        ("target_cohesion_device_key",       "Cohesion device"),
        ("target_epistemic_stance_key",      "Epistemic stance"),
        ("target_evidence_distribution_key", "Evidence placement"),
        ("target_inference_distance_key",    "Inference distance"),
        ("target_transitional_logic_key",    "Transitional logic"),
        ("target_argument_role_key",         "Argument role"),
    ]),
    ("ITEM MECHANICS", [
        ("target_difficulty_overall",        "Difficulty"),
        ("target_passage_type_key",          "Passage type"),
        ("target_blank_position_key",        "Blank position"),
        ("target_evidence_distance",         "Evidence distance (sentences)"),
        ("target_answer_pos_key",            "Answer part of speech"),
        ("target_register_contrast",         "Register contrast"),
    ]),
    ("GRAMMAR (SEC)", [
        ("target_grammar_focus_key",         "Grammar rule being tested"),
        ("target_grammar_role_key",          "Grammatical role"),
    ]),
    ("DISTRACTOR DESIGN", [
        ("target_distractor_construction_key",   "Construction method"),
        ("target_distractor_difficulty_spread",  "Difficulty spread"),
        # target_passage_source_type_key is NOT repeated here — already in PASSAGE STYLE.
        # Repeating the same key in two groups sends conflicting signal to the LLM.
    ]),
]
```

### 3c. `build_generation_system_prompt(template_skeleton)`
Same as alpha-v4: replace `<<pass1_schema>>` in the template skeleton.

### 3d. `build_generation_user_prompt(...)`

Renders three sections:

1. **SEED EXEMPLAR** — the seed question's passage, stem, choices, correct answer.
   Label: "Use as style and difficulty reference — do NOT copy."

2. **TARGET SPECIFICATIONS** — constraints rendered in groups (from `_CONSTRAINT_GROUPS`).
   Omit any group that has no populated constraints.
   Omit any field within a group whose value is None.

3. **DIFFICULTY ANCHOR** — if `irt_b_estimate` is available on the seed question,
   include: "Reference difficulty (IRT b): {value:.2f} — target a question of
   similar difficulty unless target_difficulty_overall overrides this."

### 3e. No second LLM realism call

**The subjective LLM realism judge is replaced by `corpus_conformance_score()`.**
See Task 4 (drift) and the Ground Truth section at the bottom of this document.
No second LLM call is made before staging. The corpus conformance check runs
after Pass 2 annotation completes, using the same annotation data that already
exists — zero additional API cost.

---

## Task 4 — `app/pipeline/drift.py` — NEW

Post-generation drift detection. Called after Pass 2 annotates a generated job.
Also performs the corpus conformance check that replaces the LLM realism gate.

### `compute_expected_fingerprint(snapshot: dict) -> dict`

Extracts the subset of snapshot keys that correspond to classifiable dimensions:
```python
CRITICAL_DIMENSIONS = {
    "target_difficulty_overall":        "difficulty_overall",
    "target_syntactic_complexity_key":  "syntactic_complexity_key",
    "target_prose_register_key":        "prose_register_key",
    "target_epistemic_stance_key":      "epistemic_stance_key",
    "target_rhetorical_structure_key":  "rhetorical_structure_key",
    "target_evidence_distribution_key": "evidence_distribution_key",
    "target_inference_distance_key":    "inference_distance_key",
    "target_blank_position_key":        "blank_position_key",
}

# SEC_CRITICAL_DIMENSIONS are checked ONLY for conventions_grammar family jobs.
# grammar_focus_key is the tested rule — the most important single dimension for
# SEC conformance. grammar_role_key is the syntactic position being tested.
SEC_CRITICAL_DIMENSIONS = {
    "target_grammar_focus_key":         "grammar_focus_key",
    "target_grammar_role_key":          "grammar_role_key",
}

SOFT_DIMENSIONS = {
    "target_lexical_tier_key":          "lexical_tier_key",
    "target_passage_source_type_key":   "passage_source_type_key",
    "target_narrator_perspective_key":  "narrator_perspective_key",
}
```

Note: `evidence_distribution_key`, `inference_distance_key`, and
`blank_position_key` are CRITICAL for all families. `grammar_focus_key` and
`grammar_role_key` are CRITICAL only for `conventions_grammar` — the gating
logic in `corpus_conformance_score()` must merge `SEC_CRITICAL_DIMENSIONS` into
the critical set when `family_key == 'conventions_grammar'`.

### `detect_drift(expected: dict, actual: dict) -> DriftReport`

Returns a `DriftReport` dataclass:
```python
@dataclass
class DriftReport:
    critical_drifts: list[str]   # dimension names where expected != actual
    soft_drifts: list[str]
    is_critical: bool            # True if any critical dimension drifted
    summary: str                 # human-readable summary for run_notes
```

### `corpus_conformance_score(annotation, family_key, corpus_rows) -> ConformanceReport`

**Replaces the LLM realism judge.** Uses the materialized view loaded at startup
(or cached per run) to check whether each critical dimension's annotated value
falls within the top-N modal values for that family in the approved CB corpus.

```python
@dataclass
class ConformanceReport:
    critical_misses: list[str]   # dimensions where value is out of corpus norms
    soft_misses: list[str]
    corpus_n: int                # how many CB questions back this family
    is_conformant: bool          # True if no critical misses
    explanation: str             # human-readable, stored in run_notes

def corpus_conformance_score(
    annotation: QuestionAnnotation,
    family_key: str,
    corpus_rows: list[dict],     # rows from v_corpus_fingerprint for this family
    top_n: int = 3,              # accept if value is in top-N modal values
) -> ConformanceReport:
    critical = list(CRITICAL_DIMENSIONS.values())
    if family_key == "conventions_grammar":
        critical = critical + list(SEC_CRITICAL_DIMENSIONS.values())
    soft = list(SOFT_DIMENSIONS.values())

    family_rows = [r for r in corpus_rows if r["question_family_key"] == family_key]
    corpus_n = sum(r["n"] for r in family_rows)

    # If corpus is too small (<5 approved questions for this family),
    # skip the gate — not enough ground truth yet.
    if corpus_n < 5:
        return ConformanceReport([], [], corpus_n, True,
                                 f"Corpus too small ({corpus_n}) — gate bypassed")

    def top_n_values(dim: str) -> set:
        counts = {}
        for r in family_rows:
            v = r.get(dim)
            if v:
                counts[v] = counts.get(v, 0) + r["n"]
        return set(sorted(counts, key=counts.get, reverse=True)[:top_n])

    def check(dims):
        misses = []
        for dim in dims:
            val = getattr(annotation, dim, None)
            top = top_n_values(dim)   # compute once, not twice
            if val and top and val not in top:
                misses.append(dim)
        return misses

    critical_misses = check(critical)
    soft_misses = check(soft)
    return ConformanceReport(
        critical_misses=critical_misses,
        soft_misses=soft_misses,
        corpus_n=corpus_n,
        is_conformant=len(critical_misses) == 0,
        explanation=(
            f"Conformant against {corpus_n} CB questions"
            if not critical_misses
            else f"Fails on: {', '.join(critical_misses)} (corpus n={corpus_n})"
        ),
    )
```

### `should_rerun(report: DriftReport, conformance: ConformanceReport, attempt: int) -> bool`

Returns True if (`report.is_critical` OR NOT `conformance.is_conformant`) and `attempt < 3`.

**Corpus bypass interaction:** When corpus is too small (`corpus_n < 5`),
`corpus_conformance_score()` returns `is_conformant=True`. This means the rerun
decision falls entirely on `report.is_critical` (drift from target constraints).
This is intentional — during early corpus building, drift is still enforced but
conformance is not. The implementer must NOT treat the bypass as "skip all gating."

---

## Task 5 — `app/pipeline/generate.py`

### `create_generation_run(...) -> uuid.UUID`

Validates template `constraint_schema.required` fields are present in
`target_constraints` before creating the run. Returns clear error messages
per missing field.

### `select_seed_question(pool, seed_question_ids, target_constraints) -> uuid.UUID`

**Vector similarity seed selection** (improvement over alpha-v4 round-robin):

1. Build a short text description of the target constraints:
   ```
   "{passage_source_type} passage, {prose_register}, {difficulty},
    {syntactic_complexity}, {lexical_tier}"
   ```
2. Embed it using the existing embeddings provider (text-embedding-3-small).
3. Query `question_embeddings` (embedding_type = `'taxonomy_summary'`) with
   cosine similarity against the candidate `seed_question_ids`.
4. Return the ID of the question whose taxonomy_summary embedding is closest
   to the target description.

Fallback: if no embeddings exist for the candidates, fall back to round-robin.

**Important:** Only specified `target_*` values from the run request are merged
with the seed's generation profile. Unspecified dimensions from the seed profile
are NOT silently inherited — the run's explicit constraints always win, and
unset constraints remain unset (not filled from the seed). This prevents hidden
seed-trait bleed-through.

### `process_generation_run(...)` — background loop

For each item `i` in `range(start_index, item_count)`:

```
1. seed_id = select_seed_question(pool, seed_ids, run_constraints)
2. Load seed question content + choices + generation profile from DB
3. Merge seed profile with run constraints (run wins; unspecified dims stay None)
4. Load corpus_rows for this family from v_corpus_fingerprint
5. Build system prompt from template skeleton
6. [Pre-flight] Check corpus_n for this family. If < 5, log warning but continue.
7. Attempt loop (max 3 DRIFT attempts — LLM API errors are separate):
   a. Build user prompt (grouped constraints + exemplar + IRT anchor)
   b. LLM call (temperature=0.7) → raw JSON
      LLM API error handling (timeout / rate limit / malformed JSON):
        → retry the LLM call up to 3 times with exponential backoff (1s, 2s, 4s)
        → these retries do NOT consume a drift-attempt slot
        → if all 3 LLM retries fail: mark job status='failed', break attempt loop
   c. INSERT question_ingestion_jobs row:
        content_origin = 'generated'  ← MUST be explicit; default is 'official'
        input_format   = 'generated'
        pass1_json     = <LLM generation output>  ← skip extraction step
        status         = 'annotating'             ← skip pending→extracting
        generation_run_id, seed_question_id set
   d. Run process_job() starting at Pass 2 annotation (Pass 1 already in pass1_json)
      Skip source_type/source_exam_code checks (validator.py guard, Task 12)
   e. Run detect_drift() against merged_constraints snapshot
   f. Run corpus_conformance_score() against v_corpus_fingerprint
   g. Write generation_result_jsonb to question_ingestion_jobs:
        { attempt_number, drift_report, conformance_report, model_name, provider,
          seed_question_id, target_constraints_snapshot }
      (Written for ALL outcomes including drift_failed — this is the audit trail)
   h. If not conformant OR critical drift and attempt < 3:
        mark current job status='drift_failed' (do NOT delete)
        create a new job row for the next attempt
        continue loop
      If not conformant on attempt 3:
        mark job status='conformance_failed'
   i. On success: generation_result_jsonb already contains the full record
      (conformance_report + drift_report + constraint snapshot + model).
      Do NOT write to generation_params_snapshot_jsonb on question_ingestion_jobs
      — that column does not exist on this table (it lives on generated_questions,
      migration 035). At approval time, upsert.py copies generation_result_jsonb
      into generated_questions.generation_params_snapshot_jsonb.
8. After all items:
   - Count items where final attempt status is NOT drift_failed/conformance_failed
   - If all items failed: set generation_runs.status = 'failed'
   - If some items failed: set generation_runs.status = 'partial_complete'
   - If all items succeeded: set generation_runs.status = 'complete'
```

**One JSONB column on `question_ingestion_jobs`, one on `generated_questions`:**
- `generation_result_jsonb` (on `question_ingestion_jobs`) — written for every
  attempt including drift_failed/conformance_failed. Contains: conformance_report,
  drift_report, attempt_number, model_name, provider, seed_question_id,
  target_constraints_snapshot. Used by `/generate/runs/{run_id}/jobs` and drift
  endpoint. This is the single audit column on staging rows.
- `generation_params_snapshot_jsonb` (on `generated_questions`, migration 035,
  post-approval only) — written by upsert.py at approval time by copying
  `generation_result_jsonb` from the approved staging job. Never written to
  `question_ingestion_jobs` — that column does not exist there.

---

## Task 6 — `app/prompts/coaching.py` — NEW

Prompt for generating coaching annotations after a question is approved.

### `build_coaching_prompt(passage, stem, choices, correct, annotation_types)`

Asks the LLM to identify 3–5 educationally significant spans in the question.

Output contract:
```json
{
  "annotations": [
    {
      "span_field": "passage_text | prompt_text | paired_passage_text",
      "span_text": "<exact substring>",
      "annotation_type": "syntactic_trap | key_evidence | np_cluster | clause_boundary | blank_context | distractor_lure | rhetorical_move",
      "label": "<short UI label>",
      "coaching_note": "<1–3 sentence explanation>",
      "show_condition": "always | on_error | on_request"
    }
  ],
  "coaching_summary": "<2–4 sentences: why this question is hard and how to solve it>"
}
```

The `span_text` field is used to compute `span_start_char` / `span_end_char`
and `span_sentence_index` at write time (app layer finds the substring in the
relevant field's text).

---

## Task 7 — `app/pipeline/coaching.py` — NEW

### `generate_coaching_for_question(pool, settings, question_id) -> None`

Called after a question is approved (from `routers/jobs.py` approval path).

1. Load `passage_text`, `stem_text`, `question_options`, `correct_option_label`
   and existing `question_classifications` for the question.
2. Call `build_coaching_prompt()` with the question data.
3. LLM call (temperature=0.2, deterministic).
4. Parse response:
   - For each annotation: find `span_text` in the relevant field to compute
     `span_start_char`, `span_end_char`, `span_sentence_index`.
   - Write rows to `question_coaching_annotations`.
5. Write `coaching_summary` to `question_reasoning.coaching_summary`.

### `_find_span(text: str, span_text: str) -> tuple[int, int, int]`

Returns `(start_char, end_char, sentence_index)` for a substring in `text`.
- Normalize whitespace in both `text` and `span_text` before matching to handle
  line-break and spacing variants.
- `start_char` / `end_char`: `text.index(span_text)` and offset
- `sentence_index`: count sentences before `start_char` (split on `.!?`)
- On `ValueError` (substring not found after normalization):
  return `(None, None, None)` — the DB accepts this; `span_sentence_index`
  becomes the UI fallback.
- Log every null result with the question_id and span_text for monitoring.

---

## Task 8 — `app/routers/generate.py`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/generate` | Start generation run (background). Returns `GenerationRunCreated` with optional `warning: "corpus_too_small"` if fewer than 5 approved official questions exist for the template's family. Run still proceeds — caller is explicitly informed. |
| `GET` | `/generate/runs` | List runs (filter by status, limit/offset). |
| `GET` | `/generate/runs/{run_id}` | Run detail. |
| `GET` | `/generate/runs/{run_id}/questions` | Generated questions for a run (post-approval). |
| `GET` | `/generate/runs/{run_id}/jobs` | Staging jobs for a run (pre-approval review). Queries `question_ingestion_jobs` filtered by `generation_run_id`. Returns status, pass1_json summary, conformance_report from snapshot. |
| `GET` | `/generate/templates` | Active templates with `constraint_schema`. |
| `PATCH` | `/generate/questions/{id}/status` | Review an already-approved generated question record. |
| `GET` | `/generate/runs/{run_id}/drift` | Drift + conformance report for a run. |

**The drift endpoint uses a dual-source query — not just `v_generation_traceability`:**
- `v_generation_traceability` (migration 035) only has rows for approved questions.
  It is used for post-approval drift analysis (items that made it through).
- `question_ingestion_jobs` filtered by `generation_run_id` covers all attempts
  including `drift_failed` and `conformance_failed` rows — the cases that matter
  most for prompt calibration.

The endpoint merges both: read `generation_result_jsonb` from all staging jobs
for the run (pre- and post-approval), then join `v_generation_traceability` for
any rows that were approved. Return the combined drift + conformance picture.

**Review state machine:** All pre-approval review lives on `PATCH /jobs/{id}/status`.
`PATCH /generate/questions/{id}/status` is post-approval only (operates on
`generated_questions` rows that already reference a committed `questions` row).

---

## Task 9 — `app/models/payload.py` additions

```python
class GenerationRequest(BaseModel):
    seed_question_ids: list[uuid.UUID]   # 1–5 seeds
    template_id: uuid.UUID
    item_count: int = Field(default=1, ge=1, le=20)
    target_constraints: dict = {}
    llm_provider: str | None = None
    llm_model: str | None = None
    run_notes: str | None = None

class GenerationRunCreated(BaseModel):
    run_id: uuid.UUID
    warning: str | None = None          # "corpus_too_small" if corpus_n < 5
    warning_detail: str | None = None   # human-readable explanation

class GenerationRunRead(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID | None
    template_code: str | None
    model_name: str
    status: str
    item_count: int | None
    seed_question_ids: list[uuid.UUID] | None
    target_constraints: dict | None
    run_notes: str | None
    created_at: datetime
    updated_at: datetime

class GeneratedQuestionRead(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID | None
    question_id: uuid.UUID
    seed_question_id: uuid.UUID | None
    generation_rank: int | None
    review_status: str
    review_notes: str | None
    realism_score: float | None
    generation_params_snapshot_jsonb: dict | None
    generation_model_name: str | None
    generation_provider: str | None
    approved_by: str | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

class GeneratedQuestionStatusUpdate(BaseModel):
    review_status: str
    review_notes: str | None = None
    realism_score: float | None = None
    approved_by: str | None = None
```

---

## Task 10 — Hook into approval path (`app/routers/jobs.py`)

When `PATCH /jobs/{id}/status` sets status to `'approved'` for a generated job:

1. **content_origin + source_type transition:** Before upserting to `questions`:
   - Set `content_origin = 'ai_human_revised'` (not `'generated'`). Migration 036
     constrains `questions.content_origin` to disallow `'generated'`.
   - Set `source_type = 'generated'`. Migration 036's `chk_source_origin_consistency`
     requires `source_type = 'generated'` when `content_origin = 'ai_human_revised'`.
     If `pass1_json.source_type` is null or `'official'` (possible if the LLM ignored
     the null rule), the constraint fires. `upsert.py` must override `source_type`
     for generated jobs regardless of what `pass1_json` contains.
   These are two one-line overrides in `upsert.py` when `job.content_origin == 'generated'`.

2. **IRT refresh:** `SELECT public.fn_refresh_irt_b('<question_id>'::uuid)`
   Note: `fn_refresh_irt_b` (migration 033) only updates rows where
   `irt_b_rubric_version IN ('v1', NULL)` AND `inference_distance_key IS NOT NULL`.
   A generated question missing `inference_distance_key` in `question_classifications`
   will silently get 0 IRT updates. This is not an error — log the 0-row result
   but do not fail the approval. `TestApprovalHooks` must cover this case.

3. **Corpus fingerprint refresh:** `await conn.execute("SELECT public.fn_refresh_corpus_fingerprint()")`
   — called from the app layer only. **No DB trigger.** The trigger would fire on
   `questions.review_status` which does not exist on that table (it lives on
   `generated_questions`). App-layer call here is the single refresh point.

4. **Coaching generation:** `generate_coaching_for_question(pool, settings, question_id)`
   — run as a `BackgroundTask` so approval returns immediately

All are fire-and-forget background tasks after the initial `content_origin`
rewrite (which must happen synchronously before the upsert). The corpus
fingerprint refresh ensures the next generation run sees the newly approved
question as ground truth immediately.

---

## Task 11 — `app/main.py`

Register the generate router:
```python
from app.routers import generate
app.include_router(generate.router, prefix="/generate", tags=["generation"])
```

---

## Task 12 — `app/pipeline/validator.py`

Add two guards for jobs where `content_origin = 'generated'`:
1. Skip `source_type` / `source_exam_code` / `source_module_code` / `source_question_number`
   validation — these are null by design for generated jobs.
2. Override `source_type = 'generated'` before any upsert call. This satisfies
   migration 036's `chk_source_origin_consistency` constraint regardless of what
   the LLM put in `pass1_json.source_type`.

---

## Task 13 — Tests

### `tests/test_generation.py`

| Test class | Coverage |
|------------|---------|
| `TestBuildGenerationPrompt` | Grouped constraint rendering, empty groups omitted, IRT anchor included when present, seed exemplar formatting |
| `TestCorpusConformance` | Conformant case passes; critical miss triggers rerun; SEC family: grammar_focus_key and grammar_role_key are critical; small corpus (<5) bypasses gate; soft miss logged but not rejected |
| `TestSelectSeedQuestion` | Vector path returns closest match; fallback to round-robin when no embeddings; unspecified seed dims not inherited |
| `TestDriftDetection` | Critical drift detected (incl. evidence_distribution, blank_position, grammar_focus for SEC), soft drift tolerated, rerun logic, drift report summary |
| `TestCreateGenerationRun` | Template validation, seed validation, missing required constraints rejected |
| `TestProcessGenerationRun` | Happy path (1 item, no drift, conformant); rerun on drift (attempt 2 succeeds); drift-failed job row preserved (not deleted); attempt-3 terminal failure → conformance_failed status; all items failed → run status='failed'; some failed → 'partial_complete' |
| `TestContentOriginTransition` | Approval of generated job writes content_origin='ai_human_revised' to questions, not 'generated'; job row created with explicit content_origin='generated' (not relying on default) |
| `TestPreApprovalReadPath` | GET /generate/runs/{run_id}/jobs returns all staging job rows including drift_failed ones with generation_result_jsonb data |
| `TestLLMAPIErrorHandling` | LLM timeout retried 3x with backoff, does not consume drift attempt; all LLM retries exhausted → job status='failed'; malformed JSON treated same as timeout |
| `TestPass1JsonFlow` | Generated job row has pass1_json=<LLM output>, input_format='generated', status starts at 'annotating'; process_job() skips extraction step |
| `TestCorpusPreflightWarning` | POST /generate returns warning field when corpus_n < 5 for family; run still created; warning absent when corpus >= 5 |
| `TestDriftEndpointDualSource` | Drift endpoint returns pre-approval drift_failed rows from question_ingestion_jobs AND post-approval rows from v_generation_traceability; zero-approval edge case (all attempts drift_failed): endpoint returns non-empty from jobs table, empty from traceability view — not 404 |
| `TestSourceTypeOverride` | Approval of generated job always writes source_type='generated' to questions regardless of pass1_json.source_type value; satisfies chk_source_origin_consistency |
| `TestIRTRefreshSilentSkip` | Approval hook: fn_refresh_irt_b returns 0 when inference_distance_key is NULL; approval still succeeds; 0-row result is logged not raised |
| `TestCoachingGeneration` | Span finding with whitespace normalization, DB writes, None handling for unfound spans, null logging |
| `TestGenerateEndpoint` | POST /generate returns 200 with run_id, background task registered, GET /runs, PATCH /generate/questions/{id}/status (post-approval only) |
| `TestApprovalHooks` | content_origin rewritten before upsert; IRT refresh called; corpus fingerprint refresh called (app layer, no trigger); coaching generation triggered as background task |

### `tests/test_drift.py`

Unit tests for `DriftReport`, `ConformanceReport`, `compute_expected_fingerprint`,
`detect_drift`, `corpus_conformance_score`, `should_rerun` — no DB, no LLM.

---

## Task 14 — End-to-end smoke test

After implementation:

```bash
# 1. Apply migrations
supabase db push  # runs 042_corpus_fingerprint.sql

# 2. Confirm template seeded (already done by 038)
GET /generate/templates  → should return 9 templates

# 3. Confirm corpus fingerprint has data (requires at least 5 approved official questions)
SELECT question_family_key, COUNT(*), SUM(n) FROM v_corpus_fingerprint GROUP BY 1;

# 4. Run generation
POST /generate
  { "seed_question_ids": ["<real-uuid>"], "template_id": "<words_in_context_v1>", "item_count": 1 }

# 5. Poll until complete
GET /generate/runs/{run_id}  → status = 'complete'

# 6. Inspect staging job via jobs endpoint
GET /generate/runs/{run_id}/jobs
# Confirm: returns all staging job rows for the run
# Confirm: each row has generation_result_jsonb with conformance_report and drift_report
# Confirm: content_origin='generated', generation_run_id set, seed_question_id set

# 6a. For any drift_failed attempts: confirm row preserved with status='drift_failed'
SELECT id, status, generation_result_jsonb->>'attempt_number' as attempt
FROM question_ingestion_jobs WHERE generation_run_id = '<run_id>'
ORDER BY created_at;

# 7. Approve (creates generated_questions row)
PATCH /jobs/{job_id}/status  { "status": "approved" }

# 8. Confirm IRT
SELECT irt_b_estimate, irt_b_rubric_version FROM question_classifications
WHERE question_id = '<new_question_id>'
-- expect: irt_b_estimate IS NOT NULL, irt_b_rubric_version = 'v1'
-- NOTE: if inference_distance_key was NULL in question_classifications, IRT
-- refresh silently returns 0 rows updated. Check the log for the 0-row result.

# 9. Confirm coaching
SELECT * FROM question_coaching_annotations WHERE question_id = '<new_question_id>'
-- expect: 3–5 rows with span data

# 10. Check drift + conformance report
GET /generate/runs/{run_id}/drift
-- expect: empty if generation matched targets and corpus norms

# 11. Check traceability view
SELECT * FROM v_generation_traceability WHERE run_id = '<run_id>'

# 12. Confirm corpus fingerprint refreshed
SELECT * FROM v_corpus_fingerprint WHERE question_family_key = 'words_in_context'
-- should include the newly approved question
```

---

## Ground Truth: How the Quality Gate Works

### The Problem with a Subjective Judge

The original design called for a second LLM call that rates the generated
question on a 0–1 realism scale. This is weak for three reasons:

1. **No calibration baseline** — thresholds like 0.75 or 0.80 are arbitrary.
   There is no dataset of known-good and known-bad questions to tune against.
2. **Shared blind spots** — if the generator and the judge are the same model
   family, they share systematic biases. The judge will approve what the
   generator thinks is good, not what the College Board thinks is good.
3. **Not auditable** — "realism_score: 0.82" is uninterpretable. You cannot
   explain why a question passed or failed, or improve prompts based on failures.

### The Solution: Corpus-Grounded Conformance

**The ingested official College Board questions are the ground truth.**

When Pass 2 annotates an official CB question during ingestion, it produces a
full fingerprint stored in `question_classifications`:
- `syntactic_complexity_key` — how complex is the sentence structure?
- `prose_register_key` — academic, journalistic, literary, etc.?
- `lexical_tier_key` — what vocabulary tier does this passage operate at?
- `rhetorical_structure_key` — argument, narrative, expository, etc.?
- `epistemic_stance_key` — how does the author signal certainty or hedging?
- `evidence_distribution_key` — where in the passage is the evidence?
- `inference_distance_key` — how far does the student need to reach?
- `blank_position_key` — where does the blank fall structurally?
- `difficulty_overall` — easy / medium / hard

These annotations, accumulated across all approved official questions, form the
**empirical distribution of what a real DSAT question looks like** per question
family (`words_in_context`, `transitions`, `conventions_grammar`, etc.).

The `v_corpus_fingerprint` materialized view aggregates this distribution
and makes it queryable in milliseconds.

### Evidence Carry-Through from Ingested Text

The key insight is that **the same Pass 2 prompt and annotation schema runs on
both official questions and generated questions**. This means:

- Official question fingerprints = ground truth labels
- Generated question fingerprints = measurements
- Conformance = measurement falls within the observed range of ground truth labels

No additional LLM call is needed. The Pass 2 annotation that already runs as
part of the generation pipeline produces the measurement. The comparison is
done in Python against the pre-computed corpus view.

### How the Gate Works at Runtime

```
Official CB question ingested
    → Pass 2 annotation runs
    → Fingerprint written to question_classifications
    → Human approves
    → fn_refresh_corpus_fingerprint() called
    → v_corpus_fingerprint updated

Generated question produced
    → Pass 1 generates text
    → Pass 2 annotation runs (same prompt, same schema)
    → corpus_conformance_score() called:
        for each critical dimension:
            is the annotated value in the top-3 modal values
            for this question family in the approved corpus?
    → If all critical dimensions conform → stage for human review
    → If any critical dimension misses → mark drift_failed, retry
    → On attempt 3 failure → mark conformance_failed, log explanation
```

### Graceful Degradation

When the corpus for a given question family has fewer than 5 approved official
questions, the gate is bypassed automatically and the item is staged without
conformance checking. A warning is logged. This allows the system to function
during early corpus building (before enough CB questions have been ingested)
while becoming progressively stricter as the corpus grows.

**Bootstrap path:** Ingest at least 5 approved official questions per family
before generating for that family. The corpus currently needs growth in
`data_integration_graph` and `data_integration_table` families particularly.

### Threshold Tuning

The `top_n=3` default means "accept if your annotated value is one of the three
most common values for this dimension in the approved corpus." This can be tuned
per family or per dimension without changing schema — just the Python constant.

As the corpus grows, `top_n` can be tightened (lower = stricter) or a minimum
frequency threshold (e.g., "value must appear in ≥10% of corpus rows") can be
added to `corpus_conformance_score()` without any migration.

### What This Enables Long-Term

- **Prompt calibration with receipts** — when `conformance_failed` items appear,
  the explanation field shows exactly which dimensions failed and how many CB
  questions set the norm. Prompts can be tuned to address specific misses.
- **Family-specific drift analysis** — `v_generation_traceability` + conformance
  reports give a per-family view of which constraint dimensions the generator
  struggles with, enabling targeted template improvements.
- **LoRA fine-tuning signal** — at 200+ approved official questions, the corpus
  fingerprint becomes strong enough to use as a training signal for a LoRA
  adapter on Pass 2, improving annotation consistency and reducing lookup
  hallucinations (see `TASKS.md` Future section).

---

## Deferred: Known Gaps for v2

These issues were identified in adversarial review and are deliberately deferred.
Each is documented here so they are not forgotten. None blocks v1 implementation.

### D1 — Joint Fingerprint Conformance (deferred to 200+ corpus)

**The problem:** `corpus_conformance_score()` checks each dimension
independently. A generated item can pass with a combination of dimension values
that never co-occurs in the approved CB corpus — e.g., `academic` register +
`low` difficulty + `argument` rhetoric is individually common but may not exist
as a joint pattern in the corpus. The per-dimension modal check misses this.

**Why deferred:** With fewer than 50 approved questions per family, the joint
distribution is too sparse to gate against. Joint checking on a sparse corpus
would produce excessive false-rejects that have nothing to do with quality.

**v2 trigger:** When any family reaches 50+ approved official questions, add a
joint neighborhood check: require that the generated item's full fingerprint
falls within cosine distance `d` of at least one existing corpus fingerprint
row. The threshold `d` and the neighborhood size are tunable constants.

**Implementation note:** The materialized view already stores the full
cross-product rows — the query infrastructure is ready. Only the Python-side
check in `corpus_conformance_score()` needs the new logic.

### D2 — Pass 3 (Tokenization) Feeding Generation QA

**The problem:** Pass 3 tokenization currently only runs post-approval. For
grammar question generation, the tokenized structure (blank position, grammar
tag distribution, clause boundaries) would be a powerful QA signal *before*
staging — it could verify that the generated item actually instantiates the
targeted grammar rule at the token level.

**Why deferred:** Pass 3 is computationally expensive (another LLM call), and
the current pipeline has no pre-staging hook for it. Wiring it in would require
a new pipeline stage between Pass 2 and conformance checking.

**v2 trigger:** Once `conventions_grammar` generation is in use and producing
items at volume, add an optional `run_pass3_before_staging: bool` flag on
`GenerationRequest`. When true, run a lightweight grammar-tag check on the
generated text and compare the blank's grammar tag against `target_grammar_focus_key`
before conformance scoring.

~~D3 — removed.~~ `GET /generate/runs/{run_id}/jobs` is a v1 Task 8 deliverable,
not deferred. See Task 14 smoke test step 6a which verifies this endpoint returns
`generation_result_jsonb` data including conformance_report for all staging jobs.
