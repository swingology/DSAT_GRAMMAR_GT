# Migrations & Gaps Audit Report

**Date:** 2026-04-21
**Auditor:** GLM-5.1 (Cloud)
**Scope:** All migration, gap, alignment, and drift documents — cross-referenced against live SQL, prompt code, and taxonomy sources
**Question:** Are the identified gaps still present, and do the proposed solutions align with a schema optimized for generation, text analysis, grammar classification, and QA explanations?

---

## Executive Summary

**23 original gaps identified** (4 CRITICAL, 8 HIGH, 8 MODERATE, 3 LOW) across three prior analyses. Plus 4 SQL bugs from the Codex review and 4 drift issues from the ground-truth analysis.

**Current status: 2 fully fixed, 5 partially fixed, 28 still open.**

The single most urgent runtime defect is the **syntactic_trap key mismatch** — the LLM prompts list 21 keys, but the v2 database seeds only 13. Every ingestion or generation job that produces one of the 8 phantom keys will fail with an FK constraint violation. This is a code fix, not a migration change.

The proposed solutions in the existing gap documents are architecturally sound and well-aligned with the four target capabilities (generation, text analysis, grammar, QA explanations). The main risk is execution — many fixes are documented but not yet implemented in the actual migration files or prompt code.

---

## Documents Reviewed

| Document | Path | Date |
|----------|------|------|
| Migrations PRD v2 Gap Analysis | `docs/superpowers/specs/2026-04-20-migrations-prd-v2-gap-analysis.md` | 2026-04-20 |
| Grammar Taxonomy + DB Schema Alignment | `docs/superpowers/specs/2026-04-21-grammar-taxonomy-schema-alignment.md` | 2026-04-21 |
| Codex Review: Migrations PRD v2 | `docs/migration/codex-migrations-gaps.md` | 2026-04-20 |
| PRD v2 vs Deprecated Migrations Diff | `docs/migration/migrations_diff.md` | 2026-04-20 |
| GROUND_TRUTH Drift & Alignment Issues | `docs/GRAMMAR_GUIDE/ground_truth_issues.md` | 2026-04-21 |
| Seed Data Addendum | `docs/migration/seed_data_addendum.md` | 2026-04-21 |
| Migrations PRD v2 Rebuild | `docs/migration/Migrations_PRD_v2_rebuild.md` | 2026-04-19 |
| GROUND_TRUTH_GRAMMAR | `docs/GRAMMAR_GUIDE/GROUND_TRUTH_GRAMMAR.md` | v1.2 |
| Grammar Amendment Proposals | `docs/GRAMMAR_GUIDE/GRAMMAR_AMENDMENT.md` | 2026-04-21 |
| REBUILD_FUTURE_PLANS | `docs/REBUILD_FUTURE_PLANS.md` | 2026-04-21 |

**Live code verified:**
- `_deprecated/backend/app/prompts/pass2_annotation.py` (line 40, lines 166-177)
- `_deprecated/backend/app/prompts/generation.py` (line 145)
- `_deprecated/backend/app/models/ontology.py` (lines 23, 74, 124)
- `_deprecated/migrations_v1/037_backfill_pre014_columns.sql`
- `_deprecated/migrations_v1/038_fresh_build_context_reconciliation.sql`
- `_deprecated/migrations_v1/039_grammar_keys_token_annotations.sql`
- `_deprecated/migrations_v1/040_tokenization_status.sql`
- `_deprecated/migrations_v1/041_new_grammar_focus_categories.sql`
- `_deprecated/migrations_v1/042_additional_grammar_focus_categories.sql`

---

## Part 1: Gap-by-Gap Status

### CRITICAL Gaps

#### C1. Deployment Order Bug — FK Seeds After Table Creation

**Still present.** The PRD v2 places M-022 (seed data for `lookup_stimulus_mode`, `lookup_stem_type`, `lookup_question_family`) after M-005/M-006 which have NOT NULL FKs to those tables. The Codex review further revealed the full dependency chain:

| Migration | Depends On | Reason |
|-----------|-----------|--------|
| M-022 | M-003 | Seeds tables created in M-003 |
| M-023 | M-004 | `lookup_skill_family.domain_key` FK requires `lookup_domain` seeds from M-004 |
| M-024 | M-013 + M-022 | Inserts into `generation_templates`; uses `question_family_key` values from M-022 |
| M-025 | M-016 | Inserts into `grammar_keys` (created M-016) |

**Proposed fix:** Move critical lookup seeds into M-004 alongside grammar seeds.

**Alignment assessment:** Strong alignment with all four target capabilities. The generation pipeline needs all lookup tables populated before any question write — without this fix, you cannot test generation end-to-end. Text analysis and grammar classification also require populated lookup tables for FK-valid inserts. The current dependency on M-022 running "before first insert" is fragile and undocumented.

**Recommendation:** Implement fix (a) — move `lookup_stimulus_mode`, `lookup_stem_type`, and `lookup_question_family` seeds into M-004. Document explicit rule: no data writes until M-028 is complete.

---

#### C2. No Rollback / Downgrade Plan

**Still present.** Zero `DOWN` files. Most seed migrations use bare `INSERT INTO` without `ON CONFLICT DO NOTHING`. The v1 migrations 038-042 use idempotent patterns (`ADD COLUMN IF NOT EXISTS`, `ON CONFLICT DO NOTHING`), but the PRD v2 M-004–M-028 seeds do not.

**Alignment assessment:** Directly blocks safe iteration on generation. When testing generation pipeline changes, a failed migration requires manual cleanup. The `ON CONFLICT DO NOTHING` pattern from migration 039 should be the standard.

**Recommendation:** Add `INSERT ... ON CONFLICT DO NOTHING` to all seed data. Do NOT add `down/` files — for a greenfield rebuild, re-running from scratch is simpler than downgrade paths. Document the re-run procedure instead.

---

#### C3. No Data Migration Plan from Old Schema (001-042)

**Still present.** No ETL strategy. However, this is **acceptable** — the REBUILD_FUTURE_PLANS.md and the PRD itself frame this as a greenfield rebuild. The old schema has structural defects (free-text domains, missing columns, dropped `solver_steps` table) that make column mapping unreliable. Re-ingestion from source PDFs is the correct approach.

**Alignment assessment:** Neutral for generation (new data will be ingested fresh). Positive for grammar and QA — re-annotation with the corrected taxonomy ensures consistent classification from the start rather than inheriting old inconsistencies.

**Recommendation:** Add explicit statement to PRD: "Data migration is not supported. Re-ingest from source material using the v2 pipeline."

---

#### C4. No Concurrent Migration Safety

**Still present.** No `pg_advisory_lock`, no `schema_migrations` tracking table, no transaction wrapping per migration.

**Alignment assessment:** Low impact on the four target capabilities directly, but high risk for CI/CD deployment. Two pipelines running migrations simultaneously will produce duplicate inserts and partial DDL application.

**Recommendation:** Add `schema_migrations` table in M-001. Wrap each migration in a transaction with advisory lock. Low effort, high safety.

---

### HIGH Gaps

#### H1. Grammar Focus Role Mapping Errors

**Partially fixed.** The grammar-taxonomy alignment doc (2026-04-21) correctly identified both errors:

| Key | GROUND_TRUTH § | Taxonomy v2 §7.9 | PRD v2 M-004 | Migration 041 | Correct |
|----|----------------|-------------------|---------------|---------------|---------|
| `elliptical_constructions` | §3.6 Parallel Structure | `parallel_structure` | `verb_form` | `parallel_structure` (correct in comment) | **`parallel_structure`** |
| `affirmative_agreement` | §3.2 Agreement Rules | `verb_form` | `agreement` | Comment says `verb_form` | **`agreement`** |

The alignment doc proposed fixing `elliptical_constructions → parallel_structure` in M-004. Migration 041's comment correctly says `parallel_structure`. But the **PRD v2 M-004 seed data still has `verb_form`** — the fix was documented but not applied to the PRD.

For `affirmative_agreement`, the PRD has `agreement` (correct per GROUND_TRUTH) but the taxonomy v2 has `verb_form` (incorrect). The alignment doc proposed updating the taxonomy to match GROUND_TRUTH. The resolution: `agreement` wins because so/neither inversion agrees with the antecedent clause's auxiliary — this is an agreement pattern, not a verb-form pattern.

**Alignment assessment:** Critical for grammar analysis. Wrong role mapping causes the LLM to annotate under the wrong grammar category, which cascades to:
- Wrong `target_grammar_role_key` in generation profiles → generation produces questions targeting the wrong grammatical structure
- Wrong coaching annotation explanations → students get misattributed rule explanations
- Wrong disambiguation behavior → the LLM applies the wrong priority rules

**Recommendation:** Fix M-004 seed: `elliptical_constructions → parallel_structure`. Confirm `affirmative_agreement → agreement`. Update taxonomy v2 §7.4 mapping.

---

#### H2. Disambiguation Priority Collision

**Still present.** Two issues:

1. `pronoun_case` and `pronoun_antecedent_agreement` both have `disambiguation_priority = 5` in the DB. GROUND_TRUTH §4.5 states "pronoun_case > pronoun_antecedent_agreement" — meaning `pronoun_case` should have a lower number (higher precedence).

2. The prompt (pass2_annotation.py lines 167-177) lists 11 of 12 priorities. Priority 12 (`preposition_idiom > conjunction_usage`) is missing because `preposition_idiom` was itself missing from the taxonomy until the alignment doc added it.

**Alignment assessment:** Directly affects QA explanations and grammar classification accuracy. The disambiguation rules determine which grammar rule the LLM assigns when multiple could apply. Wrong rule assignment = wrong coaching tip = wrong student explanation. For generation, the `target_grammar_focus_key` inherits from annotation, so wrong disambiguation means wrong generation target.

**Recommendation:**
- Set `pronoun_case` priority to 5, `pronoun_antecedent_agreement` to 6
- Add priority 12 (`preposition_idiom > conjunction_usage`) to the prompt
- Long-term: move disambiguation rules into a `lookup_disambiguation_rule` table so `ontology_ref.py` can render them dynamically from the DB

---

#### H3. Missing CHECK Constraints on `question_coaching_annotations`

**Still present.** The v2 rebuild has neither `chk_span_char_order` nor `chk_span_has_anchor`. The v1 migration 034 had both.

**Alignment assessment:** Critical for QA explanations. Invalid spans (`span_end_char < span_start_char`, or anchorless annotations with no `blank_context` exemption) mean the interactive grammar UI cannot render highlights. The coaching panel depends on valid character offsets.

**Recommendation:** Add to M-015:
```sql
CONSTRAINT chk_span_char_order CHECK (
    span_start_char IS NULL OR span_end_char IS NULL
    OR span_end_char > span_start_char
),
CONSTRAINT chk_span_has_anchor CHECK (
    annotation_type = 'blank_context'
    OR span_start_char IS NOT NULL
    OR span_sentence_index IS NOT NULL
)
```

---

#### H4. 12 Analytical Views Missing

**Still present.** PRD v2 M-020 creates 7 views; the v1 schema had 19. The 12 missing views are:

1. `v_question_distribution` — counts by domain/family/difficulty per module
2. `v_distractor_effectiveness` — distractor type effectiveness by family
3. `v_embedding_coverage` — which embedding types are present/missing
4. `v_ingestion_pipeline_summary` — job count by status/model
5. `v_prose_complexity_profile` — aggregate syntactic/style fingerprint counts
6. `v_style_complexity_distribution` — lexical x rhetorical x difficulty cross-tab
7. `v_style_composition_profile` — full style fingerprint per question
8. `v_item_anatomy_profile` — blank position/evidence distribution counts
9. `v_option_anatomy_distribution` — distractor construction/eliminability breakdown
10. `v_distractor_pick_analysis` — raw distractor pick rates with context
11. `v_generation_run_summary` — per-run stats: requested/approved/avg realism
12. `v_module_form_spec` — human-readable module composition spec

**Alignment assessment:** Three views are generation-critical:
- `v_distractor_effectiveness` — feeds back into generation quality gates
- `v_generation_run_summary` — tracks generation pipeline performance
- `v_style_complexity_distribution` — calibrates difficulty spread for generation targets

The remaining views support observability and human review. `v_corpus_fingerprint` (present) is the most important single view for generation.

**Recommendation:** Add generation-critical views (2, 10, 11) in Phase 7b. Defer the rest to a follow-up.

---

#### H5. RLS on Only 4 of 21+ Tables

**Still present.** Worse: the Codex review found that `generated_questions` has RLS **enabled with no policies**, meaning authenticated clients get zero access.

**Alignment assessment:** Directly blocks the generation review UI. If the frontend needs to read generated questions for human review, it gets zero rows. Only service-role connections bypass RLS.

Missing RLS on `question_options` (answer keys) and `question_performance_records` (student data) are security concerns.

**Recommendation:**
- Add permissive read policy for `generated_questions` immediately
- Add RLS policies for `question_options` and `question_performance_records`
- Defer remaining tables — document that schema-level GRANTs will be used

---

#### H6. Migration Idempotency

**Partially fixed.** V1 migrations 038-042 use `IF NOT EXISTS` and `ON CONFLICT DO NOTHING`. But the PRD v2 M-004–M-028 seeds still use bare `INSERT INTO`.

**Alignment assessment:** Blocks safe re-deployment for generation testing. When iterating on generation pipeline changes, you need to be able to re-run migrations without manual cleanup.

**Recommendation:** All PRD v2 seed data should use `INSERT ... ON CONFLICT DO NOTHING`. All DDL should use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.

---

#### H7. Under-Seeded IRT-Critical Lookup Tables

**Still present.** The PRD v2 seeds IRT-critical tables with ordinal-scale values while the classification prompts and GROUND_TRUTH use specific diagnostic vocabulary:

| Table | PRD v2 Keys | GROUND_TRUTH/Seed Addendum Keys | Gap |
|-------|------------|--------------------------------|-----|
| `lookup_syntactic_trap` | 5 (ordinal) | 13 (specific trap types) | 8 specific keys |
| `lookup_syntactic_complexity` | 5 (ordinal) | 16 (specific) | 11 classification keys |
| `lookup_noun_phrase_complexity` | 3 (ordinal) | 8 (specific) | 5 classification keys |

The seed_data_addendum.md now defines all 13 trap keys, but the PRD v2 M-022 seeds have not been updated.

`fn_compute_irt_b_v1()` hardcodes ordinal mappings for the 5-key scales. If specific keys are added, the function needs a mapping layer.

**Alignment assessment:** The most impactful gap for generation quality. The generation prompt uses `target_syntactic_trap_key` — if only ordinal values like "moderate" exist, the generated question cannot embed specific difficulty mechanisms. A `target_syntactic_trap_key = 'nearest_noun_attraction'` tells the generation model to build a question where the verb matches the closest noun instead of the head noun. A value of "moderate" tells it nothing useful.

**Recommendation:** Seed the full diagnostic vocabularies from the seed_data_addendum.md. Add a mapping function `fn_map_diagnostic_to_ordinal()` that the IRT function uses internally. This preserves IRT scoring compatibility while giving generation and annotation the full vocabulary.

---

#### H8. Supabase-Specific Operational Gaps

**Still present.** Four issues:

1. `REFRESH MATERIALIZED VIEW CONCURRENTLY` fails under PgBouncer transaction-mode pooling
2. `image_data bytea` is an anti-pattern for Supabase (use Storage API)
3. pgvector version not pinned
4. No migration tracking via `supabase_migrations.schema_migrations`

**Alignment assessment:** Low direct impact on the four target capabilities, but high deployment risk. The bytea vs Storage API question affects question images in the generation pipeline — generated questions with images need a storage strategy.

**Recommendation:** Document PgBouncer direct-connection requirement. Use Supabase Storage for images. Pin pgvector version. Add `schema_migrations` table.

---

### MODERATE Gaps

#### M1. Frequency Label Mismatch

**Still present.** `sentence_boundary` has `frequency_label = 'medium'` but `avg_questions_per_module = 1.50`, which GROUND_TRUTH Part 5 classifies as "High" (1-2 questions/module).

**Alignment assessment:** Low impact on generation. Frequency labels are used for coaching priority, not generation targeting. But incorrect labels mislead human reviewers.

**Recommendation:** Change to `frequency_label = 'high'` in M-004 seeds.

---

#### M2. Missing `fn_rebuild_embedding_index()` Function

**Still present.** M-011 creates the IVFFlat index but provides no function to rebuild it when the corpus grows.

**Alignment assessment:** Moderate impact on text analysis. Embeddings are used for semantic similarity search in the question bank. Without a rebuild function, stale indexes degrade search quality over time.

**Recommendation:** Add `fn_rebuild_embedding_index()` to M-011 or M-020.

---

#### M3. Missing Indexes for Common Query Patterns

**Still present.** Eight missing indexes:

- Composite `(domain_key, difficulty_overall)` on `question_classifications`
- Standalone index on `grammar_focus_key`
- Composite `(question_id, annotation_type)` on `question_coaching_annotations`
- Index on `generation_runs(status)`
- Index on `ontology_proposals(status)`
- Index on `lookup_dimension_compatibility.severity`
- Composite `(is_active, retirement_status)` on `questions`
- Partial index on `question_coaching_annotations(show_condition)` for preloading `on_error` annotations

**Alignment assessment:** Performance-critical for generation (generation_runs status filtering), grammar analysis (grammar_focus_key lookups), and QA explanations (coaching annotation preloading).

**Recommendation:** Add all eight indexes in M-020 or a dedicated M-020b.

---

#### M4. M-004 Title Is Misleading

**Still present.** Titled "Seed All Lookup Tables" but only seeds 7 tables.

**Recommendation:** Rename to "Seed Critical Lookup Tables (Grammar, Domain, Topic, Annotation)".

---

#### M5. Comment Block Inaccuracy in M-004

**Still present.** The comment says "1 idiom" as a separate category, but `preposition_idiom` is inserted under `verb_form`, making verb_form = 6 (not 5).

**Recommendation:** Update comment to "4 sentence_boundary + 4 agreement + 6 verb_form (including preposition_idiom) + 4 modifier + 8 punctuation + 2 parallel_structure + 1 pronoun = 29."

---

#### M6. Missing `chk_passage_word_count` CHECK Constraint

**Still present.** The trigger computes `passage_word_count` but doesn't enforce bounds.

**Alignment assessment:** Important for generation — generated passages that are too short or too long fall outside DSAT parameters and need to be rejected.

**Recommendation:** Add `CONSTRAINT chk_passage_word_count CHECK (passage_text IS NULL OR passage_word_count BETWEEN 1 AND 800)` to M-005. Use 800 (not 500) to allow longer passages per DSAT specifications.

---

#### M7. No File Naming Convention Mapping

**Still present.** The PRD uses M-001..M-028 but doesn't map to actual filenames.

**Recommendation:** Add a "File Organization" section specifying naming convention (e.g., `v2/001_platform_foundation.sql`).

---

#### M8. `grammar_focus_frequency` Provenance Lost

**Still present.** V1 had a standalone `grammar_focus_frequency` table with `source_tests text[]`, `notes text`, and `last_updated_at timestamptz`. The v2 inline approach (`avg_questions_per_module`, `frequency_label` on `lookup_grammar_focus`) loses this provenance.

**Alignment assessment:** Moderate impact on grammar analysis credibility. Without provenance, you cannot trace which practice tests confirmed each frequency data point. This matters when validating generation against College Board patterns.

**Recommendation:** Add a `grammar_focus_frequency_evidence` table (as noted in ground_truth_issues.md):
```sql
CREATE TABLE grammar_focus_frequency_evidence (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    grammar_focus_key text NOT NULL REFERENCES lookup_grammar_focus(key),
    source_test text NOT NULL,
    questions_found int NOT NULL,
    notes text,
    confirmed_at timestamptz NOT NULL DEFAULT now()
);
```

---

### LOW Gaps

#### L1. `negation` vs `affirmative_agreement` Frequency Label Inconsistency

Both have `avg_questions_per_module = 0.00` but different labels (`very_low` vs `not_tested`). Should use the same label for 0.00.

**Recommendation:** Both should use `not_tested` for 0.00.

---

#### L2. Missing Passage-Level Tense Register (GROUND_TRUTH §8.4)

GROUND_TRUTH defines passage_type to expected_tense mappings. Neither the current schema nor the PRD v2 has a `passage_tense_register_key` field.

**Alignment assessment:** Relevant for generation — knowing the expected tense register for a passage type constrains the generation model's verb-form choices.

**Recommendation:** Defer to REBUILD_FUTURE_PLANS.md. The `prose_register_key` partially covers this. Add `passage_tense_register_key` when passage-level generation is in scope.

---

#### L3. `preposition_idiom` Role Ambiguity

The comment says "1 idiom" as a separate category, but SQL places it under `verb_form`. The taxonomy has no `idiom` role.

**Recommendation:** Document as deliberate: `preposition_idiom` maps to `verb_form` because preposition selection is governed by verb complementation patterns. Update the comment per M5 fix.

---

## Part 2: Codex SQL Bugs

### Bug 1. `v_coaching_panel` — `json_agg(DISTINCT)` Is Invalid

**Location:** PRD v2 M-020
**Status:** Still present

`json_agg(DISTINCT json_build_object(...) ORDER BY ss.step_index)` is invalid in PostgreSQL — `json` has no equality operator required for `DISTINCT`.

**Impact on QA explanations:** This view is the primary data source for the coaching panel UI. If it fails to create, the entire coaching/explanation feature is broken.

**Fix:**
```sql
(SELECT jsonb_agg(x ORDER BY x->>'step_index')
 FROM (SELECT DISTINCT jsonb_build_object(...) AS x
       FROM solver_steps ss WHERE ss.question_id = q.id) sub)
```

---

### Bug 2. `v_corpus_fingerprint` Unique Index Missing `domain_key`

**Location:** PRD v2 M-020
**Status:** Still present

`domain_key` is in the `GROUP BY` but absent from the unique index. Two domains with the same style tuple would collide on `REFRESH MATERIALIZED VIEW CONCURRENTLY`.

**Impact on generation:** The corpus fingerprint view calibrates generation targets. If two domains produce the same fingerprint, one silently overwrites the other, corrupting the calibration data that generation depends on.

**Fix:**
```sql
CREATE UNIQUE INDEX idx_v_corpus_fingerprint
    ON v_corpus_fingerprint(
        question_family_key, domain_key,  -- add domain_key
        syntactic_complexity_key, lexical_tier_key,
        inference_distance_key, evidence_distribution_key, prose_register_key
    );
```

---

### Bug 3. `fn_refresh_irt_b()` Silently Skips NULL Rows

**Location:** PRD v2 M-019
**Status:** Still present

`irt_b_source != 'field_test'` and `irt_b_rubric_version NOT IN ('empirical','manual')` both evaluate `NULL` as unknown, silently excluding rows with no source/rubric set.

**Impact on generation:** IRT difficulty scores are used for generation calibration. Rows silently skipped lose their IRT scores, creating gaps in the difficulty distribution that the generation pipeline uses.

**Fix:**
```sql
WHERE (p_question_id IS NULL OR question_id = p_question_id)
  AND (irt_b_rubric_version = 'v1' OR irt_b_source IS NULL)
  AND irt_b_source IS DISTINCT FROM 'field_test'
  AND (irt_b_rubric_version IS NULL
       OR irt_b_rubric_version NOT IN ('empirical','manual'));
```

---

### Bug 4. RLS on `generated_questions` with No Policies

**Location:** PRD v2 M-021
**Status:** Still present

RLS is enabled but no row-level policies are defined. Authenticated clients get zero access.

**Impact on generation review:** The frontend cannot display generated questions for human review. Only service-role connections bypass RLS.

**Fix:** Either add policies or defer RLS:
```sql
-- Option A: add a permissive policy for service role reads
CREATE POLICY "service_role_all" ON generated_questions
    USING (true) WITH CHECK (true);

-- Option B: defer RLS — remove ALTER TABLE ... ENABLE ROW LEVEL SECURITY from M-021
```

---

## Part 3: GROUND_TRUTH Drift Issues

### Drift 1. Syntactic Trap Key Mismatch (MOST URGENT)

**Status:** Still present — confirmed in live code

The LLM prompts list 21 `syntactic_trap_key` values. The v2 database seeds exactly 13. The 8 phantom keys will cause FK constraint violations on every ingestion or generation job that produces them.

**Phantom keys in pass2_annotation.py:40 and generation.py:145:**

| Phantom Key | In GROUND_TRUTH Part 7? | In v2 DB? |
|------------|------------------------|-----------|
| `agentless_passive` | No | No |
| `full_passive_by_phrase` | No | No |
| `object_relative_clause` | No | No |
| `stacked_prepositional_phrases` | No | No |
| `multiple_negation` | No | No |
| `conditional_stacking` | No | No |
| `long_preverbal_subject` | No | No |
| `tough_movement` | No | No |

**Impact:** This is a runtime failure, not a design gap. Any ingestion job where the LLM produces one of these 8 keys will fail the FK constraint on insert into `question_classifications.syntactic_trap_key`. The same applies to generation output via `target_syntactic_trap_key`.

**If any of these are observed in real questions**, they should be proposed via `ontology_proposals` and added to GROUND_TRUTH via the amendment process (GRAMMAR_AMENDMENT.md), then seeded into the DB through a new migration. They should not be silently allowed in the prompt without DB backing.

**Fix:** Remove the 8 phantom keys from both prompt files. Replace with the 13 keys from the seed_data_addendum.md.

---

### Drift 2. Disambiguation Rules — 11 of 12 in Prompt

**Status:** Still present

Priority 12 (`preposition_idiom > conjunction_usage`) is missing from the prompt because `preposition_idiom` was missing from the taxonomy. The grammar-taxonomy alignment doc (2026-04-21) added `preposition_idiom` to the taxonomy and proposed adding priority 12, but the prompt has not been updated.

**Impact on grammar classification:** When a question tests both preposition selection and conjunction usage, the LLM has no rule to decide which `grammar_focus_key` to assign. This creates inconsistent classifications across ingestion runs.

**Fix:** Add to pass2_annotation.py line 177:
```
12. preposition_idiom > conjunction_usage (preposition governed by verb complementation)
```

---

### Drift 3. Four Copies of Grammar Focus Keys — No Sync Mechanism

**Status:** Still present

The 29 `grammar_focus_key` values exist in four places with no automated synchronization:

| Copy | Location | Can Drift? |
|------|----------|------------|
| GROUND_TRUTH Part 3 | Document | Yes — manual updates |
| DB `lookup_grammar_focus` | M-004 seeds | Yes — requires migration |
| Prompt schema | `pass2_annotation.py` | Yes — hardcoded |
| Ontology mapping | `ontology.py FIELD_TO_TABLE` | Yes — hardcoded |

**Impact:** Any update to one must be manually propagated to the other three. The current state already shows drift (taxonomy v2 has 26 keys, PRD has 29, prompt has 29 with different role mappings).

**Proposed long-term fix (from ground_truth_issues.md):**
- A. Make GROUND_TRUTH the schema-of-record; generate prompt allowlists from DB lookup tables at runtime
- B. Move disambiguation rules into a `lookup_disambiguation_rule` table; render dynamically via `ontology_ref.py`
- C. Add a startup integrity check: verify prompt allowlists match DB keys
- D. Use the amendment process (GRAMMAR_AMENDMENT.md Part 10) as the formal drift resolution mechanism

**Alignment assessment:** All four proposals are excellent for the target capabilities. Proposal A eliminates the most common drift surface. Proposal B makes disambiguation rules version-controlled in the DB. Proposal C catches drift early. Proposal D formalizes the feedback loop from ingestion/annotation back to GROUND_TRUTH.

**Recommendation:** Implement C first (startup integrity check — lowest effort, highest immediate value). Then A (runtime allowlist generation). Then B (disambiguation rules in DB). D is already in place via GRAMMAR_AMENDMENT.md.

---

### Drift 4. No Startup Integrity Check

**Status:** Not implemented

The gap analysis documents propose this fix but no code exists.

**Recommendation:** Add to `app/main.py` lifespan startup:
```python
async def verify_ontology_integrity(ontology: dict):
    """Warn if prompt allowlists diverge from DB keys."""
    prompt_trap_keys = set(PASS2_SYNTACTIC_TRAP_KEYS)
    db_trap_keys = set(ontology.get("lookup_syntactic_trap", {}).keys())
    phantom = prompt_trap_keys - db_trap_keys
    missing = db_trap_keys - prompt_trap_keys
    if phantom:
        logger.warning(f"Phantom syntactic_trap keys in prompt: {phantom}")
    if missing:
        logger.warning(f"Missing syntactic_trap keys in prompt: {missing}")
```

---

## Part 4: What's Working Well

These elements are already well-aligned with the four target capabilities:

### For Generation

1. **Seed data addendum** (`seed_data_addendum.md`) — all lookup table seeds have explicit sources from GROUND_TRUTH and Taxonomy v2. Every `target_*` field has a validated vocabulary to draw from.

2. **Generation templates (migration 038)** — 9 templates with `constraint_schema` (required vs recommended fields) give the generation pipeline clear rules per question family. The `conventions_grammar_v1` template requires `target_grammar_focus_key` and recommends `target_grammar_role_key`, `target_syntactic_trap_key`, `target_syntactic_complexity_key`, and `target_syntactic_interruption_key`.

3. **REBUILD_FUTURE_PLANS.md** — correctly defers rhetorical_device, style_trait, and grammar_subfocus tables until generation fidelity requires them. Avoids premature abstraction.

4. **DB triggers for enforcement (M-017–M-019)** — SEC grammar, dimension compatibility, skill-family/domain consistency, and grammar-focus/role mapping are enforced at the DB level, meaning generation cannot write invalid classifications.

### For Text Analysis

5. **`ontology_ref.py`** — dynamically loads allowed keys from DB lookup tables and injects them into the LLM prompt. This is the correct architecture for keeping the prompt aligned with the DB.

6. **`fn_compute_irt_b_v1()` with `irt_b_quantitative_adjustment`** — the IRT difficulty function includes the quantitative adjustment term, providing calibrated difficulty estimates for generated questions.

7. **Embeddings infrastructure (M-011)** — IVFFlat index with cosine distance for semantic similarity search.

### For Grammar

8. **29 `grammar_focus_key` values with role mapping and disambiguation priority** — the full set from day 1 (vs. 27 keys that arrived piecemeal in v1).

9. **`grammar_keys` + `question_token_annotations` tables (migration 039)** — enable the interactive grammar UI with token-level annotations for visual grammar explanations.

10. **Amendment process (GRAMMAR_AMENDMENT.md)** — structured proposal format with `supporting_evidence` and `official_tests_with_pattern` keeps GROUND_TRUTH as an evolving system of record rather than a frozen document.

### For QA Explanations

11. **`option_label` on coaching annotations** — fixed from v1 gap. Enables linking distractor_lure spans to specific answer choices.

12. **`solver_steps` table** — replaced the dropped `primary_solver_steps_jsonb` column with a proper normalized table. Step-by-step solution logic is now structured data, not embedded JSON.

13. **`question_reasoning.coaching_summary`** — present from M-008 creation (vs. added late in v1 migration 034).

14. **`evidence_span_start_char` / `evidence_span_end_char`** — character-level evidence anchors in reasoning table enable precise passage highlighting in the explanation UI.

---

## Part 5: What's Still Blocking Excellence

### For Generation

| Blocker | Impact | Effort |
|---------|--------|--------|
| 8 phantom syntactic_trap keys in prompt | FK rejections on generation output | Small — remove from prompt |
| `target_syntactic_trap_key` in generation.py also lists phantoms | Same FK rejections | Small — same fix |
| `v_corpus_fingerprint` unique index bug | Corrupted calibration data | Trivial — add `domain_key` |
| IRT function NULL logic | Missing difficulty scores | Small — IS DISTINCT FROM |
| Under-seeded IRT lookup tables | Generation can only target ordinal difficulty, not specific mechanisms | Medium — add seeds + mapping function |

### For Grammar Analysis

| Blocker | Impact | Effort |
|---------|--------|--------|
| `elliptical_constructions → verb_form` in M-004 | Wrong role assignment cascades to generation and coaching | Small — change to `parallel_structure` |
| Disambiguation priority 12 missing | Inconsistent classification when preposition_idiom conflicts with conjunction_usage | Small — add to prompt |
| `pronoun_case` vs `pronoun_antecedent_agreement` priority tie | Ambiguous classification for pronoun questions | Trivial — set priorities 5 and 6 |
| 4 copies of grammar_focus keys with no sync | Drift accumulation over time | Medium — startup integrity check + runtime allowlist generation |

### For QA Explanations

| Blocker | Impact | Effort |
|---------|--------|--------|
| `v_coaching_panel` SQL bug (`json_agg(DISTINCT)`) | Coaching view fails to create — explanation UI broken | Small — use `jsonb_agg` subquery |
| Missing CHECK constraints on coaching annotations | Invalid spans break the highlight rendering | Small — add two constraints |
| RLS on `generated_questions` with no policies | Frontend cannot display generated questions for review | Small — add policy or defer RLS |
| `fn_refresh_irt_b()` NULL logic | Some questions lose IRT scores, affecting difficulty display | Small — IS DISTINCT FROM |

---

## Part 6: Recommended Priority Order

### Immediate (code fixes — no migration changes needed)

| # | Fix | File(s) | Effort |
|---|-----|---------|--------|
| 1 | Remove 8 phantom syntactic_trap keys from prompts | `pass2_annotation.py:40`, `generation.py:145` | Small |
| 2 | Add disambiguation priority 12 to prompt | `pass2_annotation.py:177` | Trivial |
| 3 | Add startup integrity check for key drift | `app/main.py` lifespan | Small |

### PRD v2 fixes (before writing migration SQL)

| # | Fix | Location | Effort |
|---|-----|----------|--------|
| 4 | Fix `elliptical_constructions → parallel_structure` | M-004 seeds | Trivial |
| 5 | Resolve `pronoun_case` / `pronoun_antecedent_agreement` priority | M-004 seeds | Trivial |
| 6 | Move critical lookup seeds into M-004 | M-004 + M-022 | Medium |
| 7 | Add `ON CONFLICT DO NOTHING` to all seeds | M-004 through M-028 | Small |
| 8 | Seed full diagnostic vocabularies for IRT tables | M-022 | Medium |
| 9 | Add `chk_span_char_order` + `chk_span_has_anchor` | M-015 | Small |
| 10 | Add `chk_passage_word_count` | M-005 | Trivial |
| 11 | Fix `v_coaching_panel` SQL | M-020 | Small |
| 12 | Fix `v_corpus_fingerprint` unique index | M-020 | Trivial |
| 13 | Fix `fn_refresh_irt_b()` NULL logic | M-019 | Small |
| 14 | Add RLS policies or defer RLS on `generated_questions` | M-021 | Small |
| 15 | Add 8 missing indexes | M-020b (new) | Small |
| 16 | Add `fn_rebuild_embedding_index()` | M-011 or M-020 | Small |
| 17 | Add `schema_migrations` tracking table | M-001 | Small |

### Deferred (document, don't implement yet)

| # | Item | Reason |
|---|------|--------|
| 18 | `lookup_disambiguation_rule` table | Replace hardcoded priorities with DB rows — do after startup check is working |
| 19 | `grammar_focus_frequency_evidence` table | Provenance tracking — add when frequency data is actively being validated |
| 20 | 12 missing analytical views | Add generation-critical 3 first, defer rest |
| 21 | Passage-level tense register | Defer per REBUILD_FUTURE_PLANS.md |
| 22 | Rhetorical device / style trait tables | Defer per REBUILD_FUTURE_PLANS.md |
| 23 | Grammar subfocus depth | Defer per REBUILD_FUTURE_PLANS.md |

---

## Part 7: Alignment Scorecard

How well does the current state (PRD v2 + existing docs) serve each capability?

| Capability | Current Score | After Fixes 1-17 | After All 23 | Notes |
|-----------|:---:|:---:|:---:|-------|
| **Generation** | B- | A- | A | Phantom keys + IRT seeding are the biggest blockers |
| **Text Analysis** | B | A- | A | Embeddings + ontology_ref work well; needs index + rebuild function |
| **Grammar Classification** | B | A | A | Role mapping fix + disambiguation completion are the key gaps |
| **QA Explanations** | C+ | B+ | A- | Coaching view SQL bug is the hardest blocker; CHECK constraints are easy |

---

*End of report. Next step: implement fixes 1-3 (code-only), then apply 4-17 to PRD v2 before writing migration SQL.*