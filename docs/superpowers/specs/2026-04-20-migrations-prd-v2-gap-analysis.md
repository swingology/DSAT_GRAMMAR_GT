# Migrations PRD v2 — Gap Analysis

**Date:** 2026-04-20  
**Document Reviewed:** `docs/Migrations_PRD_v2_rebuild.md` v2.0  
**Cross-Referenced Against:** GROUND_TRUTH_GRAMMAR v1.2, Taxonomy v2.6, db_schema_diagram.md, original PRD v1, historical migrations 025/034/016  
**Severity Scale:** CRITICAL → HIGH → MODERATE → LOW

---

## CRITICAL Gaps (Must Fix Before Deployment)

### C1. Deployment Order Bug — FK Seeds After Table Creation

`questions` (M-005) has `NOT NULL` FKs to `lookup_stimulus_mode` and `lookup_stem_type`, both seeded in M-022. `question_classifications` (M-006) has a `NOT NULL` FK to `lookup_question_family`, also seeded in M-022.

The deployment order lists M-022 *after* M-005/M-006. While DDL-only `CREATE TABLE` succeeds without data, any `INSERT` into `questions` before M-022 runs will violate FK constraints. The dependency rules (lines 2576-2585) state "M-022 through M-028 can run in parallel after M-003" but do NOT capture the requirement that M-022 must complete before first question insert.

**Fix:** Either (a) add explicit dependency rule "M-022 must run before any data insert into questions/question_classifications" or (b) move seed data for NOT NULL FK targets into M-004 alongside the grammar seeds.

### C2. No Rollback / Downgrade Plan

Zero mention of "rollback," "downgrade," "revert," or "reverse migration." All 28 migrations are `CREATE TABLE` / `INSERT INTO` statements with no corresponding `DOWN` files. A mid-sequence failure leaves the database in a partially-migrated state with FK references to empty tables.

Seed migrations use bare `INSERT INTO` without `ON CONFLICT DO NOTHING`, so re-running M-004 after a partial failure produces duplicate key violations.

**Fix:** Add a `down/` directory with reverse SQL for each migration, or wrap seeds in `INSERT ... ON CONFLICT DO NOTHING`.

### C3. No Data Migration Plan from Old Schema (001-042)

The PRD frames this as a "greenfield rebuild" but doesn't address users with existing data. No ETL strategy exists for:
- Migrating the existing corpus of official DSAT questions
- Column renames (`topic_fine` text → `topic_fine_key` FK)
- Dropped columns (`primary_solver_steps_jsonb` → `solver_steps` table)
- New required columns with no old-schema equivalent (`no_change_is_correct`, `target_mirror_status`)

**Fix:** Add a Phase 9 "Data Migration" section, or explicitly document that re-ingestion from source is required.

### C4. No Concurrent Migration Safety

No `pg_advisory_lock`, no Supabase `schema_migrations` tracking table, no transaction wrapping per migration. Running migrations from two terminals or two CI pipelines simultaneously will corrupt state via duplicate inserts and partial DDL application.

**Fix:** Add a `schema_migrations` tracking table in M-001 and advisory lock acquisition at each migration boundary.

---

## HIGH Gaps (Should Fix)

### H1. Grammar Focus Role Mapping Errors

| Key | GROUND_TRUTH | Taxonomy §7.9 | PRD v2 | Conflict |
|---|---|---|---|---|
| `elliptical_constructions` | §3.6 Parallel Structure | `parallel_structure` | **`verb_form`** | Contradicts BOTH authoritative sources |
| `affirmative_agreement` | §3.2 Agreement Rules | `verb_form` | `agreement` | GROUND_TRUTH says agreement, Taxonomy says verb_form |

**Fix:** Change `elliptical_constructions` to `parallel_structure` role (matching both sources). Decide explicitly on `affirmative_agreement` — document the choice.

### H2. Disambiguation Priority Collision

`pronoun_case` and `pronoun_antecedent_agreement` are both assigned `disambiguation_priority = 5`. GROUND_TRUTH §4.5 states "pronoun_case > pronoun_antecedent_agreement" — meaning pronoun_case should have a lower number (higher precedence).

**Fix:** Set `pronoun_case` priority to 5, `pronoun_antecedent_agreement` to 6 (or adjust both to reflect the stated precedence rule).

### H3. Missing CHECK Constraints on `question_coaching_annotations`

Historical migration 034 created:
- `chk_span_char_order` — ensures `span_end_char > span_start_char` when both present
- `chk_span_has_anchor` — ensures at least one location anchor (char offset OR sentence index), with exemption for `blank_context` type

The v2 rebuild has **neither** constraint. This allows invalid span ranges and anchorless annotations that the UI cannot render.

**Fix:** Add to M-015:
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

### H4. 12 Analytical Views Missing

The current schema has 18+ views. PRD v2 M-020 creates only 7. These 12 are absent:

1. `v_question_distribution` — counts by domain/family/difficulty per module
2. `v_distractor_effectiveness` — distractor type effectiveness by family
3. `v_embedding_coverage` — which embedding types are present/missing
4. `v_ingestion_pipeline_summary` — job count by status/model
5. `v_prose_complexity_profile` — aggregate syntactic/style fingerprint counts
6. `v_style_complexity_distribution` — lexical × rhetorical × difficulty cross-tab
7. `v_style_composition_profile` — full style fingerprint per question
8. `v_item_anatomy_profile` — blank position/evidence distribution counts
9. `v_option_anatomy_distribution` — distractor construction/eliminability breakdown
10. `v_distractor_pick_analysis` — raw distractor pick rates with context
11. `v_generation_run_summary` — per-run stats: requested/approved/avg realism
12. `v_module_form_spec` — human-readable module composition spec

**Fix:** Add Phase 7b or extend M-020 with these views, or document that they will be added in a follow-up.

### H5. RLS on Only 4 of 21+ Tables

M-021 enables RLS on `questions`, `question_classifications`, `question_ingestion_jobs`, and `generated_questions` only. Missing from RLS:

- `question_options` (contains answer keys — high sensitivity)
- `question_performance_records` (student performance data)
- `question_embeddings` (vector data)
- `question_generation_profiles` (generation IP)
- `generation_templates` (LLM prompts)
- 12 other tables

**Fix:** Either add RLS policies for all data tables, or document that schema-level GRANTs will be used and specify the GRANT strategy.

### H6. Migration Idempotency

Only functions (`CREATE OR REPLACE`) and extensions (`IF NOT EXISTS`) are idempotent. All DDL (`CREATE TABLE`, `CREATE INDEX`, `CREATE TRIGGER`) and all DML (`INSERT INTO`) will fail on re-run. This combines with C2 (no rollback) to make recovery from partial failures extremely manual.

**Fix:** Use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, and `INSERT ... ON CONFLICT DO NOTHING` for all seed data.

### H7. Under-Seeded IRT-Critical Lookup Tables

The PRD seeds IRT-critical lookup tables with only ordinal-scale values (5 values for syntactic_complexity, 5 for syntactic_trap, 3 for noun_phrase_complexity) while the current schema and classification prompts use the full diagnostic vocabulary:

| Table | Current Keys | PRD v2 Keys | Missing |
|---|---|---|---|
| `lookup_syntactic_trap` | 21 (specific trap types) | 5 (ordinal) | 16 specific trap keys |
| `lookup_syntactic_complexity` | 16 | 5 | 11 classification keys |
| `lookup_noun_phrase_complexity` | 8 | 3 | 5 classification keys |

`fn_compute_irt_b_v1()` hardcodes ordinal mappings for the 5-key scales, which works. But the classification prompts will produce specific keys (e.g., `nearest_noun_attraction`) that don't exist in the 5-key lookup tables. This creates a validation gap: the LLM will produce keys that don't exist, and the FK constraint will reject them.

**Fix:** Either (a) seed the full diagnostic vocabularies AND update `fn_compute_irt_b_v1()` to map them to ordinal scores, or (b) add a mapping layer in the validator that normalizes specific keys to ordinal keys before DB insert.

### H8. Supabase-Specific Operational Gaps

1. **PgBouncer compatibility** — `REFRESH MATERIALIZED VIEW CONCURRENTLY` in M-020 cannot run inside a transaction block, which fails under PgBouncer transaction-mode pooling. No guidance on using direct connections.
2. **`image_data bytea`** — Storing binary data in PostgreSQL is an anti-pattern for Supabase (which provides a Storage API). No discussion of using Supabase Storage buckets.
3. **pgvector version** — `CREATE EXTENSION IF NOT EXISTS vector` doesn't pin a version. `ivfflat` with `lists = 100` assumes pgvector >= 0.5.0.
4. **No migration tracking** — No reference to `supabase_migrations.schema_migrations` or equivalent tracking mechanism.

---

## MODERATE Gaps (Worth Fixing)

### M1. Frequency Label Mismatch

`sentence_boundary` catch-all: GROUND_TRUTH Part 5 says "High" frequency (1-2 questions/module), but PRD v2 seeds `frequency_label = 'medium'` with `avg_questions_per_module = 1.50`. The label contradicts the empirical data.

**Fix:** Change to `frequency_label = 'high'` or document why 1.50 maps to "medium."

### M2. Missing `fn_rebuild_embedding_index()` Function

The current schema defines this function for rebuilding the IVFFlat index when the corpus grows. M-011 creates the index but provides no function to rebuild it.

**Fix:** Add `fn_rebuild_embedding_index()` to M-011 or M-020.

### M3. Missing Indexes for Common Query Patterns

- No composite `(domain_key, difficulty_overall)` on `question_classifications`
- No standalone index on `grammar_focus_key` (covered only by composite `grammar_role_key, grammar_focus_key`)
- No composite `(question_id, annotation_type)` on `question_coaching_annotations`
- No index on `generation_runs(status)`
- No index on `ontology_proposals(status)`
- No index on `lookup_dimension_compatibility.severity` (needed by M-017 trigger)
- No composite `(is_active, retirement_status)` on `questions`
- Partial index on `question_coaching_annotations(show_condition)` for preloading `on_error` annotations

**Fix:** Add these indexes to the appropriate migration.

### M4. M-004 Title Is Misleading

M-004 is titled "Seed All Lookup Tables" but only seeds 7 tables (grammar_role, grammar_focus, domain, passage_topic_fine, coaching_annotation_type, reasoning_step_type, dimension_compatibility). The remaining 37+ tables are seeded across M-022 through M-028.

**Fix:** Rename M-004 to "Seed Critical Lookup Tables (Grammar, Domain, Topic, Annotation)" and update the Phase 8 summary accordingly.

### M5. Comment Block Inaccuracy in M-004

The comment claims "4 sentence_boundary + 4 agreement + 5 verb_form + 4 modifier + 8 punctuation + 2 parallel_structure + 1 pronoun + 1 idiom = 29" but the actual SQL inserts `preposition_idiom` under `verb_form`, making verb_form = 6 (not 5). The "1 idiom" category doesn't exist as a separate role.

**Fix:** Update comment to "4 sentence_boundary + 4 agreement + 6 verb_form (including preposition_idiom) + 4 modifier + 8 punctuation + 2 parallel_structure + 1 pronoun = 29."

### M6. Missing `chk_passage_word_count` CHECK Constraint

PRD v1 migration 044 proposed `CHECK (passage_text IS NULL OR passage_word_count BETWEEN 1 AND 500)`. The v2 rebuild computes `passage_word_count` via trigger but doesn't enforce bounds.

**Fix:** Add `CONSTRAINT chk_passage_word_count CHECK (passage_text IS NULL OR passage_word_count BETWEEN 1 AND 800)` to M-005. (Use 800 not 500 to allow longer passages.)

### M7. No File Naming Convention Mapping

The PRD uses M-001..M-028 but doesn't map to actual filenames. Existing migrations use patterns like `001_006_core_schema.sql`. No directory structure specified for v2 alongside v1.

**Fix:** Add a "File Organization" section specifying naming convention (e.g., `v2/001_platform_foundation.sql`) and directory structure.

### M8. `grammar_focus_frequency` Provenance Lost

PRD v1 had a standalone `grammar_focus_frequency` table with `source_tests text[]`, `notes text`, and `last_updated_at timestamptz`. The v2 inline approach (`avg_questions_per_module`, `frequency_label` on `lookup_grammar_focus`) loses this provenance — you can no longer trace which practice tests confirmed each frequency data point.

**Fix:** Either add provenance columns to `lookup_grammar_focus` or create a `grammar_focus_frequency_evidence` table.

---

## LOW Gaps (Noteworthy)

### L1. `negation` vs `affirmative_agreement` Frequency Label Inconsistency

Both have `avg_questions_per_module = 0.00` but `negation` gets `very_low` while `affirmative_agreement` gets `not_tested`. These should either both use `not_tested` or both use `very_low` with 0.00.

### L2. Missing Passage-Level Tense Register (GROUND_TRUTH §8.4)

GROUND_TRUTH defines a passage_type → expected_tense mapping (narrative=past, scientific fact=present, etc.). Neither the current schema nor the PRD v2 has a field to capture this (`passage_tense_register_key` or equivalent).

### L3. `preposition_idiom` Role Ambiguity

The comment says "1 idiom" as a separate category, but the SQL places `preposition_idiom` under `verb_form`. The Taxonomy v2.6 has no `idiom` role. This should be documented as a deliberate choice pending a taxonomy update.

---

## Summary Priority Matrix

| Priority | Count | Action Required |
|----------|-------|-----------------|
| CRITICAL | 4 | Must fix before any deployment attempt |
| HIGH | 8 | Must fix before production; acceptable for dev/staging |
| MODERATE | 8 | Should fix; will cause issues at scale |
| LOW | 3 | Document or defer |

**Total gaps identified: 23** (4 critical, 8 high, 8 moderate, 3 low)