# TASKS.md — Remaining Work

Last updated: 2026-04-02. Branch: `alpha-v3-codex`.

---

## Immediate (uncommitted work on branch)

- [ ] **Commit Codex adversarial review changes**
  - `backend/app/models/ontology.py` — `FIELD_TO_TABLE` extended with 3 missing generation target keys (026 mirrors)
  - `backend/migrations/025_consolidation.sql` — `DROP VIEW question_flat_export` added before column drops
  - `backend/tests/conftest.py` — full ontology fixture expansion (migrations 017–026)
  - `backend/tests/test_models.py`, `test_ontology.py`, `test_validator.py` — expanded test coverage
  - Run tests first to confirm all pass before committing

- [ ] **Disposition untracked directories**
  - `FULL_PLAN-alpha-v3/` — archive or delete?
  - `.alpha_v3_staging/` — archive or delete?
  - `FLOW.md` — commit or discard?

---

## App Layer

- [ ] **Coaching annotation staleness on passage text edit** *(Task #1)*
  When `passage_text`, `stem_text`, `prompt_text`, or `paired_passage_text` is updated on a question, invalidate stale character offsets in `question_coaching_annotations`:
  1. Query annotations for the question
  2. Verify text at `[span_start_char:span_end_char]` still matches
  3. On mismatch: set `span_start_char = NULL`, `span_end_char = NULL` — `span_sentence_index` becomes the UI fallback
  4. Recalculate char offsets from sentence index after text is confirmed
  Consider: DB trigger on `questions UPDATE` vs. app-layer hook

- [ ] **Generation prompt builder**
  Reads `target_*` columns from `question_generation_profiles` → outputs structured natural-language style spec for LLM call. Three components:
  1. Prompt builder function (maps target columns → instruction text)
  2. Exemplar retrieval via `question_embeddings` (passage_only type) cosine similarity — 2–3 closest ground-truth questions as few-shot examples
  3. Post-generation Pass 2 diff: re-classify generated passage and compare against target fingerprint; flag `difficulty_drifted`, `syntax_drifted` (see `v_generation_traceability`)
  Full spec: `STYLE_GEN.md`

- [ ] **Call `fn_refresh_irt_b()` after bulk Pass 2 annotation runs**
  `SELECT fn_refresh_irt_b();` recomputes b-estimates for all unset/v1 rows. Hook into the ingestion approval pipeline so IRT scores are always current after a batch approval.

---

## Phase 5 — Scale

- [ ] **Scale corpus to 500–1,000+ questions**
  Ingest additional official CB practice tests beyond PT4. Target: enough volume for IVFFlat index to be meaningful (`fn_rebuild_embedding_index()` at 500+ embedding rows).

- [ ] **Row-level security (RLS)**
  Migration 016 drafted RLS policies. Verify they are correct and enabled in Supabase before scaling ingestion. Test with a non-admin role.

- [ ] **Performance benchmarking**
  Benchmark vector search (`/search` endpoint), ingestion throughput, and annotation pipeline latency at 500+ questions. Tune IVFFlat `lists` parameter via `fn_rebuild_embedding_index()`.

---

## Future (data-gated)

- [ ] **Normalize `table_data_jsonb` / `graph_data_jsonb`**
  Intentionally kept as JSONB for first build viability test. Normalize into typed tables after table/graph question ingestion is validated end-to-end. Shapes documented as `COMMENT ON COLUMN` in migration 020.

- [ ] **Empirical IRT calibration** *(at ~500+ student responses per item)*
  Overwrite `irt_b_estimate` with empirically calibrated values; set `irt_b_rubric_version = 'empirical'`. Current rubric v1 is a weighted proxy — valid for ranking but not for psychometric reporting.

- [ ] **Upgrade image parser: pytesseract → deepseek-ocr**
  Current PDF/image ingestion uses pytesseract. Upgrade when deepseek-ocr integration is available for improved OCR accuracy on scanned SAT PDFs.

- [ ] **LoRA adapter for Pass 2 classification** *(at ~200+ approved questions)*
  Fine-tune a LoRA adapter on the approved annotation corpus to improve Pass 2 classification consistency and reduce hallucinated lookup values. Use approved `question_classifications` rows as training signal.

- [ ] **Fine-tuned model for generation** *(at ~500+ approved questions)*
  Train a generation-focused fine-tune on the approved question corpus. The `generation_params_snapshot_jsonb` on `generated_questions` and `v_generation_traceability` drift flags are the training signal inputs.
