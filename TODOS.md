# TODOS

## Priority Ingestion Fixes

### 1. Retry official extraction shortfalls before annotation

**Status:** partially mitigated, still operationally expensive.

Official module completeness now routes short modules to `needs_review`, but the
check happens after annotation and persistence. A 27/33 extraction still spends
annotation work on an incomplete module before reporting the shortfall.

**Fix:**

- After `_normalize_extracted_questions`, compare extracted count to the known
  official module expected count.
- If count is low, retry Pass 1 with a corrective prompt before annotation.
- Store missing expected question numbers in `validation_errors_jsonb`.
- Keep final `module_completeness` review routing as the safety net.

### 2. Normalize amendment proposal aliases

**Status:** code-confirmed gap from ingestion runs.

The annotator can emit amendment fields like `skill_family` or
`distractor_type_key (option-level)`. Current amendment capture expects clean
ontology vocabulary names or known `affected_field` names, so useful proposals
become warnings instead of pending amendment files.

**Fix:**

- Strip parenthetical suffixes from amendment proposal vocab fields.
- Map common aliases:
  - `skill_family` -> `READING_SKILL_FAMILY_KEYS`
  - `distractor_type_key` -> `DISTRACTOR_TYPE_KEYS`
- Add tests for both observed warning cases.

### 3. Share annotation retry logic with reannotation

**Status:** code-confirmed inconsistency.

Normal ingest retries annotation JSON parse failures once. Reannotation performs
one annotation call and marks the job failed on parse errors.

**Fix:**

- Extract a shared `annotate_with_retry()` helper.
- Use it from both normal ingest and `_run_reannotate_pipeline`.
- Preserve existing metadata capture and `enforce_nullability` behavior.

### 4. Tighten OCR fallback model routing

**Status:** operational risk.

The OCR fallback chain can still reach a generic `ollama` VLM path
(`qwen3-vl:235b-instruct-cloud`) for PDF OCR. Prior runs showed this path can
fail on large or complex official pages.

**Fix:**

- Separate document-OCR-capable models from generic vision models.
- Prefer `glm` / `deepseek` style document OCR fallbacks for PDFs.
- Block generic VLM fallback for large multi-page PDFs unless explicitly
  requested.
- Record the final resolved fallback chain in job metadata for auditability.

### 5. Resolve runner and pipeline timeout conflict

**Status:** operational conflict.

The ingestion test runner polls for 30 minutes, but `pipeline_timeout_s` is 3
hours. If the runner starts the API server itself, cleanup can stop an in-process
background ingestion while the job is still `annotating`.

**Fix:**

- Align runner polling duration with `pipeline_timeout_s`, or
- Leave self-started servers alive until the job reaches a terminal status, or
- Move long-running ingestion execution out of process so server cleanup cannot
  kill the active job.

## OCR Stimulus Detection

### Harden stimulus detection matcher and layout prompt

**Status:** still open; blocked by `TASKS_OCR_IMAGE.md` Phase 0/1 evidence.

**What:** Improve `match_stimulus_regions_for_question` heuristics and the
`detect_layout` prompt so fewer chart/table/figure stimuli fail to attach to a
question in the first place.

**Why:** `TASKS_OCR_IMAGE.md` builds a backfill workflow that recovers failed
stimuli but does not reduce failures. Two of the three failure classes trace
straight to detection quality: Class B (region never detected by
`detect_layout`) and Class C (region detected but `match_stimulus_regions_for_question`
attached it to no question). Recovering a failure is more expensive than not
producing it.

**Pros:** Fewer sentinel rows, fewer `needs_review` jobs, less backfill work,
less paid re-OCR spend. Prevention scales better than recovery.

**Cons:** Layout/matcher tuning is empirical; risk of over-tightening (false
negatives) or over-loosening (false positives). No quick win guaranteed.

**Context:** Matcher heuristics live in `backend/app/storage/crop_detector.py`
(`match_stimulus_regions_for_question`, spatial thresholds `near_below`,
`near_above`, center-alignment). The layout prompt is
`backend/app/prompts/layout_prompt.py`.

**Depends on / blocked by:**

- `TASKS_OCR_IMAGE.md` Phase 0: sentinel/observable skip markers.
- `TASKS_OCR_IMAGE.md` Phase 1: flag-scan data showing whether Class B or
  Class C dominates.

## Lower-Priority Architecture Cleanup

- Reduce `backend/app/routers/ingest.py` ownership breadth: intake, OCR,
  extraction, annotation, validation, enrichment, persistence, and finalization
  currently live in one large module.
- Route status transitions through `JobOrchestrator` instead of direct persisted
  assignments.
- Replace untyped `pass1_json` / `pass2_json` handoff shapes with typed internal
  contracts.
- Separate enrichment and YAML export side effects from core DB persistence.
- Improve startup recovery: interrupted in-process background jobs are currently
  marked failed rather than resumed.

## Already Addressed Or Stale Debug-Log Items

- Unofficial non-PDF ingest crash from `pdf_result` leaking outside the PDF
  branch.
- Duplicate checksum retry for terminal partial official jobs.
- Official module completeness routing to `needs_review`.
- `{ "question": {...} }` JSON envelope unwrapping.
- 2024 PDF path fallback in `.claude/skills/ingestion-test/run.sh`.
- Nullable and fallback `correct_option_label` handling.
