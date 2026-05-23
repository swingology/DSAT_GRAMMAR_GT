# OCR Stimulus Backfill Task List

## Goal

Make skipped chart / graph / table stimuli **observable**, **re-processable**,
and **linkable** — on demand, without needing the original PDF.

Today, layout detection and stimulus annotation are enrichment steps that
"degrade gracefully" — any failure returns an empty result and never raises.
The consequence is a **silent skip**: a chart that fails to crop or annotate
simply produces no `QuestionStimulusAsset` row, with no record that anything
was missed. This feature adds a flag → re-OCR → link workflow so missing
stimuli can be recovered on demand.

## Preconditions / Scope

- The app is in **alpha**. This feature is built first, then the official PDFs
  are re-ingested with Phase 0 in place. Every job the feature operates on is
  therefore ingested **after** Phase 0 exists.
- Because of that, every Class A failure already has a sentinel row written at
  ingest time. There is **no historical-reconstruction path** — the feature
  does not attempt to re-derive failures from raw `ocr_layout` JSON for jobs
  ingested before Phase 0. Pre-Phase-0 jobs are out of scope; the re-ingest is
  the enforcement.

## Existing Foundation

- `app/storage/crop_detector.py` — `detect_layout`, `match_region_for_question`,
  `match_stimulus_regions_for_question`, `crop_and_store`. All degrade
  gracefully (return empty, never raise).
- `app/prompts/layout_prompt.py` — classifies page regions as `question_block`,
  `table`, `chart`, `figure`.
- `app/prompts/stimulus_prompt.py` — vision prompt producing `structured_data`
  (table rows, bar/line series, pie slices, scatter points, figure
  description) + `render_hints` (chart_type, axis labels).
- `ingest.py::_annotate_layout_stimulus` — vision-annotates one crop.
- `ingest.py::_build_stimulus_asset_rows` — persists `QuestionStimulusAsset`.
- Page renders are persisted in the object store (`page-renders`).
- Layout JSON is persisted per page via `put_object("ocr_layout", ...)`,
  including the bounding box of every detected `table`/`chart`/`figure`.
- `QuestionStimulusAsset` columns: `question_id`, `question_job_id`,
  `raw_asset_id`, `stimulus_type`, `storage_path`, `source_page_number`,
  `source_span_id`, `title`, `structured_data_jsonb`, `render_hints_jsonb`,
  `created_at`. **There is no unique constraint** — backfill must dedup itself.
- `validator.py` flags `command_of_evidence_quantitative` questions missing
  graphic data; the Phase 6 consistency scanner reports
  `quantitative_missing_graphic_data`.
- Config: `layout_detection_enabled=True`, `glm_ocr_model="glm-ocr:latest"`
  (Anthropic vision fallback).

## Target Flow

```text
completed ingestion job
  -> stimulus skip is recorded (no longer silent)
  -> flag scan: questions with an unconsumed table/chart/figure
  -> re-OCR: re-crop known region OR re-detect layout
  -> vision-annotate the crop (structured_data + render_hints)
  -> idempotent link: write/update QuestionStimulusAsset
  -> mark the question's stimulus state resolved
```

## Two Classes of Skip

- **Class A — detected, not annotated.** Layout found the region; crop or
  vision annotation failed. The bounding box is already in stored layout JSON.
  Fully recoverable without re-detection.
- **Class B — never detected.** Layout detection itself missed the region.
  No region in layout JSON. Recoverable only via a fresh `detect_layout` run
  or a human flag; the only existing signal is the validator / Phase 6 scanner
  "missing graphic data" finding.

## Design Decisions

- Stimulus processing stays **enrichment, never a gate** — ingestion still
  succeeds without stimuli. This feature does not change that; it makes the
  gap *visible* and *recoverable*.
- A failed or skipped stimulus must leave a durable, queryable marker. Silent
  skips are the root problem and are removed in Phase 0.
- Backfill must be **idempotent** — safe to re-run, no duplicate
  `QuestionStimulusAsset` rows (the table has no unique constraint).
- Backfill links assets to `question_id` directly (the model already FKs
  `questions`, not `question_versions`), so no new question version is created.
- Re-OCR must not require the original PDF — it works from persisted page
  renders and layout JSON.
- Deployment workflow is admin API-first; a dev CLI mirrors it and shares the
  same backfill library code.

## Phase 0: Make Skips Observable

**Goal:** Replace the silent skip with a durable marker before building any
recovery tooling.

**Marker mechanism (decided): a sentinel `QuestionStimulusAsset` row.**
A failed Class A stimulus is recorded as a real `QuestionStimulusAsset` row
with `structured_data_jsonb = NULL` and a reserved `stimulus_type`
(`failed_detection` or `failed_annotation`). Chosen over a `stimulus_status`
column because:

- No migration — the table already has every column needed.
- Per-region granularity — a question can have one extracted table and one
  failed chart; a single status column cannot represent that.
- The marker doubles as the Phase 2 work-order: the bbox, page, region type,
  and any partial crop path are stored on the row itself, so re-OCR needs no
  layout-JSON re-scan.

The failed row carries its backfill payload in `render_hints_jsonb`:

```jsonc
{
  "backfill": {
    "reason": "vision annotation returned empty",
    "region_type": "chart",
    "bbox": [120, 880, 540, 1180],
    "page_index": 3,
    "layout_json_path": "page_layout/...",
    "crop_path": "stimulus-assets/...",   // present only if crop succeeded
    // failure stage drives the Phase 2 backfill tier:
    //   "failed_annotation"  -> crop exists, re-annotate the crop only
    //   "failed_detection"   -> see crop_failure_reason below
    "crop_failure_reason": null           // null for failed_annotation; one of
                                          // "unreadable_page" | "missing_page"
                                          // | "degenerate_bbox" for failed_detection
  }
}
```

`storage_path` is currently `NOT NULL`. Phase 0 makes it nullable (one-column
migration) so a sentinel row sets `storage_path = NULL` honestly — a sentinel
has no crop. Real artifact paths still live in `render_hints_jsonb.backfill`
(`crop_path`, `layout_json_path`). The column stops meaning two things.

**Class B (never detected) is NOT given a sentinel row** — there is no region
to attach one to. Class B stays question-level and reuses the existing
validator signal in `validation_errors_jsonb`.

- [ ] Define the reserved `stimulus_type` values `failed_detection` and
  `failed_annotation`, and the `render_hints_jsonb.backfill` payload shape.
- [ ] **Dependency: `crop_and_store` must return a failure reason.** It
  currently returns a bare `None` on every failure path. Change it to return a
  structured result carrying the reason (`degenerate_bbox` / `unreadable_page`
  / `missing_page` / `pil_error`) so Phase 0 can populate `crop_failure_reason`
  — without it, the Phase 2 tier table has no input. This is a `crop_detector`
  change and a hard prerequisite for the tiered backfill.
- [ ] Write a sentinel row at the failure points below, after the matcher has
  accepted a region:
  - `crop_and_store` fails → **`failed_detection`** sentinel, with the returned
    reason in `crop_failure_reason`.
  - crop succeeds but `_annotate_layout_stimulus` yields no usable data —
    either `{}` (call raised / non-dict JSON) **or a parsed dict whose
    `structured_data` is null/empty** → **`failed_annotation`** sentinel. The
    rule is "no usable structured data," not the literal `== {}`, so a
    parsed-but-empty annotation cannot escape into a non-live, non-flagged row.
- [ ] A crop + annotation that produce real `structured_data` is a **real
  row**. (A genuinely thin but non-empty annotation — e.g. a short figure
  description — is still a real row and out of scope for review.)
- [ ] **Third failure class — detected-but-unmatched.** A `table`/`chart`/
  `figure` region that `detect_layout` found but `match_stimulus_regions_for_
  question` attached to no question produces no sentinel (no question to hang
  it on) and no Class B signal. Phase 0 records these as a job-level warning in
  `validation_errors_jsonb` (like the Class B signal) so they are queryable and
  not silent. Phase 1 surfaces them in the report.
- [ ] Region validity stays the matcher's responsibility. Phase 0 adds no
  "is this really a chart" judgment; a wrongly-matched region is a
  `crop_detector` matcher bug, not something the sentinel layer masks.
- [ ] Migration: make `QuestionStimulusAsset.storage_path` nullable; sentinel
  rows write `storage_path = NULL`.
- [ ] Ensure sentinel rows never reach downstream consumers as real stimuli —
  see the shared `is_live` predicate in Phase 3. Today only `yaml_export.py`
  reads stimulus assets; the student/questions routers return only
  `stimulus_mode_key` and gain the filter when they start serving stimulus.
- [ ] If any sentinel row was written for a job, ingest finalization sets
  `job.status = needs_review` instead of `approved`, so failed stimuli surface
  in the existing admin job queue (no new status value).
- [ ] Confirm the Class B signal is queryable: the validator
  `command_of_evidence_quantitative` "missing graphic data" result already
  lands in `validation_errors_jsonb` — no new storage needed.
- [ ] One Phase 0 migration: `storage_path` nullable. `stimulus_type`
  (`String(40)`) and the nullable `structured_data_jsonb` / `render_hints_jsonb`
  columns are already sufficient for the rest.
- [ ] Add tests proving a crop failure and an annotation failure each write a
  sentinel row, that `storage_path` is `NULL` on a sentinel, and that sentinel
  rows are excluded from downstream stimulus reads.
- [ ] Add a test that a job with a sentinel row finalizes as `needs_review`,
  and a job with no sentinel still finalizes as `approved`.
- [ ] **REGRESSION (critical):** ingest finalization behavior changes — a job
  that previously landed `approved` with a silently-skipped stimulus now lands
  `needs_review`. Audit existing `job.status == "approved"` assertions in
  `test_pipeline.py` / `test_ingest_router.py`; update any whose fixture has a
  failing stimulus, and pin the new approved-vs-needs_review boundary with a
  regression test.

**Exit criteria:** Every skipped or failed Class A stimulus is a queryable
sentinel row; Class B is queryable via the validator signal; no skip is silent
and no sentinel row leaks to consumers.

## Phase 0.5: Extract Shared Stimulus Module

**Goal:** Refactor first, so the backfill engine reuses real OCR logic instead
of importing a router's private internals. Behavior-preserving — no feature
change in this phase.

The functions Phase 2–3 must reuse — `_annotate_layout_stimulus` and
`_build_stimulus_asset_rows` — are `_`-prefixed private helpers inside the
~2,700-line `app/routers/ingest.py`. A new pipeline module importing a router's
privates is a coupling smell and an import-cycle risk.

- [ ] Create `app/pipeline/stimulus.py` and move `_annotate_layout_stimulus`,
  `_build_stimulus_asset_rows`, and shared crop/region helpers into it.
- [ ] **`_build_stimulus_asset_rows` is not cleanly extractable as-is** — it
  takes a `QuestionJob` and reads `q_data["stimulus_assets"]` populated by the
  inline enrichment loop in `_persist_question`. Extraction must generalize its
  input to a plain shape (region + crop path + annotation + page/span ids) that
  *both* ingest and backfill can construct. This is real work, not a move; the
  ingest call site adapts to the new signature.
- [ ] `ingest.py` calls the new module; ingest behavior is unchanged.
- [ ] The new `region_key()` helper (Phase 3) also lives here, as the single
  shared implementation.
- [ ] Run the existing ingest/pipeline tests unchanged — they must still pass,
  proving the refactor is behavior-preserving.

**Exit criteria:** Stimulus annotation and row-building are importable from
`app/pipeline/stimulus.py`; the existing test suite passes unchanged.

## Phase 1: Flag Scan

**Goal:** Produce the list of questions that need stimulus backfill — by direct
queries, no historical reconstruction (see Preconditions / Scope).

- [ ] **Class A:** query `QuestionStimulusAsset` rows with a `failed_*`
  `stimulus_type` (the Phase 0 sentinel rows). No `ocr_layout`-vs-stimulus
  diffing — the sentinel row is the record of failure.
- [ ] **Class B:** query the Phase 0 validator signal in
  `validation_errors_jsonb` (quantitative questions with no stimulus and no
  detected region).
- [ ] **Class C — detected-but-unmatched:** query the Phase 0 job-level
  warning for `table`/`chart`/`figure` regions the matcher attached to no
  question. These need a matcher fix, not a re-OCR — report them separately so
  they are visible but not mixed into the backfillable queue.
- [ ] **Unconfirmed backfills:** also report rows with
  `origin = backfilled AND review_status = unconfirmed` — these are recovered
  but not yet verified, and belong in the same review queue as missing stimuli.
- [ ] Emit a machine-readable report (JSON) for admin UI / CI use, each item
  tagged Class A / Class B / Class C / unconfirmed-backfill.
- [ ] Add tests with fixtures for: a sentinel row flagged as Class A, a real
  confirmed row not flagged, a quantitative-missing-data Class B signal, a
  detected-but-unmatched Class C warning, and an unconfirmed backfilled row.

**Exit criteria:** A repeatable scan lists exactly the questions missing
stimulus data, classified A vs B.

## Phase 2: Re-OCR Backfill Engine

**Goal:** Re-process one flagged question's stimulus from persisted artifacts.

**Scope decision:** Class B re-detection is **per-question and opt-in only** in
this phase. Whole-job / whole-exam batch re-detection is intentionally deferred
to Phase 7 (below), gated on the test results of per-question Class B — if the
layout pass cannot reliably find a chart it missed the first time, batch
re-detection would only multiply a bad result.

**Tiered re-OCR — send the minimum the failure needs.** The original PDF is
never sent; everything works from stored page renders.

| Failure | What is sent | Layout re-check |
|---|---|---|
| `failed_annotation` | the existing crop image only | no |
| `failed_detection` + `unreadable_page` / `missing_page` | re-crop from page render using the stored bbox, send the crop | no |
| `failed_detection` + `degenerate_bbox` | the bbox is untrusted → page-level layout re-check for that one page | yes (1 page) |
| Class B | full layout check — page render(s) → `detect_layout` → match | yes |

**Provider escalation.** The backfill function takes a `provider` argument.
Re-running the *same* provider that failed usually fails again, so the
documented operational default is to **escalate** — retry with a stronger
vision provider (e.g. Anthropic) than ingest used. Same-provider retry is
allowed (cheap, catches transient JSON-parse blips). Escalation to a paid
provider must be a deliberate choice, never an implicit default — especially
for batch (Phase 4).

- [ ] Implement a backfill function that, given a flagged question, dispatches
  on the tier table above (read `crop_failure_reason` from the sentinel
  payload to choose the `failed_detection` sub-tier).
- [ ] For the crop-only tiers, send just the crop to `_annotate_layout_stimulus`.
- [ ] For the layout-re-check tiers, re-run `detect_layout` for the affected
  page(s) only, then `match_stimulus_regions_for_question`.
- [ ] Accept a `provider` argument; do not hard-code the provider.
- [ ] Run `_annotate_layout_stimulus` on each crop to produce `structured_data`
  + `render_hints`.
- [ ] Return a structured result (per region: ok / failed, with reason) so
  failures are reported, not swallowed.
- [ ] Reuse `crop_detector` and the stimulus prompt — no duplicated OCR logic.
- [ ] Add tests for each tier: crop-only re-annotation, re-crop from page,
  single-page layout re-check, Class B full layout, and provider escalation.

**Exit criteria:** A single flagged question can be re-OCR'd from stored page
renders without the original PDF.

## Phase 3: Idempotent DB Linking

**Goal:** Write recovered stimulus data into the DB without duplicates.

**Dedup decision:** Application-level dedup keyed on a new `region_key` column.
A DB unique constraint cannot use the current columns —
`(question_id, stimulus_type, source_page_number)` is not unique because a
question can have two charts on the same page, and the only true
discriminator (the bounding box) lives in `render_hints_jsonb`. The fix:

**`region_key` is a dedup identity, not crop geometry — keep them separate.**

- `region_key = f"{page_index}:{region_type}:{round(cx,2)}:{round(cy,2)}"`
  where `cx, cy` is the bbox center (`x+w/2`, `y+h/2`), quantized to 2% of the
  page. It deliberately **omits width/height**: size is the jittery part of an
  LLM re-detection, so a size-blind key keeps dedup stable across re-runs.
- The full `bbox` (`x, y, w, h`) is the **crop geometry** and is stored
  separately in `render_hints_jsonb`. `crop_and_store` always receives the full
  bbox; it never sees `region_key`. So the captured region is always correct.
- When re-detection matches an existing `region_key` but draws a slightly
  different box, linking promotes the existing row **and refreshes the stored
  bbox** to the new one — correct behavior, not a duplicate.
- A single shared `region_key()` helper is used by ingest
  (`_build_stimulus_asset_rows`), Phase 0 sentinel writing, and backfill, so the
  key is computed identically everywhere.

One migration adds three nullable columns to `QuestionStimulusAsset`:

- `region_key` (`String`) — deterministic string from `page_index` + bbox (or
  the layout region's own id); the dedup key.
- `origin` (`String`) — `ingest` or `backfilled`.
- `review_status` (`String`) — `unconfirmed` / `confirmed` / `rejected`;
  `NULL` for ingest-origin rows (they are not in scope for review).

- [ ] Add the `region_key`, `origin`, `review_status` columns (one migration).
- [ ] Populate `region_key` from **both** the normal ingest path
  (`_build_stimulus_asset_rows`) and the backfill path, and on Phase 0
  sentinel rows.
- [ ] Implement linking that, on a successful re-OCR, **promotes the Phase 0
  sentinel row in place** — replacing `failed_*` `stimulus_type` with the real
  type, populating `structured_data_jsonb` / `render_hints_jsonb` / `title` /
  `storage_path`, and setting `origin = backfilled`,
  `review_status = unconfirmed` — or inserts such a row when no sentinel
  exists (Class B).
- [ ] **Always retain the crop image** for a backfilled row — it is the
  verification artifact a reviewer compares against `structured_data`.
- [ ] A backfilled row with `review_status = unconfirmed` must NOT reach
  downstream consumers as live stimulus data (same filter as sentinel rows).
- [ ] Define **one canonical `is_live` predicate** for `QuestionStimulusAsset`
  — a SQLAlchemy hybrid property (or query helper) capturing all three clauses:
  `stimulus_type NOT LIKE 'failed_%'` AND `structured_data_jsonb IS NOT NULL`
  AND `review_status IS DISTINCT FROM 'unconfirmed'`. Every consumer
  (`yaml_export.py` now, routers later) uses `is_live`; the predicate is never
  re-typed inline. Test all three boundaries: a sentinel row and an
  `unconfirmed` row are **excluded**, and an ingest-origin row with
  `review_status = NULL` is **included** (`NULL IS DISTINCT FROM 'unconfirmed'`
  must pass — confirm the ORM default is `NULL`, not `'unconfirmed'`).
- [ ] Dedup via application-level lookup `WHERE question_id = ? AND
  region_key = ?`: update the matching row, insert only when none matches.
  Backfill is low-concurrency admin work, so no race-level guarantee is needed.
- [ ] **Collision guard.** Promote-in-place overwrites the row matching a
  `region_key`. If the matched row is already a `confirmed` real stimulus whose
  stored bbox center is more than the quantization cell away from the incoming
  region, that is a genuine collision (two distinct stimuli quantized to one
  key), not a re-detection. Do not overwrite — record a collision warning and
  leave the existing row intact.
- [ ] **Terminal state.** Define when a job leaves `needs_review`: when the job
  has no remaining `failed_*` sentinel rows and no `unconfirmed` backfilled
  rows, the confirm action (or a finalization check) returns the job to
  `approved`. Without this the job is stuck in `needs_review` forever. Add a
  test for a multi-stimulus job that clears only after the last confirm.
- [ ] Defer the DB `UNIQUE(question_id, region_key)` partial index to Phase 7
  hardening — it is only safe once `region_key` is populated everywhere.
- [ ] Add tests proving re-running backfill twice does not create duplicate
  rows, that a sentinel row is promoted (not left alongside a real row), and
  that a promoted row is `origin=backfilled, review_status=unconfirmed`.

**Exit criteria:** Backfill is safe to re-run; recovered stimuli are linked
exactly once per question/region and land in `unconfirmed` review state.

## Phase 4: Admin API — DEFERRED

**Deferred (eng review, alpha):** the app has no admin UI consuming these
endpoints yet. Phases 2–3 expose the backfill workflow as shared library code,
and Phase 5's CLI drives the whole workflow (backfill / confirm / reject)
locally. Build this phase when an admin UI actually needs it; it drops in
cleanly on top of the shared library.

**Goal (when resumed):** Expose the backfill workflow through admin endpoints.

- [ ] Add admin endpoints:
  - `GET /admin/stimulus/missing` — flag-scan report (Phase 1): missing +
    unconfirmed-backfill review queue.
  - `POST /admin/stimulus/{question_id}/backfill` — run re-OCR + link for one
    question (Class A re-crop, or per-question Class B re-detection).
  - `POST /admin/stimulus/backfill` — batch backfill for a job or exam,
    **Class A only** (re-crop/re-annotate already-detected regions). Batch
    Class B re-detection is Phase 7.
  - `GET /admin/stimulus/{asset_id}` — show one backfilled stimulus: the crop
    image reference plus `structured_data` / `render_hints`, for side-by-side
    verification.
  - `POST /admin/stimulus/{asset_id}/confirm` — set `review_status=confirmed`;
    the row goes live to downstream consumers.
  - `POST /admin/stimulus/{asset_id}/reject` — reject a wrong backfill: revert
    the row to a `failed_*` sentinel (recording the rejected provider in the
    `backfill` payload) so it re-enters the flag queue and can be retried with
    a stronger provider.
- [ ] Backfill endpoints accept an optional `provider` override (Phase 2
  escalation). Batch backfill requires the provider to be stated explicitly
  when it is a paid provider — no implicit escalation to a billable model.
- [ ] Endpoints return per-region results (ok / failed + reason).
- [ ] Share the Phase 1–3 backfill library code; no policy logic in the router.
- [ ] Add API tests for missing-scan, single backfill, batch backfill, show,
  confirm, and reject.

**Exit criteria:** An admin can list missing stimuli, trigger recovery, and
confirm or reject each backfilled stimulus through the API.

## Phase 5: Dev CLI

**Goal:** Provide local development commands using the same backfill code.

- [ ] Add `scripts/stimulus_backfill.py` with `scan`, `show ASSET_ID`,
  `backfill QUESTION_ID` / `backfill --job JOB_ID`, `confirm ASSET_ID`, and
  `reject ASSET_ID` commands.
- [ ] `backfill --job` with an escalated paid provider first prints a dry-run
  count (regions to re-OCR × provider) and requires confirmation — no
  unbounded paid-vision spend without a visible estimate.
- [ ] CLI shares the Phase 1–3 library and the Phase 4 confirm/reject service
  with the admin API.
- [ ] Add CLI tests for scan, single backfill, idempotent re-run, confirm, and
  reject.

**Exit criteria:** The full workflow can be exercised locally without a server.

## Phase 6: Hardening

**Goal:** Prove the workflow is safe across happy and failure paths.

- [ ] Tests: skip marker recorded on crop failure and on annotation failure.
- [ ] Tests: flag scan classifies A vs B correctly.
- [ ] Tests: Class A re-crop and Class B re-detection.
- [ ] Tests: idempotent linking (no duplicate rows on re-run).
- [ ] Tests: sentinel row promoted in place after a successful link.
- [ ] Tests: sentinel rows AND unconfirmed backfilled rows are excluded from
  downstream stimulus reads.
- [ ] Tests: confirm sets a row live; reject reverts it to a sentinel.
- [ ] Tests: provider escalation tier sends the crop to the override provider.
- [ ] Tests: admin API and CLI end to end.
- [ ] Run relevant backend tests.
- [ ] Manual check: backfill a known chart question, compare the crop image
  against `structured_data_jsonb`, then confirm it.

**Exit criteria:** All acceptance criteria below are met and covered by tests
or documented manual verification.

## Phase 7: Gated Follow-Ups

**Goal:** Two items deliberately deferred until earlier phases produce the
evidence needed to do them safely. Do **not** start either until its gate is met.

### 7a. Batch Class B re-detection

**Gate:** per-question Class B re-detection (Phase 2) is verified accurate on
real official PDFs — i.e. the layout pass reliably finds charts it missed the
first time. If it does not, this item is dropped, not built.

- [ ] Add whole-job / whole-exam layout re-detection that re-runs
  `detect_layout` across all pages and flags newly found regions.
- [ ] Wire it into `POST /admin/stimulus/backfill` and the CLI as an explicit
  opt-in mode, separate from Class A batch.
- [ ] Add tests for batch re-detection over a multi-page job fixture.

### 7b. DB uniqueness constraint

**Gate:** `region_key` (Phase 3) is populated on every `QuestionStimulusAsset`
row, including pre-existing rows backfilled by the Phase 3 migration.

- [ ] Add a `UNIQUE(question_id, region_key)` partial index (excluding
  `failed_*` sentinel rows if they share keys) via migration.
- [ ] Switch linking to `INSERT ... ON CONFLICT ... DO UPDATE`, keeping the
  application-level lookup as the primary path.
- [ ] Add a test proving the constraint rejects a true duplicate.

**Exit criteria:** Either each item is shipped behind its met gate, or it is
explicitly recorded as dropped with the reason.

## Acceptance Criteria

- [ ] No stimulus skip is silent — every failure leaves a queryable marker.
- [ ] A flag scan lists exactly the questions missing stimulus data.
- [ ] A flagged question can be re-OCR'd from persisted page renders without
  the original PDF.
- [ ] Backfill is idempotent — re-running creates no duplicate
  `QuestionStimulusAsset` rows.
- [ ] Recovered `structured_data` + `render_hints` are linked to the correct
  question.
- [ ] A backfilled stimulus is not visible to downstream consumers until it is
  explicitly confirmed; rejecting it returns it to the flag queue for retry.
- [ ] The admin API and dev CLI both drive the full workflow — backfill,
  confirm, reject — and share the same library code.

## Resolved Decisions

- ~~Marker mechanism~~ — **resolved:** sentinel `QuestionStimulusAsset` row
  (Class A); validator signal for Class B. See Phase 0.
- ~~Operates on existing data vs. fresh re-ingest~~ — **resolved:** alpha; build
  the feature, then re-ingest with Phase 0 present. No historical-reconstruction
  path. See Preconditions / Scope.
- ~~Failure taxonomy~~ — **resolved:** sentinels fire at exactly two points
  (`crop_and_store` → `None`, or `_annotate_layout_stimulus` → `{}`); thin
  successful annotations are real rows, not sentinels. See Phase 0.
- ~~Backfill provider~~ — **resolved:** caller-specified `provider` with
  escalation as the documented default; paid-provider batch must be explicit.
  See Phase 2 / Phase 4.
- ~~What backfill sends~~ — **resolved:** tiered by failure mode (crop-only vs.
  single-page layout re-check vs. full Class B layout); PDF never sent. See
  Phase 2.
- ~~Verification of backfilled data~~ — **resolved:** backfilled rows carry
  `origin` + `review_status`, land `unconfirmed`, and are gated behind an
  enforced confirm/reject admin action; the crop image is the verification
  artifact. Review applies to backfilled rows only, not ingest-time rows. See
  Phases 3–4.
- ~~Failed stimulus and job status~~ — **resolved:** any sentinel row forces
  `job.status = needs_review` (no new status value). The question-withholding
  serving rule is deferred — no stimulus consumer exists yet (see Deferred).
- ~~`region_key` derivation~~ — **resolved:** quantized bbox-center key
  (`page_index:region_type:round(cx,2):round(cy,2)`), size-blind for re-run
  stability; full bbox stored separately as crop geometry. See Phase 3.
- ~~Batch vs. per-question Class B re-detection~~ — **resolved:** per-question
  only in Phase 2; whole-job batch deferred to Phase 7a, gated on per-question
  Class B accuracy testing.
- ~~DB unique constraint vs. application-level dedup~~ — **resolved:**
  application-level dedup on a new `region_key` column in Phase 3; the DB
  `UNIQUE(question_id, region_key)` index is deferred to Phase 7b, gated on
  `region_key` being fully populated. Neither column-set alone is unique today
  (two charts can share a page), so the key column must exist first.

## Deferred (Out of Scope)

- **Question-withholding policy for failed/unconfirmed essential stimuli.**
  `questions.py` / `student.py` currently serve only `stimulus_mode_key` — no
  stimulus content reaches students yet. With no consumer, an
  essential-vs-supplementary serving rule has nothing to gate. The invariant
  *"sentinel and unconfirmed rows are never served as live stimulus"* (Phase
  0/3) and the `needs_review` status signal are enough here. The withholding
  policy is decided when the student stimulus-rendering path is built, and
  belongs in that feature.

## Open Questions

- Class B accuracy: re-detection quality on charts the first pass missed is
  unverified — Phase 2 must test this before Phase 7a; it may need a
  vision-model or prompt change, which is out of scope for this doc.
