# Migrations V2 Reorganization Plan

> **Goal:** Reorganize 42 linear migrations into logical domain folders under `backend/migrations_v2/` to reduce confusion, improve discoverability, and make future schema evolution clearer.

> **Why:** The current flat structure (001-042) mixes unrelated concerns: core schema, taxonomy expansions, ingestion pipeline, generation lifecycle, UI features, and cleanup/fix migrations are all interleaved. New contributors (or future you) cannot quickly answer "where do I add a new lookup table?" or "what migrations affect the generation pipeline?"

---

## Current State Analysis

### Migration Count by Domain

| Domain | Migrations | Count |
|--------|-----------|-------|
| **Core Schema** | 001-006, 007-013 | 13 files (bundled) |
| **Ingestion Pipeline** | 014, 037, 038 | 3 files |
| **Taxonomy Expansions** | 017, 018, 019, 024, 025, 028, 029, 032, 041, 042 | 10 files |
| **Generation Lifecycle** | 020, 021, 026, 027, 031, 035, 036 | 7 files |
| **Student/Coaching Features** | 022, 034, 040 | 3 files |
| **Ontology Management** | 023 | 1 file |
| **Reporting & Views** | 015, 033, 038 | 3 files |
| **RLS & Security** | 016 | 1 file |
| **Cleanup/Consolidation** | 030, 038 | 2 files |

### Problems with Current Structure

1. **No separation of concerns** — A migration adding a lookup table sits next to one adding UI coaching annotations
2. **Consolidation migrations are confusing** — 025, 030, 032, 038 are "fix-up" migrations that should have been part of earlier work
3. **No clear path forward** — Where does migration 043 go? What number does it get?
4. **Hard to audit** — "Show me all migrations that affect generation profiles" requires grepping 42 files

---

## Proposed V2 Structure

```
backend/migrations_v2/
├── 00_core/
│   ├── 001_extensions.sql
│   ├── 002_functions.sql
│   ├── 003_core_sources.sql
│   ├── 004_questions_schema.sql
│   ├── 005_taxonomy_nodes.sql
│   └── 006_reasoning_generation.sql
│
├── 01_ingestion_pipeline/
│   ├── 010_staging_table.sql           # was 014
│   ├── 011_reporting_views.sql         # was 015
│   ├── 012_rls_policies.sql            # was 016
│   └── 019_backfill_pre014_columns.sql # was 037
│
├── 02_taxonomy_expansions/
│   ├── 020_prose_grammar_complexity.sql    # was 017
│   ├── 021_writing_style_complexity.sql    # was 018
│   ├── 022_discourse_generation_factors.sql # was 019
│   ├── 023_style_composition.sql           # was 024
│   ├── 024_consolidation.sql               # was 025
│   ├── 025_drop_taxonomy_graph.sql         # was 028
│   ├── 026_taxonomy_constraints.sql        # was 029
│   ├── 027_schema_constraints_cleanup.sql  # was 032
│   ├── 028_new_grammar_focus_categories.sql # was 041
│   └── 029_additional_grammar_categories.sql # was 042
│
├── 03_generation_lifecycle/
│   ├── 030_item_anatomy_passage_fingerprint.sql # was 020
│   ├── 031_generation_lifecycle.sql             # was 021
│   ├── 032_generation_profile_style_gaps.sql    # was 026
│   ├── 033_content_hash.sql                     # was 027
│   ├── 034_generation_profile_gaps.sql          # was 031
│   ├── 035_generated_questions_traceability.sql # was 035
│   └── 036_source_origin_constraint.sql         # was 036
│
├── 04_student_coaching/
│   ├── 040_student_performance.sql          # was 022
│   ├── 041_coaching_annotations.sql         # was 034
│   └── 042_tokenization_status.sql          # was 040
│
├── 05_ontology_management/
│   └── 050_ontology_proposals.sql           # was 023
│
├── 06_reporting_security/
│   ├── 060_irt_b_rubric.sql                 # was 033
│   └── 061_fresh_build_context_reconciliation.sql # was 038
│
└── README.md                               # Migration ordering + how to apply
```

---

## Migration Mapping Table

| Old # | New Path | New # | Notes |
|-------|----------|-------|-------|
| 001-006 | `00_core/` | 001-006 | Split bundled file into atomic files |
| 007-013 | `00_core/` | 007-013 | Split bundled file into atomic files |
| 014 | `01_ingestion_pipeline/010_staging_table.sql` | 010 | Renamed for clarity |
| 015 | `01_ingestion_pipeline/011_reporting_views.sql` | 011 | — |
| 016 | `01_ingestion_pipeline/012_rls_policies.sql` | 012 | — |
| 017 | `02_taxonomy_expansions/020_prose_grammar_complexity.sql` | 020 | Renumbered |
| 018 | `02_taxonomy_expansions/021_writing_style_complexity.sql` | 021 | — |
| 019 | `02_taxonomy_expansions/022_discourse_generation_factors.sql` | 022 | — |
| 020 | `03_generation_lifecycle/030_item_anatomy.sql` | 030 | Shortened name |
| 021 | `03_generation_lifecycle/031_generation_lifecycle.sql` | 031 | — |
| 022 | `04_student_coaching/040_student_performance.sql` | 040 | — |
| 023 | `05_ontology_management/050_ontology_proposals.sql` | 050 | — |
| 024 | `02_taxonomy_expansions/023_style_composition.sql` | 023 | — |
| 025 | `02_taxonomy_expansions/024_consolidation.sql` | 024 | — |
| 026 | `03_generation_lifecycle/032_generation_profile_style_gaps.sql` | 032 | — |
| 027 | `03_generation_lifecycle/033_content_hash.sql` | 033 | — |
| 028 | `02_taxonomy_expansions/025_drop_taxonomy_graph.sql` | 025 | — |
| 029 | `02_taxonomy_expansions/026_taxonomy_constraints.sql` | 026 | — |
| 030 | `00_core/014_schema_cleanup.sql` | 014 | Moved to core (it's cleanup) |
| 031 | `03_generation_lifecycle/034_generation_profile_gaps.sql` | 034 | — |
| 032 | `02_taxonomy_expansions/027_schema_constraints_cleanup.sql` | 027 | — |
| 033 | `06_reporting_security/060_irt_b_rubric.sql` | 060 | — |
| 034 | `04_student_coaching/041_coaching_annotations.sql` | 041 | — |
| 035 | `03_generation_lifecycle/035_generated_questions_traceability.sql` | 035 | — |
| 036 | `03_generation_lifecycle/036_source_origin_constraint.sql` | 036 | — |
| 037 | `01_ingestion_pipeline/019_backfill_pre014_columns.sql` | 019 | — |
| 038 | `06_reporting_security/061_fresh_build_reconciliation.sql` | 061 | Shortened name |
| 039 | `04_student_coaching/043_grammar_keys_token_annotations.sql` | 043 | — |
| 040 | `04_student_coaching/042_tokenization_status.sql` | 042 | — |
| 041 | `02_taxonomy_expansions/028_new_grammar_focus_categories.sql` | 028 | — |
| 042 | `02_taxonomy_expansions/029_additional_grammar_categories.sql` | 029 | — |

---

## Implementation Steps

### Task 1: Create Directory Structure

- [ ] **Step 1.1:** Create `backend/migrations_v2/` directory
- [ ] **Step 1.2:** Create subdirectories:
  ```bash
  cd backend/migrations_v2
  mkdir -p 00_core 01_ingestion_pipeline 02_taxonomy_expansions \
           03_generation_lifecycle 04_student_coaching \
           05_ontology_management 06_reporting_security
  ```

### Task 2: Split Bundled Migrations (001-006, 007-013)

- [ ] **Step 2.1:** Read `001_006_core_schema.sql` and split into 6 atomic files:
  - `00_core/001_extensions.sql` — `create extension` statements
  - `00_core/002_functions.sql` — `set_updated_at()` function
  - `00_core/003_core_sources.sql` — `exams`, `exam_sections` tables
  - `00_core/004_questions_schema.sql` — `questions`, `question_options` tables
  - `00_core/005_taxonomy_nodes.sql` — `taxonomy_nodes`, `taxonomy_edges`
  - `00_core/006_reasoning_generation.sql` — `question_reasoning`, `question_generation_profiles`

- [ ] **Step 2.2:** Read `007_013_extended_schema.sql` and split into 7 atomic files:
  - `00_core/007_reasoning_and_generation.sql`
  - `00_core/008_taxonomy_graph.sql`
  - `00_core/009_lookup_tables_core.sql`
  - `00_core/010_embeddings.sql`
  - `00_core/011_exam_modules.sql`
  - `00_core/012_views.sql`
  - `00_core/013_indexes.sql`

> **Note:** If the bundled files don't have clear section markers, split by logical table/group boundaries.

### Task 3: Copy and Rename Remaining Migrations

- [ ] **Step 3.1:** Copy migrations to their new locations per the mapping table above
- [ ] **Step 3.2:** Update header comments in each file to reflect new path/number
- [ ] **Step 3.3:** Remove `IF NOT EXISTS` from `CREATE TABLE` statements (optional — safe to keep for idempotency)

### Task 4: Write Migration Ordering README

- [ ] **Step 4.1:** Create `backend/migrations_v2/README.md`:

```markdown
# DSAT Migrations V2

Migrations are organized by domain. Apply in order within each domain, then proceed to the next domain.

## Application Order

1. `00_core/` — Core schema (extensions, functions, base tables)
2. `01_ingestion_pipeline/` — Staging tables, RLS policies
3. `02_taxonomy_expansions/` — Lookup table expansions (prose grammar, style, discourse)
4. `03_generation_lifecycle/` — Generation templates, runs, traceability
5. `04_student_coaching/` — Student performance, coaching annotations
6. `05_ontology_management/` — Ontology proposals workflow
7. `06_reporting_security/` — IRT rubric, reconciliation

## How to Apply

```bash
cd backend
DB_URL=$(grep SUPABASE_DB_URL .env | cut -d= -f2-)

# Apply a single domain
psql "$DB_URL" -f migrations_v2/00_core/001_extensions.sql
psql "$DB_URL" -f migrations_v2/00_core/002_functions.sql
# ... continue in order

# Or apply all (Unix only)
for f in migrations_v2/*/[^_]*.sql; do
  psql "$DB_URL" -f "$f"
done
```

## Naming Conventions

- Prefix files with `NN_` where NN is the order within the domain
- Use snake_case for filenames
- Prefix lookup table migrations with `lookup_` if they only add lookup data

## Adding New Migrations

1. Determine the domain (core, ingestion, taxonomy, generation, student, ontology, reporting)
2. Pick the next available number in that domain
3. Add header comment with migration purpose
4. Use `BEGIN;` / `COMMIT;` for transactional safety
5. Test on a fresh database before committing
```

### Task 5: Create Schema Log

- [ ] **Step 5.1:** Create `log_schema_migrations_v2.md` at repo root documenting:
  - Why reorganization was done
  - Mapping from old to new migration numbers
  - How to verify migrations applied correctly

### Task 6: Verification

- [ ] **Step 6.1:** Verify all 42 original migrations are represented in V2
- [ ] **Step 6.2:** Run a test apply against a fresh Supabase project (or local Postgres with vector extension)
- [ ] **Step 6.3:** Compare table counts between old and new application

```bash
# After applying old migrations (001-042)
psql "$DB_URL" -c "\dt public.*" | wc -l

# After applying new migrations (V2)
psql "$DB_URL" -c "\dt public.*" | wc -l

# Should match
```

### Task 7: Deprecate Old Migrations

- [ ] **Step 7.1:** Move `backend/migrations/` to `backend/migrations_v1_deprecated/`
- [ ] **Step 7.2:** Add `DEPRECATED.md` in `migrations_v1_deprecated/`:

```markdown
# Deprecated Migrations

These migrations (001-042) have been superseded by `migrations_v2/`.

**Do not use for new work.** New migrations should be added to `migrations_v2/` following the README.md ordering.

## Why Deprecated?

- Flat structure made it hard to find related migrations
- Consolidation migrations (025, 030, 032, 038) were confusing
- No clear path for adding new migrations

See `../migrations_v2/README.md` for the new structure.
```

### Task 8: Update CLAUDE.md

- [ ] **Step 8.1:** Update the `CLAUDE.md` file to reference `migrations_v2/` instead of `backend/migrations/`

---

## Rollback Plan

If the reorganization causes issues:

1. Keep `migrations_v1_deprecated/` intact for 30 days
2. If a fresh database build fails with V2, revert to applying V1 migrations
3. Document any missing migrations or ordering issues in `log_schema_migrations_v2.md`

---

## Files Changed

| Action | Path |
|--------|------|
| Create | `backend/migrations_v2/` (directory tree) |
| Create | `backend/migrations_v2/README.md` |
| Create | `backend/migrations_v1_deprecated/` (moved from `backend/migrations/`) |
| Create | `backend/migrations_v1_deprecated/DEPRECATED.md` |
| Create | `log_schema_migrations_v2.md` (repo root) |
| Modify | `CLAUDE.md` — update migration path reference |

---

## Success Criteria

- [ ] All 42 original migrations are represented in V2
- [ ] Fresh database build succeeds with V2 migrations
- [ ] Table count matches between V1 and V2 application
- [ ] README.md provides clear ordering and application instructions
- [ ] Schema log documents the reorganization rationale
