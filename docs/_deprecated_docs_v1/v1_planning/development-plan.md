# SAT Codex Ontology — Development Plan
_Generated: 2026-03-20 | Last updated: 2026-03-22_

---

## Project Status Summary

| Layer | Status |
|-------|--------|
| Taxonomy (Parts 1–3) | ✅ Complete |
| Schema design | ✅ Complete |
| SQL migrations (001–021) | ✅ Complete — 28 lookup tables, full classification + generation schema |
| LLM ingestion pipeline (Pass 1 + Pass 2) | ✅ Complete |
| Validation & review workflow | ✅ Complete |
| Pilot data (66 questions) | ✅ Complete |
| Backend service (FastAPI) | ✅ Complete |
| Embeddings pipeline | ✅ Script ready — blocked on OpenAI API key |
| Semantic search endpoint | ✅ Complete (`POST /search`) |
| Prose grammar re-annotation (017–019 fields) | ⏳ Script ready — blocked on Anthropic API credits |
| Item anatomy + passage fingerprint (020) | ✅ Schema complete — awaiting first annotated data |
| Generation lifecycle tables (021) | ✅ Schema complete — awaiting generation pipeline |
| Generation pipeline | ❌ Not started (next major phase) |
| Ontology evolution / approval workflow | ❌ Not started (see FUTURE_PLANS.md) |
| Image/chart storage | ❌ Not started (see FUTURE_PLANS.md) |

---

## Phase 1 — Complete Pilot Data (SQL)
**Goal:** All 66 PT4 RW questions in the database with full annotations.

### Tasks
1. **Extend pilot SQL pack** — add remaining 56 questions to `supabase/dsat_pilot_ingestion_sql_pack_pt4_rw_subset_v1.sql`
   - PT4 RW M1: Q5–Q18, Q23–Q33 (23 questions)
   - PT4 RW M2: Q1–Q8, Q13–Q33 (28 questions)
   - Follow existing idempotent upsert pattern (CTE → questions → classifications → options → reasoning → generation_profiles)

2. **Verify full load** — run migrations 001–013 then pilot SQL pack against a fresh Supabase project; confirm row counts match expectations.

**Dependencies:** None — purely additive SQL.
**Deliverables:** Updated pilot SQL pack in `supabase/`.

---

## Phase 2 — Backend Ingestion Service (Python/FastAPI)
**Goal:** Automated pipeline from raw question text → validated DB rows via LLM.

### Tasks
1. **Project scaffold** — set up `backend/` with FastAPI, Pydantic, asyncpg/supabase-py, poetry/uv.

2. **Pydantic ingestion contract** — model the exact JSON shape output by the LLM:
   - `QuestionExtract` (Pass 1 output)
   - `QuestionAnnotation` (Pass 2 output)
   - `IngestionPayload` (combined, validated)
   - Lookup value enum validators (check against allowed keys)

3. **Staging table migration** — add `question_ingestion_jobs` table (step 014):
   ```sql
   id, source_file, raw_text, raw_json, llm_output_json,
   validation_errors_json, status (draft/reviewed/approved/rejected),
   review_notes, created_at, updated_at
   ```

4. **LLM prompt layer**
   - System prompt with fixed ontology reference (all lookup table keys)
   - Pass 1 prompt: extraction only (stem, passage, choices, correct, metadata)
   - Pass 2 prompt: annotation (classification, option analysis, reasoning, generation profile)
   - Few-shot examples (2–4 annotated questions from pilot data)

5. **Validation layer**
   - Required field presence checks
   - Lookup key validation against known values
   - One-correct-option constraint
   - Option label completeness (A–D)
   - Write errors to `validation_errors_json`, set status → `draft` or `rejected`

6. **Upsert layer** — map validated `IngestionPayload` → SQL upserts across all 5 layers:
   - questions, question_classifications, question_options, question_reasoning, question_generation_profiles

7. **Review endpoint** — `PATCH /jobs/{id}/status` to move draft → reviewed → approved (triggers upsert to production tables)

**Dependencies:** Phase 1 (pilot data confirms all lookup values are seeded).
**Deliverables:** `backend/` with runnable FastAPI app, Dockerfile, `.env.example`.

---

## Phase 3 — Embeddings Pipeline
**Goal:** 1536-dim embeddings for all pilot questions, validated semantic search.

### Tasks
1. **Embedding job script** — async Python script to:
   - Query all questions missing embeddings
   - Build embedding text per type (`full_item`, `passage_only`, `explanation`, `taxonomy_summary`, `generation_profile`)
   - Call embedding API (OpenAI `text-embedding-3-small` → 1536-dim)
   - Upsert to `question_embeddings`

2. **IVFFlat index tuning** — test cosine search with `lists=100`; adjust based on 66-question pilot (rule of thumb: `lists = sqrt(n_rows)` at scale → tune for 1000+ target).

3. **Semantic search endpoint** — `POST /search` accepting query text, returning top-K questions by cosine similarity.

**Dependencies:** Phase 1 complete (questions in DB).
**Deliverables:** `backend/scripts/generate_embeddings.py`, search endpoint.

---

## Phase 4 — Reporting & Analytics Views
**Goal:** SQL views and query library for curriculum analysis.

### Tasks
1. **Migration 016** — add reporting views:
   - `question_distribution_by_family` — count per question_family_key × module
   - `distractor_effectiveness` — distractor_type breakdown with avg difficulty correlation
   - `generation_pattern_coverage` — which patterns have ≥N examples (ready for generation)
   - `topic_domain_coverage` — topic_broad × skill_family heatmap

2. **Taxonomy coverage report** — identify which subskills have <3 questions (insufficient for generation training).

**Dependencies:** Phase 1 (sufficient data volume).
**Deliverables:** `CLAUDE/migration_016_reporting_views.sql`, query documentation.

---

## Phase 5 — Scale & Hardening
**Goal:** Production-ready for 500–1000+ questions.

### Tasks
1. **Additional practice tests** — repeat Phase 1 ingestion workflow for PT5, PT6, etc.
2. **Vector index rebuild** — re-create IVFFlat index with tuned `lists` after bulk load.
3. **Row-level security** — evaluate if multi-user/multi-tenant access is needed; add RLS policies if so.
4. **Performance benchmarking** — test query times on 1000-question dataset; add covering indexes where needed.
5. **Backup/recovery** — document Supabase point-in-time recovery settings and test restore procedure.

**Dependencies:** Phases 2–3 complete.

---

## Dependency Graph

```
Phase 1 (Pilot SQL)
    └── Phase 2 (Backend service)
            ├── Phase 3 (Embeddings pipeline)
            └── Phase 4 (Reporting views)
                        └── Phase 5 (Scale & hardening)
```

---

## Immediate Next Steps (Start Here)

1. Run existing migrations 001–013 against a Supabase project to verify schema is clean.
2. Run pilot SQL pack to confirm the 10 existing questions load without errors.
3. Begin Phase 1 — extend pilot SQL for remaining 56 questions.
4. Scaffold `backend/` directory with FastAPI + Pydantic as Phase 2 foundation.

---

## Output Directory Convention

All Claude-generated artifacts for this project are written to `FULL_PLAN/CLAUDE/`.

| File | Contents |
|------|----------|
| `development-plan.md` | This file |
| `migration_016_reporting_views.sql` | Phase 4 views (when created) |
| `ingestion_contract.py` | Phase 2 Pydantic models (when created) |
| `llm_prompts.md` | Phase 2 LLM prompts (when created) |
