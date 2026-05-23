# Rules Update Feature Task List

## Goal

Build an approval-gated rules update workflow where official ingestion analysis
can propose amendments to:

- `rules_agent_dsat_reading_v2.md`
- `rules_agent_dsat_grammar_ingestion_generation_v7.md`

Approved amendments patch the body of the relevant rule doc, then promote the
approved controlled-vocabulary change into `vocabulary/master.json`. The updated
`master.json` is the compiled enforcement manifest used to regenerate validator
constants, VOCAB appendices, DB consistency checks, and JSONB consistency checks.

## Existing Foundation

- `vocabulary/master.json` exists.
- `vocabulary/candidates.json` exists.
- `scripts/gen_vocab.py --check` and `--generate` exist.
- `scripts/gen_vocab.py --promote VOCAB VALUE` currently allows direct promotion
  and must be replaced or fenced behind approved amendments.
- `backend/app/models/ontology.py` is generated from `master.json`.
- Both rule docs already contain generated VOCAB appendix blocks.
- Both rule docs already mention amendment proposals, but proposal capture,
  review, approval, promotion, and re-appraisal are not implemented.

## Target Flow

```text
official ingestion analysis
  -> LLM amendment proposal
  -> amendment file in pending review
  -> admin approval
  -> patch rule doc body
  -> promote candidate into master.json
  -> regenerate ontology.py + VOCAB appendices
  -> scan DB/JSONB consistency
  -> rerun/re-appraise ingestion analysis
  -> write per-test analysis reports
```

## Design Decisions

- Approved amendments must patch the body of the rule docs, not only generated
  appendix blocks.
- Only `content_origin == "official"` ingestion may propose rule amendments.
- Deployment workflow is admin API-first.
- Development workflow may use CLI commands, but the CLI must enforce the same
  approval gates as the admin API.
- `master.json` is not the normative authoring surface for new rules. It is the
  compiled controlled-vocabulary manifest after approved rule amendments.
- Existing unknown-key candidate capture may remain non-blocking, but candidates
  cannot be promoted into active vocabulary without an approved amendment.

## Phase 0: Governance Baseline

**Goal:** Reconcile the current vocabulary workflow with the new approval-gated
model before adding new surfaces.

- [x] Update vocabulary docs/comments so `master.json` is described as the
  compiled enforcement manifest, not the casual hand-edit source of truth.
- [x] Update `scripts/gen_vocab.py` help text and comments to distinguish:
  - regeneration from current `master.json`
  - candidate review
  - approved amendment promotion
- [x] Decide whether direct `--promote VOCAB VALUE` is removed immediately or kept
  temporarily behind an explicit unsafe/dev-only flag.
- [x] Add a regression test that proves unapproved candidate promotion cannot add
  an active key to `master.json`.
- [x] Add a short architecture note documenting the invariant:
  rule-doc body approval comes before active vocabulary growth.

**Exit criteria:** There is one unambiguous vocabulary governance model in docs,
script help, and tests.

## Phase 1: Amendment Storage and Schema

**Goal:** Add durable amendment records with official-source constraints.

- [x] Add amendment/report directories:
  - `vocabulary/amendments/pending/`
  - `vocabulary/amendments/approved/`
  - `vocabulary/amendments/rejected/`
  - `vocabulary/amendments/needs_manual_patch/`
  - `analysis/ingestion/`
- [x] Define an amendment schema as Pydantic model and/or JSON Schema with:
  - `amendment_id`
  - `status`
  - `source_job_id`
  - `source_exam_code`
  - `source_subject_code`
  - `source_section_code`
  - `source_module_code`
  - `source_question_number`
  - `content_origin`, required to equal `official`
  - `affected_doc`, reading or grammar
  - `proposal_type`
  - `affected_vocab`
  - `proposed_value`
  - `parent_key`, for hierarchical vocabularies
  - `definition`
  - `current_best_fit`
  - `why_current_rules_are_insufficient`
  - `official_evidence`
  - `rule_doc_patch`
  - `master_json_patch`
  - `supporting_examples`
  - `review_notes`
  - `admin_decision`
  - `created_at`
  - `updated_at`
- [x] Add schema validation tests for required fields, status transitions, and
  hierarchical `parent_key` requirements.
- [x] Add tests that reject amendment files from unofficial or generated jobs.

**Exit criteria:** Pending amendment files can be validated independently of the
ingestion pipeline.

## Phase 2: LLM Proposal Capture

**Goal:** Let official Pass 2 analysis propose amendments without allowing new
keys into production annotations.

- [x] Update the Pass 2 annotation prompt so the LLM:
  - uses existing approved keys for actual annotation
  - emits `reasoning.amendment_proposal` only for official-source gaps
  - never emits amendment proposals for unofficial or generated content
  - includes exact official evidence
  - explains why current rules are insufficient
  - proposes a body patch for the relevant rule doc
  - proposes the corresponding controlled-vocabulary change
- [x] Add extraction code that:
  - scans completed official ingestion jobs
  - extracts `pass2_json.reasoning.amendment_proposal`
  - writes one amendment file per proposal
  - deduplicates repeated proposals by `affected_vocab + proposed_value + parent_key`
  - links all supporting official examples
- [x] Link amendment files back to `vocabulary/candidates.json` when a matching
  candidate exists.
- [x] Ensure unofficial/generated jobs drop or ignore any LLM-emitted amendment
  proposal and record a warning rather than accepting it.

**Exit criteria:** Official jobs can produce pending amendment files; other
content origins cannot.

## Phase 3: Rule-Doc Patch Engine

**Goal:** Make rule-doc body patches reviewable and enforceable before vocabulary
promotion.

- [x] Implement patch application for:
  - `rules_agent_dsat_reading_v2.md`
  - `rules_agent_dsat_grammar_ingestion_generation_v7.md`
- [x] Rule doc body patches should update the relevant taxonomy section with:
  - new key definition
  - when-to-use guidance
  - distractor guidance, when applicable
  - generation guidance, when applicable
  - official source evidence or example
- [x] Validate that patches do not target generated VOCAB appendix blocks.
- [x] Add patch failure behavior:
  - if patch does not apply cleanly, mark amendment as `needs_manual_patch`
  - expose diff or conflict details to the admin reviewer
  - do not promote to `master.json` until the rule doc body patch is resolved
- [x] After body patching, regenerate Appendix V from `master.json`.

**Exit criteria:** A pending amendment can be dry-run patched, conflict-checked,
and blocked if the rule-doc body is not updated cleanly.

## Phase 4: Admin Review API

**Goal:** Expose approval workflow through admin API endpoints.

- [x] Add admin endpoints:
  - `GET /admin/amendments`
  - `GET /admin/amendments/{id}`
  - `POST /admin/amendments/{id}/approve`
  - `POST /admin/amendments/{id}/reject`
  - `POST /admin/amendments/{id}/request-more-evidence`
  - `POST /admin/amendments/{id}/promote`
- [x] Approval must validate:
  - source content is official
  - amendment file exists and passes schema validation
  - linked candidate exists or can be created
  - rule doc patch dry-run applies cleanly
  - proposed key is not already active
  - parent mapping is valid for hierarchical vocabularies
- [x] Promotion should perform repo-file changes as one guarded operation:
  - patch rule doc body
  - update `vocabulary/master.json`
  - regenerate `backend/app/models/ontology.py`
  - regenerate VOCAB appendix blocks
  - move amendment file to `vocabulary/amendments/approved/`
  - write promotion metadata
- [x] Add API tests for list/show/approve/reject/request-more-evidence/promote.

**Exit criteria:** Admins can approve and promote one amendment end to end
through the API without bypassing rule-doc body review.

## Phase 5: Dev CLI

**Goal:** Provide local development commands that use the same gates as the API.

- [x] Add CLI equivalents for local development:

```bash
python scripts/amendments.py list
python scripts/amendments.py show AMENDMENT_ID
python scripts/amendments.py approve AMENDMENT_ID
python scripts/amendments.py reject AMENDMENT_ID
python scripts/amendments.py request-more-evidence AMENDMENT_ID
python scripts/amendments.py promote AMENDMENT_ID
```

- [x] Update `scripts/gen_vocab.py`:
  - keep `--check`
  - keep `--generate`
  - remove or fence casual `--promote`
  - require `--promote-from-amendment AMENDMENT_ID` for active key promotion
- [x] Ensure CLI and API share validation/promotion library code rather than
  duplicating policy checks.
- [x] Add CLI tests for list/show/approval/rejection/promotion and blocked
  unapproved promotion.

**Exit criteria:** Local development can exercise the full workflow without a
server, and it cannot bypass amendment approval.

## Phase 6: Master JSON and DB/JSONB Consistency

**Goal:** Verify current data against the active compiled vocabulary.

- [x] Add a consistency scanner:

```bash
python scripts/check_vocab_consistency.py --all
```

- [x] Scanner should inspect:
  - `question_jobs.pass1_json`
  - `question_jobs.pass2_json`
  - `question_jobs.validation_errors_jsonb`
  - `question_annotations`
  - `question_options`
  - generated JSON/YAML exports, if applicable
- [x] Scanner should report:
  - unknown keys
  - deprecated keys
  - keys valid but under the wrong parent
  - reading questions with grammar keys
  - Cross-Text items without `prose_paired`
  - quantitative evidence items without table or graph data
- [x] Add a machine-readable report output option for CI or admin UI use.
- [x] Add DB/JSONB consistency scan tests using fixtures for each error type.

**Exit criteria:** Existing DB/JSONB data can be scanned against the current
`master.json`, and scanner output is usable in automation.

## Phase 7: Ingestion Analysis Reports and Re-Appraisal

**Goal:** Make official ingestion analysis reproducible across vocabulary growth.

- [x] Store hashes in every ingestion analysis:
  - `master_json_hash`
  - `reading_rules_hash`
  - `grammar_rules_hash`
  - `ontology_hash`
- [x] Organize reports as:

```text
analysis/ingestion/
  PT04/
    run_2026-05-18_<job-or-batch-id>/
      summary.md
      taxonomy_coverage.json
      validation_failures.json
      amendment_candidates.json
      reappraisal_<master_hash>.md
      questions/
        q001.md
        q002.md
```

- [x] On every `master.json` growth:
  - identify prior official ingestion analyses with older hashes
  - rerun validation/re-appraisal
  - write a new report instead of overwriting old reports
- [x] Add re-appraisal report creation tests after `master_json_hash` changes.

**Exit criteria:** Vocabulary growth creates or queues re-appraisal for affected
prior official analyses.

## Phase 8: End-to-End Hardening

**Goal:** Prove the workflow is safe across happy paths and failure paths.

- [x] Add tests for official jobs emitting amendment proposals.
  - `test_amendment_capture.py`: `test_capture_amendment_proposal_writes_pending_file_and_links_candidate`,
    `test_iter_job_amendment_payloads_reads_multi_question_metadata`,
    `test_capture_amendments_from_completed_official_jobs_scans_db`,
    `test_capture_amendments_from_job_backfills_pending_file`.
- [x] Add tests proving unofficial and generated jobs cannot emit amendment proposals.
  - `test_amendment_capture.py::test_capture_amendment_proposal_ignores_non_official_jobs`;
    `test_amendments.py::test_rule_amendment_rejects_non_official_origins`.
- [x] Add amendment file schema validation tests.
  - `test_amendments.py` (6 tests: valid payload, non-official rejection,
    hierarchical `parent_key` requirement, patch mismatch, unknown extra
    fields, lowercase vocab name).
- [x] Add admin approval flow tests.
  - `test_admin_router.py` (amendment list/show/approve/reject/request-more-evidence/promote/422)
    + `test_amendment_review.py` (11 service-level tests).
- [x] Add rule doc body patching tests.
  - `test_rule_doc_patcher.py` (10 tests: dry-run diff, body patch, generated
    VOCAB block protection, ambiguous anchor, missing section, `needs_manual_patch`).
- [x] Add promotion-to-`master.json` tests.
  - `test_amendment_review.py::test_promote_patches_doc_updates_master_regenerates_and_moves_file`,
    `test_promote_restores_master_and_doc_when_regeneration_fails`.
- [x] Add regenerated `ontology.py` sync tests.
  - `test_vocab_sync.py::test_artefacts_in_sync_with_master_json` (runs
    `gen_vocab.py --check`, the CI drift gate for `ontology.py`).
- [x] Add generated VOCAB appendix sync tests.
  - `test_vocab_sync.py::test_artefacts_in_sync_with_master_json` (same gate
    also validates both rule-doc VOCAB appendix blocks).
- [x] Add DB/JSONB consistency scan tests.
  - `test_vocab_consistency.py` (8 tests: unknown/deprecated/wrong-parent/domain/
    shape errors, option-row scan, machine-readable JSON, severity-aware exit
    codes, JSON/YAML export load, async DB streaming).
- [x] Add re-appraisal report creation tests after `master.json` hash changes.
  - `test_ingestion_analysis.py::test_write_reappraisals_after_master_hash_changes`,
    `test_reappraisal_markdown_records_exam_and_hash_comparison`.
- [x] Run `python3 scripts/gen_vocab.py --check`. — `vocabulary in sync`.
- [x] Run relevant backend tests. — `uv run pytest` (`441 passed, 2 skipped`;
  4 errors are pre-existing in `backend/test_ocr_live.py`, a standalone live-OCR
  script unrelated to this feature).

**Exit criteria:** All acceptance criteria below are met and covered by tests or
documented manual verification.

## Acceptance Criteria

- [x] No new key can reach `master.json` without an approved amendment.
  - `test_vocab_sync.py::test_direct_promote_is_blocked_without_unsafe_flag`;
    `test_amendment_review.py` promotion gate tests.
- [x] No amendment can be approved unless it comes from official ingestion evidence.
  - `test_amendment_review.py::test_approve_validates_patch_and_links_or_creates_candidate`;
    `test_amendments.py::test_rule_amendment_rejects_non_official_origins`.
- [x] Approved amendments patch the rule doc body before updating `master.json`.
  - `test_amendment_review.py::test_promote_patches_doc_updates_master_regenerates_and_moves_file`;
    `test_rule_doc_patcher.py`.
- [x] `python3 scripts/gen_vocab.py --check` passes after promotion. — `vocabulary in sync`.
- [x] Existing DB/JSONB data can be scanned against the current `master.json`.
  - `test_vocab_consistency.py` (8 tests).
- [x] Every official ingestion run has organized analysis files.
  - `test_ingestion_analysis.py::test_write_ingestion_analysis_creates_expected_report_layout`.
- [x] Every vocabulary growth creates or queues re-appraisal for affected prior analyses.
  - `test_ingestion_analysis.py::test_write_reappraisals_after_master_hash_changes`.
