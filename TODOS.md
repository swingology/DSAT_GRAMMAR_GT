# TODOS

## Priority Ingestion Fixes

### 1. Resolve runner and pipeline timeout conflict

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

- PDF OCR fallback now defaults to document-OCR strategies and records the
  resolved fallback chain; generic VLM PDF fallback requires an explicit flag.
- Reannotation now shares the normal ingest annotation retry helper for
  malformed or empty JSON responses.
- Amendment proposal aliases now normalize observed `skill_family` and
  parenthetical vocab-field forms before schema validation.
- Unofficial non-PDF ingest crash from `pdf_result` leaking outside the PDF
  branch.
- Official extraction shortfalls now retry before annotation when subject/module
  metadata gives a known expected question count.
- Duplicate checksum retry for terminal partial official jobs.
- Official module completeness routing to `needs_review`.
- `{ "question": {...} }` JSON envelope unwrapping.
- 2024 PDF path fallback in `.claude/skills/ingestion-test/run.sh`.
- Nullable and fallback `correct_option_label` handling.
