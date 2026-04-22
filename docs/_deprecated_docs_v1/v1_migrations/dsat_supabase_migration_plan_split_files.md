# DSAT Supabase Migration Plan — Split Into Files

## Goal
This plan splits the production schema into migration-safe files that can be run in order in Supabase/Postgres.

Design principles:
- additive migrations first
- schema before seed data
- lookup tables before dependent tables
- views after all referenced tables exist
- indexes and triggers created idempotently
- future taxonomy growth handled mainly through lookup inserts rather than enum alterations

---

## Recommended Migration Order

```text
001_extensions.sql
002_functions.sql
003_core_sources.sql
004_lookup_tables.sql
005_questions.sql
006_classifications_and_options.sql
007_reasoning_and_generation.sql
008_taxonomy_graph.sql
009_embeddings.sql
010_triggers.sql
011_views.sql
012_seed_lookup_values.sql
013_seed_exam_structure_optional.sql
```

---

## 001_extensions.sql

### Purpose
Install required extensions once at the start.

### Contents
```sql
create extension if not exists vector;
create extension if not exists pgcrypto;
```

### Notes
- `vector` is required for pgvector embeddings.
- `pgcrypto` is used for `gen_random_uuid()`.

---

## 002_functions.sql

### Purpose
Create reusable helper functions.

### Contents
```sql
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;
```

### Notes
- Keep helper functions early so later trigger migrations can reference them safely.

---

## 003_core_sources.sql

### Purpose
Create the stable exam hierarchy.

### Tables
- `public.exams`
- `public.exam_sections`
- `public.exam_modules`

### Notes
- This layer changes rarely.
- Safe to keep strongly normalized.

---

## 004_lookup_tables.sql

### Purpose
Create all lookup tables used by taxonomy and generation metadata.

### Tables
- `public.lookup_question_family`
- `public.lookup_stimulus_mode`
- `public.lookup_stem_type`
- `public.lookup_evidence_scope`
- `public.lookup_evidence_location`
- `public.lookup_clue_distribution`
- `public.lookup_answer_mechanism`
- `public.lookup_solver_pattern`
- `public.lookup_distractor_type`
- `public.lookup_semantic_relation`
- `public.lookup_plausibility_source`
- `public.lookup_generation_pattern_family`

### Notes
- Lookup tables come before any tables that reference them.
- This is where most future taxonomy growth should happen.

---

## 005_questions.sql

### Purpose
Create the canonical question table.

### Tables
- `public.questions`

### Dependencies
- core source hierarchy
- lookup tables for `stimulus_mode_key` and `stem_type_key`

### Notes
- This file should include indexes specific to `questions`.
- Keep prompt/stimulus content in this layer.

---

## 006_classifications_and_options.sql

### Purpose
Create classification and answer-choice analysis tables.

### Tables
- `public.question_classifications`
- `public.question_options`

### Dependencies
- `public.questions`
- all referenced lookup tables

### Notes
- This file is central to your taxonomy system.
- `question_options` is critical for LLM-ready distractor modeling.

---

## 007_reasoning_and_generation.sql

### Purpose
Create reasoning traces and generation-profile tables.

### Tables
- `public.question_reasoning`
- `public.question_generation_profiles`

### Dependencies
- `public.questions`
- lookup tables for clue distribution and generation pattern family

### Notes
- This is the layer most useful for retrieval-augmented generation and prompt construction.

---

## 008_taxonomy_graph.sql

### Purpose
Create optional graph-style ontology tables.

### Tables
- `public.taxonomy_nodes`
- `public.taxonomy_edges`
- `public.question_taxonomy_links`

### Notes
- This layer is optional.
- It is useful if you want navigable taxonomy trees or multi-parent ontology links.
- If you want a simpler first production rollout, this file can be deferred.

---

## 009_embeddings.sql

### Purpose
Create embedding storage and vector indexes.

### Tables
- `public.question_embeddings`

### Notes
- Keep this separate so embedding dimensions can be changed in an isolated migration later if needed.
- The ivfflat index should be created only after the table exists.
- In production, build vector indexes only after enough rows exist for them to be useful.

---

## 010_triggers.sql

### Purpose
Attach `updated_at` triggers to all mutable tables.

### Pattern
Use:
```sql
drop trigger if exists ...;
create trigger ...;
```

### Tables to attach
- `public.exams`
- `public.exam_sections`
- `public.exam_modules`
- `public.questions`
- `public.question_classifications`
- `public.question_options`
- `public.question_reasoning`
- `public.question_generation_profiles`
- `public.taxonomy_nodes`
- all lookup tables if you want `updated_at` maintained there too

### Notes
- This file should run after all target tables exist.

---

## 011_views.sql

### Purpose
Create convenience views for export and ingestion checks.

### Views
- `public.question_flat_export`

### Notes
- Views go late because they depend on many tables.
- If you later add reporting views, keep them in separate files like `011_views_reporting.sql`.

---

## 012_seed_lookup_values.sql

### Purpose
Seed the initial taxonomy and generation lookup values.

### Pattern
Use:
```sql
insert into ... values ...
on conflict (key) do nothing;
```

### Seeds to include
- question families
- stimulus modes
- stem types
- evidence scopes
- evidence locations
- clue distributions
- answer mechanisms
- solver patterns
- distractor types
- semantic relations
- plausibility sources
- generation pattern families

### Notes
- This file should contain only seed rows, not schema definitions.
- Future taxonomy updates should usually be additional migration files like:
  - `014_seed_new_generation_patterns.sql`
  - `015_seed_new_semantic_relations.sql`

---

## 013_seed_exam_structure_optional.sql

### Purpose
Optionally seed known exams/sections/modules for your pilot dataset.

### Typical rows
- `PT4`
- `Reading and Writing`
- `Module 1`
- `Module 2`

### Notes
- Keep this separate from lookup seeds.
- In some environments, exam content may be loaded by application code instead.

---

## Suggested Directory Structure

```text
supabase/
  migrations/
    001_extensions.sql
    002_functions.sql
    003_core_sources.sql
    004_lookup_tables.sql
    005_questions.sql
    006_classifications_and_options.sql
    007_reasoning_and_generation.sql
    008_taxonomy_graph.sql
    009_embeddings.sql
    010_triggers.sql
    011_views.sql
    012_seed_lookup_values.sql
    013_seed_exam_structure_optional.sql
```

---

## Deployment Strategy

### Phase 1: Core schema only
Run:
- 001 through 011

This gives you an empty but fully structured database.

### Phase 2: Taxonomy seed
Run:
- 012

This makes foreign-key-backed taxonomy values available.

### Phase 3: Pilot source structure
Run:
- 013

This creates exam/module rows for pilot ingestion.

### Phase 4: Ingest pilot questions
Load the pilot question set after all prior migrations succeed.

---

## Migration Safety Rules

### Prefer additive migrations
- add new tables
- add new nullable columns
- add new indexes with `if not exists`
- add new lookup rows with `on conflict do nothing`

### Avoid brittle operations when possible
- avoid dropping columns in early versions
- avoid postgres enum changes for evolving taxonomy values
- avoid changing embedding dimension in-place

### For breaking changes later
Use phased migrations:
1. add new column/table
2. backfill data
3. switch reads/writes in application
4. remove old column/table in a later migration

---

## Future Migration Examples

### Adding a new generation pattern
File:
```text
014_seed_new_generation_patterns.sql
```
Example:
```sql
insert into public.lookup_generation_pattern_family (key, display_name, sort_order)
values ('quote_claim_match', 'Quote Claim Match', 190)
on conflict (key) do nothing;
```

### Adding a new nullable question field
File:
```text
015_add_questions_source_url.sql
```
Example:
```sql
alter table public.questions
add column if not exists source_url text;
```

### Adding a new reporting view
File:
```text
016_reporting_views.sql
```

---

## Recommended Next Artifact
After this migration plan, the next useful artifact is:
- a **starter set of actual migration file contents** for files 001–013
- then a **pilot ingestion template** for PT4 question records

